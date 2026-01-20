import pygame
from colors import COLORS

class InputPopup:
    def __init__(self, screen_w, screen_h, title="Enter IP Address", default_text="127.0.0.1"):
        self.width = 400
        self.height = 200
        self.x = (screen_w - self.width) // 2
        self.y = (screen_h - self.height) // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.title = title
        self.text = default_text
        self.active = True
        self.done = False
        self.result = None
        
        self.font = pygame.font.SysFont("arial", 24)
        self.title_font = pygame.font.SysFont("arial", 28, bold=True)
        
        # UI Rects
        self.input_box = pygame.Rect(self.x + 50, self.y + 70, 300, 40)
        self.btn_ok = pygame.Rect(self.x + 50, self.y + 130, 140, 40)
        self.btn_cancel = pygame.Rect(self.x + 210, self.y + 130, 140, 40)

    def handle_event(self, event):
        if not self.active: return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.result = self.text
                self.done = True
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.result = None
                self.done = True
                self.active = False
            else:
                if len(self.text) < 20: # Limit length
                    self.text += event.unicode
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_ok.collidepoint(event.pos):
                self.result = self.text
                self.done = True
                self.active = False
            elif self.btn_cancel.collidepoint(event.pos):
                self.result = None
                self.done = True
                self.active = False

    def draw(self, screen):
        if not self.active: return
        
        # Dim background
        s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, (0, 0))
        
        # Popup Body
        pygame.draw.rect(screen, (40, 40, 50), self.rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 2, border_radius=10)
        
        # Title
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surf, (self.rect.centerx - title_surf.get_width()//2, self.rect.y + 20))
        
        # Input Box
        pygame.draw.rect(screen, (20, 20, 30), self.input_box, border_radius=5)
        pygame.draw.rect(screen, (100, 200, 255), self.input_box, 1, border_radius=5)
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.input_box.x + 10, self.input_box.centery - txt_surf.get_height()//2))
        
        # Buttons
        # OK
        pygame.draw.rect(screen, (50, 150, 50), self.btn_ok, border_radius=5)
        ok_txt = self.font.render("CONNECT", True, (255, 255, 255))
        screen.blit(ok_txt, ok_txt.get_rect(center=self.btn_ok.center))
        
        # Cancel
        pygame.draw.rect(screen, (150, 50, 50), self.btn_cancel, border_radius=5)
        cancel_txt = self.font.render("CANCEL", True, (255, 255, 255))
        screen.blit(cancel_txt, cancel_txt.get_rect(center=self.btn_cancel.center))
