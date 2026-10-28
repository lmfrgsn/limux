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
