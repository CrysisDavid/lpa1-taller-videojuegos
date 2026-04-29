"""Sistema centralizado de combate del juego."""

from __future__ import annotations

from core.sprite import Sprite
from core.vector2d import Vector2D


class CombatSystem:
    """Sistema de combate centralizado para resolver cálculos de daño y efectos especiales."""

    # Constantes de combate
    CRITICAL_CHANCE: float = 0.15  # 15% de probabilidad de crítico
    CRITICAL_MULTIPLIER: float = 1.5  # 50% más daño en crítico
    MIN_DAMAGE: float = 1.0  # Daño mínimo garantizado

    @staticmethod
    def calculate_damage(attacker_atk: float, defender_def: float) -> float:
        """
        Calcula el daño neto considerando ataque y defensa.

        Args:
            attacker_atk: Poder de ataque del atacante
            defender_def: Defensa del defensor

        Returns:
            Daño neto infligido (mínimo MIN_DAMAGE si es positivo)
        """
        if attacker_atk < 0:
            raise ValueError("attacker_atk no puede ser negativo")
        if defender_def < 0:
            raise ValueError("defender_def no puede ser negativo")

        net_damage: float = attacker_atk - defender_def
        if net_damage <= 0:
            return 0.0

        return max(CombatSystem.MIN_DAMAGE, net_damage)

    @staticmethod
    def apply_special_effect(trap: object, target: Sprite) -> float:
        """
        Aplica efectos especiales de una trampa a un objetivo.

        Args:
            trap: Objeto trampa con propiedades explosion_damage y explosion_range
            target: Sprite objetivo que recibe el efecto

        Returns:
            Daño efectivo aplicado al objetivo
        """
        if not hasattr(trap, "explosion_damage") or not hasattr(trap, "explosion_range"):
            raise ValueError("trap debe tener explosion_damage y explosion_range")

        if not hasattr(target, "position"):
            raise ValueError("target debe tener atributo position")

        trap_pos: Vector2D = trap.position
        target_pos: Vector2D = target.position
        distance: float = trap_pos.distance_to(target_pos)

        # Si está fuera del alcance, no hay daño
        if distance > trap.explosion_range:
            return 0.0

        # Daño proporcional a la cercanía: máximo en el epicentro, cero en los bordes
        range_factor: float = 1.0 - (distance / trap.explosion_range)
        explosion_damage: float = trap.explosion_damage * range_factor

        # Aplicar daño al objetivo si tiene método para ello
        net_damage: float = 0.0
        if hasattr(target, "take_damage") and callable(target.take_damage):
            net_damage = target.take_damage(explosion_damage)
        elif hasattr(target, "defend") and callable(target.defend):
            net_damage = target.defend(explosion_damage)
        elif hasattr(target, "health"):
            previous_health: float = float(target.health)
            target.health = max(0.0, target.health - explosion_damage)
            net_damage = previous_health - target.health

        return net_damage

    @staticmethod
    def resolve_combat(player: object, enemy: object) -> dict[str, float]:
        """
        Resuelve un combate entre jugador y enemigo.

        Calcula el daño que ambos infligen considerando sus atributos de ataque
        y defensa, y lo aplica mutuamente.

        Args:
            player: Objeto jugador con atributos de combate
            enemy: Objeto enemigo con atributos de combate

        Returns:
            Diccionario con:
                - 'player_damage': Daño infligido al enemigo por el jugador
                - 'enemy_damage': Daño infligido al jugador por el enemigo
                - 'player_health': Salud restante del jugador
                - 'enemy_health': Salud restante del enemigo
        """
        if not hasattr(player, "stats"):
            raise ValueError("player debe tener atributo stats")
        if not hasattr(enemy, "attack_power"):
            raise ValueError("enemy debe tener atributo attack_power")

        # Obtener atributos del player
        player_atk: float = float(getattr(player.stats, "damage", 10.0))
        player_def: float = float(getattr(player.stats, "defense", 0.0))
        player_health: float = float(getattr(player, "health", 100.0))

        # Obtener atributos del enemy
        enemy_atk: float = float(getattr(enemy, "attack_power", 10.0))
        enemy_def: float = float(getattr(enemy, "defense", 0.0))
        enemy_health: float = float(getattr(enemy, "health", 100.0))

        # Calcular daños netos
        player_damage: float = CombatSystem.calculate_damage(player_atk, enemy_def)
        enemy_damage: float = CombatSystem.calculate_damage(enemy_atk, player_def)

        # Aplicar daño al enemigo
        if hasattr(enemy, "take_damage") and callable(enemy.take_damage):
            player_damage = enemy.take_damage(player_damage)
        else:
            enemy.health = max(0.0, enemy_health - player_damage)

        # Aplicar daño al jugador
        if hasattr(player, "defend") and callable(player.defend):
            enemy_damage = player.defend(enemy_damage)
        elif hasattr(player, "take_damage") and callable(player.take_damage):
            enemy_damage = player.take_damage(enemy_damage)
        else:
            player.health = max(0.0, player_health - enemy_damage)

        return {
            "player_damage": player_damage,
            "enemy_damage": enemy_damage,
            "player_health": float(getattr(player, "health", 0.0)),
            "enemy_health": float(getattr(enemy, "health", 0.0)),
        }
