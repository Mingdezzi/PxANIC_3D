import pygame
from engine.graphics.camera import Camera
from engine.core.math_utils import IsoMath, TILE_HEIGHT

from engine.graphics.shadow_renderer import ShadowRenderer

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.camera = Camera()
        self.render_queue = []
        self.clip_rect = None # [New] 렌더링 제한 구역
        
        self.camera.update_viewport(screen.get_width(), screen.get_height())

    def _update_screen(self, screen):
        self.screen = screen
        # 기본적으로는 전체 화면 사용, 에디터 등에서 update_viewport로 재조정 가능
        self.camera.update_viewport(screen.get_width(), screen.get_height())

    def set_clip_rect(self, rect):
        """[New] 렌더링이 허용된 영역을 설정합니다 (UI 침범 방지용)"""
        self.clip_rect = rect

    def clear_queue(self):
        self.render_queue.clear()

    def submit(self, node):
        if hasattr(node, 'get_sprite'):
            sprite = node.get_sprite()
            if sprite:
                gpos = node.get_global_position()
                iso_x, iso_y = IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z)
                depth = IsoMath.get_depth(gpos.x, gpos.y, gpos.z)
                
                self.render_queue.append({
                    'depth': depth,
                    'sprite': sprite,
                    'pos': (iso_x, iso_y),
                    'scale': node.scale,
                    'node': node
                })

    def flush(self, services):
        self.camera.update()
        zoom = self.camera.zoom
        
        # [New] 클리핑 적용 (타일이 UI를 덮지 않도록 설정)
        if self.clip_rect:
            self.screen.set_clip(self.clip_rect)

        # [Performance Optimized Shadow Pass]
        # 실시간 쉐도우 볼륨 계산은 매우 무거우므로 비활성화하고, 
        # 기본적인 방향성 그림자만 낮은 해상도에서 처리합니다.
        shadow_scale = 0.25 # 해상도를 더 낮춰서 렉 방지
        sw = int(self.screen.get_width() * shadow_scale)
        sh = int(self.screen.get_height() * shadow_scale)
        shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        
        time_manager = services.get("time")
        
        # 밤이 아닐 때만 방향성 그림자 그리기
        if time_manager and time_manager.current_phase != 'NIGHT':
            sun_dir = time_manager.sun_direction
            for item in self.render_queue:
                node = item['node']
                # 벽이나 사물(높이가 있는 것)만 그림자 생성
                if getattr(node, 'size_z', 0) > 0.1:
                    ShadowRenderer.draw_directional_shadow(shadow_surf, self.camera, node, sun_dir, scale=shadow_scale)
        
        # 쉐도우 볼륨(Shadow Volume) 로직 제거 (가장 큰 렉의 원인)

        full_shadow = pygame.transform.smoothscale(shadow_surf, self.screen.get_size())
        self.screen.blit(full_shadow, (0, 0))

        # [Render Pass]
        self.render_queue.sort(key=lambda x: x['depth'])
        
        for item in self.render_queue:
            sx, sy = self.camera.world_to_screen(*item['pos'])
            img = item['sprite']
            
            # Culling: 화면 밖의 객체는 건너뜀
            if zoom != 1.0:
                w = int(img.get_width() * zoom)
                h = int(img.get_height() * zoom)
                if w < 1 or h < 1: continue
                img = pygame.transform.scale(img, (w, h))
            
            offset_y = (TILE_HEIGHT) * zoom 
            rect = img.get_rect(midbottom=(sx, sy + offset_y))
            
            if self.screen.get_rect().colliderect(rect):
                self.screen.blit(img, rect)

        # [New] 클리핑 해제
        self.screen.set_clip(None)