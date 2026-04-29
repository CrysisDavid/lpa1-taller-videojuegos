"""Tests de integración: instancias reales de Enemy en World."""

import sys
import unittest
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from entities.enemy import Enemy
from combat.shield import Shield
from entities.trap import Trap
from entities.treasure import Treasure
from core.vector2d import Vector2D
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

    def test_scroll_regenera_enemigos_y_collectibles(self) -> None:
        """Al generar plataformas nuevas deben aparecer nuevos enemies y collectibles."""
        self.world.generate(seed=11, enemy_count=0, collectible_count=0)

        initial_platforms = len(self.world.platforms)
        initial_enemies = len(self.world.enemies)
        initial_collectibles = len(self.world.collectibles)

        screen_width = self.screen.get_width()
        furthest_x = max(platform.x for platform in self.world.platforms)
        self.world.camera.offset.x = (furthest_x - screen_width) + 1.0

        self.world.update(delta_time=0.0)

        self.assertGreater(len(self.world.platforms), initial_platforms)
        self.assertGreater(len(self.world.enemies), initial_enemies)
        self.assertGreater(len(self.world.collectibles), initial_collectibles)

    def test_collectible_regenerado_es_de_tipo_valido(self) -> None:
        """Los collectibles regenerados deben ser Shield, Trap o Treasure."""
        self.world.generate(seed=21, enemy_count=0, collectible_count=0)

        screen_width = self.screen.get_width()
        furthest_x = max(platform.x for platform in self.world.platforms)
        self.world.camera.offset.x = (furthest_x - screen_width) + 1.0

        self.world.update(delta_time=0.0)

        self.assertGreater(len(self.world.collectibles), 0)
        self.assertIsInstance(self.world.collectibles[-1], (Shield, Trap, Treasure))

    def test_generate_reinicia_camara_y_spawn_points(self) -> None:
        """generate() debe resetear cámara y limpiar spawn points acumulados."""
        self.world.generate(seed=1, enemy_count=2, collectible_count=2)

        # Simula avance para crear nuevas plataformas y spawns dinámicos
        screen_width = self.screen.get_width()
        furthest_x = max(platform.x for platform in self.world.platforms)
        self.world.camera.offset.x = (furthest_x - screen_width) + 1.0
        self.world.update(delta_time=0.0)

        # Vuelve a regenerar y valida reset total
        self.world.generate(seed=2, enemy_count=2, collectible_count=2)
        self.assertEqual(self.world.camera.offset.x, 0.0)
        self.assertEqual(len(self.world.enemy_spawn_points), 2)
        self.assertEqual(len(self.world.collectible_spawn_points), 2)

        # Con cámara reseteada deben existir elementos visibles en pantalla
        visible_enemies = [
            e for e in self.world.enemies if -50 <= (e.x - self.world.camera.offset.x) <= SCREEN_W + 50
        ]
        visible_collectibles = [
            c
            for c in self.world.collectibles
            if c.is_active and -50 <= (c.x - self.world.camera.offset.x) <= SCREEN_W + 50
        ]
        self.assertGreater(len(visible_enemies), 0)
        self.assertGreater(len(visible_collectibles), 0)

    def test_update_desactiva_enemy_detras_de_camara(self) -> None:
        self.world.generate(seed=5, enemy_count=1, collectible_count=0)
        enemy = self.world.enemies[0]
        enemy.position = Vector2D(50.0, enemy.position.y)
        self.world.camera.offset.x = 600.0

        self.world.update(delta_time=0.0)

        self.assertTrue(enemy.is_defeated)

    def test_update_desactiva_collectible_detras_de_camara(self) -> None:
        self.world.generate(seed=6, enemy_count=0, collectible_count=1)
        collectible = self.world.collectibles[0]
        collectible.position = Vector2D(40.0, collectible.position.y)
        self.world.camera.offset.x = 600.0

        self.world.update(delta_time=0.0)

        self.assertFalse(collectible.is_active)


if __name__ == "__main__":
    unittest.main()
