# Client Instructions and Decisions

Every instruction that changed the drawings, grouped by what it changed rather than strictly by date — several were given in one sitting. Each one names the constant the decision became, so a decision cannot be recorded here and left unbuilt.

## Exterior scheme — 2026-10-07

**Instruction.** Scheme A, “Wave” — the serpentine balcony and the contemporary skin, chosen from three live options plus the curve then drawn.

**Where it lives.** `geometry.SCHEME / geometry.PROFILE`

**What it moved.** The plans carried the superseded curve, 17.4 m² a floor to the full 2.00 m. They are redrawn to the serpentine: 1.95 m at each end, 0.75 m at the waist, 12.8 m² a floor. A-000 and A-100 to A-104 re-issued at P18; schemes B and C stamped not selected and dropped from the issue.

## Internal partitions — 2026-10-07

**Instruction.** 100 mm red brick, where the drawings had a 120 mm partition of unstated material.

**Where it lives.** `geometry.PT / geometry.WALL_MATERIAL`

**What it moved.** Every partition is redrawn 20 mm thinner and the bill names the material. It also found a fault: six walls, 21.29 m of them, were set out between two hard-coded coordinates whose gap was 120 mm only because PT was, so they went on being drawn 120 mm and left the bill of quantities silently. Those walls now follow PT, and a check refuses any wall whose thickness is not a declared one.

## External and party walls — 2026-10-07

**Instruction.** Brick, of any colour — the 300 mm walls, which had been left unspecified rather than assumed.

**Where it lives.** `geometry.WALL_MATERIAL`

**What it moved.** The largest masonry item in the bill stops reading “material to be specified” — it is measured on QS-001 and named there. The colour being free is a decision and not a gap: both faces are plastered or rendered, so no brick on this building is ever seen and a facing brick would be bought and buried. The bill, the bill of materials and the key on every sheet that carries one now name it; the specification schedule stops asking for it and asks only for the size, strength and mortar. Nothing moved — no line on any drawing changes, because a material is not a dimension. The parapet is now the one wall nobody has specified.

## Balcony waist — 2026-10-07

**Instruction.** The serpentine's waist deepened from 0.75 m to 1.35 m, holding the deep ends at 1.95 m under the 2.00 m cap.

**Where it lives.** `geometry.EL_SERP_MEAN / geometry.EL_SERP_AMP`

**What it moved.** 0.75 m was a planting ledge; 1.35 m is usable the whole way along the frontage. The curve now swings 0.60 m rather than 1.20 m, so it reads as a gentler wave, and carries 15.7 m² a floor instead of 12.8 — 62.7 m² over the four balcony levels. It also overtakes scheme C's facet, which the C sheet used to beat it on. A-000 and A-100 to A-104 re-issued at P19.

## Site — 2026-10-07

**Instruction.** Shamandeel, Quesna, Menoufia, Egypt — central Nile Delta.

**Where it lives.** `frame.LOCATION / frame.CODES`

**What it moved.** Printed in the title block of every sheet. Fixes ECP 201 and ECP 203 as the governing codes, and with them the seismic and wind basis the structural engineer will name on STR-001.

## Ground conditions — 2026-10-07

**Instruction.** Delta ground, known as a region; no site investigation commissioned.

**Where it lives.** `—`

**What it moved.** Enough to assume a foundation type and lay the structure out, not enough to size one. GEO-001 stays open. No soil value was written on any sheet until the figures of 2026-10-12 below.

## Plot dimensions final — 2026-10-13

**Instruction.** The dimensions the client supplied are final; the boundary is no longer to be drawn indicative.

**Where it lives.** `geometry.PLOT`

**What it moved.** It ratifies a resolution the set had made: the sketch recorded a 0.50 m notch in the north boundary and a 5.50 m offset between the two north walls, which could not both be true, and the straight boundary at y = 18.00 was chosen. Nothing in the geometry moves - only its standing. SUR-001 stays open for independent measurement and setting out, which a client's figure is not: the villa stands 1.00 m clear of three boundaries and a plot narrower than stated is found out on site.

## Parapet material — 2026-10-13

**Instruction.** The 250 mm parapet to be brick, rendered both faces, like the rest of the building.

**Where it lives.** `geometry.WALL_MATERIAL`

**What it moved.** The last wall in the set that was not specified. It names the material and nothing else: since P32 the parapet is also the guard at BALUSTRADE_H, and whether 250 mm of brick carries that load is the engineer's, recorded on STR-400. The same round found that P32's own guard round the penthouse roof — 33.06 m of it — was in the bill nowhere, because the five floor plans stop below it; the parapet row goes from 27.13 to 63.49 m².

## Access to the penthouse roof — 2026-10-13

**Instruction.** The +16.45 roof to be given permanent access, accepting that the top of the building rises with it.

**Where it lives.** `geometry.EL_TOP`

**What it moved.** A fixed ladder from the north terrace, on A-104 and ARC-106 — not the open corridor, which the pergola covers end to end. The 0.60 m upstand becomes a guard at BALUSTRADE_H, so EL_TOP goes from +17.05 to +17.55 and the envelope rule in checks.py reads the constant rather than the old literal. The first and only instruction that has raised the agreed top. The same round corrected three documents that put the water tanks on the +16.45 roof: the plant deck is at +13.20 and the stair always reached it.

## Assumed ground parameters — 2026-10-12

**Instruction.** Regional typical bearing, sulphate and chloride figures supplied, with the groundwater table given as confirmed at 2.50 m below natural ground level.

**Where it lives.** `geometry.GROUND`

**What it moved.** Recorded on GEO-002 with each figure's basis, and printed on STR-100 and STR-101 beside the stamp that says what it is. GEO-001 is not closed by them: a regional typical has no source and the water table has no borehole. The water table is the one that changes a drawing — it lies below the depth the bearing figures assume, so STR-100 draws no dewatering.

## North neighbour — 2026-10-07

**Instruction.** A single storey, as on the east.

**Where it lives.** `geometry.NBR_N_STOREYS`

**What it moved.** The last unknown face. Only the ground-floor north windows look at anything; from +3.30 up they clear its roof. Nothing in the plans had to move.

## Site, corrected — 2026-10-12

**Instruction.** Ezbit Abu Rukbah, Quesna, Menoufia, Egypt — replacing Shamandeel, which was the wrong village.

**Where it lives.** `frame.LOCATION`

**What it moved.** The title block of every sheet named the wrong place for twenty-nine revisions, so the whole set reissues at P30 — this is the one change that touches all 74 drawings without altering a line of the building. The instruction of 2026-10-07 above is left as it was given.

