"""
Demo visual de integración del mundo con Player, collectibles y enemigos.
Controles: flechas/WASD para mover, W/arriba para saltar, F para disparar,
ESPACIO para regenerar, E para abrir tienda y ESC para salir.
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
from inventory.item import Item
from inventory.store import Store
from stats.stats import Stats
from ui.hud import HUD
from world.world import World

# Configuración de pantalla
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
TARGET_FPS: int = 60
BACKGROUND_COLOR: tuple[int, int, int] = (135, 206, 235)
UI_COLOR: tuple[int, int, int] = (200, 200, 200)
UI_BG_COLOR: tuple[int, int, int] = (40, 40, 50)
STORE_COLOR: tuple[int, int, int] = (225, 170, 60)
STORE_ACTIVE_COLOR: tuple[int, int, int] = (90, 220, 120)
STORE_INTERACTION_RANGE: float = 120.0


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


def create_store() -> Store:
    """Crea una tienda con inventario inicial para la demo."""
    starter_items: list[Item] = [
        Item(
            "Elixir Vital",
            description="Recupera vida al usarse.",
            buy_price=45.0,
            sell_price=22.0,
            damage=35.0,
        ),
        Item(
            "Pocion de Furia",
            description="Aumenta el dano de ataque.",
            buy_price=50.0,
            sell_price=25.0,
            attack_boost=6.0,
        ),
        Item(
            "Escudo Reforzado",
            description="Aumenta defensa base.",
            buy_price=38.0,
            sell_price=19.0,
            defense_boost=4.0,
        ),
    ]
    return Store(position=Vector2D(560.0, GROUND_Y), items=starter_items)


def describe_item_effect(item: Item) -> str:
    """Retorna un texto corto con el efecto principal de un item."""
    effect_parts: list[str] = []
    if item.damage > 0:
        effect_parts.append(f"cura +{int(item.damage)}")
    if item.attack_boost > 0:
        effect_parts.append(f"ATK +{int(item.attack_boost)}")
    if item.defense_boost > 0:
        effect_parts.append(f"DEF +{int(item.defense_boost)}")
    return ", ".join(effect_parts) if effect_parts else "sin efecto"


def buy_selected_item(player: Player, store: Store, selected_index: int) -> tuple[str, int]:
    """Intenta comprar el item seleccionado de la tienda."""
    if not store.items:
        return "Tienda sin stock", 0

    clamped_index: int = max(0, min(selected_index, len(store.items) - 1))
    item: Item = store.items[clamped_index]
    if player.buy_item(item, store):
        if store.items:
            clamped_index = min(clamped_index, len(store.items) - 1)
        else:
            clamped_index = 0
        return f"Compraste {item.name} (-${int(item.buy_price)})", clamped_index

    if player.inventory.is_full:
        return "Inventario lleno", clamped_index
    if player.cash < item.buy_price:
        return f"No alcanza para {item.name}", clamped_index
    return "No se pudo realizar la compra", clamped_index


def sell_selected_item(player: Player, store: Store, selected_index: int) -> tuple[str, int]:
    """Intenta vender el item seleccionado del inventario."""
    if not player.inventory.items:
        return "No tienes items para vender", 0

    clamped_index: int = max(0, min(selected_index, len(player.inventory.items) - 1))
    item: Item = player.inventory.items[clamped_index]
    if player.sell_item(item, store):
        if player.inventory.items:
            clamped_index = min(clamped_index, len(player.inventory.items) - 1)
        else:
            clamped_index = 0
        return f"Vendiste {item.name} (+${int(item.sell_price)})", clamped_index

    return "No se pudo realizar la venta", clamped_index


def draw_store_dialog(
    screen: pygame.Surface,
    font_small: pygame.font.Font,
    font_medium: pygame.font.Font,
    store: Store,
    player: Player,
    active_tab: str,
    buy_index: int,
    sell_index: int,
) -> None:
    """Dibuja un cuadro de dialogo de tienda con seleccion de compra/venta."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    panel_width: int = 860
    panel_height: int = 470
    panel_x: int = (SCREEN_WIDTH - panel_width) // 2
    panel_y: int = (SCREEN_HEIGHT - panel_height) // 2
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, (26, 31, 45), panel_rect, border_radius=12)
    pygame.draw.rect(screen, (220, 180, 90), panel_rect, width=2, border_radius=12)

    title = render_text_with_background(
        font_medium,
        "TIENDA - Elige que comprar o vender",
        (255, 230, 140),
        (26, 31, 45),
    )
    screen.blit(title, (panel_x + 20, panel_y + 14))

    cash_text = render_text_with_background(
        font_small,
        f"Dinero: ${player.cash}",
        (240, 210, 120),
        (26, 31, 45),
    )
    screen.blit(cash_text, (panel_x + panel_width - cash_text.get_width() - 20, panel_y + 14))

    buy_header_color = (120, 240, 150) if active_tab == "buy" else (170, 170, 170)
    sell_header_color = (120, 240, 150) if active_tab == "sell" else (170, 170, 170)
    buy_header = render_text_with_background(font_medium, "COMPRA", buy_header_color, (26, 31, 45))
    sell_header = render_text_with_background(font_medium, "VENTA", sell_header_color, (26, 31, 45))
    screen.blit(buy_header, (panel_x + 26, panel_y + 56))
    screen.blit(sell_header, (panel_x + panel_width // 2 + 20, panel_y + 56))

    buy_items = store.items[:10]
    sell_items = player.inventory.items[:10]

    buy_start_y: int = panel_y + 92
    for idx, item in enumerate(buy_items):
        selected: bool = active_tab == "buy" and idx == buy_index
        prefix: str = "> " if selected else "  "
        color = (255, 245, 200) if selected else (210, 210, 210)
        line = f"{prefix}{item.name}  ${int(item.buy_price)}  ({describe_item_effect(item)})"
        line_surface = render_text_with_background(font_small, line, color, (38, 44, 60))
        screen.blit(line_surface, (panel_x + 18, buy_start_y + idx * 30))
    if not buy_items:
        line_surface = render_text_with_background(font_small, "Sin stock disponible", (210, 140, 140), (38, 44, 60))
        screen.blit(line_surface, (panel_x + 18, buy_start_y))

    sell_start_y: int = panel_y + 92
    for idx, item in enumerate(sell_items):
        selected = active_tab == "sell" and idx == sell_index
        prefix = "> " if selected else "  "
        color = (255, 245, 200) if selected else (210, 210, 210)
        line = f"{prefix}{item.name}  +${int(item.sell_price)}  ({describe_item_effect(item)})"
        line_surface = render_text_with_background(font_small, line, color, (38, 44, 60))
        screen.blit(line_surface, (panel_x + panel_width // 2 + 12, sell_start_y + idx * 30))
    if not sell_items:
        line_surface = render_text_with_background(font_small, "Inventario vacio", (210, 140, 140), (38, 44, 60))
        screen.blit(line_surface, (panel_x + panel_width // 2 + 12, sell_start_y))

    help_text = render_text_with_background(
        font_small,
        "TAB cambia panel | Arriba/Abajo seleccionan | ENTER confirma | ESC o E cierra",
        (170, 200, 255),
        (26, 31, 45),
    )
    screen.blit(help_text, (panel_x + 20, panel_y + panel_height - 38))


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
    hud: HUD = HUD(screen=screen, player=player)
    store: Store = create_store()
    player_vy: float = 0.0  # velocidad vertical para gravedad
    on_ground: bool = True
    player_facing: Vector2D = Vector2D(1.0, 0.0)
    projectiles: list[Proyectile] = []
    messages: list[tuple[str, float]] = []  # (texto, tiempo_restante)
    game_over: bool = False
    store_dialog_open: bool = False
    store_dialog_tab: str = "buy"
    store_buy_index: int = 0
    store_sell_index: int = 0

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
        is_near_store: bool = (
            player.position.distance_to(store.position) <= STORE_INTERACTION_RANGE
        )
        if store.items:
            store_buy_index = max(0, min(store_buy_index, len(store.items) - 1))
        else:
            store_buy_index = 0
        if player.inventory.items:
            store_sell_index = max(0, min(store_sell_index, len(player.inventory.items) - 1))
        else:
            store_sell_index = 0

        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if store_dialog_open:
                        store_dialog_open = False
                    else:
                        is_running = False
                elif event.key == pygame.K_e and not game_over:
                    if not is_near_store:
                        messages.append(("Acercate a la tienda para abrir dialogo", 1.2))
                    else:
                        store_dialog_open = not store_dialog_open
                        if store_dialog_open:
                            store_dialog_tab = "buy"
                            store_buy_index = 0
                            store_sell_index = 0
                elif store_dialog_open:
                    if event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
                        store_dialog_tab = "sell" if store_dialog_tab == "buy" else "buy"
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if store_dialog_tab == "buy" and store.items:
                            store_buy_index = (store_buy_index - 1) % len(store.items)
                        elif store_dialog_tab == "sell" and player.inventory.items:
                            store_sell_index = (store_sell_index - 1) % len(player.inventory.items)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if store_dialog_tab == "buy" and store.items:
                            store_buy_index = (store_buy_index + 1) % len(store.items)
                        elif store_dialog_tab == "sell" and player.inventory.items:
                            store_sell_index = (store_sell_index + 1) % len(player.inventory.items)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if store_dialog_tab == "buy":
                            result_text, store_buy_index = buy_selected_item(player, store, store_buy_index)
                            messages.append((result_text, 1.4))
                        else:
                            result_text, store_sell_index = sell_selected_item(player, store, store_sell_index)
                            messages.append((result_text, 1.4))
                elif event.key == pygame.K_SPACE and game_over:
                    # Reiniciar
                    world.generate(
                        seed=frame_count,
                        collectible_count=12,
                        enemy_count=3,
                    )
                    world.enemies = generate_enemies_from_image(screen, world.enemy_spawn_points)
                    player = create_player(screen)
                    hud.player = player
                    store = create_store()
                    player_vy = 0.0
                    on_ground = True
                    player_facing = Vector2D(1.0, 0.0)
                    projectiles.clear()
                    messages.clear()
                    game_over = False
                    store_dialog_open = False
                    store_dialog_tab = "buy"
                    store_buy_index = 0
                    store_sell_index = 0
                elif event.key == pygame.K_SPACE and not game_over:
                    world.generate(
                        seed=frame_count,
                        collectible_count=12,
                        enemy_count=3,
                    )
                    # Generar enemigos usando la imagen
                    world.enemies = generate_enemies_from_image(screen, world.enemy_spawn_points)
                    player = create_player(screen)
                    hud.player = player
                    store = create_store()
                    player_vy = 0.0
                    on_ground = True
                    player_facing = Vector2D(1.0, 0.0)
                    projectiles.clear()
                    messages.clear()
                    store_dialog_open = False
                    store_dialog_tab = "buy"
                    store_buy_index = 0
                    store_sell_index = 0
                elif event.key in (pygame.K_UP, pygame.K_w) and on_ground and not store_dialog_open:
                    player_vy = JUMP_FORCE
                    on_ground = False
                elif event.key == pygame.K_f and not store_dialog_open:
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
                            shield_hp = result.get("shield_hp", 50.0)
                            player.shield_hp = min(
                                player.shield_hp + shield_hp,
                                player.shield_max_hp + shield_hp,
                            )
                            player.shield_max_hp = player.shield_hp
                            player.trigger_shield_pickup_effect()
                            messages.append((f"+{shield_hp:.0f} SC (Escudo)", 2.0))
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

        # Dibujar tienda con offset de camara
        store_screen_x: int = int(store.position.x - world.camera.offset.x)
        store_screen_y: int = int(store.position.y)
        store_rect = pygame.Rect(store_screen_x - 26, store_screen_y - 72, 52, 72)
        store_color = STORE_ACTIVE_COLOR if is_near_store else STORE_COLOR
        pygame.draw.rect(screen, store_color, store_rect, border_radius=8)
        pygame.draw.rect(screen, (20, 20, 20), store_rect, width=2, border_radius=8)
        sign_surface = font_small.render("STORE", True, (20, 20, 20))
        screen.blit(sign_surface, (store_screen_x - sign_surface.get_width() // 2, store_screen_y - 92))
        if is_near_store:
            pygame.draw.circle(
                screen,
                (120, 255, 160),
                (store_screen_x, store_screen_y - 36),
                int(STORE_INTERACTION_RANGE * 0.35),
                width=2,
            )

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

        # HUD del jugador (barras de HP/XP, nivel, dinero, inventario)
        hud.draw()

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

        # Panel de información (debajo del HUD)
        info_y: int = 110
        info_x: int = 10

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

        # Estado de tienda
        store_state_text = "TIENDA: EN RANGO" if is_near_store else "Tienda: fuera de rango"
        store_state_color = (100, 255, 140) if is_near_store else (200, 180, 120)
        screen.blit(
            render_text_with_background(font_small, store_state_text, store_state_color, UI_BG_COLOR),
            (info_x, info_y),
        )
        info_y += 20

        next_item_text = (
            f"Siguiente compra: {store.items[0].name} (${int(store.items[0].buy_price)})"
            if store.items
            else "Siguiente compra: sin stock"
        )
        screen.blit(
            render_text_with_background(font_small, next_item_text, (245, 210, 100), UI_BG_COLOR),
            (info_x, info_y),
        )
        info_y += 20

        inventory_text = f"Inventario: {len(player.inventory.items)}/{player.inventory.capacity}"
        screen.blit(
            render_text_with_background(font_small, inventory_text, (180, 220, 255), UI_BG_COLOR),
            (info_x, info_y),
        )
        info_y += 24

        # Instrucciones
        instructions: str = "WASD/flechas: mover | W/arriba: saltar | F: disparar | B: comprar | V: vender | ESPACIO: regenerar | ESC: salir"
        if store_dialog_open:
            instructions = "TIENDA ABIERTA: TAB cambia panel | Arriba/Abajo selecciona | ENTER confirma | E/ESC cierra"
        else:
            instructions = "WASD/flechas: mover | W/arriba: saltar | F: disparar | E: tienda | ESPACIO: regenerar | ESC: salir"
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

        if store_dialog_open and not game_over:
            draw_store_dialog(
                screen,
                font_small,
                font_medium,
                store,
                player,
                active_tab=store_dialog_tab,
                buy_index=store_buy_index,
                sell_index=store_sell_index,
            )

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
