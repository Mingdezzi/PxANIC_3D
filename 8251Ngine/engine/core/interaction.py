import pygame
import time

class NoiseEvent:
    def __init__(self, x, y, radius, color=(200, 200, 200), duration=1.0):
        self.x, self.y = x, y
        self.radius = radius
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.alpha = 150

    def update(self):
        elapsed = time.time() - self.start_time
        progress = elapsed / self.duration
        if progress > 1.0:
            return False
        
        # Fade out alpha
        self.alpha = int(150 * (1.0 - progress))
        return True

class InteractionManager:
    def __init__(self):
        self.noises = []
        self.interactables = []

    def emit_noise(self, x, y, radius, color=(200, 200, 200)):
        self.noises.append(NoiseEvent(x, y, radius, color))

    def register_interactable(self, node):
        if node not in self.interactables:
            self.interactables.append(node)

    def update(self):
        self.noises = [n for n in self.noises if n.update()]

    def draw(self, screen, camera):
        from engine.core.math_utils import IsoMath
        for n in self.noises:
            # World to Screen
            ix, iy = IsoMath.cart_to_iso(n.x, n.y, 0)
            sx, sy = camera.world_to_screen(ix, iy)
            
            # Draw expanding ring
            elapsed = time.time() - n.start_time
            curr_rad = int(n.radius * (elapsed / n.duration) * 32) # Scale to pixels
            
            s = pygame.Surface((curr_rad * 2, curr_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*n.color, n.alpha), (curr_rad, curr_rad), curr_rad, 2)
            screen.blit(s, (sx - curr_rad, sy - curr_rad))