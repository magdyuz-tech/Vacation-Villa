#!/usr/bin/env python3
"""
plans.py - generates the drawing set for the vacation house.

  A-000  Site plan                            1:100
  A-100  Ground floor plan        +0.00        1:50
  A-101  First floor plan         +3.00        1:50
  A-102  Second floor & roof plan +6.00        1:50

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

SITE_ORIGIN = (155.0, 333.0)     # 1:75
PLAN_ORIGIN = (-79.0, 480.0)     # 1:50
PARAPET_FILL = "#6f6f6f"

GIA = {0: 121.8, 1: 94.7, 2: 41.5}


# ===========================================================================
# shared pieces
# ===========================================================================
def boundary(sh, label=True):
    sh.poly(PLOT, stroke=INK, sw=0.45, dash="6 1.5 1.2 1.5")
    if label:
        sh.tag(8.60, 5.40, "SITE BOUNDARY", size=1.9, color=GREY)


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
    for x0, y0, x1, y1 in [(0.0, 5.0, 11.5, 18.6), (11.5, 17.5, 18.0, 18.6),
                           (18.0, 18.0, 23.8, 18.6), (23.0, 5.0, 23.8, 18.0)]:
        _hatch(sh, x0, y0, x1 - x0, y1 - y0)
    sh.tag(5.7, 11.8, "NEIGHBOURING PLOT", size=2.8, color=LIGHT)
    sh.tag(24.9, 11.5, "NEIGHBOURING PLOT", size=2.4, color=LIGHT, rot=-90)
    sh.tag(14.7, 18.9, "NEIGHBOURING PLOT", size=2.4, color=LIGHT)
    sh.tag(20.5, 19.4, "NEIGHBOURING PLOT", size=2.4, color=LIGHT)


def street(sh, y0=-3.4):
    sh.rect(-1.5, y0, 26.5, -y0, fill="#f5f5f5", stroke="none", sw=0)
    sh.line(-1.5, 0.0, 25.0, 0.0, w=LW_SECONDARY, color=GREY)
    sh.line(-1.5, y0, 25.0, y0, w=LW_THIN, color=LIGHT)
    for i in range(10):
        x = -0.6 + i * 2.7
        sh.line(x, y0 / 2, x + 1.4, y0 / 2, w=LW_THIN, color=LIGHT)
    sh.tag(11.5, y0 + 0.75, "S T R E E T", size=3.4, color=GREY)


def shell(sh, floor):
    o = OPENINGS[floor]
    sh.wall(A_X0, A_Y0, 17.85, A_Y0 + WT, openings=o["a_south"])
    sh.wall(A_X0, A_Y0, A_X0 + WT, A_Y1)
    sh.wall(A_X0, A_Y1 - WT, 17.85, A_Y1)
    sh.wall(PARTY_X0, A_Y0, PARTY_X1, B_Y1, openings=o["party"])
    sh.wall(b_x0, B_Y0, B_X1, B_Y0 + WT, openings=o["b_south"])
    sh.wall(B_X1 - WT, B_Y0, B_X1, B_Y1)
    sh.wall(b_x0, B_Y1 - WT, B_X1, B_Y1)


def core_walls(sh):
    """Stair enclosure and light court walls - identical on every floor."""
    sh.wall(ST_WALL_X, ST_Y0, ST_X0, CT_Y1, openings=[(15.30, 16.70)])
    sh.wall(ST_WALL_X, CT_Y0 - PT, 17.85, CT_Y0, openings=[(16.00, 17.20)])


def core_openings(sh):
    sh.window(15.30, 16.70, ST_WALL_X, ST_X0, "v")
    sh.window(16.00, 17.20, CT_Y0 - PT, CT_Y0, "h")
    sh.window(*CT_WIN_B, PARTY_X0, PARTY_X1, "v")


def light_court(sh, floor, size=2.1):
    fx.void_hatch(sh, CT_X0, CT_Y0, CT_X1 - CT_X0, CT_Y1 - CT_Y0)
    ground = floor == 0
    sh.room(CT_X0, CT_Y0, CT_X1 - CT_X0, CT_Y1 - CT_Y0,
            "Light Court" if ground else "Void over Court",
            area=6.6 if ground else None,
            sub="open to sky" if ground else "open to sky below",
            size=size, schedule=ground, show_area=ground)


def parapet(sh, x0, y0, x1, y1, openings=()):
    sh.wall(x0, y0, x1, y1, openings=openings, fill=PARAPET_FILL)


def arch_note(sh, a, b, face, axis="h", side=1):
    """Dashed semicircular arch head over an opening.

    `face` is the wall face the arch springs from and `side` is the
    direction it turns into: +1 = north / east, -1 = south / west.
    """
    r = (b - a) / 2.0
    if axis == "h":
        (x0, y0), (x1, y1) = (a, face), (b, face)
        sweep = 1 if side > 0 else 0
    else:
        (x0, y0), (x1, y1) = (face, a), (face, b)
        sweep = 0 if side > 0 else 1
    rr = D.mm(r)
    sh.raw(f'<path d="M {D.X(x0):.3f} {D.Y(y0):.3f} A {rr:.3f} {rr:.3f} '
           f'0 0 {sweep} {D.X(x1):.3f} {D.Y(y1):.3f}" fill="none" '
           f'stroke="{GREY}" stroke-width="{LW_HIDDEN}" '
           f'stroke-dasharray="1.8 1.2"/>')


OPENINGS = {
    0: dict(a_south=[WIN_A_1, WIN_A_2, DOOR_ENTRY],
            b_south=[WIN_B_1, WIN_B_2],
            party=[(6.30, 7.20), (11.00, 11.90), CT_WIN_B]),
    1: dict(a_south=[(12.00, 13.60), (14.00, 15.40), (16.10, 17.50)],
            b_south=[(18.60, 20.10), (20.90, 22.40)],
            party=[(11.40, 12.30), CT_WIN_B]),
    2: dict(a_south=[(12.00, 13.60), (14.00, 15.40), (16.10, 17.50)],
            b_south=[(18.60, 20.10), (20.90, 22.40)],
            party=[(8.00, 9.20), (11.40, 12.30), CT_WIN_B]),
}


# ===========================================================================
# A-000  SITE PLAN
# ===========================================================================
def sheet_site():
    D.set_scale(75, *SITE_ORIGIN)
    sh = Sheet("A-000", "Site Plan", "+0.00", "1:75 @ A1")
    F.border(sh)
    neighbours(sh)
    street(sh)

    walk_y0, walk_y1 = 1.60, 3.40
    fx.paving(sh, 0.30, walk_y0, 16.30, walk_y1 - walk_y0, pitch=0.9)
    sh.rect(0.30, walk_y0, 16.30, walk_y1 - walk_y0, sw=LW_SECONDARY,
            stroke=GREY)
    fx.grass(sh, 0.30, 0.35, 9.60, 1.15)
    fx.grass(sh, 0.30, 3.55, 16.30, 1.30)
    fx.planter(sh, 13.90, 0.35, 4.00, 1.15)
    for tx in (2.3, 4.8, 7.3):
        fx.tree(sh, tx, 4.20, 0.80)
    for tx in (1.7, 3.6):
        fx.tree(sh, tx, 0.95, 0.65)

    fx.pergola(sh, 5.20, 1.30, 4.00, 2.40, pitch=0.5)
    sh.tag(7.20, 3.85, "TIMBER PERGOLA OVER WALKWAY", size=2.0, color=GREY)

    fx.paving(sh, 10.10, 0.35, 3.30, 1.15, pitch=0.75, color="#dadada")
    sh.rect(10.10, 0.35, 3.30, 1.15, sw=LW_SECONDARY, stroke=GREY)
    fx.counter(sh, 10.35, 0.50, 2.20, 0.65)
    sh.tag(11.75, 1.28, "BARBECUE", size=2.0, color=GREY)

    fx.steps(sh, DOOR_ENTRY[0] - 0.35, 4.05, 1.80, 0.95, n=3)
    fx.paving(sh, 18.15, 0.40, 4.55, 4.30, pitch=0.9, color="#dadada")
    sh.rect(18.15, 0.40, 4.55, 4.30, sw=LW_SECONDARY, stroke=GREY)
    fx.table(sh, 19.45, 2.20, 1.50, 0.90, seats_n=3, seats_s=3)
    sh.tag(20.42, 0.85, "OUTDOOR DINING", size=2.0, color=GREY)
    fx.pergola(sh, 18.40, 1.70, 4.05, 2.30, pitch=0.55)

    sh.arc(0.30, 1.40, 2.40, 0, 78, sw=LW_THIN, color=GREY)
    sh.line(0.30, 1.40, 2.70, 1.40, w=LW_FIXTURE, color=INK)
    sh.tag(1.9, 5.35, "MAIN GATE", size=2.2, color=INK)

    shell(sh, 0)
    sh.rect(a_x0, a_y0, a_x1 - a_x0, a_y1 - a_y0, fill="#f1f1f1",
            stroke="none", sw=0)
    sh.rect(b_x0, b_y0, b_x1 - b_x0, b_y1 - b_y0, fill="#f1f1f1",
            stroke="none", sw=0)
    light_court(sh, 0, size=1.9)
    sh.room(a_x0, 7.0, 3.9, 4.0, "Block A — front", area=None,
            sub="6.50 × 12.50 m · three storeys", size=2.9,
            schedule=False, show_area=False, at=(14.30, 9.60))
    sh.room(b_x0, 7.0, 4.55, 4.0, "Block B — rear", area=None,
            sub="5.00 × 13.00 m · three storeys", size=2.9,
            schedule=False, show_area=False, at=(20.42, 9.60))
    sh.level_tag(12.9, 6.10, "FFL +0.00")
    sh.level_tag(2.6, 2.05, "GARDEN −0.45")

    boundary(sh)
    sh.tag(7.6, 2.55, "ENTRANCE GARDEN CORRIDOR   23.00 × 5.00 m",
           size=2.3, color=INK)

    sh.dim_h(0, 23.0, -4.8, "23.00", ext_from=0.0)
    sh.dim_h(0, 11.5, -6.6, "11.50")
    sh.dim_h(11.5, 18.0, -6.6, "6.50")
    sh.dim_h(18.0, 23.0, -6.6, "5.00")
    sh.dim_v(0, 5.0, -1.8, "5.00", ext_from=0.0)
    sh.dim_v(5.0, 17.5, -1.8, "12.50")
    sh.dim_v(0, 18.0, -3.6, "18.00")
    sh.dim_v(5.0, 18.0, 24.5, "13.00", ext_from=23.0)

    F.heading(sh)
    y = F.legend(sh, 52)
    sh.schedule = [("Garden corridor  23.00 × 5.00", 115.00),
                   ("Block A footprint  6.50 × 12.50", 81.25),
                   ("Block B footprint  5.00 × 13.00", 65.00)]
    y = F.schedule(sh, y + 8, extra=[
        ("Built footprint", "146.3 m²"),
        ("Site coverage", "56.0 %"),
        ("Gross internal area, three storeys", "258.0 m²")])
    F.notes(sh, y + 6, [
        "Site boundaries and the 23.00 × 5.00 m garden corridor are "
        "taken from the client's survey sketch. All boundary dimensions to "
        "be confirmed by measured survey before any work starts on site.",
        "Blocks A and B sit hard against the north, east and west "
        "boundaries. The south elevation onto the garden is the only open "
        "facade, so a 2.65 × 2.48 m light court is cut through all "
        "three storeys to daylight the centre of the plan.",
        "The garden falls 0.45 m from the house threshold to the gate. "
        "Surface water to a soakaway within the planted border.",
        "No part of the new work oversails or undermines the adjoining "
        "plots; party wall notices to be served on the north, east and "
        "west owners before excavation.",
    ])
    F.compass_and_scale(sh, x=502.0, y=452.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-100  GROUND FLOOR
# ===========================================================================
def sheet_ground():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-100", "Ground Floor Plan", "+0.00", "1:50 @ A1")
    F.border(sh)

    fx.paving(sh, 11.50, 2.60, 11.50, 2.40, pitch=0.9, color="#e8e8e8")
    fx.steps(sh, DOOR_ENTRY[0] - 0.35, 4.05, 1.80, 0.95, n=3)
    sh.tag(13.6, 3.35, "ENTRANCE GARDEN — SEE A-000", size=2.1,
           color=GREY)
    sh.tag(20.4, 3.35, "PRIVATE PATIO", size=2.1, color=GREY)
    for bx in (11.50, 23.00):
        sh.line(bx, 5.00, bx, 2.60, w=LW_THIN, color=LIGHT,
                dash="6 1.5 1.2 1.5")

    shell(sh, 0)
    sh.wall(15.70, a_y0, 15.82, 9.72, openings=[(5.90, 7.40)])
    sh.wall(15.82, 7.80, 17.85, 7.92, openings=[(16.20, 17.00)])
    sh.wall(15.70, 9.60, 17.85, 9.72)
    sh.wall(a_x0, ST_Y0, ST_WALL_X, ST_Y0 + PT, openings=[(12.40, 14.40)])
    core_walls(sh)
    sh.wall(b_x0, 10.60, b_x1, 10.72, openings=[(19.20, 20.10)])
    sh.wall(b_x0, 12.00, b_x1, 12.12, openings=[(18.60, 19.40),
                                                (21.10, 21.90)])
    sh.wall(20.25, 12.12, 20.37, 14.08)
    sh.wall(b_x0, 14.08, b_x1, 14.20, openings=[(19.10, 20.00)])

    for a, b in (WIN_A_1, WIN_A_2):
        sh.window(a, b, A_Y0, A_Y0 + WT, "h")
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    sh.door(*DOOR_ENTRY, A_Y0, A_Y0 + WT, "h", hinge="lo", swing="up")
    arch_note(sh, *DOOR_ENTRY, A_Y0 + WT, side=1)
    for a, b in (WIN_B_1, WIN_B_2):
        sh.window(a, b, B_Y0, B_Y0 + WT, "h")
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    sh.door(6.30, 7.20, PARTY_X0, PARTY_X1, "v", hinge="lo", swing="right")
    sh.door(11.00, 11.90, PARTY_X0, PARTY_X1, "v", hinge="hi", swing="right")
    core_openings(sh)
    sh.door(5.90, 7.40, 15.70, 15.82, "v", leaf=False)
    arch_note(sh, 5.90, 7.40, 15.70, axis="v", side=-1)
    sh.door(16.20, 17.00, 7.80, 7.92, "h", hinge="lo", swing="up")
    sh.door(12.40, 14.40, ST_Y0, ST_Y0 + PT, "h", leaf=False)
    arch_note(sh, 12.40, 14.40, ST_Y0 + PT, side=1)
    sh.door(19.20, 20.10, 10.60, 10.72, "h", hinge="lo", swing="up")
    sh.door(18.60, 19.40, 12.00, 12.12, "h", hinge="lo", swing="up")
    sh.door(21.10, 21.90, 12.00, 12.12, "h", hinge="hi", swing="down")
    sh.door(19.10, 20.00, 14.08, 14.20, "h", hinge="lo", swing="up")

    # living
    fx.sofa(sh, 11.95, 6.70, 0.90, 2.30, facing="e")
    fx.sofa(sh, 13.30, 9.30, 2.30, 0.90, facing="s")
    sh.rect(12.95, 7.65, 1.30, 0.70, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    fx.tv(sh, 15.52, 7.60, 1.40, axis="v")
    # foyer + wc
    fx.wc(sh, 17.85, 8.85, facing="w")
    fx.basin(sh, 16.30, 9.60, facing="s")
    # dining + kitchen
    fx.table(sh, 12.59, 11.95, 1.70, 1.00, seats_n=3, seats_s=3)
    fx.counter(sh, a_x0, 16.55, 2.40, 0.65)
    fx.hob(sh, 12.25, 16.60)
    fx.sink(sh, 13.35, 16.62)
    fx.fridge(sh, 14.25, 16.50)
    fx.counter(sh, 12.60, 14.60, 2.40, 0.65)
    for sx in (13.10, 13.80, 14.50):
        sh.circle(sx, 14.15, 0.22, stroke=GREY, sw=LW_FIXTURE)
    sh.tag(13.80, 13.60, "BREAKFAST BAR", size=1.8, color=GREY)
    fx.stair(sh, (ST_X0, ST_Y0, ST_X1, ST_Y1), direction="up",
             floor_to_floor=FLOOR_TO_FLOOR)
    # tv lounge
    fx.tv(sh, 18.17, 8.30, 1.40, axis="v")
    fx.sofa(sh, 21.30, 8.20, 0.90, 2.00, facing="w")
    sh.rect(19.95, 8.75, 1.10, 0.65, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    # guest bath + laundry
    fx.shower(sh, 18.25, 12.95, 0.95, 0.95)
    fx.wc(sh, b_x0, 12.55, facing="e")
    fx.basin(sh, 19.75, 14.08, facing="s")
    for wx in (20.50, 21.25):
        sh.rect(wx, 12.30, 0.65, 0.65, sw=LW_FIXTURE, stroke=GREY)
        sh.circle(wx + 0.325, 12.625, 0.20, stroke=GREY, sw=LW_FIXTURE)
    fx.counter(sh, 22.05, 12.30, 0.60, 1.55)
    # guest bedroom
    fx.bed(sh, 19.55, 15.70, 1.60, 2.00, head="n")
    for bx in (19.05, 21.20):
        sh.rect(bx, 17.20, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, 22.15, 14.35, 0.55, 3.20, axis="v")

    sh.room(a_x0, a_y0, 3.90, 5.30, "Living & Reception", area=22.8,
            size=2.7, at=(13.85, 6.65))
    sh.room(15.82, a_y0, 2.03, 2.50, "Entrance Foyer", area=5.4, size=2.1,
            at=(16.85, 7.30))
    sh.room(15.82, 7.92, 2.03, 1.68, "Guest WC", area=3.9, size=2.0,
            at=(16.45, 8.65))
    sh.room(a_x0, 10.72, 3.28, 3.88, "Dining", area=12.7, size=2.5,
            at=(13.44, 14.05))
    sh.room(a_x0, 14.60, 3.28, 2.60, "Kitchen", area=8.5, size=2.5,
            sub="open plan", at=(13.40, 15.85))
    sh.room(ST_X0, ST_Y0, 2.65, 4.00, "Stair Hall", area=10.6, size=2.1,
            show_area=False, at=(16.30, 10.92))
    light_court(sh, 0)
    sh.room(b_x0, b_y0, 4.55, 5.30, "TV Lounge", area=24.1, size=2.6,
            at=(20.30, 6.45))
    sh.room(b_x0, 10.72, 4.55, 1.28, "Corridor", area=5.8, size=1.9,
            at=(20.60, 11.36))
    sh.room(b_x0, 12.12, 2.10, 1.96, "Guest Bath", area=4.1, size=1.9,
            at=(19.62, 12.60))
    sh.room(20.37, 12.12, 2.33, 1.96, "Laundry & Store", area=4.6, size=1.9,
            at=(21.35, 13.60))
    sh.room(b_x0, 14.20, 4.55, 3.50, "Guest Bedroom", area=15.9, size=2.5,
            at=(20.80, 15.05))

    sh.dim_h(A_X0, B_X1, 1.0, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 2.2, "6.50")
    sh.dim_h(A_X1, B_X1, 2.2, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.2, "12.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.4, "13.00", ext_from=B_X1)
    sh.dim_v(A_Y0, ST_Y0, 25.6, "5.60")
    sh.dim_v(ST_Y0, ST_Y1, 25.6, "4.00")
    sh.dim_v(ST_Y1, B_Y1, 25.6, "3.40")
    sh.dim_h(b_x0, 22.15, 18.6, "4.00")
    sh.dim_v(14.20, 17.70, 23.5, "3.50")
    sh.level_tag(12.05, 10.15, "FFL +0.00")
    sh.level_tag(20.75, 7.45, "FFL +0.00")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[0]} m²"),
        ("Slab to slab", "3.00 m")])
    F.notes(sh, y + 6, [
        "Living, dining and kitchen read as one space, linked by 2.00 m and "
        "1.50 m wide arched openings; arch heads are shown dashed.",
        "South elevation glazing to the living room and TV lounge is arched "
        "and faces the 23 m garden corridor.",
        "Guest bath and laundry are internal rooms: mechanical extract to "
        "the light court at six air changes per hour.",
        "The guest bedroom takes daylight from the light court through the "
        "party wall, and is 4.00 × 3.50 m clear of the fitted wardrobe.",
        "Gross internal area excludes the light court.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-101  FIRST FLOOR
# ===========================================================================
def sheet_first():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-101", "First Floor Plan", "+3.00", "1:50 @ A1")
    F.border(sh)
    shell(sh, 1)
    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=OPENINGS[1]["a_south"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=OPENINGS[1]["b_south"])
    for a, b in OPENINGS[1]["a_south"]:
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in OPENINGS[1]["b_south"]:
        arch_note(sh, a, b, B_Y0 + WT, side=1)

    sh.wall(a_x0, 9.00, ST_WALL_X, 9.12, openings=[(12.20, 13.60)])
    sh.wall(ST_WALL_X, 8.20, 17.85, 8.32, openings=[(16.20, 17.20)])
    sh.wall(ST_WALL_X, 8.32, ST_X0, ST_Y1, openings=[(11.20, 12.10)])
    sh.wall(ST_X0, ST_Y0, 17.85, ST_Y0 + PT, openings=[(16.30, 17.10)])
    core_walls(sh)
    sh.wall(a_x0, 13.60, ST_WALL_X, 13.72)
    sh.wall(ST_WALL_X, 13.72, ST_X0, CT_Y1, openings=[(13.85, 14.55)])
    sh.wall(b_x0, 6.90, b_x1, 7.02, openings=[(19.40, 20.90),
                                              (21.50, 22.40)])
    sh.wall(b_x0, 11.20, b_x1, 11.32, openings=[(21.30, 22.20)])
    sh.wall(b_x0, 12.72, b_x1, 12.84, openings=[(18.60, 19.40),
                                                (21.20, 22.00)])
    sh.wall(20.30, 12.84, 20.42, b_y1, openings=[(16.20, 17.00)])
    sh.wall(20.30, 15.60, b_x1, 15.72)

    sh.door(11.40, 12.30, PARTY_X0, PARTY_X1, "v", hinge="lo", swing="right")
    core_openings(sh)
    sh.window(12.20, 13.60, 9.00, 9.12, "h")
    arch_note(sh, 12.20, 13.60, 9.12, side=1)
    sh.window(19.40, 20.90, 6.90, 7.02, "h")
    sh.window(21.50, 22.40, 6.90, 7.02, "h")
    sh.window(16.20, 17.20, 8.20, 8.32, "h")
    sh.door(11.20, 12.10, ST_WALL_X, ST_X0, "v", hinge="lo", swing="left")
    sh.door(16.30, 17.10, ST_Y0, ST_Y0 + PT, "h", hinge="lo", swing="down")
    sh.door(13.85, 14.55, ST_WALL_X, ST_X0, "v", hinge="lo", swing="left")
    sh.door(21.30, 22.20, 11.20, 11.32, "h", hinge="hi", swing="down")
    sh.door(18.60, 19.40, 12.72, 12.84, "h", hinge="lo", swing="down")
    sh.door(21.20, 22.00, 12.72, 12.84, "h", hinge="hi", swing="down")
    sh.door(16.20, 17.00, 20.30, 20.42, "v", hinge="lo", swing="right")

    fx.pergola(sh, 12.05, 5.55, 2.70, 2.60, pitch=0.55)
    fx.table(sh, 13.25, 6.15, 1.30, 0.85, seats_n=2, seats_s=2)
    for px, py, pw, pd in ((11.90, 8.30, 0.90, 0.55), (14.80, 5.50, 0.90, 0.55)):
        fx.planter(sh, px, py, pw, pd)
    fx.bed(sh, 12.40, 11.55, 1.60, 2.00, head="n")
    for bx in (11.90, 14.05):
        sh.rect(bx, 13.05, 0.45, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, a_x0, 9.35, 0.60, 1.60, axis="v")
    fx.bathtub(sh, 15.35, 8.45, 1.70, 0.75)
    fx.wc(sh, 17.85, 9.95, facing="w")
    fx.basin(sh, 16.05, 10.60, facing="s")
    fx.stair(sh, (ST_X0, ST_Y0, ST_X1, ST_Y1), direction="both",
             floor_to_floor=FLOOR_TO_FLOOR)
    fx.counter(sh, a_x0, 16.45, 1.30, 0.70)
    fx.table(sh, 13.20, 15.30, 1.10, 0.65, seats_s=2)
    fx.bed(sh, 18.90, 9.00, 1.80, 2.10, head="n")
    for bx in (18.35, 20.75):
        sh.rect(bx, 10.55, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    for cx in (20.30, 21.10):
        sh.rect(cx, 5.60, 0.50, 0.50, rx=D.mm(0.06), sw=LW_FIXTURE,
                stroke=GREY)
    sh.circle(20.75, 6.40, 0.34, stroke=GREY, sw=LW_FIXTURE)
    fx.wardrobe(sh, b_x0, 12.95, 0.60, 4.55, axis="v")
    fx.wardrobe(sh, 19.70, 12.95, 0.60, 3.05, axis="v")
    fx.bathtub(sh, 20.60, 12.95, 1.70, 0.75)
    fx.shower(sh, 20.55, 14.45, 0.95, 0.95)
    fx.wc(sh, 22.70, 13.95, facing="w")
    fx.basin(sh, 21.95, 15.60, facing="s")
    sh.rect(21.30, 16.00, 1.35, 0.50, sw=LW_FIXTURE, stroke=GREY)

    sh.room(a_x0, a_y0, 3.28, 3.70, "Front Terrace", area=19.8, size=2.6,
            sub="arched brick openings", at=(16.40, 6.60))
    sh.room(a_x0, 9.12, 3.28, 4.48, "Bedroom 2", area=14.7, size=2.6,
            sub="family / children", at=(13.44, 10.40))
    sh.room(ST_X0, 8.32, 2.65, 2.28, "Family Bath", area=6.0, size=2.0,
            at=(16.55, 9.55))
    sh.room(ST_X0, ST_Y0, 2.65, 4.00, "Landing", area=10.6, size=2.1,
            show_area=False, at=(16.52, 10.92))
    sh.room(a_x0, 13.72, 3.28, 3.48, "Study / Nook", area=11.4, size=2.3,
            at=(13.40, 14.35))
    light_court(sh, 1)
    sh.room(b_x0, b_y0, 4.55, 1.60, "Balcony", area=7.3, size=2.1,
            at=(19.15, 6.10))
    sh.room(b_x0, 7.02, 4.55, 4.18, "Master Bedroom", area=19.0, size=2.6,
            at=(21.30, 8.05))
    sh.room(b_x0, 11.32, 4.55, 1.40, "Suite Lobby", area=6.4, size=2.0,
            at=(20.35, 11.72))
    sh.room(b_x0, 12.84, 2.15, 4.86, "Walk-in Dressing", area=10.4, size=2.1,
            at=(19.20, 15.60))
    sh.room(20.42, 12.84, 2.28, 2.76, "Ensuite", area=6.3, size=2.1,
            at=(21.55, 13.85))
    sh.room(20.42, 15.72, 2.28, 1.98, "Linen", area=4.5, size=1.8,
            at=(21.55, 17.25))

    sh.dim_h(A_X0, B_X1, 3.4, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 4.6, "6.50")
    sh.dim_h(A_X1, B_X1, 4.6, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.2, "12.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.4, "13.00", ext_from=B_X1)
    sh.dim_v(B_Y0, 6.90, 25.6, "1.90")
    sh.dim_v(6.90, 11.20, 25.6, "4.30")
    sh.dim_v(11.20, B_Y1, 25.6, "6.80")
    sh.dim_h(a_x0, ST_WALL_X, 18.6, "3.28")
    sh.level_tag(16.30, 7.60, "TERRACE +2.97")
    sh.level_tag(21.85, 5.75, "BALCONY +2.97")

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[1]} m²"),
        ("External terrace and balcony", "27.1 m²")])
    F.notes(sh, y + 6, [
        "The front terrace and the master balcony are enclosed by a 1.10 m "
        "high parapet pierced by traditional arched brick openings; arch "
        "heads are shown dashed.",
        "Terrace finish is 30 mm below internal floor level, falling 1:80 "
        "to outlets at the parapet.",
        "The master suite occupies block B with the bedroom on the garden "
        "side; the dressing room is daylit from the light court.",
        "All bedroom doors give 900 mm clear opening, and the landing "
        "holds a 1.10 m clear route to the stair.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
# A-102  SECOND FLOOR / ROOF
# ===========================================================================
def sheet_second():
    D.set_scale(50, *PLAN_ORIGIN)
    sh = Sheet("A-102", "Second Floor & Roof Plan", "+6.00", "1:50 @ A1")
    F.border(sh)

    parapet(sh, A_X0, A_Y0, 17.85, A_Y0 + WT, openings=OPENINGS[2]["a_south"])
    parapet(sh, A_X0, A_Y0, A_X0 + PARAPET, A_Y1)
    parapet(sh, A_X0, A_Y1 - PARAPET, 17.85, A_Y1)
    sh.wall(PARTY_X0, A_Y0, PARTY_X1, B_Y1, openings=OPENINGS[2]["party"])
    parapet(sh, b_x0, B_Y0, B_X1, B_Y0 + WT, openings=OPENINGS[2]["b_south"])
    parapet(sh, B_X1 - PARAPET, B_Y0, B_X1, 10.72)
    sh.wall(B_X1 - WT, 10.60, B_X1, B_Y1)
    sh.wall(b_x0, B_Y1 - WT, B_X1, B_Y1)
    for a, b in OPENINGS[2]["a_south"]:
        arch_note(sh, a, b, A_Y0 + WT, side=1)
    for a, b in OPENINGS[2]["b_south"]:
        arch_note(sh, a, b, B_Y0 + WT, side=1)
    arch_note(sh, 8.00, 9.20, PARTY_X0, axis="v", side=-1)

    core_walls(sh)
    sh.wall(ST_X0, ST_Y0, 17.85, ST_Y0 + PT, openings=[(16.30, 17.10)])
    sh.wall(b_x0, 10.60, b_x1, 10.72, openings=[(18.60, 19.50)])
    sh.wall(20.30, 10.72, 20.42, 13.00, openings=[(11.60, 12.40)])
    sh.wall(b_x0, 13.00, b_x1, 13.12, openings=[(18.70, 19.60)])

    sh.door(16.30, 17.10, ST_Y0, ST_Y0 + PT, "h", hinge="lo", swing="down")
    sh.door(11.40, 12.30, PARTY_X0, PARTY_X1, "v", hinge="lo", swing="right")
    core_openings(sh)
    sh.door(18.60, 19.50, 10.60, 10.72, "h", hinge="lo", swing="down")
    sh.door(18.70, 19.60, 13.00, 13.12, "h", hinge="lo", swing="up")
    sh.door(11.60, 12.40, 20.30, 20.42, "v", hinge="lo", swing="right")

    fx.pergola(sh, 11.90, 5.45, 3.10, 4.10, pitch=0.55)
    fx.sofa(sh, 12.05, 5.75, 2.50, 0.85, facing="n")
    fx.sofa(sh, 11.95, 7.15, 0.85, 1.90, facing="e")
    sh.rect(13.30, 7.25, 1.15, 0.65, rx=D.mm(0.1), sw=LW_FIXTURE, stroke=GREY)
    sh.tag(13.45, 10.05, "OUTDOOR LOUNGE UNDER PERGOLA", size=2.0, color=GREY)
    fx.pergola(sh, 18.40, 5.60, 4.00, 3.00, pitch=0.55)
    fx.table(sh, 19.55, 6.45, 1.70, 1.00, seats_n=3, seats_s=3)
    for px, py, pw, pd in ((11.85, 11.10, 0.55, 2.40),
                           (11.85, 14.30, 0.55, 2.70),
                           (12.80, 16.65, 2.00, 0.50),
                           (22.25, 5.60, 0.45, 2.30)):
        fx.planter(sh, px, py, pw, pd)
    fx.stair(sh, (ST_X0, ST_Y0, ST_X1, ST_Y1), direction="dn",
             floor_to_floor=FLOOR_TO_FLOOR)

    fx.counter(sh, b_x0, 10.72, 2.15, 0.65)
    fx.sink(sh, 18.45, 10.80)
    sh.rect(19.45, 10.80, 0.55, 0.50, sw=LW_FIXTURE, stroke=GREY)
    fx.fridge(sh, 19.50, 12.25, 0.65, 0.65)
    fx.shower(sh, 21.70, 11.95, 0.95, 0.95)
    fx.wc(sh, 21.00, 10.72, facing="n")
    fx.basin(sh, 22.70, 11.20, w=0.55, d=0.45, facing="w")
    fx.bed(sh, 19.65, 15.55, 1.80, 2.10, head="n")
    for bx in (19.05, 21.55):
        sh.rect(bx, 17.15, 0.50, 0.45, sw=LW_FIXTURE, stroke=GREY)
    fx.wardrobe(sh, b_x0, 14.10, 0.60, 2.40, axis="v")
    fx.sofa(sh, 21.50, 13.30, 1.15, 0.75, facing="n")

    sh.room(a_x0, 10.60, 3.28, 4.00, "Roof Terrace", area=54.0, size=3.2,
            sub="open air · 1.10 m parapet", at=(13.45, 12.40))
    sh.room(ST_X0, ST_Y0, 2.65, 4.00, "Stair Head", area=10.6, size=2.1,
            show_area=False, at=(16.52, 10.92))
    light_court(sh, 2)
    sh.room(b_x0, b_y0, 4.55, 5.30, "Roof Terrace", area=24.1, size=2.6, sched_name="Roof terrace, block B",
            at=(20.42, 9.30))
    sh.room(b_x0, 10.72, 2.15, 2.28, "Kitchenette", area=4.9, size=2.0,
            sub="coffee bar", at=(19.72, 11.55))
    sh.room(20.42, 10.72, 2.28, 2.28, "Shower Room", area=5.2, size=1.8,
            at=(21.02, 12.70))
    sh.room(b_x0, 13.12, 4.55, 4.58, "Studio Suite", area=20.8, size=2.6,
            sub="independent guest suite", at=(20.35, 14.45))

    sh.dim_h(A_X0, B_X1, 3.4, "11.50", ext_from=A_Y0)
    sh.dim_h(A_X0, A_X1, 4.6, "6.50")
    sh.dim_h(A_X1, B_X1, 4.6, "5.00")
    sh.dim_v(A_Y0, A_Y1, 10.2, "12.50", ext_from=A_X0)
    sh.dim_v(B_Y0, B_Y1, 24.4, "13.00", ext_from=B_X1)
    sh.dim_v(B_Y0, 10.60, 25.6, "5.60")
    sh.dim_v(10.60, B_Y1, 25.6, "7.40")
    sh.level_tag(13.3, 6.30, "TERRACE +5.97")
    sh.level_tag(19.10, 13.45, "FFL +6.00")
    sh.tag(17.25, 8.60, "ARCHED LINK BETWEEN TERRACES", size=1.7,
           color=GREY, rot=-90)

    F.heading(sh)
    y = F.legend(sh, 52)
    y = F.schedule(sh, y + 8, extra=[
        ("Gross internal area, this floor", f"{GIA[2]} m²"),
        ("Open-air terrace, both blocks", "78.1 m²")])
    F.notes(sh, y + 6, [
        "Block A is given over entirely to an open-air roof terrace at this "
        "level, apart from the stair head and the light court void.",
        "Timber pergolas are set out on a 550 mm rafter pitch over the "
        "lounge and the outdoor table; both are shown dashed as they sit "
        "above the cut plane.",
        "The studio suite is self-contained, with its own shower room and "
        "kitchenette, and is entered from the stair head without crossing "
        "the family floor below.",
        "Roof falls 1:60 to rainwater outlets at the parapet; "
        "waterproofing turned up 150 mm minimum behind the terrace finish.",
    ])
    F.compass_and_scale(sh, x=470.0, y=500.0)
    F.titleblock(sh)
    return sh


# ===========================================================================
def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "drawings")
    os.makedirs(out, exist_ok=True)
    paths = []
    for builder in (sheet_site, sheet_ground, sheet_first, sheet_second):
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
