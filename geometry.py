#!/usr/bin/env python3
"""
geometry.py - the single source of truth for the building's set-out.

Origin (0, 0) is the south-west corner of the plot, x east, y north.  The
street runs along the south boundary and the entrance gate is at the west
end of the garden corridor.

Revision P3 converts the three-storey house into a four-storey building:

    +0.00   entrance, lounges, guest room/office, central service kitchen
    +3.30   two one-bedroom apartments
    +6.60   two one-bedroom apartments (identical to +3.30)
    +9.90   two-bedroom apartment, south terrace and north terrace

Only the WEST boundary is built against.  The client confirms that the
north and east boundaries are open to the environment and may be windowed;
the adjoining owner to the east will not build above 3.00 m.  The west
wall is therefore the only blind elevation, and it is opened over the
1.50 m where it faces the plot's own garden corridor.

Three set-out changes came with it:

  * The north boundary is taken as a straight line at y = 18.00.  The
    client's sketch recorded a 0.50 m notch across block A's width and a
    5.50 m offset between the two blocks' north walls; neither can be true
    at once.  Resolved in favour of a straight boundary, with both blocks
    running north to 18.00.  Still to be confirmed by measured survey.
  * The south wall of both blocks moves 1.50 m into the garden, to
    y = 3.50, so each block is 14.50 m deep.
  * Balconies on the upper floors cantilever a further 1.20 m south of
    that wall; the ground floor and the garden below are unaffected.

    garden corridor   west of the building, 11.50 x 5.00   =  57.50 m2
                      in front of it,       11.50 x 3.50   =  40.25 m2
    block A (front)                          6.50 x 14.50  =  94.25 m2
    block B (rear)                           5.00 x 14.50  =  72.50 m2
    plot                                                   = 264.50 m2
"""

import math

# ---------------------------------------------------------------------------
# site
# ---------------------------------------------------------------------------
PLOT_W = 23.00
GARDEN_D = 5.00                # corridor depth west of the building
GARDEN_D_E = 3.50              # corridor depth in front of the building
PLOT = [(0, 0), (23.00, 0), (23.00, 18.00), (11.50, 18.00),
        (11.50, 5.00), (0, 5.00)]

# ---------------------------------------------------------------------------
# building envelope (outside faces)
# ---------------------------------------------------------------------------
A_X0, A_X1 = 11.50, 18.00      # front block, 6.50 wide
A_Y0, A_Y1 = 3.50, 18.00       # 14.50 deep
B_X0, B_X1 = 18.00, 23.00      # rear block, 5.00 wide
B_Y0, B_Y1 = 3.50, 18.00       # 14.50 deep

WT = 0.30                      # external / party wall thickness
PT = 0.12                      # internal partition thickness
PARAPET = 0.25                 # terrace parapet thickness (1.10 m high)

# internal faces
a_x0, a_x1 = A_X0 + WT, 17.85          # 11.80 .. 17.85  (6.05 clear)
a_y0, a_y1 = A_Y0 + WT, A_Y1 - WT      #  3.80 .. 17.70  (13.90 clear)
b_x0, b_x1 = 18.15, B_X1 - WT          # 18.15 .. 22.70  (4.55 clear)
b_y0, b_y1 = B_Y0 + WT, B_Y1 - WT      #  3.80 .. 17.70  (13.90 clear)

PARTY_X0, PARTY_X1 = 17.85, 18.15      # wall shared by block A and block B

# ---------------------------------------------------------------------------
# RC frame
# ---------------------------------------------------------------------------
# Flat slab on a column grid set out on the wall centrelines, so every
# column falls inside a wall and none of them stands in a room.  Longest
# span 4.85 m, well within flat-slab range; the frame follows the plan
# rather than the plan working around the frame.
COL = 0.30                             # 300 x 300 columns
GRID_X = [11.65, 15.34, 18.00, 22.85]
GRID_Y = [3.65, 7.24, 10.54, 14.66, 17.85]

# ---------------------------------------------------------------------------
# vertical circulation core - identical on every floor
# ---------------------------------------------------------------------------
CORE_WALL_X = 15.28                    # west wall of the core, outer face
ST_X0, ST_X1 = 15.40, 17.85            # stair enclosure, clear
ST_Y0, ST_Y1 = 10.60, 14.60            # 2.45 x 4.00, two 1.10 m flights

LOB_X0, LOB_X1 = 15.40, 17.85          # protected lobby, clear
LOB_Y0, LOB_Y1 = 8.98, 10.48           # 2.45 x 1.50

LF_X0, LF_X1 = 15.40, 17.10            # lift shaft, clear
LF_Y0, LF_Y1 = 7.30, 8.86              # 1.70 x 1.56

RS_X0, RS_X1 = 17.20, 17.85            # services riser cupboard
RS_Y0, RS_Y1 = 7.30, 8.86              # 0.65 x 1.56, opens off the lobby

# Revision P4 removes the light court that used to fill the core's north
# end (2.45 x 2.98, open to sky on every floor).  It was there only because
# the north and east boundaries were taken as blind; with both open to the
# environment the same rooms are daylit from their own external walls, and
# the 7.3 m2 a floor comes back as usable area.
CORE_N = 14.72                         # north face of the stair enclosure

# 3.00 m clear ceiling height is the client's minimum; the structural zone
# (flat slab plus floor build-up) adds 0.30 m, so floors are 3.30 m apart.
CLEAR_HEIGHT = 3.00
STRUCTURAL_ZONE = 0.30
FLOOR_TO_FLOOR = CLEAR_HEIGHT + STRUCTURAL_ZONE          # 3.30 m

# the ground floor sits 0.50 m above the garden, reached by three risers
GARDEN_LEVEL = -0.50
ENTRY_RISERS = 3

# levels
LEVELS = {0: "+0.00", 1: "+3.30", 2: "+6.60", 3: "+9.90"}
ROOF_LEVEL = 13.20             # top of the slab over the third floor

# ---------------------------------------------------------------------------
# balconies - cantilevered 1.20 m beyond the south wall, floors 1 and 2
# ---------------------------------------------------------------------------
# Each balcony runs the full width of its own block, divided on the party
# wall line by a 250 mm screen, so every apartment gets the whole of its
# south frontage rather than a 3.00 m slot in the middle of it.
BALC_D = 1.20
BALC_A = (A_X0, 18.00)         # apartment A, 6.50 m - full width of block A
BALC_B = (18.00, B_X1)         # apartment B, 5.00 m - full width of block B

# ---------------------------------------------------------------------------
# openings in the south (garden) elevation - x ranges
# ---------------------------------------------------------------------------
WIN_A_1 = (12.20, 13.90)       # ground floor living, arched
WIN_A_2 = (14.10, 15.20)       # ground floor living, arched
DOOR_ENTRY = (16.05, 17.15)    # main entrance
WIN_B_1 = (18.70, 20.30)       # ground floor lounge, arched glazed door
WIN_B_2 = (21.00, 22.40)       # ground floor lounge, arched

UP_A_SOUTH = [(12.10, 13.80), (14.00, 15.20), (15.70, 17.50)]
UP_B_SOUTH = [(18.60, 20.40), (21.00, 22.40)]

# ---------------------------------------------------------------------------
# window in the west wall, in the 1.50 m where it faces our own garden
# ---------------------------------------------------------------------------
# South of y = 5.00 the plot's own garden corridor runs west, so this short
# length of the west wall is not a party wall and can be opened.  It gives
# apartment A's living room corner light and a view down the 23 m axis.
WIN_W_LIVING = (3.95, 4.85)

# ---------------------------------------------------------------------------
# openings in the east wall - y ranges
# ---------------------------------------------------------------------------
# The east boundary is open, so block B is windowed on this face at every
# level, at ordinary sill height.  Every range clears the 300 mm columns on
# GRID_Y, which stand in this wall at y 3.65, 7.24, 10.54, 14.66 and 17.85.
WIN_E_LIV_B = (4.60, 6.40)        # block B living room, every floor
WIN_E_LOUNGE = (7.60, 8.70)       # ground floor lounge, second window
WIN_E_LAUNDRY = (9.35, 10.15)     # ground floor central laundry
WIN_E_GBATH = (10.90, 11.90)      # ground floor guest bath
WIN_E_GBED = (15.00, 16.80)       # ground floor guest bedroom / office
WIN_E_BATH = (9.30, 10.20)        # apartment B bathroom, floors 1 and 2
WIN_E_BED = (12.20, 13.80)        # apartment B bedroom, floors 1 and 2
WIN_E_STUDY = (15.90, 17.10)      # apartment B dressing / study
WIN_E_BED1 = (8.50, 10.20)        # third floor, bedroom 1 (master)
WIN_E_ENS3 = (12.70, 13.90)       # third floor, master ensuite

# ---------------------------------------------------------------------------
# openings in the north wall - x ranges
# ---------------------------------------------------------------------------
# The north boundary is open too.  Block A's north end is one room 6.05 m
# wide on every floor now that the court has gone, and takes two windows;
# block B's north room takes two more, except on the third floor where the
# north terrace is in front of it and the wall becomes a parapet.
WIN_N_A = [(12.00, 13.60), (16.00, 17.40)]
WIN_N_B = [(18.80, 20.40), (21.00, 22.50)]

# ---------------------------------------------------------------------------
# villa ground floor (revision P5) - openings
# ---------------------------------------------------------------------------
# The building becomes one family villa, so the ground floor is re-set-out
# with two separate front doors on the south elevation: the family door at
# the west end of block A, nearest the garden corridor, and the guests'
# door into the majlis at the east end of block B.  They are as far apart
# as the frontage allows, which is what keeps the two routes from crossing.
#
# Every range clears the 300 mm columns on GRID_X / GRID_Y.
V_DOOR_FAMILY = (12.10, 13.30)      # family entrance, block A south
V_WIN_A_S = [(13.70, 15.10), (15.70, 17.50)]
V_DOOR_MAJLIS = (19.60, 20.90)      # guests' entrance, block B south
V_WIN_B_S = [(18.45, 19.35), (21.30, 22.50)]
V_DOOR_SERVICE = (18.80, 20.00)     # service door, block B north
V_WIN_B_N = [(21.00, 22.50)]
V_WIN_B_E = [(4.60, 6.40), (7.60, 9.00),    # majlis
             (11.40, 12.40),                 # guest WC
             (15.00, 16.80)]                 # dirty kitchen
V_PARTY_HALL = (4.60, 5.80)         # hall to majlis, arched, lockable
V_PARTY_SERVE = (15.40, 16.40)      # dirty kitchen to show kitchen

# villa first floor - block B is the second household's wing
V_PARTY_WING = (4.80, 5.90)         # family living into the wing's sitting room
V_WIN_B_E_1 = [(4.60, 6.40), (7.60, 8.50),   # wing sitting room
               (9.30, 10.20),                 # wing bathroom
               (12.20, 13.80),                # wing bedroom
               (15.90, 17.10)]                # wing dressing

# villa second floor - master suite in block A, two bedrooms in block B.
# The party wall is opened at the NORTH band here: block A's south band is
# the master bedroom, so the route into block B cannot run through it.
V_PARTY_BEDS = (15.40, 16.40)
V_WIN_B_E_2 = [(4.60, 6.40),                 # bedroom 4
               (9.30, 10.20),                # bath 4
               (11.60, 12.60),               # bath 3
               (15.00, 16.80)]               # bedroom 3
V_WIN_B_N_2 = [(18.40, 19.20), (20.00, 22.40)]   # wing hall, bedroom 3

# villa third floor - roof majlis, gym, maid's suite, one guest bedroom.
# The north terrace comes 2.00 m further south than it did as flats, so the
# gym can open onto it and block B keeps a usable depth of internal rooms.
V_TER_N_Y0 = 13.00
V_PARTY_MAJLIS = (4.80, 5.90)       # roof majlis into the guest bedroom
V_PARTY_TERRACE = (15.40, 16.40)    # gym out onto the north terrace
V_WIN_B_E_3 = [(4.60, 6.40), (7.60, 8.70),   # guest bedroom
               (9.30, 10.20),                 # guest ensuite
               (11.60, 12.60)]                # store and plant

# ---------------------------------------------------------------------------
# third floor
# ---------------------------------------------------------------------------
# The party wall can only be opened between y 3.80 and 7.18: north of that,
# block A's east strip is the stair, lobby, lift and riser, so the wall
# backs onto the core rather than onto a room.  The third floor apartment
# therefore runs its living space right across that band, which is the only
# place the two blocks can be joined inside one dwelling.  The south terrace
# moves out onto the cantilever so that it does not sit on the link.
LIV3_Y1 = 7.18                         # north face of the living band
TER_N_Y0, TER_N_Y1 = 15.00, 17.70      # north terrace, block B, 2.70 m deep


# ---------------------------------------------------------------------------
# detached villa, third floor (revision P6)
# ---------------------------------------------------------------------------
# The client has restarted the design.  The building is pulled 1.00 m off the
# west, north and east boundaries so that it stands clear of all three
# neighbours; the south is not set back, because there is no neighbour there
# to stand clear of - it faces the street across our own forecourt, and it is
# where the balcony goes.
#
# Detaching costs 22 % of every floor, and buys the one thing every earlier
# layout lacked: the wall between the old blocks A and B stops being a party
# wall.  There is no longer any line that can only be opened where a room
# happens to sit on both sides of it, so the floor is planned as a single
# 8.90 x 12.90 m plate.
#
# Only the third floor is drawn to this envelope for now, at the client's
# instruction; floors 0-2, the site plan and the section still sit on the old
# 11.50 x 14.50 footprint and must follow before the set is coherent again.
SETBACK = 1.00
V3_X0, V3_X1 = A_X0 + SETBACK, B_X1 - SETBACK      # 12.50 .. 22.00   (9.50)
V3_Y0, V3_Y1 = A_Y0, A_Y1 - SETBACK                #  3.50 .. 17.00  (13.50)

v3_x0, v3_x1 = V3_X0 + WT, V3_X1 - WT              # 12.80 .. 21.70   (8.90)
v3_y0, v3_y1 = V3_Y0 + WT, V3_Y1 - WT              #  3.80 .. 16.70  (12.90)
V3_PLATE = (v3_x1 - v3_x0) * (v3_y1 - v3_y0)       # 114.81 m2

# The spine: the one full-depth internal wall, dividing the west strip
# (living area, stair, hall, bedroom 3) from the east strip (the two suites).
# 300 mm, because it is structural - it carries both internal columns.
V3_SPINE_X0, V3_SPINE_X1 = 17.31, 17.61

# RC frame.  Three columns east-west, four north-south, every one of them on
# a wall centreline: the perimeter lines sit in the external walls whatever
# their other coordinate, and both internal intersections (17.46, 8.46) and
# (17.46, 12.56) fall inside the spine.  No column stands in a room.
V3_GRID_X = [12.65, 17.46, 21.85]                  # spans 4.81, 4.39
V3_GRID_Y = [3.65, 8.46, 12.56, 16.85]             # spans 4.81, 4.10, 4.29

# --- west strip -----------------------------------------------------------
# The whole west strip south of bedroom 3 is ONE room.  There is no wall
# between the living area and the stair: the stair stands in the living
# space as a feature, which is what "open living area" has to mean if it
# means anything.  Bedroom 3's wall is the only wall across the strip.
V3_LIV_Y1 = 12.42              # north face of the open living space

# A tea point rather than a second kitchen: counter, sink, kettle and coffee
# machine, in the living area's north-east corner against the spine, open to
# the room through a cased opening so it is part of the living space.  It
# costs the living area 2.3 m2 including its walls.
V3_PANT_X0, V3_PANT_X1 = 15.95, V3_SPINE_X0      # 1.36 clear
V3_PANT_Y0, V3_PANT_Y1 = 7.30, 9.00              # 1.70 clear
V3_PANT_OPEN = (16.20, 17.10)  # cased opening from the living area
V3_HALL_X0 = 16.27             # west face of the short hall to the north
V3_BED3_X1 = 16.15             # east face of bedroom 3, onto the hall
V3_BED3_Y0 = 12.54             # south face of bedroom 3
# The hall stops as soon as it has served its two doors.  It ran the full
# 4.16 m to the north wall, and everything past the far jamb of the last
# door was a dead end a metre wide - so it ends here and the 2.08 m beyond
# goes to the bedroom, which turns the corner behind it and picks up the
# north window over the old head of the spur.
V3_HALL_Y1 = 14.50             # north end of the hall; bedroom beyond

# A private villa stair, not the apartment block's: 900 mm flights, 18 risers
# at 183 mm with a 260 mm going, and a landing only as deep as a flight is
# wide.  2.00 x 3.30 against the west wall, where no room wants to be.
# The previous stair was 2.55 x 3.98 - 10.2 m2 of a 114.8 m2 floor.
V3_STAIR = (12.80, 9.12, 14.80, 12.42)   # stair well, clear: 2.00 x 3.30
V3_STAIR_RISE = 0.185          # target rise; 3.30 / 18 = 183 mm as drawn
V3_STAIR_GOING = 0.26
V3_STAIR_LANDING = 0.95
V3_STAIR_WELL = 0.20

# --- east strip: suite 1 south, shared bath in the middle, suite 2 north ---
# Suite 2 moves to the north end so its bedroom takes the north wall and can
# have a balcony off it, and the shared bath moves to the middle of the
# strip, where it is the same distance from the living area and from both
# suites - which is what makes it genuinely shared rather than suite 2's.
V3_S1_ENS_Y0 = 7.72            # suite 1: bedroom / ensuite
V3_S1_Y1 = 9.30                # suite 1 / shared bath
V3_BATH_Y1 = 11.00             # shared bath / suite 2
V3_S2_ENS_Y1 = 12.70           # suite 2: ensuite / bedroom

# Suite 2 has no balcony.  An inset one cost bedroom 2 2.5 m2 of floor for a
# 1.90 x 1.10 step-out, and a projecting one would have reached into the
# 1.00 m setback and put the building back against the boundary it was
# pulled off.  The bedroom takes the north wall and its windows instead.
V3_GIA = V3_PLATE

# doors through the spine, from the living area and the hall.  Each clears
# the 300 mm columns standing in that wall at y 8.46 and y 12.56.
V3_DOOR_S1 = (6.50, 7.40)      # living area into suite 1's bedroom
V3_DOOR_BATH = (10.10, 11.00)  # living area into the shared bath
V3_DOOR_S2 = (13.40, 14.30)    # hall into suite 2's bedroom
V3_DOOR_BED3 = (13.20, 14.10)  # hall into bedroom 3, through its east wall

# ---------------------------------------------------------------------------
# the south cantilever: a wavy reinforced-concrete balcony
# ---------------------------------------------------------------------------
# Asymmetric, a single curve, and bowed OUTWARD: every point on the edge
# stands further from the building than the straight line joining the two
# ends.  The earlier version drew in to 0.95 m between the ends, which made
# the balcony pinch in the middle exactly where the living area opens onto
# it; swelling the other way keeps the whole span usable and reads as one
# gesture pushing out toward the street.
#
# The two ends stay unequal - 2.00 m at the west, where the living area
# opens onto it, and 1.50 m at the east off suite 1.
#
#     p(t) = W + (E - W) t^2
#
# A parabola rather than a cubic, because two numbers already determine it:
# it leaves the deep end flat, sweeps away to the shallow end, and sits
# above the chord the whole way (p - chord = (E - W) t (t - 1), and with
# E < W both factors make that positive).  Nothing to tune, nothing to
# argue about beyond the two ends, and the deepest point is the west end,
# so the client's 2.00 m cap binds exactly where it is easiest to check.
V3_WAVE_SPAN = (V3_X0, V3_X1)
V3_WAVE_W = 2.00               # projection at the west end, and the deepest
V3_WAVE_E = 1.50               # projection at the east end
V3_WAVE_MAX = max(V3_WAVE_W, V3_WAVE_E)

# The client's cap, held separately from the figures that generate the curve
# and never read by them.  Checking the deep end against V3_WAVE_W would
# prove nothing - raise that and the curve rises with it.  This is the
# number the brief set, so the check has something fixed to fail against.
V3_WAVE_LIMIT = 2.00
V3_WAVE_BALUSTRADE = 0.12      # glass line, inboard of the slab edge
V3_WAVE_REVEAL = 0.40          # recessed reveal in the soffit, same curve
V3_WAVE_FASCIA = 0.15          # upstand band on the slab edge (elevation)


def wave_projection(x):
    """Projection of the south cantilever at plan x, metres from the wall."""
    x0, x1 = V3_WAVE_SPAN
    t = (x - x0) / (x1 - x0)
    return V3_WAVE_W + (V3_WAVE_E - V3_WAVE_W) * t * t


def wave_area():
    """Area under the curve: the projection integrated along the span."""
    return (V3_WAVE_W + (V3_WAVE_E - V3_WAVE_W) / 3.0) * (V3_X1 - V3_X0)


def wave_edge(x):
    """Plan y of the cantilever's slab edge at x."""
    return V3_Y0 - wave_projection(x)


def wave_points(n=72, offset=0.0):
    """The slab edge, or a curve parallel to it, as a list of (x, y).

    `offset` moves the curve inboard, which is how the balustrade, the
    soffit reveal and the fascia band are drawn from the same geometry.
    """
    x0, x1 = V3_WAVE_SPAN
    return [(x0 + (x1 - x0) * i / n, wave_edge(x0 + (x1 - x0) * i / n) + offset)
            for i in range(n + 1)]


# ---------------------------------------------------------------------------
# openings, revision P6 third floor
# ---------------------------------------------------------------------------
# East and north take ordinary windows: the neighbours on both sides are
# 3.00 m high, so neither looks into this floor.  The west takes ventilation
# openings only - louvred, for air and a little light, never a balcony.
# Every range clears the 300 mm columns on V3_GRID_X / V3_GRID_Y.
V3_WIN_S_LIV = [(13.00, 15.30), (15.60, 17.20)]    # living, to the balcony
V3_DOOR_BALC = (13.00, 15.30)   # of those, the sliding door onto it
V3_WIN_S_S1 = [(17.80, 19.60), (20.00, 21.60)]     # suite 1 bedroom
V3_WIN_E = [(4.20, 6.00), (6.40, 7.40),            # suite 1 bedroom
            (8.70, 9.20),                          # suite 1 ensuite
            (9.70, 10.70),                         # shared bath
            (11.40, 12.30),                        # suite 2 ensuite
            (13.00, 14.70)]                        # suite 2 bedroom
V3_WIN_N = [(13.10, 14.50), (14.90, 16.00),        # bedroom 3
            (16.40, 17.20),                        # head of the hall
            (18.00, 19.40), (19.90, 21.40)]        # suite 2 bedroom
V3_VENT_W = [(4.00, 4.80), (6.50, 7.30),           # living area
             (13.60, 14.40), (15.20, 16.00)]       # bedroom 3


# ---------------------------------------------------------------------------
# detached villa, second floor (revision P6) - the bedroom floor
# ---------------------------------------------------------------------------
# Two suites and two further bedrooms.  Same envelope, same spine, same column
# grid and - this is not negotiable - the SAME STAIR WELL as the third floor.
# A stair that does not stack is not a stair, so V3_STAIR fixes where the
# circulation sits and the rooms are planned around it rather than the other
# way round.
#
# That one fixed point drives the whole layout.  With the stair against the
# west wall in the middle of the plate, the south-east corner cannot be
# reached from the landing: the spine faces suite 1 along its whole southern
# length.  Hence the inner lobby - a small hall off the landing that serves
# suite 2 and the shared bath between them.  It is the price of stacking the
# stair, and it is cheaper than the alternatives.
V2_S1_BED_Y1 = 6.90            # suite 1: bedroom / ensuite + dressing
V2_S1_Y1 = 9.00                # suite 1 / landing
V2_S1_ENS_X1 = 15.00           # suite 1: ensuite | dressing
V2_LOBBY_X1 = 18.90            # lobby | suite 2's ensuite and the shared bath

# The east strip now stacks on the first floor's, line for line: the shared
# bath and the lobby are the sizes they are below (5.4 and 4.8 m2), which
# means suite 2's bedroom wall moves 1.30 m north to pick up the slack.  The
# two floors therefore share every wet-room divider and every east window,
# so the drainage drops straight and the east elevation has one set of
# openings rather than two.  These repeat V1_MBED_Y1 and V1_ENS_Y1 rather
# than aliasing them - the constants are defined further down the file - and
# checks.py fails the build if the two floors ever stop agreeing.
V2_S2_BED_Y1 = 8.60            # suite 2: bedroom / lobby + ensuite
V2_ENS2_Y1 = 10.30             # suite 2's ensuite / the shared bath

# doors, named for the wall they sit in
V2_DOOR_S1 = (15.60, 16.50)    # landing into suite 1's dressing
V2_DOOR_S1_BED = (15.60, 16.50)
V2_DOOR_S1_ENS = (7.40, 8.30)
V2_DOOR_LOBBY = (9.40, 10.30)  # landing into the lobby, through the spine
# both of these sit in suite 2's north wall, so the bedroom is entered
# straight off the lobby and its ensuite straight off the bedroom - no
# second lobby in between
V2_DOOR_S2 = (17.90, 18.70)    # lobby into suite 2's bedroom
V2_DOOR_S2_ENS = (20.20, 21.10)  # bedroom into its own ensuite
V2_DOOR_BATH = (10.90, 11.80)  # lobby into the shared bath
V2_DOOR_BED4 = (13.40, 14.30)  # spur into bedroom 4, through the spine

# The hall between bedrooms 3 and 4 is given to bedroom 3, which takes the
# whole north-west quarter - 18.8 m2 against 13.9.  Nothing is lost: the
# hall was a 1.04 m spur off the landing serving one door at each end, and
# both doors can be moved to walls that already face circulation.  Bedroom 3
# is now entered from the landing through its own south wall, and bedroom 4
# from the lobby, which already serves suite 2 and the shared bath.  The
# spine therefore carries one opening on this floor instead of two.
V2_DOOR_BED3 = (15.70, 16.60)        # landing into bedroom 3, south wall
V2_DOOR_BED4_LOBBY = (17.75, 18.55)  # lobby into bedroom 4, its south wall

# Both suites open onto the south cantilever - the same wave the first and
# third floors carry, so the three now stack and the elevation reads as one
# gesture repeated rather than a balcony missing from the middle storey.
# The lobby has no door to the landing: the spine is simply opened over its
# length, as on the first floor.  It cannot borrow the first floor's opening
# though - that one starts at 8.72, where this floor still has 280 mm of
# suite 1's dressing room, which would open the dressing room onto the
# lobby.  It starts at the landing instead, and still clears the columns at
# y 8.46 and 12.56.
V2_SPINE_OPEN = (9.12, 12.30)

V2_DOOR_BALC_1 = (13.00, 15.30)   # suite 1's bedroom onto it, sliding
V2_DOOR_BALC_2 = (17.80, 19.60)   # suite 2's bedroom onto it, sliding
V2_BALC_LEVEL = "+6.57"           # 30 mm below FFL, as on the other floors

# Openings.  The south and east ranges repeat the third floor's wherever a
# room allows it, so the two storeys line up in elevation; where they cannot,
# the elevations still have to be drawn and reconciled.
V2_WIN_S = [(13.00, 15.30), (15.60, 17.20),    # suite 1 bedroom
            (17.80, 19.60), (20.00, 21.60)]    # suite 2 bedroom
# the east range is the first floor's exactly, because the rooms behind it
# are now the same rooms at the same depths
V2_WIN_E = [(4.20, 6.00), (6.40, 7.20), (7.60, 8.20),   # suite 2 bedroom
            (8.80, 9.60),                               # suite 2 ensuite
            (10.60, 11.90),                             # shared bath
            (12.90, 14.70), (15.00, 16.40)]             # bedroom 4
V2_WIN_N = [(13.10, 14.50), (14.90, 16.00),    # bedroom 3
            (16.40, 17.20),                    # head of the spur
            (18.00, 19.40), (19.90, 21.40)]    # bedroom 4
V2_VENT_W = [(4.00, 4.80), (5.40, 6.20),       # suite 1 bedroom
             (7.60, 8.20),                     # suite 1 ensuite
             (13.60, 14.40), (15.20, 16.00)]   # bedroom 3


# ---------------------------------------------------------------------------
# detached villa, first floor (revision P6) - the living floor
# ---------------------------------------------------------------------------
# A living area and sleeping rooms.  The living area takes the south-west
# with the stair standing in it, exactly as on the third floor - same walls,
# same pantry, same opening onto the cantilever - so the west strip lines
# through from first to third.  The east strip follows the SECOND floor
# instead: master bedroom and ensuite over the south-east, lobby and shared
# bath behind them, a bedroom across the north.
#
# So the floor is not a copy of either neighbour, and every wet room and the
# pantry still sit directly over or under their counterparts.  Nearly all
# the constants it needs already exist: V3_PANT_* and V3_WIN_S_LIV from the
# third floor, V2_LOBBY_X1 and the suite-2 doors from the second.
V1_LIV_Y1 = 12.42              # north face of the open living space

# The east strip is the first floor's own, no longer borrowed wholesale from
# the second: the master bedroom's north wall moves 1.30 m north and the
# shared bath gives up the same depth, with the ensuite keeping its 1.58 m
# and simply shifting between them.  The lobby alongside loses 1.30 m of
# length as a consequence - it runs from the bedroom wall to bedroom 3's.
V1_MBED_Y1 = 8.60              # master bedroom / ensuite and lobby
V1_ENS_Y1 = 10.30              # master ensuite / shared bath
V1_DOOR_BATH = (10.90, 11.80)  # lobby into the shared bath
# The pantry here is open - a counter run against the spine, inside the
# living area, not the walled room the third floor has.  The spine is the
# only wall in reach with nothing in it: the south is glazed to the
# balcony, the west is louvred, and the television takes y 4.55-6.05.
V1_PANTRY = (16.71, 6.60, V3_SPINE_X0, 8.55)   # 0.60 deep, 1.95 long

# The lobby has no wall to the living area: the spine is opened between the
# columns at y 8.46 and y 12.56, so the two read as one space with the frame
# standing in it.  Over that length the spine stops being a wall and becomes
# a downstand beam between columns - the columns stay, the infill goes.  The
# opening starts clear of the column at 8.46 and of the pantry counter that
# backs onto the solid stretch below it.
V1_SPINE_OPEN = (8.72, 12.30)
V1_DOOR_BALC = (13.00, 15.30)  # living area onto the balcony, sliding
V1_DOOR_BALC_M = (17.80, 19.60)   # master bedroom onto it, sliding
V1_BALC_LEVEL = "+3.27"

V1_WIN_S = [(13.00, 15.30), (15.60, 17.20),    # living area
            (17.80, 19.60), (20.00, 21.60)]    # master bedroom
V1_WIN_E = [(4.20, 6.00), (6.40, 7.20), (7.60, 8.20),   # master bedroom
            (8.80, 9.60),                               # master ensuite
            (10.60, 11.90),                             # shared bath
            (12.90, 14.70), (15.00, 16.40)]             # bedroom 3
V1_WIN_N = [(13.10, 14.50), (14.90, 16.00),    # bedroom 2
            (16.40, 17.20),                    # head of the hall
            (18.00, 19.40), (19.90, 21.40)]    # bedroom 3
V1_VENT_W = [(4.00, 4.80), (6.50, 7.30),       # living area
             (13.60, 14.40), (15.20, 16.00)]   # bedroom 2


# ---------------------------------------------------------------------------
# detached villa, ground floor (revision P7) - arrival, hosting, guest suite
# ---------------------------------------------------------------------------
# The floor you receive people on.  The family living is upstairs, where the
# balconies are, so this one is given to arrival, eating and a guest suite
# for anyone who cannot manage the stair.
#
# The west strip repeats the first and third floors exactly: one open room
# from the south wall to the stair hall line, with the stair standing in it.
# Upstairs that room is the living area; here it is the reception hall, and
# the front door is in its south wall, under the cantilever - the balcony
# projects about 1.75 m at that point, so the entrance is covered without a
# porch being added to the elevation.
#
# The east strip takes dining and kitchen in the two south bands, adjacent
# to each other as they have to be, and the guest suite in the quiet
# north-east corner on the north and east windows.
V0_HALL_Y1 = V3_STAIR[3]       # reception hall / the service block

# The north-west was four small rooms - WC, laundry, lobby and store - and
# the lobby never reached the spine, so the guest bedroom's door opened off
# the store.  The lobby and the store are gone.  The services are one block
# against the west wall and the reception hall takes the rest, turning the
# corner behind the stair and running up to the north wall, so it is the
# hall the guest bedroom opens off and there is no circulation room at all.
V0_WC_X1 = 14.60               # the service block | the reception hall
V0_WC_Y1 = 14.30               # guest WC | laundry and store

V0_DIN_Y1 = 8.00               # dining / kitchen
V0_KIT_Y1 = 11.60              # kitchen / guest ensuite
V0_ENS_Y1 = 13.30              # guest ensuite / guest bedroom

V0_DOOR_ENTRY = (14.60, 15.70)    # the front door, in the south wall
V0_DOOR_WC = (12.70, 13.50)       # hall into the guest WC
V0_DOOR_LAUN = (14.90, 15.70)     # hall into the laundry and store
V0_DOOR_GUEST = (13.60, 14.50)    # hall into the guest bedroom, through
                                  # the spine
V0_DOOR_ENS = (18.60, 19.50)      # guest bedroom into its own ensuite

# Hall, dining and kitchen are one open sequence: the spine is cased open
# to both, and the kitchen's own wall to the dining is a 2.50 m opening
# rather than a door.  The columns at y 8.46 and 12.56 stand clear of all
# three and stay.
V0_OPEN_DIN = (4.60, 7.20)        # reception hall into the dining
V0_OPEN_KIT = (8.80, 10.40)       # reception hall into the kitchen
V0_OPEN_SERVE = (18.30, 20.80)    # kitchen into the dining

V0_LEVEL = "+0.00"

V0_WIN_S = [(12.95, 14.20), V0_DOOR_ENTRY, (15.95, 17.20),  # reception hall
            (17.80, 19.60), (20.00, 21.60)]                 # dining
V0_WIN_E = [(4.20, 6.00), (6.40, 7.60),        # dining
            (8.80, 10.00), (10.40, 11.40),     # kitchen
            (11.85, 12.35),                    # guest ensuite
            (13.60, 15.00), (15.30, 16.50)]    # guest bedroom
V0_WIN_N = [(13.10, 14.30),                    # laundry and store
            (14.90, 16.00),                    # lobby
            (16.40, 17.20),                    # store
            (18.00, 19.40), (19.90, 21.40)]    # guest bedroom
V0_VENT_W = [(4.50, 5.30), (6.50, 7.30),       # reception hall
             (13.00, 13.80),                   # guest WC
             (15.00, 15.80)]                   # laundry and store


# ---------------------------------------------------------------------------
# detached villa, penthouse (revision P11) - a flat between two terraces
# ---------------------------------------------------------------------------
# The CORRIDOR is the fixed thing here, and everything else is what is left
# once it has been taken.  The client asked for the north and south open
# areas to be joined from OUTSIDE the apartment, down the west side, at a
# minimum of 2.00 m clear - so that is set out first and the flat fits
# around it.
#
# It cannot pass west of the stair: the stair well is 2.00 m wide and hard
# against the west wall with 0.30 m to the parapet, and the half landing is
# at +11.55 against a floor at +13.20, so the well stays open and cannot be
# built over.  The corridor therefore runs EAST of the stair, from the
# stair's east edge to the flat's west wall.
#
# Where that west wall lands is a structural question, not a planning one.
# A 300 mm wall needs a beam under it, and the only line on this side of
# the roof with one is the column line at x 17.46 - the spine, which is a
# 300 mm wall on every floor below and has columns at y 3.65, 8.46, 12.56
# and 16.85.  Putting the flat's west wall anywhere between the stair and
# the spine would need a beam spanning the full 9.6 m depth with nothing to
# land on at either end.  So the wall goes on the spine, and the corridor
# comes out 2.51 m clear - wider than the 2.00 m asked for, because the
# 0.51 m left over is worth more as corridor than as a void behind a wall.
#
# What that costs: the stair strip plus a 2.51 m corridor take 4.81 m of
# the 9.50 m width, leaving the flat 4.09 m clear.  Two bedrooms cannot sit
# side by side in 4.09 m, and stacking them would need 12.06 m of the
# 13.50 m depth and leave 1.44 m for both terraces.  The second bedroom is
# what pays for the corridor, so this is a ONE-bedroom flat.
#
# The flat's long walls both swallow a column line: west on x 17.46, east
# on x 21.85, each taking the columns at y 8.46 and 12.56 inside the wall
# itself.  The short walls at y 5.85 and 15.19 sit on secondary beams cast
# in the roof slab, spanning the 4.39 m between those two lines - ordinary
# framing, not a transfer.
V4_CORR_X0 = V3_STAIR[2]               # 14.80, the stair's east edge
V4_CORR_X1 = V3_SPINE_X0               # 17.31; 2.51 m clear, min asked 2.00
V4_CORR_W = V4_CORR_X1 - V4_CORR_X0
V4_X0, V4_X1 = V3_SPINE_X0, V3_X1      # 17.31 .. 22.00, flush east
V4_Y0, V4_Y1 = 5.70, 15.34
v4_x0, v4_x1 = V4_X0 + WT, V4_X1 - WT  # 17.61 .. 21.70  (4.09 clear)
v4_y0, v4_y1 = V4_Y0 + WT, V4_Y1 - WT  #  6.00 .. 15.04  (9.04 clear)
V4_PLATE = (v4_x1 - v4_x0) * (v4_y1 - v4_y0)

V4_LIV_Y1 = 9.60               # living | the hall-and-bath band
V4_BATH_Y1 = 11.60             # the band | bedroom
V4_HALL_X1 = 18.71             # hall | bath; 1.10 m of hall

# Openings.  The two long walls carry the columns at y 8.46 and 12.56, so
# every opening in them clears y 8.31-8.61 and 12.41-12.71.
V4_DOOR_MAIN = (6.30, 7.10)    # the front door, off the corridor
V4_DOOR_HALL = (17.75, 18.65)  # living into the hall, cased
V4_DOOR_BATH = (10.55, 11.35)  # hall into the bath
V4_DOOR_BED = (17.80, 18.60)   # hall into the bedroom
V4_DOOR_TERR = (17.90, 19.70)  # living onto the south terrace, sliding
V4_DOOR_TERR_N = (17.70, 19.20)   # bedroom onto the north terrace, sliding

V4_LEVEL = "+13.20"
V4_TOP = 16.45

# The pergola runs over the corridor for its whole length, so the thing
# that joins the two terraces is also the thing that shades the walk
# between them, and the two open areas read as one place.
V4_PERGOLA = (V4_CORR_X0, V3_Y0, V4_CORR_X1, V3_Y1 - PARAPET)
# and a band off each slider, so the shade reaches onto both terraces and
# the three run as one structure: shade where you sit, open sky beyond
V4_PERGOLA_S = (V4_CORR_X1, V3_Y0, 19.80, V4_Y0)
V4_PERGOLA_N = (V4_CORR_X1, V4_Y1, 19.40, V3_Y1 - PARAPET)
V4_CANOPY = (V3_STAIR[0], V3_STAIR[1] - 0.30, V3_STAIR[2], V3_STAIR[3])
V4_PLANT = (V3_X0 + PARAPET, 15.34, 14.80, V3_Y1 - PARAPET)   # tanks, NW

# The flat's west wall faces our own roof - 2.51 m of corridor, then the
# terrace - not the boundary, so it takes ordinary windows.  The west rule
# in checks.py is about the building's own west wall at x 12.50, which up
# here is a parapet with nothing in it.
V4_WIN_W = [(7.60, 8.20),                      # living
            (12.90, 13.70), (14.00, 14.80)]    # bedroom
V4_WIN_S = [V4_DOOR_TERR, (20.20, 21.50)]      # living
V4_WIN_E = [(6.40, 7.80), (8.80, 9.40),        # living
            (9.80, 10.50),                     # bath
            (12.90, 14.20), (14.40, 15.00)]    # bedroom
V4_WIN_N = [V4_DOOR_TERR_N]                    # bedroom

# The open roof, measured inside the parapets, and split the way it reads:
# two terraces joined by the corridor that runs between them.
V4_ROOF_X0, V4_ROOF_X1 = V3_X0 + PARAPET, V3_X1 - PARAPET    # 12.75 .. 21.75
V4_ROOF_Y1 = V3_Y1 - PARAPET                                 # 16.75
V4_CORR_AREA = V4_CORR_W * (V4_ROOF_Y1 - V3_Y0)
V4_TERR_S = ((V4_ROOF_X1 - V4_ROOF_X0 - V4_CORR_W) * (V4_Y0 - V3_Y0)
             + (V4_CORR_X0 - V4_ROOF_X0) * (V3_STAIR[1] - V4_Y0)
             + wave_area())
V4_TERR_N = ((V4_ROOF_X1 - V4_CORR_X1) * (V4_ROOF_Y1 - V4_Y1)
             + (V4_CORR_X0 - V4_ROOF_X0) * (V4_Y1 - V3_STAIR[3]))


def area(x0, y0, x1, y1):
    return (x1 - x0) * (y1 - y0)
