import pygame
from settings import TILE_SIZE, BLOCK_HEIGHT, INDOOR_ZONES, CUSTOM_COLORS # BLOCK_HEIGHT 추가
from colors import *
from world.tiles import get_texture, get_tile_category

class CharacterRenderer:
    _sprite_cache = {}
    
    pygame.font.init()
    NAME_FONT = pygame.font.SysFont("arial", 11, bold=True)
    POPUP_FONT = pygame.font.SysFont("arial", 12, bold=True)

    RECT_BODY = pygame.Rect(4, 4, 24, 24)
    RECT_CLOTH = pygame.Rect(4, 14, 24, 14)
    RECT_ARM_L = pygame.Rect(8, 14, 4, 14)
    RECT_ARM_R = pygame.Rect(20, 14, 4, 14)
    RECT_HAT_TOP = pygame.Rect(2, 2, 28, 5)
    RECT_HAT_RIM = pygame.Rect(6, 0, 20, 7)

    _name_surface_cache = {}

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()
        cls._name_surface_cache.clear()

    @classmethod
    def _get_cache_key(cls, entity, is_highlighted):
        skin_idx = entity.custom.get('skin', 0)
        cloth_idx = entity.custom.get('clothes', 0)
        hat_idx = entity.custom.get('hat', 0)
        facing = getattr(entity, 'facing_dir', (0, 1))
        return (skin_idx, cloth_idx, hat_idx, entity.role, entity.sub_role, facing, is_highlighted)

    @staticmethod
    def draw_entity(screen, entity, camera_x, camera_y, viewer_role="PLAYER", current_phase="DAY", viewer_device_on=False):
        if not entity.alive: return
        # [수정] Z-Level 반영하여 Y좌표 보정
        draw_x = entity.rect.x - camera_x
        draw_y = entity.rect.y - camera_y - (entity.z_level * BLOCK_HEIGHT)
        screen_w, screen_h = screen.get_width(), screen.get_height()
        if not (-50 < draw_x < screen_w + 50 and -50 < draw_y < screen_h + 50): return

        alpha = 255
        is_highlighted = False
        if viewer_role == "MAFIA" and viewer_device_on:
            is_highlighted = True; alpha = 255 

        if entity.is_hiding and not is_highlighted:
            is_visible = False
            if getattr(entity, 'is_player', False) or entity.name == "Player 1": is_visible, alpha = True, 120
            elif viewer_role == "SPECTATOR": is_visible, alpha = True, 120
            if not is_visible: return

        cache_key = CharacterRenderer._get_cache_key(entity, is_highlighted)
        if cache_key in CharacterRenderer._sprite_cache:
            base_surf = CharacterRenderer._sprite_cache[cache_key]
        else:
            base_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            skin_idx = entity.custom.get('skin', 0) % len(CUSTOM_COLORS['SKIN'])
            cloth_idx = entity.custom.get('clothes', 0) % len(CUSTOM_COLORS['CLOTHES'])
            body_color = CUSTOM_COLORS['SKIN'][skin_idx]
            clothes_color = CUSTOM_COLORS['CLOTHES'][cloth_idx]
            if is_highlighted: body_color = (255, 50, 50); clothes_color = (150, 0, 0)
            pygame.draw.ellipse(base_surf, (0, 0, 0, 80), (4, TILE_SIZE - 8, TILE_SIZE - 8, 6))
            pygame.draw.rect(base_surf, body_color, CharacterRenderer.RECT_BODY, border_radius=6)
            if entity.role == "MAFIA":
                if current_phase == "NIGHT":
                    pygame.draw.rect(base_surf, (30, 30, 35), CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
                    pygame.draw.polygon(base_surf, (180, 0, 0), [(16, 14), (13, 22), (19, 22)])
                else:
                    fake_color = clothes_color
                    if entity.sub_role == "POLICE": fake_color = (20, 40, 120)
                    elif entity.sub_role == "DOCTOR": fake_color = (240, 240, 250)
                    pygame.draw.rect(base_surf, fake_color, CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            elif entity.role == "DOCTOR":
                pygame.draw.rect(base_surf, (240, 240, 250), CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            elif entity.role == "POLICE":
                pygame.draw.rect(base_surf, (20, 40, 120), CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            else:
                pygame.draw.rect(base_surf, clothes_color, CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)

            f_dir = getattr(entity, 'facing_dir', (0, 1))
            ox, oy = f_dir[0] * 3, f_dir[1] * 2
            pygame.draw.circle(base_surf, (255, 255, 255), (16 - 5 + ox, 12 + oy), 3)
            pygame.draw.circle(base_surf, (0, 0, 0), (16 - 5 + ox + f_dir[0], 12 + oy + f_dir[1]), 1)
            pygame.draw.circle(base_surf, (255, 255, 255), (16 + 5 + ox, 12 + oy), 3)
            pygame.draw.circle(base_surf, (0, 0, 0), (16 + 5 + ox + f_dir[0], 12 + oy + f_dir[1]), 1)
            CharacterRenderer._sprite_cache[cache_key] = base_surf

        final_surf = base_surf
        if alpha < 255: final_surf = base_surf.copy(); final_surf.set_alpha(alpha)
        screen.blit(final_surf, (draw_x, draw_y))

        name_color = (230, 230, 230)
        if entity.role == "POLICE" and viewer_role in ["POLICE", "SPECTATOR"]: name_color = (100, 180, 255)
        elif entity.role == "MAFIA" and viewer_role in ["MAFIA", "SPECTATOR"]: name_color = (255, 100, 100)
        text_cache_key = (entity.uid, entity.name, name_color, entity.z_level) # [수정] Z-Level 추가
        if text_cache_key in CharacterRenderer._name_surface_cache: name_surf = CharacterRenderer._name_surface_cache[text_cache_key]
        else: name_surf = CharacterRenderer.NAME_FONT.render(entity.name, True, name_color); CharacterRenderer._name_surface_cache[text_cache_key] = name_surf
        screen.blit(name_surf, (draw_x + (TILE_SIZE // 2) - (name_surf.get_width() // 2), draw_y - 14))

class MapRenderer:
    CHUNK_SIZE = 16 # Tiles per chunk (16x32 = 512px)

    def __init__(self, map_manager):
        self.map_manager = map_manager
        # 3D 캐시: {(z, cx, cy): Surface}
        self._floor_cache = {}
        self._wall_cache = {}
        self.map_width_tiles = map_manager.width
        self.map_height_tiles = map_manager.height

    def invalidate_cache(self):
        self._floor_cache.clear()
        self._wall_cache.clear()

    def _render_chunk(self, z, cx, cy, layer_name):
        surf = pygame.Surface((self.CHUNK_SIZE * TILE_SIZE, self.CHUNK_SIZE * TILE_SIZE), pygame.SRCALPHA)
        start_col = cx * self.CHUNK_SIZE
        start_row = cy * self.CHUNK_SIZE
        end_col = min(start_col + self.CHUNK_SIZE, self.map_width_tiles)
        end_row = min(start_row + self.CHUNK_SIZE, self.map_height_tiles)
        
        if z >= len(self.map_manager.layers): return surf
        layer_data = self.map_manager.layers[z][layer_name]
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                draw_x = (c - start_col) * TILE_SIZE
                draw_y = (r - start_row) * TILE_SIZE
                tid, rot = layer_data[r][c]
                if tid != 0:
                    img = get_texture(tid, rot)
                    surf.blit(img, (draw_x, draw_y))
        return surf

    def draw(self, screen, camera, dt, entities, player_z_level=0, visible_tiles=None, tile_alphas=None):
        if tile_alphas is None: tile_alphas = {}

        all_render_items = [] # 모든 맵 타일과 엔티티를 담을 리스트

        # 1. 맵 타일 데이터 수집 (모든 층)
        # 보이는 화면 범위 계산
        cam_world_x_start = camera.x
        cam_world_y_start = camera.y
        cam_world_x_end = camera.x + camera.width / camera.zoom_level
        cam_world_y_end = camera.y + camera.height / camera.zoom_level

        start_tile_x = int(max(0, cam_world_x_start // TILE_SIZE))
        start_tile_y = int(max(0, cam_world_y_start // TILE_SIZE))
        end_tile_x = int(min(self.map_manager.width, cam_world_x_end // TILE_SIZE + 2))
        end_tile_y = int(min(self.map_manager.height, cam_world_y_end // TILE_SIZE + 2))

        for z in range(len(self.map_manager.layers)): # 모든 층을 순회
            is_current_or_below = (z <= player_z_level) # 플레이어 층 이하만 그림
            if not is_current_or_below: continue # 위층은 그리지 않음

            alpha_factor = 255 if (z == player_z_level) else 150 # 현재 층은 불투명, 아래층은 반투명
            
            for r in range(start_tile_y, end_tile_y):
                for c in range(start_tile_x, end_tile_x):
                    # 2.5D 투영 좌표 계산
                    draw_base_x = c * TILE_SIZE
                    draw_base_y = r * TILE_SIZE - (z * BLOCK_HEIGHT) 

                    # Floor
                    tid_f, rot_f = self.map_manager.get_tile_full(c, r, z, 'floor')
                    if tid_f != 0:
                        img_f = get_texture(tid_f, rot_f)
                        all_render_items.append((draw_base_y, img_f, (draw_base_x - camera.x, draw_base_y - camera.y), alpha_factor))
                        
                        # Zone Overlay
                        zid = self.map_manager.zone_map[r][c]
                        if zid != 0 and zid in ZONES:
                            zone_color = ZONES[zid]['color']
                            zone_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                            zone_surf.fill(zone_color)
                            all_render_items.append((draw_base_y + 0.1, zone_surf, (draw_base_x - camera.x, draw_base_y - camera.y), alpha_factor)) # 약간 위에 그려지도록

                    # Objects (Non-Doors first)
                    tid_o, rot_o = self.map_manager.get_tile_full(c, r, z, 'object')
                    if tid_o != 0 and get_tile_category(tid_o) != 5:
                        img_o = get_texture(tid_o, rot_o)
                        all_render_items.append((draw_base_y + TILE_SIZE, img_o, (draw_base_x - camera.x, draw_base_y - camera.y), alpha_factor)) # 오브젝트는 Y Sorting을 위해 +TILE_SIZE

                    # Walls
                    tid_w, rot_w = self.map_manager.get_tile_full(c, r, z, 'wall')
                    if tid_w != 0:
                        img_w = get_texture(tid_w, rot_w)
                        all_render_items.append((draw_base_y + TILE_SIZE, img_w, (draw_base_x - camera.x, draw_base_y - camera.y), alpha_factor)) # 벽도 Y Sorting을 위해 +TILE_SIZE

        # 2. 엔티티 데이터 수집
        for entity in entities:
            if entity.alive:
                # 엔티티도 맵 타일과 같은 기준으로 Y좌표 보정
                entity_draw_y = entity.rect.y - (entity.z_level * BLOCK_HEIGHT)
                # CharacterRenderer를 직접 호출하지 않고, 필요한 정보만 저장
                all_render_items.append((entity_draw_y + TILE_SIZE, 'ENTITY', entity)) # Y Sorting을 위해 +TILE_SIZE

        # 3. 깊이 정렬 (Y-Sorting)
        all_render_items.sort(key=lambda item: item[0])

        # 4. 정렬된 순서대로 그리기
        for item in all_render_items:
            sort_key, item_type, data = item[0], item[1], item[2]
            alpha_factor = item[3] if len(item) > 3 else 255
            
            if item_type == 'ENTITY':
                CharacterRenderer.draw_entity(screen, data, camera.x, camera.y, player_z_level, "DAY", False) # phase와 device_on은 임시값
            else: # Map Tile (img, pos, alpha)
                img, pos = data, item[2]
                if alpha_factor < 255: 
                    img = img.copy()
                    img.set_alpha(alpha_factor)
                screen.blit(img, pos)

        # 5. 문 (오브젝트 중 문은 가장 마지막에 그려져야 함 -> 깊이 정렬이 깨질 수 있으므로 별도 처리)
        # 하지만 Y-Sorting에 포함시키면 더 자연스러움. 여기서는 Y-Sorting에 포함된 것으로 가정하고 별도 루프 제거.
        # 만약 문이 다른 오브젝트와 겹쳐서 이상하게 그려진다면, 문의 Z값이 더 높거나
        # 특별한 정렬 규칙이 필요할 수 있음. (일단은 Y-Sorting에 포함)