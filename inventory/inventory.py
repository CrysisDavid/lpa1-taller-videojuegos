from __future__ import annotations

from typing import List

from inventory.item import Item


class Inventory:
    """Contenedor de ítems del jugador."""

    def __init__(self, capacity: int = 20) -> None:
        if capacity < 1:
            raise ValueError("capacity debe ser al menos 1")
        self.capacity: int = capacity
        self.items: List[Item] = []

    @property
    def is_full(self) -> bool:
        return len(self.items) >= self.capacity

    def add_item(self, item: Item) -> bool:
        """Agrega un ítem si hay espacio. Retorna True si se añadió."""
        if not isinstance(item, Item):
            raise TypeError("item debe ser una instancia de Item")
        if self.is_full:
            return False
        self.items.append(item)
        return True

    def remove_item(self, item: Item) -> bool:
        """Elimina un ítem del inventario. Retorna True si se encontró y eliminó."""
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        return f"Inventory({len(self.items)}/{self.capacity} items)"
