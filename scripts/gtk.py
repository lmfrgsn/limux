"""Limux Files adapter: GTK 3 stylesheet, outline icon theme and Thunar 4.20
view settings. Appearance and view presentation only; no shortcuts or actions."""
import re
from mangobar import contrast

# Inner marks drawn once on a 16px grid and scaled for the 64px icons.
GLYPHS = {
    'text': 'M5.5 8h5M5.5 10h5M5.5 12h3',
    'image': 'M5 12.5l2.25-2.75 1.75 1.75 1.25-1.25 1.75 2.25M9.75 7.5h.01',
    'archive': 'M7 3.5v1M7 5.75v1M7 8v1M6 10.25h2v2H6z',
    'audio': 'M9.5 11.5V7.25l2 .75M9.5 11.5a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0z',
    'video': 'M7 8.25v4l3.25-2z',
    'code': 'M6.75 8.5 5.25 10l1.5 1.5M9.25 8.5l1.5 1.5-1.5 1.5',
    'sheet': 'M5 8.5h6v4H5zM5 10.5h6M8 8.5v4',
    'slides': 'M5 8.5h6v3.5H5z',
}
# Drawn icon -> (context, glyph, standard names that resolve to it before Adwaita's).
ICONS = {
    'folder': ('places', None, ['folder-documents', 'folder-download', 'folder-pictures', 'folder-music',
                                'folder-videos', 'folder-templates', 'folder-publicshare', 'user-desktop',
                                'inode-directory']),
    'document': ('mimetypes', None, ['application-x-generic']),
    'text': ('mimetypes', 'text', ['text-x-generic', 'text-plain', 'text-markdown', 'x-office-document',
                                   'application-pdf', 'application-vnd.oasis.opendocument.text']),
    'image': ('mimetypes', 'image', ['image-x-generic', 'image-png', 'image-jpeg', 'image-gif', 'image-webp',
                                     'image-svg+xml']),
    'archive': ('mimetypes', 'archive', ['package-x-generic', 'application-zip', 'application-x-tar',
                                         'application-x-compressed-tar', 'application-x-7z-compressed']),
    'audio': ('mimetypes', 'audio', ['audio-x-generic']),
    'video': ('mimetypes', 'video', ['video-x-generic']),
    'code': ('mimetypes', 'code', ['text-x-script', 'text-x-python', 'application-x-shellscript', 'text-x-csrc',
                                   'text-x-chdr', 'application-json', 'text-html', 'text-css']),
    'sheet': ('mimetypes', 'sheet', ['x-office-spreadsheet', 'application-vnd.oasis.opendocument.spreadsheet',
                                     'text-csv']),
    'slides': ('mimetypes', 'slides', ['x-office-presentation', 'application-vnd.oasis.opendocument.presentation']),
}
TOOLBAR = ('menu:0,back:1,forward:1,open-parent:0,open-home:0,new-tab:0,new-window:0,toggle-split-view:0,'
           'undo:0,redo:0,zoom-out:0,zoom-in:0,zoom-reset:0,view-as-icons:0,view-as-detailed-list:0,'
           'view-as-compact-list:0,view-switcher:0,location-bar:1,reload:0,search:1')


def palette(theme):
    t, colors = theme['thunar'], theme['colors']
    c = {}
    for role, name in t.items():
        if role in ('gtk_theme', 'icon_theme', 'hairline_alpha'):
            continue
        value = colors[name]
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
            raise ValueError(f'invalid Thunar colour: {role}')
        c[role] = value.upper()
    for ink, surface in [('text', 'surface'), ('secondary', 'surface'), ('quiet', 'surface'),
                         ('on_selected', 'selected'), ('on_selected_inactive', 'selected_inactive'),
                         ('text', 'hover'), ('text', 'field'), ('on_controls', 'controls')]:
        if contrast(c[ink], c[surface]) < 4.5:
            raise ValueError(f'insufficient Thunar contrast: {ink} on {surface}')
    return c


def _rgb(value):
    return ', '.join(str(int(value[i:i + 2], 16)) for i in (1, 3, 5))


def interface_font(theme):
    t = theme['typography']
    if not re.fullmatch(r'[\w .-]+', t['sans']) or type(t['ui_size']) is not int or not 8 <= t['ui_size'] <= 16:
        raise ValueError('invalid interface typography')
    return t['sans'], t['ui_size']


def render_css(theme):
    t, c = theme['thunar'], palette(theme)
    font, size = interface_font(theme)
    alpha = t['hairline_alpha']
    if type(alpha) not in (int, float) or not 0 < alpha < 0.5:
        raise ValueError('invalid Thunar hairline alpha')
    hair = f'rgba({_rgb(c["text"])}, {alpha})'
    defines = {
        'window_bg_color': 'surface', 'window_fg_color': 'text', 'view_bg_color': 'surface',
        'view_fg_color': 'text', 'sidebar_bg_color': 'surface', 'sidebar_fg_color': 'text',
        'sidebar_backdrop_color': 'surface', 'headerbar_bg_color': 'surface',
        'headerbar_fg_color': 'text', 'headerbar_backdrop_color': 'surface', 'card_bg_color': 'surface',
        'card_fg_color': 'text', 'popover_bg_color': 'surface', 'popover_fg_color': 'text',
        'dialog_bg_color': 'surface', 'dialog_fg_color': 'text', 'accent_bg_color': 'controls',
        # Thunar fills a selected grid item with these when file highlighting is on (needs gvfs).
        'theme_selected_bg_color': 'selected', 'theme_unfocused_selected_bg_color': 'selected_inactive',
        'accent_fg_color': 'on_controls', 'accent_color': 'focus', 'destructive_bg_color': 'destructive',
    }
    lines = ['/* Generated by Limux from themes/rhapsody.toml ([thunar]). Do not edit;',
             ' * scripts/activate-gtk.py owns this file. Named colours apply to all GTK 3',
             ' * apps; layout rules are scoped to Thunar windows. */', '']
    lines += [f'@define-color {name} {c[role]};' for name, role in defines.items()]
    lines += [f'@define-color sidebar_border_color {hair};', f'@define-color sidebar_shade_color {hair};', '']
    lines.append(f'''window.thunar {{ font-family: "{font}"; font-size: {size}pt; }}

.thunar menubar {{ background: {c["surface"]}; box-shadow: none; border: none; padding: 0 7px; min-height: 30px; }}
.thunar menubar > menuitem {{ color: {c["secondary"]}; padding: 0 9px; min-height: 30px; }}
.thunar menubar > menuitem:hover {{ color: {c["text"]}; background: {c["hover"]}; }}

.thunar toolbar {{ background: {c["surface"]}; border: none; border-bottom: 1px solid {hair}; padding: 6px 12px 6px 8px; }}
.thunar toolbar button {{ background: none; border: none; box-shadow: none; color: {c["text"]};
  min-height: 28px; min-width: 28px; border-radius: 4px; }}
.thunar toolbar button:hover {{ background: {c["hover"]}; }}
.thunar toolbar button:disabled {{ color: {c["disabled"]}; }}

/* The path is text: ancestors quiet, current folder in 600. */
.thunar .path-bar, .thunar .path-bar.linked {{ background: none; border: none; box-shadow: none; }}
.thunar .path-bar .location-button, .thunar .path-bar .path-bar-button {{ background: none; border: none;
  box-shadow: none; border-radius: 4px; color: {c["quiet"]}; font-weight: 400; padding: 0 6px; min-height: 28px; }}
.thunar .path-bar .location-button:checked {{ color: {c["text"]}; font-weight: 600; background: none; }}
.thunar .path-bar .location-button:hover {{ background: {c["hover"]}; }}

/* Text fields are flat with a metal edge; while typing, the edge and caret are orange. */
.thunar entry, .thunar treeview entry {{ background: {c["field"]}; color: {c["text"]};
  border: 1px solid {c["field_edge"]}; box-shadow: none; border-radius: 4px; min-height: 26px;
  caret-color: {c["caret"]}; }}
.thunar entry:focus {{ border-color: {c["field_focus"]}; box-shadow: inset 0 0 0 1px {c["field_focus"]}; }}

/* Sidebar shares the surface; the current location is a quiet mark. */
.thunar .sidebar, .thunar .sidebar .view {{ background: {c["surface"]}; }}
.thunar .sidebar {{ border-right: 1px solid {hair}; }}
.thunar .sidebar .view:selected, .thunar .sidebar .view:selected:focus,
.thunar .sidebar .view:selected:backdrop {{ background: {c["location"]}; color: {c["text"]}; }}

/* Column headings are quiet labels, not buttons. */
.thunar .standard-view treeview header button {{ background: {c["surface"]}; border: none;
  border-bottom: 1px solid {hair}; box-shadow: none; color: {c["quiet"]};
  font-size: {size - 1}pt; font-weight: 500; padding: 6px 12px; }}
.thunar .standard-view treeview.view:hover {{ background: {c["hover"]}; }}

/* Selection: graphite in the active window, metal when inactive. */
.thunar .standard-view .view:selected, .thunar .standard-view .view text:selected {{
  background: {c["selected"]}; color: {c["on_selected"]}; }}
.thunar .standard-view .view:selected:backdrop, .thunar .standard-view .view text:selected:backdrop {{
  background: {c["selected_inactive"]}; color: {c["on_selected_inactive"]}; }}
.thunar .standard-view treeview.view:selected {{ border-radius: 0; }}
.thunar .standard-view .view:not(treeview):selected,
.thunar .standard-view .view:not(treeview) text:selected {{ border-radius: 4px; }}

/* Measurements are quiet text at the edge. */
.thunar statusbar {{ background: {c["surface"]}; border-top: 1px solid {hair}; color: {c["quiet"]};
  font-size: {size - 1}pt; padding: 0 10px; min-height: 26px; }}

/* Frequent interactions respond instantly. */
.thunar button, .thunar .view, .thunar menuitem {{ transition: none; }}
''')
    return '\n'.join(lines)


def render_icons(theme):
    """Return ({relative path: bytes}, {relative alias: target}) for the icon theme."""
    c = palette(theme)
    shapes = {
        16: (1.25, '<path d="M1.75 4.25v8a1 1 0 0 0 1 1h10.5a1 1 0 0 0 1-1v-6.5a1 1 0 0 0-1-1H7.6L6.1 3.25H2.75a1 1 0 0 0-1 1z" fill="{fill}" {stroke}/>',
             '<path d="M4 1.75h4.9l3.1 3.1v8.4a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2.75a1 1 0 0 1 1-1z" fill="{fill}" {stroke}/>'
             '<path d="M8.75 1.9v3.1h3.1" fill="none" {stroke}/>'),
        64: (2.5, '<path d="M8 17.5v31a3.5 3.5 0 0 0 3.5 3.5h41a3.5 3.5 0 0 0 3.5-3.5v-25a3.5 3.5 0 0 0-3.5-3.5H30.5L25 14H11.5A3.5 3.5 0 0 0 8 17.5z" fill="{fill}" {stroke}/>',
             '<path d="M17.5 8H37l11 11v33.5a3.5 3.5 0 0 1-3.5 3.5h-27a3.5 3.5 0 0 1-3.5-3.5v-41A3.5 3.5 0 0 1 17.5 8z" fill="{fill}" {stroke}/>'
             '<path d="M36.5 8.5V19.5h11" fill="none" {stroke}/>'),
    }
    files, links = {}, {}
    for size, (width, folder_svg, document_svg) in shapes.items():
        directory = '16' if size == 16 else 'scalable'
        stroke = f'stroke="{c["icon_stroke"]}" stroke-width="{width}" stroke-linejoin="round"'
        scale = size // 16
        for base, (context, glyph, aliases) in ICONS.items():
            body = (folder_svg if base == 'folder' else document_svg).format(
                fill=c['icon_folder' if base == 'folder' else 'icon_document'], stroke=stroke)
            if glyph:
                body += (f'<g transform="scale({scale})"><path d="{GLYPHS[glyph]}" fill="none" '
                         f'stroke="{c["icon_stroke"]}" stroke-width="{1.1 if scale == 1 else 0.6}" '
                         'stroke-linecap="round" stroke-linejoin="round"/></g>')
            files[f'{directory}/{context}/{base}.svg'] = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
                f'viewBox="0 0 {size} {size}">{body}</svg>\n').encode()
            links.update({f'{directory}/{context}/{alias}.svg': f'{base}.svg' for alias in aliases})
    sections = [('16/places', 16, 'Places', 'Fixed'), ('16/mimetypes', 16, 'MimeTypes', 'Fixed'),
                ('scalable/places', 64, 'Places', 'Scalable'), ('scalable/mimetypes', 64, 'MimeTypes', 'Scalable')]
    index = ['[Icon Theme]', f'Name={theme["thunar"]["icon_theme"]}',
             'Comment=Limux outline file icons generated from Rhapsody tokens', 'Inherits=Adwaita,hicolor',
             'Directories=' + ','.join(name for name, *_ in sections), '']
    for name, size, context, kind in sections:
        index += [f'[{name}]', f'Size={size}', f'Context={context}', f'Type={kind}']
        if kind == 'Scalable':
            index += ['MinSize=17', 'MaxSize=512']
        index.append('')
    files['index.theme'] = '\n'.join(index).encode()
    return files, links


def thunar_settings(theme):
    """Thunar view presentation (xfconf channel 'thunar'): name -> (type, value)."""
    palette(theme)
    return {
        'last-toolbar-items': ('string', TOOLBAR),
        'last-location-bar': ('string', 'ThunarLocationButtons'),
        'last-details-view-visible-columns': ('string', 'THUNAR_COLUMN_NAME,THUNAR_COLUMN_SIZE,THUNAR_COLUMN_DATE_MODIFIED'),
        'misc-symbolic-icons-in-sidepane': ('bool', 'true'),
        'misc-small-toolbar-icons': ('bool', 'true'),
        'shortcuts-icon-size': ('string', 'THUNAR_ICON_SIZE_16'),
        'misc-date-style': ('string', 'THUNAR_DATE_STYLE_CUSTOM_SIMPLE'),
        'misc-date-custom-style': ('string', '%-d %b %Y'),
        'misc-file-size-binary': ('bool', 'false'),
    }


def gsettings(theme):
    """System GTK settings (org.gnome.desktop.interface): key -> value."""
    t = theme['thunar']
    for key in ('gtk_theme', 'icon_theme'):
        if not re.fullmatch(r'[\w.-]+', t[key]):
            raise ValueError(f'invalid Thunar {key}')
    font, size = interface_font(theme)
    return {'font-name': f'{font} {size}', 'icon-theme': t['icon_theme'], 'gtk-theme': t['gtk_theme']}


def render(theme):
    return render_css(theme)
