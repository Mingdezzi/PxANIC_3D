import pygame
from engine.core.node import Node
from engine.assets.tile_engine import TileEngine
from engine.core.math_utils import TILE_WIDTH, TILE_HEIGHT, HEIGHT_SCALE

class WallNode(Node):
    def __init__(self, name="Wall", size_z=2.0, tile_id=None, color=(120, 120, 120), wall_type="NE"):
        super().__init__(name)
        self.size_z = size_z
        self.tile_id = tile_id
        self.color = color
        self.wall_type = wall_type  # "NE" (우상향) or "NW" (좌상향)
        self.cached_surf = None
        self._regen_texture()

    def _skew_surface_y(self, surface, slope):
        """Vertical Shear: Shift columns based on x position."""
        w, h = surface.get_size()
        # Calculate new height to accommodate skew
        # Max shift is w * slope
        extra_h = int(abs(w * slope))
        new_surf = pygame.Surface((w, h + extra_h), pygame.SRCALPHA)
        
        for x in range(w):
            shift = int(x * slope)
            if slope < 0: shift = int((w - x) * abs(slope)) # Adjust for negative slope visual
            
            # Blit 1px wide column
            col_surf = surface.subsurface((x, 0, 1, h))
            new_surf.blit(col_surf, (x, shift))
            
        return new_surf

    def _regen_texture(self):
        visual_height_px = int(self.size_z * HEIGHT_SCALE)
        surf_height = TILE_HEIGHT + visual_height_px
        
        # 1. Get Texture & Create Tiled Base (Larger to handle skew)
        tid = self.tile_id if self.tile_id else 0
        tex = TileEngine.create_texture(tid)
        
        base_w, base_h = TILE_WIDTH, surf_height
        tiled_surf = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        
        for y in range(0, base_h, 32):
            for x in range(0, base_w, 32):
                tiled_surf.blit(tex, (x, y))

        # 2. Skew Texture to match Iso Slope (+/- 0.5)
        # NE (Right Face): Slope +0.5 (Down-Right)
        # NW (Left Face): Slope -0.5 (Down-Left from center.. actually Up-Right visually?)
        
        # NE Face (Right side): Goes from Top-Center to Right. (x=0..32 -> y=0..16)
        # Wait, local coordinates:
        # Texture width is 64? No wall is usually drawn on half-width visually.
        # But here WallNode draws on full TILE_WIDTH canvas.
        
        # Let's simplify.
        # NE Wall: Face is on the Right half.
        # NW Wall: Face is on the Left half.
        
        # To make horizontal brick lines follow the slope:
        # NE Slope: +0.5 (y increases as x increases)
        # NW Slope: -0.5 (y decreases as x increases? or y increases as x decreases)
        
        skewed_tex = None
        
        if self.wall_type == "NE":
            # Skew Down-Right
            skewed_tex = self._skew_surface_y(tiled_surf, 0.5)
        else:
            # Skew Down-Left (effectively Up-Right in our positive-y loop logic)
            # Actually, for NW, left side is lower Y (higher on screen), right side (center) is higher Y (lower on screen)
            # Center (32, 16), Left (0, 0).
            # As x increases (0->32), y increases (0->16). Slope is +0.5!
            # Both faces actually slope DOWN from Top-Center if we traverse outwards.
            
            # BUT in 'tiled_surf' x goes 0..64.
            # For NE: We use Right half (32..64).
            # For NW: We use Left half (0..32).
            
            # Let's try skewing the whole texture with slope 0.5 first.
            # Then for NW, we might need to flip or adjust.
            
            # Actually:
            # NE Face: (Center, Top) -> (Right, Middle). Line: y = 0.5 * (x - 32).
            # NW Face: (Center, Top) -> (Left, Middle). Line: y = -0.5 * (x - 32).
            
            # So NE needs +0.5 skew.
            # NW needs -0.5 skew.
            
            skewed_tex = self._skew_surface_y(tiled_surf, 0.5 if self.wall_type == "NE" else -0.5)

        # 3. Create Mask & Apply
        # Canvas needs to be big enough for skewed result
        final_surf = pygame.Surface(skewed_tex.get_size(), pygame.SRCALPHA)
        
        # Re-calculate polygon for the larger skewed surface
        # The skewed surface is taller.
        # However, our WallNode expects sprite to align with TILE_HEIGHT/2 offset usually?
        # Let's align the "Top Center" of the wall to (TILE_WIDTH//2, 0).
        
        # Skewing shifts pixels down.
        # At x=32 (Center), shift is 16.
        # So (32, 0) becomes (32, 16).
        # We need to offset the drawing to put (32, 16) back to (32, 0) relative to tile origin?
        # Renderer handles placement. Wall "feet" are at bottom.
        
        # Let's simply center the 'skewed' texture on the mask.
        
        cx = TILE_WIDTH // 2
        cy = 0 # Top of head
        
        if self.wall_type == "NE":
            # Poly: (32,0) -> (64,16) -> (64, H+16) -> (32, H)
            poly = [
                (cx, 0), 
                (TILE_WIDTH, TILE_HEIGHT // 2),
                (TILE_WIDTH, TILE_HEIGHT // 2 + visual_height_px),
                (cx, visual_height_px)
            ]
            # Adjust for skew shift?
            # Skewing moves (32,0) to (32,16).
            # We want the TEXTURE at (32,16) to map to Poly (32,0)?
            # No, we want the pattern to match.
            
            # Crop the useful part.
            final_surf.blit(skewed_tex, (0, -TILE_HEIGHT//2)) # Naive alignment correction
            
        else: # NW
            # Poly: (32,0) -> (0,16) -> (0, H+16) -> (32, H)
            poly = [
                (cx, 0),
                (0, TILE_HEIGHT // 2),
                (0, TILE_HEIGHT // 2 + visual_height_px),
                (cx, visual_height_px)
            ]
            # NW Skew (-0.5): (32,0) shifts to (32, -16)?? No, logic in _skew handles abs.
            # If slope -0.5:
            # x=0 -> shift (64-0)*0.5 = 32.
            # x=32 -> shift 16.
            # x=64 -> shift 0.
            # It Slopes UP.
            
            final_surf.blit(skewed_tex, (0, -TILE_HEIGHT)) # Trial adjustment

        # Mask
        mask = pygame.Surface(final_surf.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255), poly)
        final_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Shading
        if self.wall_type == "NW":
            shade = pygame.Surface(final_surf.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(shade, (0, 0, 0, 80), poly)
            final_surf.blit(shade, (0, 0))

        # Crop to standard size if possible, or keep large?
        # Renderer uses midbottom.
        # Feet are at:
        # NE: (32, H) and (64, H+16). Visual bottom is approx H+16.
        # We need to return a surface where "bottom-center" roughly aligns with tile center?
        
        # Let's just return the clipped surface, Renderer aligns midbottom.
        # The visual 'lowest' point of a wall is Bottom-Right (NE) or Bottom-Left (NW).
        # But the Pivot (Grid pos) is Bottom-Center of the theoretical tile.
        
        # For simple alignment:
        self.cached_surf = final_surf.subsurface((0, 0, TILE_WIDTH, surf_height + TILE_HEIGHT)) # Safety crop

    def get_sprite(self):
        return self.cached_surf
    
    def to_dict(self):
        """데이터 직렬화 (저장용)"""
        return {
            "type": "WALL",
            "wall_type": self.wall_type,
            "tile_id": self.tile_id,
            "size_z": self.size_z,
            "pos": [self.position.x, self.position.y],
            "color": self.color
        }