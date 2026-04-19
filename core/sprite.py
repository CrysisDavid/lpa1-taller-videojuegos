from abc import ABC
from typing import Tuple
import pygame

from core.vector2d import Vector2D

class Sprite(ABC):
    def __init__(self, screen: pygame.Surface, x:float,y:float, color: Tuple, raius: int = 40):
        if not isinstance(screen, pygame.Surface):
            raise TypeError("pantalla debe ser una instancia de pygame.Surface")
        if not isinstance(color, Tuple) or len(color) != 3:
            raise TypeError("color debe ser una tupla RGB de 3 elementos.")
        
        self.screen = screen
        self.position = Vector2D(x,y)
        self.color = color
        self.radius = int(raius)
        self.is_active = True
        
        
        
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
            pygame.draw.circle(
                self.screen,
                self.color,
                (int(self.position.x), int(self.position.y)),
                self.radius
            )
        
    
    def update():
        """
        Update the state of the sprite. This method should be overridden by subclasses to implement specific behavior.
        """
        pass
    
    @property
    def y(self):
        return self.position.y
    
    @property
    def x(self):
        return self.position.x