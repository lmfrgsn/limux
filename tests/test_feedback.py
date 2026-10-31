import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import mako  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


feedback = load('feedback', ROOT/'scripts/activate-feedback.py')
firewall = load('firewall', ROOT/'scripts/firewall.py')
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
BIN = ROOT/'machine/home/.local/bin'


class LevelCardTests(unittest.TestCase):
    def test_level_card_section(self):
        text = mako.render(THEME)
        section = text.split(f'[category={mako.LEVEL}]\n', 1)[1]
        self.assertIn('width=240\n', section)
        self.assertIn('history=0\n', section)
        self.assertIn('foreground="#343442"', section)   # graphite label over the canvas fill
        self.assertEqual(text.count('history=0'), 1)

    def test_quiet_level_label_is_refused(self):
        theme = copy.deepcopy(THEME)
        theme['mako']['level_label'] = 'text_quiet'   # about 4:1 over the canvas fill
        with self.assertRaises(ValueError):
            mako.render(theme)

    def test_pins_match_sources(self):
        feedback.sources(json.loads(feedback.MANIFEST.read_text()))
        manifest = json.loads((ROOT/'themes/recovery/mako.json').read_text())
        self.assertEqual(__import__('hashlib').sha256(mako.render(THEME).encode()).hexdigest(), manifest['baseline_sha256'])

    def test_helpers_parse(self):
        for name in feedback.HELPERS:
            subprocess.run(['bash', '-n', str(BIN/name)], check=True)
        subprocess.run(['bash', '-n', str(ROOT/'scripts/limux-update')], check=True)

    def test_level_call_is_added_and_removed_exactly(self):
        with tempfile.TemporaryDirectory() as folder:
            control = Path(folder)/'t2-hardware-control'
            original = b'#!/usr/bin/env bash\ncase "$1" in\n    volume-up) true ;;\nesac\n'
            control.write_bytes(original)
            with patch.object(feedback, 'CONTROL', control):
                self.assertFalse(feedback.control_state())
                feedback.write(control, original + feedback.LEVEL_CALL.encode(), 0o755)
                self.assertTrue(feedback.control_state())
                subprocess.run(['bash', '-n', str(control)], check=True)
                control.write_bytes(control.read_bytes().replace(feedback.LEVEL_CALL.encode(), b''))
                self.assertEqual(control.read_bytes(), original)
                control.write_bytes(original + b'limux-level volume\n')
                with self.assertRaises(RuntimeError):
                    feedback.control_state()


class BatteryWarningTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('dbus-run-session') and shutil.which('mako'), 'needs mako')
    def test_thresholds_once_each_and_clear_on_charging(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder/'bat').mkdir()
            (folder/'rt').mkdir()
            (folder/'config').write_text('max-history=0\n')
            script = folder/'run.sh'
            script.write_text(f'''
mako -c {folder}/config & m=$!; sleep 0.8
set_bat() {{ echo $1 > {folder}/bat/capacity; echo $2 > {folder}/bat/status; sleep 1.2; }}
shown() {{ makoctl list | grep -o 'Battery at [0-9]*%' | paste -sd, ; }}
set_bat 12 Discharging
XDG_RUNTIME_DIR={folder}/rt LIMUX_BATTERY={folder}/bat LIMUX_BATTERY_INTERVAL=0.3 {BIN}/limux-battery & w=$!
sleep 0.8; echo "a=$(shown)"
set_bat 9 Discharging; echo "b=$(shown)"
set_bat 8 Discharging; echo "c=$(shown)"
set_bat 4 Discharging; echo "d=$(shown)"
set_bat 4 Charging; echo "e=$(shown)"
kill $w $m
''')
            out = subprocess.run(['dbus-run-session', '--', 'bash', str(script)], capture_output=True, text=True, timeout=30).stdout
            seen = dict(re.findall(r'^(\w)=(.*)$', out, re.M))
            self.assertEqual(seen, {'a': '', 'b': 'Battery at 9%', 'c': 'Battery at 9%', 'd': 'Battery at 4%', 'e': ''})


class FirewallTests(unittest.TestCase):
    def test_ruleset_blocks_ssh_and_keeps_replies(self):
        self.assertNotIn('dport ssh', firewall.RULESET)
        self.assertIn('policy drop', firewall.RULESET)
        self.assertIn('ct state {established, related} accept', firewall.RULESET)
        self.assertIn('dhcpv6-client', firewall.RULESET)

    def test_recovery_copy_is_intact(self):
        firewall.default_bytes()

    @unittest.skipUnless(shutil.which('unshare') and shutil.which('nft'), 'needs nft')
    def test_ruleset_validates(self):
        try:
            firewall.validate(firewall.RULESET)
        except subprocess.CalledProcessError as exc:
            if 'Operation not permitted' in exc.stderr:
                self.skipTest('user namespaces unavailable')
            raise


class UpdateTests(unittest.TestCase):
    def test_every_check_exists_with_that_action(self):
        text = (ROOT/'scripts/limux-update').read_text()
        checks = re.findall(r"^\s+'[^|']+\|(\S+) (\w+)'$", text, re.M)
        self.assertGreaterEqual(len(checks), 15)
        for script, action in checks:
            source = (ROOT/'scripts'/script).read_text()
            self.assertRegex(source, rf"choices=\[[^\]]*'{action}'", script)


if __name__ == '__main__':
    unittest.main()
