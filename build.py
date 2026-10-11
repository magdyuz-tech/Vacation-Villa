#!/usr/bin/env python3
"""
build.py - produce the whole drawing set in every format, in one pass.

    python3 build.py

    documents/ written deliverables, Markdown   (the register, reports)
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


def prune(directory, keep):
    """Delete superseded issues of the sheets just written.

    The revision is part of every file name on purpose, so a stale issue
    sitting in a folder is obvious rather than silently overwritten.  The
    cost is that a re-issue leaves the old file behind, and the next build
    finds two candidates for one sheet and cannot bind the set.  So the
    build removes them: `keep` is the file name each sheet was written as,
    and anything else beginning with the same drawing number is a previous
    issue of a drawing that has just been superseded.
    """
    gone = []
    for name in sorted(os.listdir(directory)):
        stem = os.path.splitext(name)[0]
        for number, basename in keep.items():
            if stem.startswith(number + "-") and stem != basename:
                os.remove(os.path.join(directory, name))
                gone.append(name)
                break
    return gone


def main():
    import checks
    import documents
    import plans
    import viewer
    import export_cad
    import export_share

    print("checks")
    if checks.main():
        raise SystemExit("fix the plans before issuing the set")

    print("\ndocuments")
    for path in documents.main():
        print(f"{os.path.basename(path):34s} "
              f"{os.path.getsize(path) / 1024:6.1f} kB")

    print("\nsheets (svg)")
    svgs = plans.main()
    current = {sh.number: plans.sheet_basename(sh)
               for sh in (build() for build in plans.SHEETS)}
    for folder in ("drawings", "pdf", "png", "cad"):
        path = os.path.join(HERE, folder)
        if not os.path.isdir(path):
            continue
        for name in prune(path, current):
            print(f"superseded, removed: {name}")

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

    mirror()
    return svgs


def mirror():
    """Refresh the downloadable copy of the code, if it is there.

    The repository carries a second copy of these modules under
    Claude/, packaged so the project can be downloaded and run on its
    own. It was kept current by remembering to run a script, which means
    it was not kept current: it sat at P16 for twelve revisions, with a
    frame.py calling the building a four-storey vacation home and 21 MB
    of drawings of the apartment block this was before P5.

    So the build does it, every time, and no one has to remember. It is
    a no-op outside the repository - a downloaded copy has no mirror to
    refresh - and a failure here is reported rather than fatal, because
    the drawings are already written by the time it runs.
    """
    import subprocess
    script = os.path.join(os.path.dirname(HERE), "Claude",
                          "sync-from-floor-plans.sh")
    if not os.path.isfile(script):
        return
    print("\nmirror")
    try:
        done = subprocess.run(["sh", script], capture_output=True, text=True)
        print((done.stdout or done.stderr).strip() or "nothing to do")
    except OSError as exc:                       # pragma: no cover
        print(f"could not refresh the mirror: {exc}")


if __name__ == "__main__":
    main()
