from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List

from core.vector2d import Vector2D
from inventory.item import Item

if TYPE_CHECKING:
    from entities.player import Player


class Store:
    """Tienda con catálogo de ítems y operaciones de compra/venta."""

    def __init__(
        self,
        position: Vector2D,
        items: Iterable[Item] | None = None,
    ) -> None:
        self.position: Vector2D = position
        self.items: List[Item] = list(items) if items is not None else []

    def buy(self, item: Item, player: Player) -> bool:
        """Vende un ítem al jugador si hay stock, dinero y espacio."""
        if item not in self.items:
            return False
        if player.cash < item.buy_price:
            return False
        if player.inventory.is_full:
            return False

        if not player.inventory.add_item(item):
            return False

        player.cash -= int(item.buy_price)
        self.items.remove(item)
        return True

    def sell(self, item: Item, player: Player) -> bool:
        """Compra un ítem al jugador y lo agrega al stock de la tienda."""
        if not player.inventory.remove_item(item):
            return False

        player.cash += int(item.sell_price)
        self.items.append(item)
        return True

    def restock(self, items: Iterable[Item]) -> int:
        """Agrega ítems al catálogo y retorna cuántos se incorporaron."""
        new_items: List[Item] = list(items)
        self.items.extend(new_items)
        return len(new_items)

    def __repr__(self) -> str:
        return f"Store(position={self.position!r}, items={len(self.items)})"