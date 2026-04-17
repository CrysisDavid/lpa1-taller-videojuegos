from typing import Optional

import pygame

from core.vector2d import Vector2D


class Platform:
    """Representa una plataforma sobre la que el jugador puede pararse."""

    def __init__(
        self,
        world_x: float,
        world_y: float,
        width: int,
        height: int,
        color: tuple[int, int, int] = (100, 100, 100),
    ) -> None:
        """
        Inicializa una plataforma en el mundo.

        Args:
            world_x (float): Posición X en coordenadas del mundo.
            world_y (float): Posición Y en coordenadas del mundo.
            width (int): Ancho de la plataforma en píxeles.
            height (int): Alto de la plataforma en píxeles.
            color (tuple[int, int, int]): Color RGB de la plataforma.
        """
        self.position: Vector2D = Vector2D(world_x, world_y)
        self.width: int = width
        self.height: int = height
        self.color: tuple[int, int, int] = color
        self.is_active: bool = True

    @property
    def x(self) -> float:
        """Coordenada X de la plataforma."""
        return self.position.x

    @property
    def y(self) -> float:
        """Coordenada Y de la plataforma."""
        return self.position.y

    @property
    def rect(self) -> pygame.Rect:
        """Retorna un Rect para operaciones de colisión y renderizado."""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset_x: float,
    ) -> None:
        """
        Renderiza la plataforma en pantalla aplicando el offset de cámara.

        Args:
            surface (pygame.Surface): Superficie donde renderizar.
            camera_offset_x (float): Offset X de la cámara.
        """
        screen_x: float = self.x - camera_offset_x
        screen_rect: pygame.Rect = pygame.Rect(
            int(screen_x),
            int(self.y),
            self.width,
            self.height,
        )
        pygame.draw.rect(surface, self.color, screen_rect)

    def is_on_screen(self, screen_width: int, camera_offset_x: float) -> bool:
        """
        Verifica si la plataforma es visible en pantalla.

        Args:
            screen_width (int): Ancho de la pantalla.
            camera_offset_x (float): Offset X de la cámara.

        Returns:
            bool: True si la plataforma está dentro del área visible.
        """
        screen_x: float = self.x - camera_offset_x
        return screen_x + self.width >= 0 and screen_x <= screen_width
