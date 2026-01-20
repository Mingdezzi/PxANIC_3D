import heapq
from pygame.math import Vector2

class NavigationManager:
    def __init__(self, collision_world):
        self.collision_world = collision_world

    def get_path(self, start_pos, end_pos):
        start = (int(start_pos.x), int(start_pos.y))
        goal = (int(end_pos.x), int(end_pos.y))
        
        if start == goal: return []

        queue = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}

        while queue:
            current = heapq.heappop(queue)[1]

            if current == goal:
                break

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                next_node = (current[0] + dx, current[1] + dy)
                
                # 충돌 체크 (CollisionWorld 활용)
                from pygame.math import Vector3
                if self.collision_world.check_collision(Vector3(next_node[0], next_node[1], 0)):
                    continue

                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(goal, next_node)
                    heapq.heappush(queue, (priority, next_node))
                    came_from[next_node] = current

        if goal not in came_from: return []

        # 경로 재구성
        path = []
        curr = goal
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
