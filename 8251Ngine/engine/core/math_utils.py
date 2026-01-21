import math

# Engine Constants
TILE_WIDTH = 64
TILE_HEIGHT = 32
HEIGHT_SCALE = 32 

class IsoMath:
    @staticmethod
    def cart_to_iso(x, y, z=0):
        # 렌더링 좌표는 부드럽게 (float 유지)
        screen_x = (x - y) * (TILE_WIDTH / 2)
        screen_y = (x + y) * (TILE_HEIGHT / 2) - (z * HEIGHT_SCALE)
        return screen_x, screen_y

    @staticmethod
    def iso_to_cart(screen_x, screen_y):
        half_w = TILE_WIDTH / 2
        half_h = TILE_HEIGHT / 2
        cart_x = (screen_x / half_w + screen_y / half_h) / 2
        cart_y = (screen_y / half_h - screen_x / half_w) / 2
        return cart_x, cart_y

    @staticmethod
    def get_depth(x, y, z=0):
        """
        [수정] 소수점 좌표로 인한 깜빡임(Z-Fighting) 방지.
        좌표를 정수(int)로 변환하거나 올림/내림 처리하여 '타일 단위'로 깊이를 고정함.
        """
        # 정밀도 이슈 해결: 약간의 오차(epsilon)를 더하고 내림 처리
        ix = int(x + 0.5) 
        iy = int(y + 0.5)
        
        # 깊이는 정수 단위로 계단식으로 증가해야 깜빡이지 않음
        # z값(높이)은 같은 타일 내에서의 정렬을 위해 그대로 더함
        return (ix + iy) * 100 + z
