import math
import pygame

class FOVSystem:
    def __init__(self, collision_world):
        self.world = collision_world
        self.ray_count = 120
        self.view_radius = 8.0

    def calculate_fov(self, origin_pos, facing_dir=None, radius=None, fov_angle=120):
        """
        Zomboid-style FOV: Combines a forward-facing cone with a small rear circle.
        """
        view_radius = radius if radius is not None else self.view_radius

        if not facing_dir: # Fallback to 360 view if no direction
            return self._calculate_arc(origin_pos, view_radius, 0, 360)

        # 1. Forward Cone
        main_fov_points = self._calculate_arc(origin_pos, view_radius, 0, fov_angle, facing_dir)
        
        # 2. Small Rear/Peripheral Circle (for awareness behind)
        rear_radius = view_radius * 0.3
        rear_fov_points = self._calculate_arc(origin_pos, rear_radius, 0, 360)
        
        # This combination isn't a simple union. A better approach is one polygon.
        # Let's do a main cone and a smaller peripheral arc.
        
        points = []
        points.append((origin_pos.x, origin_pos.y))

        # Main forward cone
        base_angle = math.degrees(math.atan2(facing_dir[1], facing_dir[0]))
        start_angle_main = base_angle - fov_angle / 2
        end_angle_main = base_angle + fov_angle / 2
        
        # Rear peripheral arc (the remaining part of the circle)
        start_angle_rear = end_angle_main
        end_angle_rear = start_angle_main + 360
        
        # Cast rays for the main cone with full radius
        step_main = (end_angle_main - start_angle_main) / (self.ray_count * 0.8)
        for i in range(int(self.ray_count * 0.8) + 1):
            angle = start_angle_main + i * step_main
            points.append(self._cast_ray(origin_pos.x, origin_pos.y, angle, view_radius))

        # Cast rays for the rear arc with smaller radius
        step_rear = (end_angle_rear - start_angle_rear) / (self.ray_count * 0.2)
        for i in range(int(self.ray_count * 0.2) + 1):
            angle = start_angle_rear + i * step_rear
            points.append(self._cast_ray(origin_pos.x, origin_pos.y, angle, rear_radius))
            
        return points

    def _calculate_arc(self, origin, radius, start_angle, end_angle, base_dir=None):
        """Helper to calculate a visibility arc."""
        points = []
        points.append((origin.x, origin.y))
        
        base_angle_rad = 0
        if base_dir:
            base_angle_rad = math.atan2(base_dir[1], base_dir[0])

        num_steps = int(self.ray_count * ((end_angle - start_angle) / 360))
        angle_step = math.radians((end_angle - start_angle) / num_steps)
        start_angle_rad = base_angle_rad + math.radians(start_angle - (end_angle - start_angle)/2)

        for i in range(num_steps + 1):
            angle = start_angle_rad + i * angle_step
            points.append(self._cast_ray(origin.x, origin.y, angle, radius))
        return points

    def _cast_ray(self, ox, oy, angle_rad, max_dist):
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)
        
        x, y = ox, oy
        step_size = 0.5
        dist = 0
        
        while dist < max_dist:
            x += dx * step_size
            y += dy * step_size
            dist += step_size
            
            if self.world.check_collision(pygame.math.Vector3(x, y, 0), size=0.1):
                return (x, y)
                
        return (x, y)
