import pygame
from ui.widgets.settings_popup import SettingsPopup
from managers.sound_manager import SoundManager

class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.sound_manager = SoundManager.get_instance()
        self.active = False
        self.width = 300
        self.height = 300
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        
        self.title_font = pygame.font.SysFont("arial", 30, bold=True)
        self.font = pygame.font.SysFont("arial", 20)
        
        self.buttons = {}
        self.settings_popup = SettingsPopup(game)

    def open(self):
        self.active = True
        w, h = self.game.screen.get_size()
        self.rect.center = (w//2, h//2)

    def close(self):
        self.active = False

    def handle_event(self, event):
        if self.settings_popup.active:
            self.settings_popup.handle_event(event)
            return

        if not self.active: return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                if 'RESUME' in self.buttons and self.buttons['RESUME'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    self.close()
                elif 'SETTINGS' in self.buttons and self.buttons['SETTINGS'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    self.settings_popup.open()
                elif 'EXIT' in self.buttons and self.buttons['EXIT'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    self.close()
                    # Go to MenuState
                    from states.menu_state import MenuState
                    # Disconnect if connected
                    if hasattr(self.game, 'network') and self.game.network.connected:
                        self.game.network.disconnect()
                    self.game.state_machine.change(MenuState(self.game))
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.settings_popup.active:
                    self.settings_popup.close()
                else:
                    self.close()

    def draw(self, screen):
        if not self.active: return
        
        # Dim background
        s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, (0, 0))
        
        # Panel
        pygame.draw.rect(screen, (30, 30, 40), self.rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 2, border_radius=10)
        
        # Title
        title = self.title_font.render("PAUSED", True, (255, 255, 255))
        screen.blit(title, (self.rect.centerx - title.get_width()//2, self.rect.y + 30))
        
        # Buttons
        start_y = self.rect.y + 90
        self._draw_button(screen, "RESUME", self.rect.centerx, start_y, 'RESUME')
        self._draw_button(screen, "SETTINGS", self.rect.centerx, start_y + 60, 'SETTINGS')
        self._draw_button(screen, "EXIT GAME", self.rect.centerx, start_y + 120, 'EXIT')
        
        if self.settings_popup.active:
            self.settings_popup.draw(screen)

    def _draw_button(self, screen, text, cx, cy, key):
        btn_w, btn_h = 200, 40
        rect = pygame.Rect(0, 0, btn_w, btn_h)
        rect.center = (cx, cy)
        
        mx, my = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mx, my) and not self.settings_popup.active
        
        col = (60, 60, 80) if not is_hover else (80, 80, 100)
        pygame.draw.rect(screen, col, rect, border_radius=5)
        pygame.draw.rect(screen, (150, 150, 150), rect, 1, border_radius=5)
        
        txt_surf = self.font.render(text, True, (255, 255, 255))
        screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
        self.buttons[key] = rect
