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
            # PxANIC! original has a separate counter (player.powerbank_uses or player.master_key_uses)
            if p.buff_timers.get('MASTER_KEY_USES', 0) < 3: # Max 3 uses for master key
                p.buff_timers['MASTER_KEY_USES'] = p.buff_timers.get('MASTER_KEY_USES', 0) + 1
                services["popups"].add_popup(f"만능키 사용 준비 ({3 - p.buff_timers['MASTER_KEY_USES']}회 남음)", p.position.x, p.position.y, 0.5)
                return True
            else:
                services["popups"].add_popup("만능키 사용 횟수 초과!", p.position.x, p.position.y, 0.5, (255, 50, 50))
                return False

        elif item_key == 'SMOKE_BOMB':
            # Original PxANIC!: InteractionManager.emit_smoke
            services["interaction"].emit_smoke(p.position.x, p.position.y, 200, 5.0) # radius 200px, 5s duration
            used = True; popup_msg = "연막탄 사용!"
        elif item_key == 'ARMOR':
            # Original PxANIC!: Blocks 1 attack. Buff is set.
            if not p.buffs.get('ARMOR', False):
                p.buffs['ARMOR'] = True
                used = True; popup_msg = "방탄복 착용! (1회 방어)"
            else:
                services["popups"].add_popup("이미 착용 중!", p.position.x, p.position.y, 0.5)
                return False
        elif item_key == 'POTION':
            # Original PxANIC!: Revive next morning
            if not p.alive and p.hp <= 0: # Only if dead
                p.buffs['REVIVE_NEXT_MORNING'] = True
                used = True; popup_msg = "소생약 사용! (다음 날 아침 부활)"
            else:
                services["popups"].add_popup("죽지 않았습니다.", p.position.x, p.position.y, 0.5)
                return False
        elif item_key == 'TASER':
            # Original PxANIC!: Stun enemy for 3s (1 use). This is done in do_attack.
            # If used from inventory, it prepares the taser as a buff.
            # For simplicity, we'll make it a temporary buff that enables a special attack.
            if not p.buffs.get('TASER_READY', False):
                p.buffs['TASER_READY'] = True
                p.buff_timers['TASER_READY'] = 30.0 # Ready for 30s, or 1 use
                used = True; popup_msg = "테이저건 장전!"
            else:
                services["popups"].add_popup("이미 장전됨!", p.position.x, p.position.y, 0.5)
                return False
        elif item_key == 'TRAP':
            # Original PxANIC!: Place trap. Requires TrapSystem.
            # Temporarily, just indicate placement. Actual trap system needed.
            services["popups"].add_popup("함정 설치 (미구현)", p.position.x, p.position.y, 1.0, (255, 150, 50))
            # TrapSystem.place_trap(p.position.x, p.position.y, player_id=p.client_id) 
            used = True; popup_msg = "함정 설치!"

        if used:
            self.remove_item(item_key, 1)
            services["popups"].add_popup(f"{self._item_data[item_key]['name']} 사용! ({popup_msg})", p.position.x, p.position.y, 1.0)
            return True
        return False

    def buy_item(self, item_key, services):
        p = self.node
        if p.status.role == "SPECTATOR": return "Spectators cannot buy." # 관전자 구매 불가
        
        item_info = self.get_item_info(item_key)
        if not item_info:
            return "Item not found."
        
        price = item_info.get('price', 0)
        if self.coins < price:
            services["popups"].add_popup("코인 부족!", p.position.x, p.position.y, 1.0, (255, 50, 50))
            return "Not enough coins."
            
        self.coins -= price
        self.add_item(item_key, 1) # 1개 구매
        
        services["popups"].add_popup(f"{item_info['name']} 구매! (-{price} 코인)", p.position.x, p.position.y, 1.0, (100, 255, 100))
        return f"Purchased {item_info['name']} for {price} coins."
