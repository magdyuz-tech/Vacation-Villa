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
| 0 — Information required from others | 3 | 1 | 0 | 1 | 1 |
| A — Presentation and estimation | 8 | 8 | 0 | 0 | 0 |
| B — Architecture | 21 | 21 | 0 | 0 | 0 |
| C — Structure | 12 | 12 | 0 | 0 | 0 |
| D — Building services | 33 | 33 | 0 | 0 | 0 |
| E — Quantities and cost control | 4 | 4 | 0 | 0 | 0 |
| **Total** | **81** | **79** | **0** | **1** | **1** |

## Package 0 — Information required from others

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUR-001 | Measured topographic and boundary survey | Survey | 1:200 | Report + DWG | X | not started | — | — |
| GEO-001 | Soil investigation and foundation recommendation | Geotechnical | - | Report | X | blocked | SUR-001 | — |
| CLI-001 | Client instructions and decisions record | Client decision | - | Register | D | issued | — | — |

- **SUR-001** — Boundaries on A-000 are indicative until this is in hand, as are the three neighbours' heights and positions - they are recorded as the client describes them, which is enough to design against and not enough to build to.
- **GEO-001** — Central Nile Delta ground is well characterised as a region, and that is enough to assume a foundation type for layout. It is not enough to size one: allowable bearing pressure, the water table and sulphate content are plot figures, and this row stays open until they arrive with a source - boreholes, or figures the engineer will sign.
- **CLI-001** — Each instruction with its date and what it settled. Written down because a decision that lives only in a conversation gets re-argued: scheme A was chosen off three live options, and the plans were redrawn to it.

## Package A — Presentation and estimation

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-01 | Exterior views - axonometric, three schemes | Presentation | 1:250 | A1 sheet | D | issued | — | A-430 |
| A-02 | Interior cutaway axonometric - ground floor, +0.00 | Presentation | 1:75 | A1 sheet | D | issued | — | A-02 |
| A-03 | Interior cutaway axonometric - first floor, +3.30 | Presentation | 1:75 | A1 sheet | D | issued | — | A-03 |
| A-04 | Interior cutaway axonometric - second floor, +6.60 | Presentation | 1:75 | A1 sheet | D | issued | — | A-04 |
| A-05 | Interior cutaway axonometric - third floor, +9.90 | Presentation | 1:75 | A1 sheet | D | issued | — | A-05 |
| A-06 | Interior cutaway axonometric - penthouse floor, +13.20 | Presentation | 1:75 | A1 sheet | D | issued | — | A-06 |
| A-07 | Architectural design brief | Architecture | - | Report | D | issued | ARC-101, ARC-200 | — |
| A-08 | Cost estimation report - elemental | Cost | - | Report | X | issued | QS-001, QS-004 | — |

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
| ARC-001 | Cover sheet, project data and drawing index | Architecture | - | A1 sheet | D | issued | ARC-000 | ARC-001 |
| ARC-002 | General notes, symbols and code compliance matrix | Architecture | - | A1 sheet | L | issued | — | ARC-002 |
| ARC-100 | Context and master site plan | Architecture | 1:75 | A1 sheet | D | issued | SUR-001 | A-000 |
| ARC-101 | Ground floor plan, +0.00 | Architecture | 1:50 | A1 sheet | D | issued | — | A-100 |
| ARC-102 | First floor plan, +3.30 | Architecture | 1:50 | A1 sheet | D | issued | — | A-101 |
| ARC-103 | Second floor plan, +6.60 | Architecture | 1:50 | A1 sheet | D | issued | — | A-102 |
| ARC-104 | Third floor plan, +9.90 | Architecture | 1:50 | A1 sheet | D | issued | — | A-103 |
| ARC-105 | Penthouse floor plan, +13.20 | Architecture | 1:50 | A1 sheet | D | issued | — | A-104 |
| ARC-106 | Roof plan over the penthouse, +16.45 | Architecture | 1:50 | A1 sheet | D | issued | — | ARC-106 |
| ARC-200 | Facade elevations - all four faces, scheme A | Architecture | 1:50 / 1:75 | A1 sheet | D | issued | CLI-001 | A-400, A-401, A-402 |
| ARC-300 | Longitudinal section A-A | Architecture | 1:50 | A1 sheet | D | issued | — | A-200 |
| ARC-301 | Transverse section B-B | Architecture | 1:50 | A1 sheet | D | issued | ARC-300 | ARC-301 |
| ARC-400 | Reflected ceiling plan - ground floor, +0.00 | Architecture | 1:50 | A1 sheet | D | issued | ARC-101 | ARC-400 |
| ARC-401 | Reflected ceiling plan - first floor, +3.30 | Architecture | 1:50 | A1 sheet | D | issued | ARC-102 | ARC-401 |
| ARC-402 | Reflected ceiling plan - second floor, +6.60 | Architecture | 1:50 | A1 sheet | D | issued | ARC-103 | ARC-402 |
| ARC-403 | Reflected ceiling plan - third floor, +9.90 | Architecture | 1:50 | A1 sheet | D | issued | ARC-104 | ARC-403 |
| ARC-404 | Reflected ceiling plan - penthouse floor, +13.20 | Architecture | 1:50 | A1 sheet | D | issued | ARC-105 | ARC-404 |
| ARC-500 | Door and window schedule | Architecture | 1:100 | A1 sheet | D | issued | ARC-200 | ARC-500 |
| ARC-600 | Construction details | Architecture | 1:5 / 1:10 | A1 sheet | L | issued | CLI-001 | ARC-600 |
| ARC-700 | External works and landscape | Architecture | 1:75 | A1 sheet | D | issued | ARC-100 | ARC-700 |

- **ARC-000** — This register. Status on it is derived at build time from the sheet builders and the files on disk.
- **ARC-001** — The index is built from the sheet builders, not typed beside them; only the cover's own row is written down, and a check proves it matches the sheet.
- **ARC-002** — Notes and symbols are ours. The matrix is set against ECP 201 and ECP 203, the Egyptian codes the site is governed by, and signed off by the architect of record.
- **ARC-100** — Issued with the boundary marked indicative.
- **ARC-106** — Outlines, parapets, plant deck and levels are exact; the falls and outlet positions are architectural intent and PL-200 sets the real ones.
- **ARC-200** — South, the three other faces, and the street elevation in context. Schemes B and C still build and stay in the repository as the record of what was offered, but they are stamped not selected and left out of the issue.
- **ARC-301** — Cut east-west at y 10.80, looking north: the only drawing of the building's width, its spine and its two setbacks. The cantilever is not in it - an east-west cut crosses the balcony, it does not project - and A-A carries that.
- **ARC-400** — Run off the floor plan with its fittings switched off, so it cannot drift from it. A bulkhead over every room the plan calls wet; no light fitting drawn, because the EL-200 series governs those.
- **ARC-401** — Run off the floor plan with its fittings switched off, so it cannot drift from it. A bulkhead over every room the plan calls wet; no light fitting drawn, because the EL-200 series governs those.
- **ARC-402** — Run off the floor plan with its fittings switched off, so it cannot drift from it. A bulkhead over every room the plan calls wet; no light fitting drawn, because the EL-200 series governs those.
- **ARC-403** — Run off the floor plan with its fittings switched off, so it cannot drift from it. A bulkhead over every room the plan calls wet; no light fitting drawn, because the EL-200 series governs those.
- **ARC-404** — Run off the floor plan with its fittings switched off, so it cannot drift from it. A bulkhead over every room the plan calls wet; no light fitting drawn, because the EL-200 series governs those.
- **ARC-500** — Every opening in the building is already a constant, so the schedule is measured rather than compiled.
- **ARC-600** — Balcony nosing, parapet, threshold, roof upstand. Buildability, waterproofing and thermal performance are the specifier's, not ours.
- **ARC-700** — The entrance garden, gate, pergola, paving and barbecue are drawn on A-000 and would otherwise fall straight out of the quantities.

## Package C — Structure

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STR-001 | Structural notes, materials and design criteria | Structure | - | A1 sheet | L | issued | — | STR-001 |
| STR-100 | Excavation, grading and shoring | Structure | 1:75 | A1 sheet | L | issued | GEO-001, SUR-001 | STR-100 |
| STR-101 | Foundation layout | Structure | 1:50 | A1 sheet | L | issued | GEO-001, STR-200 | STR-101 |
| STR-200 | Column schedule and grid | Structure | 1:50 | A1 sheet | L | issued | — | STR-200 |
| STR-301 | Slab framing layout at +0.00 | Structure | 1:50 | A1 sheet | L | issued | STR-200 | STR-301 |
| STR-302 | Slab framing layout at +3.30 | Structure | 1:50 | A1 sheet | L | issued | STR-200 | STR-302 |
| STR-303 | Slab framing layout at +6.60 | Structure | 1:50 | A1 sheet | L | issued | STR-200 | STR-303 |
| STR-304 | Slab framing layout at +9.90 | Structure | 1:50 | A1 sheet | L | issued | STR-200 | STR-304 |
| STR-305 | Slab framing layout at +13.20 | Structure | 1:50 | A1 sheet | L | issued | STR-200 | STR-305 |
| STR-306 | Slab framing layout at +16.45 | Structure | 1:50 | A1 sheet | L | issued | STR-200 | STR-306 |
| STR-400 | Retaining and boundary walls | Structure | 1:75 | A1 sheet | L | issued | SUR-001, GEO-001 | STR-400 |
| STR-500 | Cantilever balcony structure | Structure | 1:20 | A1 sheet | L | issued | CLI-001, STR-302 | STR-500 |

- **STR-001** — To ECP 203, with loads to ECP 201. The seismic zone and its design ground acceleration, the wind basis and the concrete grades are set and signed by the structural engineer. No values assumed here.
- **STR-101** — Grid and column positions are exact; footing sizes, depths and reinforcement are the engineer's.
- **STR-200** — Every column coordinate, carried through all five levels. Sections and reinforcement left blank.
- **STR-305** — The penthouse floor and the roof over the third floor are the same slab.
- **STR-400** — Boundary line awaits the measured survey.
- **STR-500** — A 2.00 m curved cantilever repeated on four levels is the most engineering-sensitive element in the building, and had no deliverable in the list as given.

## Package D — Building services

| Code | Deliverable | Discipline | Scale | Format | Class | Status | Waits on | Resolves to |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EL-100 | Power and small power layout - ground floor, +0.00 | Electrical | 1:50 | A1 sheet | L | issued | ARC-101 | EL-100 |
| EL-101 | Power and small power layout - first floor, +3.30 | Electrical | 1:50 | A1 sheet | L | issued | ARC-102 | EL-101 |
| EL-102 | Power and small power layout - second floor, +6.60 | Electrical | 1:50 | A1 sheet | L | issued | ARC-103 | EL-102 |
| EL-103 | Power and small power layout - third floor, +9.90 | Electrical | 1:50 | A1 sheet | L | issued | ARC-104 | EL-103 |
| EL-104 | Power and small power layout - penthouse floor, +13.20 | Electrical | 1:50 | A1 sheet | L | issued | ARC-105 | EL-104 |
| EL-200 | Lighting and switching layout - ground floor, +0.00 | Electrical | 1:50 | A1 sheet | L | issued | ARC-101 | EL-200 |
| EL-201 | Lighting and switching layout - first floor, +3.30 | Electrical | 1:50 | A1 sheet | L | issued | ARC-102 | EL-201 |
| EL-202 | Lighting and switching layout - second floor, +6.60 | Electrical | 1:50 | A1 sheet | L | issued | ARC-103 | EL-202 |
| EL-203 | Lighting and switching layout - third floor, +9.90 | Electrical | 1:50 | A1 sheet | L | issued | ARC-104 | EL-203 |
| EL-204 | Lighting and switching layout - penthouse floor, +13.20 | Electrical | 1:50 | A1 sheet | L | issued | ARC-105 | EL-204 |
| EL-300 | Low voltage, data and security layout - ground floor, +0.00 | Electrical | 1:50 | A1 sheet | L | issued | ARC-101 | EL-300 |
| EL-301 | Low voltage, data and security layout - first floor, +3.30 | Electrical | 1:50 | A1 sheet | L | issued | ARC-102 | EL-301 |
| EL-302 | Low voltage, data and security layout - second floor, +6.60 | Electrical | 1:50 | A1 sheet | L | issued | ARC-103 | EL-302 |
| EL-303 | Low voltage, data and security layout - third floor, +9.90 | Electrical | 1:50 | A1 sheet | L | issued | ARC-104 | EL-303 |
| EL-304 | Low voltage, data and security layout - penthouse floor, +13.20 | Electrical | 1:50 | A1 sheet | L | issued | ARC-105 | EL-304 |
| ME-100 | HVAC layout - ground floor, +0.00 | Mechanical | 1:50 | A1 sheet | L | issued | ARC-101 | ME-100 |
| ME-101 | HVAC layout - first floor, +3.30 | Mechanical | 1:50 | A1 sheet | L | issued | ARC-102 | ME-101 |
| ME-102 | HVAC layout - second floor, +6.60 | Mechanical | 1:50 | A1 sheet | L | issued | ARC-103 | ME-102 |
| ME-103 | HVAC layout - third floor, +9.90 | Mechanical | 1:50 | A1 sheet | L | issued | ARC-104 | ME-103 |
| ME-104 | HVAC layout - penthouse floor, +13.20 | Mechanical | 1:50 | A1 sheet | L | issued | ARC-105 | ME-104 |
| PL-100 | Water supply layout - ground floor, +0.00 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-101 | PL-100 |
| PL-101 | Water supply layout - first floor, +3.30 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-102 | PL-101 |
| PL-102 | Water supply layout - second floor, +6.60 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-103 | PL-102 |
| PL-103 | Water supply layout - third floor, +9.90 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-104 | PL-103 |
| PL-104 | Water supply layout - penthouse floor, +13.20 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-105 | PL-104 |
| PL-200 | Drainage layout - ground floor, +0.00 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-101 | PL-200 |
| PL-201 | Drainage layout - first floor, +3.30 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-102 | PL-201 |
| PL-202 | Drainage layout - second floor, +6.60 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-103 | PL-202 |
| PL-203 | Drainage layout - third floor, +9.90 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-104 | PL-203 |
| PL-204 | Drainage layout - penthouse floor, +13.20 | Plumbing | 1:50 | A1 sheet | L | issued | ARC-105 | PL-204 |
| EL-400 | Electrical single line diagram | Electrical | Schematic | A1 sheet | L | issued | EL-100 | EL-400 |
| ME-200 | HVAC schematic and plant arrangement | Mechanical | Schematic | A1 sheet | L | issued | ME-100, ARC-106 | ME-200 |
| PL-300 | Drainage and water riser diagram | Plumbing | Schematic | A1 sheet | L | issued | PL-100, PL-200 | PL-300 |

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
| QS-001 | Bill of quantities - itemised, unpriced, by trade | Quantity surveying | - | Spreadsheet | D | issued | ARC-101, ARC-700 | — |
| QS-002 | Bill of materials | Quantity surveying | - | Spreadsheet | D | issued | QS-001 | — |
| QS-003 | Material requisitions and specifications | Procurement | - | Schedule | L | issued | QS-002, CLI-001 | — |
| QS-004 | Owner's cost baseline | Cost | - | Spreadsheet | X | issued | QS-001 | — |

- **QS-001** — Measured off the geometry: wall lengths, slab areas and opening counts reconcile to the plans they came from.
- **QS-002** — The same measure resolved into materials rather than trades: blockwork, concrete, reinforcement allowance, glazing and joinery.
- **QS-003** — Quantities are ours; performance specifications and approved-equal judgements are the specifier's.
- **QS-004** — The measured quantities with a rate column, for budgeting and for checking a quotation against. Rates stay empty until a named source fills them - nothing here goes out to tender.

## Open items and standing qualifications

1. A measured topographic and boundary survey (SUR-001) is not in hand; boundaries on A-000 are issued marked indicative.
2. The ground is central Nile Delta, which is well characterised as a region — enough to assume a foundation type and lay the structure out, not enough to size it. Allowable bearing pressure, the water table and sulphate content are plot figures, and GEO-001 stays open until they arrive with a source. No soil value is written on any sheet here.
3. The north neighbour is a single storey, confirmed by the client. The north wall carries windows on all five levels; only the ground floor looks at anything, and from +3.30 up they clear its roof. Its exact height and position still come with SUR-001.
4. The exterior is settled: scheme A, “Wave”, adopted at P18. Schemes B and C still build and stay in the repository as the record of what was offered, stamped not selected and left out of the issue.
5. Sheets A-300, A-301 and A-302 are withdrawn at P22, being enlargements of apartments the villa does not have. They still build and stay in the repository as the record, stamped on the face and left out of the issue.
6. ARC-600 draws four junctions figured from the geometry, and names against QS-003 every build-up it does not specify. Until those topics are answered no detail on it can be built, priced or warranted, and no quantity is taken from it.
7. Rates are class X throughout. No rate appears in any document here without a named source, and QS-004 is issued with its rate column open.

