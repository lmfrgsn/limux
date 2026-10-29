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

class PreviewFlowTest(unittest.TestCase):
    def test_order_and_section_rows(self):
        groups = commands.registry()
        self.assertEqual(groups[0][0], 'Everyday')
        self.assertEqual(groups[1][0], 'Snippets')
        self.assertTrue(any(row[1] == '⌘Space' for row in groups[0][1]))
        labels, actions = commands.display_rows(groups)
        self.assertIn('nonselectable', labels[0])
        self.assertIsNone(actions[0])
        self.assertEqual(labels[1].split('\0')[0], 'Open application launcher — ⌘Space')
        self.assertIn('meta\x1fEveryday', labels[1])

    def test_cancel_has_no_action(self):
        with patch.dict(commands.os.environ, {'WAYLAND_DISPLAY': 'wayland-1'}), \
             patch.object(commands.subprocess, 'run', return_value=MagicMock(returncode=1)), \
             patch.object(commands, 'execute') as execute:
            with patch.object(commands.sys, 'argv', ['limux-commands', 'preview']):
                commands.main()
            execute.assert_not_called()

class RefinementTest(unittest.TestCase):
    def test_required_search_terms_are_present(self):
        groups = commands.registry()
        labels, actions = commands.display_rows(groups)
        joined = '\n'.join(labels).lower()
        for term in ('workspace', 'screenshot', 'lorem', 'email'):
            self.assertIn(term, joined)
        self.assertTrue('nonselectable\x1ftrue\x1factive\x1ftrue' in labels[0])
        self.assertIsNone(actions[0])
        self.assertIn('⌘space', joined)

    def test_private_snippet_setup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'limux' / 'commands.toml'
            with patch.object(commands, 'SNIPPETS', path), \
                 patch.object(commands.sys, 'argv', ['limux-commands', 'init-snippets']):
                commands.main()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertIn(';email', path.read_text())
            with patch.object(commands, 'SNIPPETS', path), \
                 patch.object(commands.sys, 'argv', ['limux-commands', 'init-snippets']):
                with self.assertRaises(FileExistsError):
                    commands.main()

class FullShortcutLabelsTest(unittest.TestCase):
    def test_complete_live_shortcuts_in_plain_rows(self):
        labels, _ = commands.display_rows(commands.registry())
        visible = [label.split('\0', 1)[0] for label in labels]
        expected = (
            'Open application launcher — ⌘Space',
            'Capture area screenshot — ⌘⇧4',
            'Move window to workspace left — ⌃⌘←',
        )
        for label in expected:
            self.assertIn(label, visible)
        for label in visible:
            self.assertNotIn('\t', label)
            self.assertNotIn('<span', label)
            self.assertNotIn('…', label)
            self.assertNotIn('...', label)

    def test_preview_sends_plain_rows_without_markup(self):
        with patch.dict(commands.os.environ, {'WAYLAND_DISPLAY': 'wayland-1'}), \
             patch.object(commands.subprocess, 'run', return_value=MagicMock(returncode=1)) as run, \
             patch.object(commands.sys, 'argv', ['limux-commands', 'preview']):
            commands.main()
        args = run.call_args.args[0]
        self.assertNotIn('-markup-rows', args)
        self.assertIn('width: 700px;', args[args.index('-theme-str') + 1])
        self.assertIn('Open application launcher — ⌘Space', run.call_args.kwargs['input'])

class HeadingTypographyTest(unittest.TestCase):
    def test_only_section_rows_receive_heading_state(self):
        labels, actions = commands.display_rows(commands.registry())
        for label, action in zip(labels, actions):
            if 'nonselectable\x1ftrue' in label:
                self.assertIn('active\x1ftrue', label)
                self.assertIsNone(action)
            else:
                self.assertNotIn('active\x1ftrue', label)
        self.assertIn('Open application launcher — ⌘Space', labels[1])

    def test_heading_theme_uses_current_rhapsody_tokens(self):
        theme = commands.preview_theme()
        self.assertIn('font: "Inter 11";', theme)
        self.assertIn('text-color: #666573;', theme)
        self.assertIn('margin: 8px 0px 0px 0px;', theme)
        self.assertIn('padding: 2px 8px 1px 8px;', theme)
        self.assertNotIn('element selected', theme)
        self.assertNotIn('box-search', theme)
