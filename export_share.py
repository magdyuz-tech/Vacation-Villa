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
# The A-300 enlargements are of apartment units that no longer exist, and
# A-410 to A-421 are exterior schemes B and C, which the client did not
# choose.  All of them stay in the repository and still build; they are
# simply not part of the issue.
SET_ORDER = ["ARC-001", "ARC-002", "ARC-000",
             "A-000", "A-100", "A-101", "A-102", "A-103", "A-104",
             "ARC-106",
             "A-200", "ARC-301", "A-400", "A-401", "A-402", "A-430",
             "ARC-500",
             "ARC-400", "ARC-401", "ARC-402", "ARC-403", "ARC-404",
             "ARC-700"]


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
        "/Creator": "floor-plans/plans.py",
    })
    path = os.path.join(out_dir, f"vacation-villa-drawing-set-{rev}.pdf")
    with open(path, "wb") as fh:
        writer.write(fh)
    return path, bound
