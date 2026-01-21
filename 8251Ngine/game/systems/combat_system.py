from game.entities.projectiles.bullet import Projectile
import math
from settings import TILE_SIZE # TILE_SIZE 임포트

class CombatSystem:
    def __init__(self, scene):
        self.scene = scene
    
    def handle_attack(self, attacker, attack_type="MELEE"):
        # For now, single player means shooting at nothing or walls
        # If multiplayer, we check entity intersection
        
        if attack_type == "RANGED": # Police/Gun
            return self._fire_gun(attacker)
        elif attack_type == "MELEE": # Mafia/Knife
            return self._melee_attack(attacker)
        
        return None

    def _fire_gun(self, attacker):
        # Fire in facing direction
        dx, dy = attacker.facing_direction.x, attacker.facing_direction.y
        angle = math.atan2(dy, dx)
        
        # Spawn Projectile
        bullet = Projectile(attacker.position.x, attacker.position.y, angle, owner_id=attacker.name)
        self.scene.add_child(bullet)
        
        # Sound/Event
        return "GUNSHOT"

    def _melee_attack(self, attacker):
        # Check range 1.5
        target = self._find_target_in_range(attacker, 1.5, 90) # 1.5 타일 반경, 90도 시야각 (미사용)
        if target:
            # Hit logic
            target.take_damage(50, self.scene.services) # Assuming entities have take_damage and need services
            return f"Hit {target.name}!"
        else:
            return "Missed swing."

    def _find_target_in_range(self, attacker, reach, angle_deg):
        possible_targets = [self.scene.player] + list(self.scene.other_players.values()) + self.scene.npcs # 로컬 NPC도 대상에 포함
        
        targets_in_range = []
        for target in possible_targets:
            if target == attacker: # 자신은 제외
                continue
            if not target.status.alive: # 죽은 대상 제외
                continue

            dist = attacker.position.distance_to(target.position)
            if dist <= reach * TILE_SIZE: # TILE_SIZE 기준으로 거리 계산
                # 시야각 내 대상만 선택하는 로직 추가
                if angle_deg > 0: # angle_deg가 0보다 클 때만 시야각 검사
                    # 공격자의 정면 방향 벡터
                    attacker_dir = attacker.facing_direction.normalize()
                    
                    # 공격자 -> 타겟 벡터
                    target_vec = (target.position - attacker.position).normalize()
                    
                    # 두 벡터 간의 내적 계산
                    dot_product = attacker_dir.dot(target_vec)
                    
                    # 각도 계산 (라디안 -> 도)
                    angle_between = math.degrees(math.acos(max(-1, min(1, dot_product)))) # 내적 오차 보정
                    
                    if angle_between <= angle_deg / 2: # 시야각 절반 내에 있는지 확인
                        targets_in_range.append((dist, target))
                else: # angle_deg가 0이면 시야각 검사 없이 범위 내 모든 대상 포함
                    targets_in_range.append((dist, target))
        
        if targets_in_range:
            targets_in_range.sort(key=lambda x: x[0]) # 거리가 가까운 순으로 정렬
            return targets_in_range[0][1] # 가장 가까운 대상 반환
        return None
