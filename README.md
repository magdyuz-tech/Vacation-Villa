# Vacation House — 2D Drawing Set

A four-sheet architectural drawing set for a three-storey vacation house,
set out from the client's hand survey sketch (long garden corridor onto the
street, an L-shaped footprint hard against three neighbouring plots).

Everything is produced with free, open-source software — Python, [ezdxf]
for the CAD files and [CairoSVG] for the sheets — and exported in the
formats the free desktop and online design tools accept. The drawings are
generated rather than hand-drawn, so every wall, opening and dimension is
true to scale and can be measured off.

[ezdxf]: https://ezdxf.mozman.at/
[CairoSVG]: https://cairosvg.org/

Nothing here relates to the daily-movers dashboard in the rest of this
repository.

## The set

| Sheet   | Title                     | Level  | Scale |
| ------- | ------------------------- | ------ | ----- |
| `A-000` | Site Plan                 | +0.00  | 1:75  |
| `A-100` | Ground Floor Plan         | +0.00  | 1:50  |
| `A-101` | First Floor Plan          | +3.30  | 1:50  |
| `A-102` | Second Floor & Roof Plan  | +6.60  | 1:50  |

All sheets are ISO A1 landscape (841 × 594 mm) with a title block, key,
area schedule, general notes, north point and graphic scale. A-100 covers
the whole plot, so the garden corridor, barbecue, pergola and patio are
drawn with the ground floor; A-101 and A-102 cover the building only.

## Which file to open, and in what

| Folder              | Format                              | Open it in                                                                 |
| ------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| `cad/`              | DXF R2010, millimetres, 1:1         | **LibreCAD**, **QCAD**, **FreeCAD**, nanoCAD, DraftSight — editable CAD     |
| `drawings/`         | SVG, A1                             | **Inkscape**, **Penpot**, Figma, any browser — editable vector artwork      |
| `pdf/`              | vector PDF, exactly 841 × 594 mm    | any reader; prints to scale; Inkscape and Scribus can edit it              |
| `png/`              | 150 dpi, 4967 px wide               | **Sweet Home 3D** and the online planners, to trace a 3D model over        |
| `drawing-set.html`  | all four sheets, self-contained     | any browser, offline — tabs, zoom, pan                                      |

### Editing the plans as CAD

`cad/` holds one DXF per level plus `vacation-house-all-levels.dxf`, which
carries all four side by side, each on its own layer set (`…-SITE`, `…-00`,
`…-01`, `…-02`). Model space is millimetres at full size, so a wall measures
its real length and you can draw straight on top.

Entities are sorted onto standard architectural layers, so you can switch
off what you don't want and edit what you do:

```
A-WALL / A-WALL-PATT / A-WALL-PRHT   walls, poche, terrace parapets
A-DOOR / A-GLAZ                      doors and swings, glazed openings
A-FLOR-STRS / A-FURN / A-EQPM        stairs, furniture, sanitaryware
A-ANNO-TEXT / -DIMS / -SYMB / -PATT  labels, dimensions, arch heads, hatch
L-SITE / L-PLNT / G-ANNO-BNDY        paving and pergolas, planting, boundary
```

Dimensions are real DXF `DIMENSION` entities, so they stay editable and
re-measure themselves when you move something.

### Building a 3D model from the plans

Sweet Home 3D is the shortest route, and it is free:

1. `Plan > Import background image…` and choose the PNG for the level you
   want — the wizard takes BMP, JPEG, PNG or GIF.
2. When it asks for the scale, click the two ends of the overall dimension
   and type its value: **11.50 m** across the building on any floor plan, or
   **23.00 m** along the garden on the site plan.
3. Draw walls over the traced plan, then switch to the 3D view.

The online planners (Floorplanner, Planner5D, Coohom and similar) work the
same way on their free tiers: upload the PNG or PDF, set the scale from a
known dimension, and trace. DXF import is generally a paid feature there,
which is why the PNG and PDF issues exist.

## Regenerating

```sh
python3 build.py          # every format, in one pass
```

or one at a time:

```sh
python3 plans.py          # drawings/*.svg
python3 export_cad.py     # cad/*.dxf
python3 export_share.py   # pdf/*.pdf and png/*.png
python3 viewer.py         # drawing-set.html
```

`build.py` needs `ezdxf` and `cairosvg` (`pip install ezdxf cairosvg`);
`plans.py` alone needs nothing beyond the standard library.

| Module          | Role                                                          |
| --------------- | ------------------------------------------------------------- |
| `geometry.py`   | Single source of truth for the set-out: every dimension.       |
| `drafting.py`   | Drawing engine — scale, walls, doors, windows, dimensions.     |
| `fixtures.py`   | Sanitaryware, joinery, furniture, stairs, landscape symbols.   |
| `frame.py`      | Sheet border, title block, key, schedule, notes.               |
| `plans.py`      | The four sheets themselves.                                    |
| `dxf_backend.py`| The same drawing interface, emitting CAD geometry.             |
| `export_cad.py` | Runs the sheets against the CAD backend.                       |
| `export_share.py`| PDF and PNG issues.                                           |
| `viewer.py`     | Bundles the SVGs into the offline HTML page.                   |

`dxf_backend.DXFSheet` implements the same interface as `drafting.Sheet`, so
`plans.py` draws each sheet once and both the SVG and the DXF come out of
those same calls — the plotted sheets and the CAD files cannot drift apart.
Change a dimension in `geometry.py` and every format follows on the next
build.

## Set-out

Origin (0, 0) is the south-west corner of the plot; x runs east, y north.
The street is on the south side and the gate is at the west end of the
garden corridor.

```
garden corridor   23.00 × 5.00 m   115.00 m²
block A (front)    6.50 × 12.50 m   81.25 m²
block B (rear)     5.00 × 13.00 m   65.00 m²
plot                               261.25 m²   site coverage 56 %
```

External and party walls are 300 mm, internal partitions 120 mm, terrace
parapets 250 mm × 1100 mm high.

Clear ceiling height is **3.00 m**, the client's minimum. A 0.30 m
structural zone puts the floors 3.30 m apart, so levels are +0.00,
+3.30 and +6.60, and the stair is a 19-riser dog-leg at 174 × 275 mm.

The ground floor sits **0.50 m above the garden**: garden level −0.50,
finished floor level +0.00, with three risers at 167 mm at the entrance
and again at the patio doors onto the TV lounge.

Lettering is set at a minimum of 12 point (4.23 mm on the sheet); the
hierarchy between a room name, its area and its note is carried by
weight and colour rather than size.

### A note on the survey sketch

The sketch carries four figures that cannot all be true at once: blocks of
12.50 m and 13.00 m, a 5.00 m garden band, and a 5.50 m offset between the
two blocks' north walls. Taking the block and garden dimensions as given
(they are also the ones written out in the brief), the north offset resolves
to **0.50 m**, not 5.50 m. The drawings use the block and garden figures and
show the resulting offset; the 5.50 m note is the odd one out and should be
confirmed on site. Every boundary dimension needs a measured survey before
construction in any case — see note 1 on sheet A-000.

## Design response

The plot touches neighbours on its north, east and west boundaries, so the
south elevation onto the garden is the only open facade. Two moves follow
from that:

- **A light court**, 2.65 × 2.48 m, is cut through all three storeys against
  the stair. It daylights the kitchen, the stair, the ground floor guest
  bedroom, the first floor dressing room and the studio above — all rooms
  that would otherwise be landlocked.
- **Arched openings** face the garden on every level: arched glazing to the
  living room and TV lounge, and traditional arched brick openings in the
  terrace and balcony parapets above. Arch heads are shown dashed in plan.

| Level  | Accommodation                                                                       | GIA       | External  |
| ------ | ----------------------------------------------------------------------------------- | --------- | --------- |
| +0.00  | Living & reception, dining, open kitchen with breakfast bar, TV lounge, guest bedroom (4.00 × 3.50 m clear), guest bath, guest WC, laundry | 121.8 m²  | —         |
| +3.30  | Master suite (bedroom, ensuite, walk-in dressing, balcony), bedroom 2, family bathroom, study nook, front terrace | 94.7 m²   | 27.1 m²   |
| +6.60  | Studio suite with its own shower room and kitchenette, roof terraces with timber pergolas | 41.5 m²   | 78.1 m²   |
| **Total** |                                                                                  | **258.0 m²** | **105.2 m²** |

## Ventilation

The east neighbour is limited to 3.00 m in height, so the east boundary wall
is opened above that level and used to cross ventilate block B. It stays
solid at ground floor, where a 3.00 m building may be built against it.

Six openings were added on that wall:

| Level  | Room          | Opening            |
| ------ | ------------- | ------------------ |
| +3.30  | Master bedroom| 1.60 m             |
| +3.30  | Ensuite       | 0.90 m             |
| +3.30  | Linen store   | 0.60 m             |
| +6.60  | Shower room   | 0.70 m             |
| +6.60  | Studio suite  | 1.10 m + 1.10 m    |

What that changes: the master bedroom and the studio suite now cross
ventilate (balcony to east window, and light court to east windows), and the
master ensuite and the studio shower room are naturally ventilated instead of
relying on mechanical extract.

Every room, after the change:

| Room                        | Opens onto                        | Ventilation           |
| --------------------------- | --------------------------------- | --------------------- |
| Living & reception  +0.00   | 2 arched windows, garden          | single sided, 5.7 m deep |
| Dining  +0.00               | open plan to living and kitchen   | cross path, south to court |
| Kitchen  +0.00              | light court                       | natural, plus hob extract |
| TV lounge  +0.00            | 2 arched openings, garden         | single sided, 5.3 m deep |
| Guest bedroom  +0.00        | light court                       | single sided, door undercut |
| Guest WC / bath / laundry  +0.00 | —                            | mechanical extract, 6 ACH |
| Bedroom 2  +3.30            | glazed door to front terrace      | single sided, 4.5 m deep |
| Family bathroom  +3.30      | front terrace                     | natural                |
| Study nook, dressing  +3.30 | light court                       | natural                |
| Master bedroom  +3.30       | balcony **and** east window       | **cross ventilated**   |
| Ensuite, linen  +3.30       | east windows                      | **natural**            |
| Kitchenette  +6.60          | door to roof terrace              | natural                |
| Shower room  +6.60          | east window                       | **natural**            |
| Studio suite  +6.60         | light court **and** 2 east windows| **cross ventilated**   |

The four rooms that remain single sided are all shallower than 2.5 × their
ceiling height (5.7 m, 5.3 m, 4.5 m and 3.5 m deep against a 2.70 m ceiling),
which is the usual limit for single-sided ventilation to work. The light
court runs the full 9 m height of the building and is open at the top, so it
also acts as a stack for the rooms that open onto it.

Openings in a boundary wall are subject to local fire separation and rights
of light rules, whatever the neighbour's height is limited to — worth
confirming with the local code before construction. The drawings say so in
the notes on sheets A-101 and A-102.


## Status

Preliminary design issue, revision **P2** — not for construction. Work to
figured dimensions only; do not scale from the drawings.

| Rev | Date | Issued for |
| --- | ---- | ---------- |
| P1  | 2026-09-18 | First issue |
| P2  | 2026-09-24 | East boundary windows, 3.30 m floor heights, garden shown with the ground floor |

The title block carries this record and stamps the build date, so a sheet
always says which issue it is.
