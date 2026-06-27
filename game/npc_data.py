"""Per-NPC content: name, position, color, and dialogue.

Kept separate from game/config.py on purpose. config.py is for numeric
tuning (crop timers, prices, speeds) - the kind of thing you tweak
while balancing the game. This file is narrative content - the kind
of thing you rewrite while writing characters. Different reasons to
edit, different files.

To add another NPC: add a new entry below with a name, position,
color, dialogue (one list of lines per friendship tier), and gift
reactions (one line per tier). Nothing in game/world.py or
game/entities/npc.py needs to change.
"""

NPC_PROFILES = {
    "maple": {
        "name": "Maple",
        "pos": (140, 140),
        "color": (200, 120, 150),
        "dialogue": {
            "stranger": [
                "Oh, hello. I don't think we've met properly.",
                "Nice weather for farming, I suppose.",
            ],
            "friendly": [
                "Good to see you again! How's the farm coming along?",
                "I always look forward to your visits.",
            ],
            "close": [
                "You've become one of my favorite people around here.",
                "Thanks for always thinking of me.",
            ],
        },
        "gift_reactions": {
            "stranger": "Oh... thank you, I guess?",
            "friendly": "Aw, that's so thoughtful of you!",
            "close": "You always know just what I like!",
        },
    },
    "felix": {
        "name": "Felix",
        "pos": (820, 460),
        "color": (110, 130, 140),
        "dialogue": {
            "stranger": [
                "...What do you want?",
                "I'm busy. Make it quick.",
            ],
            "friendly": [
                "Oh. It's you again. ...That's not a complaint.",
                "Crops are looking decent. Don't let it go to your head.",
            ],
            "close": [
                "Didn't expect to say this, but I look forward to seeing you.",
                "You're alright, you know that?",
            ],
        },
        "gift_reactions": {
            "stranger": "...Sure. Thanks, I guess.",
            "friendly": "Huh. Didn't expect that. ...Thanks.",
            "close": "You really do pay attention. Means a lot.",
        },
    },
}
