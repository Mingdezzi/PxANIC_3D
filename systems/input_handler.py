import pygame

class InputHandler:
    def __init__(self, game=None):
        self.game = game
        self.mouse_pos = (0, 0)
        self.mouse_buttons = [False, False, False]
        self.keys = {}
        # [추가] 마우스 휠 값 저장용
        self.scroll_dy = 0 

    def update(self):
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_buttons = pygame.mouse.get_pressed()
        # 매 프레임 휠 값 초기화 (이벤트로만 받으므로)
        self.scroll_dy = 0

    # [추가] 이 메서드가 없어서 에러가 발생했습니다. 추가해주세요。
    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_dy = event.y
            # 필요하다면 여기서 카메라 줌 조절 등을 바로 호출할 수도 있음
            # if self.game and self.game.state_machine.current_state:
            #     pass

    def is_key_pressed(self, key_constant):
        # [안전장치] 키 입력이 없을 경우 False 반환
        if self.keys and len(self.keys) > 0: 
            try:
                return self.keys[key_constant]
            except IndexError: 
                return False
        return False

    def is_mouse_pressed(self, button_index):
        # 0: Left, 1: Middle, 2: Right
        # [안전장치] 버튼 인덱스 범위를 벗어날 경우 False 반환
        if 0 <= button_index < len(self.mouse_buttons):
            return self.mouse_buttons[button_index]
        return False

    def get_mouse_pos(self):
        return self.mouse_pos