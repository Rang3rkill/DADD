"""Tracks seed counts and held items (anything you can sell: crops or
fish alike).

Deliberately has zero pygame dependencies - it's plain data and logic,
which is exactly why it's easy to unit test (see tests/test_systems.py)
without needing a display or game loop running.

Named generically ("item", not "crop") because it holds both harvested
crops and caught fish - they're both just sellable goods to this
class, which doesn't need to know or care which catalog they came
from.
"""


class Inventory:
    def __init__(self):
        self.seeds = {}   # e.g. {"carrot": 3}
        self.items = {}   # e.g. {"carrot": 2, "trout": 1}

    def add_seed(self, crop_id, amount=1):
        self.seeds[crop_id] = self.seeds.get(crop_id, 0) + amount

    def remove_seed(self, crop_id, amount=1):
        if not self.has_seed(crop_id, amount):
            return False
        self.seeds[crop_id] -= amount
        return True

    def has_seed(self, crop_id, amount=1):
        return self.seeds.get(crop_id, 0) >= amount

    def add_item(self, item_id, amount=1):
        self.items[item_id] = self.items.get(item_id, 0) + amount

    def remove_item(self, item_id, amount=1):
        if not self.has_item(item_id, amount):
            return False
        self.items[item_id] -= amount
        return True

    def has_item(self, item_id, amount=1):
        return self.items.get(item_id, 0) >= amount

    def seed_count(self, crop_id):
        return self.seeds.get(crop_id, 0)

    def item_count(self, item_id):
        return self.items.get(item_id, 0)
