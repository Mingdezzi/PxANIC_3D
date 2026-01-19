import pygame
import sys
import json
import os
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BLOCK_HEIGHT, ZONES
from world.map_manager import MapManager
from world.tiles import get_texture, TILE_DATA, get_tile_category

# 고정 설정
UI_WIDTH = 280

class MapEditor:
    def __init__(self):
        pygame.init()
        # 창 조절 가능하도록 설정
        self.screen = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)
        pygame.display.set_caption("PxANIC! 2.5D Map Editor Pro")
        self.clock = pygame.time.Clock()
        
        # [상태 관리]
        self.state = "START_MENU" # START_MENU, NEW_MAP_CONFIG, EDITOR
        self.map_manager = MapManager()
        
        # [에디터 상태]
        self.camera_x, self.camera_y = 0, 0
        self.zoom = 1.0
        self.current_z = 0
        self.selected_tid = 1110000
        self.selected_layer = 'floor'
        self.selected_zone = 1
        self.rotation = 0
        self.mode = 'TILE' # 'TILE' or 'ZONE'
        self.show_grid = True
        
        # [신규 맵 설정용]
        self.input_w = "50"
        self.input_h = "50"
        self.active_input = "W" # "W" or "H"
        
        # [드래그 도구]
        self.is_dragging = False
        self.drag_start_gx, self.drag_start_gy = 0, 0
        
        # [UI]
        self.font = pygame.font.SysFont("arial", 16)
        self.small_font = pygame.font.SysFont("arial", 13)
        self.palette_scroll = 0
        self.filter_category = "ALL"
        self.filtered_tiles = []
        self.filter_rects = {} 
        self.tile_rects = []
        self.zone_rects = {}
        self.btn_new = None
        self.btn_load = None
        self.update_palette()

    def update_palette(self):
        """카테고리에 맞춰 팔레트 타일 목록 갱신"""
        self.filtered_tiles = sorted([tid for tid in TILE_DATA.keys() if self._filter_check(tid)])

    def _filter_check(self, tid):
        cat = get_tile_category(tid)
        if self.filter_category == "ALL": return True
        if self.filter_category == "FLOOR": return cat in [1, 2]
        if self.filter_category == "WALL": return cat in [3, 4]
        if self.filter_category == "OBJ": return cat in [5, 6, 7, 8, 9]
        return False

    def run(self):
        while True:
            dt = self.clock.tick(60)
            self.handle_events()
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        sw, sh = self.screen.get_size()
        map_view_w = sw - UI_WIDTH

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # --- 상태별 이벤트 처리 ---
            if self.state == "START_MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hasattr(self, 'btn_new') and self.btn_new.collidepoint(event.pos): self.state = "NEW_MAP_CONFIG"
                    if hasattr(self, 'btn_load') and self.btn_load.collidepoint(event.pos): 
                        if self.map_manager.load_map("map.json"): self.state = "EDITOR"

            elif self.state == "NEW_MAP_CONFIG":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB: self.active_input = "H" if self.active_input == "W" else "W"
                    elif event.key == pygame.K_RETURN:
                        w, h = int(self.input_w or 50), int(self.input_h or 50)
                        self.map_manager.width, self.map_manager.height = w, h
                        self.map_manager.create_default_map()
                        self.state = "EDITOR"
                        self.update_palette() # 맵 크기 변경 후 팔레트 갱신
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_input == "W": self.input_w = self.input_w[:-1]
                        else: self.input_h = self.input_h[:-1]
                    elif event.unicode.isdigit():
                        if self.active_input == "W": self.input_w += event.unicode
                        else: self.input_h += event.unicode

            elif self.state == "EDITOR":
                gx, gy = self.get_mouse_world_pos()
                if event.type == pygame.MOUSEWHEEL:
                    if mx < map_view_w: # 맵 영역: 줌
                        old_zoom = self.zoom
                        self.zoom = max(0.2, min(3.0, self.zoom + event.y * 0.1))
                        # 줌인/아웃 시 카메라 위치 보정 (마우스 위치 기준)
                        if old_zoom != self.zoom:
                            world_mx = (mx + self.camera_x) / old_zoom
                            world_my = (my + self.camera_y) / old_zoom
                            self.camera_x = (world_mx * self.zoom) - mx
                            self.camera_y = (world_my * self.zoom) - my

                    else: # UI 영역: 팔레트 스크롤
                        self.palette_scroll = max(0, self.palette_scroll - event.y * 2)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if mx > map_view_w: self.handle_ui_click(mx, my)
                    elif gx is not None:
                        if event.button in [1, 3]:
                            self.is_dragging = True
                            self.drag_start_gx, self.drag_start_gy = gx, gy
                        elif event.button == 2: self.pick_at(gx, gy)

                if event.type == pygame.MOUSEBUTTONUP:
                    if self.is_dragging:
                        self.apply_drag_tool(gx, gy, event.button == 3)
                        self.is_dragging = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB: 
                        self.mode = 'ZONE' if self.mode == 'TILE' else 'TILE'
                        self.update_palette() # 모드 변경 시 팔레트 갱신
                    elif event.key == pygame.K_PAGEUP: self.current_z += 1
                    elif event.key == pygame.K_PAGEDOWN: self.current_z = max(0, self.current_z - 1)
                    elif event.key == pygame.K_r: self.rotation = (self.rotation + 90) % 360
                    elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL): 
                        self.map_manager.save_map(); print("Saved!")
            
        # 카메라 이동 (Editor 전용)
        if self.state == "EDITOR":
            keys = pygame.key.get_pressed()
            speed = 15 / self.zoom
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.camera_x -= speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.camera_x += speed
            if keys[pygame.K_UP] or keys[pygame.K_w]: self.camera_y -= speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.camera_y += speed

    def get_mouse_world_pos(self):
        mx, my = pygame.mouse.get_pos()
        sw, sh = self.screen.get_size()
        if mx > sw - UI_WIDTH: return None, None
        world_x = (mx + self.camera_x) / self.zoom
        world_y = (my + self.camera_y) / self.zoom + (self.current_z * BLOCK_HEIGHT)
        return int(world_x // TILE_SIZE), int(world_y // TILE_SIZE)

    def draw(self):
        sw, sh = self.screen.get_size()
        self.screen.fill((30, 33, 40))

        if self.state == "START_MENU":
            self.draw_start_menu(sw, sh)
        elif self.state == "NEW_MAP_CONFIG":
            self.draw_new_config(sw, sh)
        elif self.state == "EDITOR":
            self.draw_editor_map(sw, sh) # 맵만 그리는 함수로 변경
            self.draw_ui_panel(sw, sh) # UI 패널 그리기
            self.draw_minimap(sw, sh) # 미니맵 그리기

    def draw_start_menu(self, sw, sh):
        title = self.font.render("PxANIC! 2.5D ENGINE", True, (255, 255, 255))
        self.screen.blit(title, (sw//2 - title.get_width()//2, sh//2 - 100))
        
        self.btn_new = pygame.Rect(sw//2 - 100, sh//2 - 30, 200, 40)
        self.btn_load = pygame.Rect(sw//2 - 100, sh//2 + 30, 200, 40)
        
        pygame.draw.rect(self.screen, (60, 60, 80), self.btn_new)
        pygame.draw.rect(self.screen, (60, 60, 80), self.btn_load)
        
        self.screen.blit(self.font.render("NEW MAP", True, (255, 255, 255)), (sw//2 - 35, sh//2 - 20))
        self.screen.blit(self.font.render("LOAD EXISTING", True, (255, 255, 255)), (sw//2 - 55, sh//2 + 40))

    def draw_new_config(self, sw, sh):
        # 맵 크기 입력 UI
        y_offset = sh//2 - 50
        
        txt_w = self.font.render(f"Width: {self.input_w}", True, (255,255,255))
        txt_h = self.font.render(f"Height: {self.input_h}", True, (255,255,255))
        
        self.screen.blit(txt_w, (sw//2 - txt_w.get_width()//2, y_offset))
        y_offset += 40
        self.screen.blit(txt_h, (sw//2 - txt_h.get_width()//2, y_offset))

        # 입력 필드 하이라이트
        if self.active_input == "W":
            pygame.draw.rect(self.screen, (255, 255, 0), (sw//2 - txt_w.get_width()//2 - 5, sh//2 - 50 - 5, txt_w.get_width() + 10, txt_w.get_height() + 10), 2)
        else:
            pygame.draw.rect(self.screen, (255, 255, 0), (sw//2 - txt_h.get_width()//2 - 5, sh//2 - 10 - 5, txt_h.get_width() + 10, txt_h.get_height() + 10), 2)

        info = self.small_font.render("Press ENTER to Start, TAB to switch", True, (150, 150, 150))
        self.screen.blit(info, (sw//2 - info.get_width()//2, sh//2 + 60))

    def draw_editor_map(self, sw, sh):
        map_view_w = sw - UI_WIDTH
        
        for z in range(self.current_z + 1): # 현재 층까지만 그림
            if z >= len(self.map_manager.layers): continue
            is_current = (z == self.current_z)
            
            for layer_name in ['floor', 'wall', 'object']:
                grid = self.map_manager.layers[z][layer_name]
                
                for r in range(self.map_manager.height):
                    for c in range(self.map_manager.width):
                        draw_x = c * TILE_SIZE * self.zoom - self.camera_x
                        draw_y = r * TILE_SIZE * self.zoom - self.camera_y - (z * BLOCK_HEIGHT * self.zoom)

                        # 화면 밖에 있는 타일은 그리지 않음
                        if not (-TILE_SIZE * self.zoom < draw_x < map_view_w and \
                                -TILE_SIZE * self.zoom < draw_y < sh): continue

                        tid, rot = grid[r][c]
                        if tid != 0:
                            img = get_texture(tid, rot)
                            img_s = pygame.transform.scale(img, (int(TILE_SIZE * self.zoom)+1, int(TILE_SIZE * self.zoom)+1))
                            if not is_current: # 현재 층이 아니면 흐릿하게
                                img_s.fill((80, 80, 80), special_flags=pygame.BLEND_RGB_MULT)
                                img_s.set_alpha(150)
                            self.screen.blit(img_s, (draw_x, draw_y))

                        # 구역 표시 (Z=0에서만, 그리고 ZONE 모드일 때만)
                        if self.mode == 'ZONE' and z == 0 and \
                           0 <= r < len(self.map_manager.zone_map) and \
                           0 <= c < len(self.map_manager.zone_map[r]):
                            zid = self.map_manager.zone_map[r][c]
                            if zid != 0 and zid in ZONES:
                                s = pygame.Surface((int(TILE_SIZE * self.zoom), int(TILE_SIZE * self.zoom)), pygame.SRCALPHA)
                                s.fill(ZONES[zid]['color'])
                                self.screen.blit(s, (draw_x, draw_y))
        
        # 드래그 프리뷰 (현재 층에만 표시)
        if self.is_dragging:
            mx, my = pygame.mouse.get_pos()
            end_gx, end_gy = self.get_mouse_world_pos()
            if end_gx is not None:
                x1, x2 = min(self.drag_start_gx, end_gx), max(self.drag_start_gx, end_gx)
                y1, y2 = min(self.drag_start_gy, end_gy), max(self.drag_start_gy, end_gy)
                for r in range(y1, y2 + 1):
                    for c in range(x1, x2 + 1):
                        pdx = c * TILE_SIZE * self.zoom - self.camera_x
                        pdy = r * TILE_SIZE * self.zoom - self.camera_y - (self.current_z * BLOCK_HEIGHT * self.zoom)
                        pygame.draw.rect(self.screen, (255, 255, 0), (pdx, pdy, TILE_SIZE * self.zoom, TILE_SIZE * self.zoom), 2)

        # 그리드 (현재 층에만 표시)
        if self.show_grid:
            grid_color = (200, 200, 200, 100)
            for x in range(self.map_manager.width + 1):
                sx = x * TILE_SIZE * self.zoom - self.camera_x
                pygame.draw.line(self.screen, grid_color, (sx, 0), (sx, sh))
            for y in range(self.map_manager.height + 1):
                sy = y * TILE_SIZE * self.zoom - self.camera_y - (self.current_z * BLOCK_HEIGHT * self.zoom)
                pygame.draw.line(self.screen, grid_color, (0, sy), (map_view_w, sy))

        # 마우스 커서 하이라이트
        gx, gy = self.get_mouse_world_pos()
        if gx is not None:
            cursor_draw_x = gx * TILE_SIZE * self.zoom - self.camera_x
            cursor_draw_y = gy * TILE_SIZE * self.zoom - self.camera_y - (self.current_z * BLOCK_HEIGHT * self.zoom)
            pygame.draw.rect(self.screen, (0, 255, 255), (cursor_draw_x, cursor_draw_y, TILE_SIZE * self.zoom, TILE_SIZE * self.zoom), 2)

    def draw_ui_panel(self, sw, sh):
        ui_x = sw - UI_WIDTH
        pygame.draw.rect(self.screen, (40, 44, 52), (ui_x, 0, UI_WIDTH, sh))
        pygame.draw.line(self.screen, (100, 100, 100), (ui_x, 0), (ui_x, sh), 2)
        
        y = 10
        texts = [
            f"MODE: {self.mode}", 
            f"LAYER (Z): {self.current_z}",
            f"ZOOM: {self.zoom:.1f}x",
            f"ROTATION: {self.rotation}"
        ]
        for t in texts:
            self.screen.blit(self.font.render(t, True, (255, 255, 255)), (ui_x + 10, y))
            y += 20
        y += 10 # 구분선

        # 카테고리 필터 버튼
        filter_button_y = y
        categories = [("ALL", "ALL"), ("FLOOR", "FLOOR"), ("WALL", "WALL"), ("OBJ", "OBJ")]
        self.filter_rects = {}
        for i, (btn_text, cat_filter) in enumerate(categories):
            rect = pygame.Rect(ui_x + 10 + i * 65, filter_button_y, 60, 25)
            col = (100, 100, 255) if self.filter_category == cat_filter else (60, 60, 70)
            pygame.draw.rect(self.screen, col, rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)
            self.screen.blit(self.small_font.render(btn_text, True, (255, 255, 255)), (rect.x + (rect.width - self.small_font.render(btn_text, True, (255,255,255)).get_width()) // 2, rect.y + 5))
            self.filter_rects[cat_filter] = rect
        y = filter_button_y + 40
        
        # 선택된 타일 미리보기 및 정보
        y += 10
        self.screen.blit(self.font.render(f"Selected Tile:", True, (255,255,255)), (ui_x + 10, y))
        y += 25
        if self.selected_tid != 0: # 유효한 타일일 경우
            preview_img = get_texture(self.selected_tid, self.rotation)
            preview_img_s = pygame.transform.scale(preview_img, (TILE_SIZE, TILE_SIZE))
            self.screen.blit(preview_img_s, (ui_x + 15, y))
            
            self.screen.blit(self.small_font.render(f"ID: {self.selected_tid}", True, (200,200,200)), (ui_x + 60, y + 5))
            self.screen.blit(self.small_font.render(f"Name: {TILE_DATA[self.selected_tid]['name']}", True, (200,200,200)), (ui_x + 60, y + 25))
        y += TILE_SIZE + 20

        # 타일 팔레트 목록
        self.tile_rects = []
        start_display_index = int(self.palette_scroll)
        max_display_count = (sh - y - 150) // 25 # 미니맵 공간 고려

        for i in range(max_display_count):
            idx = start_display_index + i
            if idx >= len(self.filtered_tiles): break
            
            tid = self.filtered_tiles[idx]
            rect = pygame.Rect(ui_x + 10, y + i * 25, UI_WIDTH - 20, 22)
            col = (80, 80, 100) if self.selected_tid == tid else (50, 54, 62)
            pygame.draw.rect(self.screen, col, rect)
            self.screen.blit(self.small_font.render(f"{tid}: {TILE_DATA[tid]['name']}", True, (200, 200, 200)), (rect.x + 5, rect.y + 3))
            self.tile_rects.append((tid, rect))
        
        # ZONE 모드일 경우 구역 목록 표시
        if self.mode == 'ZONE':
            zone_list_y = y + max_display_count * 25 + 10
            self.screen.blit(self.font.render("Zones:", True, (255,255,255)), (ui_x + 10, zone_list_y))
            self.zone_rects = {}
            for zid, zone_info in ZONES.items():
                if zid == 0: continue # None zone 제외
                rect = pygame.Rect(ui_x + 10, zone_list_y + zid * 25, UI_WIDTH - 20, 22)
                col = (100, 100, 255) if self.selected_zone == zid else (60, 60, 70)
                pygame.draw.rect(self.screen, col, rect)
                pygame.draw.rect(self.screen, zone_info['color'][:3], (rect.x + 5, rect.y + 5, 12, 12)); # 색상 박스
                self.screen.blit(self.small_font.render(zone_info['name'], True, (255,255,255)), (rect.x + 25, rect.y + 3))
                self.zone_rects[zid] = rect
            
    def draw_minimap(self, sw, sh):
        mm_size = 180
        rect = pygame.Rect(sw - UI_WIDTH + (UI_WIDTH - mm_size)//2, sh - mm_size - 20, mm_size, mm_size)
        pygame.draw.rect(self.screen, (0, 0, 0), rect)
        pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)
        
        # 맵 비율에 맞춰 점 찍기
        mw, mh = self.map_manager.width, self.map_manager.height
        if mw == 0 or mh == 0: return
        
        for r in range(0, mh, 2): # 큰 맵일 경우 스킵해서 그리기
            for c in range(0, mw, 2):
                tid = self.map_manager.get_tile(c, r, 0, 'floor') # 1층 바닥만 표시
                if tid != 0 and tid in TILE_DATA:
                    px = rect.x + (c / mw) * mm_size
                    py = rect.y + (r / mh) * mm_size
                    pygame.draw.rect(self.screen, TILE_DATA[tid]['color'][:3], (px, py, max(1, int(2 * mm_size / mw)), max(1, int(2 * mm_size / mh)))) # 픽셀 단위 조정
        
        # 현재 카메라 뷰포트 표시 (Z-Level 반영)
        view_w_tiles = (sw - UI_WIDTH) / (TILE_SIZE * self.zoom)
        view_h_tiles = sh / (TILE_SIZE * self.zoom)
        
        # 카메라의 월드 좌표를 타일 좌표로 변환
        cam_tile_x = self.camera_x / (TILE_SIZE * self.zoom)
        cam_tile_y = (self.camera_y + (self.current_z * BLOCK_HEIGHT * self.zoom)) / (TILE_SIZE * self.zoom) 

        cam_rect_on_map = pygame.Rect(
            rect.x + (cam_tile_x / mw) * mm_size,
            rect.y + (cam_tile_y / mh) * mm_size,
            (view_w_tiles / mw) * mm_size,
            (view_h_tiles / mh) * mm_size
        )
        pygame.draw.rect(self.screen, (255, 255, 255), cam_rect_on_map, 1)

if __name__ == "__main__":
    MapEditor().run()