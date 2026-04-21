import random
from typing import List

import pygame

from combat.shield import Shield
from core.vector2d import Vector2D
from entities.enemy import Enemy
from entities.trap import Trap
from entities.treasure import Treasure
from world.camera import Camera
from world.platform import Platform


class World:
    """Contiene y dibuja todas las plataformas del nivel."""

    CAMERA_SCROLL_SPEED: float = 200.0
    PLATFORM_WIDTH: int = 120
    PLATFORM_HEIGHT: int = 20
    PLATFORM_COLOR: tuple[int, int, int] = (100, 150, 100)
    GROUND_Y: float = 550.0
    PLATFORM_SPACING: int = 180
    DEFAULT_ENEMY_COUNT: int = 6
    DEFAULT_COLLECTIBLE_COUNT: int = 10
    PLATFORM_TOP_OFFSET: float = 30.0
    DEFAULT_SHIELD_DURATION: float = 10.0
    DEFAULT_SHIELD_DEFENSE: float = 5.0
    DEFAULT_TRAP_DAMAGE: float = 20.0
    DEFAULT_TRAP_RANGE: float = 60.0
    DEFAULT_TREASURE_BASE_VALUE: float = 50.0
    RESPAWN_VERTICAL_OFFSET: float = 30.0

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Inicializa el mundo con la cámara y plataformas iniciales.

        Args:
            screen (pygame.Surface): Superficie de renderizado del juego.
        """
        self.screen: pygame.Surface = screen
        self.camera: Camera = Camera(scroll_speed=self.CAMERA_SCROLL_SPEED)
        self.platforms: List[Platform] = []
        self.enemy_spawn_points: List[Vector2D] = []
        self.collectible_spawn_points: List[Vector2D] = []
        self.collectibles: List[Shield | Trap | Treasure] = []
        self.enemies: List[Enemy] = []
        self._rng: random.Random = random.Random()
        self._initialize_platforms()

    def _initialize_platforms(self) -> None:
        """Genera las plataformas iniciales del nivel."""
        screen_width: int = self.screen.get_width()
        # Genera plataformas desde el inicio hasta el doble del ancho de pantalla
        max_x: float = screen_width * 2.5

        current_x: float = 0.0
        while current_x < max_x:
            platform: Platform = Platform(
                world_x=current_x,
                world_y=self.GROUND_Y,
                width=self.PLATFORM_WIDTH,
                height=self.PLATFORM_HEIGHT,
                color=self.PLATFORM_COLOR,
            )
            self.platforms.append(platform)
            current_x += self.PLATFORM_SPACING

    def add_platform(self, platform: Platform) -> None:
        """
        Agrega una plataforma al mundo.

        Args:
            platform (Platform): Plataforma a agregar.
        """
        self.platforms.append(platform)

    def generate(
        self,
        seed: int | None = None,
        enemy_count: int = DEFAULT_ENEMY_COUNT,
        collectible_count: int = DEFAULT_COLLECTIBLE_COUNT,
    ) -> None:
        """
        Regenera el mundo base y distribuye enemigos/objetos de forma aleatoria.

        Args:
            seed (int | None): Semilla opcional para generación determinística.
            enemy_count (int): Cantidad de enemigos a ubicar.
            collectible_count (int): Cantidad de objetos a ubicar.
        """
        # Reinicia la cámara para volver a renderizar desde el inicio del nivel.
        self.camera.offset.x = 0.0
        self.camera.offset.y = 0.0
        self.platforms = []
        self.enemy_spawn_points = []
        self.collectible_spawn_points = []
        self.collectibles = []
        self.enemies = []
        self._initialize_platforms()
        rng: random.Random = random.Random(seed)
        self._rng = rng
        self.place_enemies(enemy_count, rng=rng)
        self.place_collectibles(collectible_count, rng=rng)
        self._instantiate_collectibles(rng)
        self._instantiate_enemies(rng)

    def _random_x_on_platform(self, platform: Platform) -> float:
        """Retorna una coordenada X válida para colocar una entidad sobre una plataforma."""
        x_min: float = platform.x + 8.0
        x_max: float = platform.x + platform.width - 8.0
        if x_min > x_max:
            x_min = platform.x
            x_max = platform.x + platform.width
        return self._rng.uniform(x_min, x_max)

    def _spawn_entities_for_platform(self, platform: Platform) -> None:
        """Regenera un enemy y un collectible al crear una nueva plataforma."""
        spawn_y: float = platform.y - self.RESPAWN_VERTICAL_OFFSET

        enemy_point: Vector2D = Vector2D(self._random_x_on_platform(platform), spawn_y)
        self.enemy_spawn_points.append(enemy_point)
        self._instantiate_enemies(self._rng)

        collectible_point: Vector2D = Vector2D(self._random_x_on_platform(platform), spawn_y)
        self.collectible_spawn_points.append(collectible_point)
        self._instantiate_collectibles(self._rng)

    def place_enemies(
        self,
        count: int = DEFAULT_ENEMY_COUNT,
        rng: random.Random | None = None,
    ) -> List[Vector2D]:
        """
        Ubica enemigos en posiciones válidas sobre plataformas existentes.

        Args:
            count (int): Cantidad de enemigos a distribuir.
            rng (random.Random | None): Generador aleatorio opcional.

        Returns:
            List[Vector2D]: Posiciones generadas para enemigos.
        """
        self.enemy_spawn_points = self._place_points_on_platforms(
            count=count,
            vertical_offset=self.PLATFORM_TOP_OFFSET,
            rng=rng,
        )
        return self.enemy_spawn_points

    def place_collectibles(
        self,
        count: int = DEFAULT_COLLECTIBLE_COUNT,
        rng: random.Random | None = None,
    ) -> List[Vector2D]:
        """
        Ubica objetos recolectables en posiciones válidas sobre plataformas.

        Args:
            count (int): Cantidad de objetos a distribuir.
            rng (random.Random | None): Generador aleatorio opcional.

        Returns:
            List[Vector2D]: Posiciones generadas para recolectables.
        """
        self.collectible_spawn_points = self._place_points_on_platforms(
            count=count,
            vertical_offset=self.PLATFORM_TOP_OFFSET,
            rng=rng,
        )
        return self.collectible_spawn_points

    def _instantiate_collectibles(self, rng: random.Random) -> None:
        """Crea instancias reales de collectibles basadas en spawn points."""
        start_index: int = len(self.collectibles)
        for point in self.collectible_spawn_points[start_index:]:
            collectible_type: int = rng.randint(0, 2)
            if collectible_type == 0:
                collectible = Shield(
                    self.screen,
                    point.x,
                    point.y,
                    duration=self.DEFAULT_SHIELD_DURATION,
                    defense_boost=self.DEFAULT_SHIELD_DEFENSE,
                    description="Escudo encontrado",
                )
            elif collectible_type == 1:
                collectible = Trap(
                    self.screen,
                    point.x,
                    point.y,
                    explosion_damage=self.DEFAULT_TRAP_DAMAGE,
                    explosion_range=self.DEFAULT_TRAP_RANGE,
                    description="Trampa peligrosa",
                )
            else:
                treasure_value: float = self.DEFAULT_TREASURE_BASE_VALUE * rng.uniform(0.5, 2.0)
                collectible = Treasure(
                    self.screen,
                    point.x,
                    point.y,
                    name=f"Tesoro #{len(self.collectibles)}",
                    monetary_value=treasure_value,
                )
            self.collectibles.append(collectible)

    def _instantiate_enemies(self, rng: random.Random) -> None:
        """Crea instancias reales de Enemy basadas en los spawn points."""
        enemy_names: list[str] = ["Golem", "Slime", "Skeleton", "Orc", "Bat", "Spider"]
        enemy_types: list[str] = ["terrestre", "terrestre", "terrestre", "terrestre", "volador", "terrestre"]
        start_index: int = len(self.enemies)
        for i, point in enumerate(self.enemy_spawn_points[start_index:], start=start_index):
            idx: int = i % len(enemy_names)
            enemy: Enemy = Enemy(
                self.screen,
                point,
                name=f"{enemy_names[idx]} #{i + 1}",
                enemy_type=enemy_types[idx],
                health=rng.uniform(60.0, 120.0),
                attack_power=rng.uniform(8.0, 20.0),
                defense=rng.uniform(2.0, 8.0),
            )
            self.enemies.append(enemy)

    def _place_points_on_platforms(
        self,
        count: int,
        vertical_offset: float,
        rng: random.Random | None = None,
    ) -> List[Vector2D]:
        """Genera puntos aleatorios sobre plataformas para entidades del mundo."""
        if count <= 0 or not self.platforms:
            return []

        random_generator: random.Random = rng if rng is not None else random
        points: List[Vector2D] = []

        for _ in range(count):
            platform: Platform = random_generator.choice(self.platforms)
            x_min: float = platform.x + 8.0
            x_max: float = platform.x + platform.width - 8.0
            if x_min > x_max:
                x_min = platform.x
                x_max = platform.x + platform.width
            world_x: float = random_generator.uniform(x_min, x_max)
            world_y: float = platform.y - vertical_offset
            points.append(Vector2D(world_x, world_y))

        return points

    def update(self, delta_time: float) -> None:
        """
        Actualiza el estado del mundo (movimiento de cámara y entidades).

        Args:
            delta_time (float): Tiempo transcurrido en segundos desde el
                                último frame.
        """
        self.camera.update(delta_time)
        self._generate_distant_platforms()
        for collectible in self.collectibles:
            if collectible.is_active:
                collectible.update(delta_time)
        for enemy in self.enemies:
            if not enemy.is_defeated:
                enemy.update(delta_time)

    def _generate_distant_platforms(self) -> None:
        """
        Genera nuevas plataformas cuando el scroll se acerca al límite.
        Evita que el jugador se quede sin plataformas.
        """
        if not self.platforms:
            return

        screen_width: int = self.screen.get_width()
        furthest_x: float = max(
            platform.x for platform in self.platforms
        )
        camera_right_edge: float = (
            self.camera.offset.x + screen_width
        )

        # Si el borde derecho visible se acerca al final de las plataformas
        if camera_right_edge > furthest_x - screen_width:
            next_x: float = furthest_x + self.PLATFORM_SPACING
            new_platform: Platform = Platform(
                world_x=next_x,
                world_y=self.GROUND_Y,
                width=self.PLATFORM_WIDTH,
                height=self.PLATFORM_HEIGHT,
                color=self.PLATFORM_COLOR,
            )
            self.platforms.append(new_platform)
            self._spawn_entities_for_platform(new_platform)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset_x: float,
    ) -> None:
        """
        Renderiza todas las plataformas y collectibles visibles del mundo.

        Args:
            surface (pygame.Surface): Superficie donde renderizar.
            camera_offset_x (float): Offset X de la cámara para aplicar scroll.
        """
        screen_width: int = surface.get_width()

        for platform in self.platforms:
            if platform.is_on_screen(screen_width, camera_offset_x):
                platform.draw(surface, camera_offset_x)

        for collectible in self.collectibles:
            if collectible.is_active:
                screen_x: float = collectible.x - camera_offset_x
                if -50 <= screen_x <= screen_width + 50:
                    collectible.draw()

        for enemy in self.enemies:
            if not enemy.is_defeated:
                screen_x = enemy.x - camera_offset_x
                if -50 <= screen_x <= screen_width + 50:
                    enemy.draw()
