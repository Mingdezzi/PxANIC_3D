import pygame

class Animation:
    def __init__(self, frames, frame_duration=0.1, loop=True):
        self.frames = frames # List of pygame.Surface
        self.frame_duration = frame_duration
        self.loop = loop

class AnimationPlayer:
    def __init__(self):
        self.animations = {}
        self.current_anim = None
        self.frame_index = 0
        self.timer = 0.0
        self.playing = False

    def add_animation(self, name, animation):
        self.animations[name] = animation

    def play(self, name):
        if self.current_anim == name: return
        self.current_anim = name
        self.frame_index = 0
        self.timer = 0.0
        self.playing = True

    def update(self, dt):
        if not self.playing or not self.current_anim: return
        
        anim = self.animations[self.current_anim]
        self.timer += dt
        
        if self.timer >= anim.frame_duration:
            self.timer = 0
            self.frame_index += 1
            
            if self.frame_index >= len(anim.frames):
                if anim.loop:
                    self.frame_index = 0
                else:
                    self.frame_index = len(anim.frames) - 1
                    self.playing = False

    def get_current_frame(self):
        if not self.current_anim: return None
        return self.animations[self.current_anim].frames[self.frame_index]
