"""
Demo visual de integración del mundo con collectibles.
Muestra plataformas, scroll, generación procedural y collectibles instanciados.
"""

import sys
from pathlib import Path

import pygame

# Agregar el directorio raíz al path para importaciones absolutas
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector2d import Vector2D
from entities.shield import Shield
from entities.trap import Trap
from entities.treasure import Treasure
from world.world import World

# Configuración de pantalla
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
TARGET_FPS: int = 60
BACKGROUND_COLOR: tuple[int, int, int] = (20, 20, 30)
UI_COLOR: tuple[int, int, int] = (200, 200, 200)
UI_BG_COLOR: tuple[int, int, int] = (40, 40, 50)


def render_text_with_background(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    bg_color: tuple[int, int, int],
    padding: int = 4,
) -> pygame.Surface:
    """Renderiza texto con fondo."""
    text_surface: pygame.Surface = font.render(text, True, color)
    text_rect: pygame.Rect = text_surface.get_rect()
    bg_surface: pygame.Surface = pygame.Surface(
        (text_rect.width + padding * 2, text_rect.height + padding * 2)
    )
    bg_surface.fill(bg_color)
    bg_surface.blit(text_surface, (padding, padding))
    return bg_surface


def main() -> None:
    """Ejecuta la demo visual de integración mundo-collectibles."""
    pygame.init()
    screen: pygame.Surface = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    pygame.display.set_caption("Demo - Mundo con Collectibles Integrados")

    clock: pygame.time.Clock = pygame.time.Clock()
    is_running: bool = True

    # Crear el mundo y generar con collectibles
    world: World = World(screen=screen)
    world.generate(seed=2026, collectible_count=12, enemy_count=0)

    # Variables para visualización
    frame_count: int = 0
    font_small: pygame.font.Font = pygame.font.Font(None, 20)
    font_medium: pygame.font.Font = pygame.font.Font(None, 24)
    font_large: pygame.font.Font = pygame.font.Font(None, 28)

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
                elif event.key == pygame.K_SPACE:
                    world.generate(
                        seed=frame_count,
                        collectible_count=12,
                        enemy_count=0,
                    )

        # Actualizar mundo
        world.update(delta_time)

        # Renderizar
        screen.fill(BACKGROUND_COLOR)

        # Dibujar mundo (plataformas y collectibles)
        world.draw(surface=screen, camera_offset_x=world.camera.offset.x)

        # Contar collectibles por tipo
        shield_count: int = sum(
            1 for c in world.collectibles if isinstance(c, Shield) and c.is_active
        )
        trap_count: int = sum(
            1 for c in world.collectibles if isinstance(c, Trap) and c.is_active
        )
        treasure_count: int = sum(
            1 for c in world.collectibles
            if isinstance(c, Treasure) and c.is_active
        )
        total_active: int = shield_count + trap_count + treasure_count

        # Panel de información
        info_y: int = 10
        info_x: int = 10

        # Título
        title_surface: pygame.Surface = font_large.render(
            "DEMO: Mundo con Collectibles",
            True,
            (100, 200, 255),
        )
        screen.blit(title_surface, (info_x, info_y))
        info_y += 35

        # Estado del mundo
        world_info: str = f"Cámara X: {world.camera.offset.x:.0f}"
        world_surface: pygame.Surface = render_text_with_background(
            font_small, world_info, UI_COLOR, UI_BG_COLOR
        )
        screen.blit(world_surface, (info_x, info_y))
        info_y += 25

        platforms_info: str = f"Plataformas: {len(world.platforms)}"
        platforms_surface: pygame.Surface = render_text_with_background(
            font_small, platforms_info, UI_COLOR, UI_BG_COLOR
        )
        screen.blit(platforms_surface, (info_x, info_y))
        info_y += 25

        # Estado de collectibles
        collectibles_info: str = f"Collectibles Activos: {total_active}/{len(world.collectibles)}"
        collectibles_surface: pygame.Surface = render_text_with_background(
            font_medium, collectibles_info, (100, 255, 100), UI_BG_COLOR
        )
        screen.blit(collectibles_surface, (info_x, info_y))
        info_y += 30

        # Desglose por tipo
        shield_info: str = f"  🛡️  Escudos: {shield_count}"
        shield_surface: pygame.Surface = render_text_with_background(
            font_small, shield_info, (80, 170, 240), UI_BG_COLOR
        )
        screen.blit(shield_surface, (info_x, info_y))
        info_y += 22

        trap_info: str = f"  💣 Trampas: {trap_count}"
        trap_surface: pygame.Surface = render_text_with_background(
            font_small, trap_info, (220, 90, 70), UI_BG_COLOR
        )
        screen.blit(trap_surface, (info_x, info_y))
        info_y += 22

        treasure_info: str = f"  💎 Tesoros: {treasure_count}"
        treasure_surface: pygame.Surface = render_text_with_background(
            font_small, treasure_info, (250, 200, 40), UI_BG_COLOR
        )
        screen.blit(treasure_surface, (info_x, info_y))
        info_y += 28

        # Instrucciones
        instructions: str = "ESPACIO: Regenerar mundo | ESC: Salir"
        instructions_surface: pygame.Surface = render_text_with_background(
            font_small, instructions, (150, 150, 150), UI_BG_COLOR
        )
        screen.blit(
            instructions_surface,
            (info_x, SCREEN_HEIGHT - 30),
        )

        # Frame counter en esquina superior derecha
        fps_info: str = f"FPS: {clock.get_fps():.0f}"
        fps_surface: pygame.Surface = render_text_with_background(
            font_small, fps_info, (100, 255, 100), UI_BG_COLOR
        )
        screen.blit(fps_surface, (SCREEN_WIDTH - 120, 10))

        frame_info: str = f"Frame: {frame_count}"
        frame_surface: pygame.Surface = render_text_with_background(
            font_small, frame_info, (100, 255, 100), UI_BG_COLOR
        )
        screen.blit(frame_surface, (SCREEN_WIDTH - 120, 35))

        # Información de collectibles visibles en pantalla
        visible_collectibles: int = sum(
            1
            for c in world.collectibles
            if c.is_active
            and -50 <= (c.x - world.camera.offset.x) <= SCREEN_WIDTH + 50
        )
        visible_info: str = f"Visibles: {visible_collectibles}"
        visible_surface: pygame.Surface = render_text_with_background(
            font_small, visible_info, (150, 200, 150), UI_BG_COLOR
        )
        screen.blit(visible_surface, (SCREEN_WIDTH - 120, 60))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
