import pygame

from entities.collectible import Collectible


class Shield(Collectible):
    """Ítem defensivo recolectable que otorga protección temporal."""

    DEFAULT_COLOR: tuple[int, int, int] = (80, 170, 240)

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        *,
        duration: float,
        description: str = "Escudo básico",
        defense_boost: float = 0.0,
    ) -> None:
        if duration <= 0:
            raise ValueError("duration debe ser mayor a 0")
        if defense_boost < 0:
            raise ValueError("defense_boost no puede ser negativo")

        super().__init__(
            screen=screen,
            x=x,
            y=y,
            color=self.DEFAULT_COLOR,
            life_time=duration,
            description=description,
        )
        self.duration: float = duration
        self.defense_boost: float = defense_boost

    def activate(self) -> dict[str, float]:
        """Activa el escudo y retorna sus efectos para el jugador."""
        self.collect()
        return {
            "duration": self.duration,
            "defense_boost": self.defense_boost,
        }
