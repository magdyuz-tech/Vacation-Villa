#!/usr/bin/env python3
"""
export_cad.py - writes the drawings as editable DXF for free CAD software.

The same four sheet builders in `plans.py` are run against `DXFSheet`
instead of the SVG sheet, so the CAD files and the plotted sheets are drawn
by identical code.  Output is full-size metric model space in millimetres,
sorted onto standard architectural layers.

    python3 export_cad.py [output_dir]

Opens in LibreCAD, QCAD, FreeCAD, DraftSight, SketchUp, Sweet Home 3D
(Plan > Import background image / DXF) and the online planners.
"""

import os
import sys

import ezdxf

import drafting as D
import plans
from dxf_backend import DXFSheet, new_document

# builder, file name, layer suffix, x offset in the combined model (metres)
LEVELS = [
    (plans.sheet_site,   "A-000-site",         "-SITE", 0.0),
    (plans.sheet_ground, "A-100-ground-floor", "-00",  30.0),
    (plans.sheet_first,  "A-101-first-floor",  "-01",  60.0),
    (plans.sheet_second, "A-102-second-floor", "-02",  90.0),
    (plans.sheet_third,  "A-103-third-floor",  "-03", 120.0),
    (plans.sheet_section, "A-200-section",      "-SEC", 150.0),
]


def _run(builder, doc, offset=(0.0, 0.0), suffix=""):
    """Run a sheet builder against the DXF backend."""
    original = plans.Sheet

    def factory(number, title, level, scale_note="1:50"):
        return DXFSheet(number, title, level, scale_note, doc=doc,
                        offset=offset, suffix=suffix)

    plans.Sheet = factory
    try:
        return builder()
    finally:
        plans.Sheet = original


def export(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    written = []

    for builder, name, _suffix, _dx in LEVELS:
        doc = new_document()
        sh = _run(builder, doc)
        doc.header["$PROJECTNAME"] = f"{sh.number} {sh.title}"
        path = os.path.join(out_dir, name + ".dxf")
        doc.saveas(path)
        written.append((path, len(doc.modelspace())))

    # every level side by side in one model, each on its own layer set
    doc = new_document()
    for builder, _name, suffix, dx in LEVELS:
        _run(builder, doc, offset=(dx * 1000.0, 0.0), suffix=suffix)
    path = os.path.join(out_dir, "vacation-home-all-levels.dxf")
    doc.saveas(path)
    written.append((path, len(doc.modelspace())))
    return written


def audit(path):
    doc = ezdxf.readfile(path)
    auditor = doc.audit()
    layers = {}
    for e in doc.modelspace():
        layers[e.dxf.layer] = layers.get(e.dxf.layer, 0) + 1
    return auditor, layers


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "cad")
    for path, n in export(out):
        auditor, layers = audit(path)
        flag = "OK" if not auditor.errors else f"{len(auditor.errors)} ERRORS"
        print(f"{os.path.basename(path):34s} {n:5d} entities  "
              f"{len(layers):2d} layers  audit: {flag}")
