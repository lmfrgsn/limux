#!/usr/bin/env python3
"""Build an isolated Mangobar 0.2.2 preview with tag background inset support.

The installed binary and retained upstream source are never modified. Exact
source hashes make an upstream change fail closed instead of patching blindly.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / '.local/state/limux/bar-migration/sources/mangobar'
OUT = ROOT / 'build/quiet-workspace-strip'
COPY = OUT / 'mangobar-source'
BUILD = OUT / 'mangobar-build'
HASHES = {
    'mangobar.c': '947e70edfbf69f0bb4a65a93ee0db5dad290abee14a22b58b5fa79522fa27194',
    'style.c': 'e6c01f2796aece2d942e8c2444ba89406d341beabc7ebb2d4b066fc5754c7f77',
    'style.h': '42e01bbe80bf290f1ba9ac8c37edd57dbe5b4142b913ab0f5efa217637567c27',
}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'expected one source match, found {text.count(old)}: {old[:60]}')
    return text.replace(old, new, 1)


def patched_sources():
    for name, expected in HASHES.items():
        actual = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Mangobar {name} differs from retained 0.2.2 source')

    header = (SOURCE / 'style.h').read_text()
    header = replace_once(header, '    int min_width; // minimum module width\n',
                          '    int min_width; // minimum module width\n'
                          '    int background_inset; // preview: vertical background inset\n')
    header = replace_once(header, '    bool min_width_set;\n',
                          '    bool min_width_set;\n    bool background_inset_set;\n')

    style = (SOURCE / 'style.c').read_text()
    style = replace_once(style, '  } else if (strcmp(prop, "min-width") == 0) {',
                         '  } else if (strcmp(prop, "background-inset") == 0) {\n'
                         '    st->background_inset = parse_int(val);\n'
                         '    st->background_inset_set = true;\n'
                         '  } else if (strcmp(prop, "min-width") == 0) {')
    style = replace_once(style, '  if (s->min_width_set)\n    dst->min_width = s->min_width;\n',
                         '  if (s->min_width_set)\n    dst->min_width = s->min_width;\n'
                         '  if (s->background_inset_set)\n    dst->background_inset = s->background_inset;\n')
    style = replace_once(style, '  dst->min_width_set |= s->min_width_set;\n',
                         '  dst->min_width_set |= s->min_width_set;\n'
                         '  dst->background_inset_set |= s->background_inset_set;\n')

    bar = (SOURCE / 'mangobar.c').read_text()
    bar = replace_once(bar, '  int min_width; // minimum module width\n',
                       '  int min_width; // minimum module width\n'
                       '  int background_inset; // preview-only vertical fill inset\n')
    bar = replace_once(bar, '    int rad = module_radius(st, buf_h);\n    // Rounded background',
                       '    int inset = strcmp(module, "tags") == 0 ? st->background_inset : 0;\n'
                       '    if (inset < 0) inset = 0;\n'
                       '    if (inset > (int)buf_h / 3) inset = (int)buf_h / 3;\n'
                       '    uint32_t fill_h = buf_h - 2 * (uint32_t)inset;\n'
                       '    int fill_y = g_rt->bar_top + inset;\n'
                       '    int rad = module_radius(st, fill_h);\n'
                       '    // Rounded background')
    bar = replace_once(bar,
                       'cairo_rounded_rect(bar_bg_cr, x1, g_rt->bar_top, (double)(x2 - x1),\n'
                       '                                (double)buf_h, rad);',
                       'cairo_rounded_rect(bar_bg_cr, x1, fill_y, (double)(x2 - x1),\n'
                       '                                (double)fill_h, rad);')
    bar = replace_once(bar,
                       '.y1 = g_rt->bar_top * s,\n                            .y2 = (g_rt->bar_top + buf_h) * s',
                       '.y1 = fill_y * s,\n                            .y2 = (fill_y + fill_h) * s')
    bar = replace_once(bar,
                       '  h = hash_mix(h, ((uint64_t)(uint32_t)st->radius << 32) |\n'
                       '                      (uint64_t)(uint32_t)st->min_width);',
                       '  h = hash_mix(h, ((uint64_t)(uint32_t)st->radius << 32) |\n'
                       '                      (uint64_t)(uint32_t)st->min_width);\n'
                       '  h = hash_mix(h, (uint64_t)(uint32_t)st->background_inset);')
    bar = replace_once(bar,
                       '  if (s.min_width_set)\n    ms->min_width = s.min_width;\n',
                       '  if (s.min_width_set)\n    ms->min_width = s.min_width;\n'
                       '  if (s.background_inset_set)\n'
                       '    ms->background_inset = s.background_inset;\n')
    # Upstream fills only the region between the left and right module groups.
    # A full backing surface lets unboxed transparent tag rasters sit on one
    # continuous porcelain strip, including their inter-tag spacing.
    bar = replace_once(bar,
                       '  int mid_x0 = (int)(left_end * (uint32_t)scale);\n'
                       '  int mid_x1 = (int)(right_start * (uint32_t)scale);',
                       '  int mid_x0 = 0;\n'
                       '  int mid_x1 = (int)bar->width;')
    bar = replace_once(bar,
                       '  bool mid_valid = right_start > left_end;',
                       '  bool mid_valid = logical_w > 0;')
    return {'style.h': header, 'style.c': style, 'mangobar.c': bar}


def build():
    sources = patched_sources()
    if not COPY.exists():
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE, COPY)
    for name, content in sources.items():
        (COPY / name).write_text(content)
    if not BUILD.exists():
        subprocess.run(['meson', 'setup', str(BUILD), str(COPY)], check=True)
    subprocess.run(['ninja', '-C', str(BUILD)], check=True)
    return BUILD / 'mangobar'


if __name__ == '__main__':
    print(build())
