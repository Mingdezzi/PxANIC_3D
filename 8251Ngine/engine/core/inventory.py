import pygame
from engine.core.component import Component

class Item:
    def __init__(self, id, name, desc, price=0, icon=None):
        self.id = id
        self.name = name
        self.desc = desc
        self.price = price
        self.icon = icon

# Global Item Database (Based on PxANIC-)
ITEM_DB = {
    'TANGERINE': Item('TANGERINE', '귤', 'HP +20', 3),
    'CHOCOBAR': Item('CHOCOBAR', '초코바', 'AP +20', 3),
    'MEDKIT': Item('MEDKIT', '구급키트', 'HP Full Recovery', 15),
    'BATTERY': Item('BATTERY', '건전지', 'Battery +50%', 3),
}

import json
import os

class InventoryComponent(Component):
    def __init__(self):
        super().__init__()
        self.items = {} # {item_key: count}
        self.coins = 0
        self.max_slots = 10
        self._item_data = self._load_item_data()

    def _load_item_data(self):
        # Assuming run from root
        try:
            path = os.path.join("game", "data", "items.json")
            if not os.path.exists(path):
                # Fallback path logic if needed
                path = os.path.join("8251Ngine", "game", "data", "items.json")
            
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Inventory] Failed to load items.json: {e}")
            return {}

    def get_item_info(self, item_key):
        return self._item_data.get(item_key, {})

    def add_item(self, item_key, count=1):
        if item_key not in self._item_data:
            print(f"[Inventory] Unknown item: {item_key}")
            return False
            
        if item_key in self.items:
            self.items[item_key] += count
        else:
            if len(self.items) >= self.max_slots:
                return False
            self.items[item_key] = count
        return True

    def remove_item(self, item_key, count=1):
        if item_key in self.items:
            if self.items[item_key] >= count:
                self.items[item_key] -= count
                if self.items[item_key] <= 0:
                    del self.items[item_key]
                return True
        return False

    def has_item(self, item_key, count=1):
        return self.items.get(item_key, 0) >= count

    def use_item(self, item_key, services):
        # self.node is the GameEntity instance
        p = self.node

        if not p.alive: return False
        if self.items.get(item_key, 0) <= 0: return False

        used = False
        # sound_type = "CRUNCH" # Placeholder, actual sounds from PxANIC! need to be mapped
        popup_msg = ""

        if item_key == 'TANGERINE':
            if p.hp < p.max_hp: p.hp = min(p.max_hp, p.hp + 20); used = True; popup_msg = "HP +20"
        elif item_key == 'CHOCOBAR':
            if p.ap < p.max_ap: p.ap = min(p.max_ap, p.ap + 20); used = True; popup_msg = "AP +20"
        elif item_key == 'TORTILLA':
            if p.hp < p.max_hp or p.ap < p.max_ap:
                p.hp = min(p.max_hp, p.hp + 30)
                p.ap = min(p.max_ap, p.ap + 30)
                used = True; popup_msg = "HP +30, AP +30"
        elif item_key == 'MEDKIT':
            if p.hp < p.max_hp: p.hp = p.max_hp; used = True; popup_msg = "HP Full!"

        elif item_key == 'ENERGY_DRINK':
            if not p.buffs.get('INFINITE_STAMINA', False):
                p.hp = max(1, p.hp - 3) # Energy drinks have a small health cost in PxANIC!
                p.buffs['INFINITE_STAMINA'] = True
                p.buff_timers['INFINITE_STAMINA'] = 30.0 # 30 seconds duration
                used = True; popup_msg = "Infinite Stamina! (HP -3)"
        elif item_key == 'PEANUT_BUTTER':
            if not p.buffs.get('SILENT', False): 
                p.buffs['SILENT'] = True
                p.buff_timers['SILENT'] = 60.0 # 60 seconds duration
                used = True; popup_msg = "Noise -30% (Buff)"
        elif item_key == 'COFFEE':
            if not p.buffs.get('FAST_WORK', False): 
                p.buffs['FAST_WORK'] = True
                p.buff_timers['FAST_WORK'] = 45.0 # 45 seconds duration
                used = True; popup_msg = "Job Speed x2 (Buff)"
        elif item_key == 'PAINKILLER':
            if not p.buffs.get('NO_PAIN', False): 
                p.buffs['NO_PAIN'] = True
                p.buff_timers['NO_PAIN'] = 60.0 # 60 seconds duration
                used = True; popup_msg = "Ignore Pain (Buff)"

        elif item_key == 'BATTERY':
            if p.device_battery < 100: p.device_battery = min(100, p.device_battery + 50); used = True; popup_msg = "Battery +50%"
        elif item_key == 'POWERBANK':
            if p.device_battery < 100:
                p.device_battery = 100
                p.powerbank_uses += 1
                if p.powerbank_uses >= 2:
                    p.powerbank_uses = 0 # Reset for next powerbank
                    used = True; popup_msg = "Battery Full! (Used Powerbank)"
                else:
                    services["popups"].add_popup("Used Powerbank (1 left)", p.position.x, p.position.y, 1.0)
                    return True # Indicate partial use
        
        elif item_key == 'KEY':
            # Key is used via ActionSystem on interaction, not directly from inventory
            # So, just indicate it's a usable item. Actual removal handled by ActionSystem.
            services["popups"].add_popup("열쇠 사용 준비", p.position.x, p.position.y, 0.5)
            return True # Not consumed here, ActionSystem will remove it
        elif item_key == 'MASTER_KEY':
            # Master Key also used via ActionSystem. Has limited uses.
            if p.buff_timers.get('MASTER_KEY_USES', 0) < 3: # Max 3 uses for master key
                p.buff_timers['MASTER_KEY_USES'] = p.buff_timers.get('MASTER_KEY_USES', 0) + 1
                services["popups"].add_popup(f"만능키 사용 준비 ({3 - p.buff_timers['MASTER_KEY_USES']}회 남음)", p.position.x, p.position.y, 0.5)
                return True
            else:
                services["popups"].add_popup("만능키 사용 횟수 초과!", p.position.x, p.position.y, 0.5, (255, 50, 50))
                return False

        # Add other item logics as needed (SMOKE_BOMB, ARMOR, POTION, TASER, TRAP)

        if used:
            self.remove_item(item_key, 1)
            services["popups"].add_popup(f"{self._item_data[item_key]['name']} 사용! ({popup_msg})", p.position.x, p.position.y, 1.0)
            return True
        return False

    def buy_item(self, item_key, services):
        # p = self.node
        # if p.role == "SPECTATOR": return
        # if item_key in self._item_data:
        #     price = self._item_data[item_key]['price']
        #     if self.coins >= price: 
        #         self.coins -= price; self.add_item(item_key, 1)
        #         services["popups"].add_popup(f"{self._item_data[item_key]['name']} 구매! (-{price} 코인)", p.position.x, p.position.y, 1.0)
        #     else: 
        #         services["popups"].add_popup("코인 부족!", p.position.x, p.position.y, 1.0)
        # Currently, buying is not hooked up, so just return None
        return None
