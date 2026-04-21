"""Tests de integración: instancias reales de Enemy en World."""

import sys
import unittest
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from entities.enemy import Enemy
from world.world import World

SCREEN_W, SCREEN_H = 800, 600


class TestWorldEnemyIntegration(unittest.TestCase):
    """Verifica que World instancia y gestiona enemigos correctamente."""

    def setUp(self) -> None:
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (SCREEN_W, SCREEN_H), flags=pygame.NOFRAME
        )
        self.world: World = World(screen=self.screen)

    def tearDown(self) -> None:
        pygame.quit()

    def test_generate_crea_enemigos(self) -> None:
        """generate() produce instancias Enemy iguales a enemy_count."""
        self.world.generate(seed=42, enemy_count=5, collectible_count=0)
        self.assertEqual(len(self.world.enemies), 5)
        for enemy in self.world.enemies:
            self.assertIsInstance(enemy, Enemy)

    def test_enemigos_sobre_plataformas(self) -> None:
        """Cada Enemy está posicionado sobre una plataforma existente."""
        self.world.generate(seed=7, enemy_count=4, collectible_count=0)
        platform_ys = {p.y for p in self.world.platforms}
        for enemy in self.world.enemies:
            # El enemigo debe estar por encima (menor Y) de alguna plataforma
            expected_y = min(platform_ys) - self.world.PLATFORM_TOP_OFFSET
            self.assertLessEqual(enemy.y, self.world.GROUND_Y)

    def test_update_mueve_enemigos(self) -> None:
        """update() modifica la posición de los enemigos activos."""
        self.world.generate(seed=1, enemy_count=3, collectible_count=0)
        initial_xs = [e.x for e in self.world.enemies]
        self.world.update(delta_time=0.1)
        for i, enemy in enumerate(self.world.enemies):
            if not enemy.is_defeated:
                # El enemigo se mueve horizontalmente
                self.assertNotEqual(enemy.x, initial_xs[i])

    def test_sin_enemigos_con_count_cero(self) -> None:
        """generate() con enemy_count=0 produce lista vacía."""
        self.world.generate(seed=99, enemy_count=0, collectible_count=0)
        self.assertEqual(len(self.world.enemies), 0)

    def test_generate_reinicia_enemigos(self) -> None:
        """Llamar generate() dos veces reemplaza los enemigos anteriores."""
        self.world.generate(seed=10, enemy_count=4, collectible_count=0)
        self.world.generate(seed=20, enemy_count=2, collectible_count=0)
        self.assertEqual(len(self.world.enemies), 2)

    def test_draw_no_lanza_excepcion(self) -> None:
        """draw() con enemigos no debe lanzar ninguna excepción."""
        self.world.generate(seed=3, enemy_count=4, collectible_count=3)
        try:
            self.world.draw(surface=self.screen, camera_offset_x=0.0)
        except Exception as exc:
            self.fail(f"draw() lanzó una excepción inesperada: {exc}")


if __name__ == "__main__":
    unittest.main()
