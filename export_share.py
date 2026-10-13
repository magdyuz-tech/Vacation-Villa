#!/usr/bin/env python3
"""
export_share.py - PDF and PNG issues of the sheets, for printing and for
tracing as a background in the free planners.

    python3 export_share.py [dpi]

PDF keeps the sheets vector and true to size (ISO A1, 841 x 594 mm), so they
print to scale from any free PDF reader.  PNG is what Sweet Home 3D's
Plan > Import background image wizard accepts, along with the online
planners that let you trace over an uploaded plan.
"""

import glob
import os
import sys

import cairosvg

A1_W_MM = 841.0

# cairo stamps every PDF with the moment it was written, and honours no
# SOURCE_DATE_EPOCH, so all 81 PDFs were rewritten on every build whether
# or not a drawing had moved.  The date tells a reader nothing the title
# block does not say better, and it cost the one thing this project uses
# to find out what changed: rebuild, and see which files differ.  So the
# metadata is flattened to the issue date after each file is written.
# Only the document information is touched - page geometry, the content
# stream and the embedded font subsets are copied through untouched.
_PDF_EPOCH = "D:{0}000000Z"


def _pin_pdf(path):
    """Replace cairo's build-time metadata with the set's issue date."""
    from pypdf import PdfReader, PdfWriter
    import frame

    reader = PdfReader(path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    stamp = _PDF_EPOCH.format(frame.DATE.replace("-", ""))
    writer.add_metadata({"/Producer": "vacation-villa",
                         "/CreationDate": stamp, "/ModDate": stamp})
    with open(path, "wb") as fh:
        writer.write(fh)


def export(svg_dir, pdf_dir, png_dir, dpi=150):
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    px = int(round(A1_W_MM / 25.4 * dpi))
    out = []
    for svg in sorted(glob.glob(os.path.join(svg_dir, "*.svg"))):
        base = os.path.splitext(os.path.basename(svg))[0]
        pdf = os.path.join(pdf_dir, base + ".pdf")
        png = os.path.join(png_dir, base + ".png")
        cairosvg.svg2pdf(url=svg, write_to=pdf)
        _pin_pdf(pdf)
        cairosvg.svg2png(url=svg, write_to=png, output_width=px,
                         background_color="white")
        out.append((pdf, png))
    return out, px


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    dpi = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    files, px = export(os.path.join(here, "drawings"),
                       os.path.join(here, "pdf"),
                       os.path.join(here, "png"), dpi)
    print(f"{dpi} dpi -> {px} px wide")
    for pdf, png in files:
        print(f"  {os.path.basename(pdf):42s} "
              f"{os.path.getsize(pdf) / 1024:7.0f} kB pdf  "
              f"{os.path.getsize(png) / 1024:7.0f} kB png")

# the sheets the villa set is issued as, in the order they are read.  Two
# groups are left out on purpose, both for the same reason: binding them
# would hand the reader drawings of a building that is not being built.
# The A-300 enlargements are of apartment units that no longer exist and
# are withdrawn at P22, and A-410 to A-421 are exterior schemes B and C,
# which the client did not choose.  All of them stay in the repository and
# still build; they are simply not part of the issue, and each says so on
# its own face - `checks.out_of_the_issue_says_why` refuses a sheet that
# leaves this list without a stamp, or arrives in it carrying one.
SET_ORDER = ["ARC-001", "ARC-002", "ARC-000",
             "A-000", "A-100", "A-101", "A-102", "A-103", "A-104",
             "ARC-106",
             "A-200", "ARC-301", "A-400", "A-401", "A-402", "A-430",
             "ARC-500", "ARC-600",
             "ARC-400", "ARC-401", "ARC-402", "ARC-403", "ARC-404",
             "ARC-700",
             "STR-001", "STR-100", "STR-101", "STR-200",
             "STR-301", "STR-302", "STR-303", "STR-304",
             "STR-305", "STR-306", "STR-400", "STR-500",
             "EL-100", "EL-101", "EL-102", "EL-103", "EL-104",
             "EL-200", "EL-201", "EL-202", "EL-203", "EL-204",
             "EL-300", "EL-301", "EL-302", "EL-303", "EL-304",
             "ME-100", "ME-101", "ME-102", "ME-103", "ME-104",
             "PL-100", "PL-101", "PL-102", "PL-103", "PL-104",
             "PL-200", "PL-201", "PL-202", "PL-203", "PL-204",
             "EL-400", "ME-200", "PL-300",
             "A-02", "A-03", "A-04", "A-05", "A-06"]


def bind(pdf_dir, out_dir=None, rev=None):
    """One combined PDF of the whole issued set, in sheet order."""
    from pypdf import PdfReader, PdfWriter

    import frame as F

    rev = rev or F.REVISIONS[-1][0]
    out_dir = out_dir or pdf_dir
    files = sorted(os.listdir(pdf_dir))
    writer, bound = PdfWriter(), []
    for number in SET_ORDER:
        hit = [f for f in files if f.startswith(number) and f.endswith(".pdf")]
        if len(hit) != 1:
            raise SystemExit(f"{number}: expected one sheet, found {hit}")
        reader = PdfReader(os.path.join(pdf_dir, hit[0]))
        for page in reader.pages:
            writer.add_page(page)
        bound.append(hit[0])
    writer.add_metadata({
        "/Title": f"Detached Vacation Villa - drawing set, revision {rev}",
        "/Subject": "Master deliverables list, site plan, five floor "
                    "plans, section A-A and the exterior schemes. "
                    "Final draft, not for construction.",
        "/Creator": "plans.py",
        "/Producer": "vacation-villa",
        # the bound set is dated by its issue, like every sheet in it
        "/CreationDate": _PDF_EPOCH.format(F.DATE.replace("-", "")),
        "/ModDate": _PDF_EPOCH.format(F.DATE.replace("-", "")),
    })
    path = os.path.join(out_dir, f"vacation-villa-drawing-set-{rev}.pdf")
    with open(path, "wb") as fh:
        writer.write(fh)
    return path, bound
