import pygame

from core.vector2d import Vector2D
from entities.collectible import Collectible


class Trap(Collectible):
    """Trampa explosiva con daño y alcance de explosión."""

    DEFAULT_COLOR: tuple[int, int, int] = (220, 90, 70)

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        *,
        explosion_damage: float,
        explosion_range: float,
        description: str = "Trampa explosiva",
        life_time: float = 30.0,
    ) -> None:
        if explosion_damage <= 0:
            raise ValueError("explosion_damage debe ser mayor a 0")
        if explosion_range <= 0:
            raise ValueError("explosion_range debe ser mayor a 0")

        super().__init__(
            screen=screen,
            x=x,
            y=y,
            color=self.DEFAULT_COLOR,
            life_time=life_time,
            description=description,
        )
        self.explosion_damage: float = explosion_damage
        self.explosion_range: float = explosion_range
        self.has_exploded: bool = False

    def explode(self, target_position: Vector2D | None = None) -> float:
        """Detona la trampa y retorna el daño aplicado al objetivo."""
        if self.has_exploded:
            return 0.0

        self.has_exploded = True
        self.collect()

        if target_position is None:
            return self.explosion_damage

        distance_to_target: float = self.position.distance_to(target_position)
        if distance_to_target <= self.explosion_range:
            return self.explosion_damage
        return 0.0
