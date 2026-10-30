# Limux

Limux is a personal, cohesive desktop environment built on Arch Linux and MangoWM. Rhapsody is its first theme. See [vision](docs/vision.md) and [architecture](docs/architecture.md).

The current approved desktop uses the Quiet Workspace Strip with one inset orange active workspace and white active number, the Limux picker for the launcher (Command+Space) and Command menu (Command+K), Rhapsody MangoWM appearance, the graphite Foot palette with an orange block cursor, Limux Files in Thunar and Rhapsody notifications. See the [current status table](docs/architecture.md#current-implementation-and-approval-status--2026-10-30) and [design language](docs/design-language.md). Older yellow Mangobar and preview instructions below are retained for recovery and historical context.

The theme foundation requires Python 3.11 or later. Validate with `python scripts/theme.py validate themes/rhapsody.toml`. Generate a preview with `python scripts/theme.py render themes/rhapsody.toml --output /tmp/limux-theme-preview`. Generation does not apply a theme to the desktop.

Mangobar CSS is generated alongside the token preview; see [architecture](docs/architecture.md) for a temporary visual preview. Run checks with `python -m unittest discover -s tests -v`.

The active Mangobar is the Quiet Workspace Strip, managed by `scripts/activate-quiet-bar.py` (`restore-prior` undoes the latest refinement; `rollback` restores the pre-Strip bar). `scripts/activate-mangobar.py` belongs to the superseded yellow boxed baseline and refuses the current launcher. See [activation and recovery](docs/architecture.md#approved-mangobar-activation-and-recovery).

The Limux picker is approved. From Foot, run `python3 scripts/activate-rofi.py activate` and `python3 scripts/launcher-entries.py activate`; `rollback` returns to the previous launcher and app list. See [the Limux picker](docs/architecture.md#limux-picker--launcher-and-command-menu). `scripts/preview-rofi.py` remains available for future reversible reviews.

MangoWM appearance at `fd645da` is approved. From Foot, run `python3 scripts/mango-appearance.py activate`, then `python3 scripts/mango-appearance.py verify`. Use `rollback` to restore the previous appearance or `preview` for a timed review. See [MangoWM activation and recovery](docs/architecture.md#mangowm-approved-appearance-and-reversible-preview).

Limux Files restyles Thunar from the `[thunar]` tokens: one porcelain surface, the path as text, outline icons and graphite selection. Install `adw-gtk-theme`, then run `python3 scripts/activate-gtk.py activate` from Foot; `rollback` restores the defaults. See [Limux Files activation and recovery](docs/architecture.md#limux-files-thunar--activation-and-recovery).

Notifications use the Rhapsody Mako design from the `[mako]` tokens. From Foot, `python3 scripts/activate-mako.py activate` applies it and `rollback` restores the previous config. See [Mako activation and recovery](docs/architecture.md#mako-notifications--activation-and-recovery).
