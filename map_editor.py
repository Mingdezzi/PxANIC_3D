import pygame
import sys
import os
import math
# settings의 SCREEN_WIDTH/HEIGHT는 게임용이므로 무시하고 동적으로 처리합니다.
from settings import TILE_SIZE, BLOCK_HEIGHT
from world.map_manager import MapManager
from world.tiles import get_texture, TILE_DATA

# --- 색상 상수 ---
C_BG = (30, 32, 36)
C_GRID = (255, 255, 255, 40)
C_UI_BG = (45, 48, 55)
C_UI_BORDER = (80, 80, 90)
C_TEXT = (220, 220, 220)
C_HIGHLIGHT = (255, 200, 0)
C_ACTIVE_TAB = (70, 130, 180)

class MapEditor:
    def __init__(self):
        pygame.init()
        
        # [수정 1] 모니터 해상도 기반 안전한 초기 크기 설정
        info = pygame.display.Info()
        monitor_w, monitor_h = info.current_w, info.current_h
        
        # 모니터의 85% 크기로 설정 (단, 최소 1024x768 보장)
        initial_w = max(1024, int(monitor_w * 0.85))
        initial_h = max(768, int(monitor_h * 0.85))
        
        self.screen = pygame.display.set_mode((initial_w, initial_h), pygame.RESIZABLE)
        pygame.display.set_caption("PxANIC! 2.5D Builder")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("malgungothic", 14) 
        self.title_font = pygame.font.SysFont("malgungothic", 20, bold=True)
        
        # 맵 시스템
        self.map_manager = MapManager()
        self.load_map_safe()
        
        # 카메라 & 뷰
        self.camera_x = -100
        self.camera_y = -100
        self.zoom = 1.0
        
        # 편집 상태
        self.current_z = 0
        self.current_layer = 'floor' 
        self.selected_tid = 1110000 
        self.rotation = 0
        
        self.show_grid = True
        self.is_dragging = False
        self.drag_button = 0 
        
        # UI 레이아웃
        self.ui_width = 320
        self.palette_scroll = 0
        self.tiles_per_row = 7
        self.tile_btn_size = 40
        self.tile_btn_margin = 5
        
        # 타일 데이터 분류
        self.categorized_tiles = {'floor': [], 'wall': [], 'object': []}
        self._categorize_tiles()

        # UI 버튼 리스트 (매 프레임 갱신)
        self.ui_tile_buttons = []
        self.ui_tab_buttons = []

    def load_map_safe(self):
        if os.path.exists("map.json"):
            try:
                self.map_manager.load_map("map.json")
                print("Map loaded successfully.")
            except Exception as e:
                print(f"Failed to load map: {e}")
                self.map_manager.create_default_map()
        else:
            self.map_manager.create_default_map()

    def _categorize_tiles(self):
        for tid, data in TILE_DATA.items():
            if 'img' not in data and not get_texture(tid): continue
            
            if 1000000 <= tid < 3000000:
                self.categorized_tiles['floor'].append(tid)
            elif 3000000 <= tid < 5000000:
                self.categorized_tiles['wall'].append(tid)
            else:
                self.categorized_tiles['object'].append(tid)
                
        for k in self.categorized_tiles:
            self.categorized_tiles[k].sort()

    def run(self):
        while True:
            dt = self.clock.tick(60)
            self.handle_events()
            self.update_camera()
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        keys = pygame.key.get_pressed()
        ctrl = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        
        # [수정 2] 현재 창 크기 가져오기
        screen_w, screen_h = self.screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_map()
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.VIDEORESIZE:
                # 창 크기 변경 시 display 다시 설정
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # --- 마우스 입력 ---
            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                # UI 영역 판정 (현재 화면 너비 기준)
                if mx > screen_w - self.ui_width:
                    self.palette_scroll = max(0, self.palette_scroll - event.y * 30)
                else:
                    if ctrl:
                        self.change_layer(event.y)
                    else:
                        self.zoom = max(0.5, min(3.0, self.zoom + event.y * 0.1))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                
                # UI 영역 클릭
                if mx > screen_w - self.ui_width:
                    self.handle_ui_click(mx, my)
                # 맵 영역 클릭
                else:
                    if event.button == 1: 
                        self.place_tile(mx, my)
                        self.is_dragging = True
                        self.drag_button = 1
                    elif event.button == 3: 
                        self.remove_tile(mx, my)
                        self.is_dragging = True
                        self.drag_button = 3
                    elif event.button == 2:
                        self.pick_tile(mx, my)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.is_dragging = False

            # --- 키보드 입력 ---
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and ctrl: self.save_map()
                elif event.key == pygame.K_g: self.show_grid = not self.show_grid
                elif event.key == pygame.K_r: self.rotation = (self.rotation + 90) % 360
                elif event.key == pygame.K_PAGEUP: self.change_layer(1)
                elif event.key == pygame.K_PAGEDOWN: self.change_layer(-1)
                elif event.key == pygame.K_1: self.set_mode('floor')
                elif event.key == pygame.K_2: self.set_mode('wall')
                elif event.key == pygame.K_3: self.set_mode('object')
                elif event.key == pygame.K_TAB:
                    modes = ['floor', 'wall', 'object']
                    idx = (modes.index(self.current_layer) + 1) % 3
                    self.set_mode(modes[idx])
                elif event.key == pygame.K_s and not ctrl:
                    mx, my = pygame.mouse.get_pos()
                    self.pick_tile(mx, my)

        # 드래그 처리
        if self.is_dragging:
            mx, my = pygame.mouse.get_pos()
            # UI 영역 밖에서만 작동
            if mx < screen_w - self.ui_width:
                if self.drag_button == 1: self.place_tile(mx, my)
                elif self.drag_button == 3: self.remove_tile(mx, my)

    def update_camera(self):
        keys = pygame.key.get_pressed()
        speed = 15 / self.zoom
        if keys[pygame.K_LSHIFT]: speed *= 2
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.camera_x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.camera_x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.camera_y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s] and not (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]): self.camera_y += speed

    # --- 기능 메서드 ---
    def set_mode(self, mode):
        self.current_layer = mode
        self.palette_scroll = 0
        tiles = self.categorized_tiles.get(mode, [])
        if tiles: self.selected_tid = tiles[0]

    def change_layer(self, delta):
        self.current_z += int(delta)
        if self.current_z < 0: self.current_z = 0

    def screen_to_world(self, sx, sy):
        wx = (sx / self.zoom) + self.camera_x
        wy = (sy / self.zoom) + self.camera_y + (self.current_z * BLOCK_HEIGHT)
        return int(wx // TILE_SIZE), int(wy // TILE_SIZE)

    def place_tile(self, mx, my):
        gx, gy = self.screen_to_world(mx, my)
        self.map_manager.set_tile(gx, gy, self.selected_tid, z=self.current_z, rotation=self.rotation, layer=self.current_layer)

    def remove_tile(self, mx, my):
        gx, gy = self.screen_to_world(mx, my)
        self.map_manager.set_tile(gx, gy, 0, z=self.current_z, layer=self.current_layer)

    def pick_tile(self, mx, my):
        gx, gy = self.screen_to_world(mx, my)
        val = self.map_manager.get_tile_full(gx, gy, self.current_z, self.current_layer)
        if val[0] != 0:
            self.selected_tid = val[0]
            self.rotation = val[1]
            print(f"Picked Tile: {self.selected_tid}")

    def save_map(self):
        self.map_manager.save_map("map.json")
        print("Map saved!")

    # --- UI 처리 ---
    def handle_ui_click(self, mx, my):
        # 저장된 버튼 충돌 체크
        for rect, tid in self.ui_tile_buttons:
            if rect.collidepoint(mx, my):
                self.selected_tid = tid
                return
        
        for rect, mode in self.ui_tab_buttons:
            if rect.collidepoint(mx, my):
                self.set_mode(mode)
                return

    def draw(self):
        self.screen.fill(C_BG)
        screen_w, screen_h = self.screen.get_size()
        
        # --- 1. Map Rendering (2.5D) ---
        vw = (screen_w - self.ui_width) / self.zoom
        vh = screen_h / self.zoom
        
        start_col = int(self.camera_x // TILE_SIZE) - 2
        start_row = int(self.camera_y // TILE_SIZE) - 6
        end_col = start_col + int(vw // TILE_SIZE) + 4
        end_row = start_row + int(vh // TILE_SIZE) + 12

        for z in range(self.current_z + 1):
            if z >= len(self.map_manager.layers): break
            is_active = (z == self.current_z)
            alpha = 255 if is_active else 80 
            
            for layer in ['floor', 'wall', 'object']:
                for r in range(start_row, end_row):
                    for c in range(start_col, end_col):
                        draw_x = (c * TILE_SIZE - self.camera_x) * self.zoom
                        draw_y = (r * TILE_SIZE - self.camera_y - (z * BLOCK_HEIGHT)) * self.zoom
                        
                        if draw_x < -TILE_SIZE*3 or draw_x > screen_w - self.ui_width: continue
                        if draw_y < -TILE_SIZE*3 or draw_y > screen_h: continue
                        
                        val = self.map_manager.get_tile_full(c, r, z, layer)
                        tid = val[0]
                        if tid == 0: continue
                        
                        img = get_texture(tid, val[1])
                        if not img: continue
                        
                        final_img = img
                        if self.zoom != 1.0:
                            w, h = img.get_size()
                            final_img = pygame.transform.scale(img, (int(w*self.zoom), int(h*self.zoom)))
                        
                        if not is_active: final_img.set_alpha(alpha)
                        self.screen.blit(final_img, (draw_x, draw_y))
                        if not is_active: final_img.set_alpha(255)

        # --- 2. Grid & Cursor ---
        if self.show_grid:
            mx, my = pygame.mouse.get_pos()
            if mx < screen_w - self.ui_width:
                gx, gy = self.screen_to_world(mx, my)
                cx = (gx * TILE_SIZE - self.camera_x) * self.zoom
                cy = (gy * TILE_SIZE - self.camera_y - (self.current_z * BLOCK_HEIGHT)) * self.zoom
                sz = TILE_SIZE * self.zoom
                
                pygame.draw.rect(self.screen, (255, 0, 0), (cx, cy, sz, sz), 2)
                coord_txt = self.font.render(f"{gx},{gy} (Z:{self.current_z})", True, (255, 255, 255))
                self.screen.blit(coord_txt, (cx + 10, cy - 20))

        # --- 3. UI Panel ---
        self.draw_ui()

    def draw_ui(self):
        screen_w, screen_h = self.screen.get_size()
        ui_x = screen_w - self.ui_width
        
        pygame.draw.rect(self.screen, C_UI_BG, (ui_x, 0, self.ui_width, screen_h))
        pygame.draw.line(self.screen, C_UI_BORDER, (ui_x, 0), (ui_x, screen_h), 2)
        
        self.ui_tile_buttons = []
        self.ui_tab_buttons = []
        
        curr_y = 10
        infos = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Layer(Z): {self.current_z}  [PgUp/Dn]",
            f"Zoom: {self.zoom:.1f}",
        ]
        for line in infos:
            t = self.font.render(line, True, C_TEXT)
            self.screen.blit(t, (ui_x + 10, curr_y))
            curr_y += 20
            
        curr_y += 10
        modes = [('floor', '1.바닥'), ('wall', '2.벽'), ('object', '3.물체')]
        tab_w = (self.ui_width - 20) // 3
        
        for i, (mode, label) in enumerate(modes):
            bx = ui_x + 10 + i * tab_w
            by = curr_y
            rect = pygame.Rect(bx, by, tab_w - 2, 30)
            col = C_ACTIVE_TAB if self.current_layer == mode else C_UI_BORDER
            pygame.draw.rect(self.screen, col, rect, 0, 5)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 1, 5)
            txt = self.font.render(label, True, (255, 255, 255))
            tx = bx + (tab_w - txt.get_width()) // 2
            ty = by + (30 - txt.get_height()) // 2
            self.screen.blit(txt, (tx, ty))
            self.ui_tab_buttons.append((rect, mode))
            
        curr_y += 40
        prev_rect = pygame.Rect(ui_x + 10, curr_y, 64, 64)
        pygame.draw.rect(self.screen, (0, 0, 0), prev_rect)
        pygame.draw.rect(self.screen, C_TEXT, prev_rect, 2)
        prev_img = get_texture(self.selected_tid, self.rotation)
        if prev_img:
            scaled = pygame.transform.scale(prev_img, (64, 64))
            self.screen.blit(scaled, prev_rect)
            
        t_info = f"ID: {self.selected_tid}"
        if self.selected_tid in TILE_DATA:
            t_name = TILE_DATA[self.selected_tid].get('name', 'Unknown')
            t_info += f"\n{t_name}"
        lines = t_info.split('\n')
        for i, ln in enumerate(lines):
            t = self.font.render(ln, True, C_HIGHLIGHT)
            self.screen.blit(t, (ui_x + 85, curr_y + i*20))
            
        curr_y += 80
        pygame.draw.line(self.screen, C_UI_BORDER, (ui_x, curr_y), (screen_w, curr_y), 2)
        curr_y += 10
        
        tiles = self.categorized_tiles.get(self.current_layer, [])
        clip_rect = pygame.Rect(ui_x, curr_y, self.ui_width, screen_h - curr_y)
        self.screen.set_clip(clip_rect)
        start_y = curr_y - self.palette_scroll
        btn_sz = self.tile_btn_size
        gap = self.tile_btn_margin
        
        col_cnt = 0
        row_cnt = 0
        
        for tid in tiles:
            img = get_texture(tid)
            if not img: continue
            bx = ui_x + 15 + col_cnt * (btn_sz + gap)
            by = start_y + row_cnt * (btn_sz + gap)
            
            if by + btn_sz > curr_y:
                rect = pygame.Rect(bx, by, btn_sz, btn_sz)
                pygame.draw.rect(self.screen, (60, 60, 70), rect)
                scaled = pygame.transform.scale(img, (btn_sz-4, btn_sz-4))
                self.screen.blit(scaled, (bx+2, by+2))
                if tid == self.selected_tid:
                    pygame.draw.rect(self.screen, C_HIGHLIGHT, rect, 2)
                self.ui_tile_buttons.append((rect, tid))
            
            col_cnt += 1
            if col_cnt >= self.tiles_per_row:
                col_cnt = 0
                row_cnt += 1
                
        self.screen.set_clip(None)

if __name__ == "__main__":
    MapEditor().run()