# Quiet Workspace Strip — unapproved Mangobar Option A

This is a Mangobar-only visual candidate. The approved live CSS and JSONC remain unchanged. The existing Rhapsody theme, MangoWM bindings and gestures, Foot, Rofi, Limux Commands and T2 hardware are untouched.

The live Mangobar 0.2.2 configuration has nine persistent workspaces, `layout`, a window title, a centered clock, and tray/Wi-Fi/battery/volume on the right. This candidate keeps the nine tags and all status modules, removes only `layout` from the preview config, and limits the subdued window title to 240 pixels. Layout switching remains in MangoWM (`SUPER,n`); there is no bar layout control to preserve. All other config values and commands are copied from the live config into an ignored build artifact. The generator refuses unexpected left-module order rather than guessing at a changed machine.

Both candidates use the same token-driven porcelain background and typography. In the warm candidate, the active number is vermillion `#AD492F` on `#F8F8FA` (measured 5.25:1). Occupied numbers use secondary graphite, empty/inactive use quiet graphite, and urgency uses red text. The neutral comparison makes the active number graphite on a single subtle chrome surface. No inactive number gets a box or border. These colour mappings are **proposals**, not a change to the approved Rhapsody selection semantic or live bar.

The observed hover-width bug has a concrete cause in the installed C implementation: after loading CSS, Mangobar forces each workspace state's minimum width to the bar height plus margins. It builds the hover CSS separately and reapplies the CSS `#tags` minimum width on pointer entry. The old CSS specified `min-width: 26px`; the live bar height is 30px, so hover could overwrite the computed 32px width with 26px. The candidate omits `min-width` from tag CSS entirely. Mangobar's own 30px minimum remains for every state, giving each number a stable 32px slot with the one-pixel margins. Hover has no colour, padding, margin or width override, so it does not animate or move neighbours.

The design review follows [Jakub Krehel's interface](https://github.com/jakubkrehel/skills), [layout](https://raw.githubusercontent.com/jakubkrehel/skills/main/skills/better-layout/SKILL.md), [typography](https://raw.githubusercontent.com/jakubkrehel/skills/main/skills/better-typography/SKILL.md) and [colour](https://raw.githubusercontent.com/jakubkrehel/skills/main/skills/better-colors/SKILL.md) guidance: group by spacing rather than decoration, retain readable compact Inter, and measure the accent on its rendered surface. [Emil Kowalski's interaction review](https://emilkowal.ski/ui/train-your-judgement) informed the choice to keep hover geometrically still and avoid motion on this frequently used strip. No external skill was installed and no runtime dependency was added. Limux's canonical design language remains the governing identity.

Render both variants without touching the desktop:

```sh
cd ~/limux
python3 scripts/quiet-bar.py render
```

From Foot in the MangoWM session, capture and try each temporary native Mangobar preview:

```sh
cd ~/limux
python3 scripts/quiet-bar.py preview --variant vermillion
python3 scripts/quiet-bar.py preview --variant neutral
```

Each command checks screenshot access before starting a second bar, captures before/candidate/hover screenshots under ignored `build/quiet-workspace-strip/`, keeps the preview for 25 seconds and closes only its own process. The hover capture occurs 10 seconds after the initial candidate capture; place the pointer over a workspace number then. The second bar may appear under or overlap the live bar. Move the pointer across numbers 1–9 and switch workspaces while it is up. Inspect the screenshots at native scale for hierarchy, density, title truncation, status legibility, alignment, active/occupied/urgent distinction, and the relationship to the light desktop and graphite Foot. Check that the workspace hit areas and neighbours do not shift. Ctrl+C closes a preview early. The Codex sandbox cannot access Wayland, so no new real screenshot or interactive hover observation was possible here; no visual approval is claimed.

The parser and native style tests cover valid CSS, measured contrast, unchanged approved output, and invariant tag geometry through hover. They cannot replace the on-device screenshot review. Activation will need separate visual approval and a guarded apply/rollback mechanism; this candidate does not install one.
