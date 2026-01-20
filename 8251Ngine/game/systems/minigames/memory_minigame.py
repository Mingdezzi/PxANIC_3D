import pygame
import random
import time
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class MemoryMinigame(BaseMinigame):
    def __init__(self, duration=15.0, grid_size=3, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.grid_size = grid_size # e.g., 3x3 grid
        self.cells = [] # Stores numbers in cells
        self.memorize_phase = True
        self.memorize_timer = 3.0 # Time to memorize
        self.current_input_number = 1
        self.selected_cells = [] # Stores (row, col) of player's selections
        
        self.cell_size = 60
        self.padding = 10
        self.grid_start_x = SCREEN_WIDTH // 2 - (self.grid_size * self.cell_size + (self.grid_size - 1) * self.padding) // 2
        self.grid_start_y = SCREEN_HEIGHT // 2 - (self.grid_size * self.cell_size + (self.grid_size - 1) * self.padding) // 2
        
        self.hovered_cell = (-1, -1)

    def start(self):
        super().start()
        self.cells = []
        numbers = list(range(1, self.grid_size * self.grid_size + 1))
        random.shuffle(numbers)
        
        for r in range(self.grid_size):
            row = []
            for c in range(self.grid_size):
                row.append(numbers.pop(0))
            self.cells.append(row)
        
        self.memorize_phase = True
        self.memorize_timer = 3.0
        self.current_input_number = 1
        self.selected_cells = []
        self.hovered_cell = (-1, -1)
        print("[MemoryMinigame] Started! Memorize the numbers!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        if self.memorize_phase:
            self.memorize_timer -= dt
            if self.memorize_timer <= 0:
                self.memorize_phase = False
                self.time_left = self.duration # Start interaction timer
                services["popups"].add_popup("Find the numbers!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100, 1.0, COLORS['WHITE'])
        else:
            if self.time_left <= 0:
                self.finish(success=False)
                services["popups"].add_popup("Memory Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

            if self.current_input_number > self.grid_size * self.grid_size:
                self.finish(success=True)
                services["popups"].add_popup("Memory Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])

    def handle_event(self, event, services):
        if not self.is_active or self.memorize_phase: return False

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered_cell = self._get_cell_from_mouse(mx, my)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
            mx, my = event.pos
            clicked_cell = self._get_cell_from_mouse(mx, my)
            
            if clicked_cell != (-1, -1):
                r, c = clicked_cell
                if (r, c) in self.selected_cells: return True # Already selected

                if self.cells[r][c] == self.current_input_number:
                    self.selected_cells.append((r, c))
                    self.current_input_number += 1
                    # services["audio"].play_sound("UI_CLICK") # Placeholder
                else:
                    self.finish(success=False)
                    services["popups"].add_popup("Memory Failed! (Wrong Number)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])
                return True # Event consumed
        return False

    def _get_cell_from_mouse(self, mx, my):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                cell_x = self.grid_start_x + c * (self.cell_size + self.padding)
                cell_y = self.grid_start_y + r * (self.cell_size + self.padding)
                cell_rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)
                if cell_rect.collidepoint(mx, my):
                    return (r, c)
        return (-1, -1)

    def draw(self, screen, services):
        if not self.is_active: return

        panel_w, panel_h = 700, 500
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)
        number_font = pygame.font.SysFont("arial", 36, bold=True)

        title_surf = font.render("MEMORY MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Draw Grid
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                cell_x = self.grid_start_x + c * (self.cell_size + self.padding)
                cell_y = self.grid_start_y + r * (self.cell_size + self.padding)
                cell_rect = pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size)
                
                cell_color = COLORS['GAUGE_BG']
                if (r, c) == self.hovered_cell and not self.memorize_phase: cell_color = COLORS['SELECTION']
                if (r, c) in self.selected_cells: cell_color = COLORS['MG_SUCCESS']

                pygame.draw.rect(screen, cell_color, cell_rect, border_radius=3)
                pygame.draw.rect(screen, COLORS['UI_BORDER'], cell_rect, 1, border_radius=3)

                if self.memorize_phase or (r, c) in self.selected_cells:
                    number = self.cells[r][c]
                    num_surf = number_font.render(str(number), True, COLORS['WHITE'])
                    screen.blit(num_surf, (cell_x + self.cell_size // 2 - num_surf.get_width() // 2,
                                           cell_y + self.cell_size // 2 - num_surf.get_height() // 2))

        # Time Left / Memorize Timer
        if self.memorize_phase:
            timer_text = f"Memorize: {self.memorize_timer:.1f}s"
        else:
            timer_text = f"Time: {self.time_left:.1f}s"

        time_surf = small_font.render(timer_text, True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        if self.memorize_phase:
            instr_surf = small_font.render(f"Remember the numbers!", True, COLORS['YELLOW'])
        else:
            instr_surf = small_font.render(f"Click number {self.current_input_number} (1-{self.grid_size*self.grid_size})", True, COLORS['YELLOW'])

        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
