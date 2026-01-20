import pygame
from engine.core.node import Node
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT, HEIGHT_SCALE
from engine.assets.tile_engine import TileEngine

# Global cache to prevent redundant surface creation
BLOCK_CACHE = {}

class Block3D(Node):
    def __init__(self, name="Block", size_z=1.0, color=(150, 150, 150), zone_id=0, interact_type="NONE", tile_id=None):
        super().__init__(name)
        self.size_z = size_z # 시각적 높이
        self.color = color
        self.zone_id = zone_id
        self.interact_type = interact_type
        self.tile_id = tile_id
        self.cached_surf = None
        self._regen_texture()

    def _regen_texture(self):
        cache_key = (self.size_z, self.color, self.tile_id)
        
        if cache_key in BLOCK_CACHE:
            self.cached_surf = BLOCK_CACHE[cache_key]
            return

        sid = str(self.tile_id) if self.tile_id else ""
        # Use TileEngine's helper to get category
        category = TileEngine.get_tile_category(self.tile_id) if self.tile_id else 0
        
        is_floor = (category == 1 or category == 2) or self.size_z < 0.1
        
        visual_height_px = 0 if is_floor else int(self.size_z * HEIGHT_SCALE)
        
        # Surface Height: Tile Height + Wall/Block Height
        surf_h = TILE_HEIGHT + visual_height_px
        surf = pygame.Surface((TILE_WIDTH, surf_h), pygame.SRCALPHA)
        
        draw_color = self.color
        if self.tile_id and self.tile_id in TileEngine.TILE_DATA:
            draw_color = TileEngine.TILE_DATA[self.tile_id]['color']
        
        # 1. Base Geometry (Sides for walls)
        if not is_floor:
            # Draw simple cube base for sides
            IsoGeometry.draw_cube(surf, TILE_WIDTH // 2, visual_height_px, TILE_WIDTH, TILE_HEIGHT, visual_height_px, draw_color)

        # 2. Top Texture Mapping
        if self.tile_id:
            tile_tex = TileEngine.create_texture(self.tile_id)
            # Resize texture to fit the isometric diamond shape roughly (naive mapping)
            # Better approach: Rotate 45deg and scale Y by 0.5
            
            # Create diamond mask
            mask = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
            points = [(TILE_WIDTH // 2, 0), (TILE_WIDTH, TILE_HEIGHT // 2), (TILE_WIDTH // 2, TILE_HEIGHT), (0, TILE_HEIGHT // 2)]
            pygame.draw.polygon(mask, (255, 255, 255, 255), points)
            
            # Prepare Texture
            scaled_tex = pygame.transform.scale(tile_tex, (TILE_WIDTH, TILE_HEIGHT))
            
            # Apply Mask
            scaled_tex.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Blit to Surface top
            # For walls, top is at (0, 0). For floors, it's also at (0, 0) but they have no height offset in logic usually,
            # but visual_height_px is 0 for floor, so it works.
            surf.blit(scaled_tex, (0, 0))
            
            # Overlay border for definition
            pygame.draw.polygon(surf, (0, 0, 0, 40), points, 1)

        else:
             # Fallback if no tile_id but color exists
             if is_floor:
                 IsoGeometry.draw_cube(surf, TILE_WIDTH // 2, 0, TILE_WIDTH, TILE_HEIGHT, 2, draw_color) # Thin plate

        BLOCK_CACHE[cache_key] = surf
        self.cached_surf = surf

    def set_tile_id(self, new_tile_id):
        if self.tile_id == new_tile_id: return
        self.tile_id = new_tile_id
        # Invalidate current surface and regen
        self._regen_texture()

    def get_sprite(self):
        return self.cached_surf

# Clear cache on module reload to ensure changes take effect
BLOCK_CACHE.clear()
