import pygame
import math
from settings import SOUND_INFO # SOUND_INFO 임포트

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.bgm_volume = 0.5
        self.sfx_volume = 1.0

    def load_sound(self, name, path):
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except:
            print(f"Failed to load sound: {path}")

    def play_sfx(self, name):
        if name in self.sounds:
            sound = self.sounds[name]
            sound.set_volume(self.sfx_volume)
            sound.play()

    def play_spatial_sfx(self, name, listener_pos, sound_pos):
        if name not in self.sounds:
            return

        sound = self.sounds[name]
        
        # PxANIC!의 SOUND_INFO에서 base_rad를 가져옴
        base_radius = SOUND_INFO.get(name, {}).get('base_rad', 10) * 32 # TILE_SIZE 곱해서 픽셀 단위로 변환
        
        distance = math.hypot(listener_pos.x - sound_pos.x, listener_pos.y - sound_pos.y)
        
        # 거리에 따라 볼륨 조절 (base_radius 내에서는 풀 볼륨, 그 이상은 감소)
        if distance < base_radius:
            volume_factor = 1.0
        else:
            volume_factor = max(0.0, 1.0 - (distance - base_radius) / (base_radius * 2)) # base_radius의 2배 거리까지 감소
            
        sound.set_volume(self.sfx_volume * volume_factor)
        sound.play()

    def play_bgm(self, path, loop=-1):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.bgm_volume)
            pygame.mixer.music.play(loop)
        except:
            print(f"Failed to play BGM: {path}")

    def set_bgm_volume(self, volume):
        self.bgm_volume = volume
        pygame.mixer.music.set_volume(volume)

    def set_sfx_volume(self, volume):
        self.sfx_volume = volume
