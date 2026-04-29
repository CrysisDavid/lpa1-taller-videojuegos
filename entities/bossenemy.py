from __future__ import annotations

from typing import Literal, Sequence

import pygame

from core.vector2d import Vector2D
from entities.enemy import Enemy
from entities.proyectile import Proyectile
from stats.stats import Stats


class BossEnemy(Enemy):
    """Variante de Enemy con fases y ataques especiales a distancia."""

    DEFAULT_SIZE: tuple[float, float] = (220.0, 220.0)
    DEFAULT_SHOT_COOLDOWN: float = 1.5
    DEFAULT_PROJECTILE_VELOCITY: float = 320.0
    DEFAULT_PROJECTILE_LIFE_TIME: float = 3.0
    DEFAULT_MAX_SPEED: float = 240.0
    DEFAULT_ACCELERATION: float = 1800.0
    DEFAULT_DRAG: float = 1200.0
    DEFAULT_GRAVITY: float = 900.0
    DEFAULT_JUMP_FORCE: float = -460.0
    DEFAULT_TURN_BUFFER: float = 20.0
    DEFAULT_JUMP_TRIGGER_DISTANCE: float = 220.0

    def __init__(
        self,
        screen: pygame.Surface,
        world_pos: Vector2D,
        name: str,
        *,
        size: Vector2D | None = None,
        velocity: float = 40.0,
        enemy_type: Literal["volador", "terrestre"] = "terrestre",
        health: float = 420.0,
        attack_power: float = 50.0,
        defense: float = 10.0,
        special_attacks: Sequence[str] | None = None,
        projectile_velocity: float = DEFAULT_PROJECTILE_VELOCITY,
        projectile_life_time: float = DEFAULT_PROJECTILE_LIFE_TIME,
        shot_cooldown: float = DEFAULT_SHOT_COOLDOWN,
    ) -> None:
        boss_size: Vector2D = (
            size if size is not None else Vector2D(*self.DEFAULT_SIZE)
        )
        super().__init__(
            screen=screen,
            world_pos=world_pos,
            name=name,
            size=boss_size,
            velocity=velocity,
            enemy_type=enemy_type,
            health=health,
            attack_power=attack_power,
            defense=defense,
        )
        if projectile_velocity <= 0:
            raise ValueError("projectile_velocity debe ser mayor a 0")
        if projectile_life_time <= 0:
            raise ValueError("projectile_life_time debe ser mayor a 0")
        if shot_cooldown < 0:
            raise ValueError("shot_cooldown no puede ser negativo")

        self.max_health: float = health
        self.phase: float = 1.0
        self.special_attacks: list[str] = list(special_attacks or ["slam"])
        self.projectile_velocity: float = projectile_velocity
        self.projectile_life_time: float = projectile_life_time
        self.shot_cooldown: float = shot_cooldown
        self._last_shot_time: float = float("-inf")
        self.horizontal_velocity: float = 0.0
        self.vertical_velocity: float = 0.0
        self.on_ground: bool = True
        self.facing_direction: float = -1.0
        self.trigger_phase_change()

    def _resolve_landing(self, platforms: Sequence[object], previous_y: float, ground_y: float) -> None:
        """Aterriza sobre plataformas o sobre el suelo base del boss."""
        self.on_ground = False
        if self.vertical_velocity < 0:
            return

        previous_bottom: float = previous_y + self.radius
        current_bottom: float = self.position.y + self.radius
        horizontal_margin: float = self.radius * 0.45
        best_top: float | None = None

        for platform in platforms:
            platform_x = float(getattr(platform, "x", 0.0))
            platform_y = float(getattr(platform, "y", 0.0))
            platform_width = float(getattr(platform, "width", 0.0))
            within_x = (
                (platform_x - horizontal_margin)
                <= self.position.x
                <= (platform_x + platform_width + horizontal_margin)
            )
            if not within_x:
                continue

            crossed_top = previous_bottom <= platform_y <= current_bottom
            if not crossed_top:
                continue

            if best_top is None or platform_y < best_top:
                best_top = platform_y

        if best_top is not None:
            self.position.y = best_top - self.radius
            self.vertical_velocity = 0.0
            self.on_ground = True
            return

        if self.position.y >= ground_y:
            self.position.y = ground_y
            self.vertical_velocity = 0.0
            self.on_ground = True

    def ai_update(
        self,
        player: object,
        platforms: Sequence[object],
        delta_time: float,
        *,
        ground_y: float,
        viewport_left: float | None = None,
        viewport_right: float | None = None,
    ) -> None:
        """Persigue al player, salta cuando conviene y se devuelve si lo sobrepasa."""
        if delta_time < 0:
            raise ValueError("delta_time no puede ser negativo")
        if not self.is_active or not hasattr(player, "position"):
            return

        player_position = player.position
        delta_x: float = player_position.x - self.position.x
        delta_y: float = player_position.y - self.position.y

        if delta_x > self.DEFAULT_TURN_BUFFER:
            target_axis = 1.0
        elif delta_x < -self.DEFAULT_TURN_BUFFER:
            target_axis = -1.0
        else:
            target_axis = 0.0

        if target_axis != 0.0:
            self.horizontal_velocity += target_axis * self.DEFAULT_ACCELERATION * delta_time
            self.facing_direction = target_axis
        elif self.horizontal_velocity > 0.0:
            self.horizontal_velocity = max(0.0, self.horizontal_velocity - self.DEFAULT_DRAG * delta_time)
        elif self.horizontal_velocity < 0.0:
            self.horizontal_velocity = min(0.0, self.horizontal_velocity + self.DEFAULT_DRAG * delta_time)

        self.horizontal_velocity = max(
            -self.DEFAULT_MAX_SPEED,
            min(self.DEFAULT_MAX_SPEED, self.horizontal_velocity),
        )
        self.position.x += self.horizontal_velocity * delta_time

        if viewport_left is not None and self.position.x < viewport_left:
            self.position.x = viewport_left
            self.horizontal_velocity = max(0.0, self.horizontal_velocity)
        if viewport_right is not None and self.position.x > viewport_right:
            self.position.x = viewport_right
            self.horizontal_velocity = min(0.0, self.horizontal_velocity)

        should_jump = (
            self.on_ground
            and abs(delta_x) <= self.DEFAULT_JUMP_TRIGGER_DISTANCE
            and delta_y < -30.0
        )
        if should_jump:
            self.vertical_velocity = self.DEFAULT_JUMP_FORCE
            self.on_ground = False

        previous_y: float = self.position.y
        self.vertical_velocity += self.DEFAULT_GRAVITY * delta_time
        self.position.y += self.vertical_velocity * delta_time
        self._resolve_landing(platforms, previous_y, ground_y)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time

    def draw(self) -> None:
        """Dibuja al boss volteando la imagen según su dirección actual."""
        if not self.is_active:
            return

        if self.image:
            if self._loaded_image is None or self._image_path != self.image:
                self._loaded_image = pygame.image.load(self.image)
                self._loaded_image = pygame.transform.scale(
                    self._loaded_image,
                    (self.radius * 2, self.radius * 2),
                )
                self._image_path = self.image

            draw_surface = self._loaded_image
            if self.facing_direction > 0:
                draw_surface = pygame.transform.flip(draw_surface, True, False)

            self.screen.blit(
                draw_surface,
                (int(self.position.x - self.radius), int(self.position.y - self.radius)),
            )

            if self.damage_effect_timer > 0:
                overlay = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 128))
                self.screen.blit(
                    overlay,
                    (int(self.position.x - self.radius), int(self.position.y - self.radius)),
                )
            return

        super().draw()

    def trigger_phase_change(self) -> None:
        """Ajusta la fase del boss según su vida restante."""
        health_ratio: float = self.health / max(self.max_health, 1.0)
        if health_ratio <= 0.33:
            self.phase = 3.0
            self.special_attacks = ["slam", "projectile_burst", "rage_shot"]
        elif health_ratio <= 0.66:
            self.phase = 2.0
            self.special_attacks = ["slam", "projectile_burst"]
        else:
            self.phase = 1.0
            self.special_attacks = ["slam"]

    def create_projectile(
        self,
        target_position: Vector2D,
        *,
        current_time: float = 0.0,
    ) -> Proyectile | None:
        """Crea un proyectil dirigido al objetivo si el cooldown lo permite."""
        if current_time < 0:
            raise ValueError("current_time no puede ser negativo")
        if not self.is_active:
            return None
        if (current_time - self._last_shot_time) < self.shot_cooldown:
            return None

        direction: Vector2D = target_position - self.position
        if direction.magnitude() == 0:
            return None

        projectile_stats = Stats(
            max_health=1.0,
            endurance=1.0,
            damage=self.attack_power * (1.0 + 0.5 * (self.phase - 1.0)),
            defense=0.0,
        )
        projectile = Proyectile(
            screen=self.screen,
            x=self.x,
            y=self.y,
            direction=direction,
            velocity=self.projectile_velocity,
            stats=projectile_stats,
            life_time=self.projectile_life_time,
        )
        self._last_shot_time = current_time
        return projectile

    def special_attack(
        self,
        player: object,
        *,
        current_time: float = 0.0,
    ) -> Proyectile | None:
        """Ejecuta el ataque especial principal del boss contra el jugador."""
        self.trigger_phase_change()
        if not hasattr(player, "position"):
            return None
        return self.create_projectile(player.position, current_time=current_time)