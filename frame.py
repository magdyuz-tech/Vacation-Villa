#!/usr/bin/env python3
"""frame.py - sheet border, title block, legend, notes and key panel."""

import datetime as _dt
import os

from drafting import (Sheet, esc, SHEET_W, SHEET_H, INK, GREY, LIGHT, FONT,
                      LW_CUT, LW_SECONDARY, LW_FIXTURE, LW_THIN, LW_HIDDEN, S)
import fixtures as fx
import geometry as G

PANEL_X = 580.0
PANEL_R = 831.0
TITLEBLOCK_Y = 468.0      # top edge of the title block with three revisions
REV_PITCH = 7.0           # spacing of the revision rows, in sheet mm
REV_ROWS = 4              # revisions printed; older ones drop off the top


def titleblock_top():
    """Top edge of the title block, in sheet mm.

    The block grows upward as revision rows are added so a new issue can
    never push the last row out through the bottom of the frame - but only
    up to REV_ROWS.  Letting it grow for ever meant every revision took
    another 7 mm from the general notes, and by P6 the notes on three
    sheets had been cut to make room for history nobody reads on a
    preliminary drawing.  The title block now shows the most recent
    revisions and the full record lives in the revision schedule.
    """
    return TITLEBLOCK_Y - max(0, min(len(REVISIONS), REV_ROWS) - 3) * REV_PITCH
PROJECT = "FIVE-STOREY VACATION VILLA"
CLIENT = "PRIVATE CLIENT"
# The site.  A drawing set without one is a set nobody can build from, and
# the location is not decoration here: it fixes the governing code, the
# seismic zone, the climate the services are sized for and the authority
# the drawings are submitted to.
LOCATION = "SHAMANDEEL, QUESNA, MENOUFIA, EGYPT"
# The codes the set is drawn to.  Named rather than left as "the local
# code", because a compliance matrix against an unnamed code is a blank
# page with a heading.
CODES = ("ECP 201 — Egyptian Code for Loads",
         "ECP 203 — Egyptian Code for Reinforced Concrete")
REV = "P4"                # the set's current revision - a sheet may be behind
# Revision record, newest last.  A revision letter is only useful if it
# says what changed, so the title block prints this.
REVISIONS = [
    ("P1", "2026-09-18", "first issue"),
    ("P2", "2026-09-24", "east windows, taller floors, garden on A-100"),
    ("P3", "2026-09-29", "four storeys, apartments, straight north boundary"),
    ("P4", "2026-09-29", "north and east opened up, light court removed"),
    ("P5", "2026-10-06", "detached villa: 1.00 m setbacks, wave cantilever"),
    ("P6", "2026-10-06", "lobby opened, north hall merged into the bedroom"),
    ("P7", "2026-10-06",
     "second floor agreed; ground floor redrawn as the villa"),
    ("P8", "2026-10-06", "ground floor opened up; guest room off the hall"),
    ("P9", "2026-10-06", "penthouse added: two-bedroom roof apartment"),
    ("P10", "2026-10-07",
     "penthouse between two terraces, pergola joining them"),
    ("P11", "2026-10-07",
     "penthouse: 2.51 m corridor outside the flat; living room to the face"),
    ("P12", "2026-10-07",
     "bedrooms numbered 1-11; all five floors issued as final draft"),
    ("P13", "2026-10-07", "site plan redrawn for the detached villa"),
    ("P14", "2026-10-07",
     "section A-A recut through the east strip, and marked on every plan"),
    ("P15", "2026-10-07",
     "exterior: two schemes, elevations and balcony curves"),
    ("P16", "2026-10-07",
     "neighbours as surveyed: west 3 storeys and blind, east single storey"),
    ("P17", "2026-10-07",
     "ARC-000 deliverables list; title corrected to five storeys"),
    ("P18", "2026-10-07",
     "scheme A adopted: serpentine balcony on every plan; site named"),
    ("P19", "2026-10-07",
     "serpentine waist deepened 0.75 to 1.35 m; 15.7 m² of balcony a floor"),
    ("P20", "2026-10-07",
     "internal partitions 100 mm red brick, specified by the client"),
    ("P21", "2026-10-07",
     "300 mm external and party walls: brick, colour unrestricted"),
    ("P22", "2026-10-08",
     "A-300 to A-302 withdrawn: enlargements of a building not being built"),
    ("P23", "2026-10-10",
     "services layouts: overlapping labels; ground floor re-centred"),
    ("P24", None,
     "EL-400, ME-200 and PL-300 drawn back onto the sheet"),
]
STATUS = "Preliminary design issue — not for construction."
STATUS_FINAL_DRAFT = ("Final draft — layout agreed with the client; "
                      "not for construction.")
# Document control rather than a view of the building: the register's own
# status is that its contents are derived, so it cannot be "preliminary"
# or "agreed" in the way a drawing is.
STATUS_REGISTER = ("Document control — every status on this sheet is "
                   "derived at build time from the issued set.")
# A drawing of a building nobody is building.  It is kept, because a set
# that destroys its own history cannot show how the building was arrived
# at, and because the client holds a bound issue with these sheets in it.
# Keeping it means marking it.
STATUS_WITHDRAWN = ("Withdrawn at {0} — superseded by {1}. Record only; "
                    "not for construction, pricing or measurement.")
# The issue date, stamped at build time. Set SHEET_DATE to pin it when a
# reproducible build matters.
DATE = os.environ.get("SHEET_DATE") or _dt.date.today().isoformat()


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


def heading(sh, sub=None):
    """Sheet title in the panel.  `sub` replaces the level/scale line for
    a sheet that is not a view of the building - the register, which has
    no level and no scale."""
    sh.text_mm(PANEL_X, 30, sh.title.upper(), size=6.6, anchor="start",
               weight=700, ls=0.6)
    sh.text_mm(PANEL_X, 40,
               sub or f"LEVEL {sh.level}   ·   {sh.scale_note}   ·   METRES",
               size=2.6, anchor="start", color=GREY, ls=0.35)
    sh.line_mm(PANEL_X, 46, PANEL_R, 46, w=0.5, color=INK)


def legend(sh, y0=52):
    """Line-weight and symbol key."""
    sh.text_mm(PANEL_X, y0, "KEY", size=3.0, anchor="start", weight=700,
               ls=0.45)
    sh.line_mm(PANEL_X, y0 + 2.2, PANEL_R, y0 + 2.2, w=0.25, color=GREY)
    y = y0 + 12
    rows = [
        # Both wall rows read geometry rather than stating a thickness in
        # prose: this one said "200 mm partition" long after the partition
        # was 120 mm, and would have gone on saying it at 100 mm.
        ("wall", f"External / party wall cut by section, "
                 f"{G.WT * 1000:.0f} mm — {G.WALL_MATERIAL[G.WT]}"),
        ("partition", f"Internal partition, {G.PT * 1000:.0f} mm — "
                      f"{G.WALL_MATERIAL[G.PT]}"),
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


def datum_panel(sh, y0, heading, rows):
    """Two-column reference panel with no total - used by the section,
    where the rows are level datums rather than areas."""
    sh.text_mm(PANEL_X, y0, heading, size=3.0, anchor="start", weight=700,
               ls=0.45)
    sh.line_mm(PANEL_X, y0 + 2.2, PANEL_R, y0 + 2.2, w=0.25, color=GREY)
    y = y0 + 11.0
    col2 = PANEL_X + 238
    for name, val in rows:
        sh.text_mm(PANEL_X + 1, y, name.upper(), size=2.3, anchor="start")
        sh.text_mm(col2, y, val, size=2.3, anchor="end")
        sh.line_mm(PANEL_X + 1, y + 1.4, col2, y + 1.4, w=0.12,
                   color="#e2e2e2")
        y += 7.4
    return y


def notes(sh, y0, items):
    sh.text_mm(PANEL_X, y0, "GENERAL NOTES", size=3.0, anchor="start",
               weight=700, ls=0.45)
    sh.line_mm(PANEL_X, y0 + 2.2, PANEL_R, y0 + 2.2, w=0.25, color=GREY)
    y = y0 + 11.0
    last = y
    for i, t in enumerate(items, 1):
        for j, line in enumerate(_wrap(t, 58)):
            sh.text_mm(PANEL_X + (1 if j else 1), y,
                       (f"{i}.  " if j == 0 else "     ") + line, size=2.2,
                       anchor="start")
            last = y
            y += 5.9
        y += 3.0
    # text is fixed at the client's 12 point minimum, so a note block that
    # is too long can only be shortened - fail loudly rather than print it
    # over the title block
    top = titleblock_top()
    if last > top - 4.0:
        raise ValueError(
            f"{sh.number}: general notes run to y={last:.1f} mm and would "
            f"print over the title block at y={top:.0f} mm - shorten them")
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


def titleblock(sh, y0=None):
    y0 = titleblock_top() if y0 is None else y0
    h = SHEET_H - 20 - y0
    sh.rect_mm(PANEL_X, y0, PANEL_R - PANEL_X, h, sw=0.6, stroke=INK)
    sh.line_mm(PANEL_X, y0 + 16, PANEL_R, y0 + 16, w=0.3, color=GREY)
    sh.line_mm(PANEL_X, y0 + 42, PANEL_R, y0 + 42, w=0.3, color=GREY)
    sh.line_mm(PANEL_X, y0 + 60, PANEL_R, y0 + 60, w=0.3, color=GREY)
    sh.text_mm(PANEL_X + 3, y0 + 11, PROJECT, size=5.2, anchor="start",
               weight=700, ls=0.5)
    # The site, not the client: "PRIVATE CLIENT" told a reader nothing, and
    # this line is the only place on the sheet that says where the building
    # goes.  The client is named in the register's project data instead.
    sh.text_mm(PANEL_R - 3, y0 + 11, LOCATION, size=2.4, anchor="end",
               color=GREY, ls=0.3)
    sh.text_mm(PANEL_X + 3, y0 + 24, "DRAWING", size=2.0, anchor="start",
               color=GREY, ls=0.4)
    sh.text_mm(PANEL_X + 3, y0 + 36, sh.title.upper(), size=5.6,
               anchor="start", weight=700, ls=0.4)
    rev = getattr(sh, "rev", None) or REV
    cols = [(PANEL_X + 3, "DRAWING No", sh.number),
            (PANEL_X + 66, "REVISION", rev),
            (PANEL_X + 116, "SCALE", sh.scale_note),
            (PANEL_X + 186, "DATE", DATE)]
    for x, k, v in cols:
        sh.text_mm(x, y0 + 50, k, size=2.0, anchor="start", color=GREY,
                   ls=0.4)
        sh.text_mm(x, y0 + 57, v, size=3.4, anchor="start", weight=700)
    sh.text_mm(PANEL_X + 3, y0 + 69,
               getattr(sh, "status", None) or STATUS,
               size=2.1, anchor="start", color=GREY)
    sh.text_mm(PANEL_X + 3, y0 + 76,
               "Do not scale; work to figured dimensions only.",
               size=2.1, anchor="start", color=GREY)
    sh.line_mm(PANEL_X, y0 + 82, PANEL_R, y0 + 82, w=0.3, color=GREY)
    sh.text_mm(PANEL_X + 3, y0 + 89, "REVISIONS", size=2.0, anchor="start",
               color=GREY, ls=0.4)
    # Only the revisions this sheet has actually been through: a sheet left
    # at P4 has not seen P5, and listing it would claim an issue that never
    # happened on this drawing.
    letters = [r for r, _w, _t in REVISIONS]
    upto = letters.index(rev) + 1 if rev in letters else len(REVISIONS)
    for i, (r, when, what) in enumerate(REVISIONS[:upto][-REV_ROWS:]):
        sh.text_mm(PANEL_X + 44, y0 + 89 + i * REV_PITCH,
                   f"{r}   {when or DATE}   {what}", size=2.1,
                   anchor="start")


def withdraw(sh, rev, superseded_by):
    """Stamp a sheet withdrawn: a status line, and the word on the face.

    The title block on its own is not enough.  A withdrawn drawing is
    dangerous exactly where a title block is not read - one sheet loose
    on a table, a photograph of the middle of it, a reader scaling a
    room off a plan of a building that was never going to be built.  So
    the word goes diagonally across the drawing itself, pale enough to
    read the plan through and large enough that no crop of it can be
    mistaken for a current drawing.

    Call it last, after the sheet's content: there is no z-order here
    beyond the order things are drawn in.
    """
    sh.rev = rev
    sh.status = STATUS_WITHDRAWN.format(rev, superseded_by)
    cx, cy = 294.0, 300.0
    sh.text_mm(cx, cy, "WITHDRAWN", size=40.0, anchor="middle", weight=700,
               color="#c4c4c4", ls=8.0, rot=-27,
               style="opacity:0.75")
    sh.text_mm(cx, cy + 24, f"SUPERSEDED BY {superseded_by.upper()}",
               size=5.4, anchor="middle", weight=400, color="#b4b4b4",
               ls=2.2, rot=-27, style="opacity:0.9")


def compass_and_scale(sh, x=440.0, y=500.0):
    fx.north_arrow(sh, x, y - 10, r=10.0)
    fx.scale_bar(sh, 60, y + 14, metres=10)


def render(sh):
    defs = ""
    if getattr(sh, "clips", None):
        paths = "".join(
            f'<clipPath id="{cid}"><rect x="{x:.2f}" y="{y:.2f}" '
            f'width="{w:.2f}" height="{h:.2f}"/></clipPath>'
            for cid, x, y, w, h in sh.clips)
        defs = f"<defs>{paths}</defs>\n"
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{SHEET_W}mm" height="{SHEET_H}mm" '
            f'viewBox="0 0 {SHEET_W} {SHEET_H}">\n'
            f'<title>{esc(sh.number)} {esc(sh.title)}</title>\n'
            f'<rect width="{SHEET_W}" height="{SHEET_H}" fill="#ffffff"/>\n'
            + defs + "\n".join(sh.body) + "\n</svg>\n")
