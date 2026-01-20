import math

# Engine Constants
TILE_WIDTH = 64
TILE_HEIGHT = 32
HEIGHT_SCALE = 32 # How many pixels up for 1 unit of Z

class IsoMath:
    @staticmethod
    def cart_to_iso(x, y, z=0):
        """
        Converts 3D Cartesian coordinates (Grid) to 2D Screen coordinates.
        x, y: Grid units
        z: Vertical units
        """
        screen_x = (x - y) * (TILE_WIDTH / 2)
        screen_y = (x + y) * (TILE_HEIGHT / 2) - (z * HEIGHT_SCALE)
        return screen_x, screen_y

    @staticmethod
    def iso_to_cart(screen_x, screen_y):
        """
        Converts Screen coordinates to 2D Grid coordinates (assuming z=0).
        Useful for mouse picking.
        """
        # Inverse matrix logic
        half_w = TILE_WIDTH / 2
        half_h = TILE_HEIGHT / 2
        
        # sx = (x-y)*hw  -> x-y = sx/hw
        # sy = (x+y)*hh  -> x+y = sy/hh
        # 2x = sx/hw + sy/hh
        # 2y = sy/hh - sx/hw
        
        cart_x = (screen_x / half_w + screen_y / half_h) / 2
        cart_y = (screen_y / half_h - screen_x / half_w) / 2
        
        return cart_x, cart_y

    @staticmethod
    def get_depth(x, y, z=0):
        """
        Calculates depth for Y-Sorting.
        Higher depth = Drawn later (on top).
        In standard Iso, depth increases with X and Y.
        """
        # Simple depth: x + y. 
        # Z adds slightly to depth because higher objects visually overlap lower ones "behind" them? 
        # Actually in strict painter's algo for iso tiles:
        # Drawing order is usually based on tile index sum (x+y).
        return (x + y) * 10 + z
