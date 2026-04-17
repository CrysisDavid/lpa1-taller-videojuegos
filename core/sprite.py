from abc import ABC
import pygame

from core.vector2d import Vector2D

class Sprite(ABC):
    def __init__(self, screen: pygame.Surface, x:float,y:float, color: tuple, raius: int):
        self.screen = screen
        self.position = Vector2D(x,y)
        self.color = color
        self.radius = raius