#!/usr/bin/env python3
"""
plans.py - generates the drawing set for the four-storey vacation home.

  A-000  Site plan                             +0.00   1:75
  A-100  Ground floor plan                     +0.00   1:50
  A-101  First floor plan                      +3.30   1:50
  A-102  Second floor plan                     +6.60   1:50
  A-103  Third floor & roof plan                +9.90   1:50

Run:  python3 plans.py [output_dir]
"""

import math
import os
import sys

import drafting as D
from drafting import (Sheet, INK, GREY, LIGHT, LW_CUT, LW_SECONDARY,
                      LW_FIXTURE, LW_THIN, LW_HIDDEN)
import axonometric as ax
import deliverables as dl
import documents as doc
import elevations as el
import services as sv
import details as det
import structure as st
import fixtures as fx
import frame as F
from geometry import *          # noqa: F401,F403  (pure constants)

SITE_ORIGIN = (150.0, 390.0)     # 1:75
PLAN_ORIGIN = (-60.0, 450.0)     # 1:50, upper floors
GF_ORIGIN = (40.0, 495.0)        # 1:50, ground floor with the whole plot
PARAPET_FILL = "#6f6f6f"

# Gross internal area per floor: the whole plate, less the open terrace on
# the third floor.  The light court that used to be cut out of it went with
# revision P4, when the north and east boundaries were confirmed open.
PLATE = (a_x1 - a_x0) * (a_y1 - a_y0) + (b_x1 - b_x0) * (b_y1 - b_y0)
TER_S = (B_X1 - A_X0) * BALC_D                  # third floor, on the cantilever
TER_N = (b_x1 - b_x0) * (TER_N_Y1 - TER_N_Y0)   # third floor, block B
V_TER_N = (b_x1 - b_x0) * (b_y1 - V_TER_N_Y0)   # villa north terrace
BALC = [(BALC_A[1] - BALC_A[0]) * BALC_D, (BALC_B[1] - BALC_B[0]) * BALC_D]
GIA = {0: PLATE, 1: PLATE, 2: PLATE, 3: PLATE - TER_N}

# block A's north end: one room the full 6.05 m width on every floor
NORTH_A = (a_x1 - a_x0) * (a_y1 - CORE_N)

# Automatic opening vent at the stair head.  The stair enclosure stands in
# the middle of block A with no external wall, so it cannot be smoke
# ventilated by a window; the vent goes through the roof slab over the top
# landing instead.  Same figures drive the plan, the section and the notes.
AOV_X = (15.55, 17.70)
AOV_Y = (13.55, 14.10)
AOV_AREA = (AOV_X[1] - AOV_X[0]) * (AOV_Y[1] - AOV_Y[0])


# ===========================================================================
# shared pieces
# ===========================================================================
def boundary(sh, label=True):
    with sh.on("G-ANNO-BNDY"):
        sh.poly(PLOT, stroke=INK, sw=0.45, dash="6 1.5 1.2 1.5")
    if label:
        sh.tag(8.60, 5.40, "SITE BOUNDARY", size=1.9, color=GREY)


@fx.layer("A-ANNO-PATT")
def _hatch(sh, x, y, w, d, pitch=0.9, color="#e2e2e2"):
    n = int((w + d) / pitch)
    for i in range(n + 1):
        t = i * pitch
        ax, ay, bx, by = x + t, y, x, y + t
        if ax > x + w:
            ay += ax - (x + w); ax = x + w
        if by > y + d:
            bx += by - (y + d); by = y + d
        if ay <= y + d and bx <= x + w:
            sh.line(ax, ay, bx, by, w=LW_THIN, color=color)


def neighbours(sh):
    """Only the west boundary is built against; north and east are open."""
    _hatch(sh, 0.0, 5.0, 11.5, 13.6)
    sh.tag(5.7, 12.1, "NEIGHBOURING PLOT", size=2.8, color=LIGHT)
    sh.tag(5.7, 11.2, "BLIND WALL — NO OPENINGS", size=2.0, color=LIGHT)
    sh.tag(24.9, 11.0, "OPEN ASPECT — WINDOWS TO EAST", size=2.4,
           color=LIGHT, rot=-90)
    sh.tag(20.1, 18.9, "OPEN ASPECT — WINDOWS TO NORTH", size=2.4,
           color=LIGHT)


@fx.layer("L-SITE")
def street(sh, top=0.0, depth=3.4):
    """Carriageway below the plot."""
    y0 = top - depth
    sh.rect(-1.5, y0, 26.5, depth, fill="#f5f5f5", stroke="none", sw=0)
    sh.line(-1.5, top, 25.0, top, w=LW_SECONDARY, color=GREY)
    sh.line(-1.5, y0, 25.0, y0, w=LW_THIN, color=LIGHT)
    for i in range(10):
        x = -0.6 + i * 2.7
        sh.line(x, y0 + depth / 2, x + 1.4, y0 + depth / 2, w=LW_THIN,
                color=LIGHT)
    sh.tag(11.5, y0 + 0.85, "S T R E E T", size=3.4, color=GREY)


def shell(sh, floor):
    """External and party walls of both blocks."""
    o = OPENINGS[floor]
    sh.wall(A_X0, A_Y0, 17.85, A_Y0 + WT, openings=o["a_south"])
    sh.wall(A_X0, A_Y0, A_X0 + WT, A_Y1, openings=o["a_west"])
    sh.wall(A_X0, A_Y1 - WT, 17.85, A_Y1, openings=o["a_north"])
    sh.wall(PARTY_X0, A_Y0, PARTY_X1, B_Y1, openings=o["party"])
    sh.wall(b_x0, B_Y0, B_X1, B_Y0 + WT, openings=o["b_south"])
    sh.wall(B_X1 - WT, B_Y0, B_X1, B_Y1, openings=o["b_east"])
    sh.wall(b_x0, B_Y1 - WT, B_X1, B_Y1, openings=o["b_north"])


def columns(sh):
    """RC frame: 300 mm columns on the grid, every one inside a wall."""
    for cx in GRID_X:
        for cy in GRID_Y:
            fx.column(sh, cx, cy, COL)


def core_walls(sh):
    """Stair, lift and riser - identical on every floor."""
    # west wall of the core, from the lift up to the head of the stair.  It
    # stops there: north of the stair, block A is one room the full width.
    sh.wall(CORE_WALL_X, LF_Y0 - PT, ST_X0, CORE_N,
            openings=[(9.40, 10.28)])
    # south wall of the lift and riser cupboard
    sh.wall(CORE_WALL_X, LF_Y0 - PT, 17.85, LF_Y0)
    # between lift / riser and the protected lobby
    sh.wall(CORE_WALL_X, LF_Y1, 17.85, LOB_Y0,
            openings=[(15.70, 16.60), (17.32, 17.76)])
    # between the lobby and the stair
    sh.wall(CORE_WALL_X, LOB_Y1, 17.85, ST_Y0, openings=[(16.30, 17.20)])
    # north wall of the stair enclosure
    sh.wall(CORE_WALL_X, ST_Y1, 17.85, CORE_N)
    # between the lift shaft and the riser cupboard
    sh.wall(LF_X1, LF_Y0, RS_X0, LF_Y1)


def core_fittings(sh, floor):
    """Lift car, riser shafts, stair and the doors that serve them."""
    fx.lift(sh, LF_X0, LF_Y0, LF_X1, LF_Y1, door="n")
    fx.riser(sh, RS_X0, RS_Y0, RS_X1, RS_Y1)
    sh.line(RS_X0, 8.10, RS_X1, 8.10, w=LW_SECONDARY, color=GREY)
    sh.door(15.70, 16.60, LF_Y1, LOB_Y0, "h", leaf=False)
    sh.door(17.32, 17.76, LF_Y1, LOB_Y0, "h", hinge="lo", swing="up")
    sh.door(16.30, 17.20, LOB_Y1, ST_Y0, "h", hinge="lo", swing="down")
    sh.door(9.40, 10.28, CORE_WALL_X, ST_X0, "v", hinge="lo", swing="left")
    direction = {0: "up", 3: "dn"}.get(floor, "both")
    fx.stair(sh, (ST_X0, ST_Y0, ST_X1, ST_Y1), direction=direction,
             floor_to_floor=FLOOR_TO_FLOOR)


def core_rooms(sh, floor, lobby_name="Fire Lobby", stair_name=None):
    """Common parts, labelled the same way on every floor."""
    sh.room(LF_X0, LF_Y0, LF_X1 - LF_X0, LF_Y1 - LF_Y0, "Lift",
            area=(LF_X1 - LF_X0) * (LF_Y1 - LF_Y0), size=1.8,
            sched_name="Lift shaft", sub="shaft reserved", show_area=False,
            at=(16.25, 8.05))
    sh.room(LOB_X0, LOB_Y0, LOB_X1 - LOB_X0, LOB_Y1 - LOB_Y0, lobby_name,
            area=(LOB_X1 - LOB_X0) * (LOB_Y1 - LOB_Y0), size=1.9,
            show_area=False, at=(16.62, 9.73))
    name = stair_name or ("Stair Hall" if floor == 0 else "Landing")
    # on the top floor the north end of the landing carries the vent over,
    # so the label drops clear of it
    sh.room(ST_X0, ST_Y0, ST_X1 - ST_X0, ST_Y1 - ST_Y0, name,
            area=(ST_X1 - ST_X0) * (ST_Y1 - ST_Y0), size=2.0,
            sched_name="Protected stair", show_area=False,
            at=(16.62, 14.35 if floor == 3 else 13.95))


def parapet(sh, x0, y0, x1, y1, openings=()):
    sh.wall(x0, y0, x1, y1, openings=openings, fill=PARAPET_FILL)


def arch_note(sh, a, b, face, axis="h", side=1):
    """Dashed semicircular arch head over an opening."""
    r = (b - a) / 2.0
    mid = (a + b) / 2.0
    if axis == "h":
        a0, a1 = (180, 0) if side > 0 else (180, 360)
        cx, cy = mid, face
    else:
        a0, a1 = (-90, 90) if side > 0 else (90, 270)
        cx, cy = face, mid
    sh.arc(cx, cy, r, a0, a1, sw=LW_HIDDEN, color=GREY, dash="1.8 1.2")


def section_line(sh, y0=2.20, y1=18.95):
    """The A-A cut line, so the section can be located on every plan."""
    with sh.on("A-ANNO-SYMB"):
        sh.line(SEC_X, y0, SEC_X, y1, w=LW_THIN, color=INK,
                dash="9 2 1.6 2")
    for yy in (y0, y1):
        sh.circle(SEC_X, yy, 0.45, fill="#ffffff", stroke=INK,
                  sw=LW_SECONDARY)
        sh.tag(SEC_X, yy - 0.17, "A", size=2.6, color=INK)
    for yy in (y0 + 0.70, y1 - 0.70):
        sh.poly([(SEC_X - 0.62, yy), (SEC_X - 0.06, yy + 0.26),
                 (SEC_X - 0.06, yy - 0.26)], fill=INK, stroke=INK,
                sw=LW_THIN)


def balcony(sh, span, level_txt, name="Balcony", screen_w=True, label=True):
    """Cantilevered slab 1.20 m beyond the south wall, full width of a block.

    `screen_w` draws the west end screen; apartment B leaves it off because
    apartment A has already drawn the shared screen on the party wall line.
    """
    x0, x1 = span
    y0, y1 = A_Y0 - BALC_D, A_Y0
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill="#fbfbfb", stroke="none", sw=0)
    parapet(sh, x0, y0, x1, y0 + PARAPET)
    if screen_w:
        parapet(sh, x0, y0, x0 + PARAPET, y1)
    parapet(sh, x1 - PARAPET, y0, x1, y1)
    if label:
        # balconies are external, so they are labelled but kept out of the
        # area schedule, which totals internal area only
        sh.room(x0, y0, x1 - x0, BALC_D, name,
                area=(x1 - x0) * BALC_D, size=2.0, schedule=False,
                sub=level_txt, at=((x0 + x1) / 2, y0 + 0.66))


# a_west stays a single window: the west wall is the one blind elevation,
# open only over the 1.50 m where it faces the plot's own garden corridor.
OPENINGS = {
    # Villa ground floor (P5): two front doors, guest wing in block B.
    # The party wall opens twice - once at the south so the family can
    # greet guests, once at the north so the dirty kitchen can serve the
    # show kitchen.  Between them it backs onto the core.
    0: dict(a_south=[V_DOOR_FAMILY] + V_WIN_A_S,
            a_west=[WIN_W_LIVING],
            a_north=WIN_N_A,
            b_south=[V_DOOR_MAJLIS] + V_WIN_B_S,
            b_north=[V_DOOR_SERVICE] + V_WIN_B_N,
            party=[V_PARTY_HALL, V_PARTY_SERVE],
            b_east=V_WIN_B_E),
    1: dict(a_south=UP_A_SOUTH,
            a_west=[WIN_W_LIVING],
            a_north=WIN_N_A,
            b_south=UP_B_SOUTH,
            b_north=WIN_N_B,
            party=[(9.30, 10.20)],
            b_east=[WIN_E_LIV_B, WIN_E_BATH, WIN_E_BED, WIN_E_STUDY]),
    # Villa third floor (P5): roof majlis, gym, maid's suite and the fifth
    # bedroom.  The party wall is opened twice - the majlis into the guest
    # bedroom at the south, the gym onto the north terrace at the north.
    3: dict(a_south=UP_A_SOUTH,
            a_west=[WIN_W_LIVING],
            a_north=WIN_N_A,
            b_south=UP_B_SOUTH,
            b_north=[],
            party=[V_PARTY_MAJLIS, V_PARTY_TERRACE],
            b_east=V_WIN_B_E_3),
}


def north_windows(sh, floor):
    """Windows in the open north boundary wall of each block."""
    o = OPENINGS[floor]
    for a, b in o["a_north"]:
        sh.window(a, b, A_Y1 - WT, A_Y1, "h")
    for a, b in o["b_north"]:
        sh.window(a, b, B_Y1 - WT, B_Y1, "h")
# Floor 2 is still the apartment plan, so it keeps the openings floor 1 had
# before the villa conversion.  Floors 1 and 2 stop being identical here.
OPENINGS[2] = dict(OPENINGS[1])

# Villa first floor (P5): block A is the family floor, block B the second
# household's wing.  The party wall is opened once, at the south, which is
# the wing's own front door.
OPENINGS[1] = dict(a_south=UP_A_SOUTH,
                   a_west=[WIN_W_LIVING],
                   a_north=WIN_N_A,
                   b_south=UP_B_SOUTH,
                   b_north=WIN_N_B,
                   party=[V_PARTY_WING],
                   b_east=V_WIN_B_E_1)

# Villa second floor (P5): the bedroom floor.
OPENINGS[2] = dict(a_south=UP_A_SOUTH,
                   a_west=[WIN_W_LIVING],
                   a_north=WIN_N_A,
                   b_south=UP_B_SOUTH,
                   b_north=V_WIN_B_N_2,
                   party=[V_PARTY_BEDS],
                   b_east=V_WIN_B_E_2)


@fx.layer("L-SITE")
def garden(sh):
    """The entrance corridor: walkway, planting, pergola, barbecue, patio.

    Replanned for the 1.50 m extension: the building now stands at y = 3.50,
    so the walkway runs to its face and the patio in front of block B is
    3.10 m deep instead of 4.30 m.
    """
    walk_y0, walk_y1 = 1.55, 3.35
    fx.paving(sh, 0.30, walk_y0, 15.90, walk_y1 - walk_y0, pitch=0.9)
    sh.rect(0.30, walk_y0, 15.90, walk_y1 - walk_y0, sw=LW_SECONDARY,
            stroke=GREY)
    fx.grass(sh, 0.30, 0.35, 9.30, 1.05)
    fx.grass(sh, 0.30, 3.50, 11.05, 1.35)
    fx.planter(sh, 13.60, 0.35, 3.90, 1.05)
    for tx in (2.3, 4.8, 7.3):
        fx.tree(sh, tx, 4.20, 0.72)
    for tx in (1.7, 3.6):
        fx.tree(sh, tx, 0.90, 0.60)

    fx.pergola(sh, 5.10, 1.25, 4.00, 2.35, pitch=0.5)
    sh.tag(7.10, 3.78, "TIMBER PERGOLA OVER WALKWAY", size=2.0, color=GREY)

    fx.paving(sh, 9.90, 0.35, 3.20, 1.05, pitch=0.75, color="#dadada")
    sh.rect(9.90, 0.35, 3.20, 1.05, sw=LW_SECONDARY, stroke=GREY)
    fx.counter(sh, 10.15, 0.48, 2.10, 0.60)
    sh.tag(11.50, 1.18, "BARBECUE", size=2.0, color=GREY)

    fx.steps(sh, DOOR_ENTRY[0] - 0.35, 2.55, 1.80, 0.95, n=ENTRY_RISERS)
    fx.paving(sh, 18.15, 0.35, 4.55, 2.95, pitch=0.9, color="#dadada")
    sh.rect(18.15, 0.35, 4.55, 2.95, sw=LW_SECONDARY, stroke=GREY)
    fx.table(sh, 19.55, 1.45, 1.50, 0.85, seats_n=3, seats_s=3)
    sh.tag(20.42, 0.62, "OUTDOOR DINING", size=2.0, color=GREY)

    sh.arc(0.30, 1.40, 2.40, 0, 78, sw=LW_THIN, color=GREY)
    sh.line(0.30, 1.40, 2.70, 1.40, w=LW_FIXTURE, color=INK)
    sh.tag(1.9, 5.35, "MAIN GATE", size=2.2, color=INK)

    # the house stands 0.50 m above the garden
    fx.steps(sh, WIN_B_1[0] - 0.05, 2.55, 1.50, 0.95, n=ENTRY_RISERS)
    # bin store displaced by the compact kitchen, clear of the patio
    sh.rect(16.20, 0.35, 1.45, 1.05, sw=LW_SECONDARY, stroke=GREY,
            dash="2.0 1.2")
    sh.tag(16.93, 0.80, "BINS", size=1.8, color=GREY)


def villa_neighbours(sh):
    """The three neighbours, named by what was surveyed rather than hatched.

    Their heights are not decoration: the east wall can only be glazed
    because the house on that side is a single storey, and the west wall
    is blind partly because the house on that side is three and faces us
    with no openings.  A site plan that says only "neighbouring plot"
    throws that away.
    """
    _hatch(sh, 0.0, 5.0, 11.5, 14.55)
    sh.tag(5.70, 12.40, "NEIGHBOURING PLOT", size=2.6, color=LIGHT)
    sh.tag(5.70, 11.35, f"{NBR_W_STOREYS} STOREYS, BLIND TO OUR GARDEN",
           size=2.0, color=LIGHT)
    _hatch(sh, 11.5, 18.0, 11.5, 1.55)
    sh.tag(17.25, 18.75,
           f"NEIGHBOURING PLOT — {NBR_N_STOREYS} STOREY", size=2.0,
           color=LIGHT)
    _hatch(sh, 23.0, 0.0, 2.05, 19.55)
    sh.tag(23.75, 9.50, "NEIGHBOURING PLOT", size=2.2, color=LIGHT, rot=-90)
    sh.tag(24.65, 9.50, f"SINGLE STOREY, CLAY BRICK", size=2.0, color=LIGHT,
           rot=-90)


def villa_garden(sh):
    """Entrance garden west of the villa, forecourt in front of it.

    The three setbacks are our own land, so each becomes a 1.00 m paved
    side passage rather than a dead strip.  The forecourt is 3.50 m deep
    and the cantilever oversails up to 2.00 m of it, which is what makes
    the front door covered without a porch on the elevation.
    """
    # the 1.00 m side passages, on three sides
    for px, py, pw, pd in ew_side_passages():
        fx.paving(sh, px, py, pw, pd, pitch=1.0)
        sh.rect(px, py, pw, pd, sw=LW_THIN, stroke=GREY)

    # the west garden: gate, walk under a pergola, lawn, barbecue
    fx.paving(sh, *EW_WALK, pitch=0.9)
    sh.rect(*EW_WALK, sw=LW_SECONDARY, stroke=GREY)
    fx.grass(sh, *EW_LAWN_S)
    fx.grass(sh, *EW_LAWN_N)
    for tx, ty, tr in EW_TREES:
        fx.tree(sh, tx, ty, tr)
    fx.pergola(sh, *EW_PERGOLA, pitch=0.5)
    sh.tag(7.10, 3.78, "TIMBER PERGOLA OVER WALKWAY", size=2.0, color=GREY)

    fx.paving(sh, *EW_BBQ, pitch=0.75, color="#dadada")
    sh.rect(*EW_BBQ, sw=LW_SECONDARY, stroke=GREY)
    fx.counter(sh, *EW_BBQ_COUNTER)
    sh.tag(11.50, 1.18, "BARBECUE", size=2.0, color=GREY)

    gx, gy, gw = EW_GATE
    sh.arc(gx, gy, gw, 0, 78, sw=LW_THIN, color=GREY)
    sh.line(gx, gy, gx + gw, gy, w=LW_FIXTURE, color=INK)
    sh.tag(1.90, 5.35, "MAIN GATE", size=2.2, color=INK)

    # the forecourt east of the door, under the cantilever
    fx.paving(sh, *EW_FORECOURT, pitch=0.9, color="#dadada")
    sh.rect(*EW_FORECOURT, sw=LW_SECONDARY, stroke=GREY)
    fx.table(sh, 18.40, 1.40, 1.50, 0.85, seats_n=3, seats_s=3)
    sh.tag(21.75, 1.80, "OUTDOOR DINING", size=2.0, color=GREY, rot=-90)

    # three risers up to the front door, under the cantilever
    fx.steps(sh, V0_DOOR_ENTRY[0] - 0.20, 2.55, 1.50, 0.95, n=ENTRY_RISERS)
    sh.rect(*EW_BINS, sw=LW_SECONDARY, stroke=GREY, dash="2.0 1.2")
    sh.tag(22.50, 4.90, "BINS", size=1.6, color=GREY, rot=-90)


# ===========================================================================
# A-000  SITE PLAN
# ===========================================================================
def sheet_site():
    D.set_scale(75, *SITE_ORIGIN)
    sh = Sheet("A-000", "Site Plan — Detached Villa", "+0.00", "1:75 @ A1")
    sh.rev, sh.status = "P22", F.STATUS_FINAL_DRAFT
    F.border(sh)
    villa_neighbours(sh)
    street(sh)
    # the cantilever is drawn before the garden, not after: its tone is a
    # slab seen from above and would otherwise bury the forecourt under it
    fx.wave_balcony(sh, wave_points(), V3_Y0, V3_WAVE_BALUSTRADE,
                    V3_WAVE_REVEAL, label=None, area=None, show_area=False)
    villa_garden(sh)

    # the villa: its ground-floor shell and the frame
    sh.rect(V3_X0, V3_Y0, V3_X1 - V3_X0, V3_Y1 - V3_Y0, fill="#f1f1f1",
            stroke="none", sw=0)
    sh.wall(V3_X0, V3_Y0, V3_X1, V3_Y0 + WT, openings=V0_WIN_S)
    sh.wall(V3_X0, V3_Y0, V3_X0 + WT, V3_Y1, openings=V0_VENT_W)
    sh.wall(V3_X0, V3_Y1 - WT, V3_X1, V3_Y1, openings=V0_WIN_N)
    sh.wall(V3_X1 - WT, V3_Y0, V3_X1, V3_Y1, openings=V0_WIN_E)
    # the structural spine, which is what the two middle columns stand in
    sh.line(V3_GRID_X[1], V3_Y0, V3_GRID_X[1], V3_Y1, w=LW_THIN,
            color=LIGHT, dash="5 3")
    sh.tag(18.15, 5.20, "STRUCTURAL SPINE", size=1.7, color=GREY, rot=-90)
    for cx in V3_GRID_X:
        for cy in V3_GRID_Y:
            fx.column(sh, cx, cy, COL)

    sh.room(V3_X0, 8.0, V3_X1 - V3_X0, 3.0, "Detached Villa", area=None,
            sub="9.50 × 13.50 m — four storeys and a penthouse", size=3.0,
            schedule=False, show_area=False, at=(17.25, 9.60))
    sh.level_tag(19.30, 6.20, "FFL +0.00")
    sh.level_tag(6.20, 1.95, "GARDEN −0.50")

    for tx, ty, rot in ((12.00, 10.50, -90), (22.50, 11.50, -90)):
        sh.tag(tx, ty, "1.00 m SETBACK", size=1.9, color=GREY, rot=rot)
    sh.tag(17.25, 17.50, "1.00 m SETBACK", size=1.9, color=GREY)

    boundary(sh)
    sh.tag(5.60, 2.55, "ENTRANCE GARDEN", size=2.3, color=INK)
    sh.tag(14.60, 0.72, "CANTILEVER OVER", size=2.0, color=INK)

    sh.dim_h(0, 23.0, -4.8, ext_from=0.0)
    sh.dim_h(0, V3_X0 - SETBACK, -6.6)
    sh.dim_h(V3_X0 - SETBACK, V3_X0, -6.6)
    sh.dim_h(V3_X0, V3_X1, -6.6)
    sh.dim_h(V3_X1, V3_X1 + SETBACK, -6.6)
    sh.dim_v(0, 5.0, -1.8, ext_from=0.0)
    sh.dim_v(0, 18.0, -3.6)
    sh.dim_v(0, V3_Y0, 25.9, ext_from=23.0)
    sh.dim_v(V3_Y0, V3_Y1, 25.9)
    sh.dim_v(V3_Y1, 18.0, 25.9)

    F.heading(sh)
    y = F.legend(sh, 52)
    sh.schedule = [("Plot, south band  23.00 × 5.00", 115.00),
                   ("Plot, east part  11.50 × 13.00", 149.50)]
    y = F.schedule(sh, y + 8, extra=[
        ("Villa footprint  9.50 × 13.50 m",
         f"{(V3_X1 - V3_X0) * (V3_Y1 - V3_Y0):.1f} m²"),
        ("Site coverage", f"{128.25 / 264.5 * 100:.1f} %"),
        ("Entrance garden, west", "57.5 m²"),
        ("Forecourt, in front", "40.3 m²"),
        ("Setbacks, three sides", "38.5 m²"),
        ("Gross internal area, five storeys",
         f"{4 * V3_PLATE + V4_PLATE:.1f} m²")])
    F.notes(sh, y + 6, [
        "Final draft — layout agreed. The villa is detached: set back "
        "1.00 m from the west, north and east boundaries, the three sides "
        "a neighbour stands on. The south is not set back — it faces the "
        "street across our own forecourt.",
        f"Footprint 9.50 × 13.50 m = "
        f"{(V3_X1 - V3_X0) * (V3_Y1 - V3_Y0):.1f} m² on a 264.5 m² plot, "
        f"{128.25 / 264.5 * 100:.1f} % "
        "coverage against 63.0 % for the attached scheme at P4. Detaching "
        "costs 22 % of each floor and buys an open aspect on all four "
        "sides and no party wall.",
        "The setbacks are our own land, so each is a 1.00 m paved side "
        "passage rather than a dead strip, reached from the forecourt on "
        "the east and from the entrance garden on the west.",
        f"The cantilever oversails the forecourt by {V3_WAVE_DEEP:.2f} m "
        f"at each end and draws in to {V3_WAVE_WAIST:.2f} m at the waist, "
        f"leaving at least {GARDEN_D_E - V3_WAVE_DEEP:.2f} m clear to the "
        f"street, and "
        "covers the front door and its three risers. Nothing projects "
        "over a boundary, but the overhang is subject to the local "
        "projection rule; confirm before construction.",
        "The client's survey sketch recorded a 0.50 m step in the north "
        "boundary and a 5.50 m offset between the two blocks' north walls; "
        "the two cannot both be true. Resolved in favour of a straight "
        "boundary at 18.00. To be confirmed by measured survey before any "
        "work starts on site.",
        "Structure is an RC frame on the grid shown, 300 mm columns on "
        "wall centrelines so none stands in a room. The A-300 "
        "enlargements, the last sheets on the old 11.50 × 14.50 "
        "footprint, are withdrawn at P22.",
    ])
    F.compass_and_scale(sh, x=502.0, y=452.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-100  GROUND FLOOR
# ===========================================================================
def _plan_ground(sh):
    """Villa ground floor: guest wing in block B, family rooms in block A.

    Two front doors on the south elevation, as far apart as the frontage
    allows: the family at the west end of block A nearest the garden, the
    guests at the east end of block B straight into the majlis.  The core
    sits between the two, so the routes never cross.
    """
    neighbours(sh)
    garden(sh)
    boundary(sh)
    sh.level_tag(6.2, 1.95, "GARDEN \u22120.50")
    sh.tag(0.55, 4.45, "ENTRANCE GARDEN CORRIDOR", size=2.1, color=GREY,
           anchor="start")

    shell(sh, 0)
    core_walls(sh)
    columns(sh)

    # --- block A: entrance hall, gallery past the core, dining, kitchen ---
    sh.wall(a_x0, 10.50, CORE_WALL_X, 10.62, openings=[(12.60, 13.80)])
    sh.wall(a_x0, 14.60, CORE_WALL_X, CORE_N, openings=[(12.40, 13.60)])

    # --- block B: majlis, guest WC, service lobby, dirty kitchen ---------
    sh.wall(b_x0, 11.00, b_x1, 11.12,
            openings=[(18.50, 19.40), (20.80, 21.90)])
    sh.wall(20.00, 11.12, 20.12, 13.00)
    sh.wall(b_x0, 13.00, b_x1, 13.12, openings=[(20.80, 21.90)])

    # --- openings ---------------------------------------------------------
    sh.door(*V_DOOR_FAMILY, A_Y0, A_Y0 + WT, "h", hinge="lo", swing="up")
    arch_note(sh, *V_DOOR_FAMILY, A_Y0 + WT, side=1)
    for a, b in V_WIN_A_S:
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    sh.window(*WIN_W_LIVING, A_X0, A_X0 + WT, "v")
    sh.door(*V_DOOR_MAJLIS, B_Y0, B_Y0 + WT, "h", hinge="lo", swing="up")
    arch_note(sh, *V_DOOR_MAJLIS, B_Y0 + WT, side=1)
    for a, b in V_WIN_B_S:
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    for a, b in V_WIN_B_E:
        sh.window(a, b, B_X1 - WT, B_X1, "v")
    for a, b in WIN_N_A:
        sh.window(a, b, A_Y1 - WT, A_Y1, "h")
    for a, b in V_WIN_B_N:
        sh.window(a, b, B_Y1 - WT, B_Y1, "h")
    sh.door(*V_DOOR_SERVICE, B_Y1 - WT, B_Y1, "h", hinge="lo", swing="down")
    sh.door(*V_PARTY_HALL, PARTY_X0, PARTY_X1, "v", leaf=False)
    arch_note(sh, *V_PARTY_HALL, PARTY_X0, axis="v", side=-1)
    sh.door(*V_PARTY_SERVE, PARTY_X0, PARTY_X1, "v", leaf=False)

    core_fittings(sh, 0)
    sh.door(12.60, 13.80, 10.50, 10.62, "h", hinge="lo", swing="up")
    sh.door(12.40, 13.60, 14.60, CORE_N, "h", hinge="lo", swing="down")
    sh.door(18.50, 19.40, 11.00, 11.12, "h", hinge="lo", swing="up")
    sh.door(20.80, 21.90, 11.00, 11.12, "h", hinge="lo", swing="up")
    sh.door(20.80, 21.90, 13.00, 13.12, "h", hinge="lo", swing="up")

    # --- block A fittings -------------------------------------------------
    # entrance hall: console against the west wall, seat by the door
    fx.counter(sh, a_x0, 5.60, 0.45, 1.40)
    sh.rect(14.60, 4.00, 1.30, 0.60, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    # formal dining
    fx.table(sh, 12.35, 11.35, 1.10, 2.60, seats_e=3, seats_w=3)
    fx.wardrobe(sh, a_x0, 14.00, 1.60, 0.50)
    # show kitchen: run along the north wall under the windows, island south
    fx.counter(sh, a_x0, 17.00, 5.20, 0.65)
    fx.sink(sh, 12.20, 17.10, w=0.80, d=0.48)
    fx.hob(sh, 16.05, 17.08, w=0.95, d=0.55)
    fx.fridge(sh, 17.20, 15.10, 0.62, 1.30)
    fx.counter(sh, 12.60, 15.25, 2.80, 0.90)
    sh.tag(14.00, 15.62, "ISLAND", size=1.6, color=GREY)

    # --- block B fittings -------------------------------------------------
    # majlis: low seating round three sides, the Gulf arrangement
    fx.sofa(sh, b_x0, 4.30, 0.78, 5.60, facing="e")
    fx.sofa(sh, 21.92, 4.30, 0.78, 5.60, facing="w")
    fx.sofa(sh, 19.70, 10.05, 2.30, 0.78, facing="s")
    sh.rect(19.90, 6.60, 1.00, 1.00, rx=D.mm(0.1), sw=LW_FIXTURE,
            stroke=GREY)
    # guest WC
    fx.wc(sh, b_x0, 11.70, facing="e")
    fx.basin(sh, 19.10, 12.88, w=0.60, d=0.44, facing="s")
    # service lobby
    fx.wardrobe(sh, 22.12, 11.30, 0.58, 1.60, axis="v")
    # dirty kitchen: heavy cooking run on the east wall, prep against party
    fx.counter(sh, 22.05, 13.30, 0.65, 3.90)
    fx.sink(sh, 22.12, 13.55, w=0.50, d=0.75)
    fx.hob(sh, 22.10, 15.60, w=0.55, d=0.95)
    fx.counter(sh, b_x0, 13.30, 0.62, 2.40)
    fx.fridge(sh, b_x0, 16.10, 0.70, 1.40)

    # --- rooms ------------------------------------------------------------
    sh.room(a_x0, a_y0, a_x1 - a_x0, LF_Y0 - PT - a_y0, "Entrance Hall",
            area=20.4, size=2.4, sub="family entrance", at=(13.70, 4.60))
    sh.room(a_x0, LF_Y0 - PT, CORE_WALL_X - a_x0, 10.50 - (LF_Y0 - PT),
            "Gallery", area=11.1, size=1.9, show_area=False,
            at=(13.54, 8.90))
    sh.room(a_x0, 10.62, CORE_WALL_X - a_x0, 14.60 - 10.62, "Formal Dining",
            area=13.8, size=2.2, at=(13.54, 13.00))
    sh.room(a_x0, CORE_N, a_x1 - a_x0, a_y1 - CORE_N, "Show Kitchen",
            area=18.0, size=2.3, sub="open to the family", at=(14.60, 16.45))
    core_rooms(sh, 0, lobby_name="Landing", stair_name="Stair Hall")
    sh.room(b_x0, b_y0, b_x1 - b_x0, 11.00 - b_y0, "Majlis", area=32.8,
            size=2.6, sub="guests\u2019 entrance", at=(20.42, 7.60))
    sh.room(b_x0, 11.12, 20.00 - b_x0, 13.00 - 11.12, "Guest WC", area=3.5,
            size=1.7, show_area=False, at=(19.08, 12.30))
    sh.room(20.12, 11.12, b_x1 - 20.12, 13.00 - 11.12, "Service Lobby",
            area=4.9, size=1.7, show_area=False, at=(21.41, 12.30))
    sh.room(b_x0, 13.12, b_x1 - b_x0, b_y1 - 13.12, "Dirty Kitchen",
            area=20.8, size=2.2, sub="service door north",
            at=(20.42, 14.90))


def _villa_ground_floor(sh):
    """Detached villa, ground floor (P7): arrival, hosting and a guest suite.

    The west strip is the first and third floors' exactly - one open room
    from the south wall to the stair hall line with the stair standing in
    it.  Upstairs that room is the living area; here it is the reception
    hall, and the front door is in its south wall under the cantilever, so
    the entrance is covered without a porch being added to the elevation.

    The east strip takes dining and kitchen in the two south bands, next to
    each other as they have to be, and the guest suite in the quiet
    north-east corner on the north and east windows.  The services - guest
    WC, laundry and store - fill the north-west behind the reception hall,
    off a lobby that also reaches the guest bedroom through the spine.
    """
    # --- shell -----------------------------------------------------------
    sh.wall(V3_X0, V3_Y0, V3_X1, V3_Y0 + WT, openings=V0_WIN_S)
    sh.wall(V3_X0, V3_Y0, V3_X0 + WT, V3_Y1, openings=V0_VENT_W)
    sh.wall(V3_X0, V3_Y1 - WT, V3_X1, V3_Y1, openings=V0_WIN_N)
    sh.wall(V3_X1 - WT, V3_Y0, V3_X1, V3_Y1, openings=V0_WIN_E)

    # --- the spine -------------------------------------------------------
    sh.wall(V3_SPINE_X0, v3_y0, V3_SPINE_X1, v3_y1,
            openings=[V0_OPEN_DIN, V0_OPEN_KIT, V0_DOOR_GUEST])

    # --- the service block, against the west wall only -------------------
    # the hall turns the corner behind the stair and runs on to the north
    # wall, so these two rooms are all that is walled here
    sh.wall(v3_x0, V0_HALL_Y1, V0_WC_X1 + PT, V3_BED3_Y0)
    sh.wall(V0_WC_X1, V3_BED3_Y0, V0_WC_X1 + PT, v3_y1,
            openings=[V0_DOOR_WC, V0_DOOR_LAUN])
    sh.wall(v3_x0, V0_WC_Y1, V0_WC_X1, V0_WC_Y1 + PT)

    # --- the east strip: dining, kitchen, guest suite --------------------
    sh.wall(V3_SPINE_X1, V0_DIN_Y1, v3_x1, V0_DIN_Y1 + PT,
            openings=[V0_OPEN_SERVE])
    sh.wall(V3_SPINE_X1, V0_KIT_Y1, v3_x1, V0_KIT_Y1 + PT)
    sh.wall(V3_SPINE_X1, V0_ENS_Y1, v3_x1, V0_ENS_Y1 + PT,
            openings=[V0_DOOR_ENS])

    for cx in V3_GRID_X:
        for cy in V3_GRID_Y:
            fx.column(sh, cx, cy, COL)

    # --- the cantilever above, shown dashed: it covers the front door ----
    with sh.on("A-FLOR-OVER"):
        sh.poly(wave_points(), stroke=GREY, sw=LW_HIDDEN, dash="4 2.5",
                close=False)
        for x in (V3_X0, V3_X1):
            sh.line(x, V3_Y0 - V3_WAVE_DEEP, x, V3_Y0, w=LW_HIDDEN,
                    color=GREY, dash="4 2.5")
    sh.tag(17.25, 2.35, "BALCONY OVER — COVERED ENTRANCE", size=1.8,
           color=GREY)

    # --- the entrance steps, up from the forecourt -----------------------
    with sh.on("A-FLOR"):
        sx = V0_DOOR_ENTRY[0] - 0.45
        sw_ = V0_DOOR_ENTRY[1] - V0_DOOR_ENTRY[0] + 0.90
        for i in range(ENTRY_RISERS):
            sh.rect(sx, V3_Y0 - 0.30 * (i + 1), sw_, 0.30,
                    sw=LW_SECONDARY, stroke=GREY)
    sh.tag(sx + sw_ + 0.30, V3_Y0 - 0.45, f"{ENTRY_RISERS}R UP", size=1.6,
           color=GREY, anchor="start")
    sh.level_tag(12.90, 2.35, f"FORECOURT {GARDEN_LEVEL:+.2f}")

    # --- openings ---------------------------------------------------------
    for a, b in V0_WIN_S:
        if (a, b) == V0_DOOR_ENTRY:
            continue
        sh.window(a, b, V3_Y0, V3_Y0 + WT, "h")
    sh.door(*V0_DOOR_ENTRY, V3_Y0, V3_Y0 + WT, "h", hinge="lo", swing="up")
    for a, b in V0_WIN_N:
        sh.window(a, b, V3_Y1 - WT, V3_Y1, "h")
    for a, b in V0_WIN_E:
        sh.window(a, b, V3_X1 - WT, V3_X1, "v")
    for a, b in V0_VENT_W:
        fx.vent(sh, a, b, V3_X0, V3_X0 + WT, "v")

    sh.door(*V0_OPEN_DIN, V3_SPINE_X0, V3_SPINE_X1, "v", leaf=False)
    sh.door(*V0_OPEN_KIT, V3_SPINE_X0, V3_SPINE_X1, "v", leaf=False)
    sh.door(*V0_DOOR_GUEST, V3_SPINE_X0, V3_SPINE_X1, "v", hinge="lo",
            swing="right")
    sh.door(*V0_OPEN_SERVE, V0_DIN_Y1, V0_DIN_Y1 + PT, "h", leaf=False)
    sh.door(*V0_DOOR_ENS, V0_ENS_Y1, V0_ENS_Y1 + PT, "h", hinge="lo",
            swing="down")
    sh.door(*V0_DOOR_WC, V0_WC_X1, V0_WC_X1 + PT, "v", hinge="lo",
            swing="left")
    sh.door(*V0_DOOR_LAUN, V0_WC_X1, V0_WC_X1 + PT, "v", hinge="lo",
            swing="left")

    # --- the stair, in the same well as every floor above ----------------
    fx.stair(sh, V3_STAIR, direction="up", floor_to_floor=FLOOR_TO_FLOOR,
             rise_target=V3_STAIR_RISE, going=V3_STAIR_GOING,
             landing_d=V3_STAIR_LANDING, well=V3_STAIR_WELL)
    sh.line(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2], V3_STAIR[1],
            w=LW_SECONDARY, color=INK)
    sh.line(V3_STAIR[2], V3_STAIR[1], V3_STAIR[2], V3_STAIR[3],
            w=LW_SECONDARY, color=INK)
    sh.tag(V3_STAIR[2] + 0.22, 10.80, "OPEN STAIR — BALUSTRADE", size=1.6,
           color=GREY, rot=-90)

    # --- reception hall: seating facing the forecourt --------------------
    fx.sofa(sh, 13.10, 4.60, 0.90, 2.20, facing="e")
    fx.sofa(sh, 15.95, 4.60, 0.90, 2.20, facing="w")
    fx.sofa(sh, 13.90, 7.10, 1.90, 0.90, facing="s")
    fx.table(sh, 14.25, 5.45, 1.20, 0.80, rx=0.18)
    fx.wardrobe(sh, V3_SPINE_X0 - 0.45, 10.50, 0.45, 1.60, axis="v")

    # --- dining -----------------------------------------------------------
    fx.table(sh, 18.55, 4.90, 2.20, 1.00, seats_n=3, seats_s=3)

    # --- kitchen: counters along the east wall and the spine -------------
    fx.counter(sh, v3_x1 - 0.65, V0_DIN_Y1 + PT, 0.65, 3.36)
    fx.sink(sh, v3_x1 - 0.58, 8.95, w=0.50, d=0.45)
    fx.hob(sh, v3_x1 - 0.60, 10.30)
    fx.counter(sh, 18.50, V0_KIT_Y1 - 0.60, 2.50, 0.60)
    fx.fridge(sh, V3_SPINE_X1, 10.55, 0.75, 0.70)

    # --- guest ensuite ----------------------------------------------------
    fx.shower(sh, V3_SPINE_X1, V0_ENS_Y1 - 1.00, 1.00, 1.00)
    fx.basin(sh, 20.00, V0_ENS_Y1, w=0.55, d=0.42, facing="s")
    fx.wc(sh, v3_x1, 12.20, facing="w")

    # --- guest bedroom ----------------------------------------------------
    fx.bed(sh, 19.10, V0_ENS_Y1 + PT, 1.80, 2.10, head="s")
    for bx in (18.60, 20.95):
        sh.rect(bx, V0_ENS_Y1 + PT, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, V3_SPINE_X1, 14.70, 0.55, 1.90, axis="v")

    # --- guest WC ---------------------------------------------------------
    fx.wc(sh, 13.95, V0_WC_Y1, facing="s")
    fx.basin(sh, 13.20, V3_BED3_Y0, w=0.55, d=0.42, facing="n")

    # --- laundry and store ------------------------------------------------
    fx.counter(sh, v3_x0, v3_y1 - 0.62, V0_WC_X1 - v3_x0, 0.62)
    fx.sink(sh, v3_x0 + 0.10, v3_y1 - 0.55, w=0.46, d=0.44)

    # --- rooms ------------------------------------------------------------
    # L-shaped: the full west strip, turning the corner behind the stair and
    # running on to the north wall past the service block
    sh.room(v3_x0, v3_y0, V3_SPINE_X0 - v3_x0, V0_HALL_Y1 - v3_y0,
            "Reception Hall", area=43.1, size=2.6, sub="open — stair within",
            sched_name="Reception hall", at=(14.15, 8.60))
    sh.room(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2] - V3_STAIR[0],
            V3_STAIR[3] - V3_STAIR[1], "Stair", area=6.6, size=1.9,
            show_area=False, at=(13.80, 12.15))
    sh.room(v3_x0, V3_BED3_Y0, V0_WC_X1 - v3_x0, V0_WC_Y1 - V3_BED3_Y0,
            "Guest WC", area=3.2, size=1.7, sched_name="Guest WC",
            show_area=False, at=(13.60, 12.95))
    sh.room(v3_x0, V0_WC_Y1 + PT, V0_WC_X1 - v3_x0, v3_y1 - V0_WC_Y1 - PT,
            "Laundry", area=4.1, size=1.7, sub="and store",
            show_area=False, at=(13.60, 15.30))
    sh.room(V3_SPINE_X1, v3_y0, v3_x1 - V3_SPINE_X1, V0_DIN_Y1 - v3_y0,
            "Dining", area=17.2, size=2.4, at=(19.95, 7.35))
    sh.room(V3_SPINE_X1, V0_DIN_Y1 + PT, v3_x1 - V3_SPINE_X1,
            V0_KIT_Y1 - V0_DIN_Y1 - PT, "Kitchen", area=14.2, size=2.4,
            at=(19.60, 9.60))
    sh.room(V3_SPINE_X1, V0_KIT_Y1 + PT, v3_x1 - V3_SPINE_X1,
            V0_ENS_Y1 - V0_KIT_Y1 - PT, "Guest Ensuite", area=6.5, size=1.7,
            sched_name="Guest ensuite", show_area=False, at=(20.20, 12.55))
    sh.room(V3_SPINE_X1, V0_ENS_Y1 + PT, v3_x1 - V3_SPINE_X1,
            v3_y1 - V0_ENS_Y1 - PT, "Guest Bedroom", area=13.4, size=2.4,
            sched_name="Guest bedroom", at=(19.95, 16.20))

    villa_section_line(sh)
    villa_section_line_b(sh)

def sheet_ground():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-100", "Ground Floor Plan \u2014 Detached Villa", "+0.00",
               "1:50 @ A1")
    sh.rev, sh.status = "P22", F.STATUS_FINAL_DRAFT
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(13.90, 17.55, "1.00 m SETBACK", size=1.8, color=GREY)

    _villa_ground_floor(sh)

    sh.dim_h(V3_X0, V3_X1, 0.95, ext_from=V3_Y0)
    sh.dim_h(V3_X0, V3_GRID_X[1], -0.30)
    sh.dim_h(V3_GRID_X[1], V3_X1, -0.30)
    sh.dim_v(V3_Y0, V3_Y1, 10.70, ext_from=V3_X0)
    # west strip: the reception hall, then the service band
    sh.dim_v(V3_Y0, V0_HALL_Y1, 11.35)
    sh.dim_v(V0_HALL_Y1, V3_Y1, 11.35)
    # east strip, room by room, south to north
    sh.dim_v(V3_Y0, V0_DIN_Y1, 23.25)
    sh.dim_v(V0_DIN_Y1, V0_KIT_Y1, 23.25)
    sh.dim_v(V0_KIT_Y1, V0_ENS_Y1, 23.25)
    sh.dim_v(V0_ENS_Y1, V3_Y1, 23.25)

    sh.tag(24.00, 7.00, "OPEN ASPECT \u2014 WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT \u2014 WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY \u2014 NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)

    sh.level_tag(13.00, 4.25, "FFL +0.00")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{V3_PLATE:.1f} m\u00b2"),
        ("Bedrooms", "1 \u2014 the guest suite; 8 above"),
        ("Floor above", "+3.30")])
    F.notes(sh, y + 6, [
        "Final draft — layout agreed. The floor you receive people on: the "
        "family living is upstairs where the balconies are, so this one "
        "takes arrival, eating and a guest suite for anyone who cannot "
        "manage the stair.",
        "Hall, dining and kitchen are one open sequence. The spine is "
        "cased open to both at 2.60 and 1.60 m, and the kitchen serves the "
        "dining through a 2.50 m opening rather than a door. Only the "
        "guest suite and the two service rooms are closed.",
        "The reception hall is the whole west strip at 43.1 m², with the "
        "stair standing in it. It turns the corner behind the stair and "
        "runs on to the north wall, so the guest bedroom opens off the "
        "hall and there is no circulation room anywhere on the floor.",
        "Guest WC, laundry and store are one block against the west wall, "
        "the only part of this floor that is walled off. East and north "
        "carry ordinary windows, the west louvred ventilation only.",
        "The front door is in the hall's south wall, under the cantilever, "
        "which projects about 1.75 m there — so the entrance is covered "
        "without a porch being added to the elevation. Three risers up "
        "from the forecourt at −0.50.",
        "Bedrooms are numbered 1 to 11 through the house, south to "
        "north and west before east on each floor; the ground "
        "floor's room is the guest bedroom and carries no number.",
        "The A-300 enlargements are withdrawn at P22: they show the "
        "apartment building, not this one.",
    ])

    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-101 / A-102  APARTMENT FLOORS
# ===========================================================================
def _plan_apartment(sh, floor, level):
    shell(sh, floor)
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=OPENINGS[floor]["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=OPENINGS[floor]["b_south"])
    core_walls(sh)
    columns(sh)
    balcony(sh, BALC_A, f"{level[:-1]}7")
    balcony(sh, BALC_B, f"{level[:-1]}7", screen_w=False)

    # apartment A.  The bathroom now sits beside the entry hall, so it is
    # reached from the front door and from the bedroom without crossing the
    # living room, and the south-east bay is given over to the kitchenette
    # against the party wall.
    sh.wall(a_x0, 8.86, CORE_WALL_X, 8.98, openings=[(13.50, 14.70)])
    sh.wall(13.28, 8.98, 13.40, 11.30, openings=[(9.60, 10.40)])
    sh.wall(a_x0, 11.30, CORE_WALL_X, 11.42, openings=[(13.40, 14.60)])
    sh.wall(a_x0, 13.00, CORE_WALL_X, 13.12, openings=[(11.95, 13.15)])

    # apartment B
    sh.wall(b_x0, 9.00, b_x1, 9.12, openings=[(18.60, 19.50)])
    sh.wall(20.28, 9.12, 20.40, 11.10, openings=[(9.35, 10.15)])
    sh.wall(b_x0, 11.10, b_x1, 11.22, openings=[(18.55, 19.45)])
    sh.wall(b_x0, 15.40, b_x1, 15.52, openings=[(21.40, 22.30)])

    for a, b in OPENINGS[floor]["a_south"]:
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in OPENINGS[floor]["b_south"]:
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    sh.window(*WIN_W_LIVING, A_X0, A_X0 + WT, "v")
    for a, b in OPENINGS[floor]["b_east"]:
        sh.window(a, b, B_X1 - WT, B_X1, "v")
    north_windows(sh, floor)
    core_fittings(sh, floor)
    sh.door(9.30, 10.20, PARTY_X0, PARTY_X1, "v", hinge="lo", swing="right")
    sh.door(13.50, 14.70, 8.86, 8.98, "h", leaf=False)
    sh.door(9.60, 10.40, 13.28, 13.40, "v", hinge="lo", swing="right")
    sh.door(13.40, 14.60, 11.30, 11.42, "h", hinge="lo", swing="up")
    sh.door(11.95, 13.15, 13.00, 13.12, "h", hinge="lo", swing="up")
    sh.door(18.60, 19.50, 9.00, 9.12, "h", hinge="lo", swing="up")
    sh.door(9.35, 10.15, 20.28, 20.40, "v", hinge="lo", swing="right")
    sh.door(18.55, 19.45, 11.10, 11.22, "h", hinge="lo", swing="up")
    sh.door(21.40, 22.30, 15.40, 15.52, "h", hinge="hi", swing="up")

    # apartment A fittings
    fx.sofa(sh, a_x0, 5.00, 0.85, 2.00, facing="e")
    fx.sofa(sh, 13.00, 4.05, 2.00, 0.85, facing="s")
    sh.rect(12.80, 5.30, 1.10, 0.62, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.kitchenette(sh, 17.20, 4.20, 0.65, 2.90, axis="v")
    fx.table(sh, 15.70, 4.25, 1.20, 0.95, seats_e=2, seats_w=2)
    fx.basin(sh, 12.54, 9.04, w=0.58, d=0.42, facing="n")
    fx.wc(sh, a_x0, 9.98, facing="e")
    fx.shower(sh, 12.15, 10.18, 1.05, 1.05)
    fx.wardrobe(sh, 13.52, 9.20, 0.55, 1.50, axis="v")
    fx.wardrobe(sh, a_x0, 11.52, 3.40, 0.58)
    fx.wardrobe(sh, a_x0, 12.36, 3.40, 0.58)
    # bed centred on the north wall between its two windows, the way the
    # room reads now that it runs the full 6.05 m width
    fx.bed(sh, 13.95, 15.55, 1.80, 2.10, head="n")
    for bx in (13.45, 15.80):
        sh.rect(bx, 17.10, 0.45, 0.55, sw=LW_FIXTURE, stroke=GREY)
    fx.counter(sh, 12.05, 17.05, 1.50, 0.62)
    sh.rect(12.05, 15.20, 0.78, 0.78, rx=D.mm(0.1), sw=LW_FIXTURE,
            stroke=GREY)
    fx.tv(sh, 17.15, 15.60, 1.20, axis="v")

    # apartment B fittings
    fx.kitchenette(sh, b_x0, 6.10, 0.65, 2.80, axis="v")
    fx.sofa(sh, 20.90, 4.95, 0.85, 2.00, facing="w")
    fx.tv(sh, 19.05, 5.00, 1.30, axis="v")
    fx.table(sh, 19.30, 7.55, 1.30, 0.85, seats_n=2, seats_s=2)
    fx.wardrobe(sh, b_x0, 9.25, 0.58, 1.75, axis="v")
    fx.bathtub(sh, 20.55, 9.30, 1.70, 0.75)
    fx.wc(sh, 22.70, 10.65, facing="w")
    fx.basin(sh, 21.30, 11.10, w=0.62, d=0.45, facing="s")
    fx.bed(sh, 19.60, 12.20, 1.80, 2.10, head="n")
    for bx in (19.05, 21.45):
        sh.rect(bx, 13.75, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, b_x0, 15.60, 0.58, 2.00, axis="v")
    fx.counter(sh, 21.00, 17.05, 1.70, 0.62)

    sh.room(a_x0, a_y0, 3.48, 5.06, "Living · Dining · Kitchen", area=26.3,
            size=2.3, sub="apartment A", sched_name="Apt A living / kitchen",
            at=(13.54, 6.45))
    sh.room(a_x0, 8.98, 1.48, 2.32, "Bath", area=3.4, size=1.7,
            sched_name="Apt A bathroom", at=(12.66, 10.70))
    sh.room(13.40, 8.98, 1.88, 2.32, "Hall", area=4.4, size=1.8,
            sched_name="Apt A entry hall", at=(14.34, 10.60))
    sh.room(a_x0, 11.42, 3.48, 1.58, "Dressing", area=5.5, size=1.9,
            sched_name="Apt A dressing", at=(13.54, 12.20))
    sh.room(a_x0, CORE_N, a_x1 - a_x0, a_y1 - CORE_N, "Bedroom", area=23.6,
            size=2.4, sub="north windows", sched_name="Apt A bedroom",
            at=(12.80, 16.55))
    core_rooms(sh, floor)
    sh.room(b_x0, b_y0, 4.55, 5.20, "Living · Dining · Kitchen", area=23.7,
            size=2.3, sub="apartment B", sched_name="Apt B living / kitchen",
            at=(20.60, 6.55))
    sh.room(b_x0, 9.12, 2.13, 1.98, "Hall", area=4.2, size=1.8,
            sched_name="Apt B entry hall", at=(19.20, 10.55))
    sh.room(20.40, 9.12, 2.30, 1.98, "Bath", area=4.6, size=1.8,
            sched_name="Apt B bathroom", at=(21.55, 10.45))
    sh.room(b_x0, 11.22, 4.55, 4.18, "Bedroom", area=19.0, size=2.4,
            sched_name="Apt B bedroom", at=(20.42, 14.85))
    sh.room(b_x0, 15.52, 4.55, 2.18, "Dressing / Study", area=9.9, size=2.0,
            sched_name="Apt B dressing / study", at=(20.42, 16.60))



def _apartment_floor(number, title, level, floor):
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet(number, title, level, "1:50 @ A1")
    F.border(sh)
    _plan_apartment(sh, floor, level)
    sh.dim_h(A_X0, B_X1, 1.6, ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 0.4)
    sh.dim_h(A_X1, B_X1, 0.4)
    sh.dim_v(A_Y0, A_Y1, 10.4, ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, ext_from=B_X1)
    sh.dim_v(B_Y0, 9.00, 26.0)
    sh.dim_v(9.00, 11.10, 26.0)
    sh.dim_v(11.10, B_Y1, 26.0)
    sh.tag(23.45, 13.20, "OPEN BOUNDARY — WINDOWS TO EAST",
           size=2.0, color=INK, rot=-90)
    sh.level_tag(12.10, 4.55, f"FFL {level}")
    sh.level_tag(18.60, 12.60, f"FFL {level}")

    section_line(sh)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[floor]:.1f} m²"),
        ("Apartment A / apartment B", "64.7 / 63.2 m²"),
        ("Balcony A / B (external)",
         f"{BALC[0]:.1f} / {BALC[1]:.1f} m²")])
    F.notes(sh, y + 6, [
        "Two one-bedroom apartments off the protected fire lobby: "
        "apartment A occupies block A around the core, apartment B the "
        "whole of block B. Balconies run the full width of each block, "
        "cantilevered 1.20 m with a 1.10 m parapet.",
        "Both units are planned open: living, dining and kitchenette read "
        "as one room with no corridor, and every other room — bathroom "
        "included — opens off the entry hall.",
        "Wet rooms stack onto the party wall spine. The riser cupboard "
        "carrying the soil, water and extract risers is entered from the "
        "fire lobby, not from either apartment.",
        "North and east are open boundaries. Block B is windowed on the "
        "east at every level and block A's bedroom takes two windows in "
        "the north wall, so every habitable room is daylit and naturally "
        "ventilated. The west wall is the only blind elevation.",
        "Escape is by a single protected stair, adopted on the client's "
        "instruction: FD30S doors onto the fire lobby, sprinklers "
        "throughout. The stair has no external wall, so it is smoke-"
        f"vented by a {AOV_AREA:.1f} m² automatic opening vent at its head "
        "— see A-103 and A-200. The governing code is still to be named "
        "and the strategy agreed.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def _villa_bedroom_floor(sh):
    """Detached villa, second floor (P6): the bedroom floor.

    Two suites and two further bedrooms, planned around a stair well that
    is fixed in plan by the floor above: the stair stacks, so it is the one
    thing here that could not be moved to suit the rooms.

    Suite 1 takes the south-west with the street frontage, suite 2 the
    south-east, bedrooms 3 and 4 the north.  The shared bath sits between
    the two bedrooms and the landing.  Because the stair sits against the
    west wall in the middle of the plate, the spine faces suite 1 along its
    whole southern length and the south-east corner cannot be reached from
    the landing directly - so a small inner lobby off the landing serves
    suite 2 and the bath.

    There is no hall between the two north bedrooms: bedroom 3 has it, and
    takes the whole north-west quarter.  The spur it replaced served one
    door at each end and both had somewhere better to go - bedroom 3 is
    entered from the landing through its own south wall, bedroom 4 from the
    lobby, which already serves suite 2 and the bath.  So the spine carries
    one opening on this floor rather than two.

    The east strip is set out on the first floor's lines: shared bath 5.4 m2
    and lobby 4.8 m2, the sizes they are below, with suite 2's bedroom wall
    1.30 m further north to take up the slack.  Every wet-room divider and
    every east window therefore stacks, which is what the drainage wants and
    what gives the east elevation one set of openings instead of two.

    Both suites open onto the south cantilever - the same wave as the floors
    above and below, so it now runs all three storeys.
    """
    # --- shell: the third floor's envelope, 1.00 m off three boundaries ---
    sh.wall(V3_X0, V3_Y0, V3_X1, V3_Y0 + WT, openings=V2_WIN_S)
    sh.wall(V3_X0, V3_Y0, V3_X0 + WT, V3_Y1, openings=V2_VENT_W)
    sh.wall(V3_X0, V3_Y1 - WT, V3_X1, V3_Y1, openings=V2_WIN_N)
    sh.wall(V3_X1 - WT, V3_Y0, V3_X1, V3_Y1, openings=V2_WIN_E)

    # --- the spine, structural and full depth, as on every floor ---------
    # one opening, and it is an opening rather than a door: the lobby is
    # open to the landing over its whole length, as on the first floor, so
    # the two read as one space with the frame standing in it.  It runs
    # between the columns at y 8.46 and 12.56, which stay.
    sh.wall(V3_SPINE_X0, v3_y0, V3_SPINE_X1, v3_y1,
            openings=[V2_SPINE_OPEN])

    # --- suite 1: bedroom south, ensuite and dressing behind it ----------
    sh.wall(v3_x0, V2_S1_BED_Y1, V3_SPINE_X0, V2_S1_BED_Y1 + PT,
            openings=[V2_DOOR_S1_BED])
    sh.wall(V2_S1_ENS_X1, V2_S1_BED_Y1 + PT, V2_S1_ENS_X1 + PT, V2_S1_Y1,
            openings=[V2_DOOR_S1_ENS])
    sh.wall(v3_x0, V2_S1_Y1, V3_SPINE_X0, V2_S1_Y1 + PT,
            openings=[V2_DOOR_S1])

    # --- suite 2: bedroom south, its ensuite beside the lobby behind -----
    # both doors sit in this one wall, so the bedroom comes straight off the
    # lobby and the ensuite straight off the bedroom
    sh.wall(V3_SPINE_X1, V2_S2_BED_Y1, v3_x1, V2_S2_BED_Y1 + PT,
            openings=[V2_DOOR_S2, V2_DOOR_S2_ENS])

    # --- the lobby, and the ensuite and shared bath stacked beside it ----
    sh.wall(V2_LOBBY_X1, V2_S2_BED_Y1 + PT, V2_LOBBY_X1 + PT, V3_STAIR[3],
            openings=[V2_DOOR_BATH])
    sh.wall(V2_LOBBY_X1 + PT, V2_ENS2_Y1, v3_x1, V2_ENS2_Y1 + PT)
    sh.wall(V3_SPINE_X1, V3_STAIR[3], v3_x1, V3_BED3_Y0,
            openings=[V2_DOOR_BED4_LOBBY])

    # --- bedroom 3, the whole north-west quarter -------------------------
    # one wall closes the landing, and bedroom 3 is entered through it; the
    # partition that made the hall a separate room has gone
    sh.wall(v3_x0, V3_STAIR[3], V3_SPINE_X0, V3_BED3_Y0,
            openings=[V2_DOOR_BED3])

    for cx in V3_GRID_X:
        for cy in V3_GRID_Y:
            fx.column(sh, cx, cy, COL)

    # --- the same wavy cantilever the floors above and below carry --------
    fx.wave_balcony(sh, wave_points(), V3_Y0, V3_WAVE_BALUSTRADE,
                    V3_WAVE_REVEAL, label="Balcony",
                    level_txt=V2_BALC_LEVEL, area=wave_area(),
                    show_area=False, label_y=3.03)

    # --- openings ---------------------------------------------------------
    for a, b in V2_WIN_S:
        if (a, b) in (V2_DOOR_BALC_1, V2_DOOR_BALC_2):
            fx.slider(sh, a, b, V3_Y0, V3_Y0 + WT, "h")
        else:
            sh.window(a, b, V3_Y0, V3_Y0 + WT, "h")
    for a, b in V2_WIN_N:
        sh.window(a, b, V3_Y1 - WT, V3_Y1, "h")
    for a, b in V2_WIN_E:
        sh.window(a, b, V3_X1 - WT, V3_X1, "v")
    for a, b in V2_VENT_W:
        fx.vent(sh, a, b, V3_X0, V3_X0 + WT, "v")

    sh.door(*V2_DOOR_S1, V2_S1_Y1, V2_S1_Y1 + PT, "h", hinge="lo",
            swing="down")
    sh.door(*V2_DOOR_S1_BED, V2_S1_BED_Y1, V2_S1_BED_Y1 + PT, "h",
            hinge="hi", swing="up")
    sh.door(*V2_DOOR_S1_ENS, V2_S1_ENS_X1, V2_S1_ENS_X1 + PT, "v",
            hinge="lo", swing="left")
    sh.door(*V2_SPINE_OPEN, V3_SPINE_X0, V3_SPINE_X1, "v", leaf=False)
    sh.door(*V2_DOOR_S2, V2_S2_BED_Y1, V2_S2_BED_Y1 + PT, "h",
            hinge="lo", swing="down")
    sh.door(*V2_DOOR_S2_ENS, V2_S2_BED_Y1, V2_S2_BED_Y1 + PT, "h",
            hinge="hi", swing="up")
    sh.door(*V2_DOOR_BATH, V2_LOBBY_X1, V2_LOBBY_X1 + PT, "v", hinge="lo",
            swing="right")
    sh.door(*V2_DOOR_BED3, V3_STAIR[3], V3_BED3_Y0, "h", hinge="lo",
            swing="up")
    sh.door(*V2_DOOR_BED4_LOBBY, V3_STAIR[3], V3_BED3_Y0, "h", hinge="lo",
            swing="up")

    # --- the stair, in the same well as the floor above -------------------
    fx.stair(sh, V3_STAIR, direction="both", floor_to_floor=FLOOR_TO_FLOOR,
             rise_target=V3_STAIR_RISE, going=V3_STAIR_GOING,
             landing_d=V3_STAIR_LANDING, well=V3_STAIR_WELL)
    sh.line(V3_STAIR[2], V3_STAIR[1], V3_STAIR[2], V3_STAIR[3],
            w=LW_SECONDARY, color=INK)
    sh.tag(V3_STAIR[2] + 0.22, 10.80, "OPEN STAIR — BALUSTRADE", size=1.6,
           color=GREY, rot=-90)
    # the linen cupboard used to back onto the spine; the spine is open
    # there now, so it would have stood free in the gap. It moves to the
    # solid stretch of the landing's north wall, east of bedroom 3's door.
    fx.wardrobe(sh, 16.61, 11.87, 0.65, 0.55, axis="h")

    # --- suite 1 ----------------------------------------------------------
    fx.bed(sh, 13.30, 4.80, 1.80, 2.10, head="n")
    for bx in (12.85, 15.15):
        sh.rect(bx, 6.45, 0.40, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 16.81, 4.00, 0.50, 2.20, axis="v")
    fx.shower(sh, 12.90, 7.90, 1.00, 1.00)
    fx.wc(sh, 14.45, V2_S1_Y1, facing="s")
    fx.basin(sh, 13.40, V2_S1_BED_Y1 + PT, w=0.60, d=0.45, facing="n")
    fx.wardrobe(sh, 16.76, V2_S1_BED_Y1 + PT, 0.55,
                V2_S1_Y1 - V2_S1_BED_Y1 - PT, axis="v")

    # --- suite 2: the deeper room the east strip now gives it -------------
    # the bed backs onto the north wall, clear of the sliding door in the
    # south wall and of the east windows
    fx.bed(sh, 19.10, 6.50, 1.80, 2.10, head="n")
    sh.rect(18.75, 8.15, 0.35, 0.45, sw=LW_FIXTURE, stroke=GREY)
    sh.rect(20.95, 8.15, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 17.73, 4.00, 0.50, 2.00, axis="v")
    # shower in the far corner, basin on the north wall, WC on the east -
    # all three clear of the door swing, which sweeps the south-east corner
    fx.shower(sh, V2_LOBBY_X1 + PT, V2_ENS2_Y1 - 1.00, 1.00, 1.00)
    fx.basin(sh, 20.60, V2_ENS2_Y1, w=0.55, d=0.42, facing="s")
    fx.wc(sh, v3_x1, 10.00, facing="w")

    # --- shared bath: fittings along the east wall ------------------------
    fx.wc(sh, v3_x1, 10.90, facing="w")
    fx.basin(sh, v3_x1, 11.90, w=0.55, d=0.42, facing="w")
    fx.shower(sh, 20.00, 11.25, 1.05, 1.05)

    # --- bedroom 3: a double now that it has the hall's width -------------
    fx.bed(sh, 13.30, 12.66, 1.80, 2.10, head="s")
    for bx in (12.85, 15.10):
        sh.rect(bx, 12.66, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, V3_SPINE_X0 - 0.55, 13.10, 0.55, 2.00, axis="v")

    # --- bedroom 4 --------------------------------------------------------
    fx.bed(sh, 19.10, 12.66, 1.80, 2.10, head="s")
    for bx in (18.60, 20.95):
        sh.rect(bx, 12.66, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 17.73, 14.60, 0.50, 1.90, axis="v")

    # --- rooms ------------------------------------------------------------
    sh.room(v3_x0, v3_y0, V3_SPINE_X0 - v3_x0, V2_S1_BED_Y1 - v3_y0,
            "Bedroom 4", area=14.0, size=2.4, sub="suite",
            sched_name="Bedroom 4 — suite", at=(15.90, 5.30))
    sh.room(v3_x0, V2_S1_BED_Y1 + PT, V2_S1_ENS_X1 - v3_x0,
            V2_S1_Y1 - V2_S1_BED_Y1 - PT, "Ensuite 4", area=4.4, size=1.7,
            sched_name="Bedroom 4 ensuite", show_area=False,
            at=(14.45, 7.70))
    sh.room(V2_S1_ENS_X1 + PT, V2_S1_BED_Y1 + PT, V3_SPINE_X0 - V2_S1_ENS_X1,
            V2_S1_Y1 - V2_S1_BED_Y1 - PT, "Dressing 4", area=4.3, size=1.7,
            sched_name="Bedroom 4 dressing", show_area=False,
            at=(16.00, 8.02))
    sh.room(V3_SPINE_X1, v3_y0, v3_x1 - V3_SPINE_X1, V2_S2_BED_Y1 - v3_y0,
            "Bedroom 5", area=19.6, size=2.4, sub="suite",
            sched_name="Bedroom 5 — suite", at=(19.95, 4.35))
    sh.room(V2_LOBBY_X1 + PT, V2_S2_BED_Y1 + PT, v3_x1 - V2_LOBBY_X1 - PT,
            V2_ENS2_Y1 - V2_S2_BED_Y1 - PT, "Ensuite 5", area=4.2, size=1.7,
            sched_name="Bedroom 5 ensuite", show_area=False,
            at=(19.80, 9.15))
    sh.room(V3_SPINE_X1, V2_S2_BED_Y1 + PT, V2_LOBBY_X1 - V3_SPINE_X1,
            V3_STAIR[3] - V2_S2_BED_Y1 - PT, "Lobby", area=4.8, size=1.7,
            sub="open", show_area=False, at=(18.25, 11.70))
    sh.room(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2] - V3_STAIR[0],
            V3_STAIR[3] - V3_STAIR[1], "Stair", area=6.6, size=1.9,
            show_area=False, at=(13.80, 12.15))
    sh.room(V3_STAIR[2] + PT, V3_STAIR[1], V3_SPINE_X0 - V3_STAIR[2] - PT,
            V3_STAIR[3] - V3_STAIR[1], "Landing", area=7.9, size=2.0,
            show_area=False, at=(16.10, 10.90))
    sh.room(V2_LOBBY_X1 + PT, V2_ENS2_Y1 + PT, v3_x1 - V2_LOBBY_X1 - PT,
            V3_STAIR[3] - V2_ENS2_Y1 - PT, "Shared Bath", area=5.4, size=1.8,
            sched_name="Shared bath", show_area=False, at=(20.05, 10.70))
    sh.room(v3_x0, V3_BED3_Y0, V3_SPINE_X0 - v3_x0, v3_y1 - V3_BED3_Y0,
            "Bedroom 6", area=18.8, size=2.4, at=(15.30, 16.20))
    sh.room(V3_SPINE_X1, V3_BED3_Y0, v3_x1 - V3_SPINE_X1, v3_y1 - V3_BED3_Y0,
            "Bedroom 7", area=17.0, size=2.4, at=(19.80, 16.30))

    villa_section_line(sh)
    villa_section_line_b(sh)

def sheet_second():
    """A-102: the villa's bedroom floor - two suites and two bedrooms.

    The first and third floors are planned around a living area; this one is
    not, so it is drawn on its own rather than shared with either.  What it
    does share is the east strip, which is set out on the first floor's
    lines exactly: every basin, WC and shower here sits directly over its
    twin below, so each wet room is one drainage stack dropping straight to
    the ground rather than a run of pipe chased sideways through a ceiling.
    The stair well, the spine, the column grid and the south cantilever line
    through for the same reason - nothing transfers.
    """
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-102", "Second Floor Plan — Detached Villa", "+6.60",
               "1:50 @ A1")
    sh.rev, sh.status = "P21", F.STATUS_FINAL_DRAFT
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(13.90, 17.55, "1.00 m SETBACK", size=1.8, color=GREY)

    _villa_bedroom_floor(sh)

    # the horizontal chains now clear the cantilever, as on the other two
    # floors: the balcony comes as close as y 1.50 at its west end
    sh.dim_h(V3_X0, V3_X1, 0.95, ext_from=V3_Y0)
    sh.dim_h(V3_X0, V3_GRID_X[1], -0.30)
    sh.dim_h(V3_GRID_X[1], V3_X1, -0.30)
    sh.dim_v(V3_Y0, V3_Y1, 10.70, ext_from=V3_X0)
    # west strip: suite 1's bedroom, its ensuite and dressing, then the hall
    sh.dim_v(V3_Y0, V2_S1_BED_Y1, 11.35)
    sh.dim_v(V2_S1_BED_Y1, V2_S1_Y1, 11.35)
    sh.dim_v(V2_S1_Y1, V3_BED3_Y0, 11.35)
    sh.dim_v(V3_BED3_Y0, V3_Y1, 11.35)
    # east strip, room by room, south to north - the first floor's chain
    sh.dim_v(V3_Y0, V2_S2_BED_Y1, 23.25)
    sh.dim_v(V2_S2_BED_Y1, V2_ENS2_Y1, 23.25)
    sh.dim_v(V2_ENS2_Y1, V3_BED3_Y0, 23.25)
    sh.dim_v(V3_BED3_Y0, V3_Y1, 23.25)
    # the cantilever's two ends, both at the deep end of the serpentine
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 22.45)

    sh.tag(24.00, 7.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY — NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)
    sh.tag(17.25, 0.25, f"CANTILEVER — SERPENTINE, {V3_WAVE_DEEP:.2f} m "
           f"AT EACH END → {V3_WAVE_WAIST:.2f} m AT THE WAIST",
           size=2.0, color=INK)

    sh.level_tag(13.00, 4.25, "FFL +6.60")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{V3_PLATE:.1f} m²"),
        ("Balcony, external", f"{wave_area():.1f} m²"),
        ("Bedrooms", "4 — two of them suites"),
        ("Floor above / below", "+9.90 / +3.30")])
    F.notes(sh, y + 6, [
        "Final draft — layout agreed. A bedroom floor: bedrooms 4 to 7, "
        "two of them suites, on the detached envelope.",
        "Bedrooms are numbered 1 to 11 through the house, south to "
        "north and west before east on each floor; the ground "
        "floor's room is the guest bedroom and carries no number.",
        "Bedroom 4 takes the south-west with its ensuite and dressing "
        "behind; bedroom 5 the south-east, its ensuite off the bedroom.",
        "The east strip is the first floor's, line for line — shared bath "
        "5.4 m², lobby 4.8 m², bedroom 5 at 19.6 m² as its wall moves "
        "1.30 m north. Every wet room and east window stacks, one drainage "
        "stack each, straight to the ground.",
        "The lobby has no door: the spine is opened its whole length "
        "between the columns, so lobby and landing read as one space. It "
        "serves bedroom 5, the shared bath and bedroom 7. Bedroom 6 has "
        "the old hall — the whole north-west quarter, 18.8 m².",
        f"The cantilever is carried here too — the same serpentine, "
        f"{V3_WAVE_DEEP:.2f} m at each end, {V3_WAVE_WAIST:.2f} m at the "
        f"waist, {wave_area():.1f} m². Both suites open onto it; a screen "
        f"between them is worth considering.",
    ])

    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def _villa_living_floor(sh):
    """Detached villa, first floor (P6): the living floor.

    A living area and three sleeping rooms.  The living area takes the
    south-west with the stair standing in it and the pantry in its corner -
    the third floor's west strip exactly, so the two line through and the
    pantry's plumbing stacks.  The east strip follows the second floor
    instead: master bedroom and ensuite over the south-east, lobby and
    shared bath behind them, a bedroom across the north.

    The floor is therefore a copy of neither neighbour while every wet room
    still sits over or under its counterpart.
    """
    # --- shell -----------------------------------------------------------
    sh.wall(V3_X0, V3_Y0, V3_X1, V3_Y0 + WT, openings=V1_WIN_S)
    sh.wall(V3_X0, V3_Y0, V3_X0 + WT, V3_Y1, openings=V1_VENT_W)
    sh.wall(V3_X0, V3_Y1 - WT, V3_X1, V3_Y1, openings=V1_WIN_N)
    sh.wall(V3_X1 - WT, V3_Y0, V3_X1, V3_Y1, openings=V1_WIN_E)

    # --- the spine -------------------------------------------------------
    # the spine carries no wall along the lobby: see V1_SPINE_OPEN
    sh.wall(V3_SPINE_X0, v3_y0, V3_SPINE_X1, v3_y1,
            openings=[V1_SPINE_OPEN, V2_DOOR_BED4])

    # --- master bedroom, with both its doors in one wall ------------------
    sh.wall(V3_SPINE_X1, V1_MBED_Y1, v3_x1, V1_MBED_Y1 + PT,
            openings=[V2_DOOR_S2, V2_DOOR_S2_ENS])

    # --- the lobby, with the ensuite and shared bath stacked beside it ---
    sh.wall(V2_LOBBY_X1, V1_MBED_Y1 + PT, V2_LOBBY_X1 + PT, V3_STAIR[3],
            openings=[V1_DOOR_BATH])
    sh.wall(V2_LOBBY_X1 + PT, V1_ENS_Y1, v3_x1, V1_ENS_Y1 + PT)
    sh.wall(V3_SPINE_X1, V3_STAIR[3], v3_x1, V3_BED3_Y0)

    # --- bedroom 2, the one wall across the west strip -------------------
    # the hall beside it stops at V3_HALL_Y1; past that the bedroom turns
    # the corner and runs through to the spine
    sh.wall(v3_x0, V1_LIV_Y1, V3_BED3_X1, V3_BED3_Y0)
    sh.wall(V3_BED3_X1, V3_BED3_Y0, V3_BED3_X1 + PT, V3_HALL_Y1,
            openings=[V3_DOOR_BED3])
    sh.wall(V3_BED3_X1, V3_HALL_Y1, V3_SPINE_X0, V3_HALL_Y1 + PT)

    for cx in V3_GRID_X:
        for cy in V3_GRID_Y:
            fx.column(sh, cx, cy, COL)

    # --- the same wavy cantilever the third floor carries ----------------
    fx.wave_balcony(sh, wave_points(), V3_Y0, V3_WAVE_BALUSTRADE,
                    V3_WAVE_REVEAL, label="Balcony",
                    level_txt=V1_BALC_LEVEL, area=wave_area(),
                    show_area=False, label_y=3.03)

    # --- openings ---------------------------------------------------------
    for a, b in V1_WIN_S:
        if (a, b) in (V1_DOOR_BALC, V1_DOOR_BALC_M):
            fx.slider(sh, a, b, V3_Y0, V3_Y0 + WT, "h")
        else:
            sh.window(a, b, V3_Y0, V3_Y0 + WT, "h")
    for a, b in V1_WIN_N:
        sh.window(a, b, V3_Y1 - WT, V3_Y1, "h")
    for a, b in V1_WIN_E:
        sh.window(a, b, V3_X1 - WT, V3_X1, "v")
    for a, b in V1_VENT_W:
        fx.vent(sh, a, b, V3_X0, V3_X0 + WT, "v")

    sh.door(*V1_SPINE_OPEN, V3_SPINE_X0, V3_SPINE_X1, "v", leaf=False)
    sh.door(*V2_DOOR_S2, V1_MBED_Y1, V1_MBED_Y1 + PT, "h",
            hinge="lo", swing="down")
    sh.door(*V2_DOOR_S2_ENS, V1_MBED_Y1, V1_MBED_Y1 + PT, "h",
            hinge="hi", swing="up")
    sh.door(*V1_DOOR_BATH, V2_LOBBY_X1, V2_LOBBY_X1 + PT, "v", hinge="lo",
            swing="right")
    sh.door(*V2_DOOR_BED4, V3_SPINE_X0, V3_SPINE_X1, "v", hinge="lo",
            swing="right")
    sh.door(*V3_DOOR_BED3, V3_BED3_X1, V3_BED3_X1 + PT, "v", hinge="lo",
            swing="left")

    # --- the stair, standing in the living area ---------------------------
    fx.stair(sh, V3_STAIR, direction="both", floor_to_floor=FLOOR_TO_FLOOR,
             rise_target=V3_STAIR_RISE, going=V3_STAIR_GOING,
             landing_d=V3_STAIR_LANDING, well=V3_STAIR_WELL)
    sh.line(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2], V3_STAIR[1],
            w=LW_SECONDARY, color=INK)
    sh.line(V3_STAIR[2], V3_STAIR[1], V3_STAIR[2], V3_STAIR[3],
            w=LW_SECONDARY, color=INK)
    sh.tag(V3_STAIR[2] + 0.22, 10.80, "OPEN STAIR — BALUSTRADE", size=1.6,
           color=GREY, rot=-90)

    # --- living area ------------------------------------------------------
    fx.tv(sh, V3_SPINE_X0 - 0.16, 4.55, w=1.50, axis="v")
    fx.sofa(sh, 13.10, 4.50, 0.88, 2.20, facing="e")
    fx.sofa(sh, 14.30, 6.60, 1.90, 0.88, facing="s")
    fx.table(sh, 14.40, 5.30, 1.10, 0.70, rx=0.18)
    fx.table(sh, 15.40, 9.60, 1.40, 0.90, seats_n=2, seats_s=2)

    # --- pantry: an open counter run against the spine --------------------
    px0, py0, px1, py1 = V1_PANTRY
    fx.counter(sh, px0, py0, px1 - px0, py1 - py0)
    fx.sink(sh, px0 + 0.10, py0 + 0.22, w=0.40, d=0.42)
    sh.rect(px0 + 0.16, py0 + 1.00, 0.24, 0.22, rx=D.mm(0.03),
            sw=LW_FIXTURE, stroke=GREY)                      # kettle
    sh.rect(px0 + 0.14, py0 + 1.45, 0.28, 0.30, rx=D.mm(0.03),
            sw=LW_FIXTURE, stroke=GREY)                      # coffee machine
    sh.tag(px0 - 0.22, (py0 + py1) / 2.0, "PANTRY",
           size=1.6, color=GREY, rot=-90)

    # --- master bedroom ---------------------------------------------------
    fx.bed(sh, 19.10, 6.50, 1.80, 2.10, head="n")
    sh.rect(18.75, 8.15, 0.35, 0.45, sw=LW_FIXTURE, stroke=GREY)
    sh.rect(20.95, 8.15, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 17.73, 4.00, 0.50, 2.00, axis="v")

    # --- master ensuite ---------------------------------------------------
    # shower in the far corner, basin on the north wall, WC on the east -
    # all three clear of the door swing, which sweeps the south-east corner
    fx.shower(sh, V2_LOBBY_X1 + PT, V1_ENS_Y1 - 1.00, 1.00, 1.00)
    fx.basin(sh, 20.60, V1_ENS_Y1, w=0.55, d=0.42, facing="s")
    fx.wc(sh, v3_x1, 10.00, facing="w")

    # --- shared bath: fittings along the east wall ------------------------
    fx.wc(sh, v3_x1, 10.90, facing="w")
    fx.basin(sh, v3_x1, 11.90, w=0.55, d=0.42, facing="w")
    fx.shower(sh, 20.00, 11.25, 1.05, 1.05)

    # --- bedroom 2 --------------------------------------------------------
    # the wardrobe used to back onto the hall partition; that partition now
    # stops at V3_HALL_Y1, so it moves to the spine in the part of the room
    # that was the dead end of the hall
    fx.bed(sh, 13.20, 12.66, 1.60, 2.00, head="s")
    fx.wardrobe(sh, V3_SPINE_X0 - 0.55, 14.80, 0.55, 1.75, axis="v")

    # --- bedroom 3 --------------------------------------------------------
    fx.bed(sh, 19.10, 12.66, 1.80, 2.10, head="s")
    for bx in (18.60, 20.95):
        sh.rect(bx, 12.66, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 17.73, 14.60, 0.50, 1.90, axis="v")

    # --- rooms ------------------------------------------------------------
    sh.room(v3_x0, v3_y0, V3_SPINE_X0 - v3_x0, V1_LIV_Y1 - v3_y0,
            "Living Area", area=32.3, size=2.6,
            sub="open plan",
            sched_name="Living area", at=(14.15, 8.60))
    sh.room(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2] - V3_STAIR[0],
            V3_STAIR[3] - V3_STAIR[1], "Stair", area=6.6, size=1.9,
            show_area=False, at=(13.80, 12.15))
    sh.room(V3_SPINE_X1, v3_y0, v3_x1 - V3_SPINE_X1, V1_MBED_Y1 - v3_y0,
            "Bedroom 1", area=19.6, size=2.4, sub="master suite",
            sched_name="Bedroom 1 — master", at=(19.95, 4.35))
    sh.room(V2_LOBBY_X1 + PT, V1_MBED_Y1 + PT, v3_x1 - V2_LOBBY_X1 - PT,
            V1_ENS_Y1 - V1_MBED_Y1 - PT, "Ensuite 1", area=4.2,
            size=1.7, sched_name="Bedroom 1 ensuite", show_area=False,
            at=(19.60, 8.88))
    sh.room(V3_SPINE_X1, V1_MBED_Y1 + PT, V2_LOBBY_X1 - V3_SPINE_X1,
            V3_STAIR[3] - V1_MBED_Y1 - PT, "Lobby", area=4.8, size=1.7,
            sub="open", show_area=False, at=(18.25, 11.70))
    sh.room(V2_LOBBY_X1 + PT, V1_ENS_Y1 + PT, v3_x1 - V2_LOBBY_X1 - PT,
            V3_STAIR[3] - V1_ENS_Y1 - PT, "Shared Bath", area=5.4, size=1.8,
            sched_name="Shared bath", show_area=False, at=(20.05, 10.70))
    # L-shaped: the strip west of the hall, plus the full width north of it
    sh.room(v3_x0, V3_BED3_Y0, V3_BED3_X1 - v3_x0, v3_y1 - V3_BED3_Y0,
            "Bedroom 2", area=16.4, size=2.4, at=(14.60, 16.00))
    sh.room(V3_HALL_X0, V3_BED3_Y0, V3_SPINE_X0 - V3_HALL_X0,
            V3_HALL_Y1 - V3_BED3_Y0, "Hall", area=2.0, size=1.8,
            show_area=False, at=(16.79, 12.95))
    sh.room(V3_SPINE_X1, V3_BED3_Y0, v3_x1 - V3_SPINE_X1, v3_y1 - V3_BED3_Y0,
            "Bedroom 3", area=17.0, size=2.4, at=(19.80, 16.30))

    villa_section_line(sh)
    villa_section_line_b(sh)

def sheet_first():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-101", "First Floor Plan — Detached Villa", "+3.30",
               "1:50 @ A1")
    sh.rev, sh.status = "P21", F.STATUS_FINAL_DRAFT
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(13.90, 17.55, "1.00 m SETBACK", size=1.8, color=GREY)

    _villa_living_floor(sh)

    sh.dim_h(V3_X0, V3_X1, 0.95, ext_from=V3_Y0)
    sh.dim_h(V3_X0, V3_GRID_X[1], -0.30)
    sh.dim_h(V3_GRID_X[1], V3_X1, -0.30)
    sh.dim_v(V3_Y0, V3_Y1, 10.70, ext_from=V3_X0)
    sh.dim_v(V3_Y0, V1_LIV_Y1, 11.35)
    sh.dim_v(V1_LIV_Y1, V3_Y1, 11.35)
    sh.dim_v(V3_Y0, V1_MBED_Y1, 23.25)
    sh.dim_v(V1_MBED_Y1, V1_ENS_Y1, 23.25)
    sh.dim_v(V1_ENS_Y1, V3_BED3_Y0, 23.25)
    sh.dim_v(V3_BED3_Y0, V3_Y1, 23.25)
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 22.45)

    sh.tag(24.00, 7.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY — NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)
    sh.tag(17.25, 0.25, f"CANTILEVER — SERPENTINE, {V3_WAVE_DEEP:.2f} m "
           f"AT EACH END → {V3_WAVE_WAIST:.2f} m AT THE WAIST",
           size=2.0, color=INK)

    sh.level_tag(13.00, 4.25, "FFL +3.30")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{V3_PLATE:.1f} m²"),
        ("Balcony, external", f"{wave_area():.1f} m²"),
        ("Bedrooms", "3 — the master, bedrooms 2 and 3"),
        ("Floor above / below", "+6.60 / +0.00")])
    F.notes(sh, y + 6, [
        "Final draft — layout agreed. The living floor: a living area and "
        "bedrooms 1 to 3. The living area is 32.3 m² with the stair "
        "standing in it and the pantry open along the spine, opening "
        "through a sliding door onto the cantilever.",
        "Bedrooms are numbered 1 to 11 through the house, south to "
        "north and west before east on each floor; the ground "
        "floor's room is the guest bedroom and carries no number.",
        "Bedroom 1 is the master at 19.6 m²: its north wall sits 1.30 m "
        "further north than the suite below it, and the shared bath gives "
        "up the same depth at 5.4 m².",
        "The pantry is a counter against the solid stretch of spine, not "
        "the walled room the third floor has. The lobby has no wall "
        "either: the spine is opened 3.69 m between the columns, a "
        "downstand beam rather than a wall.",
        "The west strip is otherwise the third floor's and the east strip "
        "the second's, so the wet rooms stack and the stair lines through. "
        "East and north carry ordinary windows, the west louvred "
        "ventilation only. The hall to the north bedrooms stops at its "
        "last door; the dead end beyond goes to bedroom 2, 16.4 m².",
        f"The cantilever runs on all three upper floors and the penthouse "
        f"— the same serpentine, {V3_WAVE_DEEP:.2f} m deep at each end "
        f"drawing in to {V3_WAVE_WAIST:.2f} m at the waist, "
        f"{wave_area():.1f} m² — with sliding "
        "doors from the living area and bedroom 1.",
    ])

    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def _wet_room(sh, y0, y1, fittings_north):
    """Shower, WC and basin in a room the full width of the east strip.

    Every fitting backs onto the same long wall - basin, WC, then shower in
    the corner - which is how a wet room is actually built: one drainage
    run, one wall of tiling, and the other side left clear to walk.  They
    were drawn floating in the middle of the room before, with the basin
    half through the south wall and the WC cistern standing in open floor.

    `fittings_north` puts them on the far wall from the door, so the leaf
    never sweeps across a fitting.
    """
    wall = y1 if fittings_north else y0
    face = "s" if fittings_north else "n"          # back to the wall
    fx.basin(sh, 18.30, wall, w=0.65, d=0.45, facing=face)
    fx.wc(sh, 19.50, wall, facing=face)
    fx.shower(sh, 20.45, wall - 1.05 if fittings_north else wall, 1.05, 1.05)


def _plan_third(sh):
    """Detached villa, third floor (P6): open living area, two suites,
    bedroom 3 and the shared bath, behind a wavy south cantilever.

    The building stands 1.00 m clear of the west, north and east
    boundaries, so nothing here is a party wall and there is no line that
    can only be opened where a room happens to sit on both sides of it.
    That is what the earlier schemes never had.  One structural spine
    divides the plate: the west strip carries the open living area, the
    stair, the hall and bedroom 3; the east strip carries the two suites
    and, in the north-east corner, the shared bath.

    The stair is a domestic stair in a single dwelling, so it is open to
    the living area - no enclosure, no fire lobby, no lift, and no smoke
    vent.  Removing that sealed box is what makes the living area open.
    """
    # --- shell: 1.00 m off three boundaries, hard to the south -----------
    sh.wall(V3_X0, V3_Y0, V3_X1, V3_Y0 + WT,
            openings=V3_WIN_S_LIV + V3_WIN_S_S1)
    sh.wall(V3_X0, V3_Y0, V3_X0 + WT, V3_Y1, openings=V3_VENT_W)
    sh.wall(V3_X0, V3_Y1 - WT, V3_X1, V3_Y1, openings=V3_WIN_N)
    sh.wall(V3_X1 - WT, V3_Y0, V3_X1, V3_Y1, openings=V3_WIN_E)

    # --- the spine, and the walls either side of it ----------------------
    sh.wall(V3_SPINE_X0, v3_y0, V3_SPINE_X1, v3_y1,
            openings=[V3_DOOR_S1, V3_DOOR_S2, V3_DOOR_BATH])
    # no wall between the living area and the stair - the stair stands in
    # the living space.  The pantry is the only enclosure in the west strip
    # apart from bedroom 3.
    sh.wall(V3_PANT_X0 - PT, V3_PANT_Y0 - PT, V3_PANT_X1, V3_PANT_Y0,
            openings=[V3_PANT_OPEN])
    sh.wall(V3_PANT_X0 - PT, V3_PANT_Y1, V3_PANT_X1, V3_PANT_Y1 + PT)
    sh.wall(V3_PANT_X0 - PT, V3_PANT_Y0, V3_PANT_X0, V3_PANT_Y1)
    # bedroom 3, the one wall across the strip; the hall beside it stops at
    # V3_HALL_Y1 and the bedroom turns the corner behind it
    sh.wall(v3_x0, V3_LIV_Y1, V3_BED3_X1, V3_BED3_Y0)
    sh.wall(V3_BED3_X1, V3_BED3_Y0, V3_BED3_X1 + PT, V3_HALL_Y1,
            openings=[V3_DOOR_BED3])
    sh.wall(V3_BED3_X1, V3_HALL_Y1, V3_SPINE_X0, V3_HALL_Y1 + PT)
    # east strip, south to north: suite 1, shared bath, suite 2
    sh.wall(V3_SPINE_X1, V3_S1_ENS_Y0 - PT, v3_x1, V3_S1_ENS_Y0,
            openings=[(17.80, 18.70)])
    sh.wall(V3_SPINE_X1, V3_S1_Y1, v3_x1, V3_S1_Y1 + PT)
    sh.wall(V3_SPINE_X1, V3_BATH_Y1, v3_x1, V3_BATH_Y1 + PT)
    sh.wall(V3_SPINE_X1, V3_S2_ENS_Y1, v3_x1, V3_S2_ENS_Y1 + PT,
            openings=[(17.80, 18.70)])

    for cx in V3_GRID_X:
        for cy in V3_GRID_Y:
            fx.column(sh, cx, cy, COL)

    # --- the wavy south cantilever ---------------------------------------
    # the label sits in the 0.90 m that is balcony everywhere along the span,
    # between the wall face and the shallowest trough
    fx.wave_balcony(sh, wave_points(), V3_Y0, V3_WAVE_BALUSTRADE,
                    V3_WAVE_REVEAL, label="Balcony", level_txt="+9.87",
                    area=wave_area(), show_area=False, label_y=3.03)

    # --- openings ---------------------------------------------------------
    for a, b in V3_WIN_S_LIV + V3_WIN_S_S1:
        if (a, b) == V3_DOOR_BALC:
            fx.slider(sh, a, b, V3_Y0, V3_Y0 + WT, "h")
        else:
            sh.window(a, b, V3_Y0, V3_Y0 + WT, "h")
    for a, b in V3_WIN_N:
        sh.window(a, b, V3_Y1 - WT, V3_Y1, "h")
    for a, b in V3_WIN_E:
        sh.window(a, b, V3_X1 - WT, V3_X1, "v")
    # the west wall takes louvred ventilation openings and nothing else
    for a, b in V3_VENT_W:
        fx.vent(sh, a, b, V3_X0, V3_X0 + WT, "v")

    # the pantry's opening is cased, not a doorway: jambs, no leaf
    sh.door(*V3_PANT_OPEN, V3_PANT_Y0 - PT, V3_PANT_Y0, "h", leaf=False)
    sh.door(*V3_DOOR_S1, V3_SPINE_X0, V3_SPINE_X1, "v", hinge="lo",
            swing="right")
    sh.door(*V3_DOOR_S2, V3_SPINE_X0, V3_SPINE_X1, "v", hinge="lo",
            swing="right")
    sh.door(*V3_DOOR_BATH, V3_SPINE_X0, V3_SPINE_X1, "v", hinge="hi",
            swing="right")
    sh.door(*V3_DOOR_BED3, V3_BED3_X1, V3_BED3_X1 + PT, "v", hinge="lo",
            swing="left")
    sh.door(17.80, 18.70, V3_S1_ENS_Y0 - PT, V3_S1_ENS_Y0, "h", hinge="lo",
            swing="up")
    sh.door(17.80, 18.70, V3_S2_ENS_Y1, V3_S2_ENS_Y1 + PT, "h", hinge="lo",
            swing="down")

    # --- the stair, open to the living area ------------------------------
    fx.stair(sh, V3_STAIR, direction="both", floor_to_floor=FLOOR_TO_FLOOR,
             rise_target=V3_STAIR_RISE, going=V3_STAIR_GOING,
             landing_d=V3_STAIR_LANDING, well=V3_STAIR_WELL)
    # balustrade on the open south and east sides of the well
    sh.line(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2], V3_STAIR[1],
            w=LW_SECONDARY, color=INK)
    sh.line(V3_STAIR[2], V3_STAIR[1], V3_STAIR[2], V3_STAIR[3],
            w=LW_SECONDARY, color=INK)
    sh.tag(V3_STAIR[2] + 0.22, 10.80, "OPEN STAIR — BALUSTRADE", size=1.6,
           color=GREY, rot=-90)
    # linen cupboards on the spine, in the stretch that is solid between
    # the shared bath's door below and the hall above
    fx.wardrobe(sh, V3_SPINE_X0 - 0.60, 11.10, 0.60, 1.30, axis="v")

    # --- living area ------------------------------------------------------
    # the television goes on the spine, the one wall here with no opening in
    # it: the south wall is glazed to the balcony and the west is louvred
    fx.tv(sh, V3_SPINE_X0 - 0.16, 4.55, w=1.50, axis="v")
    # both sofas face the set: one square on to it, one across the corner
    fx.sofa(sh, 13.10, 4.50, 0.88, 2.20, facing="e")
    fx.sofa(sh, 14.30, 6.60, 1.90, 0.88, facing="s")
    fx.table(sh, 14.40, 5.30, 1.10, 0.70, rx=0.18)
    # dining sits beside the pantry it is served from, north of the seating
    fx.table(sh, 15.40, 9.60, 1.40, 0.90, seats_n=2, seats_s=2)

    # --- pantry: counter along its north wall, tea point at the east end ---
    fx.counter(sh, V3_PANT_X0, V3_PANT_Y1 - 0.60, V3_PANT_X1 - V3_PANT_X0,
               0.60)
    fx.sink(sh, V3_PANT_X0 + 0.08, V3_PANT_Y1 - 0.52, w=0.45, d=0.40)
    sh.rect(16.60, V3_PANT_Y1 - 0.48, 0.22, 0.24, rx=D.mm(0.03),
            sw=LW_FIXTURE, stroke=GREY)                      # kettle
    sh.rect(16.92, V3_PANT_Y1 - 0.50, 0.30, 0.28, rx=D.mm(0.03),
            sw=LW_FIXTURE, stroke=GREY)                      # coffee machine
    # no fridge drawn: 1.36 x 1.40 takes a counter run or a fridge, not both,
    # and the counter is what the kettle and the coffee machine need

    # --- suite 1 ----------------------------------------------------------
    # the suite door swings into the bedroom's north-west corner, so the
    # wardrobe run starts east of the arc
    fx.bed(sh, 19.10, 5.50, 1.80, 2.10, head="n")
    for bx in (18.60, 20.95):
        sh.rect(bx, 7.15, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 17.73, 4.60, 0.50, 1.70, axis="v")
    _wet_room(sh, V3_S1_ENS_Y0, V3_S1_Y1, fittings_north=True)

    # --- shared bath, now in the middle of the strip ----------------------
    # its door comes off the living area at the north end, so the fittings
    # keep to the south half, clear of the swing
    _wet_room(sh, V3_S1_Y1 + PT, V3_BATH_Y1, fittings_north=False)

    # --- suite 2, facing north, with its inset balcony --------------------
    _wet_room(sh, V3_BATH_Y1 + PT, V3_S2_ENS_Y1, fittings_north=False)
    fx.bed(sh, 19.10, 12.94, 1.80, 2.10, head="s")
    for bx in (18.60, 20.95):
        sh.rect(bx, 12.94, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 17.73, 14.50, 0.50, 1.90, axis="v")

    # --- bedroom 3 --------------------------------------------------------
    # the wardrobe backed onto the hall partition, which now stops at
    # V3_HALL_Y1; it moves to the spine, in the part of the room that was
    # the dead end of the hall
    fx.bed(sh, 13.20, 12.66, 1.60, 2.00, head="s")
    fx.wardrobe(sh, V3_SPINE_X0 - 0.55, 14.80, 0.55, 1.75, axis="v")

    # --- rooms ------------------------------------------------------------
    sh.room(v3_x0, v3_y0, V3_SPINE_X0 - v3_x0, V3_LIV_Y1 - v3_y0,
            "Living Area", area=29.4, size=2.6, sub="open — stair within",
            sched_name="Living area", at=(14.15, 7.95))
    sh.room(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2] - V3_STAIR[0],
            V3_STAIR[3] - V3_STAIR[1], "Stair", area=6.6, size=1.9,
            show_area=False, at=(13.80, 12.15))
    sh.room(V3_HALL_X0, V3_BED3_Y0, V3_SPINE_X0 - V3_HALL_X0,
            V3_HALL_Y1 - V3_BED3_Y0, "Hall", area=2.0, size=1.8,
            show_area=False, at=(16.79, 12.95))
    sh.room(V3_SPINE_X1, v3_y0, v3_x1 - V3_SPINE_X1, V3_S1_ENS_Y0 - PT - v3_y0,
            "Bedroom 8", area=15.5, size=2.4, sub="suite",
            sched_name="Bedroom 8 — suite", at=(19.75, 6.62))
    sh.room(V3_SPINE_X1, V3_S1_ENS_Y0, v3_x1 - V3_SPINE_X1,
            V3_S1_Y1 - V3_S1_ENS_Y0, "Ensuite 8", area=6.5, size=1.8,
            sched_name="Bedroom 8 ensuite", show_area=False,
            at=(19.35, 8.00))
    sh.room(V3_SPINE_X1, V3_S1_Y1 + PT, v3_x1 - V3_SPINE_X1,
            V3_BATH_Y1 - (V3_S1_Y1 + PT), "Shared Bath", area=6.5, size=1.8,
            sched_name="Shared bath", show_area=False, at=(19.45, 9.62))
    sh.room(V3_SPINE_X1, V3_BATH_Y1 + PT, v3_x1 - V3_SPINE_X1,
            V3_S2_ENS_Y1 - (V3_BATH_Y1 + PT), "Ensuite 10", area=6.5,
            size=1.8, sched_name="Bedroom 10 ensuite", show_area=False,
            at=(19.50, 12.40))
    sh.room(V3_SPINE_X1, V3_S2_ENS_Y1 + PT, v3_x1 - V3_SPINE_X1,
            v3_y1 - (V3_S2_ENS_Y1 + PT), "Bedroom 10", area=15.9, size=2.4,
            sub="suite", sched_name="Bedroom 10 — suite",
            at=(19.65, 16.30))
    # L-shaped: the strip west of the hall, plus the full width north of it
    sh.room(v3_x0, V3_BED3_Y0, V3_BED3_X1 - v3_x0, v3_y1 - V3_BED3_Y0,
            "Bedroom 9", area=16.4, size=2.4, at=(14.60, 16.00))

    villa_section_line(sh)
    villa_section_line_b(sh)

def sheet_third():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-103", "Third Floor Plan — Detached Villa", "+9.90",
               "1:50 @ A1")
    # P9: the stair no longer stops here, it carries on to the penthouse
    sh.rev, sh.status = "P21", F.STATUS_FINAL_DRAFT
    F.border(sh)

    # the three setback lines, so the 1.00 m gap is measurable on the sheet
    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(13.90, 17.55, "1.00 m SETBACK", size=1.8, color=GREY)

    _plan_third(sh)

    # Every dimension below measures itself.  The text argument is left out
    # on purpose: the three vertical dimensions on the east once carried
    # figures typed in by hand, and when the living area moved north they
    # went on printing 4.90, 4.22 and 4.38 against spans of 8.92, 0.12 and
    # 4.46.  checks.py now fails the build if a dimension's text disagrees
    # with the distance it spans.
    sh.dim_h(V3_X0, V3_X1, 0.95, ext_from=V3_Y0)              # 9.50 overall
    sh.dim_h(V3_X0, V3_GRID_X[1], -0.30)                      # to spine centre
    sh.dim_h(V3_GRID_X[1], V3_X1, -0.30)
    sh.dim_v(V3_Y0, V3_Y1, 10.70, ext_from=V3_X0)             # 13.50 overall
    # west strip: the open living space, then bedroom 3
    sh.dim_v(V3_Y0, V3_LIV_Y1, 11.35)
    sh.dim_v(V3_LIV_Y1, V3_Y1, 11.35)
    # east strip, room by room, south to north
    sh.dim_v(V3_Y0, V3_S1_ENS_Y0, 23.25)
    sh.dim_v(V3_S1_ENS_Y0, V3_S1_Y1, 23.25)
    sh.dim_v(V3_S1_Y1, V3_BATH_Y1, 23.25)
    sh.dim_v(V3_BATH_Y1, V3_S2_ENS_Y1, 23.25)
    sh.dim_v(V3_S2_ENS_Y1, V3_Y1, 23.25)
    # the cantilever's two ends, both at the deep end of the serpentine
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 22.45)

    sh.tag(24.00, 7.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY — NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)
    sh.tag(17.25, 0.25, f"CANTILEVER — SERPENTINE, {V3_WAVE_DEEP:.2f} m "
           f"AT EACH END → {V3_WAVE_WAIST:.2f} m AT THE WAIST",
           size=2.0, color=INK)

    sh.level_tag(19.00, 4.10, "FFL +9.90")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{V3_GIA:.1f} m²"),
        ("Balcony, external", f"{wave_area():.1f} m²"),
        ("Roof over, top of slab", f"+{ROOF_LEVEL:.2f}")])
    F.notes(sh, y + 6, [
        "Final draft — layout agreed. The building is set back 1.00 m "
        "from the west, north and east boundaries; the south faces the "
        "street across our own forecourt. Detaching costs 22% of the floor "
        "— 114.8 m² against 147.3 — and removes the party wall, so one "
        "structural spine divides the plate.",
        "Bedrooms are numbered 1 to 11 through the house, south to "
        "north and west before east on each floor; the ground "
        "floor's room is the guest bedroom and carries no number.",
        "The west strip south of bedroom 9 is one room: no wall divides "
        "the living area from the stair standing in it. The stair is a "
        "private villa stair — 900 mm flights, 18R at 183 × 260 — needing "
        "no enclosure, no smoke vent and no lift.",
        f"The south cantilever is reinforced concrete: a serpentine of "
        f"one full period, {V3_WAVE_DEEP:.2f} m deep at both ends and "
        f"drawn in to {V3_WAVE_WAIST:.2f} m at the waist, which is deep "
        f"enough to sit out on along the whole frontage.",
        f"East and north carry ordinary windows. The east neighbour is a "
        f"single storey in clay brick 1.00 m away, so they clear its roof "
        f"by {FLOOR_TO_FLOOR + EL_SILL - NBR_E_STOREYS * NBR_STOREY_H:.2f} m "
        f"at the first floor. The west is louvred only — that neighbour is "
        f"{NBR_W_STOREYS} storeys, and blind toward us.",
        "Bedroom 8 and the shared bath open off the living area; bedrooms "
        "9 and 10 off the hall, whose dead end goes to bedroom 9. Bedroom "
        "10 has no balcony: it takes the north wall and two windows.",
    ])

    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-200  SECTION A-A
# ===========================================================================
# The section is drawn in the same engine as the plans by mapping the plan's
# north-south axis onto the sheet's x and the level onto the sheet's y, so
# every dimension still comes out of geometry.py and nothing is drawn twice.
SEC_ORIGIN = (96.0, 462.0)      # 1:50; x = plan y, y = level
SEC_X = 16.20                   # the cut passes through lift, stair, north room
SEC_LEVELS = [0, 1, 2, 3]


def _slab(sh, y0, y1, ffl, dash=None, openings=()):
    """Structural slab: 300 mm zone with its top at finished floor level."""
    if dash:
        sh.rect(y0, ffl - STRUCTURAL_ZONE, y1 - y0, STRUCTURAL_ZONE,
                sw=LW_SECONDARY, stroke=GREY, dash=dash)
    else:
        sh.wall(y0, ffl - STRUCTURAL_ZONE, y1, ffl, openings=openings)


def _stair_section(sh, ffl):
    """The west flight, which is the one the cut plane passes through."""
    risers, rise, going = 19, FLOOR_TO_FLOOR / 19.0, 0.275
    treads = risers // 2
    run = treads * going
    start = ST_Y1 - 1.30 - run
    x, z = start, ffl
    pts = [(x, z)]
    for _ in range(treads):
        z += rise
        pts.append((x, z))
        x += going
        pts.append((x, z))
    sh.poly(pts, close=False, stroke=INK, sw=LW_FIXTURE)
    half = ffl + rise * treads
    sh.wall(ST_Y1 - 1.30, half - 0.20, ST_Y1, half)
    sh.line(start, ffl, ST_Y1 - 1.30, half, w=LW_THIN, color=LIGHT)
    sh.tag((start + ST_Y1) / 2.0, ffl + 1.95,
           f"{risers}R @ {rise * 1000:.0f}", size=1.6, color=LIGHT)


def _villa_penthouse(sh):
    """Detached villa, penthouse (P11): a flat between two terraces.

    The client asked for the north and south open areas to be joined from
    OUTSIDE the apartment, down the west side, at a 2.00 m minimum.  That
    corridor is set out first and the flat fits around what is left, which
    is why this is a one-bedroom flat and not the two-bedroom one drawn at
    P10: 4.09 m of clear width will not take two bedrooms side by side, and
    stacking them would leave 1.44 m for both terraces.

    The corridor runs east of the stair - the stair well stays open, its
    half landing being only 1.65 m below this floor - and its east side is
    the flat's west wall, which stands on the spine at x 17.46 because that
    is the one line on this side of the roof with a beam under it.  The
    0.51 m that puts the corridor over the 2.00 m minimum is worth more as
    corridor than as a void behind a wall.
    """
    # --- the open roof: two terraces, the corridor between them -----------
    fx.wave_balcony(sh, wave_points(), V3_Y0, V3_WAVE_BALUSTRADE,
                    V3_WAVE_REVEAL, label=None, area=None, show_area=False)
    parapet(sh, V3_X0, V3_Y0, V3_X0 + PARAPET, V3_Y1)
    parapet(sh, V3_X0, V3_Y1 - PARAPET, V3_X1, V3_Y1)
    parapet(sh, V3_X1 - PARAPET, V4_Y1, V3_X1, V3_Y1)

    # --- the pergola, over the corridor for its whole length --------------
    px0, py0, px1, py1 = V4_PERGOLA
    fx.pergola(sh, px0, py0, px1 - px0, py1 - py0, axis="v", pitch=0.55)
    bx0, by0, bx1, by1 = V4_PERGOLA_N
    fx.pergola(sh, bx0, by0, bx1 - bx0, by1 - by0, axis="h", pitch=0.55)
    for ppx, ppy in ((px0, 7.00), (px0, 10.80), (px0, 14.20),
                     (px1, 4.60), (px1, 15.90)):
        sh.rect(ppx - 0.09, ppy - 0.09, 0.18, 0.18, fill=GREY, stroke=GREY,
                sw=LW_FIXTURE)

    # --- a canopy over the stair, which is otherwise open to the sky ------
    cx0, cy0, cx1, cy1 = V4_CANOPY
    with sh.on("A-FLOR-OVER"):
        sh.rect(cx0, cy0, cx1 - cx0, cy1 - cy0, sw=LW_HIDDEN, stroke=GREY,
                dash="5 3")
    sh.tag((cx0 + cx1) / 2.0, cy0 - 0.30, "CANOPY OVER", size=1.6,
           color=GREY)

    qx0, qy0, qx1, qy1 = V4_PLANT
    sh.rect(qx0, qy0, qx1 - qx0, qy1 - qy0, sw=LW_SECONDARY, stroke=GREY,
            dash="3 2")
    sh.tag((qx0 + qx1) / 2.0, (qy0 + qy1) / 2.0, "TANKS", size=1.6,
           color=GREY)

    sh.tag(18.60, 2.55, f"SOUTH BALCONY — {V4_BALCONY:.1f} m²", size=2.2,
           color=INK)
    sh.tag(20.40, 16.05, f"NORTH TERRACE — {V4_TERR_N:.1f} m²", size=2.1,
           color=INK)
    sh.tag(15.90, 7.20, f"OPEN CORRIDOR — {V4_CORR_AREA:.1f} m²", size=2.2,
           color=INK, rot=-90)
    sh.tag(16.70, 13.20, "PERGOLA OVER", size=1.8, color=GREY, rot=-90)
    sh.tag(13.78, 6.20, "TERRACE", size=1.7, color=GREY, rot=-90)
    sh.level_tag(13.35, 4.45, "TERRACE " + V4_LEVEL)

    # --- shell ------------------------------------------------------------
    sh.wall(V4_X0, V4_Y0, V4_X1, V4_Y0 + WT, openings=V4_WIN_S)
    sh.wall(V4_X0, V4_Y0, V4_X0 + WT, V4_Y1,
            openings=[V4_DOOR_MAIN] + V4_WIN_W)
    sh.wall(V4_X0, V4_Y1 - WT, V4_X1, V4_Y1, openings=V4_WIN_N)
    sh.wall(V4_X1 - WT, V4_Y0, V4_X1, V4_Y1, openings=V4_WIN_E)

    # --- the two internal lines, and the hall partition -------------------
    sh.wall(v4_x0, V4_LIV_Y1, v4_x1, V4_LIV_Y1 + PT, openings=[V4_DOOR_HALL])
    sh.wall(V4_HALL_X1, V4_LIV_Y1 + PT, V4_HALL_X1 + PT, V4_BATH_Y1,
            openings=[V4_DOOR_BATH])
    sh.wall(v4_x0, V4_BATH_Y1, v4_x1, V4_BATH_Y1 + PT,
            openings=[V4_DOOR_BED])

    # the flat's long walls swallow the column line each side; the columns
    # on the west line at x 12.65 stop at the roof slab and are not drawn
    for cx in (V3_GRID_X[1], V3_GRID_X[2]):
        for cy in (V3_GRID_Y[1], V3_GRID_Y[2]):
            fx.column(sh, cx, cy, COL)

    # --- openings ---------------------------------------------------------
    for a, b in V4_WIN_S:
        if (a, b) == V4_DOOR_TERR:
            fx.slider(sh, a, b, V4_Y0, V4_Y0 + WT, "h")
        else:
            sh.window(a, b, V4_Y0, V4_Y0 + WT, "h")
    for a, b in V4_WIN_N:
        if (a, b) == V4_DOOR_TERR_N:
            fx.slider(sh, a, b, V4_Y1 - WT, V4_Y1, "h")
        else:
            sh.window(a, b, V4_Y1 - WT, V4_Y1, "h")
    for a, b in V4_WIN_E:
        sh.window(a, b, V4_X1 - WT, V4_X1, "v")
    for a, b in V4_WIN_W:
        sh.window(a, b, V4_X0, V4_X0 + WT, "v")
    sh.door(*V4_DOOR_MAIN, V4_X0, V4_X0 + WT, "v", hinge="lo",
            swing="right")
    sh.tag(16.95, (V4_DOOR_MAIN[0] + V4_DOOR_MAIN[1]) / 2.0,
           "MAIN DOOR", size=1.9, color=INK, rot=-90)

    sh.door(*V4_DOOR_HALL, V4_LIV_Y1, V4_LIV_Y1 + PT, "h", leaf=False)
    sh.door(*V4_DOOR_BATH, V4_HALL_X1, V4_HALL_X1 + PT, "v", hinge="lo",
            swing="right")
    sh.door(*V4_DOOR_BED, V4_BATH_Y1, V4_BATH_Y1 + PT, "h", hinge="lo",
            swing="up")

    # --- the stair, open in the corridor zone -----------------------------
    fx.stair(sh, V3_STAIR, direction="dn", floor_to_floor=FLOOR_TO_FLOOR,
             rise_target=V3_STAIR_RISE, going=V3_STAIR_GOING,
             landing_d=V3_STAIR_LANDING, well=V3_STAIR_WELL)
    sh.line(13.70, V3_STAIR[1], V3_STAIR[2], V3_STAIR[1], w=LW_SECONDARY,
            color=INK)
    sh.line(V3_STAIR[2], V3_STAIR[1], V3_STAIR[2], V3_STAIR[3],
            w=LW_SECONDARY, color=INK)
    sh.line(V3_STAIR[0], V3_STAIR[3], V3_STAIR[2], V3_STAIR[3],
            w=LW_SECONDARY, color=INK)
    sh.tag(15.10, 10.80, "BALUSTRADE", size=1.6, color=GREY, rot=-90)

    # --- living and dining, with the kitchenette on the back wall ---------
    fx.sofa(sh, 18.40, 5.50, 2.10, 0.90, facing="s")
    fx.table(sh, 18.90, 4.55, 1.05, 0.65, rx=0.16)
    fx.sofa(sh, 20.70, 4.70, 0.90, 0.85, facing="w")
    fx.table(sh, 18.10, 7.70, 1.40, 0.85, seats_s=2, seats_e=1, rx=0.18)
    fx.kitchenette(sh, 19.95, 9.00, 1.75, 0.60, axis="h")

    # --- bath -------------------------------------------------------------
    fx.wc(sh, 19.40, V4_LIV_Y1 + PT, facing="n")
    fx.basin(sh, 20.40, V4_LIV_Y1 + PT, w=0.60, d=0.48, facing="n")
    fx.shower(sh, 20.70, 10.60, 1.00, 1.00)

    # --- bedroom ----------------------------------------------------------
    fx.bed(sh, 19.40, 12.94, 1.60, 2.10, head="n")
    sh.rect(21.05, 14.40, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 18.75, V4_BATH_Y1 + PT, 1.50, 0.55, axis="h")

    # --- rooms ------------------------------------------------------------
    sh.room(v4_x0, v4_y0, v4_x1 - v4_x0, V4_LIV_Y1 - v4_y0,
            "Living & Dining", area=23.7, size=2.3,
            sched_name="Living and dining", at=(19.60, 6.80))
    sh.room(v4_x0, V4_LIV_Y1 + PT, V4_HALL_X1 - v4_x0,
            V4_BATH_Y1 - V4_LIV_Y1 - PT, "Hall", area=2.1, size=1.7,
            show_area=False, at=(18.16, 10.66))
    sh.room(V4_HALL_X1 + PT, V4_LIV_Y1 + PT, v4_x1 - V4_HALL_X1 - PT,
            V4_BATH_Y1 - V4_LIV_Y1 - PT, "Bath", area=5.4, size=1.9,
            show_area=False, at=(19.72, 11.12))
    sh.room(v4_x0, V4_BATH_Y1 + PT, v4_x1 - v4_x0,
            v4_y1 - V4_BATH_Y1 - PT, "Bedroom 11", area=13.6, size=2.3,
            at=(18.50, 13.80))
    sh.room(V3_STAIR[0], V3_STAIR[1], V3_STAIR[2] - V3_STAIR[0],
            V3_STAIR[3] - V3_STAIR[1], "Stair", area=6.6, size=1.9,
            show_area=False, schedule=False, at=(13.80, 12.00))
    sh.level_tag(18.30, 12.70, "FFL " + V4_LEVEL)

    villa_section_line(sh)
    villa_section_line_b(sh)

def sheet_penthouse():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-104", "Penthouse Plan — Detached Villa", V4_LEVEL,
               "1:50 @ A1")
    sh.rev, sh.status = "P21", F.STATUS_FINAL_DRAFT
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 14.60, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)

    _villa_penthouse(sh)

    sh.dim_h(V3_X0, V3_X1, 0.95, ext_from=V3_Y0)
    sh.dim_h(V3_X0, V4_CORR_X0, -0.30)
    sh.dim_h(V4_CORR_X0, V4_CORR_X1, -0.30)
    sh.dim_h(V4_CORR_X1, V3_X1, -0.30)
    sh.dim_v(V3_Y0, V3_Y1, 10.70, ext_from=V3_X0)
    sh.dim_v(V4_Y0, V4_Y1, 11.35)
    sh.dim_v(V4_Y1, V3_Y1, 11.35)
    sh.dim_v(V4_Y0, V4_LIV_Y1, 23.25)
    sh.dim_v(V4_LIV_Y1, V4_BATH_Y1, 23.25)
    sh.dim_v(V4_BATH_Y1, V4_Y1, 23.25)
    sh.dim_v(V4_Y1, V3_Y1, 23.25)
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_DEEP, V3_Y0, 22.45)

    sh.tag(24.00, 14.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(17.25, 0.25, f"CANTILEVER CARRIED TO THE TOP — SERPENTINE, "
           f"{V3_WAVE_DEEP:.2f} m AT EACH END → {V3_WAVE_WAIST:.2f} m",
           size=2.0, color=INK)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, flat", f"{V4_PLATE:.1f} m²"),
        ("South balcony, on the cantilever", f"{V4_BALCONY:.1f} m²"),
        ("South terrace, west of the corridor",
         f"{V4_TERR_S - V4_BALCONY:.1f} m²"),
        ("North terrace", f"{V4_TERR_N:.1f} m²"),
        ("Open corridor", f"{V4_CORR_AREA:.1f} m²"),
        ("Top of penthouse slab", f"+{V4_TOP:.2f}"),
        ("Floor below", "+9.90")])
    F.notes(sh, y + 6, [
        "Bedrooms are numbered 1 to 11 through the house, south to north "
        "and west before east on each floor; the ground floor's room is "
        "the guest bedroom and carries no number. This is bedroom 11.",
        f"Final draft — layout agreed. The two open areas are joined "
        f"outside the flat, down the west, by a corridor {V4_CORR_W:.2f} m "
        f"clear against the 2.00 m asked for, pergola over its whole "
        f"length. The front door is off it.",
        f"{V4_PLATE:.1f} m² indoors; {V4_BALCONY:.1f} m² of balcony on the "
        f"cantilever, {V4_TERR_S - V4_BALCONY:.1f} m² of terrace by the "
        f"stair, {V4_TERR_N:.1f} m² north and {V4_CORR_AREA:.1f} m² of "
        f"corridor — all four run into one another.",
        "The corridor passes east of the stair: the well is 2.00 m wide "
        "and hard against the west parapet, its half landing 1.65 m below "
        "this floor, so it stays open. Its east side is the flat's west "
        "wall, on the spine at x 17.46 — the one line on this side of the "
        "roof with a beam under it.",
        "That leaves the flat 4.09 m clear, which will not take two "
        "bedrooms side by side: stacking them needs 12.06 m of the 13.50 m "
        "depth and leaves 1.44 m for both terraces. The second bedroom is "
        "what pays for the corridor.",
        "The living room runs south to the building's face, so it opens "
        "straight onto the cantilever; y 3.65 is a grid line, so that wall "
        "sits on the columns and over the wall below. At +16.45 the "
        "penthouse is a fourth storey for most planning codes.",
    ])

    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# the villa's A-A cut.  20.70 is not arbitrary: it is the one north-south
# line that passes through a room at every level and through every wet
# room in the east strip, and it clears all three column lines, so the
# section shows slabs spanning rather than a column standing in the cut.
SEC_X_V = 20.70

# what the cut passes through at each level: (south face, north face,
# whether the wall carries an opening at the cut).  Read off the plans by
# the probe in checks, not written from memory.
SEC_WALLS = {
    0: [(8.00, 8.12, True), (11.60, 11.72, False), (13.30, 13.42, False)],
    1: [(8.60, 8.72, True), (10.30, 10.42, False), (12.42, 12.54, False)],
    2: [(8.60, 8.72, True), (10.30, 10.42, False), (12.42, 12.54, False)],
    3: [(7.60, 7.72, False), (9.30, 9.42, False), (11.00, 11.12, False),
        (12.70, 12.82, False)],
}
SEC_ROOMS = {
    0: [(3.80, 8.00, "Dining"), (8.12, 11.60, "Kitchen"),
        (11.72, 13.30, "Ensuite"), (13.42, 16.70, "Guest bedroom")],
    1: [(3.80, 8.60, "Bedroom 1"), (8.72, 10.30, "Ensuite 1"),
        (10.42, 12.42, "Shared bath"), (12.54, 16.70, "Bedroom 3")],
    2: [(3.80, 8.60, "Bedroom 5"), (8.72, 10.30, "Ensuite 5"),
        (10.42, 12.42, "Shared bath"), (12.54, 16.70, "Bedroom 7")],
    3: [(3.80, 7.60, "Bedroom 8"), (7.72, 9.30, "Ensuite 8"),
        (9.42, 11.00, "Shared bath"), (11.12, 12.70, "Ensuite 10"),
        (12.82, 16.70, "Bedroom 10")],
}
SEC_PH = [(3.80, 9.60, "Living & dining"), (9.72, 11.60, "Bath"),
          (11.72, 15.04, "Bedroom 11")]

SILL, HEAD, DOOR_HEAD = 0.90, 2.40, 2.10
PH_UPSTAND = 0.60              # parapet upstand to the penthouse roof


def villa_section_line(sh, y0=1.10, y1=18.85):
    """The A-A cut line, so the section can be located on every plan."""
    with sh.on("A-ANNO-SYMB"):
        sh.line(SEC_X_V, y0, SEC_X_V, y1, w=LW_THIN, color=INK,
                dash="9 2 1.6 2")
    for yy in (y0, y1):
        sh.circle(SEC_X_V, yy, 0.45, fill="#ffffff", stroke=INK,
                  sw=LW_SECONDARY)
        sh.tag(SEC_X_V, yy - 0.17, "A", size=2.6, color=INK)
    for yy in (y0 + 0.70, y1 - 0.70):
        sh.poly([(SEC_X_V - 0.62, yy), (SEC_X_V - 0.06, yy + 0.26),
                 (SEC_X_V - 0.06, yy - 0.26)], fill=INK, stroke=INK,
                sw=LW_THIN)


def _glazed(sh, a, b, ffl, clear=CLEAR_HEIGHT):
    """External wall at the cut: piers under the sill and over the head."""
    sh.wall(a, ffl, b, ffl + SILL)
    sh.wall(a, ffl + HEAD, b, ffl + clear)
    for f in (0.3, 0.7):
        sh.line(a + (b - a) * f, ffl + SILL, a + (b - a) * f, ffl + HEAD,
                w=LW_FIXTURE, color=GREY)


def _villa_stair_beyond(sh, ffl):
    """The dog-leg stair, seen beyond the cut through the open spine.

    Drawn only within the storey it stands in.  The stair well is at
    x 12.80-14.80 and this cut is at 20.70, so the slab over it is solid
    here - a flight carried on through the slab line would be a drawing
    that lies about what the cut passes through.  The return flight is
    therefore stopped at the soffit, where it genuinely goes out of sight.
    """
    y1 = V3_STAIR[3]
    risers = round(FLOOR_TO_FLOOR / V3_STAIR_RISE)          # 18
    rise, going, treads = FLOOR_TO_FLOOR / risers, V3_STAIR_GOING, risers // 2
    run = treads * going
    half = ffl + rise * treads
    soffit = ffl + CLEAR_HEIGHT

    def flight(y, z, step):
        pts = [(y, z)]
        for _ in range(treads):
            if z + rise > soffit:
                break
            z += rise
            pts.append((y, z))
            y += step * going
            pts.append((y, z))
        sh.poly(pts, close=False, stroke=LIGHT, sw=LW_THIN)

    flight(y1 - V3_STAIR_LANDING - run, ffl, +1)           # up, walking north
    sh.line(y1 - V3_STAIR_LANDING, half, y1, half, w=LW_THIN, color=LIGHT)
    flight(y1, half, -1)                                   # up, walking south


def sheet_section():
    D.set_scale(50, *SEC_ORIGIN)
    sh = Sheet("A-200", "Section A–A — Detached Villa",
               "looking west", "1:50 @ A1")
    sh.rev, sh.status = "P21", F.STATUS_FINAL_DRAFT
    F.border(sh)

    y_s, y_n = V3_Y0, V3_Y1                      # 3.50 .. 17.00
    roof, top = ROOF_LEVEL, V4_TOP               # +13.20, +16.45
    proj = wave_projection(SEC_X_V)              # 1.63 m of balcony here
    y_b = y_s - proj

    # --- ground, forecourt and the setback strip beyond the north wall ---
    sh.rect(y_b - 1.60, -2.60, y_s - y_b + 1.60, 2.10, fill="#f4f4f4",
            stroke="none", sw=0)
    _hatch(sh, y_b - 1.60, -2.60, y_s - y_b + 1.60, 2.10, pitch=0.7,
           color="#dcdcdc")
    sh.line(y_b - 1.60, GARDEN_LEVEL, y_s, GARDEN_LEVEL, w=LW_CUT, color=INK)
    sh.rect(y_s, -2.60, y_n - y_s, 2.60, fill="#f4f4f4", stroke="none", sw=0)
    _hatch(sh, y_s, -2.60, y_n - y_s, 2.10, pitch=0.7, color="#dcdcdc")
    sh.rect(y_n, -2.60, 1.60, 2.10, fill="#f4f4f4", stroke="none", sw=0)
    _hatch(sh, y_n, -2.60, 1.60, 2.10, pitch=0.7, color="#dcdcdc")
    sh.line(y_n, GARDEN_LEVEL, y_n + 1.60, GARDEN_LEVEL, w=LW_CUT, color=INK)
    sh.level_tag(y_b - 0.95, GARDEN_LEVEL, "FORECOURT −0.50")
    sh.tag(y_n + 0.80, GARDEN_LEVEL - 0.75, "1.00 m SETBACK", size=1.7,
           color=GREY, rot=-90)

    # foundations under the two external walls, indicative
    for a, b in ((y_s, y_s + WT), (y_n - WT, y_n)):
        sh.wall(a - 0.30, -1.55, b + 0.30, -1.15)
        sh.wall(a, -1.15, b, -STRUCTURAL_ZONE)

    # --- the four villa floors -------------------------------------------
    for lv in range(4):
        ffl = lv * FLOOR_TO_FLOOR
        _slab(sh, y_s, y_n, ffl)
        if lv > 0:                                    # the cantilever
            _slab(sh, y_b, y_s, ffl - 0.03)
            sh.wall(y_b, ffl - 0.03, y_b + V3_WAVE_BALUSTRADE, ffl + 1.10,
                    fill=PARAPET_FILL)
        _glazed(sh, y_s, y_s + WT, ffl)
        _glazed(sh, y_n - WT, y_n, ffl)
        for a, b, open_ in SEC_WALLS[lv]:
            if open_:
                sh.wall(a, ffl + DOOR_HEAD, b, ffl + CLEAR_HEIGHT)
            else:
                sh.wall(a, ffl, b, ffl + CLEAR_HEIGHT)
        _villa_stair_beyond(sh, ffl)
        sh.level_tag(y_s + 0.75, ffl, f"FFL +{ffl:.2f}")
        for a, b, name in SEC_ROOMS[lv]:
            sh.tag((a + b) / 2.0, ffl + 1.05, name.upper(),
                   size=2.0 if b - a > 2.4 else 1.6, color=INK)
        if lv > 0:
            sh.tag(y_b + proj / 2.0, ffl + 0.55, "BALCONY", size=1.7,
                   color=GREY, rot=-90)

    # --- the roof deck, and the penthouse standing on it ------------------
    _slab(sh, y_s, y_n, roof)
    _slab(sh, y_b, y_s, roof - 0.03)
    sh.wall(y_b, roof - 0.03, y_b + V3_WAVE_BALUSTRADE, roof + 1.10,
            fill=PARAPET_FILL)
    sh.level_tag(y_s + 0.75, roof, f"FFL {V4_LEVEL}")

    _glazed(sh, V4_Y0, V4_Y0 + WT, roof)
    sh.wall(V4_HALL_X1 * 0 + 9.60, roof, 9.72, roof + CLEAR_HEIGHT)
    sh.wall(11.60, roof, 11.72, roof + CLEAR_HEIGHT)
    sh.wall(V4_Y1 - WT, roof, V4_Y1, roof + CLEAR_HEIGHT)
    _slab(sh, V4_Y0, V4_Y1, top)
    for a, b in ((V4_Y0, V4_Y0 + WT), (V4_Y1 - WT, V4_Y1)):
        sh.wall(a, top, b, top + PH_UPSTAND, fill=PARAPET_FILL)
    for a, b, name in SEC_PH:
        sh.tag((a + b) / 2.0, roof + 1.05, name.upper(),
               size=2.0 if b - a > 2.4 else 1.6, color=INK)
    sh.tag(y_b + proj / 2.0, roof + 0.55, "BALCONY", size=1.7, color=GREY,
           rot=-90)

    # north roof terrace and its parapet
    sh.wall(y_n - PARAPET, roof, y_n, roof + 1.10, fill=PARAPET_FILL)
    sh.tag((V4_Y1 + y_n - PARAPET) / 2.0, roof + 1.45, "TERRACE", size=1.7,
           color=GREY, rot=-90)
    sh.level_tag(y_n - 2.40, top, f"TOP OF SLAB +{top:.2f}")
    sh.line(V3_STAIR[3] - 0.60, 1.65, 14.30, 2.45, w=LW_THIN, color=GREY)
    sh.tag(15.15, 2.42, "STAIR BEYOND", size=1.8, color=GREY)

    # --- dimensions -------------------------------------------------------
    for lv in range(4):
        ffl = lv * FLOOR_TO_FLOOR
        sh.dim_v(ffl, ffl + FLOOR_TO_FLOOR, y_b - 1.05)
    sh.dim_v(roof, top, y_b - 1.05)
    sh.dim_v(GARDEN_LEVEL, 0.0, y_b - 1.05)
    sh.dim_v(GARDEN_LEVEL, top, y_b - 2.10, f"{top - GARDEN_LEVEL:.2f}")
    sh.dim_h(y_s, y_n, -3.05, ext_from=GARDEN_LEVEL)
    sh.dim_h(y_b, y_s, -3.05)
    sh.dim_h(y_n, y_n + 1.00, -3.05)
    sh.dim_h(V4_Y0, V4_Y1, top + PH_UPSTAND + 0.80, ext_from=top)
    sh.dim_h(V4_Y1, y_n, top + PH_UPSTAND + 0.80)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "LEVEL DATUMS", [
        ("Forecourt and garden", f"{GARDEN_LEVEL:+.2f}"),
        ("Ground floor", "+0.00"),
        ("First floor", f"+{FLOOR_TO_FLOOR:.2f}"),
        ("Second floor", f"+{2 * FLOOR_TO_FLOOR:.2f}"),
        ("Third floor", f"+{3 * FLOOR_TO_FLOOR:.2f}"),
        ("Penthouse floor", f"+{roof:.2f}"),
        ("Penthouse, top of slab", f"+{top:.2f}"),
        ("Clear ceiling height", f"{CLEAR_HEIGHT:.2f} m"),
        ("Structural zone", f"{STRUCTURAL_ZONE:.2f} m"),
        ("Overall, garden to top", f"{top - GARDEN_LEVEL:.2f} m")])
    F.notes(sh, y + 6, [
        f"Final draft — layout agreed. Looking west, cut on the line "
        f"marked A–A on every plan, at x {SEC_X_V:.2f}. That line is not "
        f"arbitrary: it is the one north-south cut that passes through a "
        f"room at every level and through every wet room in the east "
        f"strip, and it clears all three column lines, so the slabs are "
        f"seen spanning rather than a column standing in the cut.",
        "The wet rooms on the first and second floors sit one over the "
        "other, wall for wall — 8.60, 10.30 and 12.42 on both — so each "
        "drops a single drainage stack straight to the ground. The third "
        "floor divides the strip on its own lines and is shown as it is.",
        f"Flat slab on the column grid, {STRUCTURAL_ZONE * 1000:.0f} mm "
        f"structural zone, giving {CLEAR_HEIGHT:.2f} m clear at every "
        f"level and {FLOOR_TO_FLOOR:.2f} m floor to floor; the penthouse "
        f"is {top - roof:.2f} m floor to top of slab.",
        f"The south cantilever is carried on all three upper floors and "
        f"the penthouse. It projects {proj:.2f} m at this cut, against "
        f"{V3_WAVE_DEEP:.2f} m at each end of the curve and "
        f"{V3_WAVE_WAIST:.2f} m at its waist, with a glass balustrade at "
        f"the "
        f"slab edge.",
        "The penthouse stands clear of the north edge, leaving the roof "
        "terrace beyond its north wall. The corridor that joins the two "
        "terraces runs west of this cut and does not appear; see A-104.",
        "The stair is drawn in thin line beyond the cut, where it is seen "
        "through the open spine. Foundations are indicative only and "
        "subject to a ground investigation and the engineer's design.",
    ])
    fx.scale_bar(sh, 96, 556, metres=10)
    F.titleblock(sh)
    return sh

# ===========================================================================
# A-300 / A-301 / A-302  ENLARGED PLANS AT 1:25
# ===========================================================================
# These run the ordinary plan code at 1:25 and crop to the part being shown,
# so an enlargement can never disagree with the plan it came from.  A whole
# 13.90 m unit does not fit an A1 sheet at 1:25, which is why these cover
# the wet cores, the kitchenettes and the service floor - the places where
# the extra scale actually buys something - and the whole-unit plans stay at
# 1:50 on A-101 and A-103.
#
# WITHDRAWN AT P22.  They enlarge the apartment building the client asked
# for before the villa, down to kitchenette joinery and a 1.10 m hall; the
# villa has no apartments, no service kitchen and not that footprint.  They
# are kept and still build, because a set that deletes what it superseded
# cannot show how the building was arrived at, and because the client holds
# a bound issue with these three sheets in it - but they are stamped on the
# face, left out of the issued set, and `checks.py` refuses to let either
# half of that slip.
WITHDRAWN_BY = "A-100 to A-104"


def _detail_sheet(number, title, level, origin, clip, draw, schedule):
    D.set_scale(25, *origin)
    sh = Sheet(number, title, level, "1:25 @ A1")
    F.border(sh)
    sh.begin_clip(*clip)
    draw(sh)
    sh.end_clip()
    sh.schedule = schedule
    return sh


def sheet_unit_typical():
    sh = _detail_sheet(
        "A-300", "Typical Apartment — Enlarged Plan", "+3.30 / +6.60",
        (-432.0, 546.8), (25, 78, 490, 336),
        lambda s: _plan_apartment(s, 1, "+3.30"),
        [("Apt A bathroom", 3.4), ("Apt A entry hall", 4.4),
         ("Apt A living / kitchen", 26.3), ("Apt B entry hall", 4.2),
         ("Apt B bathroom", 4.6), ("Apt B living / kitchen", 23.7)])

    sh.dim_h(a_x0, 13.28, 11.55)
    sh.dim_h(13.40, CORE_WALL_X, 11.55)
    sh.dim_h(20.40, b_x1, 11.55)
    sh.dim_v(8.98, 11.30, 11.50)
    sh.dim_v(9.12, 11.10, 23.10)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Apartment A / apartment B", "64.7 / 63.2 m²"),
        ("Balcony A / B (external)", f"{BALC[0]:.1f} / {BALC[1]:.1f} m²")])
    F.notes(sh, y + 6, [
        "Enlarged from A-101; the second floor is identical. Only the "
        "entry, wet rooms and kitchenettes are shown at this scale — a "
        "whole 13.90 m unit does not fit an A1 sheet at 1:25.",
        "Apartment A: bathroom and entry hall side by side on the front "
        "door, so the bathroom is reached from the hall and from the "
        "bedroom without crossing the living room. Kitchenette runs "
        "against the party wall in the south-east bay.",
        "Apartment B: bathroom off its own entry hall with a window in "
        "the open east wall, kitchenette against the party wall opposite "
        "apartment A's riser.",
        "All kitchenettes are one joinery run: 600 mm sink bay, two-ring "
        "induction hob, undercounter fridge and overhead storage over the "
        "full length. Recirculating hood unless a duct to the riser is "
        "confirmed.",
        "Every wet room drains to the riser cupboard on the party wall; "
        "runs longer than 2 m fall at 1:40 within the 300 mm floor zone.",
    ])
    fx.scale_bar(sh, 40, 556, metres=5)
    F.withdraw(sh, "P22", WITHDRAWN_BY)
    F.titleblock(sh)
    return sh


def sheet_unit_third():
    sh = _detail_sheet(
        "A-301", "Third Floor Apartment — Enlarged Plan", "+9.90",
        (-432.0, 690.0), (25, 78, 490, 472), _plan_third,
        [("Living / dining / kitchen", 35.8), ("Bedroom 1", 19.6),
         ("Ensuite", 7.5), ("Dressing", 7.1), ("Family bath", 5.2),
         ("Guest WC", 2.3)])

    sh.dim_h(a_x0, b_x1, 15.20)
    sh.dim_h(b_x0, 20.30, 15.20)
    sh.dim_v(a_y0, LIV3_Y1, 11.50)
    sh.dim_v(LF_Y0, 11.60, 23.10)
    sh.tag(17.00, 4.35, "LIVING BAND ACROSS BOTH BLOCKS", size=2.4,
           color=INK)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Apartment, gross internal", "≈116 m²"),
        ("South terrace / north terrace", f"{TER_S:.1f} / {TER_N:.1f} m²")])
    F.notes(sh, y + 6, [
        "Enlarged from A-103. The party wall can only be opened between "
        "y 3.80 and 7.18, so the living, dining and kitchen occupy that "
        "whole band as one 10.60 m wide room and form the only link "
        "between the two blocks.",
        "Bedroom 1 and its ensuite take block B, windowed on the open "
        "east boundary. The ensuite is entered from the dressing room, "
        "and the dressing room from bedroom 1.",
        "Block A carries the entry hall on the front door, with the guest "
        "WC, the store, the family bath and its passage off it, and "
        f"bedroom 2 beyond — {NORTH_A:.1f} m² across the whole north end, "
        "with two windows in the north wall.",
        "No room on this floor is entered through another.",
    ])
    fx.scale_bar(sh, 40, 556, metres=5)
    F.withdraw(sh, "P22", WITHDRAWN_BY)
    F.titleblock(sh)
    return sh


def sheet_service():
    sh = _detail_sheet(
        "A-302", "Central Kitchen & Laundry — Enlarged Plan", "+0.00",
        (-412.0, 808.0), (40, 78, 480, 374), _plan_ground,
        [("Service kitchen", 12.9), ("Servery", 3.0), ("Wash-up", 3.2),
         ("Staff WC", 2.0), ("Bin store", 1.9), ("Central laundry", 4.0),
         ("Guest bath", 5.9), ("Linen & store", 3.3)])

    sh.dim_v(14.00, a_y1, 11.55)
    sh.dim_h(a_x0, CORE_WALL_X, 17.85)
    sh.dim_v(9.12, 10.32, 23.05)
    sh.dim_h(19.37, b_x1, 8.98)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Kitchen, previous issue", "18.4 m²"),
        ("Kitchen, this issue", "12.9 m²  (−30 %)"),
        ("Laundry, previous issue", "10.4 m²"),
        ("Laundry, this issue", "4.0 m²")])
    F.notes(sh, y + 6, [
        "Enlarged from A-100. The kitchen is reduced 30 % on the client's "
        "instruction; the area released carries a staff WC, an internal "
        "bin store and a servery on the route in, so bins no longer stand "
        "out on the patio.",
        "Kitchen fit-out: a wet run on the west wall with a deep bowl "
        "sink and undercounter refrigeration, a cooking line on the north "
        "wall under the extract hood, and a free-standing preparation "
        "counter between them.",
        "Laundry takes one washer-dryer, a utility sink and a folding "
        "counter, as instructed. Linen and housekeeping stores are next "
        "to it off the same hall.",
        "The hall in block B is 1.10 m clear and serves the laundry, the "
        "guest bath, the linen store and the guest bedroom, so none of "
        "them is entered through another room.",
        "Kitchen extract rises in a fire-rated shaft inside the riser "
        "cupboard off the fire lobby and discharges above roof level. "
        "Suppression over the cooking line; 2 hour separation to the "
        "floor over.",
    ])
    fx.scale_bar(sh, 50, 556, metres=5)
    F.withdraw(sh, "P22", WITHDRAWN_BY)
    F.titleblock(sh)
    return sh


# ===========================================================================
# ===========================================================================
# A-400 / A-401 / A-410 / A-411  EXTERIOR ELEVATIONS, TWO SCHEMES
# ===========================================================================
# Two skins on one agreed building.  The geometry is the plans' - the sheet
# builders live here rather than in elevations.py because export_cad swaps
# plans.Sheet to reach the DXF backend, and a builder that resolved Sheet
# from another module would quietly bypass it and export nothing.
EL_KEY = {
    "A": [("Walls", "warm limestone render"),
          ("Slab nosing", f"rounded, {A_NOSING * 1000:.0f} mm"),
          ("Cove light", "in the underside of the nosing"),
          ("Balustrade", f"clear glass, {V3_WAVE_BALUSTRADE * 1000:.0f} mm "
                         f"inboard"),
          ("Frames", "bronze anodised"),
          ("Balcony curve", "serpentine"),
          ("Projection", f"{EL_SERP_MEAN + EL_SERP_AMP:.2f} / "
                         f"{EL_SERP_MEAN - EL_SERP_AMP:.2f} m"),
          ("Balcony area", f"{wave_area('serpentine'):.1f} m² a floor"),
          ("Top of building", f"+{EL_TOP:.2f}")],
    "B": [("Walls", "ivory render, terracotta trim"),
          ("Floor bands", f"{B_BAND * 1000:.0f} mm at every level"),
          ("Openings", "round arched, keystone"),
          ("Balustrade", "wrought iron"),
          ("Frames", "dark stained timber"),
          ("Balcony curve", "bowed centre bay"),
          ("Projection", f"{EL_BOW_PEAK:.2f} / {EL_BOW_FLANK:.2f} m"),
          ("Balcony area", f"{wave_area('bow'):.1f} m² a floor"),
          ("Top of building", f"+{EL_TOP:.2f}")],
}

EL_KEY["C"] = [("Walls", "warm limestone render"),
               ("Slab nosing", f"rounded, {A_NOSING * 1000:.0f} mm"),
               ("Cove light", "in the underside of the nosing"),
               ("Balustrade", f"clear glass, "
                              f"{V3_WAVE_BALUSTRADE * 1000:.0f} mm inboard"),
               ("Frames", "bronze anodised"),
               ("Balcony curve", "straight runs, radiused"),
               ("Projection", f"{EL_FACET_DEEP:.2f} / {EL_FACET_WAIST:.2f} m"),
               ("Straight formwork",
                f"{2 * EL_FACET_RUN + (V3_X1 - V3_X0) - 2 * EL_FACET_RUN - 2 * EL_FACET_BLEND:.2f}"
                f" of {V3_X1 - V3_X0:.2f} m"),
               ("Balcony area", f"{wave_area('facet'):.1f} m² a floor"),
               ("Top of building", f"+{EL_TOP:.2f}")]

_EL_COMMON = (
    "The exterior only. The plans, site plan and section are agreed and "
    "re-issued to the adopted curve; nothing here changes the rest "
    "of them: same five levels, same 9.50 × 13.50 m footprint, same 1.00 m "
    "setbacks, same openings. Only the skin differs between the schemes.",
    "Every opening drawn here is read from the plan it belongs to rather "
    "than redrawn, and checks.py fails the build if an elevation ever "
    "shows one the plan does not have.",
)

EL_NOTES = {
    "A": list(_EL_COMMON) + [
        "Scheme A takes its material from the contemporary reference: warm "
        "limestone render, a rounded slab nosing with a cove light tucked "
        "into its underside, clear glass balustrades and planting along the "
        "balcony edge. The four south bays read as glazed ribbons between "
        "the slabs.",
        f"The balcony curve is a serpentine — one full period across the "
        f"frontage, {EL_SERP_MEAN + EL_SERP_AMP:.2f} m deep at each end "
        f"drawn in to {EL_SERP_MEAN - EL_SERP_AMP:.2f} m at the waist. At "
        f"{V3_WAVE_WAIST:.2f} m is usable the whole way along; the deep "
        f"ends carry the dining and the furniture.",
        f"This is the adopted curve, and the plans are drawn to it. It "
        f"cost area to take: {wave_area('serpentine'):.1f} m² a floor "
        f"against the {wave_area('agreed'):.1f} m² of the curve it "
        f"replaced, "
        f"{4 * (wave_area('agreed') - wave_area('serpentine')):.0f} m² "
        f"over the four balcony levels. A-000 and A-100 to A-104 are "
        f"re-issued to it.",
        "The balconies do not wrap the corner as the reference does: the "
        "1.00 m setbacks forbid anything projecting west, north or east, "
        "so the cantilever stays on the street frontage.",
    ],
    "B": list(_EL_COMMON) + [
        "Scheme B takes its ornament, not its shape, from the classical "
        "reference: ivory render with terracotta bands at every floor line, "
        "moulded surrounds, round-arched heads with keystones, and "
        "wrought-iron balustrade panels on the same cantilever.",
        "The entrance is a recessed arched porch with a tiled hood, not a "
        "projecting portico. The cantilever already gives 1.96 m of cover "
        "over the front door and the forecourt has no room for one.",
        f"The balcony curve is a bowed centre bay — flanks at "
        f"{EL_BOW_FLANK:.2f} m with a {EL_BOW_WIDTH:.2f} m bow swelling to "
        f"{EL_BOW_PEAK:.2f} m, blended so the bow meets the flanks "
        f"tangentially. Centred on the frontage rather than the door, "
        f"because symmetry is the whole character of the scheme.",
        f"It costs more area than scheme A: {wave_area('bow'):.1f} m² a "
        f"floor, {4 * (wave_area() - wave_area('bow')):.0f} m² over the "
        f"four levels. Adopting it re-issues A-000 and A-101 to A-104.",
        "No pitched roof and no dome. Both raise the building, and at "
        "+16.45 the penthouse is already a fourth storey for most planning "
        "codes.",
    ],
}

EL_NOTES["C"] = list(_EL_COMMON) + [
    "Scheme C is scheme A's skin exactly — warm limestone, cove-lit slab "
    "nosings, glass balustrades, planting, the same arched ground floor. "
    "Only the balcony curve differs, which is the whole point of putting "
    "it beside A.",
    f"The curve is the serpentine built out of straight runs: "
    f"{EL_FACET_RUN:.2f} m flat at {EL_FACET_DEEP:.2f} m deep at each end, "
    f"a flat waist at {EL_FACET_WAIST:.2f} m in the middle, and "
    f"{EL_FACET_BLEND:.2f} m radiused transitions between. Every joint is "
    "a tangent, so from the street the eye still reads one continuous edge.",
    f"What recommends it is the formwork: straight for "
    f"{(V3_X1 - V3_X0) - 2 * EL_FACET_BLEND:.2f} m of the "
    f"{V3_X1 - V3_X0:.2f} m span rather than curved end to end. It also "
    f"carried more area than the serpentine as first drawn; raising that "
    f"curve's waist to {V3_WAVE_WAIST:.2f} m reversed it, and scheme A "
    f"now carries {wave_area('serpentine'):.1f} m² a floor against this "
    f"one's {wave_area('facet'):.1f}.",
    f"It is not the adopted curve. Scheme A was chosen and the plans are "
    f"drawn to its serpentine; moving to this one now would re-issue "
    f"A-000 and A-100 to A-104 a second time, and give up "
    f"{4 * (wave_area('serpentine') - wave_area('facet')):.0f} m² of "
    f"balcony.",
    "The balconies do not wrap the corner: the 1.00 m setbacks forbid "
    "anything projecting west, north or east, so the cantilever stays on "
    "the street frontage.",
]

EL_SIDE_NOTES = list(_EL_COMMON) + [
    "The east and north boundaries are open and carry ordinary windows on "
    "every floor. The west is the blind elevation: louvred ventilation "
    "only, drawn at high level, and nothing projects.",
    "The penthouse stands back 4.81 m from the west and 1.66 m from the "
    "north, so on those two faces it is drawn in thin line behind the roof "
    "terrace parapet.",
    "The balcony appears on the street frontage only and so does not show "
    "on any of these three faces.",
]

# Origins are solved from where the face has to LAND on the sheet rather
# than guessed: ox = wanted_mm - plan_coordinate * (1000 / scale).
EL_ORIGIN = (-130.0, 482.0)       # 1:50, south elevation at x 120..310 mm
EL_CURVE_ORIGIN = (-5.0, 578.0)   # 1:100, the curve in plan beneath it
EL_ORIGIN_3 = ((-21.67, 418.0),   # 1:75, east  at  25..205 mm
               (63.33, 418.0),    #       north at 230..357 mm
               (335.33, 418.0))   #       west  at 382..562 mm


# Scheme A is the one the client chose.  B and C stay in the repository
# because a set that destroys the options it offered cannot show how the
# building was arrived at - but they carry a line saying so, and they are
# not bound into the issued set, because an unmarked drawing of a rejected
# option is a drawing somebody eventually builds.
STATUS_NOT_SELECTED = ("Option not selected — scheme {0} “{1}” was adopted "
                       "at P18. Record only; not for construction.")


def _scheme_issue(sh, scheme):
    """Stamp a scheme sheet according to whether it was chosen."""
    sh.rev = "P21"
    if scheme != SCHEME:
        sh.status = STATUS_NOT_SELECTED.format(
            SCHEME, el.SCHEME[SCHEME]["name"])


def _elevation_sheet(number, scheme):
    """The street frontage at 1:50, with that scheme's curve beside it."""
    s = el.SCHEME[scheme]
    D.set_scale(50, *EL_ORIGIN)
    sh = Sheet(number, f"South Elevation — Scheme {scheme} “{s['name']}”",
               "street frontage", "1:50 @ A1")
    _scheme_issue(sh, scheme)
    F.border(sh)
    el.elevation(sh, "s", scheme)

    sh.dim_h(V3_X0, V3_X1, GARDEN_LEVEL - 1.30, ext_from=GARDEN_LEVEL)
    # the dimensions go on the WEST side: the panel starts at 580 mm and
    # anything east of the building runs underneath it
    for i in range(4):
        sh.dim_v(EL_LEVELS[i], EL_LEVELS[i + 1], V3_X0 - 1.95)
    sh.dim_v(ROOF_LEVEL, V4_TOP, V3_X0 - 1.95)
    sh.dim_v(GARDEN_LEVEL, EL_TOP, V3_X0 - 3.05, f"{EL_TOP - GARDEN_LEVEL:.2f}")

    D.set_scale(100, *EL_CURVE_ORIGIN)
    el.curve_diagram(sh, s["profile"])
    sh.tag((V3_X0 + V3_X1) / 2.0, V3_Y0 + 1.45,
           "THE BALCONY CURVE IN PLAN — IT CANNOT SHOW IN ELEVATION",
           size=2.0, color=GREY)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, f"SCHEME {scheme} — {s['name'].upper()}",
                      EL_KEY[scheme])
    F.notes(sh, y + 6, EL_NOTES[scheme])
    fx.scale_bar(sh, 360, 566, metres=5)
    F.titleblock(sh)
    return sh


def _sides_sheet(number, scheme):
    """East, north and west on one sheet at 1:75."""
    s = el.SCHEME[scheme]
    sh = None
    for i, face in enumerate(("e", "n", "w")):
        lo, hi = el.face_span(face)
        D.set_scale(75, *EL_ORIGIN_3[i])
        if sh is None:
            sh = Sheet(number,
                       f"Side & Rear Elevations — Scheme {scheme} "
                       f"“{s['name']}”", "east, north and west", "1:75 @ A1")
            _scheme_issue(sh, scheme)
            F.border(sh)
        el.elevation(sh, face, scheme)
        sh.tag((lo + hi) / 2.0, GARDEN_LEVEL - 2.40,
               f"{el.FACE_NAME[face].upper()} ELEVATION", size=2.4, color=INK)
        sh.dim_h(lo, hi, GARDEN_LEVEL - 1.30, ext_from=GARDEN_LEVEL)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, f"SCHEME {scheme} — {s['name'].upper()}",
                      EL_KEY[scheme])
    F.notes(sh, y + 6, EL_SIDE_NOTES)
    F.titleblock(sh)
    return sh


def elevations_of(scheme):
    """Both sheets of one scheme - what the checker walks."""
    return {"A": lambda: (sheet_elev_a(), sheet_elev_a_sides()),
            "B": lambda: (sheet_elev_b(), sheet_elev_b_sides()),
            "C": lambda: (sheet_elev_c(), sheet_elev_c_sides())}[scheme]()


# 1:100.  Two views while two schemes were live, one since scheme A was
# adopted - the single view sits between where the two used to, so the
# drawing is centred on the sheet rather than sitting in the top half with
# the rejected option's space left empty under it.
EL_CTX_ORIGIN = ((60.0, 262.0), (60.0, 522.0))
EL_CTX_ONE = (60.0, 392.0)


AX_ORIGIN = ((78.8, 275.2), (256.8, 275.2), (434.8, 275.2))   # 1:250
AX_SCHEMES = (("A", "Wave", "serpentine"), ("C", "Facet", "facet"),
              ("B", "Arcade", "bow"))


def sheet_axonometric():
    """A-430: the three balcony options in 3D, projected from the geometry.

    Not a render.  Every line here is a transform of the same constants
    the plans are drawn from, so the view cannot invent a balcony, a
    garden or a neighbour - which is exactly what an image generator did
    three times before this sheet existed.
    """
    sh = None
    for i, (letter, name, profile) in enumerate(AX_SCHEMES):
        D.set_scale(250, *AX_ORIGIN[i])
        if sh is None:
            sh = Sheet("A-430", "Axonometric — Three Balcony Options",
                       "from the south-west", "1:250 @ A1")
            sh.rev = "P21"
            F.border(sh)
        ax.view(sh, el.SCHEME[letter]["render"], profile)
        u, v = ax.P(V3_X0, V3_Y0, 0.0)
        chosen = "  ·  ADOPTED" if letter == SCHEME else ""
        sh.tag(u - 1.20, v - 3.60,
               f"SCHEME {letter} — {name.upper()}{chosen}",
               size=2.4, color=INK)
        sh.tag(u - 1.20, v - 5.30,
               f"{wave_area(profile):.1f} m² of balcony a floor",
               size=2.0, color=GREY)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "THE FOUR CURVES OFFERED", [
        ("A — serpentine, ADOPTED",
         f"{wave_area('serpentine'):.1f} m² a floor"),
        ("C — facet", f"{wave_area('facet'):.1f} m² a floor"),
        ("B — bowed centre bay", f"{wave_area('bow'):.1f} m² a floor"),
        ("Superseded curve", f"{wave_area('agreed'):.1f} m² a floor"),
        ("Deepest allowed", f"{V3_WAVE_LIMIT:.2f} m"),
        ("Shallowest usable", "0.60 m"),
        ("West neighbour", f"{NBR_W_STOREYS} storeys, blind"),
        ("East neighbour", f"{NBR_E_STOREYS} storey, clay brick")])
    F.notes(sh, y + 6, [
        "Preliminary. Isometric from the south-west, which is the one "
        "corner that shows the street frontage, the blind west wall, the "
        "roof pergola and the entrance garden at once.",
        "This is a projection, not a render: every line is a transform of "
        "the constants the plans are drawn from, so it cannot show a "
        "balcony, a garden or a neighbour that the drawings do not have.",
        f"All three sit on the real plot. The villa is hard against the "
        f"east boundary with a {SETBACK:.2f} m side passage and the "
        f"{V3_X0 - SETBACK:.2f} m entrance garden on the west, the "
        f"three-storey blind neighbour standing back behind it and the "
        f"single-storey clay-brick one a metre to the east.",
        f"Scheme {SCHEME} is the one adopted, and the plans are drawn to "
        f"its curve. B and C are kept here as the record of what was "
        f"offered; their elevation sheets are stamped not selected and "
        f"are not bound into the issue.",
        "The balconies stop at the corner on all three: the 1.00 m "
        "setbacks forbid anything projecting west, north or east.",
        "Faces are painted back to front rather than depth-sorted, so a "
        "detail may overlap where two surfaces nearly touch. The measured "
        "elevations A-400 and A-401 govern.",
    ])
    F.titleblock(sh)
    return sh


def sheet_street_context():
    """A-402: the villa between its two real neighbours, as adopted.

    It carried both live schemes side by side while the client was
    choosing.  Scheme A is chosen, so it carries one: a sheet that still
    showed the rejected option would be read as a building that might
    still be built.
    """
    D.set_scale(100, *EL_CTX_ONE)
    sh = Sheet("A-402", "Street Elevation in Context",
               f"scheme {SCHEME}, as surveyed", "1:100 @ A1")
    sh.rev = "P21"
    F.border(sh)
    el.context_elevation(sh, SCHEME)
    sh.tag(11.50, GARDEN_LEVEL - 2.65,
           f"SCHEME {SCHEME} — {el.SCHEME[SCHEME]['name'].upper()}, ADOPTED",
           size=2.6, color=INK)
    sh.dim_h(0.0, V3_X1 + SETBACK, GARDEN_LEVEL - 1.35,
             ext_from=GARDEN_LEVEL)
    sh.dim_h(0.0, V3_X0, GARDEN_LEVEL - 0.55)
    sh.dim_h(V3_X0, V3_X1, GARDEN_LEVEL - 0.55)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "AS SURVEYED", [
        ("Plot width", "23.00 m"),
        ("Entrance garden, west", f"{V3_X0 - SETBACK:.2f} m"),
        ("Villa frontage", f"{V3_X1 - V3_X0:.2f} m"),
        ("Side passage, east", f"{SETBACK:.2f} m"),
        ("West neighbour", f"{NBR_W_STOREYS} storeys, blind"),
        ("East neighbour", f"{NBR_E_STOREYS} storey, clay brick"),
        ("North neighbour", f"{NBR_N_STOREYS} storey"),
        ("Our top of building", f"+{EL_TOP:.2f}"),
        ("We stand over the east",
         f"{EL_TOP - NBR_E_STOREYS * NBR_STOREY_H:.2f} m")])
    F.notes(sh, y + 6, [
        "Preliminary — the exterior only, and the first drawing in the set "
        "to show the villa against the houses it actually stands between.",
        f"The house is not in the middle of its plot. It sits hard against "
        f"the east boundary with a {SETBACK:.2f} m paved side passage, and "
        f"the whole {V3_X0 - SETBACK:.2f} m entrance garden is on the west, "
        f"gated from the west boundary with a walk running east to the "
        f"front door.",
        f"East: a single storey in clay brick, {SETBACK:.2f} m away. That "
        f"is what lets the east wall be glazed at all — our lowest east "
        f"sill at +{FLOOR_TO_FLOOR + EL_SILL:.2f} clears its roof by "
        f"{FLOOR_TO_FLOOR + EL_SILL - NBR_E_STOREYS * NBR_STOREY_H:.2f} m. "
        f"We stand {EL_TOP - NBR_E_STOREYS * NBR_STOREY_H:.2f} m over it, "
        f"which is worth seeing before the elevations are agreed.",
        f"West: {NBR_W_STOREYS} storeys and blind toward us, drawn in thin "
        f"line because it stands back behind the garden. Nothing of ours "
        f"opens that way in any case — the west wall takes louvred "
        f"ventilation only.",
        f"North: a single storey as well, confirmed by the client and not "
        f"drawn on this south-facing view. The north wall carries windows "
        f"on all five levels; only the ground floor looks at anything, and "
        f"from +{FLOOR_TO_FLOOR:.2f} up they clear its roof as the east "
        f"windows clear the east neighbour's.",
        "The garden wall height is indicative and awaits the client's "
        "choice. Boundaries to be confirmed by measured survey.",
    ])
    fx.scale_bar(sh, 360, 566, metres=10)
    F.titleblock(sh)
    return sh


def sheet_elev_a():
    return _elevation_sheet("A-400", "A")


def sheet_elev_a_sides():
    return _sides_sheet("A-401", "A")


def sheet_elev_b():
    return _elevation_sheet("A-410", "B")


def sheet_elev_c():
    return _elevation_sheet("A-420", "C")


def sheet_elev_c_sides():
    return _sides_sheet("A-421", "C")


def sheet_elev_b_sides():
    return _sides_sheet("A-411", "B")


# ===========================================================================
# A-02 ... A-06  INTERIOR CUTAWAYS
# ===========================================================================
# The last thing the set needed and the only one that is purely for
# looking at: each floor as a doll's house, walls cut at waist height,
# seen from the south-west like A-430.  Not a render and not redrawn -
# the walls come back from the probe that validates the plans, so a
# cutaway is its floor plan in three dimensions and cannot be a different
# building.
# 1:75.  The vertical origin follows the floor: v = z + (x + y) sin30, so
# a cutaway of the penthouse sits ten metres higher up the sheet than one
# of the ground floor unless the origin moves with it.
AX_CUT_SCALE = 75
AX_CUT_OX = 214.0
AX_CUT_OY = 533.0


def _cutaway_data(level):
    """The walls of one floor, and the sill each opening leaves."""
    import checks
    import elevations as el

    build = (sheet_ground, sheet_first, sheet_second, sheet_third,
             sheet_penthouse)[level]
    rec, *_rest, restore = checks._record()
    try:
        sh = build()
    finally:
        restore()
    walls = [(x0, y0, x1, y1, list(op)) for x0, y0, x1, y1, op, _f in rec]
    schedule = list(sh.schedule)
    sills = {}
    for face, lv, a, b, kind in el.openings():
        if lv != level:
            continue
        sill, _head = el.opening_head(face, lv, kind)
        sills[(round(a, 2), round(b, 2))] = sill
    return walls, sills, schedule


def _cutaway_sheet(level, name):
    walls, sills, schedule = _cutaway_data(level)
    D.set_scale(AX_CUT_SCALE, AX_CUT_OX,
                AX_CUT_OY + EL_LEVELS[level] * 1000.0 / AX_CUT_SCALE)
    sh = Sheet(f"A-{level + 2:02d}",
               f"Interior Cutaway — {name} Floor", f"+{EL_LEVELS[level]:.2f}",
               f"1:{AX_CUT_SCALE} @ A1")
    sh.rev = "P21"
    F.border(sh)
    ax.cutaway(sh, level, walls, sills,
               colour=el.SCHEME[SCHEME]["render"],
               profile=el.SCHEME[SCHEME]["profile"])

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "THIS FLOOR", [
        ("Level", f"+{EL_LEVELS[level]:.2f}"),
        ("Rooms", f"{len(schedule)}"),
        ("Net internal", f"{sum(a for _n, a in schedule):.1f} m²"),
        ("Walls cut at", f"{ax.CUT:.2f} m above the floor"),
        ("View", "isometric from the south-west"),
        ("Scheme", f"{SCHEME} — {el.SCHEME[SCHEME]['name']}"),
        ("Balcony", f"{wave_area():.1f} m²" if level else "—"),
        ("Drawn from", f"A-{100 + level}")])
    F.notes(sh, y + 6, [
        f"The {name.lower()} floor as a doll's house, its walls cut "
        f"{ax.CUT:.2f} m above the floor and seen from the south-west, "
        f"which is the corner A-430 uses.",
        "Not a render, and not redrawn. The walls come back from the "
        "same probe that validates the plans, so this is A-"
        f"{100 + level} in three dimensions and cannot be a different "
        f"building.",
        "A window leaves the wall under it standing to its sill; a door "
        "leaves a gap to the floor. Both come from the opening heights "
        "scheduled on ARC-500.",
        "Faces are painted back to front rather than depth-sorted, so a "
        "detail may overlap where two surfaces nearly touch. The plan "
        "governs.",
        "For looking at. Nothing is dimensioned here and nothing should "
        "be measured off it.",
    ])
    F.titleblock(sh)
    return sh


def _cutaway_builders():
    out = []
    for level, name, _fn in RCP_LEVELS:
        def build(level=level, name=name):
            return _cutaway_sheet(level, name)
        build.__name__ = f"sheet_cutaway_{level}"
        out.append(build)
    return out


# ===========================================================================
# EL / ME / PL  THE SERVICES PACKAGE, AS COORDINATION
# ===========================================================================
# Thirty-three sheets, every one class L.  They reserve space and record
# where the architecture already decides something - where the wet rooms
# stack, where the tanks stand, which rooms are habitable - and they draw
# no fitting, no size and no load.
_SVC_CACHE = {}


def _svc_data():
    """Rooms, the stack zone and the isolated wet rooms, measured once."""
    if not _SVC_CACHE:
        rooms = sv.rooms_by_level()
        zone = sv.stack_zone(rooms)
        _SVC_CACHE.update(rooms=rooms, zone=zone,
                          isolated=sv.isolated_wet(rooms, zone))
    return _SVC_CACHE


def _svc_sheet(code, level, title, discipline, marks, purpose):
    data = _svc_data()
    _lv, name, fn = RCP_LEVELS[level]
    # every level on the same origin: these sheets draw the building and
    # not the plot, so the ground floor has no reason to sit where A-100
    # puts it to make room for the garden - it just sat off-centre
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet(code, f"{title} — {name} Floor", f"+{EL_LEVELS[level]:.2f}",
               "1:50 @ A1")
    sh.rev = "P23"
    sh.status = sv.STAMP
    F.border(sh)

    _rcp_plan(sh, globals()[fn])
    here = data["rooms"][level]
    if marks == "habitable":
        n = sv.draw_rooms(sh, here, sv.is_habitable, "ROOMS SERVED")
    elif marks == "wet":
        n = sv.draw_rooms(sh, here, sv.is_wet, "WET ROOMS")
    else:
        n = len(here)
    zone = data["zone"]
    if zone and level in zone[4]:
        sv.draw_zone(sh, zone)
    sv.draw_isolated(sh, data["isolated"].get(level, []))
    if level == 4:
        sv.draw_plant(sh)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "COORDINATION", [
        ("Level", f"+{EL_LEVELS[level]:.2f}"),
        ("Discipline", discipline),
        ("Rooms marked", f"{n}"),
        ("Riser reserved",
         f"{zone[2] - zone[0]:.2f} × {zone[3] - zone[1]:.2f} m"
         if zone else "—"),
        ("Isolated wet rooms", f"{len(data['isolated'].get(level, []))}"),
        ("Soffit", f"+{EL_LEVELS[level] + CLEAR_HEIGHT:.2f}"),
        ("Structural zone", f"{STRUCTURAL_ZONE * 1000:.0f} mm"),
        ("Sizes and loads", "by the engineer")])
    F.notes(sh, y + 6, [
        purpose,
        "Coordination only. No fitting, outlet, diffuser, pipe or cable "
        "is drawn, and no size, load or capacity appears. Those are the "
        "services engineer's design; a layout invented here would be "
        "thrown away, and in the meantime somebody might price it.",
        "What this sheet does fix is space: the riser reserved through "
        "the building, the rooms that have to be served, and the plant "
        "position. Those are expensive to change later, which is why the "
        "architecture states them now.",
        "The plan is run from the floor plan with its fittings switched "
        "off, so it cannot drift from A-"
        f"{100 + level} when a partition moves.",
        "Builder's work — holes, chases, upstands and bases — is to be "
        "agreed against this layout before any slab is poured.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def _svc_schematic(code, title, discipline, purpose):
    """A diagram rather than a plan: levels stacked, riser through them."""
    data = _svc_data()
    zone = data["zone"]
    # Solved, not guessed: the diagram runs x 0.10 to 12.00 and y -2.05 to
    # +17.55, which at 1:50 is 238 x 392 mm, and the drawing column is
    # 552 x 520. The origin centres that. It used to be -150.0, which put
    # the whole diagram 130 mm off the left edge of the sheet - the levels,
    # the riser, the plant, all of it - leaving three issued sheets blank
    # but for their right-hand panel.
    D.set_scale(50, 169.0, 461.0)
    sh = Sheet(code, title, "the whole building", "schematic")
    sh.rev = "P24"
    sh.status = sv.STAMP
    F.border(sh)

    x0, x1 = 1.00, 9.00
    for i, ffl in enumerate(EL_LEVELS):
        sh.line(x0, ffl, x1, ffl, w=LW_CUT, color=INK)
        sh.tag(x0 - 0.90, ffl + 0.30, f"+{ffl:.2f}", size=2.0, color=INK)
        sh.tag(x1 + 1.30, ffl + 0.30, RCP_LEVELS[i][1].upper(), size=1.9,
               color=GREY)
    sh.line(x0, V4_TOP, x1, V4_TOP, w=LW_CUT, color=INK)
    sh.tag(x0 - 0.90, V4_TOP + 0.30, f"+{V4_TOP:.2f}", size=2.0, color=INK)
    sh.tag(x1 + 1.30, V4_TOP + 0.30, "ROOF", size=1.9, color=GREY)

    # the riser, running the full height
    rx0, rx1 = 5.20, 6.40
    sh.rect(rx0, 0.0, rx1 - rx0, V4_TOP, fill="#e8eef2", stroke=INK,
            sw=LW_SECONDARY, dash="5 3")
    sh.tag((rx0 + rx1) / 2.0, V4_TOP / 2.0, "RISER", size=2.2, color=INK,
           rot=-90)
    sh.rect(rx0 - 1.40, V4_TOP, 3.90, 1.10, fill="#e0e4e7", stroke=INK,
            sw=LW_SECONDARY)
    sh.tag((rx0 + rx1) / 2.0, V4_TOP + 0.45, "PLANT / TANKS", size=1.9,
           color=INK)
    sh.line((rx0 + rx1) / 2.0, 0.0, (rx0 + rx1) / 2.0, -1.60, w=LW_CUT,
            color=INK, dash="6 3")
    sh.tag((rx0 + rx1) / 2.0, -2.05, "TO BELOW-GROUND DRAINAGE — BY THE "
           "ENGINEER", size=1.8, color=INK)

    F.heading(sh)
    # no key: the frame's is a plan key - walls, doors, glazing, parapets -
    # and there is not one of those on a riser diagram. A key that
    # describes a different drawing is worse than none.
    y = F.datum_panel(sh, 52, "THE RISER", [
        ("Levels served", f"{len(EL_LEVELS)}"),
        ("Riser reserved",
         f"{zone[2] - zone[0]:.2f} × {zone[3] - zone[1]:.2f} m"
         if zone else "—"),
        ("Wet on", f"{len(zone[4])} levels" if zone else "—"),
        ("Plant", "roof, north-west"),
        ("Height served", f"{V4_TOP:.2f} m"),
        ("Sizes", "by the engineer"),
        ("Capacities", "by the engineer"),
        ("Below ground", "by the engineer")])
    F.notes(sh, y + 6, [
        purpose,
        "A diagram, not a drawing to scale, and it fixes one thing: the "
        "riser runs the full height of the building in the east strip, "
        "where the wet rooms were measured to stack on every level.",
        "No size, capacity, rating or load appears. The engineer's design "
        "fills them in; this reserves the space it has to fit through.",
        "The connection below ground waits on GEO-001 and the drainage "
        "design, and on whatever the authority requires at the boundary.",
    ])
    F.titleblock(sh)
    return sh


def _svc_builders():
    out = []
    for prefix, series, title, discipline, marks, purpose in sv.SYSTEMS:
        for level in range(len(EL_LEVELS)):
            def build(prefix=prefix, series=series, level=level, title=title,
                      discipline=discipline, marks=marks, purpose=purpose):
                return _svc_sheet(f"{prefix}-{series + level}", level, title,
                                  discipline, marks, purpose)
            build.__name__ = f"sheet_{prefix.lower()}_{series + level}"
            out.append(build)
    for code, title, discipline, purpose in sv.SCHEMATICS:
        def build(code=code, title=title, discipline=discipline,
                  purpose=purpose):
            return _svc_schematic(code, title, discipline, purpose)
        build.__name__ = f"sheet_{code.lower().replace('-', '_')}"
        out.append(build)
    return out


# ===========================================================================
# STR-001 ... STR-500  THE STRUCTURAL PACKAGE, AS LAYOUT
# ===========================================================================
# Twelve sheets, every one class L.  The grid, the coordinates, the spans,
# the slab edges and the beam lines are exact because they fall out of the
# architecture.  Sizes, depths, reinforcement and loads are nowhere on any
# of them, and the status line on every sheet says so.
STR_ORIGIN = (-60.0, 450.0)          # 1:50, as the floor plans
STR_SITE_ORIGIN = SITE_ORIGIN        # 1:75, as the site plan


def _str_sheet(number, title, level_txt, scale="1:50 @ A1"):
    sh = Sheet(number, title, level_txt, scale)
    sh.rev = "P21"
    sh.status = st.STAMP
    F.border(sh)
    return sh


def _str_panel(sh, rows, notes):
    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "THE FRAME", rows)
    F.notes(sh, y + 6, notes)
    F.titleblock(sh)
    return sh


_STR_COMMON = (
    "Layout only. No member size, no slab or footing depth, no "
    "reinforcement and no load appears on this sheet or anywhere in the "
    "STR series. Those are the structural engineer's, and a column "
    "schedule with sizes invented by an architect is worse than none, "
    "because somebody builds it.",
    "The grid, the column coordinates, the spans and the slab edges are "
    "measured from the same geometry the architecture is drawn from and "
    "are exact.",
)


def _grid_rows():
    ew, ns = grid_spans()
    return ([("Grid", f"{len(GRID_X)} × {len(GRID_Y)}, "
                      f"{GRID_LETTER[0]}–{GRID_LETTER[-1]} / 1–"
                      f"{len(GRID_Y)}")]
            + [(f"Span {n}", f"{v:.2f} m") for n, v in ew + ns]
            + [("Columns", f"{len(grid_columns())}"),
               ("Column section", f"{COL * 1000:.0f} × {COL * 1000:.0f} mm"),
               ("Structural zone", f"{STRUCTURAL_ZONE * 1000:.0f} mm"),
               ("Storey height", f"{FLOOR_TO_FLOOR:.2f} m")])


def sheet_str_notes():
    """STR-001: what the package is, and what it deliberately is not."""
    sh = _str_sheet("STR-001", "Structural Notes & Design Criteria",
                    "the whole frame", "NTS")
    sh.text_mm(18, 26, "STRUCTURAL NOTES & DESIGN CRITERIA", size=6.0,
               anchor="start", weight=700, ls=0.6)
    sh.text_mm(18, 35, f"{F.LOCATION}   ·   " + "   ·   ".join(F.CODES),
               size=2.6, anchor="start", color=GREY, ls=0.35)
    sh.line_mm(18, 40, 570, 40, w=0.5, color=INK)

    blocks = [
        ("What this package is",
         ["The frame set out: a grid, twelve column coordinates, six slab "
          "outlines, the spans between them and the lines where a beam is "
          "required. All of it falls out of the architecture and all of "
          "it is exact.",
          "It exists so the structural engineer starts from a coordinated "
          "layout rather than from nothing, and so the architecture "
          "cannot quietly move underneath the structure."]),
        ("What this package is not",
         ["It is not a structural design. No member size, no slab or "
          "footing depth, no reinforcement, no cover, no load and no "
          "analysis appears anywhere in it.",
          "Design criteria — dead and imposed loads, wind, the seismic "
          "zone and its design ground acceleration — are set and signed "
          "by the structural engineer to ECP 201, and the concrete to "
          "ECP 203. ECP 201 has five seismic zones; which governs "
          "Shamandeel is named by the engineer, not assumed here."]),
        ("What it waits on",
         ["GEO-001, the soil investigation. The ground is central Nile "
          "Delta and well characterised as a region, which is enough to "
          "assume a foundation type and lay it out, and not enough to "
          "size one. Allowable bearing pressure, the water table and "
          "sulphate content are plot figures.",
          "SUR-001, the measured survey, for the boundary STR-400 sits "
          "on."]),
        ("The one rule the architecture already settled",
         [f"A {WT * 1000:.0f} mm wall needs a beam under it, and a beam "
          f"is a column line, a wall below, or a secondary beam landing "
          f"on primary beams. Every {WT * 1000:.0f} mm wall in this "
          f"building stands on a grid line, with one exception: the "
          f"penthouse's north wall, which is a line load on the +13.20 "
          f"slab spanning B to C. STR-305 carries a secondary beam under "
          f"it for that reason.",
          f"The {PT * 1000:.0f} mm partitions do not stand on grid "
          f"lines and do not need to; they are carried by the slab."]),
    ]
    y = 52.0
    for head, paras in blocks:
        sh.text_mm(18, y, head.upper(), size=3.0, anchor="start",
                   weight=700, ls=0.45)
        sh.line_mm(18, y + 2.2, 570, y + 2.2, w=0.25, color=GREY)
        y += 10.0
        for t in paras:
            for line in F._wrap(t, 96):
                sh.text_mm(18, y, line, size=2.2, anchor="start")
                y += 6.0
            y += 2.4
        y += 5.0
    if y > 566:
        raise ValueError(f"STR-001 runs to y={y:.0f} mm")
    return _str_panel(sh, _grid_rows(), list(_STR_COMMON) + [
        "Design criteria to ECP 201 and concrete to ECP 203, set and "
        "signed by the structural engineer. No value is assumed here.",
        "The package waits on GEO-001 for anything below ground and on "
        "SUR-001 for the boundary.",
    ])


def sheet_str_excavation():
    """STR-100: the extent of the dig, which is all that can be drawn."""
    D.set_scale(75, *STR_SITE_ORIGIN)
    sh = _str_sheet("STR-100", "Excavation, Grading & Shoring",
                    f"{GARDEN_LEVEL:.2f} garden, +0.00 villa", "1:75 @ A1")
    with sh.on("G-ANNO-BNDY"):
        sh.poly(PLOT, stroke=INK, sw=LW_SECONDARY, dash="9 2 1.6 2")
    sh.rect(0.0, -2.60, 23.0, 2.60, fill="#f6f6f6", stroke="none", sw=0)
    sh.tag(11.50, -1.35, "S T R E E T", size=2.6, color=GREY)

    # the dig: the footprint plus a working margin, which is a layout
    # decision and not a design one
    margin = 1.00
    sh.rect(V3_X0 - margin, V3_Y0 - margin,
            V3_X1 - V3_X0 + 2 * margin, V3_Y1 - V3_Y0 + 2 * margin,
            fill="#eceff1", stroke=INK, sw=LW_SECONDARY, dash="6 3")
    _hatch(sh, V3_X0 - margin, V3_Y0 - margin,
           V3_X1 - V3_X0 + 2 * margin, V3_Y1 - V3_Y0 + 2 * margin,
           pitch=0.9, color="#d6dade")
    sh.rect(V3_X0, V3_Y0, V3_X1 - V3_X0, V3_Y1 - V3_Y0, fill="#ffffff",
            stroke=INK, sw=LW_CUT)
    sh.tag((V3_X0 + V3_X1) / 2.0, (V3_Y0 + V3_Y1) / 2.0, "VILLA FOOTPRINT",
           size=2.4, color=INK)
    sh.tag((V3_X0 + V3_X1) / 2.0, V3_Y0 - 1.70,
           f"{margin:.2f} m WORKING MARGIN — EXTENT ONLY, NO DEPTH",
           size=1.9, color=INK)
    sh.dim_h(V3_X0 - margin, V3_X1 + margin, GARDEN_LEVEL * 0 + 1.20)

    D.set_scale(75, *STR_SITE_ORIGIN)
    return _str_panel(sh, [
        ("Footprint", f"{(V3_X1 - V3_X0) * (V3_Y1 - V3_Y0):.1f} m²"),
        ("Working margin", f"{margin:.2f} m"),
        ("Dig extent",
         f"{(V3_X1 - V3_X0 + 2 * margin) * (V3_Y1 - V3_Y0 + 2 * margin):.1f}"
         f" m²"),
        ("Dig depth", "by GEO-001 and STR-101"),
        ("Formation level", "by GEO-001"),
        ("Shoring", "by the engineer"),
        ("Water table", "by GEO-001"),
        ("Neighbour, east", f"{NBR_E_STOREYS} storey, {SETBACK:.2f} m away"),
    ], list(_STR_COMMON) + [
        "The extent of the dig is a layout decision and is drawn. Its "
        "depth is not: formation level follows the foundation, the "
        "foundation follows the bearing pressure, and that is GEO-001.",
        "Shoring, dewatering and the sequence of excavation are the "
        "engineer's and the contractor's. The east neighbour stands "
        f"{SETBACK:.2f} m from the dig and is a single storey in clay "
        f"brick; its protection is to be designed before anything is "
        f"excavated against it.",
    ])


def sheet_str_foundation():
    """STR-101: a pad under every column, at the right coordinate."""
    D.set_scale(50, *STR_ORIGIN)
    sh = _str_sheet("STR-101", "Foundation Layout", "formation by GEO-001")
    st.grid(sh)
    nominal = st.footings(sh)
    st.columns_at(sh, 0, label=False)
    st.grid_dims(sh)
    sh.tag((GRID_X[0] + GRID_X[-1]) / 2.0, GRID_Y[-1] + 2.55,
           "PAD SIZES ARE NOT SHOWN — SEE THE NOTES", size=2.0, color=INK)
    return _str_panel(sh, _grid_rows() + [
        ("Pads", f"{len(grid_columns())}"),
        ("Pad size", "by the engineer"),
        ("Founding depth", "by GEO-001")],
        list(_STR_COMMON) + [
        f"A pad is drawn under every column at the coordinate the column "
        f"stands on. The square shown is a nominal {nominal:.2f} m so the "
        f"layout reads; it is not a size and must not be scaled.",
        "Pad sizes, founding depth, blinding and reinforcement follow the "
        "allowable bearing pressure, the water table and the sulphate "
        "content, which come from GEO-001 and do not exist yet.",
        "A raft or piles may prove more appropriate than pads. That is "
        "the engineer's call once the ground is known; the coordinates "
        "on this sheet hold either way.",
    ])


def sheet_str_columns():
    """STR-200: the grid, and every column's coordinate."""
    D.set_scale(50, *STR_ORIGIN)
    sh = _str_sheet("STR-200", "Column Schedule & Grid", "all levels")
    st.grid(sh)
    st.slab_edge(sh, 0)
    st.grid(sh, bubbles=False)
    st.columns_at(sh, 0)
    st.grid_dims(sh)

    y = 52.0
    sh.text_mm(IX_COL_X[0] * 0 + 580, 0, "", size=2)   # keep the panel clean
    rows = [("Mark", "x", "y", "Levels")]
    for mark, x, yy, levels in grid_columns():
        rows.append((mark, f"{x:.2f}", f"{yy:.2f}",
                     f"{levels[0]}–{levels[-1]}"))
    return _str_panel(sh, _grid_rows() + [
        ("Columns to +9.90", f"{sum(1 for c in grid_columns() if 4 not in c[3])}"),
        ("Columns to +13.20", f"{sum(1 for c in grid_columns() if 4 in c[3])}"),
        ("Section", "by the engineer")],
        list(_STR_COMMON) + [
        "Every column is marked by its grid intersection and stands at "
        "the coordinate printed beside it. Eight run from the foundation "
        "to +13.20; four — B2, B3, C2 and C3 — carry on to the roof over "
        "the penthouse.",
        "Sections and reinforcement are the engineer's. The marks and "
        "coordinates are what this sheet issues.",
    ])


def _str_framing(slab, level, datum):
    """One slab framing layout."""
    D.set_scale(50, *STR_ORIGIN)
    sh = _str_sheet(f"STR-{301 + slab}", f"Slab Framing Layout at {datum}",
                    datum)
    st.slab_edge(sh, level)
    st.grid(sh)
    st.beams(sh, level)
    st.voids(sh, level)
    st.columns_at(sh, min(level, 4))
    st.grid_dims(sh)
    extra = []
    if level == GRID_EXCEPTION[0]:
        extra.append(
            "This slab carries the one wall in the building that does not "
            "stand on a grid line: the penthouse's north wall, a line "
            "load spanning B to C. The secondary beam under it is drawn "
            "dashed; its size is the engineer's.")
    if 0 < level < 5:
        extra.append(
            f"The cantilever beyond grid 1 is the balcony: "
            f"{wave_area():.1f} m² a floor, {V3_WAVE_DEEP:.2f} m at its "
            f"deepest. It is the most engineering-sensitive element here "
            f"and has its own sheet, STR-500.")
    return _str_panel(sh, _grid_rows() + [
        ("This slab", datum),
        ("Slab thickness", "by the engineer")],
        list(_STR_COMMON) + extra + [
        f"Primary beams run on the grid, because every {WT * 1000:.0f} "
        f"mm wall stands on a grid line. The {PT * 1000:.0f} mm "
        f"partitions do not and do not need to: they are carried by the "
        f"slab.",
    ])


def sheet_str_walls():
    """STR-400: retaining and boundary walls."""
    D.set_scale(75, *STR_SITE_ORIGIN)
    sh = _str_sheet("STR-400", "Retaining & Boundary Walls",
                    f"{GARDEN_LEVEL:.2f} to +0.00", "1:75 @ A1")
    with sh.on("G-ANNO-BNDY"):
        sh.poly(PLOT, stroke=INK, sw=LW_SECONDARY, dash="9 2 1.6 2")
    sh.rect(0.0, -2.60, 23.0, 2.60, fill="#f6f6f6", stroke="none", sw=0)
    sh.tag(11.50, -1.35, "S T R E E T", size=2.6, color=GREY)
    sh.rect(V3_X0, V3_Y0, V3_X1 - V3_X0, V3_Y1 - V3_Y0, fill="#ffffff",
            stroke=INK, sw=LW_CUT)
    sh.tag((V3_X0 + V3_X1) / 2.0, (V3_Y0 + V3_Y1) / 2.0, "VILLA", size=2.6,
           color=INK)
    gx, gy, gw = EW_GATE
    with sh.on("S-WALL"):
        sh.wall(0.0, 0.0, gx, 0.30)
        sh.wall(gx + gw, 0.0, V3_X0 - SETBACK, 0.30)
    sh.tag(6.40, 0.80, f"STREET WALL — {GARDEN_WALL_H:.2f} m, INDICATIVE",
           size=1.9, color=INK)
    sh.tag(6.40, -0.60, "LINE AWAITS SUR-001", size=1.7, color=GREY)
    sh.tag((V3_X0 + V3_X1) / 2.0, GARDEN_LEVEL * 0 + 2.30,
           f"GARDEN {GARDEN_LEVEL:.2f} TO VILLA +0.00 — "
           f"{abs(GARDEN_LEVEL):.2f} m OF RETAINED GROUND", size=1.9,
           color=INK)
    return _str_panel(sh, [
        ("Street wall", f"{V3_X0 - SETBACK - gw:.2f} m"),
        ("Street wall height", f"{GARDEN_WALL_H:.2f} m, indicative"),
        ("Gate", f"{gw:.2f} m"),
        ("Garden level", f"{GARDEN_LEVEL:.2f}"),
        ("Villa level", "+0.00"),
        ("Ground retained", f"{abs(GARDEN_LEVEL):.2f} m"),
        ("Wall design", "by the engineer"),
        ("Boundary line", "by SUR-001"),
    ], list(_STR_COMMON) + [
        f"The garden sits {abs(GARDEN_LEVEL):.2f} m below the villa, so "
        f"the change in level is retained somewhere along the west face "
        f"and around the forecourt. Where is drawn; how is not.",
        "The street wall's height is the client's choice and indicative "
        "at 1.20 m; its line awaits the measured survey. Nothing else on "
        "this sheet depends on either.",
        "Retaining design, drainage behind the wall, movement joints and "
        "foundations are the engineer's and wait on GEO-001.",
    ])


def sheet_str_cantilever():
    """STR-500: the balcony, at 1:20, because it is the hard one."""
    D.set_scale(20, -340.0, 300.0)
    sh = _str_sheet("STR-500", "Cantilever Balcony Structure",
                    f"{V4_LEVEL} and the three floors below", "1:20 @ A1")
    pts = wave_points(n=200)
    sh.poly([(pts[0][0], V3_Y0)] + pts + [(pts[-1][0], V3_Y0)],
            fill="#e7ebee", stroke=INK, sw=LW_CUT)
    sh.poly(wave_points(n=200, offset=V3_WAVE_BALUSTRADE), close=False,
            stroke=GREY, sw=LW_SECONDARY)
    sh.line(V3_X0, V3_Y0, V3_X1, V3_Y0, w=LW_CUT, color=INK)
    for x in GRID_X:
        sh.line(x, V3_Y0 - V3_WAVE_DEEP - 0.60, x, V3_Y0 + 0.90,
                w=LW_THIN, color=GREY, dash="9 2 1.6 2")
        sh.circle(x, V3_Y0 + 1.45, 0.42, fill="#ffffff", stroke=INK,
                  sw=LW_SECONDARY)
        sh.tag(x, V3_Y0 + 1.29, GRID_LETTER[GRID_X.index(x)], size=2.2,
               color=INK)
    for x, lbl in ((V3_X0, f"{V3_WAVE_DEEP:.2f}"),
                   (V3_WAVE_WAIST_X, f"{V3_WAVE_WAIST:.2f}"),
                   (V3_X1, f"{V3_WAVE_DEEP:.2f}")):
        sh.dim_v(wave_edge(x), V3_Y0, x)
    sh.tag((V3_X0 + V3_X1) / 2.0, V3_Y0 - V3_WAVE_DEEP - 1.15,
           "SLAB EDGE — THICKNESS, ROOT DEPTH AND REINFORCEMENT BY THE "
           "ENGINEER", size=2.0, color=INK)
    return _str_panel(sh, [
        ("Projection, deepest", f"{V3_WAVE_DEEP:.2f} m"),
        ("Projection, at the waist", f"{V3_WAVE_WAIST:.2f} m"),
        ("Span of the curve", f"{V3_X1 - V3_X0:.2f} m"),
        ("Area a floor", f"{wave_area():.1f} m²"),
        ("Levels", "4"),
        ("Total", f"{4 * wave_area():.1f} m²"),
        ("Balustrade", f"glass, {V3_WAVE_BALUSTRADE * 1000:.0f} mm inboard"),
        ("Root and reinforcement", "by the engineer"),
    ], list(_STR_COMMON) + [
        f"A {V3_WAVE_DEEP:.2f} m cantilever on a curve, repeated on four "
        f"levels, is the single most engineering-sensitive element in "
        f"this building. It is drawn at 1:20 for that reason and for no "
        f"other.",
        "The curve, the span, the projection at every point and the "
        "balustrade line are exact. The slab thickness, the root depth "
        "into the floor behind, the top steel and the deflection and "
        "vibration checks are entirely the engineer's.",
        "Grid line 1 runs along the face the cantilever springs from. "
        "The balcony projects south of it and is unsupported at its far "
        "edge on all four levels.",
    ])


def _str_builders():
    out = [sheet_str_notes, sheet_str_excavation, sheet_str_foundation,
           sheet_str_columns]
    for i, (level, datum) in enumerate(
            [(0, "+0.00"), (1, "+3.30"), (2, "+6.60"), (3, "+9.90"),
             (4, f"+{ROOF_LEVEL:.2f}"), (5, f"+{V4_TOP:.2f}")]):
        def build(i=i, level=level, datum=datum):
            return _str_framing(i, level, datum)
        build.__name__ = f"sheet_str_slab_{i}"
        out.append(build)
    out += [sheet_str_walls, sheet_str_cantilever]
    return out


# ===========================================================================
# ARC-001 / ARC-002  COVER, INDEX, GENERAL NOTES
# ===========================================================================
IX_COL_X = (18.0, 300.0)
IX_TOP, IX_PITCH, IX_PER_COL = 62.0, 11.0, 44
IX_NUM, IX_TITLE, IX_LEVEL, IX_SCALE, IX_REV = 0.0, 36.0, 140.0, 214.0, 252.0


# The cover's own row, which is the one row of the index that cannot be
# built - a sheet cannot build itself to find out its own name.  Held here
# rather than written inline so checks.py can compare it against the sheet
# it claims to describe.
IX_SELF = ("ARC-001", "Cover Sheet & Drawing Index", "the whole set",
           "NTS", "P22")

_INDEXING = False


def sheet_index(skip=None):
    """Every sheet in the set: number, title, level, scale, revision.

    Built rather than listed.  An index typed out beside the drawings is
    wrong within a revision or two, and it is the one document a reader
    uses to decide a drawing does not exist.  `skip` is the builder
    asking, because a sheet cannot build itself to find out its own name.

    The guard matters: `skip` is matched by identity, so anything that
    rebinds a builder's name - a test, a patch - stops it matching and
    the index starts building the sheet that is building the index.  That
    used to be an infinite recursion with a thousand-line traceback.  It
    is now one sentence.
    """
    global _INDEXING
    if _INDEXING:
        raise RuntimeError(
            "sheet_index re-entered: a sheet is building the index while "
            "the index is building it. Pass skip=<that builder>, and "
            "check nothing has rebound its name.")
    _INDEXING = True
    try:
        rows = []
        for build in SHEETS:
            if build is skip:
                continue
            sh = build()
            rows.append((sh.number, sh.title, sh.level, sh.scale_note,
                         getattr(sh, "rev", None) or F.REV))
        return rows
    finally:
        _INDEXING = False


def _index_row(sh, x, y, row, issued):
    number, title, level, scale, rev = row
    ink = INK if number in issued else LIGHT
    sh.text_mm(x + IX_NUM, y, number, size=2.3, anchor="start", weight=700,
               color=ink)
    sh.text_mm(x + IX_TITLE, y, title, size=2.2, anchor="start", color=ink)
    sh.text_mm(x + IX_LEVEL, y, level, size=2.0, anchor="start", color=GREY)
    sh.text_mm(x + IX_SCALE, y, scale.replace(" @ A1", ""), size=2.0,
               anchor="start", color=GREY)
    sh.text_mm(x + IX_REV, y, rev, size=2.2, anchor="end", weight=700,
               color=ink)
    sh.line_mm(x, y + 1.8, x + IX_REV, y + 1.8, w=0.12, color="#e2e2e2")


def sheet_cover():
    """ARC-001: the cover sheet, project data and the drawing index."""
    import export_share

    # the cover cannot build itself to find its own name, so it is the one
    # row written down - and ARC-001 missing from its own index would be
    # the first thing a reader noticed
    rows = [IX_SELF] + sheet_index(skip=sheet_cover)
    issued = set(export_share.SET_ORDER)
    order = {n: i for i, n in enumerate(export_share.SET_ORDER)}
    rows.sort(key=lambda r: (order.get(r[0], 10_000), r[0]))

    sh = Sheet(IX_SELF[0], IX_SELF[1], IX_SELF[2], IX_SELF[3])
    sh.rev = IX_SELF[4]
    F.border(sh)

    sh.text_mm(IX_COL_X[0], 26, F.PROJECT, size=6.6, anchor="start",
               weight=700, ls=0.6)
    sh.text_mm(IX_COL_X[0], 35, f"{F.LOCATION}   ·   {F.CLIENT}", size=2.6,
               anchor="start", color=GREY, ls=0.35)
    sh.line_mm(IX_COL_X[0], 40, IX_COL_X[1] + IX_REV, 40, w=0.5, color=INK)

    for col in (0, 1):
        part = rows[col * IX_PER_COL:(col + 1) * IX_PER_COL]
        if not part:
            continue
        x = IX_COL_X[col]
        for off, txt, anc in ((IX_NUM, "SHEET", "start"),
                              (IX_TITLE, "TITLE", "start"),
                              (IX_LEVEL, "LEVEL", "start"),
                              (IX_SCALE, "SCALE", "start"),
                              (IX_REV, "REV", "end")):
            sh.text_mm(x + off, 50, txt, size=2.0, anchor=anc, color=GREY,
                       ls=0.4)
        sh.line_mm(x, 52.0, x + IX_REV, 52.0, w=0.25, color=GREY)
        for i, row in enumerate(part):
            _index_row(sh, x, IX_TOP + i * IX_PITCH, row, issued)
    if len(rows) > 2 * IX_PER_COL:
        raise ValueError(
            f"ARC-001: {len(rows)} sheets and the index holds "
            f"{2 * IX_PER_COL}")
    sh.text_mm(IX_COL_X[0], 566,
               "SHEETS IN GREY ARE BUILT BUT NOT PART OF THE ISSUE — "
               "WITHDRAWN OR NOT SELECTED, AND EACH SAYS WHICH ON ITS FACE",
               size=2.0, anchor="start", color=LIGHT, ls=0.4)

    outside, _measured = ew_unallocated()
    gia = (V3_X1 - V3_X0) * (V3_Y1 - V3_Y0)
    F.heading(sh, sub="PROJECT DATA   ·   DRAWING INDEX   ·   "
                      f"REVISION {F.REVISIONS[-1][0]}")
    y = F.datum_panel(sh, 52, "PROJECT DATA", [
        ("Plot", f"{plot_area():.1f} m²"),
        ("Footprint", f"{gia:.1f} m²"),
        ("Site coverage", f"{100 * gia / plot_area():.1f} %"),
        ("Levels", f"{len(EL_LEVELS)}"),
        ("Floor to floor", f"{FLOOR_TO_FLOOR:.2f} m"),
        ("Top of building", f"+{EL_TOP:.2f}"),
        ("External works", f"{outside:.1f} m²"),
        ("Sheets in the issue", f"{len(issued)}"),
        ("Sheets built", f"{len(rows)}"),
        ("Codes", "ECP 201 / ECP 203")])
    F.notes(sh, y + 6, [
        "The index is built, not listed: every row is a sheet this "
        "project can actually draw, with the title and revision that "
        "sheet carries. An index typed beside the drawings goes wrong "
        "within a revision or two, and it is the one document a reader "
        "trusts when deciding a drawing does not exist.",
        "Rows in grey are built but outside the issue, and each says why "
        "on its own face: the A-300 enlargements are withdrawn at P22, "
        "being of apartments the villa no longer has, and the scheme B "
        "and C elevations are stamped not selected.",
        "The prefix is part of the number. A-402 is the street elevation "
        "and ARC-402 the second floor's ceiling plan.",
        "Deliverables beyond the drawings — the structural, services and "
        "quantities packages — are registered on ARC-000 with their "
        "status.",
        "Not for construction. Issued for the owner's record, costing and "
        "construction information.",
    ])
    F.titleblock(sh)
    return sh


# What ARC-002 hands the code check: our figure for each item a domestic
# building is normally tested against, with the required value left open.
# The figures are ours and exact.  The requirement, the clause and the
# verdict are not: they belong to ECP 201 and ECP 203 and to whoever signs
# the compliance statement, and a column of invented limits would be worse
# than an empty one.
def _compliance_rows():
    sx0, sy0, sx1, sy1 = V3_STAIR
    risers = round(FLOOR_TO_FLOOR / V3_STAIR_RISE)
    return [
        ("Site coverage",
         f"{100 * (V3_X1 - V3_X0) * (V3_Y1 - V3_Y0) / plot_area():.1f} %"),
        ("Setback, west / north / east", f"{SETBACK:.2f} m each"),
        ("Height, top of building", f"+{EL_TOP:.2f}"),
        ("Storeys", f"{len(EL_LEVELS)}"),
        ("Floor to floor", f"{FLOOR_TO_FLOOR:.2f} m"),
        ("Clear height", f"{CLEAR_HEIGHT:.2f} m"),
        ("Stair, private", f"{risers}R at "
                           f"{1000 * FLOOR_TO_FLOOR / risers:.0f} × "
                           f"{V3_STAIR_GOING * 1000:.0f}"),
        # the flight, not the well: the well is 2.00 m and holds two
        # flights either side of a 0.20 m gap
        ("Stair, flight width",
         f"{(sx1 - sx0 - V3_STAIR_WELL) / 2:.2f} m"),
        ("Stair, well", f"{sx1 - sx0:.2f} × {sy1 - sy0:.2f} m"),
        ("Balustrade and parapet", "1.10 m"),
        ("Window sill", f"{EL_SILL:.2f} m above floor"),
        ("Balcony projection", f"{V3_WAVE_DEEP:.2f} m maximum"),
        ("Overlooking, east", f"single storey {SETBACK:.2f} m away"),
        ("Overlooking, west", f"{NBR_W_STOREYS} storeys, blind"),
        ("Overlooking, north", f"{NBR_N_STOREYS} storey"),
    ]


def sheet_general_notes():
    """ARC-002: general notes, symbols and the code compliance matrix."""
    sh = Sheet("ARC-002", "General Notes, Symbols & Compliance",
               "the whole set", "NTS")
    sh.rev = "P21"
    sh.status = ("Layout for the architect of record — the compliance "
                 "matrix is completed and signed against ECP 201 and "
                 "ECP 203.")
    F.border(sh)

    sh.text_mm(18, 26, "GENERAL NOTES & COMPLIANCE MATRIX", size=6.0,
               anchor="start", weight=700, ls=0.6)
    sh.text_mm(18, 35, f"{F.LOCATION}   ·   " + "   ·   ".join(F.CODES),
               size=2.6, anchor="start", color=GREY, ls=0.35)
    sh.line_mm(18, 40, 570, 40, w=0.5, color=INK)

    notes = [
        "Figured dimensions govern. Do not scale from these drawings.",
        "Dimensions are in millimetres unless a metre value is shown with "
        "two decimals. Levels are in metres to the project datum, which "
        "is the ground floor finished floor level, +0.00.",
        "Dimensions to structural faces unless noted. Opening sizes are "
        "structural; frame and tolerance allowances are the supplier's.",
        "Every discrepancy between drawings is to be referred before any "
        "work is set out or any material ordered.",
        "Boundaries, levels and the neighbours' heights are as described "
        "by the client and await a measured survey, SUR-001.",
        "Foundations, framing and every member size are the structural "
        "engineer's and are not set on any architectural sheet. The "
        "STR series is issued as layout for that design.",
        "Services layouts are coordination only. Cable, duct and pipe "
        "sizes, loads and capacities are the services engineer's.",
        "Materials, finishes, waterproofing build-ups and performance "
        "specifications are not set by these drawings.",
        "Not for construction.",
    ]
    y = 52.0
    for i, t in enumerate(notes, 1):
        for j, line in enumerate(F._wrap(t, 62)):
            sh.text_mm(18, y, (f"{i}.  " if j == 0 else "     ") + line,
                       size=2.2, anchor="start")
            y += 6.0
        y += 2.6

    y += 6.0
    sh.text_mm(18, y, "CODE COMPLIANCE MATRIX", size=3.0, anchor="start",
               weight=700, ls=0.45)
    sh.line_mm(18, y + 2.2, 570, y + 2.2, w=0.25, color=GREY)
    y += 10.0
    for off, txt, anc in ((0.0, "ITEM", "start"), (210.0, "AS DRAWN", "end"),
                          (300.0, "REQUIRED", "start"),
                          (420.0, "CLAUSE", "start"),
                          (520.0, "COMPLIES", "start")):
        sh.text_mm(18 + off, y, txt, size=2.0, anchor=anc, color=GREY,
                   ls=0.4)
    sh.line_mm(18, y + 2.0, 570, y + 2.0, w=0.25, color=GREY)
    y += 9.0
    for item, ours in _compliance_rows():
        sh.text_mm(18, y, item, size=2.2, anchor="start")
        sh.text_mm(228, y, ours, size=2.2, anchor="end", weight=700)
        for xx in (318, 438, 538):
            sh.line_mm(xx, y + 1.0, xx + 90 if xx < 500 else xx + 20,
                       y + 1.0, w=0.2, color="#c8c8c8")
        sh.line_mm(18, y + 2.4, 570, y + 2.4, w=0.12, color="#e2e2e2")
        y += 9.6
    if y > 566:
        raise ValueError(f"ARC-002: the notes and matrix run to y={y:.0f}")

    F.heading(sh, sub="GENERAL NOTES   ·   SYMBOLS   ·   COMPLIANCE")
    y = F.legend(sh, 52)
    F.notes(sh, y + 6, [
        "The matrix carries our figure for every item a house is normally "
        "tested against, measured from the geometry and exact.",
        "The required value, the clause and the verdict are left open on "
        "purpose. They belong to ECP 201 and ECP 203 and to whoever signs "
        "the compliance statement; a column of limits invented here would "
        "be worse than an empty one, because it would be believed.",
        "The symbols panel is the same key every sheet in the set "
        "carries, so a reader who has this sheet can read any of them.",
    ])
    F.titleblock(sh)
    return sh


# ===========================================================================
# ARC-400 ... ARC-404  REFLECTED CEILING PLANS
# ===========================================================================
# One per level, and each is the floor plan itself with everything that is
# not the enclosure switched off - no sanitaryware, no furniture, no door
# swings, no dimension chains.  Running the plan rather than redrawing it
# is the whole point: a ceiling plan that was traced would be a drawing
# that quietly stops agreeing with its floor the first time a partition
# moves.
#
# What the sheet adds is the ceiling: the soffit level, the stair void
# open above, the balcony soffit with its cove, and a bulkhead over every
# wet room.  The bulkheads are not placed by eye - they are drawn over the
# rooms the plan itself labels as wet, because that is where the drainage
# has to run.  Their depth, their exact extent and anything inside them
# are the services engineer's, and the sheet says so.
RCP_WET = ("bath", "ensuite", "wc", "shower", "kitchen", "laundry",
           "utility", "cloak")
RCP_BULK = 0.35                 # the zone a bulkhead is shown over, in plan

RCP_LEVELS = ((0, "Ground", "_villa_ground_floor"),
              (1, "First", "_villa_living_floor"),
              (2, "Second", "_villa_bedroom_floor"),
              (3, "Third", "_plan_third"),
              (4, "Penthouse", "_villa_penthouse"))


def _rcp_plan(sh, draw):
    """Run a floor plan with everything but its enclosure switched off.

    Returns the rooms it labelled, so the bulkheads can be put where the
    plan says the wet rooms are rather than where they look right.
    """
    rooms = []
    saved_fx = {k: v for k, v in vars(fx).items()
                if callable(v) and not k.startswith("_")}
    saved = (D.Sheet.door, D.Sheet.window, D.Sheet.dim_h, D.Sheet.dim_v,
             D.Sheet.room)

    def nothing(*_a, **_k):
        return None

    def rec_room(self, x, y, w, h, name, **kw):
        rooms.append((x, y, w, h, name))
        return saved[4](self, x, y, w, h, name, **kw)

    for k in saved_fx:
        setattr(fx, k, nothing)
    D.Sheet.door = D.Sheet.window = nothing
    D.Sheet.dim_h = D.Sheet.dim_v = nothing
    D.Sheet.room = rec_room
    try:
        draw(sh)
    finally:
        for k, v in saved_fx.items():
            setattr(fx, k, v)
        (D.Sheet.door, D.Sheet.window, D.Sheet.dim_h, D.Sheet.dim_v,
         D.Sheet.room) = saved
    return rooms


def _rcp_bulkheads(sh, rooms):
    """A bulkhead over every room the plan calls wet."""
    n = 0
    for x, y, w, h, name in rooms:
        if not any(k in name.lower() for k in RCP_WET):
            continue
        # hatched rather than filled: a solid tint sat over the room name
        # the plan had just written, and the name is why the bulkhead is
        # there at all
        _hatch(sh, x, y, w, h, pitch=0.42, color="#d3dade")
        sh.rect(x, y, w, h, fill="none", stroke=GREY, sw=LW_SECONDARY,
                dash="3 2")
        sh.rect(x + RCP_BULK, y + RCP_BULK, max(w - 2 * RCP_BULK, 0.10),
                max(h - 2 * RCP_BULK, 0.10), fill="none", stroke=LIGHT,
                sw=LW_THIN, dash="2 1.5")
        n += 1
    return n


def _rcp_sheet(level, name, draw):
    ffl = EL_LEVELS[level]
    soffit = ffl + CLEAR_HEIGHT
    D.set_scale(50, *(GF_ORIGIN if level == 0 else PLAN_ORIGIN))
    sh = Sheet(f"ARC-{400 + level}",
               f"Reflected Ceiling Plan — {name} Floor", f"+{ffl:.2f}",
               "1:50 @ A1")
    sh.rev = "P21"
    F.border(sh)

    rooms = _rcp_plan(sh, draw)
    bulks = _rcp_bulkheads(sh, rooms)

    # the stair well, open above on every floor it passes
    sx0, sy0, sx1, sy1 = V3_STAIR
    if level < 4:
        sh.rect(sx0, sy0, sx1 - sx0, sy1 - sy0, fill="none", stroke=INK,
                sw=LW_SECONDARY, dash="6 3")
        # clear of the B-B cut line, which runs through the middle of
        # this well at y 10.80
        sh.tag((sx0 + sx1) / 2.0, sy1 - 0.55, "VOID OVER STAIR",
               size=1.7, color=GREY)

    # the balcony soffit, which is the one piece of modelled ceiling
    if level > 0:
        sh.poly(wave_points(), close=False, stroke=GREY, sw=LW_SECONDARY)
        sh.poly(wave_points(offset=V3_WAVE_REVEAL), close=False,
                stroke=LIGHT, sw=LW_THIN, dash="2.4 1.4")
        sh.tag(17.25, V3_Y0 - 0.55,
               f"BALCONY SOFFIT — {A_COVE * 1000:.0f} mm COVE IN THE "
               f"{A_NOSING * 1000:.0f} mm NOSING", size=1.7, color=GREY)

    sh.level_tag(V3_X0 + 0.80, V3_Y0 + 1.30, f"SOFFIT +{soffit:.2f}")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "THE CEILING", [
        ("Finished floor level", f"+{ffl:.2f}"),
        ("Soffit, generally", f"+{soffit:.2f}"),
        ("Clear height", f"{CLEAR_HEIGHT:.2f} m"),
        ("Structural zone over", f"{STRUCTURAL_ZONE * 1000:.0f} mm"),
        ("Floor to floor", f"{FLOOR_TO_FLOOR:.2f} m"),
        ("Bulkheads shown", f"{bulks} wet rooms"),
        ("Bulkhead depth", "by the services engineer"),
        ("Light fittings", "see EL-200 series")])
    F.notes(sh, y + 6, [
        f"The ceiling of the {name.lower()} floor, seen from below. Drawn "
        f"by running the floor plan with its sanitaryware, furniture, "
        f"door swings and dimension chains switched off, so it cannot "
        f"stop agreeing with A-{100 + level} when a partition moves.",
        f"Soffit is +{soffit:.2f} throughout, {CLEAR_HEIGHT:.2f} m clear, "
        f"under a {STRUCTURAL_ZONE * 1000:.0f} mm structural zone. Any "
        f"local drop below that is a bulkhead and is shown as one.",
        "A bulkhead is drawn over every room the plan calls wet, because "
        "that is where the drainage runs. The outline is the room; the "
        "depth, the exact extent and everything inside it are the "
        "services engineer's and are set on the ME and PL series.",
        "No light fitting is drawn. Fittings, switching and emergency "
        "provision are the EL-200 series; a layout invented here would "
        "only have to be thrown away.",
        "Ceiling finishes, board type, moisture resistance in the wet "
        "rooms and access panels are specification, not geometry, and "
        "are not set on this sheet.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def _rcp_builders():
    """One sheet builder per level, named so SHEETS can hold them."""
    out = []
    for level, name, fn in RCP_LEVELS:
        def build(level=level, name=name, fn=fn):
            return _rcp_sheet(level, name, globals()[fn])
        build.__name__ = f"sheet_ceiling_{level}"
        out.append(build)
    return out


# ===========================================================================
# ARC-700  EXTERNAL WORKS AND LANDSCAPE
# ===========================================================================
# The garden is drawn on A-000 as context for the building.  It is also a
# trade package - paving, turf, a pergola, a gate, five trees and a street
# wall - and nothing measured it.  Drawn on its own here, at the plot's
# scale, with every area read from the same constants the site plan draws
# from, so the quantities and the drawing cannot disagree.
EW_HATCH = {"Paved walk": "#ececec", "Forecourt": "#dadada",
            "Barbecue terrace": "#dadada", "Side passages": "#f0f0f0",
            "Turf": "#e8efe4"}


def sheet_external_works():
    """ARC-700: the garden, the forecourt and the side passages."""
    D.set_scale(75, *SITE_ORIGIN)
    sh = Sheet("ARC-700", "External Works & Landscape",
               f"{GARDEN_LEVEL:.2f} garden, +0.00 villa", "1:75 @ A1")
    sh.rev = "P21"
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        sh.poly(PLOT, stroke=INK, sw=LW_SECONDARY, dash="9 2 1.6 2")
    sh.rect(0.0, -2.60, 23.0, 2.60, fill="#f6f6f6", stroke="none", sw=0)
    sh.tag(11.50, -1.35, "S T R E E T", size=2.6, color=GREY)

    villa_garden(sh)

    # the villa itself, as an outline only: this sheet is about what is
    # around it, and a full plan here would compete with A-100
    sh.rect(V3_X0, V3_Y0, V3_X1 - V3_X0, V3_Y1 - V3_Y0, fill="#ffffff",
            stroke=INK, sw=LW_CUT)
    sh.tag((V3_X0 + V3_X1) / 2.0, (V3_Y0 + V3_Y1) / 2.0 + 0.45, "VILLA",
           size=2.8, color=INK)
    sh.tag((V3_X0 + V3_X1) / 2.0, (V3_Y0 + V3_Y1) / 2.0 - 0.75,
           "SEE A-100", size=2.0, color=GREY)

    # the street wall and the gate in it
    gx, gy, gw = EW_GATE
    with sh.on("A-WALL-EXTR"):
        sh.wall(0.0, 0.0, gx, 0.30)
        sh.wall(gx + gw, 0.0, V3_X0 - SETBACK, 0.30)
    sh.tag(6.40, -0.55, f"STREET WALL {GARDEN_WALL_H:.2f} m, INDICATIVE",
           size=1.8, color=GREY)
    sh.tag(gx + gw / 2.0, 0.75, f"GATE {gw:.2f} m", size=1.8, color=INK)

    sh.dim_h(0.0, V3_X0 - SETBACK, 6.30)
    sh.dim_h(V3_X0 - SETBACK, V3_X0, 6.30)
    sh.dim_v(0.35, 3.35, -1.20)
    sh.level_tag(0.90, 2.45, f"GARDEN {GARDEN_LEVEL:.2f}")

    # the area schedule panel reads sh.schedule, which the plans fill
    # through Sheet.room; nothing here is a room, so it is filled from the
    # same constants the drawing above was made from
    sh.schedule = list(ew_areas().items())
    F.heading(sh)
    y = F.legend(sh, 52)
    outside, measured = ew_unallocated()
    y = F.schedule(sh, y + 8, extra=[
        ("Pergola over the walk", f"{EW_PERGOLA[2] * EW_PERGOLA[3]:.1f} m² "
                                  f"timber"),
        ("Trees", f"{len(EW_TREES)} nr"),
        ("Street wall", f"{V3_X0 - SETBACK - gw:.2f} m at "
                        f"{GARDEN_WALL_H:.2f} m, indicative"),
        ("Gate", f"{gw:.2f} m leaf"),
        ("Steps to the front door", f"{ENTRY_RISERS} risers"),
        ("Plot less the villa", f"{outside:.1f} m²"),
        ("Not measured here", f"{outside - measured:.1f} m²")])
    F.notes(sh, y + 6, [
        "The garden as a trade package rather than as context. Every area "
        "is read from the constants A-000 draws from, so this sheet and "
        "the site plan cannot disagree about a width.",
        "The three 1.00 m setbacks are our own land and are paved as side "
        "passages, reached from the forecourt on the east and the garden "
        "on the west. They are the largest paved item on the sheet.",
        f"The street wall is {GARDEN_WALL_H:.2f} m high and INDICATIVE: "
        f"its height, its coping and its finish await the client, and its "
        f"line awaits the measured survey. Nothing else on the sheet "
        f"depends on it.",
        "Paving materials, bedding, falls, sub-base, turf specification "
        "and irrigation are not set by the geometry and are not invented "
        "here. The quantities are ours; the specification is not.",
        "The forecourt is overhung by the balcony for up to 1.95 m, which "
        "is what covers the front door without a porch. See A-000 and "
        "A-400.",
        f"The schedule measures ground cover, so the pergola is listed "
        f"beside it rather than in it - it stands over paving already "
        f"counted. {outside - measured:.1f} m² of the plot outside the "
        f"villa is not measured here: margins, the bin standing and the "
        f"entrance steps. It is shown rather than absorbed.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# ARC-600  CONSTRUCTION DETAILS
# ===========================================================================
# The last sheet of package B, and the one most easily written as fiction.
# Four junctions at 1:10, each carrying two kinds of line: the dimensions
# this project owns, figured, and the build-ups nobody has specified,
# hatched and named against the specification topic that must answer for
# them.  details.py says more about why.
#
# The sheet exists partly because the bill already referred to it - "slab
# edges, the nosing and the cove are additional and are detailed on
# ARC-600" - which was a reference to a drawing that did not exist.  A
# document that cites a sheet nobody has drawn is worse than one that
# admits the gap.
# Two columns of two.  The origin of each cell is the detail's own datum,
# not the middle of the box: the drawing sits to the left of it and the
# note column to the right, which is why they are not evenly spaced.
DET_CELLS = [(150.0, 240.0), (420.0, 240.0), (150.0, 476.0), (420.0, 476.0)]


def sheet_details():
    """ARC-600: four junctions, figured but not specified."""
    sh = Sheet("ARC-600", "Construction Details", "typical junctions",
               "1:5 / 1:10 @ A1")
    sh.rev = "P22"
    F.border(sh)

    for i, (cx, cy) in enumerate(DET_CELLS):
        det.draw(sh, i, cx, cy)
        code, title = det.TITLES[i]
        sh.text_mm(cx - 132, cy + 74, code, size=3.4, anchor="start",
                   weight=700)
        sh.text_mm(cx - 118, cy + 74, title.upper(), size=2.6,
                   anchor="start", ls=0.35)
        sh.text_mm(cx - 118, cy + 79, det.scale_note(i), size=2.1,
                   anchor="start", color=GREY)
        sh.line_mm(cx - 132, cy + 82, cx + 126, cy + 82, w=0.25,
                   color=GREY)

    F.heading(sh, sub="TYPICAL JUNCTIONS   ·   1:5 AND 1:10   ·   MILLIMETRES")
    y = F.datum_panel(sh, 52, "FIGURED FROM THE GEOMETRY", [
        ("External / party wall", f"{WT * 1000:.0f} mm"),
        ("Internal partition", f"{PT * 1000:.0f} mm"),
        ("Parapet", f"{PARAPET * 1000:.0f} mm × 1100 high"),
        ("Structural zone", f"{STRUCTURAL_ZONE * 1000:.0f} mm"),
        ("Clear height", f"{CLEAR_HEIGHT:.2f} m"),
        ("Slab nosing", f"{A_NOSING * 1000:.0f} mm"),
        ("Cove light", f"{A_COVE * 1000:.0f} × {A_COVE * 1000:.0f} mm"),
        ("Balustrade", f"{BALUSTRADE_H * 1000:.0f} mm high"),
        ("Glass set in from the edge", f"{V3_WAVE_BALUSTRADE * 1000:.0f} mm")])
    F.notes(sh, y + 8, [
        "Layout only, and in a stricter sense than the rest of the set: "
        "every figured dimension here is this project's and exact, and "
        "everything hatched is a build-up nobody has specified yet. The "
        "hatched zones are drawn at a plausible thickness so the junction "
        "can be read; none of those thicknesses is a specification.",
        "Each hatched zone names the QS-003 topic that has to answer for "
        "it. Until that topic is answered the detail cannot be built, "
        "priced or warranted, and no quantity is taken from this sheet.",
        f"The {STRUCTURAL_ZONE * 1000:.0f} mm structural zone is ours "
        f"because it sets the floor-to-floor; how much of it is slab, and "
        f"what is in the slab, is the engineer's. No reinforcement, cover "
        f"or grade appears here.",
        "Thermal performance, waterproofing warranty, movement and "
        "buildability are the specifier's. The drawing shows where things "
        "meet, not that the meeting works.",
        "D1 is the junction the whole frontage depends on, and it is the "
        "one carrying a 2.00 m cantilever: read it with STR-500.",
    ])
    F.titleblock(sh)
    return sh


# ===========================================================================
# ARC-301  TRANSVERSE SECTION B-B
# ===========================================================================
# A-A cuts north-south at x 20.70 and shows the building's depth.  Nothing
# showed its width: the 9.50 m between the two 1.00 m setbacks, the spine
# that every floor hangs off, the east glazing that only works because the
# neighbour that side is one storey, and the stair well running the full
# height of the west strip.
#
# The cut is at y 10.80, which is inside the stair well (9.12 to 12.42) and
# clear of every cross wall in the house.  What it passes through was read
# off the plans by the same probe that produced SEC_WALLS, not written from
# memory: patch Sheet.wall and Sheet.room, build each floor, and record
# what crosses the line.
SEC_Y_V = 10.80
SEC2_ORIGIN = (-170.0, 448.0)        # 1:50, x 11.50 at 60 mm, -2.60 at 500

# (x0, x1) of every wall the cut crosses, by level.  The west wall is blind
# here on every floor - its louvres are elsewhere along the face - and the
# east wall is glazed at the cut on three floors out of five, which the
# section works out from FACADE rather than being told.
SEC2_WALLS = {
    0: [(12.50, 12.80), (17.31, 17.61), (21.70, 22.00)],
    1: [(12.50, 12.80), (17.31, 17.61), (18.90, 19.02), (21.70, 22.00)],
    2: [(12.50, 12.80), (17.31, 17.61), (18.90, 19.02), (21.70, 22.00)],
    3: [(12.50, 12.80), (17.31, 17.61), (21.70, 22.00)],
    4: [(17.31, 17.61), (18.71, 18.83), (21.70, 22.00)],
}
SEC2_ROOMS = {
    0: [(12.80, 17.31, "Reception hall"), (17.61, 21.70, "Kitchen")],
    1: [(12.80, 17.31, "Living area"), (17.61, 18.90, "Lobby"),
        (19.02, 21.70, "Shared bath")],
    2: [(12.80, 14.80, "Stair"), (14.92, 17.31, "Landing"),
        (17.61, 18.90, "Lobby"), (19.02, 21.70, "Shared bath")],
    3: [(12.80, 17.31, "Living area"), (17.61, 21.70, "Shared bath")],
    4: [(17.61, 18.71, "Hall"), (18.83, 21.70, "Bath")],
}


def villa_section_line_b(sh, x0=11.95, x1=22.55):
    """The B-B cut line, so the transverse section is located on the plans."""
    with sh.on("A-ANNO-SYMB"):
        sh.line(x0, SEC_Y_V, x1, SEC_Y_V, w=LW_THIN, color=INK,
                dash="9 2 1.6 2")
    for xx in (x0, x1):
        sh.circle(xx, SEC_Y_V, 0.45, fill="#ffffff", stroke=INK,
                  sw=LW_SECONDARY)
        sh.tag(xx, SEC_Y_V - 0.17, "B", size=2.6, color=INK)
    # both arrows look north, which is the direction the section is drawn
    for xx in (x0 + 0.70, x1 - 0.70):
        sh.poly([(xx, SEC_Y_V + 0.62), (xx + 0.26, SEC_Y_V + 0.06),
                 (xx - 0.26, SEC_Y_V + 0.06)], fill=INK, stroke=INK,
                sw=LW_THIN)


def _east_glazed_at_cut(level):
    """Is the east wall an opening where B-B crosses it?

    Worked out from the plan's own opening list rather than recorded, so a
    window moved along that face changes the section with it.
    """
    return any(a <= SEC_Y_V <= b for a, b in FACADE[level]["e"])


def sheet_section_b():
    """ARC-301: the transverse section, looking north."""
    D.set_scale(50, *SEC2_ORIGIN)
    sh = Sheet("ARC-301", "Section B–B — Transverse", "looking north",
               "1:50 @ A1")
    sh.rev = "P21"
    F.border(sh)

    x_w, x_e = V3_X0, V3_X1                 # 12.50 .. 22.00
    roof, top = ROOF_LEVEL, V4_TOP

    # --- ground, and the setback strip each side -------------------------
    for a, b in ((x_w - SETBACK, x_w), (x_w, x_e), (x_e, x_e + SETBACK)):
        sh.rect(a, -2.60, b - a, 2.10, fill="#f4f4f4", stroke="none", sw=0)
        _hatch(sh, a, -2.60, b - a, 2.10, pitch=0.7, color="#dcdcdc")
    sh.line(x_w - SETBACK, GARDEN_LEVEL, x_w, GARDEN_LEVEL, w=LW_CUT,
            color=INK)
    sh.line(x_e, GARDEN_LEVEL, x_e + SETBACK, GARDEN_LEVEL, w=LW_CUT,
            color=INK)
    sh.tag(x_w - 0.50, GARDEN_LEVEL - 0.80, "1.00 m SETBACK", size=1.7,
           color=GREY, rot=-90)
    sh.tag(x_e + 0.50, GARDEN_LEVEL - 0.80, "1.00 m SETBACK", size=1.7,
           color=GREY, rot=-90)

    for a, b in ((x_w, x_w + WT), (x_e - WT, x_e)):
        sh.wall(a - 0.30, -1.55, b + 0.30, -1.15)
        sh.wall(a, -1.15, b, -STRUCTURAL_ZONE)

    # --- the four floors --------------------------------------------------
    for lv in range(4):
        ffl = lv * FLOOR_TO_FLOOR
        _slab(sh, x_w, x_e, ffl)
        # the west wall is blind at this cut; the east may be glazed
        sh.wall(x_w, ffl, x_w + WT, ffl + CLEAR_HEIGHT)
        if _east_glazed_at_cut(lv):
            _glazed(sh, x_e - WT, x_e, ffl)
        else:
            sh.wall(x_e - WT, ffl, x_e, ffl + CLEAR_HEIGHT)
        for a, b in SEC2_WALLS[lv]:
            if a <= x_w + 0.01 or b >= x_e - 0.01:
                continue                        # the two external walls
            sh.wall(a, ffl, b, ffl + CLEAR_HEIGHT)
        sh.level_tag(x_w + 0.75, ffl, f"FFL +{ffl:.2f}")
        for a, b, name in SEC2_ROOMS[lv]:
            sh.tag((a + b) / 2.0, ffl + 1.05, name.upper(),
                   size=2.0 if b - a > 2.4 else 1.6, color=INK)

    # --- roof deck, open corridor and the penthouse on top ----------------
    _slab(sh, x_w, x_e, roof)
    sh.level_tag(x_w + 0.75, roof, f"FFL {V4_LEVEL}")
    for a, b in ((x_w, x_w + PARAPET), (V4_X0, V4_X0 + WT),
                 (x_e - WT, x_e)):
        if a < V4_X0:
            sh.wall(a, roof, b, roof + 1.10, fill=PARAPET_FILL)
    sh.wall(V4_X0, roof, V4_X0 + WT, roof + CLEAR_HEIGHT)
    sh.wall(V4_X1 - WT, roof, V4_X1, roof + CLEAR_HEIGHT)
    for a, b in SEC2_WALLS[4]:
        if V4_X0 < a and b < V4_X1:
            sh.wall(a, roof, b, roof + CLEAR_HEIGHT)
    _slab(sh, V4_X0, V4_X1, top)
    for a, b in ((V4_X0, V4_X0 + WT), (V4_X1 - WT, V4_X1)):
        sh.wall(a, top, b, top + PH_UPSTAND, fill=PARAPET_FILL)
    for a, b, name in SEC2_ROOMS[4]:
        sh.tag((a + b) / 2.0, roof + 1.05, name.upper(),
               size=2.0 if b - a > 2.4 else 1.6, color=INK)
    sh.tag((x_w + V4_X0) / 2.0, roof + 1.05, "OPEN CORRIDOR", size=2.0,
           color=INK)
    sh.tag((x_w + V4_X0) / 2.0, roof + 0.45, "PERGOLA OVER, OPEN TO SKY",
           size=1.6, color=GREY)

    # --- the stair, seen beyond the cut through its own open well ---------
    sx0, _sy0, sx1, _sy1 = V3_STAIR
    with sh.on("A-STRS-BEYD"):
        for lv in range(4):
            ffl = lv * FLOOR_TO_FLOOR
            risers = round(FLOOR_TO_FLOOR / V3_STAIR_RISE)
            rise = FLOOR_TO_FLOOR / risers
            for n in range(1, risers + 1):
                z = ffl + n * rise
                if z > ffl + CLEAR_HEIGHT:
                    break
                sh.line(sx0, z, sx1, z, w=LW_THIN, color=LIGHT)
            sh.line(sx0, ffl, sx0, ffl + CLEAR_HEIGHT, w=LW_THIN,
                    color=LIGHT)
            sh.line(sx1, ffl, sx1, ffl + CLEAR_HEIGHT, w=LW_THIN,
                    color=LIGHT)
            # the half landing, heavier: end-on, it is the one line that
            # says this is a dog-leg and not a single flight
            sh.line(sx0, ffl + rise * (risers // 2), sx1,
                    ffl + rise * (risers // 2), w=LW_SECONDARY, color=GREY)
    sh.tag((sx0 + sx1) / 2.0, 2 * FLOOR_TO_FLOOR + 2.05,
           "STAIR BEYOND", size=1.7, color=GREY)

    sh.dim_h(x_w, x_e, -3.35, ext_from=GARDEN_LEVEL)
    sh.dim_h(x_w - SETBACK, x_e + SETBACK, -4.15)
    sh.dim_v(GARDEN_LEVEL, EL_TOP, x_e + 1.85,
             f"{EL_TOP - GARDEN_LEVEL:.2f}")
    for lv in range(4):
        sh.dim_v(lv * FLOOR_TO_FLOOR, (lv + 1) * FLOOR_TO_FLOOR,
                 x_w - 1.45)
    sh.dim_v(roof, top, x_w - 1.45)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "THE CUT", [
        ("Section line", f"y = {SEC_Y_V:.2f}, looking north"),
        ("Width between setbacks", f"{x_e - x_w:.2f} m"),
        ("Structural spine", f"x {V3_SPINE_X0:.2f} – {V3_SPINE_X0 + WT:.2f}"),
        ("Floor to floor", f"{FLOOR_TO_FLOOR:.2f} m"),
        ("Clear height", f"{CLEAR_HEIGHT:.2f} m"),
        ("Structural zone", f"{STRUCTURAL_ZONE * 1000:.0f} mm"),
        ("Top of building", f"+{EL_TOP:.2f}"),
        ("East glazed at this cut", "levels 0, 1 and 2")])
    F.notes(sh, y + 6, [
        f"Cut at y = {SEC_Y_V:.2f}, inside the stair well and clear of "
        f"every cross wall, looking north. A-A cuts the other way and "
        f"shows the depth; this is the only drawing of the width.",
        "What the cut passes through was read off the plans by the probe "
        "in checks.py, not written from memory, and whether the east wall "
        "is glazed at the cut is worked out from the plan's own opening "
        "list each time the sheet is built.",
        "The east wall is glazed on the lower three floors and solid on "
        "the third, which is the plans' arrangement and not a drafting "
        "choice. It can be glazed at all because the neighbour a metre "
        "east is a single storey.",
        "The stair is beyond the cut, not in it: its flights run "
        "north-south, so this section crosses them end-on and they are "
        "drawn in thin line as seen through the open well.",
        "At the penthouse the west half of the plate is the open "
        "corridor, outside the flat and open to the sky under its "
        "pergola. Foundations are indicative pending GEO-001.",
    ])
    fx.scale_bar(sh, 60, 556, metres=5)
    F.titleblock(sh)
    return sh


# ===========================================================================
# ARC-106  ROOF PLAN
# ===========================================================================
# The one plan the set never had.  Everything above +13.20 was drawn on
# A-104 as the penthouse's floor; nothing drew the surfaces that actually
# shed water - the roof over the penthouse at +16.45, the two terraces and
# the balcony at +13.20, the tank deck - or said which way any of them
# fall.
#
# What is derived here and what is not, is the whole of it.  The outlines,
# the parapets, the upstands, the tank deck and the levels come straight
# out of geometry.py and are exact.  The falls and the outlet positions do
# not: they are the architectural intent, drawn so the drainage package has
# something to coordinate against, and PL-200 and PL-300 set the real
# positions, the pipe sizes and the overflow provision.  They are tagged
# INDICATIVE on the sheet for that reason.
RF_FALL = "1:60"               # the intent; confirm against the spec
RF_UPSTAND = 0.15              # waterproofing turned up at every upstand


def _rf_outlet(sh, x, y, label=True):
    """A rainwater outlet - indicative position, see PL-200."""
    sh.circle(x, y, 0.18, fill="#ffffff", stroke=INK, sw=LW_SECONDARY)
    sh.circle(x, y, 0.09, fill=INK, stroke=INK, sw=LW_FIXTURE)
    if label:
        # under the outlet, not beside it: beside it lands on the fall
        # arrow that points at it
        sh.tag(x, y - 0.62, "RWO", size=1.6, color=GREY)


def _rf_fall(sh, x0, y0, x1, y1):
    """A fall arrow: from the high point toward the outlet."""
    sh.line(x0, y0, x1, y1, w=LW_THIN, color=GREY, dash="3 2")
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    sh.poly([(x1, y1), (x1 - 0.34 * ux + 0.16 * px, y1 - 0.34 * uy + 0.16 * py),
             (x1 - 0.34 * ux - 0.16 * px, y1 - 0.34 * uy - 0.16 * py)],
            fill=GREY, stroke=GREY, sw=LW_FIXTURE)
    # three-quarters of the way along rather than halfway, which on the
    # long roof arrows is where the area label sits
    sh.tag(x0 + 0.72 * dx - 0.34 * px, y0 + 0.72 * dy - 0.34 * py,
           RF_FALL, size=1.6, color=GREY)


def _roof_area(sh, box, name, level, at, area=None, tint="#f4f6f7",
               rot=None):
    """One surface that sheds water: its outline, its name, its level."""
    x0, y0, x1, y1 = box
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill=tint, stroke=GREY,
            sw=LW_SECONDARY)
    ax_, ay = at
    sh.tag(ax_, ay, name.upper(), size=2.0, color=INK, rot=rot)
    off = (0.0, -0.62) if rot is None else (-0.62, 0.0)
    sh.tag(ax_ + off[0], ay + off[1],
           f"{area if area is not None else (x1 - x0) * (y1 - y0):.1f} m²"
           f"  ·  {level}", size=1.7, color=GREY, rot=rot)


def sheet_roof():
    """ARC-106: the roof over the penthouse, and every surface below it.

    A roof plan that showed only the top slab would leave the terraces,
    the balcony and the plant deck undrained, which is where a flat roof
    actually fails.  All of them are here, each with its level, its falls
    and an outlet.
    """
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("ARC-106", "Roof Plan", f"+{V4_TOP:.2f} / {V4_LEVEL}",
               "1:50 @ A1")
    sh.rev = "P21"
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")

    sx0, sy0, sx1, sy1 = V3_STAIR
    # the zones come from geometry.roof_zones(), which the quantities read
    # too: the sheet and the bill must give one roof area, not two
    zones = {n: (box, area) for n, box, area in roof_zones()}
    at = {"West terrace": ((13.78, 6.30), None, "#f4f6f7"),
          "Open corridor": ((16.60, 8.00), -90, "#f4f6f7"),
          "North strip": ((19.60, 16.30), None, "#f4f6f7"),
          "Penthouse roof": ((19.65, 10.20), None, "#e7ebee")}
    for name, (where, rot, tint) in at.items():
        box, area = zones[name]
        level = f"+{V4_TOP:.2f}" if name == "Penthouse roof" else V4_LEVEL
        _roof_area(sh, box, name, level, where, area=area, tint=tint,
                   rot=rot)

    # the stair well, open to the sky under its canopy, is not a surface
    sh.rect(sx0, sy0, sx1 - sx0, sy1 - sy0, fill="#ffffff", stroke=GREY,
            sw=LW_SECONDARY, dash="4 2")
    sh.tag((sx0 + sx1) / 2.0, (sy0 + sy1) / 2.0 + 0.30, "STAIR WELL",
           size=1.8, color=GREY)
    sh.tag((sx0 + sx1) / 2.0, (sy0 + sy1) / 2.0 - 0.45, "CANOPY OVER",
           size=1.6, color=GREY)

    # falls, and an outlet at the foot of each
    for x0, y0, x1, y1, ox, oy in (
            (14.50, 4.65, 13.45, 4.65, 13.05, 4.65),      # west terrace
            (17.05, 4.65, 15.70, 4.65, 15.25, 4.65),      # corridor
            (18.10, 16.30, 20.95, 16.30, 21.40, 16.30),   # north terrace
            (18.40, 13.60, 18.40, 5.45, 18.40, 4.85),     # roof, west half
            (20.90, 13.60, 20.90, 5.45, 20.90, 4.85)):    # roof, east half
        _rf_fall(sh, x0, y0, x1, y1)
        _rf_outlet(sh, ox, oy)

    # the wave cantilever, which sheds over its own edge
    fx.wave_balcony(sh, wave_points(), V3_Y0, V3_WAVE_BALUSTRADE,
                    V3_WAVE_REVEAL, label=None, area=None, show_area=False)

    parapet(sh, V3_X0, V3_Y0, V3_X0 + PARAPET, V3_Y1)
    parapet(sh, V3_X0, V3_Y1 - PARAPET, V3_X1, V3_Y1)
    parapet(sh, V3_X1 - PARAPET, V4_Y1, V3_X1, V3_Y1)

    qx0, qy0, qx1, qy1 = V4_PLANT
    sh.rect(qx0, qy0, qx1 - qx0, qy1 - qy0, fill="#e0e4e7", stroke=INK,
            sw=LW_SECONDARY)
    sh.tag((qx0 + qx1) / 2.0, 16.25, "PLANT DECK", size=1.8, color=INK)
    sh.tag((qx0 + qx1) / 2.0, 15.68, "WATER TANKS", size=1.6, color=GREY)

    px0, py0, px1, py1 = V4_PERGOLA
    with sh.on("A-FLOR-OVER"):
        sh.rect(px0, py0, px1 - px0, py1 - py0, sw=LW_HIDDEN, stroke=GREY,
                dash="5 3")
    sh.tag(15.25, 12.40, "PERGOLA OVER — OPEN, NOT A ROOF", size=1.7,
           color=GREY, rot=-90)

    # the penthouse walls under the roof, so the top slab reads in context
    with sh.on("A-WALL-BELW"):
        for a, b, c, d in ((V4_X0, V4_Y0, V4_X1, V4_Y0 + WT),
                           (V4_X0, V4_Y0, V4_X0 + WT, V4_Y1),
                           (V4_X0, V4_Y1 - WT, V4_X1, V4_Y1),
                           (V4_X1 - WT, V4_Y0, V4_X1, V4_Y1)):
            sh.rect(a, b, c - a, d - b, fill="#cdd2d6", stroke=GREY,
                    sw=LW_HIDDEN)

    sh.dim_h(V3_X0, V3_X1, 1.05, ext_from=V3_Y0)
    sh.dim_v(V4_Y0, V4_Y1, 23.05)
    sh.dim_v(V4_Y1, V3_Y1, 23.05)
    sh.tag(17.25, 0.35,
           f"BALCONY {V4_LEVEL} — {V4_BALCONY:.1f} m², FALLS TO THE EDGE",
           size=1.9, color=INK)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "THE ROOF", [
        ("Roof over penthouse", f"+{V4_TOP:.2f}"),
        ("Terraces and balcony", V4_LEVEL),
        ("Parapet", f"{PARAPET * 1000:.0f} mm × 1100 high"),
        ("Waterproofing upstand", f"{RF_UPSTAND * 1000:.0f} mm minimum"),
        ("Falls", f"{RF_FALL}, indicative"),
        ("Outlets", "5, indicative — see PL-200"),
        ("Balcony", f"{V4_BALCONY:.1f} m², falls to the edge"),
        ("Plant deck", "water tanks, north-west")])
    F.notes(sh, y + 6, [
        "The surfaces that shed water, which no other sheet draws: the "
        "roof over the penthouse at +16.45, the terraces and the open "
        "corridor at +13.20, the balcony, and the plant deck.",
        "Outlines, parapets, the plant deck and the levels are measured "
        "from the geometry and are exact. The falls and the outlet "
        "positions are architectural intent, drawn so the drainage "
        "package has something to coordinate against.",
        "PL-200 and PL-300 set the outlet positions, the pipe sizes, the "
        "downpipe routes and the overflow provision. Nothing here is a "
        "drainage design.",
        f"Waterproofing turned up {RF_UPSTAND * 1000:.0f} mm minimum at "
        f"every parapet, upstand and threshold and dressed into the "
        f"outlet. Membrane and insulation build-up to the specification.",
        "The pergola over the corridor is open and is not a roof: the "
        "corridor under it is an external surface and drains as one. The "
        "stair well is open to the sky under its canopy.",
        "The areas here are drainage zones, not the use areas on A-104, "
        "and they divide the same surfaces differently — hence \"north "
        "strip\" rather than A-104\'s north terrace, which also counts "
        "the slab north of the stair. The two differ by 0.17 m²: A-104 "
        "deducts the full 2.05 m strip for the stair well, which is "
        "2.00 m wide.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# ARC-500  DOOR AND WINDOW SCHEDULE
# ===========================================================================
# Measured, not compiled.  Every opening in this building is already a pair
# of numbers in geometry.FACADE - the same pair the plan cuts its wall with
# and the elevation draws its frame in - so the schedule is a regrouping of
# the plans rather than a document somebody types up beside them and keeps
# in step by hand.
OS_COL_X = (18.0, 300.0)      # the two columns of the schedule
OS_TOP = 62.0
OS_PITCH = 34.0               # one type, with room for its thumbnail
OS_PER_COL = 12
OS_SCALE = 10.0               # mm of sheet per metre of opening, i.e. 1:100
# offsets within a column
OS_MARK, OS_THUMB, OS_SIZE = 0.0, 26.0, 62.0
OS_SILL, OS_FACE, OS_LEVEL, OS_QTY = 104.0, 128.0, 152.0, 252.0

OS_KIND_NAME = {"door": "Door", "window": "Window", "vent": "Louvre"}


def _opening_row(sh, x, y, r):
    """One type: mark, a thumbnail to scale, its figures and where it goes."""
    sh.text_mm(x + OS_MARK, y + 8, r["mark"], size=2.6, anchor="start",
               weight=700)
    sh.text_mm(x + OS_MARK, y + 15, OS_KIND_NAME[r["kind"]], size=2.0,
               anchor="start", color=GREY)

    # the opening itself, drawn to scale: a reader can compare two marks by
    # eye rather than by reading four numbers
    w, h = r["w"] * OS_SCALE, r["h"] * OS_SCALE
    base = y + 30.0
    sh.rect_mm(x + OS_THUMB, base - h, w, h, fill="#eef2f4", stroke=INK,
               sw=LW_SECONDARY)
    if r["kind"] == "vent":
        for i in range(1, max(2, int(r["h"] / 0.12))):
            yy = base - h + i * h / max(2, int(r["h"] / 0.12))
            sh.line_mm(x + OS_THUMB, yy, x + OS_THUMB + w, yy, w=LW_THIN,
                       color=GREY)
    else:
        sh.line_mm(x + OS_THUMB + w / 2, base - h, x + OS_THUMB + w / 2,
                   base, w=LW_THIN, color=GREY)
    sh.line_mm(x + OS_THUMB - 2, base, x + OS_THUMB + w + 2, base, w=0.3,
               color=INK)

    sh.text_mm(x + OS_SIZE, y + 12, f"{r['w'] * 1000:.0f} × {r['h'] * 1000:.0f}",
               size=2.3, anchor="start")
    sh.text_mm(x + OS_SILL, y + 12,
               "floor" if r["sill"] < 0.005 else f"+{r['sill'] * 1000:.0f}",
               size=2.2, anchor="start", color=GREY)
    sh.text_mm(x + OS_FACE, y + 12,
               "".join(f.upper() for f in r["faces"]), size=2.2,
               anchor="start", color=GREY)
    for i, n in enumerate(r["levels"]):
        sh.text_mm(x + OS_LEVEL + i * 14, y + 12, str(n) if n else "·",
                   size=2.2, anchor="middle",
                   color=INK if n else "#c8c8c8")
    sh.text_mm(x + OS_QTY, y + 12, str(r["total"]), size=2.6, anchor="end",
               weight=700)
    sh.line_mm(x, y + OS_PITCH - 3, x + OS_QTY, y + OS_PITCH - 3, w=0.12,
               color="#e2e2e2")


def _opening_heads(sh, x, y):
    for off, txt, anc in ((OS_MARK, "MARK", "start"),
                          (OS_THUMB, "1:100", "start"),
                          (OS_SIZE, "W × H mm", "start"),
                          (OS_SILL, "SILL", "start"),
                          (OS_FACE, "FACE", "start"),
                          (OS_QTY, "No.", "end")):
        sh.text_mm(x + off, y, txt, size=2.0, anchor=anc, color=GREY, ls=0.4)
    for i in range(len(EL_LEVELS)):
        sh.text_mm(x + OS_LEVEL + i * 14, y, f"L{i}", size=2.0,
                   anchor="middle", color=GREY, ls=0.4)
    sh.line_mm(x, y + 2.0, x + OS_QTY, y + 2.0, w=0.25, color=GREY)


def sheet_openings():
    """ARC-500: every door, window and louvre in the building.

    The first sheet in the set that is a table rather than a view, and the
    one that makes the opening geometry orderable: 95 openings resolve to
    24 types, and a reader who wants to know how many 1.40 m windows the
    house has can answer it here instead of counting them off five plans.
    """
    rows = el.opening_schedule()
    sh = Sheet("ARC-500", "Door & Window Schedule", "all levels",
               "1:100 @ A1")
    sh.rev = "P21"
    F.border(sh)

    sh.text_mm(OS_COL_X[0], 26, "DOOR & WINDOW SCHEDULE", size=6.0,
               anchor="start", weight=700, ls=0.6)
    sh.text_mm(OS_COL_X[0], 35,
               f"{sum(r['total'] for r in rows)} OPENINGS   ·   "
               f"{len(rows)} TYPES   ·   MEASURED FROM THE PLANS",
               size=2.6, anchor="start", color=GREY, ls=0.35)
    sh.line_mm(OS_COL_X[0], 40, OS_COL_X[1] + OS_QTY, 40, w=0.5, color=INK)

    for col in (0, 1):
        part = rows[col * OS_PER_COL:(col + 1) * OS_PER_COL]
        if not part:
            continue
        _opening_heads(sh, OS_COL_X[col], 50)
        for i, r in enumerate(part):
            _opening_row(sh, OS_COL_X[col], OS_TOP + i * OS_PITCH, r)
    if len(rows) > 2 * OS_PER_COL:
        raise ValueError(
            f"ARC-500: {len(rows)} opening types and the sheet holds "
            f"{2 * OS_PER_COL} - it needs a second sheet")

    area = {k: sum(r["w"] * r["h"] * r["total"] for r in rows
                   if r["kind"] == k) for k in ("door", "window", "vent")}
    F.heading(sh, sub="SCHEDULE   ·   ALL FIVE LEVELS   ·   MILLIMETRES")
    y = F.datum_panel(sh, 52, "THE OPENINGS", [
        ("Doors", f"{sum(r['total'] for r in rows if r['kind'] == 'door')}"),
        ("Windows",
         f"{sum(r['total'] for r in rows if r['kind'] == 'window')}"),
        ("Louvres", f"{sum(r['total'] for r in rows if r['kind'] == 'vent')}"),
        ("Types", f"{len(rows)}"),
        ("Door area", f"{area['door']:.1f} m²"),
        ("Glazed area", f"{area['window']:.1f} m²"),
        ("Louvre area", f"{area['vent']:.1f} m²"),
        ("Window head, every level", f"+{EL_HEAD:.2f} above floor"),
        ("Window sill, every level", f"+{EL_SILL:.2f} above floor")])
    F.notes(sh, y + 6, [
        "Measured from the plans, not compiled beside them. Every opening "
        "is a pair of coordinates the plan cuts its wall with and the "
        "elevation draws its frame in, so this schedule and those "
        "drawings cannot disagree about a width.",
        "Marks run largest first within each kind, so D01 is the widest "
        "door and W01 the widest window. L marks are the west wall's "
        "louvres: that face is blind below the penthouse and ventilates "
        "only.",
        f"Heads and sills are constant through the building — sill "
        f"+{EL_SILL:.2f}, head +{EL_HEAD:.2f} — so a type is distinguished "
        f"by its width alone except at the doors.",
        "Operation, frame material, glazing specification, ironmongery "
        "and finishes are not set by the geometry and are not invented "
        "here. They belong to ARC-600 and the specification.",
        "Dimensions are structural opening sizes. Frame and tolerance "
        "allowances to be taken off by the supplier against the "
        "construction drawings.",
    ])
    F.titleblock(sh)
    return sh


def sheet_register():
    """ARC-000: the master deliverables list, on a sheet.

    The set has to carry its own index, because a bound PDF handed to
    anybody is the only thing they have: a register that lives in a
    separate file is the register nobody reads.  Every row, and every
    status on it, comes from `deliverables.py` - so this sheet cannot
    claim a deliverable that is not there, and cannot fall behind the
    document of the same name.
    """
    sh = Sheet("ARC-000", "Master Deliverables List", "the whole set",
               "NTS")
    sh.rev = "P21"
    sh.status = F.STATUS_REGISTER
    F.border(sh)
    doc.register_table(sh)

    rows = dl.resolved()
    counts = dl.tally(rows)
    klass = {}
    for r, _s in rows:
        klass[r.klass] = klass.get(r.klass, 0) + 1

    F.heading(sh, sub="DOCUMENT CONTROL   ·   PACKAGES 0 AND A TO E   ·   "
                      "STATUS DERIVED")
    y = F.datum_panel(sh, 52, "THE SET AT A GLANCE", [
        ("Deliverables", f"{len(rows)}"),
        ("Issued", f"{counts[dl.ISSUED]}"),
        ("In progress", f"{counts[dl.PROGRESS]}"),
        ("Blocked", f"{counts[dl.BLOCKED]}"),
        ("Not started", f"{counts[dl.OPEN]}"),
        ("Levels", f"{len(dl.levels())}"),
        ("Structural slabs", f"{len(dl.slabs())}"),
        ("D — derived", f"{klass.get('D', 0)}"),
        ("L — layout for others", f"{klass.get('L', 0)}"),
        ("X — external", f"{klass.get('X', 0)}")])
    F.notes(sh, y + 6, [
        f"{doc.RULE} Class D is generated from geometry.py and is ours to "
        f"issue. Class L is layout and coordination only, sized and "
        f"certified by others. Class X cannot be produced here at all.",
        "So the structural package carries foundation layouts on the real "
        "grid and column coordinates, and no reinforcement; the services "
        "package carries coordination layouts, and no load calculations.",
        "Status is derived at build time from the issued set, never "
        "typed. A row naming a sheet nobody draws, or a document nobody "
        "writes, fails the checks rather than printing here.",
        f"Five levels, {len(dl.slabs())} structural slabs: the slab at "
        f"+{ROOF_LEVEL:.2f} is the penthouse floor and the roof over the "
        f"third floor at once.",
        "Deliverable codes are the client's. Where one resolves to sheets "
        "already issued, the existing number is the cross reference — the "
        "agreed set is not renumbered. The prefix is part of the number: "
        "A-402 is the street elevation and ARC-402 the second floor's "
        "ceiling plan, and they are different sheets.",
        f"The exterior is settled: scheme {SCHEME}, adopted at P18. "
        f"Blocked rows now wait on the measured survey and the plot's "
        f"soil figures, neither of which can be settled from the "
        f"drawings.",
        "For the owner's own record, costing and construction "
        "information. Not a tender issue, and not for construction.",
    ])
    F.titleblock(sh)
    return sh


SHEETS = (sheet_cover, sheet_general_notes,
          *_str_builders(), *_svc_builders(),
          *_cutaway_builders(),
          sheet_register, sheet_openings, sheet_roof, sheet_details,
          sheet_section_b, sheet_external_works,
          *_rcp_builders(),
          sheet_site, sheet_ground, sheet_first, sheet_second,
          sheet_third, sheet_penthouse, sheet_section,
          sheet_elev_a, sheet_elev_a_sides,
          sheet_elev_b, sheet_elev_b_sides,
          sheet_elev_c, sheet_elev_c_sides,
          sheet_street_context, sheet_axonometric,
          sheet_unit_typical, sheet_unit_third, sheet_service)


def slugify(title):
    """Sheet title -> file name: ASCII, lower case, hyphen separated."""
    out = []
    for ch in title.lower():
        out.append(ch if (ch.isalnum() and ch.isascii()) else "-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def sheet_basename(sh):
    """Number, title and revision - the file name every format shares.

    The revision is part of the name on purpose.  Two issues of the same
    sheet otherwise land on the same file name, so the superseded one is
    silently overwritten in some folders and left sitting beside the
    current one in others, with nothing but a timestamp to tell them
    apart.  With the letter in the name a stale issue is obvious on disk
    and in anybody's downloads folder.
    """
    return f"{sh.number}-{slugify(sh.title)}-{getattr(sh, 'rev', None) or F.REV}"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "drawings")
    os.makedirs(out, exist_ok=True)
    paths = []
    for builder in SHEETS:
        sh = builder()
        path = os.path.join(out, sheet_basename(sh) + ".svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(F.render(sh))
        print(f"{os.path.basename(path):42s} {len(sh.body):5d} entities")
        paths.append(path)
    return paths


if __name__ == "__main__":
    main()
