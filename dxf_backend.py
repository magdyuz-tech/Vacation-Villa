#!/usr/bin/env python3
"""
dxf_backend.py - draws the same plans as real CAD geometry instead of SVG.

`DXFSheet` implements the drawing interface of `drafting.Sheet`, so the sheet
code in `plans.py` runs unchanged against either backend: the SVG sheets and
the DXF files are drawn by the same lines of code and cannot drift apart.

Model space is millimetres at full size (1:1), which is what LibreCAD, QCAD,
FreeCAD, Sweet Home 3D and the online planners expect from an architectural
DXF.  Annotation is scaled by the sheet scale so text and arrowheads come out
the right size when the drawing is plotted.
"""

import math
from contextlib import contextmanager

import ezdxf
from ezdxf.enums import TextEntityAlignment

import drafting as D
from drafting import INK, GREY, LIGHT, LW_CUT, LW_SECONDARY, LW_FIXTURE

PARAPET_FILL = "#6f6f6f"

# layer name -> (aci colour, lineweight in 1/100 mm, linetype)
LAYERS = {
    "A-WALL":        (7,   50, "CONTINUOUS"),   # walls cut by the section
    "A-WALL-PATT":   (7,    9, "CONTINUOUS"),   # poche
    "A-WALL-PRHT":   (9,   35, "CONTINUOUS"),   # terrace parapets
    "A-DOOR":        (3,   18, "CONTINUOUS"),
    "A-GLAZ":        (4,   18, "CONTINUOUS"),
    "A-FLOR":        (7,   25, "CONTINUOUS"),
    "A-FLOR-STRS":   (2,   18, "CONTINUOUS"),
    "A-FURN":        (6,   13, "CONTINUOUS"),
    "A-EQPM":        (6,   13, "CONTINUOUS"),
    "A-ANNO-TEXT":   (7,   13, "CONTINUOUS"),
    "A-ANNO-DIMS":   (5,   13, "CONTINUOUS"),
    "A-ANNO-SYMB":   (5,   13, "DASHED"),
    "A-ANNO-PATT":   (8,    9, "CONTINUOUS"),
    "S-COLS":        (7,   35, "CONTINUOUS"),   # RC columns
    "S-GRID":        (5,    9, "DASHDOT"),      # column grid lines
    "L-SITE":        (3,   18, "CONTINUOUS"),
    "L-PLNT":        (3,   13, "CONTINUOUS"),
    "G-ANNO-BNDY":   (1,   25, "DASHDOT"),
}


def new_document():
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4        # millimetres
    doc.header["$MEASUREMENT"] = 1     # metric
    doc.header["$LUNITS"] = 2          # decimal
    doc.header["$LWDISPLAY"] = 1
    doc.header["$LTSCALE"] = 20.0
    for name, (color, lw, ltype) in LAYERS.items():
        lt = ltype if ltype in doc.linetypes else "CONTINUOUS"
        doc.layers.add(name, color=color, lineweight=lw, linetype=lt)
    return doc


class DXFSheet(D.Sheet):
    """Same interface as drafting.Sheet; emits DXF model-space geometry."""

    def __init__(self, number, title, level, scale_note="1:50",
                 doc=None, offset=(0.0, 0.0), suffix=""):
        super().__init__(number, title, level, scale_note)
        self.doc = doc or new_document()
        self.msp = self.doc.modelspace()
        self.ox, self.oy = offset
        self.suffix = suffix               # per-level layer suffix
        self.layer = "A-FLOR"
        self._dimstyle = self._make_dimstyle()

    # -- units -------------------------------------------------------------
    @property
    def s(self):
        """Annotation scale: 1 mm on the plotted sheet, in model millimetres."""
        return D.SCALE_DEN

    def p(self, x, y):
        """Plan metres -> model millimetres."""
        return (self.ox + x * 1000.0, self.oy + y * 1000.0)

    def _lay(self, name):
        n = name + self.suffix
        if n not in self.doc.layers:
            color, lw, ltype = LAYERS.get(name, (7, 25, "CONTINUOUS"))
            self.doc.layers.add(n, color=color, lineweight=lw, linetype=ltype)
        return n

    def _furn(self, stroke):
        """Fixture linework drawn outside a named layer is furniture."""
        return "A-FURN" if (self.layer == "A-FLOR" and stroke == GREY) \
            else self.layer

    def _attribs(self, layer=None, dash=None):
        a = {"layer": self._lay(layer or self.layer)}
        if dash:
            a["linetype"] = "DASHED"
            a["ltscale"] = self.s * 0.35
        return a

    @contextmanager
    def on(self, layer):
        prev = self.layer
        self.layer = layer
        try:
            yield
        finally:
            self.layer = prev

    # -- sheet furniture: nothing to do in a model-space CAD file ----------
    def raw(self, s):
        pass

    def line_mm(self, *a, **k):
        pass

    def rect_mm(self, *a, **k):
        pass

    def text_mm(self, *a, **k):
        pass

    # -- plan primitives ---------------------------------------------------
    def line(self, x1, y1, x2, y2, w=None, color=None, dash=None, cap=None):
        self.msp.add_line(self.p(x1, y1), self.p(x2, y2),
                          dxfattribs=self._attribs(self._furn(color), dash))

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=None, dash=None,
             rx=None):
        """Only structural fills become hatches.

        The sheets use pale washes to shade floors and the street; those are
        presentation, not geometry, so they are dropped rather than laid down
        as solid hatch over a CAD drawing.
        """
        structural = fill in (INK, GREY, PARAPET_FILL)
        if stroke == "none" and not structural:
            return
        pts = [self.p(x, y), self.p(x + w, y), self.p(x + w, y + h),
               self.p(x, y + h)]
        layer = self._furn(stroke)
        if structural:
            layer = "A-WALL-PRHT" if fill == PARAPET_FILL else "A-WALL"
        if stroke != "none":
            self.msp.add_lwpolyline(pts, close=True,
                                    dxfattribs=self._attribs(layer, dash))
        if structural:
            hatch = self.msp.add_hatch(
                dxfattribs=self._attribs("A-WALL-PATT"))
            hatch.paths.add_polyline_path(pts, is_closed=True)

    def poly(self, pts, fill="none", stroke=INK, sw=None, dash=None,
             close=True):
        pp = [self.p(a, b) for a, b in pts]
        self.msp.add_lwpolyline(pp, close=close,
                                dxfattribs=self._attribs(dash=dash))
        if fill and fill != "none":
            hatch = self.msp.add_hatch(dxfattribs=self._attribs("A-ANNO-PATT"))
            hatch.paths.add_polyline_path(pp, is_closed=True)

    def circle(self, x, y, r_m, fill="none", stroke=INK, sw=None):
        self.msp.add_circle(self.p(x, y), r_m * 1000.0,
                            dxfattribs=self._attribs(self._furn(stroke)))

    def ellipse(self, cx, cy, rx_m, ry_m, fill="none", stroke=INK, sw=None):
        if rx_m >= ry_m:
            major, ratio = (rx_m * 1000.0, 0.0), (ry_m / rx_m)
        else:
            major, ratio = (0.0, ry_m * 1000.0), (rx_m / ry_m)
        self.msp.add_ellipse(self.p(cx, cy), major_axis=major,
                             ratio=max(0.01, min(1.0, ratio)),
                             dxfattribs=self._attribs())

    def arc(self, cx, cy, r_m, a0, a1, sw=None, color=None, dash=None):
        start, end = (a0, a1) if a1 > a0 else (a1, a0)
        self.msp.add_arc(self.p(cx, cy), r_m * 1000.0, start, end,
                         dxfattribs=self._attribs(
                             "A-ANNO-SYMB" if dash else None, dash))

    def door(self, *a, **k):
        with self.on("A-DOOR"):
            super().door(*a, **k)

    def window(self, *a, **k):
        with self.on("A-GLAZ"):
            super().window(*a, **k)

    def text(self, x, y, s, size=2.4, anchor="middle", color=INK, weight=400,
             ls=0.0, rot=None, style=""):
        size = max(D.MIN_TEXT, size)
        align = {"middle": TextEntityAlignment.MIDDLE_CENTER,
                 "start": TextEntityAlignment.MIDDLE_LEFT,
                 "end": TextEntityAlignment.MIDDLE_RIGHT}[anchor]
        layer = "A-ANNO-TEXT" if self.layer == "A-FLOR" else self.layer
        t = self.msp.add_text(str(s), height=size * self.s,
                              rotation=rot or 0,
                              dxfattribs=self._attribs(layer))
        t.set_placement(self.p(x, y), align=align)

    # -- annotation --------------------------------------------------------
    def room(self, x, y, w, h, name, area=None, sub=None, size=2.5,
             schedule=True, at=None, show_area=True, sched_name=None):
        cx, cy = at if at else (x + w / 2.0, y + h / 2.0)
        if area is None:
            area = w * h
        rows = [(name.upper(), max(D.MIN_TEXT, size))]
        if area and show_area:
            rows.append((f"{area:.1f} m²", max(D.MIN_TEXT, size - 0.45)))
        if sub:
            rows.append((sub, max(D.MIN_TEXT, size - 0.65)))
        lead = [r[1] * 1.38 for r in rows]
        top = cy + (sum(lead) / 2.0) * self.s / 1000.0
        with self.on("A-ANNO-TEXT"):
            for (txt, sz), ld in zip(rows, lead):
                top -= (ld * self.s / 1000.0)
                self.text(cx, top + (ld * 0.35 * self.s / 1000.0), txt,
                          size=sz)
        if schedule and area:
            self.schedule.append((sched_name or name, area))

    def _make_dimstyle(self):
        name = "ARCH"
        if name in self.doc.dimstyles:
            return name
        ds = self.doc.dimstyles.add(name)
        ds.dxf.dimtxt = 2.2
        ds.dxf.dimasz = 1.8
        ds.dxf.dimexe = 1.2
        ds.dxf.dimexo = 2.0
        ds.dxf.dimgap = 0.8
        ds.dxf.dimtad = 1            # text above the dimension line
        ds.dxf.dimlfac = 0.001       # model millimetres shown as metres
        ds.dxf.dimdec = 2
        ds.dxf.dimblk = "ARCHTICK"
        return name

    def _dim(self, p1, p2, base, text, angle):
        d = self.msp.add_linear_dim(
            base=base, p1=p1, p2=p2, angle=angle, text=text,
            dimstyle=self._dimstyle,
            override={"dimscale": self.s},
            dxfattribs={"layer": self._lay("A-ANNO-DIMS")})
        d.render()

    def dim_h(self, a, b, y_line, text=None, ext_from=None, size=None):
        self._dim(self.p(a, ext_from if ext_from is not None else y_line),
                  self.p(b, ext_from if ext_from is not None else y_line),
                  self.p((a + b) / 2.0, y_line), text, 0)

    def dim_v(self, a, b, x_line, text=None, ext_from=None, size=None):
        self._dim(self.p(ext_from if ext_from is not None else x_line, a),
                  self.p(ext_from if ext_from is not None else x_line, b),
                  self.p(x_line, (a + b) / 2.0), text, 90)

    def level_tag(self, x, y, txt):
        t = 0.30                      # 300 mm symbol, drawn at model size
        with self.on("A-ANNO-SYMB"):
            self.poly([(x, y), (x - t / 2, y - t), (x + t / 2, y - t)])
        with self.on("A-ANNO-TEXT"):
            self.text(x + t, y - t / 2, txt, size=2.0, anchor="start")
