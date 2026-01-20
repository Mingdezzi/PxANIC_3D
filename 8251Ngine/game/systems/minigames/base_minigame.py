import pygame

class BaseMinigame:
    def __init__(self, duration=3.0, success_callback=None, fail_callback=None):
        self.duration = duration
        self.time_left = duration
        self.is_active = False
        self.is_success = False
        self.success_callback = success_callback
        self.fail_callback = fail_callback

    def start(self):
        self.is_active = True
        self.time_left = self.duration
        self.is_success = False

    def update(self, dt, services, game_state):
        if not self.is_active: return
        
        self.time_left -= dt
        if self.time_left <= 0:
            self.finish()

    def draw(self, screen, services):
        if not self.is_active: return
        # Default drawing (e.g., timer)
        font = pygame.font.SysFont("arial", 24, bold=True)
        text_surf = font.render(f"Time: {self.time_left:.1f}s", True, (255, 255, 255))
        screen.blit(text_surf, (50, 50))

    def handle_event(self, event, services):
        pass

    def finish(self, success=False):
        self.is_active = False
        self.is_success = success
        if success and self.success_callback:
            self.success_callback()
        elif not success and self.fail_callback:
            self.fail_callback()

    def reset(self):
        self.is_active = False
        self.is_success = False
        self.time_left = self.duration
