import random
import pygame
from engine.core.component import Component

class AdvancedAIComponent(Component):
    def __init__(self, role="CITIZEN"):
        super().__init__()
        self.role = role
        self.state = "IDLE" # IDLE, WANDER, INVESTIGATE, FLEE, WORK
        self.path = []
        self.target_pos = None
        self.timer = 0
        self.speed = 2.0
        self.perception_radius = 8.0 # 시야 범위
        
    def update(self, dt, services, game_state):
        if not self.node: return
        
        # 1. 환경 감지 (PxANIC- 스타일)
        self._sense_environment(services)
        
        # 2. 상태 결정 (FSM)
        self._update_state_logic(dt, services)
        
        # 3. 이동 실행
        self._execute_movement(dt)

    def _sense_environment(self, services):
        interaction = services.get("interaction")
        # 최근 발생한 소음 감지
        if interaction and interaction.noises:
            for noise in interaction.noises:
                dist = self.node.position.distance_to(pygame.math.Vector3(noise.x, noise.y, 0))
                if dist < noise.radius:
                    # 위험한 소음(총성 등)이면 FLEE, 아니면 INVESTIGATE
                    if noise.color == (255, 100, 50): # Combat noise
                        self.state = "FLEE"
                        self.target_pos = self.node.position + (self.node.position - pygame.math.Vector3(noise.x, noise.y, 0)).normalize() * 5
                    else:
                        if self.state != "FLEE":
                            self.state = "INVESTIGATE"
                            self.target_pos = pygame.math.Vector3(noise.x, noise.y, 0)
                    self.path = [] # 새 경로 필요

    def _update_state_logic(self, dt, services):
        time_manager = services.get("time")
        nav_manager = services.get("nav")
        
        if self.state == "IDLE":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "WANDER"
                
        elif self.state == "WANDER":
            if not self.path:
                # 무작위 목적지 설정
                rand_x = self.node.position.x + random.uniform(-5, 5)
                rand_y = self.node.position.y + random.uniform(-5, 5)
                if nav_manager:
                    self.path = nav_manager.get_path(self.node.position, pygame.math.Vector2(rand_x, rand_y))
                if not self.path: self.state = "IDLE"; self.timer = 2.0

        elif self.state == "INVESTIGATE":
            if self.target_pos and not self.path:
                if nav_manager:
                    self.path = nav_manager.get_path(self.node.position, pygame.math.Vector2(self.target_pos.x, self.target_pos.y))
            if not self.path: self.state = "IDLE"; self.timer = 3.0

    def _execute_movement(self, dt):
        if self.path:
            target = pygame.math.Vector3(self.path[0][0], self.path[0][1], 0)
            dist = self.node.position.distance_to(target)
            
            if dist < 0.1:
                self.path.pop(0)
            else:
                dir = (target - self.node.position).normalize()
                self.node.position += dir * self.speed * dt
                self.node.is_moving = True
        else:
            self.node.is_moving = False