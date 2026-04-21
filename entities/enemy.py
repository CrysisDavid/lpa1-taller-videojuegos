from __future__ import annotations

from typing import Literal

import pygame

from core.sprite import Sprite
from core.vector2d import Vector2D


class Enemy(Sprite):
    """Entidad enemiga con estadisticas de combate y movimiento simple."""

    DEFAULT_COLOR: tuple[int, int, int] = (220, 80, 80)
    DEFAULT_RADIUS: int = 20

    def __init__(
        self,
        screen: pygame.Surface,
        world_pos: Vector2D,
        name: str,
        *,
        size: Vector2D | None = None,
        velocity: float = 120.0,
        enemy_type: Literal["volador", "terrestre"] = "terrestre",
        health: float = 100.0,
        attack_power: float = 15.0,
        defense: float = 5.0,
    ) -> None:
        if not name.strip():
            raise ValueError("name no puede estar vacio")
        if velocity < 0:
            raise ValueError("velocity no puede ser negativo")
        if health <= 0:
            raise ValueError("health debe ser mayor a 0")
        if attack_power < 0:
            raise ValueError("attack_power no puede ser negativo")
        if defense < 0:
            raise ValueError("defense no puede ser negativo")

        enemy_size: Vector2D = size if size is not None else Vector2D(40.0, 40.0)
        radius: int = max(self.DEFAULT_RADIUS, int(min(enemy_size.x, enemy_size.y) / 2))

        super().__init__(
            screen=screen,
            x=world_pos.x,
            y=world_pos.y,
            color=self.DEFAULT_COLOR,
            raius=radius,
        )

        self.size: Vector2D = enemy_size
        self.velocity: float = velocity
        self.pos: Vector2D = self.position
        self.name: str = name
        self.health: float = health
        self.attack_power: float = attack_power
        self.defense: float = defense
        self.type: Literal["volador", "terrestre"] = enemy_type

    @property
    def is_defeated(self) -> bool:
        """Indica si el enemigo quedo sin vida."""
        return self.health <= 0 or not self.is_active

    def attack(self, player: object) -> float:
        """Ataca al jugador y retorna el dano infligido."""
        if not self.is_active:
            return 0.0

        damage: float = self.attack_power

        player_defense: float = float(getattr(player, "defense", 0.0))
        if hasattr(player, "stats"):
            player_defense = float(getattr(player.stats, "defense", player_defense))

        final_damage: float = max(0.0, damage - player_defense)

        if hasattr(player, "take_damage") and callable(player.take_damage):
            player.take_damage(final_damage)
        elif hasattr(player, "health"):
            new_health: float = max(0.0, float(player.health) - final_damage)
            setattr(player, "health", new_health)

        return final_damage

    def take_damage(self, damage: float) -> float:
        """Recibe dano, aplica defensa y retorna dano neto recibido."""
        if damage < 0:
            raise ValueError("damage no puede ser negativo")
        if not self.is_active:
            return 0.0

        net_damage: float = max(0.0, damage - self.defense)
        self.health = max(0.0, self.health - net_damage)

        if self.health <= 0:
            self.is_active = False

        return net_damage

    def update(self, delta_time: float = 0.0) -> None:
        """Actualiza movimiento horizontal basico del enemigo."""
        if delta_time < 0:
            raise ValueError("delta_time no puede ser negativo")
        if not self.is_active:
            return

        self.position.x -= self.velocity * delta_time
        self.keep_on_screen()