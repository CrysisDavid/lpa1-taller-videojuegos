"""Paquete de entidades del juego."""

from entities.collectible import Collectible
from entities.trap import Trap
from entities.treasure import Treasure

__all__ = ["Collectible", "Shield", "Trap", "Treasure"]


def __getattr__(name: str) -> object:
	if name == "Shield":
		from combat.shield import Shield

		return Shield
	raise AttributeError(f"module 'entities' has no attribute {name!r}")
