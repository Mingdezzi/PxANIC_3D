import pygame
import random
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class FrequencyMinigame(BaseMinigame):
    def __init__(self, duration=10.0, target_hold_time=3.0, success_tolerance=0.1, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.current_frequency = 0.5 # 0.0 to 1.0
        self.frequency_speed = 0.05 # How fast it moves per update
        self.target_zone_start = random.uniform(0.2, 0.6)
        self.target_zone_end = self.target_zone_start + random.uniform(0.1, 0.2)
        self.target_hold_time = target_hold_time
        self.current_hold_time = 0.0
        self.success_tolerance = success_tolerance # How close player needs to be to center of target for holding
        
        self.adjust_up_key = pygame.K_UP
        self.adjust_down_key = pygame.K_DOWN

        self.bar_visual_width = 300
        self.bar_visual_height = 30

    def start(self):
        super().start()
        self.current_frequency = random.uniform(0.0, 1.0)
        self.target_zone_start = random.uniform(0.2, 0.6)
        self.target_zone_end = self.target_zone_start + random.uniform(0.1, 0.2)
        self.current_hold_time = 0.0
        print("[FrequencyMinigame] Started! Adjust frequency into the green zone!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        # Auto-drift if no input
        if not (services["input"].is_action_pressed("move_up") or services["input"].is_action_pressed("move_down")):
             # Small random drift
            self.current_frequency += random.uniform(-0.01, 0.01) * dt
            self.current_frequency = max(0.0, min(1.0, self.current_frequency))

        # Check if in target zone
        if self.target_zone_start <= self.current_frequency <= self.target_zone_end:
            self.current_hold_time += dt
            if self.current_hold_time >= self.target_hold_time:
                self.finish(success=True)
                services["popups"].add_popup("Frequency Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])
        else:
            self.current_hold_time = 0.0 # Reset if outside zone

        if self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Frequency Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN:
            if event.key == self.adjust_up_key:
                self.current_frequency = min(1.0, self.current_frequency + self.frequency_speed)
                return True
            elif event.key == self.adjust_down_key:
                self.current_frequency = max(0.0, self.current_frequency - self.frequency_speed)
                return True
        return False

    def draw(self, screen, services):
        if not self.is_active: return

        panel_w, panel_h = 400, 200
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)

        title_surf = font.render("FREQUENCY MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Draw Frequency Bar Area
        bar_x = panel_x + (panel_w - self.bar_visual_width) // 2
        bar_y = panel_y + 60
        
        # Draw target zone
        target_start_px = int(bar_x + self.bar_visual_width * self.target_zone_start)
        target_end_px = int(bar_x + self.bar_visual_width * self.target_zone_end)
        pygame.draw.rect(screen, COLORS['MG_SUCCESS'], (target_start_px, bar_y, target_end_px - target_start_px, self.bar_visual_height), border_radius=5)

        # Draw full bar background
        pygame.draw.rect(screen, COLORS['GAUGE_BG'], (bar_x, bar_y, self.bar_visual_width, self.bar_visual_height), 2, border_radius=5)

        # Draw current frequency indicator
        current_freq_px = int(bar_x + self.bar_visual_width * self.current_frequency)
        pygame.draw.rect(screen, COLORS['MG_PIN'], (current_freq_px - 5, bar_y, 10, self.bar_visual_height), border_radius=3)

        # Draw hold time progress (e.g., small bar under frequency bar)
        hold_bar_width = int(self.bar_visual_width * (self.current_hold_time / self.target_hold_time))
        pygame.draw.rect(screen, COLORS['BREATH_BAR'], (bar_x, bar_y + self.bar_visual_height + 5, hold_bar_width, 10), border_radius=2)
        pygame.draw.rect(screen, COLORS['UI_BORDER'], (bar_x, bar_y + self.bar_visual_height + 5, self.bar_visual_width, 10), 1, border_radius=2)

        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_surf = small_font.render(f"Use UP/DOWN to adjust frequency and hold in green zone! ({self.current_hold_time:.1f}/{self.target_hold_time:.1f}s)", True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
