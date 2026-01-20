import pygame
import time
import random

class Minigame:
    def __init__(self, type="MASHING", difficulty=1.0, callback=None):
        self.type = type
        self.difficulty = difficulty
        self.callback = callback # (success: bool) -> None
        self.active = True
        self.progress = 0.0
        self.start_time = time.time()
        self.duration = 5.0 / difficulty
        
        # Type specific
        self.target_val = 100.0
        self.marker_pos = 0.0
        self.marker_dir = 1.0

    def update(self, dt, input_manager):
        if not self.active: return
        
        elapsed = time.time() - self.start_time
        if elapsed > self.duration:
            self.finish(False)
            return

        if self.type == "MASHING":
            # 연타 로직: 스페이스바를 누를 때마다 진행도 상승
            if input_manager.is_action_just_pressed("jump"):
                self.progress += 5.0
            self.progress = max(0, self.progress - dt * 10.0) # 자연 감소
            if self.progress >= self.target_val:
                self.finish(True)

        elif self.type == "TIMING":
            # 타이밍 로직: 움직이는 바가 특정 구간에 있을 때 스페이스바 입력
            self.marker_pos += self.marker_dir * dt * 2.0 * self.difficulty
            if self.marker_pos > 1.0 or self.marker_pos < 0.0:
                self.marker_dir *= -1
            
            if input_manager.is_action_just_pressed("jump"):
                if 0.45 <= self.marker_pos <= 0.55: # 판정 구간
                    self.finish(True)
                else:
                    self.finish(False)

    def finish(self, success):
        self.active = False
        if self.callback:
            self.callback(success)

class MinigameManager:
    def __init__(self):
        self.current_game = None

    def start_game(self, type, difficulty, callback):
        self.current_game = Minigame(type, difficulty, callback)

    def update(self, dt, services, game_state):
        if self.current_game and self.current_game.active:
            self.current_game.update(dt, services["input"])
        else:
            self.current_game = None

    def draw(self, screen):
        if not self.current_game or not self.current_game.active: return
        
        sw, sh = screen.get_size()
        # Overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Game UI
        center_x, center_y = sw // 2, sh // 2
        pygame.draw.rect(screen, (50, 50, 50), (center_x - 150, center_y - 20, 300, 40))
        
        if self.current_game.type == "MASHING":
            prog_w = int(300 * (self.current_game.progress / self.current_game.target_val))
            pygame.draw.rect(screen, (255, 200, 50), (center_x - 150, center_y - 20, prog_w, 40))
            # Text
            font = pygame.font.SysFont("arial", 20, bold=True)
            txt = font.render("MASH [SPACE]!", True, (255, 255, 255))
            screen.blit(txt, (center_x - txt.get_width()//2, center_y - 50))
            
        elif self.current_game.type == "TIMING":
            pygame.draw.rect(screen, (0, 255, 0), (center_x - 15, center_y - 25, 30, 50), 2) # Target
            marker_x = center_x - 150 + int(300 * self.current_game.marker_pos)
            pygame.draw.rect(screen, (255, 50, 50), (marker_x - 2, center_y - 30, 4, 60))
            # Text
            font = pygame.font.SysFont("arial", 20, bold=True)
            txt = font.render("HIT [SPACE] AT CENTER!", True, (255, 255, 255))
            screen.blit(txt, (center_x - txt.get_width()//2, center_y - 50))
