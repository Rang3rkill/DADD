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
INTERACTION_RADIUS = 50   # how close the player must be to interact

# Gate between the farm and the dock. Two positions because each side
# needs its own marker and its own "where do you land" spot - they're
# not the same point, they're a doorway on each side of an area break.
DOCK_GATE_POS = (905, 320)     # the gate, as seen from the farm
FARM_GATE_POS = (40, 320)      # the gate, as seen from the dock
DOCK_ENTRY_POS = (80, 320)     # where the player lands after entering the dock
FARM_ENTRY_POS = (860, 320)    # where the player lands after returning to the farm
DOCK_UNLOCK_COST = 15          # one-time gold cost to "build the path" to the dock

FISHING_SPOTS = [(300, 200), (500, 350), (700, 220)]

# NPC positions live in game/npc_data.py alongside their dialogue,
# since they're part of each character's data rather than generic
# world layout.

# --- Property: buildings, animals, and scenery ---
# This is the first content that blocks player movement - see
# World._collides_at. Positions below were chosen by hand to stay
# clear of the farm grid, shop, gates, and NPCs; if you move things
# around, re-run the smoke test in the README to make sure nothing
# critical got walled off by accident.
BARN_POS = (650, 220)
SHED_POS = (380, 580)

CHICKEN_PEN = (560, 280, 760, 380)  # x_min, y_min, x_max, y_max
NUM_CHICKENS = 3
CHICKEN_SPEED = 30  # pixels per second - slow, ambient wandering

NEST_POS = (650, 300)
NEST_RESPAWN_MS = 25000  # how long after collecting until another egg is ready

# Rocks and trees are purely environmental - they block movement but
# have nothing to say. The shed is the one obstacle with a message:
# it's deliberately unenterable for now. That's the "mystery" - a
# locked door with a hint of something behind it, not a mechanic that
# needs to be fully built out yet.
OBSTACLES = [
    {"kind": "tree", "pos": (450, 180)},
    {"kind": "tree", "pos": (450, 470)},
    {"kind": "rock", "pos": (550, 470)},
    {"kind": "rock", "pos": (700, 540)},
    {"kind": "barn", "pos": BARN_POS},
    {
        "kind": "shed",
        "pos": SHED_POS,
        "message": (
            "The shed door is bound shut with old rope and a rusted "
            "lock. Faint scratching sounds come from inside. "
            "Whatever it is, it's not ready to come out yet."
        ),
    },
]

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

# --- Fish ---
# Fish have no seeds or growth timer - they're caught, not grown - so
# they only need a name, sell price, and a color for the catch message
# / future drawing. See World._start_fishing for the minigame itself.
FISH = {
    "minnow": {"name": "Minnow", "sell_price": 6},
    "bass": {"name": "Bass", "sell_price": 20},
    "trout": {"name": "Trout", "sell_price": 28},
}

# Anything the player can sell at the Market - crops, fish, and animal
# goods (eggs) all together. Kept as one merged dict so shop/inventory
# code doesn't need to know or care which catalog a given item came
# from.
ANIMAL_GOODS = {
    "egg": {"name": "Egg", "sell_price": 10},
}
SELLABLES = {**CROPS, **FISH, **ANIMAL_GOODS}

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
COLOR_WATER = (70, 120, 160)
COLOR_FISHING_SPOT = (140, 190, 215)
COLOR_ROCK = (140, 140, 135)
COLOR_TREE_TRUNK = (101, 67, 33)
COLOR_TREE_CANOPY = (60, 110, 60)
COLOR_BARN = (150, 60, 50)
COLOR_BARN_ROOF = (90, 40, 35)
COLOR_BARN_TRIM = (235, 225, 210)
COLOR_SHED = (70, 60, 55)
COLOR_CHICKEN = (235, 225, 205)
COLOR_CHICKEN_COMB = (200, 60, 60)
COLOR_NEST = (160, 120, 70)
