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
import re
import sys

import ezdxf

import drafting as D
import frame
import plans
from dxf_backend import DXFSheet, new_document

# builder, file name, layer suffix, x offset in the combined model (metres)
LEVELS = [
    (plans.sheet_site,   "A-000-site",         "-SITE", 0.0),
    (plans.sheet_ground, "A-100-ground-floor", "-00",  30.0),
    (plans.sheet_first,  "A-101-first-floor",  "-01",  60.0),
    (plans.sheet_second, "A-102-second-floor", "-02",  90.0),
    (plans.sheet_third,  "A-103-third-floor",  "-03", 120.0),
    (plans.sheet_penthouse, "A-104-penthouse", "-04", 150.0),
    (plans.sheet_section, "A-200-section",      "-SEC", 180.0),
    (plans.sheet_elev_a,       "A-400-elev-south-scheme-a", "-ELA", 210.0),
    (plans.sheet_elev_a_sides, "A-401-elev-sides-scheme-a", "-ELA", 240.0),
    (plans.sheet_elev_b,       "A-410-elev-south-scheme-b", "-ELB", 285.0),
    (plans.sheet_elev_b_sides, "A-411-elev-sides-scheme-b", "-ELB", 315.0),
    (plans.sheet_elev_c,       "A-420-elev-south-scheme-c", "-ELC", 360.0),
    (plans.sheet_elev_c_sides, "A-421-elev-sides-scheme-c", "-ELC", 390.0),
    (plans.sheet_street_context, "A-402-street-context", "-CTX", 435.0),
    (plans.sheet_axonometric, "A-430-axonometric", "-AXO", 480.0),
]

# enlargements are the same geometry at a larger plotted scale, so they add
# nothing to a 1:1 CAD model and are not exported as separate DXF files


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


# ezdxf writes its own version-and-timestamp stamp into the file at save
# time, so unlike the header variables it cannot be pinned beforehand.
# DXF is a plain line-based format with no offset table, so rewriting the
# stamp in the saved text is safe.
_EZDXF_STAMP = re.compile(r"\d+\.\d+\.\d+ @ [0-9T:.+-]+")


# Set as the file is saved rather than when it is built, so unlike the
# rest of the header these cannot be pinned on the document beforehand.
_PINNED_AT_SAVE = {
    "$TDUPDATE": None,            # filled from $TDCREATE, which is pinned
    "$TDUUPDATE": None,
    "$VERSIONGUID": "{00000000-0000-0000-0000-000000000002}",
}


def _pin_save(doc, path):
    """saveas, then flatten what ezdxf stamps into the file as it saves.

    DXF is a line-based format with no offset table, so a value may be
    rewritten in place without disturbing anything around it.  The header
    is a flat run of `9 / $NAME / <group> / <value>`, which puts a
    variable's value two lines after its name.
    """
    doc.saveas(path)
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    created = f"{doc.header['$TDCREATE']}"
    for i, line in enumerate(lines):
        name = line.strip()
        if name in _PINNED_AT_SAVE and i + 2 < len(lines):
            value = _PINNED_AT_SAVE[name] or created
            lines[i + 2] = value
    text = _EZDXF_STAMP.sub("vacation-villa", "\n".join(lines))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def deterministic_ordering():
    """Re-exec with a fixed hash seed, once, before any document is built.

    ezdxf emits part of the OBJECTS section in the iteration order of a
    set of strings, so the order of two entries follows the interpreter's
    hash randomisation and changes run to run.  Everything else about the
    file is pinned; this is the only cause that cannot be fixed from
    inside the process, because the seed is fixed at interpreter start.
    """
    if os.environ.get("PYTHONHASHSEED") == "0":
        return
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)


def export(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    written = []

    for builder, name, _suffix, _dx in LEVELS:
        doc = new_document()
        sh = _run(builder, doc)
        rev = getattr(sh, "rev", None) or frame.REV
        doc.header["$PROJECTNAME"] = f"{sh.number} {sh.title} ({rev})"
        # the revision rides in the file name here too, for the same reason
        # it does on the SVG: a stale DXF in a folder is otherwise invisible
        path = os.path.join(out_dir, f"{name}-{rev}.dxf")
        _pin_save(doc, path)
        written.append((path, len(doc.modelspace())))

    # every level side by side in one model, each on its own layer set
    doc = new_document()
    for builder, _name, suffix, dx in LEVELS:
        _run(builder, doc, offset=(dx * 1000.0, 0.0), suffix=suffix)
    path = os.path.join(out_dir, "vacation-villa-all-levels.dxf")
    _pin_save(doc, path)
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
    deterministic_ordering()
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "cad")
    for path, n in export(out):
        auditor, layers = audit(path)
        flag = "OK" if not auditor.errors else f"{len(auditor.errors)} ERRORS"
        print(f"{os.path.basename(path):34s} {n:5d} entities  "
              f"{len(layers):2d} layers  audit: {flag}")
