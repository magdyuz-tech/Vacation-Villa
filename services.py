#!/usr/bin/env python3
"""
services.py - Package D, drawn as coordination and not as design.

Thirty-three sheets, every one class L, and it is worth being plain about
what they can and cannot carry at this stage.

What they carry is space.  Where the wet rooms stack and therefore where
the drainage drops; where a riser is reserved and how big it is; where the
tanks stand; which rooms are habitable and so want conditioning; where a
supply enters.  All of that falls out of the architecture, and all of it
is the thing a services engineer most needs from an architect, because it
is the thing that is expensive to change later.

What they do not carry is a single socket, fitting, diffuser, pipe size,
cable size, load or capacity.  Those are the services engineer's design.
A layout invented here would be thrown away, and in the meantime somebody
might price it.

The one piece of real analysis: the wet rooms are sampled across all five
levels and the region that is wet on three or more is the stack zone.  It
comes out as a single zone in the east strip, wet on every level - which
is what the plans claimed when they said every wet room stacks, now
measured rather than asserted.
"""

import drafting as D
from drafting import (INK, GREY, LIGHT, LW_CUT, LW_SECONDARY, LW_FIXTURE,
                      LW_THIN, LW_HIDDEN)
from geometry import *          # noqa: F401,F403  (pure constants)

STAMP = ("Coordination layout for the services engineer's design — no "
         "fitting, no size, no load. Not for construction.")

WET = ("bath", "ensuite", "wc", "shower", "kitchen", "laundry", "utility",
       "cloak")
CIRCULATION = ("hall", "landing", "lobby", "stair", "corridor", "dressing",
               "store", "linen")
SAMPLE = 0.25           # metres; the grid the stack zone is sampled on
STACK_LEVELS = 3        # wet on this many levels or more makes it a stack


def rooms_by_level():
    """Every room each plan labels, as (x, y, w, h, name)."""
    import plans

    out, real = {}, D.Sheet.room
    for level, build in ((0, plans.sheet_ground), (1, plans.sheet_first),
                         (2, plans.sheet_second), (3, plans.sheet_third),
                         (4, plans.sheet_penthouse)):
        got = []

        def rec(self, x, y, w, h, name, _got=got, **kw):
            _got.append((x, y, w, h, name))
            return real(self, x, y, w, h, name, **kw)

        D.Sheet.room = rec
        try:
            build()
        finally:
            D.Sheet.room = real
        out[level] = got
    return out


def is_wet(name):
    return any(k in name.lower() for k in WET)


def is_habitable(name):
    low = name.lower()
    return not is_wet(name) and not any(k in low for k in CIRCULATION)


def stack_zone(rooms=None):
    """Where the wet rooms stack, measured rather than asserted.

    The plan area is sampled on a 250 mm grid, each cell marked with the
    levels whose wet rooms cover it, and the cells wet on STACK_LEVELS or
    more are the zone.  Sampling rather than intersecting rectangles:
    chaining overlaps transitively swallowed the whole east strip into
    one region the first time, because A overlaps B and B overlaps C
    without A and C sharing a square metre.
    """
    rooms = rooms if rooms is not None else rooms_by_level()
    cells = {}
    for level, here in rooms.items():
        for x, y, w, h, name in here:
            if not is_wet(name):
                continue
            for i in range(int(x / SAMPLE) + 1, int((x + w) / SAMPLE)):
                for j in range(int(y / SAMPLE) + 1, int((y + h) / SAMPLE)):
                    cells.setdefault((i, j), set()).add(level)
    deep = [c for c, lv in cells.items() if len(lv) >= STACK_LEVELS]
    if not deep:
        return None
    xs = [i * SAMPLE for i, _j in deep]
    ys = [j * SAMPLE for _i, j in deep]
    levels = sorted(set().union(*[cells[c] for c in deep]))
    return (min(xs), min(ys), max(xs) + SAMPLE, max(ys) + SAMPLE, levels)


def isolated_wet(rooms=None, zone=None):
    """Wet rooms outside the stack zone, which need their own drop."""
    rooms = rooms if rooms is not None else rooms_by_level()
    zone = zone if zone is not None else stack_zone(rooms)
    out = {}
    for level, here in rooms.items():
        for x, y, w, h, name in here:
            if not is_wet(name):
                continue
            cx, cy = x + w / 2, y + h / 2
            if zone and zone[0] <= cx <= zone[2] and zone[1] <= cy <= zone[3]:
                continue
            out.setdefault(level, []).append((x, y, w, h, name))
    return out


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
def draw_zone(sh, zone, label="SERVICES RISER & STACK ZONE"):
    x0, y0, x1, y1 = zone[:4]
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill="#e8eef2", stroke=INK,
            sw=LW_SECONDARY, dash="5 3")
    sh.tag((x0 + x1) / 2.0, (y0 + y1) / 2.0 + 0.30, label, size=1.8,
           color=INK)
    sh.tag((x0 + x1) / 2.0, (y0 + y1) / 2.0 - 0.60,
           f"{x1 - x0:.2f} × {y1 - y0:.2f} m RESERVED", size=1.6,
           color=GREY)


def draw_isolated(sh, here, text="OWN DROP"):
    for x, y, w, h, _name in here:
        sh.rect(x, y, w, h, fill="none", stroke=INK, sw=LW_SECONDARY,
                dash="3 2")
        sh.tag(x + w / 2, y + h / 2 - 0.45, text, size=1.6, color=INK)


def draw_rooms(sh, here, keep, text):
    n = 0
    for x, y, w, h, name in here:
        if not keep(name):
            continue
        sh.rect(x, y, w, h, fill="#eef2f4", stroke=GREY, sw=LW_THIN,
                dash="2 1.5")
        n += 1
    if n:
        sh.tag(V3_X0 + 1.30, V3_Y1 - 0.80, text, size=1.7, color=GREY)
    return n


def draw_plant(sh):
    qx0, qy0, qx1, qy1 = V4_PLANT
    sh.rect(qx0, qy0, qx1 - qx0, qy1 - qy0, fill="#e0e4e7", stroke=INK,
            sw=LW_SECONDARY)
    sh.tag((qx0 + qx1) / 2.0, (qy0 + qy1) / 2.0, "PLANT / TANKS", size=1.7,
           color=INK)


# --------------------------------------------------------------------------
# the thirty-three
# --------------------------------------------------------------------------
# code, series, title, discipline, what the sheet marks, and the one line
# that says what it is for.
SYSTEMS = (
    ("EL", 100, "Power & Small Power Layout", "Electrical", "habitable",
     "Reserved riser and the distribution route. Outlets, circuits, "
     "board schedules and loads are the electrical engineer's."),
    ("EL", 200, "Lighting & Switching Layout", "Electrical", "all",
     "The ceiling it has to work with, and the soffit level. No fitting "
     "is drawn; see the ARC-400 series for the bulkheads."),
    ("EL", 300, "Low Voltage, Data & Security Layout", "Electrical",
     "habitable",
     "Entry point and riser. Devices, containment and head-end are the "
     "engineer's."),
    ("ME", 100, "HVAC Layout", "Mechanical", "habitable",
     "Which rooms are conditioned, where the plant stands and where the "
     "risers run. Capacities, duct sizes and unit selection are the "
     "mechanical engineer's."),
    ("PL", 100, "Water Supply Layout", "Plumbing", "wet",
     "Tanks over, riser down, wet rooms served. Pipe sizes, pressures "
     "and hot water generation are the engineer's."),
    ("PL", 200, "Drainage Layout", "Plumbing", "wet",
     "Where the stacks drop, measured from where the wet rooms actually "
     "stack. Falls, pipe sizes, venting and the below-ground drainage "
     "are the engineer's."),
)

SCHEMATICS = (
    ("EL-400", "Electrical Single Line Diagram", "Electrical",
     "One diagram for the building, not one per level."),
    ("ME-200", "HVAC Schematic & Plant Arrangement", "Mechanical",
     "Plant on the roof, risers down, which is all the architecture "
     "fixes."),
    ("PL-300", "Drainage & Water Riser Diagram", "Plumbing",
     "The stack, level by level, from the tanks to the ground."),
)
