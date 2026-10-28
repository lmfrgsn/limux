# Architecture

Each theme has one canonical semantic token file, such as themes/rhapsody.toml. A theme generator translates tokens into application-native formats. Generated appearance is separate from human-maintained functionality wherever supported; applying a theme must not change shortcuts or hardware. A future `limux theme apply rhapsody` is a design possibility, not an available command.

Targets include MangoWM borders, Mangobar, Rofi, Foot, Mako and GTK/Thunar. Each target needs a reviewed adapter, native-format validation, backup and rollback before live application. Current foundation validates and generates a neutral JSON token preview only; no application adapter or live apply exists.

## Machine audit and ownership

| Component | Current location | Ownership and status |
|---|---|---|
| MangoWM | ~/.config/mango/config.conf | Manually maintained functionality and appearance mixed; includes T2 controls, input and display settings. Do not import wholesale or replace. |
| Mangobar | ~/.config/mangobar/config.jsonc, style.css | Functional config and style already separate; manually maintained, not imported. |
| Rofi | ~/.config/rofi/config.rasi, charcoal.rasi | Existing launcher and approved dark styling; manually maintained, not imported. |
| Foot | ~/.config/foot/foot.ini | Manually maintained font and clipboard shortcuts; not imported. |
| Mako | ~/.config/mako/config | Manually maintained notifications; not imported. |
| Thunar | ~/.config/Thunar/accels.scm, uca.xml | Manually maintained shortcuts and custom actions; not imported. |
| T2 | WirePlumber, PipeWire, systemd and helper scripts | Hardware-specific, outside this repository; preserve and audit separately before any import. |

No working live configuration is imported or generated yet. Audit and separate sensitive and machine-specific values before importing. No credentials, personal data or private keys belong in Git. Prefer Git history and documented rollback over accumulating backups; identify dependencies and verify a replacement before removing anything. Preserve shared dependencies. A future application process must stage, validate, back up and atomically replace only owned files; rollback must be tested. No remote is configured.
