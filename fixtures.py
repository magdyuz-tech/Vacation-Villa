#!/usr/bin/env python3
"""fixtures.py - furniture, sanitaryware, joinery and sheet furniture symbols."""

import functools
import math
import drafting as D
from drafting import (X, Y, mm, INK, GREY, LIGHT, LW_CUT, LW_SECONDARY,
                      LW_FIXTURE, LW_THIN, LW_HIDDEN, SHEET_W, SHEET_H)

F = dict(sw=LW_FIXTURE, stroke=GREY)


def layer(name):
    """Tag a symbol with the CAD layer it belongs on.

    The SVG backend ignores it; the DXF backend sorts the entities onto that
    layer, so the two outputs stay in step from one set of drawing calls.
    """
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(sh, *a, **k):
            with sh.on(name):
                return fn(sh, *a, **k)
        return wrapper
    return deco


# ---------------------------------------------------------------------------
# sanitaryware
# ---------------------------------------------------------------------------
@layer("A-EQPM")
def wc(sh, x, y, facing="n"):
    """Pan 0.38 x 0.70 with cistern against the wall behind it."""
    w, d = 0.38, 0.56
    if facing in ("n", "s"):
        sgn = 1 if facing == "n" else -1
        sh.rect(x - w / 2, min(y, y + 0.16 * sgn), w, 0.16, **F)
        sh.ellipse(x, y + sgn * (0.16 + d / 2), 0.17, d / 2, stroke=GREY)
    else:
        sgn = 1 if facing == "e" else -1
        sh.rect(min(x, x + 0.16 * sgn), y - w / 2, 0.16, w, **F)
        sh.ellipse(x + sgn * (0.16 + d / 2), y, d / 2, 0.17, stroke=GREY)


@layer("A-EQPM")
def basin(sh, x, y, w=0.60, d=0.48, facing="n"):
    if facing in ("n", "s"):
        y0 = y if facing == "n" else y - d
        sh.rect(x - w / 2, y0, w, d, **F)
        sh.circle(x, y0 + d / 2, 0.055, stroke=GREY, sw=LW_FIXTURE)
    else:
        x0 = x if facing == "e" else x - d
        sh.rect(x0, y - w / 2, d, w, **F)
        sh.circle(x0 + d / 2, y, 0.055, stroke=GREY, sw=LW_FIXTURE)


@layer("A-EQPM")
def bathtub(sh, x, y, w=1.70, d=0.75):
    sh.rect(x, y, w, d, **F)
    sh.rect(x + 0.09, y + 0.09, w - 0.22, d - 0.18, rx=1.4, **F)
    sh.circle(x + w - 0.26, y + d / 2, 0.05, stroke=GREY, sw=LW_FIXTURE)


@layer("A-EQPM")
def shower(sh, x, y, w=0.95, d=0.95):
    sh.rect(x, y, w, d, **F)
    sh.line(x, y, x + w, y + d, w=LW_THIN, color=LIGHT)
    sh.line(x + w, y, x, y + d, w=LW_THIN, color=LIGHT)
    sh.circle(x + w / 2, y + d / 2, 0.06, stroke=GREY, sw=LW_FIXTURE)


# ---------------------------------------------------------------------------
# joinery + furniture
# ---------------------------------------------------------------------------
@layer("A-FURN")
def counter(sh, x, y, w, d, label=None):
    sh.rect(x, y, w, d, **F)


@layer("A-EQPM")
def sink(sh, x, y, w=0.80, d=0.50):
    sh.rect(x, y, w, d, **F)
    sh.rect(x + 0.06, y + 0.07, w / 2 - 0.09, d - 0.14, **F)
    sh.rect(x + w / 2 + 0.03, y + 0.07, w / 2 - 0.09, d - 0.14, **F)


@layer("A-FURN")
def hob(sh, x, y, w=0.60, d=0.52):
    sh.rect(x, y, w, d, **F)
    for dx, dy in ((0.27, 0.35), (0.27, 0.15), (0.45, 0.35), (0.45, 0.15)):
        sh.circle(x + dx - 0.12, y + dy, 0.065, stroke=GREY, sw=LW_FIXTURE)


@layer("A-FURN")
def fridge(sh, x, y, w=0.75, d=0.70):
    sh.rect(x, y, w, d, **F)
    sh.line(x, y + d * 0.55, x + w, y + d * 0.55, w=LW_THIN, color=LIGHT)


@layer("A-FURN")
def bed(sh, x, y, w=1.60, l=2.00, head="n"):
    """(x, y) = south-west corner of the mattress footprint."""
    sh.rect(x, y, w, l, **F)
    if head in ("n", "s"):
        hy = y + l - 0.42 if head == "n" else y + 0.06
        sh.rect(x + 0.08, hy - 0.06, w / 2 - 0.14, 0.36, **F)
        sh.rect(x + w / 2 + 0.06, hy - 0.06, w / 2 - 0.14, 0.36, **F)
        ly = y + l if head == "n" else y
        sh.line(x, ly + (-0.62 if head == "n" else 0.62), x + w,
                ly + (-0.62 if head == "n" else 0.62), w=LW_THIN, color=LIGHT)
    else:
        hx = x + w - 0.42 if head == "e" else x + 0.06
        sh.rect(hx - 0.06, y + 0.08, 0.36, l / 2 - 0.14, **F)
        sh.rect(hx - 0.06, y + l / 2 + 0.06, 0.36, l / 2 - 0.14, **F)


@layer("A-FURN")
def sofa(sh, x, y, w=2.20, d=0.90, facing="n"):
    sh.rect(x, y, w, d, **F)
    if facing == "n":
        sh.rect(x, y, w, 0.22, **F)
    elif facing == "s":
        sh.rect(x, y + d - 0.22, w, 0.22, **F)
    elif facing == "e":
        sh.rect(x, y, 0.22, d, **F)
    else:
        sh.rect(x + w - 0.22, y, 0.22, d, **F)


@layer("A-FURN")
def table(sh, x, y, w, d, seats_n=0, seats_s=0, seats_e=0, seats_w=0, rx=0.2):
    sh.rect(x, y, w, d, rx=mm(rx), **F)
    def chairs(n, ax):
        for i in range(n):
            t = (i + 0.5) / n
            if ax == "n":
                sh.rect(x + t * w - 0.24, y + d + 0.10, 0.48, 0.44, **F)
            elif ax == "s":
                sh.rect(x + t * w - 0.24, y - 0.54, 0.48, 0.44, **F)
            elif ax == "e":
                sh.rect(x + w + 0.10, y + t * d - 0.24, 0.44, 0.48, **F)
            else:
                sh.rect(x - 0.54, y + t * d - 0.24, 0.44, 0.48, **F)
    chairs(seats_n, "n"); chairs(seats_s, "s")
    chairs(seats_e, "e"); chairs(seats_w, "w")


@layer("A-FURN")
def wardrobe(sh, x, y, w, d, axis="h"):
    sh.rect(x, y, w, d, **F)
    n = max(2, int((w if axis == "h" else d) / 0.55))
    for i in range(1, n):
        t = i / n
        if axis == "h":
            sh.line(x + t * w, y, x + t * w, y + d, w=LW_THIN, color=LIGHT)
        else:
            sh.line(x, y + t * d, x + w, y + t * d, w=LW_THIN, color=LIGHT)


@layer("A-FURN")
def tv(sh, x, y, w=1.40, axis="h"):
    if axis == "h":
        sh.rect(x, y, w, 0.16, **F)
    else:
        sh.rect(x, y, 0.16, w, **F)


@layer("L-PLNT")
def planter(sh, x, y, w, d):
    sh.rect(x, y, w, d, sw=LW_SECONDARY, stroke=GREY)
    n = max(1, int(w / 0.9)); m = max(1, int(d / 0.9))
    for i in range(n):
        for j in range(m):
            shrub(sh, x + (i + 0.5) * w / n, y + (j + 0.5) * d / m, 0.32)


@layer("L-PLNT")
def shrub(sh, x, y, r=0.40):
    pts = []
    for k in range(12):
        a = math.radians(k * 30)
        rr = r * (0.78 if k % 2 else 1.0)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    sh.poly(pts, stroke=GREY, sw=LW_THIN)


@layer("L-PLNT")
def tree(sh, x, y, r=1.1):
    shrub(sh, x, y, r)
    sh.circle(x, y, r * 0.30, stroke=LIGHT, sw=LW_THIN)


@layer("L-SITE")
def pergola(sh, x, y, w, d, axis="h", pitch=0.60):
    """Overhead timber pergola: dashed outline + rafters (above cut plane)."""
    sh.rect(x, y, w, d, sw=LW_HIDDEN, stroke=GREY, dash="2.2 1.4")
    n = int((w if axis == "h" else d) / pitch)
    for i in range(1, n):
        t = i / n
        if axis == "h":
            sh.line(x + t * w, y, x + t * w, y + d, w=LW_THIN, color=LIGHT,
                    dash="1.6 1.2")
        else:
            sh.line(x, y + t * d, x + w, y + t * d, w=LW_THIN, color=LIGHT,
                    dash="1.6 1.2")
    for px, py in ((x, y), (x + w, y), (x, y + d), (x + w, y + d)):
        sh.rect(px - 0.09, py - 0.09, 0.18, 0.18, fill=GREY, stroke=GREY,
                sw=LW_FIXTURE)


@layer("L-SITE")
def paving(sh, x, y, w, d, pitch=1.0, color="#cfcfcf"):
    n, m = max(1, round(w / pitch)), max(1, round(d / pitch))
    for i in range(1, n):
        sh.line(x + i * w / n, y, x + i * w / n, y + d, w=LW_THIN, color=color)
    for j in range(1, m):
        sh.line(x, y + j * d / m, x + w, y + j * d / m, w=LW_THIN, color=color)


@layer("L-PLNT")
def grass(sh, x, y, w, d, pitch=1.3):
    n, m = max(1, int(w / pitch)), max(1, int(d / pitch))
    for i in range(n):
        for j in range(m):
            gx = x + (i + 0.5) * w / n
            gy = y + (j + 0.5) * d / m
            for k in (-0.18, 0.0, 0.18):
                sh.line(gx + k, gy - 0.12, gx + k * 1.7, gy + 0.20,
                        w=LW_THIN, color="#c4c4c4")


@layer("A-FLOR-STRS")
def steps(sh, x, y, w, d, n=3, axis="n"):
    for i in range(1, n + 1):
        t = i / n
        if axis in ("n", "s"):
            sh.line(x, y + t * d, x + w, y + t * d, w=LW_SECONDARY, color=GREY)
        else:
            sh.line(x + t * w, y, x + t * w, y + d, w=LW_SECONDARY, color=GREY)
    sh.rect(x, y, w, d, sw=LW_SECONDARY, stroke=GREY)


@layer("A-FLOR-STRS")
def stair(sh, core, direction="up", floor_to_floor=3.00, label=True):
    """U-shaped (dog-leg) stair with a half landing, drawn inside `core`.

    core = (x0, y0, x1, y1) clear internal dimensions of the stair enclosure.
    Flights run north; the landing is at the north end.
    """
    x0, y0, x1, y1 = core
    well = 0.25
    flight_w = (x1 - x0 - well) / 2.0
    risers = max(2, round(floor_to_floor / 0.175))   # ~175 mm target rise
    rise = floor_to_floor / risers
    going = 0.275
    treads = risers // 2                             # per flight
    run = treads * going
    landing_d = 1.30
    start_y = y1 - landing_d - run                # bottom of the up flight

    # up flight (east side), walking north
    fx0 = x0 + flight_w + well
    for i in range(treads + 1):
        yy = start_y + i * going
        sh.line(fx0, yy, x1, yy, w=LW_FIXTURE, color=GREY)
    # half landing
    sh.line(x0, y1 - landing_d, x1, y1 - landing_d, w=LW_FIXTURE, color=GREY)
    # down flight (west side), walking south
    for i in range(treads + 1):
        yy = y1 - landing_d - i * going
        sh.line(x0, yy, x0 + flight_w, yy, w=LW_FIXTURE, color=GREY)
    # stringers + well
    sh.line(fx0, start_y, fx0, y1 - landing_d, w=LW_SECONDARY, color=GREY)
    sh.line(x0 + flight_w, y1 - landing_d - run, x0 + flight_w,
            y1 - landing_d, w=LW_SECONDARY, color=GREY)
    sh.rect(x0 + flight_w, y1 - landing_d - run, well, run, sw=LW_THIN,
            stroke=LIGHT)

    # direction arrows: up the east flight, down the west flight
    ax = fx0 + flight_w / 2
    dx = x0 + flight_w / 2
    if direction in ("up", "both"):
        sh.line(ax, start_y + 0.35, ax, y1 - landing_d - 0.30, w=LW_FIXTURE,
                color=INK)
        hy = y1 - landing_d - 0.30
        sh.poly([(ax, hy + 0.16), (ax - 0.09, hy - 0.10),
                 (ax + 0.09, hy - 0.10)], fill=INK, stroke=INK, sw=LW_THIN)
        if label:
            sh.tag(ax, start_y + 0.22, "UP", size=1.7)
    if direction in ("dn", "both"):
        sh.line(dx, y1 - landing_d - 0.35, dx, start_y + 0.30, w=LW_FIXTURE,
                color=INK)
        hy = start_y + 0.30
        sh.poly([(dx, hy - 0.16), (dx - 0.09, hy + 0.10),
                 (dx + 0.09, hy + 0.10)], fill=INK, stroke=INK, sw=LW_THIN)
        if label:
            sh.tag(dx, start_y + 0.22, "DN", size=1.7)
    sh.tag((x0 + x1) / 2, y1 - landing_d + 0.45,
           f"{risers}R @ {rise * 1000:.0f} × {going * 1000:.0f}",
           size=1.6, color=LIGHT)
    return dict(risers=risers, rise=rise, going=going)


@layer("A-ANNO-PATT")
def void_hatch(sh, x, y, w, d, label="OPEN TO SKY", pitch=1.1):
    """Diagonal hatch used for voids / open-to-sky courts."""
    n = int((w + d) / pitch)
    for i in range(n + 1):
        t = i * pitch
        ax, ay = x + t, y
        bx, by = x, y + t
        if ax > x + w:
            ay = ay + (ax - (x + w)); ax = x + w
        if by > y + d:
            bx = bx + (by - (y + d)); by = y + d
        if ay <= y + d and bx <= x + w:
            sh.line(ax, ay, bx, by, w=LW_THIN, color="#c9c9c9")
    sh.rect(x, y, w, d, sw=LW_SECONDARY, stroke=GREY, dash="2.5 1.5")


# ---------------------------------------------------------------------------
# sheet furniture
# ---------------------------------------------------------------------------
def north_arrow(sh, cx, cy, r=9.0):
    sh.raw(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GREY}" '
           f'stroke-width="{LW_THIN}"/>')
    sh.raw(f'<polygon points="{cx},{cy - r - 2} {cx - r * 0.42},{cy + r * 0.62} '
           f'{cx},{cy + r * 0.18} " fill="{INK}" stroke="{INK}" '
           f'stroke-width="0.2"/>')
    sh.raw(f'<polygon points="{cx},{cy - r - 2} {cx + r * 0.42},{cy + r * 0.62} '
           f'{cx},{cy + r * 0.18} " fill="none" stroke="{INK}" '
           f'stroke-width="0.35"/>')
    sh.text_mm(cx, cy + r + 6.2, "N", size=4.0, weight=700)


def scale_bar(sh, x, y, metres=10, unit_mm=None):
    """Graphic scale drawn true to the sheet's current drawing scale."""
    unit_mm = mm(1.0) if unit_mm is None else unit_mm
    h = 2.0
    for i in range(metres):
        fill = INK if i % 2 == 0 else "#ffffff"
        sh.rect_mm(x + i * unit_mm, y, unit_mm, h, fill=fill, stroke=INK,
                   sw=LW_THIN)
    for i in range(0, metres + 1, 2):
        sh.text_mm(x + i * unit_mm, y + h + 3.2, str(i), size=2.1)
    sh.text_mm(x + metres * unit_mm + 4, y + h + 3.2, "m", size=2.1,
               anchor="start")
    sh.text_mm(x, y - 1.6, f"GRAPHIC SCALE 1:{D.SCALE_DEN:.0f}", size=2.0, anchor="start",
               color=GREY, ls=0.3)
