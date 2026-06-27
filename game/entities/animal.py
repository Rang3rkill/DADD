"""A wandering farm animal.

Simple ambient AI: pick a random point inside the pen, walk toward it
slowly, then pick a new one once it arrives. Deliberately has no
collision with the player or anything else - chickens are flavor and
motion, not obstacles. If that ever needs to change (e.g. a "herd the
chickens" mechanic), this is a small enough class to revisit then.
"""

import random

import pygame

from game.config import COLOR_CHICKEN, COLOR_CHICKEN_COMB


class Chicken:
    def __init__(self, pen_bounds, speed):
        self.pen_bounds = pen_bounds
        self.speed = speed
        x_min, y_min, x_max, y_max = pen_bounds
        self.pos = pygame.Vector2(random.uniform(x_min, x_max), random.uniform(y_min, y_max))
        self.target = self._random_target()

    def _random_target(self):
        x_min, y_min, x_max, y_max = self.pen_bounds
        return pygame.Vector2(random.uniform(x_min, x_max), random.uniform(y_min, y_max))

    def update(self, dt_ms):
        to_target = self.target - self.pos
        if to_target.length() < 4:
            self.target = self._random_target()
            return
        step = to_target.normalize() * self.speed * (dt_ms / 1000)
        if step.length() >= to_target.length():
            self.pos = self.target
        else:
            self.pos += step

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.ellipse(surface, COLOR_CHICKEN, pygame.Rect(x - 10, y - 8, 20, 16))
        pygame.draw.circle(surface, COLOR_CHICKEN_COMB, (x + 8, y - 8), 3)
