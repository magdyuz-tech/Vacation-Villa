#!/usr/bin/env python3
"""
axonometric.py - a real 3D view, projected from the geometry.

Not a render.  The building is drawn by transforming the same constants
the plans are drawn from, so the view cannot show a balcony the plans do
not have, a garden the site plan does not have, or a neighbour nobody
surveyed.  An image generator can do all three and did.

Isometric, viewed from the SOUTH-WEST and above, which is the one corner
that shows what matters at once: the street frontage with its cantilever,
the blind west wall, the roof with its pergola, and the entrance garden
standing in front of all of it.

    u = (x - y) cos30
    v =  z + (x + y) sin30

so east runs right, north runs away up-left, and the nearest corner of
the model is the south-west one.  Faces are painted back to front - there
is no z-buffer here, just the order things are drawn in.
"""

import math

import drafting as D
from drafting import INK, GREY, LIGHT, LW_CUT, LW_SECONDARY, LW_THIN
from geometry import *          # noqa: F401,F403  (pure constants)

C30, S30 = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))


def P(x, y, z):
    """A point in the model -> the sheet's (u, v)."""
    return ((x - y) * C30, z + (x + y) * S30)


def quad(sh, a, b, c, d, fill, stroke=INK, sw=LW_THIN):
    sh.poly([P(*a), P(*b), P(*c), P(*d)], fill=fill, stroke=stroke, sw=sw)


def shade(hexc, f):
    """Darken a hex colour by f, so the three visible faces separate."""
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * f)))
                                   for v in (r, g, b))


def box(sh, x0, y0, x1, y1, z0, z1, colour, stroke=INK, sw=LW_THIN):
    """A rectangular solid, its three visible faces shaded apart."""
    quad(sh, (x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1),
         shade(colour, 0.78), stroke, sw)                      # west
    quad(sh, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
         shade(colour, 0.92), stroke, sw)                      # south
    quad(sh, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
         colour, stroke, sw)                                   # top


def balcony(sh, ffl, profile, colour, n=64):
    """One cantilever: the slab soffit, its curved edge band and the glass."""
    xs = [V3_X0 + (V3_X1 - V3_X0) * i / n for i in range(n + 1)]
    edge = [(x, wave_edge(x, profile)) for x in xs]
    top = ffl - 0.03
    # the slab seen from above, between the wall line and the curve
    sh.poly([P(x, V3_Y0, top) for x in xs]
            + [P(x, y, top) for x, y in reversed(edge)],
            fill=shade(colour, 0.97), stroke=INK, sw=LW_THIN)
    # the curved outer edge of the slab, which is what reads as the wave
    sh.poly([P(x, y, top) for x, y in edge]
            + [P(x, y, top - STRUCTURAL_ZONE) for x, y in reversed(edge)],
            fill=shade(colour, 0.70), stroke=INK, sw=LW_SECONDARY)
    # the glass balustrade, set inboard and following the same curve
    inb = [(x, wave_edge(x, profile) + V3_WAVE_BALUSTRADE) for x in xs]
    sh.poly([P(x, y, top) for x, y in inb]
            + [P(x, y, top + 1.10) for x, y in reversed(inb)],
            fill="#dfe6ea", stroke=GREY, sw=LW_THIN)


def villa(sh, scheme_colour, profile):
    """The massing: four storeys, the set-back penthouse, four cantilevers."""
    box(sh, V3_X0, V3_Y0, V3_X1, V3_Y1, 0.0, ROOF_LEVEL, scheme_colour)
    # the floor lines on the two visible faces, so the storeys read
    for lv in (1, 2, 3):
        z = lv * FLOOR_TO_FLOOR
        sh.poly([P(V3_X0, V3_Y1, z), P(V3_X0, V3_Y0, z), P(V3_X1, V3_Y0, z)],
                close=False, stroke=LIGHT, sw=LW_THIN)
    box(sh, V4_X0, V4_Y0, V4_X1, V4_Y1, ROOF_LEVEL, V4_TOP,
        shade(scheme_colour, 1.02))
    # the pergola over the corridor, west of the flat
    px0, py0, px1, py1 = V4_PERGOLA
    for i in range(int((py1 - py0) / 0.55) + 1):
        y = py0 + i * 0.55
        sh.poly([P(px0, y, V4_TOP - 0.35), P(px1, y, V4_TOP - 0.35)],
                close=False, stroke=GREY, sw=LW_THIN)
    for lv in (1, 2, 3, 4):
        balcony(sh, EL_LEVELS[lv], profile, scheme_colour)


def context(sh):
    """Ground, the two surveyed neighbours and the entrance garden."""
    # the plot, flat on the ground
    quad(sh, (0.0, 0.0, GARDEN_LEVEL), (V3_X1 + SETBACK, 0.0, GARDEN_LEVEL),
         (V3_X1 + SETBACK, V3_Y1, GARDEN_LEVEL), (0.0, V3_Y1, GARDEN_LEVEL),
         "#efece5", GREY, LW_THIN)
    # the street
    quad(sh, (-1.5, -3.4, GARDEN_LEVEL), (NBR_E_X1, -3.4, GARDEN_LEVEL),
         (NBR_E_X1, 0.0, GARDEN_LEVEL), (-1.5, 0.0, GARDEN_LEVEL),
         "#e4e4e4", LIGHT, LW_THIN)
    # west: three storeys, blind, standing back behind the garden
    box(sh, 0.0, 5.0, NBR_W_X1, V3_Y1, GARDEN_LEVEL,
        NBR_W_STOREYS * NBR_STOREY_H, "#dedad2", GREY, LW_THIN)
    # east: a single storey in clay brick, 1.00 m away
    box(sh, V3_X1 + SETBACK, V3_Y0, NBR_E_X1, V3_Y1, GARDEN_LEVEL,
        NBR_E_STOREYS * NBR_STOREY_H, "#cfae97", GREY, LW_THIN)
    # the entrance garden: walk, pergola over it, the gate end
    quad(sh, (0.3, 1.55, GARDEN_LEVEL), (V3_X0, 1.55, GARDEN_LEVEL),
         (V3_X0, 3.35, GARDEN_LEVEL), (0.3, 3.35, GARDEN_LEVEL),
         "#dcd6ca", GREY, LW_THIN)
    for i in range(9):
        x = 5.10 + i * 0.50
        sh.poly([P(x, 1.25, 2.35), P(x, 3.60, 2.35)], close=False,
                stroke=GREY, sw=LW_THIN)
    for tx in (2.30, 4.80, 7.30):
        sh.poly([P(tx, 4.20, GARDEN_LEVEL), P(tx, 4.20, 2.60)], close=False,
                stroke=GREY, sw=LW_SECONDARY)


def view(sh, scheme_colour, profile):
    """One complete axonometric, painted back to front."""
    context(sh)
    villa(sh, scheme_colour, profile)
