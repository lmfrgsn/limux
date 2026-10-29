# Limux Commands — preview candidate

Limux Commands uses Rofi's approved Rhapsody theme, with only the heading and search placeholder changed for this picker. It is a new Limux utility, not a second application launcher. Command+Space and the existing Rofi configuration remain unchanged. The candidate is not activated on Command+K.

The Python registry reads the actual MangoWM config each launch. It lists recognized live keyboard, workspace, mouse and gesture bindings; unsupported actions are omitted rather than guessed. Foot's explicit clipboard shortcuts are read from its live config. Categories and descriptions are maintained in one action map in `scripts/limux-commands.py`; no second binding file is generated. Editing MangoWM or Foot is reflected on the next launch. Rofi provides fuzzy search and Escape dismissal. Shortcut rows are reference only; Enter on one does nothing.

Run from Foot in the MangoWM session:

```sh
cd ~/limux
python3 scripts/limux-commands.py check
python3 scripts/limux-commands.py preview
```

Search `workspace`, `swipe`, `⌘Space`, `Foot`, `Lorem`, or `Limux`. Use arrows and Enter. Escape closes the picker. Selecting Lorem or a snippet copies its text; paste it into Foot or another application to verify. Quicklinks open Home or this project with `xdg-open`. Date and UUID copy to the clipboard. The preview makes no startup or MangoWM configuration changes.

To add personal snippets, create `~/.config/limux/commands.toml` from `examples/commands.toml`, replace the dummy values, and run `chmod 600 ~/.config/limux/commands.toml`. Edit or delete entries in its `[snippets]` table; the next picker launch reads the changes. The file stays outside Git. Values are not displayed in Rofi, but copied text remains in the Wayland clipboard until replaced. Do not put passwords or secrets in snippets. The picker refuses a config readable by other users.

Command+K was checked against the actual MangoWM config and is free. After visual and interaction review, activation would add exactly one `bind=SUPER,k,spawn,...` entry to the existing `~/.config/mango/config.conf`, validate the complete file with MangoWM's native parser, then reload. Rollback removes that one entry and reloads. No activation script or permanent binding has been installed yet; review the preview first.

Automatic `;email` expansion is deferred. Espanso has a Wayland build, but compatibility with MangoWM and this keyboard/input setup has not been tested. A global expander observes keystrokes across applications and can access replacement text. Installing it would introduce an always-on service and potentially special input-device access; that needs a separate review before use. This picker only reads snippets when launched and uses the existing `wl-copy` clipboard tool.

## Refined information hierarchy — second preview

The first rows now show the most-used actions, followed by Snippets, Quicklinks and Utilities before the longer reference sections. Section labels are not selectable. Search also matches a section name such as `Workspaces` or `Gestures` through Rofi row metadata. Descriptions use the approved proportional Inter font; shortcut labels use a narrow monospace span at a fixed tab stop. Rofi's tab stops align text to the left of that position, so the shortcut span is padded to a common right edge. The native parser accepts this preview override. No approved theme file is edited. For a long description, search or select its row to see the full text in the `list` output if it is clipped on screen; the preview avoids adding long category prefixes to each row.

Firefox's [current shortcut guide](https://support.mozilla.org/en-US/kb/keyboard-shortcuts-perform-firefox-tasks-quickly) lists its search command as the accelerator plus K. This machine's Firefox profile explicitly sets `ui.key.accelKey = 91`, which maps the accelerator to Super/Command on Linux (see [Mozilla's bug discussion](https://bugzilla.mozilla.org/show_bug.cgi?id=2069698)). A global MangoWM `SUPER,k` would therefore override Firefox's Command+K search shortcut, as well as any web app shortcut on that key. `Ctrl+K` may still work as an alternative depending on Firefox's current handling, but is not established here by an interactive test. Command+K remains unassigned until this conflict is resolved explicitly.


## Third preview — shortcut visibility and private setup

The shortcut tab stop moved from 435 to 300 logical pixels. The longer spacing pushed the Pango shortcut span beyond Rofi's available row width, leaving an ellipsis. The description retains Inter; the key span remains DejaVu Sans Mono with spaces before it to align the key's right edge, including the longest verified hardware key labels. Section rows use Rofi's `nonselectable` row option and have no action mapped. Rofi's parser accepts the override. The Codex sandbox cannot connect to the compositor, so the final Rofi raster and actual key navigation need on-device review.

Create the private snippet file with dummy examples:

```sh
cd ~/limux
python3 scripts/limux-commands.py init-snippets
$EDITOR ~/.config/limux/commands.toml
python3 scripts/limux-commands.py preview
```

The command creates the directory with mode 700 and file with mode 600, and refuses to overwrite an existing file. Replace all dummy values before use. Search `email` to find `;email`, press Enter, then paste into Foot to check the clipboard. Also try `workspace`, `screenshot` and `lorem`; search metadata keeps section names searchable without repeating them on each row. Check that arrows skip section labels, Escape dismisses, and Command+Space still opens the normal application launcher.
