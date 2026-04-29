from __future__ import annotations

import pygame
from pathlib import Path
import re

from core.sprite import Sprite
from core.vector2d import Vector2D
from entities.proyectile import Proyectile
from inventory.inventory import Inventory
from inventory.item import Item
from stats.stats import Stats
from utils.spriteSheet import SpriteSheet


class Player(Sprite):
    """Entidad jugador con estadísticas, inventario y combate."""

    DEFAULT_COLOR: tuple[int, int, int] = (80, 150, 220)
    DEFAULT_RADIUS: int = 24
    DEFAULT_SHOT_COOLDOWN: float = 2
    DEFAULT_IMAGE: str = str(Path(__file__).parent.parent / "public" / "assets" / "player.gif")
    DEFAULT_ATLAS_IMAGE: str = str(Path(__file__).parent.parent / "public" / "assets" / "player_atlas.png")
    DEFAULT_ATLAS_XML: str = str(Path(__file__).parent.parent / "public" / "assets" / "player_atlas.xml")
    DEFAULT_PROJECTILE_VELOCITY: float = 900.0
    DEFAULT_PROJECTILE_LIFE_TIME: float = 4.0
    DEFAULT_ANIMATION_FPS: float = 10.0
    WALK_SPEED_THRESHOLD: float = 30.0
    RUN_SPEED_THRESHOLD: float = 170.0
    ANIMATION_FPS_BY_STATE: dict[str, float] = {
        "idle": 8.0,
        "walk": 12.0,
        "run": 15.0,
        "jump": 12.0,
        "hurt": 20.0,
    }

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
        self.shield_hp: float = 0.0
        self.shield_max_hp: float = 0.0
        self.shield_effect_timer: float = 0.0
        self.shield_pickup_timer: float = 0.0
        self.treasure_pickup_timer: float = 0.0
        self._motion_vx: float = 0.0
        self._motion_on_ground: bool = True
        self._facing_right: bool = True
        self._anim_state: str = "idle"
        self._anim_timer: float = 0.0
        self._anim_index: int = 0
        self._animation_sequences: dict[str, list[pygame.Surface]] = {
            "idle": [],
            "walk": [],
            "run": [],
            "jump": [],
            "hurt": [],
        }
        self._load_animation_atlas()

    def _extract_sort_index(self, frame_name: str) -> int:
        match = re.search(r"(\d+)", frame_name)
        return int(match.group(1)) if match is not None else 0

    def _load_animation_atlas(self) -> None:
        atlas = SpriteSheet(self.DEFAULT_ATLAS_IMAGE, self.DEFAULT_ATLAS_XML)
        frames = atlas.get_all()
        if not frames:
            return

        categorized: dict[str, list[tuple[str, pygame.Surface]]] = {
            "idle": [],
            "walk": [],
            "run": [],
            "jump": [],
            "hurt": [],
        }

        for name, frame in frames.items():
            lname = name.lower()
            if "idle" in lname:
                categorized["idle"].append((name, frame))
            elif "walk" in lname:
                categorized["walk"].append((name, frame))
            elif "run" in lname:
                categorized["run"].append((name, frame))
            elif "jump" in lname:
                categorized["jump"].append((name, frame))
            elif "hurt" in lname or "hit" in lname:
                categorized["hurt"].append((name, frame))

        for state, pairs in categorized.items():
            pairs.sort(key=lambda item: self._extract_sort_index(item[0]))
            self._animation_sequences[state] = [frame for _, frame in pairs]

        # Fallbacks para no dejar estados vacíos.
        if not self._animation_sequences["idle"]:
            any_frame = next(iter(frames.values()))
            self._animation_sequences["idle"] = [any_frame]
        if not self._animation_sequences["walk"]:
            self._animation_sequences["walk"] = self._animation_sequences["idle"]
        if not self._animation_sequences["run"]:
            self._animation_sequences["run"] = self._animation_sequences["walk"]
        if not self._animation_sequences["jump"]:
            self._animation_sequences["jump"] = self._animation_sequences["idle"]
        if not self._animation_sequences["hurt"]:
            self._animation_sequences["hurt"] = self._animation_sequences["idle"]

    def set_motion_state(self, vx: float, on_ground: bool) -> None:
        """Recibe estado de movimiento desde GameManager para animar al player."""
        self._motion_vx = vx
        self._motion_on_ground = on_ground
        if vx < -1e-3:
            self._facing_right = False
        elif vx > 1e-3:
            self._facing_right = True

    def _pick_animation_state(self) -> str:
        if self.damage_effect_timer > 0:
            return "hurt"
        if not self._motion_on_ground:
            return "jump"

        speed = abs(self._motion_vx)
        if speed >= self.RUN_SPEED_THRESHOLD:
            return "run"
        if speed >= self.WALK_SPEED_THRESHOLD:
            return "walk"
        return "idle"

    def _update_animation(self, delta_time: float) -> None:
        next_state = self._pick_animation_state()
        if next_state != self._anim_state:
            self._anim_state = next_state
            self._anim_timer = 0.0
            self._anim_index = 0

        frames = self._animation_sequences.get(self._anim_state, [])
        if len(frames) <= 1:
            return

        anim_fps = self.ANIMATION_FPS_BY_STATE.get(self._anim_state, self.DEFAULT_ANIMATION_FPS)
        frame_duration = 1.0 / max(anim_fps, 1.0)
        self._anim_timer += delta_time
        while self._anim_timer >= frame_duration:
            self._anim_timer -= frame_duration
            self._anim_index = (self._anim_index + 1) % len(frames)

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------

    def shoot(
        self,
        direction: Vector2D,
        current_time: float,
        *,
        projectile_velocity: float = DEFAULT_PROJECTILE_VELOCITY,
        projectile_life_time: float = DEFAULT_PROJECTILE_LIFE_TIME,
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
        """Recibe daño. El escudo absorbe primero; el resto se aplica a HP con defensa."""
        if damage < 0:
            raise ValueError("damage no puede ser negativo")

        # El escudo absorbe daño antes que la vida
        if self.shield_hp > 0:
            absorbed: float = min(self.shield_hp, damage)
            self.shield_hp -= absorbed
            damage -= absorbed
            if damage <= 0:
                return 0.0

        total_defense: float = self.stats.defense + self.shield_defense_boost
        for item in self.inventory.items:
            total_defense += item.defense_boost

        net_damage: float = max(0.0, damage - total_defense)
        self.health = max(0.0, self.health - net_damage)

        if net_damage > 0:
            self.damage_effect_timer = 0.2

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

        self._update_animation(delta_time)

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

        frames = self._animation_sequences.get(self._anim_state, [])
        if frames:
            frame = frames[self._anim_index % len(frames)]
            scaled_frame = pygame.transform.scale(
                frame,
                (self.radius * 2, self.radius * 2),
            )
            if not self._facing_right:
                scaled_frame = pygame.transform.flip(scaled_frame, True, False)
            self.screen.blit(
                scaled_frame,
                (int(self.position.x - self.radius), int(self.position.y - self.radius)),
            )
        elif self.image:
            self.draw_image()
            # Efectos de overlay
            if self.shield_pickup_timer > 0:
                overlay = pygame.Surface((self.radius * 2, self.radius * 2))
                overlay.set_alpha(128)  # Semi-transparente
                overlay.fill((100, 150, 255))  # Azul para recoger escudo
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

        # Overlays de pickup/escudo sobre cualquier frame.
        if self.shield_pickup_timer > 0:
            overlay = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            overlay.fill((100, 150, 255, 128))
            self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
        elif self.treasure_pickup_timer > 0:
            overlay = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            overlay.fill((255, 255, 100, 128))
            self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
        elif self.shield_effect_timer > 0:
            overlay = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            overlay.fill((100, 150, 255, 128))
            self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))

    def collect(self, collectible: object) -> None:
        """Interactúa con un coleccionable del mundo."""
        if hasattr(collectible, "collect") and callable(collectible.collect):
            collectible.collect()

    def _is_shield_item(self, item: Item) -> bool:
        """Determina si un item debe comportarse como escudo consumible."""
        item_name = item.name.lower()
        item_description = item.description.lower()
        return "escudo" in item_name or "shield" in item_name or "escudo" in item_description

    def _apply_shield_item_effect(self, item: Item) -> None:
        """Convierte un item de escudo en puntos para la barra de escudo."""
        shield_points: float = max(10.0, item.defense_boost * 10.0)
        self.shield_max_hp = max(self.shield_max_hp, self.shield_hp) + shield_points
        self.shield_hp = min(self.shield_hp + shield_points, self.shield_max_hp)
        self.shield_effect_timer = max(self.shield_effect_timer, 2.0)
        self.trigger_shield_pickup_effect()

    def use_item(self, item: Item) -> bool:
        """Usa un ítem del inventario. Retorna True si se usó correctamente."""
        if item not in self.inventory.items:
            return False

        self.stats.damage += item.attack_boost
        self.stats.defense += item.defense_boost

        if self._is_shield_item(item):
            self._apply_shield_item_effect(item)

        previous_health = self.health
        self.health = min(self.health + item.damage, self.stats.max_health)
        if self.health > previous_health:
            self.trigger_treasure_pickup_effect()

        self.inventory.remove_item(item)
        return True

    # ------------------------------------------------------------------
    # Economía
    # ------------------------------------------------------------------

    def buy_item(self, item: Item, store: object) -> bool:
        """Compra un ítem de una tienda. Retorna True si la compra fue exitosa."""
        if hasattr(store, "buy") and callable(store.buy):
            return bool(store.buy(item, self))

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
        if hasattr(store, "sell") and callable(store.sell):
            return bool(store.sell(item, self))

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
