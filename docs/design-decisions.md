# Design decisions and implementation audit

Recorded 2026-10-28; entries preserve the state at the time recorded. The [design language](design-language.md) is the sole maintained design specification; this log records status, rationale and discrepancies. Later dated approvals supersede earlier pending or proposed states. Evidence: [original source](references/original-design-reference.md), [original image](references/braun-interface-concept.png), [tokens](../themes/rhapsody.toml), [Mangobar adapter](../scripts/mangobar.py), and locally inspected generated `build/rhapsody/mangobar.css` (ignored, reproducible output).

**Reading this log:** dated entries preserve what was proposed or pending at that time. The [current reconciliation](#current-rhapsody-reconciliation--2026-10-30) supersedes earlier yellow-workspace and pending-activation statements; it does not erase their historical rationale. The [verified current state](#verified-current-state--2026-10-30) supersedes earlier Limux Commands approval statements. [Limux Files](#limux-files--thunar-design-approved-and-implemented--2026-10-30) records the approved Thunar design.

## Reconciliation decisions

| Status | Decision | Rationale |
| --- | --- | --- |
| Established | Limux owns the product and Braun ET 66 design philosophy; Rhapsody is its first theme | Restore the original identity hierarchy, already substantially present in vision |
| Established | Platinum, Apple Rhapsody and NeXTSTEP complement Braun | Preserve light system cohesion, transitional technical character and developer utility |
| Established | Porcelain, cool grey, metal and graphite; barely lavender neutrals; sparse yellow/green/red signals | The image and source contain a richer material hierarchy than the bar experiment |
| Established | Yellow active workspace, neutral inactive controls, recessed inputs and subtle physical controls | Concrete visual decisions must survive implementation constraints |
| Established | Light system UI with coordinated dark developer tools; shared tokens and separate functionality | Preserve design cohesion and working system behaviour |
| Historical baseline | Six original foundation values retained in the canonical specification | Initial Rhapsody palette and later Braun exploration are complementary; no silent replacements |
| Proposed / approval required | Final IBM Plex versus Inter typography; exact reconciled colours and foregrounds; sizes, spacing and radii | Neither the source's samples nor candidate 1 establishes final values |
| Proposed / review required | Component mappings and supported depth treatments; which additional statuses use signals | Must be checked against native capabilities and actual screenshots before approval |

This reconciliation supersedes the former candidate-1 design-language document as design authority. That experiment remains recoverable in Git (`005efb3`); it is not maintained as another specification. The imported source is archived with only a provenance notice and repaired relative image link. No styling or token changes are approved or made by this documentation commit.

## Existing implementation contradictions and proposed corrections

| Finding and evidence | Consequence | Proposed correction and decision boundary |
| --- | --- | --- |
| `colors.accent` is `#646178`; initial token commit `f46bc73` used `#77768F`. The adapter binds `#tags.active` to accent and emits pale text on violet; the old design document explicitly prescribed grey-violet selection | Replaces the original yellow active workspace and conflates general emphasis with selection | Preserve both historical and current values in the record; propose separate emphasis and yellow workspace-selection roles with tested foreground contrast. Yellow semantics are established; exact token values/schema and implementation need review/approval before changes |
| No yellow or green token; `urgent = #945035` is warm oxide | Missing functional signals; oxide has not been approved as the reconciled signal red | Propose distinct yellow, green and red semantic roles. Select exact values and status mappings explicitly; do not use screenshot samples as approved tokens |
| Canvas, surface, chrome, text and dark-terminal values still match the initial foundation; violet accent also colours menu borders | Neutral values are not inherently a contradiction, but prominent violet selection/borders risk making purple dominant | Retain the five unchanged baselines. Review actual surface relationships and restrained general emphasis before proposing any neutral changes; this audit does not establish that live surfaces look overly purple |
| Adapter uses chrome broadly, surface for hover/menu, canvas for menu hover; no metal/recessed role. `geometry.border = 1` is unused by the adapter. Controls are flat, with square tag corners | Partial light hierarchy exists, but the reference's differentiated depth and physical affordances are not expressed | Propose material/recessed/control roles and supported edge or surface approximations. Confirm native capabilities; do not add unsupported CSS. Exact geometry/treatments remain open |
| `#tags:hover` assigns a neutral surface without an explicit active-hover treatment | Potential loss of selected-state recognition on hover, depending on renderer precedence | Inspect native hover behaviour in a future authorized preview and retain an identifiable yellow active state; no runtime claim made here |
| Tokens request Inter 13, IBM Plex Mono, radius 3 and spacing 8; adapter hardcodes weight 500, tag minimum width 25 and some margins | Candidate choices can appear final despite unresolved typography and geometry; not all visual metrics come from shared tokens | Label these as experiments. Choose fonts after availability/rendering checks; review shared versus component-specific metrics before approving a token/adapter revision |
| Only Mangobar has an adapter; dark-terminal token does not generate Foot styling. Architecture records existing dark Rofi | Coordinated light/dark system is not implemented or visually verified; live dark Rofi differs from the future light-system target | Plan coordinated native adapters and reviews for light Rofi/Mako/GTK and dark Foot/Codex; retain current live settings pending separately authorized implementation |

## Audit scope and disposition

Read all required project documents, every archive member, the complete source specification and original image; inspected the current token definition, renderer, tests and existing generated CSS. Compared the generated CSS with a fresh in-memory render. This is a repository implementation audit, not a live desktop visual certification or a new application-capability investigation. The earlier documentation reports Mangobar 0.2.2 restrictions and a historical font fallback; current installed capabilities and font availability must be rechecked for future implementation.

Already sound: product/theme distinction, named influences, restrained functional design, cool neutrals and dark developer tools in vision, shared tokens, isolation of previews, behavioural/hardware ownership and recovery principles. Missing or narrowed: the preserved original image, full material hierarchy, explicit yellow/green/red semantics, concrete launcher/control examples, historical-influence detail and a durable distinction between established decisions and experiments.

Disposition: import evidence, reconcile documentation and project instructions, record discrepancies, commit locally. Leave all tokens, scripts, generated outputs and live configurations untouched. Final typography, exact semantic colours, geometry, component implementations and technical feasibility remain decisions for subsequent work.

## Candidate 2 — authorized implementation, pending visual approval

The next user request authorizes restoring the six foundation values and implementing a temporary Mangobar candidate. Proposed signals: yellow `#E3BE47` from the reference sample; olive green `#728858` from the reference sample; red `#AD4038` as a restrained but unmistakable error/urgent red. Green is reserved for verified positive states, not applied indiscriminately to custom Wi-Fi text. Proposed metal `#A8A8B4` supplies menu structure. These exact additions are candidate values, not final approvals. Neutral emphasis remains `#77768F`; semantic mappings separately identify workspace selection, success and urgency. Geometry and Inter remain experimental. No permanent activation is authorized.

Candidate 2 implementation and evaluation:

- Restored accent `#646178` → `#77768F`; preserved the other five foundations. Added metal `#A8A8B4`, yellow `#E3BE47`, green `#728858`, red `#AD4038`, and dark signal ink `#141810` for readable text on green. Replaced the former warm-oxide urgency mapping with semantic red. Quiet text changed `#72717E` → `#686773` to reach 4.61:1 on chrome; secondary text stays `#666573`.
- Explicit semantic references separate neutral emphasis, selection, success and urgency without duplicating hex values. No colour literals are hardcoded in the adapter. Green is not assigned to unconditionally rendered Wi-Fi text. Neutral emphasis remains available but does not tint menu borders or workspaces.
- Porcelain bar, chrome empty controls, slightly deeper canvas occupied controls and yellow selection make the hierarchy legible. Metadata and status text recede; clock stays primary. Candidate workspace padding is 7, gap 1, minimum width 26, radius 2; layout has a 6-unit group gap. Live height 30, buffer scale, module order/formats and every functional setting remain untouched. Inter 13/500 remains a candidate, not a final font decision.
- Text contrast: yellow/graphite 6.83:1; red/porcelain 5.55:1; green/dark signal ink 4.60:1; quiet/chrome 4.61:1; secondary/porcelain 5.39:1. Validation rejects semantic or used neutral text pairs below 4.5:1. Neutral accent is not a small-text background. Control-fill contrast remains limited: yellow/porcelain 1.69:1, metal/porcelain 2.22:1. This is not full accessibility certification: selection still relies on colour, and stronger non-colour selection affordances need native support or further design work. Do not darken the established yellow concept silently to conceal this limitation.
- Source inspection found that native hover overlays inherited global and tag-base colours. The adapter omits these colours and uses radius-only hover, preserving yellow/red. Native tests resolve and overlay real parser styles. Urgent takes precedence over active in native code; no compositor or module logic is changed.
- Eight automated tests passed, including compiled native-parser validation against locally retained Mangobar source. The preview script was attempted but `grim` reported `failed to create display`; it exited before starting a bar. This environment cannot connect to the desktop's Wayland socket. No new before/after screenshots or actual native visual certification are claimed.
- Inspected the generated offline schematic proof: yellow provides a distinctive focal point on a porcelain rail; neutral workspace keys and subdued layout/title/status restore the reference's hierarchy without purple highlights. Compared with the original, full-height keys remain flatter and more tightly packed, with less physical depth. The proof uses fictional content and approximate text positioning; actual font rasterization, tray, width pressure, hover visibility and MacBook scaling remain to be checked on-device.
- Native limits: no workspace outlines, shadows or per-control vertical insets; module backgrounds fill bar height. Small radii, neutral surface steps and menu border colour approximate structure, not true raised/recessed edges. No decorative gradients added. Other applications and permanent autostart are unchanged. Preview instructions are in [architecture](architecture.md).

## Initial Mangobar baseline approved; activation authorized

The user visually reviewed candidate 2 and approved it as the initial Rhapsody Mangobar baseline, not a final design. This supersedes the candidate's earlier pending-approval status for Mangobar only. Permanent activation of that baseline is now authorized; other components remain separately reviewed.

The current pre-Rhapsody live CSS is preserved exactly in `themes/recovery/mangobar-before-rhapsody.css`, with hashes for that file, approved generated CSS and the existing launcher in `themes/recovery/mangobar.json`. This historical recovery artifact is not a second active theme or a maintained design source. Activation reuses the existing launcher and single MangoWM startup entry, changes only the owned live CSS atomically, verifies one managed process and unchanged functional files, and restores the previous CSS/restarts if activation fails.

Activation was attempted in this session but failed its Wayland connectivity preflight before any live write or process change. Exactly one startup entry was found, but the live desktop process namespace is unavailable here. One running bar and desktop health cannot be certified from this environment. Transaction tests cover success, idempotence, restart failure and verification-failure rollback; they do not replace an on-device activation check.

## Rofi candidate 1 — original recessed-search direction

The user authorized a token-driven Rofi adapter and reversible preview, not permanent activation. The first candidate uses the same porcelain/cool-grey palette and yellow selection semantics as the approved Mangobar baseline. Shared colours are unchanged; Rofi dimensions live in a dedicated token section and remain candidates.

The launcher has a porcelain frame, restrained metal border, small “APPLICATIONS” and “RHAPSODY / 01” labels, a canvas-grey search recess with metal top/left edges and porcelain bottom/right edges, and compact application rows. A narrow yellow selection edge accompanies neutral row fill; urgent rows use the shared red. Green is not used decoratively. Search placeholder uses primary ink because secondary ink on canvas would not meet the text contrast target. Typography uses Inter at coordinated but component-specific sizes. Existing icons, fuzzy matching, keyboard/mouse actions and application launching remain intact. Foot is unchanged.

Validation: generated Rasi accepted by installed Rofi 2.0.0; configuration dumps differed only by the explicit preview theme path. Sixteen tests pass, including native Mangobar and Rofi parsers, unchanged Mangobar approval hash, semantic contrast, token rejection and activation rollback simulations. Rofi preview was attempted but failed the Wayland screenshot preflight without starting a process. No native screenshot or visual approval is claimed. Search depth, scaling, icon/text alignment and restrained selection should be evaluated in the desktop preview before approving this component. The historical screenshot's darker search floor and precise alignment remain the visual reference; this candidate is not a new independent aesthetic.

## Rofi candidate 2 — fix native parsing and vertical expansion

The user supplied a real screenshot confirming successful Mangobar activation and exposing Rofi candidate 1 defects. Live Mangobar CSS matches its approval hash; no Mangobar changes are part of this revision. Rofi remains preview-only; do not move to Foot or activate Rofi before the next screenshot review. Permanent “RHAPSODY / 01” branding is removed as explicitly requested; the functional “APPLICATIONS” label remains.

Root causes and evidence:

- Reproduced with installed Rofi 2.0.0: putting `content: "APPLICATIONS"; font: "Inter 10";` on one line returns success but resolves the entire quoted span as content and omits the font property. Separate lines produce independent, correct properties. The [2.0.0 lexer](https://github.com/davatorium/rofi/blob/2.0.0/lexer/theme-lexer.l#L179) uses a greedy string expression permitting intermediate quote characters on that line. All generated properties now occupy separate lines. Native tests assert exact resolved values, not just a successful parser exit.
- The custom header/search boxes lacked explicit expansion constraints. Rofi's [box allocator](https://github.com/davatorium/rofi/blob/2.0.0/source/widgets/box.c#L122) distributes remaining space among expanding children; [theme documentation](https://github.com/davatorium/rofi/blob/2.0.0/doc/rofi-theme.5.markdown) describes expansion and box packing. The screenshot's blank header region and grey search tail are consistent with these expanding wrappers. Removed the branding/header wrapper; explicitly made heading, search wrapper, inputbar and message non-expanding. The entry still expands along its horizontal inputbar, not vertically. List height is now content-sensitive, including when filtering; navigation, matching and activation actions are unchanged.

Proportions: width 660→620; section spacing 12→10; search padding 12→10; entry size 16→14; row padding 10→8; row gap 4→2; icon size 22→20. Result type remains Inter 12 and heading Inter 10. All colour values and semantic mappings are unchanged. The input retains a canvas-grey floor, metal top/left boundary and porcelain bottom/right edge; constraining the wrapper makes those edges enclose the input rather than an oversized grey panel. Results share the input width and use a quiet chrome selection fill with the existing narrow yellow edge.

Visual comparison: inspected the user's native screenshot and original reference in full. The original uses a compact structural label, bounded recessed field, tightly related result rows and one restrained functional highlight. Candidate 2 addresses those relationships by removing the excessive expanding regions and reducing the type/spacing jump. Actual revised rasterization and scaled geometry remain unverified here: direct Wayland capture failed, and an isolated headless MangoWM attempt failed because no DRM renderer is available. No synthetic rendering is represented as a native screenshot. Run the revised preview from Foot and inspect its `build/rofi-candidate2/candidate.png` before approval.

Validation: 17 tests passed, including exact native Rofi string/font and expansion checks, native Mangobar parsing, unchanged approved Mangobar output and contrast checks. Rofi configuration dumps differ only by the preview theme path. Hashes confirm live Mangobar CSS/config, MangoWM config, Rofi config/theme and Foot config remain byte-identical throughout this task. No permanent activation performed.

## Rofi initial baseline approved — e1f7538

The user visually reviewed and approved `e1f7538` as the initial Rofi design baseline, resolving its former preview-only status. Activation is authorized; this task introduces no redesign. A slightly deeper search recess, typography and selection geometry remain non-blocking considerations for future explicit review. No token values, adapter output, colours or geometry are changed.

The new guarded Rofi activation tool pins approved generated bytes, preserves the original dark theme and search icon in Git, and changes only the existing live theme file. Retaining the `charcoal.rasi` path avoids editing functional configuration or shortcuts and avoids a second active configuration. Command+Space still runs `rofi -show drun`. Rollback restores exact prior styling, does not depend on future token/adapter changes and leaves the original icon in place. Both directions reject unrecognised configuration changes.

Validation: 22 tests pass, including real native Rofi parsing/default resolution in a temporary home for activation, repeated activation and rollback; exact prior-byte recovery on failed verification; symlink/unknown-theme rejection; approval pins; existing native string/expansion regressions; and the Mangobar tests. Read-only validation against the real config confirms default theme resolution and preservation of fuzzy search, application selection, navigation and Escape settings. These are parser/configuration checks, not simulated keyboard or application-launch tests.

Live activation was attempted but failed Wayland preflight before any live write. All protected live files retain their original hashes. The exact Foot activation/rollback commands and interactive search/navigation/Escape/Enter checks are in [architecture](architecture.md#rofi-activation-and-rollback). No further visual approval is needed for this baseline; on-device functional verification remains pending due to the sandbox's inaccessible compositor.

## MangoWM candidate 1 — unapproved appearance adapter

Read the complete live config and original visual reference. This candidate extends the porcelain/cool-grey/metal/graphite system to window structure; it does not revise the approved Mangobar/Rofi baselines. All exact MangoWM mappings and new geometry below are proposed, pending the user's visual review. The 6px radius is retained from the current configuration. Blur, shadows (including `shadows_color`), opacity, dimming, animation, layouts, input, hardware and autostarts are outside adapter ownership.

| Native setting | Current value | Candidate |
| --- | --- | --- |
| `border_px` | 4 | 2 |
| Inner horizontal/vertical gaps | 5 / 5 | 8 / 8 |
| Outer horizontal/vertical gaps | 10 / 10 | 12 / 12 |
| `border_radius` | 6 | 6, retained |
| `root_color` | `#201B14` | Canvas `#DADAE3` |
| `border_color` | `#444444` | Metal `#A8A8B4` |
| `focus_color` | `#C9B890` | Neutral accent `#77768F` |
| `urgent_color` | `#AD401F` | Signal red `#AD4038` |
| `drop_color` | `#8FBA7C`, alpha `55` | Signal green `#728858`, same alpha `55` |
| `split_color` | `#EB441E` | Signal yellow `#E3BE47` |
| `maximized_screen_color` | `#89AA61` | Metal `#A8A8B4` |
| `scratchpad_color` | `#516C93` | Graphite developer surface `#2F303B` |
| `global_color` | `#B153A7` | Neutral accent `#77768F` |
| `overlay_color` | `#14A57C` | Secondary ink `#666573` |

All native colours are emitted as `0xRRGGBBAA`; alpha is opaque except the existing translucent drop indicator. Yellow is proposed for the deliberate split-placement indicator, while Mangobar's yellow active workspace is unchanged. Green is limited to transient drop placement, not assigned to maximization or other states that do not mean success. Neutral state overrides avoid decorative orange/blue/violet borders; their recognizability still needs review. These roles match the [official theming definitions](https://github.com/mangowm/mango/wiki/theming) and were validated with installed MangoWM 0.18.3. Focus contrast is 3.17:1 against canvas, 4.15:1 against porcelain and 2.97:1 against the dark developer surface; the thinner border needs on-device inspection at 1.5 scaling. No accessibility certification is implied.

Engineering: the adapter emits only 16 owned appearance values. A lossless merge replaces only their existing right-hand-side values, preserving comments, spacing, line endings and every other byte. Missing/duplicate keys, included configs and unknown current visual values fail closed. No complete live config is committed or maintained as another source of truth. Original visual values alone are versioned in `themes/recovery/mango.json`.

The controller supports native checking, timed preview, rollback and a future approval-gated activation. Preview changes the one existing config temporarily and reloads it through `mmsg dispatch reload_config`; its `finally` cleanup and independent timed restorer return previous visual values. A pending operation journal stores only before/after visual values. It survives parent termination; after power loss or loss of IPC, explicit rollback may still be needed. Concurrent nonvisual edits are retained on restoration, while conflicting visual edits are refused. Permanent activation is locked by a null approval hash until the user reviews this candidate.

Validation: 30 tests passed, including native validation, exact round-trip preservation, malformed/duplicate settings rejection, failed-reload restoration, interrupted-preview watchdog recovery, concurrent-edit handling and the existing Mangobar/Rofi suites. The complete real config and its temporary candidate merge both pass `mango -p -c`. Its live hash remains unchanged; approved Mangobar/Rofi generated hashes also remain unchanged. Native IPC access returned `connect: Operation not permitted`, so no live preview was performed and no current candidate screenshot is claimed. On-device before/after capture and 2px border/gap inspection remain pending.

Reported only, unchanged:

- `bind=SUPER,n,switch_layout`: Command+N switches layouts, conflicting with expected application new-window behaviour.
- `bind=SUPER,m,quit`: Command+M quits MangoWM rather than minimizing a window.
- Animation durations: move 500ms, open 400ms, tag switch 350ms, close 800ms, focus 0ms. Closing in particular may feel slow; review timing separately, without changing curves or duration in this visual candidate.

## MangoWM initial baseline approved — fd645da

The user visually reviewed and approved the exact candidate as the initial baseline, authorizing permanent activation without redesign. `approved_sha256` now pins the existing candidate hash (`4cf4b0cdc2551be8f0a21e4baaa1532e7851ce6012093f0a15ca8e524036884e`); all 16 values and rendered output remain identical. The preceding candidate's unapproved status is historical and is superseded by this decision.

The existing activation workflow is enabled, with an additional transaction assertion that reverse-merging the old owned values reconstructs the original complete bytes. This rejects changes to anything outside the 16 appearance settings. A read-only `verify` command checks exact approved on-disk values, native syntax and one reachable compositor using the canonical config. Existing atomic replacement, journal, failure restoration and version-controlled rollback remain in place. Successful activation clears the pending journal, so the timed recovery process leaves the committed baseline alone.

Validation: 33 tests passed, including read-only verification, approved activation, repeat activation, completed-operation watchdog behaviour, rollback, nonvisual-change rejection, failed reload and existing native parser suites. The live activation attempt stopped on `mmsg get version` with `connect: Operation not permitted` before any live write. Live file hashes are unchanged; on-device activation/verification must be run from Foot. Rendered appearance cannot be newly certified from this sandbox, although the user has already approved the visual candidate. No shortcuts, gestures, layouts, animations, hardware settings, autostart entries or design values changed.


## Foot first candidate — proposed, not activated

The dark developer environment uses the established `#2F303B` graphite foundation
with `#EAE9F0` chrome text and `#A8A8B4` metal secondary text. This extends the
original [Braun reference](references/braun-interface-concept.png)'s material
hierarchy into the developer workbench; it adds no ornamental terminal chrome,
branding, glow or gradients. Eight logical pixels of padding provide a compact
inset inside the already approved MangoWM frame. Light applications, window
styling, foundation colours and shared signals are unchanged.

A small yellow block cursor marks active insertion, becoming hollow on loss of
focus. Selection uses neutral emphasis blended into graphite (`#575669`) with
porcelain text. Yellow remains purposeful in search and URL jump labels. Red
marks search failure. These component mappings and all new terminal values are
candidates; they do not supersede the approved light-system mappings.

| ANSI role | Regular | Bright |
| --- | --- | --- |
| Black / quiet neutral | `#343442` | `#A8A8B4` |
| Red | `#C88C8B` | `#D2A2A1` |
| Green | `#9CAA8D` | `#AEBAA3` |
| Yellow | `#E3BE47` | `#E7CA6B` |
| Blue | `#9DAFC8` | `#AFBED2` |
| Magenta | `#B8A2BA` | `#C5B3C7` |
| Cyan | `#91B8B5` | `#A6C5C3` |
| White | `#DADAE3` | `#F8F8FA` |

Red mixes the shared red with chrome at 45%; green mixes shared green with chrome
at 35%. The additional cool blue, muted mauve and mineral cyan serve ANSI syntax
compatibility, not new semantic signals. Bright chromatic variants mix 20%
porcelain into the regular values rather than adding saturation. Selection mixes
55% neutral accent into graphite. The recipes live only in the canonical tokens;
this table records their first-candidate outcome. Normal text contrast is
10.84:1, secondary 5.55:1, selection text 6.73:1. Regular ANSI black is reserved for
light/inverse backgrounds; all other ANSI foregrounds pass 4.5:1 on graphite.
Applications decide ANSI meanings, so the terminal cannot enforce status-only
colour use inside every program.

Typography investigation: IBM Plex Mono is absent; Fontconfig resolves its name
to DejaVu Sans Mono. DejaVu Sans Mono, Adwaita Mono and Ubuntu Mono are installed.
Plex remains the original developer-font exploration but would require an
explicit installation before a truthful visual comparison. Adwaita Mono is an
available developer-oriented alternative; Ubuntu Mono offers a more overtly
humanist character. Neither has been visually evaluated here at the display
scale. This candidate retains the existing DejaVu Sans Mono **16pt**, with its
familiar broad glyphs and current metrics, rather than combining an unverified
font change with the first palette review. The font name's capitalization is
normalized; the resolved family remains the same. Line height and DPI policy are
unchanged. This is a local Foot candidate, not a final system-wide font decision.

Validation: installed Foot 1.28 accepts the fragment and appearance overrides
layered over the actual live config. The automated suite covers token derivation,
contrast rejection, visual-only settings, native parsing, harmless specimen input
and unchanged approved light-component outputs. Live Foot, MangoWM, Mangobar and
Rofi configuration hashes remain unchanged. Actual launch/capture was attempted
but Foot could not connect to Wayland in this sandbox; **no rendered screenshot
or interactive clipboard verification is claimed**. Native visual evaluation,
font comfort and selection/cursor behaviour remain pending user review using the
[preview workflow](architecture.md#foot-preview--specimen-or-normal-shell).


## Foot palette approved — initial 5cf323e state, superseded cursor colour

The user visually approved the graphite ground, colour direction, yellow cursor,
muted functional colours and relationship to the light desktop as the initial
baseline. The later orange cursor approval below supersedes only the cursor
foreground/background mapping. DejaVu Sans Mono 16pt is retained, not finalized as a
system-wide font decision. IBM Plex Mono is not installed, so no rendered Plex
comparison is claimed. A preview-only family option now supports comparison at
the same readable point size when available, explicitly rejecting fallback.

The existing `--shell` preview launches the normal configured interactive shell
and prompt. Activation now uses a generated native include while preserving every
other live config byte. Rollback restores the original font line and removes the
include file. No shortcuts, other applications, Codex configuration, hardware,
shell configuration or startup entries are edited. Existing terminals are not
restarted. Native syntax and isolated transaction tests cover activation,
idempotence, exact rollback, verification failure, interrupted intermediate
states, approval drift and preservation of functional settings. Actual shell
preview and live activation attempts failed at Wayland access with no live writes;
interactive shell/Codex readability and clipboard/scrollback checks remain for the
desktop session before activation. The [workflow](architecture.md#foot-approved-baseline--activation-and-recovery)
contains the exact commands and limitations.

## Limux Commands — preview candidate, not activated

The Command hub reuses the approved Rhapsody Rofi theme with a local `COMMANDS` heading and search placeholder. No canonical colour, geometry, typography, state meaning or application-launcher value changes. Category/shortcut rows are derived from live MangoWM and Foot configurations on each launch. Snippets live outside the repository. Command+K remains unassigned pending on-device visual and interaction review. The original concept's recessed input, quiet neutral surfaces and narrow yellow selection are inherited from the existing approved launcher; no extra branding is introduced.

## Limux Commands second preview — hierarchy refinement, not activated

The user requested action-first rows, compact sections, everyday shortcuts first and faster access to snippets and utilities. This candidate reuses the approved Rofi surface/search/selection, adds only a local Rofi tab stop and Pango monospace shortcut span, and leaves canonical theme tokens unchanged. Section rows are nonselectable; row metadata keeps category search useful. Command+K remains unassigned, and the Firefox/global-shortcut tradeoff is documented in `docs/commands.md`.


## Limux Commands third preview — visible shortcuts, no activation

The approved direction is retained. The local tab stop is reduced to 300px with a 24-character monospace key field to keep complete Mac-style shortcuts inside Rofi's row width; no shared Rhapsody theme value changes. Section headings remain nonselectable and map to no command. The private snippet setup command creates a mode-600 file outside Git. The user's Firefox profile maps its accelerator to Super, making global Command+K conflict with Firefox search; assignment stays deferred.


## Limux Commands fourth preview — single-line shortcut labels, not activated

The third preview's tab-stop and padded monospace column visibly truncated shortcuts in the user's screenshots. This candidate abandons the two-column treatment in favor of plain action-first rows such as `Capture area screenshot — ⌘⇧4`. Only the picker gets a 700px width override. The approved Rofi launcher theme, heading behavior, category order, search metadata, yellow selection and personal-data separation are preserved. Complete labels are asserted in tests; actual Rofi pixels remain for user review. Command+K is still unassigned.

## Limux Commands fifth preview — utility heading typography, not activated

The user approved the single-line command rows and asked only for quieter section labels. This candidate marks nonselectable heading rows with Rofi's `active` state and applies a preview-only Inter 11 / Rhapsody `text_secondary` treatment with reduced heading padding and more space above than below. No selection, command text, search, shortcut, canonical token, launcher or desktop setting changes. Letter spacing is omitted because a dependable native Rofi control was not established. Command+K stays unassigned pending visual review.

## Limux Commands approved for activation

The user approved the fifth preview's exact appearance and accepted the global Command+K conflict with Firefox's Super accelerator. No appearance tokens or selector values change. A guarded binding controller adds/removes only `bind=SUPER,k` in the sole live MangoWM config, validating through MangoWM and requiring IPC before mutation. User snippets and quicklinks remain in a private config outside Git. Live activation stopped at inaccessible compositor IPC in the sandbox before any config write; the documented Foot workflow completes it.

## Limux Commands live activation verified on disk

The user approved permanent Command+K activation. The sole MangoWM config now has exactly one `SUPER,k` Commands binding and retains exactly one `SUPER,space` Rofi launcher binding. The live file passes MangoWM parsing. A nonblocking picker lock prevents duplicate Commands instances. No Rhapsody visual selectors or tokens changed. The sandbox cannot reach compositor IPC, so interactive keypress, clipboard and visual verification remains for the user's Foot session. Rollback removes only the Commands binding.

## Mangobar Option A — Quiet Workspace Strip, proposed and not activated

The user selected a quiet numbered strip with one compact, filled orange active workspace. The A/B/C previews at `cc17325` were reviewed and rejected because the inactive slots appeared segmented and the active fill occupied the full bar height. B's spacing is retained for one revised preview. Stock Mangobar 0.2.2 cannot inset a tag background: its painter always fills the bar height, and `margin-top` does not affect module painting. The segmentation comes from the absence of a full-width backing surface behind the module gaps. The revised preview uses an isolated, source-hash-checked 0.2.2 build with a dedicated `background-inset` property and full-width backing. Inactive states have no background, and the active fill uses candidate orange `#D46A43` with dark ink. This renderer patch is experimental and **not an approved live dependency**. Candidate values live only in `[mangobar_candidate]`; `semantics.selected`, the approved baseline, installed binary and live files remain intact. Generated output stays under ignored `build/quiet-workspace-strip/`. Native tests pass, but real visual approval and any maintenance decision for the patch are pending. See [the candidate review](quiet-workspace-strip.md).

## Quiet Workspace Strip engineering review — activation pending

The user approved the visual direction at `ec2ba0f` and requested an engineering review before permanent activation. The retained 0.2.2 working tree contains a pre-existing Limux T2 metrics change. The build now pins the clean upstream `0.2.2` commit and applies that hardware patch separately from the 25-added/8-removed-line visual patch. A reversible activation script is prepared but has **not** run against the live bar. The original binary, approved CSS and canonical startup path remain available. Interactive workspace clicks, all-nine switching, status modules and tray behaviour still require a Foot-session check; native parser and file-transition tests cannot certify them. See [the engineering review](quiet-bar-engineering-review.md).

## Current Rhapsody reconciliation — 2026-10-30

The user approved and activated the Quiet Workspace Strip after the engineering review. The current live stylesheet's SHA-256 matches the generated Quiet Strip (`03c674d5acb12287503b9fd08b9adb6903e8c7feaaf083d11dc8f93db598ab7c`); the live MangoWM config has one `SUPER,k` Limux Commands binding, one `SUPER,space` Rofi launcher binding and one `limux-bar start` entry. This repository inspection cannot reach the graphical process namespace, so those on-disk checks do not certify every live interaction. The [architecture status table](architecture.md#current-implementation-and-approval-status--2026-10-30) is the maintained current-state summary.

The orange active workspace at `#D46A43` is an approved component decision, superseding the original yellow boxed workspace as the live design. The six foundation colours remain. Foot's approved block cursor now shares the orange swatch, while Rofi/Commands retain a distinct yellow list edge and Foot search/ANSI yellow remain separate roles. Mako and GTK/Thunar have no approved Rhapsody adapter. The original Braun image, archived source, old boxed Mangobar renderer, pinned patches, prior binary/CSS and rollback state remain reference and recovery assets.

Verified source distinctions: `render_quiet()` maps the active workspace to orange; the legacy `render()` uses `selected` yellow; Rofi uses yellow for the selected row edge; Foot uses orange for its cursor and yellow for search match and ANSI yellow; MangoWM uses yellow for a split-placement indicator. Limux Commands previously held 700px width, 11 rows and heading metrics inside its Python theme override. These are different roles with different owners. The review's `xdg-open` observation is confirmed on this host (`command -v xdg-open` finds nothing; `xdg-utils` is not installed). Quicklink repair is a separate functional task and was not attempted here. The review's container-only test errors do not describe this host's test environment.

This reconciliation adds explicit semantic references for active workspace, list selection, terminal cursor and terminal search match. The old `selected` mapping stays solely for the recoverable boxed bar renderer. Commands' approved geometry and heading metrics move to `[limux_commands]`; the native Rofi selectors and functional registry stay in the adapter. Pre/post hashes of the generated legacy bar, active Quiet Strip, Rofi, MangoWM, Foot and Commands theme override are identical. No activation script, live appearance file, shortcut, hardware setting or rollback manifest was changed.

Separate decisions still needed: whether Rofi/Commands should keep a yellow list edge or use a neutral focus treatment; whether Foot's search cues should remain yellow or use other tested values; whether Commands should get a modern interface redesign; and later system-wide typography and Mako/GTK styling. Each needs on-device previews and explicit visual approval. The active bar and Foot cursor orange are settled.

## Limux Commands neutral candidate — preview pending screenshot review

One Commands-only preview proposes a quieter hierarchy within the existing Rofi implementation. The proposed `list_selected_neutral` semantic resolves to `metal` and `on_list_selected_neutral` to graphite text. The candidate removes the yellow selection border, keeps a visible neutral row fill, reduces section labels to Inter 10 with quieter ink, trims search/row/outer spacing and omits the redundant top label. It keeps the 700px width and existing single-line shortcut labels to protect complete combinations. Candidate-only values live in `[limux_commands_candidate]`; unchanged geometry inherits the approved `[limux_commands]` values. The normal Rofi launcher, Foot, bar and other components are untouched. Metal was preferred to canvas for the preview because canvas against porcelain is only 1.31:1; metal improves the state cue to 2.22:1 with 5.2:1 selected text contrast. Actual focus visibility remains for screenshot review.

The new `candidate` picker mode uses the same registry, rows, lock, Rofi invocation, selection handling and clipboard/open actions as `preview`; only its `-theme-str` value differs. The installed Rofi 2.0 parser resolves the neutral fill, zero row-border width, compact search and nonselectable section styling. The sandbox could not create a Wayland display for `grim`, so native screenshot and on-device interaction review remain pending. This candidate has no activation path; Command+K continues to use the approved theme until a later explicit decision.

## Foot cursor approved orange — 2026-10-30

The user reviewed and approved the orange Foot block cursor. `terminal_cursor` independently maps to the shared `workspace_orange` swatch (`#D46A43`), and `on_terminal_cursor` maps to `signal_ink` (`#141810`) at 5.09:1 contrast. `workspace_active` retains its separate semantic mapping to that same swatch. Changing the shared swatch updates both components; changing either role reference affects only its owning component. The block style and hollow unfocused cursor remain. Graphite background, typography, padding, ANSI palette, selection, search/no-match colours and keyboard behavior are unchanged.

Foot's text contrast validation remains at 4.5:1 for cursor and selection pairs; the approved orange/ink pair passes at approximately 5.09:1. The previous approved yellow-cursor fragment is preserved verbatim as `themes/recovery/foot-yellow-cursor.ini` and pinned separately. `activate-foot.py activate` targets the orange fragment; `rollback` restores the exact yellow-cursor fragment, and `restore-original` returns to the pre-Rhapsody Foot configuration. The user activated the orange appearance. `activate-foot.py verify` and native Foot configuration parsing confirm the live include and generated fragment. Existing Foot windows or a persistent server are not restarted.

## Limux Commands neutral refinement — pending visual review

The user approved the overall `73ac56c` layout and asked for quieter, truly noninteractive section headings plus a lighter selected row. The proposed `list_selected_neutral` now maps to the Commands-only `#C7C7D2` cool grey; it changes no shared surface or other component. All three Rofi heading states, including `selected.active` reached by pointer hover, resolve to transparent backgrounds, muted text, identical spacing and a default cursor. The actionable selected row alone receives the neutral fill. Native Rofi 2.0 theme resolution verifies the selectors; only an on-device screenshot can settle the visual weight at 1.5 scaling.

An appearance-only controller is prepared but has not been activated. It pins the reviewed override hash, verifies the existing Command+K binding and approved Rofi base, then writes one private state marker. The live Commands script reads that marker on its next invocation; rollback deletes only the known marker and remains available after source drift. The user's separate follow-up issue is the normal Command+Space launcher's historical yellow selection stripe. That launcher is outside this refinement and remains byte-identical.


## Quiet Workspace Strip finishing changes — 2026-10-30

The user directly approved three active-bar refinements: retain orange `#D46A43` and render the active workspace number in pure white, add an 8px left inset using the existing Rhapsody spacing token, and show a compact charging cue. White on orange is approximately 3.53:1. This is a user-approved exception for the active workspace label only; general text contrast validation remains unchanged. The active workspace foreground uses the canonical `pure_white` token and remains semantically independent from Foot's dark cursor foreground.

Mangobar 0.2.2 already reads the kernel battery status and selects its charging icon only for `Charging`. The current Inter face lacks U+26A1, and the installed renderer initializes only one font without custom fallback, so the charging cue uses plain `chg` text. Discharging, full, and unknown states have empty icons and retain the existing percentage calculation. No status daemon, new package, renderer patch, or battery arithmetic change is introduced.

The token-driven CSS keeps the orange fill, active inset, radius, workspace padding/gap, bar height and other module styles unchanged; only the group left margin is added. The guarded `activate-quiet-bar.py refine` operation snapshots the prior live candidate inside its existing private activation state. `restore-prior` returns that candidate, while the existing `rollback` retains its pre-Strip recovery behavior. The version-pinned binary, source patches, MangoWM startup, T2 support and unrelated desktop components are unchanged.

The user subsequently activated the refinement from Foot and confirmed that the result looks correct. Live config/CSS hashes match the guarded candidate, and the activation state retains the previous active candidate for exact `restore-prior` recovery.

## Verified current state — 2026-10-30

The user confirmed three points; read-only inspection supports them. No live styling, software or package changed during this documentation update.

- **Intentional decisions:** the Mangobar orange `#D46A43` active workspace with pure white text, and Foot's orange block cursor with `signal_ink` foreground, are deliberate. Live Mangobar CSS/config match `render_quiet()` output and the private activation manifest. The live Foot fragment matches its pinned hash (`activate-foot.py verify` passes).
- **Limux Commands:** functional on Command+K, but the user is not satisfied with its visual design. Its redesign is **parked, not approved**. This supersedes the earlier "approved for activation" description of the fifth-preview appearance. The neutral-v1 appearance marker is present (written 2026-10-30, mode 600) and matches the current candidate hash, so Command+K currently uses the `[limux_commands_candidate]` styling. That contradicts the earlier "not activated" entry for the neutral refinement. It is recorded here as observed state, not as approval. Rollback of the marker remains available and has not been run.
- **Package cleanup:** Waybar cleanup is complete. `cairomm`, `glibmm` and `fmt` have been removed. `pacman -Qdtq` now returns `libsigc++` and `upower`.

Other live components also match their pins: Rofi `charcoal.rasi`, the 16 MangoWM appearance values, and the single `limux-bar`, `SUPER,space` and `SUPER,k` entries.

## Limux Files — Thunar design approved and implemented — 2026-10-30

**Exploration.** The installed GTK stack is GTK 3.24 only; Thunar 4.20.10 and Firefox (default "System theme") are its consumers. Thunar was kept: it is the only option that adds no packages or services, keeps Command-key remapping possible through its GTK 3 accelerator file, and can be styled by Limux. Nautilus (89 packages, an indexer service, libadwaita that ignores themes) and Dolphin (Qt/KDE stack) were rejected. adw-gtk3 was chosen over built-in Adwaita as a calmer, maintained, data-only base.

**Rejected first pass.** Isolated previews compared built-in Adwaita, adw-gtk3 and Rhapsody colours mapped onto adw-gtk3 (graphite tint, a NeXT-style material lift, solid graphite, metal). The user found them all "fine" but indistinguishable and not designed. The diagnosis: they recoloured GTK's layout, while the approved bar's quality comes from structure, not colour.

**Approved design target.** A Limux Files target was drawn from the bar's own patterns before checking Thunar's limits: one porcelain surface with hairlines; type-led hierarchy (path as text, current folder in 600); the Rofi recessed input for search and rename; a quiet chrome mark for the sidebar location; the bar's inset control applied to selection (graphite fill, porcelain text) with metal for inactive windows; small labels instead of chrome; quiet measurements; outline icons; no Type column; no signal colour in the file window. The user approved the target as "1000% better" and asked for it to be implemented. Graphite active selection supersedes the earlier interim "metal in both views" choice, which had been a workaround for a Thunar limitation.

**What Thunar reaches.** One surface, quiet menu, plain-text path, outline icons, Name/Size/Modified columns, window-aware graphite/metal selection and graphite dialog controls. **Known gaps:** GTK 3 list selection runs edge to edge (no inset); the path has no slash separators and keeps its scroll arrows and edit pencil; search is a button until opened; section and column labels cannot be uppercased; recent dates show "Today" without time; the status bar keeps Thunar's wording; dialogs use the system font and draw their own title bar.

**Implementation.** `[thunar]` tokens map every role to an existing Rhapsody colour; no new colours. `scripts/gtk.py` generates the GTK 3 stylesheet (named colours plus rules scoped to Thunar windows, Inter applied only to Thunar windows), a `Limux-Rhapsody` outline icon theme inheriting Adwaita (folder and document drawings, 54 standard names), and Thunar view settings. `scripts/activate-gtk.py` installs `~/.config/gtk-3.0/gtk.css` and the icon theme, sets nine Thunar view properties and the GTK and icon theme GSettings, pinned by `themes/recovery/gtk.json`. It refuses unknown existing values, undoes completed steps on failure, and rolls back to the prior defaults without reading tokens, leaving any setting the user changes later untouched. Requires the `adw-gtk-theme` package. No shortcuts, actions, Thunar accelerators or system fonts change.

**Shared effects.** The GTK theme, named colours and icon theme apply to all GTK 3 apps. Firefox's default theme follows GTK, so its toolbars and file dialogs change too; review them after activation. Thumbnails and Trash still need the optional `tumbler`/`gvfs`, and Command-key shortcuts in Thunar remain a separate functional decision.

**Activated and system font approved.** The user installed `adw-gtk-theme`; `activate-gtk.py activate` and `verify` passed and the user confirmed the result looks good. The user then approved Inter as the system interface font. `typography.ui_size = 10` now feeds both the Thunar stylesheet (unchanged output) and the GTK `font-name` setting (`Inter 10`, from Adwaita Sans 11), which the same activation owns and rolls back. Monospace, document font and Foot typography are reviewed separately.

## Foot typography — Adwaita Mono — 2026-10-30

The user found Foot visually off beside the bar. Diagnosis: DejaVu Sans Mono 16pt was about 2.4 times the bar's text size, the 8px padding left text nearly touching the window border, and DejaVu's wide, tight-leading shapes sat awkwardly beside Inter. Isolated previews (the real `foot.ini`, a private fontconfig, fonts unpacked from hash-verified Arch packages, nothing installed) compared DejaVu at 16 and 12, Adwaita Mono, JetBrains Mono and IBM Plex Mono, sized by visible x-height. The user approved **Adwaita Mono 12.5 with 16px padding**: compact and modern, GNOME's companion to the Inter-based Adwaita Sans, already installed and already the GTK monospace font. Palette, cursor, selection and behaviour are unchanged. The rollback target is now the previous DejaVu Sans Mono 16 fragment (`themes/recovery/foot-dejavu-orange.ini`); the older yellow-cursor fragment remains in Git history. The GTK document font is left unchanged because no installed application uses it.

## Rhapsody notifications (Mako) — approved and activated — 2026-10-30

The previous Mako config was a dark `#202020` slab in DejaVu Sans 13 with a saturated blue progress fill and app icons found only for some apps. A design from the bar's patterns was previewed in isolated Mako instances below the real bar: a porcelain card with a 1px metal edge and 6px corners on the window grid (12px below the bar and from the right edge); a small quiet uppercase app label (Pango `text_transform`), a graphite 600 summary and a secondary body, in Inter at the interface size; signal red edge and label for critical only; quiet ink for low urgency; canvas progress. Icons were removed because the label already names the app and inconsistent icon lookup broke alignment; apps that send images lose them. The user approved it as shown. `activate-mako.py` moved the appearance into a generated include, kept every behaviour line, reloaded Mako live and passed `verify`.

## Limux picker — launcher and Command menu — 2026-10-30

The user found both menus poor. Diagnosis: the Command menu's search field and its rows started on different edges, shortcuts trailed each action after a dash, and no row showed as selected because the list opened on a section heading; the launcher still used the yellow edge, mixed full-colour and dated icons, and listed nine helper or developer entries. A design target drew both as one family from established patterns (notification card, recessed field, one left edge, graphite inset selection from Thunar, quiet labels, a quiet secondary column). The user approved it and three decisions: hide the nine entries, name Thunar and Foot by role (Files, Terminal), and drop icons. Isolated previews confirmed that Rofi matches visible text rather than markup, that a tab stop holds the secondary column without truncation, and that matching on generic names keeps Files and Terminal findable as Thunar and Foot. `list_selected` now maps to graphite; the parked neutral Commands candidate, its marker (removed with its own rollback), controller and tokens were retired. `activate-rofi.py` (with `rollback` to the yellow-edge launcher and `restore-original`) and the new `launcher-entries.py` were activated and verified, and live captures of the normal launch paths match the approved design. The user then reviewed both live menus on the desktop and approved the result.

## Thunar shortcuts and file icons — 2026-10-30

The user asked for the remaining follow-ups to be done. Thunar now has Mac-style Command shortcuts for its own actions through `thunar-shortcuts.py`, avoiding every Command key MangoWM owns globally; the conflicts (⌘N, ⌘I, ⌘R, ⌘O, ⌘M, ⌘G, ⌘←/→) keep Thunar's defaults, and changing MangoWM's bindings remains a separate decision. The Limux-Rhapsody icon set gained inner marks on the document outline for text, images, archives, audio, video, code, spreadsheets and presentations, drawn once on a 16px grid and scaled for 64px; `activate-gtk.py` now recognises the previous approved icon set and replaces it in place, restoring it if a later step fails.

**File-manager support packages.** The user installed `xdg-utils`, `gvfs` and `tumbler`. Quicklinks now open folders in Thunar and links in Firefox; Thunar shows Trash and can mount removable drives; thumbnails are generated on demand. `gvfs` brings `udisks2`, `openssh` (no server enabled) and storage libraries; none adds a boot-time service. `upower` is kept because Firefox starts it for battery status; The user then removed `libsigc++`; `upower` is the only remaining orphan.

**Icon-view selection fix.** After `gvfs` was installed, Thunar enabled file highlighting, which fills the whole selected grid item with the theme selection colour (graphite) instead of tinting the icon. The earlier workaround (metal label, graphite text, kept to stop the icon tint) then drew graphite text on graphite, and selected names became unreadable. The workaround was removed: grid selection now matches the approved target, a graphite tile with a porcelain label and the icon left untouched, and metal with graphite text in an inactive window. Verified in isolated previews in both views, then activated as an in-place stylesheet upgrade. If `gvfs` is removed, highlighting turns off and the old icon tint returns, so `gvfs` is now part of Limux Files.

## Night light — wlsunset — 2026-10-30

The user chose location-based night light over fixed times. MangoWM supports the wlroots gamma-control protocol, so `wlsunset` (already installed) now starts from one `exec_once` line in the MangoWM config, after the notifications entry, with approximate coordinates for the user's city, kept only in the live config. Defaults are kept (4000K at night, 6500K by day). The Quiet Strip activation pins the whole MangoWM config by hash, so its pin was updated in the same change; its `check` passed before and after. This is a display behaviour, not a Rhapsody token output.

When the machine files were brought into Git, the coordinates moved out of the MangoWM config into the private `~/.config/limux/location`, read by the tracked `limux-night-light` helper, so no location is committed.

## Bar status icons and agent indicators — design target approved — 2026-10-30

**Request.** Show what Codex and Claude Code sessions are doing from any workspace (working, needs input, idle, error), and let Wi-Fi, battery and volume appear as text, icon + value or icons only, without rewriting the bar.

**Icon family.** Isolated previews ran temporary overlay Mangobar instances with private fontconfig files (fonts unpacked from hash-verified packages; nothing installed). Material Symbols (Arch `ttf-material-symbols-variable`) and Nerd Fonts symbols drew status as filled shapes (a solid Wi-Fi wedge and battery block) that read as a phone status bar, away from the reference's thin Wi-Fi arcs. The user chose **Tabler Icons** (MIT, line-drawn; npm `@tabler/icons-webfont` 3.49.0, integrity-verified) at its **regular stroke and the bar's text size**, as **icon + value**, over the 200/300 strokes and a 1.3× scale.

**Spacing.** With even gaps, values floated between neighbouring icons. Approved: icon and value **4px** apart, **20px** between pairs, **36px** between the agent group and the system group, and a **20px** right inset matching the left inset measured on the live bar (20.0px left; preview right 20.7px, the difference being the percent glyph's side bearing). These become tokens.

**States.** Working: open spinner, quiet. Needs input: alert circle in orange with the agent name in ink. Idle: dashed circle, quiet. Error: circled ×, signal red. Codex has no failure hook, so it shows working, needs input and idle only.

**Technical findings.**
- Mangobar uses one font (fcft) for the whole bar; per-module `font-family` replaces the bar font. Icons therefore come from fontconfig fallback behind Inter, inheriting its size and weight. A fontconfig `matrix` rule can scale only the icon font, so larger icons need no bar patch.
- Inter and Adwaita Sans contain private-use glyphs (for example U+E000, U+E04D–E050) that collide with Material code points; Tabler's needed code points are free.
- Mangobar's `padding` reads only the vertical and horizontal pair; asymmetric spacing needs `padding-left`/`padding-right`.
- Custom modules support `exec`, `interval`, `signal` (SIGRTMIN+N for immediate refresh) and click actions, but not per-state classes; state colour needs a small bar patch or one module per state.
- Claude Code hooks: `UserPromptSubmit`, `PreToolUse`/`PostToolUse`, `PermissionRequest` and approval notifications, `Stop`, `StopFailure` (API errors), `SessionEnd`. Codex 0.165 hooks (enabled by default, trusted once in `/hooks`): `UserPromptSubmit`, `PreToolUse`/`PostToolUse`, `PermissionRequest`, `Stop`, `Interrupt`, `SessionEnd`; no failure event. Both support asynchronous command hooks. MangoWM reports each window's process ID, so a click can focus the agent's Foot window.

**Status.** Design target approved; not implemented or activated. Implementation needs the Tabler font installed as a pinned user font, one fontconfig fallback rule, display and spacing tokens, the hook writers, the bar module and click-to-focus, each with activation and rollback.

**Implementation, preview stage.** `[bar_status]` tokens; `scripts/bar_status.py` generates the agent modules (one per colour slot per agent, so an absent state takes no space), the icon + value formats for Wi-Fi, battery and volume (Tabler level icons) and the spacing CSS; `scripts/agent-status.py` records hook events per session in `$XDG_RUNTIME_DIR/limux/agents`, drops sessions whose agent has exited, shows each agent's most urgent session with a count, refreshes the bar by real-time signal and focuses the agent's Foot window on click. It signals only a bar whose config declares the refresh signal, because an unhandled real-time signal would terminate the live bar. `patches/mangobar/03-hide-empty-custom-modules.patch` makes empty custom modules collapse; it is not yet part of the pinned build. A preview with the privately built patched bar, a private Tabler fontconfig and simulated sessions showed no agents, working with needs input, two idle Codex sessions with a Claude error, and Claude alone; the right inset measured 20.7px. Not yet activated: the font, fontconfig rule, Wi-Fi script options, rebuilt bar and hooks.

**Activated.** The user watched a 30-second live overlay on the real bar and approved activation. `activate-bar-status.py activate` and `verify` passed; the first live session (this Claude Code session) registered as working through the real hooks, and click-to-focus selected its Foot window. Codex hooks await trust in its `/hooks` screen.


**Working spinner rotation, approved and activated 2026-10-31.** At full size the user found the working icon static: Mangobar refreshes custom modules in whole seconds and has no animation. The user chose to keep the Tabler open-arc spinner and rotate it, over braille frames or a colour pulse. `patches/mangobar/04-spin-custom-modules.patch` adds a custom-module `spin-period` (ms per clockwise turn): the bar rotates the glyph bitmap about its centre with bilinear filtering, at about 15 frames a second, only while such a module is visible; layout and advance are unchanged and nothing else wakes the bar. Working moves to its own `icon-spin` slot so the idle circle never turns; `spin_period = 1000` is a token. The preview exposed that Mangobar keeps CSS selectors and click actions in 32-byte buffers, so `custom-agent-claude-icon-working` lost its style; slot names now stay within 31 characters, guarded by a test. A 30-second overlay with Claude and two Codex sessions working showed both arcs turning crisply, with 1.9% of one core for the bar. The user approved activation: the previous activation was rolled back, the config, CSS and binary re-pinned, and `activate` and `verify` passed; the live bar showed this session's arc at different angles 0.3s apart.

**Wi-Fi and battery icon size, approved and activated 2026-10-31.** At full size the user found the Wi-Fi and battery icons too small: drawn at the 13px text size, the Wi-Fi ink was 7px and the battery 9px tall against 14px capitals, while the spinner, circles and volume read well. Scaling the whole icon font (1.25× and 1.35× previews) enlarged those too, which the user rejected. `patches/mangobar/05-icon-glyphs.patch` centres icon glyphs on the text's cap height (each measured within half a pixel of it) and adds `glyph-scale`, drawing chosen glyphs from the same font pattern at a multiple of the size for both layout and drawing. A live preview of Wi-Fi and battery alone at 1.25× and 1.35× followed; the user chose **1.25×**, now the `wifi_icon_scale` and `battery_icon_scale` tokens. Re-pinned and activated by rollback and `activate`; `verify` passed and the live bar matched the preview.

**Battery level rounding, approved and activated 2026-10-31.** At 39% the battery icon showed one bar of four: Mangobar's equal bands (`percent * n // 101`) round down by up to a fifth. The generated config now lists eight bands with each inner level twice, so the icon shows the nearest quarter (1 bar from 13%, 2 from 38%, 3 from 64%, full from 89%); no bar code changed. The user approved activation without a preview; `activate` and `verify` passed.

**Calmer left group, approved and activated 2026-10-31.** The user questioned the window title and the nine fixed workspace numbers. The title only repeated what the focus border shows (usually a terminal title), so it is removed. Workspaces with windows and the current one are listed, through Mangobar's native `hide-empty`; numbers stay because with gaps they identify the workspace and double as its Ctrl+number shortcut, where dots or icons would be ambiguous. The active orange and plain inactive numbers are unchanged. Tokens `hide_empty_workspaces = true` and `window_title = false`; the user watched a live preview and approved activation, and `verify` passed.

## Limux picker and Files fields — workspace orange — 2026-10-31

The user felt the picker and file window had drifted from the bar and terminal: no trace of the brand orange, and a recessed search field whose retro look no longer fit. Orange already meant "where you are" (active workspace, terminal cursor), so it was placed only where it carries that meaning. A design target page compared the current state with A (flat field, orange caret, graphite selection) and B (A plus the bar's orange inset with white text as the picker selection). The user chose **B**.

Picker: the search sits flat on the card (Inter 13, `text_quiet` placeholder, 2px `text_caret`), divided from the list by a full-width hairline at the Thunar hairline weight; card padding moved to the list so search text, labels and rows keep one left edge. `list_selected` → `workspace_orange` and `on_list_selected` → `pure_white` extend the bar's white-on-orange exception (~3.53:1) to exactly this pairing through `[rofi] selected_contrast_exception`; every other picker check stays at 4.5:1. Thunar: text fields are porcelain with a metal edge and 4px corners; while typing, the edge and caret are orange. File selection stays graphite. The recess tokens were retired.

An isolated preview showed the launcher (empty and with a query), the Command menu and an isolated Thunar. The orange caret, bold match highlighting on the orange row and the secondary column read correctly; Thunar's typing state could not be captured without a keystroke tool, so the user chose to check it on the live app. `activate-rofi.py` and `activate-gtk.py` activated and verified; the live launcher matched the preview. Rollback restores the graphite picker (`themes/recovery/rofi-limux-picker-graphite.rasi`); the yellow-edge launcher is in Git history.

## Lock screen and idle — approved and activated — 2026-10-31

The desktop had no lock screen: suspend worked on lid close, but opening the lid returned straight to the session. The user chose hyprlock and hypridle, a 5-minute idle lock (dim 30 s before, display off 30 s after), idle suspend after 15 minutes on battery only, locking before every sleep, and Ctrl+Command+Q. A porcelain design target was approved: the canvas ground, a light 96 px clock, the date, one 280 × 40 porcelain field with a 2 px orange edge (you always type there), metal while checking, signal red for a wrong password, a quiet Caps Lock line and the user name at the bottom edge. One deviation from the drawing: secondary and quiet greys reach only 4.12:1 and 4.0:1 on canvas, so the date and small labels are graphite, set apart by size and weight; the placeholder stays quiet on the porcelain field.

The first unlock test showed raw markup in the field because hyprlang reads `#` as a comment; colours in markup are now `##`, guarded by a test. The second test passed on the real session through every state (resting, typing, checking, wrong password, retry, unlock). Known small gaps: the date sits slightly tighter under the clock than drawn, and the placeholder is smaller because hyprlock sizes it from the field height. Video playback keeps the session awake through the app's own idle inhibit rather than MangoWM's full-screen inhibit, so a full-screen terminal still locks. `activate-lock.py activate` and `verify` passed; hypridle runs once from a single `exec_once`.

**Refinements after first use (2026-10-31).** The user found three problems. The dots touched: hyprlock's `dots_spacing` is the gap as a fraction of the dot size, and the generator had passed 0.12; it is now `dot_gap / dot_size` (0.88). The unlock felt slow: hyprlock's default animations are replaced by 0.2 s transitions for fade in, fade out and the field's colour, dot and fade changes (`[lock] motion`). The double-arrow resize cursor showed on the lock screen because MangoWM keeps the last cursor until the pointer moves; with the user's approval MangoWM now sets `cursor_hide_on_keypress=1`, hiding the pointer whenever you type, everywhere, as macOS does. `activate-lock.py` gained an in-place upgrade for a recognised previous appearance. A fresh password-unlock test on the real session passed before the update was applied.

## Polkit agent — activated — 2026-10-31

No authentication agent ran, so admin actions from the desktop (for example mounting some drives in Thunar) could not ask for a password. polkit-gnome was chosen over hyprpolkitagent, which would add Qt 6 and eleven packages and could not follow the GTK-based Rhapsody theme, and over mate-polkit, which adds the accountsservice system service and tray libraries. polkit-gnome is one GTK 3 package with no new dependencies; its dialog inherits adw-gtk3, the Limux named colours and Inter. `activate-polkit.py` adds one guarded `exec_once` and starts the agent; a real `pkexec true` showed the dialog and the user's password approved it. The user asked for the dialog to be on brand now rather than deferred. It is drawn from established patterns: the lock screen's flat field with an orange edge and caret, Files' graphite control for the default action with quiet text buttons, a hairline above the actions, and a new Limux outline padlock (`dialog-password`, added to the Limux-Rhapsody icon set) instead of the full-colour key. Scoping: the rules live in a private generated GTK theme, `Limux-Dialog`, which imports adw-gtk3; only the agent loads it, through `GTK_THEME` on its autostart, so other apps' dialogs are untouched while the user stylesheet's named colours still apply. Two preview bugs were fixed before activation: a general label rule hid the default button's text, and adw-gtk3's focus rule outranked the orange edge (`:focus-within` is not GTK 3 syntax and was dropped). The live dialog matched the preview and approved with the user's password.

## Desktop portals — screen sharing and file choosers — 2026-10-31

The user approved installing xdg-desktop-portal, -wlr and -gtk (MangoWM ships the matching `mango-portals.conf`) and asked that what they show be on brand. Screen sharing asks in the Limux picker ("Share your screen", "Built-in display" with `eDP-1` quiet beside it, orange selection), previewed before activation. GTK file choosers, previously unstyled even in Firefox, take the Files rules through `filechooser` selectors; portal file choosers float centred at 1100×700 through one MangoWM `window_rule` (MangoWM's syntax is `window_rule=is_floating:1,…,app_id:…`, found with its parser). The header bar's Cancel and Select first kept adw-gtk3's grey buttons: a `GTK_THEME` drop-in for the gtk portal had no effect, and a probe stylesheet showed the portal ignores `GTK_THEME`, so the drop-in was retired and the rules moved to the user stylesheet under `dialog headerbar`, which reaches only real dialog windows. The live chooser then showed quiet text buttons on the porcelain header bar with a hairline below. A restart of only the backends stranded the portal front end; activation now restarts it too.

**Screen-share fixes after the first real share (2026-10-31).** The first Firefox share failed with NotAllowedError: the wlr portal's service PATH is only `/usr/local/bin:/usr/bin`, so it could not find the chooser in `~/.local/bin`; the config now names it by absolute path. The working picker showed that MangoWM also offers individual windows, and that the portal's lines carry more than names: monitors add the make and model after the connector, windows end with a bracketed handle. The picker now shows "Built-in display" (or an external monitor's model) with "Screen", and each window by its title with "Window"; the connector name `eDP-1` meant nothing to the user and is no longer shown. The portal still receives its exact line back. `activate-portals.py` upgrades a recognised previous config or chooser in place.

## Clipboard history — activated — 2026-10-31

The user asked for clipboard history. cliphist (one package, depends only on wl-clipboard) records text and image copies through two `wl-paste --watch` watchers; cliphist 0.7 skips copies that password managers mark sensitive. The user chose memory-only storage (`$XDG_RUNTIME_DIR/limux/clipboard.db`, gone at logout) and 50 items. Command+Shift+V, free in MangoWM, opens the approved Limux picker ("Search clipboard"; each copy on one line with Text, Link or Image and its size in the quiet column); Enter copies the choice back, since no keystroke tool exists to paste it. The Command menu lists it under Everyday and offers Clear clipboard history in Utilities (a new `run` action), and now also lists Lock screen (Ctrl+Command+Q), which was missed when the lock screen was added. A preview with real copies matched the design before activation; `activate-clipboard.py` installs the helper, adds one validated autostart and binding, and starts the watcher; rollback wipes the history too.

**Command menu runs shortcuts (2026-10-31).** The user found that Enter on a shortcut row did nothing: rows built from MangoWM bindings were reference-only. Keyboard shortcut rows now run exactly what their key runs, `mmsg dispatch` with the binding's own action and arguments, or the binding's command for launchers. Gestures, mouse actions and Foot's in-terminal shortcuts stay reference-only, and so does Quit MangoWM, so a stray Enter cannot end the session. The menu closes first, so window actions apply to the window behind it. Column order now follows the row type (verb rows for snippets, quicklinks and utilities; key rows for shortcuts) instead of whether a row has an action, which the new actions would otherwise have swapped.

**Pickers close instantly (2026-10-31).** The user found that Escape on the launcher, Command menu and clipboard history felt slow and off. MangoWM closed every Rofi layer with an 800 ms zoom (`animation_duration_close`, shared with windows). The Rofi layer rule's close animation is now `none`, validated with MangoWM's parser, so a picker disappears on Escape; opening keeps its zoom and window animations are unchanged.
