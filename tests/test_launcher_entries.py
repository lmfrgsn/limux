import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('launcher_entries', ROOT/'scripts/launcher-entries.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
MANIFEST = json.loads((ROOT/'themes/recovery/launcher-entries.json').read_text())


def system_fixture(folder):
    folder.mkdir()
    (folder/'thunar.desktop').write_text(
        '[Desktop Entry]\nName[en_GB]=Thunar File Manager\nName=Thunar File Manager\nGenericName=File Manager\n'
        'Exec=thunar %F\nActions=open-home;\n\n[Desktop Action open-home]\nName=Home\nExec=thunar %U\n')
    (folder/'foot.desktop').write_text('[Desktop Entry]\nName=Foot\nGenericName=Terminal\nExec=foot\n')
    (folder/'btop.desktop').write_text('[Desktop Entry]\nName=btop++\nGenericName=System Monitor\n'
                                       'GenericName[it]=Monitor di sistema\nExec=btop\nTerminal=true\n')
    return folder


class LauncherEntriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.system = system_fixture(root/'system')
        self.live = root/'data/applications'
        files, sources = e.generate(self.system)
        self.files = files
        self.manifest = {'sources': sources, 'files': {n: e.digest(d) for n, d in files.items()}}

    def tearDown(self):
        self.tmp.cleanup()

    def test_rename_touches_only_the_main_entry(self):
        thunar = self.files['thunar.desktop'].decode()
        self.assertIn('Name=Files\n', thunar)
        self.assertIn('GenericName=Thunar\n', thunar)
        self.assertNotIn('Name[en_GB]', thunar)
        self.assertIn('Exec=thunar %F\n', thunar)
        self.assertIn('[Desktop Action open-home]\nName=Home\n', thunar)
        self.assertIn('Name=Terminal\n', self.files['foot.desktop'].decode())
        monitor = self.files['btop.desktop'].decode()
        self.assertIn('Name=Activity Monitor\nGenericName=btop\n', monitor)
        self.assertNotIn('Monitor di sistema', monitor)
        self.assertIn('Terminal=true\n', monitor)

    def test_hidden_entries_use_the_desktop_entry_hidden_key(self):
        for app in e.HIDE:
            self.assertIn(b'Hidden=true\n', self.files[f'{app}.desktop'])

    def test_activate_and_rollback_are_exact_and_idempotent(self):
        e.activate(self.live, self.manifest, self.files)
        self.assertEqual(set(e.classify(self.live, self.manifest).values()), {'active'})
        self.assertEqual(e.activate(self.live, self.manifest, self.files), [])
        self.assertEqual(e.rollback(self.live, self.manifest), [])
        self.assertEqual(list(self.live.iterdir()), [])

    def test_existing_entries_are_never_overwritten(self):
        self.live.mkdir(parents=True)
        (self.live/'rofi.desktop').write_text('[Desktop Entry]\nName=My Rofi\n')
        with self.assertRaisesRegex(RuntimeError, 'rofi.desktop'):
            e.activate(self.live, self.manifest, self.files)
        self.assertEqual(sorted(p.name for p in self.live.iterdir()), ['rofi.desktop'])
        self.assertEqual(e.rollback(self.live, self.manifest), ['rofi.desktop'])
        self.assertTrue((self.live/'rofi.desktop').exists())

    def test_changed_system_entry_requires_review(self):
        (self.system/'foot.desktop').write_text('[Desktop Entry]\nName=Foot\nExec=foot --new\n')
        with self.assertRaisesRegex(RuntimeError, 'changed since approval'):
            e.candidate(self.manifest, self.system)

    def test_real_system_entries_match_the_approval_pin(self):
        e.candidate(MANIFEST)


if __name__ == '__main__':
    unittest.main()
