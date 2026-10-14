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
    # The top used to be held at V4_TOP + 0.60, a drained upstand on a roof
    # nobody stood on.  The client gave that roof permanent access on
    # 2026-10-13, so the upstand became a guard and the ceiling became
    # V4_TOP + BALUSTRADE_H.  Read from the constant rather than retyped:
    # whichever code finally sets the guarding height sets this too.
    if g.EL_TOP > g.V4_TOP + g.BALUSTRADE_H + 1e-9:
        problems.append(
            f"the exterior schemes top out at +{g.EL_TOP:.2f}, above the "
            f"agreed slab at +{g.V4_TOP:.2f} and its guard at "
            f"{g.BALUSTRADE_H:.2f} m")
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


def nothing_is_drawn_off_the_sheet():
    """Every drawn thing must land inside the drawing area.

    Which is the sheet's border on three sides and the left edge of the
    right-hand panel on the fourth, because a drawing that runs in behind
    the panel is as lost as one that runs off the paper. Everything
    frame.py draws is exempt: the panel, the title block, the key and the
    notes are the frame's business and the panel is where they live.

    This rule exists because of EL-400, ME-200 and PL-300, which set
    their origin to x -150 mm and drew content starting at 20 mm: the
    levels, the riser, the plant and the connection below ground were
    all 130 mm off the left edge of the paper.  Three sheets were issued
    blank but for their right-hand panel, and nothing complained,
    because every one of those lines was drawn perfectly - just not on
    the page.

    An origin is the one number on a sheet that is easy to get badly
    wrong and impossible to notice in code: the geometry is right, the
    scale is right, and the drawing is somewhere else.

    Clipped drawing is exempt.  The 1:25 enlargements run the whole plan
    and crop to a window, so they legitimately draw far outside the
    sheet and rely on the clip to cut it; anything between begin_clip
    and end_clip is not checked.

    What it cannot catch: text.  Only the anchor point is recorded, so a
    label anchored just inside the border can still run off it, and a
    label inside the border can still sit on top of another one.  That
    is what looking at the sheet is for.
    """
    import drafting as D
    import plans

    lo_x, lo_y = 10.0 - 2.0, 10.0 - 2.0
    hi_x, hi_y = D.SHEET_W - 10.0 + 2.0, D.SHEET_H - 10.0 + 2.0
    out, depth, framing = [], [0], [0]

    def note(x, y):
        if depth[0] or framing[0]:
            return
        # the right-hand panel is the frame's. A sheet that draws its own
        # content into it has not gone off the paper, so the border test
        # misses it entirely - STR-500 ran 185 mm of a 9.50 m cantilever
        # in behind the panel and looked, on the sheet, like a balcony
        # two thirds the width of the building.
        if not (lo_x <= x <= F_PANEL and lo_y <= y <= hi_y):
            out.append((x, y))

    import frame as F

    # Everything frame.py draws is the frame's business, panel included.
    # Wrapping its entry points is how the rule tells a sheet's drawing
    # from the sheet furniture around it.
    # the LEFT edge of the panel, which is the right edge of the drawing
    # column; PANEL_R is its far side and would have let a sheet draw
    # clean across the panel and still pass
    F_PANEL = F.PANEL_X - 5.0
    framed = ("border", "heading", "legend", "schedule", "datum_panel",
              "notes", "titleblock", "withdraw")
    real_f = {n: getattr(F, n) for n in framed}

    def wrap(fn):
        def inner(*a, **kw):
            framing[0] += 1
            try:
                return fn(*a, **kw)
            finally:
                framing[0] -= 1
        return inner

    real = {n: getattr(D.Sheet, n) for n in
            ("line_mm", "rect_mm", "text_mm", "poly", "circle", "ellipse",
             "arc", "begin_clip", "end_clip")}

    def line_mm(self, x1, y1, x2, y2, **kw):
        note(x1, y1); note(x2, y2)
        return real["line_mm"](self, x1, y1, x2, y2, **kw)

    def rect_mm(self, x, y, w, h, **kw):
        note(x, y); note(x + w, y + h)
        return real["rect_mm"](self, x, y, w, h, **kw)

    def text_mm(self, x, y, s, **kw):
        note(x, y)
        return real["text_mm"](self, x, y, s, **kw)

    def poly(self, pts, **kw):
        for a, b in pts:
            note(D.X(a), D.Y(b))
        return real["poly"](self, pts, **kw)

    def circle(self, x, y, r_m, **kw):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            note(D.X(x + dx * r_m), D.Y(y + dy * r_m))
        return real["circle"](self, x, y, r_m, **kw)

    def ellipse(self, cx, cy, rx_m, ry_m, **kw):
        note(D.X(cx - rx_m), D.Y(cy - ry_m))
        note(D.X(cx + rx_m), D.Y(cy + ry_m))
        return real["ellipse"](self, cx, cy, rx_m, ry_m, **kw)

    def arc(self, cx, cy, r_m, a0, a1, **kw):
        note(D.X(cx - r_m), D.Y(cy - r_m))
        note(D.X(cx + r_m), D.Y(cy + r_m))
        return real["arc"](self, cx, cy, r_m, a0, a1, **kw)

    def begin_clip(self, x, y, w, h):
        depth[0] += 1
        return real["begin_clip"](self, x, y, w, h)

    def end_clip(self):
        depth[0] = max(0, depth[0] - 1)
        return real["end_clip"](self)

    patched = dict(line_mm=line_mm, rect_mm=rect_mm, text_mm=text_mm,
                   poly=poly, circle=circle, ellipse=ellipse, arc=arc,
                   begin_clip=begin_clip, end_clip=end_clip)
    problems = []
    try:
        for name, fn in patched.items():
            setattr(D.Sheet, name, fn)
        for name, fn in real_f.items():
            setattr(F, name, wrap(fn))
            setattr(plans.F, name, getattr(F, name))
        for build in plans.SHEETS:
            out.clear()
            depth[0] = 0
            sh = build()
            if out:
                xs = [p[0] for p in out]
                ys = [p[1] for p in out]
                problems.append(
                    f"{sh.number}: {len(out)} points are drawn outside the "
                    f"drawing area — x {min(xs):.0f} to {max(xs):.0f}, y "
                    f"{min(ys):.0f} to {max(ys):.0f}, against "
                    f"{lo_x + 2:.0f},{lo_y + 2:.0f} to {F_PANEL:.0f},"
                    f"{hi_y - 2:.0f}")
    finally:
        for name, fn in real.items():
            setattr(D.Sheet, name, fn)
        for name, fn in real_f.items():
            setattr(F, name, fn)
            setattr(plans.F, name, fn)
    return problems


def details_point_at_real_topics():
    """ARC-600's unspecified zones must name a topic that exists.

    The detail sheet's whole claim is that what it does not specify is
    named somewhere that will: each hatched build-up carries "TO BE
    SPECIFIED - QS-003, <topic>".  That is a pointer, and a pointer into
    another document is exactly the thing that rots - rename a topic in
    the specification schedule and the detail still reads perfectly
    while sending its reader to a heading that no longer exists.

    So every topic ARC-600 names must be one `documents.SPEC_TOPICS`
    actually has.

    What it cannot catch: a zone pointing at a topic that exists but is
    the wrong one - a membrane sent to Masonry would pass.
    """
    import re
    import documents
    import drafting as D
    import plans

    said = []
    text_mm, tag = D.Sheet.text_mm, D.Sheet.tag

    def _text(self, x, y, s, **kw):
        said.append(s)
        return text_mm(self, x, y, s, **kw)

    def _tag(self, x, y, s, **kw):
        said.append(s)
        return tag(self, x, y, s, **kw)

    D.Sheet.text_mm, D.Sheet.tag = _text, _tag
    try:
        plans.sheet_details()
    finally:
        D.Sheet.text_mm, D.Sheet.tag = text_mm, tag

    topics = {t for t, _what in documents.SPEC_TOPICS}
    problems, seen = [], set()
    for s in said:
        if not isinstance(s, str):
            continue
        m = re.search(r"QS-003,\s*(.+?)\s*$", s)
        if m and m.group(1) not in topics and m.group(1) not in seen:
            seen.add(m.group(1))
            problems.append(
                f"ARC-600 sends a reader to QS-003 topic “{m.group(1)}”, "
                f"which the specification schedule does not have")
    if not any(re.search(r"QS-003,", s) for s in said if isinstance(s, str)):
        problems.append(
            "ARC-600 carries no specification pointers at all - either the "
            "sheet changed or the notes stopped being drawn")
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


def guards_are_measured_at_the_constant():
    """Every parapet drawn must be in the bill, at the height it stands.

    Two faults, both of which had already happened.

    The measure typed 1.10 and 0.25 where BALUSTRADE_H and PARAPET
    exist.  They agreed, so nothing looked wrong - but BALUSTRADE_H is
    there precisely because the guarding height is a code figure that can
    move, and if it moved the bill would have gone on measuring the old
    one with no sheet contradicting it.

    And the guard round the penthouse roof was measured nowhere.  The
    five plan builders stop at +13.20, so nothing draws it; P32 raised it
    from a 0.60 m drained upstand to a 1.10 m guard and the bill did not
    move, leaving 33 m of masonry - more than the parapet that was being
    measured - bought by nobody.  `bill_reconciles` could not see it: it
    ties the bill to the roof zones, the opening schedule and the
    external areas, and a parapet is in none of those.

    So this recomputes the parapet area from the drawn runs and the
    derived guard, at BALUSTRADE_H, and insists the bill agrees.

    What it cannot catch: a parapet somewhere else again, drawn by no
    plan and derived by no function.  It checks the two the building has,
    not that they are the only two.
    """
    import geometry as G
    import quantities as Q

    w, _rooms = Q.walls()
    drawn = sum(w[lv].get(round(G.PARAPET, 2), (0.0, 0.0))[0] for lv in w)
    want = (drawn + G.penthouse_guard_run()) * G.BALUSTRADE_H

    row = next((i for i in Q.takeoff()
                if i.desc.startswith("Parapet")), None)
    if row is None:
        return ["the bill carries no parapet row at all"]
    if abs(row.qty - want) > 0.01:
        return [
            f"the bill measures {row.qty:.2f} m² of parapet where the "
            f"drawings carry {drawn:.2f} m run plus "
            f"{G.penthouse_guard_run():.2f} m of guard round the "
            f"penthouse roof, which at {G.BALUSTRADE_H:.2f} m is "
            f"{want:.2f} m² - a guard is drawn that nobody is buying"]
    return []


def the_plant_deck_stands_on_something():
    """A deck must be at a level the building has a slab at.

    The water tanks were recorded on the roof at +16.45 in five places -
    the README, the design brief, the specification schedule, and drawn
    that way on all three riser schematics, which then reported a height
    served 3.25 m too high.  Nothing in the geometry ever agreed: the
    plant deck lies outside the penthouse flat's footprint, and the slab
    at V4_TOP measures that footprint and stops at its walls, so there
    has never been any structure at +16.45 under those tanks.

    Nobody could see it.  On every plan the deck is in the right place -
    only its level was wrong, and a level is a number in prose, not a
    line on a drawing.  So this rule asks the one question the drawings
    could not: at the level the deck claims, is there a slab under it?

    What it cannot catch: a deck correctly on a slab and in the wrong
    place on it, or a level that is right here and contradicted in prose
    somewhere this does not read.  It ties the deck to structure, not
    every sentence about it to the deck.
    """
    import geometry as G

    problems = []
    px0, py0, px1, py1 = G.V4_PLANT
    # the floor plates, by level: the penthouse roof covers the flat only
    plates = {
        G.ROOF_LEVEL: (G.V3_X0, G.V3_Y0, G.V3_X1, G.V3_Y1),
        G.V4_TOP: (G.V4_X0, G.V4_Y0, G.V4_X1, G.V4_Y1),
    }
    plate = plates.get(G.V4_PLANT_LEVEL)
    if plate is None:
        problems.append(
            f"the plant deck claims +{G.V4_PLANT_LEVEL:.2f}, which is not "
            f"a level this building has a slab at")
        return problems
    sx0, sy0, sx1, sy1 = plate
    if not (sx0 - TOL <= px0 and sy0 - TOL <= py0
            and px1 <= sx1 + TOL and py1 <= sy1 + TOL):
        problems.append(
            f"the plant deck at +{G.V4_PLANT_LEVEL:.2f} runs outside the "
            f"slab at that level - the tanks stand on "
            f"({px0:.2f}, {py0:.2f}) to ({px1:.2f}, {py1:.2f}) and the "
            f"slab is ({sx0:.2f}, {sy0:.2f}) to ({sx1:.2f}, {sy1:.2f}), "
            f"so part of them is carried by nothing")
    return problems


def the_bill_is_exactly_summed():
    """A measured figure must be the building's, not the machine's.

    The glazing total is exactly 127.875 m2 of structural opening, which
    lands precisely on the rounding boundary of "%.2f".  Added
    left-to-right in binary it comes to 127.87499999999999 and prints
    127.87; summed exactly it is 127.875 and prints 127.88.  Which one
    appeared depended on the interpreter - CPython 3.12 gave sum()
    compensated summation - and on the order the opening schedule
    happened to be in.  So the bill said one thing on one machine and
    another on the next, with nothing in the building changed.

    This rebuilds each schedule-derived area with math.fsum, which is
    exactly rounded and order-independent, and insists the figure the
    document prints agrees.  A return to naive accumulation moves the
    glazing row and fails here.

    What it cannot catch: a figure that is exactly summed and measures
    the wrong thing.  It ties the printed number to the arithmetic, not
    the arithmetic to the building - `bill_reconciles` is what ties the
    measure to the drawings.
    """
    import math
    import documents as D
    import elevations as el
    import geometry as G

    sched = el.opening_schedule()
    exact = {
        "Glazing": math.fsum(r["w"] * r["h"] * r["total"]
                             for r in sched if r["kind"] == "window"),
        "Door leaves and frames": math.fsum(
            r["w"] * r["h"] * r["total"]
            for r in sched if r["kind"] == "door"),
        "Louvres": math.fsum(r["w"] * r["h"] * r["total"]
                             for r in sched if r["kind"] == "vent"),
        "Waterproofing membrane": math.fsum(
            a for _n, _b, a in G.roof_zones()),
        "Paving": math.fsum(v for k, v in G.ew_areas().items()
                            if "Turf" not in k),
    }

    printed = {}
    for line in D.materials_markdown().split("\n"):
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 5 and cells[2] in exact:
            printed[cells[2]] = cells[4]

    problems = []
    for label, value in sorted(exact.items()):
        want = f"{value:.2f}"
        got = printed.get(label)
        if got is None:
            problems.append(
                f"the bill prints no row for {label!r}, so its figure "
                f"cannot be checked against the measure")
        elif got != want:
            problems.append(
                f"{label}: the bill prints {got} where the exact sum is "
                f"{want} ({value!r}) - the figure is following the "
                f"summation rather than the building")
    return problems


def the_priced_schedule_carries_every_row():
    """A schedule somebody prices must show the work it cannot price.

    QS-004 is the only document with a rate column, so it is the one a
    contractor fills in and returns.  It used to be built by skipping
    every row that was not class D.  Thirteen rows vanished silently:
    the foundations, all six suspended slabs, the stair structure and
    every electrical, mechanical and plumbing item.  Nothing said they
    had been left out - a priced return would have come back totalling
    twenty-four rows and looking complete, with the structure of the
    building missing from it, and the omission is invisible in the file
    because an absent row leaves no trace.

    This insists every row of the bill reaches the priced schedule, that
    a row which is not class D says in its rate cell why nobody can price
    it, and that no class D row arrives with a rate already in it.  The
    class decides that, not whether a quantity is printed: six slab rows
    carry an area and are still class L, because the area is ours and the
    thickness is the structural engineer's.  Reinstating the
    `klass != "D": continue` filter fails here with the name of each row
    it drops.

    What it cannot catch: a reason that is present and wrong, or a class
    D quantity that is measured wrongly - `bill_reconciles` and
    `the_bill_is_exactly_summed` are what tie the measure to the
    drawings.  It only insists the pricer is shown every row.
    """
    import csv
    import io
    import documents as D
    import quantities as Q

    rows = list(csv.reader(io.StringIO(D.baseline_csv())))
    header, body = rows[0], [r for r in rows[1:] if r and r[2] != "TOTAL"]
    priced = {(r[0], r[2]): r for r in body}

    problems = []
    for trade, items in Q.by_trade():
        for i in items:
            key = (trade, i.desc.replace('"', "'"))
            row = priced.get(key)
            if row is None:
                problems.append(
                    f"the priced schedule drops {trade} / {i.desc!r} "
                    f"(class {i.klass}), so a priced return comes back "
                    f"with that work missing and nothing saying so")
                continue
            if i.klass != "D" and not row[header.index("rate")].strip():
                problems.append(
                    f"{trade} / {i.desc!r} is class {i.klass} and gives no "
                    f"reason in its rate cell, so it reads as priceable")
            if i.klass == "D" and row[header.index("rate")].strip():
                problems.append(
                    f"{trade} / {i.desc!r} is measured, but its rate cell "
                    f"is already filled with "
                    f"{row[header.index('rate')]!r} - this document is "
                    f"issued unpriced")
    if len(body) != sum(len(i) for _t, i in Q.by_trade()):
        problems.append(
            f"the priced schedule carries {len(body)} rows where the bill "
            f"carries {sum(len(i) for _t, i in Q.by_trade())}")
    return problems


def every_revision_carries_its_date():
    """A revision must say when it was issued, the current one included.

    The issue date on all 81 sheets is read from the last entry in
    `frame.REVISIONS`.  That entry used to be allowed to carry None,
    meaning "today", and the cost was invisible: a sheet nobody had
    touched for a week printed a date a week newer than the issue it
    belongs to, and because the date prints on every sheet, every build
    on a new day rewrote all 81 of them.

    That second part is what makes this worth a rule rather than a
    convention.  This project finds out what changed by rebuilding and
    seeing which files differ - it is how P31's five changed sheets were
    identified out of 74.  A floating date silently turns that answer
    into "all of them", and the failure cannot be seen on any sheet,
    because a date that is wrong by a day looks exactly like one that is
    right.

    What it cannot catch: a date that is present and wrong.  Typing
    2026-01-01 against P31 passes here and is nonsense; the rule only
    insists that a revision commits to a date, not that the date is true.
    """
    import re
    import frame as F

    problems = []
    for entry in F.REVISIONS:
        rev, when = entry[0], entry[1]
        if not when:
            problems.append(
                f"{rev} carries no date. The issue date of every sheet is "
                f"read from the last revision, so a missing one dates the "
                f"set from the clock and rewrites all 81 sheets on the "
                f"next day's build")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(when)):
            problems.append(
                f"{rev} is dated {when!r}, which is not an ISO date")
    if F.DATE and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(F.DATE)):
        problems.append(f"frame.DATE is {F.DATE!r}, not an ISO date")
    return problems


def ground_figures_own_their_basis():
    """A soil figure may not appear on a sheet without saying what it is.

    A bearing pressure is the one number on a structural sheet a
    contractor could act on without reading a note, and every figure this
    project holds about the ground is an assumption: regional typicals
    with no source at all, and a water table the client gives as
    confirmed but nobody has drilled for.  Printing them is still right -
    the assumption was being made anyway, in the choice to draw pads
    rather than a raft, and a number on the sheet is a number the
    engineer can argue with.  Printing them bare would be worse than not
    printing them.

    So two rules.  Any sheet that prints one of geometry.GROUND's figures
    must also print that figure's stamp, so the figure and the warning
    cannot be separated by a later edit that moves one and not the other.
    And any text that looks like a ground figure - a pressure in kPa, a
    concentration in mg/L or mg/kg, a depth below natural ground level -
    must be one GROUND actually declares, so a typed value cannot drift
    from the constant the way the 120 mm partitions did.

    What it cannot catch: a figure quoted against the wrong parameter.
    Printing the soil sulphate range under a chloride heading reads as
    fine here, because both numbers are declared.  It catches a figure
    losing its stamp or drifting from its source, not a label being
    wrong.  Nor does it know whether any figure is true - no check can,
    and that is exactly what GEO-001 is still open for.
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

    # Figures as GROUND declares them, and the stamp each one travels with.
    stamps = {figure: G.GROUND_BASIS[basis].split(" - ")[0]
              for _label, figure, basis, _note in G.GROUND}
    # Anything shaped like a ground figure, declared or not.
    shaped = re.compile(
        r"\d[\d,.]*\s*(?:-\s*[\d,.]+\s*)?"
        r"(?:kPa|kg/cm²|mg/L|mg/kg|%\s*by\s*weight"
        r"|m\s*below\s*(?:natural\s*ground\s*level|NGL))",
        re.IGNORECASE)

    problems, seen = [], set()
    D.Sheet.text_mm, D.Sheet.tag = _text, _tag
    try:
        for build in plans.SHEETS:
            said.clear()
            sh = build()
            page = [s for s in said if isinstance(s, str)]
            whole = " \n".join(page)
            for figure, stamp in stamps.items():
                if figure in whole and stamp not in whole:
                    key = (sh.number, figure, "stamp")
                    if key not in seen:
                        seen.add(key)
                        problems.append(
                            f"{sh.number}: prints the ground figure "
                            f"“{figure}” with no “{stamp}” anywhere on the "
                            f"sheet - the figure has lost the one thing "
                            f"that says it is not a measurement")
            for s in page:
                for m in shaped.finditer(s):
                    hit = m.group(0).strip()
                    if any(hit in figure or figure in hit
                           for figure in stamps):
                        continue
                    key = (sh.number, hit)
                    if key not in seen:
                        seen.add(key)
                        problems.append(
                            f"{sh.number}: says “{hit}” of the ground, "
                            f"which geometry.GROUND does not declare - a "
                            f"soil figure typed rather than derived: "
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
        # Almost every class D row is measured off the geometry.  PRG-001
        # is not: it is derived from this register's own dependency graph,
        # which is one step further from geometry.py but no less derived -
        # and no less able to name where it comes from.  So a source
        # resolves against either module, and a name in neither still
        # fails.
        for name in r.source:
            if not (hasattr(G, name) or hasattr(DL, name)):
                problems.append(
                    f"{r.code} says it is derived from {name}, which is in "
                    f"neither geometry.py nor deliverables.py")

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


def guarding_height_comes_from_the_constant():
    """No sheet may print a guarding height the geometry does not hold.

    `BALUSTRADE_H` exists for one reason, written in geometry.py: the
    guarding height is a code figure rather than a shape, whichever fire
    and safety code is finally named sets it, and if it moves every
    balustrade and parapet in the set has to move with it - which they
    can only do from one place.

    ARC-002's compliance matrix typed it.  The one sheet in the set whose
    whole job is to be checked against a code was carrying the code's own
    figure by hand, where a change to BALUSTRADE_H would have redrawn
    every balustrade in the building and left the matrix saying 1.10.

    So this reads back every string every sheet prints, finds any height
    in metres that looks like a guarding or parapet figure, and refuses
    one that is not BALUSTRADE_H.  The same shape of rule as
    `prose_says_the_real_thickness`, pointed at the other number in this
    set that a code owns.

    What it cannot catch: a guarding height drawn at the wrong height
    without being written down.  `elevation_envelope` holds the drawn
    ones to the constant.
    """
    import re

    import frame as F
    import geometry as G
    import plans

    want = G.BALUSTRADE_H
    # Heights only.  A parapet is 0.25 m thick and 1.10 m high, and both
    # numbers sit in the same sentence, so a rule reading every figure
    # near the word "parapet" would fail on the thickness for ever.
    # `every_wall_has_a_material` and `prose_says_the_real_thickness`
    # own thicknesses; this owns heights, and takes only a figure the
    # text itself calls one.
    metres = re.compile(r"\b(\d\.\d{2})\s*m\b(?!m)")
    mils = re.compile(r"\b(\d{3,4})\s*mm\s*(?:high|tall)")
    problems = []
    for build in plans.SHEETS:
        sh = build()
        # a row of a table is several text elements on one baseline, so
        # the keyword and the figure are rarely in the same string - the
        # first version of this rule looked inside one string and could
        # not fire at all
        rows = {}
        for y, body in re.findall(
                r'<text x="[-\d.]+" y="([-\d.]+)"[^>]*>([^<]*)</text>',
                F.render(sh)):
            rows.setdefault(round(float(y) * 2) / 2, []).append(body)
        for line in (" ".join(cells) for cells in rows.values()):
            if not re.search(r"balustrade|parapet|guard", line, re.I):
                continue
            if "high" not in line.lower() and "tall" not in line.lower():
                found = [float(h) for h in metres.findall(line)]
            else:
                found = ([float(h) for h in metres.findall(line)]
                         + [int(h) / 1000.0 for h in mils.findall(line)])
            for h in found:
                if abs(h - want) > 0.005:
                    problems.append(
                        f"{sh.number} prints a guarding or parapet height "
                        f"of {h:.2f} m; geometry.BALUSTRADE_H is "
                        f"{want:.2f} m - that figure belongs to a code, "
                        f"and it is typed here: {line.strip()[:60]!r}")
    return problems


def title_block_text_fits():
    """A title-block line runs off the sheet rather than wrapping.

    `F.notes` raises when a note would overprint the title block, so
    prose on the face of a sheet is protected.  The revision lines inside
    the title block are not: they are drawn at a fixed start with no
    wrap and no guard, so an over-long one is simply cut off at the
    panel edge - and the sentence that says what changed at this
    revision is the one sentence on the sheet a reader checks first.
    P29's own note was written too long and lost its last four words,
    which is what prompted this.

    The budget is derived from the panel rather than guessed: the text
    starts 44 mm into the panel, the panel ends at PANEL_R, and every
    character of this font at this size is about half its height wide.
    The factor is approximate, so the rule is set to bite a little
    before the clip rather than after it.

    What it cannot catch: a note that fits and says nothing useful.
    """
    import drafting as D
    import frame as F
    import plans

    def budget(indent):
        return int((F.PANEL_R - (F.PANEL_X + indent)) / (0.50 * D.MIN_TEXT))

    problems = []

    # the revision notes, drawn 44 mm into the panel
    limit = budget(44)
    for rev, when, what in F.REVISIONS:
        line = f"{rev}   {when or F.DATE}   {what}"
        if len(line) > limit:
            problems.append(
                f"{rev}'s note is {len(line)} characters and the title "
                f"block holds about {limit}: the last "
                f"{len(line) - limit} would be cut off at the panel edge "
                f"- {what[-40:]!r}")

    # and the status line, drawn 3 mm in, which has the same fault and
    # no guard at all.  Found when ARC-002's status grew to name the
    # fire code and lost the end of it - "...and Code 3".
    limit = budget(3)
    for build in plans.SHEETS:
        sh = build()
        status = getattr(sh, "status", None) or F.STATUS
        if len(status) > limit:
            problems.append(
                f"{sh.number}'s status line is {len(status)} characters "
                f"and the title block holds about {limit}: it would be "
                f"cut at the panel edge - {status[-40:]!r}")
    return problems


def a_schedule_shows_its_rows():
    """A sheet called a schedule must have the schedule on it.

    STR-200 is called "Column Schedule & Grid".  It built its twelve rows
    into a local variable, never drew them, and returned - so for seven
    revisions it issued a grid with no coordinates anywhere on it, under
    a note promising "the coordinate printed beside it" and a register
    row promising "every column coordinate".  Nothing caught it: the
    sheet drew without error, every geometric check passed, and the only
    way to see it was to read the sheet and notice an absence, which is
    the hardest thing to see on a drawing.

    So the rule reads the text the sheet actually emits and insists the
    marks are in it: every column mark on STR-200, every opening mark on
    ARC-500.  A table dropped, a loop that stops early, a column of the
    table moved off the page - all of them fail here.

    The mark alone is not enough to look for, and the first version of
    this rule found that out: STR-200's grid plan labels every column
    A1 to C4 on the drawing, so a check for the marks passed happily
    with the table deleted.  It has to look for the ROW - the mark and
    its figures side by side, on one line of the sheet - which is the
    thing that was actually missing.

    What it cannot catch, and what covers it:

      * whether the figures on each line are right.
        `schedule_matches_the_openings` holds ARC-500 to the plans, and
        STR-200's coordinates come from `grid_columns()`, which
        `grid_carries_the_walls` holds to them too.
      * a row emitted but printed off the page.  This rule reads the
        text, not where it landed, so a table driven past the sheet edge
        still satisfies it; `nothing_is_drawn_off_the_sheet` is what
        fails on that, and both were injected to be sure one of them
        fires.
    """
    import re

    import elevations as el
    import frame as F
    import geometry as G
    import plans

    def lines(sheet, band=0.5):
        """[[text]] - what the sheet prints, gathered into rows.

        A table row is several text elements on one baseline, so the
        baseline groups them.  `band` is how far apart two baselines can
        be and still count as one row: STR-200 puts a whole row on one
        baseline and wants 0.5 mm, while ARC-500 sets each mark 4 mm
        above its own figures, so its row is a band rather than a line.

        A band wide enough to hold ARC-500's row is also wide enough to
        hold the matching row of its second column, so a mark and a size
        found in one band are not proof they are side by side.  This
        rule is only asking whether the line is on the sheet at all;
        `schedule_matches_the_openings` is what proves the figures are
        the right ones.
        """
        found = {}
        for x, y, s in re.findall(
                r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>([^<]*)</text>',
                F.render(sheet)):
            found.setdefault(float(y), []).append(s.strip())
        out, last = [], None
        for y in sorted(found):
            if last is None or y - last > band:
                out.append([])
            out[-1].extend(found[y])
            last = y
        return out

    problems = []
    rows = lines(plans.sheet_str_columns())
    for mark, x, y, _levels in G.grid_columns():
        if not any(mark in cells and f"{x:.2f}" in cells
                   and f"{y:.2f}" in cells for cells in rows):
            problems.append(
                f"STR-200 is called a column schedule and prints no line "
                f"giving {mark} its coordinates {x:.2f}, {y:.2f} - the "
                f"mark on the grid is not a schedule")

    rows = lines(plans.sheet_openings(), band=5.0)
    for r in el.opening_schedule():
        size = f"{r['w'] * 1000:.0f} × {r['h'] * 1000:.0f}"
        if not any(r["mark"] in cells and size in cells for cells in rows):
            problems.append(
                f"ARC-500 prints no line giving {r['mark']} its size "
                f"{size} mm")
    return problems


def programme_carries_no_dates():
    """PRG-001 must stay a sequence, and never become a promise.

    The programme is the one document in the set whose whole discipline is
    a negative: it says what order the work goes in and refuses to say how
    long any of it takes, because a duration is a commitment somebody
    makes and nobody here has been asked.  That refusal is one sentence
    away from being lost - a helpful "about 3 weeks" in a note, a worked
    example with a date in it - and once a figure is on the page it gets
    quoted back as a date whatever the surrounding prose says.  So the
    rule is mechanical: no duration, no date, no month, and the Duration
    column open on every single row.

    Also proves the sequence covers the register exactly once and runs
    the right way round, so a row can never print above something it
    waits on.

    What it cannot catch: whether the dependencies in the register are the
    real ones.  A programme derived from a graph that is missing an edge
    is a wrong programme derived faithfully, and no rule here would know.
    That is a judgement about the work, and it stays with whoever reads
    the sequence.
    """
    import re

    import deliverables as DL
    import documents
    import programme as P

    problems = []
    rows = DL.register()

    # every deliverable placed exactly once
    placed = [r.code for _n, group in P.stages(rows) for r in group]
    if len(placed) != len(set(placed)):
        problems.append("a deliverable is in the programme twice")
    missing = {r.code for r in rows} - set(placed)
    if missing:
        problems.append(f"the programme leaves out {', '.join(sorted(missing))}")

    # and behind everything it waits on
    index = {r.code: r for r in rows}
    stage = {r.code: P.stage(r.code, index) for r in rows}
    for r in rows:
        for d in r.depends:
            if d in stage and stage[d] >= stage[r.code]:
                problems.append(
                    f"{r.code} is in stage {stage[r.code]} and waits on "
                    f"{d}, which is in stage {stage[d]} - the sequence "
                    f"would have it start before its own dependency")

    text = documents.programme_markdown()

    # no duration, in any of the ways one gets written
    units = (r"day|days|week|weeks|wk|wks|month|months|mo|year|years|yr"
             r"|hour|hours|working day|working days|calendar day")
    for hit in re.findall(rf"\b\d+(?:\.\d+)?\s*(?:{units})\b", text, re.I):
        problems.append(f"the programme states a duration: {hit!r}")

    # no date, written as a number or as a month
    months = ("january february march april may june july august september "
              "october november december").split()
    for pattern, what in ((r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b", "a date"),
                          (r"\bQ[1-4]\s*(?:19|20)\d{2}\b", "a quarter"),
                          (r"\b(?:19|20)\d{2}\b", "a year"),
                          (r"\b(?:" + "|".join(months) + r")\b", "a month")):
        for hit in re.findall(pattern, text, re.I):
            problems.append(f"the programme states {what}: {hit!r}")

    # the duration column open on every row of the sequence
    body = text.partition("## The sequence")[2]
    lines = [ln for ln in body.splitlines()
             if ln.startswith("| ") and not set(ln) <= set("|-: ")]
    lines = [ln for ln in lines if "Duration" not in ln]
    if len(lines) != len(rows):
        problems.append(
            f"the sequence table has {len(lines)} rows and the register "
            f"has {len(rows)}")
    for ln in lines:
        if not ln.rstrip().endswith(f"| {documents.OPEN} |"):
            problems.append(f"a programme row has a duration in it: "
                            f"{ln[:60]!r}")
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
                     ("detail", details_point_at_real_topics),
                     ("onpage", nothing_is_drawn_off_the_sheet),
                     ("bill", bill_reconciles),
                     ("grid", grid_carries_the_walls),
                     ("mdl", deliverables_register),
                     ("prog", programme_carries_no_dates),
                     ("table", a_schedule_shows_its_rows),
                     ("fits", title_block_text_fits),
                     ("guard", guarding_height_comes_from_the_constant),
                     ("ground", ground_figures_own_their_basis),
                     ("dated", every_revision_carries_its_date),
                     ("exact", the_bill_is_exactly_summed),
                     ("plant", the_plant_deck_stands_on_something),
                     ("guards", guards_are_measured_at_the_constant),
                     ("priced", the_priced_schedule_carries_every_row)):
        problems = fn()
        total += len(problems)
        state = "OK" if not problems else f"{len(problems)} PROBLEMS"
        print(f"{name:6s} {state}")
        for line in problems:
            print(f"       {line}")
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
