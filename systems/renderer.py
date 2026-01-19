import pygame
from settings import TILE_SIZE, BLOCK_HEIGHT, TILE_STEP_Y, INDOOR_ZONES, ZONES

try:
    from colors import CUSTOM_COLORS
except ImportError:
    CUSTOM_COLORS = {}

from world.tiles import get_texture, get_tile_category

class CharacterRenderer:
    _name_surface_cache = {}
    _sprite_cache = {}
    
    pygame.font.init()
    NAME_FONT = pygame.font.SysFont("malgungothic", 12, bold=True)

    RECT_BODY = pygame.Rect(4, 4, 24, 24)
    RECT_CLOTH = pygame.Rect(4, 14, 24, 14)

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()
        cls._name_surface_cache.clear()

    @staticmethod
    def draw_entity(screen, entity, camera_x, camera_y, role_name="CITIZEN", phase="DAY", device_on=False):
        if not entity.alive: return

        # [핵심] 캐릭터 위치 Y축 압축 (Isometric Projection)
        # 논리적 좌표(rect.y)를 시각적 좌표(visual_y)로 변환
        # TILE_SIZE(32) -> TILE_STEP_Y(24) 비율로 압축
        visual_entity_y = (entity.rect.y / TILE_SIZE) * TILE_STEP_Y
        
        draw_x = entity.rect.x - camera_x
        draw_y = visual_entity_y - camera_y - (entity.z_level * BLOCK_HEIGHT)
        
        screen_w, screen_h = screen.get_width(), screen.get_height()

        if not (-100 < draw_x < screen_w + 100 and -100 < draw_y < screen_h + 100): return

        alpha = 255
        is_highlighted = False
        if role_name == "MAFIA" and device_on:
            is_highlighted = True; alpha = 255 

        if entity.is_hiding and not is_highlighted:
            is_visible = False
            if getattr(entity, 'is_player', False) or entity.name == "Player": is_visible, alpha = True, 120
            elif role_name == "SPECTATOR": is_visible, alpha = True, 120
            if not is_visible: return

        cache_key = CharacterRenderer._get_cache_key(entity, is_highlighted)
        if cache_key in CharacterRenderer._sprite_cache:
            base_surf = CharacterRenderer._sprite_cache[cache_key]
        else:
            base_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            skin_idx = entity.custom.get('skin', 0) % len(CUSTOM_COLORS.get('SKIN', [(0,0,0)])) if CUSTOM_COLORS.get('SKIN') else 0
            cloth_idx = entity.custom.get('clothes', 0) % len(CUSTOM_COLORS.get('CLOTHES', [(0,0,0)])) if CUSTOM_COLORS.get('CLOTHES') else 0
            body_color = CUSTOM_COLORS.get('SKIN', [(255,255,255)])[skin_idx]
            clothes_color = CUSTOM_COLORS.get('CLOTHES', [(255,255,255)])[cloth_idx]
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
        if role_name == "POLICE" and entity.role in ["POLICE", "SPECTATOR"]: name_color = (100, 180, 255)
        elif role_name == "MAFIA" and entity.role in ["MAFIA", "SPECTATOR"]: name_color = (255, 100, 100)
        text_cache_key = (entity.uid, entity.name, name_color, entity.z_level) 
        if text_cache_key in CharacterRenderer._name_surface_cache: name_surf = CharacterRenderer._name_surface_cache[text_cache_key]
        else: name_surf = CharacterRenderer.NAME_FONT.render(entity.name, True, name_color); CharacterRenderer._name_surface_cache[text_cache_key] = name_surf
        screen.blit(name_surf, (draw_x + (TILE_SIZE // 2) - (name_surf.get_width() // 2), draw_y - 14))

class MapRenderer:
    def __init__(self, map_manager):
        self.map_manager = map_manager
        self.map_width = map_manager.width
        self.map_height = map_manager.height
        
        # [Debug] 텍스처 로딩 실패 시 사용할 핑크색 텍스처
        self.error_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.error_surf.fill((255, 0, 255)) # Magenta
        pygame.draw.rect(self.error_surf, (0, 0, 0), (0, 0, TILE_SIZE, TILE_SIZE), 1)

    def draw(self, screen, camera, dt, entities, player_z_level=0, visible_tiles=None, tile_alphas=None, viewer_role="CITIZEN", current_phase="DAY", viewer_device_on=False):
        if tile_alphas is None: tile_alphas = {}

        # 렌더링 범위 계산 (Y축이 압축되었으므로 더 많은 행을 그려야 함)
        start_col = int(camera.x // TILE_SIZE) - 2
        end_col = int((camera.x + camera.width / camera.zoom_level) // TILE_SIZE) + 4
        
        # Y축 역산: camera.y / TILE_STEP_Y
        start_row = int(camera.y // TILE_STEP_Y) - 6 
        end_row = int((camera.y + camera.height / camera.zoom_level) // TILE_STEP_Y) + 12

        entities_by_row = {}
        for ent in entities:
            if not ent.alive: continue
            # Y축 압축을 고려한 정렬 기준 Y 좌표 계산
            r = int(ent.rect.bottom // TILE_SIZE) # 기존 rect.bottom은 TILE_SIZE 기준이므로 그대로 사용
            if r not in entities_by_row: entities_by_row[r] = []
            entities_by_row[r].append(ent)

        # --- Y축 루프 --- (압축된 행 기준)
        for r in range(start_row, end_row):
            # Z축 루프
            for z in range(len(self.map_manager.layers)):
                
                # 지붕 가림 처리
                draw_alpha = 255
                if z > player_z_level:
                    draw_alpha = 40 # 플레이어 위층은 반투명
                
                if draw_alpha < 10: continue # 너무 투명하면 건너뜀

                # X축 루프
                for c in range(start_col, end_col):
                    if not (0 <= c < self.map_manager.width and 0 <= r < self.map_manager.height): continue

                    # [핵심] Y좌표 압축 (Foreshortening)
                    # TILE_SIZE(32) 대신 TILE_STEP_Y(24)를 곱해서 그립니다.
                    # 이렇게 하면 뒷줄(r)과 앞줄(r+1)이 8px만큼 겹치게 됩니다.
                    
                    base_x = c * TILE_SIZE - camera.x
                    base_y = r * TILE_STEP_Y - camera.y - (z * BLOCK_HEIGHT)

                    # 각 레이어 순회 (Floor -> Wall -> Object)
                    for layer in ['floor', 'wall', 'object']:
                        val = self.map_manager.get_tile_full(c, r, z, layer)
                        tid = val[0]
                        if tid == 0: continue
                        
                        img = get_texture(tid, val[1])
                        if not img: img = self.error_surf
                        
                        # 렌더링 좌표 설정
                        draw_x = base_x
                        draw_y = base_y
                        
                        # 벽/오브젝트는 위로 솟구치게 (Standing)
                        if layer != 'floor':
                            draw_y -= BLOCK_HEIGHT

                        # 알파값 적용 및 렌더링
                        if draw_alpha < 255:
                            temp_img = img.copy()
                            temp_img.set_alpha(draw_alpha)
                            screen.blit(temp_img, (draw_x, draw_y))
                        else:
                            screen.blit(img, (draw_x, draw_y))

            # 엔티티 그리기 (해당 줄)
            # 엔티티는 자기 자체의 Y좌표 (rect.bottom)를 기준으로 정렬되므로, 
            # 렌더링 시에는 압축된 Y좌표 (base_y)를 사용해야 합니다.
            if r in entities_by_row:
                # 같은 줄 내에서도 Y좌표 기준으로 정렬 (Y-Sorting)
                sorted_entities = sorted(entities_by_row[r], key=lambda e: e.rect.bottom - (e.z_level * BLOCK_HEIGHT))
                for ent in sorted_entities:
                    ent_z = getattr(ent, 'z_level', 0)
                    z_offset = ent_z * BLOCK_HEIGHT
                    
                    # CharacterRenderer.draw_entity 내부에서 Y축 압축을 수행하므로
                    # 여기서는 그냥 Z오프셋만 넘겨주면 됩니다.
                    CharacterRenderer.draw_entity(screen, ent, camera.x, camera.y + z_offset, ent.role, phase, device_on)