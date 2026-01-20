import pygame
from core.base_state import BaseState
from managers.resource_manager import ResourceManager
from managers.sound_manager import SoundManager
from ui.widgets.input_popup import InputPopup
from ui.widgets.settings_popup import SettingsPopup
from settings import SERVER_IP

class MultiMenuState(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.resource_manager = ResourceManager.get_instance()
        self.sound_manager = SoundManager.get_instance()
        self.buttons = {}
        self.title_font = self.resource_manager.get_font('title')
        self.large_font = self.resource_manager.get_font('large')
        self.panel_bg = self._create_panel_bg(400, 300)
        self.last_hover = None
        
        self.popup = None # IP Input Popup
        self.settings_popup = SettingsPopup(game) # Settings Popup

    def _create_panel_bg(self, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 25, 220), (0, 0, w, h), border_radius=15)
        pygame.draw.rect(s, (80, 80, 100, 255), (0, 0, w, h), 2, border_radius=15)
        return s

    def enter(self, params=None):
        pass # BGM continues from MenuState

    def update(self, dt):
        pass

    def draw(self, screen):
        w, h = screen.get_width(), screen.get_height()
        self.buttons = {}
        
        # Background
        screen.fill((10, 10, 15))
        self._draw_grid_bg(screen, w, h)

        # Top Bar
        self._draw_top_bar(screen, w)

        # Title
        title_surf = self.title_font.render("MULTIPLAYER", True, (100, 200, 255))
        screen.blit(title_surf, (w//2 - title_surf.get_width()//2, h//4))

        # Panel
        panel_rect = self.panel_bg.get_rect(center=(w//2, h//2 + 50))
        screen.blit(self.panel_bg, panel_rect)

        # Buttons
        start_y = panel_rect.top + 60
        self._draw_styled_button(screen, "CREATE GAME", w//2, start_y, 'Create')
        self._draw_styled_button(screen, "JOIN GAME", w//2, start_y + 80, 'Join')
        self._draw_styled_button(screen, "BACK", w//2, start_y + 160, 'Back')
        
        # Popups
        if self.popup and self.popup.active:
            self.popup.draw(screen)
        if self.settings_popup.active:
            self.settings_popup.draw(screen)

    def _draw_top_bar(self, screen, w):
        # Simple text buttons for navigation
        btn_w, btn_h = 80, 30
        gap = 10
        
        # Back Button (Top Left)
        self._draw_nav_button(screen, "BACK", 10, 10, btn_w, btn_h, 'Nav_Back')
        # Home Button (Top Left - next to Back)
        self._draw_nav_button(screen, "HOME", 10 + btn_w + gap, 10, btn_w, btn_h, 'Nav_Home')
        # Settings Button (Top Right)
        self._draw_nav_button(screen, "CONFIG", w - btn_w - 10, 10, btn_w, btn_h, 'Nav_Settings')

    def _draw_nav_button(self, screen, text, x, y, w, h, key):
        rect = pygame.Rect(x, y, w, h)
        mx, my = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mx, my) and not (self.popup and self.popup.active) and not self.settings_popup.active
        
        col = (100, 100, 120) if not is_hover else (150, 150, 200)
        pygame.draw.rect(screen, (30, 30, 40), rect, border_radius=5)
        pygame.draw.rect(screen, col, rect, 1, border_radius=5)
        
        txt_surf = self.resource_manager.get_font('default').render(text, True, (200, 200, 200))
        screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
        self.buttons[key] = rect

    def _draw_grid_bg(self, screen, w, h):
        for x in range(0, w, 40):
            pygame.draw.line(screen, (20, 20, 30), (x, 0), (x, h))
        for y in range(0, h, 40):
            pygame.draw.line(screen, (20, 20, 30), (0, y), (w, y))

    def _draw_styled_button(self, screen, text, cx, cy, key):
        if (self.popup and self.popup.active) or self.settings_popup.active: return
        
        btn_w, btn_h = 280, 50
        rect = pygame.Rect(0, 0, btn_w, btn_h)
        rect.center = (cx, cy)
        
        mx, my = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mx, my)
        
        if is_hover and self.last_hover != key:
            self.sound_manager.play_sfx("HOVER")
            self.last_hover = key
        elif not is_hover and self.last_hover == key:
            self.last_hover = None
        
        bg_col = (40, 40, 50) if not is_hover else (60, 60, 80)
        border_col = (100, 100, 120) if not is_hover else (100, 255, 100)
        text_col = (200, 200, 200) if not is_hover else (255, 255, 255)
        
        pygame.draw.rect(screen, bg_col, rect, border_radius=8)
        pygame.draw.rect(screen, border_col, rect, 2 if not is_hover else 3, border_radius=8)
        
        txt_surf = self.large_font.render(text, True, text_col)
        screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))
        
        self.buttons[key] = rect

    def handle_event(self, event):
        if self.settings_popup.active:
            self.settings_popup.handle_event(event)
            return

        if self.popup and self.popup.active:
            self.popup.handle_event(event)
            if self.popup.done:
                if self.popup.result:
                    # Join Game Logic
                    target_ip = self.popup.result
                    self.sound_manager.play_sfx("CLICK")
                    from states.lobby_state import LobbyState
                    # Pass IP to LobbyState via params or shared_data
                    self.game.shared_data['server_ip'] = target_ip
                    self.game.state_machine.change(LobbyState(self.game))
                self.popup = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                if 'Nav_Back' in self.buttons and self.buttons['Nav_Back'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    from states.menu_state import MenuState
                    self.game.state_machine.change(MenuState(self.game))
                if 'Nav_Home' in self.buttons and self.buttons['Nav_Home'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    from states.menu_state import MenuState
                    self.game.state_machine.change(MenuState(self.game))
                if 'Nav_Settings' in self.buttons and self.buttons['Nav_Settings'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    self.settings_popup.open()

                if 'Create' in self.buttons and self.buttons['Create'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    from states.lobby_state import LobbyState
                    self.game.shared_data['server_ip'] = '127.0.0.1' 
                    self.game.state_machine.change(LobbyState(self.game))
                
                if 'Join' in self.buttons and self.buttons['Join'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    w, h = self.game.screen.get_size()
                    self.popup = InputPopup(w, h, "Enter Server IP", SERVER_IP)
                    
                if 'Back' in self.buttons and self.buttons['Back'].collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    from states.menu_state import MenuState
                    self.game.state_machine.change(MenuState(self.game))
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
             from states.menu_state import MenuState
             self.game.state_machine.change(MenuState(self.game))
