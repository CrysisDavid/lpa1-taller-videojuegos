"""Tests unitarios para la entidad BossEnemy."""

import sys
import unittest
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.bossenemy import BossEnemy
from entities.enemy import Enemy
from entities.player import Player
from entities.proyectile import Proyectile
from stats.stats import Stats


class TestBossEnemy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.screen = pygame.Surface((800, 600))

    def test_bossenemy_inicializa_mas_grande_que_enemy(self) -> None:
        boss = BossEnemy(self.screen, Vector2D(300.0, 200.0), "Boss")

        self.assertEqual(boss.image, Enemy.DEFAULT_IMAGE)
        self.assertGreater(boss.radius, Enemy.DEFAULT_RADIUS)
        self.assertEqual(boss.phase, 1.0)

    def test_trigger_phase_change_actualiza_fase(self) -> None:
        boss = BossEnemy(self.screen, Vector2D(300.0, 200.0), "Boss")
        boss.health = boss.max_health * 0.2

        boss.trigger_phase_change()

        self.assertEqual(boss.phase, 3.0)
        self.assertIn("rage_shot", boss.special_attacks)

    def test_special_attack_crea_proyectil(self) -> None:
        boss = BossEnemy(self.screen, Vector2D(300.0, 200.0), "Boss")
        player = Player(
            self.screen,
            Vector2D(500.0, 200.0),
            "Hero",
            stats=Stats(max_health=100.0, damage=10.0, defense=5.0),
        )

        projectile = boss.special_attack(player, current_time=1.0)

        self.assertIsNotNone(projectile)
        self.assertIsInstance(projectile, Proyectile)

    def test_proyectil_del_boss_dana_al_player(self) -> None:
        boss = BossEnemy(self.screen, Vector2D(300.0, 200.0), "Boss")
        player = Player(
            self.screen,
            Vector2D(500.0, 200.0),
            "Hero",
            stats=Stats(max_health=100.0, damage=10.0, defense=5.0),
        )

        projectile = boss.special_attack(player, current_time=1.0)
        self.assertIsNotNone(projectile)

        projectile.position.x = player.position.x
        projectile.position.y = player.position.y
        damage = projectile.hit(player)

        self.assertGreater(damage, 0.0)
        self.assertLess(player.health, player.stats.max_health)


if __name__ == "__main__":
    unittest.main()