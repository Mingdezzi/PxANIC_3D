import pygame
import random
import os
from engine.core.node import Node
from engine.graphics.block import Block3D
from engine.physics.collision import CollisionWorld
from engine.core.math_utils import IsoMath
from engine.graphics.lighting import LightSource, DirectionalLight
from game.scripts.entity import GameEntity
from engine.physics.fov import FOVSystem
from game.utils.map_loader import MapLoader
from engine.ui.gui import Control, Label, Panel
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, ITEMS, SPEED_WALK, SPEED_RUN, SPEED_CROUCH, PHASE_SETTINGS, TILE_SIZE
from game.data.colors import COLORS

class PlayScene(Node):
    def _ready(self, services):
        self.services = services
        print("PlayScene Ready. Loading PxANIC! Map...")
        self.collision_world = CollisionWorld()
        self.fov_system = FOVSystem(self.collision_world)
        self.camera_follow = True
        self.player = None
        self.day_count = 1
        
        # --- UI Setup ---
        self.ui_root = Control(0, 0, 1280, 720)
        
        # Top-Left: Debug Info
        debug_panel = Panel(10, 10, 150, 70, color=COLORS['UI_BG'])
        self.lbl_fps = Label("FPS: 0", 10, 10, size=16, color=COLORS['TEXT'])
        self.lbl_pos = Label("Pos: (0, 0)", 10, 35, size=16, color=COLORS['TEXT'])
        debug_panel.add_child(self.lbl_fps); debug_panel.add_child(self.lbl_pos)
        self.ui_root.add_child(debug_panel)
        
        # Top-Center: Time/Day
        time_panel = Panel(SCREEN_WIDTH//2 - 100, 10, 200, 40, color=COLORS['UI_BG'])
        self.lbl_time = Label("Day 1 - MORNING", 20, 10, color=COLORS['MSG_DAWN'], size=18)
        time_panel.add_child(self.lbl_time)
        self.ui_root.add_child(time_panel)
        
        # Bottom-Left: Player Stats
        stats_panel = Panel(10, SCREEN_HEIGHT - 160, 260, 150, color=COLORS['UI_BG'])
        stats_panel.tag = "stats_panel"
        self.lbl_role = Label("Role: CITIZEN", 10, 10, color=COLORS['ROLE_CITIZEN'], size=20)
        self.lbl_hp = Label("HP: 100/100", 10, 45, color=COLORS['HP_BAR'], size=18)
        self.lbl_ap = Label("AP: 100/100", 10, 70, color=COLORS['AP_BAR'], size=18)
        self.lbl_battery = Label("Bat: 100%", 10, 95, size=18, color=COLORS['BREATH_BAR'])
        stats_panel.add_child(self.lbl_role); stats_panel.add_child(self.lbl_hp); stats_panel.add_child(self.lbl_ap); stats_panel.add_child(self.lbl_battery)
        
        lbl_help = Label("[WASD] Move  [E] Interact  [I] Inv  [F] Light  [Z] Atk", 10, 125, size=12, color=COLORS['TEXT'])
        stats_panel.add_child(lbl_help)
        self.ui_root.add_child(stats_panel)
        
        # Center: Inventory Panel
        self.inv_panel = Panel(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 150, 400, 300, color=COLORS['UI_BG'])
        self.inv_panel.visible = False
        self.inv_panel.add_child(Label("INVENTORY", 20, 20, size=24, color=COLORS['WHITE']))
        self.inv_labels = []
        for i in range(10):
            lbl = Label("", 30, 60 + i * 25, size=18, color=COLORS['TEXT'])
            self.inv_labels.append(lbl); self.inv_panel.add_child(lbl)
        self.ui_root.add_child(self.inv_panel)
        
        if services.get("app"): services["app"].set_ui(self.ui_root)
        
        # --- Environment ---
        self.sun = DirectionalLight(name="Sun", intensity=0.5)
        self.add_child(self.sun)

        # --- World ---
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        map_path = os.path.join(base_path, "data", "map.json")
        tiles_path = os.path.join(base_path, "data", "tiles.json")
        
        from engine.assets.tile_engine import TileEngine
        import json
        with open(tiles_path, 'r', encoding='utf-8') as f: TileEngine.init(json.load(f))
        
        self.map_loader = MapLoader(map_path, tiles_path)
        self.block_map = self.map_loader.build_world(self, self.collision_world)
        
        from game.systems.action_system import ActionSystem
        from game.systems.combat_system import CombatSystem
        self.action_system = ActionSystem(self)
        self.combat_system = CombatSystem(self)

        self._spawn_player()
        self._spawn_npcs()

    def _spawn_player(self):
        roles = ["CITIZEN", "MAFIA", "POLICE", "DOCTOR"]
        sub_roles = ["FARMER", "MINER", "FISHER"]
        role = random.choice(roles)
        sub = random.choice(sub_roles) if role == "CITIZEN" else None
        
        self.player = GameEntity(name="Player", role=role)
        self.player.position.x, self.player.position.y = 10, 10
        self.player.set_role(role, sub)
        
        self.player.inventory.add_item("TANGERINE", 2)
        self.player.inventory.add_item("CHOCOBAR", 2)
        self.player.inventory.add_item("BATTERY", 1)
        self._update_inventory_ui()
        
        role_str = f"{role} ({sub})" if sub else role
        self.lbl_role.set_text(role_str)
        if role == "MAFIA": self.lbl_role.color = COLORS['ROLE_MAFIA']
        elif role == "POLICE": self.lbl_role.color = COLORS['ROLE_POLICE']
        elif role == "DOCTOR": self.lbl_role.color = COLORS['ROLE_DOCTOR']
        
        self.add_child(self.player)
        player_light = LightSource("PlayerLight", radius=250, color=(255, 200, 100), intensity=0.6)
        self.player.add_child(player_light)

    def _spawn_npcs(self):
        from game.scripts.npc import NpcEntity
        print("Spawning NPCs...")
        self.npcs = []
        for i in range(5):
            npc = NpcEntity(f"Citizen_{i}")
            nx, ny = random.randint(5, 15), random.randint(5, 15)
            if not self.collision_world.check_collision(pygame.math.Vector3(nx, ny, 0)):
                npc.position.x, npc.position.y = nx, ny
                self.add_child(npc); self.npcs.append(npc)

    def update(self, dt, services, game_state):
        input_manager = services["input"]
        renderer = services["renderer"]
        time_manager = services["time"]
        app = services["app"]

        self.lbl_fps.set_text(f"FPS: {int(app.clock.get_fps())}")
        self._update_time_ui(time_manager)
        
        minigame_manager = services["minigame"]
        if minigame_manager.is_minigame_active():
            if self.player: self.player.is_moving = False
        else:
            if self.player:
                # Stats UI
                self.lbl_hp.set_text(f"HP: {int(self.player.hp)}/{int(self.player.max_hp)}")
                self.lbl_ap.set_text(f"AP: {int(self.player.ap)}/{int(self.player.max_ap)}")
                self.lbl_battery.set_text(f"Bat: {int(self.player.device_battery)}%")
                self.lbl_pos.set_text(f"Pos: ({int(self.player.position.x)}, {int(self.player.position.y)})")

                self._handle_player_input(dt, input_manager)
                self._handle_interaction(input_manager, services)
                
                # FOV 계산 제거 (성능 개선 및 시야 확보)
                app.fov_polygon = None
                
                if self.camera_follow:
                    ix, iy = IsoMath.cart_to_iso(self.player.position.x, self.player.position.y, 0)
                    renderer.camera.follow(ix, iy)

        self.sun.intensity = 0.6 if time_manager.current_phase != 'NIGHT' else 0.05
        # super().update will handle children and components

    def _update_time_ui(self, time_mgr):
        self.lbl_time.set_text(f"Day {time_mgr.day_count} - {time_mgr.current_phase}")

    def _update_inventory_ui(self):
        if not self.player: return
        inv = self.player.inventory
        items_list = list(inv.items.items())
        for i, lbl in enumerate(self.inv_labels):
            if i < len(items_list):
                key, count = items_list[i]
                info = inv.get_item_info(key)
                lbl.set_text(f"{i+1}. {info.get('name', key)} x{count}")
            else: lbl.set_text("")

    def _handle_player_input(self, dt, input_manager):
        if input_manager.is_action_just_pressed("inventory"):
            self.inv_panel.visible = not self.inv_panel.visible
            self._update_inventory_ui()

        if input_manager.is_action_just_pressed("toggle_flashlight"):
            if self.player: self.player.toggle_device(self.services)

        if self.inv_panel.visible:
            if self.player:
                for item_key, item_info in ITEMS.items():
                    key = item_info.get('key')
                    if key and input_manager.is_action_just_pressed(f"item_{key}"):
                        if self.player.inventory.use_item(item_key, services=self.services):
                            self._update_inventory_ui()
                        break
            return

        move_x, move_y = input_manager.get_vector("move_left", "move_right", "move_up", "move_down")
        speed = SPEED_WALK
        if input_manager.is_action_pressed("run") and not getattr(self.player, 'exhausted', False): speed = SPEED_RUN
        elif getattr(self.player, 'exhausted', False): speed = SPEED_CROUCH
        
        if move_x != 0 or move_y != 0:
            if move_x != 0 and move_y != 0: speed *= 0.7071
            tx = self.player.position.x + move_x * speed * dt
            if not self.collision_world.check_collision(pygame.math.Vector3(tx, self.player.position.y, 0)): self.player.position.x = tx
            ty = self.player.position.y + move_y * speed * dt
            if not self.collision_world.check_collision(pygame.math.Vector3(self.player.position.x, ty, 0)): self.player.position.y = ty
            self.player.is_moving = True
            self.player.facing_direction = pygame.math.Vector2(move_x, move_y).normalize()
            self.player.flip_h = move_x < 0
        else: self.player.is_moving = False

    def _handle_interaction(self, input_mgr, services):
        if input_mgr.is_action_just_pressed("interact"):
            msg = self.action_system.handle_interact(self.player, interact_mode='short')
            if msg: services["popups"].add_popup(msg, self.player.position.x, self.player.position.y, 1.0)
        
        if input_mgr.is_action_just_pressed("attack") and self.player:
            res = self.combat_system.handle_attack(self.player, "RANGED" if self.player.role == "POLICE" else "MELEE")
            if res: services["popups"].add_popup(res, self.player.position.x, self.player.position.y, 0.8)
