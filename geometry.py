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


def area(x0, y0, x1, y1):
    return (x1 - x0) * (y1 - y0)
