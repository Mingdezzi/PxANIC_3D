import pygame
import random
from game.scripts.entity import GameEntity
from settings import TILE_SIZE

class NpcEntity(GameEntity):
    def __init__(self, name="Citizen", skin_color=None, clothes_color=None, role="CITIZEN"):
        if skin_color is None:
            skin_color = (random.randint(200, 255), random.randint(180, 230), random.randint(150, 200))
        if clothes_color is None:
            clothes_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            
        super().__init__(name, skin_color, clothes_color, role=role)
        
        self.move_timer = 0
        self.wait_time = random.uniform(1.0, 3.0)
        self.state = "IDLE" # IDLE, WALK
        self.target_x = 0
        self.target_y = 0

    def update(self, dt, services, game_state):
        scene = self.get_scene()
        if not scene: return
        
        # Update NPC's own status component
        self.status.update(dt, services, game_state)

        self.move_timer -= dt
        
        if self.state == "IDLE":
            if self.move_timer <= 0:
                # Pick new target
                self._pick_random_target(scene)
        
        elif self.state == "WALK":
            # Move towards target
            dx = self.target_x - self.position.x
            dy = self.target_y - self.position.y
            dist = (dx**2 + dy**2)**0.5
            
            if dist < 0.1:
                self.position.x = self.target_x
                self.position.y = self.target_y
                self.state = "IDLE"
                self.move_timer = random.uniform(2.0, 5.0)
                self.is_moving = False
            else:
                speed = 2.0
                move_x = (dx / dist) * speed * dt
                move_y = (dy / dist) * speed * dt
                
                # Update facing
                if move_x > 0: self.flip_h = False
                elif move_x < 0: self.flip_h = True
                
                # Collision Check (Simple)
                new_x = self.position.x + move_x
                new_y = self.position.y + move_y
                
                if self._check_collision(scene, new_x, new_y):
                    # Hit wall, stop
                    self.state = "IDLE"
                    self.move_timer = random.uniform(1.0, 2.0)
                    self.is_moving = False
                else:
                    self.position.x = new_x
                    self.position.y = new_y
                    self.is_moving = True

        super().update(dt, services, game_state) # Pass services and game_state to super().update
    def _pick_random_target(self, scene):
        # Random walk within small radius
        rx = random.randint(-3, 3)
        ry = random.randint(-3, 3)
        tx = self.position.x + rx
        ty = self.position.y + ry
        
        if self._check_collision(scene, tx, ty):
            self.move_timer = 0.5 # Try again soon
        else:
            self.target_x = tx
            self.target_y = ty
            self.state = "WALK"
            self.is_moving = True

    def _check_collision(self, scene, x, y):
        bx, by = int(round(x)), int(round(y))
        if hasattr(scene, 'collision_world'):
            # This check might be too strict if collision_world only has static blocks
            # Ideally use collision_world.check_collision
            return scene.collision_world.check_collision(pygame.math.Vector3(x, y, 0))
        return False

    def get_scene(self):
        node = self
        while node.parent:
            node = node.parent
            if hasattr(node, 'collision_world'): # Simple duck typing for scene
                return node
        return None
