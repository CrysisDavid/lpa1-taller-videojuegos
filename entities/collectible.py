from __future__ import annotations

import math

import pygame

from core.sprite import Sprite


class Collectible(Sprite):
    """Objeto recolectable con tiempo de vida y estado de colección."""

    DEFAULT_COLOR: tuple[int, int, int] = (240, 220, 80)
    DEFAULT_RADIUS: int = 14

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        *,
        color: tuple[int, int, int] = DEFAULT_COLOR,
        radius: int = DEFAULT_RADIUS,
        life_time: float = math.inf,
        description: str = "",
        image: str = None,
    ) -> None:
        if life_time <= 0:
            raise ValueError("life_time debe ser mayor a 0")

        super().__init__(screen=screen, x=x, y=y, color=color, radius=radius, image=image)
        self.life_time: float = float(life_time)
        self.description: str = description
        self.elapsed_time: float = 0.0
        self.is_collected: bool = False

    @property
    def remaining_life_time(self) -> float:
        """Tiempo restante antes de expirar."""
        if math.isinf(self.life_time):
            return math.inf
        return max(0.0, self.life_time - self.elapsed_time)

    def collect(self) -> None:
        """Marca el objeto como recolectado y lo desactiva."""
        self.is_collected = True
        self.is_active = False

    def update(self, delta_time: float = 0.0) -> None:
        """Avanza el tiempo de vida del recolectable."""
        if delta_time < 0:
            raise ValueError("delta_time no puede ser negativo")
        if not self.is_active or math.isinf(self.life_time):
            return

        self.elapsed_time += delta_time
        if self.elapsed_time >= self.life_time:
            self.is_active = False
