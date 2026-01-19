import pygame
import os

class SoundManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    def __init__(self):
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except:
                print("[SoundManager] Mixer Init Failed")
        
        self.sounds = {}
        self.music_volume = 0.3
        self.sfx_volume = 0.5
        self.current_bgm = None
        self._load_sounds()

    def _load_sounds(self):
        sfx_dir = "assets/sounds/sfx"
        if os.path.exists(sfx_dir):
            for f in os.listdir(sfx_dir):
                if f.endswith(".wav") or f.endswith(".ogg") or f.endswith(".mp3"):
                    key = os.path.splitext(f)[0].upper()
                    try:
                        sound = pygame.mixer.Sound(os.path.join(sfx_dir, f))
                        sound.set_volume(self.sfx_volume)
                        self.sounds[key] = sound
                    except Exception as e:
                        print(f"[SoundManager] Failed to load {f}: {e}")
        else:
            print("[SoundManager] SFX directory not found")

    def play_sfx(self, key, volume=None):
        if key in self.sounds:
            try:
                sound = self.sounds[key]
                if volume is not None:
                    # 일회성 볼륨 조절을 위해 별도 채널 사용하거나, 
                    # Sound 객체의 볼륨을 잠시 바꾸는 방식은 다른 재생에 영향을 줌.
                    # 여기서는 간단히 Sound 객체 볼륨을 설정하고 재생 (동시 재생 시 볼륨 간섭 있을 수 있음)
                    # 더 정교하게 하려면 Channel 객체를 받아 set_volume 해야 함.
                    sound.set_volume(min(1.0, max(0.0, volume * self.sfx_volume)))
                else:
                    sound.set_volume(self.sfx_volume)
                sound.play()
            except: pass

    def play_music(self, name):
        if self.current_bgm == name: return
        
        # Try multiple extensions
        extensions = ['.mp3', '.ogg', '.wav']
        bgm_path = None
        
        for ext in extensions:
            path = f"assets/sounds/bgm/{name}{ext}"
            if os.path.exists(path):
                bgm_path = path
                break
        
        if not bgm_path:
            # print(f"[SoundManager] BGM not found: {name} (Checked {extensions})")
            return

        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(self.music_volume)
            self.current_bgm = name
        except Exception as e:
            print(f"[SoundManager] BGM Error ({bgm_path}): {e}")

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_bgm = None
