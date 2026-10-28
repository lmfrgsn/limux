# Architecture

The [canonical design language](design-language.md), [original visual reference](references/braun-interface-concept.png) and [decision log](design-decisions.md) govern appearance. Current tokens and the Mangobar preview are implementation experiments, not proof of final design approval. This architecture describes ownership and mechanics; it does not override established visual semantics.

Each theme has one canonical semantic token file, such as themes/rhapsody.toml. A theme generator translates tokens into application-native formats. Generated appearance is separate from human-maintained functionality wherever supported; applying a theme must not change shortcuts or hardware. A future `limux theme apply rhapsody` is a design possibility, not an available command.

Targets include MangoWM borders, Mangobar, Rofi, Foot, Mako and GTK/Thunar. Each target needs a reviewed adapter, native-format validation, backup and rollback before live application. The Mangobar adapter generates CSS and a JSON token preview. No live apply exists.

## Machine audit and ownership

| Component | Current location | Ownership and status |
|---|---|---|
| MangoWM | ~/.config/mango/config.conf | Manually maintained functionality and appearance mixed; includes T2 controls, input and display settings. Do not import wholesale or replace. |
| Mangobar | ~/.config/mangobar/config.jsonc, style.css | Functional config and live style remain manually maintained; a theme-driven CSS preview is generated separately. |
| Rofi | ~/.config/rofi/config.rasi, charcoal.rasi | Existing launcher and previously approved live dark styling; manually maintained, not imported. Preserve it operationally; the reconciled Rhapsody target is light Rofi. |
| Foot | ~/.config/foot/foot.ini | Manually maintained font and clipboard shortcuts; not imported. |
| Mako | ~/.config/mako/config | Manually maintained notifications; not imported. |
| Thunar | ~/.config/Thunar/accels.scm, uca.xml | Manually maintained shortcuts and custom actions; not imported. |
| T2 | WirePlumber, PipeWire, systemd and helper scripts | Hardware-specific, outside this repository; preserve and audit separately before any import. |

No working live configuration is imported or applied yet. Audit and separate sensitive and machine-specific values before importing. No credentials, personal data or private keys belong in Git. Prefer Git history and documented rollback over accumulating backups; identify dependencies and verify a replacement before removing anything. Preserve shared dependencies. A future application process must stage, validate, back up and atomically replace only owned files; rollback must be tested. No remote is configured.

## Mangobar preview adapter

Mangobar 0.2.2 reads the generated CSS independently from its JSON behaviour config. Theme tokens drive font family and size, foregrounds, surfaces, accent, menu border colour, menu radius and spacing. The adapter currently chooses readable active text from theme colours and uses the general accent for active workspaces. This conflicts with established signal-yellow selection; see the [audit](design-decisions.md). No correction is applied by the documentation reconciliation. Bar border-width is unsupported by Mangobar's parser, so adjacent surface colours provide separation; menu border colour is supported. Current preview tokens request Inter for sans and IBM Plex Mono for mono; final typography remains open. Check installed fonts and actual fallback before future previews. The earlier IBM Plex Sans fallback observation is historical.

Workspace actions, tags, layout and title formats, clock, Wi-Fi helper, battery device, corrected battery computation, PipeWire controls, tray, height, scaling and startup remain in the existing live configuration and scripts. The adapter never edits them. Generated files under build/ are disposable and ignored by Git.

Run `python scripts/theme.py render themes/rhapsody.toml --output build/rhapsody` and inspect `build/rhapsody/mangobar.css`. For a temporary visual preview from a Foot window on the desktop, run `timeout 15s ~/.local/bin/mangobar -c ~/.config/mangobar/config.jsonc -s "$HOME/limux/build/rhapsody/mangobar.css"`. This starts a second bar for 15 seconds; it may overlap the existing bar and the existing tray watcher can prevent its tray from appearing. It does not replace or stop the running bar. Exit early with Ctrl+C. Close the preview and confirm the original bar remains. Visual verification and any future apply/rollback remain separate steps.
