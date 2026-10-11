#!/usr/bin/env python3
"""
elevations.py - the exterior, drawn from the plans.

Two schemes for the same building.  Nothing here invents geometry: every
opening comes from `geometry.FACADE`, which is a view onto the very lists
the plans draw from, and `checks.elevations_match_the_plans` fails the
build if an elevation ever shows an opening the plan does not have.

The frame is the section's trick turned ninety degrees: the horizontal
axis is the position ALONG the face being drawn, the vertical axis is the
level.  Looking at the south face you stand south of the building looking
north, so east falls to the right and plan x maps straight across; from
the north you look south and it mirrors.  Same for the two long faces,
where the axis is plan y.

One rule governs how things are drawn: anything that is geometry carries a
stroke.  `dxf_backend.rect` deliberately drops a fill with no stroke - pale
washes are presentation, not CAD - so an elevation painted as flat colour
would export as an empty DXF.  Colour is therefore only ever laid behind
or over a stroked outline, which has the happy side effect of keeping the
two schemes honest: strip the colour and the same building is underneath.
"""

import math

import drafting as D
from drafting import (INK, GREY, LIGHT, LW_CUT, LW_SECONDARY, LW_FIXTURE,
                      LW_THIN, LW_HIDDEN)
from geometry import *          # noqa: F401,F403  (pure constants)

FACES = ("s", "e", "n", "w")
FACE_NAME = {"s": "South", "e": "East", "n": "North", "w": "West"}

# the scheme palettes, keyed so a sheet builder passes one letter around
SCHEME = {
    "A": dict(name="Wave", render=A_RENDER, soffit=A_SOFFIT, frame=A_FRAME,
              glass=A_GLASS, profile="serpentine"),
    "B": dict(name="Arcade", render=B_RENDER, soffit=B_TRIM, frame=B_FRAME,
              glass=B_GLASS, profile="bow"),
    # C wears A's skin exactly: the only thing that differs is the curve,
    # which is the point of offering it.
    "C": dict(name="Facet", render=A_RENDER, soffit=A_SOFFIT, frame=A_FRAME,
              glass=A_GLASS, profile="facet"),
}


# ---------------------------------------------------------------------------
# the frame: plan coordinate -> position along the face
# ---------------------------------------------------------------------------
def face_span(face):
    """(lo, hi) of the face in the plan axis it runs along."""
    return (V3_X0, V3_X1) if face in ("s", "n") else (V3_Y0, V3_Y1)


def u(face, v):
    """A plan coordinate mapped onto the elevation's horizontal axis."""
    lo, hi = face_span(face)
    return v if face in ("s", "e") else lo + hi - v


def u_range(face, a, b):
    """An opening's (a, b) mapped onto the face, low end first."""
    p, q = u(face, a), u(face, b)
    return (p, q) if p <= q else (q, p)


def penthouse_span(face):
    """(lo, hi) of the penthouse along the face, and how far it stands back."""
    if face in ("s", "n"):
        lo, hi, back = V4_X0, V4_X1, (0.0 if face == "s" else V3_Y1 - V4_Y1)
    else:
        lo, hi, back = V4_Y0, V4_Y1, (0.0 if face == "e" else V4_X0 - V3_X0)
    p, q = u(face, lo), u(face, hi)
    return (min(p, q), max(p, q), back)


# ---------------------------------------------------------------------------
# the one funnel every opening passes through
# ---------------------------------------------------------------------------
def opening_kind(face, level, a, b):
    """window, door or louvre.

    The one rule.  The elevations classified openings inline and the door
    and window schedule would have had to classify them again; two copies
    of a rule like this diverge on the first exception, and the schedule
    would then measure a building the elevations do not draw.
    """
    if (a, b) in FACADE_DOORS.get((level, face), []):
        return "door"
    # the west wall is blind below the penthouse - louvred ventilation
    # only - so every opening in it is a louvre rather than a window
    if face == "w" and level < 4:
        return "vent"
    return "window"


def opening_head(face, level, kind):
    """(sill, head) of an opening, as heights above its own floor."""
    if kind == "vent":
        return EL_VENT_LO, EL_VENT_HI
    if kind == "door":
        # the front door is not full height; every other door is
        return 0.0, (EL_DOOR_HEAD if (level, face) == (0, "s") else EL_HEAD)
    return EL_SILL, EL_HEAD


def openings():
    """Every opening in the building: (face, level, a, b, kind).

    Read straight off the plans' own lists, in the order the elevations
    draw them.
    """
    out = []
    for level in range(len(EL_LEVELS)):
        for face in FACES:
            for a, b in FACADE[level][face]:
                out.append((face, level, a, b,
                            opening_kind(face, level, a, b)))
    return out


# the mark letters, and the order the schedule reads in
MARK = {"door": "D", "window": "W", "vent": "L"}


def opening_schedule():
    """The door and window schedule: one row per distinct opening type.

    Grouped by what a supplier would quote against - kind, width, height
    and sill - rather than by where each one sits, which is what the
    location columns carry.  Marks are allocated largest first inside each
    kind, so D01 is the biggest door and W01 the biggest window; a type
    added later takes its place in the order rather than being appended as
    an orphan at the end.
    """
    kinds = {}
    for face, level, a, b, kind in openings():
        sill, head = opening_head(face, level, kind)
        key = (kind, round(b - a, 3), round(head - sill, 3), round(sill, 3))
        kinds.setdefault(key, []).append((level, face))

    rows = []
    for kind in ("door", "window", "vent"):
        here = sorted((k for k in kinds if k[0] == kind),
                      key=lambda k: (-k[1], -k[2]))
        for i, key in enumerate(here, 1):
            _k, w, h, sill = key
            where = kinds[key]
            rows.append(dict(
                mark=f"{MARK[kind]}{i:02d}", kind=kind, w=w, h=h, sill=sill,
                faces=sorted({f for _lvl, f in where},
                             key=lambda f: FACES.index(f)),
                levels=[sum(1 for lvl, _f in where if lvl == n)
                        for n in range(len(EL_LEVELS))],
                total=len(where)))
    return rows


def _opening(sh, face, level, a, b, kind, scheme):
    """Draw one opening and record what was drawn.

    Every window, door and louvre goes through here so `checks.py` has a
    single function to patch when it compares the elevations against the
    plans.  `a`, `b` are the PLAN coordinates, not the mapped ones.
    """
    s = SCHEME[scheme]
    ffl = EL_LEVELS[level]
    p, q = u_range(face, a, b)
    sill, head = opening_head(face, level, kind)
    lo, hi = ffl + sill, ffl + head

    if scheme == "B" and kind != "vent":
        _surround(sh, p, q, lo, hi)
    sh.rect(p, lo, q - p, hi - lo, fill=s["glass"], stroke=s["frame"],
            sw=LW_SECONDARY)
    if scheme == "B" and kind != "vent":
        _arch_head(sh, p, q, hi, s)
    if kind == "vent":
        n = max(2, int((hi - lo) / 0.12))
        for i in range(1, n):
            y = lo + i * (hi - lo) / n
            sh.line(p, y, q, y, w=LW_THIN, color=s["frame"])
    else:
        mid = (p + q) / 2.0
        sh.line(mid, lo, mid, hi, w=LW_THIN, color=s["frame"])
    return (face, level, round(a, 2), round(b, 2), kind)


def _surround(sh, p, q, lo, hi, d=None):
    """Scheme B's moulded band around an opening."""
    d = B_SURROUND if d is None else d
    sh.rect(p - d, lo - d, (q - p) + 2 * d, (hi - lo) + 2 * d, fill="none",
            stroke=B_TRIM, sw=LW_FIXTURE)


def _segmental(sh, p, q, z, rise, colour, sw=LW_SECONDARY):
    """A segmental arc of a given rise over the chord p..q at height z.

    NOT a semicircle.  The south bays are 1.60 to 2.30 m wide, so a
    semicircular head would rise up to 1.15 m above a head already at
    2.40 m and burst through the slab at 3.00 m.  A segmental arch sets
    its own radius from the rise the storey can actually spare:

        R = (w/2)^2 + h^2  over  2h,   half-angle  asin((w/2) / R)
    """
    w = (q - p) / 2.0
    if rise <= 0 or w <= 0:
        return
    r = (w * w + rise * rise) / (2.0 * rise)
    half = math.degrees(math.asin(min(1.0, w / r)))
    sh.arc((p + q) / 2.0, z + rise - r, r, 90.0 - half, 90.0 + half,
           sw=sw, color=colour)


def _arch_head(sh, p, q, hi, s):
    """A segmental head with a keystone, scheme B."""
    cx = (p + q) / 2.0
    _segmental(sh, p, q, hi, B_ARCH_RISE, s["frame"], LW_SECONDARY)
    _segmental(sh, p - B_SURROUND, q + B_SURROUND, hi + B_SURROUND,
               B_ARCH_RISE, B_TRIM, LW_FIXTURE)
    sh.rect(cx - 0.11, hi + B_ARCH_RISE - 0.10, 0.22, 0.26, fill=B_TRIM,
            stroke=B_TRIM, sw=LW_FIXTURE)


# ---------------------------------------------------------------------------
# the balcony, which only ever appears on the south face
# ---------------------------------------------------------------------------
def _balcony(sh, scheme):
    """The cantilever at each upper level, seen face on.

    The slab is level, so the curve does not show here - what shows is the
    band of slab edge and the balustrade standing on it.  The curve is on
    the sheet as a plan diagram beside the elevation instead.
    """
    s = SCHEME[scheme]
    lo, hi = face_span("s")
    for level in (1, 2, 3, 4):
        ffl = EL_LEVELS[level]
        nose = A_NOSING if scheme in ("A", "C") else V3_WAVE_FASCIA
        sh.rect(lo, ffl - STRUCTURAL_ZONE, hi - lo,
                STRUCTURAL_ZONE + nose - 0.15, fill=s["soffit"],
                stroke=INK, sw=LW_CUT)
        if scheme in ("A", "C"):
            # the cove light tucked into the underside of the nosing
            sh.rect(lo, ffl - STRUCTURAL_ZONE - A_COVE, hi - lo, A_COVE,
                    fill="#f6e4c0", stroke=GREY, sw=LW_THIN)
            _glass_balustrade(sh, lo, hi, ffl, s)
            for i in range(6):
                px = lo + (hi - lo) * (i + 0.5) / 6.0
                w, h = A_PLANTER
                sh.rect(px - w / 2, ffl, w, h, fill="none", stroke=s["frame"],
                        sw=LW_FIXTURE)
        else:
            _iron_balustrade(sh, lo, hi, ffl)


def _glass_balustrade(sh, lo, hi, ffl, s):
    sh.rect(lo, ffl, hi - lo, BALUSTRADE_H, fill="none", stroke=s["frame"],
            sw=LW_SECONDARY)
    sh.line(lo, ffl + BALUSTRADE_H, hi, ffl + BALUSTRADE_H, w=LW_CUT,
            color=s["frame"])


def _iron_balustrade(sh, lo, hi, ffl):
    """Scheme B: wrought-iron panels between rendered piers."""
    sh.line(lo, ffl + BALUSTRADE_H, hi, ffl + BALUSTRADE_H, w=LW_CUT,
            color=B_FRAME)
    sh.line(lo, ffl + 0.08, hi, ffl + 0.08, w=LW_SECONDARY, color=B_FRAME)
    n = int((hi - lo) / B_BALUSTER)
    for i in range(1, n):
        x = lo + i * (hi - lo) / n
        sh.line(x, ffl + 0.08, x, ffl + BALUSTRADE_H, w=LW_THIN,
                color=B_FRAME)


# ---------------------------------------------------------------------------
# scheme ornament that runs the whole width of a face
# ---------------------------------------------------------------------------
def _cornice(sh, lo, hi, z, depth, colour):
    sh.rect(lo, z, hi - lo, depth, fill=colour, stroke=INK, sw=LW_SECONDARY)


def _wall(sh, lo, hi, z0, z1, s):
    sh.rect(lo, z0, hi - lo, z1 - z0, fill=s["render"], stroke=INK,
            sw=LW_CUT)


# ---------------------------------------------------------------------------
# a whole face
# ---------------------------------------------------------------------------
def elevation(sh, face, scheme, levels=True, ground=1.40):
    """Draw one face of one scheme.  Returns what it drew, for the checker.

    `levels` is off in the street context drawing, where the villa has
    neighbours either side and its level tags would land on them.
    """
    s = SCHEME[scheme]
    lo, hi = face_span(face)
    drawn = []

    # ground, and the wall from it to the roof slab
    # `ground` is how far the ground line runs past the building each
    # side: generous on a sheet carrying one elevation, short on A-401,
    # where three stand side by side and 1.40 m of it ran the east
    # elevation's ground line off the left edge of the paper and 12 mm
    # into the north elevation's.
    sh.line(lo - ground, GARDEN_LEVEL, hi + ground, GARDEN_LEVEL, w=LW_CUT,
            color=INK)
    _wall(sh, lo, hi, GARDEN_LEVEL, ROOF_LEVEL, s)

    # the penthouse, standing on the roof slab; lighter where it stands back
    p0, p1, back = penthouse_span(face)
    sh.rect(lo, ROOF_LEVEL, hi - lo, 1.10, fill=s["render"], stroke=INK,
            sw=LW_SECONDARY)                       # the terrace parapet
    sh.rect(p0, ROOF_LEVEL, p1 - p0, V4_TOP - ROOF_LEVEL, fill=s["render"],
            stroke=INK if back < 0.01 else GREY,
            sw=LW_CUT if back < 0.01 else LW_SECONDARY)
    _cornice(sh, p0, p1, V4_TOP, EL_TOP - V4_TOP,
             B_TRIM if scheme == "B" else s["soffit"])

    # scheme B's trim band at every floor line, under everything else
    if scheme == "B":
        for level in range(1, 5):
            _cornice(sh, lo, hi, EL_LEVELS[level] - STRUCTURAL_ZONE, B_BAND,
                     B_TRIM)
        _cornice(sh, lo, hi, ROOF_LEVEL - B_CORNICE, B_CORNICE, B_TRIM)

    # the openings, level by level, straight out of the plans
    for level in range(len(EL_LEVELS)):
        for a, b in FACADE[level][face]:
            drawn.append(_opening(sh, face, level, a, b,
                                  opening_kind(face, level, a, b), scheme))

    if face == "s":
        if scheme in ("A", "C"):
            # the contemporary reference arches its ground floor too, which
            # is the one thing the two schemes share
            for a, b in FACADE[0]["s"]:
                p, q = u_range("s", a, b)
                _segmental(sh, p, q, EL_HEAD + 0.10, 0.25, s["frame"],
                           LW_FIXTURE)
        _balcony(sh, scheme)
        if scheme == "B":
            _tiled_hood(sh)

    # the set-back note goes on last: the level 4 openings are drawn after
    # the penthouse and would otherwise paint straight over it
    if back >= 0.01:
        sh.tag((p0 + p1) / 2.0, ROOF_LEVEL + 0.52,
               f"PENTHOUSE {back:.2f} m BEHIND", size=1.7, color=GREY)

    if levels:
        for level, z in enumerate(EL_LEVELS):
            sh.level_tag(lo - 1.15, z, f"+{z:.2f}")
        sh.level_tag(lo - 1.15, V4_TOP, f"+{V4_TOP:.2f}")
    return drawn


def _tiled_hood(sh):
    """Scheme B: a tiled hood over the front door, within the cantilever."""
    a, b = V0_DOOR_ENTRY
    p, q = u_range("s", a - 0.35, b + 0.35)
    sh.poly([(p, EL_DOOR_HEAD + 0.10), (q, EL_DOOR_HEAD + 0.10),
             (q - 0.25, EL_DOOR_HEAD + 0.55), (p + 0.25,
                                               EL_DOOR_HEAD + 0.55)],
            fill=B_TRIM, stroke=INK, sw=LW_SECONDARY)


# ---------------------------------------------------------------------------
# the curve, which the elevation cannot show
# ---------------------------------------------------------------------------
def curve_diagram(sh, profile, label=True):
    """The balcony curve in plan, drawn where the elevation cannot show it."""
    pts = wave_points(n=200, profile=profile)
    sh.line(V3_X0, V3_Y0, V3_X1, V3_Y0, w=LW_CUT, color=INK)
    sh.poly(pts, close=False, stroke=INK, sw=LW_SECONDARY)
    sh.poly(wave_points(n=200, offset=V3_WAVE_BALUSTRADE, profile=profile),
            close=False, stroke=GREY, sw=LW_THIN)
    for x in (V3_X0, V3_X1):
        sh.line(x, V3_Y0, x, wave_edge(x, profile), w=LW_SECONDARY, color=INK)
    deep = min(wave_edge(x, profile)
               for x in [V3_X0 + i * (V3_X1 - V3_X0) / 400 for i in range(401)])
    shallow = max(wave_edge(x, profile)
                  for x in [V3_X0 + i * (V3_X1 - V3_X0) / 400
                            for i in range(401)])
    if label:
        sh.tag((V3_X0 + V3_X1) / 2.0, V3_Y0 + 0.55,
               f"{V3_Y0 - deep:.2f} m DEEPEST  ·  {V3_Y0 - shallow:.2f} m "
               f"SHALLOWEST  ·  {wave_area(profile):.1f} m² A FLOOR",
               size=2.0, color=INK)

# ---------------------------------------------------------------------------
# the street in context: the villa between the two houses it actually has
# ---------------------------------------------------------------------------
def context_elevation(sh, scheme):
    """The street frontage with both surveyed neighbours either side.

    The set had no drawing of the villa against its neighbours, which is
    the one thing a client standing on the pavement will see first.  It is
    also the drawing that makes the asymmetry honest: the house is not in
    the middle of its plot, it is hard against the east boundary with a
    single-storey house a metre away and the whole garden on the west.
    """
    s = SCHEME[scheme]
    w_top = NBR_W_STOREYS * NBR_STOREY_H
    e_top = NBR_E_STOREYS * NBR_STOREY_H

    # ground across the whole plot and a little beyond, both neighbours on it
    sh.line(-1.20, GARDEN_LEVEL, NBR_E_X1 + 0.60, GARDEN_LEVEL, w=LW_CUT,
            color=INK)

    # WEST: three storeys, blind, standing back behind our garden - thin
    # line because it is seen beyond, not cut
    sh.rect(0.0, GARDEN_LEVEL, NBR_W_X1, w_top - GARDEN_LEVEL, fill="#f2f2f2",
            stroke=GREY, sw=LW_SECONDARY)
    for i in range(1, NBR_W_STOREYS):
        sh.line(0.0, i * NBR_STOREY_H, NBR_W_X1, i * NBR_STOREY_H,
                w=LW_THIN, color=LIGHT)
    sh.tag(NBR_W_X1 / 2.0, w_top * 0.55,
           f"NEIGHBOUR — {NBR_W_STOREYS} STOREYS", size=2.0, color=GREY)
    sh.tag(NBR_W_X1 / 2.0, w_top * 0.55 - 1.10, "BLIND TO OUR GARDEN",
           size=1.8, color=GREY)

    # our entrance garden in front of it: wall, pergola and trees, all beyond
    sh.rect(0.0, GARDEN_LEVEL, V3_X0 - SETBACK, GARDEN_WALL_H - GARDEN_LEVEL,
            fill="#e8e4dc", stroke=INK, sw=LW_SECONDARY)
    sh.tag((V3_X0 - SETBACK) / 2.0, GARDEN_LEVEL + 0.42,
           "ENTRANCE GARDEN WALL — INDICATIVE", size=1.7, color=GREY)
    with sh.on("A-FLOR-OVER"):
        sh.rect(4.60, 2.35, 4.00, 0.18, sw=LW_HIDDEN, stroke=GREY,
                dash="2.2 1.4")
    for tx in (2.30, 4.80, 7.30):
        sh.line(tx, GARDEN_WALL_H, tx, 3.60, w=LW_THIN, color=LIGHT)
        sh.circle(tx, 4.20, 0.72, stroke=LIGHT, sw=LW_THIN)

    # EAST: a single storey in clay brick, 1.00 m from our wall
    sh.rect(V3_X1 + SETBACK, GARDEN_LEVEL, NBR_E_X1 - V3_X1 - SETBACK,
            e_top - GARDEN_LEVEL, fill="#d8bda8", stroke=INK, sw=LW_SECONDARY)
    for i in range(1, int((e_top - GARDEN_LEVEL) / 0.30)):
        z = GARDEN_LEVEL + i * 0.30
        sh.line(V3_X1 + SETBACK, z, NBR_E_X1, z, w=LW_THIN, color="#b99a84")
    sh.tag((V3_X1 + SETBACK + NBR_E_X1) / 2.0, e_top + 0.70,
           "NEIGHBOUR", size=2.0, color=GREY)
    sh.tag((V3_X1 + SETBACK + NBR_E_X1) / 2.0, e_top - 0.40,
           "SINGLE STOREY", size=1.8, color=GREY)
    sh.tag((V3_X1 + SETBACK + NBR_E_X1) / 2.0, e_top - 1.35,
           "CLAY BRICK", size=1.8, color=GREY)

    # and then our villa, drawn by the same code as its own elevation
    elevation(sh, "s", scheme, levels=False)
    for z in list(EL_LEVELS) + [V4_TOP]:
        sh.level_tag(NBR_E_X1 + 0.30, z, f"+{z:.2f}")

    sh.tag(V3_X1 + SETBACK / 2.0, e_top + 2.40, f"{SETBACK:.2f} m", size=1.7,
           color=INK, rot=-90)
