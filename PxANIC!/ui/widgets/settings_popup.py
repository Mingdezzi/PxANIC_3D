import pygame
from managers.sound_manager import SoundManager

class SettingsPopup:
    def __init__(self, game):
        self.game = game
        self.sound_manager = SoundManager.get_instance()
        self.width = 400
        self.height = 300
        self.active = False
        
        self.font = pygame.font.SysFont("arial", 20)
        self.title_font = pygame.font.SysFont("arial", 24, bold=True)
        
        # UI Elements (Relatively calculated in update/draw)
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.btn_close = pygame.Rect(0, 0, 100, 40)
        
        # Sliders (0.0 ~ 1.0)
        self.bgm_slider_rect = pygame.Rect(0, 0, 200, 20)
        self.sfx_slider_rect = pygame.Rect(0, 0, 200, 20)
        self.dragging_bgm = False
        self.dragging_sfx = False

    def open(self):
        self.active = True
        w, h = self.game.screen.get_size()
        self.rect.center = (w//2, h//2)
        self.btn_close.midbottom = (self.rect.centerx, self.rect.bottom - 20)
        
        cx = self.rect.centerx
        top = self.rect.top
        self.bgm_slider_rect.topleft = (cx - 100, top + 100)
        self.sfx_slider_rect.topleft = (cx - 100, top + 180)

    def close(self):
        self.active = False
        self.dragging_bgm = False
        self.dragging_sfx = False

    def handle_event(self, event):
        if not self.active: return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                if self.btn_close.collidepoint(mx, my):
                    self.sound_manager.play_sfx("CLICK")
                    self.close()
                elif self.bgm_slider_rect.collidepoint(mx, my):
                    self.dragging_bgm = True
                    self._update_volume(mx, 'bgm')
                elif self.sfx_slider_rect.collidepoint(mx, my):
                    self.dragging_sfx = True
                    self._update_volume(mx, 'sfx')
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging_bgm = False
                self.dragging_sfx = False
                
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.dragging_bgm: self._update_volume(mx, 'bgm')
            elif self.dragging_sfx: self._update_volume(mx, 'sfx')

    def _update_volume(self, mx, type):
        ratio = (mx - self.bgm_slider_rect.x) / self.bgm_slider_rect.width
        ratio = max(0.0, min(1.0, ratio))
        
        if type == 'bgm':
            self.sound_manager.music_volume = ratio
            pygame.mixer.music.set_volume(ratio)
        else:
            self.sound_manager.sfx_volume = ratio

    def draw(self, screen):
        if not self.active: return
        
        # Dim
        s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, (0, 0))
        
        # Panel
        pygame.draw.rect(screen, (40, 40, 50), self.rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 2, border_radius=10)
        
        # Title
        title = self.title_font.render("SETTINGS", True, (255, 255, 255))
        screen.blit(title, (self.rect.centerx - title.get_width()//2, self.rect.top + 20))
        
        # BGM Slider
        bgm_label = self.font.render(f"Music Volume: {int(self.sound_manager.music_volume*100)}%", True, (200, 200, 200))
        screen.blit(bgm_label, (self.bgm_slider_rect.x, self.bgm_slider_rect.y - 25))
        pygame.draw.rect(screen, (60, 60, 70), self.bgm_slider_rect, border_radius=5)
        fill_w = int(self.bgm_slider_rect.width * self.sound_manager.music_volume)
        pygame.draw.rect(screen, (100, 200, 255), (self.bgm_slider_rect.x, self.bgm_slider_rect.y, fill_w, self.bgm_slider_rect.height), border_radius=5)
        
        # SFX Slider
        sfx_label = self.font.render(f"SFX Volume: {int(self.sound_manager.sfx_volume*100)}%", True, (200, 200, 200))
        screen.blit(sfx_label, (self.sfx_slider_rect.x, self.sfx_slider_rect.y - 25))
        pygame.draw.rect(screen, (60, 60, 70), self.sfx_slider_rect, border_radius=5)
        fill_w = int(self.sfx_slider_rect.width * self.sound_manager.sfx_volume)
        pygame.draw.rect(screen, (100, 255, 100), (self.sfx_slider_rect.x, self.sfx_slider_rect.y, fill_w, self.sfx_slider_rect.height), border_radius=5)
        
        # Close Button
        col = (150, 50, 50) if self.btn_close.collidepoint(pygame.mouse.get_pos()) else (100, 40, 40)
        pygame.draw.rect(screen, col, self.btn_close, border_radius=5)
        close_txt = self.font.render("CLOSE", True, (255, 255, 255))
        screen.blit(close_txt, close_txt.get_rect(center=self.btn_close.center))
