import pygame
import random
import math
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class CircleMinigame(BaseMinigame):
    def __init__(self, duration=5.0, success_tolerance_deg=30, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.indicator_angle = 0.0 # Current angle of the indicator (0-360 degrees)
        self.indicator_speed = 90.0 # Degrees per second
        self.target_angle_start = random.uniform(0, 360) # Start angle of the target zone
        self.target_angle_end = (self.target_angle_start + random.uniform(30, 90)) % 360 # End angle of the target zone
        self.success_tolerance_deg = success_tolerance_deg # How close to the center of the target zone is required
        
        self.trigger_key = pygame.K_SPACE
        self.center_x, self.center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.radius = 100

    def start(self):
        super().start()
        self.indicator_angle = random.uniform(0, 360)
        self.indicator_speed = random.uniform(70, 120)
        self.target_angle_start = random.uniform(0, 360)
        self.target_angle_end = (self.target_angle_start + random.uniform(30, 90)) % 360
        
        # Ensure target_angle_end is greater than target_angle_start for drawing arcs easily
        if self.target_angle_end < self.target_angle_start:
            self.target_angle_end += 360 # Wrap around

        print("[CircleMinigame] Started! Press SPACE in the green arc!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        self.indicator_angle = (self.indicator_angle + self.indicator_speed * dt) % 360

        if self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Circle Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN and event.key == self.trigger_key:
            # Check if indicator is in the target zone
            # We check if indicator_angle is within the target arc, handling wrap-around
            is_in_target_zone = False
            if self.target_angle_start <= self.target_angle_end: # Normal arc
                if self.target_angle_start <= self.indicator_angle <= self.target_angle_end:
                    is_in_target_zone = True
            else: # Wrapped arc (e.g., 300 to 60 degrees)
                if self.indicator_angle >= self.target_angle_start or self.indicator_angle <= self.target_angle_end % 360: # Modulo to handle wrapping
                    is_in_target_zone = True

            if is_in_target_zone:
                self.finish(success=True)
                services["popups"].add_popup("Circle Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])
            else:
                self.finish(success=False)
                services["popups"].add_popup("Circle Failed!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])
            return True # Event consumed
        return False

    def draw(self, screen, services):
        if not self.is_active: return

        panel_w, panel_h = 400, 400
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)

        title_surf = font.render("CIRCLE MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Draw the main circle
        pygame.draw.circle(screen, COLORS['GAUGE_BG'], (self.center_x, self.center_y), self.radius + 10, 2) # Outer ring
        pygame.draw.circle(screen, COLORS['GAUGE_BG'], (self.center_x, self.center_y), self.radius, 1) # Inner ring

        # Draw target zone arc
        # Pygame arc takes rectangle, start_angle, stop_angle, width
        # Angles are in radians, clockwise from x-axis
        rect_for_arc = (self.center_x - self.radius, self.center_y - self.radius, self.radius * 2, self.radius * 2)
        pygame.draw.arc(screen, COLORS['MG_SUCCESS'], rect_for_arc, 
                        math.radians(self.target_angle_start), math.radians(self.target_angle_end), 15)

        # Draw indicator line
        ind_x = self.center_x + self.radius * math.cos(math.radians(self.indicator_angle))
        ind_y = self.center_y + self.radius * math.sin(math.radians(self.indicator_angle))
        pygame.draw.line(screen, COLORS['MG_PIN'], (self.center_x, self.center_y), (ind_x, ind_y), 3)

        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_surf = small_font.render(f"Press '{pygame.key.name(self.trigger_key).upper()}' when the line is in the green arc!", True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
