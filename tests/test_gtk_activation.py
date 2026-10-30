import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('activate_gtk', ROOT/'scripts/activate-gtk.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class FakeLive:
    """In-memory GSettings and xfconf with real files under a temporary home."""

    def __init__(self, folder):
        self.css = folder/'config/gtk-3.0/gtk.css'
        self.icons = folder/'data/icons'
        self.defaults = {'font-name': 'Adwaita Sans 11', 'gtk-theme': 'Adwaita', 'icon-theme': 'Adwaita'}
        self.settings = dict(self.defaults)
        self.props = {}
        self.fail_on = None

    def get_setting(self, key):
        return self.settings[key]

    def set_setting(self, key, value):
        if key == self.fail_on:
            raise RuntimeError('simulated GSettings failure')
        self.settings[key] = value

    def reset_setting(self, key):
        self.settings[key] = self.defaults[key]

    def get_prop(self, name):
        return self.props.get(name)

    def set_prop(self, name, kind, value):
        self.props[name] = value

    def reset_prop(self, name):
        self.props.pop(name, None)


class GtkActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.live = FakeLive(Path(self.tmp.name))
        self.manifest = json.loads((ROOT/'themes/recovery/gtk.json').read_text())
        self.candidate = a.candidate(self.manifest)

    def tearDown(self):
        self.tmp.cleanup()

    def assert_original(self):
        self.assertEqual(set(a.classify(self.live, self.manifest).values()), {'original'})
        self.assertFalse(self.live.css.exists())
        self.assertFalse((self.live.icons/self.manifest['icon_theme']).exists())
        self.assertEqual(self.live.props, {})

    def test_activate_is_complete_idempotent_and_rollback_is_exact(self):
        self.assert_original()
        a.activate(self.live, self.manifest, *self.candidate)
        self.assertEqual(set(a.classify(self.live, self.manifest).values()), {'active'})
        self.assertEqual(self.live.settings, self.manifest['gsettings'])
        self.assertEqual(a.activate(self.live, self.manifest, *self.candidate), [])
        self.assertEqual(a.rollback(self.live, self.manifest), [])
        self.assert_original()
        self.assertEqual(a.rollback(self.live, self.manifest), [])
        self.assertEqual(list(self.live.icons.iterdir()), [])

    def test_failed_theme_switch_restores_everything(self):
        self.live.fail_on = 'gtk-theme'
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            a.activate(self.live, self.manifest, *self.candidate)
        self.assert_original()

    def test_unknown_existing_values_are_never_overwritten(self):
        self.live.css.parent.mkdir(parents=True)
        self.live.css.write_text('/* hand-written */\n')
        with self.assertRaisesRegex(RuntimeError, 'css'):
            a.activate(self.live, self.manifest, *self.candidate)
        self.assertEqual(self.live.css.read_text(), '/* hand-written */\n')
        self.live.css.unlink()
        self.live.settings['gtk-theme'] = 'Materia'
        with self.assertRaisesRegex(RuntimeError, 'gsettings:gtk-theme'):
            a.activate(self.live, self.manifest, *self.candidate)
        self.assertFalse(self.live.css.exists())

    def test_rollback_keeps_settings_changed_after_activation(self):
        a.activate(self.live, self.manifest, *self.candidate)
        self.live.props['last-location-bar'] = 'ThunarLocationEntry'
        kept = a.rollback(self.live, self.manifest)
        self.assertEqual(kept, ['xfconf:last-location-bar'])
        self.assertEqual(self.live.props, {'last-location-bar': 'ThunarLocationEntry'})
        self.assertFalse(self.live.css.exists())
        self.assertEqual(self.live.settings, self.live.defaults)

    def test_rollback_does_not_depend_on_current_tokens(self):
        a.activate(self.live, self.manifest, *self.candidate)
        original = a.candidate
        a.candidate = lambda manifest: (_ for _ in ()).throw(RuntimeError('tokens drifted'))
        try:
            a.rollback(self.live, self.manifest)
        finally:
            a.candidate = original
        self.assert_original()


    def install_previous_icons(self):
        files = {'index.theme': b'[Icon Theme]\nName=old\n', '16/places/folder.svg': b'<svg/>'}
        manifest = dict(self.manifest, icons_previous_sha256=[a.tree_digest(files, {})])
        a.install_icons(self.live, manifest, files, {})
        return manifest

    def test_previous_icon_set_is_upgraded_in_place(self):
        manifest = self.install_previous_icons()
        self.assertEqual(a.classify(self.live, manifest)['icons'], 'previous')
        a.activate(self.live, manifest, *self.candidate)
        self.assertEqual(set(a.classify(self.live, manifest).values()), {'active'})
        self.assertEqual([p.name for p in self.live.icons.iterdir()], [manifest['icon_theme']])

    def test_failed_activation_restores_the_previous_icon_set(self):
        manifest = self.install_previous_icons()
        self.live.fail_on = 'gtk-theme'
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            a.activate(self.live, manifest, *self.candidate)
        self.assertEqual(a.classify(self.live, manifest)['icons'], 'previous')
        self.assertEqual([p.name for p in self.live.icons.iterdir()], [manifest['icon_theme']])

    def test_rollback_also_removes_a_previous_icon_set(self):
        manifest = self.install_previous_icons()
        a.rollback(self.live, manifest)
        self.assertFalse((self.live.icons/manifest['icon_theme']).exists())

    def install_previous_css(self):
        old = b'/* earlier approved stylesheet */\n'
        a.write_css(self.live, old)
        return dict(self.manifest, css_previous_sha256=[a.digest(old)]), old

    def test_previous_stylesheet_is_upgraded_in_place(self):
        manifest, _ = self.install_previous_css()
        self.assertEqual(a.classify(self.live, manifest)['css'], 'previous')
        a.activate(self.live, manifest, *self.candidate)
        self.assertEqual(set(a.classify(self.live, manifest).values()), {'active'})
        self.assertEqual(sorted(p.name for p in self.live.css.parent.iterdir()), ['gtk.css'])

    def test_failed_activation_restores_the_previous_stylesheet(self):
        manifest, old = self.install_previous_css()
        self.live.fail_on = 'gtk-theme'
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            a.activate(self.live, manifest, *self.candidate)
        self.assertEqual(self.live.css.read_bytes(), old)

    def test_rollback_also_removes_a_previous_stylesheet(self):
        manifest, _ = self.install_previous_css()
        a.rollback(self.live, manifest)
        self.assertFalse(self.live.css.exists())

if __name__ == '__main__':
    unittest.main()
