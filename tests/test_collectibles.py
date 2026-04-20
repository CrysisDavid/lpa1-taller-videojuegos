"""Pruebas unitarias para entidades que heredan de Collectible."""

import math
import sys
from pathlib import Path
import unittest

import pygame

# Agregar el directorio raíz al path para importaciones absolutas.
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.collectible import Collectible
from entities.shield import Shield
from entities.trap import Trap
from entities.treasure import Treasure


class TestCollectibles(unittest.TestCase):
    """Valida herencia y mecánicas básicas de recolectables."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.screen: pygame.Surface = pygame.Surface((800, 600))

    def test_subclasses_inherit_collectible(self) -> None:
        shield = Shield(self.screen, 10.0, 10.0, duration=5.0)
        trap = Trap(
            self.screen,
            20.0,
            10.0,
            explosion_damage=30.0,
            explosion_range=50.0,
        )
        treasure = Treasure(
            self.screen,
            30.0,
            10.0,
            name="Moneda",
            monetary_value=100.0,
        )

        self.assertIsInstance(shield, Collectible)
        self.assertIsInstance(trap, Collectible)
        self.assertIsInstance(treasure, Collectible)

    def test_collectible_expires_by_lifetime(self) -> None:
        collectible = Collectible(
            self.screen,
            50.0,
            50.0,
            life_time=1.0,
            description="temporal",
        )

        collectible.update(0.4)
        self.assertTrue(collectible.is_active)
        self.assertAlmostEqual(collectible.remaining_life_time, 0.6, places=5)

        collectible.update(0.6)
        self.assertFalse(collectible.is_active)
        self.assertAlmostEqual(collectible.remaining_life_time, 0.0, places=5)

    def test_trap_explode_applies_damage_inside_range(self) -> None:
        trap = Trap(
            self.screen,
            100.0,
            100.0,
            explosion_damage=45.0,
            explosion_range=30.0,
        )
        target_position = Vector2D(120.0, 110.0)

        damage = trap.explode(target_position)

        self.assertEqual(damage, 45.0)
        self.assertTrue(trap.has_exploded)
        self.assertFalse(trap.is_active)

    def test_treasure_collect_value_marks_collected(self) -> None:
        treasure = Treasure(
            self.screen,
            200.0,
            300.0,
            name="Gema",
            monetary_value=250.0,
        )

        value = treasure.collect_value()

        self.assertEqual(value, 250.0)
        self.assertTrue(treasure.is_collected)
        self.assertFalse(treasure.is_active)

    def test_shield_activate_returns_effect_payload(self) -> None:
        shield = Shield(
            self.screen,
            300.0,
            100.0,
            duration=8.0,
            defense_boost=12.5,
        )

        payload = shield.activate()

        self.assertEqual(payload["duration"], 8.0)
        self.assertEqual(payload["defense_boost"], 12.5)
        self.assertTrue(shield.is_collected)
        self.assertFalse(shield.is_active)

    def test_collectible_default_lifetime_is_infinite(self) -> None:
        collectible = Collectible(self.screen, 10.0, 10.0)

        collectible.update(9999.0)

        self.assertTrue(collectible.is_active)
        self.assertTrue(math.isinf(collectible.remaining_life_time))


if __name__ == "__main__":
    unittest.main()
