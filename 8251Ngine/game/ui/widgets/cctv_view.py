import pygame
from engine.ui.gui import Control, Label, Panel, Button
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS # COLORS는 settings.py 또는 game.data.colors에서 가져올 수 있음
import random

class CCTVViewWidget(Panel):
    def __init__(self, scene):
        super().__init__(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, color=(0, 0, 0, 200)) # 전체 화면을 덮는 패널
        self.scene = scene
        self.active = False
        self.current_cam_idx = 0
        self.camera_locations = [] # 맵에서 CCTV 카메라 위치를 가져와야 함 (TODO)

        self.lbl_cam_name = Label("CCTV CAM 01", 10, 10, size=24, color=(0, 255, 0))
        self.add_child(self.lbl_cam_name)

        self.btn_next_cam = Button("NEXT", SCREEN_WIDTH - 100, 10, 80, 30, on_click=self.next_cam)
        self.add_child(self.btn_next_cam)

        self.btn_close = Button("CLOSE (Q)", SCREEN_WIDTH - 100, SCREEN_HEIGHT - 40, 80, 30, on_click=self.close)
        self.add_child(self.btn_close)

    def open(self):
        self.active = True
        self.visible = True
        self._init_camera_locations()
        self.current_cam_idx = 0
        self._update_cam_view()

    def close(self):
        self.active = False
        self.visible = False

    def next_cam(self):
        if not self.camera_locations: return
        self.current_cam_idx = (self.current_cam_idx + 1) % len(self.camera_locations)
        self._update_cam_view()

    def _init_camera_locations(self):
        # TODO: 맵 데이터에서 CCTV 타일(TID) 위치를 가져와야 함
        # 현재는 임시로 몇 군데 설정
        self.camera_locations = [
            pygame.math.Vector2(5, 5),
            pygame.math.Vector2(15, 15),
            pygame.math.Vector2(25, 5),
        ]
        # PxANIC!의 CCTV_TID를 사용하여 맵에서 실제 카메라 위치를 찾아야 함
        # self.scene.map_loader.get_tile_positions(CCTV_TID)와 같은 기능이 MapLoader에 있어야 함

    def _update_cam_view(self):
        if not self.camera_locations:
            self.lbl_cam_name.set_text("NO CAMERAS")
            return

        cam_pos = self.camera_locations[self.current_cam_idx]
        self.lbl_cam_name.set_text(f"CCTV CAM {self.current_cam_idx + 1} ({int(cam_pos.x)}, {int(cam_pos.y)})")
        
        # 실제 CCTV 화면을 렌더링하는 로직 (TODO)
        # self.scene.services["renderer"].render_from_camera(cam_pos, zoom_level=1.0)
        # 현재는 그냥 UI만 표시
