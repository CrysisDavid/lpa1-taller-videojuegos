"""Pruebas unitarias para la entidad Enemy."""

import sys
from pathlib import Path
import unittest

import pygame

# Agregar el directorio raíz al path para importaciones absolutas.
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.enemy import Enemy


class DummyPlayer:
    def __init__(self, health: float = 100.0, defense: float = 0.0) -> None:
        self.health = health
        self.defense = defense


class TestEnemy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.screen: pygame.Surface = pygame.Surface((800, 600))

    def test_enemy_initialization(self) -> None:
        enemy = Enemy(
            screen=self.screen,
            world_pos=Vector2D(200.0, 150.0),
            name="Goblin",
            enemy_type="terrestre",
        )

        self.assertEqual(enemy.name, "Goblin")
        self.assertEqual(enemy.type, "terrestre")
        self.assertTrue(enemy.is_active)

    def test_take_damage_uses_defense(self) -> None:
        enemy = Enemy(
            screen=self.screen,
            world_pos=Vector2D(100.0, 100.0),
            name="Orco",
            defense=5.0,
            health=30.0,
        )

        net_damage = enemy.take_damage(12.0)

        self.assertEqual(net_damage, 7.0)
        self.assertEqual(enemy.health, 23.0)

    def test_enemy_attack_reduces_player_health(self) -> None:
        enemy = Enemy(
            screen=self.screen,
            world_pos=Vector2D(100.0, 100.0),
            name="Murcielago",
            attack_power=20.0,
        )
        player = DummyPlayer(health=50.0, defense=3.0)

        damage = enemy.attack(player)

        self.assertEqual(damage, 17.0)
        self.assertEqual(player.health, 33.0)

    def test_enemy_update_moves_left(self) -> None:
        enemy = Enemy(
            screen=self.screen,
            world_pos=Vector2D(400.0, 200.0),
            name="Lobo",
            velocity=100.0,
        )

        initial_x = enemy.x
        enemy.update(0.5)

        self.assertLess(enemy.x, initial_x)


if __name__ == "__main__":
    unittest.main()
