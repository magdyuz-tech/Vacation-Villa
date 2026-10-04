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
        "Only the west boundary is built against, so the west wall is "
        "blind except where it faces the plot's own garden. The north and "
        "east boundaries are open on the client's confirmation and are "
        "windowed on every floor; the light court shown in P3 has gone.",
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


def sheet_ground():
    D.set_scale(50, *GF_ORIGIN)
    sh = Sheet("A-100", "Ground Floor Plan", "+0.00", "1:50 @ A1")
    F.border(sh)
    _plan_ground(sh)
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

    section_line(sh)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[0]:.1f} m²"),
        ("Slab to slab", "3.30 m · 3.00 m clear")])
    F.notes(sh, y + 6, [
        "The villa is entered twice from the south. The family door is at "
        "the west end of block A, nearest the garden corridor; the "
        "guests\u2019 door is at the east end of block B, straight into the "
        "majlis. The core stands between them, so the two routes never "
        "cross and a guest reaches no family room.",
        "Block B is the guest wing: a 32.8 m² majlis with low seating to "
        "three sides, a guest WC opening off it, and a service lobby "
        "linking it to the dirty kitchen for serving.",
        "Two kitchens, as Gulf practice wants. The show kitchen opens to "
        "the family side of block A under its north windows; the closed "
        "dirty kitchen takes the north of block B with its own service "
        "door. Each has its own extract, and the dirty kitchen door is "
        "not in sight of the majlis.",
        "The party wall is opened twice and nowhere else: an arched "
        "opening at the south so the family can greet guests, and a "
        "serving opening at the north between the two kitchens. Between "
        "them it backs onto the lift, the riser and the stair.",
        "Maid\u2019s accommodation goes at the top of the house with the "
        "laundry. It does not fit on this floor once the majlis and both "
        "kitchens are placed.",
    ])
    F.compass_and_scale(sh, x=500.0, y=548.0)
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



def _plan_first(sh, level):
    """Villa first floor: the family floor, with the second household's
    wing in block B.

    The wing has its own sitting room, bathroom, bedroom, dressing room and
    kitchenette, and the lift reaches it - which is the point of it, for
    grandparents.  Its door is the arched opening at the south of the party
    wall, and it locks.
    """
    shell(sh, 1)
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=OPENINGS[1]["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=OPENINGS[1]["b_south"])
    core_walls(sh)
    columns(sh)
    balcony(sh, BALC_A, f"{level[:-1]}7")
    balcony(sh, BALC_B, f"{level[:-1]}7", screen_w=False)

    # --- block A: living at the south, hall past the core, family room ---
    sh.wall(13.30, 7.30, 13.42, 9.40, openings=[(8.00, 8.90)])
    sh.wall(a_x0, 9.40, 13.42, 9.52)
    sh.wall(a_x0, 14.60, CORE_WALL_X, CORE_N, openings=[(12.40, 13.60)])

    # --- block B: the wing ------------------------------------------------
    sh.wall(b_x0, 8.60, b_x1, 8.72, openings=[(21.20, 22.10)])
    sh.wall(20.60, 8.72, 20.72, 11.00, openings=[(9.40, 10.30)])
    sh.wall(b_x0, 11.00, b_x1, 11.12, openings=[(21.20, 22.10)])
    sh.wall(b_x0, 15.30, b_x1, 15.42, openings=[(20.80, 21.70)])

    # --- openings ---------------------------------------------------------
    for a, b in OPENINGS[1]["a_south"]:
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in OPENINGS[1]["b_south"]:
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    sh.window(*WIN_W_LIVING, A_X0, A_X0 + WT, "v")
    for a, b in OPENINGS[1]["b_east"]:
        sh.window(a, b, B_X1 - WT, B_X1, "v")
    north_windows(sh, 1)
    sh.door(*V_PARTY_WING, PARTY_X0, PARTY_X1, "v", leaf=False)
    arch_note(sh, *V_PARTY_WING, PARTY_X0, axis="v", side=-1)

    core_fittings(sh, 1)
    sh.door(8.00, 8.90, 13.30, 13.42, "v", hinge="lo", swing="right")
    sh.door(12.40, 13.60, 14.60, CORE_N, "h", hinge="lo", swing="down")
    sh.door(21.20, 22.10, 8.60, 8.72, "h", hinge="lo", swing="up")
    sh.door(9.40, 10.30, 20.60, 20.72, "v", hinge="lo", swing="right")
    sh.door(21.20, 22.10, 11.00, 11.12, "h", hinge="lo", swing="up")
    sh.door(20.80, 21.70, 15.30, 15.42, "h", hinge="lo", swing="up")

    # --- block A fittings -------------------------------------------------
    fx.sofa(sh, 12.10, 5.55, 2.40, 0.85, facing="s")
    fx.sofa(sh, a_x0, 3.95, 0.80, 1.50, facing="e")
    sh.rect(12.60, 4.70, 1.25, 0.72, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.table(sh, 15.30, 4.40, 1.45, 1.00, seats_n=3, seats_s=3)
    fx.wc(sh, a_x0, 7.60, facing="e")
    fx.basin(sh, 12.55, 9.40, w=0.58, d=0.42, facing="s")
    fx.counter(sh, a_x0, 11.00, 0.45, 1.60)
    fx.wardrobe(sh, a_x0, 12.90, 0.45, 1.60, axis="v")
    fx.sofa(sh, 12.30, 15.05, 2.40, 0.85, facing="n")
    fx.tv(sh, 15.10, 15.70, 1.30, axis="v")
    sh.rect(12.85, 16.20, 1.30, 0.70, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)

    # --- block B fittings: the wing ---------------------------------------
    fx.kitchenette(sh, b_x0, 6.55, 0.65, 1.95, axis="v")
    fx.sofa(sh, 19.45, 4.20, 2.20, 0.85, facing="s")
    sh.rect(19.95, 5.45, 1.15, 0.68, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.table(sh, 20.95, 6.70, 1.30, 0.85, seats_n=2, seats_s=2)
    fx.shower(sh, 18.25, 8.85, 1.20, 1.20)
    fx.wc(sh, 20.60, 9.20, facing="w")
    fx.basin(sh, 18.40, 11.00, w=0.65, d=0.45, facing="s")
    fx.wardrobe(sh, 22.10, 8.90, 0.58, 1.40, axis="v")
    fx.bed(sh, 19.50, 12.25, 1.80, 2.10, head="n")
    for bx in (18.95, 21.35):
        sh.rect(bx, 13.80, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, b_x0, 15.55, 0.58, 2.00, axis="v")
    fx.wardrobe(sh, 22.12, 15.55, 0.58, 2.00, axis="v")

    # --- rooms ------------------------------------------------------------
    sh.room(a_x0, a_y0, a_x1 - a_x0, LF_Y0 - PT - a_y0,
            "Family Living \u00b7 Dining", area=20.4, size=2.3,
            sched_name="Family living / dining", sub="to the balcony",
            at=(13.55, 7.00))
    sh.room(a_x0, 7.30, 13.30 - a_x0, 9.40 - 7.30, "Powder", area=3.2,
            size=1.7, show_area=False, at=(12.55, 8.30))
    sh.room(13.42, 7.30, CORE_WALL_X - 13.42, 14.60 - 7.30, "Upper Hall",
            area=22.2, size=2.0, sched_name="Upper hall", show_area=False,
            at=(13.80, 11.90))
    sh.room(a_x0, CORE_N, a_x1 - a_x0, a_y1 - CORE_N, "Family Room",
            area=18.0, size=2.3, sub="north windows", at=(13.60, 17.30))
    core_rooms(sh, 1, lobby_name="Landing", stair_name="Stair")
    sh.room(b_x0, b_y0, b_x1 - b_x0, 8.60 - b_y0, "Wing Sitting",
            area=21.8, size=2.2, sched_name="Wing sitting / kitchenette",
            sub="second household", at=(20.42, 7.95))
    sh.room(b_x0, 8.72, 20.60 - b_x0, 11.00 - 8.72, "Wing Bath", area=5.6,
            size=1.7, show_area=False, at=(19.30, 9.65))
    sh.room(20.72, 8.72, b_x1 - 20.72, 11.00 - 8.72, "Wing Hall", area=4.5,
            size=1.7, show_area=False, at=(21.71, 10.60))
    sh.room(b_x0, 11.12, b_x1 - b_x0, 15.30 - 11.12, "Wing Bedroom",
            area=19.0, size=2.2, at=(20.42, 14.60))
    sh.room(b_x0, 15.42, b_x1 - b_x0, b_y1 - 15.42, "Wing Dressing",
            area=10.4, size=1.9, show_area=False, at=(20.42, 16.60))


def _plan_second(sh, level):
    """Villa second floor: master suite in block A, two bedrooms in block B.

    Block A's south band is the master bedroom, so the route into block B
    cannot run through it.  The hall therefore turns north along the core
    and crosses the party wall at the north band instead.
    """
    shell(sh, 2)
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=OPENINGS[2]["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=OPENINGS[2]["b_south"])
    core_walls(sh)
    columns(sh)
    balcony(sh, BALC_A, f"{level[:-1]}7")
    balcony(sh, BALC_B, f"{level[:-1]}7", screen_w=False)

    # --- block A: master suite, with the hall tucked against the core -----
    sh.wall(a_x0, LF_Y0 - PT, CORE_WALL_X, LF_Y0,
            openings=[(12.30, 13.20), (14.10, 15.00)])
    sh.wall(13.78, 7.30, 13.90, 14.60)
    sh.wall(a_x0, 10.60, 13.78, 10.72, openings=[(12.30, 13.20)])
    sh.wall(a_x0, 14.60, CORE_WALL_X, CORE_N, openings=[(14.10, 15.00)])

    # --- block B: hall on the party wall, two bedrooms and two baths -----
    sh.wall(19.40, 8.40, 19.52, b_y1,
            openings=[(9.20, 10.10), (11.60, 12.50), (14.20, 15.10)])
    sh.wall(b_x0, 8.28, b_x1, 8.40, openings=[(18.40, 19.30)])
    sh.wall(19.52, 11.08, b_x1, 11.20)
    sh.wall(19.52, 13.48, b_x1, 13.60)

    # --- openings ---------------------------------------------------------
    for a, b in OPENINGS[2]["a_south"]:
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in OPENINGS[2]["b_south"]:
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    sh.window(*WIN_W_LIVING, A_X0, A_X0 + WT, "v")
    for a, b in OPENINGS[2]["b_east"]:
        sh.window(a, b, B_X1 - WT, B_X1, "v")
    north_windows(sh, 2)
    sh.door(*V_PARTY_BEDS, PARTY_X0, PARTY_X1, "v", leaf=False)

    core_fittings(sh, 2)
    sh.door(12.30, 13.20, LF_Y0 - PT, LF_Y0, "h", hinge="lo", swing="up")
    sh.door(14.10, 15.00, LF_Y0 - PT, LF_Y0, "h", hinge="lo", swing="up")
    sh.door(12.30, 13.20, 10.60, 10.72, "h", hinge="lo", swing="up")
    sh.door(14.10, 15.00, 14.60, CORE_N, "h", hinge="lo", swing="down")
    sh.door(9.20, 10.10, 19.40, 19.52, "v", hinge="lo", swing="right")
    sh.door(11.60, 12.50, 19.40, 19.52, "v", hinge="lo", swing="right")
    sh.door(14.20, 15.10, 19.40, 19.52, "v", hinge="lo", swing="right")
    sh.door(18.40, 19.30, 8.28, 8.40, "h", hinge="lo", swing="down")

    # --- block A fittings -------------------------------------------------
    fx.bed(sh, 14.20, 4.55, 1.90, 2.15, head="n")
    for bx in (13.65, 16.15):
        sh.rect(bx, 6.20, 0.50, 0.50, sw=LW_FIXTURE, stroke=GREY)
    sh.rect(14.45, 4.05, 1.45, 0.45, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    sh.rect(11.95, 5.55, 0.82, 0.82, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 11.85, 7.45, 0.55, 2.90, axis="v")
    fx.wardrobe(sh, 13.20, 7.45, 0.55, 2.90, axis="v")
    fx.bathtub(sh, 11.85, 10.85, 1.70, 0.75)
    fx.shower(sh, 11.85, 11.85, 1.12, 1.12)
    fx.wc(sh, 13.78, 12.10, facing="w")
    fx.basin(sh, 12.00, 14.60, w=1.20, d=0.50, facing="s")
    fx.counter(sh, 13.95, 11.60, 0.40, 1.20)
    fx.wardrobe(sh, a_x0, 17.10, 1.80, 0.55)

    # --- block B fittings -------------------------------------------------
    fx.bed(sh, 19.70, 4.55, 1.80, 2.10, head="n")
    for bx in (19.20, 21.55):
        sh.rect(bx, 6.15, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 18.20, 6.95, 2.40, 0.55)
    fx.bathtub(sh, 19.62, 8.55, 1.70, 0.75)
    fx.wc(sh, b_x1, 9.65, facing="w")
    fx.basin(sh, 19.70, 11.08, w=0.60, d=0.45, facing="s")
    fx.shower(sh, 19.62, 11.35, 1.15, 1.15)
    fx.wc(sh, b_x1, 11.55, facing="w")
    fx.basin(sh, 19.70, 13.48, w=0.60, d=0.45, facing="s")
    fx.bed(sh, 20.20, 14.15, 1.60, 2.05, head="n")
    for bx in (19.65, 21.85):
        sh.rect(bx, 15.70, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 19.62, 16.85, 1.60, 0.55)

    # --- rooms ------------------------------------------------------------
    sh.room(a_x0, a_y0, a_x1 - a_x0, LF_Y0 - PT - a_y0, "Master Bedroom",
            area=20.4, size=2.4, sub="to the balcony", at=(13.00, 4.60))
    sh.room(a_x0, 7.30, 13.78 - a_x0, 10.60 - 7.30, "Dressing", area=6.5,
            size=1.8, sched_name="Master dressing", show_area=False,
            at=(12.79, 9.40))
    sh.room(a_x0, 10.72, 13.78 - a_x0, 14.60 - 10.72, "Ensuite", area=7.7,
            size=1.8, sched_name="Master ensuite", show_area=False,
            at=(12.79, 13.70))
    sh.room(13.90, 7.30, CORE_WALL_X - 13.90, 14.60 - 7.30, "Hall",
            area=10.1, size=1.7, show_area=False, schedule=False,
            at=(14.59, 9.00))
    sh.room(a_x0, CORE_N, a_x1 - a_x0, a_y1 - CORE_N, "Upper Hall",
            area=18.0, size=2.0, sched_name="Upper hall", show_area=False,
            at=(15.80, 16.20))
    core_rooms(sh, 2, lobby_name="Landing", stair_name="Stair")
    sh.room(b_x0, b_y0, b_x1 - b_x0, 8.28 - b_y0, "Bedroom 4", area=20.4,
            size=2.3, sub="to the balcony", at=(20.42, 7.95))
    sh.tag(18.78, 12.60, "HALL", size=1.9, color=INK, rot=-90)
    sh.room(19.52, 8.40, b_x1 - 19.52, 11.08 - 8.40, "Bath 4", area=8.5,
            size=1.8, show_area=False, at=(21.11, 10.40))
    sh.room(19.52, 11.20, b_x1 - 19.52, 13.48 - 11.20, "Bath 3", area=7.3,
            size=1.8, show_area=False, at=(21.11, 12.90))
    sh.room(19.52, 13.60, b_x1 - 19.52, b_y1 - 13.60, "Bedroom 3", area=13.0,
            size=2.2, at=(21.11, 17.30))


def _apartment_floor(number, title, level, floor):
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet(number, title, level, "1:50 @ A1")
    F.border(sh)
    _plan_apartment(sh, floor, level)
    sh.dim_h(A_X0, B_X1, 1.6, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 0.4, "6.50")
    sh.dim_h(A_X1, B_X1, 0.4, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.4, "14.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, "14.50", ext_from=B_X1)
    sh.dim_v(B_Y0, 9.00, 26.0, "5.50")
    sh.dim_v(9.00, 11.10, 26.0, "2.10")
    sh.dim_v(11.10, B_Y1, 26.0, "6.60")
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


def sheet_first():
    """A-101, the villa family floor - no longer the apartment plan."""
    level = "+3.30"
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-101", "First Floor Plan", level, "1:50 @ A1")
    F.border(sh)
    _plan_first(sh, level)
    sh.dim_h(A_X0, B_X1, 1.6, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 0.4, "6.50")
    sh.dim_h(A_X1, B_X1, 0.4, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.4, "14.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, "14.50", ext_from=B_X1)
    sh.dim_v(B_Y0, 8.60, 26.0, "5.10")
    sh.dim_v(8.60, 11.00, 26.0, "2.40")
    sh.dim_v(11.00, 15.30, 26.0, "4.30")
    sh.dim_v(15.30, B_Y1, 26.0, "2.70")
    sh.tag(23.45, 13.20, "OPEN BOUNDARY \u2014 WINDOWS TO EAST",
           size=2.0, color=INK, rot=-90)
    sh.level_tag(12.60, 10.60, f"FFL {level}")
    sh.level_tag(18.40, 11.60, f"FFL {level}")

    section_line(sh)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[1]:.1f} m\u00b2"),
        ("Family floor / wing", "64.7 / 63.2 m\u00b2"),
        ("Balcony A / B (external)",
         f"{BALC[0]:.1f} / {BALC[1]:.1f} m\u00b2")])
    F.notes(sh, y + 6, [
        "The family floor. Block A holds the everyday living and dining at "
        "the south, opening onto the full-width balcony, with the family "
        "room at the north under its own windows and the upper hall "
        "running past the core between them.",
        "Block B is the second household\u2019s wing: sitting room with a "
        "kitchenette, bathroom, bedroom and dressing room, 63.2 m\u00b2 in "
        "all. The lift reaches it, which is the point of putting it here "
        "rather than at the top.",
        "The wing has one door \u2014 the arched opening at the south of the "
        "party wall \u2014 and it locks. Everywhere else the party wall backs "
        "onto the lift, the riser and the stair, so it cannot be opened.",
        "Balconies cantilever 1.20 m beyond the south wall, the full width "
        "of each block, divided on the party wall line by a 250 mm screen.",
        "Every habitable room is on an external wall. The west wall stays "
        "blind except where it faces the plot\u2019s own garden.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


def sheet_second():
    """A-102, the villa bedroom floor - no longer the apartment plan."""
    level = "+6.60"
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-102", "Second Floor Plan", level, "1:50 @ A1")
    F.border(sh)
    _plan_second(sh, level)
    sh.dim_h(A_X0, B_X1, 1.6, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 0.4, "6.50")
    sh.dim_h(A_X1, B_X1, 0.4, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.4, "14.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, "14.50", ext_from=B_X1)
    sh.dim_v(B_Y0, 8.28, 26.0, "4.78")
    sh.dim_v(8.28, 11.08, 26.0, "2.80")
    sh.dim_v(11.08, 13.48, 26.0, "2.40")
    sh.dim_v(13.48, B_Y1, 26.0, "4.22")
    sh.tag(23.45, 13.20, "OPEN BOUNDARY \u2014 WINDOWS TO EAST",
           size=2.0, color=INK, rot=-90)
    sh.level_tag(14.40, 12.40, f"FFL {level}")
    sh.level_tag(18.30, 5.60, f"FFL {level}")

    section_line(sh)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[2]:.1f} m\u00b2"),
        ("Master suite, total", "34.6 m\u00b2"),
        ("Balcony A / B (external)",
         f"{BALC[0]:.1f} / {BALC[1]:.1f} m\u00b2")])
    F.notes(sh, y + 6, [
        "The bedroom floor. The master suite takes block A\u2019s south band "
        "and the west strip beside the core: bedroom onto the full-width "
        "balcony, dressing room off it, ensuite beyond the dressing room.",
        "The master bedroom occupies the south band, so the route into "
        "block B cannot run through it. The hall turns north along the "
        "core instead and crosses the party wall at the north band \u2014 the "
        "only other place that wall has a room on both sides.",
        "Block B carries bedrooms 3 and 4 with their bathrooms, off a hall "
        "on the party wall. Bedroom 4 takes the south end and its own "
        "balcony; bedroom 3 the north end under the north windows.",
        "Bedrooms 3 and 4 share the two bathrooms off the hall rather than "
        "having ensuites: block B is 4.55 m wide, and a corridor plus an "
        "ensuite each would leave the bedrooms too narrow.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-103  THIRD FLOOR / ROOF
# ===========================================================================
def _plan_third(sh):
    """Villa third floor: roof majlis, gym, maid's suite, the fifth bedroom.

    The majlis takes block A's south band and opens onto the full-width
    terrace on the cantilever.  A corridor beside the core runs north past
    the maid's suite and the laundry to the gym, which in turn opens onto
    the north terrace.  Block B holds the guest bedroom and its ensuite.
    """
    o = OPENINGS[3]

    shell(sh, 3)
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=o["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=o["b_south"])
    core_walls(sh)
    columns(sh)

    # the south terrace runs the whole frontage on the cantilever
    balcony(sh, (A_X0, B_X1), "+9.87", name="South Terrace")

    # north terrace, block B, with its parapets over the shell wall
    parapet(sh, b_x0, B_Y1 - PARAPET, B_X1, B_Y1)
    parapet(sh, B_X1 - PARAPET, V_TER_N_Y0, B_X1, B_Y1)
    sh.wall(b_x0, V_TER_N_Y0, b_x1, V_TER_N_Y0 + PT,
            openings=[(19.60, 20.50)])

    # --- block A: majlis, corridor, maid's suite, laundry, gym -----------
    sh.wall(a_x0, LF_Y0 - PT, CORE_WALL_X, LF_Y0, openings=[(14.10, 15.00)])
    sh.wall(13.78, 7.30, 13.90, 14.60,
            openings=[(7.90, 8.80), (10.90, 11.80), (13.00, 13.90)])
    sh.wall(a_x0, 10.40, 13.78, 10.52)
    sh.wall(a_x0, 12.40, 13.78, 12.52)
    sh.wall(a_x0, 14.60, CORE_WALL_X, CORE_N, openings=[(14.10, 15.00)])

    # --- block B: guest bedroom, ensuite, store and plant ----------------
    sh.wall(b_x0, 9.00, b_x1, 9.12, openings=[(20.00, 20.90)])
    sh.wall(b_x0, 11.00, b_x1, 11.12)

    # --- openings ---------------------------------------------------------
    for a, b in o["a_south"]:
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in o["b_south"]:
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    sh.window(*WIN_W_LIVING, A_X0, A_X0 + WT, "v")
    for a, b in o["b_east"]:
        sh.window(a, b, B_X1 - WT, B_X1, "v")
    north_windows(sh, 3)
    sh.door(*V_PARTY_MAJLIS, PARTY_X0, PARTY_X1, "v", leaf=False)
    arch_note(sh, *V_PARTY_MAJLIS, PARTY_X0, axis="v", side=-1)
    sh.door(*V_PARTY_TERRACE, PARTY_X0, PARTY_X1, "v", leaf=False)

    core_fittings(sh, 3)
    sh.door(14.10, 15.00, LF_Y0 - PT, LF_Y0, "h", hinge="lo", swing="up")
    sh.door(14.10, 15.00, 14.60, CORE_N, "h", hinge="lo", swing="down")
    sh.door(7.90, 8.80, 13.78, 13.90, "v", hinge="lo", swing="left")
    sh.door(10.90, 11.80, 13.78, 13.90, "v", hinge="lo", swing="left")
    sh.door(13.00, 13.90, 13.78, 13.90, "v", hinge="lo", swing="left")
    sh.door(20.00, 20.90, 9.00, 9.12, "h", hinge="lo", swing="up")
    sh.door(19.60, 20.50, V_TER_N_Y0, V_TER_N_Y0 + PT, "h", leaf=False)

    # --- block A fittings -------------------------------------------------
    # roof majlis: low seating to three sides, as on the ground floor
    fx.sofa(sh, a_x0, 4.20, 0.78, 2.60, facing="e")
    fx.sofa(sh, 17.07, 4.20, 0.78, 2.60, facing="w")
    fx.sofa(sh, 13.30, 6.25, 2.60, 0.78, facing="s")
    sh.rect(14.05, 4.95, 1.10, 1.00, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    # maid's room, bath and laundry off the corridor
    fx.bed(sh, 11.90, 7.60, 1.00, 2.00, head="n")
    fx.wardrobe(sh, 13.20, 7.60, 0.50, 1.40, axis="v")
    fx.shower(sh, 11.90, 10.65, 1.00, 1.00)
    fx.wc(sh, 13.78, 11.70, facing="w")
    fx.basin(sh, 11.90, 12.40, w=0.55, d=0.40, facing="s")
    sh.rect(11.90, 12.70, 0.64, 0.64, sw=LW_FIXTURE, stroke=GREY)
    sh.circle(12.22, 13.02, 0.20, stroke=GREY, sw=LW_FIXTURE)
    fx.counter(sh, 12.70, 12.70, 1.00, 0.60)
    fx.sink(sh, 12.85, 12.80, w=0.55, d=0.40)
    # gym: equipment against the north windows, mirror on the core wall
    fx.counter(sh, a_x0, 15.00, 1.80, 0.70)
    sh.rect(13.90, 14.95, 1.50, 0.70, rx=D.mm(0.1), sw=LW_FIXTURE,
            stroke=GREY)
    sh.rect(15.80, 14.95, 1.90, 0.70, rx=D.mm(0.1), sw=LW_FIXTURE,
            stroke=GREY)
    sh.line(a_x0, 17.62, 17.80, 17.62, w=LW_FIXTURE, color=GREY)
    sh.tag(16.60, 17.32, "MIRROR OVER", size=1.6, color=GREY)

    # --- block B fittings -------------------------------------------------
    fx.bed(sh, 19.70, 4.60, 1.80, 2.10, head="n")
    for bx in (19.20, 21.55):
        sh.rect(bx, 6.20, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 18.20, 7.10, 2.40, 0.55)
    fx.shower(sh, 18.25, 9.25, 1.15, 1.15)
    fx.wc(sh, b_x1, 9.35, facing="w")
    fx.basin(sh, 20.40, 11.00, w=0.65, d=0.45, facing="s")
    fx.wardrobe(sh, 18.20, 11.30, 0.55, 1.50, axis="v")
    sh.rect(21.20, 11.40, 1.20, 1.20, sw=LW_FIXTURE, stroke=GREY)
    sh.tag(21.80, 11.90, "TANKS", size=1.6, color=GREY)
    # north terrace
    fx.pergola(sh, 19.00, 14.00, 2.80, 2.40, pitch=0.55)
    for px in (18.25, 22.05):
        fx.planter(sh, px, 13.40, 0.55, 2.00)
    fx.table(sh, 19.60, 15.90, 1.50, 0.90, seats_n=3, seats_s=3)
    # south terrace, under its pergola
    fx.pergola(sh, A_X0 + 0.30, A_Y0 - BALC_D + 0.25, 6.05, 0.95, pitch=0.55)
    fx.pergola(sh, b_x0, A_Y0 - BALC_D + 0.25, 4.30, 0.95, pitch=0.55)

    # --- rooms ------------------------------------------------------------
    sh.room(a_x0, a_y0, a_x1 - a_x0, LF_Y0 - PT - a_y0, "Roof Majlis",
            area=20.4, size=2.5, sub="to the south terrace", at=(14.90, 5.60))
    sh.room(13.90, 7.30, CORE_WALL_X - 13.90, 14.60 - 7.30, "Corridor",
            area=10.1, size=1.7, show_area=False, schedule=False,
            at=(14.59, 9.10))
    sh.room(a_x0, 7.30, 13.78 - a_x0, 10.40 - 7.30, "Maid\u2019s Room",
            area=6.1, size=1.8, sched_name="Maid\u2019s room",
            show_area=False, at=(12.79, 9.90))
    sh.room(a_x0, 10.52, 13.78 - a_x0, 12.40 - 10.52, "Maid\u2019s Bath",
            area=3.7, size=1.6, sched_name="Maid\u2019s bath",
            show_area=False, at=(12.79, 11.95))
    sh.room(a_x0, 12.52, 13.78 - a_x0, 14.60 - 12.52, "Laundry", area=4.1,
            size=1.7, show_area=False, at=(12.79, 14.15))
    sh.room(a_x0, CORE_N, a_x1 - a_x0, a_y1 - CORE_N, "Gym", area=18.0,
            size=2.4, sub="to the north terrace", at=(13.40, 17.35))
    core_rooms(sh, 3, lobby_name="Landing", stair_name="Stair")
    sh.room(b_x0, b_y0, b_x1 - b_x0, 9.00 - b_y0, "Bedroom 5", area=23.7,
            size=2.3, sub="guest suite", at=(20.42, 8.60))
    sh.room(b_x0, 9.12, b_x1 - b_x0, 11.00 - 9.12, "Ensuite", area=8.6,
            size=1.8, sched_name="Guest ensuite", show_area=False,
            at=(20.42, 10.60))
    sh.room(b_x0, 11.12, b_x1 - b_x0, V_TER_N_Y0 - 11.12, "Store & Plant",
            area=8.6, size=1.8, sched_name="Store & plant",
            show_area=False, at=(19.60, 12.60))
    sh.room(b_x0, V_TER_N_Y0, b_x1 - b_x0, b_y1 - V_TER_N_Y0,
            "North Terrace", area=21.4, size=2.1, sub="shaded",
            sched_name="North terrace", at=(20.42, 17.30))


def sheet_third():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-103", "Third Floor & Roof Plan", "+9.90", "1:50 @ A1")
    F.border(sh)
    _plan_third(sh)
    sh.dim_h(A_X0, B_X1, 1.05, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, -0.15, "6.50")
    sh.dim_h(A_X1, B_X1, -0.15, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.4, "14.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.6, "14.50", ext_from=B_X1)
    sh.dim_v(B_Y0, 9.00, 26.0, "5.50")
    sh.dim_v(9.00, V_TER_N_Y0, 26.0, "4.00")
    sh.dim_v(V_TER_N_Y0, b_y1, 26.0, "4.70")
    sh.tag(23.45, 7.00, "OPEN BOUNDARY \u2014 WINDOWS TO EAST",
           size=2.0, color=INK, rot=-90)
    sh.level_tag(12.30, 2.62, "TERRACE +9.87")
    sh.level_tag(16.20, 4.10, "FFL +9.90")
    sh.level_tag(21.60, 13.60, "+9.87")

    # the stair-head vent, in the roof slab over the top landing
    sh.rect(AOV_X[0], AOV_Y[0], AOV_X[1] - AOV_X[0], AOV_Y[1] - AOV_Y[0],
            sw=LW_HIDDEN, stroke=INK, dash="2.6 1.4")
    sh.tag((AOV_X[0] + AOV_X[1]) / 2.0, (AOV_Y[0] + AOV_Y[1]) / 2.0 - 0.10,
           f"AOV {AOV_AREA:.1f} m\u00b2", size=1.6, color=INK)

    section_line(sh)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{PLATE - V_TER_N:.1f} m\u00b2"),
        ("Open-air terrace, north and south",
         f"{TER_S + V_TER_N:.1f} m\u00b2"),
        ("Roof over, top of slab", f"+{ROOF_LEVEL:.2f}")])
    F.notes(sh, y + 6, [
        "The roof floor. The majlis takes block A\u2019s south band and opens "
        "onto the terrace that runs the whole frontage on the 1.20 m "
        "cantilever, under a pergola.",
        "A corridor beside the core runs north from the majlis past the "
        "maid\u2019s room, her bath and the laundry to the gym, which takes "
        "the north end of block A under its own windows and opens onto "
        "the north terrace.",
        "Block B holds bedroom 5 \u2014 the guest suite \u2014 with its ensuite, "
        "and the store and plant room behind. The guest bedroom is "
        "entered from the majlis through the party wall, which is the "
        "only place at this level where that wall has a room on both "
        "sides apart from the terrace door.",
        "Terrace finish is 30 mm below floor level, falling 1:80 to "
        "outlets. Parapets are 250 mm thick and 1.10 m high.",
        f"The roof over falls 1:60 to outlets. The {AOV_AREA:.1f} m\u00b2 vent "
        "shown over the landing smoke-vents the stair, which has no "
        "external wall of its own.",
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


def sheet_section():
    D.set_scale(50, *SEC_ORIGIN)
    sh = Sheet("A-200", "Section A–A", "through the core", "1:50 @ A1")
    F.border(sh)

    top = 3 * FLOOR_TO_FLOOR                      # +9.90
    roof = ROOF_LEVEL                             # +13.20

    # ground, garden and the street beyond
    sh.rect(-1.0, -2.60, A_Y0 + 1.0, 2.10, fill="#f4f4f4", stroke="none",
            sw=0)
    _hatch(sh, -1.0, -2.60, A_Y0 + 1.0, 2.10, pitch=0.7, color="#dcdcdc")
    sh.line(-1.0, GARDEN_LEVEL, A_Y0, GARDEN_LEVEL, w=LW_CUT, color=INK)
    sh.rect(A_Y0, -2.60, A_Y1 - A_Y0, 2.60, fill="#f4f4f4", stroke="none",
            sw=0)
    _hatch(sh, A_Y0, -2.60, A_Y1 - A_Y0, 2.10, pitch=0.7, color="#dcdcdc")
    sh.level_tag(1.60, GARDEN_LEVEL, "GARDEN −0.50")
    fx.steps(sh, A_Y0 - 0.95, GARDEN_LEVEL, 0.95, 0.50, n=ENTRY_RISERS,
             axis="e")

    # foundations, indicative
    for a, b in ((A_Y0, A_Y0 + WT), (LF_Y0 - PT, LF_Y0), (LOB_Y1, ST_Y0),
                 (ST_Y1, CORE_N), (a_y1, A_Y1)):
        sh.wall(a - 0.25, -1.55, b + 0.25, -1.15)
        sh.wall(a, -1.15, b, -STRUCTURAL_ZONE)

    for lv in SEC_LEVELS:
        ffl = lv * FLOOR_TO_FLOOR
        # floor slabs, continuous from the south wall to the north
        _slab(sh, A_Y0, A_Y1, ffl)
        # the lift shaft carries removable infill slabs, shown dashed
        _slab(sh, LF_Y0, LF_Y1, ffl, dash="2.2 1.4")
        # cantilevered balcony or terrace slab
        if lv > 0:
            _slab(sh, A_Y0 - BALC_D, A_Y0, ffl - 0.03)
            sh.wall(A_Y0 - BALC_D, ffl - 0.03, A_Y0 - BALC_D + PARAPET,
                    ffl + 1.10)
        # external and core walls of the storey
        clear = CLEAR_HEIGHT
        for a, b in ((LF_Y0 - PT, LF_Y0), (LF_Y1, LOB_Y0),
                     (LOB_Y1, ST_Y0), (ST_Y1, CORE_N)):
            sh.wall(a, ffl, b, ffl + clear)
        # north wall: the boundary is open, so the cut passes through a
        # window in it on every floor
        sh.wall(a_y1, ffl, A_Y1, ffl + clear,
                openings=[(ffl + 0.90, ffl + 2.40)])
        sh.window(ffl + 0.90, ffl + 2.40, a_y1, A_Y1, "v")
        # south wall: glazed at the cut, so only the piers above and below
        sh.wall(A_Y0, ffl + 2.35, A_Y0 + WT, ffl + clear)
        sh.wall(A_Y0, ffl, A_Y0 + WT, ffl + 0.10)
        sh.line(A_Y0 + WT / 2, ffl + 0.10, A_Y0 + WT / 2, ffl + 2.35,
                w=LW_FIXTURE, color=GREY)
        _stair_section(sh, ffl)
        sh.level_tag(A_Y0 + 0.9, ffl, f"FFL +{ffl:.2f}")

    # roof slab and parapets, with the stair-head vent opening in it
    _slab(sh, A_Y0, A_Y1, roof, openings=[AOV_Y])
    sh.wall(A_Y0, roof, A_Y0 + PARAPET, roof + 1.10)
    sh.wall(a_y1, roof, A_Y1, roof + 1.10)
    sh.level_tag(A_Y0 + 0.9, roof, f"ROOF +{roof:.2f}")

    # the stair-head vent, drawn open: kerb upstand, the closed lid dashed
    # and the flap in its open position
    kerb = 0.30
    sh.wall(AOV_Y[0] - PT, roof, AOV_Y[0], roof + kerb)
    sh.wall(AOV_Y[1], roof, AOV_Y[1] + PT, roof + kerb)
    sh.line(AOV_Y[0] - PT, roof + kerb, AOV_Y[1] + PT, roof + kerb,
            w=LW_SECONDARY, color=GREY, dash="2.2 1.4")
    sh.line(AOV_Y[0] - PT, roof + kerb, AOV_Y[1] - 0.05, roof + kerb + 0.55,
            w=LW_CUT, color=INK)
    sh.tag((AOV_Y[0] + AOV_Y[1]) / 2.0, roof + 1.20,
           f"AOV {AOV_AREA:.1f} m² — STAIR SMOKE VENT", size=1.9, color=INK)

    # lift shaft: pit, car and overrun
    sh.wall(LF_Y0 - PT, -1.45, LF_Y0, 0.0)
    sh.wall(LF_Y1, -1.45, LOB_Y0, 0.0)
    sh.wall(LF_Y0 - PT, -1.55, LOB_Y0, -1.45)
    sh.tag((LF_Y0 + LF_Y1) / 2.0, -0.95, "PIT", size=1.7, color=GREY)
    sh.rect(LF_Y0, top + 0.10, LF_Y1 - LF_Y0, 1.55, sw=LW_SECONDARY,
            stroke=GREY, dash="2.2 1.4")
    sh.tag((LF_Y0 + LF_Y1) / 2.0, top + 1.00, "OVERRUN", size=1.6,
           color=GREY)
    for lv in SEC_LEVELS:
        sh.tag((LF_Y0 + LF_Y1) / 2.0, lv * FLOOR_TO_FLOOR + 1.35, "LIFT",
               size=1.8, color=GREY)

    # what the cut passes through, named at each level
    rooms = {0: ("Entrance lobby", "Fire lobby", "Store & plant"),
             1: ("Apt A living", "Fire lobby", "Apt A bedroom"),
             2: ("Apt A living", "Fire lobby", "Apt A bedroom"),
             3: ("Living / dining", "Fire lobby", "Bedroom 2")}
    for lv in SEC_LEVELS:
        ffl = lv * FLOOR_TO_FLOOR
        south, lobby, north = rooms[lv]
        sh.tag((a_y0 + LF_Y0) / 2.0, ffl + 1.05, south.upper(), size=1.9,
               color=INK)
        sh.tag((LOB_Y0 + LOB_Y1) / 2.0, ffl + 1.05, lobby.upper(), size=1.7,
               color=INK)
        sh.tag((CORE_N + a_y1) / 2.0, ffl + 1.05, north.upper(), size=1.7,
               color=INK)
        if lv > 0:
            sh.tag(A_Y0 - BALC_D / 2.0, ffl + 0.62,
                   "TERRACE" if lv == 3 else "BALCONY", size=1.7, color=GREY,
                   rot=-90)

    # dimensions: storey heights on the left, the plan axis along the bottom
    for lv in SEC_LEVELS:
        ffl = lv * FLOOR_TO_FLOOR
        sh.dim_v(ffl, ffl + FLOOR_TO_FLOOR if lv < 3 else roof, -1.60,
                 f"{FLOOR_TO_FLOOR:.2f}" if lv < 3 else f"{roof - top:.2f}")
    sh.dim_v(GARDEN_LEVEL, 0.0, -1.60, "0.50")
    sh.dim_v(GARDEN_LEVEL, roof, -2.65, f"{roof - GARDEN_LEVEL:.2f}")
    sh.dim_h(A_Y0, A_Y1, -3.05, "14.50", ext_from=GARDEN_LEVEL)
    sh.dim_h(A_Y0 - BALC_D, A_Y0, -3.05, "1.20")
    sh.dim_h(CORE_N, a_y1, -2.05, "2.98")
    sh.dim_h(ST_Y0, ST_Y1, -2.05, "4.00")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.datum_panel(sh, y + 8, "LEVEL DATUMS", [
        ("Garden", f"{GARDEN_LEVEL:+.2f}"),
        ("Ground floor", "+0.00"),
        ("First floor", f"+{FLOOR_TO_FLOOR:.2f}"),
        ("Second floor", f"+{2 * FLOOR_TO_FLOOR:.2f}"),
        ("Third floor", f"+{top:.2f}"),
        ("Roof, top of slab", f"+{roof:.2f}"),
        ("Clear ceiling height", f"{CLEAR_HEIGHT:.2f} m"),
        ("Structural zone", f"{STRUCTURAL_ZONE:.2f} m"),
        ("Overall, garden to roof", f"{roof - GARDEN_LEVEL:.2f} m")])
    F.notes(sh, y + 6, [
        "Section looking west, cut on the line marked A–A on the floor "
        "plans: through the south glazing, the lift shaft, the protected "
        "lobby, the stair and the room at the north end of block A.",
        "Both ends of block A are glazed: the north boundary is open, so "
        "the cut passes through a north window at every level. The light "
        "court that stood here in P3 has been built over, giving back "
        "7.3 m² a floor.",
        "The lift shaft is built full height with removable infill slabs "
        "at each level, shown dashed, so a lift can be installed later "
        "without cutting structure. Pit and overrun are indicative and to "
        "be confirmed against the chosen lift.",
        "Flat slab on the column grid, 300 mm structural zone, giving "
        "3.00 m clear at every level and 3.30 m floor to floor.",
        "The stair is enclosed in the middle of block A and has no "
        "external wall, so it is smoke-vented at its head by a "
        f"{AOV_AREA:.1f} m² automatic opening vent through the roof slab, "
        "shown open. The single-stair strategy is the client's decision "
        "and still needs the authority's agreement.",
        "Foundations are shown indicatively only and are subject to a "
        "ground investigation and the engineer's design.",
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

    sh.dim_h(a_x0, 13.28, 11.55, "1.48")
    sh.dim_h(13.40, CORE_WALL_X, 11.55, "1.88")
    sh.dim_h(20.40, b_x1, 11.55, "2.30")
    sh.dim_v(8.98, 11.30, 11.50, "2.32")
    sh.dim_v(9.12, 11.10, 23.10, "1.98")

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
    F.titleblock(sh)
    return sh


def sheet_unit_third():
    sh = _detail_sheet(
        "A-301", "Third Floor Apartment — Enlarged Plan", "+9.90",
        (-432.0, 690.0), (25, 78, 490, 472), _plan_third,
        [("Living / dining / kitchen", 35.8), ("Bedroom 1", 19.6),
         ("Ensuite", 7.5), ("Dressing", 7.1), ("Family bath", 5.2),
         ("Guest WC", 2.3)])

    sh.dim_h(a_x0, b_x1, 15.20, "10.90")
    sh.dim_h(b_x0, 20.30, 15.20, "2.15")
    sh.dim_v(a_y0, LIV3_Y1, 11.50, "3.38")
    sh.dim_v(LF_Y0, 11.60, 23.10, "4.30")
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
    F.titleblock(sh)
    return sh


def sheet_service():
    sh = _detail_sheet(
        "A-302", "Central Kitchen & Laundry — Enlarged Plan", "+0.00",
        (-412.0, 808.0), (40, 78, 480, 374), _plan_ground,
        [("Service kitchen", 12.9), ("Servery", 3.0), ("Wash-up", 3.2),
         ("Staff WC", 2.0), ("Bin store", 1.9), ("Central laundry", 4.0),
         ("Guest bath", 5.9), ("Linen & store", 3.3)])

    sh.dim_v(14.00, a_y1, 11.55, "3.70")
    sh.dim_h(a_x0, CORE_WALL_X, 17.85, "3.48")
    sh.dim_v(9.12, 10.32, 23.05, "1.20")
    sh.dim_h(19.37, b_x1, 8.98, "3.33")

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
    F.titleblock(sh)
    return sh


# ===========================================================================
SHEETS = (sheet_site, sheet_ground, sheet_first, sheet_second, sheet_third,
          sheet_section, sheet_unit_typical, sheet_unit_third, sheet_service)


def slugify(title):
    """Sheet title -> file name: ASCII, lower case, hyphen separated."""
    out = []
    for ch in title.lower():
        out.append(ch if (ch.isalnum() and ch.isascii()) else "-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "drawings")
    os.makedirs(out, exist_ok=True)
    paths = []
    for builder in SHEETS:
        sh = builder()
        slug = slugify(sh.title)
        path = os.path.join(out, f"{sh.number}-{slug}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(F.render(sh))
        print(f"{os.path.basename(path):42s} {len(sh.body):5d} entities")
        paths.append(path)
    return paths


if __name__ == "__main__":
    main()
