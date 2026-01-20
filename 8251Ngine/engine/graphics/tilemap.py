import pygame
from engine.core.node import Node
from engine.assets.tile_engine import TileEngine
from engine.core.math_utils import IsoMath, TILE_WIDTH, TILE_HEIGHT

class TileMap(Node):
    def __init__(self, name="TileMap"):
        super().__init__(name)
        self.map_surface = None
        self.map_data = None
        self.width = 0
        self.height = 0

    def load_from_blocks(self, blocks, width, height):
        """
        로드된 블록 데이터 리스트에서 바닥 타일만 추출하여 맵을 생성합니다.
        """
        self.width = width
        self.height = height
        
        # 1. 렌더링에 필요한 최종 서피스 크기 계산
        # 맵의 (0,0)과 (width, height)를 아이소메트릭 좌표로 변환하여 전체 크기를 추정
        iso_w = (width + height) * TILE_WIDTH // 2
        iso_h = (width + height) * TILE_HEIGHT // 2 + TILE_HEIGHT # 추가 여유 공간
        
        self.map_surface = pygame.Surface((iso_w, iso_h), pygame.SRCALPHA)
        
        # 2. 모든 블록을 순회하며 서피스에 그리기
        #    기존에는 바닥 타일만 필터링했으나, 이제 오브젝트 등도 렌더링하도록 변경
        for block_data in blocks: # Removed filtering for floor_blocks
            pos = block_data["pos"]
            tid = block_data["tile_id"]
            
            if tid:
                # TileEngine에서 텍스처 가져오기
                tile_tex = TileEngine.create_texture(tid)
                if tile_tex:
                    # Cartesian 좌표(pos)를 Isometric 화면 좌표로 변환
                    screen_x, screen_y = IsoMath.cart_to_iso(pos[0], pos[1])
                    
                    # 맵의 (0,0)이 서피스의 중앙 부근에 오도록 오프셋 조정
                    # 맵의 가장 왼쪽 꼭짓점(0, height)이 (0, iso_h/2) 근처에 오게 됨
                    offset_x = (height) * TILE_WIDTH // 2
                    
                    self.map_surface.blit(tile_tex, (screen_x + offset_x, screen_y))
        
        print(f"[TileMap] Generated map surface ({iso_w}x{iso_h}) with {len(blocks)} blocks.") # Updated print statement

    def get_sprite(self):
        # Renderer가 이 서피스를 직접 사용하도록 반환
        return self.map_surface

    def _draw(self, services):
        # Renderer가 get_sprite()를 사용하므로 이 메서드는 비워둘 수 있음
        # 하지만 직접 그리기를 원할 경우를 대비해 로직 추가 가능
        if self.visible and self.map_surface:
            renderer = services.get("renderer")
            if renderer:
                # TileMap은 이미 월드 좌표계이므로, 카메라 오프셋만 적용하여 그림
                renderer.screen.blit(self.map_surface, (-renderer.camera.position.x, -renderer.camera.position.y))