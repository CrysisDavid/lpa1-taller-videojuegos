import pygame
from pathlib import Path

from entities.collectible import Collectible


class Shield(Collectible):
    """Ítem defensivo recolectable que otorga protección temporal."""

    DEFAULT_COLOR: tuple[int, int, int] = (80, 170, 240)
    DEFAULT_IMAGE: str = str(Path(__file__).parent.parent / "public" / "assets" / "escudo.png")

    DEFAULT_SHIELD_HP: float = 50.0

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        *,
        duration: float,
        description: str = "Escudo básico",
        defense_boost: float = 0.0,
        shield_hp: float = DEFAULT_SHIELD_HP,
    ) -> None:
        if duration <= 0:
            raise ValueError("duration debe ser mayor a 0")
        if defense_boost < 0:
            raise ValueError("defense_boost no puede ser negativo")
        if shield_hp < 0:
            raise ValueError("shield_hp no puede ser negativo")

        super().__init__(
            screen=screen,
            x=x,
            y=y,
            color=self.DEFAULT_COLOR,
            life_time=duration,
            description=description,
            image=self.DEFAULT_IMAGE,
        )
        self.duration: float = duration
        self.defense_boost: float = defense_boost
        self.shield_hp: float = shield_hp

    def draw(self) -> None:
        """Dibuja el escudo usando imagen si está disponible, sino círculo."""
        if self.is_active:
            if self.image:
                self.draw_image()
            else:
                super().draw()

    def activate(self) -> dict[str, float]:
        """Activa el escudo y retorna sus efectos para el jugador."""
        return {
            "duration": self.duration,
            "defense_boost": self.defense_boost,
            "shield_hp": self.shield_hp,
        }
