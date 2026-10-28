# Rhapsody: instrument panel direction

Status: candidate 1, awaiting actual Wayland screenshot review. The saved migration screenshot is historical evidence, not a capture of the current desktop. It shows uniform workspace tiles and a prominent layout badge competing for attention. The initial adapter also gave urgent and active workspaces identical treatment, and requested IBM Plex Sans despite that font being absent (fontconfig selected DejaVu Sans).

## Shared visual language

Use a continuous cool chrome surface for system infrastructure, pale paper surfaces for content, and charcoal for developer tools. Avoid floating pills, decorative gradients, oversized rounding and historical ornamental bevels. The Macintosh influence should live in clarity and hierarchy; Braun in restraint and meaningful states; NeXTSTEP in compact structure.

Use installed Inter at 13 logical pixels for the first bar candidate. Evaluate IBM Plex later as an explicit system-wide typography experiment. Do not silently rely on font fallback. A 4-unit spacing rhythm, 8-unit internal spacing and 12–16-unit group separation are the broader direction. Geometry remains compact and squared; popup corners may soften to 3 units. Borders should define boundaries, not surround every status item.

Primary ink identifies actions and current information; secondary ink marks context, quiet ink empty workspaces. A deep grey-violet selection anchors the current workspace. Reserve warm oxide for urgency rather than routine volume or battery values. Hover is a light surface change. Disabled states must remain distinguishable from merely inactive or empty states; the current bar exposes empty, occupied, active and urgent states, not a universal disabled state.

## Component expressions

- Mangobar: one instrument rail. Empty workspaces recede; occupied workspaces use primary ink without boxes; active gets one solid selection. Layout and title are secondary. Clock and system measurements stay clear. No generic CSS border-width, shadows or per-module font-size assumptions: Mangobar 0.2.2 has global typography and restricted surface styling. Menu borders are supported.
- MangoWM: future focused border in the same selection family, restrained inactive border; preserve all behaviour and animation settings until separately reviewed.
- Rofi: future paper-like search panel, structured result rows and the same selection language; current approved design remains live.
- Foot: dark workbench using the same spacing and semantic accent family; do not change terminal keybindings or existing typography during this bar experiment.
- Notifications: compact paper surfaces, clear source/message hierarchy, warm accent only for urgency.
- GTK/Thunar: consistent content/chrome distinction and selected-state semantics via a compatible GTK theme, never simulated through unsupported application CSS.

## Iteration procedure

Run `python3 scripts/preview-mangobar.py` from Foot in the desktop session. It generates CSS, captures before.png, starts only a temporary second bar, captures candidate.png, and closes that process after 20 seconds (or Ctrl+C). The running original remains untouched. A second tray watcher may be unavailable; duplicate bars can affect available window area. Screenshots are private build artifacts excluded from Git.

Review actual screenshots at native scale: workspace distinction, legibility, baseline alignment, density, title/status balance and hover/urgent states. The first automated capture only captures the current state; interactive states need additional captures. Do not call the design polished or verified until those images have been inspected. Refine tokens and adapter from that evidence, regenerate and capture again. No live apply is part of this iteration.
