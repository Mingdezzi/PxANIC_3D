import pygame
from settings import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from systems.renderer import MapRenderer
from world.tiles import get_texture

class CCTVViewWidget:
    def __init__(self, state):
        self.state = state
        self.active = False
        self.current_cam_idx = 0
        self.cctv_list = []
        
        # 5x5 view -> 5 * 32 = 160px. Scale up to 400x400?
        self.view_w_tiles = 7
        self.view_h_tiles = 7
        self.view_size = 500
        self.surface = pygame.Surface((self.view_size, self.view_size))
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        
    def open(self):
        self.active = True
        self.cctv_list = self.state.world.map_manager.tile_cache.get(7310011, [])
        if not self.cctv_list:
            self.active = False
            return
        self.current_cam_idx = 0

    def close(self):
        self.active = False

    def next_cam(self):
        if self.cctv_list:
            self.current_cam_idx = (self.current_cam_idx + 1) % len(self.cctv_list)

    def draw(self, screen):
        if not self.active or not self.cctv_list: return
        
        # Dim Background
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 230))
        screen.blit(overlay, (0, 0))
        
        # CCTV Logic
        cx, cy = self.cctv_list[self.current_cam_idx]
        
        # Draw View
        self.surface.fill((0, 0, 0))
        
        # Center in tiles
        center_tx = cx // TILE_SIZE
        center_ty = cy // TILE_SIZE
        
        start_tx = center_tx - self.view_w_tiles // 2
        start_ty = center_ty - self.view_h_tiles // 2
        
        scale = self.view_size / (self.view_w_tiles * TILE_SIZE)
        
        mm = self.state.world.map_manager
        
        # 1. Floor & Wall & Object
        for ry in range(self.view_h_tiles):
            for rx in range(self.view_w_tiles):
                tx = start_tx + rx
                ty = start_ty + ry
                
                if 0 <= tx < mm.width and 0 <= ty < mm.height:
                    # Draw Floor
                    tid, rot = mm.get_tile_full(tx, ty, 'floor')
                    if tid: self._draw_tile(tid, rot, rx, ry, scale)
                    
                    # Draw Wall
                    tid, rot = mm.get_tile_full(tx, ty, 'wall')
                    if tid: self._draw_tile(tid, rot, rx, ry, scale)
                    
                    # Draw Object
                    tid, rot = mm.get_tile_full(tx, ty, 'object')
                    if tid: self._draw_tile(tid, rot, rx, ry, scale)

        # 2. Entities
        for n in self.state.world.npcs + [self.state.player]:
            if n.alive:
                ntx = n.rect.centerx / TILE_SIZE
                nty = n.rect.centery / TILE_SIZE
                
                if start_tx <= ntx < start_tx + self.view_w_tiles and start_ty <= nty < start_ty + self.view_h_tiles:
                    # Rel pos
                    rel_x = (ntx - start_tx) * TILE_SIZE * scale
                    rel_y = (nty - start_ty) * TILE_SIZE * scale
                    
                    # Simple circle for entities in CCTV (Low res style)
                    col = (255, 255, 255)
                    if n.role == "MAFIA": col = (255, 0, 0) # Police CCTV can identify? Maybe not fully detailed
                    
                    pygame.draw.circle(self.surface, col, (int(rel_x), int(rel_y)), int(10 * scale))

        # Scanline Effect
        for i in range(0, self.view_size, 4):
            pygame.draw.line(self.surface, (0, 0, 0, 50), (0, i), (self.view_size, i))
            
        # Blit View
        view_x = (SCREEN_WIDTH - self.view_size) // 2
        view_y = (SCREEN_HEIGHT - self.view_size) // 2
        screen.blit(self.surface, (view_x, view_y))
        
        # Border
        pygame.draw.rect(screen, (200, 50, 50), (view_x, view_y, self.view_size, self.view_size), 3)
        
        # Text
        txt = self.font.render(f"CAM-{self.current_cam_idx + 1:02d} [REC]", True, (255, 50, 50))
        screen.blit(txt, (view_x + 10, view_y + 10))
        
        help_txt = self.font.render("SPACE: Next Cam | Q: Exit", True, (200, 200, 200))
        screen.blit(help_txt, (view_x, view_y + self.view_size + 10))

    def _draw_tile(self, tid, rot, rx, ry, scale):
        img = get_texture(tid, rot)
        scaled_img = pygame.transform.scale(img, (int(TILE_SIZE * scale), int(TILE_SIZE * scale)))
        self.surface.blit(scaled_img, (rx * TILE_SIZE * scale, ry * TILE_SIZE * scale))
