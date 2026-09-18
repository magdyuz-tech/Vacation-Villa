# Vacation House — 2D Drawing Set

A four-sheet architectural drawing set for a three-storey vacation house,
set out from the client's hand survey sketch (long garden corridor onto the
street, an L-shaped footprint hard against three neighbouring plots).

The drawings are **generated**, not hand-drawn: a small drafting engine emits
true-to-scale SVG, so every wall, opening and dimension on the sheet can be
scaled off with a rule. Nothing here relates to the daily-movers dashboard
that occupies the rest of this repository.

## The set

| Sheet   | Title                     | Level  | Scale |
| ------- | ------------------------- | ------ | ----- |
| `A-000` | Site Plan                 | +0.00  | 1:75  |
| `A-100` | Ground Floor Plan         | +0.00  | 1:50  |
| `A-101` | First Floor Plan          | +3.00  | 1:50  |
| `A-102` | Second Floor & Roof Plan  | +6.00  | 1:50  |

All sheets are ISO A1 landscape (841 × 594 mm) with a title block, key,
area schedule, general notes, north point and graphic scale.

- `drawings/*.svg` — the four sheets, one file each, print-ready at A1.
- `drawing-set.html` — all four sheets in one self-contained page with tabs,
  zoom and pan. Inline SVG only: no libraries, fonts or network calls, so it
  opens offline.

## Regenerating

```sh
python3 plans.py          # writes drawings/*.svg
python3 viewer.py         # bundles them into drawing-set.html
```

No dependencies beyond the Python standard library.

| Module        | Role                                                        |
| ------------- | ----------------------------------------------------------- |
| `geometry.py` | Single source of truth for the set-out: every dimension.     |
| `drafting.py` | Drawing engine — scale, walls, doors, windows, dimensions.   |
| `fixtures.py` | Sanitaryware, joinery, furniture, stairs, landscape symbols. |
| `frame.py`    | Sheet border, title block, key, schedule, notes.             |
| `plans.py`    | The four sheets themselves.                                  |
| `viewer.py`   | Bundles the SVGs into the offline HTML viewer.               |

Change a dimension in `geometry.py` and every sheet follows.

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
parapets 250 mm × 1100 mm high. Floor to floor is 3.00 m; the stair is a
17-riser dog-leg at 176 × 275 mm.

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
| +3.00  | Master suite (bedroom, ensuite, walk-in dressing, balcony), bedroom 2, family bathroom, study nook, front terrace | 94.7 m²   | 27.1 m²   |
| +6.00  | Studio suite with its own shower room and kitchenette, roof terraces with timber pergolas | 41.5 m²   | 78.1 m²   |
| **Total** |                                                                                  | **258.0 m²** | **105.2 m²** |

## Status

Preliminary design issue, revision P1 — not for construction. Work to
figured dimensions only; do not scale from the drawings.
