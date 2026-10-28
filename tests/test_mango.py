import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from mango import extract, merge, render, values, KEYS
spec = importlib.util.spec_from_file_location('mango_control', ROOT/'scripts/mango-appearance.py')
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
MANIFEST = json.loads((ROOT/'themes/recovery/mango.json').read_text())


def fixture():
    owned = ''.join(f'  {k} = {v}  # keep this comment\r\n' for k,v in MANIFEST['rollback'].items())
    return ('# machine-specific functionality\r\nblur=0\r\nshadows=0\r\n'
            'monitor_rule=name:eDP-1,width:2880,height:1800,refresh:60,scale:1.5\r\n'
            'bind=SUPER,m,quit\r\nbind=SUPER,n,switch_layout\r\n'
            'animation_duration_close=800\r\nexec_once=/do/not/run\r\n' + owned).encode()


class MangoTests(unittest.TestCase):
    def test_lossless_visual_only_roundtrip(self):
        original = fixture()
        merged = merge(original, values(THEME))
        self.assertEqual(extract(merged), values(THEME))
        self.assertEqual(merge(merged, extract(original)), original)
        self.assertEqual(merged.splitlines()[:8], original.splitlines()[:8])
        self.assertEqual(merged.count(b'keep this comment'), len(KEYS))
        self.assertEqual(merged.count(b'\r\n'), original.count(b'\r\n'))

    def test_rejects_duplicates_missing_keys_includes_and_functional_injection(self):
        for data in (fixture()+b'focus_color=0x77768FFF\n', fixture()+b'source=other.conf\n',
                     fixture().replace(b'  focus_color',b'# focus_color')):
            with self.assertRaises(ValueError):
                merge(data, values(THEME))
        malicious = values(THEME)
        malicious['focus_color'] = '0x77768FFF\nbind=SUPER,m,quit'
        with self.assertRaises(ValueError):
            merge(fixture(), malicious)
        malicious = values(THEME)
        malicious['blur'] = '1'
        with self.assertRaises(ValueError):
            merge(fixture(), malicious)

    def test_shared_palette_and_alpha(self):
        v = values(THEME)
        self.assertEqual(v['focus_color'], '0x77768FFF')
        self.assertEqual(v['urgent_color'], '0xAD4038FF')
        self.assertEqual(v['drop_color'], '0x72885855')
        other = copy.deepcopy(THEME)
        other['colors']['accent'] = '#123456'
        self.assertEqual(values(other)['focus_color'], '0x123456FF')
        other['mango']['drop_alpha'] = 256
        with self.assertRaises(ValueError):
            values(other)
        import hashlib
        self.assertEqual(MANIFEST['approved_sha256'], hashlib.sha256(render(THEME).encode()).hexdigest())
        self.assertEqual(MANIFEST['candidate_values'], values(THEME))

    @unittest.skipUnless(shutil.which('mango'), 'MangoWM not installed')
    def test_native_full_config_validation(self):
        control.native_check(fixture())
        control.native_check(merge(fixture(), values(THEME)))
        import subprocess
        with self.assertRaises(subprocess.CalledProcessError):
            control.native_check(fixture()+b'unknown_limux_setting=1\n')

    def test_permanent_activation_locked_before_live_access(self):
        unapproved = dict(MANIFEST, approved_sha256=None)
        with patch.object(control.json, 'loads', return_value=unapproved), \
             patch.object(sys, 'argv', ['mango-appearance.py','activate']), patch.object(control,'read_live') as read:
            with self.assertRaisesRegex(RuntimeError, 'awaits user visual approval'):
                control.main()
            read.assert_not_called()

    def test_restore_keeps_nonvisual_edits_and_recovers_after_failed_reload(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)/'state';state.mkdir()
            live = Path(d)/'config.conf';live.write_bytes(fixture())
            with patch.object(control,'STATE',state), patch.object(control,'LIVE',live), \
                 patch.object(control,'reload_config', side_effect=[RuntimeError('IPC failure'),None]), \
                 patch.object(control.subprocess,'Popen'), patch.object(control,'native_check'):
                with self.assertRaisesRegex(RuntimeError,'IPC failure'):
                    control.apply(fixture(),merge(fixture(),values(THEME)),30)
                self.assertEqual(live.read_bytes(),fixture())
                self.assertFalse((state/'pending.json').exists())
            record={'id':'test','before':extract(fixture()),'after':values(THEME)}
            live.write_bytes(merge(fixture(),values(THEME))+b'# added during preview\n')
            (state/'pending.json').write_text(json.dumps(record))
            with patch.object(control,'STATE',state), patch.object(control,'LIVE',live), \
                 patch.object(control,'reload_config'):
                control.restore(record)
            self.assertEqual(live.read_bytes(),fixture()+b'# added during preview\n')

    def test_watchdog_restores_abandoned_preview_and_ignores_other_operation(self):
        with tempfile.TemporaryDirectory() as d:
            state=Path(d)/'state';state.mkdir()
            live=Path(d)/'config.conf';live.write_bytes(merge(fixture(),values(THEME)))
            record={'id':'pending','before':extract(fixture()),'after':values(THEME)}
            (state/'pending.json').write_text(json.dumps(record))
            with patch.object(control,'STATE',state), patch.object(control,'LIVE',live), \
                 patch.object(control,'reload_config'), patch.object(control.time,'sleep'):
                control.watchdog('different',0)
                self.assertTrue((state/'pending.json').exists())
                control.watchdog('pending',0)
            self.assertEqual(live.read_bytes(),fixture())
            self.assertFalse((state/'pending.json').exists())

    def test_concurrent_visual_edit_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            live=Path(d)/'config.conf'
            unexpected=values(THEME);unexpected['border_px']='3'
            data=merge(fixture(),unexpected);live.write_bytes(data)
            with patch.object(control,'LIVE',live):
                with self.assertRaisesRegex(RuntimeError,'concurrently'):
                    control.restore({'before':extract(fixture()),'after':values(THEME)})
            self.assertEqual(live.read_bytes(),data)

    def test_approved_activation_survives_watchdog_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)/'state'; state.mkdir()
            live = Path(d)/'config.conf'; live.write_bytes(fixture())
            candidate = merge(fixture(), values(THEME))
            with patch.object(control, 'STATE', state), patch.object(control, 'LIVE', live), \
                 patch.object(control, 'reload_config') as reload, patch.object(control, 'native_check'), \
                 patch.object(control.subprocess, 'Popen'), patch.object(control.time, 'sleep'):
                record = control.apply(fixture(), candidate)
                self.assertFalse((state/'pending.json').exists())
                control.watchdog(record['id'], 0)
                self.assertEqual(live.read_bytes(), candidate)
                control.apply(candidate, candidate)
                self.assertEqual(live.read_bytes(), candidate)
                with patch.object(sys, 'argv', ['mango-appearance.py', 'rollback']):
                    control.main()
                self.assertEqual(live.read_bytes(), fixture())
                self.assertEqual(reload.call_count, 3)

    def test_apply_rejects_nonvisual_change_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)/'state'; state.mkdir()
            live = Path(d)/'config.conf'; live.write_bytes(fixture())
            candidate = merge(fixture(), values(THEME)).replace(b'shadows=0', b'shadows=1')
            with patch.object(control, 'STATE', state), patch.object(control, 'LIVE', live):
                with self.assertRaisesRegex(RuntimeError, 'outside the 16'):
                    control.apply(fixture(), candidate)
            self.assertEqual(live.read_bytes(), fixture())
            self.assertFalse((state/'pending.json').exists())

    @unittest.skipUnless(shutil.which('mango'), 'MangoWM not installed')
    def test_verify_requires_approved_values_and_reachable_session(self):
        with tempfile.TemporaryDirectory() as d:
            live = Path(d)/'config.conf'; live.write_bytes(fixture())
            with patch.object(control, 'LIVE', live), patch.object(control, 'session') as session, \
                 patch.object(sys, 'argv', ['mango-appearance.py', 'verify']):
                with self.assertRaisesRegex(RuntimeError, 'does not contain the approved'):
                    control.main()
                session.assert_not_called()
                live.write_bytes(merge(fixture(), values(THEME)))
                control.main()
                session.assert_called_once_with(MANIFEST['version'])
                session.side_effect = RuntimeError('session unavailable')
                with self.assertRaisesRegex(RuntimeError, 'session unavailable'):
                    control.main()
                self.assertEqual(live.read_bytes(), merge(fixture(), values(THEME)))
