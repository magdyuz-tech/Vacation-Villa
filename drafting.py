#!/usr/bin/env python3
"""
drafting.py - a minimal 2D architectural drafting engine that emits SVG.

All plan geometry is given in metres with the origin at the south-west corner
of the plot, x running east and y running north.  The engine converts to sheet
millimetres (ISO A2, 594 x 420) at a fixed drawing scale, so every line on the
sheet is dimensionally true and can be scaled off with a rule.

No external libraries: the output is a self-contained SVG that opens offline.
"""

import math
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# sheet + scale
# ---------------------------------------------------------------------------
SHEET_W, SHEET_H = 841.0, 594.0          # ISO A1 landscape, millimetres
SCALE_DEN = 100.0                        # 1:100
S = 1000.0 / SCALE_DEN                   # 10 mm of sheet per metre of building
OX, OY = 52.0, 320.0                     # sheet position of plan origin (0, 0)

# line weights (mm) -- ISO 128 pen set
LW_CUT = 0.70        # walls cut by the horizontal section
LW_SECONDARY = 0.35  # parapets, steps, sills
LW_FIXTURE = 0.20    # sanitaryware, joinery, furniture
LW_THIN = 0.13       # dimension lines, hatching, leaders
LW_HIDDEN = 0.18     # elements above / below the cut plane

# Minimum lettering height on the sheet.  The client asked for 12 point as a
# floor; everything smaller is raised to it, and hierarchy is carried by
# weight and colour rather than size.
POINT = 25.4 / 72.0
MIN_TEXT = 12.0 * POINT          # 4.23 mm

INK = "#141414"
GREY = "#5d5d5d"
LIGHT = "#9a9a9a"
FONT = ("ui-sans-serif,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',"
        "Arial,sans-serif")


def set_scale(denominator, ox, oy):
    """Switch drawing scale and plan origin for the next sheet."""
    global SCALE_DEN, S, OX, OY
    SCALE_DEN = float(denominator)
    S = 1000.0 / SCALE_DEN
    OX, OY = float(ox), float(oy)


def mm(metres):
    """Convert a length in metres to sheet millimetres at the current scale."""
    return metres * S


def X(x):
    return OX + x * S


def Y(y):
    return OY - y * S


def _short(a0, a1):
    """Nearest equivalent of a1 so the swept angle is at most 180 degrees."""
    while a1 - a0 > 180:
        a1 -= 360
    while a1 - a0 < -180:
        a1 += 360
    return a1


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


class Sheet:
    """One drawing sheet.  Coordinates are metres unless the name ends _mm."""

    def __init__(self, number, title, level, scale_note="1:100 @ A2"):
        self.number = number
        self.title = title
        self.level = level
        self.scale_note = scale_note
        self.body = []
        self.schedule = []          # (room name, area m2)
        self.clips = []             # (id, x, y, w, h) in sheet millimetres

    # -- raw primitives ----------------------------------------------------
    def raw(self, s):
        self.body.append(s)

    def begin_clip(self, x, y, w, h):
        """Clip everything until end_clip() to a window on the sheet.

        Enlarged details run the ordinary plan code at a larger scale and
        simply crop to the part being shown, so the detail and the plan can
        never disagree.  The CAD backend ignores it and keeps the geometry.
        """
        cid = f"clip{len(self.clips) + 1}"
        self.clips.append((cid, x, y, w, h))
        self.raw(f'<g clip-path="url(#{cid})">')
        return cid

    def end_clip(self):
        self.raw("</g>")

    @contextmanager
    def on(self, layer):
        """Name the drawing layer for the enclosed calls.

        Layers mean nothing to SVG, but the DXF backend uses the same calls
        to sort entities onto proper CAD layers, so the drawing code names
        them once, here, for both.
        """
        yield

    def line_mm(self, x1, y1, x2, y2, w=LW_THIN, color=INK, dash=None,
                cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" '
                 f'y2="{y2:.3f}" stroke="{color}" stroke-width="{w}" '
                 f'stroke-linecap="{cap}"{d}/>')

    def rect_mm(self, x, y, w, h, fill="none", stroke=INK, sw=LW_THIN,
                dash=None, rx=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        self.raw(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" '
                 f'height="{h:.3f}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}{r}/>')

    def text_mm(self, x, y, s, size=2.4, anchor="middle", color=INK,
                weight=400, ls=0.0, rot=None, style=""):
        size = max(MIN_TEXT, size)
        t = (f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot is not None
             else "")
        self.raw(f'<text x="{x:.3f}" y="{y:.3f}" font-family="{FONT}" '
                 f'font-size="{size}" fill="{color}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" letter-spacing="{ls}" '
                 f'style="{style}"{t}>{esc(s)}</text>')

    # -- plan-space primitives --------------------------------------------
    def line(self, x1, y1, x2, y2, **kw):
        self.line_mm(X(x1), Y(y1), X(x2), Y(y2), **kw)

    def rect(self, x, y, w, h, **kw):
        """x, y = south-west corner in metres."""
        self.rect_mm(X(x), Y(y + h), w * S, h * S, **kw)

    def poly(self, pts, fill="none", stroke=INK, sw=LW_THIN, dash=None,
             close=True):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{X(a):.3f},{Y(b):.3f}" for a, b in pts)
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}"{d}/>')

    def circle(self, x, y, r_m, fill="none", stroke=INK, sw=LW_FIXTURE):
        self.raw(f'<circle cx="{X(x):.3f}" cy="{Y(y):.3f}" r="{r_m * S:.3f}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def ellipse(self, cx, cy, rx_m, ry_m, fill="none", stroke=INK,
                sw=LW_FIXTURE):
        self.raw(f'<ellipse cx="{X(cx):.3f}" cy="{Y(cy):.3f}" '
                 f'rx="{mm(rx_m):.3f}" ry="{mm(ry_m):.3f}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def arc(self, cx, cy, r_m, a0, a1, sw=LW_THIN, color=INK, dash=None):
        """Angles in degrees, counter-clockwise from east, plan space."""
        x0, y0 = cx + r_m * math.cos(math.radians(a0)), cy + r_m * math.sin(math.radians(a0))
        x1, y1 = cx + r_m * math.cos(math.radians(a1)), cy + r_m * math.sin(math.radians(a1))
        large = 1 if abs(a1 - a0) > 180 else 0
        sweep = 0 if a1 > a0 else 1     # SVG sweep 1 = clockwise on the sheet
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<path d="M {X(x0):.3f} {Y(y0):.3f} A {r_m * S:.3f} '
                 f'{r_m * S:.3f} 0 {large} {sweep} {X(x1):.3f} {Y(y1):.3f}" '
                 f'fill="none" stroke="{color}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, **kw):
        self.text_mm(X(x), Y(y), s, **kw)

    # -- walls -------------------------------------------------------------
    def wall(self, x0, y0, x1, y1, openings=(), fill=INK):
        """Solid-poché wall between two opposite corners, minus openings.

        Openings are (start, end) pairs measured along the wall's long axis.
        """
        horiz = (x1 - x0) >= (y1 - y0)
        lo, hi = (x0, x1) if horiz else (y0, y1)
        pos = lo
        for a, b in sorted(openings):
            a, b = max(a, lo), min(b, hi)
            if a > pos:
                self._wall_piece(x0, y0, x1, y1, pos, a, horiz, fill)
            pos = max(pos, b)
        if pos < hi:
            self._wall_piece(x0, y0, x1, y1, pos, hi, horiz, fill)

    def _wall_piece(self, x0, y0, x1, y1, a, b, horiz, fill):
        if horiz:
            self.rect(a, y0, b - a, y1 - y0, fill=fill, stroke=fill,
                      sw=0.05)
        else:
            self.rect(x0, a, x1 - x0, b - a, fill=fill, stroke=fill,
                      sw=0.05)

    # -- openings ----------------------------------------------------------
    def door(self, a, b, wall_lo, wall_hi, axis, hinge="lo", swing="up",
             leaf=True):
        """Door in an opening running from a..b along `axis` ('h' or 'v').

        wall_lo/wall_hi bracket the wall thickness on the other axis.
        `swing` is the side the leaf opens towards: up/down for 'h' walls,
        left/right for 'v' walls.
        """
        w = b - a
        mid = (wall_lo + wall_hi) / 2.0
        if axis == "h":
            # jambs
            self.line(a, wall_lo, a, wall_hi, w=LW_SECONDARY)
            self.line(b, wall_lo, b, wall_hi, w=LW_SECONDARY)
            if not leaf:
                return
            hx = a if hinge == "lo" else b
            sgn = 1 if swing == "up" else -1
            ex = hx + (w if hinge == "lo" else -w)
            self.line(hx, mid, hx, mid + sgn * w, w=LW_FIXTURE)   # leaf
            a0 = 90 * sgn
            a1 = _short(a0, 0 if hinge == "lo" else 180)
            self.arc(hx, mid, w, a0, a1, sw=LW_THIN, color=GREY)
        else:
            self.line(wall_lo, a, wall_hi, a, w=LW_SECONDARY)
            self.line(wall_lo, b, wall_hi, b, w=LW_SECONDARY)
            if not leaf:
                return
            hy = a if hinge == "lo" else b
            sgn = 1 if swing == "right" else -1
            self.line(mid, hy, mid + sgn * w, hy, w=LW_FIXTURE)
            a0 = 0 if swing == "right" else 180
            a1 = _short(a0, 90 if hinge == "lo" else -90)
            self.arc(mid, hy, w, a0, a1, sw=LW_THIN, color=GREY)

    def window(self, a, b, wall_lo, wall_hi, axis, arched=False):
        """Glazed opening: frame lines across the reveal + glass line.

        Drawn in full-weight ink.  At 1:50 the wall is only 6 mm wide on the
        sheet, so hairlines inside it read as an empty gap rather than as a
        window -- these have to carry the same weight as the wall itself.
        """
        t = wall_hi - wall_lo
        if axis == "h":
            self.line(a, wall_lo, a, wall_hi, w=LW_CUT)
            self.line(b, wall_lo, b, wall_hi, w=LW_CUT)
            for f in (0.22, 0.78):
                self.line(a, wall_lo + t * f, b, wall_lo + t * f,
                          w=LW_SECONDARY)
            self.line(a, (wall_lo + wall_hi) / 2, b, (wall_lo + wall_hi) / 2,
                      w=LW_FIXTURE)
            if arched:
                self.arc((a + b) / 2, (wall_lo + wall_hi) / 2, (b - a) / 2.4,
                         180, 0, sw=LW_THIN, color=LIGHT, dash="0.8 0.6")
        else:
            self.line(wall_lo, a, wall_hi, a, w=LW_CUT)
            self.line(wall_lo, b, wall_hi, b, w=LW_CUT)
            for f in (0.22, 0.78):
                self.line(wall_lo + t * f, a, wall_lo + t * f, b,
                          w=LW_SECONDARY)
            self.line((wall_lo + wall_hi) / 2, a, (wall_lo + wall_hi) / 2, b,
                      w=LW_FIXTURE)
            if arched:
                self.arc((wall_lo + wall_hi) / 2, (a + b) / 2, (b - a) / 2.4,
                         -90, 90, sw=LW_THIN, color=LIGHT, dash="0.8 0.6")

    # -- annotation --------------------------------------------------------
    def room(self, x, y, w, h, name, area=None, sub=None, size=2.5,
             schedule=True, at=None, show_area=True, sched_name=None):
        """Stacked room label, set in sheet millimetres so the leading stays
        typographically correct whatever the drawing scale."""
        cx, cy = at if at else (x + w / 2.0, y + h / 2.0)
        if area is None:
            area = w * h
        # sizes are clamped here as well as in text_mm, so the leading
        # matches the type that actually gets drawn
        rows = [(name.upper(), max(MIN_TEXT, size), 700, INK, 0.18)]
        if area and show_area:
            rows.append((f"{area:.1f} m²", max(MIN_TEXT, size - 0.45),
                         400, GREY, 0.0))
        if sub:
            rows.append((sub, max(MIN_TEXT, size - 0.65), 400, GREY, 0.0))
        total = sum(r[1] * 1.38 for r in rows)
        yy = Y(cy) - total / 2.0 + rows[0][1]
        for txt, sz, wt, col, ls in rows:
            self.text_mm(X(cx), yy, txt, size=sz, weight=wt, color=col, ls=ls)
            yy += sz * 1.38
        if schedule and area:
            self.schedule.append((sched_name or name, area))

    def tag(self, x, y, s, size=1.9, color=GREY, rot=None, anchor="middle"):
        self.text(x, y, s, size=size, color=color, rot=rot, anchor=anchor)

    # -- dimensions --------------------------------------------------------
    def dim_h(self, a, b, y_line, text=None, ext_from=None, size=2.1):
        """Horizontal dimension between x=a and x=b, witness line at y_line."""
        ya = Y(y_line)
        self.line_mm(X(a), ya, X(b), ya, w=LW_THIN, color=INK)
        for xv in (a, b):
            self.line_mm(X(xv) - 1.1, ya + 1.1, X(xv) + 1.1, ya - 1.1,
                         w=LW_THIN)
            if ext_from is not None:
                self.line_mm(X(xv), Y(ext_from), X(xv), ya + (2.0 if Y(ext_from) < ya else -2.0),
                             w=LW_THIN, color=LIGHT)
        self.text_mm((X(a) + X(b)) / 2, ya - 1.3, text or f"{b - a:.2f}",
                     size=size)

    def dim_v(self, a, b, x_line, text=None, ext_from=None, size=2.1):
        xa = X(x_line)
        self.line_mm(xa, Y(a), xa, Y(b), w=LW_THIN, color=INK)
        for yv in (a, b):
            self.line_mm(xa - 1.1, Y(yv) + 1.1, xa + 1.1, Y(yv) - 1.1,
                         w=LW_THIN)
            if ext_from is not None:
                self.line_mm(X(ext_from), Y(yv), xa + (2.0 if X(ext_from) < xa else -2.0), Y(yv),
                             w=LW_THIN, color=LIGHT)
        self.text_mm(xa - 1.3, (Y(a) + Y(b)) / 2, text or f"{b - a:.2f}",
                     size=size, rot=-90)

    def level_tag(self, x, y, txt):
        """Standard level datum triangle."""
        px, py = X(x), Y(y)
        self.raw(f'<polygon points="{px:.2f},{py:.2f} {px - 1.6:.2f},'
                 f'{py - 2.4:.2f} {px + 1.6:.2f},{py - 2.4:.2f}" fill="none" '
                 f'stroke="{INK}" stroke-width="{LW_THIN}"/>')
        self.text_mm(px + 2.4, py - 0.6, txt, size=2.0, anchor="start")
