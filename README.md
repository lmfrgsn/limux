# Limux

Limux is a personal desktop environment for Arch Linux, built on the
[MangoWM](https://github.com/mangowm/mango) Wayland compositor. It is not a
distribution or a dotfiles dump: it is one designed system, with its own
interaction model and a first theme, **Rhapsody**.

The design draws on Braun's industrial design (the ET 66 calculator by Dietrich
Lubs and Dieter Rams) and on the light, cohesive feel of classic Macintosh and
NeXTSTEP: porcelain and cool-grey system surfaces, graphite developer tools,
precise type, and colour used only where it means something. The one warm accent,
workspace orange, marks where you are: the active workspace, the selected row, the
text cursor.

> **Built for one machine.** Limux runs on a 2018 MacBook Pro (MacBookPro15,1, T2
> chip). It is published to read and borrow from, not to install. See
> [Using it elsewhere](#using-it-elsewhere).

## What it includes

| Area | Limux |
| --- | --- |
| Bar | Mangobar with a quiet workspace strip (one inset orange mark), Wi-Fi, battery and volume as line icons, and live status for Claude Code and Codex sessions; click an agent to jump to its terminal |
| Launcher and Command menu | One Rofi picker: Command+Space for apps, Command+K for every shortcut, snippets, quicklinks, utilities and power actions, each runnable from the list |
| Terminal | Foot in graphite with Adwaita Mono and an orange block cursor |
| Files | Thunar restyled as one porcelain surface, with outline icons and Mac-style Command shortcuts |
| Notifications | Mako cards; a level card for the volume, brightness and keyboard-light keys; a low-battery warning |
| Session | hyprlock lock screen and hypridle, a branded polkit password prompt, desktop portals for screen sharing and file choosers |
| Utilities | Clipboard history in the picker, imv for images, btop as Activity Monitor, night light that follows sunset |
| System | An nftables firewall, LLMNR off, and Update system: `pacman -Syu` followed by a check of every Limux component |
| Hardware | T2 speaker DSP, Touch Bar, display and keyboard backlight, tracked under `machine/` |

## How it is built

- **One token file per theme.** `themes/rhapsody.toml` names every colour by its
  purpose (active workspace, list selection, terminal cursor) rather than by hue.
- **Adapters generate each app's native styling** from those tokens: Rofi themes,
  Foot and Mako fragments, a GTK 3 stylesheet and icon set, the bar's CSS, and so on
  (`scripts/*.py`). Appearance stays separate from behaviour: a theme never changes a
  shortcut or a hardware setting.
- **Guarded activation.** Each component has its own controller
  (`scripts/activate-*.py`) with `activate`, `verify` and `rollback`. Approved output
  is pinned by hash, unknown edits are refused rather than overwritten, and failures
  restore the previous state.
- **Design first.** Every visual change starts from the
  [design language](docs/design-language.md), is previewed in isolation on the real
  desktop, and is approved before activation. The
  [decision log](docs/design-decisions.md) records each choice and why.
- **The machine is tracked.** `machine/` mirrors the hand-maintained configuration
  and helpers at their real paths; `scripts/machine.py status` reports drift.

## Repository

| Path | Contents |
| --- | --- |
| `themes/` | Rhapsody tokens and the recovery pins for every activation |
| `scripts/` | Adapters, activation controllers, the Command menu and the update check |
| `patches/mangobar/` | Mangobar changes (GPL-3.0, see that folder) |
| `machine/` | Tracked copy of this machine's configuration, T2 helpers and package list |
| `docs/` | [Vision](docs/vision.md), [architecture](docs/architecture.md), [design language](docs/design-language.md), [decision log](docs/design-decisions.md), [machine files](docs/machine.md), [system inventory](docs/system-inventory.md) |
| `tests/` | `python3 -m unittest discover -s tests` |

## Using it elsewhere

Most of Limux is portable in principle, but it is not packaged for other machines:

- The T2 audio, Touch Bar and backlight parts only fit this MacBook model.
- Activations check exact hashes of what they expect to find, including a locally
  built bar and the system's desktop entries, so on another system they refuse to run
  until those pins are reviewed.
- `machine/` holds this machine's own configuration.

The quickest things to borrow are the token-and-adapter approach and individual
adapters, such as `scripts/rofi.py`, `scripts/foot.py`, `scripts/mako.py` or
`scripts/btop.py`, each a short file that turns `themes/rhapsody.toml` into one
app's configuration.

## Credits

- [MangoWM](https://github.com/mangowm/mango) and
  [Mangobar](https://github.com/mangowm/mangobar)
- T2 speaker DSP adapted from
  [lemmyg/t2-apple-audio-dsp](https://github.com/lemmyg/t2-apple-audio-dsp) (MIT),
  with the [t2linux](https://t2linux.org) project's kernel and firmware work
- [Tabler Icons](https://tabler.io/icons) (MIT) in the bar
- Ideas for the level card, battery warning, firewall and checked update came from
  reviewing [Omarchy](https://omarchy.org)

## License

MIT, see [LICENSE](LICENSE), except `patches/mangobar/`, which is GPL-3.0 like
Mangobar itself.
