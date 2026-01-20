import pygame
from engine.core.node import Node
from engine.assets.tile_engine import TileEngine
from engine.graphics.geometry import IsoGeometry
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT, HEIGHT_SCALE

class TileNode(Node):
    def __init__(self, tid, x, y, layer=0, size_z=0.1):
        super().__init__(f"Tile_{tid}")
        self.tid = tid
        self.position.x = x
        self.position.y = y
        self.position.z = 0 # Base is always on floor
        self.layer = layer # 0: Floor, 1: Wall, 2: Furniture
        self.size_z = size_z 
        
        self.sprite = None
        self._regen_sprite()
        
        # Y-sorting: layer * 100 + grid depth
        self.z_index = layer * 100

    def _regen_sprite(self):
        # 1. Get Texture from Engine
        tex = TileEngine.create_texture(self.tid)
        
        if self.layer == 0: # Flat Floor (바닥)
            # Transform 32x32 Flat -> 64x32 Isometric Diamond (Screen Aligned)
            # 회전하지 않고 가로 2배, 세로 1배로 늘린 후 마름모 마스킹
            
            # 1. Scale: Width 200%, Height 100%
            # (Perspective Squash: 사실상 높이가 50% 줄어든 효과)
            scaled = pygame.transform.scale(tex, (TILE_WIDTH, TILE_HEIGHT))
            
            # 2. Masking to Diamond
            mask = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
            points = [
                (TILE_WIDTH // 2, 0),
                (TILE_WIDTH, TILE_HEIGHT // 2),
                (TILE_WIDTH // 2, TILE_HEIGHT),
                (0, TILE_HEIGHT // 2)
            ]
            pygame.draw.polygon(mask, (255, 255, 255), points)
            
            # 3. Apply Mask
            self.sprite = scaled.copy()
            self.sprite.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            self.size_z = 0.05 

        else: # Objects (Billboard style for now)
            # Just use the texture as is, maybe scaled up slightly?
            # Or map it to a cube face?
            # For "Billboard" objects (Tree, Flower), we just want them standing up.
            
            # If it's a cube-like object (Box, Crate), we might want 3D.
            # But for now, let's render them as "Standing Sprites" (Billboards).
            
            # Scale up for visibility? 32x32 might be small on a 64-wide tile.
            # Let's keep 1:1 scale for now, centered.
            
            # However, Renderer expects (iso_x, iso_y) which is the center-bottom of the tile.
            # The sprite should have its "feet" at the bottom-center.
            
            scale_factor = 1.5 if self.layer == 1 else 1.0 # Walls/Objects slightly larger?
            w, h = int(tex.get_width() * scale_factor), int(tex.get_height() * scale_factor)
            self.sprite = pygame.transform.scale(tex, (w, h))

    def get_sprite(self):
        return self.sprite

    def to_dict(self):
        return {
            "tid": self.tid,
            "pos": [self.position.x, self.position.y],
            "layer": self.layer,
            "size_z": self.size_z
        }