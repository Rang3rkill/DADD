"""Static, collidable scenery: rocks, trees, and buildings.

Obstacles are the first thing in this prototype that block player
movement - see World._collides_at. Most are pure environment with
nothing to say. The shed is the exception: it carries a one-off
flavor-text message instead of a real mechanic. That's the cheapest
way to plant a narrative hook ("what's making that noise?") without
committing to building the system behind it yet - when you're ready
to actually build what's in the shed, that message is the place to
start.
"""

import pygame

from game.config import (
    COLOR_BARN,
    COLOR_BARN_ROOF,
    COLOR_BARN_TRIM,
    COLOR_ROCK,
    COLOR_SHED,
    COLOR_TREE_CANOPY,
    COLOR_TREE_TRUNK,
)

# The collision box for each kind is deliberately smaller than the
# shape actually drawn (see draw() below). That gives the player a
# little breathing room to stand close enough to read a shed's message
# without the hitbox and the sprite edge feeling like the exact same
# line - and it means INTERACTION_RADIUS can comfortably reach the
# object's center even when standing right against it.
_COLLISION_SIZES = {
    "rock": (32, 28),
    "tree": (30, 36),
    "barn": (100, 70),
    "shed": (56, 44),
}


class Obstacle:
    def __init__(self, kind, pos, message=None):
        self.kind = kind
        self.pos = pygame.Vector2(pos)
        self.message = message
        self.rect = self._build_rect()

    def _build_rect(self):
        width, height = _COLLISION_SIZES.get(self.kind, (32, 32))
        rect = pygame.Rect(0, 0, width, height)
        rect.center = self.pos
        return rect

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        if self.kind == "rock":
            pygame.draw.circle(surface, COLOR_ROCK, (x, y), 18)
            pygame.draw.circle(surface, (0, 0, 0), (x, y), 18, width=2)
        elif self.kind == "tree":
            trunk = pygame.Rect(0, 0, 10, 22)
            trunk.center = (x, y + 14)
            pygame.draw.rect(surface, COLOR_TREE_TRUNK, trunk)
            pygame.draw.circle(surface, COLOR_TREE_CANOPY, (x, y - 6), 22)
        elif self.kind == "barn":
            body = pygame.Rect(0, 0, 100, 60)
            body.center = (x, y + 10)
            pygame.draw.rect(surface, COLOR_BARN, body)
            pygame.draw.rect(surface, COLOR_BARN_TRIM, body, width=3)
            roof = [(x - 60, y - 20), (x + 60, y - 20), (x, y - 55)]
            pygame.draw.polygon(surface, COLOR_BARN_ROOF, roof)
        elif self.kind == "shed":
            body = pygame.Rect(0, 0, 56, 44)
            body.center = (x, y)
            pygame.draw.rect(surface, COLOR_SHED, body)
            pygame.draw.rect(surface, COLOR_BARN_TRIM, body, width=2)
