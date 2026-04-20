import pygame

from entities.collectible import Collectible


class Treasure(Collectible):
    """Tesoro recolectable que otorga valor monetario."""

    DEFAULT_COLOR: tuple[int, int, int] = (250, 200, 40)

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
            life_time=life_time,
            description=description,
        )
        self.name: str = name
        self.monetary_value: float = monetary_value

    def collect_value(self) -> float:
        """Recolecta el tesoro y retorna su valor monetario."""
        self.collect()
        return self.monetary_value
