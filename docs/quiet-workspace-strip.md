# Quiet Workspace Strip — approved current design and preview record

**Current status:** the user approved and activated this exact inset orange design. The preview procedure below documents the pre-activation comparison and expects the former module list; it is not a current activation command. The [architecture status table](architecture.md#current-implementation-and-approval-status--2026-10-30) and [engineering review](quiet-bar-engineering-review.md) describe current ownership and rollback.

The user preferred candidate B's workspace spacing but rejected its segmented surface and full-height active fill. The approved design keeps B's 30px bar and 7px workspace padding. Eight inactive workspace numbers sit on one uninterrupted porcelain surface; only the active number has a 30×22px orange fill, inset 4px above and below, with a 4px radius. `workspace_active` maps to approved `#D46A43`, with dark `signal_ink` text at 5.09:1 contrast.

## Renderer finding

In stock Mangobar 0.2.2, `paint_module()` paints every tag background from the bar's top through its full height. The stylesheet parser accepts `margin-top`, but the module painter does not use it. It does not support an inset tag fill. The stock compositor also fills only the middle region behind the modules; gaps around workspace raster slots therefore expose the desktop. That is why surface-coloured individual tags still looked like rectangles in the reviewed screenshot.

The revised preview used an isolated, minimally patched 0.2.2 build. [The build script](../scripts/quiet-mangobar-build.py) archives the pinned clean upstream commit and applies separate [T2 and visual patches](quiet-bar-engineering-review.md). The visual patch adds an explicit `background-inset` stylesheet property for tag fills and paints a full-width porcelain backing surface. Inactive tag backgrounds use native `background: none`; the backing surface shows through their slots and gaps. The CSS does not define a hover colour or any width/spacing override. The patch does not change tag hit areas or text baselines. The original system-managed binary and source tree remain untouched; the patched binary now runs from its isolated Limux path.

The historical preview JSONC copied the former live modules and commands, removed only the visible layout module and retained the 240px window-title limit. MangoWM layout switching remained available. Clock, window information, Wi-Fi, battery, volume and tray stayed in their positions.

## Preview in Foot

```sh
cd ~/limux && python3 scripts/quiet-bar.py preview
```

The command renders one CSS/JSONC pair, checks screenshot access, builds the isolated bar using the already installed Meson/Ninja and native libraries, captures before/candidate/hover images in ignored `build/quiet-workspace-strip/`, then closes only its preview process after 25 seconds. Ctrl+C closes it early. At the hover capture, roughly 10 seconds after startup, put the pointer over a workspace number. Move across all nine numbers and switch among occupied and empty workspaces while the preview is visible. Check that the orange fill has visible air above and below, inactive numbers have no tile edges, no slot or neighbour shifts, and the clock/status/title hierarchy remains quiet at 1.5 scaling. The second bar may overlap the live bar while open.

Native parser tests verified transparent inactive states, active inset, contrast and unchanged hover geometry. The patched binary builds and loads its generated config. The original preview's screenshot and pointer checks were later reviewed by the user before activation. Exiting that historical preview closed only its temporary bar.
