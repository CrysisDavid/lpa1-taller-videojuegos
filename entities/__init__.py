"""Paquete de entidades del juego."""

from entities.bossenemy import BossEnemy
from entities.collectible import Collectible
from entities.enemy import Enemy
from entities.player import Player
from entities.trap import Trap
from entities.treasure import Treasure

__all__ = [
	"BossEnemy",
	"Collectible",
	"Enemy",
	"Player",
	"Shield",
	"Trap",
	"Treasure",
]


def __getattr__(name: str) -> object:
	if name == "Shield":
		from combat.shield import Shield

		return Shield
	raise AttributeError(f"module 'entities' has no attribute {name!r}")
