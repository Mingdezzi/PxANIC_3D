import pygame

class InputManager:
    def __init__(self):
        self._actions = {
            "move_left": [pygame.K_LEFT, pygame.K_a],
            "move_right": [pygame.K_RIGHT, pygame.K_d],
            "move_up": [pygame.K_UP, pygame.K_w],
            "move_down": [pygame.K_DOWN, pygame.K_s],
            "jump": [pygame.K_SPACE],
            "run": [pygame.K_LSHIFT, pygame.K_RSHIFT],
            "crouch": [pygame.K_LCTRL, pygame.K_RCTRL],
            "toggle_camera": [pygame.K_c],
            "interact": [pygame.K_e],
            "inventory": [pygame.K_i],
            "map": [pygame.K_m],
            "attack": [pygame.K_x, pygame.K_z],
            "toggle_flashlight": [pygame.K_f],
        }
        
        # Add item usage actions dynamically from settings
        from settings import ITEMS # Import ITEMS here to avoid circular dependency on first load
        for item_key, item_info in ITEMS.items():
            if item_info.get('key'):
                action_name = f"item_{item_info['key']}"
                if action_name not in self._actions: # Prevent re-adding if already defined
                    self._actions[action_name] = [item_info['key']]

        self._pressed_keys = None
        self._prev_pressed_keys = None

    def update(self):
        self._prev_pressed_keys = self._pressed_keys
        self._pressed_keys = pygame.key.get_pressed()

    def is_action_pressed(self, action_name):
        if action_name not in self._actions: return False
        for key in self._actions[action_name]:
            if self._pressed_keys and self._pressed_keys[key]:
                return True
        return False

    def is_action_just_pressed(self, action_name):
        if action_name not in self._actions: return False
        for key in self._actions[action_name]:
            is_pressed_now = self._pressed_keys and self._pressed_keys[key]
            is_pressed_before = self._prev_pressed_keys and self._prev_pressed_keys[key]
            if is_pressed_now and not is_pressed_before:
                return True
        return False

    def get_vector(self, left, right, up, down):
        x, y = 0, 0
        if self.is_action_pressed(right): x += 1
        if self.is_action_pressed(left): x -= 1
        if self.is_action_pressed(down): y += 1
        if self.is_action_pressed(up): y -= 1
        return x, y
    
    def get_mouse_grid_pos(self, camera):
        from engine.core.math_utils import IsoMath
        mx, my = pygame.mouse.get_pos()
        wx = (mx - camera.offset.x) / camera.zoom + camera.position.x
        wy = (my - camera.offset.y) / camera.zoom + camera.position.y
        cart_pos = IsoMath.iso_to_cart(wx, wy)
        return pygame.math.Vector2(cart_pos[0], cart_pos[1])
