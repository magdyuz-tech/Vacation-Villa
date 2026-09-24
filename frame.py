#!/usr/bin/env python3
"""frame.py - sheet border, title block, legend, notes and key panel."""

from drafting import (Sheet, esc, SHEET_W, SHEET_H, INK, GREY, LIGHT, FONT,
                      LW_CUT, LW_SECONDARY, LW_FIXTURE, LW_THIN, LW_HIDDEN, S)
import fixtures as fx

PANEL_X = 580.0
PANEL_R = 831.0
PROJECT = "VACATION HOUSE — NEW BUILD"
CLIENT = "PRIVATE CLIENT"
REV = "P1"
DATE = "2026-09-18"


def border(sh):
    sh.rect_mm(10, 10, SHEET_W - 20, SHEET_H - 20, sw=0.7, stroke=INK)
    sh.rect_mm(13, 13, SHEET_W - 26, SHEET_H - 26, sw=0.25, stroke=GREY)
    # sheet-edge registration ticks
    for i in range(1, 7):
        x = 10 + i * (SHEET_W - 20) / 7
        sh.line_mm(x, 10, x, 13, w=0.25, color=GREY)
        sh.line_mm(x, SHEET_H - 13, x, SHEET_H - 10, w=0.25, color=GREY)
    for i in range(1, 4):
        y = 10 + i * (SHEET_H - 20) / 4
        sh.line_mm(10, y, 13, y, w=0.25, color=GREY)
        sh.line_mm(SHEET_W - 13, y, SHEET_W - 10, y, w=0.25, color=GREY)


def heading(sh):
    sh.text_mm(PANEL_X, 30, sh.title.upper(), size=6.6, anchor="start",
               weight=700, ls=0.6)
    sh.text_mm(PANEL_X, 40, f"LEVEL {sh.level}   ·   {sh.scale_note}"
               "   ·   METRES", size=2.6,
               anchor="start", color=GREY, ls=0.35)
    sh.line_mm(PANEL_X, 46, PANEL_R, 46, w=0.5, color=INK)


def legend(sh, y0=52):
    """Line-weight and symbol key."""
    sh.text_mm(PANEL_X, y0, "KEY", size=3.0, anchor="start", weight=700,
               ls=0.45)
    sh.line_mm(PANEL_X, y0 + 2.2, PANEL_R, y0 + 2.2, w=0.25, color=GREY)
    y = y0 + 12
    rows = [
        ("wall", "Masonry wall cut by section — 200 mm partition,"
                 " 300 mm external / party"),
        ("partition", "Internal stud or block partition, 120 mm"),
        ("parapet", "Terrace parapet, 250 mm × 1100 mm high"),
        ("door", "Single leaf door, swing shown to opening side"),
        ("window", "Glazed opening — arched head where noted"),
        ("hidden", "Element above the cut plane (pergola, slab over)"),
        ("void", "Void / open to sky"),
        ("level", "Finished floor level datum"),
    ]
    for kind, txt in rows:
        _symbol(sh, PANEL_X + 1, y, kind)
        for k, line in enumerate(_wrap(txt, 46)):
            sh.text_mm(PANEL_X + 30, y + 1.4 + k * 5.4, line, size=2.25,
                       anchor="start", color=INK)
        y += 11.5
    return y


def _symbol(sh, x, y, kind):
    w = 24.0
    if kind == "wall":
        sh.rect_mm(x, y - 1.0, w, 2.4, fill=INK, stroke=INK, sw=0.05)
    elif kind == "partition":
        sh.rect_mm(x, y - 0.3, w, 1.2, fill=INK, stroke=INK, sw=0.05)
    elif kind == "parapet":
        sh.rect_mm(x, y - 0.6, w, 1.8, fill="#6f6f6f", stroke=INK, sw=0.1)
    elif kind == "door":
        sh.rect_mm(x, y - 0.3, 7, 1.2, fill=INK, stroke=INK, sw=0.05)
        sh.rect_mm(x + 17, y - 0.3, 7, 1.2, fill=INK, stroke=INK, sw=0.05)
        sh.line_mm(x + 7, y + 0.3, x + 7, y - 9.2, w=LW_FIXTURE, color=INK)
        sh.raw(f'<path d="M {x + 7} {y - 9.2} A 10 10 0 0 1 {x + 17} '
               f'{y + 0.3}" fill="none" stroke="{GREY}" '
               f'stroke-width="{LW_THIN}"/>')
    elif kind == "window":
        sh.rect_mm(x, y - 0.9, 5, 2.2, fill=INK, stroke=INK, sw=0.05)
        sh.rect_mm(x + 19, y - 0.9, 5, 2.2, fill=INK, stroke=INK, sw=0.05)
        for f in (-0.55, 0.0, 0.55):
            sh.line_mm(x + 5, y + 0.2 + f, x + 19, y + 0.2 + f,
                       w=LW_FIXTURE, color=GREY if f else INK)
    elif kind == "hidden":
        sh.line_mm(x, y + 0.3, x + w, y + 0.3, w=LW_HIDDEN, color=GREY)
        sh.raw(f'<line x1="{x}" y1="{y + 0.3}" x2="{x + w}" y2="{y + 0.3}" '
               f'stroke="{GREY}" stroke-width="{LW_HIDDEN}" '
               f'stroke-dasharray="2.2 1.4"/>')
    elif kind == "void":
        sh.rect_mm(x, y - 3.2, w, 6.6, sw=LW_SECONDARY, stroke=GREY,
                   dash="2.5 1.5")
        for i in range(5):
            sh.line_mm(x + i * 5.2, y + 3.4, x + i * 5.2 + 6.6, y - 3.2,
                       w=LW_THIN, color="#c9c9c9")
    elif kind == "level":
        sh.raw(f'<polygon points="{x + 4},{y + 1.2} {x + 1.6},{y - 2.2} '
               f'{x + 6.4},{y - 2.2}" fill="none" stroke="{INK}" '
               f'stroke-width="{LW_THIN}"/>')
        sh.text_mm(x + 9, y + 1.0, "+0.00", size=2.1, anchor="start",
                   color=INK)


def schedule(sh, y0, extra=()):
    """Room area schedule from everything the sheet labelled."""
    sh.text_mm(PANEL_X, y0, "AREA SCHEDULE", size=3.0, anchor="start",
               weight=700, ls=0.45)
    sh.line_mm(PANEL_X, y0 + 2.2, PANEL_R, y0 + 2.2, w=0.25, color=GREY)
    y = y0 + 11.0
    col2 = PANEL_X + 238
    total = 0.0
    for name, a in sh.schedule:
        sh.text_mm(PANEL_X + 1, y, name.upper(), size=2.3, anchor="start")
        sh.text_mm(col2, y, f"{a:>6.1f} m²", size=2.3, anchor="end")
        sh.line_mm(PANEL_X + 1, y + 1.4, col2, y + 1.4, w=0.12,
                   color="#e2e2e2")
        total += a
        y += 7.4
    sh.line_mm(PANEL_X, y - 2.2, col2, y - 2.2, w=0.4, color=INK)
    y += 2.4
    sh.text_mm(PANEL_X + 1, y, "TOTAL", size=2.5, anchor="start", weight=700)
    sh.text_mm(col2, y, f"{total:>6.1f} m²", size=2.5, anchor="end",
               weight=700)
    y += 8.5
    for label, val in extra:
        sh.text_mm(PANEL_X + 1, y, label.upper(), size=2.3, anchor="start",
                   color=GREY)
        sh.text_mm(col2, y, val, size=2.3, anchor="end", color=GREY)
        y += 7.4
    return y


def notes(sh, y0, items):
    sh.text_mm(PANEL_X, y0, "GENERAL NOTES", size=3.0, anchor="start",
               weight=700, ls=0.45)
    sh.line_mm(PANEL_X, y0 + 2.2, PANEL_R, y0 + 2.2, w=0.25, color=GREY)
    y = y0 + 11.0
    for i, t in enumerate(items, 1):
        for j, line in enumerate(_wrap(t, 58)):
            sh.text_mm(PANEL_X + (1 if j else 1), y,
                       (f"{i}.  " if j == 0 else "     ") + line, size=2.2,
                       anchor="start")
            y += 5.9
        y += 3.0
    return y


def _wrap(t, n):
    out, line = [], ""
    for w in t.split():
        if len(line) + len(w) + 1 > n:
            out.append(line); line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


def titleblock(sh, y0=468):
    h = SHEET_H - 20 - y0
    sh.rect_mm(PANEL_X, y0, PANEL_R - PANEL_X, h, sw=0.6, stroke=INK)
    sh.line_mm(PANEL_X, y0 + 16, PANEL_R, y0 + 16, w=0.3, color=GREY)
    sh.line_mm(PANEL_X, y0 + 42, PANEL_R, y0 + 42, w=0.3, color=GREY)
    sh.line_mm(PANEL_X, y0 + 60, PANEL_R, y0 + 60, w=0.3, color=GREY)
    sh.text_mm(PANEL_X + 3, y0 + 11, PROJECT, size=5.2, anchor="start",
               weight=700, ls=0.5)
    sh.text_mm(PANEL_R - 3, y0 + 11, CLIENT, size=2.4, anchor="end",
               color=GREY, ls=0.3)
    sh.text_mm(PANEL_X + 3, y0 + 24, "DRAWING", size=2.0, anchor="start",
               color=GREY, ls=0.4)
    sh.text_mm(PANEL_X + 3, y0 + 36, sh.title.upper(), size=5.6,
               anchor="start", weight=700, ls=0.4)
    cols = [(PANEL_X + 3, "DRAWING No", sh.number),
            (PANEL_X + 66, "REVISION", REV),
            (PANEL_X + 116, "SCALE", sh.scale_note),
            (PANEL_X + 186, "DATE", DATE)]
    for x, k, v in cols:
        sh.text_mm(x, y0 + 50, k, size=2.0, anchor="start", color=GREY,
                   ls=0.4)
        sh.text_mm(x, y0 + 57, v, size=3.4, anchor="start", weight=700)
    sh.text_mm(PANEL_X + 3, y0 + 69,
               "Preliminary design issue — not for construction.",
               size=2.1, anchor="start", color=GREY)
    sh.text_mm(PANEL_X + 3, y0 + 76,
               "Do not scale; work to figured dimensions only.",
               size=2.1, anchor="start", color=GREY)


def compass_and_scale(sh, x=440.0, y=500.0):
    fx.north_arrow(sh, x, y - 10, r=10.0)
    fx.scale_bar(sh, 60, y + 14, metres=10)


def render(sh):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{SHEET_W}mm" height="{SHEET_H}mm" '
            f'viewBox="0 0 {SHEET_W} {SHEET_H}">\n'
            f'<title>{esc(sh.number)} {esc(sh.title)}</title>\n'
            f'<rect width="{SHEET_W}" height="{SHEET_H}" fill="#ffffff"/>\n'
            + "\n".join(sh.body) + "\n</svg>\n")
