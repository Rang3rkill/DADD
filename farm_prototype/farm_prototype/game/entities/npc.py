"""The NPC: a friendship meter plus a few lines of dialogue per tier.

Deliberately small for this prototype - one character, three tiers -
but it's the seed of a bigger relationship system later. The
friendship logic lives directly on NPC rather than in a separate
"Relationship" class because there's only one NPC right now; if you
add more characters later and find yourself repeating this logic,
that's the point where pulling it out into its own system earns its
keep. Not before.
"""

import random

import pygame

from game.config import (
    COLOR_NPC,
    COLOR_TEXT_CREAM,
    COLOR_UI_PANEL,
    RELATIONSHIP_GIFT_INCREASE,
    RELATIONSHIP_MAX,
    RELATIONSHIP_TALK_INCREASE,
)

DIALOGUE = {
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
}

GIFT_REACTIONS = {
    "stranger": "Oh... thank you, I guess?",
    "friendly": "Aw, that's so thoughtful of you!",
    "close": "You always know just what I like!",
}


class NPC:
    def __init__(self, name, pos, font):
        self.name = name
        self.pos = pygame.Vector2(pos)
        self.font = font
        self.friendship = 0

    def get_tier(self):
        if self.friendship >= 60:
            return "close"
        if self.friendship >= 25:
            return "friendly"
        return "stranger"

    def talk(self):
        self.friendship = min(RELATIONSHIP_MAX, self.friendship + RELATIONSHIP_TALK_INCREASE)
        return random.choice(DIALOGUE[self.get_tier()])

    def receive_gift(self):
        self.friendship = min(RELATIONSHIP_MAX, self.friendship + RELATIONSHIP_GIFT_INCREASE)
        return GIFT_REACTIONS[self.get_tier()]

    def draw(self, surface):
        body_rect = pygame.Rect(0, 0, 28, 40)
        body_rect.center = (int(self.pos.x), int(self.pos.y))
        pygame.draw.rect(surface, COLOR_NPC, body_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_UI_PANEL, body_rect, width=2, border_radius=4)

        label = self.font.render(self.name, True, COLOR_TEXT_CREAM)
        surface.blit(label, label.get_rect(center=(int(self.pos.x), int(self.pos.y) - 32)))
