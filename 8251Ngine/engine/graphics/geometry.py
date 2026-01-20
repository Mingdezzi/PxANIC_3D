import pygame

class IsoGeometry:
    @staticmethod
    def draw_cube(surface, x, y, w, h, height, color):
        """
        Draws a 3D-looking isometric cube on the given surface.
        w, h: base diamond width/height
        height: the height of the cube side
        """
        top_color = color
        # Left face is darker
        left_color = [max(0, c - 40) for c in color]
        # Right face is even darker
        right_color = [max(0, c - 80) for c in color]

        # Points for the Top Face (Diamond)
        top_pts = [
            (x, y - height),           # Top
            (x + w//2, y + h//2 - height), # Right
            (x, y + h - height),       # Bottom
            (x - w//2, y + h//2 - height)  # Left
        ]

        # Points for the Left Face
        left_pts = [
            (x - w//2, y + h//2 - height),
            (x, y + h - height),
            (x, y + h),
            (x - w//2, y + h//2)
        ]

        # Points for the Right Face
        right_pts = [
            (x + w//2, y + h//2 - height),
            (x, y + h - height),
            (x, y + h),
            (x + w//2, y + h//2)
        ]

        # Draw faces
        pygame.draw.polygon(surface, left_color, left_pts)
        pygame.draw.polygon(surface, right_color, right_pts)
        pygame.draw.polygon(surface, top_color, top_pts)
        
        # Draw Outlines
        outline_col = (20, 20, 20)
        pygame.draw.polygon(surface, outline_col, top_pts, 1)
        pygame.draw.polygon(surface, outline_col, left_pts, 1)
        pygame.draw.polygon(surface, outline_col, right_pts, 1)
