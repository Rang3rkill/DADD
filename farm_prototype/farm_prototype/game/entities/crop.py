"""A single planted crop.

Tracks growth stage over time and knows how to draw itself. Has no
knowledge of the farm grid or tiles - the World decides where to plant
it and what to do once it's grown. That separation is what makes it
easy to add a third or fourth crop type later without touching the
farm-tile logic at all.
"""

import pygame

from game.config import CROPS, TILE_SIZE


class Crop:
    def __init__(self, crop_id, center_pos, planted_at_ms):
        self.crop_id = crop_id
        self.center_pos = center_pos
        self.planted_at_ms = planted_at_ms
        self.data = CROPS[crop_id]
        self.stage = "sprout"  # "sprout" -> "growing" -> "grown"

    def is_grown(self):
        return self.stage == "grown"

    def update(self, now_ms):
        if self.is_grown():
            return
        elapsed = now_ms - self.planted_at_ms
        total = self.data["sprout_ms"] + self.data["grow_ms"]
        if elapsed >= total:
            self.stage = "grown"
        elif elapsed >= self.data["sprout_ms"]:
            self.stage = "growing"
        else:
            self.stage = "sprout"

    def _current_radius(self):
        max_radius = TILE_SIZE * 0.32
        if self.stage == "grown":
            return max_radius
        if self.stage == "sprout":
            return max_radius * 0.3

        # "growing" - smoothly scale up between sprout size and full size
        now_ms = pygame.time.get_ticks()
        elapsed_in_grow = (now_ms - self.planted_at_ms) - self.data["sprout_ms"]
        progress = min(max(elapsed_in_grow / self.data["grow_ms"], 0), 1)
        return max_radius * (0.3 + 0.7 * progress)

    def draw(self, surface):
        radius = int(self._current_radius())
        pygame.draw.circle(surface, self.data["color"], self.center_pos, radius)
        if self.is_grown():
            # A white outline signals "ready to harvest."
            pygame.draw.circle(surface, (255, 255, 255), self.center_pos, radius, width=2)
