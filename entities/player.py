from __future__ import annotations

import pygame

from core.sprite import Sprite
from core.vector2d import Vector2D
from inventory.inventory import Inventory
from inventory.item import Item
from stats.stats import Stats


class Player(Sprite):
    """Entidad jugador con estadísticas, inventario y combate."""

    DEFAULT_COLOR: tuple[int, int, int] = (80, 150, 220)
    DEFAULT_RADIUS: int = 24

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
            raius=self.DEFAULT_RADIUS,
        )

        self.name: str = name
        self.cash: int = cash
        self.stats: Stats = stats if stats is not None else Stats()
        self.inventory: Inventory = inventory if inventory is not None else Inventory()
        self.health: float = self.stats.max_health

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------

    def attack(self, enemy: object) -> float:
        """Ataca a un enemigo y retorna el daño infligido."""
        if not self.is_active:
            return 0.0

        raw_damage: float = self.stats.damage

        # Bonus de ítems equipados en inventario
        for item in self.inventory.items:
            raw_damage += item.attack_boost

        enemy_defense: float = float(getattr(enemy, "defense", 0.0))
        final_damage: float = max(0.0, raw_damage - enemy_defense)

        if hasattr(enemy, "take_damage") and callable(enemy.take_damage):
            enemy.take_damage(final_damage)
        elif hasattr(enemy, "health"):
            new_health: float = max(0.0, float(enemy.health) - final_damage)
            setattr(enemy, "health", new_health)

        return final_damage

    def defend(self, damage: float) -> float:
        """Recibe daño, aplica defensa y retorna el daño neto recibido."""
        if damage < 0:
            raise ValueError("damage no puede ser negativo")

        total_defense: float = self.stats.defense
        for item in self.inventory.items:
            total_defense += item.defense_boost

        net_damage: float = max(0.0, damage - total_defense)
        self.health = max(0.0, self.health - net_damage)

        if self.health <= 0:
            self.is_active = False

        return net_damage

    # ------------------------------------------------------------------
    # Recolección y uso de ítems
    # ------------------------------------------------------------------

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
