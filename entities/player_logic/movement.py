import pygame
from settings import SPEED_WALK, SPEED_RUN, SPEED_CROUCH, POLICE_SPEED_MULTI, TILE_SIZE, BLOCK_HEIGHT # BLOCK_HEIGHT 추가
from world.tiles import STAIRS_UP_TILES, STAIRS_DOWN_TILES

class MovementLogic:
    def __init__(self, player):
        self.p = player
        self.logger = None
        if hasattr(self.p, 'game') and self.p.game is not None:
            self.logger = getattr(self.p.game, 'logger', None)
        
        # [Z-Physics] 낙하 관련 상태 변수
        self.is_falling = False
        self.fall_speed = 0
        self.last_ground_z = 0

    def get_current_speed(self):
        speed = SPEED_WALK
        if self.p.crouching: speed = SPEED_CROUCH
        elif self.p.running: speed = SPEED_RUN
        
        if self.p.role == 'POLICE':
            speed *= POLICE_SPEED_MULTI
        return speed

    def handle_input(self):
        # 1. 키 입력 처리
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        # 낙하 중이 아닐 때만 이동 가능
        if not self.is_falling:
            if keys[pygame.K_LEFT]: dx = -1
            elif keys[pygame.K_RIGHT]: dx = 1
            
            if keys[pygame.K_UP]: dy = -1
            elif keys[pygame.K_DOWN]: dy = 1

            # 달리기/웅크리기 상태 확인
            self.p.running = keys[pygame.K_LSHIFT] # and not self.p.crouching (crouching은 player 클래스에 없음)
            self.p.crouching = keys[pygame.K_LCTRL]

        # 2. 이동 속도 계산 및 이동 실행
        speed = self.get_current_speed()
        is_moving = False
        if dx != 0 or dy != 0:
            # 대각선 이동 보정
            if dx != 0 and dy != 0:
                speed *= 0.7071
            
            # 실제 이동 (충돌 처리는 Entity.move_single_axis에서 수행)
            self.p.move_single_axis(dx * speed, 0)
            self.p.move_single_axis(0, dy * speed)
            
            is_moving = True
        else:
            is_moving = False

        # 3. [핵심] Z축 물리 및 계단 처리 호출
        self._handle_z_physics()

        # [Optimization] Update Spatial Grid Position (handle_input에 직접 포함)
        if hasattr(self.p, 'world') and self.p.world.spatial_grid:
            self.p.world.spatial_grid.update_entity(self.p)

        self.p.is_moving = is_moving
        return is_moving

    def _handle_z_physics(self):
        """
        중력(낙하)과 계단 이동을 처리하는 함수
        매 프레임 호출됩니다.
        """
        map_mgr = self.p.map_manager
        
        # 현재 플레이어의 타일 좌표
        # 플레이어의 발 위치가 아니라 중심 위치로 Z축 계산
        cx = int(self.p.rect.centerx // TILE_SIZE)
        cy = int(self.p.rect.centery // TILE_SIZE)
        cz = self.p.z_level

        # 맵 범위 밖이면 처리 안 함
        if not (0 <= cx < map_mgr.width and 0 <= cy < map_mgr.height): return 

        # --- A. 계단 처리 (Stairs) ---
        # 발 밑의 오브젝트 레이어 확인
        obj_tid = map_mgr.get_tile(cx, cy, cz, 'object')
        floor_tid = map_mgr.get_tile(cx, cy, cz, 'floor') # 바닥 자체도 계단일 수 있음
        
        # 위로 가는 계단
        if obj_tid in STAIRS_UP_TILES or floor_tid in STAIRS_UP_TILES: 
            target_z = cz + 1
            # 다음 층(z+1)에 바닥이 있는지 확인 (천장 뚫고 올라가는 것 방지)
            if target_z < len(map_mgr.layers) and map_mgr.get_tile(cx, cy, target_z, 'floor') != 0: 
                self.p.z_level = target_z
                self.p.add_popup("Stairs Up!", (100, 255, 100))
                # 계단 오를 때 Y좌표 조정 (화면상 위로 이동)
                self.p.rect.y -= BLOCK_HEIGHT
                self.p.pos_y = float(self.p.rect.y)
                self.last_ground_z = self.p.z_level

        # 아래로 가는 계단 (1층(Z=0)에서는 내려갈 수 없음)
        elif (obj_tid in STAIRS_DOWN_TILES or floor_tid in STAIRS_DOWN_TILES) and cz > 0:
            target_z = cz - 1
            # 아래층(z-1)에 바닥이 있는지 확인 (없는 곳으로 내려가지 않도록)
            if target_z >= 0 and map_mgr.get_tile(cx, cy, target_z, 'floor') != 0:
                self.p.z_level = target_z
                self.p.add_popup("Stairs Down!", (100, 255, 100))
                # 계단 내려갈 때 Y좌표 조정 (화면상 아래로 이동)
                self.p.rect.y += BLOCK_HEIGHT
                self.p.pos_y = float(self.p.rect.y)
                self.last_ground_z = self.p.z_level
        
        # --- B. 중력 처리 (Gravity) ---
        # 현재 서 있는 곳에 바닥(Floor)이 있는지 확인
        current_floor_tid = map_mgr.get_tile(cx, cy, cz, 'floor')
        
        # 바닥이 없고 + 1층 이상이라면 -> 낙하
        if current_floor_tid == 0 and cz > 0:
            if not self.is_falling:
                self.is_falling = True
                # self.last_ground_z = cz # 이미 위에서 설정
                print("[Physics] Start Falling!")
            
            # 바로 아래층에 바닥이 있는지 확인
            below_floor_exists = (cz - 1 >= 0 and map_mgr.get_tile(cx, cy, cz - 1, 'floor') != 0)

            if below_floor_exists:
                # 바로 아래층에 바닥이 있으면 착지
                self.p.z_level -= 1
                self.is_falling = False
                # [Sound] 착지 사운드 재생
                # self.p.game.sound_manager.play_sfx('FOOTSTEP') 
                self.p.add_popup("Land!", (200, 200, 200))
                print(f"[Physics] Landed on Z={self.p.z_level}")
                # 약간의 y 보정으로 착지 충돌 방지
                self.p.rect.y += BLOCK_HEIGHT # 아래층으로 떨어진 만큼 y좌표 보정
                self.p.pos_y = float(self.p.rect.y)
                self.last_ground_z = self.p.z_level
            else: # 아래층도 바닥이 없으면 계속 떨어짐
                # 이 로직은 매 프레임 호출되므로, 층을 계속 낮춤
                # 만약 낙하 애니메이션 등을 구현하려면 여기에 타이머/속도 로직 추가
                self.p.z_level -= 1
                self.p.rect.y += BLOCK_HEIGHT # 계속 떨어지는 효과
                self.p.pos_y = float(self.p.rect.y)
                if self.p.z_level < 0: # 맵 최하단 이하로 떨어지면 사망 처리 등
                    # self.p.is_dead = True # 예시: 사망 처리
                    self.p.z_level = 0 # 0층 이하로는 안 떨어지게 일단 고정
                    print("[Physics] Fell out of map!")
        elif self.is_falling and current_floor_tid != 0: # 바닥에 닿음
            self.is_falling = False
            self.last_ground_z = self.p.z_level

    def update_stamina(self, is_moving):
        infinite = (('RAGE' in self.p.emotions and self.p.role == "POLICE") or self.p.buffs['INFINITE_STAMINA'])
        if self.p.running and is_moving and not infinite: self.p.breath_gauge -= 0.5
        elif not self.p.running: self.p.breath_gauge = min(100, self.p.breath_gauge + 0.5)
