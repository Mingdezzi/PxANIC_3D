import pygame
import math
from engine.core.node import Node
from engine.core.math_utils import IsoMath
from settings import TILE_SIZE

class Projectile(Node):
    def __init__(self, x, y, angle, speed=15.0, range_tiles=20, owner_id=None):
        super().__init__(f"Bullet_{owner_id}")
        self.position.x = x
        self.position.y = y
        self.position.z = 1.5 # Height
        self.angle = angle
        self.speed = speed
        self.max_dist = range_tiles
        self.dist_traveled = 0
        self.owner_id = owner_id
        self.alive = True
        
        # Velocity
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt, services, game_state):
        if not self.alive: return
        
        move_dist = self.speed * dt
        self.position.x += self.vx * dt
        self.position.y += self.vy * dt
        self.dist_traveled += move_dist
        
        if self.dist_traveled >= self.max_dist:
            self.alive = False
            self.parent.remove_child(self)
            return

        # Collision Check (Simple Tile Check)
        scene = self.get_scene()
        if hasattr(scene, 'block_map'):
            bx, by = int(self.position.x), int(self.position.y)
            block = scene.block_map.get((bx, by))
            if block and block.size_z > 0.5: # Hit wall/tall object
                self.alive = False
                self.parent.remove_child(self)
                # Effect
                services["popups"].add_popup("Hit Wall", self.position.x, self.position.y, 0.5)
                return

    def draw(self, screen, camera):
        # Draw small yellow sphere/line
        ix, iy = IsoMath.cart_to_iso(self.position.x, self.position.y, self.position.z)
        sx, sy = camera.world_to_screen(ix, iy)
        
        # Trail
        tail_len = 10
        ex = sx - math.cos(self.angle) * tail_len
        ey = sy - math.sin(self.angle) * tail_len * 0.5 # Iso foreshortening
        
        pygame.draw.line(screen, (255, 200, 50), (ex, ey), (sx, sy), 2)
        pygame.draw.circle(screen, (255, 255, 200), (int(sx), int(sy)), 2)

    def get_scene(self):
        node = self
        while node.parent:
            node = node.parent
        return node
