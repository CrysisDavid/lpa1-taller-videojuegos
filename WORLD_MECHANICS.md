# Mecánica del Mundo - Documentación

## Resumen de Implementación

Se ha implementado la mecánica principal del mundo del videojuego siguiendo los lineamientos de **ARCHITECTURE.md**. El sistema consta de tres clases coordinadas:

---

## 1. Clase `Camera` (world/camera.py)

### Responsabilidad
Traducir coordenadas del mundo a coordenadas de pantalla y viceversa, facilitando el efecto de scroll.

### Atributos
- `offset: Vector2D` — Desplazamiento actual del mundo (aumenta constantemente hacia la izquierda)
- `scroll_speed: float` — Velocidad de scroll en píxeles/segundo (default: 200.0)

### Métodos
- **`update(delta_time: float)`** — Incrementa `offset.x` según la velocidad y el tiempo transcurrido
  - Cálculo: `scroll_distance = scroll_speed * delta_time`
- **`apply(world_x: float) -> float`** — Convierte coord del mundo a pantalla
  - Fórmula: `screen_x = world_x - offset.x`
- **`to_world(screen_x: float) -> float`** — Convierte coord de pantalla a mundo
  - Fórmula: `world_x = screen_x + offset.x`

### Características
Scroll constante e independiente del jugador  
Permite mover las coordenadas sin afectar el mundo  
Listo para integración con el movimiento del mouse del jugador  

---

## 2. Clase `Platform` (world/platform.py)

### Responsabilidad
Representar una plataforma individual sobre la que el jugador puede pararse.

### Atributos
- `position: Vector2D` — Coordenadas en el mundo
- `width: int` — Ancho en píxeles
- `height: int` — Alto en píxeles
- `color: tuple[int, int, int]` — Color RGB
- `is_active: bool` — Estado de la plataforma

### Métodos
- **`draw(surface, camera_offset_x)`** — Renderiza la plataforma aplicando offset de cámara
- **`is_on_screen(screen_width, camera_offset_x) -> bool`** — Verifica si es visible
  - Evita renderizar plataformas fuera de pantalla

### Propiedades
- `x`, `y` — Coordenadas directas
- `rect` — Retorna un `pygame.Rect` para colisiones

---

## 3. Clase `World` (world/world.py)

### Responsabilidad
Contener y orquestar todas las plataformas del nivel y la cámara.

### Constantes de Clase
```python
CAMERA_SCROLL_SPEED = 200.0       # píxeles/segundo
PLATFORM_WIDTH = 120               # ancho de plataforma
PLATFORM_HEIGHT = 20               # alto de plataforma
PLATFORM_SPACING = 180             # espacio entre plataformas
GROUND_Y = 550.0                   # altura Y del suelo
```

### Atributos
- `camera: Camera` — Cámara del mundo
- `platforms: List[Platform]` — Lista de todas las plataformas

### Métodos
- **`update(delta_time: float)`** — Actualiza la cámara y genera nuevas plataformas
  - Llama a `camera.update()` para mover el scroll
  - Llama a `_generate_distant_platforms()` para generar proceduralmente
- **`draw(surface, camera_offset_x)`** — Renderiza solo las plataformas visibles
  - Optimización: solo dibuja plataformas dentro del área de pantalla
- **`add_platform(platform: Platform)`** — Permite agregar plataformas manualmente
- **`_initialize_platforms()`** — Genera el nivel inicial
- **`_generate_distant_platforms()`** — Genera nuevas plataformas proceduralmente

### Características
Generación procedural infinita de plataformas  
Renderizado optimizado (culling)  
Movimiento constante hacia la izquierda  
Plataformas se generan automáticamente al avanzar  

---

## Flujo de Integración con GameManager

```python
# En GameManager.__init__()
self.world: World = World(screen=screen)

# En GameManager.update()
self.world.update(delta_time)

# En GameManager.draw()
self.world.draw(surface=self.screen, camera_offset_x=self.world.camera.offset.x)
```

---

## Próximos Pasos (Funcionalidad NO incluida)

Estas características están fuera del alcance de esta tarea:

1. **Movimiento del Jugador en Eje X** — Integrar movimiento del mouse
2. **Sistema de Colisiones** — Detectar colisión Player-Platform
3. **Game Over** — Cuando el jugador cae del mundo
4. **Efectos Visuales** — Paralaje, efectos de scroll

---

## Prueba

Se incluye un script de prueba en `tests/test_world_mechanics.py` que visualiza:
- El scroll constante en acción
- Las plataformas generadas proceduralmente
- El offset de la cámara en tiempo real
- El número de plataformas visibles

Para ejecutar:
```bash
python tests/test_world_mechanics.py
```

---

## Conformidad con ARCHITECTURE.md

**Tipado estricto** — Todos los parámetros y retornos tipados  
**Responsabilidad única** — Cada clase tiene una razón para cambiar  
**Nombres autodocumentados** — Sin abreviaciones, verbos claros  
**Principios SOLID** — Aplicados en la estructura  
**Docstrings completos** — Cada clase y método documentado  
**Sin números mágicos** — Constantes de clase organizadas  
**Sin comentarios superfluos** — El código se explica a sí mismo  
