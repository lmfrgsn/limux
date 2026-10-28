# Design decisions and implementation audit

Recorded 2026-10-28. The [design language](design-language.md) is the sole maintained design specification; this log records status, rationale and discrepancies. Evidence: [original source](references/original-design-reference.md), [original image](references/braun-interface-concept.png), [tokens](../themes/rhapsody.toml), [Mangobar adapter](../scripts/mangobar.py), and locally inspected generated `build/rhapsody/mangobar.css` (ignored, reproducible output).

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
