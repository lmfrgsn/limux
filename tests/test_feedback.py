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
    """Runs the real watcher against a stand-in battery with stand-in notify-send and
    makoctl that only log, so the test never starts Mako or reaches the screen."""

    def run_watcher(self, steps, charge=True):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            bat, stubs, log = folder/'bat', folder/'bin', folder/'log'
            bat.mkdir(); stubs.mkdir(); (folder/'rt').mkdir()
            (stubs/'notify-send').write_text('#!/bin/sh\necho "notify $*" >> "$STUB_LOG"\necho 7\n')
            (stubs/'makoctl').write_text('#!/bin/sh\necho "makoctl $*" >> "$STUB_LOG"\n')
            for stub in stubs.iterdir():
                stub.chmod(0o755)

            def set_battery(percent, status):
                if charge:   # worn battery: full is 75% of design, as on this MacBook
                    (bat/'charge_full').write_text('7500\n')
                    (bat/'charge_now').write_text(f'{percent * 75}\n')
                    (bat/'capacity').write_text(f'{round(percent * 0.75)}\n')
                else:
                    (bat/'capacity').write_text(f'{percent}\n')
                (bat/'status').write_text(status + '\n')

            env = {**os.environ, 'PATH': f'{stubs}:{os.environ["PATH"]}', 'STUB_LOG': str(log),
                   'XDG_RUNTIME_DIR': str(folder/'rt'), 'LIMUX_BATTERY': str(bat),
                   'LIMUX_BATTERY_INTERVAL': '0.1', 'WAYLAND_DISPLAY': '', 'DBUS_SESSION_BUS_ADDRESS': 'disabled:'}
            set_battery(*steps[0])
            watcher = subprocess.Popen([str(BIN/'limux-battery')], env=env)
            try:
                seen = []
                for percent, status in steps:
                    set_battery(percent, status)
                    __import__('time').sleep(0.5)
                    seen.append(log.read_text().splitlines() if log.exists() else [])
            finally:
                watcher.terminate()
                watcher.wait(5)
            return seen

    def test_thresholds_once_each_and_clear_on_charging(self):
        seen = self.run_watcher([(12, 'Discharging'), (9, 'Discharging'), (8, 'Discharging'),
                                 (4, 'Discharging'), (4, 'Charging')])
        notes = [line for line in seen[-1] if line.startswith('notify')]
        self.assertEqual(seen[0], [])
        self.assertEqual(len(notes), 2)
        self.assertIn('Battery at 9%', notes[0])
        self.assertIn('Battery at 4%', notes[1])
        self.assertIn('--replace-id=7', notes[1])          # the 5% card replaces the 10% one
        self.assertIn('makoctl dismiss -n 7', seen[-1])

    def test_uses_the_bars_percentage_not_design_capacity(self):
        # At a true 12% of what it holds now, design capacity reads 9%: no warning yet.
        seen = self.run_watcher([(12, 'Discharging')])
        self.assertEqual(seen[-1], [])

    def test_falls_back_to_capacity(self):
        seen = self.run_watcher([(9, 'Discharging')], charge=False)
        self.assertIn('Battery at 9%', seen[-1][0])


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


class LlmnrTests(unittest.TestCase):
    def test_dropin_turns_off_only_llmnr(self):
        llmnr = load('llmnr', ROOT/'scripts/llmnr.py')
        settings = [line for line in llmnr.CONTENT.splitlines() if '=' in line and not line.startswith('#')]
        self.assertEqual(settings, ['LLMNR=no'])
        self.assertIn('[Resolve]', llmnr.CONTENT)

    def test_edited_dropin_is_refused(self):
        llmnr = load('llmnr', ROOT/'scripts/llmnr.py')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'limux-no-llmnr.conf'
            with patch.object(llmnr, 'DROPIN', path):
                self.assertEqual(llmnr.state(), 'original')
                path.write_text(llmnr.CONTENT)
                self.assertEqual(llmnr.state(), 'active')
                path.write_text(llmnr.CONTENT + 'MulticastDNS=no\n')
                with self.assertRaises(RuntimeError):
                    llmnr.state()


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
