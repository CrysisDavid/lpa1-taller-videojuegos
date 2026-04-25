from abc import ABC
from typing import Tuple
import pygame

from core.vector2d import Vector2D

class Sprite(ABC):
    def __init__(self, screen: pygame.Surface, x:float,y:float, color: Tuple, radius: int = 40, image: str = None):
        if not isinstance(screen, pygame.Surface):
            raise TypeError("pantalla debe ser una instancia de pygame.Surface")
        if not isinstance(color, Tuple) or len(color) != 3:
            raise TypeError("color debe ser una tupla RGB de 3 elementos.")
        
        self.screen = screen
        self.position = Vector2D(x,y)
        self.color = color
        self.radius = int(radius)
        self.is_active = True
        self.image = image
        self._loaded_image = None
        self._image_path = image
        self.damage_effect_timer: float = 0.0
        
        
        
    def colission(self, other:'Sprite'):
        if not(self.is_active and other.is_active):
            return False
        distance = self.position.distance_to(other.position)
        return distance <= (self.radius + other.radius)
        
    def keep_on_screen(self):
        """Adjust the position of the sprite to keep it within the screen boundaries."""
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Keep the sprite within the horizontal boundaries
        self.position.x = max(self.radius, self.position.x)
        self.position.x = min(screen_width - self.radius, self.position.x)
        
        # Keep the sprite within the vertical boundaries
        self.position.y = max(self.radius, self.position.y)
        self.position.y = min(screen_height - self.radius, self.position.y)
    
    def draw(self) -> None:
        """
        Draws the sprite on the screen using pygame.draw.circle. The sprite is only drawn if it is active."""
        
        if self.is_active:
            draw_color = (255, 0, 0) if self.damage_effect_timer > 0 else self.color
            pygame.draw.circle(
                self.screen,
                draw_color,
                (int(self.position.x), int(self.position.y)),
                self.radius
            )

    def draw_image(self):
        """
        Draws the sprite using an image. This method should be overridden by subclasses that use images instead of circles.
        """
        if not isinstance(self.image, str):
            raise TypeError("La propiedad 'image' debe ser una cadena que representa la ruta de la imagen.")
        if len(self.image) == 0:
            raise TypeError("La propiedad 'image' no puede estar vacía.")
        
        if self._loaded_image is None or self._image_path != self.image:
            try:
                self._loaded_image = pygame.image.load(self.image)
                self._loaded_image = pygame.transform.scale(self._loaded_image, (self.radius * 2, self.radius * 2))
                self._image_path = self.image
            except pygame.error as e:
                raise ValueError(f"No se pudo cargar la imagen: {self.image}. Error: {e}")
        self.screen.blit(self._loaded_image, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
        
        # Efecto de daño: overlay rojo si está activo
        if self.damage_effect_timer > 0:
            overlay = pygame.Surface((self.radius * 2, self.radius * 2))
            overlay.set_alpha(128)  # Semi-transparente
            overlay.fill((255, 0, 0))  # Rojo
            self.screen.blit(overlay, (int(self.position.x - self.radius), int(self.position.y - self.radius)))
        
    
    def update(self, delta_time: float = 0.0):
        """
        Update the state of the sprite. This method should be overridden by subclasses to implement specific behavior.
        """
        if self.damage_effect_timer > 0:
            self.damage_effect_timer -= delta_time
    
    @property
    def y(self):
        return self.position.y
    
    @property
    def x(self):
        return self.position.x