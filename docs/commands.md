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

Firefox's [current shortcut guide](https://support.mozilla.org/en-US/kb/keyboard-shortcuts-perform-firefox-tasks-quickly) lists **Ctrl+K** for focusing search on Linux and **Command+K** on macOS. On this Linux desktop, Limux's Command key is Super; a global `SUPER,k` would intercept Super+K before Firefox or any other application receives it. Firefox's standard Linux Ctrl+K would remain available, but custom Firefox or web-app uses of Super+K would lose that key. Command+K remains unassigned until you decide this tradeoff is acceptable.
