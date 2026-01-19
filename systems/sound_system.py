import math
import random
from settings import SOUND_INFO, TILE_SIZE
from systems.effects import VisualSound, SoundDirectionIndicator
from managers.sound_manager import SoundManager

class SoundSystem:
    def __init__(self, game_world):
        self.world = game_world
        self.sound_manager = SoundManager.get_instance()

    def process_sound_effect(self, f, player):
        """
        사운드 이펙트를 처리하고 시각적 효과를 생성합니다.
        f: (s_type, fx_x, fx_y, rad, source_role) 튜플
        player: 현재 플레이어 엔티티 (청자)
        """
        if len(f) == 5:
            s_type, fx_x, fx_y, rad, source_role = f
        else:
            s_type, fx_x, fx_y, rad = f
            source_role = "UNKNOWN"

        # --- [Play Real Sound] ---
        # Calculate distance for volume attenuation
        # Use player's rect center directly
        dist = math.sqrt((player.rect.centerx - fx_x)**2 + (player.rect.centery - fx_y)**2)
        
        # Max audible distance (e.g., 20 tiles)
        max_dist = TILE_SIZE * 20
        
        # Always play UI-like sounds or self-sounds with full volume if very close
        if dist < max_dist:
            vol = 1.0 - (dist / max_dist)
            # Ensure volume is not too low
            vol = max(0.1, vol)
            
            # Map sound types to file keys if needed (or assume 1:1 mapping)
            # Current keys in generated: FOOTSTEP, RUN, GUNSHOT, etc.
            # s_type from game logic: 'FOOTSTEP', 'BANG!' -> 'EXPLOSION'?, 'GULP' -> 'DRINK'
            
            sound_key = s_type
            if s_type == 'BANG!': sound_key = 'EXPLOSION' # Or HIT
            elif s_type == 'GULP': sound_key = 'DRINK'
            elif s_type == 'CRUNCH': sound_key = 'EAT'
            elif s_type == 'KA-CHING': sound_key = 'COIN_GET'
            elif s_type == 'BEEP': sound_key = 'CLICK' # or ERROR
            elif s_type == 'THUD': sound_key = 'RUN' # Heavy step
            elif s_type == 'HEARTBEAT': sound_key = None # No sound for heartbeat yet
            
            if sound_key:
                self.sound_manager.play_sfx(sound_key, vol)

        # --- [Visual Effects Logic] ---
        if dist < rad * 1.5:
            info = SOUND_INFO.get(s_type, {'base_rad': 5, 'color': (200, 200, 200)})
            base_color = info['color']
            
            my_role = player.role
            importance = 1.0
            final_color = base_color
            shake = False
            blink = False
            
            # --- [Listener-Speaker Importance Logic] ---
            if my_role in ["CITIZEN", "DOCTOR"]:
                if source_role == "MAFIA":
                    importance = 2.0
                    final_color = (255, 50, 50) # Red (Danger)
                    shake = True 
                    if s_type in ["BANG!", "SLASH", "SCREAM", "GUNSHOT"]: importance = 2.5
                elif source_role == "POLICE":
                    importance = 1.5
                    final_color = (50, 150, 255) # Blue (Rescue)
            
            elif my_role == "MAFIA":
                if source_role == "POLICE":
                    importance = 2.5
                    final_color = (200, 50, 255) # Purple (Warning)
                    blink = True 
                    if s_type == "SIREN": importance = 3.0
                elif source_role in ["CITIZEN", "DOCTOR"]:
                    importance = 1.5
                    final_color = (255, 255, 100) # Yellow (Prey)
            
            elif my_role == "POLICE":
                if source_role == "MAFIA":
                    importance = 2.0
                    final_color = (255, 150, 0) # Orange (Target)
                elif source_role in ["CITIZEN", "DOCTOR"]:
                    importance = 0.6 # Low importance (Noise)

            if s_type in ["SIREN", "BOOM"]: 
                importance = 2.5
                blink = True

            # --- [Size Calculation] ---
            # Distance Falloff: Closer is bigger
            dist_factor = 1.0 - (dist / (rad * 1.5))
            dist_factor = max(0.2, dist_factor)
            
            # Base Scale (based on radius relative to footstep)
            base_scale = (rad / (6 * TILE_SIZE))
            
            # Final Scale
            final_scale = base_scale * importance * dist_factor
            final_scale = max(0.5, min(2.5, final_scale))

            self.world.effects.append(VisualSound(fx_x, fx_y, s_type, final_color, size_scale=final_scale, shake=shake, blink=blink))
            self.world.indicators.append(SoundDirectionIndicator(fx_x, fx_y))
