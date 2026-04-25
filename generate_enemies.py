import pygame
from pathlib import Path
from core.vector2d import Vector2D
from entities.enemy import Enemy

def generate_enemies_from_image(screen: pygame.Surface, positions: list[Vector2D], image_path: str = str(Path(__file__).parent / "public" / "assets" / "Basic-enemy.png")) -> list[Enemy]:
    """
    Genera una lista de enemigos usando la imagen especificada.

    Args:
        screen: Superficie de Pygame para renderizar.
        positions: Lista de posiciones Vector2D donde colocar los enemigos.
        image_path: Ruta a la imagen del enemigo.

    Returns:
        Lista de instancias Enemy creadas.
    """
    enemies = []
    for i, pos in enumerate(positions):
        enemy = Enemy(
            screen=screen,
            world_pos=pos,
            name=f"Enemy #{i+1}",
            enemy_type="terrestre",  # o "volador" según necesidad
            health=100.0,
            attack_power=15.0,
            defense=5.0
        )
        # Asegurarse de que use la imagen
        enemy.image = image_path
        enemies.append(enemy)
    return enemies

# Ejemplo de uso:
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Generar Enemigos")

    # Posiciones de ejemplo
    positions = [
        Vector2D(100, 500),
        Vector2D(300, 450),
        Vector2D(500, 400)
    ]

    # Generar enemigos
    enemies = generate_enemies_from_image(screen, positions)

    # Bucle simple para mostrar
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((135, 206, 235))  # Fondo azul claro más oscuro

        # Dibujar enemigos
        for enemy in enemies:
            enemy.draw_image()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()