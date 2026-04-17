from core.vector2d import Vector2D


class Camera:
    """Traduce coordenadas del mundo a coordenadas de pantalla y viceversa."""

    def __init__(self, scroll_speed: float = 200.0) -> None:
        """
        Inicializa la cámara con velocidad de scroll.

        Args:
            scroll_speed (float): Velocidad de scroll en píxeles/segundo.
        """
        self.offset: Vector2D = Vector2D(0.0, 0.0)
        self.scroll_speed: float = scroll_speed

    def update(self, delta_time: float) -> None:
        """
        Actualiza la posición del offset de la cámara.
        El mundo se mueve hacia la izquierda constantemente.

        Args:
            delta_time (float): Tiempo transcurrido en segundos desde el
                                último frame.
        """
        scroll_distance: float = self.scroll_speed * delta_time
        self.offset.x += scroll_distance

    def apply(self, world_x: float) -> float:
        """
        Convierte una coordenada X del mundo a coordenada X de pantalla.

        Args:
            world_x (float): Coordenada X en coordenadas del mundo.

        Returns:
            float: Coordenada X en coordenadas de pantalla.
        """
        return world_x - self.offset.x

    def to_world(self, screen_x: float) -> float:
        """
        Convierte una coordenada X de pantalla a coordenada X del mundo.

        Args:
            screen_x (float): Coordenada X en coordenadas de pantalla.

        Returns:
            float: Coordenada X en coordenadas del mundo.
        """
        return screen_x + self.offset.x
