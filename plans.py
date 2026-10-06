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

    sh.dim_h(0, 23.0, -4.8, ext_from=0.0)
    sh.dim_h(0, 11.5, -6.6)
    sh.dim_h(11.5, 18.0, -6.6)
    sh.dim_h(18.0, 23.0, -6.6)
    sh.dim_v(0, 5.0, -1.8, ext_from=0.0)
    sh.dim_v(0, 18.0, -3.6)
    sh.dim_v(3.5, 18.0, 24.5, ext_from=23.0)
    sh.dim_v(0, 3.5, 24.5)

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
    sh.dim_h(0, PLOT_W, -2.0, ext_from=0.0)
    sh.dim_h(A_X0, A_X1, -0.9)
    sh.dim_h(A_X1, B_X1, -0.9)
    sh.dim_v(0, GARDEN_D, -1.0, ext_from=0.0)
    sh.dim_v(A_Y0, A_Y1, -1.0)
    sh.dim_v(B_Y0, B_Y1, 24.2, ext_from=B_X1)
    sh.dim_v(A_Y0, LF_Y0, 25.6)
    sh.dim_v(LF_Y0, ST_Y0, 25.6)
    sh.dim_v(ST_Y0, ST_Y1, 25.6)
    sh.dim_v(ST_Y1, B_Y1, 25.6)
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
            "Suite 1", area=14.0, size=2.4, sub="bedroom",
            sched_name="Suite 1 bedroom", at=(15.90, 5.30))
    sh.room(v3_x0, V2_S1_BED_Y1 + PT, V2_S1_ENS_X1 - v3_x0,
            V2_S1_Y1 - V2_S1_BED_Y1 - PT, "Ensuite 1", area=4.4, size=1.7,
            sched_name="Suite 1 ensuite", show_area=False, at=(14.45, 7.70))
    sh.room(V2_S1_ENS_X1 + PT, V2_S1_BED_Y1 + PT, V3_SPINE_X0 - V2_S1_ENS_X1,
            V2_S1_Y1 - V2_S1_BED_Y1 - PT, "Dressing 1", area=4.3, size=1.7,
            sched_name="Suite 1 dressing", show_area=False, at=(16.00, 8.02))
    sh.room(V3_SPINE_X1, v3_y0, v3_x1 - V3_SPINE_X1, V2_S2_BED_Y1 - v3_y0,
            "Suite 2", area=19.6, size=2.4, sub="bedroom",
            sched_name="Suite 2 bedroom", at=(19.95, 4.35))
    sh.room(V2_LOBBY_X1 + PT, V2_S2_BED_Y1 + PT, v3_x1 - V2_LOBBY_X1 - PT,
            V2_ENS2_Y1 - V2_S2_BED_Y1 - PT, "Ensuite 2", area=4.2, size=1.7,
            sched_name="Suite 2 ensuite", show_area=False, at=(19.80, 9.15))
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
            "Bedroom 3", area=18.8, size=2.4, at=(15.30, 16.20))
    sh.room(V3_SPINE_X1, V3_BED3_Y0, v3_x1 - V3_SPINE_X1, v3_y1 - V3_BED3_Y0,
            "Bedroom 4", area=17.0, size=2.4, at=(19.80, 16.30))


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
    # the villa revision, but still under discussion - no final-draft status
    sh.rev = "P6"
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 10.00, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 10.00, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
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
    # the cantilever's two ends
    sh.dim_v(V3_Y0 - V3_WAVE_W, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_E, V3_Y0, 22.45)

    sh.tag(24.00, 7.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY — NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)
    sh.tag(17.25, 0.25, f"CANTILEVER — SINGLE ASYMMETRIC CURVE, "
           f"{V3_WAVE_W:.2f} m WEST → {V3_WAVE_E:.2f} m EAST",
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
        "Draft for comment. A bedroom floor: two suites and two further "
        "bedrooms, on the detached envelope. The ground floor and the site "
        "plan are still on the old 11.50 \u00d7 14.50 footprint.",
        "The east strip is the first floor's, line for line \u2014 shared bath "
        "5.4 m\u00b2, lobby 4.8 m\u00b2, suite 2's bedroom 19.6 m\u00b2 as its wall "
        "moves 1.30 m north. Every wet room and east window stacks, one "
        "drainage stack each, straight to the ground.",
        "Suite 1 takes the south-west, ensuite and dressing behind; suite 2 "
        "the south-east, its ensuite off the bedroom.",
        "The lobby has no door: the spine is opened its whole length between "
        "the columns, so lobby and landing read as one space. It serves "
        "suite 2, the shared bath and bedroom 4. Bedroom 3 has the old hall "
        "\u2014 the whole north-west quarter, 18.8 m\u00b2.",
        f"The cantilever is carried here too \u2014 the same curve, "
        f"{V3_WAVE_W:.2f} m west to {V3_WAVE_E:.2f} m east, "
        f"{wave_area():.1f} m\u00b2 \u2014 so it now runs all three upper floors "
        "and the slabs stack. Both suites open onto it; a screen between "
        "the two is worth considering.",
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
            "Master Bedroom", area=19.6, size=2.4, sub="master suite",
            sched_name="Master bedroom", at=(19.95, 4.35))
    sh.room(V2_LOBBY_X1 + PT, V1_MBED_Y1 + PT, v3_x1 - V2_LOBBY_X1 - PT,
            V1_ENS_Y1 - V1_MBED_Y1 - PT, "Ensuite", area=4.2,
            size=1.7, sched_name="Master ensuite", show_area=False,
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


def sheet_first():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-101", "First Floor Plan — Detached Villa", "+3.30",
               "1:50 @ A1")
    sh.rev, sh.status = "P6", F.STATUS_FINAL_DRAFT
    F.border(sh)

    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 10.00, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 10.00, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
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
    sh.dim_v(V3_Y0 - V3_WAVE_W, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_E, V3_Y0, 22.45)

    sh.tag(24.00, 7.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY — NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)
    sh.tag(17.25, 0.25, f"CANTILEVER — SINGLE ASYMMETRIC CURVE, "
           f"{V3_WAVE_W:.2f} m WEST → {V3_WAVE_E:.2f} m EAST",
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
        "three sleeping rooms. The living area is 32.3 m² with the stair "
        "standing in it and the pantry open along the spine, opening "
        "through a sliding door onto the cantilever.",
        "The pantry is a counter against the solid stretch of spine, not "
        "the walled room the third floor has. The lobby has no wall either: "
        "the spine is opened 3.69 m between the columns, a downstand beam "
        "rather than a wall.",
        "The west strip is otherwise the third floor's and the east strip "
        "the second's, so the wet rooms stack and the stair lines through. "
        "East and north carry ordinary windows, the west louvred "
        "ventilation only. The hall to the north bedrooms stops at its last "
        "door; the dead end beyond goes to bedroom 2, 16.4 m\u00b2.",
        "The master bedroom's north wall is 1.30 m further north than the "
        "suite below it, taking it to 19.6 m²; the shared bath gives up the "
        "same depth, at 5.4 m².",
        "The south cantilever repeats the third floor's: the same "
        f"asymmetric curve, {V3_WAVE_W:.2f} m west sweeping to "
        f"{V3_WAVE_E:.2f} m east, {wave_area():.1f} m², with sliding doors "
        "from the living area and the master bedroom. The second floor has "
        "none, so the two do not yet stack.",
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
    fx.stair(sh, V3_STAIR, direction="dn", floor_to_floor=FLOOR_TO_FLOOR,
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
            "Suite 1", area=15.5, size=2.4, sub="bedroom",
            sched_name="Suite 1 bedroom", at=(19.75, 6.62))
    sh.room(V3_SPINE_X1, V3_S1_ENS_Y0, v3_x1 - V3_SPINE_X1,
            V3_S1_Y1 - V3_S1_ENS_Y0, "Ensuite 1", area=6.5, size=1.8,
            sched_name="Suite 1 ensuite", show_area=False, at=(19.35, 8.00))
    sh.room(V3_SPINE_X1, V3_S1_Y1 + PT, v3_x1 - V3_SPINE_X1,
            V3_BATH_Y1 - (V3_S1_Y1 + PT), "Shared Bath", area=6.5, size=1.8,
            sched_name="Shared bath", show_area=False, at=(19.45, 9.62))
    sh.room(V3_SPINE_X1, V3_BATH_Y1 + PT, v3_x1 - V3_SPINE_X1,
            V3_S2_ENS_Y1 - (V3_BATH_Y1 + PT), "Ensuite 2", area=6.5,
            size=1.8, sched_name="Suite 2 ensuite", show_area=False,
            at=(19.50, 12.40))
    sh.room(V3_SPINE_X1, V3_S2_ENS_Y1 + PT, v3_x1 - V3_SPINE_X1,
            v3_y1 - (V3_S2_ENS_Y1 + PT), "Suite 2", area=15.9, size=2.4,
            sub="bedroom", sched_name="Suite 2 bedroom",
            at=(19.65, 16.30))
    # L-shaped: the strip west of the hall, plus the full width north of it
    sh.room(v3_x0, V3_BED3_Y0, V3_BED3_X1 - v3_x0, v3_y1 - V3_BED3_Y0,
            "Bedroom 3", area=16.4, size=2.4, at=(14.60, 16.00))


def sheet_third():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-103", "Third Floor Plan — Detached Villa", "+9.90",
               "1:50 @ A1")
    sh.rev, sh.status = "P6", F.STATUS_FINAL_DRAFT
    F.border(sh)

    # the three setback lines, so the 1.00 m gap is measurable on the sheet
    with sh.on("G-ANNO-BNDY"):
        for a, b, c, d in ((A_X0, A_Y0, A_X0, A_Y1), (A_X0, A_Y1, B_X1, A_Y1),
                           (B_X1, A_Y0, B_X1, A_Y1)):
            sh.line(a, b, c, d, w=LW_THIN, color=LIGHT, dash="4 2")
    sh.tag(11.95, 10.00, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
    sh.tag(22.55, 10.00, "1.00 m SETBACK", size=1.8, color=GREY, rot=-90)
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
    # the cantilever's two ends
    sh.dim_v(V3_Y0 - V3_WAVE_W, V3_Y0, 12.10)
    sh.dim_v(V3_Y0 - V3_WAVE_E, V3_Y0, 22.45)

    sh.tag(24.00, 7.00, "OPEN ASPECT — WINDOWS TO EAST", size=2.0,
           color=INK, rot=-90)
    sh.tag(19.60, 17.45, "OPEN ASPECT — WINDOWS TO NORTH", size=2.0,
           color=INK)
    sh.tag(11.60, 6.60, "VENTILATION ONLY — NO BALCONY WEST", size=2.0,
           color=INK, rot=-90)
    sh.tag(17.25, 0.25, f"CANTILEVER — SINGLE ASYMMETRIC CURVE, "
           f"{V3_WAVE_W:.2f} m WEST → {V3_WAVE_E:.2f} m EAST",
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
        "The west strip south of bedroom 3 is one room: no wall divides the "
        "living area from the stair standing in it, and the pantry is its "
        "only enclosure. The stair is a private villa stair — 900 mm "
        "flights, 18R at 183 × 260, landing 950 mm — needing no enclosure, "
        "no smoke vent and no lift.",
        f"The south cantilever is reinforced concrete: one asymmetric "
        f"curve bowed outward, {V3_WAVE_W:.2f} m at the west end sweeping "
        f"away to {V3_WAVE_E:.2f} m at the east. Every point on the edge "
        "stands outside the line joining the two ends.",
        "East and north carry ordinary windows; both neighbours are "
        "3.00 m high. The west carries louvred ventilation only.",
        "Suite 1 and the shared bath open off the living area; suite 2 and "
        "bedroom 3 off the hall, which stops once it has served those two "
        "doors \u2014 the 2.08 m of dead end beyond goes to bedroom 3, which "
        "turns the corner behind it at 16.4 m\u00b2.",
        "Suite 2 has no balcony: its bedroom takes the north wall and two "
        "windows instead. Floors 0–2, the site plan and section A-A are "
        "still on the old 11.50 × 14.50 footprint.",
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
    sh.dim_v(GARDEN_LEVEL, 0.0, -1.60)
    sh.dim_v(GARDEN_LEVEL, roof, -2.65, f"{roof - GARDEN_LEVEL:.2f}")
    sh.dim_h(A_Y0, A_Y1, -3.05, ext_from=GARDEN_LEVEL)
    sh.dim_h(A_Y0 - BALC_D, A_Y0, -3.05)
    sh.dim_h(CORE_N, a_y1, -2.05)
    sh.dim_h(ST_Y0, ST_Y1, -2.05)

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
