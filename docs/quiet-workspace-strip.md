# Quiet Workspace Strip — filled active workspace, preview only

These are three refinements of the selected Limux direction for **Mangobar 0.2.2**. The nine workspaces remain plain numbers; only the active number has a compact orange fill. The porcelain background, quiet title, centered clock and status area are shared. The preview config removes the visible layout module, while MangoWM's `SUPER,n` layout switching remains intact. It retains the live workspace, tray, network, battery and volume configuration. No candidate is activated.

| Candidate | Bar height | Workspace padding | Active radius | Active fill | Contrast with porcelain text |
| --- | ---: | ---: | ---: | --- | ---: |
| A — Compact | 26px | 4px | 2px | `#AD492F` | 5.25:1 |
| B — Balanced | 30px | 7px | 3px | `#AD492F` | 5.25:1 |
| C — Softer | 30px | 7px | 3px | `#A55A43` | 4.78:1 |

The values are candidate-only tokens in `themes/rhapsody.toml`. The approved global yellow selection semantic and live CSS do not change. Mangobar paints a workspace background at the full bar height; its CSS subset does not provide a reliable vertical inset. The filled active shape therefore uses the bar height, with a small corner radius rather than a pill. The original Braun reference supports the restrained fill as a purposeful state marker, while the running bar's boxed workspaces and `Layout T` compete with the information in the strip. B is the provisional recommendation: it keeps the current 30px status-bar height and makes the active number easier to scan without changing the status hierarchy. A is tighter; C has the same geometry as B with a quieter signal. This recommendation needs the on-device screenshots below before approval.

## Stable hover geometry

The previous shifting came from the native implementation: after CSS loading, Mangobar sets every workspace state's minimum width from bar height and margins, but a CSS `min-width` can be reapplied by the hover overlay. These candidate rules omit `min-width` and do not define a hover selector. Every workspace state has identical padding and margins, and only the active state changes colour and radius. Native parser tests cover empty, inactive, occupied, active and urgent states, plus hover overlays. Visual pointer checks are still required.

## Native previews

From Foot in the MangoWM session, run each command separately:

```sh
cd ~/limux && python3 scripts/quiet-bar.py preview --variant A
cd ~/limux && python3 scripts/quiet-bar.py preview --variant B
cd ~/limux && python3 scripts/quiet-bar.py preview --variant C
```

Each invocation renders token-derived CSS and a temporary JSONC config under ignored `build/quiet-workspace-strip/`, captures the current desktop, starts a second native Mangobar for 25 seconds, captures the candidate and a hover frame, then stops only that preview process. Put the pointer over a workspace number before the hover capture at about 10 seconds. While the preview is visible, move across all nine numbers, switch between occupied and empty workspaces, and check that no slot or neighbour moves. Compare the active shape, number spacing, title and status alignment, contrast, and balance against the light desktop and graphite Foot at 1.5 display scaling. The second bar may overlap the live one during capture; Ctrl+C closes it early. Repeating a command regenerates the same candidate files.

The Codex sandbox cannot access the Wayland session, so it cannot capture or judge these new real frames. Native CSS parsing and tests pass; final visual approval remains with the user after running these previews. Rollback of a preview is automatic when its command exits. No live files are replaced.
