from __future__ import annotations

import sys

import pygame

from combat.combat_system import CombatSystem
from combat.shield import Shield
from core.vector2d import Vector2D
from entities.bossenemy import BossEnemy
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


class GameManager:
    """Orquesta el bucle de juego, progreso, UI y condiciones de victoria."""

    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    TARGET_FPS: int = 60

    BACKGROUND_COLOR: tuple[int, int, int] = (135, 206, 235)
    UI_COLOR: tuple[int, int, int] = (200, 200, 200)
    UI_BG_COLOR: tuple[int, int, int] = (40, 40, 50)
    STORE_COLOR: tuple[int, int, int] = (225, 170, 60)
    STORE_ACTIVE_COLOR: tuple[int, int, int] = (90, 220, 120)

    PLAYER_SPEED: float = 320.0
    AIR_CONTROL_MULTIPLIER: float = 1.5
    GROUND_ACCELERATION: float = 3600.0
    AIR_ACCELERATION: float = 1800.0
    GROUND_DRAG: float = 2200.0
    AIR_DRAG: float = 700.0
    GRAVITY: float = 800.0
    JUMP_FORCE: float = -380.0
    GROUND_Y: float = 510.0
    VOID_Y_MARGIN: float = 180.0
    STORE_INTERACTION_RANGE: float = 120.0
    STORE_UNLOCK_CASH: int = 200

    VICTORY_CAMERA_X: float = 7000.0
    BOSS_SPAWN_OFFSET_X: float = 1800.0
    WORLD_BASE_SCROLL_SPEED: float = 200.0
    TOTAL_ENEMIES_BEFORE_BOSS: int = 20

    # world_speed_multiplier, enemy_damage_multiplier, boss_damage_multiplier, enemy_spawn_interval
    DIFFICULTY_SETTINGS: dict[str, dict[str, float]] = {
        "facil": {
            "world_speed_multiplier": 0.8,
            "enemy_damage_multiplier": 0.7,
            "boss_damage_multiplier": 0.7,
            "enemy_spawn_interval": 2.0,
        },
        "media": {
            "world_speed_multiplier": 1.0,
            "enemy_damage_multiplier": 1.0,
            "boss_damage_multiplier": 1.0,
            "enemy_spawn_interval": 1.2,
        },
        "dificil": {
            "world_speed_multiplier": 1.25,
            "enemy_damage_multiplier": 1.35,
            "boss_damage_multiplier": 1.35,
            "enemy_spawn_interval": 0.7,
        },
    }
    DIFFICULTY_ORDER: tuple[str, str, str] = ("facil", "media", "dificil")
    DIFFICULTY_DESCRIPTIONS: dict[str, str] = {
        "facil": "Menos enemigos, mundo mas lento y dano bajo.",
        "media": "Balance estandar para una partida normal.",
        "dificil": "Mas enemigos, mundo rapido y dano alto.",
    }

    def __init__(self, screen: pygame.Surface | None = None) -> None:
        pygame.init()
        self.screen: pygame.Surface = (
            screen
            if screen is not None
            else pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        )
        pygame.display.set_caption("Game - LPA1 Taller Videojuegos")

        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_playing: bool = True
        self.frame_count: int = 0
        self.score: float = 0.0
        self.exploration_pct: float = 0.0

        self.world: World = World(screen=self.screen)
        self.player: Player = self._create_player()
        self.hud: HUD = HUD(screen=self.screen, player=self.player)
        self.store: Store = self._create_store()

        self.player_vy: float = 0.0
        self.player_vx: float = 0.0
        self.on_ground: bool = True
        self.player_facing: Vector2D = Vector2D(1.0, 0.0)
        self.projectiles: list[Proyectile] = []
        self.boss_projectiles: list[Proyectile] = []
        self.boss_enemy: BossEnemy | None = None
        self.messages: list[tuple[str, float]] = []
        self.game_over: bool = False
        self.paused: bool = False
        self.current_difficulty: str = "media"
        self.difficulty_menu_active: bool = False
        self._difficulty_selection_pending: bool = True
        self._difficulty_selected_index: int = self.DIFFICULTY_ORDER.index(
            self.current_difficulty
        )
        self.enemy_count_for_run: int = self.TOTAL_ENEMIES_BEFORE_BOSS
        self.enemy_damage_multiplier: float = self.DIFFICULTY_SETTINGS[
            self.current_difficulty
        ]["enemy_damage_multiplier"]
        self.boss_damage_multiplier: float = self.DIFFICULTY_SETTINGS[
            self.current_difficulty
        ]["boss_damage_multiplier"]
        self.enemy_spawn_interval: float = self.DIFFICULTY_SETTINGS[
            self.current_difficulty
        ]["enemy_spawn_interval"]
        self.enemy_spawn_timer: float = 0.0
        self.pending_enemy_pool: list[object] = []
        self.spawned_enemy_total: int = 0
        self.boss_spawned: bool = False

        self.store_dialog_open: bool = False
        self.store_dialog_tab: str = "buy"
        self.store_buy_index: int = 0
        self.store_sell_index: int = 0
        self.store_unlocked: bool = False
        self._store_unlock_announced: bool = False

        self.font_small: pygame.font.Font = pygame.font.Font(None, 20)
        self.font_medium: pygame.font.Font = pygame.font.Font(None, 24)

        self.game_over_image: pygame.Surface = pygame.image.load("public/assets/game-over.png")
        self.game_over_image = pygame.transform.scale(self.game_over_image, (400, 300))

        self._apply_difficulty_settings()
        self.start_game(seed=2026)

    # ------------------------------------------------------------------
    # Inicializacion y utilidades
    # ------------------------------------------------------------------

    def _create_player(self) -> Player:
        return Player(
            self.screen,
            Vector2D(200.0, self.GROUND_Y),
            "Hero",
            cash=100,
            stats=Stats(max_health=100.0, damage=15.0, defense=5.0),
        )

    def _create_store(self) -> Store:
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
        return Store(position=Vector2D(560.0, self.GROUND_Y), items=starter_items)

    def _render_text_with_background(
        self,
        text: str,
        color: tuple[int, int, int],
        bg_color: tuple[int, int, int],
        *,
        font: pygame.font.Font | None = None,
        padding: int = 4,
    ) -> pygame.Surface:
        active_font: pygame.font.Font = font if font is not None else self.font_small
        text_surface: pygame.Surface = active_font.render(text, True, color)
        text_rect: pygame.Rect = text_surface.get_rect()
        bg_surface: pygame.Surface = pygame.Surface(
            (text_rect.width + padding * 2, text_rect.height + padding * 2)
        )
        bg_surface.fill(bg_color)
        bg_surface.blit(text_surface, (padding, padding))
        return bg_surface

    def _describe_item_effect(self, item: Item) -> str:
        effect_parts: list[str] = []
        if item.damage > 0:
            effect_parts.append(f"cura +{int(item.damage)}")
        if item.attack_boost > 0:
            effect_parts.append(f"ATK +{int(item.attack_boost)}")
        if item.defense_boost > 0:
            effect_parts.append(f"DEF +{int(item.defense_boost)}")
        return ", ".join(effect_parts) if effect_parts else "sin efecto"

    def _resolve_platform_landing(self, previous_y: float) -> None:
        """Resuelve aterrizaje sobre plataformas al caer."""
        self.on_ground = False
        if self.player_vy < 0:
            return

        previous_bottom: float = previous_y + self.player.radius
        current_bottom: float = self.player.position.y + self.player.radius

        best_top: float | None = None
        horizontal_margin: float = self.player.radius * 0.4

        for platform in self.world.platforms:
            within_x = (
                (platform.x - horizontal_margin)
                <= self.player.position.x
                <= (platform.x + platform.width + horizontal_margin)
            )
            if not within_x:
                continue

            platform_top: float = platform.y
            crossed_top = previous_bottom <= platform_top <= current_bottom
            if not crossed_top:
                continue

            if best_top is None or platform_top < best_top:
                best_top = platform_top

        if best_top is not None:
            self.player.position.y = best_top - self.player.radius
            self.player_vy = 0.0
            self.on_ground = True

    def _update_store_unlock_state(self) -> None:
        """Desbloquea tienda al alcanzar el umbral de dinero."""
        if self.store_unlocked:
            return
        if self.player.cash >= self.STORE_UNLOCK_CASH:
            self.store_unlocked = True
            if not self._store_unlock_announced:
                self.messages.append(("Tienda desbloqueada!", 1.8))
                self._store_unlock_announced = True

    def _apply_difficulty_settings(self) -> None:
        settings = self.DIFFICULTY_SETTINGS[self.current_difficulty]
        self.enemy_count_for_run = self.TOTAL_ENEMIES_BEFORE_BOSS
        self.enemy_damage_multiplier = settings["enemy_damage_multiplier"]
        self.boss_damage_multiplier = settings["boss_damage_multiplier"]
        self.enemy_spawn_interval = settings["enemy_spawn_interval"]
        world_speed_multiplier = settings["world_speed_multiplier"]
        self.world.camera.scroll_speed = self.WORLD_BASE_SCROLL_SPEED * world_speed_multiplier

    def _create_boss_enemy(self) -> BossEnemy:
        return BossEnemy(
            self.screen,
            Vector2D(
                self.world.camera.offset.x + self.SCREEN_WIDTH + self.BOSS_SPAWN_OFFSET_X,
                self.GROUND_Y,
            ),
            "Boss Prime",
            attack_power=25.0 * self.boss_damage_multiplier,
        )

    def _update_enemy_spawning(self, dt: float) -> None:
        """Spawnea enemigos progresivamente según dificultad y luego habilita el boss."""
        if self.pending_enemy_pool:
            self.enemy_spawn_timer += dt
            while self.enemy_spawn_timer >= self.enemy_spawn_interval and self.pending_enemy_pool:
                self.enemy_spawn_timer -= self.enemy_spawn_interval
                enemy = self.pending_enemy_pool.pop(0)
                self.world.enemies.append(enemy)
                self.spawned_enemy_total += 1
            return

        if self.boss_spawned:
            return

        if any(not enemy.is_defeated for enemy in self.world.enemies):
            return

        self.boss_enemy = self._create_boss_enemy()
        self.boss_spawned = True
        self.messages.append(("Boss detectado!", 2.0))

    def set_difficulty(self, difficulty: str, *, restart: bool = True) -> None:
        """Configura la dificultad actual y opcionalmente reinicia la partida."""
        normalized = difficulty.strip().lower()
        if normalized not in self.DIFFICULTY_SETTINGS:
            raise ValueError("difficulty debe ser: facil, media o dificil")

        self.current_difficulty = normalized
        self._apply_difficulty_settings()
        self.messages.append((f"Dificultad: {normalized.upper()}", 1.8))
        if restart:
            self.start_game(seed=self.frame_count)

    def _confirm_difficulty_selection(self, difficulty: str) -> None:
        """Confirma dificultad elegida desde el menú inicial y arranca partida."""
        self.set_difficulty(difficulty, restart=False)
        self.difficulty_menu_active = False
        self._difficulty_selection_pending = False
        seed = 2026 if self.frame_count == 0 else self.frame_count
        self.start_game(seed=seed)

    def _snap_player_to_spawn_platform(self) -> None:
        """Posiciona al jugador sobre una plataforma válida al iniciar."""
        if not self.world.platforms:
            self.player.position.y = self.GROUND_Y
            self.on_ground = True
            self.player_vy = 0.0
            return

        horizontal_margin: float = self.player.radius * 0.4
        supporting_platforms = [
            platform
            for platform in self.world.platforms
            if (platform.x - horizontal_margin)
            <= self.player.position.x
            <= (platform.x + platform.width + horizontal_margin)
        ]

        if supporting_platforms:
            spawn_platform = min(supporting_platforms, key=lambda p: p.y)
        else:
            # Fallback: usa la plataforma más cercana en X.
            spawn_platform = min(
                self.world.platforms,
                key=lambda p: abs((p.x + p.width * 0.5) - self.player.position.x),
            )
            self.player.position.x = spawn_platform.x + spawn_platform.width * 0.5

        self.player.position.y = spawn_platform.y - self.player.radius
        self.on_ground = True
        self.player_vy = 0.0

    def start_game(self, seed: int | None = None) -> None:
        """Inicializa o reinicia una partida completa."""
        self.world.dynamic_enemy_spawn_enabled = False
        self.world.dynamic_collectible_spawn_enabled = True
        self.world.generate(
            seed=seed,
            collectible_count=12,
            enemy_count=self.enemy_count_for_run,
        )
        self.world.enemies = generate_enemies_from_image(
            self.screen,
            self.world.enemy_spawn_points,
        )

        for enemy in self.world.enemies:
            enemy.attack_power *= self.enemy_damage_multiplier

        self.pending_enemy_pool = list(self.world.enemies)
        self.world.enemies = []
        self.enemy_spawn_timer = 0.0
        self.spawned_enemy_total = 0

        self.player = self._create_player()
        self._snap_player_to_spawn_platform()
        self.hud.player = self.player
        self.store = self._create_store()
        self.boss_enemy = None
        self.boss_spawned = False

        self.player_vy = 0.0
        self.player_vx = 0.0
        self.on_ground = True
        self.player_facing = Vector2D(1.0, 0.0)
        self.projectiles.clear()
        self.boss_projectiles.clear()
        self.messages.clear()
        self.game_over = False
        self.paused = False

        self.store_dialog_open = False
        self.store_dialog_tab = "buy"
        self.store_buy_index = 0
        self.store_sell_index = 0
        self.store_unlocked = self.player.cash >= self.STORE_UNLOCK_CASH
        self._store_unlock_announced = self.store_unlocked

    # ------------------------------------------------------------------
    # Tienda
    # ------------------------------------------------------------------

    def _buy_selected_item(self, selected_index: int) -> tuple[str, int]:
        if not self.store.items:
            return "Tienda sin stock", 0

        clamped_index: int = max(0, min(selected_index, len(self.store.items) - 1))
        item: Item = self.store.items[clamped_index]
        if self.player.buy_item(item, self.store):
            if self.store.items:
                clamped_index = min(clamped_index, len(self.store.items) - 1)
            else:
                clamped_index = 0
            return f"Compraste {item.name} (-${int(item.buy_price)})", clamped_index

        if self.player.inventory.is_full:
            return "Inventario lleno", clamped_index
        if self.player.cash < item.buy_price:
            return f"No alcanza para {item.name}", clamped_index
        return "No se pudo realizar la compra", clamped_index

    def _sell_selected_item(self, selected_index: int) -> tuple[str, int]:
        if not self.player.inventory.items:
            return "No tienes items para vender", 0

        clamped_index: int = max(
            0,
            min(selected_index, len(self.player.inventory.items) - 1),
        )
        item: Item = self.player.inventory.items[clamped_index]
        if self.player.sell_item(item, self.store):
            if self.player.inventory.items:
                clamped_index = min(clamped_index, len(self.player.inventory.items) - 1)
            else:
                clamped_index = 0
            return f"Vendiste {item.name} (+${int(item.sell_price)})", clamped_index

        return "No se pudo realizar la venta", clamped_index

    def _use_selected_inventory_item(self, selected_index: int) -> tuple[str, int]:
        if not self.player.inventory.items:
            return "Inventario vacio", 0

        clamped_index: int = max(
            0,
            min(selected_index, len(self.player.inventory.items) - 1),
        )
        item: Item = self.player.inventory.items[clamped_index]
        if self.player.use_item(item):
            if self.player.inventory.items:
                clamped_index = min(clamped_index, len(self.player.inventory.items) - 1)
            else:
                clamped_index = 0
            return f"Usaste {item.name}", clamped_index

        return f"No se pudo usar {item.name}", clamped_index

    def _draw_store_dialog(self, *, remote_mode: bool = False) -> None:
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        panel_width: int = 860
        panel_height: int = 470
        panel_x: int = (self.SCREEN_WIDTH - panel_width) // 2
        panel_y: int = (self.SCREEN_HEIGHT - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (26, 31, 45), panel_rect, border_radius=12)
        pygame.draw.rect(
            self.screen,
            (220, 180, 90),
            panel_rect,
            width=2,
            border_radius=12,
        )

        title_text = (
            "TIENDA REMOTA - Elige que comprar o vender"
            if remote_mode
            else "TIENDA - Elige que comprar o vender"
        )
        title_color = (255, 210, 140) if remote_mode else (255, 230, 140)
        title = self._render_text_with_background(
            title_text,
            title_color,
            (26, 31, 45),
            font=self.font_medium,
        )
        self.screen.blit(title, (panel_x + 20, panel_y + 14))

        cash_text = self._render_text_with_background(
            f"Dinero: ${self.player.cash}",
            (240, 210, 120),
            (26, 31, 45),
        )
        self.screen.blit(
            cash_text,
            (panel_x + panel_width - cash_text.get_width() - 20, panel_y + 14),
        )

        buy_header_color = (120, 240, 150) if self.store_dialog_tab == "buy" else (170, 170, 170)
        sell_header_color = (120, 240, 150) if self.store_dialog_tab == "sell" else (170, 170, 170)

        buy_header = self._render_text_with_background(
            "COMPRA", buy_header_color, (26, 31, 45), font=self.font_medium
        )
        sell_header = self._render_text_with_background(
            "VENTA", sell_header_color, (26, 31, 45), font=self.font_medium
        )
        self.screen.blit(buy_header, (panel_x + 26, panel_y + 56))
        self.screen.blit(sell_header, (panel_x + panel_width // 2 + 20, panel_y + 56))

        buy_items = self.store.items[:10]
        sell_items = self.player.inventory.items[:10]

        buy_start_y: int = panel_y + 92
        for idx, item in enumerate(buy_items):
            selected: bool = self.store_dialog_tab == "buy" and idx == self.store_buy_index
            prefix: str = "> " if selected else "  "
            color = (255, 245, 200) if selected else (210, 210, 210)
            line = f"{prefix}{item.name}  ${int(item.buy_price)}  ({self._describe_item_effect(item)})"
            line_surface = self._render_text_with_background(line, color, (38, 44, 60))
            self.screen.blit(line_surface, (panel_x + 18, buy_start_y + idx * 30))

        if not buy_items:
            line_surface = self._render_text_with_background(
                "Sin stock disponible",
                (210, 140, 140),
                (38, 44, 60),
            )
            self.screen.blit(line_surface, (panel_x + 18, buy_start_y))

        sell_start_y: int = panel_y + 92
        for idx, item in enumerate(sell_items):
            selected = self.store_dialog_tab == "sell" and idx == self.store_sell_index
            prefix = "> " if selected else "  "
            color = (255, 245, 200) if selected else (210, 210, 210)
            line = f"{prefix}{item.name}  +${int(item.sell_price)}  ({self._describe_item_effect(item)})"
            line_surface = self._render_text_with_background(line, color, (38, 44, 60))
            self.screen.blit(
                line_surface,
                (panel_x + panel_width // 2 + 12, sell_start_y + idx * 30),
            )

        if not sell_items:
            line_surface = self._render_text_with_background(
                "Inventario vacio",
                (210, 140, 140),
                (38, 44, 60),
            )
            self.screen.blit(line_surface, (panel_x + panel_width // 2 + 12, sell_start_y))

        help_text = self._render_text_with_background(
            "TAB cambia panel | Arriba/Abajo seleccionan | ENTER compra/vende | U usa item | ESC o E cierra",
            (170, 200, 255),
            (26, 31, 45),
        )
        self.screen.blit(help_text, (panel_x + 20, panel_y + panel_height - 38))

    def _draw_victory_banner(self) -> None:
        """Dibuja un cartel de victoria con resumen final de la partida."""
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        panel_width: int = 560
        panel_height: int = 290
        panel_x: int = (self.SCREEN_WIDTH - panel_width) // 2
        panel_y: int = (self.SCREEN_HEIGHT - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (22, 30, 36), panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, (120, 255, 160), panel_rect, width=3, border_radius=16)

        title = self._render_text_with_background(
            "HAS GANADO LA PARTIDA",
            (150, 255, 170),
            (22, 30, 36),
            font=self.font_medium,
            padding=6,
        )
        self.screen.blit(
            title,
            (self.SCREEN_WIDTH // 2 - title.get_width() // 2, panel_y + 24),
        )

        defeated_count: int = sum(1 for enemy in self.world.enemies if enemy.is_defeated)
        summary_lines: list[tuple[str, tuple[int, int, int]]] = [
            (f"Enemigos vencidos: {defeated_count}", (255, 220, 140)),
            (f"Experiencia obtenida: {self.player.stats.experience:.0f}", (200, 170, 255)),
            (f"Dinero obtenido: ${self.player.cash}", (255, 230, 120)),
            (f"Score final: {self.score:.0f}", (180, 220, 255)),
        ]

        line_y: int = panel_y + 92
        for text, color in summary_lines:
            line_surface = self._render_text_with_background(
                text,
                color,
                (30, 40, 48),
                font=self.font_medium,
            )
            self.screen.blit(
                line_surface,
                (self.SCREEN_WIDTH // 2 - line_surface.get_width() // 2, line_y),
            )
            line_y += 42

        restart_text = self._render_text_with_background(
            "Presiona ESPACIO para volver a empezar",
            (235, 235, 235),
            (22, 30, 36),
        )
        self.screen.blit(
            restart_text,
            (
                self.SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                panel_y + panel_height - 44,
            ),
        )

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def handle_event(self) -> None:
        """Procesa entrada de teclado/ventana y acciones de UI."""
        self._update_store_unlock_state()
        is_near_store: bool = (
            self.store_unlocked
            and
            self.player.position.distance_to(self.store.position)
            <= self.STORE_INTERACTION_RANGE
        )

        if self.store.items:
            self.store_buy_index = max(0, min(self.store_buy_index, len(self.store.items) - 1))
        else:
            self.store_buy_index = 0

        if self.player.inventory.items:
            self.store_sell_index = max(
                0,
                min(self.store_sell_index, len(self.player.inventory.items) - 1),
            )
        else:
            self.store_sell_index = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_playing = False
            elif event.type == pygame.KEYDOWN:
                if self.difficulty_menu_active:
                    if event.key == pygame.K_ESCAPE:
                        self.is_playing = False
                    elif event.key in (pygame.K_1, pygame.K_KP1):
                        self._difficulty_selected_index = 0
                        self._confirm_difficulty_selection("facil")
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self._difficulty_selected_index = 1
                        self._confirm_difficulty_selection("media")
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self._difficulty_selected_index = 2
                        self._confirm_difficulty_selection("dificil")
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self._difficulty_selected_index = (
                            self._difficulty_selected_index - 1
                        ) % len(self.DIFFICULTY_ORDER)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._difficulty_selected_index = (
                            self._difficulty_selected_index + 1
                        ) % len(self.DIFFICULTY_ORDER)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        selected = self.DIFFICULTY_ORDER[self._difficulty_selected_index]
                        self._confirm_difficulty_selection(selected)
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.store_dialog_open:
                        self.store_dialog_open = False
                    else:
                        self.is_playing = False
                elif event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                elif event.key == pygame.K_e and not self.game_over:
                    self.store_dialog_open = not self.store_dialog_open
                    if self.store_dialog_open:
                        self.store_dialog_tab = "buy"
                        self.store_buy_index = 0
                        self.store_sell_index = 0
                elif self.store_dialog_open:
                    if event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
                        self.store_dialog_tab = "sell" if self.store_dialog_tab == "buy" else "buy"
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if self.store_dialog_tab == "buy" and self.store.items:
                            self.store_buy_index = (self.store_buy_index - 1) % len(self.store.items)
                        elif self.store_dialog_tab == "sell" and self.player.inventory.items:
                            self.store_sell_index = (
                                (self.store_sell_index - 1) % len(self.player.inventory.items)
                            )
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if self.store_dialog_tab == "buy" and self.store.items:
                            self.store_buy_index = (self.store_buy_index + 1) % len(self.store.items)
                        elif self.store_dialog_tab == "sell" and self.player.inventory.items:
                            self.store_sell_index = (
                                (self.store_sell_index + 1) % len(self.player.inventory.items)
                            )
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if self.store_dialog_tab == "buy":
                            result_text, self.store_buy_index = self._buy_selected_item(self.store_buy_index)
                            self.messages.append((result_text, 1.4))
                        else:
                            result_text, self.store_sell_index = self._sell_selected_item(self.store_sell_index)
                            self.messages.append((result_text, 1.4))
                    elif event.key == pygame.K_u:
                        if self.store_dialog_tab == "sell":
                            result_text, self.store_sell_index = self._use_selected_inventory_item(self.store_sell_index)
                            self.messages.append((result_text, 1.4))
                        else:
                            self.messages.append(("Cambia a VENTA para usar items", 1.2))
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self.set_difficulty("facil", restart=True)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.set_difficulty("media", restart=True)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.set_difficulty("dificil", restart=True)
                elif event.key == pygame.K_q and not self.game_over:
                    result_text, _ = self._use_selected_inventory_item(0)
                    self.messages.append((result_text, 1.2))
                elif event.key == pygame.K_SPACE:
                    self.start_game(seed=self.frame_count)

    def update(self, dt: float) -> None:
        """Actualiza estado de mundo, jugador y combate."""
        if self.difficulty_menu_active:
            return
        if self.game_over:
            return
        if self.paused:
            return
        if self.store_dialog_open:
            return

        self._update_enemy_spawning(dt)

        self.frame_count += 1

        keys = pygame.key.get_pressed()
        input_axis: float = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            input_axis -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            input_axis += 1.0

        move_speed: float = (
            self.PLAYER_SPEED
            if self.on_ground
            else self.PLAYER_SPEED * self.AIR_CONTROL_MULTIPLIER
        )

        acceleration: float = (
            self.GROUND_ACCELERATION if self.on_ground else self.AIR_ACCELERATION
        )
        drag: float = self.GROUND_DRAG if self.on_ground else self.AIR_DRAG

        if input_axis != 0.0:
            self.player_vx += input_axis * acceleration * dt
        elif self.player_vx > 0.0:
            self.player_vx = max(0.0, self.player_vx - drag * dt)
        elif self.player_vx < 0.0:
            self.player_vx = min(0.0, self.player_vx + drag * dt)

        self.player_vx = max(-move_speed, min(move_speed, self.player_vx))
        self.player.position.x += self.player_vx * dt

        viewport_left_world = self.world.camera.offset.x + self.player.radius
        viewport_right_world = (
            self.world.camera.offset.x + self.SCREEN_WIDTH - self.player.radius
        )
        if self.player.position.x < viewport_left_world:
            self.player.position.x = viewport_left_world
            self.player_vx = max(0.0, self.player_vx)
        elif self.player.position.x > viewport_right_world:
            self.player.position.x = viewport_right_world
            self.player_vx = min(0.0, self.player_vx)

        if self.player_vx < -1e-3:
            self.player_facing = Vector2D(-1.0, 0.0)
        elif self.player_vx > 1e-3:
            self.player_facing = Vector2D(1.0, 0.0)

        if (
            (keys[pygame.K_UP] or keys[pygame.K_w])
            and self.on_ground
            and not self.store_dialog_open
        ):
            self.player_vy = self.JUMP_FORCE
            self.on_ground = False

        if keys[pygame.K_f] and not self.store_dialog_open:
            now_seconds: float = pygame.time.get_ticks() / 1000.0
            projectile = self.player.shoot(self.player_facing, current_time=now_seconds)
            if projectile is not None:
                self.projectiles.append(projectile)

        previous_y: float = self.player.position.y
        self.player_vy += self.GRAVITY * dt
        self.player.position.y += self.player_vy * dt
        self._resolve_platform_landing(previous_y)

        void_limit_y: float = self.SCREEN_HEIGHT + self.VOID_Y_MARGIN
        if (self.player.position.y - self.player.radius) > void_limit_y:
            self.player.is_active = False
            self.game_over = True
            self.messages.append(("Caíste al vacío", 2.0))
            return

        for collectible in self.world.collectibles:
            if not collectible.is_active:
                continue
            if isinstance(collectible, Treasure):
                distance = self.player.position.distance_to(collectible.position)
                if distance < 50.0:
                    value = collectible.collect_value()
                    self.player.cash += int(value)
                    self._update_store_unlock_state()
                    self.player.trigger_treasure_pickup_effect()
                    self.messages.append((f"+${value:.0f} (Tesoro)", 2.0))
                    collectible.is_active = False
            elif self.player.colission(collectible):
                if isinstance(collectible, Shield):
                    result = collectible.activate()
                    shield_hp = result.get("shield_hp", 50.0)
                    self.player.shield_hp = min(
                        self.player.shield_hp + shield_hp,
                        self.player.shield_max_hp + shield_hp,
                    )
                    self.player.shield_max_hp = self.player.shield_hp
                    self.player.trigger_shield_pickup_effect()
                    self.messages.append((f"+{shield_hp:.0f} SC (Escudo)", 2.0))
                elif isinstance(collectible, Trap):
                    dmg = collectible.explode(self.player.position)
                    net = self.player.defend(dmg)
                    self.messages.append((f"-{net:.0f} HP (Trampa)", 2.0))
                collectible.is_active = False

        for enemy in self.world.enemies:
            if not enemy.is_defeated and enemy.attack_cooldown <= 0:
                distance = self.player.position.distance_to(enemy.position)
                if distance < 100.0:
                    combat_result = CombatSystem.resolve_combat(self.player, enemy)
                    enemy_damage = combat_result["enemy_damage"]
                    if enemy_damage > 0:
                        self.messages.append((f"-{enemy_damage:.0f} HP (Enemigo cercano)", 1.5))
                    enemy.attack_cooldown = 1.0

        if self.boss_enemy is not None and not self.boss_enemy.is_defeated:
            viewport_left_world = self.world.camera.offset.x + self.boss_enemy.radius
            viewport_right_world = (
                self.world.camera.offset.x + self.SCREEN_WIDTH - self.boss_enemy.radius
            )
            self.boss_enemy.ai_update(
                self.player,
                self.world.platforms,
                dt,
                ground_y=self.GROUND_Y,
                viewport_left=viewport_left_world,
                viewport_right=viewport_right_world,
            )

        if self.boss_enemy is not None and not self.boss_enemy.is_defeated:
            boss_projectile = self.boss_enemy.special_attack(
                self.player,
                current_time=pygame.time.get_ticks() / 1000.0,
            )
            if boss_projectile is not None:
                self.boss_projectiles.append(boss_projectile)

        for projectile in self.projectiles:
            if not projectile.is_active:
                continue
            projectile.update(dt)
            for enemy in self.world.enemies:
                if enemy.is_defeated:
                    continue
                hit_damage = projectile.hit(enemy)
                if hit_damage > 0:
                    self.messages.append((f"-{hit_damage:.0f} HP al enemigo", 1.0))
                    if enemy.is_defeated:
                        gained_levels = self.player.gain_experience(25.0)
                        if gained_levels > 0:
                            self.player.health = self.player.stats.max_health
                            self.messages.append((f"LEVEL UP x{gained_levels}!", 1.5))
                        else:
                            self.messages.append(("+25 XP", 1.0))

            if self.boss_enemy is not None and not self.boss_enemy.is_defeated:
                hit_damage = projectile.hit(self.boss_enemy)
                if hit_damage > 0:
                    self.messages.append((f"-{hit_damage:.0f} HP al boss", 1.0))
                    if self.boss_enemy.is_defeated:
                        gained_levels = self.player.gain_experience(100.0)
                        self.player.health = self.player.stats.max_health
                        self.messages.append((f"Boss derrotado! +{100:.0f} XP", 2.0))
                        if gained_levels > 0:
                            self.messages.append((f"LEVEL UP x{gained_levels}!", 1.5))

        for boss_projectile in self.boss_projectiles:
            if not boss_projectile.is_active:
                continue
            boss_projectile.update(dt)
            hit_damage = boss_projectile.hit(self.player)
            if hit_damage > 0:
                self.messages.append((f"-{hit_damage:.0f} HP (Proyectil Boss)", 1.0))

        self.projectiles = [p for p in self.projectiles if p.is_active]
        self.boss_projectiles = [p for p in self.boss_projectiles if p.is_active]
        self.messages = [(txt, t - dt) for txt, t in self.messages if t > 0]

        self.world.update(dt)
        self.player.set_motion_state(self.player_vx, self.on_ground)
        self.player.update(dt)

        defeated_count = sum(1 for enemy in self.world.enemies if enemy.is_defeated)
        self.score = defeated_count * 100.0 + self.player.stats.experience + self.player.cash
        self.exploration_pct = min(
            100.0,
            (self.world.camera.offset.x / self.VICTORY_CAMERA_X) * 100.0,
        )

        if not self.player.is_active:
            self.game_over = True

    def draw(self) -> None:
        """Renderiza mundo, entidades y capas de interfaz."""
        if self.difficulty_menu_active:
            self.screen.fill((18, 22, 34))

            title = self._render_text_with_background(
                "SELECCIONA DIFICULTAD",
                (245, 230, 160),
                (18, 22, 34),
                font=self.font_medium,
                padding=6,
            )
            self.screen.blit(
                title,
                (self.SCREEN_WIDTH // 2 - title.get_width() // 2, 140),
            )

            y_base: int = 240
            for i, difficulty in enumerate(self.DIFFICULTY_ORDER):
                selected = i == self._difficulty_selected_index
                marker = "> " if selected else "  "
                color = (120, 245, 160) if selected else (210, 210, 210)
                line = f"{marker}{i + 1}. {difficulty.upper()}"
                option = self._render_text_with_background(
                    line,
                    color,
                    (30, 36, 52),
                    font=self.font_medium,
                )
                self.screen.blit(
                    option,
                    (self.SCREEN_WIDTH // 2 - option.get_width() // 2, y_base + i * 52),
                )

                settings = self.DIFFICULTY_SETTINGS[difficulty]
                desc = self.DIFFICULTY_DESCRIPTIONS[difficulty]
                details = (
                    f"{desc} Enemigos: {self.TOTAL_ENEMIES_BEFORE_BOSS} | "
                    f"Vel mundo: x{settings['world_speed_multiplier']:.2f} | "
                    f"Spawn: {settings['enemy_spawn_interval']:.1f}s"
                )
                detail_surface = self._render_text_with_background(
                    details,
                    (150, 180, 210) if selected else (130, 145, 160),
                    (25, 30, 44),
                )
                self.screen.blit(
                    detail_surface,
                    (
                        self.SCREEN_WIDTH // 2 - detail_surface.get_width() // 2,
                        y_base + i * 52 + 30,
                    ),
                )

            menu_controls = self._render_text_with_background(
                "Menu: 1/2/3 selecciona | ARRIBA/ABAJO navega | ENTER confirma | ESC salir",
                (160, 190, 230),
                (18, 22, 34),
            )
            self.screen.blit(
                menu_controls,
                (self.SCREEN_WIDTH // 2 - menu_controls.get_width() // 2, 500),
            )

            gameplay_controls = self._render_text_with_background(
                "Juego: WASD/flechas mover | W/ARRIBA saltar | F disparar | E tienda | ESPACIO reiniciar",
                (170, 210, 240),
                (18, 22, 34),
            )
            self.screen.blit(
                gameplay_controls,
                (self.SCREEN_WIDTH // 2 - gameplay_controls.get_width() // 2, 530),
            )

            pygame.display.flip()
            return

        self.screen.fill(self.BACKGROUND_COLOR)

        is_near_store: bool = (
            self.store_unlocked
            and
            self.player.position.distance_to(self.store.position)
            <= self.STORE_INTERACTION_RANGE
        )

        self.world.draw(surface=self.screen, camera_offset_x=self.world.camera.offset.x)

        if self.store_unlocked:
            store_screen_x: int = int(self.store.position.x - self.world.camera.offset.x)
            store_screen_y: int = int(self.store.position.y)
            store_rect = pygame.Rect(store_screen_x - 26, store_screen_y - 72, 52, 72)
            store_color = self.STORE_ACTIVE_COLOR if is_near_store else self.STORE_COLOR
            pygame.draw.rect(self.screen, store_color, store_rect, border_radius=8)
            pygame.draw.rect(self.screen, (20, 20, 20), store_rect, width=2, border_radius=8)
            sign_surface = self.font_small.render("STORE", True, (20, 20, 20))
            self.screen.blit(
                sign_surface,
                (store_screen_x - sign_surface.get_width() // 2, store_screen_y - 92),
            )

        saved_x = self.player.position.x
        self.player.position.x = self.player.position.x - self.world.camera.offset.x
        self.player.draw()
        self.player.position.x = saved_x

        for projectile in self.projectiles:
            saved_proj_x = projectile.position.x
            projectile.position.x = projectile.position.x - self.world.camera.offset.x
            projectile.draw()
            projectile.position.x = saved_proj_x

        for boss_projectile in self.boss_projectiles:
            saved_proj_x = boss_projectile.position.x
            boss_projectile.position.x = (
                boss_projectile.position.x - self.world.camera.offset.x
            )
            boss_projectile.draw()
            boss_projectile.position.x = saved_proj_x

        if self.boss_enemy is not None and not self.boss_enemy.is_defeated:
            saved_boss_x = self.boss_enemy.position.x
            self.boss_enemy.position.x = (
                self.boss_enemy.position.x - self.world.camera.offset.x
            )
            self.boss_enemy.draw()
            self.boss_enemy.position.x = saved_boss_x

        self.hud.draw()

        info_y: int = 110
        info_x: int = 10
        blocks: list[tuple[str, tuple[int, int, int]]] = [
            (
                f"Dificultad: {self.current_difficulty.upper()}",
                (255, 200, 120),
            ),
            (f"Camara X: {self.world.camera.offset.x:.0f}", self.UI_COLOR),
            (f"Plataformas: {len(self.world.platforms)}", self.UI_COLOR),
            (
                f"{self.player.name} Lv.{self.player.stats.level}",
                (80, 200, 255) if self.player.is_active else (150, 50, 50),
            ),
            (
                f"HP: {self.player.health:.0f}/{self.player.stats.max_health:.0f}",
                (80, 220, 80),
            ),
            (
                f"XP: {self.player.stats.experience:.0f}/{self.player.stats.experience_threshold:.0f}",
                (180, 130, 220),
            ),
            (
                f"$ {self.player.cash} | DEF {self.player.stats.defense:.0f} | "
                f"ATK {self.player.stats.damage:.0f}",
                (250, 210, 60),
            ),
            (f"Enemigos activos: {sum(1 for e in self.world.enemies if not e.is_defeated)}", (255, 120, 120)),
            (
                f"Proyectiles: {len(self.projectiles)} / Boss: {len(self.boss_projectiles)}",
                (255, 220, 100),
            ),
            (
                (
                    f"Boss HP: {self.boss_enemy.health:.0f}"
                    if self.boss_enemy is not None and not self.boss_enemy.is_defeated
                    else "Boss HP: --"
                ),
                (255, 130, 190),
            ),
            (
                f"Spawn enemigos: {self.spawned_enemy_total}/{self.TOTAL_ENEMIES_BEFORE_BOSS}",
                (255, 200, 140),
            ),
            (
                (
                    "TIENDA: EN RANGO"
                    if is_near_store
                    else "Tienda: fuera de rango"
                )
                if self.store_unlocked
                else f"Tienda bloqueada: ${self.player.cash}/${self.STORE_UNLOCK_CASH}",
                (100, 255, 140) if is_near_store else (200, 180, 120),
            ),
            (f"Score: {self.score:.0f}", (180, 220, 255)),
            (f"Exploracion: {self.exploration_pct:.1f}%", (180, 220, 255)),
        ]

        for text, color in blocks:
            surf = self._render_text_with_background(text, color, self.UI_BG_COLOR)
            self.screen.blit(surf, (info_x, info_y))
            info_y += 24

        instructions = (
            "TIENDA ABIERTA: TAB cambia panel | Arriba/Abajo selecciona | "
            "ENTER confirma | E/ESC cierra"
            if self.store_dialog_open
            else "WASD/flechas: mover | W/arriba: saltar | F: disparar | "
            "Q: usar item | E: tienda | P: pausa | 1/2/3: dificultad | ESPACIO: regenerar | ESC: salir"
        )
        instructions_surface = self._render_text_with_background(
            instructions,
            (150, 150, 150),
            self.UI_BG_COLOR,
        )
        self.screen.blit(instructions_surface, (info_x, self.SCREEN_HEIGHT - 30))

        for i, (msg_text, _) in enumerate(self.messages[-5:]):
            msg_surf = self._render_text_with_background(
                msg_text,
                (255, 255, 100),
                (0, 0, 0),
                font=self.font_medium,
            )
            self.screen.blit(
                msg_surf,
                (self.SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, 60 + i * 28),
            )

        fps_info = self._render_text_with_background(
            f"FPS: {self.clock.get_fps():.0f}",
            (100, 255, 100),
            self.UI_BG_COLOR,
        )
        self.screen.blit(fps_info, (self.SCREEN_WIDTH - 120, 10))

        frame_info = self._render_text_with_background(
            f"Frame: {self.frame_count}",
            (100, 255, 100),
            self.UI_BG_COLOR,
        )
        self.screen.blit(frame_info, (self.SCREEN_WIDTH - 120, 35))

        victory = self.check_victory()
        if victory:
            win_surface = self._render_text_with_background(
                "VICTORIA! Objetivos cumplidos.",
                (120, 255, 120),
                (0, 0, 0),
                font=self.font_medium,
            )
            self.screen.blit(
                win_surface,
                (self.SCREEN_WIDTH // 2 - win_surface.get_width() // 2, 26),
            )

        if self.game_over:
            image_rect = self.game_over_image.get_rect(
                center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
            )
            self.screen.blit(self.game_over_image, image_rect)
            restart_text = self._render_text_with_background(
                "Presiona ESPACIO para reiniciar",
                (255, 255, 255),
                (0, 0, 0),
                font=self.font_medium,
            )
            self.screen.blit(
                restart_text,
                (
                    self.SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                    self.SCREEN_HEIGHT // 2 + 150,
                ),
            )

        if self.paused and not self.game_over:
            pause_overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 120))
            self.screen.blit(pause_overlay, (0, 0))
            pause_text = self._render_text_with_background(
                "PAUSA - Presiona P para continuar",
                (255, 255, 255),
                (0, 0, 0),
                font=self.font_medium,
            )
            self.screen.blit(
                pause_text,
                (
                    self.SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                    self.SCREEN_HEIGHT // 2 - pause_text.get_height() // 2,
                ),
            )

        if self.store_dialog_open and not self.game_over:
            self._draw_store_dialog(
                remote_mode=(not self.store_unlocked) or (not is_near_store),
            )

        if self.boss_enemy is not None and self.boss_enemy.is_defeated:
            self._draw_victory_banner()

        pygame.display.flip()

    def check_victory(self) -> bool:
        """Indica si se alcanzaron condiciones de victoria del nivel."""
        if self.boss_enemy is None:
            return False
        if self.boss_enemy is not None and not self.boss_enemy.is_defeated:
            return False
        enemies_cleared: bool = all(enemy.is_defeated for enemy in self.world.enemies)
        exploration_done: bool = self.world.camera.offset.x >= self.VICTORY_CAMERA_X
        return enemies_cleared or exploration_done

    def exec(self) -> None:
        """Ejecuta el loop principal hasta cierre de la partida."""
        if self._difficulty_selection_pending:
            self.difficulty_menu_active = True

        while self.is_playing:
            dt: float = self.clock.tick(self.TARGET_FPS) / 1000.0
            self.handle_event()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit(0)
