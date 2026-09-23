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
