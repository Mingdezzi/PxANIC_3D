import pygame
import json
import os

from engine.core.node import Node
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT
from engine.graphics.tile_node import TileNode
from engine.graphics.wall import WallNode
from engine.assets.tile_engine import TileEngine

# ==========================================
# 1. 내장 UI 시스템 (Simple GUI System)
# ==========================================
class UIElement:
    def handle_event(self, event): pass
    def draw(self, screen): pass

class UIButton(UIElement):
    def __init__(self, rect, text, callback, data=None, color=(70, 70, 80)):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.data = data
        self.base_color = color
        self.hover_color = (min(255, color[0]+40), min(255, color[1]+40), min(255, color[2]+40))
        self.is_hovered = False

    def handle_event(self, event, offset_y=0):
        if event.type == pygame.MOUSEMOTION:
            adj_rect = self.rect.copy()
            adj_rect.y += offset_y
            self.is_hovered = adj_rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            adj_rect = self.rect.copy()
            adj_rect.y += offset_y
            if adj_rect.collidepoint(event.pos):
                if self.data is not None: self.callback(self.data)
                else: self.callback()
                return True
        return False

    def draw(self, screen, font, offset_y=0):
        draw_rect = self.rect.copy()
        draw_rect.y += offset_y
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, draw_rect, border_radius=4)
        pygame.draw.rect(screen, (30, 30, 30), draw_rect, 1, border_radius=4)
        
        txt = font.render(self.text, True, (220, 220, 220))
        txt_rect = txt.get_rect(center=draw_rect.center)
        screen.blit(txt, txt_rect)

class UIInput(UIElement):
    def __init__(self, rect, label, default_text=""):
        self.rect = rect
        self.label = label
        self.text = default_text
        self.active = False
        self.color_inactive = (50, 50, 60)
        self.color_active = (70, 70, 90)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.unicode.isdigit(): 
                self.text += event.unicode
            return True
        return False

    def draw(self, screen, font):
        lbl_surf = font.render(self.label, True, (200, 200, 200))
        screen.blit(lbl_surf, (self.rect.x, self.rect.y - 20))
        
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(screen, (100, 100, 200) if self.active else (30, 30, 30), self.rect, 2, border_radius=4)
        
        txt_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + 5))

# ==========================================
# 2. 에디터 씬 (Editor Scene)
# ==========================================
class EditorScene(Node):
    def __init__(self, name="EditorScene"):
        super().__init__(name)
        self.state = "LAUNCHER"
        
        # Engine Components
        self.camera = None
        self.font = None
        self.title_font = None
        
        # Map Data
        self.map_data = {}
        self.map_width = 30
        self.map_height = 30
        
        # [New] UI 영역 분리 설정
        self.ui_width = 220
        self.screen_width = 1280
        self.screen_height = 720
        self.map_view_rect = None # 맵이 보여질 실제 사각형 영역
        
        self.modes = ["FLOOR", "WALL", "OBJECT"]
        self.modes = ["FLOOR", "WALL", "OBJECT"]
        self.current_mode_idx = 0
        self.current_tile_id = 0
        self.wall_type = "NE"
        
        # Interaction State
        self.is_dragging = False
        self.drag_mode = 0 # 1:Left(Place), 3:Right(Delete)
        self.drag_start = (0, 0)
        self.drag_end = (0, 0)
        self.hover_grid = (0, 0)
        
        # Visuals
        self.ghost_node = None
        self.preview_nodes = [] 
        self.time_paused = False 
        self.time_reset_req = False
        self.time_display_btn = None
        
        # UI Lists
        self.launcher_buttons = []
        self.new_map_inputs = []
        self.new_map_buttons = []
        self.editor_buttons = []
        self.editor_scroll_y = 0
        self.editor_max_scroll = 0
        
        self.tile_data_list = []
        self._load_tile_data()

    def _load_tile_data(self):
        self.tile_data_list = []
        if hasattr(TileEngine, 'TILE_DATA'):
            for tid, data in TileEngine.TILE_DATA.items():
                self.tile_data_list.append({'id': tid, 'name': data.get('name', str(tid))})
        self.tile_data_list.sort(key=lambda x: x['id'])

    def _ready(self, services):
        print("Editor Scene Ready")
        renderer = services.get("renderer")
        if renderer:
            self.camera = renderer.camera
            self.screen_width, self.screen_height = renderer.screen.get_size()
            # [New] 초기 맵 뷰 영역 설정
            self.map_view_rect = pygame.Rect(0, 0, self.screen_width - self.ui_width, self.screen_height)
            # 카메라 뷰포트도 맵 영역에 맞춤
            self.camera.update_viewport(self.map_view_rect.width, self.map_view_rect.height)
            # 렌더러에 클리핑 영역 전달
            renderer.set_clip_rect(self.map_view_rect)
        
        # 폰트 로드 (한글 지원 시도)
        self.font = pygame.font.SysFont("malgungothic", 12)
        if not self.font: self.font = pygame.font.SysFont(None, 18)
        self.title_font = pygame.font.SysFont("malgungothic", 24)

        self._setup_launcher_ui()
        self._setup_new_map_ui()

    # --- UI Setup ---
    def _setup_launcher_ui(self):
        cx, cy = self.screen_width // 2, self.screen_height // 2
        self.launcher_buttons = [
            UIButton(pygame.Rect(cx - 100, cy - 30, 200, 40), "New Map", lambda: self._change_state("NEW_MAP")),
            UIButton(pygame.Rect(cx - 100, cy + 30, 200, 40), "Load Map", self._load_map_dialog)
        ]

    def _setup_new_map_ui(self):
        cx, cy = self.screen_width // 2, self.screen_height // 2
        self.new_map_inputs = [
            UIInput(pygame.Rect(cx - 100, cy - 40, 90, 30), "Width", "30"),
            UIInput(pygame.Rect(cx + 10, cy - 40, 90, 30), "Height", "30")
        ]
        self.new_map_buttons = [
            UIButton(pygame.Rect(cx - 100, cy + 20, 200, 40), "Create", self._create_new_map),
            UIButton(pygame.Rect(cx - 100, cy + 70, 200, 30), "Back", lambda: self._change_state("LAUNCHER"), color=(80, 50, 50))
        ]

    def _time_play(self): self.time_paused = False
    def _time_pause(self): self.time_paused = True
    def _time_stop(self): 
        self.time_paused = True
        # Request reset to day (handled in _update)
        self.time_reset_req = True

    def _refresh_editor_ui(self):
        self.editor_buttons = []
        ui_x = self.screen_width - self.ui_width
        start_y = 60
        btn_h = 30
        gap = 5
        
        # [New] Time Control Panel
        # Time Display
        self.time_display_btn = UIButton(pygame.Rect(ui_x + 10, start_y, self.ui_width - 20, btn_h), "Phase: --", lambda: None, color=(40, 40, 50))
        self.editor_buttons.append(self.time_display_btn)
        start_y += btn_h + gap
        
        # Controls Row
        w3 = (self.ui_width - 20 - gap*2) // 3
        b_play = UIButton(pygame.Rect(ui_x + 10, start_y, w3, btn_h), "▶", self._time_play, color=(50, 150, 50))
        b_pause = UIButton(pygame.Rect(ui_x + 10 + w3 + gap, start_y, w3, btn_h), "||", self._time_pause, color=(150, 150, 50))
        b_stop = UIButton(pygame.Rect(ui_x + 10 + (w3 + gap)*2, start_y, w3, btn_h), "■", self._time_stop, color=(150, 50, 50))
        
        self.editor_buttons.extend([b_play, b_pause, b_stop])
        start_y += btn_h + gap * 2

        current_mode = self.get_current_mode()
        
        # 타일 필터링
        filtered = []
        for item in self.tile_data_list:
            tid_s = str(item['id'])
            digit = tid_s[0] if tid_s else "0"
            if current_mode == "FLOOR" and digit == '1': filtered.append(item)
            elif current_mode == "WALL" and digit == '2': filtered.append(item)
            elif current_mode == "OBJECT" and digit == '3': filtered.append(item)

        # 버튼 생성
        for i, item in enumerate(filtered):
            rect = pygame.Rect(ui_x + 10, start_y + i * (btn_h + gap), self.ui_width - 20, btn_h)
            color = (80, 120, 80) if item['id'] == self.current_tile_id else (60, 60, 60)
            btn = UIButton(rect, item['name'], self._on_tile_select, item['id'], color)
            self.editor_buttons.append(btn)
            
        total_h = len(self.editor_buttons) * (btn_h + gap) + 100
        self.editor_max_scroll = min(0, -(total_h - self.screen_height))
        
        # 자동 선택
        if filtered and (self.current_tile_id not in [t['id'] for t in filtered]):
             self.current_tile_id = filtered[0]['id']
             self._on_tile_select(self.current_tile_id)

    def _change_state(self, new_state):
        self.state = new_state
        if self.state == "EDITOR":
            self._refresh_editor_ui()
            if self.camera:
                self.camera.update_viewport(self.screen_width - self.ui_width, self.screen_height)

    # --- Logic ---
    def _create_new_map(self):
        try: w, h = int(self.new_map_inputs[0].text), int(self.new_map_inputs[1].text)
        except: w, h = 30, 30
        self.map_width, self.map_height = w, h
        self.map_data = {}; self.children.clear()
        self._change_state("EDITOR")
        
        # 맵 중앙으로 카메라 이동
        cx, cy = IsoMath.cart_to_iso(w//2, h//2)
        self.camera.position.x, self.camera.position.y = cx, cy

    def _load_map_dialog(self):
        if os.path.exists("map_data.json"):
            self.load_map("map_data.json")
            self._change_state("EDITOR")
        else: print("No 'map_data.json' found.")

    def _on_tile_select(self, tile_id):
        self.current_tile_id = tile_id
        self._refresh_editor_ui()
        self._update_ghost()

    def _get_mouse_grid_pos(self, y_bias=0):
        mx, my = pygame.mouse.get_pos()
        my += y_bias # Apply offset
        if self.camera:
            wx, wy = self.camera.screen_to_world(mx, my)
            gx, gy = IsoMath.iso_to_cart(wx, wy)
            return int(gx), int(gy)
        return 0, 0

    def _update_ghost(self):
        # 1. Clear previous previews
        if self.ghost_node and self.ghost_node in self.children:
            self.children.remove(self.ghost_node)
        for p in self.preview_nodes:
            if p in self.children: self.children.remove(p)
        self.preview_nodes.clear()
        self.ghost_node = None

        if not self.is_dragging:
            # Single Ghost (Hover)
            mode = self.get_current_mode()
            if mode == "FLOOR":
                self.ghost_node = TileNode(self.current_tile_id, 0, 0, layer=0)
            elif mode == "WALL":
                self.ghost_node = WallNode(tile_id=self.current_tile_id, wall_type=self.wall_type, size_z=2.0)
            elif mode == "OBJECT":
                self.ghost_node = TileNode(self.current_tile_id, 0, 0, layer=1)
                
            if self.ghost_node:
                s = self.ghost_node.get_sprite()
                if s: s.set_alpha(150)
                self.add_child(self.ghost_node)
        
        else:
            # Drag Preview (Multiple Ghosts)
            x1, y1 = self.drag_start
            x2, y2 = self.drag_end # Updated in _update loop
            points = []
            
            mode = self.get_current_mode()
            is_delete = (self.drag_mode == 3)
            if is_delete: return # No preview for delete (red box is enough)

            if mode == "WALL":
                dx_raw = x2 - x1
                dy_raw = y2 - y1
                wall_t = "NE"
                if abs(dx_raw) >= abs(dy_raw): # Horizontal -> NE
                    wall_t = "NE"
                    y2 = y1; step = 1 if x2 >= x1 else -1
                    points = [(ix, y1, wall_t) for ix in range(x1, x2 + step, step)]
                else: # Vertical -> NW
                    wall_t = "NW"
                    x2 = x1; step = 1 if y2 >= y1 else -1
                    points = [(x1, iy, wall_t) for iy in range(y1, y2 + step, step)]
            else:
                rx1, rx2 = sorted([x1, x2])
                ry1, ry2 = sorted([y1, y2])
                for dy in range(ry1, ry2 + 1):
                    for dx in range(rx1, rx2 + 1):
                        points.append((dx, dy, None))
            
            # Create Nodes
            count = 0
            for px, py, wt in points:
                if count > 100: break # Safety limit
                node = None
                if mode == "FLOOR": node = TileNode(self.current_tile_id, px, py, layer=0)
                elif mode == "WALL": node = WallNode(tile_id=self.current_tile_id, wall_type=wt, size_z=2.0)
                elif mode == "OBJECT": node = TileNode(self.current_tile_id, px, py, layer=1)
                
                if node:
                    node.position.x, node.position.y = px, py
                    s = node.get_sprite()
                    if s: s.set_alpha(100) # More transparent
                    self.preview_nodes.append(node)
                    self.add_child(node)
                count += 1

    def _pick_node_at_mouse(self):
        """Find the top-most node under the mouse cursor, filtered by current mode."""
        mx, my = pygame.mouse.get_pos()
        picked = None
        max_depth = -999999
        
        mode = self.get_current_mode()
        
        for child in self.children:
            # Mode Filtering
            if mode == "FLOOR":
                if not (isinstance(child, TileNode) and child.layer == 0): continue
            elif mode == "WALL":
                if not isinstance(child, WallNode): continue
            elif mode == "OBJECT":
                if not (isinstance(child, TileNode) and child.layer == 1): continue
            else:
                continue

            # Simple Rect Collision based on Screen Position
            if not self.camera: continue
            
            gpos = child.get_global_position()
            ix, iy = IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z)
            sx, sy = self.camera.world_to_screen(ix, iy)
            
            # Sprite Rect
            sprite = child.get_sprite()
            if not sprite: continue
            
            zoom = self.camera.zoom
            w = int(sprite.get_width() * zoom)
            h = int(sprite.get_height() * zoom)
            
            # Pivot is midbottom
            offset_y = (TILE_HEIGHT) * zoom
            rect = sprite.get_rect(midbottom=(sx, sy + offset_y))
            
            if rect.collidepoint(mx, my):
                # Check pixel alpha for precise picking
                rel_x = int((mx - rect.x) / zoom)
                rel_y = int((my - rect.y) / zoom)
                
                try:
                    if 0 <= rel_x < sprite.get_width() and 0 <= rel_y < sprite.get_height():
                        if sprite.get_at((rel_x, rel_y)).a > 10:
                            # Depth check
                            depth = IsoMath.get_depth(gpos.x, gpos.y, gpos.z)
                            if hasattr(child, 'layer'): depth += child.layer * 1000
                            
                            if depth > max_depth:
                                max_depth = depth
                                picked = child
                except: pass
                
        return picked

    # --- Update Loop ---
    def _update(self, dt, services):
        if self.state != "EDITOR": return

        # Time Control
        tm = services.get("time")
        if tm: 
            tm.time_scale = 0.0 if self.time_paused else 1.0
            if self.time_reset_req:
                # Force set to NOON (Brightest)
                # PHASE_ORDER = ['DAWN', 'MORNING', 'NOON', 'AFTERNOON', 'EVENING', 'NIGHT']
                # NOON is index 2
                tm.current_phase_idx = 2 
                tm.phase_timer = 0.0
                tm.target_ambient = tm.PHASES['NOON']['ambient']
                tm.current_ambient = tm.target_ambient # Instant change
                self.time_reset_req = False
            
            # Update UI Text
            if self.time_display_btn:
                self.time_display_btn.text = f"Phase: {tm.current_phase}"

        # Camera Move
        keys = pygame.key.get_pressed()
        speed = 800 * dt
        if keys[pygame.K_LSHIFT]: speed *= 2
        
        mx, my = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: mx -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mx += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: my -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: my += speed
        if self.camera: self.camera.move(mx, my)

        # [New] 매 프레임 렌더러에 클리핑 영역 갱신 (창 크기 변경 대응)
        renderer = services.get("renderer")
        if renderer and self.map_view_rect:
            renderer.set_clip_rect(self.map_view_rect)

        # 마우스 처리
        mouse_x, mouse_y = pygame.mouse.get_pos()
        is_in_map_view = self.map_view_rect.collidepoint(mouse_x, mouse_y)
        
        # Wall Edge Highlight (Pre-placement)
        if not self.is_dragging and self.get_current_mode() == "WALL" and is_in_map_view:
            # Auto-detect edge based on mouse position relative to tile center
            gx, gy = self.hover_grid
            
            # Calculate Screen Center of the tile
            cx_world, cy_world = IsoMath.cart_to_iso(gx + 0.5, gy + 0.5)
            sx_center, sy_center = self.camera.world_to_screen(cx_world, cy_world)
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Determine Wall Type based on mouse X relative to tile center
            # Left of center -> NW (Left Edge)
            # Right of center -> NE (Right Edge)
            new_type = "NW" if mouse_x < sx_center else "NE"
            
            if self.wall_type != new_type:
                self.wall_type = new_type
                self._update_ghost()

        

        self.hovered_node = None # [New] Picked Node

        

        if is_in_map_view:

            # [New] Wall Offset: Shift detection point down by half tile height

            # so clicking the top edge of a tile counts as that tile

            bias = TILE_HEIGHT / 2 if self.get_current_mode() == "WALL" else 0

            gx, gy = self._get_mouse_grid_pos(y_bias=bias)

            self.hover_grid = (gx, gy)

            

            # [New] Delete Mode Picking            # If we are dragging Right Mouse (Delete), or just hovering in delete mode?
            # User said: "Cursor hover -> highlight object -> click to delete".
            # So if current drag_mode is 3 (Delete) OR we are not dragging but will right click?
            # Actually, drag_mode is set ON CLICK.
            # We want to highlight when NOT dragging too, if intention is delete?
            # Or just always picking? Let's picking always if not dragging creation.
            
            if not self.is_dragging or self.drag_mode == 3:
                 self.hovered_node = self._pick_node_at_mouse()
            
            if self.is_dragging: 
                self.drag_end = (gx, gy)
                # Only update ghost preview if NOT deleting
                if self.drag_mode != 3: 
                    self._update_ghost()

            if self.ghost_node:
                self.ghost_node.visible = (not self.is_dragging and self.drag_mode != 3 and not self.hovered_node)
                # If we are hovering a node to delete, hide ghost? 
                # Or just show ghost if we are in placement mode.
                
                # Logic:
                # Placement Mode: Show Ghost.
                # Delete Mode (Right Click?): Show Red Highlight on Hovered Node.
                
                # Since we don't have explicit "Delete Mode" toggle (it's Right Mouse Button),
                # We can't know intent until click.
                # But user asked for "Hover -> Highlight".
                # Let's assume Right Click is delete.
                # We can show highlight on hovered object always?
                pass
                
                if not self.is_dragging:
                     self.ghost_node.position.x, self.ghost_node.position.y = gx, gy
        else:
            if self.ghost_node: self.ghost_node.visible = False

    def handle_event(self, event):
        # Resize
        if event.type == pygame.VIDEORESIZE:
            self.screen_width, self.screen_height = event.w, event.h
            # [New] 리사이즈 시 맵 뷰 영역 재계산
            self.map_view_rect = pygame.Rect(0, 0, self.screen_width - self.ui_width, self.screen_height)
            if self.camera:
                self.camera.update_viewport(self.map_view_rect.width, self.map_view_rect.height)
            
            self._setup_launcher_ui(); self._setup_new_map_ui()
            if self.state == "EDITOR":
                self._refresh_editor_ui()
            return

        # State Handling
        if self.state == "LAUNCHER":
            for btn in self.launcher_buttons: btn.handle_event(event)
        elif self.state == "NEW_MAP":
            for inp in self.new_map_inputs: inp.handle_event(event)
            for btn in self.new_map_buttons: btn.handle_event(event)
        elif self.state == "EDITOR":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            is_in_map_view = self.map_view_rect.collidepoint(mouse_x, mouse_y)
            
            if not is_in_map_view: # UI 영역
                if event.type == pygame.MOUSEWHEEL:
                    self.editor_scroll_y += event.y * 20
                    self.editor_scroll_y = max(self.editor_max_scroll, min(0, self.editor_scroll_y))
                else:
                    for btn in self.editor_buttons:
                        if btn.handle_event(event, self.editor_scroll_y): return
            
            else: # 맵 영역
                if event.type == pygame.MOUSEWHEEL:
                     if self.camera:
                        zoom = self.camera.zoom + (event.y * 0.1)
                        # [New] 줌아웃 한계 확장 (0.5 -> 0.1)
                        self.camera.zoom = max(0.1, min(zoom, 3.0))
                
                # Drag Start / Click
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    bias = TILE_HEIGHT / 2 if self.get_current_mode() == "WALL" else 0
                    
                    if event.button == 1: # Left Click: Place
                        self.is_dragging = True
                        self.drag_mode = 1
                        self.drag_start = self._get_mouse_grid_pos(y_bias=bias)
                        self.drag_end = self.drag_start
                    
                    elif event.button == 3: # Right Click: Delete
                        if self.hovered_node:
                            # Single Object Delete
                            self._remove_node_instance(self.hovered_node)
                        else:
                            # Drag Delete (Grid based)
                            self.is_dragging = True
                            self.drag_mode = 3
                            self.drag_start = self._get_mouse_grid_pos(y_bias=bias)
                            self.drag_end = self.drag_start
                
                # Drag End
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.is_dragging and event.button == self.drag_mode:
                        self.is_dragging = False
                        is_delete = (self.drag_mode == 3)
                        x1, y1 = self.drag_start
                        x2, y2 = self.drag_end
                        
                        # [New] Wall Placement: Line only (Not Delete)
                        if self.get_current_mode() == "WALL" and not is_delete:
                            dx_raw = x2 - x1
                            dy_raw = y2 - y1
                            
                            # Enforce Orthogonal
                            if abs(dx_raw) >= abs(dy_raw):
                                # Horizontal (Lock Y) -> NE Wall (Right-Face for Horizontal run)
                                step = 1 if x2 >= x1 else -1
                                for ix in range(x1, x2 + step, step):
                                    self.place_tile(ix, y1, override_wall_type="NE")
                            else:
                                # Vertical (Lock X) -> NW Wall (Left-Face for Vertical run)
                                step = 1 if y2 >= y1 else -1
                                for iy in range(y1, y2 + step, step):
                                    self.place_tile(x1, iy, override_wall_type="NW")
                        
                        # Existing Logic (Rect Area) for Floor/Object/Delete
                        else:
                            rx1, rx2 = sorted([x1, x2])
                            ry1, ry2 = sorted([y1, y2])
                            for dy in range(ry1, ry2 + 1):
                                for dx in range(rx1, rx2 + 1):
                                    if is_delete: self.remove_tile(dx, dy)
                                    else: self.place_tile(dx, dy)

            # Shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.current_mode_idx = (self.current_mode_idx + 1) % len(self.modes)
                    self._refresh_editor_ui(); self._update_ghost()
                elif event.key == pygame.K_r:
                    if self.get_current_mode() == "WALL":
                        self.wall_type = "NW" if self.wall_type == "NE" else "NE"
                        self._update_ghost()
                elif event.key == pygame.K_s: self.save_map("map_data.json")

    # --- Rendering ---
    def _draw_grid(self, screen):
        if not self.camera: return
        col_normal, col_major, col_center = (60, 60, 60), (100, 100, 120), (200, 80, 80)
        mw, mh = self.map_width, self.map_height
        
        # 세로선
        for x in range(mw + 1):
            start = IsoMath.cart_to_iso(x, 0)
            end = IsoMath.cart_to_iso(x, mh)
            p1 = self.camera.world_to_screen(*start)
            p2 = self.camera.world_to_screen(*end)
            w = 1; c = col_normal
            if x == mw // 2: w=3; c=col_center
            elif x % 10 == 0: w=2; c=col_major
            pygame.draw.line(screen, c, p1, p2, w)
            
        # 가로선
        for y in range(mh + 1):
            start = IsoMath.cart_to_iso(0, y)
            end = IsoMath.cart_to_iso(mw, y)
            p1 = self.camera.world_to_screen(*start)
            p2 = self.camera.world_to_screen(*end)
            w = 1; c = col_normal
            if y == mh // 2: w=3; c=col_center
            elif y % 10 == 0: w=2; c=col_major
            pygame.draw.line(screen, c, p1, p2, w)

    def _remove_node_instance(self, node):
        if node in self.children:
            self.children.remove(node)
        
        # Remove from map_data (Linear search needed as we don't know the key easily)
        # Optimization: Node could store its key? Or we search.
        keys_to_remove = []
        for k, v in self.map_data.items():
            if v == node:
                keys_to_remove.append(k)
        for k in keys_to_remove:
            del self.map_data[k]

    def draw_gizmos(self, screen, camera):
        if self.state != "EDITOR":
            screen.fill((40, 40, 50))
            if self.state == "LAUNCHER":
                title = self.title_font.render("8251Ngine Editor", True, (255, 200, 50))
                screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
                for btn in self.launcher_buttons: btn.draw(screen, self.font)
            elif self.state == "NEW_MAP":
                title = self.title_font.render("Create New Map", True, (255, 255, 255))
                screen.blit(title, (self.screen_width//2 - title.get_width()//2, 100))
                for inp in self.new_map_inputs: inp.draw(screen, self.font)
                for btn in self.new_map_buttons: btn.draw(screen, self.font)
            return

        self._draw_grid(screen)

        # [New] Wall Edge Line Highlight
        if not self.is_dragging and self.get_current_mode() == "WALL":
            gx, gy = self.hover_grid
            ix, iy = IsoMath.cart_to_iso(gx, gy)
            sx, sy = self.camera.world_to_screen(ix, iy)
            hw, hh = (TILE_WIDTH/2)*self.camera.zoom, (TILE_HEIGHT/2)*self.camera.zoom
            
            p_top = (sx, sy)
            p_right = (sx + hw, sy + hh)
            p_left = (sx - hw, sy + hh)
            
            line_col = (50, 255, 255)
            if self.wall_type == "NE":
                pygame.draw.line(screen, line_col, p_top, p_right, 3)
            else:
                pygame.draw.line(screen, line_col, p_top, p_left, 3)
        
        # [New] Hover Highlight (Mask Outline)
        if hasattr(self, 'hovered_node') and self.hovered_node:
            s = self.hovered_node.get_sprite()
            if s and self.camera:
                gpos = self.hovered_node.get_global_position()
                ix, iy = IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z)
                sx, sy = self.camera.world_to_screen(ix, iy)
                zoom = self.camera.zoom
                
                # Scale sprite to screen size
                w = int(s.get_width() * zoom)
                h = int(s.get_height() * zoom)
                if w > 0 and h > 0:
                    scaled_s = pygame.transform.scale(s, (w, h))
                    
                    # Create Mask & Outline
                    mask = pygame.mask.from_surface(scaled_s)
                    outline = mask.outline() # List of (x, y)
                    
                    # Pivot Correction: midbottom of sprite is at (sx, sy + TILE_HEIGHT*zoom)
                    # Rect pos (topleft):
                    offset_y = (TILE_HEIGHT) * zoom
                    dest_rect = scaled_s.get_rect(midbottom=(sx, sy + offset_y))
                    
                    # Draw Outline
                    if outline:
                        # Convert local points to screen points
                        screen_points = [(p[0] + dest_rect.x, p[1] + dest_rect.y) for p in outline]
                        pygame.draw.lines(screen, (255, 50, 50), True, screen_points, 2)
        
        # Drag Highlight
        if self.is_dragging and self.camera:
            x1, y1 = self.drag_start
            x2, y2 = self.drag_end
            is_delete = (self.drag_mode == 3)
            highlight_col = (50, 255, 50) if not is_delete else (255, 50, 50)
            
            points_to_draw = []
            
            # Line Highlight for Wall Placement
            if self.get_current_mode() == "WALL" and not is_delete:
                dx_raw = x2 - x1
                dy_raw = y2 - y1
                
                # Enforce Orthogonal (Straight) Line
                if abs(dx_raw) >= abs(dy_raw):
                    y2 = y1 # Lock Y -> Horizontal Line
                    steps = abs(x2 - x1)
                else:
                    x2 = x1 # Lock X -> Vertical Line
                    steps = abs(y2 - y1)

                if steps == 0: points_to_draw.append((x1, y1))
                else:
                    # Bresenham / Linear for orthogonal is simple
                    # We can just iterate the changing axis
                    if y1 == y2: # Horizontal
                        step = 1 if x2 >= x1 else -1
                        for ix in range(x1, x2 + step, step):
                            points_to_draw.append((ix, y1))
                    else: # Vertical
                        step = 1 if y2 >= y1 else -1
                        for iy in range(y1, y2 + step, step):
                            points_to_draw.append((x1, iy))
            
            # Rect Highlight for Others
            else:
                rx1, rx2 = sorted([x1, x2])
                ry1, ry2 = sorted([y1, y2])
                for dy in range(ry1, ry2 + 1):
                    for dx in range(rx1, rx2 + 1):
                        points_to_draw.append((dx, dy))

            # Draw
            for dx, dy in points_to_draw:
                ix, iy = IsoMath.cart_to_iso(dx, dy)
                sx, sy = self.camera.world_to_screen(ix, iy)
                
                hw, hh = (TILE_WIDTH/2)*self.camera.zoom, (TILE_HEIGHT/2)*self.camera.zoom
                pts = [
                    (sx, sy),               # Top
                    (sx + hw, sy + hh),     # Right
                    (sx, sy + hh * 2),      # Bottom
                    (sx - hw, sy + hh)      # Left
                ]
                pygame.draw.polygon(screen, highlight_col, pts, 2)
                    
        screen.set_clip(None)

        # 2. UI Panel
        ui_x = self.screen_width - self.ui_width
        pygame.draw.rect(screen, (30, 30, 35), (ui_x, 0, self.ui_width, self.screen_height))
        pygame.draw.line(screen, (80, 80, 80), (ui_x, 0), (ui_x, self.screen_height))
        
        pygame.draw.rect(screen, (50, 50, 60), (ui_x, 0, self.ui_width, 50))
        mode_txt = self.font.render(f"MODE: {self.get_current_mode()}", True, (255, 200, 50))
        screen.blit(mode_txt, (ui_x + 10, 15))

        clip_rect = pygame.Rect(ui_x, 50, self.ui_width, self.screen_height - 50)
        screen.set_clip(clip_rect)
        for btn in self.editor_buttons: btn.draw(screen, self.font, self.editor_scroll_y)
        screen.set_clip(None)

        info = f"Size: {self.map_width}x{self.map_height} | Grid: {self.hover_grid}"
        info_surf = self.font.render(info, True, (150, 150, 150))
        bg_rect = info_surf.get_rect(topleft=(10, 10))
        bg_rect.inflate_ip(10, 10)
        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect, border_radius=5)
        screen.blit(info_surf, (10, 10))

    # --- Helper ---
    def get_current_mode(self): return self.modes[self.current_mode_idx]
    
    def place_tile(self, x, y, override_wall_type=None):
        if not (0 <= x < self.map_width and 0 <= y < self.map_height): return
        mode = self.get_current_mode()
        
        target_wall = override_wall_type if override_wall_type else self.wall_type
        
        key = (x, y, mode)
        if mode == "WALL": key = (x, y, "WALL_" + target_wall)
        if key in self.map_data: return
        
        node = None
        if mode == "FLOOR": node = TileNode(self.current_tile_id, x, y, layer=0)
        elif mode == "WALL":
            node = WallNode(tile_id=self.current_tile_id, wall_type=target_wall, size_z=2.0)
            node.position.x, node.position.y = x, y
        elif mode == "OBJECT": node = TileNode(self.current_tile_id, x, y, layer=1)
            
        if node: self.add_child(node); self.map_data[key] = node

    def remove_tile(self, x, y):
        mode = self.get_current_mode()
        key = (x, y, mode)
        if mode == "WALL": key = (x, y, "WALL_" + self.wall_type)
        if key in self.map_data:
            self.remove_child(self.map_data[key]); del self.map_data[key]

    def save_map(self, filename):
        out = {"width": self.map_width, "height": self.map_height, "items": []}
        for key, node in self.map_data.items():
            item = {"x": node.position.x, "y": node.position.y}
            if isinstance(node, WallNode): item.update({"type": "WALL", "wall_type": node.wall_type, "tile_id": node.tile_id})
            elif isinstance(node, TileNode): item.update({"type": "TILE", "layer": node.layer, "tile_id": node.tid})
            out["items"].append(item)
        try:
            with open(filename, 'w') as f: json.dump(out, f, indent=4)
            print("Map Saved.")
        except: print("Save Failed")

    def load_map(self, filename):
        if not os.path.exists(filename): return
        with open(filename, 'r') as f: data = json.load(f)
        self.map_width, self.map_height = data.get("width", 30), data.get("height", 30)
        self.map_data = {}; self.children.clear()
        for item in data.get("items", []):
            x, y = item['x'], item['y']
            if item['type'] == "WALL":
                self.wall_type = item['wall_type']; self.current_tile_id = item['tile_id']
                node = WallNode(tile_id=item['tile_id'], wall_type=item['wall_type'], size_z=2.0)
                node.position.x, node.position.y = x, y
                self.add_child(node); self.map_data[(x, y, "WALL_" + item['wall_type'])] = node
            elif item['type'] == "TILE":
                mode = "FLOOR" if item['layer'] == 0 else "OBJECT"
                node = TileNode(item['tile_id'], x, y, layer=item['layer'])
                self.add_child(node); self.map_data[(x, y, mode)] = node
        print("Map Loaded.")