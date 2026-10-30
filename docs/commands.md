# Limux Commands — approved current picker and preview history

Limux Commands uses Rofi's approved Rhapsody theme and is activated on Command+K. Command+Space remains the application launcher. Approved picker width, visible row count and small heading metrics are in `[limux_commands]` tokens; the script retains native Rofi syntax and behaviour. The early preview notes below document how this design evolved. The [live activation status](#live-activation-status--2026-10-30) is authoritative.

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
