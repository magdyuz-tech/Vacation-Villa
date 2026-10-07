# Bill of Materials

The same measure as QS-001, resolved into materials rather than trades.

Measured from `geometry.py`, not scaled off the drawings. Wall runs come
from the drawing calls themselves — the same calls the sheets are drawn
with — so the bill cannot drift from the building it bills for.

Every row carries a class: **D** measured here and exact, **L** needing
someone else's design before it can be measured, **X** impossible here at
all. **Nothing in this document is priced.**


| Class | Material | Unit | Quantity | Note |
| --- | --- | --- | ---: | --- |
| D | Masonry, 300 mm | m² | 600.63 | Masonry — material to be specified. Unit size, strength and mortar are specification. |
| D | Red brick, 100 mm | m² | 281.40 | Material specified by the client; a half-brick partition. Brick size, strength and mortar are still specification. |
| D | Masonry, 250 mm parapet | m² | 27.13 | Masonry — material to be specified. |
| D | Concrete, columns | m³ | 15.44 | 300 mm square × the storey height, measured. Grade is the engineer's. |
| L | Concrete, slabs | m³ | — | Area is measured; the thickness is the engineer's. |
| X | Reinforcement | t | — | The engineer's, entirely. |
| D | Glazing | m² | 127.87 | Structural opening area. Glass build-up is specification. |
| D | Door leaves and frames | m² | 38.31 |  |
| D | Louvres | m² | 6.70 |  |
| D | Internal plaster | m² | 1,163.43 |  |
| D | External render | m² | 600.63 |  |
| D | Floor finish | m² | 473.70 | One figure; the split between finishes is specification. |
| D | Waterproofing membrane | m² | 120.38 |  |
| D | Paving | m² | 88.59 |  |
| D | Turf | m² | 24.68 |  |
| D | Timber, pergola | m² | 9.40 |  |
| D | Trees | nr | 5.00 |  |

## Excluded

1. Everything below ground. The foundation type is not chosen and its depth is not known; GEO-001 and STR-101 come first.
2. Slab, beam and footing thicknesses, so no concrete volume is given for them. The areas are ours; the depths are the structural engineer's, and a volume needs both.
3. Reinforcement, in any form.
4. Services. The EL, ME and PL series are coordination layouts; their quantities follow the services engineer's design.
5. Rates, overheads, preliminaries, profit and contingency.
