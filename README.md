# Four-Storey Vacation Home — 2D Drawing Set

A five-sheet architectural drawing set for a four-storey building on a
narrow plot: a long garden corridor onto the street and two blocks hard
against three neighbouring plots.

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
| `A-102` | Second Floor Plan         | +6.60  | 1:50  |
| `A-103` | Third Floor & Roof Plan   | +9.90  | 1:50  |

All sheets are ISO A1 landscape (841 × 594 mm) with a title block, key,
area schedule, general notes, north point and graphic scale. A-100 covers
the whole plot, so the garden corridor, barbecue, pergola and patio are
drawn with the ground floor; the upper sheets cover the building only.

## What the building is

| Level  | Accommodation | GIA | External |
| ------ | ------------- | --- | -------- |
| +0.00  | Entrance lobby and reception, living and reception, lounge and breakfast room, guest bedroom or office, central service kitchen (18.4 m²) and wash-up, central laundry (10.4 m²), guest bath, WC, linen | 140.0 m² | — |
| +3.30  | Two one-bedroom apartments — A 57.1 m², B 63.3 m² — each with a kitchenette and a cantilevered balcony | 140.0 m² | 7.2 m² |
| +6.60  | Identical to the floor below | 140.0 m² | 7.2 m² |
| +9.90  | Two-bedroom apartment (≈73 m²) between a south terrace under a pergola and a shaded north terrace | 92.4 m² | 47.7 m² |
| **Total** | Five apartments over a floor of shared service accommodation | **512.5 m²** | **62.1 m²** |

The service kitchen and laundry on the ground floor serve every apartment
above.

## Which file to open, and in what

| Folder              | Format                              | Open it in                                                                 |
| ------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| `cad/`              | DXF R2010, millimetres, 1:1         | **LibreCAD**, **QCAD**, **FreeCAD**, nanoCAD, DraftSight — editable CAD     |
| `drawings/`         | SVG, A1                             | **Inkscape**, **Penpot**, Figma, any browser — editable vector artwork      |
| `pdf/`              | vector PDF, exactly 841 × 594 mm    | any reader; prints to scale; Inkscape and Scribus can edit it              |
| `png/`              | 150 dpi, 4967 px wide               | **Sweet Home 3D** and the online planners, to trace a 3D model over        |
| `drawing-set.html`  | all five sheets, self-contained     | any browser, offline — tabs, zoom, pan                                      |

### Editing the plans as CAD

`cad/` holds one DXF per level plus `vacation-home-all-levels.dxf`, which
carries all five side by side, each on its own layer set (`…-SITE`, `…-00`,
`…-01`, `…-02`, `…-03`). Model space is millimetres at full size, so a wall
measures its real length and you can draw straight on top.

Entities are sorted onto standard architectural layers, so you can switch
off what you don't want and edit what you do:

```
A-WALL / A-WALL-PATT / A-WALL-PRHT   walls, poche, terrace parapets
A-DOOR / A-GLAZ                      doors and swings, glazed openings
A-FLOR-STRS / A-FURN / A-EQPM        stairs, furniture, sanitaryware
S-COLS / S-GRID                      RC columns and the column grid
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
| `fixtures.py`   | Sanitaryware, joinery, furniture, stairs, lift, landscape.     |
| `frame.py`      | Sheet border, title block, key, schedule, notes.               |
| `plans.py`      | The five sheets themselves.                                    |
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
garden corridor, west of the building   11.50 × 5.00 m    57.50 m²
garden corridor, in front of it         11.50 × 3.50 m    40.25 m²
block A (front)                          6.50 × 14.50 m   94.25 m²
block B (rear)                           5.00 × 14.50 m   72.50 m²
plot                                                     264.50 m²
built footprint                                          166.75 m²   coverage 63 %
```

External and party walls are 300 mm, internal partitions 120 mm, terrace
parapets 250 mm × 1100 mm high.

Clear ceiling height is **3.00 m**, the client's minimum. A 0.30 m
structural zone puts the floors 3.30 m apart, so levels are +0.00, +3.30,
+6.60 and +9.90, the roof over the third floor is at +13.20, and the stair
is a 19-riser dog-leg at 174 × 275 mm.

The ground floor sits **0.50 m above the garden**: garden level −0.50,
finished floor level +0.00, with three risers at 167 mm at the entrance and
again at the patio doors.

Lettering is set at a minimum of 12 point (4.23 mm on the sheet); the
hierarchy between a room name, its area and its note is carried by weight
and colour rather than size.

### Structure

An RC frame, columns 300 × 300 on a grid set out along the wall
centrelines so that none of them stands in a room:

```
x  11.65   15.34   18.00   22.85      spans 3.69 / 2.66 / 4.85 m
y   3.65    7.24   10.54   14.66   17.85    spans 3.59 / 3.30 / 4.12 / 3.19 m
```

Longest span 4.85 m, comfortably within flat-slab range. The frame follows
the plan rather than the plan working around the frame.

### Resolving the survey sketch

The client's sketch recorded a 0.50 m step in the north boundary across
block A's width *and* a 5.50 m offset between the two blocks' north walls.
Those cannot both be true. It is resolved here in favour of a **straight
boundary at y = 18.00**, with both blocks running north to meet it, which
is the 0.50 m northward shift the client asked for. Every boundary
dimension still needs a measured survey before construction — see note 1 on
sheet A-000.

## Design response

The plot touches neighbours on its north, east and west boundaries, so the
south elevation onto the garden is the only fully open facade. Four moves
follow from that:

- **A light court**, 2.45 × 2.98 m, is cut through all four storeys against
  the stair. It daylights the service kitchen, the stair, the ground floor
  guest bedroom and apartment A's bedroom on each floor above — rooms that
  would otherwise be landlocked.
- **The building moves 1.50 m south** into its own garden, so each block is
  14.50 m deep instead of 13.00, and **balconies cantilever a further
  1.20 m** beyond that on the upper floors. Nothing projects over a
  boundary; the overhang is subject to the local projection rule.
- **The west wall is opened** where it faces our own garden, south of
  y = 5.00 — a short length that is not a party wall and gives apartment A's
  living room corner light down the 23 m garden axis.
- **Arched openings** face the garden on every level, and arch heads are
  shown dashed in plan.

### The core

Stair, lift, protected lobby and services riser stack identically on every
floor in the east strip of block A:

```
light court     15.40 – 17.85   14.72 – 17.70    2.45 × 2.98   open to sky
protected stair 15.40 – 17.85   10.60 – 14.60    2.45 × 4.00   two 1.10 m flights
fire lobby      15.40 – 17.85    8.98 – 10.48    2.45 × 1.50
lift shaft      15.40 – 17.10    7.30 –  8.86    1.70 × 1.56   knock-out slabs
riser cupboard  17.20 – 17.85    7.30 –  8.86    0.65 × 1.56   off the lobby
```

The lift shaft is built full height now with removable infill slabs at each
level, so a lift can be installed later without cutting structure or taking
area out of an occupied apartment. Both apartments on a floor open directly
off the fire lobby, and the riser cupboard is entered from the lobby rather
than from inside a dwelling.

### Services

All wet rooms stack floor to floor onto a spine on the party wall.
Apartment A's bathroom takes the full width of block A's east end so that
it sits hard against the party wall, directly below the riser cupboard;
apartment B's kitchenette runs along the other face of the same wall.
Kitchen extract from the ground floor rises in its own fire-rated shaft
within that cupboard and discharges above roof level.

## Ventilation

The east neighbour is limited to 3.00 m in height, so the east boundary
wall is opened above that level. It stays solid at ground floor, where a
3.00 m building may be built against it.

| Level  | Room                    | Opening       |
| ------ | ----------------------- | ------------- |
| +3.30  | Apt B bathroom          | 0.85 m        |
| +3.30  | Apt B bedroom           | 1.60 m        |
| +3.30  | Apt B dressing / study  | 1.20 m        |
| +6.60  | as +3.30                |               |
| +9.90  | Bedroom 2               | 1.40 m        |
| +9.90  | Bedroom 1               | 1.60 m        |

Apartment B's bathroom is naturally ventilated from it rather than
mechanically extracted, and its bedroom cross ventilates between the south
balcony and the east window. Apartment A's bedroom and the ground floor
service kitchen are daylit and ventilated from the light court, which runs
the full 13 m height of the building and is open at the top, so it also
acts as a stack. The remaining internal rooms — both bathrooms on the third
floor, the stores, the laundry and the guest bath — are mechanically
extracted at six air changes per hour.

Openings in a boundary wall are subject to local fire separation and rights
of light rules, whatever the neighbour's height is limited to. The drawings
say so in the notes on A-101, A-102 and A-103.

## Fire

Drawn as a **proposal**, not a compliance check — the governing code has
not been named yet, and the sheets say so.

- Single protected stair, FD30S self-closing doors onto a fire lobby at
  every level, apartments opening off that lobby.
- Sprinklers throughout.
- The ground floor is one non-residential compartment under the
  apartments: 2 hour separation to the floor over, with a suppression hood
  over the cooking line.
- Kitchen grease extract in a dedicated fire-rated shaft.

At four storeys with five dwellings and a commercial kitchen beneath
sleeping accommodation, this needs verifying against the local authority
before it goes any further.

## Status

Preliminary design issue, revision **P3** — not for construction. Work to
figured dimensions only; do not scale from the drawings.

| Rev | Date | Issued for |
| --- | ---- | ---------- |
| P1  | 2026-09-18 | First issue |
| P2  | 2026-09-24 | East boundary windows, 3.30 m floor heights, garden shown with the ground floor |
| P3  | 2026-09-29 | Four storeys, apartments and central service floor, straight north boundary, 1.50 m south extension, RC frame, lift shaft |

The title block carries this record and stamps the build date, so a sheet
always says which issue it is.

### Still open

- The governing fire code, and with it the single-stair strategy.
- Measured survey of the north boundary, and the local rule on the 1.20 m
  balcony overhang.
- A long section (A-200) and 1:25 unit plans (A-300 series) are to follow.
