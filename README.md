# Limux

Limux is a personal, cohesive desktop environment built on Arch Linux and MangoWM. Rhapsody is its first theme. See [vision](docs/vision.md) and [architecture](docs/architecture.md).

The theme foundation requires Python 3.11 or later. Validate with `python scripts/theme.py validate themes/rhapsody.toml`. Generate a preview with `python scripts/theme.py render themes/rhapsody.toml --output /tmp/limux-theme-preview`. Generation does not apply a theme to the desktop.

Mangobar CSS is generated alongside the token preview; see [architecture](docs/architecture.md) for a temporary visual preview. Run checks with `python -m unittest discover -s tests -v`.

The initial Rhapsody Mangobar baseline is approved. From Foot, run `python3 scripts/activate-mangobar.py activate`; use `rollback` to restore the version-controlled pre-Rhapsody style. The tool refuses inaccessible sessions or unexpected process/configuration ownership. See [activation and recovery](docs/architecture.md#approved-mangobar-activation-and-recovery).

Rofi is preview-only: `python3 scripts/preview-rofi.py` opens the generated light launcher with the existing functional configuration. Escape closes it; permanent styling remains unchanged.
