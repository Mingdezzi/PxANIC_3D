import pygame
from engine.core.node import Node
from engine.graphics.animation import AnimationPlayer

class AnimatedSprite(Node):
    def __init__(self, name="AnimatedSprite"):
        super().__init__(name)
        self.anim_player = AnimationPlayer()
        self.offset_y = 0
        self.offset_x = 0
        self.flip_h = False # Horizontal flip

    def update(self, dt, services, game_state):
        self.anim_player.update(dt)
        super().update(dt, services, game_state)

    def get_sprite(self):
        frame = self.anim_player.get_current_frame()
        if frame:
            if self.flip_h:
                return pygame.transform.flip(frame, True, False)
            return frame
        return None
