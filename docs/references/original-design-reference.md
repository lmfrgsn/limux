> Archived source from `limux-design-reference.zip`, imported 2026-10-28. Historical reference, not a second maintained specification. The [canonical design language](../design-language.md) reconciles this source with project decisions. Source text is preserved below; only the image link was adjusted for its repository location.

# Limux and Rhapsody — Design Decisions and Visual Reference

**Purpose:** Preserve the full design concept agreed in conversation, including the actual visual reference, and distinguish established direction from implementation experiments. This document is a proposed authoritative reconciliation source for `~/limux/docs/design-language.md`, not an instruction to overwrite files blindly.

**Visual reference:** [`references/braun-interface-concept.png`](braun-interface-concept.png) — original screenshot from the Limux design discussion. Study the entire image, including the application launcher concept, the named Braun palette, and the surrounding design rationale. It is a *concept*, not a pixel-perfect implementation specification.

## 1. Identity hierarchy

- **Limux**: the overall Arch Linux + MangoWM desktop environment, core interaction model, engineering philosophy, and enduring design language.
- **Braun ET 66 / Dieter Rams / Dietrich Lubs**: the primary industrial-design influence for Limux itself, not a decorative afterthought or merely another visual theme.
- **Rhapsody**: Limux's first visual theme, drawing from late-1990s Apple Rhapsody, classic Macintosh Platinum (System 7–9) and NeXTSTEP. It expresses Limux's Braun-led philosophy through a cool, gently lavender-grey desktop with intentionally dark developer tools.

## 2. The specific visual idea that must not disappear

The supplied concept showed:

- A quiet, pale, precisely proportioned operating-system bar.
- A compact workspace switcher with small physical-button-like controls, where **one active workspace is signal yellow** and inactive workspaces are neutral. The image displays four workspaces as an *illustration*; actual Limux must preserve its configured workspace count and functionality.
- A light application launcher with a restrained structural border, small uppercase section label, and a **subtly recessed mid-grey search field** rather than a generic floating translucent panel.
- Legible, compact application rows, with **one meaningful yellow status/selection indicator** and quieter neutral alternatives.
- Minimal technical annotations and consistent alignment, not prominent decoration.
- A cool grey-lavender undertone so subtle that purple is perceived within the neutrals, **not presented as an obvious purple theme**.
- **Signal green and signal yellow** as purposeful functional accents, with red reserved for destructive actions and errors.

The tactile inspiration is an abstraction of Braun's intelligently laid-out instrument panels: porcelain-like light surfaces, metal-like greys, shallow recesses, precise borders and differentiated controls. Do **not** turn every item into a calculator key or add heavy skeuomorphism.

## 3. Named Limux identity palette — from the visual reference

These six **roles and their relative appearance** are part of the concept. Approximate RGB samples taken from the screenshot (not independently approved production colour tokens) are included solely to help compare the screenshot against the theme:

| Identity role | Approx. screenshot sample | Intended use |
| --- | --- | --- |
| Porcelain | `#F4F3F3` | Light, clean foreground/application surfaces |
| Cool grey | `#DCDCE5` | Quiet lavender-cast system ground and chrome |
| Metal | `#A8A8B4` | Mid-grey structural details, recessed control surfaces and separation |
| Graphite | `#303039` | Text, technical depth, dark development surfaces |
| Signal green | `#728858` | Positive/connected/successful states where appropriate |
| Signal yellow | `#E3BE47` | Active selection/attention/meaningful emphasis (e.g. selected workspace) |

**Signal red** is reserved for errors, danger and destructive actions; no definitive red hex was agreed.

Do not automatically replace the existing Rhapsody foundation values. Earlier tokens were:

- Canvas `#DADAE3`
- Light surface `#F8F8FA`
- Chrome `#EAE9F0`
- Slate-lavender accent `#77768F`
- Text `#343442`
- Dark developer surface `#2F303B`

These earlier values and the Braun reference palette are **not competing themes**. The values are close for several neutral roles; the critical correction is that the previously overlooked *yellow/green functional signals, neutral physical material hierarchy, and subtle-only lavender* are essential. Map material roles, semantic tokens and theme-specific values carefully. Identify and propose any discrepancies rather than silently replacing established values or turning the lavender accent into the principal active-state highlight.

## 4. Deliberate light/dark design

- Predominantly **light**: MangoWM window presentation, Mangobar, Rofi, Mako, Thunar and compatible GTK UI.
- Deliberately **dark**: Foot, terminal-based Codex and appropriate developer tools, using the graphite/charcoal family.
- They must feel related through typography, geometry, borders, spacing and shared semantic signals. The goal is a coherent system, not one global theme that makes everything the same colour.

## 5. Typography, controls and hierarchy

- Precise, compact, readable typography. IBM Plex Sans and IBM Plex Mono were proposed; Inter was later tried but **not agreed as final**.
- Delicate 1px edges and low, purposeful dimensionality: slightly raised controls versus subtly recessed fields.
- Functional hierarchy: quiet status text, prominent available controls when needed, unmistakable active state.
- Avoid generic Linux status-bar badges, excessive pills/rounding, glowing accents, blurred transparent layers, gradients, noisy skeuomorphism, or decorating every element with green/yellow.
- Rhapsody should feel like a *quiet, well-engineered instrument panel*, not merely a lavender recolour.

## 6. Engineering and ownership rules

- A canonical `themes/rhapsody.toml` defines tokens; application-specific adapters generate styling supported by the **installed** component versions.
- Separate appearance from application behaviour and T2-specific hardware config. Preserve MangoWM keyboard mappings, gestures, window and workspace behaviour; Mangobar module logic; functioning battery and audio reporting; Foot terminal interrupts; Wi-Fi, Touch Bar, keyboard lighting and 1.5x scaling.
- One canonical active config per component; no stale Waybar, duplicate autostarts, orphan scripts, abandoned dependencies or accumulating backup files. Validate, test a reversible preview, then remove obsolete things safely. Use local Git for recovery.
- Treat the attached visual as a design decision reference, not a screenshot of the current desktop. Confirm actual results by inspecting renders/screenshots.

## 7. Agreed vs. still open

**Established:** Names; Braun ET 66 industrial philosophy; precise/tactile/recessed restraint; porcelain/cool grey/metal/graphite neutral hierarchy; subtle lavender as undertone; semantic yellow and green (red for danger); largely light OS with integrated dark developer tools; classic Macintosh Platinum / Apple Rhapsody / NeXTSTEP references; canonical theme tokens; separation from behaviour and hardware; cleanliness.

**Still open:** Exact final hex values for the reconciled palette; which individual statuses merit yellow/green; final typography; component dimensions/radii; precise native styling feasible in Mangobar/MangoWM/Rofi/Foot/GTK. Implementations should be proposed, visually reviewed and refined without overwriting the agreed philosophy.

## 8. Review criteria for every future visual iteration

1. Does it **visibly** communicate Braun's functional precision instead of merely changing colours?
2. Is the lavender an undertone rather than a conspicuous main accent?
3. Are yellow/green used **purposefully**, with a clear active or system-state role?
4. Do light system components and dark developer tools look designed together?
5. Are raised/recessed cues and control affordances subtle but legible?
6. Does it preserve all operational behaviour, accessible focus/contrast and keyboard usability?
7. Is the implementation maintainable from one source of truth without stale config?

Before more styling, reconcile existing `AGENTS.md`, `docs/vision.md`, `docs/design-language.md`, `docs/architecture.md` and `themes/rhapsody.toml` against this source and the actual screenshot. Document conflicts and proposed resolution, preserve working settings, and ask for approval before changing the agreed identity or permanently activating a new design.
