import pygame
import math
import random
from engine.graphics.animated_sprite import AnimatedSprite
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT
from engine.core.status import StatusComponent
from engine.graphics.custom_renderer import CustomizationComponent
from engine.core.inventory import InventoryComponent
from game.data.colors import CUSTOM_COLORS

class GameEntity(AnimatedSprite):
    def __init__(self, name="Entity", skin_color=None, clothes_color=None, client_id=None, role="CITIZEN"):
        super().__init__(name)
        self.client_id = client_id
        self.is_moving = False
        self.facing_direction = pygame.math.Vector2(0, 1) # 초기 방향 (아래)
        
        # --- Components ---
        self.status = self.add_component(StatusComponent(role=role)) # Pass role to StatusComponent
        self.role = role # Initialize GameEntity role too
        
        # Pick random colors if not provided
        if skin_color is None: skin_color = random.choice(CUSTOM_COLORS['SKIN'])
        if clothes_color is None: clothes_color = random.choice(CUSTOM_COLORS['CLOTHES'])
        
        self.custom = self.add_component(CustomizationComponent(skin_color, clothes_color))
        self.inventory = self.add_component(InventoryComponent())
        
        # Network Interpolation
        self.target_pos = None
        self.lerp_speed = 10.0
        
        # Role System
        self.role = "CITIZEN"
        self.sub_role = None # For Citizen Jobs (FARMER, MINER, etc.)
        self.team = "CIVIL" # CIVIL, MAFIA
        self.max_hp = 100
        self.max_ap = 100
        self.hp = 100
        self.ap = 100
        self.alive = True
        
        # For Item Usage and Status
        self.buffs = {}
        self.device_on = False
        self.device_battery = 100.0
        self.powerbank_uses = 0
        self.breath_gauge = 100.0 # Stamina
        self.exhausted = False
        self.shiver_timer = 0.0 # For cold/fear effects
        
        self.buff_timers = {} # {buff_key: remaining_time}
        
        self._setup_procedural_animations()

    def update_status_and_movement(self, dt, services):
        # Import settings here to avoid circular dependency on first load
        from settings import SPEED_RUN, SPEED_WALK, SPEED_CROUCH
        
        # --- Buff Timers ---
        # Create a list of buffs to remove to avoid modifying dict during iteration
        buffs_to_remove = []
        for buff_key, remaining_time in self.buff_timers.items():
            self.buff_timers[buff_key] -= dt
            if self.buff_timers[buff_key] <= 0:
                buffs_to_remove.append(buff_key)
        
        for buff_key in buffs_to_remove:
            del self.buff_timers[buff_key]
            if buff_key in self.buffs:
                del self.buffs[buff_key] # Remove actual buff effect
                services["popups"].add_popup(f"{buff_key} 효과 종료!", self.position.x, self.position.y, 0.5)

        # --- Stamina (Breath Gauge) ---
        if self.is_moving and services["input"].is_action_pressed("run"):
            # Running consumes stamina
            if not self.buffs.get('INFINITE_STAMINA', False):
                self.breath_gauge = max(0, self.breath_gauge - 10.0 * dt) # 10 units per second
                if self.breath_gauge <= 0: 
                    self.exhausted = True
                    # Stop running if exhausted
                    # This will be handled by PlayScene input or MovementLogic later
        else:
            # Recover stamina when not running or moving
            self.breath_gauge = min(100, self.breath_gauge + 15.0 * dt) # 15 units per second
            if self.breath_gauge > 20: self.exhausted = False

        # --- Device Battery ---
        if self.device_on:
            self.device_battery = max(0, self.device_battery - 2.0 * dt) # 2 units per second
            if self.device_battery <= 0: self.device_on = False # Turn off device if battery depleted

        # --- Other Status Effects (e.g., Shivering) ---
        if self.shiver_timer > 0:
            self.shiver_timer -= dt
            # Apply visual/audio shiver effects here (e.g., screen shake, sound)

        # This method doesn't handle HP/AP direct changes (items/combat do that).
        # It focuses on passive/time-based status updates.

    def set_role(self, role, sub_role=None):
        self.role = role
        self.sub_role = sub_role
        
        if role == "MAFIA":
            self.team = "MAFIA"
            self.custom.clothes_color = (20, 20, 20) # Black Suit
        elif role == "POLICE":
            self.team = "CIVIL"
            self.custom.clothes_color = (20, 40, 120) # Blue Uniform
        elif role == "DOCTOR":
            self.team = "CIVIL"
            self.custom.clothes_color = (240, 240, 250) # White Coat
        else: # CITIZEN
            self.team = "CIVIL"
            # Keep original random colors or reset
            pass

        print(f"[Entity] Role Set: {self.role} ({self.sub_role})")
        self.status.role = self.role # Update StatusComponent's role
        self._setup_procedural_animations() # Refresh visuals

    def _setup_procedural_animations(self):
        from engine.graphics.animation import Animation
        from settings import TILE_SIZE # TILE_SIZE from settings.py
        
        # PxANIC! CharacterRenderer definitions for 2D style
        RECT_BODY = pygame.Rect(4, 4, 24, 24)
        RECT_CLOTH = pygame.Rect(4, 14, 24, 14)

        def create_frame(height_mod, tilt): # tilt is ignored for 2D style
            skin_color = self.custom.skin_color
            clothes_color = self.custom.clothes_color
            
            base_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Body (Skin color, rounded rect)
            pygame.draw.rect(base_surf, skin_color, RECT_BODY, border_radius=6)
            
            # Clothes (on top of body)
            # Role-specific clothes drawing
            if self.role == "MAFIA":
                # Mafia gets black suit, red tie (always for sprite, phase handled by actual renderer)
                pygame.draw.rect(base_surf, (30, 30, 35), RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
                pygame.draw.polygon(base_surf, (180, 0, 0), [(16, 14), (13, 22), (19, 22)]) # Red Tie
            elif self.role == "DOCTOR":
                pygame.draw.rect(base_surf, (240, 240, 250), RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            elif self.role == "POLICE":
                pygame.draw.rect(base_surf, (20, 40, 120), RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            else: # CITIZEN
                pygame.draw.rect(base_surf, clothes_color, RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)

            # Eyes (based on facing_direction)
            f_dir = self.facing_direction
            ox, oy = int(f_dir.x * 3), int(f_dir.y * 2) # PxANIC! style eye offset
            pygame.draw.circle(base_surf, (255, 255, 255), (16 - 5 + ox, 12 + oy), 3) # Left eye white
            pygame.draw.circle(base_surf, (0, 0, 0), (16 - 5 + ox + int(f_dir.x), 12 + oy + int(f_dir.y)), 1) # Left pupil
            pygame.draw.circle(base_surf, (255, 255, 255), (16 + 5 + ox, 12 + oy), 3) # Right eye white
            pygame.draw.circle(base_surf, (0, 0, 0), (16 + 5 + ox + int(f_dir.x), 12 + oy + int(f_dir.y)), 1) # Right pupil
            
            return base_surf

        idle_frames = [create_frame(0, 0)]
        walk_frames = [create_frame(-2, 0), create_frame(0, 0), create_frame(-2, 0), create_frame(0, 0)]
        
        self.anim_player.add_animation("idle", Animation(idle_frames, 0.5))
        self.anim_player.add_animation("walk", Animation(walk_frames, 0.15))
        self.anim_player.play("idle")

    def update(self, dt, services, game_state):
        # Pass game_state to components that need it
        self.status.update(dt, services, game_state) # Pass services to status update
        
        # Apply shiver offset from status component
        self.offset_x = self.status.shiver_offset[0]
        self.offset_y = self.status.shiver_offset[1]

        # 네트워크 보간 및 이동 상태 업데이트
        if self.target_pos:
            prev_pos = pygame.math.Vector2(self.position.x, self.position.y)
            curr_pos = pygame.math.Vector2(self.position.x, self.position.y)
            new_pos = curr_pos.lerp(self.target_pos, min(1.0, dt * self.lerp_speed))
            
            # 이동 방향에 따른 좌우 반전 (Flip)
            move_dir = new_pos - prev_pos
            if move_dir.x > 0.01: self.flip_h = False # 오른쪽 방향
            elif move_dir.x < -0.01: self.flip_h = True # 왼쪽 방향
            
            self.position.x, self.position.y = new_pos.x, new_pos.y
            self.is_moving = curr_pos.distance_to(self.target_pos) > 0.05
            if not self.is_moving: self.target_pos = None
        else:
            # 로컬 이동 시 방향 감지 (PxAnicScene 등에서 직접 이동시킬 때 대응)
            # 여기서는 Scene에서 위치를 직접 수정하므로, 이전 프레임 위치와 비교
            if not hasattr(self, "_prev_pos"): self._prev_pos = self.position.copy()
            move_delta = self.position - self._prev_pos
            if move_delta.x > 0.001: self.flip_h = False
            elif move_delta.x < -0.001: self.flip_h = True
            self._prev_pos = self.position.copy()

        if self.is_moving:
            self.anim_player.play("walk")
            # 걷는 속도에 따라 애니메이션 속도 조절
            self.anim_player.speed_scale = 1.5 if services["input"].is_action_pressed("run") else 1.0
        else:
            self.anim_player.play("idle")
            self.anim_player.speed_scale = 1.0
        
        super().update(dt, services, game_state) # Pass game_state to super().update
    def set_network_pos(self, x, y):
        if self.target_pos is None:
            self.position.x, self.position.y = x, y
        self.target_pos = pygame.math.Vector2(x, y)

    def fire_weapon(self, direction, services):
        """총기 발사 로직"""
        combat = services.get("combat")
        if combat and self.status.ap >= 5:
            self.status.ap -= 5
            # 탄환 발사 위치 (머리 높이쯤)
            spawn_pos = self.position.copy()
            spawn_pos.z += 1.5
            combat.spawn_bullet(spawn_pos, direction, 20, self.client_id)
            # 소음 발생
            services["interaction"].emit_noise(self.position.x, self.position.y, 15, (255, 100, 50))
            return True
        return False

    def toggle_device(self, services):
        # Check if player has any device in inventory, for now assuming a default flashlight
        if self.device_battery > 0:
            self.device_on = not self.device_on
            # Update light source if player has one
            player_light = self.get_child("PlayerLight") # Assuming light is a child with this name
            if player_light:
                player_light.intensity = 0.6 if self.device_on else 0.0 # Turn off completely if device off
            
            if self.device_on:
                services["popups"].add_popup("손전등 ON", self.position.x, self.position.y, 0.5)
            else:
                services["popups"].add_popup("손전등 OFF", self.position.x, self.position.y, 0.5)
            return True
        else:
            services["popups"].add_popup("배터리 부족!", self.position.x, self.position.y, 0.5, (255, 50, 50))
            return False
