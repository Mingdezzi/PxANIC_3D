import pygame
from engine.core.node import Node

class Sprite2D(Node):
    def __init__(self, name="Sprite", texture=None, color=(255, 255, 255)):
        super().__init__(name)
        self.texture = texture
        if self.texture is None:
            # Create a placeholder cube-ish rect
            self.texture = pygame.Surface((64, 64), pygame.SRCALPHA)
            self.texture.fill(color)
            # Make it look like a diamond tile
            # (Just a placeholder)
            pygame.draw.rect(self.texture, (0, 0, 0), (0,0,64,64), 2)

    def get_sprite(self):
        return self.texture
