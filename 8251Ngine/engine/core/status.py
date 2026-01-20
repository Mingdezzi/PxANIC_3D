import pygame
import math
import random
from engine.core.component import Component
from settings import TILE_SIZE, VISION_RADIUS, PHASE_SETTINGS, MAFIA_DETECT_RANGE

class StatusComponent(Component):
    def __init__(self, hp=100, ap=100, role="CITIZEN"):
        super().__init__()
        self.max_hp = hp
        self.hp = hp
        self.max_ap = ap
        self.ap = ap
        self.role = role
        self.emotions = {}
        self.shiver_offset = [0, 0]
        self.is_dead = False
        self.node = None

    def _on_added(self, node):
        self.node = node
        if hasattr(node, 'role'): self.role = node.role

    def update(self, dt, services, game_state):
        # 딕셔너리 안전 접근
        if not game_state or 'is_blackout' not in game_state:
            return

        if self.node and hasattr(self.node, 'hp'):
            self.hp = self.node.hp
            if self.hp <= 0:
                self.is_dead = True
                return

        self.update_emotions(game_state)
        self.apply_emotion_effects(game_state)

    def update_emotions(self, game_state):
        self.emotions = {}
        if self.is_dead: return

        # 1. HAPPINESS
        if self.hp >= 80 and self.ap >= 80:
            self.emotions['HAPPINESS'] = 1

        # 2. PAIN
        if self.hp <= 50:
            level = max(1, 5 - int(self.hp / 10))
            self.emotions['PAIN'] = min(5, level)

        # 3. FATIGUE
        if self.ap <= 50:
            level = max(1, 5 - int(self.ap / 10))
            self.emotions['FATIGUE'] = min(5, level)

        # 4. FEAR
        if game_state.get('is_blackout', False):
            self.emotions['FEAR'] = 1
        
        # 5. Distance Based
        phase = game_state.get('current_phase', "DAY")
        target_roles = []
        emotion_type = None

        if self.role == "MAFIA" and phase in ["NIGHT", "DAWN"]:
            target_roles = ["CITIZEN", "POLICE", "DOCTOR"]
            emotion_type = 'DOPAMINE'
        elif self.role == "POLICE" and phase in ["NIGHT", "DAWN"]:
            target_roles = ["MAFIA"]
            emotion_type = 'RAGE'
        elif self.role != "MAFIA" and phase in ["EVENING", "NIGHT", "DAWN"]:
            target_roles = ["MAFIA"]
            emotion_type = 'ANXIETY'

        if emotion_type and target_roles and 'all_entities' in game_state:
            min_dist = 999.0
            for entity in game_state['all_entities']:
                if entity == self.node: continue
                if hasattr(entity, 'role') and entity.role in target_roles:
                    dist = self.node.position.distance_to(entity.position)
                    if dist < min_dist: min_dist = dist
            
            if min_dist <= 30:
                level = max(1, 6 - int(min_dist / 5))
                self.emotions[emotion_type] = min(5, level)

        if not self.emotions: self.emotions['CALM'] = 1

    def apply_emotion_effects(self, game_state):
        fear = self.emotions.get('FEAR', 0)
        pain = self.emotions.get('PAIN', 0)
        anxiety = self.emotions.get('ANXIETY', 0)
        intensity = (fear * 1.5) + (pain >= 3) * 1.0 + (anxiety * 0.8)
        if intensity > 0:
            self.shiver_offset = [random.uniform(-intensity, intensity), random.uniform(-intensity, intensity)]
        else:
            self.shiver_offset = [0, 0]

    def get_vision_radius(self, base_radius, phase_settings, is_blackout, services):
        current_phase = services["time"].current_phase
        base_v = base_radius * phase_settings.get(current_phase, {}).get('vision_factor', 1.0)
        if 'FATIGUE' in self.emotions: base_v *= (1.0 - self.emotions['FATIGUE'] * 0.1)
        if 'FEAR' in self.emotions: base_v *= 0.5
        
        if current_phase == 'NIGHT':
            if self.role == 'POLICE' and getattr(self.node, 'device_on', False): return VISION_RADIUS['NIGHT_POLICE_FLASH']
            if self.role == 'MAFIA': return VISION_RADIUS['NIGHT_MAFIA']
            return VISION_RADIUS['NIGHT_CITIZEN']
        return max(1.0, base_v)