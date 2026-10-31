from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location('commands', Path(__file__).resolve().parents[1] / 'scripts/limux-commands.py')
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


@contextmanager
def isolated_picker():
    """Run the picker against a temporary lock path, never the live desktop's."""
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        with patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-1'}), patch.object(commands, 'HOME', folder):
            yield folder


def visible(label):
    """What Rofi shows for a markup row: tags removed, metadata dropped."""
    return re.sub(r'<[^>]+>', '', label.split('\0', 1)[0])

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
        self.assertEqual(visible(labels[1]), 'Open application launcher\t⌘Space')
        self.assertIn('meta\x1fEveryday', labels[1])

    def test_cancel_has_no_action(self):
        with isolated_picker(), \
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
    def test_action_then_quiet_key_column(self):
        labels, actions = commands.display_rows(commands.registry())
        shown = [visible(label) for label in labels]
        for row in ('Open application launcher\t⌘Space', 'Capture area screenshot\t⌘⇧4',
                    'Move window to workspace left\t⌃⌘←', ';email\tCopy', 'Home folder\tOpen'):
            self.assertIn(row, shown)
        for label, action, text in zip(labels, actions, shown):
            if 'nonselectable\x1ftrue' in label:
                continue
            self.assertEqual(text.count('\t'), 1, text)
            self.assertNotIn(' — ', text)
            self.assertIn('<span fgalpha="75%">', label)

    def test_user_text_is_escaped_for_markup(self):
        rows = [('Snippets', 'R&D <draft>', 'Copy snippet', ('copy', 'x'))]
        labels, _ = commands.display_rows([('Snippets', rows)])
        self.assertIn('R&amp;D &lt;draft&gt;\t', labels[1])

    def test_preview_opens_markup_rows_on_the_first_command(self):
        with isolated_picker(), \
             patch.object(commands.subprocess, 'run', return_value=MagicMock(returncode=1)) as run, \
             patch.object(commands.sys, 'argv', ['limux-commands', 'preview']):
            commands.main()
        args = run.call_args.args[0]
        self.assertIn('-markup-rows', args)
        self.assertEqual(args[args.index('-selected-row') + 1], '1')
        self.assertIn('Search commands', args[args.index('-theme-str') + 1])
        self.assertIn('Open application launcher\t', run.call_args.kwargs['input'])

class HeadingTypographyTest(unittest.TestCase):
    def test_only_section_rows_receive_heading_state(self):
        labels, actions = commands.display_rows(commands.registry())
        for label, action in zip(labels, actions):
            if 'nonselectable\x1ftrue' in label:
                self.assertIn('active\x1ftrue', label)
                self.assertIsNone(action)
            else:
                self.assertNotIn('active\x1ftrue', label)

    def test_override_is_small_and_uses_tokens(self):
        theme = commands.preview_theme()
        self.assertIn('font: "Inter 8";', theme)
        self.assertIn('text-color: #686773;', theme)
        self.assertIn('padding: 12px 12px 4px 12px;', theme)
        self.assertIn('cursor: default;', theme)
        self.assertNotIn('box-search', theme)
        self.assertNotIn('width', theme)


class PickerThemeTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('rofi'), 'Rofi is not installed')
    def test_native_parser_resolves_shared_picker_and_command_override(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
        from rofi import render
        theme = tomllib.loads((Path(__file__).resolve().parents[1] / 'themes/rhapsody.toml').read_text())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'picker.rasi'
            path.write_text(render(theme))
            result = subprocess.run(['rofi', '-theme', str(path), '-theme-str', commands.preview_theme(), '-dump-theme'],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        blocks = dict(re.findall(r'(?m)^([\w*. -]+) \{([^}]+)\}', result.stdout))
        self.assertIn('"box-search","listview","message"', blocks['mainbox'].replace(' ', ''))
        self.assertIn('212, 106, 67', blocks['element selected.normal'])
        self.assertNotIn('227, 190, 71', result.stdout)
        for state in ('element normal.active', 'element alternate.active', 'element selected.active'):
            self.assertIn('background-color: transparent', blocks[state])
            self.assertIn('cursor:           default', blocks[state])
        self.assertIn('font: "Inter 8"', blocks['element-text selected.active'])
        self.assertIn('430px', blocks['element-text'])

class PersonalQuicklinksTest(unittest.TestCase):
    def test_private_links_and_empty_groups(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'commands.toml'
            path.write_text('[snippets]\n";email"="person@example.invalid"\n[quicklinks]\n"Project"="/tmp"\n')
            path.chmod(0o600)
            self.assertEqual(commands.quicklinks(path)[0][3], ('open', '/tmp'))
            self.assertEqual(commands.snippets(path)[0][1], ';email')
            path.write_text('[quicklinks]\n"Bad"="javascript:alert(1)"\n')
            with self.assertRaises(ValueError):
                commands.quicklinks(path)
        groups = commands.registry()
        self.assertTrue(all(items for _, items in groups))


class SingleInstanceTest(unittest.TestCase):
    def test_second_picker_cannot_open_until_first_closes(self):
        import os

        with tempfile.TemporaryDirectory() as folder, patch.object(commands, 'HOME', Path(folder)):
            first = commands.picker_lock()
            self.assertIsNotNone(first)
            try:
                self.assertIsNone(commands.picker_lock())
            finally:
                os.close(first)
            second = commands.picker_lock()
            self.assertIsNotNone(second)
            os.close(second)
