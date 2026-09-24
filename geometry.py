#!/usr/bin/env python3
"""
geometry.py - the single source of truth for the building's set-out.

Derived from the site sketch.  Origin (0, 0) is the south-west corner of the
plot, x east, y north.  The street runs along the south boundary and the
entrance gate is at the west end of the garden corridor.

Plot boundary (anti-clockwise from the gate):
    (0,0) (23,0) (23,18) (18,18) (18,17.5) (11.5,17.5) (11.5,5) (0,5)

    garden corridor   23.00 x  5.00  = 115.00 m2
    block A (front)    6.50 x 12.50  =  81.25 m2
    block B (rear)     5.00 x 13.00  =  65.00 m2
    plot                             = 261.25 m2
"""

# ---------------------------------------------------------------------------
# site
# ---------------------------------------------------------------------------
PLOT_W = 23.00
GARDEN_D = 5.00
PLOT = [(0, 0), (23.00, 0), (23.00, 18.00), (18.00, 18.00), (18.00, 17.50),
        (11.50, 17.50), (11.50, 5.00), (0, 5.00)]

# ---------------------------------------------------------------------------
# building envelope (outside faces)
# ---------------------------------------------------------------------------
A_X0, A_X1 = 11.50, 18.00      # front block, 6.50 wide
A_Y0, A_Y1 = 5.00, 17.50       # 12.50 deep
B_X0, B_X1 = 18.00, 23.00      # rear block, 5.00 wide
B_Y0, B_Y1 = 5.00, 18.00       # 13.00 deep

WT = 0.30                      # external / party wall thickness
PT = 0.12                      # internal partition thickness
PARAPET = 0.25                 # terrace parapet thickness (1.10 m high)

# internal faces
a_x0, a_x1 = A_X0 + WT, 17.85          # 11.80 .. 17.85  (6.05 clear)
a_y0, a_y1 = A_Y0 + WT, A_Y1 - WT      #  5.30 .. 17.20  (11.90 clear)
b_x0, b_x1 = 18.15, B_X1 - WT          # 18.15 .. 22.70  (4.55 clear)
b_y0, b_y1 = B_Y0 + WT, B_Y1 - WT      #  5.30 .. 17.70  (12.40 clear)

PARTY_X0, PARTY_X1 = 17.85, 18.15      # wall shared by block A and block B

# ---------------------------------------------------------------------------
# vertical circulation and the light court - identical on every floor
# ---------------------------------------------------------------------------
ST_X0, ST_X1 = 15.20, 17.85            # stair enclosure, clear
ST_Y0, ST_Y1 = 10.60, 14.60            # 2.65 x 4.00
ST_WALL_X = 15.08                      # west wall of the stair enclosure

CT_X0, CT_X1 = 15.20, 17.85            # light court / void, clear
CT_Y0, CT_Y1 = 14.72, 17.20            # 2.65 x 2.48 = 6.6 m2, open to sky

# 3.00 m clear ceiling height is the client's minimum; the structural zone
# (slab plus floor build-up) adds 0.30 m, so floors are 3.30 m apart.
CLEAR_HEIGHT = 3.00
STRUCTURAL_ZONE = 0.30
FLOOR_TO_FLOOR = CLEAR_HEIGHT + STRUCTURAL_ZONE          # 3.30 m

# the ground floor sits 0.50 m above the garden, reached by three risers
GARDEN_LEVEL = -0.50
ENTRY_RISERS = 3

# levels
LEVELS = {0: "+0.00", 1: "+3.30", 2: "+6.60"}

# ---------------------------------------------------------------------------
# openings in the south (garden) elevation - x ranges
# ---------------------------------------------------------------------------
WIN_A_1 = (12.30, 13.70)       # living, arched
WIN_A_2 = (14.20, 15.30)       # living, arched
DOOR_ENTRY = (16.25, 17.35)    # main entrance
WIN_B_1 = (18.80, 20.20)       # TV lounge, arched glazed door
WIN_B_2 = (21.00, 22.30)       # TV lounge, arched

# window from block B onto the light court, through the party wall
CT_WIN_B = (15.00, 16.60)

# ---------------------------------------------------------------------------
# openings in the east boundary wall - y ranges
# ---------------------------------------------------------------------------
# The adjoining owner to the east is limited to 3.00 m in height, so that
# wall is free to open above first floor level and is used to cross
# ventilate block B.  It stays solid at ground floor, where a 3.00 m
# neighbouring building may be built against it.
WIN_E_MASTER = (8.60, 10.20)      # master bedroom, +3.00
WIN_E_ENSUITE = (14.40, 15.30)    # master ensuite, +3.00
WIN_E_LINEN = (16.65, 17.25)      # linen store, +3.00
WIN_E_SHOWER = (11.05, 11.75)     # studio shower room, +6.00
WIN_E_STUDIO_1 = (14.40, 15.50)   # studio suite, +6.00
WIN_E_STUDIO_2 = (16.00, 17.10)   # studio suite, +6.00


def area(x0, y0, x1, y1):
    return (x1 - x0) * (y1 - y0)
