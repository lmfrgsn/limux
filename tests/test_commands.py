import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location('commands', Path(__file__).resolve().parents[1] / 'scripts/limux-commands.py')
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)

class CommandsTest(unittest.TestCase):
    def test_actual_bindings_and_gestures(self):
        rows = commands.shortcuts()
        self.assertIn(('Apps', '⌘Space', 'Open application launcher', None), rows)
        self.assertTrue(any(r[1] == '4-finger swipe up' for r in rows))
        self.assertFalse(any(r[1] == '⌘K' for r in rows))
        self.assertTrue(any(r[1] == '⌃1' and 'workspace 1' in r[2] for r in rows))

    def test_snippets_private_and_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'commands.toml'
            path.write_text('[snippets]\n";email" = "person@example.invalid"\n')
            path.chmod(0o600)
            self.assertEqual(commands.snippets(path)[0][3], ('copy', 'person@example.invalid'))
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                commands.snippets(path)
        with patch.object(commands.subprocess, 'run') as run:
            commands.execute(('copy', 'sample'))
            run.assert_called_once_with(['wl-copy', '--', 'sample'], check=True)

    def test_no_unverified_bindings(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'mango.conf'
            path.write_text('bind=SUPER,k,spawn,unknown-app\nbind=SUPER,space,spawn,rofi -show drun\n# bind=SUPER,x,quit\n')
            self.assertEqual(commands.shortcuts(path), [('Apps', '⌘Space', 'Open application launcher', None)])

if __name__ == '__main__':
    unittest.main()
