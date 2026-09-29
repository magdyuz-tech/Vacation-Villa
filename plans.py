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

import os
import sys

import drafting as D
from drafting import (Sheet, INK, GREY, LIGHT, LW_CUT, LW_SECONDARY,
                      LW_FIXTURE, LW_THIN, LW_HIDDEN)
import fixtures as fx
import frame as F
from geometry import *          # noqa: F401,F403  (pure constants)

SITE_ORIGIN = (150.0, 390.0)     # 1:75
PLAN_ORIGIN = (-60.0, 450.0)     # 1:50, upper floors
GF_ORIGIN = (40.0, 495.0)        # 1:50, ground floor with the whole plot
PARAPET_FILL = "#6f6f6f"

# Gross internal area per floor: the whole plate less the light court, less
# the open terraces on the third floor.
PLATE = (a_x1 - a_x0) * (a_y1 - a_y0) + (b_x1 - b_x0) * (b_y1 - b_y0)
COURT = (CT_X1 - CT_X0) * (CT_Y1 - CT_Y0)
TER_S = (a_x1 - a_x0 + b_x1 - b_x0) * (TER_S_Y1 - TER_S_Y0)
TER_N = (CORE_WALL_X - a_x0 + b_x1 - b_x0) * (TER_N_Y1 - TER_N_Y0)
GIA = {0: PLATE - COURT, 1: PLATE - COURT, 2: PLATE - COURT,
       3: PLATE - COURT - TER_S - TER_N}


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
    """The three blind boundaries.  The north line is now straight at 18.00."""
    for x0, y0, x1, y1 in [(0.0, 5.0, 11.5, 18.6),
                           (11.5, 18.0, 23.8, 18.6),
                           (23.0, 3.5, 23.8, 18.0)]:
        _hatch(sh, x0, y0, x1 - x0, y1 - y0)
    sh.tag(5.7, 11.8, "NEIGHBOURING PLOT", size=2.8, color=LIGHT)
    sh.tag(24.9, 11.0, "NEIGHBOURING PLOT", size=2.4, color=LIGHT, rot=-90)
    sh.tag(17.2, 18.9, "NEIGHBOURING PLOT", size=2.4, color=LIGHT)


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
    sh.wall(A_X0, A_Y1 - WT, 17.85, A_Y1)
    sh.wall(PARTY_X0, A_Y0, PARTY_X1, B_Y1, openings=o["party"])
    sh.wall(b_x0, B_Y0, B_X1, B_Y0 + WT, openings=o["b_south"])
    sh.wall(B_X1 - WT, B_Y0, B_X1, B_Y1, openings=o["b_east"])
    sh.wall(b_x0, B_Y1 - WT, B_X1, B_Y1)


def columns(sh):
    """RC frame: 300 mm columns on the grid, every one inside a wall."""
    for cx in GRID_X:
        for cy in GRID_Y:
            fx.column(sh, cx, cy, COL)


def core_walls(sh):
    """Stair, lift, riser and light court - identical on every floor."""
    # west wall of the core, from the lift up to the north wall
    sh.wall(CORE_WALL_X, LF_Y0 - PT, ST_X0, a_y1,
            openings=[(9.40, 10.28), (15.00, 16.80)])
    # south wall of the lift and riser cupboard
    sh.wall(CORE_WALL_X, LF_Y0 - PT, 17.85, LF_Y0)
    # between lift / riser and the protected lobby
    sh.wall(CORE_WALL_X, LF_Y1, 17.85, LOB_Y0,
            openings=[(15.70, 16.60), (17.32, 17.76)])
    # between the lobby and the stair
    sh.wall(CORE_WALL_X, LOB_Y1, 17.85, ST_Y0, openings=[(16.30, 17.20)])
    # between the stair and the light court
    sh.wall(CORE_WALL_X, ST_Y1, 17.85, CT_Y0)
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
    sh.window(15.00, 16.80, CORE_WALL_X, ST_X0, "v")
    sh.window(*CT_WIN_B, PARTY_X0, PARTY_X1, "v")
    direction = {0: "up", 3: "dn"}.get(floor, "both")
    fx.stair(sh, (ST_X0, ST_Y0, ST_X1, ST_Y1), direction=direction,
             floor_to_floor=FLOOR_TO_FLOOR)


def core_rooms(sh, floor):
    """Common parts, labelled the same way on every floor."""
    sh.room(LF_X0, LF_Y0, LF_X1 - LF_X0, LF_Y1 - LF_Y0, "Lift",
            area=(LF_X1 - LF_X0) * (LF_Y1 - LF_Y0), size=1.8,
            sched_name="Lift shaft", sub="shaft reserved", show_area=False,
            at=(16.25, 8.05))
    sh.room(LOB_X0, LOB_Y0, LOB_X1 - LOB_X0, LOB_Y1 - LOB_Y0, "Fire Lobby",
            area=(LOB_X1 - LOB_X0) * (LOB_Y1 - LOB_Y0), size=1.9,
            show_area=False, at=(16.62, 9.73))
    name = "Stair Hall" if floor == 0 else "Landing"
    sh.room(ST_X0, ST_Y0, ST_X1 - ST_X0, ST_Y1 - ST_Y0, name,
            area=(ST_X1 - ST_X0) * (ST_Y1 - ST_Y0), size=2.0,
            sched_name="Protected stair", show_area=False, at=(16.62, 13.95))
    light_court(sh, floor)


def light_court(sh, floor, size=2.1):
    fx.void_hatch(sh, CT_X0, CT_Y0, CT_X1 - CT_X0, CT_Y1 - CT_Y0)
    ground = floor == 0
    sh.room(CT_X0, CT_Y0, CT_X1 - CT_X0, CT_Y1 - CT_Y0,
            "Light Court" if ground else "Void over Court",
            area=COURT if ground else None,
            sub="open to sky" if ground else "open to sky below",
            size=size, schedule=False, show_area=ground)


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


def balcony(sh, span, level_txt, label=True):
    """Cantilevered balcony slab, 1.20 m beyond the south wall."""
    x0, x1 = span
    y0, y1 = A_Y0 - BALC_D, A_Y0
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill="#fbfbfb", stroke="none", sw=0)
    parapet(sh, x0, y0, x1, y0 + PARAPET)
    parapet(sh, x0, y0, x0 + PARAPET, y1)
    parapet(sh, x1 - PARAPET, y0, x1, y1)
    if label:
        # balconies are external, so they are labelled but kept out of the
        # area schedule, which totals internal area only
        sh.room(x0, y0, x1 - x0, BALC_D, "Balcony",
                area=(x1 - x0) * BALC_D, size=1.9, schedule=False,
                sub=level_txt, at=((x0 + x1) / 2, y0 + 0.66))


OPENINGS = {
    0: dict(a_south=[WIN_A_1, WIN_A_2, DOOR_ENTRY],
            a_west=[WIN_W_LIVING],
            b_south=[WIN_B_1, WIN_B_2],
            party=[(5.00, 6.00), (7.30, 8.30), CT_WIN_B],
            b_east=[]),
    1: dict(a_south=UP_A_SOUTH,
            a_west=[WIN_W_LIVING],
            b_south=UP_B_SOUTH,
            party=[(9.30, 10.20), CT_WIN_B],
            b_east=[WIN_E_BATH, WIN_E_BED, WIN_E_STUDY]),
    3: dict(a_south=UP_A_SOUTH,
            a_west=[WIN_W_LIVING],
            b_south=UP_B_SOUTH,
            party=[(4.50, 5.60), (7.00, 8.40), (10.90, 11.80), CT_WIN_B],
            b_east=[WIN_E_BED2, WIN_E_BED1]),
}
OPENINGS[2] = OPENINGS[1]


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


# ===========================================================================
# A-000  SITE PLAN
# ===========================================================================
def sheet_site():
    D.set_scale(75, *SITE_ORIGIN)
    sh = Sheet("A-000", "Site Plan", "+0.00", "1:75 @ A1")
    F.border(sh)
    neighbours(sh)
    street(sh)
    garden(sh)

    shell(sh, 0)
    sh.rect(a_x0, a_y0, a_x1 - a_x0, a_y1 - a_y0, fill="#f1f1f1",
            stroke="none", sw=0)
    sh.rect(b_x0, b_y0, b_x1 - b_x0, b_y1 - b_y0, fill="#f1f1f1",
            stroke="none", sw=0)
    columns(sh)
    light_court(sh, 0, size=1.9)
    sh.room(a_x0, 7.0, 3.9, 4.0, "Block A — front", area=None,
            sub="6.50 × 14.50 m", size=2.9,
            schedule=False, show_area=False, at=(13.60, 8.60))
    sh.room(b_x0, 7.0, 4.55, 4.0, "Block B — rear", area=None,
            sub="5.00 × 14.50 m", size=2.9,
            schedule=False, show_area=False, at=(20.42, 8.60))
    sh.level_tag(12.9, 4.30, "FFL +0.00")
    sh.level_tag(2.2, 2.00, "GARDEN −0.50")

    boundary(sh)
    sh.tag(6.5, 2.45, "ENTRANCE GARDEN CORRIDOR", size=2.3, color=INK)

    sh.dim_h(0, 23.0, -4.8, "23.00", ext_from=0.0)
    sh.dim_h(0, 11.5, -6.6, "11.50")
    sh.dim_h(11.5, 18.0, -6.6, "6.50")
    sh.dim_h(18.0, 23.0, -6.6, "5.00")
    sh.dim_v(0, 5.0, -1.8, "5.00", ext_from=0.0)
    sh.dim_v(0, 18.0, -3.6, "18.00")
    sh.dim_v(3.5, 18.0, 24.5, "14.50", ext_from=23.0)
    sh.dim_v(0, 3.5, 24.5, "3.50")

    F.heading(sh)
    y = F.legend(sh, 52)
    sh.schedule = [("Garden corridor, west  11.50 × 5.00", 57.50),
                   ("Garden corridor, front  11.50 × 3.50", 40.25),
                   ("Block A footprint  6.50 × 14.50", 94.25),
                   ("Block B footprint  5.00 × 14.50", 72.50)]
    y = F.schedule(sh, y + 8, extra=[
        ("Built footprint", "166.8 m²"),
        ("Site coverage", "63.0 %"),
        ("Gross internal area, four storeys",
         f"{sum(GIA.values()):.1f} m²")])
    F.notes(sh, y + 6, [
        "The client's survey sketch recorded a 0.50 m step in the north "
        "boundary and a 5.50 m offset between the two blocks' north walls; "
        "the two cannot both be true. Resolved in favour of a straight "
        "boundary at 18.00, with both blocks running north to meet it. To "
        "be confirmed by measured survey before any work starts on site.",
        "The south wall of both blocks stands 1.50 m further into the "
        "garden than the previous issue, giving each block a 14.50 m depth. "
        "The garden corridor is 5.00 m deep west of the building and "
        "3.50 m deep in front of it.",
        "Upper floor balconies cantilever a further 1.20 m south of that "
        "wall. Nothing projects over a boundary, but the overhang is "
        "subject to the local projection rule; confirm before construction.",
        "Blocks A and B sit hard against the north, east and west "
        "boundaries, so a 2.45 × 2.98 m light court is cut through all "
        "four storeys to daylight the centre of the plan.",
        "The ground floor sits 0.50 m above the garden, reached by three "
        "risers at 167 mm at the entrance and at the patio doors.",
        "Structure is an RC frame on the grid shown, columns set out on "
        "wall centrelines so none stands in a room; flat slab where spans "
        "and layout make it the simpler solution.",
    ])
    F.compass_and_scale(sh, x=502.0, y=452.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-100  GROUND FLOOR
# ===========================================================================
def sheet_ground():
    D.set_scale(50, *GF_ORIGIN)
    sh = Sheet("A-100", "Ground Floor Plan", "+0.00", "1:50 @ A1")
    F.border(sh)
    neighbours(sh)
    garden(sh)
    boundary(sh)
    sh.level_tag(6.2, 1.95, "GARDEN −0.50")
    sh.tag(0.55, 4.45, "ENTRANCE GARDEN CORRIDOR", size=2.1, color=GREY,
           anchor="start")

    shell(sh, 0)
    core_walls(sh)
    columns(sh)

    # block A: entrance lobby, living, service band, kitchen.  The hall sits
    # on the fire-lobby door so the route runs lobby - hall - living or
    # kitchen without passing through a room.
    sh.wall(CORE_WALL_X, a_y0, ST_X0, LF_Y0 - PT, openings=[(4.55, 6.05)])
    sh.wall(a_x0, 8.90, CORE_WALL_X, 9.02, openings=[(13.50, 14.80)])
    sh.wall(13.28, 9.02, 13.40, 10.60, openings=[(9.45, 10.25)])
    sh.wall(a_x0, 10.60, CORE_WALL_X, 10.72, openings=[(13.40, 14.60)])
    sh.wall(a_x0, 12.28, CORE_WALL_X, 12.40, openings=[(13.30, 14.60)])

    # block B: lounge, laundry, guest bath, guest bedroom
    sh.wall(b_x0, 9.00, b_x1, 9.12, openings=[(18.60, 19.60)])
    sh.wall(b_x0, 11.40, b_x1, 11.52, openings=[(21.50, 22.40)])
    sh.wall(20.30, 11.52, 20.42, 13.30)
    sh.wall(b_x0, 13.30, b_x1, 13.42, openings=[(18.60, 19.50)])

    for a, b in (WIN_A_1, WIN_A_2):
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    sh.door(*DOOR_ENTRY, A_Y0, A_Y0 + WT, "h", hinge="lo", swing="up")
    arch_note(sh, *DOOR_ENTRY, A_Y0 + WT, side=1)
    sh.window(*WIN_W_LIVING, A_X0, A_X0 + WT, "v")
    for a, b in (WIN_B_1, WIN_B_2):
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    sh.door(5.00, 6.00, PARTY_X0, PARTY_X1, "v", leaf=False)
    arch_note(sh, 5.00, 6.00, PARTY_X0, axis="v", side=-1)
    sh.door(7.30, 8.30, PARTY_X0, PARTY_X1, "v", leaf=False)
    arch_note(sh, 7.30, 8.30, PARTY_X0, axis="v", side=-1)
    core_fittings(sh, 0)
    sh.door(4.55, 6.05, CORE_WALL_X, ST_X0, "v", leaf=False)
    arch_note(sh, 4.55, 6.05, CORE_WALL_X, axis="v", side=-1)
    sh.door(13.50, 14.80, 8.90, 9.02, "h", leaf=False)
    sh.door(9.45, 10.25, 13.28, 13.40, "v", hinge="lo", swing="right")
    sh.door(13.40, 14.60, 10.60, 10.72, "h", hinge="lo", swing="up")
    sh.door(13.30, 14.60, 12.28, 12.40, "h", leaf=False)
    sh.door(18.60, 19.60, 9.00, 9.12, "h", hinge="lo", swing="up")
    sh.door(21.50, 22.40, 11.40, 11.52, "h", hinge="hi", swing="down")
    sh.door(18.60, 19.50, 13.30, 13.42, "h", hinge="lo", swing="up")

    # entrance lobby
    fx.counter(sh, 16.95, 5.60, 0.65, 1.70)
    sh.tag(16.05, 6.45, "RECEPTION", size=1.7, color=GREY, rot=-90)
    # living and reception
    fx.sofa(sh, a_x0, 5.20, 0.85, 2.10, facing="e")
    fx.sofa(sh, 13.10, 4.00, 2.10, 0.85, facing="s")
    sh.rect(12.85, 5.40, 1.20, 0.65, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.tv(sh, 15.10, 5.10, 1.40, axis="v")
    fx.table(sh, 12.55, 7.15, 1.60, 0.95, seats_n=3, seats_s=3)
    # guest wc
    fx.wc(sh, 12.25, 9.18, facing="n")
    fx.basin(sh, 12.90, 10.55, facing="s")
    # central service kitchen
    fx.counter(sh, a_x0, 12.50, 0.70, 5.00)
    fx.counter(sh, 12.60, 16.90, 2.60, 0.70)
    fx.sink(sh, 12.05, 12.70, w=0.60, d=0.90)
    fx.hob(sh, 14.20, 16.95, w=0.90, d=0.60)
    fx.fridge(sh, a_x0, 14.20, 0.70, 1.40)
    fx.counter(sh, 14.55, 12.55, 0.70, 3.20)
    for sy in (13.10, 13.90, 14.70):
        sh.circle(14.90, sy, 0.22, stroke=GREY, sw=LW_FIXTURE)
    fx.counter(sh, 12.70, 10.90, 2.00, 0.70)
    # lounge
    fx.tv(sh, 18.17, 5.00, 1.40, axis="v")
    fx.sofa(sh, 21.30, 4.90, 0.85, 2.00, facing="w")
    sh.rect(19.95, 5.45, 1.10, 0.65, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.table(sh, 19.10, 7.40, 1.50, 0.90, seats_n=3, seats_s=3)
    # laundry
    for wx in (18.35, 19.15, 19.95):
        sh.rect(wx, 9.35, 0.70, 0.70, sw=LW_FIXTURE, stroke=GREY)
        sh.circle(wx + 0.35, 9.70, 0.21, stroke=GREY, sw=LW_FIXTURE)
    fx.counter(sh, 21.00, 9.35, 1.70, 0.70)
    fx.counter(sh, 18.15, 10.60, 4.55, 0.65)
    # guest bath + linen
    fx.shower(sh, 18.25, 12.15, 0.95, 0.95)
    fx.wc(sh, 20.18, 11.85, facing="w")
    fx.basin(sh, 19.20, 13.30, facing="s")
    fx.wardrobe(sh, 20.55, 11.60, 2.00, 0.55)
    # guest bedroom / office
    fx.bed(sh, 19.40, 14.70, 1.60, 2.00, head="n")
    for bx in (18.90, 21.05):
        sh.rect(bx, 16.20, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 22.15, 13.90, 0.55, 2.60, axis="v")

    sh.room(ST_X0, a_y0, 2.45, 3.38, "Entrance Lobby", area=8.3, size=2.2,
            sched_name="Entrance lobby & reception", at=(16.62, 4.70))
    sh.room(a_x0, a_y0, 3.48, 5.10, "Living & Reception", area=17.8,
            size=2.5, at=(13.54, 6.30))
    sh.room(a_x0, 9.02, 1.48, 1.58, "Guest WC", area=2.3, size=1.8,
            at=(12.54, 9.92))
    sh.room(13.40, 9.02, 1.88, 1.58, "Hall", area=3.0, size=1.8,
            sched_name="Hall", at=(14.34, 9.86))
    sh.room(a_x0, 10.72, 3.48, 1.56, "Wash-up & Store", area=5.4, size=1.8,
            at=(13.54, 11.50))
    sh.room(a_x0, 12.40, 3.48, 5.30, "Service Kitchen", area=18.4, size=2.4,
            sub="central, serves all floors", at=(13.54, 15.40))
    core_rooms(sh, 0)
    sh.room(b_x0, b_y0, 4.55, 5.20, "Lounge & Breakfast", area=23.7,
            size=2.5, at=(20.42, 6.35))
    sh.room(b_x0, 9.12, 4.55, 2.28, "Laundry", area=10.4, size=2.1,
            sched_name="Central laundry", at=(20.42, 10.15))
    sh.room(b_x0, 11.52, 2.15, 1.78, "Guest Bath", area=3.8, size=1.8,
            at=(19.22, 12.90))
    sh.room(20.42, 11.52, 2.28, 1.78, "Linen", area=4.1, size=1.8,
            sched_name="Linen & store", at=(21.56, 12.90))
    sh.room(b_x0, 13.42, 4.55, 4.28, "Guest Bedroom", area=19.5, size=2.4,
            sub="or office", at=(20.42, 16.30))

    sh.dim_h(0, PLOT_W, -2.0, "23.00", ext_from=0.0)
    sh.dim_h(A_X0, A_X1, -0.9, "6.50")
    sh.dim_h(A_X1, B_X1, -0.9, "5.00")
    sh.dim_v(0, GARDEN_D, -1.0, "5.00", ext_from=0.0)
    sh.dim_v(A_Y0, A_Y1, -1.0, "14.50")
    sh.dim_v(B_Y0, B_Y1, 24.2, "14.50", ext_from=B_X1)
    sh.dim_v(A_Y0, LF_Y0, 25.6, "3.80")
    sh.dim_v(LF_Y0, ST_Y0, 25.6, "3.30")
    sh.dim_v(ST_Y0, ST_Y1, 25.6, "4.00")
    sh.dim_v(ST_Y1, B_Y1, 25.6, "3.40")
    sh.level_tag(12.05, 8.40, "FFL +0.00")
    sh.level_tag(20.75, 4.60, "FFL +0.00")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[0]:.1f} m²"),
        ("Light court, open to sky", f"{COURT:.1f} m²"),
        ("Slab to slab", "3.30 m · 3.00 m clear")])
    F.notes(sh, y + 6, [
        "The whole of this floor is one non-residential compartment under "
        "the apartments: 2 hour separation to the floor over, sprinklered "
        "throughout, with a suppression hood over the cooking line.",
        "The service kitchen and laundry serve all four storeys. Kitchen "
        "extract rises in a dedicated fire-rated shaft within the riser "
        "cupboard off the fire lobby, run at high level from the kitchen "
        "and discharged above roof level.",
        "Living, reception, entrance lobby and the lounge read as one "
        "connected sequence through 1.00 m arched openings in the party "
        "wall; arch heads are shown dashed.",
        "The east boundary wall is solid at this level: the adjoining "
        "owner may build up to 3.00 m against it. The kitchen and the "
        "guest bedroom are daylit from the light court, and the west wall "
        "is opened where it faces our own garden south of y = 5.00.",
        "Bins stand outside in the garden, clear of the patio; the compact "
        "kitchen has no room for an internal bin lobby. Guest bath, "
        "laundry and WC are internal, mechanically extracted at six air "
        "changes per hour.",
        "Gross internal area excludes the light court.",
    ])
    F.compass_and_scale(sh, x=500.0, y=548.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-101 / A-102  APARTMENT FLOORS
# ===========================================================================
def _apartment_floor(number, title, level, floor):
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet(number, title, level, "1:50 @ A1")
    F.border(sh)
    shell(sh, floor)
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=OPENINGS[floor]["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=OPENINGS[floor]["b_south"])
    core_walls(sh)
    columns(sh)
    balcony(sh, BALC_A, f"{level[:-1]}7")
    balcony(sh, BALC_B, f"{level[:-1]}7")

    # apartment A.  The bathroom takes the full width of the block's east
    # end so it sits hard against the party wall, directly below the riser
    # cupboard; the hall sits on the fire-lobby door.
    sh.wall(CORE_WALL_X, 5.18, 17.85, 5.30, openings=[(15.90, 16.80)])
    sh.wall(CORE_WALL_X, 5.30, ST_X0, LF_Y0 - PT)
    sh.wall(a_x0, 8.90, CORE_WALL_X, 9.02, openings=[(13.50, 14.80)])
    sh.wall(13.28, 9.02, 13.40, 10.60, openings=[(9.45, 10.25)])
    sh.wall(a_x0, 10.60, CORE_WALL_X, 10.72, openings=[(13.40, 14.60)])
    sh.wall(a_x0, 12.90, CORE_WALL_X, 13.02, openings=[(11.95, 13.15)])

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
    core_fittings(sh, floor)
    sh.door(9.30, 10.20, PARTY_X0, PARTY_X1, "v", hinge="lo", swing="right")
    sh.door(15.90, 16.80, 5.18, 5.30, "h", hinge="lo", swing="up")
    sh.door(13.50, 14.80, 8.90, 9.02, "h", leaf=False)
    sh.door(9.45, 10.25, 13.28, 13.40, "v", hinge="lo", swing="right")
    sh.door(13.40, 14.60, 10.60, 10.72, "h", hinge="lo", swing="up")
    sh.door(11.95, 13.15, 12.90, 13.02, "h", hinge="lo", swing="up")
    sh.door(18.60, 19.50, 9.00, 9.12, "h", hinge="lo", swing="up")
    sh.door(9.35, 10.15, 20.28, 20.40, "v", hinge="lo", swing="right")
    sh.door(18.55, 19.45, 11.10, 11.22, "h", hinge="lo", swing="up")
    sh.door(21.40, 22.30, 15.40, 15.52, "h", hinge="hi", swing="up")

    # apartment A fittings
    fx.sofa(sh, a_x0, 5.00, 0.85, 2.00, facing="e")
    fx.sofa(sh, 13.00, 4.05, 2.00, 0.85, facing="s")
    sh.rect(12.80, 5.30, 1.10, 0.62, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.kitchenette(sh, 12.75, 8.20, 2.50, 0.65, axis="h")
    fx.table(sh, 15.90, 4.05, 1.30, 0.90, seats_e=2, seats_w=2)
    fx.bathtub(sh, 15.45, 6.30, 1.70, 0.75)
    fx.wc(sh, 17.85, 5.82, facing="w")
    fx.basin(sh, 15.95, 5.98, w=0.60, d=0.45, facing="s")
    fx.wardrobe(sh, a_x0, 9.15, 1.40, 0.55)
    fx.wardrobe(sh, a_x0, 10.85, 3.40, 0.58)
    fx.wardrobe(sh, a_x0, 12.25, 3.40, 0.58)
    fx.bed(sh, 12.55, 14.10, 1.60, 2.05, head="n")
    for bx in (12.05, 14.20):
        sh.rect(bx, 15.65, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)

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

    sh.room(a_x0, a_y0, 3.48, 5.10, "Living · Dining · Kitchen", area=21.3,
            size=2.3, sub="apartment A", sched_name="Apt A living / kitchen",
            at=(13.54, 6.60))
    sh.room(CORE_WALL_X, 5.30, 2.57, 1.88, "Bath", area=4.8, size=1.9,
            sched_name="Apt A bathroom", at=(16.56, 6.95))
    sh.room(13.40, 9.02, 1.88, 1.58, "Hall", area=3.0, size=1.8,
            sched_name="Apt A entry hall", at=(14.34, 9.86))
    sh.room(a_x0, 9.02, 1.48, 1.58, "Store", area=2.3, size=1.8,
            sched_name="Apt A store", at=(12.54, 9.86))
    sh.room(a_x0, 10.72, 3.48, 2.18, "Dressing", area=7.6, size=2.0,
            sched_name="Apt A dressing", at=(13.54, 11.75))
    sh.room(a_x0, 13.02, 3.48, 4.68, "Bedroom", area=16.3, size=2.4,
            sub="light court", sched_name="Apt A bedroom", at=(13.54, 16.55))
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

    sh.dim_h(A_X0, B_X1, 1.6, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 0.4, "6.50")
    sh.dim_h(A_X1, B_X1, 0.4, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.4, "14.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, "14.50", ext_from=B_X1)
    sh.dim_v(B_Y0, 9.00, 26.0, "5.50")
    sh.dim_v(9.00, 11.10, 26.0, "2.10")
    sh.dim_v(11.10, B_Y1, 26.0, "6.60")
    sh.tag(23.45, 13.20,
           "OPENABLE WINDOWS TO EAST BOUNDARY, ABOVE +3.00",
           size=2.0, color=INK, rot=-90)
    sh.level_tag(12.10, 4.55, f"FFL {level}")
    sh.level_tag(18.60, 12.60, f"FFL {level}")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[floor]:.1f} m²"),
        ("Apartment A / apartment B", "57.1 / 63.3 m²"),
        ("Balcony, each (external)",
         f"{(BALC_A[1] - BALC_A[0]) * BALC_D:.1f} m²")])
    F.notes(sh, y + 6, [
        "Two one-bedroom apartments, both entered off the protected fire "
        "lobby: apartment A occupies block A around the core, apartment B "
        "the whole of block B.",
        "Both units are planned open: living, dining and kitchenette read "
        "as one room with no corridor, and every other room is reached "
        "directly from the entry hall. Kitchenettes are a single joinery "
        "run — sink, two-ring cooktop, undercounter fridge, overhead "
        "storage.",
        "Wet rooms stack floor to floor onto the party wall spine. The "
        "riser cupboard carrying the soil, water and extract risers is "
        "entered from the fire lobby, not from either apartment; "
        "apartment A's kitchenette drains east to it in the floor zone.",
        "East boundary openings: the adjoining plot is limited to 3.00 m "
        "in height, so the east wall is opened above that level and "
        "apartment B's bathroom is naturally ventilated. Openings in a "
        "boundary wall are subject to local fire separation and rights of "
        "light rules; confirm before construction.",
        "Balconies cantilever 1.20 m beyond the south wall with a 1.10 m "
        "parapet, falling 1:80 to an outlet. Escape is by the single "
        "protected stair with FD30S self-closing doors onto the lobby and "
        "sprinklers throughout — a proposal, to be verified against the "
        "governing code.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def sheet_first():
    return _apartment_floor("A-101", "First Floor Plan", "+3.30", 1)


def sheet_second():
    return _apartment_floor("A-102", "Second Floor Plan", "+6.60", 2)


# ===========================================================================
# A-103  THIRD FLOOR / ROOF
# ===========================================================================
def sheet_third():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-103", "Third Floor & Roof Plan", "+9.90", "1:50 @ A1")
    F.border(sh)
    o = OPENINGS[3]

    # south terrace: parapet on three sides
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=o["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=o["b_south"])
    parapet(sh, A_X0, A_Y0, A_X0 + PARAPET, TER_S_Y1, openings=o["a_west"])
    parapet(sh, B_X1 - PARAPET, B_Y0, B_X1, TER_S_Y1)
    # north terrace: parapet on the boundary walls
    parapet(sh, A_X0, TER_N_Y0, A_X0 + PARAPET, A_Y1)
    parapet(sh, A_X0, A_Y1 - PARAPET, CORE_WALL_X, A_Y1)
    parapet(sh, b_x0, B_Y1 - PARAPET, B_X1, B_Y1)
    parapet(sh, B_X1 - PARAPET, TER_N_Y0, B_X1, B_Y1)
    # enclosed walls of the apartment
    sh.wall(A_X0, TER_S_Y1, A_X0 + WT, TER_N_Y0)
    sh.wall(B_X1 - WT, TER_S_Y1, B_X1, TER_N_Y0, openings=o["b_east"])
    sh.wall(CORE_WALL_X, A_Y1 - WT, 17.85, A_Y1)
    sh.wall(PARTY_X0, A_Y0, PARTY_X1, B_Y1, openings=o["party"])
    core_walls(sh)
    columns(sh)

    # terrace enclosing walls
    sh.wall(a_x0, TER_S_Y1, ST_X0, TER_S_Y1 + PT,
            openings=[(12.30, 14.30), (15.70, 17.40)])
    sh.wall(b_x0, TER_S_Y1, b_x1, TER_S_Y1 + PT, openings=[(19.20, 21.60)])
    sh.wall(a_x0, TER_N_Y0 - PT, CORE_WALL_X, TER_N_Y0,
            openings=[(12.60, 13.80)])
    sh.wall(b_x0, TER_N_Y0 - PT, b_x1, TER_N_Y0, openings=[(19.30, 20.50)])

    # apartment partitions.  Block A carries the entry, the wet rooms and
    # bedroom 2; block B carries the living sequence and bedroom 1, where
    # the east wall can be opened above +3.00.
    sh.wall(a_x0, 8.90, CORE_WALL_X, 9.02, openings=[(13.50, 14.80)])
    sh.wall(13.28, 9.02, 13.40, 10.60, openings=[(9.45, 10.25)])
    sh.wall(a_x0, 10.60, CORE_WALL_X, 10.72, openings=[(13.40, 14.60)])
    sh.wall(13.28, 10.72, 13.40, 12.90, openings=[(11.00, 11.80)])
    sh.wall(a_x0, 12.90, CORE_WALL_X, 13.02, openings=[(11.95, 13.15)])
    sh.wall(b_x0, 11.00, b_x1, 11.12, openings=[(18.55, 19.55)])
    sh.wall(b_x0, 8.60, b_x1, 8.72, openings=[(21.30, 22.30)])

    for a, b in o["a_south"]:
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in o["b_south"]:
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    arch_note(sh, *WIN_W_LIVING, A_X0 + PARAPET, axis="v", side=1)
    arch_note(sh, 4.50, 5.60, PARTY_X0, axis="v", side=-1)
    for a, b in o["b_east"]:
        sh.window(a, b, B_X1 - WT, B_X1, "v")
    core_fittings(sh, 3)
    sh.door(7.00, 8.40, PARTY_X0, PARTY_X1, "v", leaf=False)
    sh.door(10.90, 11.80, PARTY_X0, PARTY_X1, "v", hinge="lo", swing="right")
    sh.door(12.30, 14.30, TER_S_Y1, TER_S_Y1 + PT, "h", leaf=False)
    sh.door(15.70, 17.40, TER_S_Y1, TER_S_Y1 + PT, "h", leaf=False)
    sh.door(19.20, 21.60, TER_S_Y1, TER_S_Y1 + PT, "h", leaf=False)
    sh.door(12.60, 13.80, TER_N_Y0 - PT, TER_N_Y0, "h", leaf=False)
    sh.door(19.30, 20.50, TER_N_Y0 - PT, TER_N_Y0, "h", leaf=False)
    sh.door(13.50, 14.80, 8.90, 9.02, "h", leaf=False)
    sh.door(9.45, 10.25, 13.28, 13.40, "v", hinge="lo", swing="right")
    sh.door(13.40, 14.60, 10.60, 10.72, "h", hinge="lo", swing="up")
    sh.door(11.00, 11.80, 13.28, 13.40, "v", hinge="lo", swing="right")
    sh.door(11.95, 13.15, 12.90, 13.02, "h", hinge="lo", swing="up")
    sh.door(18.55, 19.55, 11.00, 11.12, "h", hinge="lo", swing="up")
    sh.door(21.30, 22.30, 8.60, 8.72, "h", hinge="hi", swing="down")

    # south terrace
    fx.pergola(sh, a_x0, 3.95, 6.05, 2.15, pitch=0.55)
    fx.pergola(sh, b_x0, 3.95, 4.55, 2.15, pitch=0.55)
    fx.table(sh, 19.35, 4.55, 1.60, 0.95, seats_n=3, seats_s=3)
    fx.sofa(sh, 12.20, 4.10, 2.30, 0.85, facing="n")
    fx.sofa(sh, 15.30, 4.20, 0.85, 1.80, facing="w")
    for px, py, pw, pd in ((11.90, 5.55, 0.50, 0.55), (17.20, 3.95, 0.60, 2.15)):
        fx.planter(sh, px, py, pw, pd)
    # kitchen and dining
    fx.kitchenette(sh, b_x0, 6.55, 0.65, 2.00, axis="v")
    fx.table(sh, 20.70, 6.70, 1.40, 0.90, seats_n=2, seats_s=2)
    # living
    fx.sofa(sh, 18.75, 8.95, 2.20, 0.85, facing="n")
    fx.sofa(sh, b_x0, 9.95, 0.85, 1.80, facing="e")
    sh.rect(19.35, 10.05, 1.20, 0.62, rx=D.mm(0.1), sw=LW_FIXTURE,
            stroke=GREY)
    fx.tv(sh, 22.54, 9.45, 1.30, axis="v")
    # bedroom 1
    fx.bed(sh, 19.55, 12.10, 1.80, 2.10, head="n")
    for bx in (19.00, 21.40):
        sh.rect(bx, 13.65, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, b_x0, 11.30, 0.58, 2.40, axis="v")
    # block A rooms
    fx.bed(sh, 12.55, 6.60, 1.60, 2.05, head="n")
    fx.wardrobe(sh, a_x0, 6.55, 0.55, 1.80, axis="v")
    fx.wardrobe(sh, a_x0, 9.15, 1.40, 0.55)
    fx.bathtub(sh, 13.50, 10.90, 1.70, 0.75)
    fx.wc(sh, CORE_WALL_X, 12.05, facing="w")
    fx.basin(sh, 13.95, 12.86, w=0.60, d=0.45, facing="s")
    fx.wardrobe(sh, a_x0, 10.90, 0.55, 1.80, axis="v")
    fx.wardrobe(sh, a_x0, 13.20, 3.40, 0.58)
    fx.counter(sh, 14.05, 14.25, 1.20, 0.65)
    # north terrace
    for px, py, pw, pd in ((11.90, 15.20, 0.55, 2.30),
                           (13.20, 17.00, 1.80, 0.55),
                           (22.10, 15.30, 0.55, 2.20)):
        fx.planter(sh, px, py, pw, pd)
    fx.pergola(sh, 18.60, 15.25, 3.30, 2.20, pitch=0.55)
    sh.rect(18.30, 15.20, 0.90, 2.40, sw=LW_HIDDEN, stroke=GREY,
            dash="2.0 1.2")
    sh.tag(18.75, 16.40, "PLANT", size=1.7, color=GREY, rot=-90)

    sh.room(a_x0, TER_S_Y0, 6.05, 2.45, "South Terrace", area=26.0, size=2.5,
            sub="pergola over · over the garden",
            sched_name="South terrace", at=(14.60, 5.60))
    sh.room(a_x0, 6.37, 3.48, 2.53, "Bedroom 2", area=10.9, size=2.2,
            at=(13.54, 7.95))
    sh.room(13.40, 9.02, 1.88, 1.58, "Hall", area=3.0, size=1.8,
            sched_name="Entry hall", at=(14.34, 9.86))
    sh.room(a_x0, 9.02, 1.48, 1.58, "Store", area=2.3, size=1.8,
            at=(12.54, 9.86))
    sh.room(13.40, 10.72, 1.88, 2.18, "Bath", area=4.1, size=1.8,
            sched_name="Family bathroom", at=(14.34, 11.95))
    sh.room(a_x0, 10.72, 1.48, 2.18, "Linen", area=3.2, size=1.8,
            at=(12.54, 11.90))
    sh.room(a_x0, 13.02, 3.48, 1.98, "Dressing / Laundry", area=6.9,
            size=1.8, sched_name="Dressing & laundry", at=(13.54, 13.95))
    core_rooms(sh, 3)
    sh.room(b_x0, 6.37, 4.55, 2.23, "Kitchen & Dining", area=10.2, size=2.1,
            at=(20.42, 7.50))
    sh.room(b_x0, 8.72, 4.55, 2.28, "Living", area=10.4, size=2.1,
            at=(21.20, 10.60))
    sh.room(b_x0, 11.12, 4.55, 3.88, "Bedroom 1", area=17.7, size=2.4,
            sub="master", at=(20.42, 14.20))
    sh.room(b_x0, TER_N_Y0, 4.55, 2.70, "North Terrace", area=21.7, size=2.2,
            sub="shaded · plant", sched_name="North terrace",
            at=(20.42, 16.40))
    sh.tag(13.54, 16.25, "NORTH TERRACE", size=2.0, color=INK)
    sh.tag(13.54, 15.55, "wraps the light court", size=1.8, color=GREY)

    sh.dim_h(A_X0, B_X1, 1.6, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 0.4, "6.50")
    sh.dim_h(A_X1, B_X1, 0.4, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.4, "14.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, "14.50", ext_from=B_X1)
    sh.dim_v(TER_S_Y0, TER_S_Y1, 26.0, "2.45")
    sh.dim_v(TER_S_Y1, TER_N_Y0, 26.0, "8.75")
    sh.dim_v(TER_N_Y0, b_y1, 26.0, "2.70")
    sh.tag(23.45, 12.00, "OPENABLE WINDOWS TO EAST BOUNDARY",
           size=2.0, color=INK, rot=-90)
    sh.level_tag(16.30, 4.35, "TERRACE +9.87")
    sh.level_tag(18.55, 13.00, "FFL +9.90")
    sh.level_tag(14.30, 17.35, "TERRACE +9.87")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[3]:.1f} m²"),
        ("Open-air terrace, north and south", f"{TER_S + TER_N:.1f} m²"),
        ("Roof over, top of slab", f"+{ROOF_LEVEL:.2f}")])
    F.notes(sh, y + 6, [
        "A single two-bedroom apartment with a terrace on each side: the "
        "south terrace over the garden under a pergola, the north terrace "
        "shaded against the boundary wall and carrying the plant.",
        "Living, kitchen and dining run through the party wall as one "
        "space and open onto the south terrace through 2.00 m and 2.40 m "
        "sliding screens.",
        "Bedroom 1 takes block B with an openable east window above +3.00; "
        "bedroom 2 sits in block A and opens onto the south terrace. "
        "Bathroom, linen and store are internal, with mechanical extract "
        "to the riser.",
        "Terrace finish is 30 mm below internal floor level, falling 1:80 "
        "to outlets at the parapet. Parapets are 250 mm thick and 1.10 m "
        "high above the terrace finish.",
        "Condensers, the sprinkler tank and the roof plant stand on the "
        "north terrace behind a screen, clear of the usable area. The "
        "roof over falls 1:60 to outlets at the parapet, waterproofing "
        "turned up 150 mm minimum.",
        "The light court is carried up through this floor and remains "
        "open to sky; the north terrace wraps it on both sides.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
SHEETS = (sheet_site, sheet_ground, sheet_first, sheet_second, sheet_third)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "drawings")
    os.makedirs(out, exist_ok=True)
    paths = []
    for builder in SHEETS:
        sh = builder()
        slug = sh.title.lower().replace(" & ", "-").replace(" ", "-")
        path = os.path.join(out, f"{sh.number}-{slug}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(F.render(sh))
        print(f"{os.path.basename(path):42s} {len(sh.body):5d} entities")
        paths.append(path)
    return paths


if __name__ == "__main__":
    main()
