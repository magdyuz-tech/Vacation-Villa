#!/usr/bin/env python3
"""
checks.py - geometric checks run over the plans before they are issued.

    python3 checks.py

These are the mistakes that are easy to make in a plan written as code and
hard to see on a sheet, because the drawing looks perfectly tidy either
way.  Each sheet is built with `Sheet.wall`, `Sheet.door` and
`Sheet.window` recording what they were asked to draw, and the record is
then read back:

  * a door or window drawn where its wall carries no opening - the leaf is
    drawn over solid poche, so on the sheet it reads as a door into a wall;
  * an opening cut in a wall with no leaf drawn in it - a hole in the plan;
  * an opening that runs through one of the 300 mm columns standing in that
    same wall, which the sheet shows as a window neatly bisected by a
    black square.

The first of these caught the ground floor's second arched opening, which
was cut through the party wall into the services riser cupboard rather
than into a room.

The site plan is a 1:75 massing diagram that draws the shell without
leaves, so only its column rule is checked; the section works in a
different frame (plan y against level) and is left out.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TOL = 0.02          # metres; openings are set out to the nearest 10 mm


def _record():
    """Patch the drawing calls so a sheet build reports its own geometry."""
    import drafting as D
    import fixtures as fx
    import plans

    walls, leaves, cols, vents = [], [], [], []
    wall, door, window, column = (D.Sheet.wall, D.Sheet.door, D.Sheet.window,
                                  fx.column)
    vent = fx.vent

    def _wall(self, x0, y0, x1, y1, openings=(), **kw):
        walls.append((x0, y0, x1, y1, list(openings)))
        return wall(self, x0, y0, x1, y1, openings=openings, **kw)

    def _door(self, a, b, lo, hi, axis, **kw):
        leaves.append(("door", a, b, lo, hi, axis))
        return door(self, a, b, lo, hi, axis, **kw)

    def _window(self, a, b, lo, hi, axis, **kw):
        leaves.append(("window", a, b, lo, hi, axis))
        return window(self, a, b, lo, hi, axis, **kw)

    def _column(sh, cx, cy, s=0.30):
        cols.append((cx, cy, s))
        return column(sh, cx, cy, s)

    def _vent(sh, a, b, lo, hi, axis):
        vents.append((a, b, lo, hi, axis))
        return vent(sh, a, b, lo, hi, axis)

    D.Sheet.wall, D.Sheet.door, D.Sheet.window = _wall, _door, _window
    fx.column = plans.fx.column = _column
    fx.vent = plans.fx.vent = _vent

    def restore():
        D.Sheet.wall, D.Sheet.door, D.Sheet.window = wall, door, window
        fx.column = plans.fx.column = column
        fx.vent = plans.fx.vent = vent

    return walls, leaves, cols, vents, restore


def _near(a, b):
    return abs(a - b) <= TOL


def _wall_span(x0, y0, x1, y1):
    """(axis, along, lo, hi) - which way the wall runs and how thick it is."""
    if (x1 - x0) >= (y1 - y0):
        return "h", (x0, x1), y0, y1
    return "v", (y0, y1), x0, x1


def check(build, leaves_expected=True, west_vent_only=False):
    """Build one sheet and return a list of problems, worst first."""
    walls, leaves, cols, vents, restore = _record()
    try:
        build()
    finally:
        restore()
    problems = []

    if west_vent_only:
        problems += _west_is_vent_only(leaves, vents)

    for kind, a, b, lo, hi, axis in leaves:
        for x0, y0, x1, y1, openings in walls:
            ax, (s, e), wlo, whi = _wall_span(x0, y0, x1, y1)
            if ax != axis or not _near(wlo, lo) or not _near(whi, hi):
                continue
            if a < s - TOL or b > e + TOL:
                continue
            if any(_near(p, a) and _near(q, b) for p, q in openings):
                break
        else:
            problems.append(
                f"{kind} {a:.2f}-{b:.2f} across {lo:.2f}-{hi:.2f} ({axis}) "
                f"is drawn in solid wall - no matching opening")

    if leaves_expected:
        for x0, y0, x1, y1, openings in walls:
            ax, _, wlo, whi = _wall_span(x0, y0, x1, y1)
            for p, q in openings:
                if not any(a2 == ax and _near(a, p) and _near(b, q)
                           and _near(lo, wlo) and _near(hi, whi)
                           for _k, a, b, lo, hi, a2 in leaves):
                    problems.append(
                        f"opening {p:.2f}-{q:.2f} in the wall at "
                        f"{wlo:.2f}-{whi:.2f} ({ax}) carries no door or "
                        f"window - it reads as a hole")

    for kind, a, b, lo, hi, axis in leaves:
        for cx, cy, s in cols:
            centre, span = ((cx, (cy - s / 2, cy + s / 2)) if axis == "h"
                            else (cy, (cx - s / 2, cx + s / 2)))
            if span[0] >= hi - TOL or span[1] <= lo + TOL:
                continue                       # column is not in this wall
            if centre - s / 2 < b - TOL and centre + s / 2 > a + TOL:
                problems.append(
                    f"{kind} {a:.2f}-{b:.2f} ({axis}) runs through the "
                    f"column at ({cx:.2f}, {cy:.2f})")
    return problems


def _west_is_vent_only(leaves, vents):
    """The west wall takes louvred ventilation openings and nothing else.

    The client is explicit: rooms may sit against the west wall on
    ventilation windows, but nothing there is a view window and nothing
    projects west.  A plain `window` on that wall draws identically to a
    vent minus its blades, so the sheet gives no clue - this does.
    """
    import geometry as g

    problems = []
    for kind, a, b, lo, hi, axis in leaves:
        if axis != "v" or not (_near(lo, g.V3_X0) and _near(hi, g.V3_X0 + g.WT)):
            continue
        if not any(_near(a, p) and _near(b, q) for p, q, _l, _h, _x in vents):
            problems.append(
                f"{kind} {a:.2f}-{b:.2f} in the WEST wall is not a vent - "
                f"the west elevation takes ventilation openings only")
    return problems


def wave_cantilever():
    """The south cantilever must not pass the projection the client set."""
    import geometry as g

    problems = []
    pts = g.wave_points(n_per_crest=200)
    worst = max(g.V3_Y0 - y for _x, y in pts)
    if worst > g.V3_WAVE_LIMIT + 1e-9:
        problems.append(
            f"the wave balcony projects {worst:.3f} m, past the "
            f"{g.V3_WAVE_LIMIT:.2f} m the client set")
    # the balcony oversails our own forecourt, which is GARDEN_D_E deep;
    # at least 1.00 m of it has to stay clear to the street
    if worst > g.GARDEN_D_E - 1.00:
        problems.append(
            f"the wave balcony leaves only {g.GARDEN_D_E - worst:.2f} m of "
            f"forecourt to the street")
    inboard = min(g.V3_Y0 - y for _x, y in pts)
    if inboard < 0.60:
        problems.append(
            f"the wave balcony narrows to {inboard:.2f} m - too shallow "
            f"to stand on at the troughs")
    for x, _y in pts:
        if x < g.V3_X0 - TOL or x > g.V3_X1 + TOL:
            problems.append(f"the wave balcony runs past the envelope at "
                            f"x = {x:.2f}")
            break
    return problems


def main():
    import plans

    sheets = [(plans.sheet_site, "A-000", False, False),
              (plans.sheet_ground, "A-100", True, False),
              (plans.sheet_first, "A-101", True, False),
              (plans.sheet_second, "A-102", True, False),
              (plans.sheet_third, "A-103", True, True)]
    total = 0
    for build, number, leaves_expected, west in sheets:
        problems = check(build, leaves_expected, west_vent_only=west)
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{number:6s} {state}")
        for line in problems:
            print(f"       {line}")

    problems = wave_cantilever()
    total += len(problems)
    print(f"{'wave':6s} {'OK' if not problems else f'{len(problems)} PROBLEMS'}")
    for line in problems:
        print(f"       {line}")
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
