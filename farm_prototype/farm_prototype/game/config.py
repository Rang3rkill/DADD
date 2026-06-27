"""All tunable numbers and layout positions for the game live here.

Change a value once, it updates everywhere it's used. This is the
first place to look when balancing the game (crop timings, prices,
movement speed) later on.
"""

# --- Window / timing ---
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60

# --- World layout ---
TILE_SIZE = 48
FARM_COLS = 6
FARM_ROWS = 5

FARM_ORIGIN = (40, 300)   # top-left corner of the farm grid, in world pixels
SHOP_POS = (860, 140)     # center of the market stall
NPC_POS = (140, 140)      # center of the NPC's standing spot
INTERACTION_RADIUS = 50   # how close the player must be to interact

# --- Player ---
PLAYER_SPEED = 160        # pixels per second
PLAYER_START = (480, 560)
PLAYER_SIZE = (28, 36)

# --- Crops ---
# Growth timing is in milliseconds. Each crop has two stages after
# planting: "sprout" then "growing" until it reaches "grown" (ready to
# harvest). Total time to harvest = sprout_ms + grow_ms.
CROPS = {
    "carrot": {
        "name": "Carrot",
        "sprout_ms": 4000,
        "grow_ms": 6000,
        "seed_cost": 5,
        "sell_price": 12,
        "color": (255, 140, 66),
    },
    "potato": {
        "name": "Potato",
        "sprout_ms": 6000,
        "grow_ms": 9000,
        "seed_cost": 8,
        "sell_price": 18,
        "color": (201, 123, 61),
    },
}

STARTING_GOLD = 30

# --- Relationship ---
RELATIONSHIP_GIFT_INCREASE = 8
RELATIONSHIP_TALK_INCREASE = 2
RELATIONSHIP_MAX = 100

# --- Color palette ---
# Deliberate warm farm tones instead of default UI blue/gray.
COLOR_SKY = (175, 219, 220)
COLOR_GRASS = (127, 176, 105)
COLOR_SOIL_DRY = (138, 106, 79)
COLOR_SOIL_TILLED = (92, 69, 48)
COLOR_UI_PANEL = (62, 44, 28)
COLOR_UI_PANEL_BORDER = (217, 165, 102)
COLOR_TEXT_CREAM = (244, 236, 216)
COLOR_GOLD_TEXT = (232, 184, 75)
COLOR_PLAYER = (217, 165, 102)
COLOR_NPC = (200, 120, 150)
