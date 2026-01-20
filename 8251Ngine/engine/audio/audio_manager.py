import pygame

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
