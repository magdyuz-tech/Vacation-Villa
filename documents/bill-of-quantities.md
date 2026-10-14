# Bill of Quantities

Detached vacation villa — Ezbit Abu Rukbah, Quesna, Menoufia, Egypt.

**Itemised, unpriced, by trade.**

Measured from `geometry.py`, not scaled off the drawings. Wall runs come
from the drawing calls themselves — the same calls the sheets are drawn
with — so the bill cannot drift from the building it bills for.

Every row carries a class: **D** measured here and exact, **L** needing
someone else's design before it can be measured, **X** impossible here at
all. **Nothing in this document is priced.**

The rate and amount columns are open on a class D row and closed on every
other, so a priced return cannot carry a figure against work whose design
is still somebody else's. A class L row may still show a quantity — the
six slab areas are ours, their thickness and reinforcement are not — and
a rate against one of those would be priced against nothing. The same
rows, in the same classes, are in `cost-baseline.csv` for pricing.


## Substructure

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| X | Excavation, blinding, footings and ground slab | item | — | NOT PRICEABLE - class X, cannot be measured here | — | Waits on GEO-001 and STR-101. Nothing below ground is measured here: the foundation type is not chosen and its depth is not known. |

## Frame

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| L | Suspended slab at +0.00 | m² | 128.25 | NOT PRICEABLE - class L, awaiting another designer | — | Area measured; thickness is the engineer's, so no volume is given. |
| L | Suspended slab at +3.30 | m² | 128.25 | NOT PRICEABLE - class L, awaiting another designer | — | Area measured; thickness is the engineer's, so no volume is given. |
| L | Suspended slab at +6.60 | m² | 128.25 | NOT PRICEABLE - class L, awaiting another designer | — | Area measured; thickness is the engineer's, so no volume is given. |
| L | Suspended slab at +9.90 | m² | 128.25 | NOT PRICEABLE - class L, awaiting another designer | — | Area measured; thickness is the engineer's, so no volume is given. |
| L | Suspended slab at +13.20 | m² | 128.25 | NOT PRICEABLE - class L, awaiting another designer | — | Area measured; thickness is the engineer's, so no volume is given. |
| L | Suspended slab at +16.45 | m² | 55.53 | NOT PRICEABLE - class L, awaiting another designer | — | Area measured; thickness is the engineer's, so no volume is given. |
| L | Cantilever balcony slab, A serpentine | m² | 62.70 | NOT PRICEABLE - class L, awaiting another designer | — | Four levels at 15.7 m² each. The most engineering-sensitive element in the building; see STR-500. |
| D | Columns, 300 × 300 mm | nr | 52.00 | &nbsp; | &nbsp; | 171.4 m of lift, 15.43 m³ of concrete. Reinforcement is the engineer's. |

## Masonry

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| D | External and party wall, 300 mm — brick, colour unrestricted | m² | 600.63 | &nbsp; | &nbsp; | 806.0 m² gross, openings deducted. |
| D | Internal partition, 100 mm — red brick | m² | 281.40 | &nbsp; | &nbsp; | 326.8 m² gross, openings deducted. |
| D | Parapet, 250 mm — brick, rendered both faces | m² | 63.49 | &nbsp; | &nbsp; | 63.5 m² gross. 33.06 m of it is the guard round the penthouse roof at +16.45, which no plan draws - the floor plans stop below it. |

## Openings

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| D | Doors, 6 types | nr | 9.00 | &nbsp; | &nbsp; | 38.3 m² of structural opening. See ARC-500. Frames, glazing and ironmongery are specification, not geometry. |
| D | Windows, 16 types | nr | 69.00 | &nbsp; | &nbsp; | 127.9 m² of structural opening. See ARC-500. Frames, glazing and ironmongery are specification, not geometry. |
| D | Louvres, 2 types | nr | 17.00 | &nbsp; | &nbsp; | 6.7 m² of structural opening. See ARC-500. Frames, glazing and ironmongery are specification, not geometry. |

## Stair

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| L | Reinforced concrete dog-leg flights and half landings, 4 storeys | m² | 24.45 | NOT PRICEABLE - class L, awaiting another designer | — | 4 storey rises of 18 risers at 183 mm, 18 treads a storey at 260 mm going, flights 900 mm wide, half landings 1.90 m² each. Plan area of flight and landing; waist thickness and reinforcement are the engineer's, so no volume is given. |
| D | Tread, riser and nosing finish | nr | 72.00 | &nbsp; | &nbsp; | 72 treads and the risers with them, measured as the geometry sets them out. Material, nosing profile and the slip resistance of it are specification - see QS-003. |
| D | Balustrade to the open well | m | 16.50 | &nbsp; | &nbsp; | The east edge of the well on all 5 levels, which the plans tag OPEN STAIR — BALUSTRADE, at 1.10 m. Infill, fixings and the handrail on it are specification. |
| L | Handrail to the flights | m | — | NOT PRICEABLE - class L, awaiting another designer | — | Not measured: a handrail follows an arrangement nobody has drawn yet - one side or both, wall-fixed or on the balustrade, with or without the extensions past the top and bottom risers that a code may require. It is named here so it cannot be forgotten, and stays unmeasured until QS-003 answers it. |

## Finishes

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| D | Floor finish, net internal | m² | 473.70 | &nbsp; | &nbsp; | Every room the plans schedule. Finish type is specification. |
| D | Ceiling finish, net internal | m² | 473.70 | &nbsp; | &nbsp; | Equal to the floor area; bulkheads add to it once their depth is set. See the ARC-400 series. |
| D | Internal plaster | m² | 1,163.43 | &nbsp; | &nbsp; | The inside face of the external walls plus both faces of the partitions. Wet-room tiling comes out of it once the specification says which rooms are tiled and how high. |
| D | External render | m² | 600.63 | &nbsp; | &nbsp; | The outside face. Slab edges, the nosing and the cove are additional and are detailed on ARC-600. |

## Roof

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| D | Waterproofing — west terrace | m² | 17.67 | &nbsp; | &nbsp; | As ARC-106, which reads the same zones. Membrane, insulation and build-up are specification. |
| D | Waterproofing — open corridor | m² | 33.26 | &nbsp; | &nbsp; | As ARC-106, which reads the same zones. Membrane, insulation and build-up are specification. |
| D | Waterproofing — north strip | m² | 6.26 | &nbsp; | &nbsp; | As ARC-106, which reads the same zones. Membrane, insulation and build-up are specification. |
| D | Waterproofing — penthouse roof | m² | 47.51 | &nbsp; | &nbsp; | As ARC-106, which reads the same zones. Membrane, insulation and build-up are specification. |
| D | Waterproofing — balcony | m² | 15.67 | &nbsp; | &nbsp; | As ARC-106, which reads the same zones. Membrane, insulation and build-up are specification. |
| L | Rainwater outlets | nr | 5.00 | NOT PRICEABLE - class L, awaiting another designer | — | Indicative on ARC-106; PL-200 sets the number, the positions and the sizes. |

## External works

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| D | Paved walk | m² | 28.44 | &nbsp; | &nbsp; | Measured on ARC-700. |
| D | Forecourt | m² | 18.29 | &nbsp; | &nbsp; | Measured on ARC-700. |
| D | Barbecue terrace | m² | 3.36 | &nbsp; | &nbsp; | Measured on ARC-700. |
| D | Side passages | m² | 38.50 | &nbsp; | &nbsp; | Measured on ARC-700. |
| D | Turf | m² | 24.68 | &nbsp; | &nbsp; | Measured on ARC-700. |
| D | Trees | nr | 5.00 | &nbsp; | &nbsp; |  |
| L | Street wall | m | 9.10 | NOT PRICEABLE - class L, awaiting another designer | — | 1.20 m high is indicative and its line awaits the survey. |

## Services

| Class | Description | Unit | Quantity | Rate | Amount | Note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| L | Electrical, mechanical and plumbing | item | — | NOT PRICEABLE - class L, awaiting another designer | — | Not measurable from the architecture. The EL, ME and PL series are coordination layouts; quantities follow the services engineer's design. |

## Excluded

1. Everything below ground. The foundation type is not chosen and its depth is not known; GEO-001 and STR-101 come first.
2. Slab, beam and footing thicknesses, so no concrete volume is given for them. The areas are ours; the depths are the structural engineer's, and a volume needs both.
3. Reinforcement, in any form.
4. Services. The EL, ME and PL series are coordination layouts; their quantities follow the services engineer's design.
5. Rates, overheads, preliminaries, profit and contingency.

37 items: 24 class D, 12 class L, 1 class X.
