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
    "The north neighbour has not been surveyed. The north wall carries "
    "windows on every level, so the overlooking check on that face is "
    "open.",
    "Three exterior schemes are live on one agreed building. The scheme "
    "selection (CLI-001) gates the details, the finishes and the finishes "
    "quantities.",
    "Sheets A-300, A-301 and A-302 are enlargements of apartment units "
    "that no longer exist. They are already left out of the bound set and "
    "should be formally withdrawn rather than reissued.",
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

    w("## Open items")
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


# file name -> what writes it.  deliverables.status() reads the keys.
RENDERS = {"master-deliverables-list.md": write_markdown}


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
