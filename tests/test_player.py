"""Tests unitarios para Player."""

import sys
import unittest
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.player import Player
from entities.proyectile import Proyectile
from inventory.item import Item
from inventory.store import Store
from stats.stats import Stats


SCREEN_W, SCREEN_H = 800, 600


def make_screen() -> pygame.Surface:
    pygame.init()
    return pygame.display.set_mode((SCREEN_W, SCREEN_H), flags=pygame.NOFRAME)


def make_player(screen: pygame.Surface, **kwargs) -> Player:
    return Player(screen, Vector2D(100.0, 400.0), "Hero", **kwargs)


class TestPlayerInit(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_atributos_por_defecto(self) -> None:
        p = make_player(self.screen)
        self.assertEqual(p.name, "Hero")
        self.assertEqual(p.cash, 0)
        self.assertEqual(p.health, p.stats.max_health)
        self.assertIsInstance(p.stats, Stats)

    def test_health_inicial_igual_a_max_health(self) -> None:
        s = Stats(max_health=150.0)
        p = make_player(self.screen, stats=s)
        self.assertEqual(p.health, 150.0)

    def test_name_vacio_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Player(self.screen, Vector2D(0, 0), "   ")

    def test_cash_negativo_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            make_player(self.screen, cash=-10)


class TestPlayerCombat(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_shoot_crea_proyectil(self) -> None:
        p = make_player(self.screen, stats=Stats(damage=20.0))
        projectile = p.shoot(Vector2D(1.0, 0.0), current_time=1.0)
        self.assertIsNotNone(projectile)
        self.assertIsInstance(projectile, Proyectile)

    def test_shoot_respeta_cadencia(self) -> None:
        p = make_player(self.screen)
        p.shot_cooldown = 0.5
        first = p.shoot(Vector2D(1.0, 0.0), current_time=1.0)
        second = p.shoot(Vector2D(1.0, 0.0), current_time=1.2)
        third = p.shoot(Vector2D(1.0, 0.0), current_time=1.6)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertIsNotNone(third)

    def test_shoot_tiempo_negativo_lanza_error(self) -> None:
        p = make_player(self.screen)
        with self.assertRaises(ValueError):
            p.shoot(Vector2D(1.0, 0.0), current_time=-0.1)

    def test_defend_reduce_health(self) -> None:
        p = make_player(self.screen, stats=Stats(defense=5.0))
        initial = p.health
        net = p.defend(15.0)
        self.assertEqual(net, 10.0)
        self.assertEqual(p.health, initial - 10.0)

    def test_defend_damage_menor_que_defensa(self) -> None:
        p = make_player(self.screen, stats=Stats(defense=10.0))
        initial = p.health
        net = p.defend(5.0)
        self.assertEqual(net, 0.0)
        self.assertEqual(p.health, initial)

    def test_defend_negativo_lanza_error(self) -> None:
        p = make_player(self.screen)
        with self.assertRaises(ValueError):
            p.defend(-1.0)


class TestPlayerInventory(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_buy_item_exitoso(self) -> None:
        p = make_player(self.screen, cash=100)
        item = Item("Espada", buy_price=50.0, sell_price=25.0)

        class FakeStore:
            items = [item]

        bought = p.buy_item(item, FakeStore())
        self.assertTrue(bought)
        self.assertEqual(p.cash, 50)
        self.assertIn(item, p.inventory.items)

    def test_buy_item_exitoso_con_store_real(self) -> None:
        p = make_player(self.screen, cash=90)
        item = Item("Arco", buy_price=40.0, sell_price=20.0)
        store = Store(position=Vector2D(0.0, 0.0), items=[item])

        bought = p.buy_item(item, store)

        self.assertTrue(bought)
        self.assertEqual(p.cash, 50)
        self.assertIn(item, p.inventory.items)
        self.assertNotIn(item, store.items)

    def test_buy_item_sin_dinero(self) -> None:
        p = make_player(self.screen, cash=10)
        item = Item("Espada", buy_price=50.0)
        bought = p.buy_item(item, object())
        self.assertFalse(bought)
        self.assertEqual(p.cash, 10)

    def test_sell_item_exitoso(self) -> None:
        p = make_player(self.screen)
        item = Item("Poción", sell_price=30.0)
        p.inventory.add_item(item)

        class FakeStore:
            items: list = []

        sold = p.sell_item(item, FakeStore())
        self.assertTrue(sold)
        self.assertEqual(p.cash, 30)
        self.assertNotIn(item, p.inventory.items)

    def test_sell_item_exitoso_con_store_real(self) -> None:
        p = make_player(self.screen)
        item = Item("Casco", buy_price=50.0, sell_price=15.0)
        p.inventory.add_item(item)
        store = Store(position=Vector2D(10.0, 10.0))

        sold = p.sell_item(item, store)

        self.assertTrue(sold)
        self.assertEqual(p.cash, 15)
        self.assertNotIn(item, p.inventory.items)
        self.assertIn(item, store.items)

    def test_sell_item_no_en_inventario(self) -> None:
        p = make_player(self.screen)
        item = Item("Poción", sell_price=30.0)
        sold = p.sell_item(item, object())
        self.assertFalse(sold)


class TestPlayerProgression(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_gain_experience_delega_a_stats(self) -> None:
        p = make_player(self.screen)
        p.gain_experience(50.0)
        self.assertEqual(p.stats.experience, 50.0)

    def test_level_up_restaura_salud(self) -> None:
        p = make_player(self.screen)
        p.health = 10.0
        p.level_up()
        self.assertEqual(p.health, p.stats.max_health)
        self.assertEqual(p.stats.level, 2)


class TestPlayerAnimationState(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_anim_state_run_con_velocidad_alta_en_suelo(self) -> None:
        p = make_player(self.screen)
        p.set_motion_state(vx=220.0, on_ground=True)

        p.update(0.05)

        self.assertEqual(p._anim_state, "run")

    def test_anim_state_hurt_tiene_prioridad(self) -> None:
        p = make_player(self.screen)
        p.set_motion_state(vx=220.0, on_ground=True)
        p.damage_effect_timer = 0.2

        p.update(0.01)

        self.assertEqual(p._anim_state, "hurt")


if __name__ == "__main__":
    unittest.main()
