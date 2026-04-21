from __future__ import annotations

import pygame

from core.sprite import Sprite
from core.vector2d import Vector2D
from stats.stats import Stats


class Proyectile(Sprite):
    """Proyectil disparado por el jugador que causa daño a enemigos."""

    DEFAULT_COLOR: tuple[int, int, int] = (255, 230, 80)
    DEFAULT_RADIUS: int = 6

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        direction: Vector2D,
        *,
        velocity: float = 400.0,
        stats: Stats,
        life_time: float = 2.0,
    ) -> None:
        if velocity <= 0:
            raise ValueError("velocity debe ser mayor a 0")
        if life_time <= 0:
            raise ValueError("life_time debe ser mayor a 0")

        magnitude = direction.magnitude()
        if magnitude == 0:
            raise ValueError("direction no puede ser el vector cero")

        super().__init__(
            screen=screen,
            x=x,
            y=y,
            color=self.DEFAULT_COLOR,
            raius=self.DEFAULT_RADIUS,
        )

        self.direction: Vector2D = direction * (1.0 / magnitude)  # normalizado
        self.velocity: float = velocity
        self.stats: Stats = stats
        self._life_time: float = life_time
        self._elapsed: float = 0.0

    @property
    def remaining_life_time(self) -> float:
        return max(0.0, self._life_time - self._elapsed)

    def update(self, dt: float) -> None:
        """Mueve el proyectil y lo desactiva si agotó su vida útil."""
        if dt < 0:
            raise ValueError("dt no puede ser negativo")
        if not self.is_active:
            return

        self._elapsed += dt
        if self._elapsed >= self._life_time:
            self.is_active = False
            return

        self.position.x += self.direction.x * self.velocity * dt
        self.position.y += self.direction.y * self.velocity * dt

    def hit(self, enemy: object) -> float:
        """
        Aplica daño a un enemigo si colisiona con él.

        Returns:
            float: Daño infligido (0.0 si no hubo impacto).
        """
        if not self.is_active:
            return 0.0
        if not (hasattr(enemy, "is_active") and enemy.is_active):
            return 0.0
        if not (hasattr(enemy, "colission") and self.colission(enemy)):
            return 0.0

        damage: float = self.stats.damage
        if hasattr(enemy, "take_damage") and callable(enemy.take_damage):
            net = enemy.take_damage(damage)
        elif hasattr(enemy, "health"):
            net = damage
            setattr(enemy, "health", max(0.0, float(enemy.health) - net))
        else:
            return 0.0

        self.is_active = False
        return net
