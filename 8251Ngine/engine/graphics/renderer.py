import pygame
from engine.graphics.camera import Camera
from engine.core.math_utils import IsoMath, TILE_HEIGHT
from engine.graphics.shadow_renderer import ShadowRenderer
from settings import ENABLE_SHADOWS, SHADOW_QUALITY, USE_CULLING

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.camera = Camera()
        self.render_queue = [] # 바닥과 물체 모두 임시 저장
        self.clip_rect = None 
        
        self.camera.update_viewport(screen.get_width(), screen.get_height())
        
        self._shadow_surf = None

    def _update_screen(self, screen):
        self.screen = screen
        self.camera.update_viewport(screen.get_width(), screen.get_height())

    def set_clip_rect(self, rect):
        self.clip_rect = rect

    def clear_queue(self):
        self.render_queue.clear()

    def submit(self, node):
        if hasattr(node, 'get_sprite'):
            sprite = node.get_sprite()
            if sprite:
                gpos = node.get_global_position()
                
                # [수정] 픽셀 위치 계산
                iso_x, iso_y = IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z)
                
                # [수정] 깊이 계산 (정수형으로 변환하여 깜빡임 방지)
                depth = IsoMath.get_depth(gpos.x, gpos.y, gpos.z)
                
                # 바닥 여부 확인 (높이가 0.1 미만이면 바닥 취급)
                is_floor = getattr(node, 'size_z', 0) < 0.1
                
                # 캐릭터(GameEntity/Player)는 size_z가 없어도 무조건 물체 레이어로 분류
                # GameEntity는 role을 가짐. NpcEntity도 GameEntity 상속받아 role 가짐.
                if hasattr(node, 'role') or hasattr(node, 'is_moving'): 
                    is_floor = False # 캐릭터나 움직이는 엔티티는 무조건 오브젝트로

                self.render_queue.append({
                    'is_floor': is_floor, # 레이어 구분을 위한 플래그
                    'depth': depth,
                    'sprite': sprite,
                    'pos': (iso_x, iso_y),
                    'scale': node.scale,
                    'node': node
                })

    def flush(self, services):
        self.camera.update()
        zoom = self.camera.zoom
        
        if self.clip_rect:
            self.screen.set_clip(self.clip_rect)

        # 1. 큐 분리 (바닥 vs 물체)
        floors = []
        objects = []
        
        for item in self.render_queue:
            if item['is_floor']:
                floors.append(item)
            else:
                objects.append(item)

        # [최적화] 그림자 처리 (물체만 생성, 바닥 위 & 물체 아래에 그려짐)
        if ENABLE_SHADOWS: # settings에서 ENABLE_SHADOWS 설정 확인
            self._render_shadows(services, objects) # _render_shadows는 항상 services와 objects를 받음

        # 2. 바닥 먼저 그리기 (배경) - 깊이 순 정렬
        floors.sort(key=lambda x: x['depth'])
        self._render_list(floors, zoom)

        # 3. 물체 그리기 (전경) - 바닥을 덮어씀
        objects.sort(key=lambda x: x['depth'])
        self._render_list(objects, zoom)

        self.screen.set_clip(None)

    def _render_shadows(self, services, objects):
        time_manager = services.get("time")
        # 밤이거나 그림자 설정 꺼짐이면 패스
        if not time_manager or time_manager.current_phase == 'NIGHT':
            return

        sw, sh = self.screen.get_size()
        scale_factor = 0.5 if SHADOW_QUALITY == 'LOW' else 1.0
        target_w, target_h = int(sw * scale_factor), int(sh * scale_factor)
        
        # 서피스 캐싱 (크기 변경시에만 재생성)
        if self._shadow_surf is None or self._shadow_surf.get_size() != (target_w, target_h):
            self._shadow_surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        
        self._shadow_surf.fill((0,0,0,0))
        sun_dir = time_manager.sun_direction
        
        for item in objects:
            # 화면 밖 컬링 (렌더링 전 처리)
            sx_raw, sy_raw = self.camera.world_to_screen(*item['pos'])
            # Larger buffer for shadow casting
            if not (-100 < sx_raw < sw + 100 and -100 < sy_raw < sh + 100): 
                continue
                
            ShadowRenderer.draw_directional_shadow(
                self._shadow_surf, self.camera, item['node'], sun_dir, scale=scale_factor
            )
        
        # [최적화] smoothscale 대신 scale 사용 (훨씬 빠름)
        if scale_factor != 1.0:
            full_shadow = pygame.transform.scale(self._shadow_surf, (sw, sh))
            self.screen.blit(full_shadow, (0, 0))
        else:
            self.screen.blit(self._shadow_surf, (0, 0))

    def _render_list(self, render_list, zoom):
        screen_rect = self.screen.get_rect() # 매 프레임 다시 얻기
        offset_y_base = TILE_HEIGHT 
        
        for item in render_list:
            sx, sy = self.camera.world_to_screen(*item['pos'])
            img = item['sprite']
            
            if zoom != 1.0:
                w = int(img.get_width() * zoom)
                h = int(img.get_height() * zoom)
                if w < 1 or h < 1: continue
                img = pygame.transform.scale(img, (w, h))
            
            offset_y = offset_y_base * zoom 
            rect = img.get_rect(midbottom=(sx, sy + offset_y))
            
            # 컬링
            if USE_CULLING:
                if not screen_rect.colliderect(rect):
                    continue
            
            self.screen.blit(img, rect)