# Assumed Ground Parameters

The soil figures this set's layout rests on. Every one of them is written here with its basis, and the basis is the point of the document.

**This is not a ground investigation and it does not close GEO-001.** No borehole was sunk, no sample was tested and no engineer has signed any figure below. Nothing here may be designed to, and no foundation may be sized from it.

It exists because the assumption was being made either way. A set that draws pad footings under twelve columns has already assumed a bearing pressure and a founding stratum; for thirty revisions this one made that assumption silently and said the soil values "do not exist yet". They did exist, as regional knowledge rather than measurement. Writing them down is what lets the engineer disagree with a number instead of guessing at one.

| Parameter | Figure | Basis | Bears on |
| --------- | ------ | ----- | -------- |
| Net allowable bearing pressure | 80 - 110 kPa | ASSUMED - Nile Delta regional typical, no source | On undisturbed natural alluvial silty clay at 1.2 - 1.8 m depth. Consolidation settlement governs over shear failure. |
| Bearing pressure, replaced ground | 120 - 150 kPa | ASSUMED - Nile Delta regional typical, no source | Reachable by taking out the soft organic crust and replacing it with 0.8 - 1.2 m of compacted sandy gravel. The replacement is a design decision nobody has taken. |
| Groundwater table | 2.50 m below natural ground level | CLIENT-CONFIRMED - not measured, no borehole | Below the 1.2 - 1.8 m the bearing figures assume, so the dig is dry at that depth. Seasonal fluctuation with flood irrigation next door is not quantified here. |
| Sulphates in soil | 0.20 - 0.80 % by weight | ASSUMED - Nile Delta regional typical, no source | 2,000 - 8,000 mg/kg. Agricultural runoff and fertiliser. |
| Sulphates in groundwater | 1,200 - 3,500 mg/L | ASSUMED - Nile Delta regional typical, no source | Reported as ECP 203 moderate to severe exposure, class 2 to 3. The class is quoted as given, not determined here. |
| Chlorides in soil | 0.05 - 0.30 % by weight | ASSUMED - Nile Delta regional typical, no source | Pitting and depassivation risk to foundation reinforcement. |
| Chlorides in groundwater | 500 - 2,000 mg/L | ASSUMED - Nile Delta regional typical, no source | Bears on cover and cement type, both of which are specification. |

## The two kinds of fact in that table

The ranges are **regional typicals for the central Nile Delta** and have no source whatever. They are the published character of Delta alluvium, not of this plot, and the plot can differ from its region by more than the range is wide.

The water table is **the client's**, who gives it as confirmed for this plot at 2.50 m below natural ground level. That is a better fact than a regional typical and still not a measurement, so it is recorded the way this set already records the neighbours' heights on SUR-001: as the client describes them, which is enough to design against and not enough to build to.

## What follows from it, and what does not

The bearing figures are quoted at 1.2 - 1.8 m. The water table lies below that, so a dig to that depth is expected to be dry, and STR-100 draws no dewatering. That is the one place where a figure in this table changes what a drawing shows, and it is the one most worth confirming first: the figure is a single depth with no seasonal range on it, and the fields next door are flood-irrigated.

The sulphate and chloride figures are reported as ECP 203 moderate to severe exposure, class 2 to 3. That class is quoted as it was given and is not determined here. Cement type, cover and water-cement ratio follow from it and are the engineer's specification; none of them is written on any sheet in this set.

The replacement-layer bearing pressure describes a ground improvement nobody has decided on. It is listed so the option is visible, not because it is in the design.

## What would close GEO-001
Boreholes to a depth the engineer specifies, with laboratory testing for sulphates and chlorides, reported and signed. Four rows wait on it: STR-100, STR-101, STR-400 and PRG-002. Until then every figure above travels with its stamp, and `checks.ground_figures_own_their_basis` refuses any sheet that prints one without it.
