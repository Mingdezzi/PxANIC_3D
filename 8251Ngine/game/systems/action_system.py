import random
from engine.core.math_utils import IsoMath
from engine.assets.tile_engine import TileEngine
from settings import VENDING_MACHINE_TID # VENDING_MACHINE_TID 임포트

class ActionSystem:
    def __init__(self, scene):
        self.scene = scene
        self.collision_world = scene.collision_world
        
        # Tile ID Mapping based on PxANIC! logic
        # 531xxxx: Open, 532xxxx: Closed, 5323xxx: Locked
        # Mapping: Closed <-> Open
        self.DOOR_MAP = {
            # Closed -> Open
            5321008: 5310002, # Glass
            5321206: 5310000, # Wood
            5321207: 5310001, # Iron
            5321009: 5310003, # Prison
            5321010: 5310004, # Lab
            
            # Open -> Closed (Revert)
            5310002: 5321008,
            5310000: 5321206,
            5310001: 5321207,
            5310003: 5321009,
            5310004: 5321010,
        }
        
        # Locked Doors (Requires Key/Lockpick - Future implementation)
        self.LOCKED_DOORS = [5323220, 5323221, 5323022, 5323023, 5323024]
        
        # Chests
        self.CHEST_CLOSED = 5321025
        self.CHEST_OPEN = 5310025
        
        # Work Sequences (From Settings)
        # Simplified: Just key tiles to work on
        self.WORK_TILES = {
            'FARMER': [9312000, 9312001, 9312002], # Fields
            'MINER': [9322004, 9322005, 9322006],  # Ore/Furnace
            'FISHER': [9312003, 9322007, 8320205], # Water/Cutting Board/Fridge
            'DOCTOR': [9322008, 9322009, 9322011], # Lab Equipment
        }

    def handle_interact(self, player, interact_mode='short'):
        # 1. Get Target Tile Coords
        # Use simple grid check based on direction
        # Fix: Manually add components to avoid Vector3 + Vector2 error
        tx = int(round(player.position.x + player.facing_direction.x))
        ty = int(round(player.position.y + player.facing_direction.y))
        
        # 2. Find Block at (tx, ty)
        # Assuming scene has a grid or we iterate children (Optimization needed for large worlds, but fine for now)
        target_block = self._find_block_at(tx, ty)
        
        if not target_block:
            return "Nothing there."
            
        tid = int(target_block.tile_id) if target_block.tile_id else 0
        
        # --- Work Logic ---
        job = player.sub_role if player.role == 'CITIZEN' else player.role
        minigame_manager = self.scene.services["minigame"]
        
        if job in self.WORK_TILES and not minigame_manager.is_minigame_active():
            if tid in self.WORK_TILES[job]:
                import random # Local import for random
                from game.systems.minigames.mashing_minigame import MashingMinigame
                from game.systems.minigames.timing_minigame import TimingMinigame
                from game.systems.minigames.command_minigame import CommandMinigame
                from game.systems.minigames.circle_minigame import CircleMinigame
                from game.systems.minigames.memory_minigame import MemoryMinigame
                from game.systems.minigames.lockpick_minigame import LockpickMinigame
                from game.systems.minigames.frequency_minigame import FrequencyMinigame
                
                # Define callbacks
                def on_success():
                    if hasattr(player, 'inventory'):
                        player.inventory.coins += 5
                        self.scene.services["popups"].add_popup(f"{job} 작업 성공! (+5 코인)", player.position.x, player.position.y, 1.5)
                        # Optional: Advance work sequence, change tile appearance
                
                def on_fail():
                    player.hp = max(1, player.hp - 10) # Example penalty
                    self.scene.services["popups"].add_popup(f"{job} 작업 실패! (HP -10)", player.position.x, player.position.y, 1.5, (255, 50, 50))
                
                # Randomly choose a minigame for now (Mashing, Timing, Wiring, Command, Circle, Memory, Lockpick, Frequency)
                chosen_minigame_class = random.choice([MashingMinigame, TimingMinigame, WiringMinigame, CommandMinigame, CircleMinigame, MemoryMinigame, LockpickMinigame, FrequencyMinigame])
                
                if chosen_minigame_class == MashingMinigame:
                    minigame_manager.start_minigame(MashingMinigame(duration=3.0, target_mashes=15), on_success, on_fail)
                    return "미니게임 시작: 연타!"
                elif chosen_minigame_class == TimingMinigame:
                    minigame_manager.start_minigame(TimingMinigame(duration=4.0), on_success, on_fail)
                    return "미니게임 시작: 타이밍 맞추기!"
                elif chosen_minigame_class == WiringMinigame:
                    minigame_manager.start_minigame(WiringMinigame(duration=10.0, num_wires=4), on_success, on_fail)
                    return "미니게임 시작: 전선 연결!"
                elif chosen_minigame_class == CommandMinigame:
                    minigame_manager.start_minigame(CommandMinigame(duration=5.0, sequence_length=4), on_success, on_fail)
                    return "미니게임 시작: 커맨드 입력!"
                elif chosen_minigame_class == CircleMinigame:
                    minigame_manager.start_minigame(CircleMinigame(duration=5.0), on_success, on_fail)
                    return "미니게임 시작: 원형 타이밍!"
                elif chosen_minigame_class == MemoryMinigame:
                    minigame_manager.start_minigame(MemoryMinigame(duration=15.0, grid_size=3), on_success, on_fail)
                    return "미니게임 시작: 숫자 기억!"
                elif chosen_minigame_class == LockpickMinigame:
                    minigame_manager.start_minigame(LockpickMinigame(duration=15.0, num_pins=3), on_success, on_fail)
                    return "미니게임 시작: 자물쇠 따기!"
                elif chosen_minigame_class == FrequencyMinigame:
                    minigame_manager.start_minigame(FrequencyMinigame(duration=10.0, target_hold_time=3.0), on_success, on_fail)
                    return "미니게임 시작: 주파수 맞추기!"
            elif tid in [t for sublist in self.WORK_TILES.values() for t in sublist]:
                return "내 직업의 작업이 아닙니다."
        
        # --- Doors ---
        if tid in self.DOOR_MAP:
            new_tid = self.DOOR_MAP[tid]
            target_block.set_tile_id(new_tid)
            
            # Update Collision
            is_open = str(new_tid).startswith("531")
            if is_open:
                self.collision_world.remove_static(target_block)
            else:
                self.collision_world.add_static(target_block)
                
            return "Door " + ("Opened" if is_open else "Closed")
            
        elif tid in self.LOCKED_DOORS: # Locked door interaction
            player_inventory = player.inventory
            minigame_manager = self.scene.services["minigame"]

            # Attempt to use Master Key first
            if player_inventory.has_item('MASTER_KEY') and player.buff_timers.get('MASTER_KEY_USES', 0) < 3:
                # Unlock door directly
                open_tid = None
                if tid == 5323220: open_tid = 5310000 # Wood Locked -> Wood Open
                elif tid == 5323221: open_tid = 5310001 # Iron Locked -> Iron Open
                elif tid == 5323022: open_tid = 5310002 # Glass Locked -> Glass Open
                elif tid == 5323023: open_tid = 5310003 # Prison Locked -> Prison Open
                elif tid == 5323024: open_tid = 5310004 # Lab Locked -> Lab Open
                
                if open_tid: 
                    target_block.set_tile_id(open_tid)
                    self.collision_world.remove_static(target_block)
                    player.buff_timers['MASTER_KEY_USES'] = player.buff_timers.get('MASTER_KEY_USES', 0) + 1 # Increment use count
                    self.scene.services["popups"].add_popup(f"만능키 사용! ({3 - player.buff_timers['MASTER_KEY_USES']}회 남음)", player.position.x, player.position.y, 1.5)
                    return f"Unlocked with Master Key!"

            # If no Master Key or uses exhausted, attempt to use regular Key
            elif player_inventory.has_item('KEY'):
                # Unlock door directly
                open_tid = None
                if tid == 5323220: open_tid = 5310000 # Wood Locked -> Wood Open
                elif tid == 5323221: open_tid = 5310001 # Iron Locked -> Iron Open
                elif tid == 5323022: open_tid = 5310002 # Glass Locked -> Glass Open
                elif tid == 5323023: open_tid = 5310003 # Prison Locked -> Prison Open
                elif tid == 5323024: open_tid = 5310004 # Lab Locked -> Lab Open
                
                if open_tid: 
                    target_block.set_tile_id(open_tid)
                    self.collision_world.remove_static(target_block)
                    player_inventory.remove_item('KEY', 1) # Consume the key
                    self.scene.services["popups"].add_popup("열쇠 사용!", player.position.x, player.position.y, 1.5)
                    return f"Unlocked with Key!"

            # If no keys, proceed with Lockpick Minigame (existing logic)
            from game.systems.minigames.lockpick_minigame import LockpickMinigame
            # Define callbacks for lockpicking
            def on_lockpick_success():
                self.scene.services["popups"].add_popup("자물쇠 따기 성공!", player.position.x, player.position.y, 1.5)
                # Find the open version of the locked door and set it
                open_tid = None
                if tid == 5323220: open_tid = 5310000 # Wood Locked -> Wood Open
                elif tid == 5323221: open_tid = 5310001 # Iron Locked -> Iron Open
                elif tid == 5323022: open_tid = 5310002 # Glass Locked -> Glass Open
                elif tid == 5323023: open_tid = 5310003 # Prison Locked -> Prison Open
                elif tid == 5323024: open_tid = 5310004 # Lab Locked -> Lab Open
                
                if open_tid: 
                    target_block.set_tile_id(open_tid)
                    self.collision_world.remove_static(target_block)

            def on_lockpick_fail():
                player.ap = max(0, player.ap - 5) # Lockpick failure cost AP
                self.scene.services["popups"].add_popup("자물쇠 따기 실패! (AP -5)", player.position.x, player.position.y, 1.5, (255, 50, 50))
            
            if not minigame_manager.is_minigame_active():
                minigame_manager.start_minigame(LockpickMinigame(duration=15.0, num_pins=3), on_lockpick_success, on_lockpick_fail)
                return "미니게임 시작: 자물쇠 따기!"
            return "It's Locked. (Minigame Active)"
            
        # --- Chests ---
        elif tid == self.CHEST_CLOSED:
            # Simple open for now
            target_block.set_tile_id(self.CHEST_OPEN)
            # Give random item
            import random
            possible_items = ["TANGERINE", "CHOCOBAR", "BATTERY"] # Simple list for now
            item = random.choice(possible_items)
            
            if hasattr(player, 'inventory'):
                player.inventory.add_item(item, 1)
                info = player.inventory.get_item_info(item)
                name = info.get('name', item)
                return f"Found {name}!"
            
            return "Chest Opened"
            
        elif tid == self.CHEST_OPEN:
            return "Already Empty"
            
        # --- Vending Machine ---
        elif tid == VENDING_MACHINE_TID:
            self.scene.toggle_vending_machine()
            return "Vending machine opened."

        return f"Interacted with {tid}"

    def _find_block_at(self, x, y):
        if hasattr(self.scene, 'block_map'):
            return self.scene.block_map.get((x, y))
        return None
