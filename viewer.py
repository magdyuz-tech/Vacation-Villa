#!/usr/bin/env python3
"""
viewer.py - bundles the generated sheets into one self-contained HTML file.

The SVGs are inlined, so the page opens offline with no external libraries,
fonts or network calls, matching this project's output conventions.
"""

import os
import re
import sys

SHEETS = [
    ("A-000", "Site Plan", "+0.00", "1:75",
     "The plot, the garden corridor and the building footprint."),
    ("A-100", "Ground Floor Plan", "+0.00", "1:50",
     "Entrance, lounges, guest room and the central kitchen and laundry."),
    ("A-101", "First Floor Plan", "+3.30", "1:50",
     "Two one-bedroom apartments with balconies and kitchenettes."),
    ("A-102", "Second Floor Plan", "+6.60", "1:50",
     "Two one-bedroom apartments, identical to the floor below."),
    ("A-103", "Third Floor & Roof Plan", "+9.90", "1:50",
     "Two-bedroom apartment between a south and a north terrace."),
    ("A-200", "Section A–A", "through the core", "1:50",
     "Cut through the glazing, lift shaft, stair and light court."),
    ("A-300", "Typical Apartment — Enlarged Plan", "+3.30 / +6.60", "1:25",
     "Entry, wet rooms and kitchenettes of both apartments."),
    ("A-301", "Third Floor Apartment — Enlarged Plan", "+9.90", "1:25",
     "The living band across both blocks and the master suite."),
    ("A-302", "Central Kitchen & Laundry — Enlarged Plan", "+0.00", "1:25",
     "The service floor: kitchen, servery, wash-up, laundry, stores."),
]

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#11161c; --panel:#1a2029; --line:#2b333f; --ink:#e8ecf1;
  --muted:#93a0b0; --accent:#d8b26a; --paper:#fff;
}
html,body{height:100%}
body{
  background:var(--bg); color:var(--ink); font:14px/1.5 ui-sans-serif,
  -apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
  display:flex; flex-direction:column; overflow:hidden;
}
header{
  padding:14px 20px; border-bottom:1px solid var(--line);
  display:flex; align-items:baseline; gap:16px; flex-wrap:wrap;
}
h1{font-size:15px; font-weight:700; letter-spacing:.14em; text-transform:uppercase}
header .sub{color:var(--muted); font-size:12px; letter-spacing:.04em}
nav{display:flex; gap:6px; padding:10px 16px; border-bottom:1px solid var(--line);
    background:var(--panel); flex-wrap:wrap; align-items:center}
button{
  font:inherit; color:var(--ink); background:transparent; cursor:pointer;
  border:1px solid var(--line); border-radius:6px; padding:7px 13px;
}
button:hover{border-color:var(--muted)}
.tab{display:flex; flex-direction:column; align-items:flex-start; line-height:1.25}
.tab b{font-size:12.5px; letter-spacing:.06em}
.tab span{font-size:11px; color:var(--muted)}
.tab[aria-selected="true"]{border-color:var(--accent); background:#232b36}
.tab[aria-selected="true"] b{color:var(--accent)}
.spacer{flex:1}
.zoom{display:flex; gap:6px; align-items:center}
.zoom output{min-width:52px; text-align:center; color:var(--muted);
             font-variant-numeric:tabular-nums; font-size:12px}
main{flex:1; overflow:hidden; position:relative; background:#0c1014}
.stage{position:absolute; inset:0; overflow:auto; cursor:grab;
       display:flex; align-items:flex-start; justify-content:center; padding:24px}
.stage.drag{cursor:grabbing}
.sheet{display:none}
.sheet.on{display:block}
.paper{background:var(--paper); box-shadow:0 18px 50px rgba(0,0,0,.55)}
.paper svg{display:block; width:841px; height:594px}
footer{padding:9px 20px; border-top:1px solid var(--line); color:var(--muted);
       font-size:11.5px; letter-spacing:.03em; background:var(--panel)}
kbd{border:1px solid var(--line); border-radius:4px; padding:1px 5px;
    font:inherit; font-size:10.5px; color:var(--ink)}
"""

JS = """
const sheets=[...document.querySelectorAll('.sheet')];
const tabs=[...document.querySelectorAll('.tab')];
const svgs=[...document.querySelectorAll('.paper svg')];
const stage=document.getElementById('stage');
const out=document.getElementById('pct');
const W=841, H=594;                       // ISO A1 sheet, millimetres
let z=1;

function apply(){
  z=Math.max(0.15,Math.min(4,z));
  svgs.forEach(s=>{s.style.width=(W*z)+'px';s.style.height=(H*z)+'px';});
  out.value=Math.round(z*100)+'%';
}
function fit(){
  z=Math.min((stage.clientWidth-56)/W,(stage.clientHeight-56)/H);
  apply();
}
function show(i){
  sheets.forEach((s,n)=>s.classList.toggle('on',n===i));
  tabs.forEach((t,n)=>t.setAttribute('aria-selected',n===i));
  stage.scrollTop=0;stage.scrollLeft=0;
}
tabs.forEach((t,i)=>t.onclick=()=>show(i));
document.getElementById('in').onclick=()=>{z*=1.25;apply()};
document.getElementById('out').onclick=()=>{z/=1.25;apply()};
document.getElementById('fit').onclick=fit;
document.getElementById('full').onclick=()=>{z=1;apply()};
addEventListener('keydown',e=>{
  if(e.key>='1'&&e.key<='9'){show(+e.key-1);return}
  if(e.key==='+'||e.key==='='){z*=1.25;apply()}
  if(e.key==='-'){z/=1.25;apply()}
  if(e.key==='0'){fit()}
});
stage.addEventListener('wheel',e=>{
  if(!e.ctrlKey&&!e.metaKey)return;
  e.preventDefault();z*=(e.deltaY<0?1.1:1/1.1);apply();
},{passive:false});
let dragging=false,sx=0,sy=0,ox=0,oy=0;
stage.addEventListener('pointerdown',e=>{
  dragging=true;sx=e.clientX;sy=e.clientY;
  ox=stage.scrollLeft;oy=stage.scrollTop;
  stage.classList.add('drag');stage.setPointerCapture(e.pointerId);
});
stage.addEventListener('pointermove',e=>{
  if(!dragging)return;
  stage.scrollLeft=ox-(e.clientX-sx);stage.scrollTop=oy-(e.clientY-sy);
});
['pointerup','pointercancel'].forEach(ev=>stage.addEventListener(ev,()=>{
  dragging=false;stage.classList.remove('drag');
}));
addEventListener('resize',fit);
show(0);fit();
"""


def _slug(title):
    """Must match plans.slugify so the viewer finds the generated files."""
    out = []
    for ch in title.lower():
        out.append(ch if (ch.isalnum() and ch.isascii()) else "-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def inline(svg_text):
    """Strip the XML declaration and let the SVG scale inside its frame."""
    svg_text = re.sub(r"<\?xml[^>]*\?>\s*", "", svg_text)
    return re.sub(r'width="[^"]*mm"\s+height="[^"]*mm"',
                  'width="841" height="594"', svg_text, count=1)


def build(drawings_dir, out_path):
    parts, tabs = [], []
    for i, (num, title, level, scale, blurb) in enumerate(SHEETS):
        slug = _slug(title)
        path = os.path.join(drawings_dir, f"{num}-{slug}.svg")
        with open(path, encoding="utf-8") as fh:
            svg = inline(fh.read())
        tabs.append(f'<button class="tab" aria-selected="false">'
                    f'<b>{num}</b><span>{title}</span></button>')
        parts.append(f'<section class="sheet" aria-label="{num} {title}">'
                     f'<div class="paper">{svg}</div></section>')
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Four-Storey Vacation Home — Drawing Set</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Four-Storey Vacation Home</h1>
  <span class="sub">Preliminary drawing set · Rev P3 · ISO A1 ·
  nine sheets</span>
</header>
<nav>
  {''.join(tabs)}
  <span class="spacer"></span>
  <span class="zoom">
    <button id="out" title="Zoom out">−</button>
    <output id="pct">100%</output>
    <button id="in" title="Zoom in">+</button>
    <button id="fit">Fit</button>
    <button id="full">1:1</button>
  </span>
</nav>
<main><div class="stage" id="stage">{''.join(parts)}</div></main>
<footer>
  <kbd>1</kbd>–<kbd>9</kbd> sheets &nbsp;·&nbsp;
  <kbd>+</kbd> <kbd>−</kbd> <kbd>0</kbd> zoom &nbsp;·&nbsp;
  ctrl/⌘ + scroll to zoom, drag to pan &nbsp;·&nbsp;
  Preliminary design issue — not for construction.
</footer>
<script>{JS}</script>
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "drawings")
    o = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "drawing-set.html")
    p = build(d, o)
    print(p, os.path.getsize(p), "bytes")
