import pygame
import os

class ResourceManager:
    def __init__(self):
        self.images = {}
        self.fonts = {}
        self.base_path = "assets"

    def get_image(self, filename):
        if filename not in self.images:
            path = os.path.join(self.base_path, "images", filename)
            try:
                self.images[filename] = pygame.image.load(path).convert_alpha()
            except:
                print(f"ResourceManager: Failed to load image {path}")
                return None
        return self.images[filename]

    def get_font(self, name, size):
        key = (name, size)
        if key not in self.fonts:
            try:
                self.fonts[key] = pygame.font.SysFont(name, size)
            except:
                self.fonts[key] = pygame.font.Font(None, size)
        return self.fonts[key]