import pygame
import random
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class LockpickMinigame(BaseMinigame):
    def __init__(self, duration=15.0, num_pins=3, success_tolerance=0.1, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.num_pins = num_pins
        self.pins = [] # Each pin has {position, direction, speed, sweet_spot_start, sweet_spot_end, locked}
        self.current_pin_index = 0
        self.success_tolerance = success_tolerance # 0.0 to 1.0
        
        self.trigger_key = pygame.K_SPACE
        
        self.bar_height = 80 # Visual height of pin movement
        self.bar_width = 10
        self.pin_spacing = 60
        self.start_x = SCREEN_WIDTH // 2 - (self.num_pins * self.pin_spacing) // 2

    def start(self):
        super().start()
        self.pins = []
        for _ in range(self.num_pins):
            self.pins.append({
                'position': random.uniform(0.0, 1.0), # 0.0 top, 1.0 bottom
                'direction': random.choice([-1, 1]),
                'speed': random.uniform(0.5, 1.0), # Units per second
                'sweet_spot_start': random.uniform(0.2, 0.7),
                'sweet_spot_end': 0.0,
                'locked': False
            })
            self.pins[-1]['sweet_spot_end'] = self.pins[-1]['sweet_spot_start'] + random.uniform(0.1, 0.2)
        
        self.current_pin_index = 0
        print("[LockpickMinigame] Started! Lockpick the pins!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        if self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Lockpick Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])
            return

        all_pins_locked = True
        for i, pin in enumerate(self.pins):
            if not pin['locked']:
                all_pins_locked = False
                if i == self.current_pin_index: # Only move current pin
                    pin['position'] += pin['direction'] * pin['speed'] * dt
                    # Bounce off edges
                    if pin['position'] < 0:
                        pin['position'] = -pin['position']
                        pin['direction'] *= -1
                    elif pin['position'] > 1:
                        pin['position'] = 2 - pin['position']
                        pin['direction'] *= -1
                
        if all_pins_locked:
            self.finish(success=True)
            services["popups"].add_popup("Lockpick Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN and event.key == self.trigger_key:
            if self.current_pin_index < self.num_pins:
                current_pin = self.pins[self.current_pin_index]
                
                # Check if in sweet spot
                if current_pin['sweet_spot_start'] <= current_pin['position'] <= current_pin['sweet_spot_end']:
                    current_pin['locked'] = True
                    self.current_pin_index += 1
                    # services["audio"].play_sound("LOCK_CLICK") # Placeholder
                else:
                    # Fail if pressed outside sweet spot
                    self.finish(success=False)
                    services["popups"].add_popup("Lockpick Failed! (Wrong timing)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])
            return True # Event consumed
        return False

    def draw(self, screen, services):
        if not self.is_active: return

        panel_w, panel_h = self.num_pins * self.pin_spacing + 100, 250
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)

        title_surf = font.render("LOCKPICK MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Draw Pins
        for i, pin in enumerate(self.pins):
            pin_center_x = panel_x + 50 + i * self.pin_spacing
            bar_top_y = panel_y + 80
            bar_bottom_y = bar_top_y + self.bar_height

            # Draw pin track
            pygame.draw.line(screen, COLORS['GAUGE_BG'], (pin_center_x, bar_top_y), (pin_center_x, bar_bottom_y), 4)

            # Draw sweet spot
            spot_y_start = bar_top_y + int(self.bar_height * pin['sweet_spot_start'])
            spot_y_end = bar_top_y + int(self.bar_height * pin['sweet_spot_end'])
            pygame.draw.rect(screen, COLORS['MG_SUCCESS'], (pin_center_x - self.bar_width // 2, spot_y_start, self.bar_width, spot_y_end - spot_y_start), border_radius=2)

            # Draw moving indicator
            if not pin['locked']:
                indicator_y = bar_top_y + int(self.bar_height * pin['position'])
                pygame.draw.rect(screen, COLORS['MG_PIN'], (pin_center_x - self.bar_width // 2, indicator_y - self.bar_width // 2, self.bar_width, self.bar_width), border_radius=2)
            else:
                # Draw locked indicator (e.g., green dot at sweet spot)
                locked_y = bar_top_y + int(self.bar_height * (pin['sweet_spot_start'] + pin['sweet_spot_end']) / 2)
                pygame.draw.circle(screen, COLORS['MG_SUCCESS'], (pin_center_x, locked_y), self.bar_width // 2 + 2)
            
            # Highlight current pin
            if i == self.current_pin_index and not pin['locked']:
                pygame.draw.rect(screen, COLORS['YELLOW'], (pin_center_x - self.bar_width // 2 - 2, bar_top_y - 2, self.bar_width + 4, self.bar_height + 4), 2, border_radius=3)

        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_surf = small_font.render(f"Press '{pygame.key.name(self.trigger_key).upper()}' to lock the pin in the green zone!", True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
