import pygame
import random
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class TimingMinigame(BaseMinigame):
    def __init__(self, duration=4.0, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.bar_position = 0.0 # 0.0 to 1.0
        self.bar_direction = 1 # 1 for right, -1 for left
        self.bar_speed = 0.8 # units per second
        self.target_zone_start = random.uniform(0.2, 0.6) # 0.0 to 1.0
        self.target_zone_end = self.target_zone_start + random.uniform(0.1, 0.2)
        
        self.progress_bar_width = 300
        self.progress_bar_height = 30
        self.trigger_key = pygame.K_SPACE

    def start(self):
        super().start()
        self.bar_position = random.uniform(0.0, 1.0) # Start randomly
        self.bar_direction = random.choice([-1, 1])
        self.target_zone_start = random.uniform(0.2, 0.6)
        self.target_zone_end = self.target_zone_start + random.uniform(0.1, 0.2)
        print("[TimingMinigame] Started! Press SPACE in the green zone!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        self.bar_position += self.bar_direction * self.bar_speed * dt
        
        # Bounce off edges
        if self.bar_position < 0:
            self.bar_position = -self.bar_position # Reflect
            self.bar_direction *= -1
        elif self.bar_position > 1:
            self.bar_position = 2 - self.bar_position # Reflect
            self.bar_direction *= -1

        if self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Timing Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN and event.key == self.trigger_key:
            # Check if bar is in target zone
            if self.target_zone_start <= self.bar_position <= self.target_zone_end:
                self.finish(success=True)
                services["popups"].add_popup("Timing Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])
            else:
                self.finish(success=False)
                services["popups"].add_popup("Timing Failed!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])
            return True # Event consumed
        return False

    def draw(self, screen, services):
        if not self.is_active: return

        # Background panel for minigame
        panel_w, panel_h = 400, 150
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)

        # Title
        title_surf = font.render("TIMING MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Progress Bar Area
        bar_area_x = panel_x + (panel_w - self.progress_bar_width) // 2
        bar_area_y = panel_y + 60
        
        # Draw target zone
        target_start_px = int(bar_area_x + self.progress_bar_width * self.target_zone_start)
        target_end_px = int(bar_area_x + self.progress_bar_width * self.target_zone_end)
        pygame.draw.rect(screen, COLORS['MG_SUCCESS'], (target_start_px, bar_area_y, target_end_px - target_start_px, self.progress_bar_height), border_radius=5)

        # Draw full bar background
        pygame.draw.rect(screen, COLORS['GAUGE_BG'], (bar_area_x, bar_area_y, self.progress_bar_width, self.progress_bar_height), 2, border_radius=5)

        # Draw moving bar (indicator)
        current_bar_px = int(bar_area_x + self.progress_bar_width * self.bar_position)
        pygame.draw.rect(screen, COLORS['MG_PIN'], (current_bar_px - 5, bar_area_y, 10, self.progress_bar_height), border_radius=3)
        
        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_surf = small_font.render(f"Press '{pygame.key.name(self.trigger_key).upper()}' in the green zone!", True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
