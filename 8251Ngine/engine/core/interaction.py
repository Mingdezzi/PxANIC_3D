import pygame
import time
import math # math 임포트 추가

class NoiseEvent:
    def __init__(self, x, y, radius, color=(200, 200, 200), duration=1.0):
        self.x, self.y = x, y
        self.radius = radius
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.alpha = 150

    def update(self):
        elapsed = time.time() - self.start_time
        progress = elapsed / self.duration
        if progress > 1.0:
            return False
        
        # Fade out alpha
        self.alpha = int(150 * (1.0 - progress))
        return True

class SoundIndicator:
    def __init__(self, listener_pos, sound_pos, color=(255, 255, 255), duration=1.0):
        self.listener_pos = listener_pos # PxANIC!에서는 player.rect.center를 사용했지만, 여기서는 Vector2
        self.sound_pos = sound_pos       # Vector2
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.alpha = 255

    def update(self):
        elapsed = time.time() - self.start_time
        progress = elapsed / self.duration
        if progress > 1.0:
            return False
        
        # Fade out alpha
        self.alpha = int(255 * (1.0 - progress))
        return True

    def draw(self, screen, camera):
        # PxANIC!의 SoundDirectionIndicator는 화면 중앙에서 소리 방향으로 화살표를 그림
        # 여기서는 화면 중앙 (screen.get_width() // 2, screen.get_height() // 2)을 기준으로 그림
        center_x, center_y = screen.get_width() // 2, screen.get_height() // 2
        
        # 사운드 -> 리스너 벡터 (월드 좌표)
        vec_to_listener = self.listener_pos - self.sound_pos
        
        # 방향 (월드 좌표계)
        if vec_to_listener.length_squared() == 0: # 같은 위치면 방향 없음
            return
        direction_vec = vec_to_listener.normalize()
        
        # 화면 가장자리에 그리기 위한 계산
        indicator_size = 20 # 화살표 크기
        padding = 10        # 화면 가장자리로부터의 간격
        
        # PxANIC!는 player.rect를 기준으로 그림. 여기서는 player.position.x, player.position.y를 기준으로 그림.
        # 즉, 리스너 위치를 Player의 월드 좌표로 사용해야 함.
        
        # 각도 계산
        angle = math.atan2(direction_vec.y, direction_vec.x)
        
        # 화면 중앙에서 바깥으로 뻗어나가는 방향 벡터
        draw_direction = pygame.math.Vector2(math.cos(angle), math.sin(angle))
        
        # 화면 가장자리에 위치시키기 (간단한 방법: 일정 거리만큼 떨어진 곳)
        indicator_center_x = center_x + draw_direction.x * (center_x - padding - indicator_size // 2)
        indicator_center_y = center_y + draw_direction.y * (center_y - padding - indicator_size // 2)
        
        # 색상에 투명도 적용
        draw_color = (*self.color[:3], self.alpha)
        
        # 원형 외곽선
        pygame.draw.circle(screen, draw_color, (int(indicator_center_x), int(indicator_center_y)), indicator_size, 2)
        
        # 방향을 나타내는 작은 선
        line_start = pygame.math.Vector2(indicator_center_x, indicator_center_y) - draw_direction * (indicator_size - 5)
        line_end = pygame.math.Vector2(indicator_center_x, indicator_center_y) + draw_direction * (indicator_size - 5)
        pygame.draw.line(screen, draw_color, line_start, line_end, 2)
        
        # 화살촉 (간단한 삼각형)
        arrow_len = indicator_size // 2
        arrow_base = pygame.math.Vector2(indicator_center_x, indicator_center_y) + draw_direction * indicator_size
        
        # 화살촉 양쪽 끝
        # draw_direction과 수직인 벡터를 찾아서 사용
        perp_vec = pygame.math.Vector2(-draw_direction.y, draw_direction.x)
        point1 = arrow_base + perp_vec * (arrow_len / 2)
        point2 = arrow_base - perp_vec * (arrow_len / 2)
        
        # 화살촉 중앙점 (direction_vec 반대 방향)
        point3 = pygame.math.Vector2(indicator_center_x, indicator_center_y) - draw_direction * (indicator_size - 5 + arrow_len)
        
        # pygame.draw.polygon(screen, draw_color, [point1, point2, point3])
        # 더 간단한 화살표: 삼각형이 아니라 꺾인 선으로
        line_point1 = pygame.math.Vector2(indicator_center_x, indicator_center_y) + draw_direction * (indicator_size - 5) + perp_vec * (arrow_len / 2)
        line_point2 = pygame.math.Vector2(indicator_center_x, indicator_center_y) + draw_direction * (indicator_size - 5) - perp_vec * (arrow_len / 2)
        
        pygame.draw.line(screen, draw_color, line_point1, line_end, 2)
        pygame.draw.line(screen, draw_color, line_point2, line_end, 2)
        
        # PxANIC!는 player.rect를 기준으로 그림. 여기서는 player.position.x, player.position.y를 기준으로 그림.
        # 즉, 리스너 위치를 Player의 월드 좌표로 사용해야 함.

class InteractionManager:
    def __init__(self):
        self.noises = []
        self.interactables = []
        self.sound_indicators = [] # SoundDirectionIndicator 리스트 추가

    def emit_noise(self, x, y, radius, color=(200, 200, 200), duration=1.0): # duration 추가
        self.noises.append(NoiseEvent(x, y, radius, color, duration))

    def register_interactable(self, node):
        if node not in self.interactables:
            self.interactables.append(node)

    def add_sound_indicator(self, listener_pos, sound_pos, color=(255, 255, 255), duration=1.0):
        # 이미 같은 방향에 비슷한 인디케이터가 있으면 추가하지 않거나 갱신하는 로직 필요
        self.sound_indicators.append(SoundIndicator(listener_pos, sound_pos, color, duration))

    def update(self):
        self.noises = [n for n in self.noises if n.update()]
        self.sound_indicators = [i for i in self.sound_indicators if i.update()] # 인디케이터 업데이트

    def draw(self, screen, camera):
        from engine.core.math_utils import IsoMath
        for n in self.noises:
            # World to Screen
            ix, iy = IsoMath.cart_to_iso(n.x, n.y, 0)
            sx, sy = camera.world_to_screen(ix, iy)
            
            # Draw expanding ring
            elapsed = time.time() - n.start_time
            curr_rad = int(n.radius * (elapsed / n.duration) * 32) # Scale to pixels
            
            s = pygame.Surface((curr_rad * 2, curr_rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*n.color, n.alpha), (curr_rad, curr_rad), curr_rad, 2)
            screen.blit(s, (sx - curr_rad, sy - curr_rad))
        
        # SoundDirectionIndicator 그리기
        for indicator in self.sound_indicators:
            indicator.draw(screen, camera)