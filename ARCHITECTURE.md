# Arquitectura del Videojuego — Lineamientos de Desarrollo

> **Versión:** 1.0 | **Motor:** Python 3.11+ / Pygame 2.x  
> **Este documento es la fuente de verdad del proyecto. Todo código nuevo y toda IA asistente deben regirse por él.**

---

## Índice

1. [Principios Generales](#1-principios-generales)
2. [Estructura del Proyecto](#2-estructura-del-proyecto)
3. [Diagrama de Clases y Responsabilidades](#3-diagrama-de-clases-y-responsabilidades)
4. [Convenciones de Código](#4-convenciones-de-código)
5. [Tipado Estricto](#5-tipado-estricto)
6. [Nombres Autodocumentados](#6-nombres-autodocumentados)
7. [Principios SOLID](#7-principios-solid)
8. [DRY — Don't Repeat Yourself](#8-dry--dont-repeat-yourself)
9. [Manejo de Errores](#9-manejo-de-errores)
10. [Instrucciones para Uso de IA](#10-instrucciones-para-uso-de-ia)

---

## 1. Principios Generales

El proyecto sigue un diseño orientado a objetos con responsabilidades claras por clase. Cada módulo debe ser:

- **Legible sin comentarios extra:** si el nombre del método o variable necesita un comentario para ser entendido, debe renombrarse.
- **Tipado completo:** ningún parámetro, atributo ni retorno puede omitir su tipo.
- **Cohesivo:** cada clase hace una sola cosa y la hace bien (Single Responsibility).
- **Testeable de forma aislada:** las dependencias se inyectan, no se crean internamente cuando sea posible.

---

## 2. Estructura del Proyecto

```
videojuego/
├── main.py                  # Punto de entrada: instancia GameManager y llama exec()
├── arquitectura.md          # Este archivo — fuente de verdad
├── core/
│   ├── vector2d.py          # Clase Vector2D (matemáticas 2D)
│   ├── sprite.py            # Clase base Sprite
│   └── game_manager.py      # Clase GameManager (bucle principal)
├── entities/
│   ├── player.py            # Clase Player
│   ├── enemy.py             # Clase Enemy
│   ├── collectible.py       # Clase base Collectible
│   ├── trap.py              # Clase Trap
│   └── treasure.py          # Clase Treasure
├── combat/
│   ├── weapon.py            # Clase Weapon
│   ├── shield.py            # Clase Shield
│   └── projectile.py        # Clase Projectile
├── world/
│   ├── world.py             # Clase World
│   ├── platform.py          # Clase Platform
│   └── camera.py            # Clase Camera
├── inventory/
│   ├── inventory.py         # Clase Inventory
│   ├── item.py              # Clase Item
│   └── store.py             # Clase Store
└── stats/
    └── stats.py             # Clase Stats
```

**Regla:** un archivo = una clase principal. No agrupar clases no relacionadas en el mismo módulo.

---

## 3. Diagrama de Clases y Responsabilidades

### Jerarquía de herencia

```
Sprite (base)
 ├── Collectible
 │    ├── Trap
 │    ├── Treasure
 │    └── Enemy
 ├── Weapon
 ├── Shield
 └── Projectile
```

### Composición (has-a)

```
GameManager ◆── World
GameManager ◆── Player
GameManager ◆── Enemy
Player      ◆── Inventory
Player      ◆── Stats
World       ◆── List[Platform]
Store       ◆── List[Item]
```

### Uso (uses)

```
Sprite      ──> Vector2D  (posición)
Camera      ──> Vector2D  (offset, velocidad de scroll)
Platform    ──> Vector2D  (pos, size)
Enemy       ──> Vector2D  (size, velocity, pos)
GameManager ──> Stats      (<<use>> — consulta estadísticas del jugador)
Player      ──> Vector2D  (hereda de Sprite)
```

### Responsabilidades por clase

| Clase | Responsabilidad única |
|---|---|
| `Vector2D` | Matemáticas de vectores 2D: suma, resta, normalización, distancia, lerp, dot |
| `Sprite` | Estado y dibujo base de cualquier entidad visual en pantalla |
| `Player` | Estado del jugador: dinero, salud, inventario, estadísticas |
| `Enemy` | Comportamiento y movimiento del enemigo en el mundo |
| `Collectible` | Lógica compartida de objetos recogibles (activación, detección de colisión) |
| `Trap` | Efecto negativo al contacto con el jugador |
| `Treasure` | Recompensa al ser recogido por el jugador |
| `Weapon` | Disparar proyectiles hacia una dirección |
| `Shield` | Absorber o reducir daño recibido por el portador |
| `Projectile` | Moverse en línea recta y detectar colisión con entidades |
| `Stats` | Contener y validar las estadísticas de una entidad (salud máx., resistencia, daño) |
| `Inventory` | Gestionar la lista de ítems que posee el jugador |
| `Item` | Representar un ítem con precio y atributos propios |
| `Store` | Exponer ítems disponibles para compra y procesar transacciones |
| `Camera` | Traducir coordenadas del mundo a coordenadas de pantalla y viceversa |
| `Platform` | Representar una superficie sobre la que el jugador puede pararse |
| `World` | Contener y dibujar todas las plataformas del nivel |
| `GameManager` | Orquestar el bucle de juego: eventos, actualización, renderizado |

---

## 4. Convenciones de Código

### Estilo general

- Seguir **PEP 8** estrictamente.
- Máximo **80 caracteres** por línea.
- **Snake_case** para variables y funciones; **PascalCase** para clases; **SCREAMING_SNAKE_CASE** para constantes.
- Usar `__slots__` en clases de datos frecuentemente instanciadas (`Vector2D`, `Stats`, `Item`) para reducir uso de memoria.

### Docstrings

Toda clase pública debe tener un docstring de una línea que describa su responsabilidad. Los métodos complejos (más de 10 líneas) llevan docstring con descripción, parámetros y retorno.

```python
# ✅ Correcto
class Camera:
    """Traduce coordenadas del mundo a coordenadas de pantalla y viceversa."""

    def apply(self, world_x: float) -> float:
        """Convierte una coordenada X del mundo a coordenada X de pantalla."""
        return world_x - self.offset.x

# ❌ Incorrecto — sin docstring y nombre ambiguo
class Cam:
    def conv(self, x):
        return x - self.off.x
```

### Imports

Ordenar en tres bloques separados por línea en blanco:

```python
# 1. Librería estándar
from typing import Optional

# 2. Dependencias externas
import pygame

# 3. Módulos propios
from core.vector2d import Vector2D
from stats.stats import Stats
```

---

## 5. Tipado Estricto

**Regla:** ningún parámetro, atributo de clase ni valor de retorno puede carecer de anotación de tipo. El proyecto se valida con `mypy --strict`.

### Tipos permitidos en anotaciones

```python
from typing import Optional, Union
```

### Ejemplos por clase clave

#### `Vector2D`

```python
from __future__ import annotations
from typing import Union

class Vector2D:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: Union[int, float]) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: Union[int, float]) -> Vector2D:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: Union[int, float]) -> Vector2D:
        if scalar == 0:
            raise ZeroDivisionError("No se puede dividir un Vector2D por cero.")
        return Vector2D(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vector2D:
        return Vector2D(-self.x, -self.y)

    def __repr__(self) -> str:
        return f"Vector2D(x={self.x:.2f}, y={self.y:.2f})"

    def normalizar(self) -> Vector2D:
        """Retorna el vector unitario. Si la magnitud es 0, retorna Vector2D(0, 0)."""
        mag: float = self.magnitud()
        return self / mag if mag > 0 else Vector2D(0.0, 0.0)

    def magnitud(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def distancia_a(self, other: Vector2D) -> float:
        return (other - self).magnitud()

    def lerp(self, other: Vector2D, t: float) -> Vector2D:
        """Interpolación lineal entre este vector y `other` con factor `t` en [0, 1]."""
        return self + (other - self) * t

    def dot(self, other: Vector2D) -> float:
        return self.x * other.x + self.y * other.y

    def to_tuple(self) -> tuple[int, int]:
        return (int(self.x), int(self.y))

    @classmethod
    def from_tuple(cls, t: tuple[int, int]) -> Vector2D:
        return cls(float(t[0]), float(t[1]))
```

#### `Stats`

```python
from dataclasses import dataclass, field

@dataclass
class Stats:
    """Estadísticas de combate de una entidad."""
    max_health: float
    endurance: float
    damage: float

    def __post_init__(self) -> None:
        if self.max_health <= 0:
            raise ValueError(f"max_health debe ser positivo, se recibió {self.max_health}.")
        if self.endurance < 0:
            raise ValueError("endurance no puede ser negativa.")
        if self.damage < 0:
            raise ValueError("damage no puede ser negativo.")
```

#### `Sprite` (clase base)

```python
import pygame
from core.vector2d import Vector2D

class Sprite:
    """Entidad visual base para todo objeto renderizable en pantalla."""

    def __init__(
        self,
        screen: pygame.Surface,
        x: float,
        y: float,
        color: tuple[int, int, int],
        radius: int,
    ) -> None:
        self.screen: pygame.Surface = screen
        self.position: Vector2D = Vector2D(x, y)
        self.color: tuple[int, int, int] = color
        self.is_active: bool = True
        self.image: Optional[pygame.Surface] = None
        self.radius: int = radius

    @property
    def x(self) -> float:
        return self.position.x

    @property
    def y(self) -> float:
        return self.position.y

    def keep_on_screen(self) -> None:
        """Limita la posición del sprite al área visible de la pantalla."""
        screen_width, screen_height = self.screen.get_size()
        self.position.x = max(self.radius, min(screen_width - self.radius, self.position.x))
        self.position.y = max(self.radius, min(screen_height - self.radius, self.position.y))

    def draw(self) -> None:
        """Renderiza el sprite en pantalla. Sobrescribir en subclases para lógica personalizada."""
        if self.image:
            self.screen.blit(self.image, self.position.to_tuple())
        else:
            pygame.draw.circle(self.screen, self.color, self.position.to_tuple(), self.radius)

    def update(self) -> None:
        """Actualiza el estado del sprite. Sobrescribir en subclases."""
        pass
```

#### `Player`

```python
from typing import Optional
import pygame
from core.sprite import Sprite
from core.vector2d import Vector2D
from inventory.inventory import Inventory
from stats.stats import Stats

class Player(Sprite):
    """Entidad controlada por el jugador con inventario, salud y estadísticas."""

    INITIAL_CASH: int = 100

    def __init__(
        self,
        screen: pygame.Surface,
        spawn_position: Vector2D,
        initial_stats: Stats,
    ) -> None:
        super().__init__(
            screen=screen,
            x=spawn_position.x,
            y=spawn_position.y,
            color=(0, 128, 255),
            radius=16,
        )
        self.cash: int = self.INITIAL_CASH
        self.health: float = initial_stats.max_health
        self.inventory: Inventory = Inventory()
        self.stats: Stats = initial_stats

    def receive_damage(self, raw_damage: float) -> None:
        """Aplica daño mitigado por la resistencia del jugador."""
        mitigated_damage: float = max(0.0, raw_damage - self.stats.endurance)
        self.health = max(0.0, self.health - mitigated_damage)
        if self.health <= 0:
            self.is_active = False

    def is_alive(self) -> bool:
        return self.health > 0 and self.is_active
```

#### `Camera`

```python
from core.vector2d import Vector2D

class Camera:
    """Traduce coordenadas del mundo a coordenadas de pantalla y viceversa."""

    def __init__(self, scroll_speed: float = 1.0) -> None:
        self.offset: Vector2D = Vector2D(0.0, 0.0)
        self.scroll_speed: float = scroll_speed

    def update(self) -> None:
        """Actualiza la posición del offset de la cámara (seguimiento del jugador, etc.)."""
        pass

    def apply(self, world_x: float) -> float:
        """Convierte una coordenada X del mundo a coordenada X de pantalla."""
        return world_x - self.offset.x

    def to_world(self, screen_x: float) -> float:
        """Convierte una coordenada X de pantalla a coordenada X del mundo."""
        return screen_x + self.offset.x
```

#### `GameManager`

```python
import pygame
from core.vector2d import Vector2D
from entities.player import Player
from entities.enemy import Enemy
from world.world import World
from stats.stats import Stats

class GameManager:
    """Orquesta el bucle principal de juego: eventos, actualización y renderizado."""

    TARGET_FPS: int = 60

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.is_playing: bool = False

        initial_stats = Stats(max_health=100.0, endurance=5.0, damage=15.0)
        self.player: Player = Player(
            screen=screen,
            spawn_position=Vector2D(100.0, 300.0),
            initial_stats=initial_stats,
        )
        self.enemy: Enemy = Enemy(
            world_pos=Vector2D(500.0, 300.0),
        )
        self.world: World = World(screen=screen)

    def start_game(self) -> None:
        self.is_playing = True

    def handle_event(self) -> None:
        """Procesa todos los eventos de pygame en el frame actual."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_playing = False

    def update(self, delta_time: float) -> None:
        """Actualiza el estado de todos los objetos del juego."""
        self.player.update()
        self.enemy.update()
        self.world.update()

    def draw(self) -> None:
        """Renderiza todos los objetos del juego en el orden correcto."""
        self.screen.fill((30, 30, 30))
        self.world.draw(surface=self.screen, camera=self.world.camera)
        self.player.draw()
        self.enemy.draw()
        pygame.display.flip()

    def exec(self) -> None:
        """Inicia y mantiene el bucle principal del juego."""
        self.start_game()
        while self.is_playing:
            delta_time: float = self.clock.tick(self.TARGET_FPS) / 1000.0
            self.handle_event()
            self.update(delta_time)
            self.draw()
```

---

## 6. Nombres Autodocumentados

### Variables

El nombre debe explicar qué contiene, sin abreviaciones salvo convenciones ampliamente conocidas (`dt` para delta time, `x`/`y` para coordenadas).

```python
# ✅ Correcto
remaining_health: float = player.health - received_damage
distance_to_enemy: float = player.position.distancia_a(enemy.position)
is_player_in_jump_range: bool = distance_to_enemy < JUMP_ATTACK_THRESHOLD

# ❌ Incorrecto — abreviado e ilegible
rem: float = p.hp - dmg
d: float = p.pos.distancia_a(e.pos)
flag: bool = d < THRESH
```

### Métodos

Usar verbos que describan la acción. Si el método retorna un booleano, comenzar con `is_`, `has_`, `can_`.

```python
# ✅ Correcto
def calculate_mitigated_damage(self, raw_damage: float) -> float: ...
def is_within_attack_range(self, target: Sprite) -> bool: ...
def collect_treasure(self, treasure: Treasure) -> None: ...

# ❌ Incorrecto
def calc(self, d: float) -> float: ...
def check(self, t: Sprite) -> bool: ...
def do_thing(self, tr) -> None: ...
```

### Constantes

Todas las constantes de configuración van en `SCREAMING_SNAKE_CASE` al nivel del módulo o como atributos de clase.

```python
# ✅ Correcto (en game_manager.py o config.py)
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
GRAVITY_ACCELERATION: float = 980.0  # píxeles/s²
JUMP_ATTACK_THRESHOLD: float = 64.0

# ❌ Incorrecto — número mágico incrustado
if distance < 64.0:  # ¿por qué 64?
    ...
```

---

## 7. Principios SOLID

### S — Single Responsibility

Cada clase tiene exactamente **una razón para cambiar**.

```python
# ✅ Correcto — Stats solo valida y contiene estadísticas
@dataclass
class Stats:
    max_health: float
    endurance: float
    damage: float

# ❌ Incorrecto — Stats NO debe calcular daño ni renderizar barras
class Stats:
    def render_health_bar(self, screen: pygame.Surface) -> None: ...  # responsabilidad de UI
    def apply_damage_to_player(self, player: Player) -> None: ...     # responsabilidad de Player
```

### O — Open/Closed

Las clases están **abiertas para extensión, cerradas para modificación**. Usar herencia o composición para agregar comportamiento sin romper el existente.

```python
# ✅ Correcto — nueva entidad sin modificar Sprite
class Trap(Collectible):
    def __init__(self, world_pos: Vector2D, damage_on_contact: float) -> None:
        super().__init__(world_pos=world_pos)
        self.damage_on_contact: float = damage_on_contact

    def on_player_contact(self, player: Player) -> None:
        player.receive_damage(self.damage_on_contact)
        self.is_active = False
```

### L — Liskov Substitution

Las subclases deben poder usarse donde se usa la clase padre sin romper el comportamiento.

```python
# ✅ Correcto — Treasure y Trap son Collectible intercambiables para el World
def activate_collectible(collectible: Collectible, player: Player) -> None:
    if collectible.is_active:
        collectible.on_player_contact(player)
```

### I — Interface Segregation

No forzar a las clases a implementar métodos que no necesitan. Usar clases base pequeñas o protocolos.

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

class Updatable(Protocol):
    def update(self) -> None: ...

# Enemy implementa ambas; Item solo implementa ni draw() ni update() porque no lo necesita
```

### D — Dependency Inversion

Las clases de alto nivel (`GameManager`) no dependen de implementaciones concretas; reciben dependencias por constructor.

```python
# ✅ Correcto — GameManager recibe screen, no crea pygame internamente
class GameManager:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

# En main.py
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
manager = GameManager(screen=screen)
manager.exec()
```

---

## 8. DRY — Don't Repeat Yourself

### Ejemplo: detección de colisión

En lugar de repetir la lógica de colisión circular en `Trap`, `Treasure` y `Enemy`, se centraliza en `Sprite` o en una función de utilidad:

```python
# core/collision.py
def are_circles_overlapping(
    position_a: Vector2D,
    radius_a: float,
    position_b: Vector2D,
    radius_b: float,
) -> bool:
    """Retorna True si dos círculos definidos por posición y radio se solapan."""
    return position_a.distancia_a(position_b) < (radius_a + radius_b)

# Uso en Enemy, Trap, Treasure — sin duplicar la fórmula
from core.collision import are_circles_overlapping

if are_circles_overlapping(self.position, self.radius, player.position, player.radius):
    self.on_player_contact(player)
```

### Ejemplo: conversión de coordenadas

La cámara centraliza toda la lógica de proyección. Ninguna clase debe calcular `world_x - camera.offset.x` por su cuenta:

```python
# ✅ Correcto — Platform usa Camera.apply()
def draw(self, surface: pygame.Surface, camera: Camera) -> None:
    screen_x: float = camera.apply(self.pos.x)
    screen_y: float = camera.apply(self.pos.y)
    pygame.draw.rect(surface, (180, 140, 80), (screen_x, screen_y, *self.size.to_tuple()))

# ❌ Incorrecto — duplicar la fórmula en Platform
def draw(self, surface: pygame.Surface, camera_offset_x: float) -> None:
    screen_x: float = self.pos.x - camera_offset_x  # lógica que ya vive en Camera
```

---

## 9. Manejo de Errores

- Preferir excepciones descriptivas sobre valores centinela (`-1`, `None`) para errores irrecuperables.
- Validar en `__post_init__` o `__init__` cuando los invariantes de la clase deben cumplirse siempre.
- Usar `Optional[T]` solo cuando la ausencia de valor es un estado legítimo del negocio.

```python
# ✅ Correcto
class Inventory:
    def get_item_by_name(self, item_name: str) -> Optional[Item]:
        """Retorna el ítem si existe en el inventario, None si no."""
        return next((item for item in self._items if item.name == item_name), None)

# ❌ Incorrecto — retornar -1 o lanzar KeyError genérico
def get_item(self, name):
    if name not in self._items:
        return -1  # el llamador no sabrá qué significa -1
```

---

## 10. Instrucciones para Uso de IA

> Esta sección define cómo cualquier herramienta de IA (GitHub Copilot, Claude, ChatGPT, Cursor, etc.) debe comportarse al asistir en el desarrollo de este proyecto.

### 10.1 Regla principal

**Toda sugerencia de IA debe ser compatible con este documento antes de ser aceptada.**  
Si una sugerencia viola cualquier lineamiento aquí descrito, debe rechazarse o ajustarse antes de integrarse.

### 10.2 Instrucciones que la IA debe seguir siempre

La IA **debe**:

1. **Respetar el diagrama de clases.** Antes de crear o modificar una clase, verificar que su responsabilidad, atributos y relaciones coincidan con la sección 3 de este documento. No inventar clases nuevas ni mover responsabilidades sin justificación explícita.

2. **Tipar todos los parámetros y retornos.** Ningún parámetro puede quedar sin tipo. Si el tipo no es obvio, preguntar antes de generar el código.

3. **Usar nombres autodocumentados.** Si sugiere un nombre abreviado o genérico (`flag`, `val`, `tmp`, `data`, `obj`), debe corregirse automáticamente al nombre descriptivo correcto.

4. **No duplicar lógica existente.** Antes de generar una función, verificar si ya existe en otro módulo. Si existe, usarla en lugar de reimplementarla.

5. **Producir métodos de tamaño mínimo.** Cada método debe hacer una sola cosa. Si una función sugerida supera las 20 líneas sin ser un bucle principal, debe dividirse en subfunciones con nombres descriptivos.

6. **Seguir la jerarquía de clases del diagrama.** No romper herencia ni composición definida. Si `Enemy` extiende `Collectible`, la IA no debe sugerir que extienda directamente `Sprite`.

7. **Generar código en español para nombres de dominio del juego** (nombres de métodos de negocio, variables del dominio del juego) y en inglés solo para convenciones técnicas universales (`__init__`, `update`, `draw`, `screen`, etc.) — a menos que el equipo decida un idioma único, en cuyo caso se actualiza este documento.

8. **No usar números mágicos.** Todo valor literal que no sea `0`, `1`, `-1` o `True`/`False` debe asignarse a una constante con nombre descriptivo.

### 10.3 La IA NO debe

- Crear atributos de instancia sin tipo anotado.
- Agregar lógica de renderizado en clases que no sean `Sprite` o sus subclases.
- Implementar lógica de física o movimiento en `GameManager` (corresponde a `Player` o `Enemy`).
- Mezclar responsabilidades de `Camera` con `World` o `Sprite`.
- Generar código sin respetar el principio de responsabilidad única.
- Sugerir el patrón Singleton para `GameManager` — la instancia se maneja en `main.py`.
- Añadir dependencias externas al proyecto sin indicarlo explícitamente en su respuesta.

### 10.4 Prompt de contexto recomendado para la IA

Al iniciar una sesión de desarrollo asistida por IA, incluir el siguiente prompt de contexto:

```
Estás asistiendo en el desarrollo de un videojuego en Python con Pygame.
El proyecto sigue las reglas definidas en arquitectura.md:
- Tipado estricto en todos los parámetros, atributos y retornos (PEP 484, mypy --strict).
- Nombres autodocumentados: sin abreviaciones, sin variables genéricas.
- Principios SOLID y DRY.
- Diagrama de clases fijo: Sprite como base, Player/Enemy/Collectible como entidades,
  Camera para proyección, GameManager como orquestador, Vector2D para matemáticas 2D.
- Ninguna clase debe asumir responsabilidades ajenas a las definidas en el diagrama.
Antes de generar código, confirma que cumple todos estos lineamientos.
```

### 10.5 Checklist de revisión para código generado por IA

Antes de aceptar cualquier bloque de código sugerido por IA, verificar:

- [ ] ¿Todos los parámetros y retornos tienen tipo anotado?
- [ ] ¿Los nombres de variables y métodos son descriptivos y en el idioma correcto?
- [ ] ¿La clase modificada o creada tiene una sola responsabilidad?
- [ ] ¿Se usa alguna función o lógica que ya existe en otro módulo (DRY)?
- [ ] ¿La herencia y composición respetan el diagrama de clases de la sección 3?
- [ ] ¿Hay números mágicos que deberían ser constantes?
- [ ] ¿El código pasa `mypy --strict` sin errores?

---

*Fin del documento — última actualización: versión inicial.*