import pygame
import time
from engine.core.math_utils import IsoMath

class Popup:
    def __init__(self, text, x, y, z, color=(255, 255, 255), duration=1.5):
        self.text = text
        self.pos = [x, y, z]
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.alive = True

    def update(self, dt):
        elapsed = time.time() - self.start_time
        if elapsed > self.duration:
            self.alive = False
        # 위로 떠오르는 효과
        self.pos[2] += dt * 1.5
        return self.alive

class WorldPopupManager:
    def __init__(self):
        self.popups = []

    def add_popup(self, text, x, y, z, color=(255, 255, 255), duration=1.5):
        self.popups.append(Popup(text, x, y, z, color, duration))

    def update(self, dt):
        self.popups = [p for p in self.popups if p.update(dt)]

    def draw(self, screen, camera):
        font = pygame.font.SysFont("arial", 14, bold=True)
        for p in self.popups:
            ix, iy = IsoMath.cart_to_iso(p.pos[0], p.pos[1], p.pos[2])
            sx, sy = camera.world_to_screen(ix, iy)
            
            # Fade out
            elapsed = time.time() - p.start_time
            alpha = int(255 * (1.0 - (elapsed / p.duration)))
            
            txt_surf = font.render(p.text, True, p.color)
            txt_surf.set_alpha(alpha)
            screen.blit(txt_surf, (sx - txt_surf.get_width() // 2, sy))
