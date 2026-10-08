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
    """The south cantilever must not pass the projection the client set.

    Run over EVERY profile, not just the one the issued sheets are drawn
    with.  The exterior schemes gave the curve two more shapes, and a
    scheme that breached the 2.00 m cap or pinched below the 0.60 m floor
    would otherwise reach a client drawing with nothing to stop it.
    """
    import geometry as g

    problems = []
    for profile in g.EL_PROFILES:
        pts = g.wave_points(n=2000, profile=profile)
        where = f" ({profile})" if profile != "agreed" else ""
        worst = max(g.V3_Y0 - y for _x, y in pts)
        if worst > g.V3_WAVE_LIMIT + 1e-9:
            problems.append(
                f"the wave balcony{where} projects {worst:.3f} m, past the "
                f"{g.V3_WAVE_LIMIT:.2f} m the client set")
        # the balcony oversails our own forecourt, which is GARDEN_D_E deep;
        # at least 1.00 m of it has to stay clear to the street
        if worst > g.GARDEN_D_E - 1.00:
            problems.append(
                f"the wave balcony{where} leaves only "
                f"{g.GARDEN_D_E - worst:.2f} m of forecourt to the street")
        inboard = min(g.V3_Y0 - y for _x, y in pts)
        if inboard < 0.60:
            problems.append(
                f"the wave balcony{where} narrows to {inboard:.2f} m - too "
                f"shallow to stand on at the troughs")
        for x, _y in pts:
            if x < g.V3_X0 - TOL or x > g.V3_X1 + TOL:
                problems.append(f"the wave balcony{where} runs past the "
                                f"envelope at x = {x:.2f}")
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
    for build, number in ((plans.sheet_ground, "A-100"),
                          (plans.sheet_first, "A-101"),
                          (plans.sheet_second, "A-102"),
                          (plans.sheet_third, "A-103"),
                          (plans.sheet_penthouse, "A-104")):
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


def joinery_backs_onto_solid(build, number):
    """A cupboard pushed against a wall must not stand in an opening in it.

    A wardrobe is drawn as a rectangle, so it looks the same whether the
    wall behind it is there or not.  Twice now an opening has been widened
    on one floor and left a linen cupboard standing free in the gap - once
    on the first floor when the spine was opened to the lobby, once on the
    second when the same opening was made to replace the lobby door.  Both
    read as perfectly ordinary joinery on the sheet.

    Height matters, so the two kinds of joinery are judged differently.  A
    wardrobe is full height and may not cross any opening at all.  A counter
    is 900 mm high and passes happily under a window sill - a sink under a
    window is the right place for it - but it must not cross a door or a
    cased opening, which go to the floor.

    It runs on every sheet that carries rooms.  The site plan is a massing
    diagram with no joinery in it and is skipped.
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
                if min(b, q) - max(a, p) <= TOL:
                    continue
                glazed = any(k == "window" and _near(la, p) and _near(lb, q)
                             and _near(llo, lo) and _near(lhi, hi)
                             and lax == ax
                             for k, la, lb, llo, lhi, lax in leaves)
                if kind == "counter" and glazed:
                    continue            # 900 mm high, it passes under a sill
                what = "window" if glazed else "doorway"
                problems.append(
                    f"{number}: the {kind} at ({x0:.2f}, {y0:.2f}) backs "
                    f"onto the {ax} wall at {lo:.2f}-{hi:.2f}, but there is "
                    f"a {what} from {p:.2f} to {q:.2f} - it stands in the "
                    f"opening")
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


def _face_wall(level, face):
    """(axis, lo, hi) of the external wall a given face is drawn of."""
    import geometry as g

    if level == 4:
        y0, y1, x0, x1 = g.V4_Y0, g.V4_Y1, g.V4_X0, g.V4_X1
    else:
        y0, y1, x0, x1 = g.V3_Y0, g.V3_Y1, g.V3_X0, g.V3_X1
    return {"s": ("h", y0, y0 + g.WT), "n": ("h", y1 - g.WT, y1),
            "e": ("v", x1 - g.WT, x1), "w": ("v", x0, x0 + g.WT)}[face]


def elevations_match_the_plans():
    """An elevation may not show an opening its plan does not have.

    The elevations exist to show the skin.  The moment they carry their own
    copy of the openings they start drifting from the agreed plans, and the
    drift is invisible: a window moved on a plan and left alone on an
    elevation looks perfectly ordinary on both sheets.  So every opening is
    drawn through one funnel, `elevations._opening`, and this reads the
    record back against the wall the plan actually drew.

    It compares in BOTH directions.  An elevation that omits an opening the
    plan has is just as wrong as one that invents a window.
    """
    import elevations as el
    import plans

    builders = {0: plans.sheet_ground, 1: plans.sheet_first,
                2: plans.sheet_second, 3: plans.sheet_third,
                4: plans.sheet_penthouse}

    # what the plans actually drew, per level and face
    in_plan = {}
    for level, build in builders.items():
        walls, leaves, cols, vents, dims, restore = _record()
        try:
            build()
        finally:
            restore()
        for face in el.FACES:
            axis, lo, hi = _face_wall(level, face)
            found = set()
            for x0, y0, x1, y1, openings, _fill in walls:
                ax, _span, wlo, whi = _wall_span(x0, y0, x1, y1)
                if ax != axis or not _near(wlo, lo) or not _near(whi, hi):
                    continue
                found |= {(round(a, 2), round(b, 2)) for a, b in openings}
            in_plan[(level, face)] = found

    problems = []
    for scheme, number in (("A", "A-400/A-401"), ("B", "A-410/A-411"),
                           ("C", "A-420/A-421")):
        drawn = {}
        real = el._opening

        def _spy(sh, face, level, a, b, kind, sc, _real=real, _d=drawn):
            _d.setdefault((level, face), set()).add((round(a, 2), round(b, 2)))
            return _real(sh, face, level, a, b, kind, sc)

        el._opening = _spy
        try:
            plans.elevations_of(scheme)
        finally:
            el._opening = real

        for key, shown in sorted(drawn.items()):
            level, face = key
            expected = in_plan[key]
            for a, b in sorted(shown - expected):
                problems.append(
                    f"{number}: scheme {scheme} draws an opening "
                    f"{a:.2f}-{b:.2f} on the {face} face at level {level} "
                    f"that the plan's wall does not have")
            for a, b in sorted(expected - shown):
                problems.append(
                    f"{number}: the plan has an opening {a:.2f}-{b:.2f} on "
                    f"the {face} face at level {level} that scheme "
                    f"{scheme}'s elevation leaves out")
    return problems


def elevation_envelope():
    """No scheme may raise the building or cross a setback."""
    import geometry as g

    problems = []
    if g.EL_LEVELS != [0.0, g.FLOOR_TO_FLOOR, 2 * g.FLOOR_TO_FLOOR,
                       3 * g.FLOOR_TO_FLOOR, g.ROOF_LEVEL]:
        problems.append("the elevations no longer stand on the agreed five "
                        "levels")
    if g.EL_TOP > g.V4_TOP + 0.60 + 1e-9:
        problems.append(
            f"the exterior schemes top out at +{g.EL_TOP:.2f}, above the "
            f"agreed slab at +{g.V4_TOP:.2f} and its parapet")
    # scheme B arches its openings, and an arch is a crown height the
    # storey has to be able to spare.  A semicircular head on a 2.30 m bay
    # would rise 1.15 m over a head already at 2.40 m and come out through
    # the slab - which looks perfectly ordinary on an elevation.
    widest = max(b - a for lv in range(5) for f in ("s", "e", "n", "w")
                 for a, b in g.FACADE[lv][f])
    crown = g.EL_HEAD + g.B_ARCH_RISE + g.B_SURROUND
    if crown > g.CLEAR_HEIGHT:
        problems.append(
            f"scheme B's arched heads crown at {crown:.2f} m, through the "
            f"soffit at {g.CLEAR_HEIGHT:.2f} m (widest bay {widest:.2f} m)")

    for profile in g.EL_PROFILES:
        for x, y in g.wave_points(n=500, profile=profile):
            if x < g.V3_X0 - TOL or x > g.V3_X1 + TOL:
                problems.append(f"the {profile} curve runs past the south "
                                f"frontage at x = {x:.2f}")
                break
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

    ACCEPTED = {"A-000", "A-100", "A-101", "A-102", "A-103", "A-104",
                "A-200"}
    letters = [r for r, _w, _t in F.REVISIONS]
    current = letters[-1]
    in_use = set()

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
        if letters.index(rev) > letters.index(current):
            problems.append(
                f"{sh.number} claims {rev}, later than the set's {current}")
        if final and sh.number not in ACCEPTED:
            problems.append(
                f"{sh.number} is marked final draft, but the client has "
                f"only agreed {', '.join(sorted(ACCEPTED))}")
        if sh.number in ACCEPTED and not final:
            problems.append(
                f"{sh.number} was agreed with the client but no longer "
                f"carries the final-draft status")
        in_use.add(rev)
    # a sheet that has not changed legitimately stays at an older letter, so
    # "final draft" no longer has to mean "current".  What must hold is that
    # the newest letter in the record is actually on a sheet - otherwise a
    # revision has been written down that nobody issued.
    if current not in in_use:
        problems.append(
            f"the record's newest revision {current} is not carried by any "
            f"sheet - it was added but never issued")
    return problems


def schedule_matches_the_openings():
    """ARC-500 must schedule the openings the plans actually have.

    What this cannot catch is the schedule drifting from the plans: it is
    generated from the very lists the plans draw from, so widening a
    window moves both sides together.  That is the point of deriving it,
    and it is worth being clear that the rule earns its place somewhere
    else.

    What it catches is `opening_schedule` itself going wrong - two types
    collapsed into one mark, a level column off by one, a mark issued
    twice, totals that do not add up.  So the counting here is written
    out again rather than borrowed from it: a grouping confirmed by its
    own grouping proves nothing.  Both mistakes were injected and both
    fail here.
    """
    import elevations as el
    import geometry as G

    rows = el.opening_schedule()
    problems = []

    want = {}
    per_level = {}
    for level in range(len(G.EL_LEVELS)):
        for face in el.FACES:
            for a, b in G.FACADE[level][face]:
                kind = el.opening_kind(face, level, a, b)
                sill, head = el.opening_head(face, level, kind)
                key = (kind, round(b - a, 3), round(head - sill, 3),
                       round(sill, 3))
                want[key] = want.get(key, 0) + 1
                per_level.setdefault(key, [0] * len(G.EL_LEVELS))
                per_level[key][level] += 1

    got = {(r["kind"], round(r["w"], 3), round(r["h"], 3),
            round(r["sill"], 3)): r for r in rows}

    for key, n in sorted(want.items()):
        if key not in got:
            problems.append(f"the plans have {n} × {key} and the schedule "
                            f"has no mark for it")
            continue
        r = got[key]
        if r["total"] != n:
            problems.append(f"{r['mark']} is scheduled {r['total']} times "
                            f"and the plans have {n}")
        if r["levels"] != per_level[key]:
            problems.append(f"{r['mark']} is scheduled per level as "
                            f"{r['levels']} and the plans have "
                            f"{per_level[key]}")
    for key, r in sorted(got.items()):
        if key not in want:
            problems.append(f"{r['mark']} is scheduled but no opening in "
                            f"the plans matches it")

    marks = [r["mark"] for r in rows]
    if len(set(marks)) != len(marks):
        problems.append("two schedule rows share a mark")
    for r in rows:
        if sum(r["levels"]) != r["total"]:
            problems.append(f"{r['mark']}: the level columns add to "
                            f"{sum(r['levels'])}, not {r['total']}")
    return problems


def index_is_honest():
    """ARC-001 lists itself once, and lists what it is.

    Every other row of the index is built, so it cannot be wrong.  The
    cover's own row cannot be built - a sheet cannot build itself to find
    out its own name - so it is held in `plans.IX_SELF`, and the sheet
    takes its number, title, level, scale and revision from that same
    constant.  The first rule below therefore cannot fail by drift: the
    two sides are one value.  It is kept as a cheap guard against someone
    putting literals back into the Sheet() call, and is honest about
    proving nothing more than that.

    The rule that does bite is the second.  `sheet_index` skips the cover
    by identity, and anything that rebinds that name - a patch, a
    decorator, a second entry in SHEETS - stops it matching, and ARC-001
    is then listed twice or, worse, recurses.  The duplicate fails here;
    the recursion fails in sheet_index's own guard.  Both were injected
    and both fired.
    """
    import plans

    sh = plans.sheet_cover()
    built = (sh.number, sh.title, sh.level, sh.scale_note,
             getattr(sh, "rev", None) or F_REV())
    problems = []
    if tuple(plans.IX_SELF) != built:
        problems.append(
            f"ARC-001 lists itself as {tuple(plans.IX_SELF)} and builds "
            f"as {built}")
    numbers = [n for n, *_r in plans.sheet_index(skip=plans.sheet_cover)]
    if plans.IX_SELF[0] in numbers:
        problems.append(
            f"{plans.IX_SELF[0]} appears twice in the drawing index")
    return problems


def F_REV():
    import frame
    return frame.REV


def every_wall_has_a_material():
    """No wall may be a thickness nobody declared.

    This rule exists because of a specific failure.  The client specified
    a 100 mm red brick partition where the drawings had 120 mm, and PT
    changed - but six walls were set out between two hard-coded
    coordinates whose gap had been 120 mm only because PT was.  They went
    on being drawn 120 mm thick, and because the bill of quantities sums
    the thicknesses it knows about, 21.29 m of wall silently left the
    bill.  Nothing looked wrong on any drawing.

    So: every wall thickness must be one of the declared ones in
    geometry.WALL_MATERIAL, which is also what the bill measures and what
    names the material.  A wall that is not a declared thickness is a wall
    nobody is buying.
    """
    import geometry as G
    import plans

    problems = []
    declared = {round(t, 3) for t in G.WALL_MATERIAL}
    for build, number in ((plans.sheet_ground, "A-100"),
                          (plans.sheet_first, "A-101"),
                          (plans.sheet_second, "A-102"),
                          (plans.sheet_third, "A-103"),
                          (plans.sheet_penthouse, "A-104")):
        walls, *_rest, restore = _record()
        try:
            build()
        finally:
            restore()
        seen = {}
        for x0, y0, x1, y1, _op, _fill in walls:
            t = round(min(x1 - x0, y1 - y0), 3)
            if t not in declared:
                seen[t] = seen.get(t, 0.0) + max(x1 - x0, y1 - y0)
        for t, run in sorted(seen.items()):
            problems.append(
                f"{number}: {run:.2f} m of wall is {t * 1000:.0f} mm thick, "
                f"which is not a declared thickness - it has no material "
                f"and the bill does not measure it")
    return problems


def out_of_the_issue_says_why():
    """A sheet outside the issued set must say so on its own face.

    Two things can go wrong, and they are opposites.

    A sheet drops out of `SET_ORDER` - by an edit, a rename, a merge -
    and nothing anywhere says it is not current.  It still builds, still
    renders, still looks exactly like the drawings beside it, and the
    only trace of its leaving is a number missing from a list nobody
    reads line by line.  That is how a drawing of a superseded building
    ends up in somebody's hand.

    Or a sheet that is marked withdrawn or not selected gets bound into
    the issue anyway, which is worse: now it is stamped AND current.

    So: in the issue and unmarked, or out of the issue and marked.  The
    mark is the status line, which is also what the title block prints,
    so the rule and the drawing cannot disagree about it.

    What it cannot catch: a sheet marked withdrawn that should not be.
    Nothing here knows what the client agreed to; it only knows that
    whatever a sheet claims about itself matches where it is bound.
    """
    import export_share
    import frame as F
    import plans

    marks = ("Withdrawn", "Option not selected")
    issued = set(export_share.SET_ORDER)
    problems = []
    for build in plans.SHEETS:
        sh = build()
        status = getattr(sh, "status", None) or F.STATUS
        marked = status.startswith(marks)
        if sh.number in issued and marked:
            problems.append(
                f"{sh.number} is bound into the issue and stamped "
                f"“{status.split('—')[0].strip()}” - it cannot be both")
        if sh.number not in issued and not marked:
            problems.append(
                f"{sh.number} is built but left out of the issue, and "
                f"nothing on the sheet says why: it reads as current "
                f"wherever it is read on its own")
    return problems


def prose_says_the_real_thickness():
    """A wall thickness written in words must be one that exists.

    `every_wall_has_a_material` watches the geometry; this watches the
    prose, which drifts the same way and is not drawn, so nothing looks
    wrong.  The key said "200 mm partition" long after the partition was
    120 mm, and eight sheets of structural notes explained that "the
    120 mm partitions" are carried by the slab after the client specified
    100 mm - a sentence that is now about a wall this building does not
    have.  Both were typed rather than derived, which is the same fault
    the hard-coded 12.54 was.

    So: any text on any sheet that names a thickness in millimetres in
    the same breath as a wall or a partition must name a declared one.
    The 50-500 mm window keeps parapet heights, door widths and room
    dimensions out of it.

    What it cannot catch: prose that quotes a declared thickness for the
    wrong wall.  "300 mm partitions" would read as perfectly fine here,
    because 300 is a thickness this building has.  It catches the number
    going stale, not the sentence being wrong.

    One wrinkle in the reporting: the cover builds the index, which builds
    every other sheet, so text written by a nested build is attributed to
    the outer sheet as well.  A sentence on STR-001 is therefore reported
    against ARC-001 too.  The quoted text is in the message, so it is
    findable either way; it is noted here so nobody hunts for a note on
    the cover that is not on it.
    """
    import re
    import drafting as D
    import geometry as G
    import plans

    said = []
    text_mm, tag = D.Sheet.text_mm, D.Sheet.tag

    def _text(self, x, y, s, **kw):
        said.append(s)
        return text_mm(self, x, y, s, **kw)

    def _tag(self, x, y, s, **kw):
        said.append(s)
        return tag(self, x, y, s, **kw)

    declared = {round(t * 1000) for t in G.WALL_MATERIAL}
    problems, seen = [], set()
    D.Sheet.text_mm, D.Sheet.tag = _text, _tag
    try:
        for build in plans.SHEETS:
            said.clear()
            sh = build()
            for s in said:
                if not isinstance(s, str):
                    continue
                low = s.lower()
                if "wall" not in low and "partition" not in low:
                    continue
                for m in re.finditer(r"(\d{2,4})\s*mm", s):
                    v = int(m.group(1))
                    if 50 <= v <= 500 and v not in declared \
                            and (sh.number, v) not in seen:
                        seen.add((sh.number, v))
                        problems.append(
                            f"{sh.number}: the sheet says {v} mm of a wall "
                            f"or partition, which is not a thickness this "
                            f"building has ({', '.join(str(d) for d in sorted(declared))}): "
                            f"“{s.strip()[:60]}…”")
    finally:
        D.Sheet.text_mm, D.Sheet.tag = text_mm, tag
    return problems


def bill_reconciles():
    """The bill must agree with the drawings it was measured from.

    A bill is read by somebody buying things, and the one way it goes
    wrong that nobody notices is quietly measuring a different building
    from the sheets beside it.  Three ties are checked, each between the
    bill and a drawing that states the same figure in its own panel:
    ARC-106's roof zones, ARC-500's opening counts, ARC-700's external
    areas.  Two of them already disagreed once - the roof by 15 m², when
    the bill took the penthouse footprint and counted the stair well -
    which is why they are checked rather than assumed.
    """
    import geometry as G
    import elevations as el
    import quantities as Q

    items = Q.takeoff()
    problems = []

    def found(prefix, trade=None):
        return [i for i in items if i.desc.startswith(prefix)
                and (trade is None or i.trade == trade)]

    roof = sum(i.qty for i in items if i.trade == "Roof" and i.unit == "m²")
    zones = sum(a for _n, _b, a in G.roof_zones())
    if abs(roof - zones) > 0.01:
        problems.append(f"the bill measures {roof:.2f} m² of roof and "
                        f"ARC-106 draws {zones:.2f} m²")

    sched = el.opening_schedule()
    for kind, prefix in (("door", "Doors"), ("window", "Windows"),
                         ("vent", "Louvres")):
        want = sum(r["total"] for r in sched if r["kind"] == kind)
        rows = found(prefix, "Openings")
        if len(rows) != 1:
            problems.append(f"the bill has {len(rows)} rows for {prefix}")
        elif abs(rows[0].qty - want) > 0.001:
            problems.append(f"the bill counts {rows[0].qty:.0f} {prefix} "
                            f"and ARC-500 schedules {want}")

    for name, area in G.ew_areas().items():
        rows = found(name, "External works")
        if len(rows) != 1:
            problems.append(f"the bill has {len(rows)} rows for the "
                            f"external works item {name!r}")
        elif abs(rows[0].qty - area) > 0.01:
            problems.append(f"the bill measures {rows[0].qty:.2f} m² of "
                            f"{name} and ARC-700 draws {area:.2f} m²")

    # nothing may be priced, and nothing unmeasured may carry a quantity
    for i in items:
        if i.klass == "X" and i.qty is not None:
            problems.append(f"{i.desc!r} is class X but carries a quantity")
    return problems


def grid_carries_the_walls():
    """The rule the whole frame rests on.

    A 300 mm wall needs a beam under it, and a beam is a column line, a
    wall below, or a secondary beam landing on primary beams.  The
    structural package is drawn on the claim that every 300 mm wall in
    this building stands on a grid line, so the primary beams are the
    grid and nothing else is needed - with one exception, declared in
    geometry.GRID_EXCEPTION, which is why STR-305 carries a secondary
    beam the other five framing layouts do not.

    If that claim ever stops being true, a framing layout is issued
    showing a slab with an unsupported wall on it.  So it is checked
    rather than believed, and the exception is checked too: exactly one,
    and that one.
    """
    import geometry as G
    import plans

    WT = G.WT
    problems, found = [], []
    declared = {round(x, 2) for x in G.GRID_X}
    declared_y = {round(y, 2) for y in G.GRID_Y}

    for build, level in ((plans.sheet_ground, 0), (plans.sheet_first, 1),
                         (plans.sheet_second, 2), (plans.sheet_third, 3),
                         (plans.sheet_penthouse, 4)):
        walls, _l, cols, *_rest, restore = _record()
        try:
            build()
        finally:
            restore()
        # the declaration must still match the columns the plans draw
        for cx, cy, _s in cols:
            if round(cx, 2) not in declared or round(cy, 2) not in declared_y:
                problems.append(
                    f"level {level}: a column at ({cx:.2f}, {cy:.2f}) is "
                    f"not on the declared grid")
        for x0, y0, x1, y1, _op, _fill in walls:
            if abs(min(x1 - x0, y1 - y0) - WT) > 0.01:
                continue
            horiz = (x1 - x0) > (y1 - y0)
            mid = (y0 + y1) / 2.0 if horiz else (x0 + x1) / 2.0
            lines = G.GRID_Y if horiz else G.GRID_X
            if min(abs(mid - g) for g in lines) > WT / 2 + 0.01:
                found.append((level, "h" if horiz else "v", round(mid, 2)))

    want = tuple(G.GRID_EXCEPTION)
    extra = [f for f in found if f != want]
    for level, axis, mid in extra:
        problems.append(
            f"level {level}: a {WT * 1000:.0f} mm wall at {axis}={mid:.2f} "
            f"stands on no grid line and is not the declared exception - "
            f"it has no beam under it")
    if want not in found:
        problems.append(
            f"the declared grid exception {want} is not in the plans any "
            f"more; STR-305 draws a secondary beam for a wall that has "
            f"moved")
    return problems


def deliverables_register():
    """The Master Deliverables List must describe the building that exists.

    The register is the one document that is read instead of the drawings,
    so every way it can lie is worth a rule.  The one that matters most is
    the last: the client's own list assumed three floor plans, and every
    per-level family here is generated by looping EL_LEVELS.  If a level is
    ever added to the building and a loop is not, that family comes up a
    row short - which is exactly the mistake this whole register exists to
    stop, and it would otherwise be invisible among eighty rows.
    """
    import export_share
    import geometry as G
    import deliverables as DL
    import documents
    import plans

    problems = []
    rows = DL.register()
    codes = {}
    for r in rows:
        if r.code in codes:
            problems.append(f"{r.code} appears twice in the register")
        codes[r.code] = r

    packages = {letter for letter, _t in DL.PACKAGES}
    built = {build().number for build in plans.SHEETS}
    issued = set(export_share.SET_ORDER)

    for number in issued:
        if number not in built:
            problems.append(
                f"{number} is in the issued set but no builder in "
                f"plans.SHEETS draws it")

    for r in rows:
        if r.package not in packages:
            problems.append(f"{r.code} is in package {r.package!r}, which "
                            f"is not one of {sorted(packages)}")
        if r.klass not in DL.CLASSES:
            problems.append(f"{r.code} is class {r.klass!r}, which is not "
                            f"one of {sorted(DL.CLASSES)}")
        for d in r.depends:
            if d not in codes:
                problems.append(f"{r.code} waits on {d}, which is not a "
                                f"deliverable")
            if d == r.code:
                problems.append(f"{r.code} waits on itself")
        for number in r.sheet:
            if number not in issued:
                problems.append(
                    f"{r.code} resolves to sheet {number}, which is not in "
                    f"the issued set")
        if r.doc and r.doc not in documents.RENDERS:
            problems.append(
                f"{r.code} names the document {r.doc}, which nothing in "
                f"documents.py writes")
        # a row is only class D if the geometry really holds its figures
        if r.klass == "D" and not r.sheet and not r.source:
            problems.append(
                f"{r.code} is class D but names neither an issued sheet "
                f"nor the constants it is derived from")
        for name in r.source:
            if not hasattr(G, name):
                problems.append(
                    f"{r.code} says it is derived from geometry.{name}, "
                    f"which does not exist")

    # dependencies must terminate, or "blocked" means nothing
    seen, stack = set(), set()

    def walk(code):
        if code in stack:
            problems.append(f"{code} is in a circle of dependencies")
            return
        if code in seen or code not in codes:
            return
        stack.add(code)
        for d in codes[code].depends:
            walk(d)
        stack.discard(code)
        seen.add(code)

    for r in rows:
        walk(r.code)

    # the rule this register exists for
    if len(DL.LEVEL_NAMES) != len(G.EL_LEVELS):
        problems.append(
            f"deliverables.LEVEL_NAMES names {len(DL.LEVEL_NAMES)} levels "
            f"but the building has {len(G.EL_LEVELS)}")
    across = {"levels": len(DL.levels()), "slabs": len(DL.slabs())}
    families = {}
    for r in rows:
        if r.series is None:
            continue
        if r.across not in across:
            problems.append(f"{r.code} repeats across {r.across!r}, which "
                            f"is neither levels nor slabs")
            continue
        families.setdefault((r.series, r.across), []).append(r.index)
    for (series, dimension), got in sorted(families.items()):
        want = set(range(across[dimension]))
        if set(got) != want or len(got) != len(want):
            problems.append(
                f"{series} covers {sorted(got)} of the {across[dimension]} "
                f"{dimension} - the building has "
                f"{sorted(want)}")
    if not families:
        problems.append("no family in the register repeats per level - the "
                        "per-level rule is not being tested")

    # a decision recorded but never built is worse than one never recorded:
    # it reads as settled on paper while the drawings still show the old
    # thing.  Every decision names the constant it became, and every one of
    # those has to resolve.
    import documents as DOC

    for when, subject, _decision, constant, _effect in DOC.DECISIONS:
        if constant == "—":
            continue
        for ref in constant.split(" / "):
            module, _, name = ref.partition(".")
            try:
                holder = __import__(module)
            except ImportError:
                problems.append(f"decision {subject!r} of {when} points at "
                                f"{ref}, and there is no module {module}")
                continue
            if not hasattr(holder, name):
                problems.append(
                    f"decision {subject!r} of {when} says it became {ref}, "
                    f"which does not exist - it was recorded but never "
                    f"built")
    return problems


def main():
    import plans

    sheets = [(plans.sheet_site, "A-000", False, False),
              (plans.sheet_ground, "A-100", True, True),
              (plans.sheet_first, "A-101", True, True),
              (plans.sheet_second, "A-102", True, True),
              (plans.sheet_third, "A-103", True, True),
              (plans.sheet_penthouse, "A-104", True, True)]
    total = 0
    for build, number, leaves_expected, west in sheets:
        problems = check(build, leaves_expected, west_vent_only=west)
        problems += fittings_clear(build, number)
        if number != "A-000":
            problems += joinery_backs_onto_solid(build, number)
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{number:6s} {state}")
        for line in problems:
            print(f"       {line}")

    for name, fn in (("stair", stair_stacks), ("wave", wave_cantilever),
                     ("balc", balconies_stack), ("east", east_strip_stacks),
                     ("elev", elevations_match_the_plans),
                     ("envel", elevation_envelope),
                     ("issue", issue_status),
                     ("sched", schedule_matches_the_openings),
                     ("index", index_is_honest),
                     ("walls", every_wall_has_a_material),
                     ("prose", prose_says_the_real_thickness),
                     ("issued", out_of_the_issue_says_why),
                     ("bill", bill_reconciles),
                     ("grid", grid_carries_the_walls),
                     ("mdl", deliverables_register)):
        problems = fn()
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{name:6s} {state}")
        for line in problems:
            print(f"       {line}")
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
