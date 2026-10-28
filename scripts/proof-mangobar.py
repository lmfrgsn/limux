#!/usr/bin/env python3
"""Generate a schematic SVG proof from candidate tokens, not a desktop capture.

Native module geometry, scaling, text rasterization and tray icons still need
Wayland review. Sample labels below are fictional and never read live data.
"""
from html import escape
from pathlib import Path
import tomllib
from mangobar import render, contrast

root = Path(__file__).resolve().parents[1]
t = tomllib.loads((root/'themes/rhapsody.toml').read_text())
render(t)  # Same validation as the actual CSS.
c, b, s = t['colors'], t['mangobar'], t['semantics']
out = root/'build/rhapsody-candidate2'
out.mkdir(parents=True, exist_ok=True)
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="340" viewBox="0 0 1280 340">']
def rect(x,y,w,h,fill,r=0):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')
def text(x,y,label,fill,size=13,weight=500):
    svg.append(f'<text x="{x}" y="{y}" fill="{fill}" font-family="{escape(t["typography"]["sans"])}" font-size="{size}" font-weight="{weight}">{escape(label)}</text>')
rect(0,0,1280,340,c['canvas'])
text(24,32,'RHAPSODY / CANDIDATE 02',c['text'],19)
text(24,56,'Offline schematic • fictional content • 30-unit bar • not a Wayland screenshot',c['text_secondary'])
rect(24,80,1232,30,c['surface'])
for i in range(9):
    x=24+i*28
    state='active' if i==1 else ('occupied' if i==0 else 'empty')
    bg=c[s['selected']] if state=='active' else c['canvas'] if state=='occupied' else c['chrome']
    fg=c['text'] if state!='empty' else c['text_quiet']
    rect(x+1,80,26,30,bg,b['control_radius'])
    text(x+9,100,str(i+1),fg)
rect(282,80,76,30,c['chrome'],b['control_radius'])
text(290,100,'Layout []=',c['text_secondary'])
text(374,100,'project / editor',c['text_secondary'])
text(580,100,'Wed 28 Oct  20:42',c['text'])
text(946,100,'Wi-Fi connected   Bat 82%   Vol 35%',c['text_secondary'])
text(24,151,'STATE STUDY',c['text_secondary'])
for i,(label,fg,bg) in enumerate([
    ('Selected',c[s['on_selected']],c[s['selected']]),
    ('Urgent',c[s['on_urgent']],c[s['urgent']]),
    ('Success / reserved',c[s['on_success']],c[s['success']]),
    ('Neutral emphasis',c['surface'],c[s['emphasis']]),
]):
    x=24+i*306
    if label == 'Neutral emphasis':
        rect(x,168,270,34,c['surface'],2)
        rect(x,168,8,34,bg)
        text(x+18,190,label,c['text'])
        text(x,224,'Emphasis swatch; not a text background',c['text_secondary'])
    else:
        rect(x,168,270,34,bg,2)
        text(x+10,190,label,fg)
        text(x,224,f'Text contrast {contrast(fg,bg):.2f}:1',c['text_secondary'])
text(24,269,'Yellow selection anchors the porcelain rail; neutral keys recede and technical metadata stays quiet.',c['text'])
text(24,295,'Native limits: full-height controls; no workspace outlines/shadows. Hover squares corners without recolouring.',c['text_secondary'])
text(24,319,'Control-fill contrast is subtle; final selection affordance and display scaling require on-device review.',c['text_secondary'])
svg.append('</svg>')
(out/'proof.svg').write_text('\n'.join(svg))
print(out/'proof.svg')
