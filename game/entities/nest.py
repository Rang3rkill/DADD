"""A nest the player can collect an egg from periodically.

Same "wait, then it's ready" idea as a growing crop, just simpler -
one resource, no planting step. Kept as its own small class rather
than folded into World for the same reason Crop is its own class: the
timer logic is easy to read - and easy to test - in isolation from
drawing and input.
"""

import pygame

from game.config import COLOR_GOLD_TEXT, COLOR_NEST, NEST_RESPAWN_MS


class Nest:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.ready_at = 0  # ready immediately at the start of a new game

    def is_ready(self, now_ms):
        return now_ms >= self.ready_at

    def collect(self, now_ms):
        self.ready_at = now_ms + NEST_RESPAWN_MS

    def draw(self, surface, now_ms):
        rect = pygame.Rect(0, 0, 30, 20)
        rect.center = (int(self.pos.x), int(self.pos.y))
        pygame.draw.ellipse(surface, COLOR_NEST, rect)
        if self.is_ready(now_ms):
            pygame.draw.ellipse(surface, COLOR_GOLD_TEXT, rect, width=2)
