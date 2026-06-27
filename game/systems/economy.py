"""Gold, buying seeds, and selling items.

Pure logic, no pygame dependency - same reasoning as Inventory. This
is the module to test first if you start tuning prices and want to
make sure you didn't break "can't buy what you can't afford."

sell_item works against SELLABLES (crops + fish merged) rather than
CROPS specifically, since both are sellable goods. buy_seed stays
CROPS-only on purpose - fish aren't planted, so they have no seeds.
"""

from game.config import CROPS, SELLABLES, STARTING_GOLD


class Economy:
    def __init__(self):
        self.gold = STARTING_GOLD

    def can_afford(self, amount):
        return self.gold >= amount

    def spend(self, amount):
        if not self.can_afford(amount):
            return False
        self.gold -= amount
        return True

    def earn(self, amount):
        self.gold += amount

    def buy_seed(self, inventory, crop_id):
        crop = CROPS.get(crop_id)
        if not crop:
            return False
        if not self.spend(crop["seed_cost"]):
            return False
        inventory.add_seed(crop_id)
        return True

    def sell_item(self, inventory, item_id, amount=1):
        data = SELLABLES.get(item_id)
        if not data:
            return False
        if not inventory.remove_item(item_id, amount):
            return False
        self.earn(data["sell_price"] * amount)
        return True
