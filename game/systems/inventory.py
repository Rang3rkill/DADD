"""Tracks seed and harvested-crop counts.

Deliberately has zero pygame dependencies - it's plain data and logic,
which is exactly why it's easy to unit test (see tests/test_systems.py)
without needing a display or game loop running.
"""


class Inventory:
    def __init__(self):
        self.seeds = {}   # e.g. {"carrot": 3}
        self.crops = {}   # e.g. {"carrot": 2}

    def add_seed(self, crop_id, amount=1):
        self.seeds[crop_id] = self.seeds.get(crop_id, 0) + amount

    def remove_seed(self, crop_id, amount=1):
        if not self.has_seed(crop_id, amount):
            return False
        self.seeds[crop_id] -= amount
        return True

    def has_seed(self, crop_id, amount=1):
        return self.seeds.get(crop_id, 0) >= amount

    def add_crop(self, crop_id, amount=1):
        self.crops[crop_id] = self.crops.get(crop_id, 0) + amount

    def remove_crop(self, crop_id, amount=1):
        if not self.has_crop(crop_id, amount):
            return False
        self.crops[crop_id] -= amount
        return True

    def has_crop(self, crop_id, amount=1):
        return self.crops.get(crop_id, 0) >= amount

    def seed_count(self, crop_id):
        return self.seeds.get(crop_id, 0)

    def crop_count(self, crop_id):
        return self.crops.get(crop_id, 0)
