# Módulo World

Módulo responsable de la mecánica del mundo del videojuego, incluyendo scroll constante, plataformas y la cámara.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         GameManager                              │
│  update(delta_time)                                              │
│    ↓                                                              │
│    world.update(delta_time)                                      │
│                                                              │
│  draw()                                                          │
│    ↓                                                              │
│    world.draw(surface, camera_offset_x)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    World                                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ camera: Camera                                              │ │
│  │   offset.x ←─ scroll constante (200 px/s)                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ platforms: List[Platform]                                   │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │ Platform 0  │  │ Platform 1  │  │ Platform N  │        │ │
│  │  │ x=0, y=550  │  │ x=180, y=550│  │ ...         │        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │ │
│  │  (Generadas proceduralmente)                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Flujo de Renderizado

```
Frame N:
├─ world.update(delta_time)
│  ├─ camera.update(delta_time)
│  │  └─ offset.x += scroll_speed * delta_time
│  └─ _generate_distant_platforms() [generar si es necesario]
│
└─ world.draw(surface, camera_offset_x)
   └─ for platform in platforms:
      ├─ if platform.is_on_screen():
      └─ platform.draw(surface, camera_offset_x)
         └─ screen_x = world_x - camera_offset_x
            pygame.draw.rect(...)
```

## Ejemplo de Transformación de Coordenadas

```
MUNDO (Coordenadas del Mundo)
├─ Platform 0: x = 0
├─ Platform 1: x = 180
├─ Platform 2: x = 360
└─ Platform 3: x = 540

Camera offset.x = 200

PANTALLA (t=0, offset=200)
├─ Platform 0: screen_x = 0 - 200 = -200 (fuera de pantalla, izquierda)
├─ Platform 1: screen_x = 180 - 200 = -20 (fuera de pantalla, borde)
├─ Platform 2: screen_x = 360 - 200 = 160 ✓ visible
└─ Platform 3: screen_x = 540 - 200 = 340 ✓ visible

[PANTALLA (1280px de ancho)]
                    │←camera offset─→│
              ┌─────┴─────────────────┐
        ┌─────┴──────────────────────┐│
  ──────┤ Platform 2 Platform 3      ││
        └──────────────────────────┬─┘│
              └────────────────────┴──┘
```

## Clases

### Camera
**Responsabilidad:** Traducir coordenadas del mundo a pantalla y viceversa.

- `offset: Vector2D` — Desplazamiento actual
- `scroll_speed: float` — Velocidad (200 px/s)
- `update(delta_time)` — Avanza el scroll
- `apply(world_x) -> float` — Mundo → Pantalla
- `to_world(screen_x) -> float` — Pantalla → Mundo

### Platform
**Responsabilidad:** Representar una plataforma individual.

- `position: Vector2D` — Coordenadas en el mundo
- `width, height` — Dimensiones
- `draw(surface, camera_offset_x)` — Renderiza con scroll
- `is_on_screen(screen_width, camera_offset_x)` — Visibility culling

### World
**Responsabilidad:** Orquestar plataformas y cámara del nivel.

- `camera: Camera` — Cámara del mundo
- `platforms: List[Platform]` — Todas las plataformas
- `update(delta_time)` — Actualiza scroll y genera plataformas
- `draw(surface, camera_offset_x)` — Renderiza solo visibles
- `add_platform(platform)` — Agregar plataformas manuales

## Características

**Scroll Constante** — Mundo se mueve automáticamente hacia la izquierda  
**Generación Procedural** — Plataformas infinitas generadas bajo demanda  
**Optimización** — Solo renderiza plataformas visibles en pantalla  
**Tipado Estricto** — Conforme a ARCHITECTURE.md  
**Responsabilidades Claras** — Cada clase hace una cosa bien  

## Integración

Ver [WORLD_MECHANICS.md](../WORLD_MECHANICS.md) para detalles completos de integración con GameManager.
