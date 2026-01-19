import pygame
from settings import ITEMS
from systems.logger import GameLogger

class InventoryLogic:
    def __init__(self, player):
        self.p = player
        self.logger = GameLogger.get_instance()

    def use_item(self, item_key):
        if not self.p.alive: return False
        if self.p.inventory.get(item_key, 0) <= 0: return False

        used = False
        s_type = "CRUNCH"

        if item_key == 'TANGERINE':
            if self.p.hp < self.p.max_hp: self.p.hp = min(self.p.max_hp, self.p.hp + 2); used = True
        elif item_key == 'CHOCOBAR':
            if self.p.ap < self.p.max_ap: self.p.ap = min(self.p.max_ap, self.p.ap + 2); used = True
        elif item_key == 'TORTILLA':
            if self.p.hp < self.p.max_hp or self.p.ap < self.p.max_ap:
                self.p.hp = min(self.p.max_hp, self.p.hp + 3)
                self.p.ap = min(self.p.max_ap, self.p.ap + 3)
                used = True
        elif item_key == 'MEDKIT':
            if self.p.hp < self.p.max_hp: self.p.hp = self.p.max_hp; used = True
            s_type = "CLICK"

        elif item_key == 'ENERGY_DRINK':
            if not self.p.buffs['INFINITE_STAMINA']:
                self.p.hp = max(1, self.p.hp - 3)
                self.p.buffs['INFINITE_STAMINA'] = True
                used = True; s_type = "GULP"
        elif item_key == 'PEANUT_BUTTER':
            if not self.p.buffs['SILENT']: self.p.buffs['SILENT'] = True; used = True
        elif item_key == 'COFFEE':
            if not self.p.buffs['FAST_WORK']: self.p.buffs['FAST_WORK'] = True; used = True; s_type = "GULP"
        elif item_key == 'PAINKILLER':
            if not self.p.buffs['NO_PAIN']: self.p.buffs['NO_PAIN'] = True; used = True; s_type = "GULP"

        elif item_key == 'BATTERY':
            if self.p.device_battery < 100: self.p.device_battery = min(100, self.p.device_battery + 50); used = True; s_type = "CLICK"
        elif item_key == 'POWERBANK':
            if self.p.device_battery < 100:
                self.p.device_battery = 100
                self.p.powerbank_uses += 1
                if self.p.powerbank_uses >= 2:
                    self.p.powerbank_uses = 0
                    used = True
                else:
                    self.p.add_popup("Used once (1 left)", (100, 255, 100))
                    return ("Used once (1 left)", ("CLICK", self.p.rect.centerx, self.p.rect.centery, 3 * TILE_SIZE, self.p.role))
                s_type = "CLICK"

        if used:
            self.p.inventory[item_key] -= 1
            return ("Used " + ITEMS[item_key]['name'], (s_type, self.p.rect.centerx, self.p.rect.centery, 4 * TILE_SIZE, self.p.role))
        return False

    def pick_up_item(self):
        if not self.p.alive: return None
        if not hasattr(self.p.game.world, 'items'): return None # world에 items가 없으면 리턴

        nearby_items = []
        for item in self.p.game.world.items: # item 객체들이 world에 있다고 가정
            # [수정] Z축 일치 여부 확인
            if getattr(item, 'z_level', 0) != self.p.z_level:
                continue
                
            dist = math.hypot(item.x - self.p.rect.centerx, item.y - self.p.rect.centery)
            if dist < TILE_SIZE * 1.5: # 1.5 타일 반경 내 아이템
                nearby_items.append(item)
        
        if nearby_items:
            closest_item = min(nearby_items, key=lambda item: math.hypot(item.x - self.p.rect.centerx, item.y - self.p.rect.centery))
            self.p.inventory[closest_item.item_key] = self.p.inventory.get(closest_item.item_key, 0) + 1
            self.p.game.world.items.remove(closest_item)
            return f"Picked up {ITEMS[closest_item.item_key]['name']}!"
        return None

    def buy_item(self, item_key):
        if self.p.role == "SPECTATOR": return
        if item_key in ITEMS:
            p = ITEMS[item_key]['price']
            if self.p.coins >= p: 
                self.p.coins -= p; self.p.inventory[item_key] = self.p.inventory.get(item_key, 0) + 1; 
                self.logger.info("PLAYER", f"Bought {item_key}")
                return ("Bought " + ITEMS[item_key]['name'], ("KA-CHING", self.p.rect.centerx, self.p.rect.centery, 5 * TILE_SIZE, self.p.role))
            else: print("Not enough coins!")
