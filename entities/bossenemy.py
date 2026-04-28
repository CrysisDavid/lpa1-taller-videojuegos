from __future__ import annotations

from typing import Literal, Sequence

import pygame

from core.vector2d import Vector2D
from entities.enemy import Enemy
from entities.proyectile import Proyectile
from stats.stats import Stats


class BossEnemy(Enemy):
    """Variante de Enemy con fases y ataques especiales a distancia."""

    DEFAULT_SIZE: tuple[float, float] = (220.0, 220.0)
    DEFAULT_SHOT_COOLDOWN: float = 1.5
    DEFAULT_PROJECTILE_VELOCITY: float = 320.0
    DEFAULT_PROJECTILE_LIFE_TIME: float = 3.0

    def __init__(
        self,
        screen: pygame.Surface,
        world_pos: Vector2D,
        name: str,
        *,
        size: Vector2D | None = None,
        velocity: float = 40.0,
        enemy_type: Literal["volador", "terrestre"] = "terrestre",
        health: float = 260.0,
        attack_power: float = 25.0,
        defense: float = 10.0,
        special_attacks: Sequence[str] | None = None,
        projectile_velocity: float = DEFAULT_PROJECTILE_VELOCITY,
        projectile_life_time: float = DEFAULT_PROJECTILE_LIFE_TIME,
        shot_cooldown: float = DEFAULT_SHOT_COOLDOWN,
    ) -> None:
        boss_size: Vector2D = (
            size if size is not None else Vector2D(*self.DEFAULT_SIZE)
        )
        super().__init__(
            screen=screen,
            world_pos=world_pos,
            name=name,
            size=boss_size,
            velocity=velocity,
            enemy_type=enemy_type,
            health=health,
            attack_power=attack_power,
            defense=defense,
        )
        if projectile_velocity <= 0:
            raise ValueError("projectile_velocity debe ser mayor a 0")
        if projectile_life_time <= 0:
            raise ValueError("projectile_life_time debe ser mayor a 0")
        if shot_cooldown < 0:
            raise ValueError("shot_cooldown no puede ser negativo")

        self.max_health: float = health
        self.phase: float = 1.0
        self.special_attacks: list[str] = list(special_attacks or ["slam"])
        self.projectile_velocity: float = projectile_velocity
        self.projectile_life_time: float = projectile_life_time
        self.shot_cooldown: float = shot_cooldown
        self._last_shot_time: float = float("-inf")
        self.trigger_phase_change()

    def trigger_phase_change(self) -> None:
        """Ajusta la fase del boss según su vida restante."""
        health_ratio: float = self.health / max(self.max_health, 1.0)
        if health_ratio <= 0.33:
            self.phase = 3.0
            self.special_attacks = ["slam", "projectile_burst", "rage_shot"]
        elif health_ratio <= 0.66:
            self.phase = 2.0
            self.special_attacks = ["slam", "projectile_burst"]
        else:
            self.phase = 1.0
            self.special_attacks = ["slam"]

    def create_projectile(
        self,
        target_position: Vector2D,
        *,
        current_time: float = 0.0,
    ) -> Proyectile | None:
        """Crea un proyectil dirigido al objetivo si el cooldown lo permite."""
        if current_time < 0:
            raise ValueError("current_time no puede ser negativo")
        if not self.is_active:
            return None
        if (current_time - self._last_shot_time) < self.shot_cooldown:
            return None

        direction: Vector2D = target_position - self.position
        if direction.magnitude() == 0:
            return None

        projectile_stats = Stats(
            max_health=1.0,
            endurance=1.0,
            damage=self.attack_power * (1.0 + 0.5 * (self.phase - 1.0)),
            defense=0.0,
        )
        projectile = Proyectile(
            screen=self.screen,
            x=self.x,
            y=self.y,
            direction=direction,
            velocity=self.projectile_velocity,
            stats=projectile_stats,
            life_time=self.projectile_life_time,
        )
        self._last_shot_time = current_time
        return projectile

    def special_attack(
        self,
        player: object,
        *,
        current_time: float = 0.0,
    ) -> Proyectile | None:
        """Ejecuta el ataque especial principal del boss contra el jugador."""
        self.trigger_phase_change()
        if not hasattr(player, "position"):
            return None
        return self.create_projectile(player.position, current_time=current_time)