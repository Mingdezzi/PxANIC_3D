from game.entities.projectiles.bullet import Projectile
import math

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
        target = self._find_target_in_range(attacker, 1.5, 90)
        if target:
            # Hit logic
            target.take_damage(50) # Assuming entities have take_damage
            return f"Hit {target.name}!"
        else:
            return "Missed swing."

    def _find_target_in_range(self, attacker, reach, angle_deg):
        # Placeholder for entity lookup
        # In single player, no other targets usually.
        return None
