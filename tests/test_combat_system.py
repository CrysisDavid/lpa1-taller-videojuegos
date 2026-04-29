"""Tests unitarios para el sistema de combate."""

import unittest
import pygame
from unittest.mock import Mock, MagicMock

from combat.combat_system import CombatSystem
from core.vector2d import Vector2D
from core.sprite import Sprite
from stats.stats import Stats


class MockSprite(Sprite):
    """Mock de Sprite para testing."""
    def __init__(self, screen: pygame.Surface, x: float = 0.0, y: float = 0.0):
        super().__init__(screen, x, y, (255, 255, 255), 20)


def make_screen() -> pygame.Surface:
    """Crea una pantalla de prueba."""
    pygame.init()
    return pygame.display.set_mode((800, 600))


class TestCombatSystemCalculateDamage(unittest.TestCase):
    """Tests para el cálculo de daño."""

    def test_calculate_damage_basico(self) -> None:
        """El daño neto es ataque - defensa."""
        damage = CombatSystem.calculate_damage(100.0, 30.0)
        self.assertEqual(damage, 70.0)

    def test_calculate_damage_defensa_mayor_ataque(self) -> None:
        """Si defensa >= ataque, el daño es 0."""
        damage = CombatSystem.calculate_damage(30.0, 100.0)
        self.assertEqual(damage, 0.0)

    def test_calculate_damage_minimo_garantizado(self) -> None:
        """El daño mínimo es MIN_DAMAGE cuando es positivo."""
        damage = CombatSystem.calculate_damage(10.0, 5.0)
        self.assertGreaterEqual(damage, CombatSystem.MIN_DAMAGE)

    def test_calculate_damage_ataque_negativo_lanza_error(self) -> None:
        """Ataque negativo lanza error."""
        with self.assertRaises(ValueError):
            CombatSystem.calculate_damage(-10.0, 5.0)

    def test_calculate_damage_defensa_negativa_lanza_error(self) -> None:
        """Defensa negativa lanza error."""
        with self.assertRaises(ValueError):
            CombatSystem.calculate_damage(100.0, -5.0)

    def test_calculate_damage_cero_ataque_cero_defensa(self) -> None:
        """Ataque 0 y defensa 0 retorna 0."""
        damage = CombatSystem.calculate_damage(0.0, 0.0)
        self.assertEqual(damage, 0.0)


class TestCombatSystemApplySpecialEffect(unittest.TestCase):
    """Tests para aplicar efectos especiales de trampas."""

    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_apply_special_effect_dentro_del_rango(self) -> None:
        """La trampa aplica daño si el objetivo está dentro del rango."""
        trap = Mock()
        trap.position = Vector2D(0.0, 0.0)
        trap.explosion_damage = 100.0
        trap.explosion_range = 100.0

        target = MockSprite(self.screen, x=50.0, y=0.0)
        target.health = 100.0
        target.take_damage = Mock(return_value=50.0)

        damage = CombatSystem.apply_special_effect(trap, target)
        self.assertGreater(damage, 0.0)
        target.take_damage.assert_called_once()

    def test_apply_special_effect_fuera_del_rango(self) -> None:
        """La trampa no aplica daño si el objetivo está fuera del rango."""
        trap = Mock()
        trap.position = Vector2D(0.0, 0.0)
        trap.explosion_damage = 100.0
        trap.explosion_range = 50.0

        target = MockSprite(self.screen, x=100.0, y=0.0)
        target.health = 100.0
        target.take_damage = Mock(return_value=0.0)

        damage = CombatSystem.apply_special_effect(trap, target)
        self.assertEqual(damage, 0.0)
        target.take_damage.assert_not_called()

    def test_apply_special_effect_epicentro(self) -> None:
        """Daño máximo en el epicentro de la explosión."""
        trap = Mock()
        trap.position = Vector2D(0.0, 0.0)
        trap.explosion_damage = 100.0
        trap.explosion_range = 100.0

        target = MockSprite(self.screen, x=0.0, y=0.0)
        target.take_damage = Mock(return_value=100.0)

        damage = CombatSystem.apply_special_effect(trap, target)
        target.take_damage.assert_called()

    def test_apply_special_effect_sin_take_damage(self) -> None:
        """Si no tiene take_damage, intenta usar defend."""
        trap = Mock()
        trap.position = Vector2D(0.0, 0.0)
        trap.explosion_damage = 100.0
        trap.explosion_range = 100.0

        target = MockSprite(self.screen, x=10.0, y=0.0)
        target.take_damage = None
        target.defend = Mock(return_value=50.0)

        damage = CombatSystem.apply_special_effect(trap, target)
        self.assertGreater(damage, 0.0)
        target.defend.assert_called_once()

    def test_apply_special_effect_trap_sin_atributos_lanza_error(self) -> None:
        """Trampa sin explosion_damage lanza error."""
        trap = Mock(spec=[])
        target = MockSprite(self.screen)

        with self.assertRaises(ValueError):
            CombatSystem.apply_special_effect(trap, target)

    def test_apply_special_effect_target_sin_position_lanza_error(self) -> None:
        """Target sin position lanza error."""
        trap = Mock()
        trap.position = Vector2D(0.0, 0.0)
        trap.explosion_damage = 100.0
        trap.explosion_range = 100.0
        
        target = Mock(spec=[])
        with self.assertRaises(ValueError):
            CombatSystem.apply_special_effect(trap, target)


class TestCombatSystemResolveCombat(unittest.TestCase):
    """Tests para resolver combate entre player y enemy."""

    def setUp(self) -> None:
        self.screen = make_screen()

    def tearDown(self) -> None:
        pygame.quit()

    def test_resolve_combat_player_gana(self) -> None:
        """El combate retorna daños aplicados correctamente."""
        player = Mock()
        player.stats = Stats()
        player.stats.damage = 50.0
        player.stats.defense = 10.0
        player.health = 100.0
        player.defend = Mock(return_value=0.0)

        enemy = Mock()
        enemy.attack_power = 20.0
        enemy.defense = 5.0
        enemy.health = 80.0
        enemy.take_damage = Mock(return_value=45.0)

        result = CombatSystem.resolve_combat(player, enemy)

        self.assertIn("player_damage", result)
        self.assertIn("enemy_damage", result)
        self.assertIn("player_health", result)
        self.assertIn("enemy_health", result)
        self.assertGreater(result["player_damage"], 0.0)

    def test_resolve_combat_sin_stats_lanza_error(self) -> None:
        """Si player no tiene stats lanza error."""
        player = Mock(spec=[])
        enemy = Mock()

        with self.assertRaises(ValueError):
            CombatSystem.resolve_combat(player, enemy)

    def test_resolve_combat_sin_attack_power_lanza_error(self) -> None:
        """Si enemy no tiene attack_power lanza error."""
        player = Mock()
        player.stats = Stats()
        
        enemy = Mock(spec=[])

        with self.assertRaises(ValueError):
            CombatSystem.resolve_combat(player, enemy)

    def test_resolve_combat_simetrico(self) -> None:
        """Ambos bandos reciben daño."""
        player = Mock()
        player.stats = Stats()
        player.stats.damage = 60.0
        player.stats.defense = 8.0
        player.health = 150.0
        player.defend = Mock(side_effect=lambda x: max(0.0, x - 8.0))

        enemy = Mock()
        enemy.attack_power = 40.0
        enemy.defense = 10.0
        enemy.health = 120.0
        enemy.take_damage = Mock(side_effect=lambda x: max(0.0, x - 10.0))

        result = CombatSystem.resolve_combat(player, enemy)

        self.assertGreater(result["player_damage"], 0.0)
        self.assertGreater(result["enemy_damage"], 0.0)

    def test_resolve_combat_retorna_salud_actual(self) -> None:
        """El resultado incluye la salud actual después del combate."""
        player = Mock()
        player.stats = Stats()
        player.stats.damage = 100.0
        player.stats.defense = 20.0
        player.health = 200.0
        player.defend = Mock(return_value=10.0)

        enemy = Mock()
        enemy.attack_power = 30.0
        enemy.defense = 5.0
        enemy.health = 100.0
        enemy.take_damage = Mock(return_value=95.0)

        result = CombatSystem.resolve_combat(player, enemy)

        self.assertIn("player_health", result)
        self.assertIn("enemy_health", result)


if __name__ == "__main__":
    unittest.main()
