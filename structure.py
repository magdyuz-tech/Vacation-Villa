#!/usr/bin/env python3
"""
structure.py - Package C, drawn as layout and not as engineering.

Every sheet in the STR series is class L.  That is not a disclaimer, it
is the whole design of the package: the grid, the column coordinates, the
slab edges, the spans and the lines where a beam is required are ours and
exact, because they fall out of the architecture.  Member sizes, slab and
footing depths, reinforcement, cover and every load are the structural
engineer's, and none of them appears anywhere here.

So the drawings are deliberately incomplete in one direction only.  A
column schedule with coordinates and blank sections is useful: an
engineer fills the blanks.  A column schedule with sizes invented by an
architect is worse than no schedule at all, because somebody builds it.

The one piece of real structural reasoning the architecture already
settled: a 300 mm wall needs a beam under it, and a beam is a column line,
a wall below, or a secondary beam landing on primary beams.  Every 300 mm
wall in this building stands on a grid line - checks.py proves it - with
one declared exception, the penthouse's north wall, which is why STR-305
carries a secondary beam the other framing layouts do not.
"""

import drafting as D
from drafting import (INK, GREY, LIGHT, LW_CUT, LW_SECONDARY, LW_FIXTURE,
                      LW_THIN, LW_HIDDEN)
from geometry import *          # noqa: F401,F403  (pure constants)

STAMP = ("Layout for the engineer's design — no member sizes, no "
         "reinforcement, no loads. Not for construction.")

GRID_OVER = 1.55                # how far a grid line runs past the frame
BUBBLE = 0.52


def grid(sh, bubbles=True):
    """The structural grid, lettered A–C and numbered 1–4."""
    x0, x1 = GRID_X[0] - GRID_OVER, GRID_X[-1] + GRID_OVER
    # the south bubbles have to clear the cantilever, which reaches
    # further out than the usual grid overrun
    y0 = min(GRID_Y[0] - GRID_OVER, V3_Y0 - V3_WAVE_DEEP - 0.95)
    y1 = GRID_Y[-1] + GRID_OVER
    with sh.on("S-GRID"):
        for i, x in enumerate(GRID_X):
            sh.line(x, y0, x, y1, w=LW_THIN, color=GREY, dash="9 2 1.6 2")
            if bubbles:
                for yy in (y0, y1):
                    sh.circle(x, yy, BUBBLE, fill="#ffffff", stroke=INK,
                              sw=LW_SECONDARY)
                    sh.tag(x, yy - 0.20, GRID_LETTER[i], size=2.4,
                           color=INK)
        for j, y in enumerate(GRID_Y, 1):
            sh.line(x0, y, x1, y, w=LW_THIN, color=GREY, dash="9 2 1.6 2")
            if bubbles:
                for xx in (x0, x1):
                    sh.circle(xx, y, BUBBLE, fill="#ffffff", stroke=INK,
                              sw=LW_SECONDARY)
                    sh.tag(xx, y - 0.20, str(j), size=2.4, color=INK)


def grid_dims(sh):
    """The spans, which are what a flat slab is sized by."""
    for i in range(len(GRID_X) - 1):
        sh.dim_h(GRID_X[i], GRID_X[i + 1], GRID_Y[0] - 2.75)
    for j in range(len(GRID_Y) - 1):
        sh.dim_v(GRID_Y[j], GRID_Y[j + 1], GRID_X[-1] + 2.75)


def columns_at(sh, level, label=True):
    """Every column standing at this level, on the grid."""
    n = 0
    with sh.on("S-COLS"):
        for mark, x, y, levels in grid_columns():
            if level not in levels:
                continue
            sh.rect(x - COL / 2, y - COL / 2, COL, COL, fill="#2a2a2a",
                    stroke="#2a2a2a", sw=0.05)
            if label:
                sh.tag(x + 0.62, y + 0.42, mark, size=1.8, color=INK,
                       anchor="start")
            n += 1
    return n


def slab_edge(sh, level):
    """The slab at this level: its outline, and the balcony beyond it."""
    if level >= len(EL_LEVELS):           # the roof over the penthouse
        sh.rect(V4_X0, V4_Y0, V4_X1 - V4_X0, V4_Y1 - V4_Y0, fill="#f3f5f6",
                stroke=INK, sw=LW_CUT)
        return
    if level == 4:
        sh.rect(V3_X0, V3_Y0, V3_X1 - V3_X0, V3_Y1 - V3_Y0, fill="#f3f5f6",
                stroke=INK, sw=LW_CUT)
    else:
        sh.rect(V3_X0, V3_Y0, V3_X1 - V3_X0, V3_Y1 - V3_Y0, fill="#f3f5f6",
                stroke=INK, sw=LW_CUT)
    if level > 0:
        pts = wave_points()
        sh.poly([(pts[0][0], V3_Y0)] + pts + [(pts[-1][0], V3_Y0)],
                fill="#e7ebee", stroke=INK, sw=LW_CUT)


def beams(sh, level):
    """Where a beam is required, and why.

    Primary beams run on the grid, because every 300 mm wall stands on a
    grid line.  One secondary beam exists, under the penthouse's north
    wall, which is the single wall that does not.
    """
    drawn = []
    with sh.on("S-BEAM"):
        for x in GRID_X:
            sh.line(x, GRID_Y[0], x, GRID_Y[-1], w=LW_SECONDARY, color=INK)
            drawn.append(("primary", "v", x))
        for y in GRID_Y:
            sh.line(GRID_X[0], y, GRID_X[-1], y, w=LW_SECONDARY, color=INK)
            drawn.append(("primary", "h", y))
        lvl, _axis, yy = GRID_EXCEPTION
        if level == lvl:
            sh.line(GRID_X[1], yy, GRID_X[2], yy, w=LW_SECONDARY,
                    color=INK, dash="7 3")
            sh.tag((GRID_X[1] + GRID_X[2]) / 2.0, yy + 0.42,
                   "SECONDARY BEAM UNDER THE PENTHOUSE NORTH WALL",
                   size=1.7, color=INK)
            drawn.append(("secondary", "h", yy))
    return drawn


def voids(sh, level):
    """Holes in the slab: the stair well, open on every floor it passes.

    Including the slab at +13.20: the stair arrives at the penthouse
    level and its well is open to the sky there, under a canopy.  Only
    the roof over the penthouse, which is nowhere near it, is solid.
    """
    if level >= 5:
        return
    sx0, sy0, sx1, sy1 = V3_STAIR
    sh.rect(sx0, sy0, sx1 - sx0, sy1 - sy0, fill="#ffffff", stroke=INK,
            sw=LW_SECONDARY, dash="5 3")
    sh.tag((sx0 + sx1) / 2.0, (sy0 + sy1) / 2.0, "VOID", size=1.9,
           color=GREY)


def footings(sh):
    """A pad under every column, at the coordinate the column stands on.

    The pad is drawn at a nominal 1.20 m square so the layout reads.  It
    is not a size: GEO-001 gives the bearing pressure and the engineer
    gives the footing, and the sheet says so in as many words.
    """
    nominal = 1.20
    for mark, x, y, _levels in grid_columns():
        sh.rect(x - nominal / 2, y - nominal / 2, nominal, nominal,
                fill="#eceff1", stroke=INK, sw=LW_SECONDARY, dash="4 2")
        sh.tag(x, y - 0.95, f"F-{mark}", size=1.7, color=GREY)
    return nominal
