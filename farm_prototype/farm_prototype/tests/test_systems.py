"""A few smoke tests for the pure-logic systems (Inventory, Economy).

These don't need pygame at all, which is exactly why they're easy to
test - the rendering and input code is deliberately kept separate from
this kind of game-rule logic. This is intentionally small: just enough
to catch a broken buy/sell rule before it ships, not a full test suite
for a weekend prototype.

Run with:
    python -m unittest discover -s tests -t .
"""

import unittest

from game.systems.economy import Economy
from game.systems.inventory import Inventory


class TestInventory(unittest.TestCase):
    def test_add_and_remove_seed(self):
        inv = Inventory()
        inv.add_seed("carrot", 3)
        self.assertEqual(inv.seed_count("carrot"), 3)
        self.assertTrue(inv.remove_seed("carrot", 2))
        self.assertEqual(inv.seed_count("carrot"), 1)

    def test_cannot_remove_more_than_available(self):
        inv = Inventory()
        inv.add_seed("carrot", 1)
        self.assertFalse(inv.remove_seed("carrot", 2))
        self.assertEqual(inv.seed_count("carrot"), 1)


class TestEconomy(unittest.TestCase):
    def test_buy_seed_spends_gold_and_adds_seed(self):
        econ = Economy()
        inv = Inventory()
        starting_gold = econ.gold

        self.assertTrue(econ.buy_seed(inv, "carrot"))
        self.assertEqual(inv.seed_count("carrot"), 1)
        self.assertLess(econ.gold, starting_gold)

    def test_cannot_buy_without_enough_gold(self):
        econ = Economy()
        econ.gold = 0
        inv = Inventory()

        self.assertFalse(econ.buy_seed(inv, "carrot"))
        self.assertEqual(inv.seed_count("carrot"), 0)

    def test_sell_crop_requires_inventory(self):
        econ = Economy()
        inv = Inventory()

        self.assertFalse(econ.sell_crop(inv, "carrot"))
        inv.add_crop("carrot", 2)
        self.assertTrue(econ.sell_crop(inv, "carrot", 2))
        self.assertEqual(inv.crop_count("carrot"), 0)


if __name__ == "__main__":
    unittest.main()
