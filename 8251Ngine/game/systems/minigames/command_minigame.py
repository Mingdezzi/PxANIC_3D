import pygame
import random
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class CommandMinigame(BaseMinigame):
    def __init__(self, duration=5.0, sequence_length=4, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.sequence_length = sequence_length
        self.command_sequence = []
        self.current_input_index = 0
        
        self.key_map = {
            pygame.K_UP: "UP",
            pygame.K_DOWN: "DOWN",
            pygame.K_LEFT: "LEFT",
            pygame.K_RIGHT: "RIGHT",
        }
        self.reverse_key_map = {v: k for k, v in self.key_map.items()}

    def start(self):
        super().start()
        self.command_sequence = random.choices(list(self.key_map.values()), k=self.sequence_length)
        self.current_input_index = 0
        print(f"[CommandMinigame] Started! Sequence: {self.command_sequence}")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        if self.current_input_index == self.sequence_length:
            self.finish(success=True)
            services["popups"].add_popup("Command Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])
        elif self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Command Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN:
            if event.key in self.key_map:
                if self.current_input_index < self.sequence_length:
                    expected_command = self.command_sequence[self.current_input_index]
                    if self.key_map[event.key] == expected_command:
                        self.current_input_index += 1
                        # services["audio"].play_sound("UI_CLICK") # Placeholder for sound feedback
                    else:
                        # Fail on incorrect input
                        self.finish(success=False)
                        services["popups"].add_popup("Command Failed! (Wrong Key)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])
                return True # Event consumed
        return False

    def draw(self, screen, services):
        if not self.is_active: return

        panel_w, panel_h = 500, 200
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)

        title_surf = font.render("COMMAND MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Draw Command Sequence
        arrow_size = 40
        total_seq_width = self.sequence_length * (arrow_size + 10) - 10
        start_x = panel_x + panel_w // 2 - total_seq_width // 2
        start_y = panel_y + 70

        for i, cmd in enumerate(self.command_sequence):
            x_pos = start_x + i * (arrow_size + 10)
            arrow_color = COLORS['TEXT']
            if i < self.current_input_index:
                arrow_color = COLORS['MG_SUCCESS'] # Completed
            elif i == self.current_input_index:
                arrow_color = COLORS['YELLOW'] # Current
            
            # Draw arrow (simplified, could use actual arrow sprites)
            if cmd == "UP":
                pygame.draw.polygon(screen, arrow_color, [(x_pos + arrow_size//2, start_y), (x_pos, start_y + arrow_size), (x_pos + arrow_size, start_y + arrow_size)])
            elif cmd == "DOWN":
                pygame.draw.polygon(screen, arrow_color, [(x_pos, start_y), (x_pos + arrow_size, start_y), (x_pos + arrow_size//2, start_y + arrow_size)])
            elif cmd == "LEFT":
                pygame.draw.polygon(screen, arrow_color, [(x_pos, start_y + arrow_size//2), (x_pos + arrow_size, start_y), (x_pos + arrow_size, start_y + arrow_size)])
            elif cmd == "RIGHT":
                pygame.draw.polygon(screen, arrow_color, [(x_pos, start_y), (x_pos + arrow_size, start_y + arrow_size//2), (x_pos, start_y + arrow_size)])

        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_surf = small_font.render(f"Input the sequence using arrow keys!", True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + 35))
