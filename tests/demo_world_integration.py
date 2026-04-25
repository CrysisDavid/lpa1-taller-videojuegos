"""
Demo visual de integración del mundo con Player, collectibles y enemigos.
Controles: flechas/WASD para mover, W/arriba para saltar, F para disparar,
ESPACIO para regenerar y ESC para salir.
"""

import sys
from pathlib import Path

import pygame

# Agregar el directorio raíz al path para importaciones absolutas
sys.path.insert(0, str(Path(__file__).parent.parent))

from combat.shield import Shield
from core.vector2d import Vector2D
from entities.player import Player
from entities.proyectile import Proyectile
from entities.trap import Trap
from entities.treasure import Treasure
from generate_enemies import generate_enemies_from_image
from stats.stats import Stats
from world.world import World

# Configuración de pantalla
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
TARGET_FPS: int = 60
BACKGROUND_COLOR: tuple[int, int, int] = (135, 206, 235)
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


PLAYER_SPEED: float = 200.0
GRAVITY: float = 600.0
JUMP_FORCE: float = -380.0
GROUND_Y: float = 510.0  # posición Y en la que el jugador toca suelo


def create_player(screen: pygame.Surface) -> Player:
    return Player(
        screen,
        Vector2D(200.0, GROUND_Y),
        "Hero",
        cash=100,
        stats=Stats(max_health=100.0, damage=15.0, defense=5.0),
    )


def main() -> None:
    """Ejecuta la demo visual de integración mundo-player-collectibles."""
    pygame.init()
    screen: pygame.Surface = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    pygame.display.set_caption("Demo - Mundo con Player, Collectibles y Enemigos")

    # Cargar imagen de game over
    game_over_image = pygame.image.load("public/assets/game-over.png")
    game_over_image = pygame.transform.scale(game_over_image, (400, 300))  # Ajustar tamaño

    clock: pygame.time.Clock = pygame.time.Clock()
    is_running: bool = True

    # Crear mundo y player
    world: World = World(screen=screen)
    world.generate(seed=2026, collectible_count=12, enemy_count=6)
    player: Player = create_player(screen)
    player_vy: float = 0.0  # velocidad vertical para gravedad
    on_ground: bool = True
    player_facing: Vector2D = Vector2D(1.0, 0.0)
    projectiles: list[Proyectile] = []
    messages: list[tuple[str, float]] = []  # (texto, tiempo_restante)
    game_over: bool = False

    # Generar enemigos usando la imagen
    world.enemies = generate_enemies_from_image(screen, world.enemy_spawn_points)

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
                elif event.key == pygame.K_SPACE and game_over:
                    # Reiniciar
                    world.generate(
                        seed=frame_count,
                        collectible_count=12,
                        enemy_count=3,
                    )
                    world.enemies = generate_enemies_from_image(screen, world.enemy_spawn_points)
                    player = create_player(screen)
                    player_vy = 0.0
                    on_ground = True
                    player_facing = Vector2D(1.0, 0.0)
                    projectiles.clear()
                    messages.clear()
                    game_over = False
                elif event.key == pygame.K_SPACE and not game_over:
                    world.generate(
                        seed=frame_count,
                        collectible_count=12,
                        enemy_count=3,
                    )
                    # Generar enemigos usando la imagen
                    world.enemies = generate_enemies_from_image(screen, world.enemy_spawn_points)
                    player = create_player(screen)
                    player_vy = 0.0
                    on_ground = True
                    player_facing = Vector2D(1.0, 0.0)
                    projectiles.clear()
                    messages.clear()
                elif event.key in (pygame.K_UP, pygame.K_w) and on_ground:
                    player_vy = JUMP_FORCE
                    on_ground = False
                elif event.key == pygame.K_f:
                    now_seconds: float = pygame.time.get_ticks() / 1000.0
                    projectile = player.shoot(player_facing, current_time=now_seconds)
                    if projectile is not None:
                        projectiles.append(projectile)
                    else:
                        messages.append(("Cadencia activa: espera para disparar", 0.7))

        if not game_over:
            # Movimiento horizontal
            keys = pygame.key.get_pressed()
            dx: float = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= PLAYER_SPEED * delta_time
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += PLAYER_SPEED * delta_time
            player.position.x += dx

            # Mantiene al player dentro de la ventana visible actual de la cámara.
            viewport_left_world = world.camera.offset.x + player.radius
            viewport_right_world = world.camera.offset.x + SCREEN_WIDTH - player.radius
            if player.position.x < viewport_left_world:
                player.position.x = viewport_left_world
            elif player.position.x > viewport_right_world:
                player.position.x = viewport_right_world

            if dx < 0:
                player_facing = Vector2D(-1.0, 0.0)
            elif dx > 0:
                player_facing = Vector2D(1.0, 0.0)

            # Gravedad y salto
            player_vy += GRAVITY * delta_time
            player.position.y += player_vy * delta_time
            if player.position.y >= GROUND_Y:
                player.position.y = GROUND_Y
                player_vy = 0.0
                on_ground = True

            # Colisión con collectibles
            for collectible in world.collectibles:
                if collectible.is_active:
                    if isinstance(collectible, Treasure):
                        # Recolectar tesoro si está cerca del jugador
                        distance = player.position.distance_to(collectible.position)
                        if distance < 50.0:
                            value = collectible.collect_value()
                            player.cash += int(value)
                            player.trigger_treasure_pickup_effect()  # Efecto visual amarillo
                            messages.append((f"+${value:.0f} (Tesoro)", 2.0))
                            collectible.is_active = False
                    elif player.colission(collectible):
                        if isinstance(collectible, Shield):
                            result = collectible.activate()
                            boost = result.get("defense_boost", 0.0)
                            player.stats.defense += boost
                            player.trigger_shield_pickup_effect()  # Efecto visual azul
                            messages.append((f"+{boost:.0f} DEF (Escudo)", 2.0))
                        elif isinstance(collectible, Trap):
                            dmg = collectible.explode(player.position)
                            net = player.defend(dmg)
                            messages.append((f"-{net:.0f} HP (Trampa)", 2.0))
                        collectible.is_active = False

            # Colisión con enemigos (ataque por proximidad)
            for enemy in world.enemies:
                if not enemy.is_defeated and enemy.attack_cooldown <= 0:
                    distance = player.position.distance_to(enemy.position)
                    if distance < 100.0:  # Distancia de ataque
                        dmg = enemy.attack(player)
                        if dmg > 0:
                            messages.append((f"-{dmg:.0f} HP (Enemigo cercano)", 1.5))
                        enemy.attack_cooldown = 1.0  # Cooldown de 1 segundo entre ataques

            # Actualizar proyectiles y resolver impactos con enemigos
            for projectile in projectiles:
                if not projectile.is_active:
                    continue
                projectile.update(delta_time)
                for enemy in world.enemies:
                    if enemy.is_defeated:
                        continue
                    hit_damage = projectile.hit(enemy)
                    if hit_damage > 0:
                        messages.append((f"-{hit_damage:.0f} HP al enemigo", 1.0))
                        if enemy.is_defeated:
                            gained_levels = player.gain_experience(25.0)
                            if gained_levels > 0:
                                player.health = player.stats.max_health
                                messages.append((f"LEVEL UP x{gained_levels}!", 1.5))
                            else:
                                messages.append(("+25 XP", 1.0))

            # Limpiar proyectiles inactivos
            projectiles = [p for p in projectiles if p.is_active]

            # Expirar mensajes
            messages = [(txt, t - delta_time) for txt, t in messages if t > 0]

            # Actualizar mundo
            world.update(delta_time)
            player.update(delta_time)

            # Verificar game over
            if not player.is_active and not game_over:
                game_over = True
        # Renderizar
        screen.fill(BACKGROUND_COLOR)

        # Dibujar mundo (plataformas, collectibles y enemigos)
        world.draw(surface=screen, camera_offset_x=world.camera.offset.x)

        # Dibujar player con offset de cámara
        saved_x = player.position.x
        player.position.x = player.position.x - world.camera.offset.x
        player.draw()
        player.position.x = saved_x

        # Dibujar proyectiles con offset de cámara
        for projectile in projectiles:
            saved_proj_x = projectile.position.x
            projectile.position.x = projectile.position.x - world.camera.offset.x
            projectile.draw()
            projectile.position.x = saved_proj_x

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
            "DEMO: Mundo con Player, Collectibles y Enemigos",
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

        # Stats del player
        player_color = (80, 200, 255) if player.is_active else (150, 50, 50)
        player_label: pygame.Surface = render_text_with_background(
            font_medium, f"[ {player.name} ]  Lv.{player.stats.level}", player_color, UI_BG_COLOR
        )
        screen.blit(player_label, (info_x, info_y))
        info_y += 26

        hp_pct = player.health / player.stats.max_health
        hp_color = (80, 220, 80) if hp_pct > 0.5 else (220, 180, 40) if hp_pct > 0.25 else (220, 60, 60)
        hp_info: str = f"  HP: {player.health:.0f}/{player.stats.max_health:.0f}"
        screen.blit(render_text_with_background(font_small, hp_info, hp_color, UI_BG_COLOR), (info_x, info_y))
        info_y += 20
        xp_info: str = f"  XP: {player.stats.experience:.0f}/{player.stats.experience_threshold:.0f}"
        screen.blit(render_text_with_background(font_small, xp_info, (180, 130, 220), UI_BG_COLOR), (info_x, info_y))
        info_y += 20
        cash_info: str = f"  ${player.cash}  |  DEF {player.stats.defense:.0f}  |  ATK {player.stats.damage:.0f}"
        screen.blit(render_text_with_background(font_small, cash_info, (250, 210, 60), UI_BG_COLOR), (info_x, info_y))
        info_y += 24

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

        # Contador de enemigos
        active_enemies: int = sum(1 for e in world.enemies if not e.is_defeated)
        enemies_info: str = f"Enemigos Activos: {active_enemies}/{len(world.enemies)}"
        enemies_surface: pygame.Surface = render_text_with_background(
            font_medium, enemies_info, (255, 120, 120), UI_BG_COLOR
        )
        screen.blit(enemies_surface, (info_x, info_y))
        info_y += 28

        projectile_info: str = f"Proyectiles Activos: {len(projectiles)}"
        projectile_surface: pygame.Surface = render_text_with_background(
            font_small, projectile_info, (255, 220, 100), UI_BG_COLOR
        )
        screen.blit(projectile_surface, (info_x, info_y))
        info_y += 22

        # Instrucciones
        instructions: str = "WASD/flechas: mover | W/arriba: saltar | F: disparar | ESPACIO: regenerar | ESC: salir"
        instructions_surface: pygame.Surface = render_text_with_background(
            font_small, instructions, (150, 150, 150), UI_BG_COLOR
        )
        screen.blit(
            instructions_surface,
            (info_x, SCREEN_HEIGHT - 30),
        )

        # Mensajes de feedback en pantalla (centro-arriba)
        for i, (msg_text, _) in enumerate(messages[-5:]):
            msg_surf = render_text_with_background(font_medium, msg_text, (255, 255, 100), (0, 0, 0))
            screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, 60 + i * 28))

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

        # Mostrar game over si es necesario
        if game_over:
            image_rect = game_over_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(game_over_image, image_rect)
            # Mensaje para reiniciar
            restart_text = render_text_with_background(font_medium, "Presiona ESPACIO para reiniciar", (255, 255, 255), (0, 0, 0))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 150))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
