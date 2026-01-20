import pygame
from pygame.math import Vector3
from engine.core.math_utils import IsoMath

class Projectile:
    def __init__(self, pos, vel, damage, owner):
        self.pos = Vector3(pos)
        self.vel = Vector3(vel)
        self.damage = damage
        self.owner = owner
        self.alive = True
        self.lifetime = 2.0

    def update(self, dt):
        self.pos += self.vel * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

class CombatManager:
    def __init__(self):
        self.projectiles = []

    def spawn_bullet(self, pos, direction, damage, owner):
        vel = Vector3(direction) * 12.0 # Grid units per second
        self.projectiles.append(Projectile(pos, vel, damage, owner))

    def update(self, dt, services, game_state):
        collision_world = services.get("collision_world") # If exists
        
        for p in self.projectiles:
            p.update(dt)
            # Simple collision check with world blocks would go here
            if not p.alive: continue
            
        self.projectiles = [p for p in self.projectiles if p.alive]

    def draw(self, screen, camera):
        for p in self.projectiles:
            ix, iy = IsoMath.cart_to_iso(p.pos.x, p.pos.y, p.pos.z)
            sx, sy = camera.world_to_screen(ix, iy)
            # 탄환 그리기 (작은 노란색 점)
            pygame.draw.circle(screen, (255, 255, 100), (int(sx), int(sy)), 3)
