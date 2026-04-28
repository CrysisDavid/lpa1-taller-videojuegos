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

        self.assertTrue(self.manager.check_victory())

    def test_check_victory_por_enemigos(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(True)]
        self.manager.world.camera.offset.x = 0.0

        self.assertTrue(self.manager.check_victory())

    def test_check_victory_falsa_si_faltan_objetivos(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(False)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X - 1.0

        self.assertFalse(self.manager.check_victory())


if __name__ == "__main__":
    unittest.main()
