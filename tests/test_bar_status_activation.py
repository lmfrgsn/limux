import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('activate_bar_status', ROOT/'scripts/activate-bar-status.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
MANIFEST = json.loads((ROOT/'themes/recovery/bar-status.json').read_text())
QUIET_CONFIG = json.dumps({
    'layer': 'top', 'height': 30, 'modules-left': ['workspaces', 'window'], 'modules-center': ['clock'],
    'modules-right': ['tray', 'custom/wifi', 'battery', 'pulseaudio'], 'window': {'max-length': 240},
    'custom/wifi': {'exec': 'python3 /home/x/.local/share/limux/mangobar/wifi-status.py', 'interval': 5},
    'battery': {'device': 'BAT0'}, 'pulseaudio': {'format': 'Vol {volume}%'}}, indent=2).encode()


def h(data):
    return hashlib.sha256(data).hexdigest()


class BarStatusActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        paths = {'STATE': root/'state/bar-status', 'QUIET_STATE': root/'state/quiet',
                 'CONFIG': root/'mangobar/config.jsonc', 'CSS': root/'mangobar/style.css',
                 'PATCHED': root/'libexec/mangobar', 'WIFI': root/'share/wifi-status.py',
                 'FONT': root/'fonts/limux/tabler.ttf', 'RULE': root/'fontconfig/conf.d/60.conf',
                 'CLAUDE': root/'claude/settings.json', 'CODEX': root/'codex/hooks.json'}
        self.p = paths
        self.original = {'config': QUIET_CONFIG, 'css': b'/* quiet */\n', 'binary': b'quiet-binary',
                         'wifi': b'# old wifi\n'}
        for name, key in (('config', 'CONFIG'), ('css', 'CSS'), ('binary', 'PATCHED'), ('wifi', 'WIFI')):
            paths[key].parent.mkdir(parents=True, exist_ok=True)
            paths[key].write_bytes(self.original[name])
        paths['QUIET_STATE'].mkdir(parents=True)
        (paths['QUIET_STATE']/'manifest.json').write_text(json.dumps({
            'candidate': {'config': h(QUIET_CONFIG), 'css': h(self.original['css'])}, 'binary': h(b'quiet-binary')}))
        paths['CLAUDE'].parent.mkdir(parents=True)
        self.claude_before = b'{\n  "theme": "light"\n}\n'
        paths['CLAUDE'].write_bytes(self.claude_before)
        config, css, rule = a.generate(QUIET_CONFIG)
        self.manifest = dict(MANIFEST, config=h(config), css=h(css), rule=h(rule), binary=h(b'status-binary'),
                             wifi_previous_sha256=h(self.original['wifi']),
                             font=dict(MANIFEST['font'], sha256=h(b'font')))
        self.running = {'binary': None}
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        for key, value in paths.items():
            stack.enter_context(patch.object(a, key, value))
        stack.enter_context(patch.object(a, 'build_binary', return_value=b'status-binary'))
        stack.enter_context(patch.object(a, 'fetch_font', return_value=b'font'))
        stack.enter_context(patch.object(a, 'fc_cache'))
        stack.enter_context(patch.object(a, 'refresh_bar'))
        stack.enter_context(patch.object(a.subprocess, 'run'))

    def tearDown(self):
        self.tmp.cleanup()

    def test_activate_then_rollback_restores_every_byte(self):
        a.activate(self.manifest)
        self.assertEqual(set(a.classify(self.manifest).values()), {'active'})
        settings = json.loads(self.p['CLAUDE'].read_text())
        self.assertEqual(settings['theme'], 'light')
        self.assertEqual(set(settings['hooks']), set(a.CLAUDE_EVENTS))
        self.assertTrue(all(h_['async'] for g in settings['hooks'].values() for grp in g for h_ in grp['hooks']))
        codex = json.loads(self.p['CODEX'].read_text())['hooks']
        self.assertNotIn('async', codex['SessionEnd'][0]['hooks'][0])
        a.activate(self.manifest)  # idempotent
        a.rollback(self.manifest)
        for name, key in (('config', 'CONFIG'), ('css', 'CSS'), ('binary', 'PATCHED'), ('wifi', 'WIFI')):
            self.assertEqual(self.p[key].read_bytes(), self.original[name], name)
        self.assertEqual(self.p['CLAUDE'].read_bytes(), self.claude_before)
        for key in ('CODEX', 'FONT', 'RULE', 'STATE'):
            self.assertFalse(self.p[key].exists(), key)
        self.assertEqual(set(a.classify(self.manifest).values()), {'original'})

    def test_rollback_keeps_claude_settings_the_user_changed_since(self):
        a.activate(self.manifest)
        settings = json.loads(self.p['CLAUDE'].read_text())
        settings['model'] = 'opus'
        self.p['CLAUDE'].write_text(json.dumps(settings))
        a.rollback(self.manifest)
        self.assertEqual(json.loads(self.p['CLAUDE'].read_text()), {'theme': 'light', 'model': 'opus'})

    def test_failure_midway_restores_everything(self):
        with patch.object(a, 'codex_document', side_effect=[a.codex_document(), RuntimeError('boom')]):
            with self.assertRaisesRegex(RuntimeError, 'activation failed'):
                a.activate(self.manifest)
        self.assertEqual(self.p['PATCHED'].read_bytes(), b'quiet-binary')
        self.assertEqual(self.p['CLAUDE'].read_bytes(), self.claude_before)
        self.assertFalse(self.p['STATE'].exists())
        self.assertFalse(self.p['FONT'].exists())

    def test_unknown_values_are_refused(self):
        self.p['CODEX'].parent.mkdir(parents=True)
        self.p['CODEX'].write_text('{"hooks": {}}')
        with self.assertRaisesRegex(RuntimeError, 'codex'):
            a.activate(self.manifest)
        self.assertEqual(self.p['PATCHED'].read_bytes(), b'quiet-binary')

    def test_pins_match_the_live_generators(self):
        self.assertEqual(h(a.codex_document()), MANIFEST['codex'])
        self.assertEqual(h(a.WIFI_SOURCE.read_bytes()), MANIFEST['wifi'])


if __name__ == '__main__':
    unittest.main()
