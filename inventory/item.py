from __future__ import annotations


class Item:
    """Objeto que el jugador puede comprar, vender o usar."""

    def __init__(
        self,
        name: str,
        *,
        description: str = "",
        buy_price: float = 0.0,
        sell_price: float = 0.0,
        attack_boost: float = 0.0,
        defense_boost: float = 0.0,
        damage: float = 0.0,
    ) -> None:
        if not name.strip():
            raise ValueError("name no puede estar vacío")
        if buy_price < 0:
            raise ValueError("buy_price no puede ser negativo")
        if sell_price < 0:
            raise ValueError("sell_price no puede ser negativo")

        self.name: str = name
        self.description: str = description
        self.buy_price: float = buy_price
        self.sell_price: float = sell_price
        self.attack_boost: float = attack_boost
        self.defense_boost: float = defense_boost
        self.damage: float = damage

    def __repr__(self) -> str:
        return (
            f"Item(name={self.name!r}, buy={self.buy_price}, "
            f"sell={self.sell_price}, atk_boost={self.attack_boost}, "
            f"def_boost={self.defense_boost})"
        )
