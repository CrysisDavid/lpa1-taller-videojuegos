"""Pruebas automatizadas para el feature de World."""

import sys
from pathlib import Path
import unittest

import pygame

# Agregar el directorio raíz al path para importaciones absolutas.
sys.path.insert(0, str(Path(__file__).parent.parent))

from world.world import World


class TestWorldFeature(unittest.TestCase):
    """Valida la generación del mundo sin romper mecánicas existentes."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.screen: pygame.Surface = pygame.Surface((800, 600))
        self.world: World = World(screen=self.screen)

    def test_update_keeps_scroll_and_infinite_platform_generation(self) -> None:
        """Debe mantener el scroll de cámara y generar plataformas distantes."""
        initial_platform_count: int = len(self.world.platforms)
        initial_offset_x: float = self.world.camera.offset.x

        # Fuerza avance grande para acercarse al límite y disparar generación.
        self.world.update(delta_time=5.0)

        self.assertGreater(self.world.camera.offset.x, initial_offset_x)
        self.assertGreater(len(self.world.platforms), initial_platform_count)

    def test_generate_populates_enemy_and_collectible_spawn_points(self) -> None:
        """La generación debe poblar spawns de enemigos y recolectables."""
        self.world.generate(seed=123, enemy_count=4, collectible_count=7)

        self.assertEqual(len(self.world.enemy_spawn_points), 4)
        self.assertEqual(len(self.world.collectible_spawn_points), 7)

        # Todos los puntos deben quedar por encima de alguna plataforma.
        for point in (
            self.world.enemy_spawn_points + self.world.collectible_spawn_points
        ):
            matching_platform_count: int = sum(
                1
                for platform in self.world.platforms
                if platform.x <= point.x <= platform.x + platform.width
                and abs((platform.y - self.world.PLATFORM_TOP_OFFSET) - point.y)
                < 0.0001
            )
            self.assertGreater(
                matching_platform_count,
                0,
                "Se encontró un punto fuera de plataforma.",
            )

    def test_place_methods_are_deterministic_with_seeded_rng(self) -> None:
        """Con semilla fija, la distribución debe ser reproducible."""
        self.world.generate(seed=999, enemy_count=3, collectible_count=3)
        first_enemy_points: list[tuple[float, float]] = [
            (point.x, point.y) for point in self.world.enemy_spawn_points
        ]
        first_collectible_points: list[tuple[float, float]] = [
            (point.x, point.y)
            for point in self.world.collectible_spawn_points
        ]

        self.world.generate(seed=999, enemy_count=3, collectible_count=3)
        second_enemy_points: list[tuple[float, float]] = [
            (point.x, point.y) for point in self.world.enemy_spawn_points
        ]
        second_collectible_points: list[tuple[float, float]] = [
            (point.x, point.y)
            for point in self.world.collectible_spawn_points
        ]

        self.assertEqual(first_enemy_points, second_enemy_points)
        self.assertEqual(first_collectible_points, second_collectible_points)


if __name__ == "__main__":
    unittest.main()
