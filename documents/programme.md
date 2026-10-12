# Design and Information Release Programme

The order the work has to happen in, derived from the register's own dependencies rather than judged by eye. Every deliverable in the Master Deliverables List appears here exactly once, in the earliest stage it can possibly sit in.

## There are no dates in this document

That is not an omission, it is the same rule the rest of the set is issued under. A duration is a commitment somebody makes — the surveyor, the municipality holding the permit, the structural engineer, the contractor — and none of those people have been asked yet. A bar chart with invented bar lengths is the programme equivalent of a foundation detail with invented reinforcement: it looks like information, it gets built from, and it is worth nothing. So the **Duration** column below is printed open, exactly as QS-004's rate column is, and **PRG-002** — the dated construction programme — is in the register as class X and not started.

What is here instead is true and useful today: the sequence, the longest chain through the project, and what each thing the project cannot produce is holding up.

## Where the project stands

- **84 deliverables** in **6 stages**.
- **20** wait on nothing at all and could be started the day the brief is agreed.
- **12** sit behind something this project cannot produce. **10** of those are issued anyway, against an assumption written on the face of the drawing; the other **2** cannot start. See the gates below.
- The longest chain is **6 deliverables** deep. Nothing compresses it, because each step waits on the one before it.

## The critical chain

The longest path through the register. This is the project's own lower bound on time, named at the start rather than discovered at the end:

**SUR-001** Measured topographic and boundary survey — class X, open duration
  ↳ **ARC-100** Context and master site plan — class D, open duration
    ↳ **ARC-700** External works and landscape — class D, open duration
      ↳ **QS-001** Bill of quantities - itemised, unpriced, by trade — class D, open duration
        ↳ **QS-004** Owner's cost baseline — class X, open duration
          ↳ **A-08** Cost estimation report - elemental — class X, open duration

It starts at a survey nobody has commissioned and ends at a cost report, which is worth reading twice: the figure the owner most wants is the furthest thing in the project from being producible, and the single instruction that shortens the whole programme is to order SUR-001.

## The gates

A gate is a class X row — something that cannot be produced here at any level of effort. The count is the argument: each is one line in the register with this much work standing behind it.

The second column matters as much as the first. Where the design could proceed against an open gate it has, and the drawing says so on its face: ARC-100 is issued with the boundary marked indicative, not held back until a surveyor arrives. Those rows are **issued provisionally** — real, usable, and liable to move when the gate closes. The rest genuinely cannot start.

| Gate | What it is | Issued provisionally | Cannot start | Blocked deliverables |
| --- | --- | ---: | ---: | --- |
| **SUR-001** | Measured topographic and boundary survey | 10 | 2 | GEO-001, PRG-002 |
| **GEO-001** | Soil investigation and foundation recommendation | 3 | 1 | PRG-002 |
| **QS-004** | Owner's cost baseline | 1 | 0 | — |
| **A-08** | Cost estimation report - elemental | 0 | 0 | — |
| **PRG-002** | Dated construction programme | 0 | 0 | — |

A row counted provisional is not a row that got away with something: it is a decision, recorded, to issue against an assumption that is written on the drawing. When the gate closes, every one of them is re-checked against what arrives, and any that moves is reissued at the next revision.

## The sequence

Stage 0 waits on nothing. A row in stage *n* has at least *n* deliverables that must finish in order before it starts — not before one of them is done, before all of them are. Status is the register's, derived at build time.

| Stage | Deliverable | | Class | Status | Waits on | Duration |
| ---: | --- | --- | :-: | --- | --- | --- |
| 0 | **SUR-001** | Measured topographic and boundary survey | X | not started | — | open |
| 0 | **GEO-002** | Assumed ground parameters for layout | D | issued | — | open |
| 0 | **CLI-001** | Client instructions and decisions record | D | issued | — | open |
| 0 | **A-01** | Exterior views - axonometric, three schemes | D | issued | — | open |
| 0 | **A-02** | Interior cutaway axonometric - ground floor, +0.00 | D | issued | — | open |
| 0 | **A-03** | Interior cutaway axonometric - first floor, +3.30 | D | issued | — | open |
| 0 | **A-04** | Interior cutaway axonometric - second floor, +6.60 | D | issued | — | open |
| 0 | **A-05** | Interior cutaway axonometric - third floor, +9.90 | D | issued | — | open |
| 0 | **A-06** | Interior cutaway axonometric - penthouse floor, +13.20 | D | issued | — | open |
| 0 | **ARC-000** | Master deliverables list and document register | D | issued | — | open |
| 0 | **ARC-002** | General notes, symbols and code compliance matrix | L | issued | — | open |
| 0 | **ARC-101** | Ground floor plan, +0.00 | D | issued | — | open |
| 0 | **ARC-102** | First floor plan, +3.30 | D | issued | — | open |
| 0 | **ARC-103** | Second floor plan, +6.60 | D | issued | — | open |
| 0 | **ARC-104** | Third floor plan, +9.90 | D | issued | — | open |
| 0 | **ARC-105** | Penthouse floor plan, +13.20 | D | issued | — | open |
| 0 | **ARC-106** | Roof plan over the penthouse, +16.45 | D | issued | — | open |
| 0 | **ARC-300** | Longitudinal section A-A | D | issued | — | open |
| 0 | **STR-001** | Structural notes, materials and design criteria | L | issued | — | open |
| 0 | **STR-200** | Column schedule and grid | L | issued | — | open |
| 1 | **GEO-001** | Soil investigation and foundation recommendation | X | blocked | SUR-001 | open |
| 1 | **ARC-001** | Cover sheet, project data and drawing index | D | issued | ARC-000 | open |
| 1 | **ARC-100** | Context and master site plan | D | issued | SUR-001 | open |
| 1 | **ARC-200** | Facade elevations - all four faces, scheme A | D | issued | CLI-001 | open |
| 1 | **ARC-301** | Transverse section B-B | D | issued | ARC-300 | open |
| 1 | **ARC-400** | Reflected ceiling plan - ground floor, +0.00 | D | issued | ARC-101 | open |
| 1 | **ARC-401** | Reflected ceiling plan - first floor, +3.30 | D | issued | ARC-102 | open |
| 1 | **ARC-402** | Reflected ceiling plan - second floor, +6.60 | D | issued | ARC-103 | open |
| 1 | **ARC-403** | Reflected ceiling plan - third floor, +9.90 | D | issued | ARC-104 | open |
| 1 | **ARC-404** | Reflected ceiling plan - penthouse floor, +13.20 | D | issued | ARC-105 | open |
| 1 | **ARC-600** | Construction details | L | issued | CLI-001 | open |
| 1 | **STR-301** | Slab framing layout at +0.00 | L | issued | STR-200 | open |
| 1 | **STR-302** | Slab framing layout at +3.30 | L | issued | STR-200 | open |
| 1 | **STR-303** | Slab framing layout at +6.60 | L | issued | STR-200 | open |
| 1 | **STR-304** | Slab framing layout at +9.90 | L | issued | STR-200 | open |
| 1 | **STR-305** | Slab framing layout at +13.20 | L | issued | STR-200 | open |
| 1 | **STR-306** | Slab framing layout at +16.45 | L | issued | STR-200 | open |
| 1 | **EL-100** | Power and small power layout - ground floor, +0.00 | L | issued | ARC-101 | open |
| 1 | **EL-101** | Power and small power layout - first floor, +3.30 | L | issued | ARC-102 | open |
| 1 | **EL-102** | Power and small power layout - second floor, +6.60 | L | issued | ARC-103 | open |
| 1 | **EL-103** | Power and small power layout - third floor, +9.90 | L | issued | ARC-104 | open |
| 1 | **EL-104** | Power and small power layout - penthouse floor, +13.20 | L | issued | ARC-105 | open |
| 1 | **EL-200** | Lighting and switching layout - ground floor, +0.00 | L | issued | ARC-101 | open |
| 1 | **EL-201** | Lighting and switching layout - first floor, +3.30 | L | issued | ARC-102 | open |
| 1 | **EL-202** | Lighting and switching layout - second floor, +6.60 | L | issued | ARC-103 | open |
| 1 | **EL-203** | Lighting and switching layout - third floor, +9.90 | L | issued | ARC-104 | open |
| 1 | **EL-204** | Lighting and switching layout - penthouse floor, +13.20 | L | issued | ARC-105 | open |
| 1 | **EL-300** | Low voltage, data and security layout - ground floor, +0.00 | L | issued | ARC-101 | open |
| 1 | **EL-301** | Low voltage, data and security layout - first floor, +3.30 | L | issued | ARC-102 | open |
| 1 | **EL-302** | Low voltage, data and security layout - second floor, +6.60 | L | issued | ARC-103 | open |
| 1 | **EL-303** | Low voltage, data and security layout - third floor, +9.90 | L | issued | ARC-104 | open |
| 1 | **EL-304** | Low voltage, data and security layout - penthouse floor, +13.20 | L | issued | ARC-105 | open |
| 1 | **ME-100** | HVAC layout - ground floor, +0.00 | L | issued | ARC-101 | open |
| 1 | **ME-101** | HVAC layout - first floor, +3.30 | L | issued | ARC-102 | open |
| 1 | **ME-102** | HVAC layout - second floor, +6.60 | L | issued | ARC-103 | open |
| 1 | **ME-103** | HVAC layout - third floor, +9.90 | L | issued | ARC-104 | open |
| 1 | **ME-104** | HVAC layout - penthouse floor, +13.20 | L | issued | ARC-105 | open |
| 1 | **PL-100** | Water supply layout - ground floor, +0.00 | L | issued | ARC-101 | open |
| 1 | **PL-101** | Water supply layout - first floor, +3.30 | L | issued | ARC-102 | open |
| 1 | **PL-102** | Water supply layout - second floor, +6.60 | L | issued | ARC-103 | open |
| 1 | **PL-103** | Water supply layout - third floor, +9.90 | L | issued | ARC-104 | open |
| 1 | **PL-104** | Water supply layout - penthouse floor, +13.20 | L | issued | ARC-105 | open |
| 1 | **PL-200** | Drainage layout - ground floor, +0.00 | L | issued | ARC-101 | open |
| 1 | **PL-201** | Drainage layout - first floor, +3.30 | L | issued | ARC-102 | open |
| 1 | **PL-202** | Drainage layout - second floor, +6.60 | L | issued | ARC-103 | open |
| 1 | **PL-203** | Drainage layout - third floor, +9.90 | L | issued | ARC-104 | open |
| 1 | **PL-204** | Drainage layout - penthouse floor, +13.20 | L | issued | ARC-105 | open |
| 1 | **PRG-001** | Design and information release programme | D | issued | ARC-000 | open |
| 2 | **A-07** | Architectural design brief | D | issued | ARC-101, ARC-200 | open |
| 2 | **ARC-500** | Door and window schedule | D | issued | ARC-200 | open |
| 2 | **ARC-700** | External works and landscape | D | issued | ARC-100 | open |
| 2 | **STR-100** | Excavation, grading and shoring | L | issued | GEO-001, SUR-001 | open |
| 2 | **STR-101** | Foundation layout | L | issued | GEO-001, STR-200 | open |
| 2 | **STR-400** | Retaining and boundary walls | L | issued | SUR-001, GEO-001 | open |
| 2 | **STR-500** | Cantilever balcony structure | L | issued | CLI-001, STR-302 | open |
| 2 | **EL-400** | Electrical single line diagram | L | issued | EL-100 | open |
| 2 | **ME-200** | HVAC schematic and plant arrangement | L | issued | ME-100, ARC-106 | open |
| 2 | **PL-300** | Drainage and water riser diagram | L | issued | PL-100, PL-200 | open |
| 3 | **QS-001** | Bill of quantities - itemised, unpriced, by trade | D | issued | ARC-101, ARC-700 | open |
| 4 | **QS-002** | Bill of materials | D | issued | QS-001 | open |
| 4 | **QS-004** | Owner's cost baseline | X | issued | QS-001 | open |
| 4 | **PRG-002** | Dated construction programme | X | blocked | PRG-001, QS-001, GEO-001 | open |
| 5 | **A-08** | Cost estimation report - elemental | X | issued | QS-001, QS-004 | open |
| 5 | **QS-003** | Material requisitions and specifications | L | issued | QS-002, CLI-001 | open |

> **Nothing is issued as engineering that has not been engineered.**

The same rule reads, on a programme: no duration is issued that nobody has committed to.
