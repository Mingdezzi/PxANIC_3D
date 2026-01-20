import pygame
from engine.core.node import Node
from engine.core.math_utils import IsoMath

class FogOfWar(Node):
    def __init__(self, name="FogOfWar"):
        super().__init__(name)
        self.color = (20, 20, 25, 220) # 거의 불투명한 어두운 색
        self.fov_polygon_world = [] # 월드 좌표계의 시야 폴리곤
        self.surface = None
        self.z_index = 999 # 항상 맨 위에 그려지도록

    def update_resolution(self, width, height):
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)

    def set_fov_polygon(self, polygon_world):
        self.fov_polygon_world = polygon_world

    def _draw(self, services):
        if not self.visible or not self.surface:
            return

        renderer = services.get("renderer")
        if not renderer:
            return

        # 1. 화면 전체를 어둡게 덮음
        self.surface.fill(self.color)
        
        # 2. 시야 다각형(FOV) 부분만 투명하게 뚫음
        if self.fov_polygon_world:
            # 월드 좌표계의 폴리곤을 화면 좌표계로 변환
            fov_screen_points = []
            for wx, wy in self.fov_polygon_world:
                # 월드 좌표 (아이소메트릭) -> 화면 좌표
                sx, sy = renderer.camera.world_to_screen(wx, wy)
                fov_screen_points.append((sx, sy))

            # 폴리곤 영역을 완전히 투명하게 만듦 (BLEND_RGBA_MAX: 알파값을 최대로)
            if len(fov_screen_points) > 2:
                pygame.draw.polygon(self.surface, (0, 0, 0, 0), fov_screen_points)

        # 3. 최종 결과를 화면에 블릿
        renderer.screen.blit(self.surface, (0, 0))
