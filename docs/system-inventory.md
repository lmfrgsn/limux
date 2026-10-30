# Limux system inventory and cleanup review

Read-only snapshot: 30 October 2026, updated after the user's Waybar and library cleanup. This document records observed files, package metadata and configured startup paths. It changes no live setting. The Codex sandbox cannot connect to the user's systemd buses or inspect the desktop's process namespace, so **configured/enabled** is distinguished from **confirmed running** below. The user confirms one managed custom Mangobar; its on-disk files match the approved candidate. No private snippet values or Firefox profile identifier are recorded.

## At a glance

| Question | Finding |
| --- | --- |
| Installed packages | 498 pacman packages: 51 explicitly installed, one foreign package (`apple-bcm-firmware`), and two current orphans (`libsigc++`, `upower`). The user removed `cairomm`, `glibmm` and `fmt`. The foreign package is hardware firmware and must remain. |
| Desktop shell | MangoWM 0.18.3, configured for the internal display at 1.5 scale. One `exec_once` path starts `limux-bar`; two more start Mako through a wrapper and initialize keyboard backlight. |
| Bar | The **activated** Quiet Workspace Strip CSS/config hashes match the approved candidate. `limux-bar` points to a versioned custom Mangobar 0.2.2; the previous user-installed binary and exact rollback bytes remain available. The user reports one managed process; the sandbox cannot independently inspect it. |
| Rhapsody | MangoWM, Mangobar, the Limux picker (launcher and Command menu), Foot, Thunar and Mako use approved Rhapsody outputs. Firefox follows the GTK theme. |
| Waybar status | The user removed Waybar and its unused dependency chain. Pacman, user config, packaged examples and active startup paths now have no Waybar installation; old migration references remain only in historical documentation/scripts and duplicate-start guards. |
| Functional gap | Limux Commands quicklinks invoke `xdg-open`; neither `xdg-open` nor `xdg-utils` is installed. Snippets and other picker actions have separate paths. Repair needs a separate decision. |

## Installed software

The 51 explicitly installed packages are grouped here; the other 447 packages are libraries and transitive dependencies. Package installation does not prove a daemon is running or an application is used.

| Area | Explicit packages and purpose | Current Limux use |
| --- | --- | --- |
| Base, boot, storage | `base`, `grub`, `efibootmgr`, `btrfs-progs`, `lvm2`, `sudo`, `linux-firmware`, `mesa` | Keep for boot, storage and graphics; do not infer redundancy from this inventory. |
| T2 Mac hardware | `linux-t2`, `linux-t2-headers`, `apple-bcm-firmware`, `apple-t2-audio-config`, `arch-mact2-mirrorlist`, `arch-mact2-rankmirrors`, `tiny-dfr`, `t2fanrd`, `alsa-utils`, `brightnessctl`, `lilv-tools`, `lsp-plugins-lv2`, `rtkit`, `playerctl` | Keep. Kernel, Wi-Fi firmware, Touch Bar, fan, DSP/audio, media keys and backlight paths are working hardware dependencies. `apple-bcm-firmware` is both foreign and unrequired in pacman metadata; that is **not** evidence it is unused. |
| Network, Bluetooth, audio | `networkmanager`, `bluez`, `bluez-tools`, `bluez-utils`, `pipewire-alsa`, `pipewire-pulse` | NetworkManager, Bluetooth stack and PipeWire audio integration. WirePlumber and PipeWire core are installed as dependencies. |
| Shell and applications | `mangowm`, `foot`, `rofi`, `thunar`, `mako`, `firefox`, `libnotify`, `inter-font`, `ttf-dejavu` | MangoWM shell; Foot terminal; Rofi launcher and Commands picker; Thunar files; Mako notifications; Firefox browser. Inter is used in the light UI; Foot currently uses DejaVu Sans Mono. |
| Wayland utilities | `grim`, `slurp`, `wl-clipboard`, `wlr-randr`, `wlsunset` | Screenshot and clipboard tools are used. `wlr-randr` is installed for display control, while the observed 1.5 scale is in MangoWM config. `wlsunset` is installed but has no observed autostart. Waybar has been removed. |
| Development and maintenance | `base-devel`, `git`, `meson`, `ninja`, `rust`, `tllist`, `nano`, `less`, `libxslt` | Build and maintenance tools. Meson/Ninja and `tllist` support rebuilding custom Mangobar. Git supports Limux recovery. Do not remove build tools while a patched bar is maintained. |

`pacman -Qdtq` now returns exactly `libsigc++` and `upower`. The user removed Waybar and its unused dependency chain, then `cairomm`, `glibmm` and `fmt`; `playerctl` is now explicitly installed because Limux's T2 media-key helper uses it. `jack` and `sndio` remain shared dependencies. No recursive package removal is proposed.

The system also has a standalone Codex executable under the user's `.codex` installation and several user-maintained scripts in `~/.local/bin`; pacman does not own those files. The two Mangobar binaries are locally built, not Arch package files.

### Orphan candidates

| Package | Evidence and Limux relationship | Assessment before approval |
| --- | --- | --- |
| `libsigc++` 2.12.2 | C++ callback library; was a dependency of the removed C++ wrappers. No pacman required/optional user, and neither Mangobar binary nor MangoWM, Foot, Rofi, Mako, Thunar, tiny-dfr or `wlsunset` links it. | **Likely safe removal candidate**; not yet reviewed for approval. |
| `upower` 1.91.5 | Power-information daemon/library; no pacman required/optional user or Limux config/script call. Mangobar gets battery readings from sysfs; the T2 helpers do not call UPower. It remains D-Bus-activatable, and this sandbox cannot inspect live D-Bus clients. | **Likely safe removal candidate**, conditional on a Foot-session check that no desired application relies on its power service. Reinstallable if a future application needs it. |

The earlier ELF and reference checks found no use of the removed libraries or UPower in the custom Mangobar binaries, MangoWM, tiny-dfr, Foot, Rofi, Mako, Thunar, `wlsunset`, user scripts or Limux configuration. This cannot prove that no on-demand application will use UPower over D-Bus. No package was removed by Limux tooling; the user performed the removals.

## Desktop applications, configuration and appearance

“Tracked” refers to the source of the appearance or activation logic in `~/limux`, **not** to the live files in `~/.config`, which are outside Git.

| Application and version | Active role / functional config | Live styling and source | Git / update / rollback |
| --- | --- | --- | --- |
| MangoWM 0.18.3 | Session compositor and bindings: `~/.config/mango/config.conf`; configured at 2880×1800, 1.5 scale. | Approved appearance values are in that same config, derived from `[mango]` in `themes/rhapsody.toml`. | Live config outside Git. `scripts/mango-appearance.py` owns a guarded appearance-only update and rollback; functional bindings and gestures stay manual. Offline check reports approved baseline. |
| Custom Mangobar 0.2.2 | `~/.config/mangobar/config.jsonc` holds modules, nine workspaces, clicks and status commands. Launcher is `~/.local/bin/limux-bar`. | `~/.config/mangobar/style.css` matches the Quiet Strip generated from candidate tokens; orange inset is implemented by the versioned patched binary. | Source patches, build script and tokens in Git; live files outside Git. `scripts/activate-quiet-bar.py` has a private exact-byte rollback snapshot. See detailed section below. |
| Rofi 2.0.0 | `~/.config/rofi/config.rasi` defines fuzzy drun search, icons, keys and selected theme. Command+Space launches it. | `~/.config/rofi/charcoal.rasi` has the approved light Rhapsody theme, despite its historical filename; live hash matches the recovery manifest. | Tokens and adapter in Git; `scripts/activate-rofi.py` supports guarded activation/rollback. Live theme/config outside Git. |
| Limux Commands | Native Python script `~/limux/scripts/limux-commands.py`; Command+K is bound in MangoWM. Reads live MangoWM/Foot shortcuts. | Shares the Limux picker theme with a small override. | Implementation in Git. Private snippets/quicklinks are in `~/.config/limux/commands.toml` (mode 600, outside Git); contents were not read. `scripts/activate-commands.py` rolls back only the binding. Quicklinks currently lack `xdg-open`. |
| Foot 1.28.0 | `~/.config/foot/foot.ini` retains clipboard bindings and includes a generated appearance file. | `~/.config/foot/rhapsody.ini` is the approved graphite Rhapsody palette with orange `#D46A43` cursor, Adwaita Mono 12.5 and 16px padding; its live hash matches the recovery manifest. | Tokens/adapter and guarded `scripts/activate-foot.py` are in Git. Rollback restores the exact previous DejaVu Sans Mono 16 file; `restore-original` removes the appearance include. Live files remain outside Git. |
| Mako 1.11.0 | `~/.config/mako/config` keeps anchor, timeouts and visible count; starts via `~/.local/bin/mango-notifications`, which locks against duplicates. | `~/.config/mako/rhapsody` is the approved Rhapsody appearance, included by the config. | Tokens, adapter and guarded `scripts/activate-mako.py` in Git; rollback restores the exact previous config from `themes/recovery/`. |
| Thunar 4.20.10 / GTK 3.24 | `~/.config/Thunar/accels.scm`, `uca.xml`, and xfconf `thunar.xml` carry functional shortcuts/actions and view state. | No user GTK theme file was found. GSettings reports Adwaita theme/icons and Adwaita Sans defaults, but this sandbox cannot confirm rendered GTK state. **Not Rhapsody.** | Live files outside Git; no Limux styling adapter/rollback yet. Preserve shortcuts and custom actions. |
| Firefox 159.0 | Browser profile outside Git; `ui.key.accelKey = 91` is present. Global Command+K takes precedence over Firefox's own Command+K. | Firefox's own theme/GTK integration, no Rhapsody adapter observed. | Package-managed application; profile is user data and was not imported. No Limux styling rollback. |
| `wlsunset` 0.4.0 | Wayland colour-temperature utility installed recently. No MangoWM or systemd startup/config entry found. A manually launched process cannot be ruled out from this sandbox. | Independent display effect, not a Rhapsody token output. | Package-managed; no Limux startup/rollback mechanism yet. Keep pending a separate night-light decision. |

Style changes belong in `themes/rhapsody.toml` and the component adapters for the token-driven components. Mako and GTK/Thunar need their own reviewed adapters before they can be described as Rhapsody. No single generic theme-apply command exists.

## Mangobar origin, rollback and old files

- **Selected binary:** `~/.local/libexec/limux/mangobar-0.2.2-quiet/mangobar`. The existing `limux-bar` launcher points to it. Its hash matches the reproducible binary in ignored `build/quiet-workspace-strip/mangobar-build/`; the live CSS/JSONC hashes match `revised.css`/`revised.jsonc`.
- **Build source:** `scripts/quiet-mangobar-build.py` archives pinned upstream commit `84f25a7`, applies separate Git-tracked T2 metrics and Quiet Strip patches, and builds with Meson/Ninja. The retained upstream checkout is under `~/.local/state/limux/bar-migration/sources/mangobar`; its working tree also has the pre-existing T2 metrics modification. Preserve that checkout or obtain and verify the same upstream commit before future builds.
- **Previous binary:** `~/.local/bin/mangobar` remains a user-installed, T2-aware 0.2.2 build. It is **not** the selected launcher target now. Keep it: the current rollback script expects its exact hash and returns to it.
- **Previous yellow style:** the exact prior CSS, config and launcher bytes live in private `~/.local/state/limux/quiet-bar-activation/`. Keep this directory and the previous binary until an intentional rollback or a redesigned recovery mechanism replaces them. The older `themes/recovery/mangobar-before-rhapsody.css` is a Git-tracked historical baseline from before the first Rhapsody bar; it is a different recovery point.
- **Generated artifacts:** `~/limux/build/quiet-workspace-strip/` is ignored and rebuildable. Its old A/B/C previews, copied source and Meson build are not active or rollback dependencies. Keep reviewed screenshots while useful, then remove selected artifacts by approval. The versioned installed binary and private rollback state are **not** build artifacts.
- **Startup:** exactly one MangoWM bar startup declaration was found: `exec_once=~/.local/bin/limux-bar start` (stored as an absolute path). No Waybar startup entry or user Waybar config was found. The launcher verifies against duplicates; the user confirms one managed bar. This sandbox cannot independently confirm the process count.
- **Legacy migration tools:** `~/.local/bin/install-limux-mangobar` builds into the old `~/.local/bin/mangobar` path and can alter the rollback binary; do not rerun it while Quiet Strip is active. The old `cleanup-limux-waybar` script has been removed. The current version-pinned patch build and the package-only plan below are safer ownership paths.

Waybar and its unused dependency chain have been removed by the user. `pacman -Q waybar` fails; no `~/.config/waybar`, `/etc/xdg/waybar`, old `restart-waybar` launcher, user autostart or MangoWM Waybar entry exists. The existing `activate-mangobar.py` and `activate-quiet-bar.py` mention Waybar only to reject duplicate startup paths; retain those guards. `~/.local/share/limux/docs/mangobar.md` still describes the completed migration. An old private `~/.local/state/limux/waybar-recovery.tar.gz` contains historical Waybar/MangoWM migration files; it is not referenced by the active bar or Quiet Strip rollback, but is the sole observed copy of that historical configuration.

There is one live Mangobar JSONC, one live CSS and one MangoWM bar startup entry. The Git-tracked Quiet Strip builder and patches are the current source for the custom binary. The old local installer and local guide still describe the previous source/build ownership; they are **documentation/tooling overlap**, not a second active bar configuration. No active startup file contains a Waybar command.

## Startup and hardware

| Configured start | Source | Purpose / treatment |
| --- | --- | --- |
| MangoWM session | `/usr/share/wayland-sessions/mango.desktop` | Starts MangoWM. Its sole live config supplies the 1.5 display scale, shortcuts and gestures. |
| `limux-bar start` | One `exec_once` in MangoWM | Starts the selected patched Mangobar through the existing managed launcher. Keep exactly one. |
| `mango-notifications` | One `exec_once` in MangoWM | Starts Mako with a session lock; keep until Mako design work. |
| `t2-hardware-control keyboard-init` | One `exec_once` in MangoWM | Initializes keyboard backlight; preserve. |
| NetworkManager, Bluetooth, `t2fanrd` | Enabled system-unit links | Network, Bluetooth and fan control; preserve. |
| `tiny-dfr` and `limux-touchbar-recover` | Enabled system-unit links | Touch Bar daemon and boot-time recovery; preserve both. They have distinct roles. |
| PipeWire, PipeWire Pulse, WirePlumber, T2 speaker mute | Enabled user-unit links | Audio graph, Pulse compatibility, session policy and safe DSP speaker initialization; preserve. |

The unit links and files prove enabled/configured state, not current running state. System/user-bus inspection was denied by the sandbox. The user confirms one managed Mangobar and completed Waybar removal; the sandbox cannot independently inspect Mako or `wlsunset` processes. T2 backlight permission and audio files were inspected only by path and ownership; they were not modified.

To close the process-level gap, run these read-only checks from Foot in the desktop session before cleanup:

```sh
~/.local/bin/limux-bar status
pgrep -a -x mangobar || true
pgrep -a -x waybar || true
pgrep -a -x mako || true
pgrep -a -x wlsunset || true
systemctl --user --no-pager --plain status pipewire wireplumber t2-speaker-mute
systemctl --no-pager --plain status tiny-dfr limux-touchbar-recover t2fanrd NetworkManager
```

## Cleanup classification and proposed order

| Class | Item | Reason, dependency and proposed action |
| --- | --- | --- |
| **Keep** | Patched and previous Mangobar binaries; private Quiet Strip rollback state; pinned source/patches; `limux-bar`; live CSS/config | Required for active bar, reproducible upgrades and exact rollback. Do not clear the private state as ordinary cache. |
| **Keep** | T2 packages, services and `~/.local/bin` hardware helpers; `playerctl`, audio and backlight dependencies | Functional hardware paths. Pacman orphan/reverse-dependency status does not override this. |
| **Keep** | Private Commands config, Foot/Rofi live files and Git recovery manifests | Active behaviour, personal data and rollback. Never copy private snippets into Git. |
| **Consolidate** | Old local migration instructions (`~/.local/share/limux/docs/mangobar.md`) | Repository docs are reconciled. Retire or update the local guide separately. Do not create a second live config or startup path. |
| **Completed by user** | Waybar and unused dependency chain | Package, user/package configuration and old launcher are absent. One managed Mangobar is user-confirmed. No further Waybar package action is needed. |
| **Completed by user** | `cairomm`, `glibmm`, `fmt` | Removed. |
| **Remove candidate** | `libsigc++` | Remaining orphan with no observed client. Proposed package-only command after approval: `sudo pacman -R libsigc++`. No `-Rs`/`-Rns`. |
| **Investigate before removal** | `upower` | No configured Limux caller, but an application can request its D-Bus service dynamically. Check `systemctl --no-pager status upower.service` from Foot and confirm no desired power-status function uses it. If clear and separately approved, proposed command: `sudo pacman -R upower`. |
| **Completed** | `~/.config/Thunar/accels.scm.before-command-keys` | No longer present. |
| **Completed** | `~/.local/bin/cleanup-limux-waybar` | No longer present. Its reference in the old local guide remains to be corrected. |
| **Remove candidate** | Old Quiet Strip Meson build and copied source under ignored `build/quiet-workspace-strip/` | Rebuildable from the retained pinned checkout and Git patches; no runtime or exact rollback dependency. The installed versioned binary and private rollback state are separate. Keep reviewed PNGs. Proposed command after approval and zero preview processes: `rm -rf -- ~/limux/build/quiet-workspace-strip/mangobar-build ~/limux/build/quiet-workspace-strip/mangobar-source`. |
| **Investigate** | Old Waybar recovery archive and historical `~/.local/share/limux/docs/mangobar.md` | The archive is small and the sole observed copy of old Waybar/MangoWM migration files. It is not used by current rollback, but deleting unique historical recovery evidence is a separate decision. The local guide still describes Waybar cleanup as pending and should be retired or updated after the current plan is approved. |
| **Investigate** | `install-limux-mangobar`, old capacity/volume patch copy, one-shot desktop/Rofi setup scripts | Not in startup. The old installer can modify the previous binary that exact rollback expects; keep it and its patch until a replacement reconstruction path is documented. The one-shot setup scripts are unreferenced but can reinstall/reload components; review their recovery value before deleting. |
| **Keep** | `~/.config/foot/foot.ini.before-command-clipboard-20261028` | It is the only complete copy of the pre-Command clipboard configuration; the Foot manifest records only its original font line and hash, not a full config backup. Retain for functional-key recovery. |
| **Investigate** | `wlsunset` startup, GTK/Thunar theme, Firefox appearance, absent XDG portal | Night-light behaviour may be manual. GTK and Firefox styling are independent. Portal packages are absent; determine actual screen-sharing/file-picker needs before proposing installs. |
| **Repair separately** | Limux Commands quicklinks | `xdg-open` is absent, while the picker calls it. Confirm desired URL/folder opening behaviour; install `xdg-utils` or change the picker to a verified existing handler in a separate functional change. Do not change it during cleanup. |

Recommended order: (1) inspect UPower from Foot; (2) decide on `libsigc++` separately from UPower; (3) approve the two reproducible preview build directories for deletion; (4) correct the stale local Waybar guide; (5) decide whether to retain the unique Waybar recovery archive and old installer; (6) resolve the quicklink handler and night-light ownership; (7) return to Rhapsody Mako, then GTK/Thunar. No package or file cleanup command in this update has been run.
