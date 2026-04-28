from __future__ import annotations

import pygame

from entities.player import Player


class HUD:
    """Interfaz de usuario superpuesta que muestra el estado del jugador en pantalla."""

    # Panel superior
    PANEL_HEIGHT: int = 100
    PANEL_COLOR: tuple[int, int, int] = (20, 20, 30)
    PANEL_ALPHA: int = 0

    # Barras
    BAR_HEIGHT: int = 16
    BAR_RADIUS: int = 6
    HP_COLOR_FULL: tuple[int, int, int] = (60, 200, 80)
    HP_COLOR_LOW: tuple[int, int, int] = (220, 60, 60)
    HP_LOW_THRESHOLD: float = 0.3
    SHIELD_BAR_COLOR: tuple[int, int, int] = (80, 160, 255)
    SHIELD_BAR_EMPTY_COLOR: tuple[int, int, int] = (40, 60, 100)
    XP_COLOR: tuple[int, int, int] = (160, 100, 220)
    BAR_BG_COLOR: tuple[int, int, int] = (50, 50, 60)

    # Texto
    FONT_SIZE_LARGE: int = 18
    FONT_SIZE_SMALL: int = 14
    TEXT_COLOR: tuple[int, int, int] = (15, 15, 30)
    LABEL_COLOR: tuple[int, int, int] = (40, 40, 60)
    CASH_COLOR: tuple[int, int, int] = (150, 80, 0)
    SHIELD_COLOR: tuple[int, int, int] = (0, 60, 180)
    LEVEL_COLOR: tuple[int, int, int] = (140, 60, 0)

    # Inventario
    SLOT_SIZE: int = 44
    SLOT_MARGIN: int = 6
    SLOT_BG_COLOR: tuple[int, int, int] = (30, 30, 45)
    SLOT_BORDER_COLOR: tuple[int, int, int] = (80, 80, 110)
    SLOT_ACTIVE_COLOR: tuple[int, int, int] = (100, 130, 200)
    INVENTORY_PANEL_ALPHA: int = 190
    MAX_VISIBLE_SLOTS: int = 8

    # Recuadro del HUD
    BOX_PAD: int = 8
    BOX_COLOR: tuple[int, int, int] = (180, 180, 190)
    BOX_ALPHA: int = 210
    BOX_BORDER_COLOR: tuple[int, int, int] = (100, 100, 120)
    BOX_BORDER_RADIUS: int = 12

    # Márgenes internos
    PADDING_X: int = 16
    PADDING_Y: int = 10
    BAR_WIDTH: int = 180

    def __init__(self, screen: pygame.Surface, player: Player) -> None:
        self.screen = screen
        self.player = player
        self._font_large = pygame.font.SysFont("Arial", self.FONT_SIZE_LARGE, bold=True)
        self._font_small = pygame.font.SysFont("Arial", self.FONT_SIZE_SMALL)

    # ------------------------------------------------------------------
    # Dibujo principal
    # ------------------------------------------------------------------

    def draw(self) -> None:
        """Dibuja todos los elementos del HUD sobre la pantalla."""
        self._draw_top_panel()
        self._draw_inventory_panel()

    # ------------------------------------------------------------------
    # Panel superior: HP, XP, nivel, dinero, escudo
    # ------------------------------------------------------------------

    def _draw_top_panel(self) -> None:
        panel = pygame.Surface((self.screen.get_width(), self.PANEL_HEIGHT), pygame.SRCALPHA)
        panel.fill((*self.PANEL_COLOR, self.PANEL_ALPHA))
        self.screen.blit(panel, (0, 0))

        x = self.PADDING_X
        y = self.PADDING_Y

        # --- Recuadro gris con esquinas redondeadas ---
        box_x = x - self.BOX_PAD
        box_y = y - self.BOX_PAD
        # ancho: etiqueta(28) + barra(BAR_WIDTH) + valor(80) + hueco(40) + columna nivel/cash(100)
        box_w = 28 + self.BAR_WIDTH + 80 + 40 + 100 + self.BOX_PAD * 2
        # alto: 3 barras con sus separadores + padding vertical
        box_h = 3 * self.BAR_HEIGHT + 2 * 6 + self.BOX_PAD * 2
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(
            box_surf,
            (*self.BOX_COLOR, self.BOX_ALPHA),
            pygame.Rect(0, 0, box_w, box_h),
            border_radius=self.BOX_BORDER_RADIUS,
        )
        pygame.draw.rect(
            box_surf,
            (*self.BOX_BORDER_COLOR, 255),
            pygame.Rect(0, 0, box_w, box_h),
            width=2,
            border_radius=self.BOX_BORDER_RADIUS,
        )
        self.screen.blit(box_surf, (box_x, box_y))

        # --- Barra de HP ---
        hp_ratio = self.player.health / max(self.player.stats.max_health, 1)
        hp_color = self.HP_COLOR_LOW if hp_ratio <= self.HP_LOW_THRESHOLD else self.HP_COLOR_FULL
        self._draw_label("HP", x, y)
        self._draw_bar(x + 28, y, self.BAR_WIDTH, hp_ratio, hp_color)
        hp_text = f"{int(self.player.health)}/{int(self.player.stats.max_health)}"
        self._draw_text_small(hp_text, x + 28 + self.BAR_WIDTH + 6, y, self.TEXT_COLOR)

        # --- Barra de escudo ---
        y += self.BAR_HEIGHT + 6
        shield_ratio = (
            self.player.shield_hp / max(self.player.shield_max_hp, 1)
            if self.player.shield_max_hp > 0 else 0.0
        )
        shield_bar_color = self.SHIELD_BAR_COLOR if self.player.shield_hp > 0 else self.SHIELD_BAR_EMPTY_COLOR
        self._draw_label("SC", x, y)
        self._draw_bar(x + 28, y, self.BAR_WIDTH, shield_ratio, shield_bar_color)
        shield_text = f"{int(self.player.shield_hp)}/{int(self.player.shield_max_hp)}"
        self._draw_text_small(shield_text, x + 28 + self.BAR_WIDTH + 6, y, self.SHIELD_COLOR)

        # --- Barra de XP ---
        y += self.BAR_HEIGHT + 6
        xp_ratio = self.player.stats.experience / max(self.player.stats.experience_threshold, 1)
        self._draw_label("XP", x, y)
        self._draw_bar(x + 28, y, self.BAR_WIDTH, xp_ratio, self.XP_COLOR)
        xp_text = f"{int(self.player.stats.experience)}/{int(self.player.stats.experience_threshold)}"
        self._draw_text_small(xp_text, x + 28 + self.BAR_WIDTH + 6, y, self.LABEL_COLOR)

        # --- Nivel ---
        level_x = x + 28 + self.BAR_WIDTH + 90
        level_surf = self._font_large.render(
            f"Nv. {self.player.stats.level}", True, self.LEVEL_COLOR
        )
        self.screen.blit(level_surf, (level_x, self.PADDING_Y))

        # --- Dinero ---
        cash_x = level_x
        cash_surf = self._font_small.render(
            f"$ {self.player.cash}", True, self.CASH_COLOR
        )
        self.screen.blit(cash_surf, (cash_x, self.PADDING_Y + self.BAR_HEIGHT + 8))

        # --- Nombre del jugador ---
        name_surf = self._font_small.render(self.player.name, True, self.LABEL_COLOR)
        self.screen.blit(name_surf, (self.screen.get_width() - name_surf.get_width() - self.PADDING_X, self.PADDING_Y))

    # ------------------------------------------------------------------
    # Panel de inventario (esquina inferior izquierda)
    # ------------------------------------------------------------------

    def _draw_inventory_panel(self) -> None:
        items = self.player.inventory.items
        visible = min(len(items), self.MAX_VISIBLE_SLOTS)
        total_width = visible * (self.SLOT_SIZE + self.SLOT_MARGIN) - self.SLOT_MARGIN + self.PADDING_X * 2
        panel_height = self.SLOT_SIZE + self.PADDING_Y * 2

        bottom_y = self.screen.get_height() - panel_height - 8

        panel = pygame.Surface((total_width, panel_height), pygame.SRCALPHA)
        panel.fill((*self.SLOT_BG_COLOR, self.INVENTORY_PANEL_ALPHA))
        self.screen.blit(panel, (8, bottom_y))

        slot_x = 8 + self.PADDING_X
        slot_y = bottom_y + self.PADDING_Y

        for i in range(visible):
            item = items[i]
            self._draw_item_slot(slot_x, slot_y, item)
            slot_x += self.SLOT_SIZE + self.SLOT_MARGIN

    def _draw_item_slot(self, x: int, y: int, item: object) -> None:
        slot_rect = pygame.Rect(x, y, self.SLOT_SIZE, self.SLOT_SIZE)
        pygame.draw.rect(self.screen, self.SLOT_BG_COLOR, slot_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.SLOT_BORDER_COLOR, slot_rect, width=2, border_radius=6)

        if hasattr(item, "name"):
            label = item.name[:6]
            text_surf = self._font_small.render(label, True, self.TEXT_COLOR)
            text_x = x + (self.SLOT_SIZE - text_surf.get_width()) // 2
            text_y = y + (self.SLOT_SIZE - text_surf.get_height()) // 2
            self.screen.blit(text_surf, (text_x, text_y))

    # ------------------------------------------------------------------
    # Helpers de dibujo
    # ------------------------------------------------------------------

    def _draw_bar(
        self,
        x: int,
        y: int,
        width: int,
        ratio: float,
        color: tuple[int, int, int],
    ) -> None:
        ratio = max(0.0, min(1.0, ratio))
        bg_rect = pygame.Rect(x, y, width, self.BAR_HEIGHT)
        fill_rect = pygame.Rect(x, y, int(width * ratio), self.BAR_HEIGHT)
        pygame.draw.rect(self.screen, self.BAR_BG_COLOR, bg_rect, border_radius=self.BAR_RADIUS)
        if fill_rect.width > 0:
            pygame.draw.rect(self.screen, color, fill_rect, border_radius=self.BAR_RADIUS)

    def _draw_label(self, text: str, x: int, y: int) -> None:
        surf = self._font_small.render(text, True, self.LABEL_COLOR)
        self.screen.blit(surf, (x, y + 1))

    def _draw_text_small(self, text: str, x: int, y: int, color: tuple[int, int, int]) -> None:
        surf = self._font_small.render(text, True, color)
        self.screen.blit(surf, (x, y + 1))
