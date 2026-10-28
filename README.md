# Limux

Limux is a personal, cohesive desktop environment built on Arch Linux and MangoWM. Rhapsody is its first theme. See [vision](docs/vision.md) and [architecture](docs/architecture.md).

The theme foundation requires Python 3.11 or later. Validate with `python scripts/theme.py validate themes/rhapsody.toml`. Generate a preview with `python scripts/theme.py render themes/rhapsody.toml --output /tmp/limux-theme-preview`. Generation does not apply a theme to the desktop.

Mangobar CSS is generated alongside the token preview; see [architecture](docs/architecture.md) for a temporary visual preview. Run checks with `python -m unittest discover -s tests -v`.

The initial Rhapsody Mangobar baseline is approved. From Foot, run `python3 scripts/activate-mangobar.py activate`; use `rollback` to restore the version-controlled pre-Rhapsody style. The tool refuses inaccessible sessions or unexpected process/configuration ownership. See [activation and recovery](docs/architecture.md#approved-mangobar-activation-and-recovery).

Rofi at `e1f7538` is approved. From Foot, run `python3 scripts/activate-rofi.py activate`; normal Command+Space then uses Rhapsody. Use `python3 scripts/activate-rofi.py rollback` for the previous theme, or `check` for read-only validation. See [Rofi activation and rollback](docs/architecture.md#rofi-activation-and-rollback) for on-device search, navigation, Escape and application-launch checks. `scripts/preview-rofi.py` remains available for future reversible reviews.

MangoWM appearance is an unapproved candidate. Run `python3 scripts/mango-appearance.py check`, then `python3 scripts/mango-appearance.py preview` from Foot for a 30-second reversible preview. Use `rollback` for explicit recovery. Permanent activation stays locked until visual approval; see [MangoWM preview and recovery](docs/architecture.md#mangowm-appearance-candidate-and-reversible-preview).
