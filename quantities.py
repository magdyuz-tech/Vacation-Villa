#!/usr/bin/env python3
"""
quantities.py - the building, measured.

    python3 quantities.py            the takeoff, to the terminal

Package E's measure.  Nothing here is estimated and nothing is scaled off
a drawing: every figure is read from the same geometry the sheets are
drawn from, and the wall lengths come from the drawing calls themselves.
`checks._record` patches `Sheet.wall` so a sheet build reports what it was
asked to draw; that was written to catch a door in a solid wall, and it is
also, exactly, a wall takeoff.  Measuring the drawing rather than the
model is the usual way a bill drifts from the thing it bills for, and this
cannot: it is the same call.

What is deliberately NOT here matters as much.

  * Slab, beam and foundation THICKNESSES.  Areas are ours; depths are the
    structural engineer's, and a concrete volume needs both.  The bill
    carries slab areas and says so.
  * Excavation, blinding, hardcore and anything below ground, which wait
    on GEO-001.
  * Reinforcement, in any form.
  * Rates.  Every quantity here is unpriced.  QS-004 carries the same rows
    with a rate column, and that column stays empty until a named source
    fills it.

Each row carries a class, the same three the register uses: D measured
from the geometry, L needing someone else's design before it can be
measured, X impossible here at all.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import geometry as G

WALL_H = None           # set from CLEAR_HEIGHT at import, below
WALL_H = G.CLEAR_HEIGHT  # blockwork runs slab top to slab soffit
INT_DOOR_H = 2.10        # internal door head, as the section draws it
PARAPET_T = 0.25         # the terrace parapet, which stands 1.10 m not 3.00


class Item:
    """One line of the bill."""

    __slots__ = ("trade", "desc", "unit", "qty", "klass", "note")

    def __init__(self, trade, desc, unit, qty, klass="D", note=""):
        self.trade = trade
        self.desc = desc
        self.unit = unit
        self.qty = qty
        self.klass = klass
        self.note = note


# --------------------------------------------------------------------------
# the measure
# --------------------------------------------------------------------------
def _levels():
    """Each level's plan builder, in order."""
    import plans
    return [(0, "Ground", plans.sheet_ground),
            (1, "First", plans.sheet_first),
            (2, "Second", plans.sheet_second),
            (3, "Third", plans.sheet_third),
            (4, "Penthouse", plans.sheet_penthouse)]


def walls():
    """Wall runs and opening deductions, by level and thickness.

    Returns {level: {thickness: [run_m, opening_run_m]}} plus the rooms
    each level schedules, read off one build of each plan.
    """
    import checks

    out, rooms = {}, {}
    for level, _name, build in _levels():
        rec, *_rest, restore = checks._record()
        try:
            sh = build()
        finally:
            restore()
        rooms[level] = list(sh.schedule)
        here = {}
        for x0, y0, x1, y1, openings, _fill in rec:
            t = round(min(x1 - x0, y1 - y0), 2)
            run = max(x1 - x0, y1 - y0)
            here.setdefault(t, [0.0, 0.0])
            here[t][0] += run
            here[t][1] += sum(b - a for a, b in openings)
        out[level] = here
    return out, rooms


def facade_openings():
    """{level: (run_m, area_m2)} of everything in an external wall."""
    import elevations as el

    out = {}
    for face, level, a, b, kind in el.openings():
        sill, head = el.opening_head(face, level, kind)
        run, area = out.get(level, (0.0, 0.0))
        out[level] = (run + b - a, area + (b - a) * (head - sill))
    return out


def columns():
    """Column lifts and their concrete, which is measurable: the section
    is a constant and every storey height is one.  What is not measurable
    is the reinforcement in them.

    The lift above the penthouse is not FLOOR_TO_FLOOR.  +13.20 to the
    roof at +16.45 is 3.25 m, and multiplying every lift in the building
    by 3.30 counted 50 mm of column that is not there on each of the four
    that go up there.  Small - 0.2 m of lift, 0.018 m³ - and wrong in the
    direction a bill is always wrong in, so each lift is measured between
    the levels it actually spans.
    """
    import checks

    tops = list(G.EL_LEVELS[1:]) + [G.V4_TOP]
    lifts, height = 0, 0.0
    for level, _name, build in _levels():
        _w, _l, cols, *_rest, restore = checks._record()
        try:
            build()
        finally:
            restore()
        lifts += len(cols)
        height += len(cols) * (tops[level] - G.EL_LEVELS[level])
    return lifts, height, height * G.COL ** 2


def stair():
    """The stair, by the same arithmetic `fixtures.stair` draws it with.

    It was measured nowhere.  The dog-leg runs in one well from the ground
    floor to the penthouse, it is drawn on all five plans, it is in both
    sections and - since P27 - in all five cutaways, and the bill had no
    stair in it and the specification schedule asked for no tread, no
    nosing and no handrail.  A whole trade, drawn five times and bought by
    nobody.

    The figures are recomputed here from the same constants rather than
    read back out of the drawing, and `checks.stair_stacks` already proves
    the drawn stair matches them.  Returns the numbers the bill needs:

        (storeys, risers, rise, treads, going, width, landing_area)
    """
    x0, y0, x1, y1 = G.V3_STAIR
    storeys = len(G.EL_LEVELS) - 1            # four rises to five levels
    width = (x1 - x0 - G.V3_STAIR_WELL) / 2.0
    risers = max(2, round(G.FLOOR_TO_FLOOR / G.V3_STAIR_RISE))
    rise = G.FLOOR_TO_FLOOR / risers
    treads = (risers // 2) * 2                # two flights to a storey
    landing = (x1 - x0) * G.V3_STAIR_LANDING
    return (storeys, risers, rise, treads, G.V3_STAIR_GOING, width, landing)


def takeoff():
    """The whole bill, by trade."""
    import documents  # noqa: F401  (kept out of the import cycle)
    import elevations as el

    w, rooms = walls()
    fac = facade_openings()
    items = []

    # --- substructure -----------------------------------------------------
    items.append(Item(
        "Substructure", "Excavation, blinding, footings and ground slab",
        "item", None, "X",
        "Waits on GEO-001 and STR-101. Nothing below ground is measured "
        "here: the foundation type is not chosen and its depth is not "
        "known."))

    # --- frame ------------------------------------------------------------
    plate = (G.V3_X1 - G.V3_X0) * (G.V3_Y1 - G.V3_Y0)
    slabs = [("+0.00", plate), ("+3.30", plate), ("+6.60", plate),
             ("+9.90", plate), (f"+{G.ROOF_LEVEL:.2f}", plate),
             (f"+{G.V4_TOP:.2f}", (G.V4_X1 - G.V4_X0) * (G.V4_Y1 - G.V4_Y0))]
    for name, area in slabs:
        items.append(Item("Frame", f"Suspended slab at {name}", "m²", area,
                          "L", "Area measured; thickness is the engineer's, "
                               "so no volume is given."))
    items.append(Item(
        "Frame", f"Cantilever balcony slab, {G.SCHEME} serpentine", "m²",
        G.wave_area() * 4, "L",
        "Four levels at %.1f m² each. The most engineering-sensitive "
        "element in the building; see STR-500." % G.wave_area()))
    lifts, height, volume = columns()
    items.append(Item("Frame",
                      f"Columns, {G.COL * 1000:.0f} × {G.COL * 1000:.0f} mm",
                      "nr", lifts, "D",
                      f"{height:.1f} m of lift, {volume:.2f} m³ of "
                      f"concrete. Reinforcement is the engineer's."))

    # --- masonry ----------------------------------------------------------
    # the labels carry the thickness and the material from geometry, so a
    # wall that changes thickness or gets specified cannot leave a stale
    # figure in the bill
    def label_for(t, what):
        return f"{what}, {t * 1000:.0f} mm — {G.WALL_MATERIAL[t]}"

    for t, label in ((G.WT, label_for(G.WT, "External and party wall")),
                     (G.PT, label_for(G.PT, "Internal partition")),
                     (PARAPET_T, label_for(PARAPET_T, "Parapet"))):
        # a parapet stands 1.10 m, everything else runs floor to soffit.
        # The branches compare against the constants, not against 0.30 and
        # 0.12: they used to be literals, and when PT moved to 0.10 the
        # partitions stopped matching their own branch and fell through to
        # the parapet's, which deducts no openings at all. The bill then
        # carried 326.76 m² of partition where the answer was 281.40 -
        # gross, with every door still in it.
        height = 1.10 if t == PARAPET_T else WALL_H
        gross = net = 0.0
        for level in w:
            run, op_run = w[level].get(t, (0.0, 0.0))
            gross += run * height
            if t == G.WT:
                ext_run, ext_area = fac.get(level, (0.0, 0.0))
                internal = max(op_run - ext_run, 0.0)
                net += run * height - ext_area - internal * INT_DOOR_H
            elif t == G.PT:
                net += run * height - op_run * INT_DOOR_H
            else:
                net += run * height
        items.append(Item("Masonry", label, "m²", net, "D",
                          f"{gross:.1f} m² gross, openings deducted."))

    # --- openings ---------------------------------------------------------
    sched = el.opening_schedule()
    for kind, label in (("door", "Doors"), ("window", "Windows"),
                        ("vent", "Louvres")):
        rows = [r for r in sched if r["kind"] == kind]
        items.append(Item(
            "Openings", f"{label}, {len(rows)} types", "nr",
            sum(r["total"] for r in rows), "D",
            f"{math.fsum(r['w'] * r['h'] * r['total'] for r in rows):.1f} m² of "
            f"structural opening. See ARC-500. Frames, glazing and "
            f"ironmongery are specification, not geometry."))

    # --- stair ------------------------------------------------------------
    storeys, risers, rise, treads, going, width, landing = stair()
    items.append(Item(
        "Stair", f"Reinforced concrete dog-leg flights and half landings, "
        f"{storeys} storeys", "m²",
        storeys * (treads * going * width + landing), "L",
        f"{storeys} storey rises of {risers} risers at "
        f"{rise * 1000:.0f} mm, {treads} treads a storey at "
        f"{going * 1000:.0f} mm going, flights {width * 1000:.0f} mm wide, "
        f"half landings {landing:.2f} m² each. Plan area of flight and "
        f"landing; waist thickness and reinforcement are the engineer's, "
        f"so no volume is given."))
    items.append(Item(
        "Stair", "Tread, riser and nosing finish", "nr",
        storeys * treads, "D",
        f"{storeys * treads} treads and the risers with them, measured as "
        f"the geometry sets them out. Material, nosing profile and the "
        f"slip resistance of it are specification - see QS-003."))
    items.append(Item(
        "Stair", "Balustrade to the open well", "m",
        (G.V3_STAIR[3] - G.V3_STAIR[1]) * len(G.EL_LEVELS), "D",
        f"The east edge of the well on all {len(G.EL_LEVELS)} levels, "
        f"which the plans tag OPEN STAIR — BALUSTRADE, at "
        f"{G.BALUSTRADE_H:.2f} m. Infill, fixings and the handrail on it "
        f"are specification."))
    items.append(Item(
        "Stair", "Handrail to the flights", "m", None, "L",
        "Not measured: a handrail follows an arrangement nobody has drawn "
        "yet - one side or both, wall-fixed or on the balustrade, with or "
        "without the extensions past the top and bottom risers that a code "
        "may require. It is named here so it cannot be forgotten, and "
        "stays unmeasured until QS-003 answers it."))

    # --- finishes ---------------------------------------------------------
    floor = sum(sum(a for _n, a in rooms[lv]) for lv in rooms)
    items.append(Item("Finishes", "Floor finish, net internal", "m²", floor,
                      "D", "Every room the plans schedule. Finish type is "
                           "specification."))
    items.append(Item("Finishes", "Ceiling finish, net internal", "m²", floor,
                      "D", "Equal to the floor area; bulkheads add to it "
                           "once their depth is set. See the ARC-400 "
                           "series."))
    # the outside face of an external wall is render, not plaster: counting
    # both faces of it as plaster rendered the outside of the building in
    # the wrong material and overstated the trade by 600 m²
    ext = next(i.qty for i in items if i.desc.startswith("External and"))
    part = next(i.qty for i in items if i.desc.startswith("Internal part"))
    items.append(Item("Finishes", "Internal plaster", "m²",
                      ext + 2 * part, "D",
                      "The inside face of the external walls plus both "
                      "faces of the partitions. Wet-room tiling comes out "
                      "of it once the specification says which rooms are "
                      "tiled and how high."))
    items.append(Item("Finishes", "External render", "m²", ext, "D",
                      "The outside face. Slab edges, the nosing and the "
                      "cove are additional and are detailed on ARC-600."))

    # --- roof and external ------------------------------------------------
    for name, _box, area in G.roof_zones():
        items.append(Item("Roof", f"Waterproofing — {name.lower()}", "m²",
                          area, "D",
                          "As ARC-106, which reads the same zones. "
                          "Membrane, insulation and build-up are "
                          "specification."))
    items.append(Item("Roof", "Rainwater outlets", "nr", 5, "L",
                      "Indicative on ARC-106; PL-200 sets the number, the "
                      "positions and the sizes."))

    for name, area in G.ew_areas().items():
        items.append(Item("External works", name, "m²", area, "D",
                          "Measured on ARC-700."))
    items.append(Item("External works", "Trees", "nr", len(G.EW_TREES), "D"))
    items.append(Item(
        "External works", "Street wall", "m",
        G.V3_X0 - G.SETBACK - G.EW_GATE[2], "L",
        f"{G.GARDEN_WALL_H:.2f} m high is indicative and its line awaits "
        f"the survey."))

    # --- services ---------------------------------------------------------
    items.append(Item("Services", "Electrical, mechanical and plumbing",
                      "item", None, "L",
                      "Not measurable from the architecture. The EL, ME "
                      "and PL series are coordination layouts; quantities "
                      "follow the services engineer's design."))
    return items


def by_trade(items=None):
    items = items if items is not None else takeoff()
    out = []
    for trade in ("Substructure", "Frame", "Masonry", "Openings", "Stair",
                  "Finishes", "Roof", "External works", "Services"):
        here = [i for i in items if i.trade == trade]
        if here:
            out.append((trade, here))
    return out


def main():
    items = takeoff()
    for trade, here in by_trade(items):
        print(f"\n{trade.upper()}")
        for i in here:
            q = "—" if i.qty is None else f"{i.qty:10.2f}"
            print(f"  {i.klass}  {q} {i.unit:5s}  {i.desc}")
    counts = {}
    for i in items:
        counts[i.klass] = counts.get(i.klass, 0) + 1
    print("\n" + ", ".join(f"{n} class {k}" for k, n in sorted(counts.items())))


if __name__ == "__main__":
    main()
