import pygame
from settings import TILE_SIZE

class Camera:
    def __init__(self, screen_width, screen_height, map_width=0, map_height=0):
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.width = screen_width
        self.height = screen_height
        
        self.map_width = map_width
        self.map_height = map_height
        self.zoom_level = 1.0

        self.map_width_px = map_width * TILE_SIZE
        self.map_height_px = map_height * TILE_SIZE
        
        # [수정] 초기화 시 뷰포트 크기 계산 (__init__ 마지막에 호출)
        self._update_viewport_size()

    @property
    def x(self):
        return self.camera_x

    @x.setter
    def x(self, value):
        self.camera_x = value

    @property
    def y(self):
        return self.camera_y

    @y.setter
    def y(self, value):
        self.camera_y = value

    def resize(self, w, h):
        self.width = w
        self.height = h
        self._update_viewport_size()

    def set_zoom(self, zoom):
        self.zoom_level = zoom
        self._update_viewport_size()
        
    def set_bounds(self, width_px, height_px):
        self.map_width_px = width_px
        self.map_height_px = height_px

    def _update_viewport_size(self):
        """줌이나 해상도 변경 시 1회만 호출"""
        if self.zoom_level > 0:
            self.view_w = self.width / self.zoom_level
            self.view_h = self.height / self.zoom_level
        else:
            self.view_w = self.width
            self.view_h = self.height

    def move(self, dx, dy):
        self.camera_x += dx
        self.camera_y += dy

    def update(self, target_x, target_y):
        # 타겟을 화면 중앙에 위치시키기 위한 카메라의 좌상단 좌표 계산
        x = target_x - self.view_w / 2
        y = target_y - self.view_h / 2
        
        # 맵 경계 제한 (Clamp)
        x, y = self._clamp(x, y)

        self.camera_x = x
        self.camera_y = y

    def smooth_update(self, target_x, target_y, dt, speed=5.0):
        # 1. 목표 위치 계산
        target_cam_x = target_x - self.view_w / 2
        target_cam_y = target_y - self.view_h / 2
        
        # 2. 맵 경계 제한 (목표 위치 자체를 제한)
        target_cam_x, target_cam_y = self._clamp(target_cam_x, target_cam_y)
        
        # 3. Lerp 적용
        # dt * speed가 1.0을 넘으면 overshoot 할 수 있으므로 min 사용 가능하지만, 
        # 일반적인 프레임레이트에서는 괜찮음. 
        # 부드러움을 위해 speed 조절 (기본 5.0 ~ 10.0)
        self.camera_x += (target_cam_x - self.camera_x) * speed * dt
        self.camera_y += (target_cam_y - self.camera_y) * speed * dt
        
        # 작은 오차로 떨림 방지 (선택 사항)
        if abs(self.camera_x - target_cam_x) < 0.5: self.camera_x = target_cam_x
        if abs(self.camera_y - target_cam_y) < 0.5: self.camera_y = target_cam_y

    def _clamp(self, x, y):
        # 가로축
        if self.map_width_px > self.view_w:
            x = max(0, min(x, self.map_width_px - self.view_w))
        else:
            x = -(self.view_w - self.map_width_px) / 2

        # 세로축
        if self.map_height_px > self.view_h:
            y = max(0, min(y, self.map_height_px - self.view_h))
        else:
            y = -(self.view_h - self.map_height_px) / 2
            
        return x, y
