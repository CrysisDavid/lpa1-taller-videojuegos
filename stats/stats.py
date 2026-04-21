from __future__ import annotations


class Stats:
    """Estadísticas de combate y progresión del jugador."""

    BASE_EXPERIENCE_THRESHOLD: float = 100.0
    EXPERIENCE_MULTIPLIER: float = 1.5
    HEALTH_PER_LEVEL: float = 20.0
    DAMAGE_PER_LEVEL: float = 5.0
    DEFENSE_PER_LEVEL: float = 2.0
    ENDURANCE_PER_LEVEL: float = 10.0

    def __init__(
        self,
        *,
        max_health: float = 100.0,
        endurance: float = 100.0,
        damage: float = 10.0,
        defense: float = 5.0,
        level: int = 1,
        experience: float = 0.0,
    ) -> None:
        if max_health <= 0:
            raise ValueError("max_health debe ser mayor a 0")
        if endurance <= 0:
            raise ValueError("endurance debe ser mayor a 0")
        if damage < 0:
            raise ValueError("damage no puede ser negativo")
        if defense < 0:
            raise ValueError("defense no puede ser negativo")
        if level < 1:
            raise ValueError("level debe ser al menos 1")
        if experience < 0:
            raise ValueError("experience no puede ser negativa")

        self.max_health: float = max_health
        self.endurance: float = endurance
        self.damage: float = damage
        self.defense: float = defense
        self.level: int = level
        self.experience: float = experience

    @property
    def experience_threshold(self) -> float:
        """Experiencia necesaria para subir al siguiente nivel."""
        return self.BASE_EXPERIENCE_THRESHOLD * (
            self.EXPERIENCE_MULTIPLIER ** (self.level - 1)
        )

    def gain_experience(self, amount: float) -> int:
        """
        Añade experiencia y sube de nivel automáticamente si corresponde.

        Returns:
            int: Cantidad de niveles ganados.
        """
        if amount < 0:
            raise ValueError("amount no puede ser negativo")

        self.experience += amount
        levels_gained: int = 0

        while self.experience >= self.experience_threshold:
            self.experience -= self.experience_threshold
            self.level_up()
            levels_gained += 1

        return levels_gained

    def level_up(self) -> None:
        """Sube un nivel y aplica la mejora de atributos."""
        self.level += 1
        self.upgrade_attributes()

    def upgrade_attributes(self) -> None:
        """Mejora los atributos base al subir de nivel."""
        self.max_health += self.HEALTH_PER_LEVEL
        self.endurance += self.ENDURANCE_PER_LEVEL
        self.damage += self.DAMAGE_PER_LEVEL
        self.defense += self.DEFENSE_PER_LEVEL

    def __repr__(self) -> str:
        return (
            f"Stats(level={self.level}, max_health={self.max_health}, "
            f"damage={self.damage}, defense={self.defense}, "
            f"endurance={self.endurance}, experience={self.experience:.1f}/"
            f"{self.experience_threshold:.1f})"
        )
