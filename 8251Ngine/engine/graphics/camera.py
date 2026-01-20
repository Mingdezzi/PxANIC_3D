from pygame.math import Vector2

class Camera:
    def __init__(self):
        self.position = Vector2(0, 0)
        self.target_position = Vector2(0, 0)
        self.zoom = 1.0
        self.offset = Vector2(0, 0)
        
        # Settings
        self.smoothing = 0.1
        self.is_following = False
        self.bounds = None # (min_x, min_y, max_x, max_y)

    def update_viewport(self, width, height):
        self.offset = Vector2(width / 2, height / 2)

    def follow(self, target_pos_x, target_pos_y, immediate=False):
        """Sets the target to follow. If immediate is True, snaps instantly."""
        self.is_following = True
        self.target_position = Vector2(target_pos_x, target_pos_y)
        if immediate:
            self.position = Vector2(target_pos_x, target_pos_y)

    def stop_following(self):
        self.is_following = False

    def move(self, dx, dy):
        """Manually move camera (only if not following)"""
        if not self.is_following:
            self.target_position.x += dx
            self.target_position.y += dy

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.bounds = (min_x, min_y, max_x, max_y)

    def update(self):
        # Lerp towards target
        diff = self.target_position - self.position
        
        # If very close, snap
        if diff.length_squared() < 1.0:
            self.position = self.target_position
        else:
            self.position += diff * self.smoothing

        # Apply Bounds
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            # Clamp position considering zoom and offset? 
            # Usually clamp the center position.
            self.position.x = max(min_x, min(max_x, self.position.x))
            self.position.y = max(min_y, min(max_y, self.position.y))

    def world_to_screen(self, x, y):
        return (x - self.position.x) * self.zoom + self.offset.x, \
               (y - self.position.y) * self.zoom + self.offset.y
    
    def screen_to_world(self, sx, sy):
        return (sx - self.offset.x) / self.zoom + self.position.x, \
               (sy - self.offset.y) / self.zoom + self.position.y
