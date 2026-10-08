#!/usr/bin/env python3
"""
details.py - ARC-600's four junctions, at 1:10.

A construction detail is where a drawing set is most often read as
engineering and most often is not.  Everything on this sheet is one of
two things, and each is marked as which:

  * a DIMENSION this project owns - a wall thickness, the structural
    zone, the guarding height, the nosing and the cove.  Those come from
    `geometry.py` and are figured.
  * a BUILD-UP nobody has specified - the membrane, the insulation, the
    falls screed, the finishes, the sealants, the frame.  Those are drawn
    as a labelled zone of the right thickness-to-be, hatched, and named
    against the specification topic that has to answer for them.

So the sheet can be measured off for setting out and cannot be bought
from.  The structural depths are the engineer's and say so: the 300 mm
zone is ours because it is a planning dimension - it is what sets the
floor-to-floor - but how much of it is slab is not.

The register's row for ARC-600 names four junctions: balcony nosing,
parapet, threshold and roof upstand.  These are those four, in that
order, and `checks.py` holds the sheet to it.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import drafting as D
from drafting import (X, Y, INK, GREY, LIGHT, LW_CUT, LW_SECONDARY,
                      LW_THIN, LW_FIXTURE)
import geometry as G

# A junction is drawn at the scale that makes its smallest real dimension
# readable, not at one scale for tidiness.  The threshold turns on a 20 mm
# fall and a 75 mm step, which at 1:10 are 2 and 7.5 mm on the sheet: it
# is drawn at 1:5 and says so under the detail.
SCALES = [10, 10, 5, 10]
SPEC = "#8a8a8a"                # the ink of anything unspecified
TBS = "TO BE SPECIFIED"

# the four junctions, in the register's order
TITLES = [
    ("D1", "Balcony slab edge, nosing and cove"),
    ("D2", "Terrace parapet and coping"),
    ("D3", "Threshold onto the balcony"),
    ("D4", "Roof upstand at the penthouse wall"),
]


# --------------------------------------------------------------------------
# the vocabulary
# --------------------------------------------------------------------------
def concrete(sh, x, y, w, h):
    """Structural concrete: poche plus the engineer's caveat elsewhere."""
    sh.rect(x, y, w, h, fill="#d9d9d9", stroke=INK, sw=LW_CUT)


def brick(sh, x, y, w, h, pitch=0.075):
    """Masonry, drawn as courses because the detail is about the joint."""
    sh.rect(x, y, w, h, fill="#ececec", stroke=INK, sw=LW_CUT)
    n = int(h / pitch)
    for i in range(1, n + 1):
        yy = y + i * pitch
        if yy < y + h - 0.005:
            sh.line(x, yy, x + w, yy, w=LW_THIN, color="#b4b4b4")


def zone(sh, x, y, w, h, pitch=0.06):
    """A build-up nobody has specified: hatched, dashed, never solid."""
    sh.rect(x, y, w, h, fill="#f6f6f6", stroke=SPEC, sw=LW_THIN,
            dash="1.2 0.8")
    t = 0.0
    while t < w + h:
        ax, ay = x + t, y
        bx, by = x, y + t
        if ax > x + w:
            ay += ax - (x + w)
            ax = x + w
        if by > y + h:
            bx += by - (y + h)
            by = y + h
        if ay <= y + h and bx <= x + w:
            sh.line(ax, ay, bx, by, w=LW_THIN, color="#cfcfcf")
        t += pitch


# Every note on this sheet hangs in one column to the right of its
# detail.  Labels that wander find the next detail, the title block or
# the panel, and a detail sheet is mostly labels: one column, one
# direction, no exceptions.
NOTE_X = 0.46


def leader(sh, x, y, ty, text, size=1.9, color=INK):
    """A note in the column, with a line back to the thing it is about."""
    sh.line(x, y, NOTE_X - 0.03, ty, w=LW_THIN, color=GREY)
    sh.circle(x, y, 0.012, fill=INK, stroke=INK, sw=LW_THIN)
    sh.tag(NOTE_X, ty, text, size=size, color=color, anchor="start")


def spec_note(sh, x, y, ty, text, topic):
    """The same, for something that is not ours to name."""
    leader(sh, x, y, ty, text, color=SPEC)
    sh.tag(NOTE_X, ty - 0.075, f"{TBS} — QS-003, {topic}", size=1.6,
           color=SPEC, anchor="start")


# --------------------------------------------------------------------------
# D1 - the balcony slab edge
# --------------------------------------------------------------------------
def balcony_edge(sh):
    """Local origin: top of the structural slab at the slab edge."""
    z = G.STRUCTURAL_ZONE
    nose, cove = G.A_NOSING, G.A_COVE
    inb = G.V3_WAVE_BALUSTRADE

    concrete(sh, -1.05, -z, 1.05, z)
    # the nosing: the outer band of the edge, rounded off below
    sh.rect(-nose, -z - 0.06, nose, 0.06, fill="#d9d9d9", stroke=INK,
            sw=LW_CUT)
    sh.line(-nose, -z - 0.06, -nose, -z, w=LW_THIN, color=GREY)
    # the cove light, a recess in the soffit inboard of the nosing
    sh.rect(-nose - cove, -z - 0.005, cove, cove, fill="#ffffff",
            stroke=INK, sw=LW_SECONDARY)
    # the drip under the edge
    sh.rect(-0.06, -z - 0.06, 0.02, 0.012, fill=INK, stroke=INK, sw=LW_THIN)

    # what goes on top of it, none of which is ours
    zone(sh, -1.05, 0.0, 1.05 - inb, 0.055)
    # the glass, its channel, and the handrail
    sh.rect(-inb - 0.05, 0.0, 0.10, 0.09, fill="#e8e8e8", stroke=SPEC,
            sw=LW_SECONDARY)
    sh.rect(-inb - 0.008, 0.09, 0.016, G.BALUSTRADE_H - 0.09,
            fill="#e4ebee", stroke=SPEC, sw=LW_SECONDARY)
    sh.line(-inb - 0.03, G.BALUSTRADE_H, -inb + 0.03, G.BALUSTRADE_H,
            w=LW_CUT, color=SPEC)

    sh.line(-1.05, -z - 0.12, -1.05, 0.16, w=LW_THIN, color=GREY,
            dash="2 1.5")
    sh.tag(-1.02, 0.22, "SLAB CONTINUES", size=1.6, color=GREY,
           anchor="start")

    sh.dim_v(0.0, G.BALUSTRADE_H, 0.24,
             text=f"{G.BALUSTRADE_H * 1000:.0f}")
    sh.dim_v(-z, 0.0, -1.18, text=f"{z * 1000:.0f}")
    sh.dim_h(-nose, 0.0, -z - 0.22, text=f"{nose * 1000:.0f}")
    sh.dim_h(-inb, 0.0, 0.20, text=f"{inb * 1000:.0f}")

    spec_note(sh, -inb, G.BALUSTRADE_H * 0.7, 1.12,
              "GLASS BALUSTRADE AND CHANNEL", "External finishes")
    spec_note(sh, -0.50, 0.03, 0.62, "BALCONY FINISH AND FALLS",
              "External finishes")
    leader(sh, -0.60, -z * 0.5, 0.18,
           "RC SLAB — DEPTH BY THE ENGINEER")
    leader(sh, -nose - cove * 0.5, -z - cove * 0.5, -0.12,
           f"COVE LIGHT {cove * 1000:.0f} × {cove * 1000:.0f}")
    leader(sh, -0.05, -z - 0.055, -0.36, f"NOSING {nose * 1000:.0f}, DRIPPED")


# --------------------------------------------------------------------------
# D2 - the terrace parapet
# --------------------------------------------------------------------------
def parapet(sh):
    """Local origin: top of the roof structural slab at the inner face."""
    z = G.STRUCTURAL_ZONE
    t, h = G.PARAPET, 1.10
    up = 0.15                           # membrane turn-up, the minimum drawn

    concrete(sh, -0.95, -z, 0.95 + t, z)
    brick(sh, 0.0, 0.0, t, h)
    # coping, overhanging and dripped both sides
    sh.rect(-0.04, h, t + 0.08, 0.06, fill="#e2e2e2", stroke=SPEC,
            sw=LW_SECONDARY)
    for xx in (-0.03, t + 0.012):
        sh.rect(xx, h, 0.018, 0.012, fill=SPEC, stroke=SPEC, sw=LW_THIN)

    zone(sh, -0.95, 0.0, 0.95, 0.09)            # falls screed and build-up
    sh.line(-0.95, 0.09, 0.0, 0.055, w=LW_SECONDARY, color=SPEC)
    sh.line(0.0, 0.0, 0.0, up, w=LW_CUT, color=SPEC)
    sh.line(0.0, up, 0.045, up, w=LW_THIN, color=SPEC)

    sh.line(-0.95, -z - 0.10, -0.95, 0.20, w=LW_THIN, color=GREY,
            dash="2 1.5")
    sh.dim_v(0.0, h, -0.30, text=f"{h * 1000:.0f}")
    sh.dim_h(0.0, t, -z - 0.22, text=f"{t * 1000:.0f}")
    sh.dim_v(0.0, up, 0.34, text=f"{up * 1000:.0f} MIN")

    spec_note(sh, t * 0.5, h + 0.03, h + 0.16, "COPING, FIXING AND DRIP",
              "Roof")
    # the parapet is the one wall nobody has specified, so it is annotated
    # the way the unspecified things are, not the way the walls are
    spec_note(sh, t * 0.5, h * 0.55, h * 0.62,
              f"PARAPET {t * 1000:.0f} mm", "Masonry")
    spec_note(sh, 0.0, up * 0.6, 0.30, f"MEMBRANE UP {up * 1000:.0f} MIN",
              "Roof")
    spec_note(sh, -0.45, 0.05, -0.16,
              "FALLS SCREED AND INSULATION", "Roof")


# --------------------------------------------------------------------------
# D3 - the threshold
# --------------------------------------------------------------------------
def threshold(sh):
    """Local origin: finished floor level at the line of the door.

    Drawn at 1:5.  The whole point of the junction is a 75 mm step and a
    20 mm fall, and at 1:10 those are 7.5 and 2 mm of sheet - a detail
    that cannot be read is not a detail.
    """
    fin = 0.055                         # the finish zone, inside and out
    drop = 0.02                         # the fall away from the door
    deep = 0.16                         # as much slab as the junction needs

    # one slab, stepped on top: the fall is in the structure, not in the
    # finish, which is what keeps the finish thickness constant
    sh.poly([(-0.45, -fin - deep), (0.45, -fin - deep),
             (0.45, -fin - drop), (0.0, -fin - drop), (0.0, -fin),
             (-0.45, -fin)], fill="#d9d9d9", stroke=INK, sw=LW_CUT)
    zone(sh, -0.45, -fin, 0.45, fin, pitch=0.035)
    zone(sh, 0.14, -fin - drop, 0.31, fin, pitch=0.035)

    # the channel in front of the track, and its grating
    sh.rect(0.02, -fin - drop - 0.05, 0.10, 0.05, fill="#ffffff",
            stroke=SPEC, sw=LW_SECONDARY)
    for i in range(5):
        sh.line(0.03 + i * 0.02, -drop, 0.03 + i * 0.02, -drop - 0.012,
                w=LW_THIN, color=SPEC)
    # the track and the leaf standing on it
    sh.rect(-0.04, -fin + fin, 0.06, 0.024, fill="#e8e8e8", stroke=SPEC,
            sw=LW_SECONDARY)
    sh.rect(-0.032, 0.024, 0.018, 0.30, fill="#e4ebee", stroke=SPEC,
            sw=LW_SECONDARY)

    sh.line(-0.45, -fin - deep, 0.45, -fin - deep, w=LW_THIN, color=GREY,
            dash="2 1.5")
    sh.tag(-0.42, -fin - deep - 0.035, "SLAB CONTINUES", size=1.6,
           color=GREY, anchor="start")

    sh.dim_h(0.02, 0.12, -fin - deep + 0.02, text="100")
    sh.dim_v(-fin - drop, 0.0, -0.50, text=f"{(fin + drop) * 1000:.0f}")

    sh.tag(-0.40, 0.10, "INSIDE", size=1.9, color=GREY, anchor="start")
    sh.tag(0.42, 0.10, "BALCONY", size=1.9, color=GREY, anchor="end")
    spec_note(sh, -0.02, 0.22, 0.42, "SLIDING DOOR, TRACK AND SEALS",
              "Openings")
    spec_note(sh, 0.07, -fin - drop - 0.025, 0.08,
              "CHANNEL, GRATING AND OUTLET", "Services")
    spec_note(sh, 0.35, -drop - fin * 0.5, -0.12,
              "FLOOR FINISH, BOTH SIDES", "Internal finishes")
    leader(sh, 0.42, -fin - drop * 0.5, -0.27,
           f"STEP {(fin + drop) * 1000:.0f} AND FALL "
           f"{drop * 1000:.0f}, BOTH IN THE SLAB")


# --------------------------------------------------------------------------
# D4 - the roof upstand
# --------------------------------------------------------------------------
def upstand(sh):
    """Local origin: top of the roof slab at the face of the wall."""
    z = G.STRUCTURAL_ZONE
    up = 0.15
    chase = 0.025

    concrete(sh, -0.95, -z, 0.95, z)
    brick(sh, 0.0, -z, G.WT, 1.05)
    zone(sh, -0.95, 0.0, 0.95, 0.09)
    sh.line(-0.95, 0.09, 0.0, 0.055, w=LW_SECONDARY, color=SPEC)
    sh.line(0.0, 0.0, 0.0, up, w=LW_CUT, color=SPEC)
    # the flashing, chased into the wall above the turn-up
    sh.rect(0.0, up + 0.02, chase, 0.012, fill=SPEC, stroke=SPEC,
            sw=LW_THIN)
    sh.line(chase, up + 0.026, 0.0, up - 0.03, w=LW_SECONDARY, color=SPEC)
    zone(sh, G.WT, -z, 0.05, 1.05, pitch=0.05)          # external render

    sh.line(-0.95, -z - 0.10, -0.95, 0.20, w=LW_THIN, color=GREY,
            dash="2 1.5")
    sh.line(0.0, 1.05 - z, G.WT + 0.05, 1.05 - z, w=LW_THIN, color=GREY,
            dash="2 1.5")
    sh.dim_h(0.0, G.WT, -z - 0.22, text=f"{G.WT * 1000:.0f}")
    sh.dim_v(0.0, up, -0.22, text=f"{up * 1000:.0f} MIN")

    leader(sh, G.WT * 0.5, 0.55, 0.72,
           f"PENTHOUSE WALL, {G.WT * 1000:.0f} mm BRICK")
    spec_note(sh, chase, up + 0.026, 0.48, "FLASHING, CHASED AND POINTED",
              "Roof")
    spec_note(sh, G.WT + 0.025, 0.18, 0.08, "RENDER AND BELL-CAST STOP",
              "External finishes")
    spec_note(sh, -0.45, 0.05, -0.26, "FALLS SCREED AND INSULATION",
              "Roof")


DRAW = [balcony_edge, parapet, threshold, upstand]


def draw(sh, index, ox, oy):
    """Draw detail `index` with its local origin at sheet mm (ox, oy)."""
    D.set_scale(SCALES[index], ox, oy)
    DRAW[index](sh)


def scale_note(index):
    return f"1:{SCALES[index]}"
