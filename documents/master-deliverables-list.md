# Master Deliverables List

Detached vacation villa — five levels, six structural slabs.

**Site** — Shamandeel, Quesna, Menoufia, Egypt, in the central Nile Delta.
**Client** — Private Client.

**Codes** — ECP 201 — Egyptian Code for Loads; ECP 203 — Egyptian Code for Reinforced Concrete. ECP 201 (2012) divides Egypt into five seismic zones with design ground accelerations of 0.10 g, 0.13 g, 0.15 g and 0.20 g for zones 1 to 4 and 0.25 g and 0.30 g for zones 5a and 5b. Which zone governs this site, and the wind basis with it, is named by the structural engineer on STR-001 — it is not assumed here.

> **Nothing is issued as engineering that has not been engineered.**

These documents are for the owner's own use: design record, build
information and cost planning.  They are not a tender issue - there is no
instruction to tenderers, no bid form and no document whose job is to be
priced by a competing contractor.

Every row carries a competence class, because a drawing that looks
engineered and is not gets built from by whoever holds it:

- **D** — derived from the geometry
- **L** — layout for the engineer's design
- **X** — external - cannot be produced here

Status on every row is derived at build time from the issued set and from the documents this project actually writes. It is not typed in, and `checks.py` fails the build if a row names a sheet nobody draws or a document nobody renders — so the register cannot claim a deliverable that is not there.

## The building

| | Level | Finished floor level |
| --- | --- | --- |
| L0 | Ground | +0.00 |
| L1 | First | +3.30 |
| L2 | Second | +6.60 |
| L3 | Third | +9.90 |
| L4 | Penthouse | +13.20 |

Structural slabs: +0.00, +3.30, +6.60, +9.90, +13.20, +16.45 — six slabs to five levels, because the slab at +13.20 is the penthouse floor and the roof over the third floor at once.

## Summary

| Package | Deliverables | Issued | In progress | Blocked | Not started |
| --- | --- | --- | --- | --- | --- |
| 0 — Information required from others | 3 | 0 | 0 | 1 | 2 |
| A — Presentation and estimation | 8 | 1 | 0 | 1 | 6 |
| B — Architecture | 21 | 9 | 0 | 1 | 11 |
| C — Structure | 12 | 0 | 0 | 10 | 2 |
| D — Building services | 33 | 0 | 0 | 3 | 30 |
| E — Quantities and cost control | 4 | 0 | 0 | 4 | 0 |
| **Total** | **81** | **10** | **0** | **20** | **51** |

## Package 0 — Information required from others

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUR-001 | Measured topographic and boundary survey | Survey | 1:200 | Report + DWG | X | not started | — | — |
| GEO-001 | Soil investigation and foundation recommendation | Geotechnical | - | Report | X | blocked | SUR-001 | — |
| CLI-001 | Exterior scheme selection - A, B or C | Client decision | - | Written instruction | X | not started | ARC-200 | — |

- **SUR-001** — Boundaries on A-000 are indicative until this is in hand. The north neighbour has not been surveyed at all.
- **GEO-001** — Central Nile Delta ground is well characterised as a region, and that is enough to assume a foundation type for layout. It is not enough to size one: allowable bearing pressure, the water table and sulphate content are plot figures, and this row stays open until they arrive with a source - boreholes, or figures the engineer will sign.
- **CLI-001** — Three skins are live on one agreed building. Finishes, details and the finishes quantities all wait on this.

## Package A — Presentation and estimation

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-01 | Exterior views - axonometric, three schemes | Presentation | 1:250 | A1 sheet | D | issued | — | A-430 |
| A-02 | Interior cutaway axonometric - ground floor, +0.00 | Presentation | 1:100 | A1 sheet | D | not started | — | — |
| A-03 | Interior cutaway axonometric - first floor, +3.30 | Presentation | 1:100 | A1 sheet | D | not started | — | — |
| A-04 | Interior cutaway axonometric - second floor, +6.60 | Presentation | 1:100 | A1 sheet | D | not started | — | — |
| A-05 | Interior cutaway axonometric - third floor, +9.90 | Presentation | 1:100 | A1 sheet | D | not started | — | — |
| A-06 | Interior cutaway axonometric - penthouse floor, +13.20 | Presentation | 1:100 | A1 sheet | D | not started | — | — |
| A-07 | Architectural design brief | Architecture | - | Report | D | not started | ARC-101, ARC-200 | — |
| A-08 | Cost estimation report - elemental | Cost | - | Report | X | blocked | QS-001, QS-004 | — |

- **A-01** — A projection of the geometry, not a render: it cannot show a balcony, a garden or a neighbour the drawings do not have.
- **A-02** — Projected by axonometric.py from the same constants as the floor plan.
- **A-03** — Projected by axonometric.py from the same constants as the floor plan.
- **A-04** — Projected by axonometric.py from the same constants as the floor plan.
- **A-05** — Projected by axonometric.py from the same constants as the floor plan.
- **A-06** — Projected by axonometric.py from the same constants as the floor plan.
- **A-07** — Accommodation, areas, levels and the reasoning behind them, measured off the issued plans.
- **A-08** — Quantities are ours; rates are not. Every rate carries its source or is shown as an open assumption.

## Package B — Architecture

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARC-000 | Master deliverables list and document register | Architecture | - | A1 sheet + Markdown | D | issued | — | ARC-000 |
| ARC-001 | Cover sheet, project data and drawing index | Architecture | - | A1 sheet | D | not started | ARC-000 | — |
| ARC-002 | General notes, symbols and code compliance matrix | Architecture | - | A1 sheet | L | not started | — | — |
| ARC-100 | Context and master site plan | Architecture | 1:75 | A1 sheet | D | issued | SUR-001 | A-000 |
| ARC-101 | Ground floor plan, +0.00 | Architecture | 1:50 | A1 sheet | D | issued | — | A-100 |
| ARC-102 | First floor plan, +3.30 | Architecture | 1:50 | A1 sheet | D | issued | — | A-101 |
| ARC-103 | Second floor plan, +6.60 | Architecture | 1:50 | A1 sheet | D | issued | — | A-102 |
| ARC-104 | Third floor plan, +9.90 | Architecture | 1:50 | A1 sheet | D | issued | — | A-103 |
| ARC-105 | Penthouse floor plan, +13.20 | Architecture | 1:50 | A1 sheet | D | issued | — | A-104 |
| ARC-106 | Roof plan over the penthouse, +16.45 | Architecture | 1:50 | A1 sheet | D | not started | — | — |
| ARC-200 | Facade elevations - all four faces, three schemes | Architecture | 1:50 / 1:75 | A1 sheet | D | issued | — | A-400, A-401, A-410, A-411, A-420, A-421, A-402 |
| ARC-300 | Longitudinal section A-A | Architecture | 1:50 | A1 sheet | D | issued | — | A-200 |
| ARC-301 | Transverse section B-B | Architecture | 1:50 | A1 sheet | D | not started | ARC-300 | — |
| ARC-400 | Reflected ceiling plan - ground floor, +0.00 | Architecture | 1:50 | A1 sheet | D | not started | ARC-101 | — |
| ARC-401 | Reflected ceiling plan - first floor, +3.30 | Architecture | 1:50 | A1 sheet | D | not started | ARC-102 | — |
| ARC-402 | Reflected ceiling plan - second floor, +6.60 | Architecture | 1:50 | A1 sheet | D | not started | ARC-103 | — |
| ARC-403 | Reflected ceiling plan - third floor, +9.90 | Architecture | 1:50 | A1 sheet | D | not started | ARC-104 | — |
| ARC-404 | Reflected ceiling plan - penthouse floor, +13.20 | Architecture | 1:50 | A1 sheet | D | not started | ARC-105 | — |
| ARC-500 | Door and window schedule | Architecture | - | A1 sheet | D | not started | ARC-200 | — |
| ARC-600 | Construction details | Architecture | 1:5 / 1:10 | A1 sheet | L | blocked | CLI-001 | — |
| ARC-700 | External works and landscape | Architecture | 1:75 | A1 sheet | D | not started | ARC-100 | — |

- **ARC-000** — This register. Status on it is derived at build time from the sheet builders and the files on disk.
- **ARC-002** — Notes and symbols are ours. The matrix is set against ECP 201 and ECP 203, the Egyptian codes the site is governed by, and signed off by the architect of record.
- **ARC-100** — Issued with the boundary marked indicative.
- **ARC-106** — Falls, outlets, parapets, water tanks and the plant deck. Drawn nowhere in the set today.
- **ARC-200** — Seven sheets: south and sides for each scheme, plus the street elevation in context.
- **ARC-301** — Cut east-west through the stair and the wave cantilever, which section A-A runs parallel to and cannot show.
- **ARC-400** — Soffit levels, bulkheads and ceiling layout. Fittings are indicative; the EL-200 series governs.
- **ARC-401** — Soffit levels, bulkheads and ceiling layout. Fittings are indicative; the EL-200 series governs.
- **ARC-402** — Soffit levels, bulkheads and ceiling layout. Fittings are indicative; the EL-200 series governs.
- **ARC-403** — Soffit levels, bulkheads and ceiling layout. Fittings are indicative; the EL-200 series governs.
- **ARC-404** — Soffit levels, bulkheads and ceiling layout. Fittings are indicative; the EL-200 series governs.
- **ARC-500** — Every opening in the building is already a constant, so the schedule is measured rather than compiled.
- **ARC-600** — Balcony nosing, parapet, threshold, roof upstand. Buildability, waterproofing and thermal performance are the specifier's, not ours.
- **ARC-700** — The entrance garden, gate, pergola, paving and barbecue are drawn on A-000 and would otherwise fall straight out of the quantities.

## Package C — Structure

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STR-001 | Structural notes, materials and design criteria | Structure | - | A1 sheet | L | not started | — | — |
| STR-100 | Excavation, grading and shoring | Structure | 1:100 | A1 sheet | L | blocked | GEO-001, SUR-001 | — |
| STR-101 | Foundation layout | Structure | 1:50 | A1 sheet | L | blocked | GEO-001, STR-200 | — |
| STR-200 | Column schedule and grid | Structure | 1:50 | A1 sheet | L | not started | — | — |
| STR-301 | Slab framing layout at +0.00 | Structure | 1:50 | A1 sheet | L | blocked | STR-200 | — |
| STR-302 | Slab framing layout at +3.30 | Structure | 1:50 | A1 sheet | L | blocked | STR-200 | — |
| STR-303 | Slab framing layout at +6.60 | Structure | 1:50 | A1 sheet | L | blocked | STR-200 | — |
| STR-304 | Slab framing layout at +9.90 | Structure | 1:50 | A1 sheet | L | blocked | STR-200 | — |
| STR-305 | Slab framing layout at +13.20 | Structure | 1:50 | A1 sheet | L | blocked | STR-200 | — |
| STR-306 | Slab framing layout at +16.45 | Structure | 1:50 | A1 sheet | L | blocked | STR-200 | — |
| STR-400 | Retaining and boundary walls | Structure | 1:50 | A1 sheet | L | blocked | SUR-001, GEO-001 | — |
| STR-500 | Cantilever balcony structure | Structure | 1:20 | A1 sheet | L | blocked | CLI-001, STR-302 | — |

- **STR-001** — To ECP 203, with loads to ECP 201. The seismic zone and its design ground acceleration, the wind basis and the concrete grades are set and signed by the structural engineer. No values assumed here.
- **STR-101** — Grid and column positions are exact; footing sizes, depths and reinforcement are the engineer's.
- **STR-200** — Every column coordinate, carried through all five levels. Sections and reinforcement left blank.
- **STR-305** — The penthouse floor and the roof over the third floor are the same slab.
- **STR-400** — Boundary line awaits the measured survey.
- **STR-500** — A 2.00 m curved cantilever repeated on four levels is the most engineering-sensitive element in the building, and had no deliverable in the list as given.

## Package D — Building services

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EL-100 | Power and small power layout - ground floor, +0.00 | Electrical | 1:50 | A1 sheet | L | not started | ARC-101 | — |
| EL-101 | Power and small power layout - first floor, +3.30 | Electrical | 1:50 | A1 sheet | L | not started | ARC-102 | — |
| EL-102 | Power and small power layout - second floor, +6.60 | Electrical | 1:50 | A1 sheet | L | not started | ARC-103 | — |
| EL-103 | Power and small power layout - third floor, +9.90 | Electrical | 1:50 | A1 sheet | L | not started | ARC-104 | — |
| EL-104 | Power and small power layout - penthouse floor, +13.20 | Electrical | 1:50 | A1 sheet | L | not started | ARC-105 | — |
| EL-200 | Lighting and switching layout - ground floor, +0.00 | Electrical | 1:50 | A1 sheet | L | not started | ARC-101 | — |
| EL-201 | Lighting and switching layout - first floor, +3.30 | Electrical | 1:50 | A1 sheet | L | not started | ARC-102 | — |
| EL-202 | Lighting and switching layout - second floor, +6.60 | Electrical | 1:50 | A1 sheet | L | not started | ARC-103 | — |
| EL-203 | Lighting and switching layout - third floor, +9.90 | Electrical | 1:50 | A1 sheet | L | not started | ARC-104 | — |
| EL-204 | Lighting and switching layout - penthouse floor, +13.20 | Electrical | 1:50 | A1 sheet | L | not started | ARC-105 | — |
| EL-300 | Low voltage, data and security layout - ground floor, +0.00 | Electrical | 1:50 | A1 sheet | L | not started | ARC-101 | — |
| EL-301 | Low voltage, data and security layout - first floor, +3.30 | Electrical | 1:50 | A1 sheet | L | not started | ARC-102 | — |
| EL-302 | Low voltage, data and security layout - second floor, +6.60 | Electrical | 1:50 | A1 sheet | L | not started | ARC-103 | — |
| EL-303 | Low voltage, data and security layout - third floor, +9.90 | Electrical | 1:50 | A1 sheet | L | not started | ARC-104 | — |
| EL-304 | Low voltage, data and security layout - penthouse floor, +13.20 | Electrical | 1:50 | A1 sheet | L | not started | ARC-105 | — |
| ME-100 | HVAC layout - ground floor, +0.00 | Mechanical | 1:50 | A1 sheet | L | not started | ARC-101 | — |
| ME-101 | HVAC layout - first floor, +3.30 | Mechanical | 1:50 | A1 sheet | L | not started | ARC-102 | — |
| ME-102 | HVAC layout - second floor, +6.60 | Mechanical | 1:50 | A1 sheet | L | not started | ARC-103 | — |
| ME-103 | HVAC layout - third floor, +9.90 | Mechanical | 1:50 | A1 sheet | L | not started | ARC-104 | — |
| ME-104 | HVAC layout - penthouse floor, +13.20 | Mechanical | 1:50 | A1 sheet | L | not started | ARC-105 | — |
| PL-100 | Water supply layout - ground floor, +0.00 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-101 | — |
| PL-101 | Water supply layout - first floor, +3.30 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-102 | — |
| PL-102 | Water supply layout - second floor, +6.60 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-103 | — |
| PL-103 | Water supply layout - third floor, +9.90 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-104 | — |
| PL-104 | Water supply layout - penthouse floor, +13.20 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-105 | — |
| PL-200 | Drainage layout - ground floor, +0.00 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-101 | — |
| PL-201 | Drainage layout - first floor, +3.30 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-102 | — |
| PL-202 | Drainage layout - second floor, +6.60 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-103 | — |
| PL-203 | Drainage layout - third floor, +9.90 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-104 | — |
| PL-204 | Drainage layout - penthouse floor, +13.20 | Plumbing | 1:50 | A1 sheet | L | not started | ARC-105 | — |
| EL-400 | Electrical single line diagram | Electrical | Schematic | A1 sheet | L | blocked | EL-100 | — |
| ME-200 | HVAC schematic and plant arrangement | Mechanical | Schematic | A1 sheet | L | blocked | ME-100, ARC-106 | — |
| PL-300 | Drainage and water riser diagram | Plumbing | Schematic | A1 sheet | L | blocked | PL-100, PL-200 | — |

- **EL-100** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-101** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-102** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-103** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-104** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-200** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-201** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-202** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-203** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-204** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-300** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-301** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-302** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-303** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-304** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **ME-100** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **ME-101** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **ME-102** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **ME-103** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **ME-104** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-100** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-101** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-102** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-103** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-104** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-200** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-201** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-202** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-203** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **PL-204** — Coordination layout. Cable sizes, duct sizes, pipe sizes and loads are the services engineer's.
- **EL-400** — One diagram for the whole building, not one per level.

## Package E — Quantities and cost control

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QS-001 | Bill of quantities - itemised, unpriced, by trade | Quantity surveying | - | Spreadsheet | D | blocked | ARC-101, ARC-700 | — |
| QS-002 | Bill of materials | Quantity surveying | - | Spreadsheet | D | blocked | QS-001 | — |
| QS-003 | Material requisitions and specifications | Procurement | - | Schedule | L | blocked | QS-002, CLI-001 | — |
| QS-004 | Owner's cost baseline | Cost | - | Spreadsheet | X | blocked | QS-001 | — |

- **QS-001** — Measured off the geometry: wall lengths, slab areas and opening counts reconcile to the plans they came from.
- **QS-002** — The same measure resolved into materials rather than trades: blockwork, concrete, reinforcement allowance, glazing and joinery.
- **QS-003** — Quantities are ours; performance specifications and approved-equal judgements are the specifier's.
- **QS-004** — The measured quantities with a rate column, for budgeting and for checking a quotation against. Rates stay empty until a named source fills them - nothing here goes out to tender.

## Open items

1. A measured topographic and boundary survey (SUR-001) is not in hand; boundaries on A-000 are issued marked indicative.
2. The ground is central Nile Delta, which is well characterised as a region — enough to assume a foundation type and lay the structure out, not enough to size it. Allowable bearing pressure, the water table and sulphate content are plot figures, and GEO-001 stays open until they arrive with a source. No soil value is written on any sheet here.
3. The north neighbour has not been surveyed. The north wall carries windows on every level, so the overlooking check on that face is open.
4. Three exterior schemes are live on one agreed building. The scheme selection (CLI-001) gates the details, the finishes and the finishes quantities.
5. Sheets A-300, A-301 and A-302 are enlargements of apartment units that no longer exist. They are already left out of the bound set and should be formally withdrawn rather than reissued.
6. Rates are class X throughout. No rate appears in any document here without a named source, and QS-004 is issued with its rate column open.

