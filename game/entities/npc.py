"""An NPC: a friendship meter plus dialogue that changes with it.

Each NPC's personality (name, position, color, dialogue lines, gift
reactions) is passed in rather than hardcoded here - see
game/npc_data.py for the actual character data. That's what makes
adding a second (or third) NPC a data change instead of a code change.

The friendship logic still lives directly on this class rather than a
separate "Relationship" class. Adding a second character didn't
require repeating any of that logic - only new *data* - which is
exactly the signal that this was the right level of abstraction and
didn't need to be split out further.
"""

import random

import pygame

from game.config import (
    COLOR_TEXT_CREAM,
    COLOR_UI_PANEL,
    RELATIONSHIP_GIFT_INCREASE,
    RELATIONSHIP_MAX,
    RELATIONSHIP_TALK_INCREASE,
)


class NPC:
    def __init__(self, name, pos, color, dialogue, gift_reactions, font):
        self.name = name
        self.pos = pygame.Vector2(pos)
        self.color = color
        self.dialogue = dialogue
        self.gift_reactions = gift_reactions
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
        return random.choice(self.dialogue[self.get_tier()])

    def receive_gift(self):
        self.friendship = min(RELATIONSHIP_MAX, self.friendship + RELATIONSHIP_GIFT_INCREASE)
        return self.gift_reactions[self.get_tier()]

    def draw(self, surface):
        body_rect = pygame.Rect(0, 0, 28, 40)
        body_rect.center = (int(self.pos.x), int(self.pos.y))
        pygame.draw.rect(surface, self.color, body_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_UI_PANEL, body_rect, width=2, border_radius=4)

        label = self.font.render(self.name, True, COLOR_TEXT_CREAM)
        surface.blit(label, label.get_rect(center=(int(self.pos.x), int(self.pos.y) - 32)))
