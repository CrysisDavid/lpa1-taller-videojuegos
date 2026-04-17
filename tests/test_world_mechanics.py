"""
Script de prueba para validar la mecánica del mundo.
Muestra el scroll constante hacia la izquierda y las plataformas generadas
proceduralmente.
"""

import sys
from pathlib import Path

import pygame

# Agregar el directorio raíz al path para importaciones absolutas
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from world.world import World

# Configuración de pantalla
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
TARGET_FPS: int = 60
BACKGROUND_COLOR: tuple[int, int, int] = (30, 30, 30)


def main() -> None:
    """Ejecuta la prueba de la mecánica del mundo."""
    pygame.init()
    screen: pygame.Surface = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    pygame.display.set_caption("Prueba - Mecánica del Mundo")

    clock: pygame.time.Clock = pygame.time.Clock()
    is_running: bool = True

    # Crear el mundo
    world: World = World(screen=screen)

    # Variables para visualización
    frame_count: int = 0
    font: pygame.font.Font = pygame.font.Font(None, 24)

    while is_running:
        delta_time: float = clock.tick(TARGET_FPS) / 1000.0
        frame_count += 1

        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    is_running = False

        # Actualizar mundo
        world.update(delta_time)

        # Renderizar
        screen.fill(BACKGROUND_COLOR)

        # Dibujar mundo
        world.draw(surface=screen, camera_offset_x=world.camera.offset.x)

        # Información de depuración
        camera_x_text: str = (
            f"Camera Offset X: {world.camera.offset.x:.1f}"
        )
        platforms_count_text: str = (
            f"Plataformas: {len(world.platforms)}"
        )
        visible_platforms_text: str = (
            f"Plataformas visibles: "
            f"{sum(1 for p in world.platforms if p.is_on_screen(SCREEN_WIDTH, world.camera.offset.x))}"
        )

        # Renderizar información
        camera_label: pygame.Surface = font.render(camera_x_text, True, (200, 200, 200))
        platforms_label: pygame.Surface = font.render(
            platforms_count_text, True, (200, 200, 200)
        )
        visible_label: pygame.Surface = font.render(
            visible_platforms_text, True, (200, 200, 200)
        )

        screen.blit(camera_label, (10, 10))
        screen.blit(platforms_label, (10, 35))
        screen.blit(visible_label, (10, 60))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
