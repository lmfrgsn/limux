# Architecture

The [canonical design language](design-language.md), [original visual reference](references/braun-interface-concept.png) and [decision log](design-decisions.md) govern appearance. Mangobar candidate 2 is approved as the initial baseline; Rofi remains an unapproved preview. Approval status is recorded in the decision log. This architecture describes ownership and mechanics; it does not override established visual semantics.

Each theme has one canonical semantic token file, such as themes/rhapsody.toml. A theme generator translates tokens into application-native formats. Generated appearance is separate from human-maintained functionality wherever supported; applying a theme must not change shortcuts or hardware. A future `limux theme apply rhapsody` is a design possibility, not an available command.

Targets include MangoWM borders, Mangobar, Rofi, Foot, Mako and GTK/Thunar. Each target needs a reviewed adapter, native-format validation, backup and rollback before live application. The generator emits Mangobar CSS, Rofi Rasi and a JSON token preview. A guarded Mangobar-only activation mechanism is available below; no generic live theme application command exists.

## Machine audit and ownership

| Component | Current location | Ownership and status |
|---|---|---|
| MangoWM | ~/.config/mango/config.conf | Manually maintained functionality and appearance mixed; includes T2 controls, input and display settings. Do not import wholesale or replace. |
| Mangobar | ~/.config/mangobar/config.jsonc, style.css | Functional config remains manually maintained. The approved generated CSS can replace only the live style through the guarded activation mechanism; the user has activated it successfully, and its live CSS matches the approved baseline. |
| Rofi | ~/.config/rofi/config.rasi, charcoal.rasi | Existing launcher and previously approved live dark styling; manually maintained, not imported. Preserve it operationally; the reconciled Rhapsody target is light Rofi. |
| Foot | ~/.config/foot/foot.ini | Manually maintained font and clipboard shortcuts; not imported. |
| Mako | ~/.config/mako/config | Manually maintained notifications; not imported. |
| Thunar | ~/.config/Thunar/accels.scm, uca.xml | Manually maintained shortcuts and custom actions; not imported. |
| T2 | WirePlumber, PipeWire, systemd and helper scripts | Hardware-specific, outside this repository; preserve and audit separately before any import. |

Only the pre-Rhapsody Mangobar CSS has been imported as a historical recovery artifact; no functional configuration is imported. The user subsequently completed Mangobar activation in the desktop session. Audit and separate sensitive and machine-specific values before importing. No credentials, personal data or private keys belong in Git. Prefer Git history and documented rollback over accumulating backups; identify dependencies and verify a replacement before removing anything. Preserve shared dependencies. A future application process must stage, validate, back up and atomically replace only owned files; rollback must be tested. No remote is configured.

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


## Rofi candidate 2 — preview only

`python3 scripts/theme.py render themes/rhapsody.toml --output build/rhapsody` now also generates `rofi.rasi`. The adapter uses shared palette and semantics, with component dimensions in `[rofi]`. It emits visual theme properties only; existing `~/.config/rofi/config.rasi` retains fuzzy matching, application names, icons, input bindings and launch behaviour. The current dark theme stays active. Foot and other applications are untouched.

Run `python3 scripts/preview-rofi.py` from Foot to validate the theme with the installed Rofi parser, capture before/after screenshots and open a temporary launcher with a command-line theme override. Escape closes it; ordinary app selection launches the chosen app. The preview ends after 45 seconds and terminates only its own process. It refuses an already-open Rofi. Artifacts live under ignored `build/rofi-candidate2/`. No live file or shortcut is rewritten, so closing the preview is the rollback.

Native Rasi supports opposing border widths and nested boxes: the darker search floor gets metal top/left edges and porcelain bottom/right edges, giving a shallow recessed treatment. Selection has a narrow yellow edge and neutral row fill rather than a large decorative yellow panel. Exact depth, font scale and selection affordance still need on-device visual review. Rofi's functional configuration dump was compared with and without the candidate: only the theme override differed. Native parser tests pass; desktop screenshot capture is unavailable in this execution environment.

Candidate 2 emits one property per line: the installed Rofi 2.0.0 lexer consumes adjacent quoted values on the same line as one string. Validation now checks exact resolved header/placeholder/font values and expansion properties. The header, search wrapper and inputbar are explicitly non-expanding; only the entry expands horizontally. The list can shrink to the available/filtered results (up to seven visible rows). Width is 620px, section spacing 10px, search padding 10px, row padding 8px and row gap 2px. Branding has been removed; “APPLICATIONS” identifies the current launcher purpose. These are preview decisions, not permanent activation.
