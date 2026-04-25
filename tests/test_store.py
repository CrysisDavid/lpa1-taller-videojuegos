"""Tests unitarios para el sistema de Store."""

import sys
import unittest
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.player import Player
from inventory.item import Item
from inventory.store import Store


def make_player(cash: int = 100, capacity: int = 20) -> Player:
    screen = pygame.Surface((800, 600))
    return Player(screen, Vector2D(100.0, 300.0), "Tester", cash=cash)


class TestStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_buy_transfiere_item_y_descuenta_cash(self) -> None:
        item = Item("Espada", buy_price=60.0, sell_price=30.0)
        store = Store(position=Vector2D(0.0, 0.0), items=[item])
        player = make_player(cash=100)

        result = store.buy(item, player)

        self.assertTrue(result)
        self.assertEqual(player.cash, 40)
        self.assertIn(item, player.inventory.items)
        self.assertNotIn(item, store.items)

    def test_buy_falla_sin_dinero(self) -> None:
        item = Item("Armadura", buy_price=120.0)
        store = Store(position=Vector2D(0.0, 0.0), items=[item])
        player = make_player(cash=50)

        result = store.buy(item, player)

        self.assertFalse(result)
        self.assertEqual(player.cash, 50)
        self.assertNotIn(item, player.inventory.items)
        self.assertIn(item, store.items)

    def test_sell_transfiere_item_y_suma_cash(self) -> None:
        item = Item("Pocion", buy_price=25.0, sell_price=10.0)
        store = Store(position=Vector2D(0.0, 0.0))
        player = make_player(cash=5)
        player.inventory.add_item(item)

        result = store.sell(item, player)

        self.assertTrue(result)
        self.assertEqual(player.cash, 15)
        self.assertNotIn(item, player.inventory.items)
        self.assertIn(item, store.items)

    def test_restock_agrega_items_y_retorna_cantidad(self) -> None:
        store = Store(position=Vector2D(0.0, 0.0))
        items = [Item("i1"), Item("i2"), Item("i3")]

        added = store.restock(items)

        self.assertEqual(added, 3)
        self.assertEqual(len(store.items), 3)


if __name__ == "__main__":
    unittest.main()