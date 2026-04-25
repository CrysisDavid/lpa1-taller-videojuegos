import pygame
from pathlib import Path

from entities.collectible import Collectible


class Treasure(Collectible):
    """Tesoro recolectable que otorga valor monetario."""

    DEFAULT_COLOR: tuple[int, int, int] = (250, 200, 40)
    DEFAULT_IMAGE: str = str(Path(__file__).parent.parent / "public" / "assets" / "treasure.png")

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        *,
        name: str,
        monetary_value: float,
        description: str = "",
        life_time: float = 60.0,
        radius: int = 30,
        velocity: float = 80.0,
    ) -> None:
        if not name.strip():
            raise ValueError("name no puede estar vacío")
        if monetary_value < 0:
            raise ValueError("monetary_value no puede ser negativo")

        super().__init__(
            screen=screen,
            x=x,
            y=y,
            color=self.DEFAULT_COLOR,
            radius=radius,
            life_time=life_time,
            description=description,
            image=self.DEFAULT_IMAGE,
        )
        self.name: str = name
        self.monetary_value: float = monetary_value
        self.velocity: float = velocity

    def draw(self) -> None:
        """Dibuja el tesoro usando imagen si está disponible, sino círculo."""
        if self.is_active:
            if self.image:
                self.draw_image()
            else:
                super().draw()

    def update(self, delta_time: float = 0.0) -> None:
        """Actualiza movimiento y tiempo de vida del tesoro."""
        super().update(delta_time)
        if delta_time < 0:
            raise ValueError("delta_time no puede ser negativo")
        if not self.is_active:
            return
        self.position.x -= self.velocity * delta_time
        self.keep_on_screen()

    def collect_value(self) -> float:
        """Recolecta el tesoro y retorna su valor monetario."""
        self.collect()
        return self.monetary_value
