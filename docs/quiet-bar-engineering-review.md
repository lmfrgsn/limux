# Quiet Workspace Strip — Mangobar engineering review

**Status:** visual direction approved after `ec2ba0f` and subsequently activated by the user. This document records the pre-activation engineering review; its pending language below is historical. The [architecture status table](architecture.md#current-implementation-and-approval-status--2026-10-30) records current ownership and rollback. The visual review itself changed no live files or startup entries.

## Upstream comparison

The retained repository points to official [Mangobar 0.2.2](https://github.com/mangowm/mangobar/releases/tag/0.2.2), commit `84f25a77706c31b49b865d08bc5429ca61115971`. The retained working tree was already dirty for Limux T2 reporting. The build now archives the **clean pinned commit**, then applies two separately versioned patches in order:

| Patch | Scope | Added / removed lines |
| --- | --- | ---: |
| [`01-limux-t2-metrics.patch`](../patches/mangobar/01-limux-t2-metrics.patch) | Existing local battery normalization against learned full capacity; volume rounding; opt-in metric logs | +20 / −1, one C file |
| [`02-quiet-workspace-strip.patch`](../patches/mangobar/02-quiet-workspace-strip.patch) | New `background-inset` style property for tag fills; inset background painting and cache identity; full-width porcelain backing behind transparent tag gaps | +25 / −8, three C files |

The visual patch does not change tag hit-test geometry, workspace switching, text baselines, module order, tray handling, audio control callbacks, battery measurement or Wi-Fi execution. The T2 patch was present in the retained source before the visual work; it is kept separate so an upstream update can be assessed independently. Both the installed and newly built binaries contain the local T2 metric strings. The build uses the already installed Meson/Ninja and native dependencies, requires no network or privileged install, and fails if the retained checkout is not the pinned commit or either patch cannot apply without fuzz.

## Why upstream configuration cannot make this appearance

Stock 0.2.2 parses `margin-top` but does not apply it to tag background painting. `paint_module()` draws every tag fill from `bar_top` through `bar_h`. Setting `background: none` on inactive workspaces exposes transparent gaps because the stock renderer fills the bar background only between the left and right module groups. CSS alone can provide either separate full-height coloured slots or a text-only active state; neither matches the approved inset button and uninterrupted surface. The visual patch supplies the missing renderer behaviours explicitly. A package-free configuration-only fallback would compromise the approved design, so none is proposed for activation.

The new property affects **tag background paint only**. It does not shrink clickable slots. In the approved candidate, the 30px bar uses B's spacing, and the active fill has a 4px vertical inset and 4px radius. The `#D46A43` fill used dark signal ink at 5.09:1 contrast at review time; the current approved label is pure white (see the [finishing changes](design-decisions.md#quiet-workspace-strip-finishing-changes--2026-10-30)). The global selection token and all other styling remain unchanged.

## Prepared activation and rollback

[`activate-quiet-bar.py`](../scripts/activate-quiet-bar.py) offers `check`, `activate` and `rollback`; **none has been run against the live session**. From Foot, `check` would verify one managed bar, no preview process, one canonical MangoWM startup entry, exact reviewed live-file hashes and the pinned build. `activate` would store the exact old launcher, config and CSS in a private 0700 recovery directory, install the patched binary at `~/.local/libexec/limux/mangobar-0.2.2-quiet/mangobar`, atomically replace the sole live config/CSS and the existing launcher binary path, then refresh the existing `limux-bar` process. It verifies one managed bar afterward and restores old bytes automatically if activation fails. It does **not** overwrite `~/.local/bin/mangobar`, any package-managed file, MangoWM config or the one `exec_once` line. `rollback` restores those exact bytes, refreshes the upstream bar, verifies one process, then removes the patched binary and recovery directory. A crash between file writes leaves the recovery directory for explicit rollback; atomic file replacements prevent partially written files.

The older `activate-mangobar.py` intentionally refuses the modified launcher while the Quiet Strip is active; use `activate-quiet-bar.py rollback` to return to the prior approved state. On a future upstream release, update the pinned commit, rebase the two small patches independently, rebuild, rerun tests and review the new native screenshots before changing the active binary. This is a continuing maintenance obligation: the patched binary does not automatically receive upstream bug or security fixes.

## Verified and pending

The source patches apply to clean pinned 0.2.2 without fuzz; the binary builds and identifies itself as `mangobar 0.2.2`; the generated config loads. Native parser tests cover transparent inactive states, the active inset, unchanged hover width/padding/radius and the absence of a hover override. The configuration diff retains nine tag names, click actions, clock, window, Wi-Fi, battery, volume and tray settings; only the visible layout module, title limit and bar appearance differ from the prior live baseline. An isolated file-transition test covers exact activation and rollback bytes. The sandbox has no live Wayland/process visibility, so these tests do **not** prove interaction.

Before activation, run `python3 scripts/quiet-bar.py preview --seconds 120` from Foot and check: click each workspace number 1–9, return to occupied workspaces, traverse all nine with the pointer and confirm no movement, check the title and clock update, inspect Wi-Fi and battery readings, change and mute volume using the existing controls, and open a tray menu. Close the preview and confirm `~/.local/bin/limux-bar status` reports one managed bar. After an eventual activation, repeat the same checks and use `activate-quiet-bar.py rollback` if any fail. The preview may have a competing tray watcher, so final tray verification must occur with the single active bar.

Proposing the full-width backing fix and vertical tag background inset upstream makes sense: both address general renderer limitations, and the visual patch is small. The property name and scope should be discussed with maintainers before submitting a PR. The separate T2 battery/volume patch is machine-specific and need not be bundled into that design proposal.
