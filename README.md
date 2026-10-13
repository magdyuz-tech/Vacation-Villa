# Five-Storey Vacation Villa — 2D Drawing Set

An architectural drawing set for a detached five-storey villa at
Ezbit Abu Rukbah, Quesna, Menoufia, Egypt — the central Nile Delta. The house
stands 1.00 m clear of all three side boundaries, hard against the east
setback with its whole entrance garden to the west,
a three-storey blind neighbour behind that garden, a single-storey
clay-brick one to the east and another single storey to the north. Drawn
to ECP 201, ECP 203 and Code 305.

Until P22 this file still described the **four-storey apartment building
the design began as** — the building became a villa at P5 and the README
did not. Its accommodation, set-out, design, ventilation and fire
sections were rewritten then to the villa the drawings actually show,
and the areas in them are measured by `quantities.py` rather than typed.
That sentence is about this file's own history, not the building's, and
it is kept because the stale-description habit it records is the one
this project keeps having to catch. Where this file and a sheet
disagree, the sheet is right.

Everything is produced with free, open-source software — Python, [ezdxf]
for the CAD files and [CairoSVG] for the sheets — and exported in the
formats the free desktop and online design tools accept. The drawings are
generated rather than hand-drawn, so every wall, opening and dimension is
true to scale and can be measured off.

[ezdxf]: https://ezdxf.mozman.at/
[CairoSVG]: https://cairosvg.org/

This repository is the whole project: clone it, `pip install -r
requirements.txt`, run `python3 build.py`, and it writes every sheet in
every format next to itself. It began life in a folder of another
repository and moved here at P29 with its history intact, which is why
the record below starts at P1.

## The set

**74 sheets** are issued, across five packages. `ARC-001` is the cover and
the index — built from the sheets themselves rather than typed — and
`ARC-000` is the Master Deliverables List, which carries every deliverable
including the ones that are not drawings.

| Sheets | What | Class |
| ------ | ---- | ----- |
| `ARC-001`, `ARC-002` | Cover, project data and drawing index; general notes and the code matrix | D |
| `ARC-000` | Master Deliverables List — 84 rows, status derived | D |
| `A-000` | Site plan, 1:75 | D |
| `A-100` … `A-104` | The five floor plans, 1:50 — ground, first, second, third, penthouse | D |
| `ARC-106` | Roof plan over the penthouse: falls, outlets, parapets | D |
| `A-200`, `ARC-301` | Sections A–A and B–B, 1:50 | D |
| `A-400`, `A-401`, `A-402` | South, side and rear elevations and the street in context — scheme A | D |
| `A-430` | Axonometric, three balcony options compared | D |
| `ARC-400` … `ARC-404` | Reflected ceiling plans, one per level | D |
| `ARC-500` | Door and window schedule, measured off the plans' own openings | D |
| `ARC-600` | Four construction details at 1:5 and 1:10 — figured, not specified | **L** |
| `ARC-700` | External works: paving, turf, pergola, barbecue, gate and trees | D |
| `A-02` … `A-06` | Interior cutaway axonometrics, one per level | D |
| `STR-001` … `STR-500` | 12 structural sheets: grid, footings, six slab framing layouts, the cantilever | **L** |
| `EL-`, `ME-`, `PL-` | 33 services coordination layouts and schematics | **L** |

Class **D** is derived from `geometry.py` and ours to issue; class **L**
is layout and coordination for an engineer to size and certify, stamped
as such on every sheet. Nothing is issued as engineering that has not been
engineered.

Scheme A, "Wave", was adopted at P18, and the plans are drawn to its
serpentine balcony: 1.95 m deep at each end and, since the client deepened
the waist at P19, 1.35 m there — 15.7 m² a floor. `A-410` / `A-411`
(scheme B, Arcade) and `A-420` / `A-421` (scheme C, Facet) still build and
stay here as the record of what was offered, stamped not selected and left
out of the issue.

`A-300`, `A-301` and `A-302` are enlargements of apartment units that the
detached villa no longer has. They are **withdrawn at P22**: kept and
still building, because a set that deletes what it superseded cannot show
how the building was arrived at and the client holds a bound issue
containing them, but stamped across the face, left out of the issued set,
and held there by `checks.out_of_the_issue_says_why` — which also refuses
a sheet that falls out of the issue without saying why.

All sheets are ISO A1 landscape (841 × 594 mm) with a title block, key,
area schedule, general notes, north point and graphic scale. A-100 covers
the whole plot, so the entrance garden, barbecue, pergola and forecourt
are drawn with the ground floor; the upper sheets cover the building only.
ARC-700 measures all of it.

## What the building is

One household, eleven numbered bedrooms, over five levels on a 128.3 m²
plate. Every area below is measured from the plans by `quantities.py`,
not typed here.

| Level  | Accommodation | Net internal | External |
| ------ | ------------- | ------------ | -------- |
| +0.00  | Reception hall (43.1 m²) opening onto the garden frontage, dining and kitchen, guest bedroom with its own ensuite, laundry and guest WC | 108.3 m² | garden |
| +3.30  | Living area on the frontage, master bedroom with ensuite, two further bedrooms off a lobby and a shared bath | 108.3 m² | 15.7 m² |
| +6.60  | Four bedrooms — two of them suites with ensuite and dressing — a shared bath, landing and lobby | 107.0 m² | 15.7 m² |
| +9.90  | Second living area on the frontage, three bedrooms, two of them ensuite suites | 105.3 m² | 15.7 m² |
| +13.20 | Set-back penthouse: living and dining, one bedroom and a bath, between a west terrace, a north terrace and an open corridor | 44.8 m² | 15.7 m² balcony, 11.5 m² west and 12.2 m² north terrace, 33.3 m² corridor |
| **Total** | A single house, not flats | **473.7 m²** | — |

The accommodation above was agreed level by level and the sheets are
stamped final draft for it. An earlier design on this plot — four
storeys, five apartments and a shared service kitchen — is what sheets
`A-300` to `A-302` enlarge, and is the reason some of the module and
fixture names in the code still read "apt A" and "apt B".

## Which file to open, and in what

| Folder              | Format                              | Open it in                                                                 |
| ------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| `cad/`              | DXF R2010, millimetres, 1:1         | **LibreCAD**, **QCAD**, **FreeCAD**, nanoCAD, DraftSight — editable CAD     |
| `drawings/`         | SVG, A1                             | **Inkscape**, **Penpot**, Figma, any browser — editable vector artwork      |
| `pdf/`              | vector PDF, exactly 841 × 594 mm    | any reader; prints to scale; Inkscape and Scribus can edit it              |
| `png/`              | 150 dpi, 4967 px wide               | **Sweet Home 3D** and the online planners, to trace a 3D model over        |
| `drawing-set.html`  | the whole issue, self-contained     | any browser, offline — tabs, zoom, pan                                      |

### Editing the plans as CAD

`cad/` holds one DXF per plan, elevation and section, plus
`vacation-villa-all-levels.dxf`, which carries the site and all five levels
side by side, each on its own layer set (`…-SITE`, `…-00` to `…-04`).
Model space is millimetres at full size, so a wall measures its real
length and you can draw straight on top.

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
   and type its value: **9.50 m** across the building on any floor plan, or
   **23.00 m** along the street frontage on the site plan.
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
python3 documents.py      # documents/*.md
python3 deliverables.py    # the register, to the terminal
python3 export_cad.py     # cad/*.dxf
python3 export_share.py   # pdf/*.pdf and png/*.png
python3 viewer.py         # drawing-set.html
```

`build.py` needs `ezdxf` and `cairosvg` (`pip install ezdxf cairosvg`);
`plans.py` alone needs nothing beyond the standard library.

Every push and pull request runs `.github/workflows/checks.yml`: the 29
rules, then a build, then two assertions. That the committed `drawings/`
and `documents/` match what the source generates — so a sheet cannot be
edited in the repository without its generator, and a generator cannot
change without its sheets being rebuilt. And that two builds on the same
machine agree byte for byte. The committed PDFs and PNGs are deliberately
*not* compared against the runner's: they are rasterised against whatever
fonts the machine has, and the runner's are not the ones the committed
renders were made with, so comparing them would fail on a difference that
is not a change to any drawing. Each of the three assertions was checked
by breaking it on purpose before the workflow was committed.

The build is **reproducible**: two runs of `build.py` on the same source
produce byte-identical output in all four formats, 259 files, so
`git status` after a build is an honest answer to "what did I change".
That is a working tool here rather than a nicety, because it is how a
revision's changed sheets are identified. It took pinning four things
that record *when* rather than *what*: the sheet date, which now comes
from the revision record; cairo's PDF `/CreationDate`, rewritten to the
issue date after each file is written, since cairo honours no
`SOURCE_DATE_EPOCH`; the DXF header's four timestamps, two GUIDs and two
ezdxf stamps; and the interpreter's hash seed, which ezdxf's ordering of
part of the OBJECTS section follows. `SHEET_DATE` still overrides the
date if a build needs a different one.

| Module          | Role                                                          |
| --------------- | ------------------------------------------------------------- |
| `geometry.py`   | Single source of truth for the set-out: every dimension.       |
| `drafting.py`   | Drawing engine — scale, walls, doors, windows, dimensions.     |
| `fixtures.py`   | Sanitaryware, joinery, furniture, stairs, lift, landscape.     |
| `frame.py`      | Sheet border, title block, key, schedule, notes.               |
| `plans.py`      | The sheets themselves.                                         |
| `elevations.py` | The exterior schemes, drawn off the plans' own openings.       |
| `axonometric.py`| Isometric projection of the geometry — a view, not a render.   |
| `deliverables.py`| The Master Deliverables List as data; status derived.         |
| `documents.py`  | Renders the register to Markdown and onto sheet ARC-000.       |
| `quantities.py` | The measure: the bill, taken off the drawing calls themselves. |
| `structure.py`  | Package C's grid, footings, beams and voids.                   |
| `services.py`   | Package D's zones, wet-room stacks and schematics.             |
| `details.py`    | ARC-600's four junctions: what is figured, what is not.        |
| `checks.py`     | The rules, run before every build.                             |
| `build.py`      | Every format in one pass, and prunes superseded issues.        |
| `dxf_backend.py`| The same drawing interface, emitting CAD geometry.             |
| `export_cad.py` | Runs the sheets against the CAD backend.                       |
| `export_share.py`| PDF and PNG issues, and the bound set.                        |
| `viewer.py`     | Bundles the SVGs into the offline HTML page.                   |

`dxf_backend.DXFSheet` implements the same interface as `drafting.Sheet`, so
`plans.py` draws each sheet once and both the SVG and the DXF come out of
those same calls — the plotted sheets and the CAD files cannot drift apart.
Change a dimension in `geometry.py` and every format follows on the next
build.

## Set-out

Origin (0, 0) is the south-west corner of the plot; x runs east, y north.
The street is on the south side; the gate is a 2.40 m opening at the west
end of the frontage, and the forecourt in front of the door is at the
east end.

```
plot, an L on the street frontage                        264.50 m²
house, 9.50 × 13.50 m                      12.50 .. 22.00 x
                                            3.50 .. 17.00 y   128.25 m²
entrance garden, west of the house       11.50 m of frontage
setbacks, paved as side passages         1.00 m on three sides
built footprint                                          128.25 m²   coverage 48 %
```

The house is not in the middle of its plot and the drawings do not pretend
it is: it stands hard against the east setback, and the whole of the west
is one entrance garden.

External and party walls are 300 mm brick of any colour — both faces are
plastered or rendered, so no brick on this building is ever seen — internal
partitions 100 mm red brick, terrace parapets 250 mm × 1100 mm high, brick and
rendered like the rest — specified at P33, the last wall in the set that
was not. `geometry.WALL_MATERIAL` holds all three, and
every drawing, every key and every bill row reads it rather than naming a
material of its own.

Clear ceiling height is **3.00 m**, the client's minimum. A 0.30 m
structural zone puts the floors 3.30 m apart, so levels are +0.00, +3.30,
+6.60, +9.90 and the penthouse at +13.20, with the roof over it at +16.45
and the top of the building at +17.55. The stair is a dog-leg in a
2.00 × 3.30 m well, 18 risers at 183 × 260 mm in two 0.90 m flights, and
it stacks on the same well at every level.

The ground floor sits **0.50 m above the garden**: garden level −0.50,
finished floor level +0.00, with three risers at 167 mm at the entrance and
again at the patio doors.

Lettering is set at a minimum of 12 point (4.23 mm on the sheet); the
hierarchy between a room name, its area and its note is carried by weight
and colour rather than size.

### Structure

An RC frame, columns 300 × 300 on a 3 × 4 grid set out along the wall
centrelines so that none of them stands in a room:

```
A  12.65   B  17.46   C  21.85        spans A–B 4.81, B–C 4.39 m
1   3.65   2   8.46   3  12.56   4  16.85
                                      spans 1–2 4.81, 2–3 4.10, 3–4 4.29 m
```

Longest span 4.81 m, comfortably within flat-slab range. The frame follows
the plan rather than the plan working around the frame, and `checks.py`
proves the rule it rests on: every 300 mm wall stands on a grid line, so
every one of them has a beam under it. There is exactly one exception —
the penthouse's north wall, a line load on the +13.20 slab spanning B to
C — and because the check named it rather than passing it, STR-305
carries a secondary beam under it.

### The plot dimensions

The client's sketch recorded a 0.50 m step in the north boundary *and* a
5.50 m offset between the two north walls of the building as it then was.
Those cannot both be true. It was resolved in favour of a **straight
boundary at y = 18.00**, and at P34 the client made the dimensions final,
which settles that resolution.

So the boundary is no longer drawn indicative. It is the client's figure,
final, and the building is set out from it. `SUR-001` stays open for what
a client's figure is not: nobody has independently measured this plot,
the villa stands 1.00 m clear of three boundaries, and a plot even
slightly narrower than stated is found out when somebody sets it out on
site with the foundations already priced. The survey is a setting-out and
verification job now, not a design input.

## Design response

**The villa is detached on three sides.** The client took the building off
the east boundary at P5, setting it back 1.00 m from west, north and east
and facing the street across its own forecourt. That cost 22 % of the
floor — 114.8 m² inside the walls against 147.3 as a party-wall
building — and it
bought the one thing a party wall cannot: daylight and cross ventilation
on every face. Three moves follow from it.

- **The party wall becomes a spine.** With no neighbour attached there is
  no wall that must stay solid, so the line down the middle of the plate
  is structure only: a row of columns on grid B with downstand beams
  between them, opened the full 4.81 m where a plan wants to read across
  it. The first floor's lobby and the second floor's landing are both
  that opening.
- **The frontage is a serpentine cantilever.** Scheme A, adopted at P18
  and deepened at P19, carries 15.7 m² of balcony on each of the four
  upper levels: 1.95 m at each end, drawn in to 1.35 m at the waist, deep
  enough to sit out on along the whole frontage. It is the most
  engineering-sensitive element in the building and has its own sheet,
  STR-500.
- **The west is louvred, not glazed.** The neighbour behind the garden is
  three storeys and blind toward us, so the west wall takes ventilation
  louvres and no view. East and north carry ordinary windows: the east
  neighbour is a single storey in clay brick 1.00 m away, which the first
  floor's sills clear by 1.20 m.

Arched openings face the garden at ground level, and arch heads are shown
dashed in plan.

### The stair

A private villa stair, not a protected one: two 0.90 m flights, 18 risers
at 183 × 260 mm, in a 2.00 × 3.30 m well that stacks at every level. It
needs no enclosure, no smoke vent and no lift — and on the first and third
floors it is not even in a room of its own, standing openly in the living
area with no wall between.

That stacking is not negotiable: the well is fixed in `geometry.py` once
and every floor is set out from it, so a stair that failed to line
through would be a geometry error rather than a drafting one.

### The penthouse, and what it cost

The penthouse is set back on the east half of the plate, between a west
terrace, a north terrace and an open corridor that joins them down the
west side — 2.51 m clear against the 2.00 m the client asked for, pergola
over its whole length, with the front door off it. That corridor leaves
the flat 4.09 m clear, which will not take two bedrooms side by side, and
stacking them would need 12.06 m of the 13.50 m depth and leave 1.44 m
for both terraces. The second bedroom is what pays for the corridor, and
the drawing says so rather than quietly dropping one.

At +16.45 the penthouse is a fourth storey for most planning codes.

### Getting onto the roof

The stair stops at the penthouse, and for three revisions the set said
the reason that mattered was the water tanks: nobody could reach them.
That was wrong, and the geometry had always said so. `V4_PLANT` lies
outside the penthouse flat's footprint, and the slab at +16.45 measures
that footprint and stops at its walls — so there has never been any
structure up there to carry a tank. **The plant deck is at +13.20**, in
the north-west corner beside the west terrace, three metres from where
the stair lands. The tanks were always reachable. What had no access was
the +16.45 roof itself: 47.5 m² of membrane with falls and outlets.

Giving it access was not the free choice between a hatch and a flight
that the record implied. A roof people stand on has to be guarded, and
guarding is `BALUSTRADE_H`; the 0.60 m upstand there was a drained
edge, not a guard. So access cost 0.50 m on the top of the building —
+17.05 to +17.55 — which is the one thing `EL_TOP` said no scheme may
do. The client took that decision on 2026-10-13 and it is recorded with
the constant it became, like every other instruction.

The ladder is on the north terrace, not the open corridor, which is the
obvious place until you notice the pergola runs over the corridor end to
end. Where it stands is drawn; its rung pitch, hoops, the step-over at
the guard and its fixings into the wall are specification and are not.

### Services

Wet rooms stack floor to floor. The services package measured exactly one
zone that is wet on all five levels — 2.50 × 3.50 m on the east side —
and the PL series is laid out on it, one drainage stack straight to the
ground. Everything else in the EL, ME and PL sheets is coordination
layout for the services engineer, carrying no sizes.

## Ventilation

Three elevations are open, so every habitable room is daylit and
ventilated from its own external wall.

| Wall  | Openings |
| ----- | -------- |
| South | The garden frontage at every level: arched at ground floor, sliding doors onto the cantilever above |
| East  | Ordinary windows at every level, clearing the single-storey neighbour's roof from the first floor up |
| North | Ordinary windows at every level; only the ground floor looks at anything, and the neighbour there is a single storey too |
| West  | Louvred ventilation only — the neighbour behind the garden is three storeys and blind toward us |

Every window range clears the 300 mm columns standing in that wall, which
is a check rather than a claim: `checks.py` rebuilds each plan and refuses
an opening that runs through a column. What is left internal is the
circulation and the wet rooms, and those are mechanically extracted; the
rate is the services engineer's, and no figure for it is written on any
sheet here.

## Fire

This is a single dwelling, and it is drawn as one: one private stair, no
protected lobby, no smoke vent, no sprinklers and no lift. That follows
from the building being a house rather than the five flats the design
started as — but it is **not a compliance check**, and the set does not
pretend otherwise.

The governing code is named at P30: **Code 305**, the Egyptian code for
the design principles and implementation requirements for protecting
structures from fire, issued by the Housing and Building National
Research Centre and enforced through Civil Protection, which does not
accept a building that does not comply with it. It joins ECP 201 and
ECP 203 on ARC-002 and STR-001 — those two are loads and reinforced
concrete and say nothing whatever about means of escape, so for
twenty-nine revisions this set named no code that governed fire at all.

Naming it is all that is done, and the distinction matters. **No
requirement from Code 305 is written on any sheet here, because its text
could not be read.** Two things in particular are open:

- **Which edition is in force.** Code 305 has been issued in parts and
  editions over two decades, and the Ministry of Housing issued a
  decision in March 2026 requiring a new fire-prevention code to be
  applied. Whether that supersedes 305, and what it changes, is not
  something this office can establish from here.
- **How a detached single-family dwelling is treated.** This is the
  question worth asking first, and asking plainly: a house for one
  household is not an apartment block, and the provisions that would
  make a five-storey building with one unenclosed stair impossible are
  generally written for buildings with several households in them.
  Whether Code 305 draws that line, and where, decides whether this
  stair is a problem at all.

A code is not something a project chooses. There is no laxer Egyptian
fire code to adopt instead, and nominating one would not relax the
building — it would fail at permit, which is the expensive way to find
out. The useful move is the question above, put to Civil Protection or
to an Egyptian engineer licensed to answer it, before the stair is
built rather than after.

`EXITS_PER_FLOOR` is now a constant in `geometry.py` and prints on the
compliance matrix: one, the private stair, unenclosed. It is the single
fact an authority will ask about, and a number nowhere written down is a
number nobody checks.

## Status

Final draft for the agreed levels, set revision **P34** — not for
construction. Work to figured dimensions only; do not scale from the
drawings.

**74 sheets issued**, and **81 of the 84 deliverables** on `ARC-000`.
The three that are not are `SUR-001`, a measured survey, `GEO-001`, a
ground investigation, and `PRG-002`, the dated construction programme:
all class **X**, the first two needing somebody to visit the plot and
the third needing durations that only the people who will do the work
can give. Nothing else in the register is waiting on this office.

`PRG-001`, new at P29, is the programme those three sit in: the order
the work has to happen in, derived from the register's own dependencies.
It carries no dates, for the same reason the structural sheets carry no
reinforcement.

The revision record is `frame.REVISIONS`, and the title block prints the
issues each sheet has actually been through, with the date and what
changed. The rule is that a sheet which has not changed keeps its own
letter rather than being swept up in a set-wide bump, and for nine
revisions that left the issued set spread across seven letters at once.

**P30 is the exception that proves the rule.** The title block of every
sheet named the wrong village — Shamandeel, where the house is at Ezbit
Abu Rukbah — so every sheet genuinely changed, and all **74 issued
sheets reissue together at P30**. It is the only set-wide reissue in the
project's history, and not one line of the building moved to cause it.

**P31 goes back to the rule.** Ground parameters arrived, and exactly
five sheets changed: `ARC-000` gained the `GEO-002` row, `STR-001`,
`STR-100` and `STR-101` carry the figures, and `ARC-001` changed because
the index prints each sheet's revision and four of its rows now read
P31. That last one is the cascade worth knowing about — the cover is
never edited directly and reissues whenever anything else does. The
other 69 sheets are byte-identical to their P30 issue, which is how the
five were identified: the SVGs reproduce exactly, so the build itself
says which sheets changed rather than anybody deciding.

**P32 raised the agreed top, which nothing had ever done.** The client
gave the +16.45 roof permanent access, and a roof people stand on has to
be guarded: the 0.60 m upstand became a guard at `BALUSTRADE_H`, so the
building went from +17.05 to +17.55. That reached well past the two
sheets the ladder is drawn on — every elevation carries the top, the
cover and the compliance matrix print it, and the penthouse base plan is
drawn under six services layouts and a ceiling plan — so **22 sheets
reissued**. Which ones is `plans.P32_SHEETS`, listed once rather than
typed into twenty builders: the rule that an unchanged sheet keeps its
letter is only as good as somebody's memory of which sheets moved.

The three withdrawn `A-300` sheets stay at P22. A withdrawn drawing is a
record of what was once issued; reprinting it with a corrected address
would be tidying a record, which is the one thing a record must not
allow.

Earlier turning points, from the record: **P3** four storeys of
apartments over a service floor; **P5** the detached villa, 1.00 m
setbacks on three sides, the party wall gone; **P9** the penthouse;
**P12** bedrooms numbered 1 to 11 and all five floors agreed; **P18**
scheme A adopted and the site named; **P19** the serpentine's waist
deepened 0.75 to 1.35 m; **P20** internal partitions 100 mm red brick.

So the drawings carry their own history: nothing in this file is the
record, and where the two disagree the title block is right.

### What has changed since P21

P21 was the last change to the building itself. Everything after it is
the set being read rather than designed: a withdrawal that should have
happened when the villa replaced the apartments, and then six rounds of
faults found by looking at the sheets — labels printed over one another,
three schematics drawn off the edge of the paper, a cantilever sheet with
a third of the cantilever behind the panel, five cutaways that did not
draw the stair, and a column schedule with no columns on it. Not one was
a geometry error and not one could have been found in the geometry.

Three of them have become rules, because they turned out to be
checkable after all: an origin, a schedule missing its own rows, and a
revision note too long for the panel. P29's round found a further class
of absence the drawings could not show — the stair was drawn five times
and measured nowhere, the specification schedule asked for no tread and
no handrail, and nothing in the project said what order any of the work
goes in. The rest is what looking is for.

P25 is not in the table above because no issued sheet still carries it:
it was the cutaways, and P27 moved them again.

### The section and the enlargements

`A-200` is drawn by the same engine as the plans, by mapping the plan's
north–south axis onto the sheet's x and the level onto its y, so its
dimensions come out of `geometry.py` like everything else. It cuts at
x = 20.70 — marked A–A on every floor plan — looking west: the one
north–south line that passes through a room at every level and through
every wet room in the east strip, while clearing all three column lines,
so the slabs are seen spanning rather than a column standing in the cut.

`ARC-301` cuts the other way, at y = 10.80 through the stair well, and is
the only drawing of the building's width. What each cut passes through is
read off the plans by the same probe `checks.py` uses, so a section
cannot show a wall the plan does not have — on ARC-301 even the question
of whether the east wall is glazed at the cut is answered from that
level's own opening list, each time the sheet is built.

### Checks

`checks.py` runs before every build and stops it if the plans have gone
astray. It rebuilds each sheet with the drawing calls recording what they
were asked to draw, then reads the record back for three faults that a
tidy-looking sheet hides: a door or window drawn where its wall carries no
opening, an opening cut with no leaf in it, and an opening running through
one of the 300 mm columns standing in that same wall.

It earned its place immediately: it found that the ground floor's second
arched opening was cut through the party wall into the services riser
cupboard rather than into a room. Both arches now sit in y 3.80 – 7.18,
the only band where the wall has a room on each side.

Two later rules watch for the same fault in two places. A thickness that
was typed rather than derived goes stale the moment the constant moves,
and nothing on the sheet looks wrong afterwards. `every_wall_has_a_material`
refuses any wall drawn at a thickness `WALL_MATERIAL` does not declare —
it was written after six walls, set out between two hard-coded
coordinates, went on being drawn 120 mm thick and left the bill in
silence. `prose_says_the_real_thickness` does the same for the words: it
reads back every string a sheet prints and refuses one that names a wall
or partition thickness the building does not have. It was written after
the key had said "200 mm partition" for weeks, and it immediately found
eight sheets of structural notes still explaining what "the 120 mm
partitions" do.

A third rule watches the one thing that is easy to get badly wrong and
impossible to see in code: the origin. `nothing_is_drawn_off_the_sheet`
rebuilds every sheet with the drawing primitives recording where they
land, and refuses anything outside the border. It was written after
`EL-400`, `ME-200` and `PL-300` were found to have drawn their whole
diagram 130 mm off the left edge of the paper — the geometry right, the
scale right, the drawing somewhere else — and it reproduces that failure
when the old origin is put back. Clipped drawing is exempt, because the
1:25 enlargements run the whole plan and crop to a window. It cannot see
a label sitting on another label; only looking can, which is what the
contact sheet is for.

Three rules added at P29 watch a fault that is quieter than any of
those: a document that is complete in its own terms and silently missing
something. `a_schedule_shows_its_rows` reads back the text each schedule
sheet prints and insists every mark appears on a line with its figures.
It was written because `STR-200`, "Column Schedule & Grid", built its
twelve rows into a local variable, never drew them, and had been issued
that way since P21 — a grid with no coordinates anywhere on it, under a
note promising "the coordinate printed beside it". The first version of
the rule looked for the marks alone and passed happily with the table
deleted, because the grid plan labels every column; it has to look for
the row. `revision_notes_fit_the_title_block` derives how many
characters the title block holds and refuses a longer one, after P29's
own revision note was written too long and lost its last four words
off the panel edge. And `programme_carries_no_dates` holds `PRG-001` to
its one discipline: no duration, no date, no month, and the duration
column open on every row.

`ground_figures_own_their_basis`, added at P31, guards the newest and
most dangerous kind of figure in the set. A bearing pressure is the one
number on a structural sheet somebody could act on without reading a
note, and every ground figure here is an assumption. So a sheet
printing one of `geometry.GROUND`'s figures must also print that
figure's stamp — `ASSUMED` or `CLIENT-CONFIRMED` — and any text shaped
like a soil figure must be one `GROUND` declares, so a typed value
cannot drift from the constant the way the 120 mm partitions did. Both
halves were proved by injection: stripping the stamp off `STR-100`'s
water table and typing an undeclared `95 kPa` into `STR-101` each
failed the build. What it cannot catch is a figure quoted against the
wrong parameter — the soil sulphate range under a chloride heading
reads as fine, because both numbers are declared — and it has no
opinion whatever on whether any figure is true. That is what `GEO-001`
is still open for.

`guards_are_measured_at_the_constant` catches two faults that had both
already happened. The measure typed `1.10` and `0.25` where
`BALUSTRADE_H` and `PARAPET` exist — they agreed, so nothing looked
wrong, but that constant exists *because* the guarding height is a code
figure that can move, and if it moved the bill would have gone on
measuring the old one. And the guard round the penthouse roof was
measured nowhere: the five plan builders stop at +13.20, so nothing
draws it, and **P32 raised it to a 1.10 m guard without the bill
moving** — 33 m of masonry, more than the parapet that *was* being
measured, bought by nobody. `bill_reconciles` could not see it, because
it ties the bill to roof zones, openings and external areas, and a
parapet is in none of those. The rule recomputes the parapet from the
drawn runs plus the derived guard, at `BALUSTRADE_H`, and the bill must
agree. It cannot catch a third parapet somewhere else, drawn by no plan
and derived by no function.

`the_plant_deck_stands_on_something` asks the one question the drawings
could not. The water tanks were recorded on the roof at +16.45 in five
places — this file, the design brief, the specification schedule, and
drawn that way on all three riser schematics, which then reported a
height served 3.25 m too high. Nothing in the geometry ever agreed, and
nobody could see it: on every plan the deck is in the right *place*, and
only its *level* was wrong — a level being a number in prose rather than
a line on a drawing. The rule asks whether there is a slab at the level
the deck claims, and the old belief fails it, because the deck lies
outside the only slab at +16.45. It cannot catch a deck correctly on a
slab and in the wrong place on it.

`the_bill_is_exactly_summed` guards a figure that was reading the
machine rather than the building. The glazing total is exactly
**127.875 m²** of structural opening, which lands precisely on the
rounding boundary of `%.2f`. Added left to right in binary it comes to
127.87499999999999 and prints 127.87; summed exactly it is 127.875 and
prints 127.88. Which one appeared depended on the interpreter — CPython
3.12 gave `sum()` compensated summation — and on the order the opening
schedule happened to be in, so the bill said one thing on one machine
and another on the next with nothing in the building changed. The
measure now sums with `math.fsum`, which is exactly rounded and
order-independent, and the rule insists the printed figure agrees with
it. It cannot catch a figure that is exactly summed and measures the
wrong thing; `bill_reconciles` is what ties the measure to the drawings.

`every_revision_carries_its_date` guards the date on all 81 sheets.
That date used to be `date.today()`, which was wrong twice over: a sheet
nobody had touched for a week printed a date a week newer than the issue
it belongs to, and because the date prints on every sheet, **every build
on a new day rewrote every sheet**. The second part is what made it
serious. This project finds out what changed by rebuilding and seeing
which files differ — it is how P31's five changed sheets were found out
of 74 — and a floating date silently turns that answer into "all of
them". Nothing on any sheet looks wrong, because a date that is off by a
day looks exactly like one that is right. The date is now read from
`frame.REVISIONS`, each sheet taking the date of its own revision, and
the rule refuses a revision that carries no date. It cannot catch a date
that is present and wrong.

The 1:25 sheets run the ordinary plan code at a larger scale and crop to
the part being shown, so an enlargement cannot disagree with the plan it
came from. They cover the wet cores, the kitchenettes and the service
floor; a whole 13.90 m unit does not fit an A1 sheet at 1:25, so the
whole-unit plans stay at 1:50 on A-101 and A-103.

### The adopted scheme

`geometry.SCHEME` and `geometry.PROFILE` hold what the client chose, and
the default profile of every `wave_*` function resolves to them. That is
the whole mechanism: the plans, the section, the elevations and the
quantities all measure one balcony, because they all ask the same
function the same question. Before the choice the default was the literal
`"agreed"`, which would have left every plan drawing the superseded curve
while the elevations drew the chosen one.

`documents.DECISIONS` records each instruction with the constant it
became, and a `checks.py` rule resolves every one of those constants — so
a decision cannot be written down here and left unbuilt.

### The deliverables register

`deliverables.py` holds the Master Deliverables List: eighty-four rows
across packages 0 and A to F, printed on sheet `ARC-000` and written to
`documents/master-deliverables-list.md`. Two things about it are worth
knowing.

Every family that repeats per level — floor plans, reflected ceiling
plans, the six MEP series — is generated by looping `EL_LEVELS`, and
every family that repeats per slab by looping the slabs. The brief this
register answers assumed three floor plans; the building has five levels
and six structural slabs, which multiplies through every package. A
`checks.py` rule proves each family covers the whole building, so adding
a level cannot quietly leave a package a row short.

Every row carries a competence class, because the set is read as
instructions by whoever holds it: **D** derived from `geometry.py` and
ours to issue, **L** layout and coordination for an engineer to size and
certify, **X** impossible here at all — a measured survey, a soil report,
a market rate. Nothing is issued as engineering that has not been
engineered.

Status is derived, never typed: a row reports issued only where the
project really produces its sheets or documents, and `checks.py` fails
the build if a row names a sheet no builder draws or a document nothing
writes.

### The programme

The register says what is produced and who is competent to produce it.
It never said *when*, and for eighty-four deliverables that is a real
gap: which of them could be started today, and which cannot start
because somebody else has not done something, was nowhere written down.

`programme.py` closes it without inventing anything. Every row already
carries what it waits on, so the sequence is already in the register —
`stage()` is the longest path to a row, which is the earliest stage it
can sit in, and the stages fall out of that. A dependency added to a row
moves it, and everything behind it, on the next build. The document is
`documents/programme.md`, deliverable `PRG-001`.

What it will not do is put a number against any of it. How long a
survey takes, how long a municipality holds a permit, what a contractor
will commit to — every one is class **X**, and a bar chart with invented
bar lengths is the programme equivalent of a foundation detail with
invented reinforcement. So the duration column is printed open, exactly
as `QS-004`'s rate column is, `PRG-002` carries the dated programme as a
class **X** row nobody has started, and a check refuses a date, a month
or a duration anywhere in the document.

What is left is true today and worth reading. The critical chain is
`SUR-001 → ARC-100 → ARC-700 → QS-001 → QS-004 → A-08`: the longest path
in the project starts at a survey nobody has commissioned and ends at
the cost report the owner most wants, so the single instruction that
shortens the whole programme is to order the survey. Behind the two
site gates sit twelve rows, ten of them issued anyway against an
assumption written on the face of the drawing, and two that genuinely
cannot start.

### Still open

- **The authority's view of a five-storey house on one unenclosed
  stair.** The code is named at P30 — Code 305 — but its text was not
  readable from here, the edition in force is unconfirmed after the
  Ministry's March 2026 decision, and whether a single-family dwelling
  is treated separately is the question that decides this. Nothing in
  this set should be read as a compliance check.
- **SUR-001**, a measured survey. The plot dimensions are the client's
  and were made final at P34, so this is no longer a design input — but
  nobody has independently measured the plot, the setbacks are 1.00 m on
  three sides, and the local rule on the cantilever's projection over the
  frontage still turns on where the boundary actually is.
- **GEO-001**, a ground investigation. The ground *data* is complete and
  issued: `GEO-002` carries all seven parameters in full, each with its
  basis, and nothing further is waiting on this office. What stays open
  is the investigation itself, which is a different thing — somebody
  sinking boreholes and signing the result. Four structural rows still
  wait on it, and the row cannot be closed from here even as a
  bookkeeping matter: status is derived, so `GEO-001` would have to be
  given a document to read as issued, and the only document that would
  do it is a soil report nobody has written.
- **PRG-002**, the dated construction programme. `PRG-001` gives the
  sequence; the durations are the surveyor's, the authority's, the
  engineer's and the contractor's to supply.

Those are in the register on `ARC-000` with their class and their
status, and the status is derived rather than typed: a row cannot claim
to be issued because somebody forgot to change it back.
