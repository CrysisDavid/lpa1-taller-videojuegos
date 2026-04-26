"""Tests unitarios para ui.HUD."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pygame

from core.vector2d import Vector2D
from entities.player import Player
from inventory.item import Item
from stats.stats import Stats
from ui.hud import HUD

SCREEN_W, SCREEN_H = 800, 600


def make_screen() -> pygame.Surface:
    pygame.init()
    return pygame.display.set_mode((SCREEN_W, SCREEN_H))


def make_player(screen: pygame.Surface, name: str = "Hero", cash: int = 100) -> Player:
    return Player(screen, Vector2D(100.0, 400.0), name, cash=cash)


class TestHUDInit(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_crea_sin_error(self) -> None:
        player = make_player(self.screen)
        hud = HUD(screen=self.screen, player=player)
        self.assertIs(hud.player, player)
        self.assertIs(hud.screen, self.screen)

    def test_draw_no_lanza_excepcion(self) -> None:
        player = make_player(self.screen)
        hud = HUD(screen=self.screen, player=player)
        hud.draw()


class TestHUDBars(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_hp_ratio_completo(self) -> None:
        player = make_player(self.screen)
        player.health = player.stats.max_health
        ratio = player.health / player.stats.max_health
        self.assertAlmostEqual(ratio, 1.0)

    def test_hp_ratio_bajo_activa_color_critico(self) -> None:
        player = make_player(self.screen)
        player.health = player.stats.max_health * 0.2
        ratio = player.health / player.stats.max_health
        self.assertLessEqual(ratio, HUD.HP_LOW_THRESHOLD)

    def test_xp_ratio_cero_al_inicio(self) -> None:
        player = make_player(self.screen)
        ratio = player.stats.experience / player.stats.experience_threshold
        self.assertAlmostEqual(ratio, 0.0)

    def test_xp_ratio_tras_ganar_experiencia(self) -> None:
        player = make_player(self.screen)
        player.stats.experience = 50.0
        ratio = player.stats.experience / player.stats.experience_threshold
        self.assertGreater(ratio, 0.0)
        self.assertLess(ratio, 1.0)


class TestHUDInventario(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_draw_con_inventario_lleno_no_lanza(self) -> None:
        player = make_player(self.screen)
        for i in range(HUD.MAX_VISIBLE_SLOTS + 2):
            item = Item(name=f"Item{i}", buy_price=10.0, sell_price=5.0)
            player.inventory.add_item(item)
        hud = HUD(screen=self.screen, player=player)
        hud.draw()

    def test_draw_con_inventario_vacio_no_lanza(self) -> None:
        player = make_player(self.screen)
        hud = HUD(screen=self.screen, player=player)
        hud.draw()

    def test_max_visible_slots_es_positivo(self) -> None:
        self.assertGreater(HUD.MAX_VISIBLE_SLOTS, 0)


class TestHUDEscudo(unittest.TestCase):
    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_barra_escudo_con_shield_hp_no_lanza(self) -> None:
        player = make_player(self.screen)
        player.shield_hp = 50.0
        player.shield_max_hp = 50.0
        hud = HUD(screen=self.screen, player=player)
        hud.draw()

    def test_barra_escudo_sin_shield_hp_no_lanza(self) -> None:
        player = make_player(self.screen)
        player.shield_hp = 0.0
        player.shield_max_hp = 0.0
        hud = HUD(screen=self.screen, player=player)
        hud.draw()

    def test_shield_absorbe_dano_antes_que_hp(self) -> None:
        player = make_player(self.screen)
        player.shield_hp = 30.0
        player.shield_max_hp = 30.0
        hp_inicial = player.health
        player.defend(20.0)
        self.assertEqual(player.shield_hp, 10.0)
        self.assertEqual(player.health, hp_inicial)

    def test_dano_supera_escudo_reduce_hp(self) -> None:
        player = make_player(self.screen)
        player.shield_hp = 10.0
        player.shield_max_hp = 10.0
        player.stats.defense = 0.0
        hp_inicial = player.health
        player.defend(30.0)
        self.assertEqual(player.shield_hp, 0.0)
        self.assertLess(player.health, hp_inicial)

    def test_sin_escudo_dano_va_directo_a_hp(self) -> None:
        player = make_player(self.screen)
        player.shield_hp = 0.0
        player.stats.defense = 0.0
        hp_inicial = player.health
        player.defend(10.0)
        self.assertLess(player.health, hp_inicial)


if __name__ == "__main__":
    unittest.main()
