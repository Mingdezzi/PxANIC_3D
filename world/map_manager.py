import json
import os
import pygame
from settings import TILE_SIZE
from world.tiles import check_collision, TILE_DATA, BED_TILES, HIDEABLE_TILES

class MapManager:
    def __init__(self):
        # [Core Change] 3차원 레이어 시스템
        # layers[z] = {'floor': 2D배열, 'wall': 2D배열, 'object': 2D배열}
        self.layers = [] 
        self.width = 0
        self.height = 0
        self.spawn_x = 100
        self.spawn_y = 100
        
        # 3D 충돌 맵: self.collision_cache[z][y][x]
        self.collision_cache = [] 
        
        # 타일 캐시: {tid: [(x, y, z), ...]}
        self.tile_cache = {} 
        self.tile_cooldowns = {}
        self.open_doors = {}
        self.zone_map = []
        
        self.name_to_tid = {data['name']: tid for tid, data in TILE_DATA.items()}

    def _ensure_z_layer(self, target_z):
        """해당 Z층이 존재하지 않으면, 그 사이의 모든 층을 생성합니다."""
        while len(self.layers) <= target_z:
            new_layer = {
                'floor': [[(0, 0) for _ in range(self.width)] for _ in range(self.height)],
                'wall': [[(0, 0) for _ in range(self.width)] for _ in range(self.height)],
                'object': [[(0, 0) for _ in range(self.width)] for _ in range(self.height)]
            }
            self.layers.append(new_layer)
            # 새 층의 충돌 맵도 생성
            self.collision_cache.append([[False for _ in range(self.width)] for _ in range(self.height)])

    def get_tile(self, gx, gy, z=0, layer='floor'):
        # 범위 체크에 z 추가
        if 0 <= z < len(self.layers) and 0 <= gx < self.width and 0 <= gy < self.height:
            return self.layers[z][layer][gy][gx][0]
        return 0

    def get_tile_full(self, gx, gy, z=0, layer='floor'):
        if 0 <= z < len(self.layers) and 0 <= gx < self.width and 0 <= gy < self.height:
            return self.layers[z][layer][gy][gx]
        return (0, 0)

    def set_tile(self, gx, gy, tid, z=0, rotation=0, layer=None):
        if not (0 <= gx < self.width and 0 <= gy < self.height): return
        
        # 필요한 층까지 자동 생성
        self._ensure_z_layer(z)
        
        if layer is None:
            # ID 범위로 레이어 자동 추론
            if 1000000 <= tid < 3000000: layer = 'floor'
            elif 3000000 <= tid < 5000000: layer = 'wall'
            else: layer = 'object'
            
        # 데이터 설정
        self.layers[z][layer][gy][gx] = (tid, rotation)
        
        # 최적화: 충돌 갱신 (Z축 반영)
        self._update_collision_at(gx, gy, z)
        
        # 타일 캐시 갱신 (간소화됨)
        # 실제로는 old_tid를 추적해서 remove하고 append 해야 함

    def _update_collision_at(self, x, y, z):
        if not (0 <= z < len(self.layers) and 0 <= x < self.width and 0 <= y < self.height): return
        
        is_blocked = False
        # 벽이나 오브젝트가 있으면 충돌
        for layer in ['wall', 'object']:
            tid = self.layers[z][layer][y][x][0]
            if tid != 0 and check_collision(tid):
                if tid not in BED_TILES and tid not in HIDEABLE_TILES and tid != 5310005:
                    is_blocked = True
                    break
        
        self.collision_cache[z][y][x] = is_blocked

    def check_any_collision(self, gx, gy, z=0):
        # [Engine] 3D 충돌 체크
        # 1. 맵 범위 밖
        if not (0 <= gx < self.width and 0 <= gy < self.height): return True
        # 2. 해당 층이 없으면? (낙하 로직이 없다면 이동 불가로 처리하거나, 1층이면 허용 등 정책 필요)
        # 여기서는 "없는 층 = 허공 = 이동 불가"로 가정하거나 "데이터 없으면 통과"로 할 수 있음.
        # 안전하게: 층 데이터가 없으면 충돌은 아님 (단, 바닥이 없으면 추락해야 함 -> 이는 물리엔진 영역)
        if not (0 <= z < len(self.layers)): return False
        
        return self.collision_cache[z][gy][gx]

    def create_default_map(self):
        self.width, self.height = 40, 30
        self.layers = []
        self._ensure_z_layer(0) # 1층(Z=0) 생성
        
        # 기본 잔디 깔기 (Z=0)
        for y in range(self.height):
            for x in range(self.width): 
                self.set_tile(x, y, 1110000, z=0)
        
        # 테두리 벽
        for x in range(self.width):
            self.set_tile(x, 0, 3220000, z=0); self.set_tile(x, self.height-1, 3220000, z=0)
        for y in range(self.height):
            self.set_tile(0, y, 3220000, z=0); self.set_tile(self.width-1, y, 3220000, z=0)

        self.zone_map = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.build_collision_cache()

    def build_collision_cache(self):
        self.collision_cache = []
        for z in range(len(self.layers)):
            self.collision_cache.append([[False for _ in range(self.width)] for _ in range(self.height)])
            for y in range(self.height):
                for x in range(self.width):
                    self._update_collision_at(x, y, z)

    def load_map(self, filename="map.json"):
        if not os.path.exists(filename): self.create_default_map(); return True
        try:
            with open(filename, 'r', encoding='utf-8') as f: data = json.load(f)
            self.width = data.get('width', 50)
            self.height = data.get('height', 50)
            
            self.layers = []
            
            # [Migration] 데이터 구조 확인
            if 'layers' in data and isinstance(data['layers'], list):
                # 신규 3D 포맷 (리스트 형태)
                loaded_layers = data['layers']
                for z, l_data in enumerate(loaded_layers):
                    self._ensure_z_layer(z)
                    for ln in ['floor', 'wall', 'object']:
                        grid = l_data.get(ln, [])
                        for y in range(min(len(grid), self.height)):
                            for x in range(min(len(grid[y]), self.width)):
                                val = grid[y][x]
                                self.layers[z][ln][y][x] = (val, 0) if isinstance(val, int) else tuple(val)
            else:
                # 구버전 포맷 (단일 층) -> Z=0으로 변환
                self._ensure_z_layer(0)
                # 'layers' 키가 있거나 'map_data' 등 과거 필드명 호환
                legacy = data.get('layers', data.get('map_data', {}))
                for ln in ['floor', 'wall', 'object']:
                    if ln in legacy:
                        grid = legacy[ln]
                        for y in range(min(len(grid), self.height)):
                            for x in range(min(len(grid[y]), self.width)):
                                val = grid[y][x]
                                self.layers[0][ln][y][x] = (val, 0) if isinstance(val, int) else tuple(val)
            
            self.zone_map = data.get('zones', [[0 for _ in range(self.width)] for _ in range(self.height)])
            self.build_collision_cache()
            
            # 스폰 포인트 갱신
            for y in range(self.height):
                for x in range(self.width):
                    if self.zone_map[y][x] == 1: 
                        self.spawn_x, self.spawn_y = x * TILE_SIZE, y * TILE_SIZE
                        break
            return True
        except Exception as e:
            import traceback; traceback.print_exc()
            self.create_default_map()
            return True

    def save_map(self, filename="map.json"):
        data = {
            "width": self.width,
            "height": self.height,
            "layers": self.layers, # 3D 데이터 저장
            "zones": self.zone_map
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
    # [Helper Methods]
    def is_tile_on_cooldown(self, gx, gy):
        now = pygame.time.get_ticks()
        if (gx, gy) in self.tile_cooldowns:
            if now < self.tile_cooldowns[(gx, gy)]: return True
            else: del self.tile_cooldowns[(gx, gy)]
        return False

    def set_tile_cooldown(self, gx, gy, duration_ms=3000):
        self.tile_cooldowns[(gx, gy)] = pygame.time.get_ticks() + duration_ms

    def update_doors(self, dt, entities):
        # 현재는 Z=0 문만 처리 (추후 확장 필요)
        now = pygame.time.get_ticks()
        to_close = []
        active_rects = [ent.rect.inflate(-15, -15) for ent in entities if ent.alive]
        
        for (gx, gy), open_time in list(self.open_doors.items()):
            if now < open_time + 5000: continue 
            door_rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if door_rect.collidelist(active_rects) != -1: continue
            to_close.append((gx, gy))
        
        for (gx, gy) in to_close:
            self.close_door(gx, gy)

    def _find_state_tile(self, current_tid, find_str, replace_str):
        if current_tid not in TILE_DATA: return None
        current_name = TILE_DATA[current_tid]['name']
        target_name = current_name.replace(find_str, replace_str)
        if target_name in self.name_to_tid: return self.name_to_tid[target_name]
        korean_map = {"Closed": "닫힘", "Open": "열림", "Locked": "잠김"}
        if find_str in korean_map and replace_str in korean_map:
            target_name_fixed = target_name.replace(korean_map[find_str], korean_map[replace_str])
            if target_name_fixed in self.name_to_tid: return self.name_to_tid[target_name_fixed]
        return None

    def open_door(self, gx, gy, layer='object', z=0):
        tid, rot = self.get_tile_full(gx, gy, z, layer)
        target_tid = self._find_state_tile(tid, "Closed", "Open")
        if not target_tid: target_tid = self._find_state_tile(tid, "Locked", "Open")
        if target_tid:
            self.set_tile(gx, gy, target_tid, z=z, rotation=rot, layer=layer)
            self.open_doors[(gx, gy)] = pygame.time.get_ticks()

    def close_door(self, gx, gy, layer='object', z=0):
        tid, rot = self.get_tile_full(gx, gy, z, layer)
        target_tid = self._find_state_tile(tid, "Open", "Closed")
        if target_tid:
            self.set_tile(gx, gy, target_tid, z=z, rotation=rot, layer=layer)
            if (gx, gy) in self.open_doors: del self.open_doors[(gx, gy)]

    def lock_door(self, gx, gy, layer='object', z=0):
        tid, rot = self.get_tile_full(gx, gy, z, layer)
        target_tid = self._find_state_tile(tid, "Closed", "Locked")
        if target_tid:
            self.set_tile(gx, gy, target_tid, z=z, rotation=rot, layer=layer)
            return True
        return False

    def unlock_door(self, gx, gy, layer='object', z=0):
        tid, rot = self.get_tile_full(gx, gy, z, layer)
        target_tid = self._find_state_tile(tid, "Locked", "Closed")
        if target_tid:
            self.set_tile(gx, gy, target_tid, z=z, rotation=rot, layer=layer)
            return True
        return False
        
    def get_spawn_points(self, zone_id=1):
        points = []
        # 현재는 Z=0 스폰 포인트만 검색
        for y in range(self.height):
            for x in range(self.width):
                if self.zone_map[y][x] == zone_id:
                    if not self.check_any_collision(x, y, z=0):
                        points.append((x * TILE_SIZE, y * TILE_SIZE))
        return points
