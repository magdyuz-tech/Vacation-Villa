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

    walls, leaves, cols = [], [], []
    wall, door, window, column = (D.Sheet.wall, D.Sheet.door, D.Sheet.window,
                                  fx.column)

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

    D.Sheet.wall, D.Sheet.door, D.Sheet.window = _wall, _door, _window
    fx.column = plans.fx.column = _column

    def restore():
        D.Sheet.wall, D.Sheet.door, D.Sheet.window = wall, door, window
        fx.column = plans.fx.column = column

    return walls, leaves, cols, restore


def _near(a, b):
    return abs(a - b) <= TOL


def _wall_span(x0, y0, x1, y1):
    """(axis, along, lo, hi) - which way the wall runs and how thick it is."""
    if (x1 - x0) >= (y1 - y0):
        return "h", (x0, x1), y0, y1
    return "v", (y0, y1), x0, x1


def check(build, leaves_expected=True):
    """Build one sheet and return a list of problems, worst first."""
    walls, leaves, cols, restore = _record()
    try:
        build()
    finally:
        restore()
    problems = []

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


def main():
    import plans

    sheets = [(plans.sheet_site, "A-000", False),
              (plans.sheet_ground, "A-100", True),
              (plans.sheet_first, "A-101", True),
              (plans.sheet_second, "A-102", True),
              (plans.sheet_third, "A-103", True)]
    total = 0
    for build, number, leaves_expected in sheets:
        problems = check(build, leaves_expected)
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{number:6s} {state}")
        for line in problems:
            print(f"       {line}")
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
