#!/usr/bin/env python3
"""
build.py - produce the whole drawing set in every format, in one pass.

    python3 build.py

    drawings/  SVG sheets, ISO A1               (Inkscape, Figma, browsers)
    cad/       DXF, metric, 1:1 model space     (LibreCAD, QCAD, FreeCAD)
    pdf/       vector sheets, true to size      (print to scale)
    png/       150 dpi sheets                   (trace in the online planners)
    drawing-set.html  all four sheets offline, with zoom and pan

Everything is generated from `geometry.py`, so a dimension changed there
flows into every format on the next build.  `checks.py` runs first and
stops the build if a door, window or opening has gone astray.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    import checks
    import plans
    import viewer
    import export_cad
    import export_share

    print("checks")
    if checks.main():
        raise SystemExit("fix the plans before issuing the set")

    print("\nsheets (svg)")
    svgs = plans.main()

    print("\ncad (dxf)")
    for path, n in export_cad.export(os.path.join(HERE, "cad")):
        auditor, layers = export_cad.audit(path)
        state = "OK" if not auditor.errors else f"{len(auditor.errors)} ERRORS"
        print(f"{os.path.basename(path):34s} {n:5d} entities  "
              f"{len(layers):2d} layers  audit: {state}")

    print("\npdf + png")
    files, px = export_share.export(os.path.join(HERE, "drawings"),
                                    os.path.join(HERE, "pdf"),
                                    os.path.join(HERE, "png"), dpi=150)
    for pdf, png in files:
        print(f"{os.path.basename(pdf):34s} "
              f"{os.path.getsize(pdf) / 1024:6.0f} kB pdf   "
              f"{os.path.getsize(png) / 1024:6.0f} kB png ({px}px)")

    print("\nbound set")
    path, bound = export_share.bind(os.path.join(HERE, "pdf"), HERE)
    print(f"{os.path.basename(path):34s} "
          f"{os.path.getsize(path) / 1024:6.0f} kB   {len(bound)} sheets")

    print("\nviewer")
    out = viewer.build(os.path.join(HERE, "drawings"),
                       os.path.join(HERE, "drawing-set.html"))
    print(f"{os.path.basename(out):34s} {os.path.getsize(out) / 1024:6.0f} kB")
    return svgs


if __name__ == "__main__":
    main()
