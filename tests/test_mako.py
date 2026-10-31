import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from mako import FUNCTIONAL, render
spec = importlib.util.spec_from_file_location('activate_mako', ROOT/'scripts/activate-mako.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
MANIFEST = json.loads((ROOT/'themes/recovery/mako.json').read_text())
ORIGINAL = (ROOT/'themes/recovery'/MANIFEST['recovery_file']).read_bytes()


class MakoAdapterTests(unittest.TestCase):
    def test_fragment_is_appearance_only_and_token_coloured(self):
        text = render(THEME)
        section = ''
        for line in text.splitlines():
            section = line if line.startswith('[') else section
            # The single behaviour exception: Limux's own level card stays out of history.
            if line == 'history=0' and section == '[category=limux.level]':
                continue
            self.assertNotIn(line.split('=', 1)[0], FUNCTIONAL)
        tokens = {v.upper() for v in THEME['colors'].values()}
        for colour in re.findall(r'#[0-9A-Fa-f]{6}', text):
            self.assertIn(colour.upper(), tokens)
        self.assertIn('font=Inter 10', text)
        self.assertIn('icons=0', text)

    def test_contrast_is_enforced(self):
        t = copy.deepcopy(THEME)
        t['mako']['label'] = 'metal'
        with self.assertRaisesRegex(ValueError, 'contrast'):
            render(t)

    def test_generated_fragment_matches_approval_pin(self):
        self.assertEqual(hashlib.sha256(render(THEME).encode()).hexdigest(), MANIFEST['baseline_sha256'])
        self.assertEqual(hashlib.sha256(ORIGINAL).hexdigest(), MANIFEST['original_sha256'])

    def test_active_config_keeps_behaviour_and_drops_appearance(self):
        active = a.active_from(ORIGINAL, Path('/x/rhapsody')).decode()
        for line in ('anchor=top-right', 'default-timeout=5000', 'max-visible=3', 'default-timeout=0'):
            self.assertIn(line, active)
        for key in ('font', 'background-color', 'border-color', 'padding', 'width'):
            self.assertNotRegex(active, rf'(?m)^{key}=')
        self.assertLess(active.index('include=/x/rhapsody'), active.index('[urgency=critical]'))


class MakoActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name)
        self.config, self.style = folder/'config', folder/'rhapsody'
        self.config.write_bytes(ORIGINAL)
        self.data = a.candidate(MANIFEST)

    def tearDown(self):
        self.tmp.cleanup()

    def test_activate_and_rollback_are_exact_and_idempotent(self):
        with patch.object(a, 'reload') as reload:
            _, _, original, active = a.versions(self.config, self.style, MANIFEST)
            a.transition(self.config, self.style, active, self.data)
            self.assertEqual(self.config.read_bytes(), active)
            self.assertEqual(self.style.read_bytes(), self.data)
            a.transition(self.config, self.style, active, self.data)
            a.transition(self.config, self.style, original, None)
            self.assertEqual(self.config.read_bytes(), ORIGINAL)
            self.assertFalse(self.style.exists())
            self.assertEqual(reload.call_count, 3)

    def test_failed_reload_restores_prior_bytes(self):
        _, _, _, active = a.versions(self.config, self.style, MANIFEST)
        with patch.object(a, 'reload', side_effect=[RuntimeError('reload failed'), None]):
            with self.assertRaisesRegex(RuntimeError, 'reload failed'):
                a.transition(self.config, self.style, active, self.data)
        self.assertEqual(self.config.read_bytes(), ORIGINAL)
        self.assertFalse(self.style.exists())

    def test_unknown_config_or_fragment_is_refused(self):
        self.config.write_bytes(ORIGINAL + b'\nfont=Hand Edited 12\n')
        with self.assertRaisesRegex(RuntimeError, 'Unknown Mako configuration'):
            a.versions(self.config, self.style, MANIFEST)
        self.config.write_bytes(ORIGINAL)
        self.style.write_bytes(b'font=Other 9\n')
        with self.assertRaisesRegex(RuntimeError, 'Unknown Mako appearance'):
            a.versions(self.config, self.style, MANIFEST)


if __name__ == '__main__':
    unittest.main()
