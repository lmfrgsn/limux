# Limux design language — Rhapsody

This is the maintained design specification. Read alongside the [vision](vision.md), [architecture](architecture.md), [current implementation tokens](../themes/rhapsody.toml) and [decision log](design-decisions.md). Approved component states take precedence over earlier proposals; a new token or preview is not approval.

The [original reference specification](references/original-design-reference.md) is archived evidence, not a competing maintained specification. Its [original visual reference](references/braun-interface-concept.png) is a concept, not a capture of the working desktop or a pixel-perfect layout requirement.

![Original Limux concept: light bar, yellow active workspace, recessed launcher and material palette](references/braun-interface-concept.png)

## Current direction and influences

Limux is the desktop product and interaction model; Rhapsody is its first theme. Braun industrial design, especially the ET 66 by Dietrich Lubs and Dieter Rams, informs precise proportions, typography, alignment and purposeful colour. The approved direction is a contemporary, quiet workspace: clear hierarchy, stable geometry and restrained surfaces. Recesses or control depth are useful when they clarify interaction, not requirements to decorate every component. The desktop should not imitate a historical machine or turn every element into a calculator button.

Rhapsody expresses that foundation through complementary historical influences:

- Classic Macintosh Platinum: light system cohesion, compact information density and clear states.
- Apple Rhapsody: the transition from classic Macintosh personality to a modern developer-oriented system; cool, restrained, slightly technical character.
- NeXTSTEP: developer utility and deliberate hierarchy.

This is a contemporary reinterpretation, not a literal historical replica. Other themes may express different appearance while retaining Limux's functional precision and engineering principles.

## Material and colour hierarchy

The six initial Rhapsody foundation values remain documented baselines. The subsequent Braun exploration adds material roles and functional signals; it does not constitute a competing palette. Neither approximate screenshot samples nor current experimental tokens silently supersede those baselines.

| Initial Rhapsody role | Foundation value | Relationship to material language |
| --- | --- | --- |
| Canvas | `#DADAE3` | Cool grey system ground, with an almost imperceptible lavender undertone |
| Surface | `#F8F8FA` | Porcelain-like light, clean system and content surfaces |
| Chrome | `#EAE9F0` | Light structural system surfaces, distinguished from content and recessed controls |
| Accent | `#77768F` | Restrained general interface emphasis; not authority to make active workspaces violet |
| Text | `#343442` | Graphite-family readable ink |
| Dark developer surface | `#2F303B` | Graphite-family dark workbench |

The original concept explored the following material and signal roles. Its sample colours and yellow workspace remain historical reference, while the current token file and approved component states define today's implementation:

| Material or signal | Established role | Approximate sample recorded in original specification; proposed comparison only |
| --- | --- | --- |
| Porcelain | Light, clean application and system surfaces | `#F4F3F3` |
| Cool grey | Quiet backgrounds and chrome, barely lavender-tinted | `#DCDCE5` |
| Metal | Secondary and recessed surfaces, borders, control treatments and structural separation | `#A8A8B4` |
| Graphite | Dark surfaces, developer tools and technical depth | `#303039` |
| Signal yellow | Original active workspace; current Rofi list edge and ANSI yellow have separate roles | `#E3BE47` |
| Workspace orange | Approved active Quiet Workspace Strip control only | `#D46A43` |
| Signal green | Meaningful positive, connected, successful or functional status where justified | `#728858` |
| Signal red | Destructive actions, errors and urgent states | No agreed hex |

Lavender is quiet within the neutral greys. Signals are sparse and tied to a state. The active orange workspace and Foot cursor deliberately share the orange swatch through independent semantic mappings. The active workspace uses pure-white text, with a user-approved contrast exception of approximately 3.53:1 for this specific label; other text validation thresholds are unchanged. The yellow Rofi list edge, red urgency and terminal ANSI yellow serve separate purposes. Do not globally recolour these roles together.

The token file now names active workspace, list selection, terminal cursor and terminal search match separately. The old `selected` role is retained only for the recoverable boxed Mangobar renderer. Each mapping currently preserves approved output. Future colour changes need component previews and explicit approval. Verify contrast in light and dark contexts and retain non-colour cues where supported.

## Original concept and current components

Study the complete image, including its rationale and palette, before visual work:

- The image's light bar and yellow boxed workspaces explain the original concept. The approved live Mangobar uses nine plain numbers on one uninterrupted porcelain surface, with one small inset orange active control and no visible layout indicator.
- The approved Rofi launcher retains a recessed search field and compact rows. “RHAPSODY / 01” was rejected as decorative branding.
- The current Rofi list uses a pale-grey selected row with a narrow yellow edge. This is an approved baseline, open to a separate future colour review. Limux Commands inherits it and adds small nonselectable section labels; its next design task is separate.
- Controls, content and passive information are visibly different. Typography, boundaries and surface depth work together: porcelain foregrounds, cool neutral ground, metal-like recesses and graphite ink. Passive measurements should not become competing badges.

The screenshot is source context, not a layout target. Avoid gratuitous boxes, stripes, bevels, oversized controls, blur and gradients. Use depth only when it helps show interaction or material relationship.

## Typography, geometry and states

Typography is compact, readable and aligned; technical metadata is quieter than primary actions. Inter is the approved current bar and Rofi baseline, not a system-wide font commitment. Foot currently uses DejaVu Sans Mono. IBM Plex remains an unapproved future comparison. Check installed fonts and native rendering before changing them.

The live component geometries are approved individually; they are not universal spacing or radius rules. The original 1px edge and 4-unit rhythm are historical exploration. Preserve stable hover geometry, especially across all workspace states.

Keep focused, selected, hovered, occupied, empty, inactive, disabled and urgent meanings distinct where exposed. Empty workspaces are interactive, and hover must neither move controls nor erase the active state. Avoid boxing passive items.

## One coordinated light and dark system

Rhapsody is predominantly a light system environment with integrated dark developer tools:

| Light system components | Dark developer components |
| --- | --- |
| Mangobar, Rofi and MangoWM chrome currently; Mako and GTK/Thunar are future targets | Foot, terminal-based Codex and appropriate developer-oriented tools |

Light and dark components share hierarchy, alignment and contrast discipline. Dark developer surfaces belong to the porcelain-to-graphite system; the current Rofi launcher is light.

## Semantic ownership and migration

| Role | Current mapping | Owner and status |
| --- | --- | --- |
| Active workspace/navigation | `workspace_active` → `workspace_orange` (`#D46A43`); `on_workspace_active` → `pure_white` (`#FFFFFF`) | Approved Quiet Workspace Strip; white on orange is a narrow, documented contrast exception (~3.53:1); inset geometry is component-specific |
| Selected list row | `list_selected` → `signal_yellow` | Approved Rofi and Commands edge; visual reconsideration requires separate approval |
| Terminal cursor | `terminal_cursor` → `workspace_orange`; `on_terminal_cursor` → `signal_ink` | Approved Foot block cursor; semantic role is independent of workspace-active |
| Terminal match/URL | `terminal_match` → `signal_yellow` | Existing Foot search/URL presentation; review with Foot separately |
| Urgency/error and positive status | `urgent` → `signal_red`; `success` → `signal_green` | Red is used for supported urgent states; green is reserved where positive meaning is verified |
| Neutral emphasis | `emphasis` → `accent` | General non-signal emphasis; MangoWM focus currently refers to the neutral accent |
| Terminal ANSI | `[foot]` regular/bright and `[foot.colors]`/`[foot.blends]` | Terminal palette, including ANSI yellow; ANSI names do not dictate UI state colours |
| Historical boxed workspace | `selected` → `signal_yellow` | Kept only for the old Mangobar renderer and rollback evidence; not a current universal selection role |

The first migration step is complete: approved values are named by purpose, and active adapter output is generated from the tokens. Workspace and cursor roles may point to the same canonical colour while retaining independent mappings. The active-workspace white foreground exception is enforced only in the Mangobar adapter; other general contrast validation remains unchanged. The old boxed renderer and its guarded recovery hash remain. Later visual changes should alter only the relevant role mapping and recovery pins. Do not alter the six foundation colours to accomplish these reviews. Retire the legacy `selected` name only when the old renderer and rollback path have a reviewed replacement.

Approved repeated design constants belong in theme tokens: Commands picker width, visible row count and heading metrics now use `[limux_commands]`, while Rofi launcher metrics remain in `[rofi]` and the active bar geometry remains in `[mangobar_candidate]` for compatibility with its guarded activation. Native selector syntax, Rofi metadata, headings' nonselectability, search behaviour, shortcut parsing and clipboard actions belong in adapters. Literal application labels and text are content, not design tokens. Further tokenization should follow a real second use or an approved visual change.

## Architecture, review and approval boundaries

Use one canonical token file per theme and reviewed adapters generating native application styling. Separate functional settings from appearance. See [architecture](architecture.md) for actual ownership, supported behaviour and preview procedures. Current adapter limitations are implementation constraints, not permission to discard the design language. Verify installed application capabilities before promising borders, shadows, recesses or per-module typography.

Maintain one canonical active configuration per component, no stale packages/configurations, duplicate autostarts, orphan scripts or redundant backup clutter. Preserve shared dependencies; verify replacements before safely removing obsolete items. Use Git history for recovery. Preserve MangoWM, Mangobar module logic and startup, shortcuts, Command-key behaviour, workspaces, gestures, Foot interrupts, T2 audio, Touch Bar, keyboard lighting, trackpad, Wi-Fi, display and scaling configuration.

Before each future visual iteration:

1. Read this complete specification and inspect the original image, alongside the required project documents and current tokens.
2. Identify discrepancies and document proposed token, state and component changes. Obtain approval for unresolved final choices or changes to established identity/semantics; do not promote a preview to a permanent decision.
3. Generate supported styling from shared tokens, validate native formats and inspect real screenshots at native scale, including hover, focus, selected and urgent states. Check functional precision, subtle lavender, purposeful signals, depth, accessibility and light/dark cohesion.
4. Preserve behaviour and hardware. Live activation requires explicit authorization and a validated rollback path; a generated preview is not proof of visual approval.

The Quiet Workspace Strip, Rofi launcher, MangoWM appearance, Foot palette and Limux Commands are the current activated baselines. The approved Strip supersedes the older boxed yellow Mangobar appearance without deleting its recovery path. Activation, interactive verification limits and pending design work are recorded in the [architecture](architecture.md) and [decision log](design-decisions.md).
