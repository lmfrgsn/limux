# Architecture

The [canonical design language](design-language.md), [original visual reference](references/braun-interface-concept.png) and [decision log](design-decisions.md) govern appearance. Mangobar candidate 2, Rofi at `e1f7538`, and MangoWM appearance at `fd645da` are approved initial baselines. Approval status is recorded in the decision log. This architecture describes ownership and mechanics; it does not override established visual semantics.

Each theme has one canonical semantic token file, such as themes/rhapsody.toml. A theme generator translates tokens into application-native formats. Generated appearance is separate from human-maintained functionality wherever supported; applying a theme must not change shortcuts or hardware. A future `limux theme apply rhapsody` is a design possibility, not an available command.

Targets include MangoWM borders, Mangobar, Rofi, Foot, Mako and GTK/Thunar. Each target needs a reviewed adapter, native-format validation, backup and rollback before live application. The generator emits Mangobar CSS, Rofi Rasi, a MangoWM appearance fragment and a JSON token preview. Guarded component-specific activation mechanisms are available below; no generic live theme application command exists.

## Machine audit and ownership

| Component | Current location | Ownership and status |
|---|---|---|
| MangoWM | ~/.config/mango/config.conf | Sole complete live config; functionality stays manually maintained. The candidate adapter can replace only 16 reviewed appearance values, preserving all other bytes. Do not import wholesale or replace from a generated full config. |
| Mangobar | ~/.config/mangobar/config.jsonc, style.css | Functional config remains manually maintained. The approved generated CSS can replace only the live style through the guarded activation mechanism; the user has activated it successfully, and its live CSS matches the approved baseline. |
| Rofi | ~/.config/rofi/config.rasi, charcoal.rasi | Functional config stays manually maintained. Approved generated Rhapsody styling can replace only charcoal.rasi through the guarded activation tool; historical theme and icon are versioned for rollback. |
| Foot | ~/.config/foot/foot.ini | Manually maintained font and clipboard shortcuts; not imported. |
| Mako | ~/.config/mako/config | Manually maintained notifications; not imported. |
| Thunar | ~/.config/Thunar/accels.scm, uca.xml | Manually maintained shortcuts and custom actions; not imported. |
| T2 | WirePlumber, PipeWire, systemd and helper scripts | Hardware-specific, outside this repository; preserve and audit separately before any import. |

Pre-Rhapsody Mangobar CSS and the Rofi theme/search icon have been imported as historical recovery artifacts; no functional configuration is imported. The user subsequently completed Mangobar activation in the desktop session. Audit and separate sensitive and machine-specific values before importing. No credentials, personal data or private keys belong in Git. Prefer Git history and documented rollback over accumulating backups; identify dependencies and verify a replacement before removing anything. Preserve shared dependencies. A future application process must stage, validate, back up and atomically replace only owned files; rollback must be tested. No remote is configured.

## Mangobar preview adapter

Mangobar 0.2.2 reads generated CSS independently from its JSON behaviour config. The adapter maps semantic colour references and component geometry from the canonical tokens. Candidate 2 uses signal yellow for active workspaces and signal red for urgent workspaces; neutral accent is restored but not used as selection. It validates text contrast before writing output. Green is reserved until a module exposes a reliable positive state.

Inspection of the locally retained native `style.c` and `mangobar.c` confirms horizontal padding/margins, minimum width, corner radius and menu border colour. Workspace border width, shadows and vertical control inset are unavailable. Global typography applies throughout. Hover overlays inherited base/global styles, so global and base-tag rules deliberately omit colours; a radius-only hover preserves selected/urgent colours. This is covered by an optional compiled native-parser test. Inter is installed and remains the preview choice; final typography is unresolved.

Workspace actions, tags, layout and title formats, clock, Wi-Fi helper, battery device, corrected battery computation, PipeWire controls, tray, height, scaling and startup remain in the existing live configuration and scripts. The adapter never edits them. Generated files under build/ are disposable and ignored by Git.

Run `python scripts/theme.py render themes/rhapsody.toml --output build/rhapsody` and inspect `build/rhapsody/mangobar.css`. For a temporary visual preview from a Foot window on the desktop, run `timeout 15s ~/.local/bin/mangobar -c ~/.config/mangobar/config.jsonc -s "$HOME/limux/build/rhapsody/mangobar.css"`. This starts a second bar for 15 seconds; it may overlap the existing bar and the existing tray watcher can prevent its tray from appearing. It does not replace or stop the running bar. Exit early with Ctrl+C. Close the preview and confirm the original bar remains. Visual verification and any future apply/rollback remain separate steps.


For candidate 2, run `python3 scripts/preview-mangobar.py` from Foot in the active desktop session. It renders into `build/rhapsody-candidate2/`, captures `before.png`, launches a temporary second bar, captures `candidate.png`, then closes only that process after 20 seconds (or Ctrl+C). Capture failure exits before launching. The second bar can affect window area or tray ownership; this is not permanent activation. Earlier images in `build/rhapsody/` are historical, not candidate-2 evidence.

`python3 scripts/proof-mangobar.py` generates an offline schematic `build/rhapsody-candidate2/proof.svg` with fictional labels; it is not a native screenshot. For native parser integration tests, set `MANGOBAR_SOURCE` to a local Mangobar source checkout and run `python3 -m unittest discover -s tests -v`. The test compiles the source parser in a temporary directory; no code is downloaded or installed.

## Approved Mangobar activation and recovery

The user has approved candidate 2 as the initial baseline. `python3 scripts/activate-mangobar.py activate` performs session, startup, process ownership, launcher identity and known-style preflight checks, then atomically replaces only `~/.config/mangobar/style.css` and refreshes through the existing `~/.local/bin/limux-bar`. It requires an existing single managed bar, verifies exactly one afterward and leaves the existing single `exec_once` entry untouched. It refuses unknown styles or modified launchers rather than overwriting them.

Run from Foot in the desktop session:

```sh
cd ~/limux
python3 scripts/activate-mangobar.py check
python3 scripts/activate-mangobar.py activate
# Restore the pre-Rhapsody styling if needed:
python3 scripts/activate-mangobar.py rollback
```

The [recovery CSS](../themes/recovery/mangobar-before-rhapsody.css) is a historical version-controlled snapshot, guarded by the [manifest](../themes/recovery/mangobar.json). The manifest also pins the approved generated CSS: later token/adapter changes cannot silently become an authorized activation. Update that pin only after a new visual approval. Functional config and hardware are never copied into the repository or rewritten by this mechanism. No additional startup entry or service is installed. Failure during restart/verification restores the prior CSS and attempts a managed restart. Abrupt power loss/SIGKILL cannot run Python recovery, but atomic replacement prevents a partial CSS file; explicit rollback remains available from a healthy managed session. If the bar itself is absent, use the existing `~/.local/bin/limux-bar start` first, inspect its status/log, then retry rollback.


## Rofi approved baseline — adapter and preview

`python3 scripts/theme.py render themes/rhapsody.toml --output build/rhapsody` now also generates `rofi.rasi`. The adapter uses shared palette and semantics, with component dimensions in `[rofi]`. It emits visual theme properties only; existing `~/.config/rofi/config.rasi` retains fuzzy matching, application names, icons, input bindings and launch behaviour. The current dark theme stays active until the activation command below succeeds. Foot and other applications are untouched.

Run `python3 scripts/preview-rofi.py` from Foot to validate the theme with the installed Rofi parser, capture before/after screenshots and open a temporary launcher with a command-line theme override. Escape closes it; ordinary app selection launches the chosen app. The preview ends after 45 seconds and terminates only its own process. It refuses an already-open Rofi. Artifacts live under ignored `build/rofi-candidate2/`. No live file or shortcut is rewritten, so closing the preview is the rollback.

Native Rasi supports opposing border widths and nested boxes: the darker search floor gets metal top/left edges and porcelain bottom/right edges, giving a shallow recessed treatment. Selection has a narrow yellow edge and neutral row fill rather than a large decorative yellow panel. Exact depth, font scale and selection affordance still need on-device visual review. Rofi's functional configuration dump was compared with and without the candidate: only the theme override differed. Native parser tests pass; desktop screenshot capture is unavailable in this execution environment.

Candidate 2 emits one property per line: the installed Rofi 2.0.0 lexer consumes adjacent quoted values on the same line as one string. Validation now checks exact resolved header/placeholder/font values and expansion properties. The header, search wrapper and inputbar are explicitly non-expanding; only the entry expands horizontally. The list can shrink to the available/filtered results (up to seven visible rows). Width is 620px, section spacing 10px, search padding 10px, row padding 8px and row gap 2px. Branding has been removed; “APPLICATIONS” identifies the current launcher purpose. These values are now approved as the initial baseline, with activation authorized separately below.


## Rofi activation and rollback

The user approved commit `e1f7538` and authorized its permanent activation. No design values change in this workflow. From Foot in the desktop session:

```sh
cd ~/limux
python3 scripts/activate-rofi.py check
python3 scripts/activate-rofi.py activate
# Return to the previous working dark launcher:
python3 scripts/activate-rofi.py rollback
```

The tool reuses the token-driven adapter and pins its exact generated output in [rofi.json](../themes/recovery/rofi.json). It stages and parses the chosen theme, checks default config resolution and the existing Command+Space binding, compares complete functional configuration dumps, and requires a reachable Wayland session with no Rofi open before writing. Only `~/.config/rofi/charcoal.rasi` is replaced, atomically. Its historical filename is retained so `config.rasi` and all normal `rofi -show drun` shortcuts remain byte-identical. No wrapper, second active configuration, autostart entry or permanent backup is introduced. Temporary staging files are automatically removed; the operation lock lives in the runtime directory.

After replacement the tool validates the normal launcher with no theme override, verifies the selected theme and all protected hashes, and restores the immediately previous bytes if validation fails. Repeated activation/rollback is idempotent. A process/power failure cannot leave a partially written theme because replacement is atomic; explicit rollback remains available. Rofi reads the new theme on its next normal invocation, so no background service restart is needed.

The [original theme](../themes/recovery/rofi-before-rhapsody.rasi) and [original search icon](../themes/recovery/rofi-search.svg) are version-controlled historical recovery evidence, not additional live configs. The existing live icon is retained and checked for rollback integrity. The tool refuses unknown/modified live themes, functional configs or icons rather than overwriting them. Rollback does not depend on future adapter/token output matching the approved baseline.

Desktop functional validation after activation:

1. Press Command+Space. Confirm the approved Rhapsody launcher opens normally.
2. Type an installed application's name and confirm filtering; clear the search and use Up/Down (or Control+p/n) to move selection.
3. Press Escape and confirm dismissal without launching anything.
4. Reopen with Command+Space, search for a harmless application such as Thunar, select it and press Enter. Confirm it opens and Rofi closes.
5. If any check fails, close Rofi and run `rollback`, then repeat the checks with the prior theme.

The Codex environment cannot reach the live compositor, so interactive input/application-launch checks are pending on-device. Native parser/default-config checks and isolated activation/rollback tests pass; these do not claim to simulate keyboard input or application launching.

## MangoWM approved appearance and reversible preview

The `[mango]` section in [Rhapsody tokens](../themes/rhapsody.toml) drives `scripts/mango.py`. The generator writes an appearance-only `mango.conf` fragment under the chosen build directory; it is not a standalone configuration and is not sourced by the live file. `~/.config/mango/config.conf` remains the sole active complete configuration. Only 16 allowlisted values can be replaced; no functional settings are emitted by the adapter. Blur, shadows, radius-disabling behaviour, opacity, hardware and all functional lines remain intact.

From Foot in the running MangoWM session:

```sh
cd ~/limux
python3 scripts/mango-appearance.py check
python3 scripts/mango-appearance.py preview --seconds 30
# Explicit recovery if a preview was interrupted:
python3 scripts/mango-appearance.py rollback
```

`check` validates both the original and merged full configuration with the installed parser, using temporary files removed immediately afterward. `preview` requires MangoWM 0.18.3, one existing compositor using the expected config, working IPC, and screenshot capture. It changes only owned values in the existing file, reloads that compositor, captures before/after images under `build/mango-candidate1/`, and restores after the timeout or Ctrl+C. It does not launch another compositor, bar or autostart entry. Native config reload reapplies the existing configuration; its unchanged `exec_once` entries are retained. Check window layout, focus, scaling and application controls during the preview as well as appearance.

An independent timed restorer is armed before any live replacement and exits after its bounded recovery window (preview duration plus 8 seconds). A single operation lock, pending visual-value journal and overwritten watchdog log live under `${XDG_STATE_HOME:-~/.local/state}/limux/mango-appearance/`. The pending journal is deleted after successful restoration; there are no accumulated full-config backups. After power loss or unavailable IPC, run `rollback` from Foot. Recovery restores disk values before attempting reload and keeps a failed operation journal for retry. Concurrent edits to nonvisual settings survive recovery; concurrent edits to owned visual values require review rather than being silently overwritten.

The [versioned recovery manifest](../themes/recovery/mango.json) records original values and the approved `fd645da` candidate hash. The user has approved that exact initial baseline; future adapter/token changes cannot silently inherit its approval. Activation uses native validation, atomic replacement, journalling and rollback in the existing single config. The transaction rejects any change outside the 16 owned values. Rollback is independent of future token changes. No general `limux theme apply` command is introduced.

Activate and validate from Foot:

```sh
cd ~/limux
python3 scripts/mango-appearance.py activate
python3 scripts/mango-appearance.py verify
# Restore the pre-Rhapsody appearance if necessary:
python3 scripts/mango-appearance.py rollback
```

`check` validates the configuration offline and reports whether its appearance is the approved baseline or the previous version. `verify` additionally requires the exact approved live values and one reachable compositor using that config; it does not claim pixel-level verification. Activation confirms exact post-reload config bytes and compositor IPC responsiveness before clearing the recovery journal. After success the timed restorer sees no pending operation and cannot undo the committed activation. Inspect the desktop to confirm the 2px borders, 8px inner / 12px outer gaps, 6px corners and approved colours. Shortcuts, layouts, gestures, animation and hardware settings are outside ownership and remain unchanged.
