import pygame
import random
from settings import TILE_SIZE, ITEMS
from colors import CUSTOM_COLORS
from world.tiles import check_collision, get_tile_function, get_tile_category, BED_TILES, HIDEABLE_TILES

class Entity:
    def __init__(self, x, y, map_data, map_width, map_height, zone_map, name="Entity", role="CITIZEN", map_manager=None):

        # [Optimization] Hitbox reduction: 32x32 -> 20x20 for smoother passage through doors
        self.rect = pygame.Rect(x + 6, y + 6, TILE_SIZE - 12, TILE_SIZE - 12)
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.color = (255, 255, 255)

        self.map_data = map_data
        # [Safety] 초기화 시 None이면 0으로 설정 (map_manager가 우선하도록 변경)
        self.map_width = map_width if map_width is not None else 0
        self.map_height = map_height if map_height is not None else 0
        self.zone_map = zone_map
        self.map_manager = map_manager

        self.name = name
        self.role = role
        self.sub_role = None

        # [수정] 기본 스탯 100으로 확장
        self.max_hp = 100
        self.hp = 100
        self.max_ap = 100
        self.ap = 100

        self.coins = 0
        self.alive = True

        # [New] Status Effects & Emotions
        self.status_effects = {
            'ANXIETY': 0,    # 0~10: Anxiety Level (Heartbeat)
            'PAIN': False,   # Low HP
            'FATIGUE': False,# Low AP
            'FEAR': False,   # Encounter Mafia
            'RAGE': False,   # Police/Mafia Buff
            'DOPAMINE': False# Mafia Chase Buff
        }

        self.is_hiding = False
        self.hiding_type = 0
        self.hidden_in_solid = False
        self.inventory = {k: 0 for k in ITEMS.keys()}
        self.inventory['BATTERY'] = 1
        self.emotions = {}

        self.buffs = {
            'INFINITE_STAMINA': False,
            'SILENT': False,
            'FAST_WORK': False,
            'NO_PAIN': False
        }

        self.is_moving = False
        self.custom = {
            'skin': random.randint(0, len(CUSTOM_COLORS['SKIN'])-1),
            'clothes': random.randint(0, len(CUSTOM_COLORS['CLOTHES'])-1),
            'hat': random.randint(0, len(CUSTOM_COLORS['HAT'])-1)
        }
        self.facing_right = True
        self.facing_dir = (0, 1)
        self.stun_timer = 0
        self.device_on = False
        self.device_battery = 100.0
        self.powerbank_uses = 0
        self.z_level = 0 # [추가] 현재 위치한 층 (0: 1층, 1: 2층 ...)

        self.popups = []

    def add_popup(self, text, color=(255, 255, 255)):
        """엔티티 머리 위에 1.5초간 지속되는 팝업 메시지 추가"""
        self.popups.append({
            'text': text,
            'color': color,
            'timer': pygame.time.get_ticks() + 1500
        })

    def is_visible_villain(self, phase):
        if self.role == "MAFIA" and phase in ['NIGHT', 'DAWN']:
            return True
        return False

    def morning_process(self):
        for k in self.buffs: self.buffs[k] = False
        self.hp = min(self.max_hp, self.hp + 1)

    def is_stunned(self):
        return pygame.time.get_ticks() < self.stun_timer

    def take_stun(self, duration_ms=2000):
        self.stun_timer = pygame.time.get_ticks() + duration_ms
        self.is_moving = False
        if hasattr(self, 'path'): self.path = []

    def take_damage(self, amount):
        if not self.alive: return "ALREADY_DEAD"
        if self.role == "POLICE": return "IMMUNE"

        if self.inventory.get('ARMOR', 0) > 0:
            self.inventory['ARMOR'] -= 1
            return "BLOCKED"

        if self.inventory.get('POTION', 0) > 0 and self.hp - amount <= 0:
            self.inventory['POTION'] -= 1
            self.hp = 5
            self.alive = False
            return "DIED_BUT_REVIVABLE"

        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return "DIED"
        return "HIT"

    def heal(self, amount):
        if self.alive and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + amount)
            return True
        return False

    def try_spend_ap(self, amount, allow_health_cost=True):
        if self.ap >= amount:
            self.ap -= amount
            return True
        else:
            if self.role == "POLICE": self.ap = 0; return True
            if not allow_health_cost: return False
            
            if self.buffs['NO_PAIN']: hp_cost = 0
            else: hp_cost = amount * 2

            if hp_cost > 0: self.take_damage(hp_cost)
            return True

    def use_item(self, item_key):
        if not self.alive: return False
        if self.inventory.get(item_key, 0) <= 0: return False

        used = False
        s_type = "CRUNCH"

        if item_key == 'TANGERINE':
            if self.hp < self.max_hp: self.hp = min(self.max_hp, self.hp + 2); used = True
        elif item_key == 'CHOCOBAR':
            if self.ap < self.max_ap: self.ap = min(self.max_ap, self.ap + 2); used = True
        elif item_key == 'TORTILLA':
            if self.hp < self.max_hp or self.ap < self.max_ap:
                self.hp = min(self.max_hp, self.hp + 3)
                self.ap = min(self.max_ap, self.ap + 3)
                used = True
        elif item_key == 'MEDKIT':
            if self.hp < self.max_hp: self.hp = self.max_hp; used = True
            s_type = "CLICK"

        elif item_key == 'ENERGY_DRINK':
            if not self.buffs['INFINITE_STAMINA']:
                self.hp = max(1, self.hp - 3)
                self.buffs['INFINITE_STAMINA'] = True
                used = True; s_type = "GULP"
        elif item_key == 'PEANUT_BUTTER':
            if not self.buffs['SILENT']: self.buffs['SILENT'] = True; used = True
        elif item_key == 'COFFEE':
            if not self.buffs['FAST_WORK']: self.buffs['FAST_WORK'] = True; used = True; s_type = "GULP"
        elif item_key == 'PAINKILLER':
            if not self.buffs['NO_PAIN']: self.buffs['NO_PAIN'] = True; used = True; s_type = "GULP"

        elif item_key == 'BATTERY':
            if self.device_battery < 100: self.device_battery = min(100, self.device_battery + 50); used = True; s_type = "CLICK"
        elif item_key == 'POWERBANK':
            if self.device_battery < 100:
                self.device_battery = 100
                self.powerbank_uses += 1
                if self.powerbank_uses >= 2:
                    self.powerbank_uses = 0
                    used = True
                else:
                    self.add_popup("Used once (1 left)", (100, 255, 100))
                    return ("Used once (1 left)", ("CLICK", self.rect.centerx, self.rect.centery, 3 * TILE_SIZE, self.role))
                s_type = "CLICK"

        if used:
            self.inventory[item_key] -= 1
            return ("Used " + ITEMS[item_key]['name'], (s_type, self.rect.centerx, self.rect.centery, 4 * TILE_SIZE, self.role))
        return False

    def move_single_axis(self, dx, dy, npcs=None):
        if dx > 0: self.facing_right = True; self.facing_dir = (1, 0)
        elif dx < 0: self.facing_right = False; self.facing_dir = (-1, 0)
        if dy > 0: self.facing_dir = (0, 1)
        elif dy < 0: self.facing_dir = (0, -1)

        self.pos_x += dx; self.pos_y += dy
        self.rect.x, self.rect.y = round(self.pos_x), round(self.pos_y)

        if self.hidden_in_solid: return

        # [수정] 맵 크기 안전하게 가져오기 (MapManager 우선 사용)
        current_map_w = self.map_manager.width if self.map_manager else self.map_width
        current_map_h = self.map_manager.height if self.map_manager else self.map_height
        
        # 만약 여전히 None이거나 0이면 기본값 사용 (안전장치)
        if not current_map_w: current_map_w = 100
        if not current_map_h: current_map_h = 100

        # 충돌 검사 범위 계산
        start_gx = max(0, self.rect.left // TILE_SIZE)
        end_gx = min(current_map_w, (self.rect.right // TILE_SIZE) + 1)
        start_gy = max(0, self.rect.top // TILE_SIZE)
        end_gy = min(current_map_h, (self.rect.bottom // TILE_SIZE) + 1)

        # 캐시 조회용 변수
        collision_cache = getattr(self.map_manager, 'collision_cache', None)

        for y in range(start_gy, end_gy):
            for x in range(start_gx, end_gx):
                is_blocking = False
                
                # [Z축 적용] 캐시 확인
                if collision_cache and self.z_level < len(collision_cache):
                    # 범위 안전 체크
                    if 0 <= y < len(collision_cache[self.z_level]) and 0 <= x < len(collision_cache[self.z_level][0]):
                        if collision_cache[self.z_level][y][x]:
                            is_blocking = True
                else:
                    # 백업 로직
                    tids_to_check = []
                    if self.map_manager:
                        for layer in ['wall', 'object']:
                            val = self.map_manager.get_tile_full(x, y, self.z_level, layer)
                            if val[0] != 0: tids_to_check.append(val[0])
                    elif self.map_data:
                        # 2D 맵 데이터 폴백
                        if 0 <= y < len(self.map_data) and 0 <= x < len(self.map_data[0]):
                            tids_to_check.append(self.map_data[y][x])

                    for tid in tids_to_check:
                        if check_collision(tid):
                            if tid not in BED_TILES and tid not in HIDEABLE_TILES and tid != 5310005:
                                is_blocking = True; break

                if is_blocking:
                    tile_left = x * TILE_SIZE
                    tile_top = y * TILE_SIZE
                    tile_right = tile_left + TILE_SIZE
                    tile_bottom = tile_top + TILE_SIZE
                    
                    if (self.rect.right > tile_left and self.rect.left < tile_right and
                        self.rect.bottom > tile_top and self.rect.top < tile_bottom):
                        
                        if dx > 0: self.rect.right = tile_left
                        elif dx < 0: self.rect.left = tile_right
                        if dy > 0: self.rect.bottom = tile_top
                        elif dy < 0: self.rect.top = tile_bottom
                        
                        self.pos_x, self.pos_y = float(self.rect.x), float(self.rect.y)

        # [수정] 맵 밖으로 나가지 못하게 처리 (Safe Bounds)
        map_w_px = current_map_w * TILE_SIZE
        map_h_px = current_map_h * TILE_SIZE
        
        if self.rect.left < 0: self.rect.left = 0
        elif self.rect.right > map_w_px: self.rect.right = map_w_px
        if self.rect.top < 0: self.rect.top = 0
        elif self.rect.bottom > map_h_px: self.rect.bottom = map_h_px
        
        self.pos_x, self.pos_y = self.rect.x, self.rect.y