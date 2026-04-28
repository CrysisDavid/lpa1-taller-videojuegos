"""Tests básicos para GameManager."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from game_manager import GameManager


class DummyEnemy:
    """Representa un enemigo mínimo para validar victoria."""

    def __init__(self, is_defeated: bool) -> None:
        self.is_defeated = is_defeated


class FakeKeys:
    """Simula teclado para tests de movimiento."""

    def __init__(self, pressed: set[int]) -> None:
        self.pressed = pressed

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


class TestGameManager(unittest.TestCase):
    """Verifica inicialización, reinicio y victoria del GameManager."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.screen = pygame.Surface((1280, 720))

        image_patcher = patch(
            "game_manager.pygame.image.load",
            return_value=pygame.Surface((64, 64)),
        )
        enemies_patcher = patch(
            "game_manager.generate_enemies_from_image",
            return_value=[],
        )

        self.addCleanup(image_patcher.stop)
        self.addCleanup(enemies_patcher.stop)

        image_patcher.start()
        enemies_patcher.start()

        self.manager = GameManager(screen=self.screen)

    def test_init_configura_estado_base(self) -> None:
        self.assertTrue(self.manager.is_playing)
        self.assertFalse(self.manager.game_over)
        self.assertEqual(self.manager.player.name, "Hero")
        self.assertIs(self.manager.hud.player, self.manager.player)
        self.assertEqual(len(self.manager.store.items), 3)
        self.assertGreater(len(self.manager.world.platforms), 0)

    def test_start_game_reinicia_estado_transitorio(self) -> None:
        old_player = self.manager.player
        self.manager.projectiles.append(object())
        self.manager.messages.append(("temp", 1.0))
        self.manager.game_over = True
        self.manager.store_dialog_open = True
        self.manager.store_dialog_tab = "sell"
        self.manager.store_buy_index = 2
        self.manager.store_sell_index = 1
        self.manager.player.cash = 0

        self.manager.start_game(seed=99)

        self.assertIsNot(self.manager.player, old_player)
        self.assertIs(self.manager.hud.player, self.manager.player)
        self.assertEqual(self.manager.player.cash, 100)
        self.assertEqual(self.manager.projectiles, [])
        self.assertEqual(self.manager.messages, [])
        self.assertFalse(self.manager.game_over)
        self.assertFalse(self.manager.store_dialog_open)
        self.assertEqual(self.manager.store_dialog_tab, "buy")
        self.assertEqual(self.manager.store_buy_index, 0)
        self.assertEqual(self.manager.store_sell_index, 0)

    def test_check_victory_por_exploracion(self) -> None:
        self.manager.world.enemies = [DummyEnemy(False)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X
        self.manager.boss_enemy = DummyEnemy(True)

        self.assertTrue(self.manager.check_victory())

    def test_check_victory_por_enemigos(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(True)]
        self.manager.world.camera.offset.x = 0.0
        self.manager.boss_enemy = DummyEnemy(True)

        self.assertTrue(self.manager.check_victory())

    def test_check_victory_falsa_si_faltan_objetivos(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(False)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X - 1.0
        self.manager.boss_enemy = DummyEnemy(False)

        self.assertFalse(self.manager.check_victory())

    def test_check_victory_falsa_si_boss_sigue_vivo(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(True)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X
        self.manager.boss_enemy = DummyEnemy(False)

        self.assertFalse(self.manager.check_victory())

    def test_caida_al_vacio_activa_game_over(self) -> None:
        self.manager.player.position.y = (
            self.manager.SCREEN_HEIGHT + self.manager.VOID_Y_MARGIN + 300.0
        )
        self.manager.player_vy = 0.0
        self.manager.on_ground = False

        self.manager.update(0.016)

        self.assertTrue(self.manager.game_over)
        self.assertFalse(self.manager.player.is_active)

    def test_spawn_inicia_sobre_una_plataforma(self) -> None:
        player_bottom = self.manager.player.position.y + self.manager.player.radius
        support_margin = self.manager.player.radius * 0.4

        is_supported = any(
            abs(platform.y - player_bottom) < 1e-6
            and (platform.x - support_margin)
            <= self.manager.player.position.x
            <= (platform.x + platform.width + support_margin)
            for platform in self.manager.world.platforms
        )

        self.assertTrue(self.manager.on_ground)
        self.assertTrue(is_supported)

    def test_player_puede_moverse_en_aire(self) -> None:
        self.manager.on_ground = False
        self.manager.player_vy = -100.0
        start_x = self.manager.player.position.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.1)

        self.assertGreater(self.manager.player.position.x, start_x)

    def test_player_desacelera_sin_input(self) -> None:
        self.manager.on_ground = True
        self.manager.player_vx = self.manager.PLAYER_SPEED

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys(set())):
            self.manager.update(0.05)

        self.assertLess(self.manager.player_vx, self.manager.PLAYER_SPEED)

    def test_player_sale_del_borde_izquierdo_al_mover_derecha(self) -> None:
        left_world = self.manager.world.camera.offset.x + self.manager.player.radius
        self.manager.player.position.x = left_world
        start_screen_x = self.manager.player.position.x - self.manager.world.camera.offset.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.1)

        end_screen_x = self.manager.player.position.x - self.manager.world.camera.offset.x
        self.assertGreater(end_screen_x, start_screen_x)


if __name__ == "__main__":
    unittest.main()
