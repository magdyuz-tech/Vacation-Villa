#!/usr/bin/env python3
"""
deliverables.py - the Master Deliverables List, as data.

    python3 deliverables.py            the register, to the terminal

One row per deliverable: code, title, discipline, scale, format, the
competence class it is issued under, what it waits on, and the sheet or
document it resolves to.

Two rules shape the file.

**Levels are generated, never typed.**  The client's own list assumed
three floor plans.  The building has five levels and six structural
slabs, which multiplies through every package: five floor plans, five
reflected ceiling plans, six framing layouts, thirty MEP layouts.  Every
per-level family here is built by looping `geometry.EL_LEVELS`, so a
level added to the building cannot leave a package short - and `checks.py`
proves the loop ran.

**Status is derived, never typed.**  `status()` resolves a row against
the issued set and against the documents something here actually writes,
and `checks.py` proves both: a row naming a sheet no builder draws, or a
document nothing renders, fails the build.  A register maintained by hand
drifts within a week and then quietly claims deliverables that do not
exist; this one can only report what the project really holds.

The competence class is the safety rule of the set, written into every
row:

    D  derived   generated from geometry.py - exact, checkable, ours to
                 issue.
    L  layout    positions and coordination, architecturally correct,
                 sized and certified by others.  Issued stamped "layout
                 for the engineer's design": no member sizes, no
                 reinforcement, no load calculations.
    X  external  cannot be produced here at all - a measured survey, a
                 soil report, a verified market rate.  Named, scheduled
                 and left open rather than invented.

Nothing is issued as engineering that has not been engineered.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import geometry as G

# --------------------------------------------------------------------------
# the building, read off the geometry
# --------------------------------------------------------------------------
# Names only.  The levels themselves - how many there are and what they sit
# at - come from EL_LEVELS, and checks.py fails if this list falls out of
# step with it.
LEVEL_NAMES = ("Ground", "First", "Second", "Third", "Penthouse")


def levels():
    """(index, name, FFL text) for every level of the building."""
    out = []
    for i, ffl in enumerate(G.EL_LEVELS):
        name = LEVEL_NAMES[i] if i < len(LEVEL_NAMES) else f"Level {i}"
        out.append((i, name, f"+{ffl:.2f}"))
    return out


def slabs():
    """Every structural slab, bottom up.

    One per level, plus the roof over the penthouse.  The slab at +13.20
    is the penthouse floor and the roof over the third floor at once,
    which is why there are six slabs and five levels.
    """
    return [f"+{z:.2f}" for z in list(G.EL_LEVELS) + [G.V4_TOP]]


# --------------------------------------------------------------------------
# the register
# --------------------------------------------------------------------------
PACKAGES = (
    ("0", "Information required from others"),
    ("A", "Presentation and estimation"),
    ("B", "Architecture"),
    ("C", "Structure"),
    ("D", "Building services"),
    ("E", "Quantities and cost control"),
)

CLASSES = {
    "D": "derived from the geometry",
    "L": "layout for the engineer's design",
    "X": "external - cannot be produced here",
}


class Row:
    """One deliverable.

    `sheet` is a tuple because one of the client's codes can resolve to
    several of our sheets: ARC-200 "facade elevations" is seven.
    `source` names the geometry constants a class D document is measured
    off, and checks.py resolves each one, so a row cannot claim to be
    derived from something that is not there.
    """

    __slots__ = ("code", "title", "discipline", "scale", "fmt", "klass",
                 "package", "depends", "sheet", "doc", "source", "note",
                 "series", "index", "across")

    def __init__(self, code, title, package, klass, discipline="Architecture",
                 scale="-", fmt="A1 sheet", depends=(), sheet=(), doc=None,
                 source=(), note="", series=None, index=None, across=None):
        self.code = code
        self.title = title
        self.package = package
        self.klass = klass
        self.discipline = discipline
        self.scale = scale
        self.fmt = fmt
        self.depends = tuple(depends)
        self.sheet = (sheet,) if isinstance(sheet, str) else tuple(sheet)
        self.doc = doc
        self.source = tuple(source)
        self.note = note
        # A row belonging to a family that repeats once per level or once
        # per slab records which one it is, so checks.py can prove the
        # family covers the whole building rather than the three floors
        # the client's list assumed.
        self.series = series
        self.index = index
        self.across = across

    def __repr__(self):
        return f"<{self.code} {self.title!r} {self.klass}>"


def _package_0():
    return [
        Row("SUR-001", "Measured topographic and boundary survey", "0", "X",
            discipline="Survey", scale="1:200", fmt="Report + DWG",
            note="Boundaries on A-000 are indicative until this is in hand. "
                 "The north neighbour has not been surveyed at all."),
        Row("GEO-001", "Soil investigation and foundation recommendation",
            "0", "X", discipline="Geotechnical", fmt="Report",
            depends=("SUR-001",),
            note="Central Nile Delta ground is well characterised as a "
                 "region, and that is enough to assume a foundation type "
                 "for layout. It is not enough to size one: allowable "
                 "bearing pressure, the water table and sulphate content "
                 "are plot figures, and this row stays open until they "
                 "arrive with a source - boreholes, or figures the "
                 "engineer will sign."),
        Row("CLI-001", "Exterior scheme selection - A, B or C", "0", "X",
            discipline="Client decision", fmt="Written instruction",
            depends=("ARC-200",),
            note="Three skins are live on one agreed building. Finishes, "
                 "details and the finishes quantities all wait on this."),
    ]


def _package_a():
    rows = [
        Row("A-01", "Exterior views - axonometric, three schemes", "A", "D",
            discipline="Presentation", scale="1:250", sheet="A-430",
            note="A projection of the geometry, not a render: it cannot "
                 "show a balcony, a garden or a neighbour the drawings "
                 "do not have."),
    ]
    for i, name, ffl in levels():
        rows.append(Row(
            f"A-{i + 2:02d}", f"Interior cutaway axonometric - {name.lower()} "
            f"floor, {ffl}", "A", "D", discipline="Presentation",
            scale="1:100", source=("EL_LEVELS",),
            series="A interior cutaways", index=i, across="levels",
            note="Projected by axonometric.py from the same constants as "
                 "the floor plan."))
    rows += [
        Row("A-07", "Architectural design brief", "A", "D",
            discipline="Architecture", fmt="Report",
            depends=("ARC-101", "ARC-200"),
            source=("V3_X0", "V3_X1", "EL_LEVELS", "PLOT_W"),
            note="Accommodation, areas, levels and the reasoning behind "
                 "them, measured off the issued plans."),
        Row("A-08", "Cost estimation report - elemental", "A", "X",
            discipline="Cost", fmt="Report",
            depends=("QS-001", "QS-004"),
            note="Quantities are ours; rates are not. Every rate carries "
                 "its source or is shown as an open assumption."),
    ]
    return rows


def _package_b():
    plan_sheets = ["A-100", "A-101", "A-102", "A-103", "A-104"]
    rows = [
        Row("ARC-000", "Master deliverables list and document register",
            "B", "D", fmt="A1 sheet + Markdown", sheet="ARC-000",
            doc="master-deliverables-list.md",
            source=("EL_LEVELS", "V4_TOP"),
            note="This register. Status on it is derived at build time "
                 "from the sheet builders and the files on disk."),
        Row("ARC-001", "Cover sheet, project data and drawing index", "B",
            "D", depends=("ARC-000",), source=("EL_LEVELS",)),
        Row("ARC-002", "General notes, symbols and code compliance matrix",
            "B", "L",
            note="Notes and symbols are ours. The matrix is set against "
                 "ECP 201 and ECP 203, the Egyptian codes the site is "
                 "governed by, and signed off by the architect of record."),
        Row("ARC-100", "Context and master site plan", "B", "D",
            scale="1:75", sheet="A-000", depends=("SUR-001",),
            note="Issued with the boundary marked indicative."),
    ]
    for (i, name, ffl), number in zip(levels(), plan_sheets):
        rows.append(Row(
            f"ARC-{101 + i}", f"{name} floor plan, {ffl}", "B", "D",
            scale="1:50", sheet=number, source=("EL_LEVELS",),
            series="ARC floor plans", index=i, across="levels"))
    rows += [
        Row(f"ARC-{101 + len(G.EL_LEVELS)}",
            f"Roof plan over the penthouse, {slabs()[-1]}", "B", "D",
            scale="1:50", source=("V4_TOP", "V4_PLANT", "PARAPET"),
            note="Falls, outlets, parapets, water tanks and the plant "
                 "deck. Drawn nowhere in the set today."),
        Row("ARC-200", "Facade elevations - all four faces, three schemes",
            "B", "D", scale="1:50 / 1:75",
            sheet=("A-400", "A-401", "A-410", "A-411", "A-420", "A-421",
                   "A-402"),
            source=("FACADE", "EL_TOP"),
            note="Seven sheets: south and sides for each scheme, plus the "
                 "street elevation in context."),
        Row("ARC-300", "Longitudinal section A-A", "B", "D", scale="1:50",
            sheet="A-200", source=("EL_LEVELS",)),
        Row("ARC-301", "Transverse section B-B", "B", "D", scale="1:50",
            depends=("ARC-300",), source=("EL_LEVELS", "V3_Y0", "V3_Y1"),
            note="Cut east-west through the stair and the wave cantilever, "
                 "which section A-A runs parallel to and cannot show."),
    ]
    for i, name, ffl in levels():
        rows.append(Row(
            f"ARC-{400 + i}", f"Reflected ceiling plan - {name.lower()} "
            f"floor, {ffl}", "B", "D", scale="1:50",
            depends=(f"ARC-{101 + i}",), source=("FLOOR_TO_FLOOR",),
            series="ARC reflected ceiling plans", index=i, across="levels",
            note="Soffit levels, bulkheads and ceiling layout. Fittings "
                 "are indicative; the EL-200 series governs."))
    rows += [
        Row("ARC-500", "Door and window schedule", "B", "D", fmt="A1 sheet",
            depends=("ARC-200",), source=("FACADE", "FACADE_DOORS",
                                          "EL_SILL", "EL_HEAD"),
            note="Every opening in the building is already a constant, so "
                 "the schedule is measured rather than compiled."),
        Row("ARC-600", "Construction details", "B", "L", scale="1:5 / 1:10",
            depends=("CLI-001",),
            note="Balcony nosing, parapet, threshold, roof upstand. "
                 "Buildability, waterproofing and thermal performance are "
                 "the specifier's, not ours."),
        Row("ARC-700", "External works and landscape", "B", "D",
            scale="1:75", depends=("ARC-100",),
            source=("GARDEN_WALL_H", "SETBACK"),
            note="The entrance garden, gate, pergola, paving and barbecue "
                 "are drawn on A-000 and would otherwise fall straight "
                 "out of the quantities."),
    ]
    return rows


def _package_c():
    rows = [
        Row("STR-001", "Structural notes, materials and design criteria",
            "C", "L", discipline="Structure", fmt="A1 sheet",
            note="To ECP 203, with loads to ECP 201. The seismic zone and "
                 "its design ground acceleration, the wind basis and the "
                 "concrete grades are set and signed by the structural "
                 "engineer. No values assumed here."),
        Row("STR-100", "Excavation, grading and shoring", "C", "L",
            discipline="Structure", scale="1:100",
            depends=("GEO-001", "SUR-001")),
        Row("STR-101", "Foundation layout", "C", "L", discipline="Structure",
            scale="1:50", depends=("GEO-001", "STR-200"),
            note="Grid and column positions are exact; footing sizes, "
                 "depths and reinforcement are the engineer's."),
        Row("STR-200", "Column schedule and grid", "C", "L",
            discipline="Structure", scale="1:50",
            source=("EL_LEVELS",),
            note="Every column coordinate, carried through all five "
                 "levels. Sections and reinforcement left blank."),
    ]
    for i, z in enumerate(slabs()):
        note = ("The penthouse floor and the roof over the third floor are "
                "the same slab." if z == f"+{G.ROOF_LEVEL:.2f}" else "")
        rows.append(Row(
            f"STR-{301 + i}", f"Slab framing layout at {z}", "C", "L",
            discipline="Structure", scale="1:50",
            depends=("STR-200",), source=("EL_LEVELS", "V4_TOP"),
            series="STR slab framing", index=i, across="slabs", note=note))
    rows += [
        Row("STR-400", "Retaining and boundary walls", "C", "L",
            discipline="Structure", scale="1:50",
            depends=("SUR-001", "GEO-001"),
            note="Boundary line awaits the measured survey."),
        # the lowest slab that carries a balcony is the one over the ground
        # floor, level index 1
        Row("STR-500", "Cantilever balcony structure", "C", "L",
            discipline="Structure", scale="1:20",
            depends=("CLI-001", f"STR-{301 + 1}"),
            source=("V3_WAVE_LIMIT", "V3_WAVE_BALUSTRADE"),
            note="A 2.00 m curved cantilever repeated on four levels is "
                 "the most engineering-sensitive element in the building, "
                 "and had no deliverable in the list as given."),
    ]
    return rows


# system code, series, title, discipline
_MEP = (
    ("EL", 100, "Power and small power layout", "Electrical"),
    ("EL", 200, "Lighting and switching layout", "Electrical"),
    ("EL", 300, "Low voltage, data and security layout", "Electrical"),
    ("ME", 100, "HVAC layout", "Mechanical"),
    ("PL", 100, "Water supply layout", "Plumbing"),
    ("PL", 200, "Drainage layout", "Plumbing"),
)


def _package_d():
    rows = []
    for prefix, series, title, discipline in _MEP:
        for i, name, ffl in levels():
            rows.append(Row(
                f"{prefix}-{series + i}",
                f"{title} - {name.lower()} floor, {ffl}", "D", "L",
                discipline=discipline, scale="1:50",
                depends=(f"ARC-{101 + i}",), source=("EL_LEVELS",),
                series=f"{prefix}-{series}", index=i, across="levels",
                note="Coordination layout. Cable sizes, duct sizes, pipe "
                     "sizes and loads are the services engineer's."))
    rows += [
        Row("EL-400", "Electrical single line diagram", "D", "L",
            discipline="Electrical", fmt="A1 sheet", scale="Schematic",
            depends=("EL-100",),
            note="One diagram for the whole building, not one per level."),
        Row("ME-200", "HVAC schematic and plant arrangement", "D", "L",
            discipline="Mechanical", fmt="A1 sheet", scale="Schematic",
            depends=("ME-100", "ARC-106")),
        Row("PL-300", "Drainage and water riser diagram", "D", "L",
            discipline="Plumbing", fmt="A1 sheet", scale="Schematic",
            depends=("PL-100", "PL-200")),
    ]
    return rows


def _package_e():
    return [
        Row("QS-001", "Bill of quantities - itemised, unpriced, by trade",
            "E", "D", discipline="Quantity surveying", fmt="Spreadsheet",
            depends=("ARC-101", "ARC-700"),
            source=("V3_X0", "V3_X1", "V3_Y0", "V3_Y1", "EL_LEVELS",
                    "WT", "PT"),
            note="Measured off the geometry: wall lengths, slab areas and "
                 "opening counts reconcile to the plans they came from."),
        Row("QS-002", "Bill of materials", "E", "D",
            discipline="Quantity surveying", fmt="Spreadsheet",
            depends=("QS-001",), source=("WT", "PT", "PARAPET", "COL"),
            note="The same measure resolved into materials rather than "
                 "trades: blockwork, concrete, reinforcement allowance, "
                 "glazing and joinery."),
        Row("QS-003", "Material requisitions and specifications", "E", "L",
            discipline="Procurement", fmt="Schedule",
            depends=("QS-002", "CLI-001"),
            note="Quantities are ours; performance specifications and "
                 "approved-equal judgements are the specifier's."),
        Row("QS-004", "Owner's cost baseline", "E", "X",
            discipline="Cost", fmt="Spreadsheet", depends=("QS-001",),
            note="The measured quantities with a rate column, for "
                 "budgeting and for checking a quotation against. Rates "
                 "stay empty until a named source fills them - nothing "
                 "here goes out to tender."),
    ]


def register():
    """Every deliverable, in package order."""
    rows = (_package_0() + _package_a() + _package_b() + _package_c()
            + _package_d() + _package_e())
    return rows


def by_code():
    return {r.code: r for r in register()}


def by_package():
    """[(letter, title, rows)] - the register grouped for printing."""
    rows = register()
    return [(letter, title, [r for r in rows if r.package == letter])
            for letter, title in PACKAGES]


# --------------------------------------------------------------------------
# status, derived
# --------------------------------------------------------------------------
ISSUED, PROGRESS, BLOCKED, OPEN = ("issued", "in progress", "blocked",
                                   "not started")


def _sheet_numbers():
    """The sheets the set is issued as.

    `export_share.SET_ORDER` rather than a walk of `plans.SHEETS`,
    because ARC-000 is itself one of the sheets: building every sheet to
    find out what exists would re-enter the register while it is being
    drawn.  SET_ORDER is the right notion anyway - it is the issued set,
    which is why the withdrawn A-300 enlargements are not in it - and
    checks.py proves every number in it is one a builder produces.
    """
    import export_share
    return set(export_share.SET_ORDER)


def _renderable():
    """The document file names something here can actually write."""
    import documents
    return set(documents.RENDERS)


def status(row, numbers=None, renders=None):
    """issued / in progress / blocked / not started - never typed in.

    A deliverable exists when the project produces it: a sheet that is in
    the issued set, or a document `documents.RENDERS` writes.  Both are
    proved by checks.py - a row naming a sheet no builder draws, or a
    document nothing writes, fails there - so the register cannot claim
    something that is not real.

    Deliberately not "is the file on disk".  The register is itself one
    of the deliverables, so a status read off the output folder would
    depend on whether this build had yet reached the step that writes it,
    and ARC-000 would report on itself differently depending on the order
    the build ran in.  What a reader wants to know is what the project
    holds, not which files survived the last clean.

    A row with several artefacts - ARC-200 is seven sheets - is in
    progress while only some of them exist.
    """
    numbers = _sheet_numbers() if numbers is None else numbers
    renders = _renderable() if renders is None else renders

    have = [n in numbers for n in row.sheet]
    if row.doc:
        have.append(row.doc in renders)

    if have and all(have):
        return ISSUED
    if any(have):
        return PROGRESS
    return OPEN


def resolved(numbers=None, renders=None):
    """[(row, status)] with blocked rows worked out after the rest.

    Blocking is relative to what is issued, so it can only be settled
    once every row's own status is known.
    """
    numbers = _sheet_numbers() if numbers is None else numbers
    renders = _renderable() if renders is None else renders
    rows = register()
    state = {r.code: status(r, numbers, renders) for r in rows}
    for r in rows:
        if state[r.code] == OPEN and r.depends:
            if any(state.get(d) != ISSUED for d in r.depends):
                state[r.code] = BLOCKED
    return [(r, state[r.code]) for r in rows]


def tally(rows=None):
    """Counts by status, for the sheet and the notification line."""
    rows = rows if rows is not None else resolved()
    out = {ISSUED: 0, PROGRESS: 0, BLOCKED: 0, OPEN: 0}
    for _r, s in rows:
        out[s] += 1
    return out


def main():
    rows = resolved()
    state = {r.code: s for r, s in rows}
    for letter, title, group in by_package():
        print(f"\nPACKAGE {letter} - {title} ({len(group)})")
        for r in group:
            print(f"  {r.code:9s} {r.klass}  {state[r.code]:11s} {r.title}")
    counts = tally(rows)
    print(f"\n{len(rows)} deliverables: "
          + ", ".join(f"{n} {k}" for k, n in counts.items() if n))
    print("levels:", ", ".join(f"{n} {f}" for _i, n, f in levels()))
    print("slabs: ", ", ".join(slabs()))


if __name__ == "__main__":
    main()
