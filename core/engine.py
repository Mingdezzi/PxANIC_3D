import pygame
import sys
import gc
import time
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from core.state_machine import StateMachine
from systems.logger import GameLogger
from systems.input_handler import InputHandler # [추가 1] 임포트 추가

class GameEngine:
    def __init__(self):
        pygame.init()
        gc.disable()
        
        self.logger = GameLogger.get_instance()
        self.logger.info("SYSTEM", "Game Engine Initializing...")

        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("PxANIC!")

        self.clock = pygame.time.Clock()
        self.running = True

        # [추가 2] InputHandler 초기화
        self.input_handler = InputHandler(self)
        
        self.state_machine = StateMachine(self)
        self.shared_data = {}

        from states.menu_state import MenuState
        self.state_machine.push(MenuState(self))
        
        # Profiling
        self.last_profile_time = time.time()
        self.frame_count = 0

    def run(self):
        self.logger.info("SYSTEM", "Engine Loop Started")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            start_t = time.perf_counter()
            
            self.process_events()
            self.update(dt)
            self.draw()
            
            end_t = time.perf_counter()
            frame_time = (end_t - start_t) * 1000
            
            self.frame_count += 1
            if time.time() - self.last_profile_time >= 1.0:
                self.last_profile_time = time.time()
                self.frame_count = 0

        self.quit()

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # [추가 3] InputHandler가 이벤트를 처리하도록 호출
            self.input_handler.handle_event(event)

            self.state_machine.handle_event(event)

    def update(self, dt):
        # [추가 4] InputHandler가 매 프레임 업데이트되도록 호출 (InputHandler에 update 메서드가 있다고 가정)
        if hasattr(self.input_handler, 'update'):
            self.input_handler.update()
        
        self.state_machine.update(dt)

    def draw(self):
        self.state_machine.draw(self.screen)
        pygame.display.flip()

    def quit(self):
        self.logger.info("SYSTEM", "Engine Shutting Down")
        pygame.quit()
        sys.exit()
