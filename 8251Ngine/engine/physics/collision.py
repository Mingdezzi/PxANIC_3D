from pygame.math import Vector3
import math

class CollisionWorld:
    def __init__(self):
        # pyspatialgrid 대신 간단한 Dictionary 기반 공간 해싱 사용
        self.static_grid = {}
        self.cell_size = 2.0 # 그리드 셀 크기

    def _get_grid_coords(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))

    def _get_bounding_box(self, entity):
        size = 0.8
        half_size = size / 2
        pos = entity.get_global_position()
        return (
            pos.x - half_size, pos.y - half_size,
            pos.x + half_size, pos.y + half_size
        )

    def add_static(self, entity):
        pos = entity.get_global_position()
        coords = self._get_grid_coords(pos)
        if coords not in self.static_grid:
            self.static_grid[coords] = []
        self.static_grid[coords].append(entity)

    def remove_static(self, entity):
        coords = self._get_grid_coords(entity.get_global_position())
        if coords in self.static_grid and entity in self.static_grid[coords]:
            self.static_grid[coords].remove(entity)

    def get_nearby_objects(self, pos):
        objects = []
        cx, cy = self._get_grid_coords(pos)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                key = (cx + dx, cy + dy)
                if key in self.static_grid:
                    objects.extend(self.static_grid[key])
        return objects

    def check_collision(self, pos, size=0.4):
        nearby = self.get_nearby_objects(pos)
        for body in nearby:
            dist_x = abs(pos.x - body.position.x)
            dist_y = abs(pos.y - body.position.y)
            
            body_size = 0.4 # 충돌체의 기본 크기
            if dist_x < (size + body_size) and dist_y < (size + body_size):
                body_h = getattr(body, 'size_z', 1.0) * 5 # HEIGHT_SCALE 가정
                if pos.z < body.position.z + body_h and pos.z + 1.8 > body.position.z:
                    return True
        return False

    def raycast(self, start, end, step=0.1):
        dist = start.distance_to(end)
        if dist == 0: return None
        direction = (end - start).normalize()
        current = Vector3(start)
        travelled = 0
        while travelled < dist:
            if self.check_collision(current, size=0.1):
                return current
            current += direction * step
            travelled += step
        return None
