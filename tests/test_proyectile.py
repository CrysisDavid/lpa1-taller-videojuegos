"""Tests unitarios para Proyectile."""

import sys
import unittest
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.proyectile import Proyectile
from stats.stats import Stats

SCREEN_W, SCREEN_H = 800, 600


def make_proyectile(screen: pygame.Surface, **kwargs) -> Proyectile:
    stats = kwargs.pop("stats", Stats(damage=20.0))
    return Proyectile(
        screen, 100.0, 300.0, Vector2D(1.0, 0.0), stats=stats, **kwargs
    )


class TestProyectileInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags=pygame.NOFRAME)

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_atributos_iniciales(self) -> None:
        p = make_proyectile(self.screen)
        self.assertTrue(p.is_active)
        self.assertEqual(p.remaining_life_time, 2.0)

    def test_direction_normalizada(self) -> None:
        p = Proyectile(
            self.screen, 0.0, 0.0, Vector2D(3.0, 4.0),
            stats=Stats(damage=10.0)
        )
        mag = (p.direction.x ** 2 + p.direction.y ** 2) ** 0.5
        self.assertAlmostEqual(mag, 1.0, places=5)

    def test_velocity_cero_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Proyectile(self.screen, 0.0, 0.0, Vector2D(1.0, 0.0),
                       stats=Stats(), velocity=0.0)

    def test_direction_cero_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Proyectile(self.screen, 0.0, 0.0, Vector2D(0.0, 0.0),
                       stats=Stats())

    def test_life_time_cero_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Proyectile(self.screen, 0.0, 0.0, Vector2D(1.0, 0.0),
                       stats=Stats(), life_time=0.0)


class TestProyectileUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags=pygame.NOFRAME)

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_update_mueve_proyectil(self) -> None:
        p = make_proyectile(self.screen, velocity=200.0)
        initial_x = p.position.x
        p.update(0.1)
        self.assertGreater(p.position.x, initial_x)

    def test_update_expira_por_life_time(self) -> None:
        p = make_proyectile(self.screen, life_time=0.5)
        p.update(0.6)
        self.assertFalse(p.is_active)

    def test_remaining_life_time_decrece(self) -> None:
        p = make_proyectile(self.screen, life_time=2.0)
        p.update(0.5)
        self.assertAlmostEqual(p.remaining_life_time, 1.5, places=5)

    def test_update_dt_negativo_lanza_error(self) -> None:
        p = make_proyectile(self.screen)
        with self.assertRaises(ValueError):
            p.update(-0.1)


class TestProyectileHit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags=pygame.NOFRAME)

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _make_enemy(self, health: float = 100.0, defense: float = 0.0):
        class FakeEnemy:
            def __init__(self):
                self.health = health
                self.defense = defense
                self.is_active = True
                self.position = Vector2D(100.0, 300.0)  # mismo lugar que el proyectil
                self.radius = 20

            def colission(self, other):
                return True  # siempre colisiona en tests

            def take_damage(self, d: float) -> float:
                net = max(0.0, d - self.defense)
                self.health = max(0.0, self.health - net)
                return net

        return FakeEnemy()

    def test_hit_usa_stats_damage(self) -> None:
        stats = Stats(damage=25.0)
        p = make_proyectile(self.screen, stats=stats)
        enemy = self._make_enemy(health=100.0, defense=0.0)
        net = p.hit(enemy)
        self.assertEqual(net, 25.0)
        self.assertEqual(enemy.health, 75.0)

    def test_hit_level_up_aumenta_danio(self) -> None:
        stats = Stats(damage=10.0)
        stats.level_up()  # damage += 5 → 15
        p = make_proyectile(self.screen, stats=stats)
        enemy = self._make_enemy(health=100.0, defense=0.0)
        net = p.hit(enemy)
        self.assertEqual(net, 15.0)

    def test_hit_desactiva_proyectil(self) -> None:
        p = make_proyectile(self.screen)
        enemy = self._make_enemy()
        p.hit(enemy)
        self.assertFalse(p.is_active)

    def test_hit_inactivo_no_hace_danio(self) -> None:
        p = make_proyectile(self.screen)
        p.is_active = False
        enemy = self._make_enemy()
        net = p.hit(enemy)
        self.assertEqual(net, 0.0)
        self.assertEqual(enemy.health, 100.0)

    def test_hit_enemigo_inactivo_no_hace_danio(self) -> None:
        p = make_proyectile(self.screen)
        enemy = self._make_enemy()
        enemy.is_active = False
        net = p.hit(enemy)
        self.assertEqual(net, 0.0)


if __name__ == "__main__":
    unittest.main()
