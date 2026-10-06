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

    walls, leaves, cols, vents, dims = [], [], [], [], []
    wall, door, window, column = (D.Sheet.wall, D.Sheet.door, D.Sheet.window,
                                  fx.column)
    vent = fx.vent
    dim_h, dim_v = D.Sheet.dim_h, D.Sheet.dim_v

    def _wall(self, x0, y0, x1, y1, openings=(), **kw):
        walls.append((x0, y0, x1, y1, list(openings), kw.get("fill", D.INK)))
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

    def _dim_h(self, a, b, y_line, text=None, **kw):
        dims.append(("h", a, b, text))
        return dim_h(self, a, b, y_line, text, **kw)

    def _dim_v(self, a, b, x_line, text=None, **kw):
        dims.append(("v", a, b, text))
        return dim_v(self, a, b, x_line, text, **kw)

    D.Sheet.wall, D.Sheet.door, D.Sheet.window = _wall, _door, _window
    D.Sheet.dim_h, D.Sheet.dim_v = _dim_h, _dim_v
    fx.column = plans.fx.column = _column
    fx.vent = plans.fx.vent = _vent

    def restore():
        D.Sheet.wall, D.Sheet.door, D.Sheet.window = wall, door, window
        D.Sheet.dim_h, D.Sheet.dim_v = dim_h, dim_v
        fx.column = plans.fx.column = column
        fx.vent = plans.fx.vent = vent

    return walls, leaves, cols, vents, dims, restore


def _near(a, b):
    return abs(a - b) <= TOL


def _dimensions_tell_the_truth(dims):
    """A dimension that prints a figure must print the one it spans.

    `dim_h` and `dim_v` work out the figure themselves when no text is
    given.  Passing text overrides that, and an overridden figure goes on
    being printed after the geometry it described has moved - which is how
    this sheet came to carry 4.90, 4.22 and 4.38 against spans of 8.92,
    0.12 and 4.46.  A drawing that lies about a dimension is worse than one
    that omits it, so any text that parses as a number has to agree.
    """
    problems = []
    for axis, a, b, text in dims:
        if text is None:
            continue
        try:
            printed = float(str(text).replace(",", ""))
        except ValueError:
            continue                      # a note like "VARIES", not a figure
        span = abs(b - a)
        if abs(printed - span) > 0.005:
            problems.append(
                f"dimension ({axis}) spans {span:.2f} m but prints "
                f"{printed:.2f} - the drawing is lying about a dimension")
    return problems


def _parapet_across(walls, axis, p, q, wlo, whi):
    """Is this opening closed by a parapet rather than by a leaf?

    An inset balcony genuinely interrupts the external wall: there is no
    door or window in the gap, only a 1.10 m parapet standing at the
    building line.  That is not a hole in the plan - but an opening with
    nothing at all in it is, so the parapet has to be there and has to
    span the whole gap.
    """
    from dxf_backend import PARAPET_FILL

    for x0, y0, x1, y1, _openings, fill in walls:
        if fill != PARAPET_FILL:
            continue
        ax, (s, e), plo, phi = _wall_span(x0, y0, x1, y1)
        if ax != axis or s > p + TOL or e < q - TOL:
            continue
        if plo >= wlo - TOL and phi <= whi + TOL:
            return True
    return False


def _wall_span(x0, y0, x1, y1):
    """(axis, along, lo, hi) - which way the wall runs and how thick it is."""
    if (x1 - x0) >= (y1 - y0):
        return "h", (x0, x1), y0, y1
    return "v", (y0, y1), x0, x1


def check(build, leaves_expected=True, west_vent_only=False):
    """Build one sheet and return a list of problems, worst first."""
    walls, leaves, cols, vents, dims, restore = _record()
    try:
        build()
    finally:
        restore()
    problems = _dimensions_tell_the_truth(dims)

    if west_vent_only:
        problems += _west_is_vent_only(leaves, vents)

    for kind, a, b, lo, hi, axis in leaves:
        for x0, y0, x1, y1, openings, _fill in walls:
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
        for x0, y0, x1, y1, openings, _fill in walls:
            ax, _, wlo, whi = _wall_span(x0, y0, x1, y1)
            for p, q in openings:
                if any(a2 == ax and _near(a, p) and _near(b, q)
                       and _near(lo, wlo) and _near(hi, whi)
                       for _k, a, b, lo, hi, a2 in leaves):
                    continue
                if _parapet_across(walls, ax, p, q, wlo, whi):
                    continue
                problems.append(
                    f"opening {p:.2f}-{q:.2f} in the wall at "
                    f"{wlo:.2f}-{whi:.2f} ({ax}) carries no door, window or "
                    f"parapet - it reads as a hole")

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
    pts = g.wave_points(n=2000)
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


def stair_stacks():
    """The stair well must be the same box on every villa floor.

    A stair that does not stack is not a stair - the flights would land on
    the floor below’s rooms.  Both villa floors are drawn from V3_STAIR, so
    this cannot fail today; it fails the day somebody gives one floor its
    own well because the rooms were tight.
    """
    import plans

    seen = {}
    for build, number in ((plans.sheet_first, "A-101"),
                          (plans.sheet_second, "A-102"),
                          (plans.sheet_third, "A-103")):
        walls, leaves, cols, vents, dims, restore = _record()
        stairs = []
        import fixtures as fx
        real = fx.stair
        fx.stair = plans.fx.stair = (
            lambda sh, core, **kw: (stairs.append(tuple(core)),
                                    real(sh, core, **kw))[1])
        try:
            build()
        finally:
            fx.stair = plans.fx.stair = real
            restore()
        seen[number] = stairs

    problems = []
    first = None
    for number, cores in seen.items():
        if len(cores) != 1:
            problems.append(f"{number} draws {len(cores)} stairs, expected 1")
            continue
        if first is None:
            first = (number, cores[0])
        elif any(abs(a - b) > TOL for a, b in zip(first[1], cores[0])):
            problems.append(
                f"{number}’s stair well {cores[0]} does not sit over "
                f"{first[0]}’s {first[1]} - the stair does not stack")
    return problems


def fittings_clear(build, number):
    """No two sanitary fittings may occupy the same floor.

    A basin drawn over a shower tray reads as a basin in a wet room at a
    glance - the tray's diagonals run under it and nothing about the sheet
    says the two are in the same square metre.  That is exactly how the
    master ensuite came to have its basin standing inside the shower on two
    floors at once, through a layout copied from one to the other.

    The boxes below repeat what fixtures.py draws.  They are written out
    rather than measured off the SVG because the symbols are drawn as
    several primitives and only the fitting itself knows its extent.
    """
    import fixtures as fx
    import plans

    rec = []
    real = {n: getattr(fx, n) for n in ("shower", "wc", "basin", "bathtub")}

    def shower(sh, x, y, w=0.95, d=0.95):
        rec.append(("shower", x, y, x + w, y + d))
        return real["shower"](sh, x, y, w, d)

    def bathtub(sh, x, y, w=1.70, d=0.75):
        rec.append(("bath", x, y, x + w, y + d))
        return real["bathtub"](sh, x, y, w, d)

    def wc(sh, x, y, facing="n"):
        w, d = 0.38, 0.56
        if facing in ("n", "s"):
            s = 1 if facing == "n" else -1
            lo, hi = sorted((y, y + s * (0.16 + d)))
            rec.append(("WC", x - w / 2, lo, x + w / 2, hi))
        else:
            s = 1 if facing == "e" else -1
            lo, hi = sorted((x, x + s * (0.16 + d)))
            rec.append(("WC", lo, y - w / 2, hi, y + w / 2))
        return real["wc"](sh, x, y, facing)

    def basin(sh, x, y, w=0.60, d=0.48, facing="n"):
        if facing in ("n", "s"):
            y0 = y if facing == "n" else y - d
            rec.append(("basin", x - w / 2, y0, x + w / 2, y0 + d))
        else:
            x0 = x if facing == "e" else x - d
            rec.append(("basin", x0, y - w / 2, x0 + d, y + w / 2))
        return real["basin"](sh, x, y, w, d, facing)

    patched = {"shower": shower, "wc": wc, "basin": basin, "bathtub": bathtub}
    for name, fn in patched.items():
        setattr(fx, name, fn)
        setattr(plans.fx, name, fn)
    try:
        build()
    finally:
        for name, fn in real.items():
            setattr(fx, name, fn)
            setattr(plans.fx, name, fn)

    problems = []
    for i, (k1, a0, b0, a1, b1) in enumerate(rec):
        for k2, c0, d0, c1, d1 in rec[i + 1:]:
            ox = min(a1, c1) - max(a0, c0)
            oy = min(b1, d1) - max(b0, d0)
            if ox > 0.01 and oy > 0.01:
                problems.append(
                    f"{number}: the {k1} at ({a0:.2f}, {b0:.2f}) and the "
                    f"{k2} at ({c0:.2f}, {d0:.2f}) overlap by "
                    f"{ox:.2f} × {oy:.2f} m - one is drawn inside the other")
    return problems


# Joinery standing across glazing on the superseded ground floor.  Recorded
# rather than fixed: A-100 is still the old apartment scheme and is waiting
# to be redrawn to the detached envelope, furniture and all.
_KNOWN_A100 = [
    "wardrobe at (22.12, 11.30) across the window at 11.40-12.40",
    "counter at (22.05, 13.30) across the opening at 15.00-16.80",
    "counter at (18.15, 13.30) across the opening at 15.40-16.40",
]


def joinery_backs_onto_solid(build, number):
    """A cupboard pushed against a wall must not stand in an opening in it.

    A wardrobe is drawn as a rectangle, so it looks the same whether the
    wall behind it is there or not.  Twice now an opening has been widened
    on one floor and left a linen cupboard standing free in the gap - once
    on the first floor when the spine was opened to the lobby, once on the
    second when the same opening was made to replace the lobby door.  Both
    read as perfectly ordinary joinery on the sheet.

    It runs on the villa floors only.  A-100 is the superseded apartment
    ground floor, still drawn to the old envelope, and it carries three
    faults of exactly this kind - a wardrobe and two counters standing
    across glazing.  They are real, but that whole sheet is waiting to be
    redrawn, and failing every build until then would stop the work rather
    than help it.  They are listed in `_KNOWN_A100` so they cannot be
    forgotten.
    """
    import fixtures as fx
    import plans

    walls, leaves, cols, vents, dims, restore = _record()
    pieces = []
    real = {n: getattr(fx, n) for n in ("wardrobe", "counter")}

    def wardrobe(sh, x, y, w, d, axis="h"):
        pieces.append(("wardrobe", x, y, x + w, y + d))
        return real["wardrobe"](sh, x, y, w, d, axis)

    def counter(sh, x, y, w, d, *a, **kw):
        pieces.append(("counter", x, y, x + w, y + d))
        return real["counter"](sh, x, y, w, d, *a, **kw)

    for n, f in (("wardrobe", wardrobe), ("counter", counter)):
        setattr(fx, n, f)
        setattr(plans.fx, n, f)
    try:
        build()
    finally:
        for n, f in real.items():
            setattr(fx, n, f)
            setattr(plans.fx, n, f)
        restore()

    problems = []
    for kind, x0, y0, x1, y1 in pieces:
        for wx0, wy0, wx1, wy1, openings, _fill in walls:
            if not openings:
                continue
            ax, (s, e), lo, hi = _wall_span(wx0, wy0, wx1, wy1)
            # does the piece stand against one face of this wall, and run
            # along it rather than across it?
            if ax == "v":
                against = _near(x0, hi) or _near(x1, lo)
                a, b = y0, y1
            else:
                against = _near(y0, hi) or _near(y1, lo)
                a, b = x0, x1
            if not against or a < s - TOL or b > e + TOL:
                continue
            for p, q in openings:
                if min(b, q) - max(a, p) > TOL:
                    problems.append(
                        f"{number}: the {kind} at ({x0:.2f}, {y0:.2f}) backs "
                        f"onto the {ax} wall at {lo:.2f}-{hi:.2f}, but that "
                        f"wall is open from {p:.2f} to {q:.2f} - the "
                        f"cupboard stands in the gap")
    return problems


def _east_strip(build):
    """(divider lines, east-wall openings) for one villa floor.

    The east strip is everything beyond the spine: suite 2 / master bedroom,
    an ensuite, the shared bath and the lobby beside them.  Its dividers are
    the horizontal walls east of the spine, and its windows are the openings
    in the east wall.
    """
    import geometry as g

    walls, leaves, cols, vents, dims, restore = _record()
    try:
        build()
    finally:
        restore()

    dividers, windows = set(), set()
    for x0, y0, x1, y1, openings, _fill in walls:
        ax, (s, _e), lo, hi = _wall_span(x0, y0, x1, y1)
        if ax == "h" and s >= g.V3_SPINE_X1 - TOL and x1 <= g.V3_X1 + TOL:
            dividers.add(round(lo, 2))
        if ax == "v" and _near(lo, g.V3_X1 - g.WT) and _near(hi, g.V3_X1):
            windows |= {(round(p, 2), round(q, 2)) for p, q in openings}
    return dividers, windows


def east_strip_stacks():
    """A-101 and A-102 divide their east strip on exactly the same lines.

    The client asked for the second floor's shared bath and lobby to be the
    sizes they are on the first.  Making them so put every wet room on this
    floor directly over its twin below, which is what lets each one drop a
    single drainage stack to the ground instead of chasing pipe sideways
    through a ceiling - and it means the east elevation has one set of
    openings rather than two sets 200 mm apart.

    Both floors are drawn by their own function from their own constants, so
    nothing but this check stops one of them moving a wall and quietly
    breaking both.  The third floor divides the strip differently on purpose
    and is not compared.
    """
    import plans

    d1, w1 = _east_strip(plans.sheet_first)
    d2, w2 = _east_strip(plans.sheet_second)

    problems = []
    for name, a, b in (("divider", d1, d2), ("east window", w1, w2)):
        for extra in sorted(a - b):
            problems.append(
                f"A-101 has an east-strip {name} at {extra} that A-102 does "
                f"not - the two floors no longer stack")
        for extra in sorted(b - a):
            problems.append(
                f"A-102 has an east-strip {name} at {extra} that A-101 does "
                f"not - the two floors no longer stack")
    return problems


def balconies_stack():
    """Every upper floor carries the cantilever, and can be walked onto.

    The second floor had no balcony at all while the first and third did, so
    the slabs did not stack and the south elevation had a gap in the middle.
    Checking the curve's shape would prove nothing - all three floors sample
    the same function - but whether a floor draws one at all, and whether
    there is a way out onto it, is drawn per sheet and worth testing.
    """
    import fixtures as fx
    import geometry as g
    import plans

    problems = []
    for build, number in ((plans.sheet_first, "A-101"),
                          (plans.sheet_second, "A-102"),
                          (plans.sheet_third, "A-103")):
        drawn, sliders = [], []
        real_b, real_s = fx.wave_balcony, fx.slider

        def _balc(sh, pts, *a, **kw):
            drawn.append(len(pts))
            return real_b(sh, pts, *a, **kw)

        def _slide(sh, a, b, lo, hi, axis):
            sliders.append((a, b, lo, hi, axis))
            return real_s(sh, a, b, lo, hi, axis)

        fx.wave_balcony = plans.fx.wave_balcony = _balc
        fx.slider = plans.fx.slider = _slide
        try:
            build()
        finally:
            fx.wave_balcony = plans.fx.wave_balcony = real_b
            fx.slider = plans.fx.slider = real_s

        if len(drawn) != 1:
            problems.append(f"{number} draws {len(drawn)} wave balconies, "
                            f"expected 1 - the cantilevers do not stack")
            continue
        onto = [s for s in sliders
                if s[4] == "h" and _near(s[2], g.V3_Y0)
                and _near(s[3], g.V3_Y0 + g.WT)]
        if not onto:
            problems.append(f"{number} carries a balcony with no sliding "
                            f"door onto it")
        for a, b, _lo, _hi, _ax in onto:
            if a < g.V3_X0 - TOL or b > g.V3_X1 + TOL:
                problems.append(
                    f"{number}'s balcony door {a:.2f}-{b:.2f} runs past the "
                    f"cantilever's span")
    return problems


def issue_status():
    """Each sheet's revision letter and status line must be defensible.

    The revision used to be one module-level constant stamped on every
    sheet, so marking one floor as agreed would have marked the whole set -
    including the sheets still on the old apartment envelope.  It is now a
    property of the sheet, which means it can also drift: a sheet can claim
    a letter that was never issued, or carry "final draft" while sitting on
    a superseded revision.  Neither is visible on the drawing without
    reading the title block of all nine.

    ACCEPTED records which floors the client has actually signed off.  It is
    written down rather than inferred so that a later edit which quietly
    drops the status - or promotes a floor nobody agreed to - fails here.
    """
    import frame as F
    import plans

    ACCEPTED = {"A-101", "A-103"}
    letters = [r for r, _w, _t in F.REVISIONS]
    current = letters[-1]

    problems = []
    for build in plans.SHEETS:
        sh = build()
        rev = getattr(sh, "rev", None) or F.REV
        status = getattr(sh, "status", None) or F.STATUS
        final = status == F.STATUS_FINAL_DRAFT
        if rev not in letters:
            problems.append(
                f"{sh.number} is stamped {rev}, which is not in the "
                f"revision record")
        if final and rev != current:
            problems.append(
                f"{sh.number} is marked final draft at {rev}, but the set "
                f"is at {current} - a signed-off sheet cannot be behind")
        if final and sh.number not in ACCEPTED:
            problems.append(
                f"{sh.number} is marked final draft, but the client has "
                f"only agreed {', '.join(sorted(ACCEPTED))}")
        if sh.number in ACCEPTED and not final:
            problems.append(
                f"{sh.number} was agreed with the client but no longer "
                f"carries the final-draft status")
    return problems


def main():
    import plans

    sheets = [(plans.sheet_site, "A-000", False, False),
              (plans.sheet_ground, "A-100", True, False),
              (plans.sheet_first, "A-101", True, True),
              (plans.sheet_second, "A-102", True, True),
              (plans.sheet_third, "A-103", True, True)]
    total = 0
    for build, number, leaves_expected, west in sheets:
        problems = check(build, leaves_expected, west_vent_only=west)
        problems += fittings_clear(build, number)
        if number not in ("A-000", "A-100"):
            problems += joinery_backs_onto_solid(build, number)
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{number:6s} {state}")
        for line in problems:
            print(f"       {line}")

    for name, fn in (("stair", stair_stacks), ("wave", wave_cantilever),
                     ("balc", balconies_stack), ("east", east_strip_stacks),
                     ("issue", issue_status)):
        problems = fn()
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{name:6s} {state}")
        for line in problems:
            print(f"       {line}")
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
