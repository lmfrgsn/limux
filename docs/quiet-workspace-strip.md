# Quiet Workspace Strip — one revised preview, pending review

The user preferred candidate B's workspace spacing but rejected its segmented surface and full-height active fill. This single revised preview keeps B's 30px bar and 7px workspace padding. Eight inactive workspace numbers sit on one uninterrupted porcelain surface; only the active number has a 30×22px orange fill, inset 4px above and below, with a 4px radius. The orange is a candidate-only `#D46A43`. Dark `signal_ink` text on it measures 5.09:1. No canonical selection semantic or live styling changes.

## Renderer finding

In stock Mangobar 0.2.2, `paint_module()` paints every tag background from the bar's top through its full height. The stylesheet parser accepts `margin-top`, but the module painter does not use it. It does not support an inset tag fill. The stock compositor also fills only the middle region behind the modules; gaps around workspace raster slots therefore expose the desktop. That is why surface-coloured individual tags still looked like rectangles in the reviewed screenshot.

The revised preview **uses an isolated, minimally patched 0.2.2 build**. [The build script](../scripts/quiet-mangobar-build.py) archives the pinned clean upstream commit and applies separate [T2 and visual patches](quiet-bar-engineering-review.md). The visual patch adds an explicit `background-inset` stylesheet property for tag fills and paints a full-width porcelain backing surface. Inactive tag backgrounds use native `background: none`; the backing surface shows through their slots and gaps. The CSS does not define a hover colour or any width/spacing override. The patch does not change tag hit areas or text baselines. The installed Mangobar binary and source tree are untouched. A reversible activation workflow is prepared but remains unexecuted pending the engineering and functional review.

The preview JSONC copies the live modules and commands, removes only the visible layout module and retains the previous candidate's 240px window-title limit. MangoWM layout switching remains available. Clock, window information, Wi-Fi, battery, volume and tray stay in their current positions and use the same rules as B.

## Preview in Foot

```sh
cd ~/limux && python3 scripts/quiet-bar.py preview
```

The command renders one CSS/JSONC pair, checks screenshot access, builds the isolated bar using the already installed Meson/Ninja and native libraries, captures before/candidate/hover images in ignored `build/quiet-workspace-strip/`, then closes only its preview process after 25 seconds. Ctrl+C closes it early. At the hover capture, roughly 10 seconds after startup, put the pointer over a workspace number. Move across all nine numbers and switch among occupied and empty workspaces while the preview is visible. Check that the orange fill has visible air above and below, inactive numbers have no tile edges, no slot or neighbour shifts, and the clock/status/title hierarchy remains quiet at 1.5 scaling. The second bar may overlap the live bar while open.

Native parser tests verify transparent inactive states, active inset, contrast and unchanged hover geometry. The patched binary builds and loads its generated config. The Codex sandbox cannot capture the live Wayland output, so actual visual and pointer inspection remains pending. Nothing has been permanently activated; exiting the preview restores the unchanged live bar automatically.
