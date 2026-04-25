import pygame
from pathlib import Path

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
            image=str(Path(__file__).parent.parent / "public" / "assets" / "tramp.png"),
        )
        self.explosion_damage: float = explosion_damage
        self.explosion_range: float = explosion_range
        self.has_exploded: bool = False
        self.explosion_effect_timer: float = 0.0

    def draw(self) -> None:
        """Dibuja la trampa usando imagen si está disponible, sino círculo."""
        if self.is_active:
            if self.image:
                self.draw_image()
            else:
                super().draw()
        
        # Efecto de explosión: círculo rojo expandiéndose
        if self.explosion_effect_timer > 0:
            explosion_radius = self.radius * (1 + (0.5 - self.explosion_effect_timer) * 2)  # Expande de radius a 2*radius
            pygame.draw.circle(
                self.screen,
                (255, 100, 0),  # Naranja rojizo
                (int(self.position.x), int(self.position.y)),
                int(explosion_radius)
            )

    def explode(self, target_position: Vector2D | None = None) -> float:
        """Detona la trampa y retorna el daño aplicado al objetivo."""
        if self.has_exploded:
            return 0.0

        self.has_exploded = True
        self.explosion_effect_timer = 0.5  # Efecto de explosión por 0.5 segundos
        self.collect()

        if target_position is None:
            return self.explosion_damage

        distance_to_target: float = self.position.distance_to(target_position)
        if distance_to_target <= self.explosion_range:
            return self.explosion_damage
        return 0.0

    def update(self, delta_time: float = 0.0) -> None:
        """Actualiza el estado de la trampa."""
        super().update(delta_time)
        if self.explosion_effect_timer > 0:
            self.explosion_effect_timer -= delta_time
