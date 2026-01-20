import pygame
import random
from game.systems.minigames.base_minigame import BaseMinigame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.colors import COLORS

class WiringMinigame(BaseMinigame):
    def __init__(self, duration=10.0, num_wires=4, success_callback=None, fail_callback=None):
        super().__init__(duration, success_callback, fail_callback)
        self.num_wires = num_wires
        self.wire_colors = []
        self.left_side = [] # (color, is_connected)
        self.right_side = [] # (color, is_connected)
        self.connections = {} # {left_index: right_index}
        self.selected_left_wire = -1
        self.is_connecting = False
        
        self.wire_palette = [
            COLORS['MG_WIRE_RED'], 
            COLORS['MG_WIRE_BLUE'], 
            COLORS['MG_WIRE_YELLOW'], 
            COLORS['GREEN'], 
            COLORS['PURPLE'], # Assuming PURPLE exists or define it
            COLORS['ORANGE']
        ]
        
        # Add a default purple if it doesn't exist for example
        if 'PURPLE' not in COLORS: COLORS['PURPLE'] = (128, 0, 128)

    def start(self):
        super().start()
        self.wire_colors = random.sample(self.wire_palette, self.num_wires)
        self.left_side = [(c, False) for c in self.wire_colors]
        
        shuffled_colors = list(self.wire_colors)
        random.shuffle(shuffled_colors)
        self.right_side = [(c, False) for c in shuffled_colors]
        
        self.connections = {}
        self.selected_left_wire = -1
        self.is_connecting = False
        print("[WiringMinigame] Started! Connect the wires!")

    def update(self, dt, services, game_state):
        super().update(dt, services, game_state)
        if not self.is_active: return

        if self.time_left <= 0:
            self.finish(success=False)
            services["popups"].add_popup("Wiring Failed! (Timeout)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_FAIL'])

        # Check if all wires are connected and correct
        if len(self.connections) == self.num_wires:
            all_correct = True
            for left_idx, right_idx in self.connections.items():
                if self.left_side[left_idx][0] != self.right_side[right_idx][0]:
                    all_correct = False
                    break
            
            if all_correct:
                self.finish(success=True)
                services["popups"].add_popup("Wiring Success!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 1.5, COLORS['MG_SUCCESS'])
            else:
                # Only fail if connections are complete but wrong
                # For now, let player keep trying within time
                pass # Will implement explicit fail later if needed

    def handle_event(self, event, services):
        if not self.is_active: return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: # Move selection up
                if self.is_connecting:
                    # Move right side selection
                    current_right_idx = self.selected_left_wire # Use left_idx as current right_idx initially
                    for k,v in self.connections.items():
                        if k == self.selected_left_wire: current_right_idx = v

                    if current_right_idx > 0:
                        self._set_connection(self.selected_left_wire, current_right_idx - 1)
                else:
                    # Move left side selection
                    self.selected_left_wire = (self.selected_left_wire - 1) % self.num_wires
                    if self.selected_left_wire < 0: self.selected_left_wire = self.num_wires - 1

            elif event.key == pygame.K_DOWN: # Move selection down
                if self.is_connecting:
                    # Move right side selection
                    current_right_idx = self.selected_left_wire
                    for k,v in self.connections.items():
                        if k == self.selected_left_wire: current_right_idx = v

                    if current_right_idx < self.num_wires - 1:
                        self._set_connection(self.selected_left_wire, current_right_idx + 1)
                else:
                    # Move left side selection
                    self.selected_left_wire = (self.selected_left_wire + 1) % self.num_wires
            
            elif event.key == pygame.K_SPACE: # Select / Confirm connection
                if self.selected_left_wire == -1: # First selection
                    self.selected_left_wire = 0
                    self.is_connecting = False
                elif not self.is_connecting:
                    # Start connecting from left side
                    self.is_connecting = True
                    # Initialize right selection to the same index as left for convenience
                    self._set_connection(self.selected_left_wire, self.selected_left_wire)
                else:
                    # Finish connection, check if it's correct (handled in update)
                    self.is_connecting = False # Ready for next connection
                    if len(self.connections) == self.num_wires: # All connected, check final state
                        # No need to finish here, update will handle it
                        pass
            
            return True # Event consumed
        return False

    def _set_connection(self, left_idx, right_idx):
        # Ensure no other left wire connects to this right_idx
        for k, v in list(self.connections.items()):
            if v == right_idx and k != left_idx:
                # Disconnect old wire
                del self.connections[k]
                # Update visual state
                self.left_side[k] = (self.left_side[k][0], False)
                self.right_side[v] = (self.right_side[v][0], False)
        
        self.connections[left_idx] = right_idx
        # Update visual state of wires
        for i in range(self.num_wires):
            self.left_side[i] = (self.left_side[i][0], i in self.connections)
        for i in range(self.num_wires):
            self.right_side[i] = (self.right_side[i][0], i in self.connections.values())


    def draw(self, screen, services):
        if not self.is_active: return

        panel_w, panel_h = 600, 400
        panel_x, panel_y = SCREEN_WIDTH // 2 - panel_w // 2, SCREEN_HEIGHT // 2 - panel_h // 2
        pygame.draw.rect(screen, COLORS['MM_BG'], (panel_x, panel_y, panel_w, panel_h), border_radius=5)
        pygame.draw.rect(screen, COLORS['MM_BORDER'], (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)

        font = pygame.font.SysFont("arial", 24, bold=True)
        small_font = pygame.font.SysFont("arial", 18)

        title_surf = font.render("WIRING MINIGAME", True, COLORS['WHITE'])
        screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 10))

        # Draw Wires
        wire_spacing = (panel_h - 100) // self.num_wires
        left_col_x = panel_x + 50
        right_col_x = panel_x + panel_w - 50

        for i in range(self.num_wires):
            left_y = panel_y + 60 + i * wire_spacing
            
            # Left side wire
            color, is_connected = self.left_side[i]
            rect_color = color if not is_connected else (color[0]//2, color[1]//2, color[2]//2) # Dim if connected
            pygame.draw.rect(screen, rect_color, (left_col_x - 10, left_y - 10, 20, 20))
            pygame.draw.rect(screen, COLORS['UI_BORDER'], (left_col_x - 10, left_y - 10, 20, 20), 1)

            # Highlight selected left wire
            if i == self.selected_left_wire and not self.is_connecting:
                pygame.draw.rect(screen, COLORS['SELECTION'], (left_col_x - 12, left_y - 12, 24, 24), 2)

            # Right side wire
            right_color, right_connected = self.right_side[i]
            rect_color_right = right_color if not right_connected else (right_color[0]//2, right_color[1]//2, right_color[2]//2)
            pygame.draw.rect(screen, rect_color_right, (right_col_x - 10, left_y - 10, 20, 20))
            pygame.draw.rect(screen, COLORS['UI_BORDER'], (right_col_x - 10, left_y - 10, 20, 20), 1)
            
            # Highlight selected right wire (if connecting)
            if self.is_connecting and self.selected_left_wire != -1 and self.connections.get(self.selected_left_wire) == i:
                pygame.draw.rect(screen, COLORS['SELECTION'], (right_col_x - 12, left_y - 12, 24, 24), 2)

            # Draw connection line
            if i in self.connections:
                target_right_idx = self.connections[i]
                target_right_y = panel_y + 60 + target_right_idx * wire_spacing
                pygame.draw.line(screen, self.left_side[i][0], (left_col_x, left_y), (right_col_x, target_right_y), 3)

        # Time Left
        time_surf = small_font.render(f"Time: {self.time_left:.1f}s", True, COLORS['TEXT'])
        screen.blit(time_surf, (panel_x + panel_w // 2 - time_surf.get_width() // 2, panel_y + panel_h - 30))

        # Instruction
        instr_text = "Use UP/DOWN to select. SPACE to connect."
        if self.is_connecting: instr_text = "Use UP/DOWN to choose right wire. SPACE to confirm."
        instr_surf = small_font.render(instr_text, True, COLORS['YELLOW'])
        screen.blit(instr_surf, (panel_x + panel_w // 2 - instr_surf.get_width() // 2, panel_y + panel_h - 60))
