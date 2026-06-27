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

    def test_items_track_crops_and_fish_the_same_way(self):
        # Inventory doesn't care whether an item is a crop or a fish -
        # both are just sellable goods to this class.
        inv = Inventory()
        inv.add_item("carrot", 2)
        inv.add_item("trout", 1)
        self.assertEqual(inv.item_count("carrot"), 2)
        self.assertEqual(inv.item_count("trout"), 1)
        self.assertTrue(inv.remove_item("trout", 1))
        self.assertEqual(inv.item_count("trout"), 0)


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

    def test_sell_item_requires_inventory(self):
        econ = Economy()
        inv = Inventory()

        self.assertFalse(econ.sell_item(inv, "carrot"))
        inv.add_item("carrot", 2)
        self.assertTrue(econ.sell_item(inv, "carrot", 2))
        self.assertEqual(inv.item_count("carrot"), 0)

    def test_sell_item_works_for_fish_too(self):
        econ = Economy()
        inv = Inventory()
        inv.add_item("trout", 1)
        starting_gold = econ.gold

        self.assertTrue(econ.sell_item(inv, "trout", 1))
        self.assertEqual(inv.item_count("trout"), 0)
        self.assertGreater(econ.gold, starting_gold)

    def test_cannot_buy_seeds_for_fish(self):
        # Fish aren't planted - there's no such thing as a "trout seed."
        econ = Economy()
        inv = Inventory()
        self.assertFalse(econ.buy_seed(inv, "trout"))


if __name__ == "__main__":
    unittest.main()
