import pygame
from settings import *
from colors import *
from world.tiles import get_texture, get_tile_category

def get_render_height(target):
    """
    Returns the virtual 3D height (Z-axis) of an entity or tile ID.
    Used for shadow length calculation.
    """
    # 1. Entity
    if hasattr(target, 'rect'):
        # Character
        return 22
    
    # 2. Tile ID (int)
    tid = target
    
    # Check High Objects (Walls, Large objects)
    # Walls are 322xxxx
    s_tid = str(tid)
    if s_tid.startswith('322'): return 48 # Wall
    if s_tid.startswith('422'): return 32 # Fence
    if s_tid.startswith('53'): return 40 # Door
    
    # Specific High Objects
    HIGH_OBJS = [
        6310106, 6310107, # Trees
        7310010, # Street Light
        8320205, # Fridge
        8320209, # Closet
        8320213, # Vent (High on wall)
        8320214, # Barrel (Medium)
        8321006, # Vending Machine
        9322006, # Furnace
    ]
    if tid in HIGH_OBJS: return 64
    
    # Specific Low Objects
    LOW_OBJS = [
        1110000, 1110001, # Floors (Should be skipped by caller usually)
        8310208, # Box
        8321211, # Bed
        8320210, # Desk
        8320200, # Table
        9322007, # Cutting Board
    ]
    if tid in LOW_OBJS: return 12
    
    # Default Medium
    return 24

def shear_surface(surf, slope_x):
    """
    Shears a surface horizontally by slope_x.
    Used for 2.5D shadow projection.
    """
    w, h = surf.get_size()
    # Calculate new width based on max shift
    # shift = h * abs(slope_x)
    extra_w = int(h * abs(slope_x))
    new_w = w + extra_w
    
    if new_w <= 0 or h <= 0: return surf # Safety
    
    result = pygame.Surface((new_w, h), pygame.SRCALPHA)
    
    # Iterate rows
    # Top row (y=0) moves the most? Or Bottom?
    # For a standing object casting shadow on ground:
    # The FEET (Bottom, y=h) are fixed.
    # The HEAD (Top, y=0) moves based on light direction.
    # So shift is proportional to (h - y).
    
    for y in range(h):
        src_rect = pygame.Rect(0, y, w, 1)
        
        # Calculate shift
        # When slope_x > 0 (Shadow Right): Top moves Right.
        # shift = (h - y) * slope_x
        # But we need to handle negative slope (Shadow Left) too.
        
        shift_amt = (h - y) * slope_x
        
        # Determine Draw X
        # If slope > 0: start at 0? No, feet are at 'some' x.
        # Let's say original x=0 corresponds to left edge.
        # If skew right, top moves right. Bottom stays.
        # So dest_x = shift_amt
        # But if skew left (slope < 0), top moves left (negative shift).
        # We need to offset everything so it fits in positive coords.
        
        if slope_x >= 0:
            dest_x = int(shift_amt)
        else:
            dest_x = int(shift_amt + extra_w) # Shift is negative, so add max width
            
        result.blit(surf, (dest_x, y), src_rect)
        
    return result

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
    def get_base_surface(entity, is_highlighted=False, current_phase="DAY"):
        """Generates or retrieves the cached base sprite for an entity."""
        cache_key = CharacterRenderer._get_cache_key(entity, is_highlighted)
        if cache_key in CharacterRenderer._sprite_cache:
            return CharacterRenderer._sprite_cache[cache_key]
        
        base_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        skin_idx = entity.custom.get('skin', 0) % len(CUSTOM_COLORS['SKIN'])
        cloth_idx = entity.custom.get('clothes', 0) % len(CUSTOM_COLORS['CLOTHES'])
        body_color = CUSTOM_COLORS['SKIN'][skin_idx]
        clothes_color = CUSTOM_COLORS['CLOTHES'][cloth_idx]
        if is_highlighted: body_color = (255, 50, 50); clothes_color = (150, 0, 0)
        
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
        return base_surf

    @staticmethod
    def draw_shadow(screen, entity, camera_x, camera_y, shift_x=0, shift_y=0):
        if not entity.alive: return
        draw_x = entity.rect.x - camera_x
        draw_y = entity.rect.y - camera_y
        
        # Simple culling
        screen_w, screen_h = screen.get_width(), screen.get_height()
        if not (-50 < draw_x < screen_w + 50 and -50 < draw_y < screen_h + 50): return

        # Base Position (Feet)
        cx = draw_x + (TILE_SIZE // 2)
        cy = draw_y + TILE_SIZE - 2
        
        # 1. Contact Shadow
        contact_w, contact_h = 16, 6
        contact_surf = pygame.Surface((contact_w, contact_h), pygame.SRCALPHA)
        pygame.draw.ellipse(contact_surf, (0, 0, 0, 120), (0, 0, contact_w, contact_h))
        screen.blit(contact_surf, (cx - contact_w // 2, cy - contact_h // 2))

        # 2. Projected Silhouette Shadow
        base_surf = CharacterRenderer.get_base_surface(entity)
        mask = pygame.mask.from_surface(base_surf)
        silhouette = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        
        real_h = get_render_height(entity)
        
        # Dynamic Height Calculation
        target_shadow_h = int(real_h * abs(shift_y))
        target_shadow_h = max(4, target_shadow_h) 
        
        sprite_w = silhouette.get_width()
        scaled_surf = pygame.transform.scale(silhouette, (sprite_w, target_shadow_h))
        
        # Slope Calculation
        if target_shadow_h > 0:
            slope = (real_h * shift_x) / target_shadow_h
        else:
            slope = 0
        
        sheared_surf = shear_surface(scaled_surf, slope)
        
        sw, sh = sheared_surf.get_size()
        
        # Alignment
        if shift_x >= 0:
            shadow_draw_x = draw_x 
        else:
            shadow_draw_x = draw_x - (sw - sprite_w)

        shadow_draw_y = (draw_y + TILE_SIZE) - sh + 2
        
        screen.blit(sheared_surf, (shadow_draw_x, shadow_draw_y))

    @staticmethod
    def draw_entity(screen, entity, camera_x, camera_y, viewer_role="PLAYER", current_phase="DAY", viewer_device_on=False):
        if not entity.alive: return
        draw_x = entity.rect.x - camera_x
        draw_y = entity.rect.y - camera_y
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

        base_surf = CharacterRenderer.get_base_surface(entity, is_highlighted, current_phase)

        final_surf = base_surf
        if alpha < 255: final_surf = base_surf.copy(); final_surf.set_alpha(alpha)
        screen.blit(final_surf, (draw_x, draw_y))

        name_color = (230, 230, 230)
        if entity.role == "POLICE" and viewer_role in ["POLICE", "SPECTATOR"]: name_color = (100, 180, 255)
        elif entity.role == "MAFIA" and viewer_role in ["MAFIA", "SPECTATOR"]: name_color = (255, 100, 100)
        text_cache_key = (id(entity), entity.name, name_color)
        if text_cache_key in CharacterRenderer._name_surface_cache: name_surf = CharacterRenderer._name_surface_cache[text_cache_key]
        else: name_surf = CharacterRenderer.NAME_FONT.render(entity.name, True, name_color); CharacterRenderer._name_surface_cache[text_cache_key] = name_surf
        screen.blit(name_surf, (draw_x + (TILE_SIZE // 2) - (name_surf.get_width() // 2), draw_y - 14))

class MapRenderer:
    CHUNK_SIZE = 16 # Tiles per chunk (16x32 = 512px)

    def __init__(self, map_manager):
        self.map_manager = map_manager
        self._floor_cache = {} # {(cx, cy): Surface}
        self.map_width_tiles = map_manager.width
        self.map_height_tiles = map_manager.height
        self.zone_mesher = None
        self._init_zone_mesher()
        
        # [NEW Shadow Buffer]
        self.shadow_buffer = None
        # [NEW Wall Clusters]
        self.wall_clusters = [] # Stores {surf, silhouette, world_x, world_y, height}
        self._build_wall_clusters()

    def invalidate_cache(self):
        self._floor_cache.clear()
        self.zone_mesher = None # Rebuild on map change
        # Rebuild wall clusters
        self.wall_clusters = []
        self._build_wall_clusters()

    def _init_zone_mesher(self):
        from systems.zone_mesher import ZoneMesher
        self.zone_mesher = ZoneMesher(self.map_manager)
    
    def _build_wall_clusters(self):
        """
        Groups connected wall tiles into single large surfaces (Clusters).
        This ensures buildings cast a single, unified shadow.
        """
        self.wall_clusters = []
        walls = self.map_manager.map_data['wall']
        visited = set()
        rows = self.map_manager.height
        cols = self.map_manager.width
        
        for r in range(rows):
            for c in range(cols):
                if (c, r) in visited: continue
                
                t_data = walls[r][c]
                tid = t_data[0] if isinstance(t_data, (list, tuple)) else t_data
                
                if tid == 0: continue
                
                # Use only high walls for clustering
                h = get_render_height(tid)
                if h <= 12: continue # Skip floors/low objects
                
                # Start searching for connected walls (Flood Fill)
                stack = [(c, r)]
                visited.add((c, r))
                
                min_x, max_x = c, c
                min_y, max_y = r, r
                
                cluster_tiles = []
                cluster_h = h # Use first tile's height as cluster height
                
                while stack:
                    curr_c, curr_r = stack.pop()
                    
                    ct_data = walls[curr_r][curr_c]
                    ct_tid = ct_data[0] if isinstance(ct_data, (list, tuple)) else ct_data
                    ct_rot = ct_data[1] if isinstance(ct_data, (list, tuple)) else 0
                    
                    cluster_tiles.append((curr_c, curr_r, ct_tid, ct_rot))
                    
                    min_x = min(min_x, curr_c)
                    max_x = max(max_x, curr_c)
                    min_y = min(min_y, curr_r)
                    max_y = max(max_y, curr_r)
                    
                    # 4-Way Neighbors
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = curr_c + dx, curr_r + dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if (nx, ny) not in visited:
                                n_data = walls[ny][nx]
                                n_tid = n_data[0] if isinstance(n_data, (list, tuple)) else n_data
                                if n_tid != 0:
                                    nh = get_render_height(n_tid)
                                    # Group only walls of similar height
                                    if abs(nh - cluster_h) < 10: 
                                        visited.add((nx, ny))
                                        stack.append((nx, ny))
                
                # Build Cluster Surface
                w_tiles = (max_x - min_x + 1)
                h_tiles = (max_y - min_y + 1)
                cluster_surf = pygame.Surface((w_tiles * TILE_SIZE, h_tiles * TILE_SIZE), pygame.SRCALPHA)
                
                for tx, ty, ttid, trot in cluster_tiles:
                    img = get_texture(ttid, trot)
                    draw_x = (tx - min_x) * TILE_SIZE
                    draw_y = (ty - min_y) * TILE_SIZE
                    cluster_surf.blit(img, (draw_x, draw_y))
                
                # Pre-generate Silhouette (Optimization)
                mask = pygame.mask.from_surface(cluster_surf)
                silhouette = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
                
                self.wall_clusters.append({
                    'silhouette': silhouette,
                    'world_x': min_x * TILE_SIZE,
                    'world_y': min_y * TILE_SIZE,
                    'width': w_tiles * TILE_SIZE,
                    'height': h_tiles * TILE_SIZE,
                    'render_h': cluster_h
                })

    def _render_floor_chunk(self, cx, cy):
        surf = pygame.Surface((self.CHUNK_SIZE * TILE_SIZE, self.CHUNK_SIZE * TILE_SIZE), pygame.SRCALPHA)
        start_col = cx * self.CHUNK_SIZE
        start_row = cy * self.CHUNK_SIZE
        end_col = min(start_col + self.CHUNK_SIZE, self.map_width_tiles)
        end_row = min(start_row + self.CHUNK_SIZE, self.map_height_tiles)
        floors = self.map_manager.map_data['floor']
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                draw_x = (c - start_col) * TILE_SIZE
                draw_y = (r - start_row) * TILE_SIZE
                tile_data = floors[r][c]
                tid = tile_data[0] if isinstance(tile_data, (tuple, list)) else tile_data
                rot = tile_data[1] if isinstance(tile_data, (tuple, list)) else 0
                if tid != 0:
                    img = get_texture(tid, rot)
                    surf.blit(img, (draw_x, draw_y))
        return surf

    def get_vertical_objects(self, camera):
        """Returns list of vertical objects (Walls, Doors) for Y-sorting"""
        renderables = []
        
        vw, vh = camera.width / camera.zoom_level, camera.height / camera.zoom_level
        start_col = int(max(0, camera.x // TILE_SIZE))
        start_row = int(max(0, camera.y // TILE_SIZE))
        end_col = int(min(self.map_manager.width, (camera.x + vw) // TILE_SIZE + 2))
        end_row = int(min(self.map_manager.height, (camera.y + vh) // TILE_SIZE + 2))
        
        walls = self.map_manager.map_data['wall']
        objects = self.map_manager.map_data['object']
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                # 1. Walls
                w_data = walls[r][c]
                w_tid = w_data[0] if isinstance(w_data, (tuple, list)) else w_data
                w_rot = w_data[1] if isinstance(w_data, (tuple, list)) else 0
                if w_tid != 0:
                    # Construct renderable
                    rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    renderables.append({'type': 'WALL', 'rect': rect, 'tid': w_tid, 'rot': w_rot})
                
                # 2. Doors (Objects category 5)
                o_data = objects[r][c]
                o_tid = o_data[0] if isinstance(o_data, (tuple, list)) else o_data
                o_rot = o_data[1] if isinstance(o_data, (tuple, list)) else 0
                if o_tid != 0:
                    if get_tile_category(o_tid) == 5: # Door
                        rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        renderables.append({'type': 'DOOR', 'rect': rect, 'tid': o_tid, 'rot': o_rot})
        
        return renderables

    def draw_all_shadows(self, screen, camera, shift_x, shift_y):
        """
        Draws merged shadows using pre-calculated clusters and a shadow buffer.
        """
        # Buffer Init
        screen_w, screen_h = screen.get_size()
        if self.shadow_buffer is None or self.shadow_buffer.get_size() != (screen_w, screen_h):
            self.shadow_buffer = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        
        self.shadow_buffer.fill((0, 0, 0, 0))

        # Culling bounds
        cam_x, cam_y = camera.x, camera.y
        vw, vh = camera.width / camera.zoom_level, camera.height / camera.zoom_level
        
        # === 1. Wall Clusters (Buildings) ===
        for cluster in self.wall_clusters:
            # Simple Culling
            if (cluster['world_x'] > cam_x + vw + 100 or 
                cluster['world_x'] + cluster['width'] < cam_x - 100 or
                cluster['world_y'] > cam_y + vh + 100 or
                cluster['world_y'] + cluster['height'] < cam_y - 100):
                continue
            
            # Use Pre-calculated Silhouette
            silhouette = cluster['silhouette']
            real_h = cluster['render_h']
            
            # Dynamic Height & Scale
            target_shadow_h = int(real_h * abs(shift_y))
            target_shadow_h = max(4, target_shadow_h)
            
            sw, sh = silhouette.get_size()
            scaled = pygame.transform.scale(silhouette, (sw, target_shadow_h))
            
            # Shear
            if target_shadow_h > 0:
                slope = (real_h * shift_x) / target_shadow_h
            else:
                slope = 0
            sheared = shear_surface(scaled, slope)
            
            # Position
            draw_x = cluster['world_x'] - cam_x
            draw_y = cluster['world_y'] - cam_y
            
            shadow_w, shadow_h = sheared.get_size()
            
            if shift_x >= 0: sx = draw_x
            else: sx = draw_x - (shadow_w - sw)
            
            # Anchor to bottom of the cluster
            sy = (draw_y + cluster['height']) - shadow_h + 2
            
            self.shadow_buffer.blit(sheared, (sx, sy))

        # === 2. Individual Objects ===
        # Objects are still processed individually as they are dynamic/scattered
        objects = self.map_manager.map_data['object']
        start_col = int(max(0, cam_x // TILE_SIZE))
        start_row = int(max(0, cam_y // TILE_SIZE))
        end_col = int(min(self.map_manager.width, (cam_x + vw) // TILE_SIZE + 2))
        end_row = int(min(self.map_manager.height, (cam_y + vh) // TILE_SIZE + 2))
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                o_data = objects[r][c]
                o_tid = o_data[0] if isinstance(o_data, (tuple, list)) else o_data
                o_rot = o_data[1] if isinstance(o_data, (tuple, list)) else 0
                
                if o_tid == 0: continue
                if get_tile_category(o_tid) == 1: continue 
                
                img = get_texture(o_tid, o_rot)
                mask = pygame.mask.from_surface(img)
                silhouette = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
                
                real_h = get_render_height(o_tid)
                
                target_shadow_h = int(real_h * abs(shift_y))
                target_shadow_h = max(4, target_shadow_h)

                sw, sh = silhouette.get_size()
                scaled = pygame.transform.scale(silhouette, (sw, target_shadow_h))
                
                if target_shadow_h > 0:
                    slope = (real_h * shift_x) / target_shadow_h
                else:
                    slope = 0
                sheared = shear_surface(scaled, slope)
                
                draw_x = c * TILE_SIZE - cam_x
                draw_y = r * TILE_SIZE - cam_y
                
                shadow_w, shadow_h = sheared.get_size()
                if shift_x >= 0: sx = draw_x
                else: sx = draw_x - (shadow_w - sw)
                sy = (draw_y + TILE_SIZE) - shadow_h + 2
                
                self.shadow_buffer.blit(sheared, (sx, sy))
        
        # Final Composite
        self.shadow_buffer.set_alpha(80) 
        screen.blit(self.shadow_buffer, (0, 0))

    def draw_ground(self, screen, camera, visible_tiles=None, tile_alphas=None):
        if tile_alphas is None: tile_alphas = {}
        
        # 1. Calculate Visible Chunks
        start_chunk_x = int(max(0, camera.x // (self.CHUNK_SIZE * TILE_SIZE)))
        start_chunk_y = int(max(0, camera.y // (self.CHUNK_SIZE * TILE_SIZE)))
        end_chunk_x = int(min((self.map_width_tiles // self.CHUNK_SIZE) + 1, (camera.x + camera.width / camera.zoom_level) // (self.CHUNK_SIZE * TILE_SIZE) + 1))
        end_chunk_y = int(min((self.map_height_tiles // self.CHUNK_SIZE) + 1, (camera.y + camera.height / camera.zoom_level) // (self.CHUNK_SIZE * TILE_SIZE) + 1))

        # 2. Draw Floors (Background)
        for cy in range(start_chunk_y, end_chunk_y + 1):
            for cx in range(start_chunk_x, end_chunk_x + 1):
                chunk_key = (cx, cy)
                if chunk_key not in self._floor_cache:
                    self._floor_cache[chunk_key] = self._render_floor_chunk(cx, cy)
                
                chunk_surf = self._floor_cache[chunk_key]
                dest_x = (cx * self.CHUNK_SIZE * TILE_SIZE) - camera.x
                dest_y = (cy * self.CHUNK_SIZE * TILE_SIZE) - camera.y
                screen.blit(chunk_surf, (dest_x, dest_y))

        # Calculate Tile Range for Dynamic Rendering
        vw, vh = camera.width / camera.zoom_level, camera.height / camera.zoom_level
        start_col = int(max(0, camera.x // TILE_SIZE))
        start_row = int(max(0, camera.y // TILE_SIZE))
        end_col = int(min(self.map_manager.width, (camera.x + vw) // TILE_SIZE + 2))
        end_row = int(min(self.map_manager.height, (camera.y + vh) // TILE_SIZE + 2))
        zones = self.map_manager.zone_map

        # 3. Draw Objects (Non-Door objects only)
        objects = self.map_manager.map_data['object']
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                tile_data = objects[r][c]
                tid = tile_data[0] if isinstance(tile_data, (tuple, list)) else tile_data
                rot = tile_data[1] if isinstance(tile_data, (tuple, list)) else 0
                if tid != 0:
                    if get_tile_category(tid) != 5: # NOT Door
                        draw_x = c * TILE_SIZE - camera.x
                        draw_y = r * TILE_SIZE - camera.y
                        img = get_texture(tid, rot)
                        screen.blit(img, (draw_x, draw_y))

        # 4. Apply Indoor Masking
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                if zones[r][c] in INDOOR_ZONES:
                    draw_alpha = 255
                    if visible_tiles is not None:
                        draw_alpha = tile_alphas.get((c, r), 0)
                    
                    if draw_alpha < 255:
                        draw_x = c * TILE_SIZE - camera.x
                        draw_y = r * TILE_SIZE - camera.y
                        black_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        black_surf.fill((0, 0, 0, 255 - draw_alpha))
                        screen.blit(black_surf, (draw_x, draw_y))
