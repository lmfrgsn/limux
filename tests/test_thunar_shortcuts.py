import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('thunar_shortcuts', ROOT/'scripts/thunar-shortcuts.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
MANIFEST = json.loads((ROOT/'themes/recovery/thunar-shortcuts.json').read_text())
DEFAULTS = (ROOT/'themes/recovery'/MANIFEST['recovery_file']).read_text()
# MangoWM owns these Command keys globally; Thunar must never be given them.
MANGO_SUPER = {'r', 'm', 'Tab', 'g', 'i', 'o', 'n', 'Left', 'Right', 'space', 'k', 'e'}

PARSER = r'''
#include <gtk/gtk.h>
int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++) {
        guint key = 0; GdkModifierType mods = 0;
        gtk_accelerator_parse(argv[i], &key, &mods);
        if (key == 0 || !(mods & GDK_SUPER_MASK)) { g_print("bad %s\n", argv[i]); return 1; }
    }
    return 0;
}
'''


class ThunarShortcutTests(unittest.TestCase):
    def test_defaults_are_pinned_and_unset(self):
        self.assertEqual(t.digest(DEFAULTS.encode()), MANIFEST['original_sha256'])
        self.assertEqual(t.state(DEFAULTS), 'original')

    def test_render_sets_exactly_the_limux_shortcuts(self):
        active = t.render(DEFAULTS)
        self.assertEqual(t.parse(active), t.SHORTCUTS)
        self.assertEqual(t.state(active), 'active')
        # Every other action keeps Thunar's commented default line.
        self.assertEqual(len(active.splitlines()), len(DEFAULTS.splitlines()))

    def test_no_shortcut_collides_with_mangowm(self):
        for accel in t.SHORTCUTS.values():
            if accel.count('<') == 1:
                self.assertNotIn(accel.split('>')[-1], MANGO_SUPER, accel)
        self.assertEqual(len(set(t.SHORTCUTS.values())), len(t.SHORTCUTS))

    def test_state_is_semantic_so_thunar_rewrites_still_classify(self):
        reordered = '\n'.join(reversed(t.render(DEFAULTS).splitlines())) + '\n'
        self.assertEqual(t.state(reordered), 'active')
        self.assertEqual(t.state(DEFAULTS + '(gtk_accel_path "<Actions>/ThunarWindow/reload" "<Super>y")\n'), 'unknown')

    def test_thunar_modifier_order_still_counts_as_active(self):
        saved = t.render(DEFAULTS).replace('"<Super><Shift>z"', '"<Shift><Super>z"')
        self.assertIn('"<Shift><Super>z"', saved)
        self.assertEqual(t.state(saved), 'active')
        self.assertEqual(t.state(saved.replace('"<Shift><Super>z"', '"<Shift><Super>y"')), 'unknown')
        self.assertEqual(t.state(saved.replace('"<Shift><Super>z"', '"<Super>z"')), 'unknown')

    def test_activate_and_rollback_in_isolated_config(self):
        with tempfile.TemporaryDirectory() as folder:
            live = Path(folder)/'Thunar/accels.scm'
            live.parent.mkdir()
            live.write_text(DEFAULTS)
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}), patch.object(t, 'thunar_running', return_value=False):
                for action in ('activate', 'activate', 'verify', 'rollback', 'rollback'):
                    with patch('sys.argv', ['thunar-shortcuts.py', action]):
                        t.main()
                    if action == 'activate':
                        self.assertEqual(t.state(live.read_text()), 'active')
                self.assertEqual(live.read_text(), DEFAULTS)
                with patch.object(t, 'thunar_running', return_value=True), patch('sys.argv', ['x', 'activate']):
                    with self.assertRaisesRegex(RuntimeError, 'Close every Thunar window'):
                        t.main()

    @unittest.skipUnless(shutil.which('cc') and shutil.which('pkg-config'), 'no C compiler')
    def test_gtk_parses_every_shortcut_as_a_command_key(self):
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'gtk+-3.0'], capture_output=True, text=True)
        if flags.returncode != 0:
            self.skipTest('GTK 3 headers unavailable')
        with tempfile.TemporaryDirectory() as folder:
            source, binary = Path(folder)/'parse.c', Path(folder)/'parse'
            source.write_text(PARSER)
            subprocess.run(['cc', str(source), '-o', str(binary), *flags.stdout.split()], check=True)
            result = subprocess.run([str(binary), *t.SHORTCUTS.values()], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
