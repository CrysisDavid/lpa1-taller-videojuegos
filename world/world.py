from typing import List

import pygame

from world.camera import Camera
from world.platform import Platform


class World:
    """Contiene y dibuja todas las plataformas del nivel."""

    CAMERA_SCROLL_SPEED: float = 200.0
    PLATFORM_WIDTH: int = 120
    PLATFORM_HEIGHT: int = 20
    PLATFORM_COLOR: tuple[int, int, int] = (100, 150, 100)
    GROUND_Y: float = 550.0
    PLATFORM_SPACING: int = 180

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Inicializa el mundo con la cámara y plataformas iniciales.

        Args:
            screen (pygame.Surface): Superficie de renderizado del juego.
        """
        self.screen: pygame.Surface = screen
        self.camera: Camera = Camera(scroll_speed=self.CAMERA_SCROLL_SPEED)
        self.platforms: List[Platform] = []
        self._initialize_platforms()

    def _initialize_platforms(self) -> None:
        """Genera las plataformas iniciales del nivel."""
        screen_width: int = self.screen.get_width()
        # Genera plataformas desde el inicio hasta el doble del ancho de pantalla
        max_x: float = screen_width * 2.5

        current_x: float = 0.0
        while current_x < max_x:
            platform: Platform = Platform(
                world_x=current_x,
                world_y=self.GROUND_Y,
                width=self.PLATFORM_WIDTH,
                height=self.PLATFORM_HEIGHT,
                color=self.PLATFORM_COLOR,
            )
            self.platforms.append(platform)
            current_x += self.PLATFORM_SPACING

    def add_platform(self, platform: Platform) -> None:
        """
        Agrega una plataforma al mundo.

        Args:
            platform (Platform): Plataforma a agregar.
        """
        self.platforms.append(platform)

    def update(self, delta_time: float) -> None:
        """
        Actualiza el estado del mundo (movimiento de cámara).

        Args:
            delta_time (float): Tiempo transcurrido en segundos desde el
                                último frame.
        """
        self.camera.update(delta_time)
        self._generate_distant_platforms()

    def _generate_distant_platforms(self) -> None:
        """
        Genera nuevas plataformas cuando el scroll se acerca al límite.
        Evita que el jugador se quede sin plataformas.
        """
        if not self.platforms:
            return

        screen_width: int = self.screen.get_width()
        furthest_x: float = max(
            platform.x for platform in self.platforms
        )
        camera_right_edge: float = (
            self.camera.offset.x + screen_width
        )

        # Si el borde derecho visible se acerca al final de las plataformas
        if camera_right_edge > furthest_x - screen_width:
            next_x: float = furthest_x + self.PLATFORM_SPACING
            new_platform: Platform = Platform(
                world_x=next_x,
                world_y=self.GROUND_Y,
                width=self.PLATFORM_WIDTH,
                height=self.PLATFORM_HEIGHT,
                color=self.PLATFORM_COLOR,
            )
            self.platforms.append(new_platform)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset_x: float,
    ) -> None:
        """
        Renderiza todas las plataformas visibles del mundo.

        Args:
            surface (pygame.Surface): Superficie donde renderizar.
            camera_offset_x (float): Offset X de la cámara para aplicar scroll.
        """
        screen_width: int = surface.get_width()

        for platform in self.platforms:
            if platform.is_on_screen(screen_width, camera_offset_x):
                platform.draw(surface, camera_offset_x)
