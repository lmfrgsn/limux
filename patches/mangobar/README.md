# Mangobar patches

These patches modify [Mangobar](https://github.com/mangowm/mangobar) 0.2.2 and are
licensed under the GNU General Public License version 3, Mangobar's own license,
not the MIT license that covers the rest of Limux.

| Patch | Change |
| --- | --- |
| `01-limux-t2-metrics.patch` | Battery percentage against the battery's current full charge, and volume readings, for the T2 MacBook |
| `02-quiet-workspace-strip.patch` | `background-inset`, so the active workspace can be an inset mark on one continuous bar |
| `03-hide-empty-custom-modules.patch` | Empty custom modules take no space |
| `04-spin-custom-modules.patch` | `spin-period`, rotating a custom module's glyph (the agent working spinner) |
| `05-icon-glyphs.patch` | Icon glyphs centred on the text's cap height, and `glyph-scale` for chosen glyphs |

`scripts/quiet-mangobar-build.py` applies them to the pinned upstream commit.
