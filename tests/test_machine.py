import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('machine', ROOT/'scripts/machine.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MachineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home, self.system, store = root/'home', root/'system', root/'store'
        for rel in m.HOME_FILES[:2]:
            (store/'home'/rel).parent.mkdir(parents=True, exist_ok=True)
            (store/'home'/rel).write_text(f'stored {rel}\n')
        script = store/'home'/m.HOME_FILES[-1]
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text('#!/bin/sh\n')
        script.chmod(0o755)
        system = store/'system'/m.SYSTEM_FILES[0].lstrip('/')
        system.parent.mkdir(parents=True, exist_ok=True)
        system.write_text('GRUB_DEFAULT=0\n')
        patches = [patch.object(m, 'STORE', store), patch.object(m, 'PACKAGES', store/'packages.txt'),
                   patch.object(m, 'explicit_packages', return_value='base\n')]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.store = store

    def tearDown(self):
        self.tmp.cleanup()

    def test_restore_fills_only_missing_home_files_and_lists_system_steps(self):
        first = self.home/m.HOME_FILES[0]
        first.parent.mkdir(parents=True)
        first.write_text('my own edit\n')
        restored, conflicts, pending = m.restore(self.home, self.system)
        self.assertEqual(first.read_text(), 'my own edit\n')
        self.assertEqual(conflicts, [first])
        self.assertIn(self.home/m.HOME_FILES[1], restored)
        self.assertTrue(os.access(self.home/m.HOME_FILES[-1], os.X_OK))
        self.assertEqual([live for _, live in pending], [self.system/m.SYSTEM_FILES[0].lstrip('/')])
        self.assertFalse((self.system/m.SYSTEM_FILES[0].lstrip('/')).exists())

    def test_capture_then_status_is_clean_for_tracked_files(self):
        m.restore(self.home, self.system)
        edited = self.home/m.HOME_FILES[1]
        edited.write_text('changed live\n')
        self.assertIn(f'differs: {edited}', m.status(self.home, self.system, live_checks=False))
        with patch.object(m, 'HOME_FILES', m.HOME_FILES[:2] + m.HOME_FILES[-1:]), \
                patch.object(m, 'SYSTEM_FILES', ()), patch.object(m, 'ROOT', self.store.parent):
            m.capture(self.home, self.system)
            self.assertEqual(m.status(self.home, self.system, live_checks=False), [])
        self.assertEqual((self.store/'home'/m.HOME_FILES[1]).read_text(), 'changed live\n')

    def test_symlinked_live_files_are_never_replaced(self):
        link = self.home/m.HOME_FILES[1]
        link.parent.mkdir(parents=True)
        link.symlink_to(self.home/'elsewhere')
        _, conflicts, _ = m.restore(self.home, self.system)
        self.assertIn(link, conflicts)
        self.assertTrue(link.is_symlink())

    def test_private_and_generated_files_are_not_tracked(self):
        tracked = set(m.HOME_FILES)
        private = {'.config/limux/commands.toml', '.config/limux/location'}
        generated = {'.config/gtk-3.0/gtk.css', '.config/foot/rhapsody.ini', '.config/mako/rhapsody',
                     '.config/rofi/charcoal.rasi', '.config/Thunar/accels.scm',
                     '.config/mangobar/style.css', '.config/mangobar/config.jsonc',
                     '.config/hypr/limux-lock.conf'}
        self.assertFalse(tracked & (private | generated))
        self.assertNotIn('/etc/fstab', m.SYSTEM_FILES)
        stored = {p.relative_to(ROOT/'machine/home').as_posix() for p in (ROOT/'machine/home').rglob('*') if p.is_file()}
        self.assertEqual(stored, tracked)


if __name__ == '__main__':
    unittest.main()
