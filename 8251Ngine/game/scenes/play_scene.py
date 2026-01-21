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
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, ITEMS, SPEED_WALK, SPEED_RUN, SPEED_CROUCH, PHASE_SETTINGS, TILE_SIZE, MAX_PLAYERS, INDOOR_ZONES, VENDING_MACHINE_TID, CCTV_TID
from game.data.colors import COLORS
from game.ui.widgets.cctv_view import CCTVViewWidget # CCTVViewWidget 임포트

class PlayScene(Node):
    def _ready(self, services):
        self.services = services
        print("PlayScene Ready. Loading PxANIC! Map...")
        self.collision_world = CollisionWorld()
        self.fov_system = FOVSystem(self.collision_world)
        self.camera_follow = True
        self.player = None
        self.day_count = 1
        
        # [네트워크 관련 추가]
        self.last_sent_pos = (0, 0) # PxANIC!의 last_sent_pos 초기화
        self.other_players = {} # 다른 플레이어 엔티티 관리를 위한 딕셔너리
        self.game_started = False # 게임 시작 상태 플래그 추가
        self.last_phase = None # 이전 시간 단계 추적용
        
        # [PxANIC! 이식] 월드 상태 관련 (사이렌, 사보타주)
        self.is_mafia_frozen = False
        self.frozen_timer = 0.0
        self.is_blackout = False
        self.blackout_timer = 0.0
        self.show_vote_ui = False # 투표 UI 가시성 플래그
        self.my_vote_target = None # 플레이어가 투표한 대상
        self.has_murder_occurred = False # 살인 발생 여부 플래그
        self.daily_news_log = [] # 일일 뉴스 로그 리스트
        self.cctv_widget = CCTVViewWidget(self) # CCTV 위젯 추가
        
        
        
        
        
        
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

        # [네트워크 관련 UI 추가] 플레이어 목록 패널
        self.player_list_panel = Panel(SCREEN_WIDTH - 220, 10, 200, 200, color=COLORS['UI_BG'])
        self.player_list_panel.add_child(Label("Players", 10, 10, size=20, color=COLORS['WHITE']))
        self.player_labels = []
        for i in range(MAX_PLAYERS): # MAX_PLAYERS는 settings에서 가져와야 함
            lbl = Label("", 10, 40 + i * 20, size=16, color=COLORS['TEXT'])
            self.player_labels.append(lbl); self.player_list_panel.add_child(lbl)
        self.ui_root.add_child(self.player_list_panel)

        # [UI 추가] 자판기 패널
        self.vending_panel = Panel(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 200, 500, 400, color=COLORS['UI_BG'])
        self.vending_panel.visible = False
        self.vending_panel.add_child(Label("VENDING MACHINE", 20, 20, size=24, color=COLORS['WHITE']))
        
        self.vending_labels = []
        for i, (item_key, item_info) in enumerate(ITEMS.items()):
            # 아이템 라벨 대신 버튼으로 변경
            btn = Button(
                f"{i+1}. {item_info['name']} ({item_info['price']}G)",
                30, 60 + i * 25,
                200, 20, # 버튼 크기
                on_click=lambda key=item_key: self._buy_item_from_vending(key) # 클릭 이벤트 연결
            )
            self.vending_labels.append(btn)
            self.vending_panel.add_child(btn)
        
        self.lbl_player_coins = Label("Coins: 0", 30, 60 + len(ITEMS) * 25 + 20, size=18, color=COLORS['TEXT'])
        self.vending_panel.add_child(self.lbl_player_coins)

        btn_close_vending = Button("Close", self.vending_panel.rect.w - 100, 10, 80, 30, on_click=self.toggle_vending_machine)
        self.vending_panel.add_child(btn_close_vending)

        self.ui_root.add_child(self.vending_panel)
        
        # [UI 추가] 투표 패널
        self.voting_panel = Panel(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 150, 400, 300, color=COLORS['UI_BG'])
        self.voting_panel.visible = False
        self.voting_panel.add_child(Label("VOTE", 20, 20, size=24, color=COLORS['WHITE']))
        
        self.candidate_buttons = []
        # 투표 대상은 동적으로 생성되므로, 초기에는 빈 목록으로 버튼 생성
        for i in range(MAX_PLAYERS): # MAX_PLAYERS는 settings에서 가져와야 함. 일단 최대 플레이어 수만큼 버튼 공간 확보
            btn = Button("", 30, 60 + i * 30, 340, 25, on_click=lambda idx=i: self._cast_vote(idx))
            btn.visible = False # 초기에는 보이지 않게
            self.candidate_buttons.append(btn)
            self.voting_panel.add_child(btn)

        self.lbl_vote_status = Label("Select a candidate", 30, 60 + MAX_PLAYERS * 30 + 10, size=16, color=COLORS['TEXT'])
        self.voting_panel.add_child(self.lbl_vote_status)

        self.ui_root.add_child(self.voting_panel)
        
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
        
        # [네트워크 관련 추가] 초기 플레이어 위치 전송
        network_manager = self.services.get("network")
        if self.player and network_manager and network_manager.client_id is not None:
            network_manager.send_move(
                int(self.player.position.x), 
                int(self.player.position.y), 
                False, 
                self.player.facing_direction
            )
            self.last_sent_pos = (int(self.player.position.x), int(self.player.position.y))

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
        
        # [PxANIC! 이식] 시간 단계 변경 감지 및 콜백 호출
        if self.last_phase is None: # 초기화
            self.last_phase = time_manager.current_phase
        elif self.last_phase != time_manager.current_phase:
            # Phase changed
            old_phase = self.last_phase
            new_phase = time_manager.current_phase
            self.on_phase_change(old_phase, new_phase)
            self.last_phase = new_phase
            
            if new_phase == "MORNING":
                self.on_morning()
        
        # [네트워크 관련 추가] 네트워크 이벤트 처리
        network_manager = services.get("network")
        if network_manager and network_manager.client_id is not None:
            for e in network_manager.get_messages():
                if e.get('type') == 'MOVE' and e.get('id') != network_manager.client_id: # 다른 플레이어의 이동 메시지
                    target_id = e.get('id')
                    if target_id in self.other_players: # 이미 존재하는 다른 플레이어
                        other_player_entity = self.other_players[target_id]
                        other_player_entity.set_network_state(
                            e['x'], e['y'], e.get('is_moving', False), e.get('facing', other_player_entity.facing_direction)
                        )
                        # print(f"Updated Other Player {target_id}: {e['x']}, {e['y']}")
                    # else: # TODO: 아직 씬에 없는 플레이어의 MOVE 메시지를 받으면 어떻게 처리할지 (PLAYER_LIST에서 먼저 처리되어야 함)
                    #     print(f"Received MOVE for unknown player {target_id}")
                elif e.get('type') == 'TIME_SYNC': # 시간 동기화
                    time_manager.sync_time(e['phase_idx'], e['timer'], e['day'])
                    print(f"Time Sync: Day {e['day']}, Phase {e['phase_idx']}, Timer {e['timer']}")
                elif e.get('type') == 'PLAYER_LIST': # 플레이어 목록 업데이트
                    # 현재 씬에 있는 다른 플레이어 ID 집합
                    current_other_player_ids = set(self.other_players.keys())
                    
                    # 새로운 플레이어 목록 ID 집합
                    new_player_list_ids = {p['id'] for p in e['participants'] if p['id'] != network_manager.client_id}
                    
                    # 제거해야 할 플레이어 (씬에는 있지만 새 목록에 없는 경우)
                    for removed_id in current_other_player_ids - new_player_list_ids:
                        if removed_id in self.other_players:
                            removed_entity = self.other_players.pop(removed_id)
                            self.remove_child(removed_entity)
                            print(f"Removed player {removed_id}")
                            
                    # 추가하거나 업데이트해야 할 플레이어
                    for p_data in e['participants']:
                        player_id = p_data['id']
                        if player_id == network_manager.client_id: # 자기 자신은 스킵
                            # 자기 자신의 역할, 서브 역할, 그룹 업데이트
                            if 'role' in p_data: self.player.set_role(p_data['role'], p_data.get('sub_role'))
                            if 'group' in p_data: self.player.set_group(p_data['group'])
                            continue
                            
                        if player_id not in self.other_players: # 새로운 플레이어
                            # GameEntity 생성 시 client_id 전달
                            new_player_entity = GameEntity(name=p_data.get('name', f"Player {player_id+1}"), client_id=player_id)
                            new_player_entity.position.x = p_data.get('x', 0)
                            new_player_entity.position.y = p_data.get('y', 0)
                            new_player_entity.set_role(p_data.get('role', 'CITIZEN'), p_data.get('sub_role'))
                            if 'group' in p_data: new_player_entity.set_group(p_data['group']) # 그룹 설정
                            new_player_entity.is_moving = p_data.get('is_moving', False)
                            # facing_direction은 Vector2로 변환 필요
                            if 'facing' in p_data and isinstance(p_data['facing'], (list, tuple)):
                                new_player_entity.facing_direction = pygame.math.Vector2(p_data['facing'][0], p_data['facing'][1])
                            
                            self.add_child(new_player_entity)
                            self.other_players[player_id] = new_player_entity
                            print(f"Added new player {player_id}: {p_data.get('name')}")
                        else: # 기존 플레이어 업데이트 (역할, 이름, 그룹 등)
                            existing_entity = self.other_players[player_id]
                            existing_entity.name = p_data.get('name', existing_entity.name)
                            existing_entity.set_role(p_data.get('role', existing_entity.role), p_data.get('sub_role', existing_entity.sub_role))
                            if 'group' in p_data: existing_entity.set_group(p_data['group']) # 그룹 설정
                            # 위치는 MOVE 메시지에서 지속적으로 업데이트되므로 여기서는 역할 등만 업데이트
                            # print(f"Updated existing player {player_id}: {p_data.get('name')}")

                    print(f"Player List updated. Current other players: {list(self.other_players.keys())}")
                    self._update_player_list_ui(e['participants']) # UI 업데이트
                elif event.key == pygame.K_q:
                    # [CCTV Logic]
                    if self.player.status.role == "POLICE": # PxANIC! 역할 확인
                        if self.cctv_widget.active: self.cctv_widget.close()
                        else: self.cctv_widget.open()
                    else:
                        msg = self.player.toggle_device(self.services) # GameEntity에 toggle_device 구현 필요
                        if msg: self.services["popups"].add_popup(msg, self.player.position.x, self.player.position.y, 1.0) 
                elif e.get('type') == 'GAME_START':
                    print(f"GAME STARTED! Initial players: {e['players']}")
                    # PxANIC! 서버로부터 받은 초기 플레이어 정보(역할 등)를 바탕으로 엔티티 상태 업데이트
                    # self.player의 역할 업데이트 (자신이 누구인지 확인)
                    for p_data in e['players'].values():
                        if p_data['id'] == network_manager.client_id:
                            self.player.set_role(p_data['role'], p_data.get('sub_role'))
                            self.lbl_role.set_text(f"{p_data['role']} ({p_data['sub_role']})" if p_data.get('sub_role') else p_data['role'])
                            if p_data.get('group'): self.player.set_group(p_data['group'])
                            print(f"Your role: {self.player.role}, group: {self.player.team}")
                        elif p_data['id'] in self.other_players:
                            other_player_entity = self.other_players[p_data['id']]
                            other_player_entity.set_role(p_data['role'], p_data.get('sub_role'))
                            if p_data.get('group'): other_player_entity.set_group(p_data['group'])
                    
                    # TODO: 게임 시작 관련 UI 업데이트 (예: '게임 시작' 메시지 표시, 카운트다운 등)
                    # TODO: 게임 시작 후 특정 엔티티 초기화 로직 (예: 스폰 위치 조정)
                    self.game_started = True # PlayScene에 game_started 플래그 설정
                elif e.get('type') == 'UPDATE_ROLE':
                    target_id = e.get('id')
                    new_role = e.get('role')
                    if target_id == network_manager.client_id: # 자기 자신의 역할 업데이트
                        self.player.set_role(new_role)
                        self.lbl_role.set_text(new_role) # UI 업데이트
                        # TODO: 서브 역할 (sub_role)도 업데이트해야 할 수 있음
                    elif target_id in self.other_players: # 다른 플레이어의 역할 업데이트
                        other_player_entity = self.other_players[target_id]
                        other_player_entity.set_role(new_role)
                    # NPC(봇) 역할 업데이트는 PLAYER_LIST를 통해 이루어지므로 여기서는 처리하지 않음
                    print(f"Player {target_id} role updated to {new_role}")
                elif e.get('type') == 'CHANGE_GROUP':
                    target_id = e.get('target_id')
                    new_group = e.get('group')
                    if target_id == network_manager.client_id: # 자기 자신의 그룹 업데이트
                        self.player.set_group(new_group)
                    elif target_id in self.other_players: # 다른 플레이어의 그룹 업데이트
                        other_player_entity = self.other_players[target_id]
                        other_player_entity.set_group(new_group)
                    print(f"Player {target_id} group updated to {new_group}")
        
        minigame_manager = services["minigame"]
        if minigame_manager.is_minigame_active() or self.cctv_widget.active: # CCTV 활성화 시 플레이어 입력 막기
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
                
                # [네트워크 관련 추가] 플레이어 위치가 변경되면 서버에 전송
                curr_pos = (int(self.player.position.x), int(self.player.position.y))
                if curr_pos != self.last_sent_pos and network_manager and network_manager.client_id is not None:
                    network_manager.send_move(
                        curr_pos[0], 
                        curr_pos[1], 
                        self.player.is_moving, 
                        self.player.facing_direction
                    )
                    self.last_sent_pos = curr_pos
                
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

    def _update_player_list_ui(self, participants):
        # MAX_PLAYERS 대신 실제 참가자 수에 맞춰 표시
        for i, lbl in enumerate(self.player_labels):
            if i < len(participants):
                p = participants[i]
                role_str = f"({p['role']})" if 'role' in p else ""
                lbl.set_text(f"{p['name']} {role_str}")
            else:
                lbl.set_text("")
    
    # [PxANIC! 이식] 시간 단계 변경 콜백 로직
    def on_phase_change(self, old_phase, new_phase):
        print(f"[PlayScene] Phase changed from {old_phase} to {new_phase}")
        # PxANIC!의 _process_voting_results()에 해당하는 로직
        if old_phase == "AFTERNOON":
            self.show_vote_ui = False # 투표 UI 숨기기
            self.voting_panel.visible = False # 투표 패널 숨기기
            self._process_voting_results() # 투표 결과 처리
        # TODO: 투표 UI 표시 로직은 필요 없음 (AFTERNOON에만 띄우므로)
        
    def on_morning(self):
        print(f"[PlayScene] New Day: {self.services['time'].day_count}")
        if self.player:
            # PxANIC!의 is_indoors 로직 이식
            gx, gy = int(self.player.position.x), int(self.player.position.y) # GameEntity의 position은 월드 좌표
            
            # MapLoader를 통해 zone_id 확인
            zone_id = self.map_loader.get_zone_id(gx, gy)
            is_indoors = zone_id in INDOOR_ZONES
            
            self.player.morning_process(is_indoors)
        
        # self.other_players (네트워크 플레이어)는 서버에서 관리하므로 클라이언트에서 직접 morning_process 호출하지 않음
        # self.npcs (로컬 NPC)에 대해서만 호출
        for n in self.npcs:
            # 로컬 NPC의 위치를 기반으로 is_indoors 계산
            gx, gy = int(n.position.x), int(n.position.y)
            zone_id = self.map_loader.get_zone_id(gx, gy)
            is_indoors_npc = zone_id in INDOOR_ZONES
            n.morning_process(is_indoors_npc)

        self.has_murder_occurred = False # 살인 발생 여부 초기화

        # PxANIC!의 daily_news_log 및 ui.show_daily_news 로직
        # 이 로직들은 PlayScene의 UI 시스템에 맞춰 이식되었음 (팝업으로 표시)

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

    # [PxANIC! 이식] 역할별 특수 스킬 (비전투)
    def execute_siren(self):
        # 마피아 NPC 동결 로직
        for n in [x for x in self.npcs if x.status.role == "MAFIA" and x.status.alive]:
            n.status.is_frozen = True
            n.status.frozen_timer = pygame.time.get_ticks() + 5000 # 5초 동결
            self.services["interaction"].emit_noise(
                n.position.x, n.position.y,
                999, # SIREN의 base_rad (PxANIC! settings.py 참고)
                (0, 0, 255) # SIREN의 색상
            )
        
        self.is_mafia_frozen = True
        self.frozen_timer = pygame.time.get_ticks() + 5000
        
        self.services["popups"].add_popup("!!! SIREN !!!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 2.0, (100, 100, 255))
        self._process_sound_effect(("SIREN", self.player.position.x, self.player.position.y, 999)) # rad 999는 전역 효과

    def execute_sabotage(self):
        self.is_blackout = True
        self.blackout_timer = pygame.time.get_ticks() + 10000 # 10초 정전
        
        self.services["interaction"].emit_noise(
            self.player.position.x, self.player.position.y,
            999, # BOOM(EXPLOSION)의 base_rad (PxANIC! settings.py 참고)
            (50, 50, 50) # BOOM의 색상
        )
        self.services["popups"].add_popup("!!! SABOTAGE !!!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 2.0, (255, 0, 0))
        self._process_sound_effect(("EXPLOSION", self.player.position.x, self.player.position.y, 999)) # rad 999는 전역 효과
        
        # 시민/의사 역할 플레이어에게 공포 감정 부여 (GameEntity에 emotions 속성 필요)
        for t in [self.player] + [x for x in self.npcs if x.status.role in ["CITIZEN", "DOCTOR"] and x.status.alive]:
            if hasattr(t.status, 'emotions'):
                t.status.emotions['FEAR'] = 1 # GameEntity의 StatusComponent에 emotions 딕셔너리가 있다고 가정

    # [UI 이식] 자판기 관련 메서드
    def toggle_vending_machine(self):
        self.vending_panel.visible = not self.vending_panel.visible
        if self.vending_panel.visible:
            self._update_vending_ui() # 자판기 열릴 때 UI 업데이트

    def _update_vending_ui(self):
        if not self.player: return
        self.lbl_player_coins.set_text(f"Coins: {self.player.inventory.coins}")
        # TODO: 각 아이템 라벨의 가격/재고 등을 업데이트할 수 있음

    def _buy_item_from_vending(self, item_key):
        if self.player:
            result = self.player.inventory.buy_item(item_key, self.services)
            if result:
                print(result) # 팝업은 buy_item 내부에서 발생
                self._update_vending_ui() # 코인 정보 업데이트

    # [UI 이식] 투표 관련 메서드
    def _cast_vote(self, button_idx):
        if not self.voting_candidates: return
        if button_idx < 0 or button_idx >= len(self.voting_candidates): return

        target_entity = self.voting_candidates[button_idx]
        self.my_vote_target = target_entity # PxANIC!의 my_vote_target
        
        self.services["popups"].add_popup(f"Voted for {target_entity.name}", self.player.position.x, self.player.position.y, 1.5, (100, 255, 100))
        self.show_vote_ui = False # 투표 후 UI 닫기
        self.voting_panel.visible = False # 패널 숨기기

    def _update_voting_ui(self):
        # 투표 대상 목록 생성 (자신 포함 모든 플레이어 및 NPC)
        # TODO: 실제 투표 로직에서는 죽은 사람, 네트워크에 없는 사람 등 제외해야 함
        self.voting_candidates = [self.player] + list(self.other_players.values()) + self.npcs
        # 서버에서 받은 PARTICIPANTS 목록을 기반으로 하는 것이 더 정확함

        for i, btn in enumerate(self.candidate_buttons):
            if i < len(self.voting_candidates):
                candidate = self.voting_candidates[i]
                btn.set_text(f"{i+1}. {candidate.name} ({candidate.status.role})")
                btn.visible = True
            else:
                btn.visible = False

        self.lbl_vote_status.set_text("Select a candidate")

    # [PxANIC! 이식] 투표 결과 처리
    def _process_voting_results(self):
        # 모든 가능한 투표 대상을 수집
        all_possible_targets = [self.player] + list(self.other_players.values()) + self.npcs
        # 각 엔티티의 vote_count 초기화
        for entity in all_possible_targets:
            # GameEntity 또는 NpcEntity에 vote_count 속성이 있다고 가정
            if hasattr(entity, 'vote_count'):
                entity.vote_count = 0
            else:
                entity.vote_count = 0 # 없으면 추가

        # 플레이어의 투표 반영
        if hasattr(self, 'my_vote_target') and self.my_vote_target:
            self.my_vote_target.vote_count += 1
            self.my_vote_target = None # 투표 완료 후 초기화

        # NPC의 랜덤 투표 (PxANIC! 로직)
        for n in [x for x in self.npcs if x.status.alive]:
            if random.random() < 0.3: 
                # 자신과 다른 플레이어, 로컬 NPC 중에서 랜덤 선택 (죽은 대상 제외)
                alive_targets = [t for t in ([self.player] + list(self.other_players.values()) + self.npcs) if t.status.alive]
                if alive_targets:
                    target = random.choice(alive_targets)
                    target.vote_count += 1

        # 투표 결과 집계
        # 죽지 않은 모든 대상 (자신, 다른 플레이어, 로컬 NPC)
        voting_candidates_alive = [t for t in all_possible_targets if t.status.alive]
        
        candidates = sorted(voting_candidates_alive, key=lambda x: x.vote_count, reverse=True)

        if candidates and candidates[0].vote_count >= 2:
            # 최다 득표자들 중 랜덤 선택
            top_voted_entities = [c for c in candidates if c.vote_count == candidates[0].vote_count]
            if top_voted_entities:
                executed_entity = random.choice(top_voted_entities)
                executed_entity.status.is_dead = True # 사망 처리
                self.services["popups"].add_popup(f"{executed_entity.name} EXECUTION!", executed_entity.position.x, executed_entity.position.y, 2.0, (255, 0, 0))
                print(f"[PlayScene] {executed_entity.name} was executed with {executed_entity.vote_count} votes.")
            else:
                self.services["popups"].add_popup("No clear execution target!", self.player.position.x, self.player.position.y, 1.5, (255, 255, 0))
        else:
            self.services["popups"].add_popup("No execution this round.", self.player.position.x, self.player.position.y, 1.5, (100, 100, 255))
        
        # 모든 vote_count 초기화 (다음 라운드를 위해)
        for entity in all_possible_targets:
            entity.vote_count = 0


    # [PxANIC! 이식] 사운드 효과 처리
    def _process_sound_effect(self, f):
        s_type, fx_x, fx_y, rad = f # f는 (s_type, fx_x, fx_y, rad) 튜플로 가정 (source_role은 현재 미사용)
        
        # 날씨에 따른 반경 감소 (PxANIC! 로직)
        # if self.weather == 'RAIN': rad *= 0.8 # PlayScene에 weather 속성 없음

        self.services["audio"].play_spatial_sfx(s_type, self.player.position, pygame.math.Vector2(fx_x, fx_y))
        
        # SoundDirectionIndicator는 플레이어가 소리를 들을 수 있으나 시야에 없을 때 표시
        # PxANIC!의 is_visible_tile 확인 로직이 PlayScene에는 없으므로 일단 거리 기준으로만
        # TODO: FOV 시스템과 연동하여 시야 내/외 확인 로직 추가 필요
        if rad < 999: # 전역 효과가 아닐 때만 인디케이터 표시
            dist = self.player.position.distance_to(pygame.math.Vector2(fx_x, fx_y))
            # 임시로 플레이어로부터 특정 거리 이상 떨어져 있으면 인디케이터 표시
            if dist > 5 * TILE_SIZE: # 5타일 이상 떨어져 있으면
                # TODO: Sound_INFO에서 색상 가져오기
                self.services["interaction"].add_sound_indicator(self.player.position, pygame.math.Vector2(fx_x, fx_y), (255, 255, 255), duration=1.5)
