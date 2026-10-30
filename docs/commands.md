# Limux Commands — functional picker and design history

**Current status (2026-10-30):** Limux Commands is functional and bound to Command+K. Command+Space remains the application launcher. The user is not satisfied with its visual design: the redesign is **parked, not approved**. The private appearance marker `~/.local/state/limux/commands-appearance` is present and matches the neutral-v1 candidate hash, so Command+K currently renders the `[limux_commands_candidate]` styling. That styling is not a design decision. `python3 scripts/activate-commands-appearance.py rollback` removes only the marker and returns to the `[limux_commands]` styling; whether to do so is a separate choice.

The script retains native Rofi syntax and behaviour. The preview and approval notes below are history; earlier "approved" wording describes the state at that time.

The Python registry reads the actual MangoWM config each launch. It lists recognized live keyboard, workspace, mouse and gesture bindings; unsupported actions are omitted rather than guessed. Foot's explicit clipboard shortcuts are read from its live config. Categories and descriptions are maintained in one action map in `scripts/limux-commands.py`; no second binding file is generated. Editing MangoWM or Foot is reflected on the next launch. Rofi provides fuzzy search and Escape dismissal. Shortcut rows are reference only; Enter on one does nothing.

Run from Foot in the MangoWM session:

```sh
cd ~/limux
python3 scripts/limux-commands.py check
python3 scripts/limux-commands.py preview
```

Search `workspace`, `swipe`, `⌘Space`, `Foot`, `Lorem`, or `Limux`. Use arrows and Enter. Escape closes the picker. Selecting Lorem or a snippet copies its text; paste it into Foot or another application to verify. Quicklinks open Home or this project with `xdg-open`. Date and UUID copy to the clipboard. The preview makes no startup or MangoWM configuration changes.

To add personal snippets, create `~/.config/limux/commands.toml` from `examples/commands.toml`, replace the dummy values, and run `chmod 600 ~/.config/limux/commands.toml`. Edit or delete entries in its `[snippets]` table; the next picker launch reads the changes. The file stays outside Git. Values are not displayed in Rofi, but copied text remains in the Wayland clipboard until replaced. Do not put passwords or secrets in snippets. The picker refuses a config readable by other users.

Command+K was checked for conflicts and later activated with the user's approval. The guarded controller owns exactly one `SUPER,k` binding; rollback removes only that binding. Firefox's Command+K conflict was explicitly accepted.

Automatic `;email` expansion is deferred. Espanso has a Wayland build, but compatibility with MangoWM and this keyboard/input setup has not been tested. A global expander observes keystrokes across applications and can access replacement text. Installing it would introduce an always-on service and potentially special input-device access; that needs a separate review before use. This picker only reads snippets when launched and uses the existing `wl-copy` clipboard tool.

## Refined information hierarchy — second preview

The first rows show the most-used actions, followed by Snippets, Quicklinks and Utilities before the longer reference sections. Section labels are nonselectable. Search also matches section names through Rofi row metadata. Current shortcut rows use one plain-text run, `Action — ⌘Key`, in the approved proportional Inter row font. The preview widens only this picker to 700px; the approved application launcher remains 620px. Rofi receives no tabs, Pango spans or artificial spaces in command rows.

Firefox's [current shortcut guide](https://support.mozilla.org/en-US/kb/keyboard-shortcuts-perform-firefox-tasks-quickly) lists its search command as the accelerator plus K. This machine's Firefox profile explicitly sets `ui.key.accelKey = 91`, which maps the accelerator to Super/Command on Linux (see [Mozilla's bug discussion](https://bugzilla.mozilla.org/show_bug.cgi?id=2069698)). A global MangoWM `SUPER,k` would therefore override Firefox's Command+K search shortcut, as well as any web app shortcut on that key. `Ctrl+K` may still work as an alternative depending on Firefox's current handling, but is not established here by an interactive test. Command+K remains unassigned until this conflict is resolved explicitly.


## Fourth preview — complete shortcut labels

The earlier tab-stop design visibly clipped keys, including short ones, despite passing Rofi's theme parser. It has been replaced by a single-line action-first format. The formatted string sent to Rofi is inspectable with `python3 scripts/limux-commands.py list`; for example, `Open application launcher — ⌘Space`. The heading and row metadata remain. Rofi's native parser accepts the 700px width override. Automated tests assert the complete shortcut strings and absence of tabs/markup. This environment cannot connect to the Wayland compositor, so the actual Rofi rendering still requires on-device inspection.

Create the private snippet file with dummy examples:

```sh
cd ~/limux
python3 scripts/limux-commands.py init-snippets
$EDITOR ~/.config/limux/commands.toml
python3 scripts/limux-commands.py preview
```

The command creates the directory with mode 700 and file with mode 600, and refuses to overwrite an existing file. Replace all dummy values before use. Search `email` to find `;email`, press Enter, then paste into Foot to check the clipboard. Also try `workspace`, `screenshot` and `lorem`; search metadata keeps section names searchable without repeating them on each row. Check that arrows skip section labels, Escape dismisses, and Command+Space still opens the normal application launcher.

## Fifth preview — quieter section labels

The single-line command layout and 700px picker width are unchanged. Nonselectable section rows carry Rofi's `active` row flag solely as a style hook. A preview-only theme override gives those rows Inter 11 from the canonical Rhapsody font family, the `text_secondary` neutral colour, 2px top/1px bottom padding and 8px margin above. Rofi has no reliable letter-spacing control in this setup, so no tracking is added. The ordinary command row, yellow selection edge, pale-grey selected fill and recessed search field use the existing approved theme rules. This candidate remains a reversible preview; Command+K is unassigned.

From Foot, run `python3 ~/limux/scripts/limux-commands.py preview`. Check that headings feel quieter, arrow keys skip them, and the long shortcut labels remain complete. Escape dismisses the picker. Interactive rendering remains an on-device check because the development sandbox cannot connect to MangoWM's Wayland socket.

## Approved design and guarded activation

The user approved the fifth preview, including its exact visual design, and authorized Command+K despite Firefox's accelerator conflict. The picker theme override remains unchanged. The existing Command+Space launcher stays in the same MangoWM config. `scripts/activate-commands.py` owns only one exact `SUPER,k` binding; it checks for conflicts, validates the full candidate config with MangoWM's native parser, requires working compositor IPC before writing, reloads after an atomic replacement, and restores the previous bytes if reload or verification fails. Rollback removes that exact binding, preserving all unrelated settings.

Run from Foot in the live MangoWM desktop session:

```sh
cd ~/limux
python3 scripts/activate-commands.py check
python3 scripts/activate-commands.py activate
# Verify Command+K opens Commands and Command+Space still opens applications.
# If needed, undo just the Commands binding:
python3 scripts/activate-commands.py rollback
```

The Codex sandbox cannot reach the compositor IPC socket, so it cannot complete the live activation. Its attempted activation exited before writing. The full live config and candidate were parsed successfully; isolated activation/rollback tests passed. Visual and keypress checks must be done in Foot after activation.

Personal snippets and quicklinks share `~/.config/limux/commands.toml`, outside Git. `python3 scripts/limux-commands.py init-snippets` creates it with mode 600 and dummy examples, and refuses to overwrite an existing file. Edit `[snippets]` for copyable text and `[quicklinks]` for named HTTPS URLs or absolute paths. The picker rereads it each launch. Keep personal values only in that file.

## Live activation status — 2026-10-30

The sole live MangoWM config now contains one `SUPER,k` binding to Limux Commands and the original `SUPER,space` Rofi application binding. MangoWM's native parser accepts the live file. Limux Commands holds a nonblocking per-user lock for the duration of its Rofi picker, so repeated Command+K presses cannot open a second Commands instance. The approved Rhapsody theme override, command text, section styling, search behaviour, private snippets and quicklinks are unchanged. The personal config remains outside Git with mode 600.

The Codex sandbox can inspect the live config but cannot connect to the Wayland compositor. Its tests validate binding parsing, single-instance locking, section metadata, search terms, selection mapping, cancellation and clipboard invocation; actual keypresses and visual interactions must be checked in Foot: Command+K opens Commands; a second Command+K does not open another copy; arrows skip headings; typing `workspace`, `screenshot`, `lorem` or `email` filters; Escape closes; Enter on Lorem or a snippet copies text; Command+Space still opens the normal application launcher. To remove the binding, run `python3 ~/limux/scripts/activate-commands.py rollback` from Foot. Activation can be repeated with `activate`.

## Neutral Commands refinement — candidate, not approved

Historical record of the neutral-v1 candidate. Its marker has since been written, but the candidate was not approved and the redesign is parked; see the current status at the top of this page.

The user reviewed the first neutral candidate at `73ac56c` and requested two focused refinements. The selected row now uses a lighter cool-grey `commands_selection_cool` token (`#C7C7D2`) with graphite text and no yellow edge. Text contrast is 7.3:1; the fill differs 1.58:1 from the porcelain window, so focus visibility still needs screenshot review. EVERYDAY, SNIPPETS and other section headings use the same transparent background, quiet colour, 10px type and fixed spacing in normal, alternate and selected states. Rofi marks them nonselectable; hovering cannot give them the actionable row fill. The previously approved compact search, spacing, 700px width and complete single-line shortcut labels stay intact. The normal Command+Space launcher and current Command+K appearance remain unchanged.

Review it from Foot without changing a live file:

```sh
cd ~/limux
python3 scripts/limux-commands.py candidate
```

Escape closes the candidate. Command+K still opens the approved design. To capture a screenshot while the candidate is open, run this in Foot; the screenshot stays under Git-ignored `build/` and may contain private snippet *names*:

```sh
cd ~/limux
(sleep 3; grim build/limux-commands-candidate.png) &
python3 scripts/limux-commands.py candidate
```

Check the selected row, header hierarchy and full shortcut labels at the desktop's actual scale. Search `workspace`, `screenshot`, `lorem` and `email`; verify arrow navigation, nonselectable headings, Enter on Lorem or a nonprivate test snippet, and Escape. The candidate theme passes the installed Rofi 2.0 parser, but parser success does not prove pixels or keyboard interaction. The known missing `xdg-open` dependency affects quicklink launching in both the approved and candidate pickers; fixing it is separate functional work.

After visual approval, the prepared appearance controller can switch Command+K to the reviewed candidate without changing MangoWM bindings or the shared Rofi launcher theme:

```sh
cd ~/limux
python3 scripts/activate-commands-appearance.py check
python3 scripts/activate-commands-appearance.py activate
# Restore the current approved Commands appearance:
python3 scripts/activate-commands-appearance.py rollback
```

The controller writes only `~/.local/state/limux/commands-appearance`, an exact, private marker containing the reviewed candidate hash. It refuses unknown markers, a changed candidate, changed base Rofi styling, a different Command+K binding or an open Commands picker. The picker rejects a marker whose hash no longer matches its generated theme. Rollback removes the known marker even if source tokens later drift. No live theme file is copied and no application launcher, shortcut or hardware setting is changed. **Do not run `activate` until this refinement has been visually approved.**
