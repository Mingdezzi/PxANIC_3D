import pygame
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class MashingMinigame(BaseMinigame):
    def __init__(self, duration=3.0, target_mashes=20, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.target_mashes = target_mashes
        self.current_mashes = 0
        self.mash_key = pygame.K_SPACE # Default mashing key
        self.progress_bar_width = 300
        self.progress_bar_height = 30

    def start(self):
        super().start()
        self.current_mashes = 0
        print("[MashingMinigame] Started! Mash the SPACE key!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        # Check for success condition continuously
        if self.current_mashes >= self.target_mashes:
            self.finish(success=True)
            services["popups"].add_popup("Mashing Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])
        elif self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Mashing Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN and event.key == self.mash_key:
            self.current_mashes += 1
            # Optional: provide feedback like a sound or visual indicator for each mash
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
        title_surf = font.render("MASHING MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Progress Bar
        bar_x = panel_x + (panel_w - self.progress_bar_width) // 2
        bar_y = panel_y + 60
        
        # Background of bar
        pygame.draw.rect(screen, COLORS['GAUGE_BG'], (bar_x, bar_y, self.progress_bar_width, self.progress_bar_height), border_radius=5)

        # Current progress
        progress_ratio = min(1.0, self.current_mashes / self.target_mashes)
        current_bar_width = int(self.progress_bar_width * progress_ratio)
        pygame.draw.rect(screen, COLORS['GAUGE_BAR'], (bar_x, bar_y, current_bar_width, self.progress_bar_height), border_radius=5)
        
        # Border for bar
        pygame.draw.rect(screen, COLORS['UI_BORDER'], (bar_x, bar_y, self.progress_bar_width, self.progress_bar_height), 2, border_radius=5)

        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_surf = small_font.render(f"Press '{pygame.key.name(self.mash_key).upper()}' repeatedly!", True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
