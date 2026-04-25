from __future__ import annotations

import pygame
from pathlib import Path

from core.sprite import Sprite
from core.vector2d import Vector2D
from entities.proyectile import Proyectile
from inventory.inventory import Inventory
from inventory.item import Item
from stats.stats import Stats


class Player(Sprite):
    """Entidad jugador con estadísticas, inventario y combate."""

    DEFAULT_COLOR: tuple[int, int, int] = (80, 150, 220)
    DEFAULT_RADIUS: int = 24
    DEFAULT_SHOT_COOLDOWN: float = 0.35
    DEFAULT_IMAGE: str = str(Path(__file__).parent.parent / "public" / "assets" / "player.gif")

    def __init__(
        self,
        screen: pygame.Surface,
        world_pos: Vector2D,
        name: str,
        *,
        cash: int = 0,
        stats: Stats | None = None,
        inventory: Inventory | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("name no puede estar vacío")
        if cash < 0:
            raise ValueError("cash no puede ser negativo")

        super().__init__(
            screen=screen,
            x=world_pos.x,
            y=world_pos.y,
            color=self.DEFAULT_COLOR,
            radius=self.DEFAULT_RADIUS,
            image=self.DEFAULT_IMAGE,
        )

        self.name: str = name
        self.cash: int = cash
        self.stats: Stats = stats if stats is not None else Stats()
        self.inventory: Inventory = inventory if inventory is not None else Inventory()
        self.health: float = self.stats.max_health
        self.shot_cooldown: float = self.DEFAULT_SHOT_COOLDOWN
        self._last_shot_time: float = float("-inf")
        self.shield_duration: float = 0.0
        self.shield_defense_boost: float = 0.0
        self.shield_effect_timer: float = 0.0
        self.shield_pickup_timer: float = 0.0
        self.treasure_pickup_timer: float = 0.0

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------

    def shoot(
        self,
        direction: Vector2D,
        current_time: float,
        *,
        projectile_velocity: float = 400.0,
        projectile_life_time: float = 2.0,
    ) -> Proyectile | None:
        """Dispara un proyectil si la cadencia lo permite."""
        if current_time < 0:
            raise ValueError("current_time no puede ser negativo")
        if not self.is_active:
            return None
        if (current_time - self._last_shot_time) < self.shot_cooldown:
            return None

        projectile = Proyectile(
            screen=self.screen,
            x=self.x,
            y=self.y,
            direction=direction,
            velocity=projectile_velocity,
            stats=self.stats,
            life_time=projectile_life_time,
        )
        self._last_shot_time = current_time
        return projectile

    def defend(self, damage: float) -> float:
        """Recibe daño, aplica defensa y retorna el daño neto recibido."""
        if damage < 0:
            raise ValueError("damage no puede ser negativo")

        total_defense: float = self.stats.defense + self.shield_defense_boost
        for item in self.inventory.items:
            total_defense += item.defense_boost

        net_damage: float = max(0.0, damage - total_defense)
        self.health = max(0.0, self.health - net_damage)

        if net_damage > 0:
            self.damage_effect_timer = 0.2  # Efecto de daño por 0.2 segundos

        if self.health <= 0:
            self.is_active = False

        return net_damage
        """Activa un escudo temporal con boost de defensa."""
        if duration <= 0:
            raise ValueError("duration debe ser mayor a 0")
        if defense_boost < 0:
            raise ValueError("defense_boost no puede ser negativo")
        self.shield_duration = duration
        self.shield_defense_boost = defense_boost
        self.shield_effect_timer = 2.0  # Efecto visual por 2 segundos

    def update(self, delta_time: float = 0.0) -> None:
        """Actualiza el estado del jugador, incluyendo escudos temporales."""
        super().update(delta_time)
        if delta_time < 0:
            raise ValueError("delta_time no puede ser negativo")
        if not self.is_active:
            return

        # Actualizar duración del escudo
        if self.shield_duration > 0:
            self.shield_duration -= delta_time
            if self.shield_duration <= 0:
                self.shield_defense_boost = 0.0

        # Actualizar cooldown de disparo
        if self.shot_cooldown > 0:
            self.shot_cooldown -= delta_time

        # Actualizar timers de efectos de recolección
        if self.shield_pickup_timer > 0:
            self.shield_pickup_timer -= delta_time
        if self.treasure_pickup_timer > 0:
            self.treasure_pickup_timer -= delta_time

    def trigger_shield_pickup_effect(self) -> None:
        """Activa el efecto visual de recoger un escudo."""
        self.shield_pickup_timer = 0.5  # Efecto por 0.5 segundos

    def trigger_treasure_pickup_effect(self) -> None:
        """Activa el efecto visual de recoger un tesoro."""
        self.treasure_pickup_timer = 0.5  # Efecto por 0.5 segundos

    def draw(self) -> None:
        """Dibuja el jugador con efectos visuales para daño, escudo y recolectables."""
        if not self.is_active:
            return

        if self.image:
            self.draw_image()
            # Efectos de overlay
            if self.shield_pickup_timer > 0:
                overlay = pygame.Surface((self.radius * 2, self.radius * 2))
                overlay.set_alpha(128)  # Semi-transparente
                overlay.fill((100, 150, 255))  # Azul para recoger escudo
                self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
            elif self.treasure_pickup_timer > 0:
                overlay = pygame.Surface((self.radius * 2, self.radius * 2))
                overlay.set_alpha(128)  # Semi-transparente
                overlay.fill((255, 255, 100))  # Amarillo para recoger tesoro
                self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
            elif self.shield_effect_timer > 0:
                overlay = pygame.Surface((self.radius * 2, self.radius * 2))
                overlay.set_alpha(128)  # Semi-transparente
                overlay.fill((100, 150, 255))  # Azul para escudo activo
                self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
        else:
            if self.damage_effect_timer > 0:
                draw_color = (255, 100, 100)  # Rojo para daño
            elif self.shield_pickup_timer > 0:
                draw_color = (100, 150, 255)  # Azul para recoger escudo
            elif self.treasure_pickup_timer > 0:
                draw_color = (255, 255, 100)  # Amarillo para recoger tesoro
            elif self.shield_effect_timer > 0:
                draw_color = (100, 150, 255)  # Azul para escudo
            else:
                draw_color = self.color

            pygame.draw.circle(
                self.screen,
                draw_color,
                (int(self.position.x), int(self.position.y)),
                self.radius
            )

    def collect(self, collectible: object) -> None:
        """Interactúa con un coleccionable del mundo."""
        if hasattr(collectible, "collect") and callable(collectible.collect):
            collectible.collect()

    def use_item(self, item: Item) -> bool:
        """Usa un ítem del inventario. Retorna True si se usó correctamente."""
        if item not in self.inventory.items:
            return False
        self.stats.damage += item.attack_boost
        self.stats.defense += item.defense_boost
        self.health = min(self.health + item.damage, self.stats.max_health)
        self.inventory.remove_item(item)
        return True

    # ------------------------------------------------------------------
    # Economía
    # ------------------------------------------------------------------

    def buy_item(self, item: Item, store: object) -> bool:
        """Compra un ítem de una tienda. Retorna True si la compra fue exitosa."""
        if self.cash < item.buy_price:
            return False
        if self.inventory.is_full:
            return False
        self.cash -= int(item.buy_price)
        self.inventory.add_item(item)
        if hasattr(store, "items") and item in store.items:
            store.items.remove(item)
        return True

    def sell_item(self, item: Item, store: object) -> bool:
        """Vende un ítem a una tienda. Retorna True si la venta fue exitosa."""
        if not self.inventory.remove_item(item):
            return False
        self.cash += int(item.sell_price)
        if hasattr(store, "items"):
            store.items.append(item)
        return True

    # ------------------------------------------------------------------
    # Progresión
    # ------------------------------------------------------------------

    def gain_experience(self, amount: float) -> int:
        """Delega la ganancia de experiencia a Stats. Retorna niveles ganados."""
        return self.stats.gain_experience(amount)

    def level_up(self) -> None:
        """Sube de nivel y restaura la salud al nuevo máximo."""
        self.stats.level_up()
        self.health = self.stats.max_health

    def __repr__(self) -> str:
        return (
            f"Player(name={self.name!r}, health={self.health}/{self.stats.max_health}, "
            f"cash={self.cash}, level={self.stats.level})"
        )
