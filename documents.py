#!/usr/bin/env python3
"""
documents.py - the written deliverables, rendered from the register.

    python3 documents.py [output_dir]      default: documents/

Two outputs from one source.  `markdown()` writes the Master Deliverables
List as a document anybody can read, and `register_table()` draws the same
rows on sheet ARC-000 so the set carries its own index.  Both read
`deliverables.register()`, so the sheet and the document cannot disagree
about what exists.

`RENDERS` maps a file name to the function that writes it.  It is also how
`deliverables.status()` knows a document is buildable rather than merely
wished for: a row naming a document nothing here renders reads as not
started.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import deliverables as DL

RULE = "Nothing is issued as engineering that has not been engineered."

PREAMBLE = """\
These documents are for the owner's own use: design record, build
information and cost planning.  They are not a tender issue - there is no
instruction to tenderers, no bid form and no document whose job is to be
priced by a competing contractor.

Every row carries a competence class, because a drawing that looks
engineered and is not gets built from by whoever holds it:
"""

OPEN_ITEMS = [
    "A measured topographic and boundary survey (SUR-001) is not in hand; "
    "boundaries on A-000 are issued marked indicative.",
    "The ground is central Nile Delta, which is well characterised as a "
    "region — enough to assume a foundation type and lay the structure "
    "out, not enough to size it. Allowable bearing pressure, the water "
    "table and sulphate content are plot figures, and GEO-001 stays open "
    "until they arrive with a source. No soil value is written on any "
    "sheet here.",
    "The north neighbour is a single storey, confirmed by the client. The "
    "north wall carries windows on all five levels; only the ground floor "
    "looks at anything, and from +3.30 up they clear its roof. Its exact "
    "height and position still come with SUR-001.",
    "The exterior is settled: scheme A, “Wave”, adopted at P18. Schemes B "
    "and C still build and stay in the repository as the record of what "
    "was offered, stamped not selected and left out of the issue.",
    "Sheets A-300, A-301 and A-302 are withdrawn at P22, being "
    "enlargements of apartments the villa does not have. They still "
    "build and stay in the repository as the record, stamped on the "
    "face and left out of the issue.",
    "Rates are class X throughout. No rate appears in any document here "
    "without a named source, and QS-004 is issued with its rate column "
    "open.",
]


# --------------------------------------------------------------------------
# the register as a document
# --------------------------------------------------------------------------
def markdown(rows=None):
    """The Master Deliverables List, as Markdown."""
    rows = rows if rows is not None else DL.resolved()
    state = {r.code: s for r, s in rows}
    out = []
    w = out.append

    import frame as F

    w("# Master Deliverables List")
    w("")
    w("Detached vacation villa — five levels, six structural slabs.")
    w("")
    w(f"**Site** — {F.LOCATION.title()}, in the central Nile Delta.")
    w(f"**Client** — {F.CLIENT.title()}.")
    w("")
    w("**Codes** — " + "; ".join(F.CODES) + ". ECP 201 (2012) divides "
      "Egypt into five seismic zones with design ground accelerations of "
      "0.10 g, 0.13 g, 0.15 g and 0.20 g for zones 1 to 4 and 0.25 g and "
      "0.30 g for zones 5a and 5b. Which zone governs this site, and the "
      "wind basis with it, is named by the structural engineer on "
      "STR-001 — it is not assumed here.")
    w("")
    w(f"> **{RULE}**")
    w("")
    w(PREAMBLE)
    for k in ("D", "L", "X"):
        w(f"- **{k}** — {DL.CLASSES[k]}")
    w("")
    w("Status on every row is derived at build time from the issued set "
      "and from the documents this project actually writes. It is not "
      "typed in, and `checks.py` fails the build if a row names a sheet "
      "nobody draws or a document nobody renders — so the register "
      "cannot claim a deliverable that is not there.")
    w("")

    w("## The building")
    w("")
    w("| | Level | Finished floor level |")
    w("| --- | --- | --- |")
    for i, name, ffl in DL.levels():
        w(f"| L{i} | {name} | {ffl} |")
    w("")
    w(f"Structural slabs: {', '.join(DL.slabs())} — six slabs to five "
      f"levels, because the slab at +{DL.G.ROOF_LEVEL:.2f} is the "
      f"penthouse floor and the roof over the third floor at once.")
    w("")

    counts = DL.tally(rows)
    w("## Summary")
    w("")
    w("| Package | Deliverables | Issued | In progress | Blocked | "
      "Not started |")
    w("| --- | --- | --- | --- | --- | --- |")
    for letter, title, group in DL.by_package():
        c = {k: 0 for k in (DL.ISSUED, DL.PROGRESS, DL.BLOCKED, DL.OPEN)}
        for r in group:
            c[state[r.code]] += 1
        w(f"| {letter} — {title} | {len(group)} | {c[DL.ISSUED]} | "
          f"{c[DL.PROGRESS]} | {c[DL.BLOCKED]} | {c[DL.OPEN]} |")
    w(f"| **Total** | **{len(rows)}** | **{counts[DL.ISSUED]}** | "
      f"**{counts[DL.PROGRESS]}** | **{counts[DL.BLOCKED]}** | "
      f"**{counts[DL.OPEN]}** |")
    w("")

    for letter, title, group in DL.by_package():
        w(f"## Package {letter} — {title}")
        w("")
        w("| Code | Deliverable | Discipline | Scale | Format | Class | "
          "Status | Waits on | Resolves to |")
        w("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in group:
            w(f"| {r.code} | {r.title} | {r.discipline} | {r.scale} | "
              f"{r.fmt} | {r.klass} | {state[r.code]} | "
              f"{', '.join(r.depends) or '—'} | "
              f"{', '.join(r.sheet) or '—'} |")
        w("")
        notes = [r for r in group if r.note]
        if notes:
            for r in notes:
                w(f"- **{r.code}** — {r.note}")
            w("")

    # not all of these are open any more - the scheme is chosen and the
    # A-300s are withdrawn - but a reader of the register needs the
    # settled ones as much as the open ones, and dropping a line the day
    # it is answered is how a register stops explaining itself.
    w("## Open items and standing qualifications")
    w("")
    for i, item in enumerate(OPEN_ITEMS, 1):
        w(f"{i}. {item}")
    w("")
    return "\n".join(out) + "\n"


def write_markdown(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "documents")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "master-deliverables-list.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(markdown())
    return path


# --------------------------------------------------------------------------
# the decisions record
# --------------------------------------------------------------------------
# What the client settled, when, and what each answer moved.  Written down
# because a decision that lives only in a conversation gets re-argued, and
# because several of these are the reason a drawing looks the way it does.
# Each one names the constant it became, so the record and the geometry
# cannot drift: a decision nobody implemented has nothing to point at.
DECISIONS = [
    ("2026-10-07", "Exterior scheme",
     "Scheme A, “Wave” — the serpentine balcony and the contemporary skin, "
     "chosen from three live options plus the curve then drawn.",
     "geometry.SCHEME / geometry.PROFILE",
     "The plans carried the superseded curve, 17.4 m² a floor to the full "
     "2.00 m. They are redrawn to the serpentine: 1.95 m at each end, "
     "0.75 m at the waist, 12.8 m² a floor. A-000 and A-100 to A-104 "
     "re-issued at P18; schemes B and C stamped not selected and dropped "
     "from the issue."),
    ("2026-10-07", "Internal partitions",
     "100 mm red brick, where the drawings had a 120 mm partition of "
     "unstated material.",
     "geometry.PT / geometry.WALL_MATERIAL",
     "Every partition is redrawn 20 mm thinner and the bill names the "
     "material. It also found a fault: six walls, 21.29 m of them, were "
     "set out between two hard-coded coordinates whose gap was 120 mm "
     "only because PT was, so they went on being drawn 120 mm and left "
     "the bill of quantities silently. Those walls now follow PT, and a "
     "check refuses any wall whose thickness is not a declared one."),
    ("2026-10-07", "External and party walls",
     "Brick, of any colour — the 300 mm walls, which had been left "
     "unspecified rather than assumed.",
     "geometry.WALL_MATERIAL",
     "The largest masonry item in the bill stops reading “material to be "
     "specified” — it is measured on QS-001 and named there. The "
     "colour being free is a decision and not a gap: both faces are "
     "plastered or rendered, so no brick on this building is ever seen "
     "and a facing brick would be bought and buried. The bill, the bill "
     "of materials and the key on every sheet that carries one now name "
     "it; the "
     "specification schedule stops asking for it and asks only for the "
     "size, strength and mortar. Nothing moved — no line on any drawing "
     "changes, because a material is not a dimension. The parapet is now "
     "the one wall nobody has specified."),
    ("2026-10-07", "Balcony waist",
     "The serpentine's waist deepened from 0.75 m to 1.35 m, holding the "
     "deep ends at 1.95 m under the 2.00 m cap.",
     "geometry.EL_SERP_MEAN / geometry.EL_SERP_AMP",
     "0.75 m was a planting ledge; 1.35 m is usable the whole way along "
     "the frontage. The curve now swings 0.60 m rather than 1.20 m, so it "
     "reads as a gentler wave, and carries 15.7 m² a floor instead of "
     "12.8 — 62.7 m² over the four balcony levels. It also overtakes "
     "scheme C's facet, which the C sheet used to beat it on. A-000 and "
     "A-100 to A-104 re-issued at P19."),
    ("2026-10-07", "Site",
     "Shamandeel, Quesna, Menoufia, Egypt — central Nile Delta.",
     "frame.LOCATION / frame.CODES",
     "Printed in the title block of every sheet. Fixes ECP 201 and ECP 203 "
     "as the governing codes, and with them the seismic and wind basis the "
     "structural engineer will name on STR-001."),
    ("2026-10-07", "Ground conditions",
     "Delta ground, known as a region; no site investigation commissioned.",
     "—",
     "Enough to assume a foundation type and lay the structure out, not "
     "enough to size one. GEO-001 stays open and no soil value is written "
     "on any sheet."),
    ("2026-10-07", "North neighbour",
     "A single storey, as on the east.",
     "geometry.NBR_N_STOREYS",
     "The last unknown face. Only the ground-floor north windows look at "
     "anything; from +3.30 up they clear its roof. Nothing in the plans "
     "had to move."),
]


def decisions_markdown():
    out = ["# Client Instructions and Decisions", "",
           "Every instruction that changed the drawings, grouped by what it "
           "changed rather than strictly by date — several were given in "
           "one sitting. Each one names the constant the decision became, "
           "so a decision cannot be recorded here and left unbuilt.", ""]
    for when, subject, decision, constant, effect in DECISIONS:
        out += [f"## {subject} — {when}", "",
                f"**Instruction.** {decision}", "",
                f"**Where it lives.** `{constant}`", "",
                f"**What it moved.** {effect}", ""]
    return "\n".join(out) + "\n"


def write_decisions(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "documents")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "client-decisions.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(decisions_markdown())
    return path


# --------------------------------------------------------------------------
# Package E - the measure, the materials, what must be specified, the rates
# --------------------------------------------------------------------------
# Four documents off one takeoff.  The bill is what was measured, the
# materials are the same measure resolved into things you buy, the
# specification schedule is what has to be decided before any of it can be
# bought, and the baseline is the bill with a rate column that stays empty
# until a named source fills it.
QS_HEAD = """\
Measured from `geometry.py`, not scaled off the drawings. Wall runs come
from the drawing calls themselves — the same calls the sheets are drawn
with — so the bill cannot drift from the building it bills for.

Every row carries a class: **D** measured here and exact, **L** needing
someone else's design before it can be measured, **X** impossible here at
all. **Nothing in this document is priced.**
"""

QS_EXCLUDED = [
    "Everything below ground. The foundation type is not chosen and its "
    "depth is not known; GEO-001 and STR-101 come first.",
    "Slab, beam and footing thicknesses, so no concrete volume is given "
    "for them. The areas are ours; the depths are the structural "
    "engineer's, and a volume needs both.",
    "Reinforcement, in any form.",
    "Services. The EL, ME and PL series are coordination layouts; their "
    "quantities follow the services engineer's design.",
    "Rates, overheads, preliminaries, profit and contingency.",
]


def _qs_rows():
    import quantities as Q
    return Q.by_trade()


def quantities_markdown():
    import quantities as Q

    out = ["# Bill of Quantities", "",
           "Detached vacation villa — Shamandeel, Quesna, Menoufia, Egypt.",
           "", "**Itemised, unpriced, by trade.**", "", QS_HEAD, ""]
    totals = {}
    for trade, items in _qs_rows():
        out += [f"## {trade}", "",
                "| Class | Description | Unit | Quantity | Note |",
                "| --- | --- | --- | ---: | --- |"]
        for i in items:
            q = "—" if i.qty is None else f"{i.qty:,.2f}"
            out.append(f"| {i.klass} | {i.desc} | {i.unit} | {q} | "
                       f"{i.note} |")
            totals[i.klass] = totals.get(i.klass, 0) + 1
        out.append("")
    out += ["## Excluded", ""]
    out += [f"{n}. {t}" for n, t in enumerate(QS_EXCLUDED, 1)]
    out += ["", f"{sum(totals.values())} items: "
                + ", ".join(f"{v} class {k}" for k, v in sorted(totals.items()))
                + ".", ""]
    return "\n".join(out)


def quantities_csv():
    rows = ["trade,class,description,unit,quantity,note"]
    for trade, items in _qs_rows():
        for i in items:
            q = "" if i.qty is None else f"{i.qty:.2f}"
            desc = i.desc.replace('"', "'")
            note = i.note.replace('"', "'").replace("\n", " ")
            rows.append(f'"{trade}",{i.klass},"{desc}",{i.unit},{q},"{note}"')
    return "\n".join(rows) + "\n"


def baseline_csv():
    """QS-004: the measure with a rate column nobody has filled."""
    import quantities as Q

    rows = ["trade,class,description,unit,quantity,rate,source,amount"]
    for trade, items in _qs_rows():
        for i in items:
            if i.klass != "D":
                continue            # only what is measured can be priced
            desc = i.desc.replace('"', "'")
            rows.append(f'"{trade}",D,"{desc}",{i.unit},{i.qty:.2f},,,')
    rows.append('"","","TOTAL","","",,,')
    return "\n".join(rows) + "\n"


def materials_markdown():
    """QS-002: the same measure, resolved into things you buy."""
    import quantities as Q
    import elevations as el
    import geometry as G

    items = Q.takeoff()
    def q(prefix):
        return next((i.qty for i in items if i.desc.startswith(prefix)), 0.0)

    sched = el.opening_schedule()
    def area(kind):
        return sum(r["w"] * r["h"] * r["total"]
                   for r in sched if r["kind"] == kind)

    _lifts, _h, col_vol = Q.columns()
    # All three masonry rows name their material out of geometry, the same
    # way the bill's labels do, so a wall that gets specified cannot leave
    # the material it used to be in this document.
    def mat(t, what):
        return f"{what}, {t * 1000:.0f} mm — {G.WALL_MATERIAL[t]}"

    rows = [
        (mat(G.WT, "External and party wall"), "m²", q("External and"), "D",
         "Brick, specified by the client, with no colour constraint: both "
         "faces are plastered or rendered, so a facing brick would be paid "
         "for and never seen. Unit size, strength and mortar are "
         "specification."),
        (mat(G.PT, "Internal partition"), "m²", q("Internal part"), "D",
         "Material specified by the client; a half-brick partition. "
         "Brick size, strength and mortar are still specification."),
        (mat(0.25, "Parapet"), "m²", q("Parapet"), "D",
         "The one wall left unspecified."),
        ("Concrete, columns", "m³", col_vol, "D",
         f"{G.COL * 1000:.0f} mm square × the storey height, measured. "
         f"Grade is the engineer's."),
        ("Concrete, slabs", "m³", None, "L",
         "Area is measured; the thickness is the engineer's."),
        ("Reinforcement", "t", None, "X", "The engineer's, entirely."),
        ("Glazing", "m²", area("window"), "D",
         "Structural opening area. Glass build-up is specification."),
        ("Door leaves and frames", "m²", area("door"), "D", ""),
        ("Louvres", "m²", area("vent"), "D", ""),
        ("Internal plaster", "m²", q("Internal plaster"), "D", ""),
        ("External render", "m²", q("External render"), "D", ""),
        ("Floor finish", "m²", q("Floor finish"), "D",
         "One figure; the split between finishes is specification."),
        ("Waterproofing membrane", "m²",
         sum(a for _n, _b, a in G.roof_zones()), "D", ""),
        ("Paving", "m²", sum(v for k, v in G.ew_areas().items()
                             if "Turf" not in k), "D", ""),
        ("Turf", "m²", G.ew_areas()["Turf"], "D", ""),
        ("Timber, pergola", "m²", G.EW_PERGOLA[2] * G.EW_PERGOLA[3], "D", ""),
        ("Trees", "nr", float(len(G.EW_TREES)), "D", ""),
    ]
    out = ["# Bill of Materials", "",
           "The same measure as QS-001, resolved into materials rather "
           "than trades.", "", QS_HEAD, "",
           "| Class | Material | Unit | Quantity | Note |",
           "| --- | --- | --- | ---: | --- |"]
    for desc, unit, qty, klass, note in rows:
        v = "—" if qty is None else f"{qty:,.2f}"
        out.append(f"| {klass} | {desc} | {unit} | {v} | {note} |")
    out += ["", "## Excluded", ""]
    out += [f"{n}. {t}" for n, t in enumerate(QS_EXCLUDED, 1)]
    return "\n".join(out) + "\n"


# What has to be decided before any of the measure can be bought.  Topics,
# not specifications: naming a block strength or a membrane here would be
# inventing the one thing this document exists to ask for.
SPEC_TOPICS = [
    ("Masonry", "Both walls are brick, specified by the client: the 100 mm "
                "partitions red, the 300 mm external and party walls any "
                "colour. Still to be specified: brick size and strength, "
                "the parapet's material, mortar, movement joints, wall "
                "ties and lintels over every opening."),
    ("Concrete", "Grade, cover, aggregate and finish — all to the "
                 "structural engineer's specification, not this one."),
    ("Openings", "Frame material and finish, glazing build-up and "
                 "performance, operation, ironmongery, seals and "
                 "thresholds. ARC-500 measures the openings; none of this "
                 "is in them."),
    ("Internal finishes", "Plaster system, paint, which rooms are tiled "
                          "and to what height, floor finish per room, "
                          "skirtings and junctions."),
    ("External finishes", "Render system and colour, the slab nosing and "
                          "its cove light, balustrade glass and fixings."),
    ("Roof", "Membrane, insulation, falls screed, upstands, outlets and "
             "overflows, protection and the walking surface."),
    ("External works", "Paving material and bedding, sub-base, falls, "
                       "edgings, turf and topsoil, irrigation, the gate, "
                       "the street wall's coping and finish."),
    ("Services", "Everything. The EL, ME and PL series are coordination "
                 "only."),
]


def specification_markdown():
    out = ["# Material Requisitions and Specification Schedule", "",
           "What has to be decided before the measure can be bought.", "",
           "These are topics, not specifications. Naming a block strength "
           "or a membrane here would be inventing the one thing this "
           "document exists to ask for — it is issued so that whoever "
           "specifies has a complete list to answer, and so that nothing "
           "is priced against an assumption nobody wrote down.", "",
           "| Trade | To be specified |", "| --- | --- |"]
    for trade, topics in SPEC_TOPICS:
        out.append(f"| {trade} | {topics} |")
    out += ["", "Quantities for every item above are in QS-001 and QS-002 "
                "where the geometry fixes them, and are marked class L or "
                "X where it does not.", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------
# Package A - the brief, and the estimate that cannot be totalled
# --------------------------------------------------------------------------
def brief_markdown():
    """A-07: what was asked for, what was built, and why it looks like it."""
    import frame as F
    import geometry as G
    import plans
    import quantities as Q

    _w, rooms = Q.walls()
    gross = (G.V3_X1 - G.V3_X0) * (G.V3_Y1 - G.V3_Y0)
    net = sum(sum(a for _n, a in rooms[lv]) for lv in rooms)
    outside, _m = G.ew_unallocated()

    out = ["# Architectural Design Brief", "",
           f"**{F.PROJECT.title()}** — {F.LOCATION.title()}.", "",
           "Written from the drawings rather than before them: every "
           "figure below is measured from the same geometry the set is "
           "drawn from, so the brief describes the building that exists "
           "rather than the one that was intended.", ""]

    out += ["## The site", "",
            f"- Plot {G.plot_area():.1f} m², an L on a street frontage "
            f"{G.PLOT[1][0]:.2f} m wide.",
            f"- The house sits hard against the east boundary with a "
            f"{G.SETBACK:.2f} m paved side passage, and the whole "
            f"{G.V3_X0 - G.SETBACK:.2f} m entrance garden on the west. It "
            f"is not in the middle of its plot, and the drawings show "
            f"that rather than a symmetrical fiction.",
            f"- Neighbours: west {G.NBR_W_STOREYS} storeys and blind "
            f"toward the garden, east {G.NBR_E_STOREYS} storey in clay "
            f"brick {G.SETBACK:.2f} m away, north {G.NBR_N_STOREYS} "
            f"storey. The east wall can be glazed at all because of that "
            f"single storey: the lowest east sill at "
            f"+{G.FLOOR_TO_FLOOR + G.EL_SILL:.2f} clears its roof by "
            f"{G.FLOOR_TO_FLOOR + G.EL_SILL - G.NBR_E_STOREYS * G.NBR_STOREY_H:.2f} m.",
            f"- Setbacks of {G.SETBACK:.2f} m on three sides, which are "
            f"our own land and are paved as side passages rather than "
            f"left dead.", ""]

    out += ["## The building", "",
            "| | Level | FFL | Rooms | Net internal |",
            "| --- | --- | --- | ---: | ---: |"]
    for i, name, ffl in [(i, n, f"+{G.EL_LEVELS[i]:.2f}")
                         for i, n, _f in plans.RCP_LEVELS]:
        here = rooms[i]
        out.append(f"| L{i} | {name} | {ffl} | {len(here)} | "
                   f"{sum(a for _n, a in here):.1f} m² |")
    out += ["", f"Gross plate {gross:.1f} m² a floor over four floors and "
                f"a set-back penthouse; {net:.1f} m² net internal in all. "
                f"{outside:.1f} m² of the plot lies outside the building.",
            "",
            f"- {G.FLOOR_TO_FLOOR:.2f} m floor to floor, "
            f"{G.CLEAR_HEIGHT:.2f} m clear under a "
            f"{G.STRUCTURAL_ZONE * 1000:.0f} mm structural zone, top of "
            f"building +{G.EL_TOP:.2f}.",
            f"- Eleven numbered bedrooms and a guest room, each with its "
            f"own or a shared bath; the wet rooms stack on one riser in "
            f"the east strip, measured on PL-200.",
            f"- A private stair, {round(G.FLOOR_TO_FLOOR / G.V3_STAIR_RISE)}"
            f"R at {1000 * G.FLOOR_TO_FLOOR / round(G.FLOOR_TO_FLOOR / G.V3_STAIR_RISE):.0f}"
            f" × {G.V3_STAIR_GOING * 1000:.0f}, in an open well with no "
            f"enclosure and no lift.", ""]

    out += ["## The street front", "",
            f"Scheme {G.SCHEME}, \"{plans.el.SCHEME[G.SCHEME]['name']}\", "
            f"chosen from three. A serpentine cantilever of one full "
            f"period across the {G.V3_X1 - G.V3_X0:.2f} m frontage, "
            f"{G.V3_WAVE_DEEP:.2f} m deep at each end and "
            f"{G.V3_WAVE_WAIST:.2f} m at the waist — "
            f"{G.wave_area():.1f} m² a floor, {4 * G.wave_area():.1f} m² "
            f"over the four levels that carry it.", "",
            f"The waist was 0.75 m when the scheme was adopted and was "
            f"deepened to {G.V3_WAVE_WAIST:.2f} m so the balcony is "
            f"usable along its whole length rather than only at the ends. "
            f"That cost the curve half its swing and gained 2.9 m² a "
            f"floor.", "",
            "The balconies stop at the corner on every level: the 1.00 m "
            "setbacks forbid anything projecting west, north or east, so "
            "the cantilever stays on the street frontage.", ""]

    out += ["## What the drawings do not decide", ""]
    out += [f"- {t}" for t in OPEN_ITEMS]
    out += ["", "The set is issued for the owner's record, costing and "
                "construction information. It is not a tender issue and "
                "it is not for construction.", ""]
    return "\n".join(out)


def estimate_markdown():
    """A-08: the elemental estimate, and why it has no total."""
    import geometry as G
    import quantities as Q

    items = [i for i in Q.takeoff() if i.klass == "D" and i.qty is not None]
    gross = (G.V3_X1 - G.V3_X0) * (G.V3_Y1 - G.V3_Y0) * 4 + G.V4_PLATE

    out = ["# Cost Estimation Report", "",
           f"**{len(items)} measured items. No total.**", "",
           "This report is class **X**: it cannot be completed here. The "
           "quantities are ours and exact; the rates are not ours at all, "
           "and an elemental estimate is quantities times rates.", "",
           "What follows is therefore the estimate with every quantity "
           "filled in and every rate left open, which is the honest shape "
           "of it. Filling the rate column from memory or from another "
           "country's prices would produce a number, and the number would "
           "be believed.", "",
           "## What is needed to complete it", "",
           "1. Current rates for Menoufia, from a named source — a local "
           "quantity surveyor, a recent comparable build, or quotations.",
           "2. The structural design, which fixes the concrete and "
           "reinforcement that are the largest single element in a frame "
           "like this and are not measurable yet (STR series, class L).",
           "3. The services design, same reason (EL, ME and PL series).",
           "4. The specification, which decides what the finishes are "
           "(QS-003).",
           "5. Preliminaries, overheads, profit, contingency and "
           "professional fees, none of which is a quantity.", "",
           "## The measured elements", "",
           "| Element | Item | Unit | Quantity | Rate | Source | Amount |",
           "| --- | --- | --- | ---: | ---: | --- | ---: |"]
    for i in items:
        out.append(f"| {i.trade} | {i.desc} | {i.unit} | {i.qty:,.2f} | | | |")
    out += ["| | | | | | **Total** | **not calculable** |", "",
            f"Gross floor area {gross:.1f} m², which is the divisor for a "
            f"cost per square metre once rates exist. It is given so the "
            f"figure can be worked out, not so a figure can be guessed.",
            "",
            "## Excluded", ""]
    out += [f"{n}. {t}" for n, t in enumerate(QS_EXCLUDED, 1)]
    out.append("")
    return "\n".join(out)


def _writer(name, render):
    def write(out_dir=None):
        out_dir = out_dir or os.path.join(HERE, "documents")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render())
        return path
    return write


# file name -> what writes it.  deliverables.status() reads the keys.
RENDERS = {"master-deliverables-list.md": write_markdown,
           "client-decisions.md": write_decisions,
           "bill-of-quantities.md": _writer("bill-of-quantities.md",
                                            quantities_markdown),
           "bill-of-quantities.csv": _writer("bill-of-quantities.csv",
                                             quantities_csv),
           "bill-of-materials.md": _writer("bill-of-materials.md",
                                           materials_markdown),
           "specification-schedule.md": _writer("specification-schedule.md",
                                                specification_markdown),
           "cost-baseline.csv": _writer("cost-baseline.csv", baseline_csv),
           "design-brief.md": _writer("design-brief.md", brief_markdown),
           "cost-estimation-report.md": _writer("cost-estimation-report.md",
                                                estimate_markdown)}


# --------------------------------------------------------------------------
# the register on a sheet
# --------------------------------------------------------------------------
# Two columns in the drawing area; the right-hand panel is the frame's.
COL_X = (18.0, 300.0)
COL_TOP = 50.0
COL_BOTTOM = 566.0
PITCH = 7.0             # one row; text is clamped to 4.23 mm, so this is tight
HEAD_PITCH = 13.0       # a package heading, with air above it

# offsets within a column
C_CODE, C_CLASS, C_STATUS, C_TITLE, C_SCALE = 0.0, 26.0, 34.0, 68.0, 256.0

STATUS_INK = {
    DL.ISSUED: "#141414",
    DL.PROGRESS: "#5d5d5d",
    DL.BLOCKED: "#141414",
    DL.OPEN: "#9a9a9a",
}
# Status is carried by a mark as well as a tint, for the same reason the
# plans tag the per-cent columns with a symbol: tint alone is not legible
# in a monochrome print or to a colour-blind reader.
STATUS_MARK = {DL.ISSUED: "+", DL.PROGRESS: ">", DL.BLOCKED: "!",
               DL.OPEN: "·"}


def register_table(sh, rows=None):
    """Draw the whole register in the drawing area of a sheet.

    Only `sh` methods are used, so this runs against the DXF backend
    unchanged.
    """
    from drafting import INK, GREY, LIGHT

    rows = rows if rows is not None else DL.resolved()
    state = {r.code: s for r, s in rows}

    sh.text_mm(COL_X[0], 26, "MASTER DELIVERABLES LIST", size=6.0,
               anchor="start", weight=700, ls=0.6)
    sh.text_mm(COL_X[0], 35,
               f"{len(rows)} DELIVERABLES   ·   "
               f"{len(DL.levels())} LEVELS, {len(DL.slabs())} SLABS   ·   "
               f"STATUS DERIVED AT BUILD TIME", size=2.6, anchor="start",
               color=GREY, ls=0.35)
    sh.line_mm(COL_X[0], 40, COL_X[1] + C_SCALE, 40, w=0.5, color=INK)

    def column_head(x, y):
        for off, txt, anc in ((C_CODE, "CODE", "start"),
                              (C_CLASS, "CL", "start"),
                              (C_STATUS, "STATUS", "start"),
                              (C_TITLE, "DELIVERABLE", "start"),
                              (C_SCALE, "SCALE", "end")):
            sh.text_mm(x + off, y, txt, size=2.0, anchor=anc, color=GREY,
                       ls=0.4)
        sh.line_mm(x, y + 2.0, x + C_SCALE, y + 2.0, w=0.25, color=GREY)

    def package_head(x, y, letter, title, n):
        sh.text_mm(x, y + 4.0,
                   f"PACKAGE {letter} — {title.upper()} ({n})", size=2.6,
                   anchor="start", weight=700, ls=0.4)

    def deliverable(x, y, r):
        s = state[r.code]
        sh.text_mm(x + C_CODE, y, r.code, size=2.2, anchor="start",
                   weight=700)
        sh.text_mm(x + C_CLASS, y, r.klass, size=2.2, anchor="start",
                   color=GREY)
        sh.text_mm(x + C_STATUS, y, f"{STATUS_MARK[s]} {s}", size=2.1,
                   anchor="start", color=STATUS_INK[s])
        sh.text_mm(x + C_TITLE, y, r.title, size=2.2, anchor="start")
        sh.text_mm(x + C_SCALE, y, r.scale, size=2.1, anchor="end",
                   color=GREY)
        sh.line_mm(x, y + 1.6, x + C_SCALE, y + 1.6, w=0.12, color="#e2e2e2")

    # One flat list of (height, draw) first, so the break between the two
    # columns can be chosen to balance them rather than taken wherever the
    # first column happens to run out.
    items = []
    for letter, title, group in DL.by_package():
        items.append((HEAD_PITCH, letter,
                      lambda x, y, a=letter, b=title, n=len(group):
                      package_head(x, y, a, b, n)))
        for r in group:
            items.append((PITCH, None,
                          lambda x, y, r=r: deliverable(x, y, r)))
        items.append((2.0, None, None))

    top = COL_TOP + 9.0
    room = COL_BOTTOM - top
    heights = [h for h, _k, _d in items]
    total = sum(heights)

    def tallest(i):
        return max(sum(heights[:i]), sum(heights[i:]))

    # prefer breaking between packages; fall back to any row if no package
    # boundary leaves both columns on the sheet
    breaks = [i for i, (_h, k, _d) in enumerate(items) if k] or [len(items)]
    cut = min(breaks, key=tallest)
    if tallest(cut) > room:
        cut = min(range(1, len(items)), key=tallest)
    if tallest(cut) > room:
        raise ValueError(
            f"ARC-000: the register is {total:.0f} mm of rows and two "
            f"columns hold {2 * room:.0f} mm - it needs a second sheet")

    for col, part in enumerate((items[:cut], items[cut:])):
        x, y = COL_X[col], top
        column_head(x, COL_TOP)
        for h, _k, draw in part:
            if draw is not None:
                draw(x, y)
            y += h
    sh.text_mm(COL_X[1], COL_BOTTOM + 6, "+ ISSUED   > IN PROGRESS   "
               "! BLOCKED   · NOT STARTED", size=2.0, anchor="start",
               color=LIGHT, ls=0.4)
    return total


def main(out=None):
    """Write every document. Returns the paths, in file-name order."""
    out = out or os.path.join(HERE, "documents")
    return [render(out) for _name, render in sorted(RENDERS.items())]


if __name__ == "__main__":
    for p in main(sys.argv[1] if len(sys.argv) > 1 else None):
        print(f"{os.path.basename(p):42s} "
              f"{os.path.getsize(p) / 1024:6.1f} kB")
