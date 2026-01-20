import pygame
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT

class ShadowRenderer:
    @staticmethod
    def draw_directional_shadow(screen, camera, node, light_dir, scale=1.0):
        """
        태양/달과 같은 전역 광원에 의한 그림자를 그립니다.
        light_dir: 빛이 나아가는 방향 벡터
        """
        if not hasattr(node, 'size_z') or node.size_z <= 0.1: return
        
        obj_pos = node.get_global_position()
        w_half = 0.5
        h = node.size_z
        
        # 바닥 지점들
        base_corners = [
            (obj_pos.x, obj_pos.y - w_half, 0),
            (obj_pos.x + w_half, obj_pos.y, 0),
            (obj_pos.x, obj_pos.y + w_half, 0),
            (obj_pos.x - w_half, obj_pos.y, 0)
        ]
        
        projected_points = []
        for bx, by, bz in base_corners:
            # 높이와 빛 방향에 따른 투영 위치 계산
            px = bx + light_dir.x * h * 2.0
            py = by + light_dir.y * h * 2.0
            
            iso_x, iso_y = IsoMath.cart_to_iso(px, py, 0)
            sx, sy = camera.world_to_screen(iso_x, iso_y)
            projected_points.append((sx * scale, sy * scale))
            
            # 바닥 지점도 추가하여 폴리곤 연결
            b_iso_x, b_iso_y = IsoMath.cart_to_iso(bx, by, 0)
            bsx, bsy = camera.world_to_screen(b_iso_x, b_iso_y)
            projected_points.append((bsx * scale, bsy * scale))

        if len(projected_points) > 2:
            pygame.draw.polygon(screen, (0, 0, 0, 80), projected_points)

    @staticmethod
    def draw_shadow_volume(screen, camera, node, light_pos, scale=1.0):
        """
        점 광원(횃불 등)에 의한 그림자 볼륨을 그립니다.
        """
        if not hasattr(node, 'size_z') or node.size_z <= 0.1: return 
        
        obj_pos = node.get_global_position()
        w_half = 0.5
        h = node.size_z
        
        corners = [
            (obj_pos.x, obj_pos.y - w_half, obj_pos.z + h), 
            (obj_pos.x + w_half, obj_pos.y, obj_pos.z + h), 
            (obj_pos.x, obj_pos.y + w_half, obj_pos.z + h), 
            (obj_pos.x - w_half, obj_pos.y, obj_pos.z + h) 
        ]
        
        projected_points = []
        lz = light_pos.z
        if lz <= obj_pos.z + h: return 
        
        for cx, cy, cz in corners:
            dx = cx - light_pos.x
            dy = cy - light_pos.y
            dz = cz - lz
            
            if dz == 0: continue
            t = -lz / dz
            
            gx = light_pos.x + dx * t
            gy = light_pos.y + dy * t
            
            iso_x, iso_y = IsoMath.cart_to_iso(gx, gy, 0)
            sx, sy = camera.world_to_screen(iso_x, iso_y)
            projected_points.append((sx * scale, sy * scale))
            
        if len(projected_points) == 4:
            pygame.draw.polygon(screen, (0, 0, 0, 120), projected_points)
