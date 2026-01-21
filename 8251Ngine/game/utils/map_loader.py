import json
import os
from engine.graphics.block import Block3D
from engine.graphics.lighting import LightSource
from engine.assets.tile_engine import TileEngine # Import TileEngine
from settings import TILE_SIZE # TILE_SIZE 임포트

class MapLoader:
    def __init__(self, map_path, tiles_path):
        self.map_data = self._load_json(map_path)
        self.tile_data = self._load_json(tiles_path)
        self.width = self.map_data.get("width", 100)
        self.height = self.map_data.get("height", 100)
        self.zone_map = self.map_data.get('zone_map', [[0 for _ in range(self.width)] for _ in range(self.height)]) # PxANIC!의 zone_map 이식

    def _load_json(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def build_world(self, scene_node, collision_world):
        print("Building World from Map...")
        layers = self.map_data.get("layers", {})
        block_map = {}
        
        # Process Floor
        if "floor" in layers:
            self._process_layer(layers["floor"], scene_node, collision_world, block_map)
            
        for layer_name, grid in layers.items():
            if layer_name == "floor": continue
            print(f"Processing layer: {layer_name}")
            self._process_layer(grid, scene_node, collision_world, block_map)
            
        return block_map

    def _process_layer(self, grid, scene_node, collision_world, block_map):
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if not cell: continue
                tile_id = str(cell[0])
                rotation = cell[1]
                
                if tile_id == "0": continue # Empty
                
                tile_info = self.tile_data.get(tile_id)
                if not tile_info:
                    # print(f"Unknown tile ID: {tile_id}")
                    continue
                
                name = tile_info.get("name", "Unknown")
                color = tile_info.get("color", [255, 255, 255])
                
                # Determine Block properties based on TileEngine.get_tile_category
                category = TileEngine.get_tile_category(tile_id)
                
                is_solid = False
                height = 0.05
                
                if category == 1 or category == 2: # Floors (e.g., 11xxxx, 21xxxx)
                    height = 0.05
                elif category == 3: # Walls (e.g., 32xxxx)
                    height = 2.0
                    is_solid = True
                elif category == 4: # Fences (e.g., 42xxxx)
                    height = 1.0
                    is_solid = True
                elif category == 5: # Doors/Chests (e.g., 53xxxx)
                    height = 1.8
                    is_solid = True 
                elif category == 8: # Furniture (e.g., 83xxxx)
                    height = 0.8
                    is_solid = True
                elif category == 9: # Fields/Objects (e.g., 93xxxx)
                    height = 0.3
                
                block = Block3D(f"{name}_{x}_{y}", size_z=height, color=tuple(color), tile_id=tile_id)
                block.position.x = x
                block.position.y = y
                
                scene_node.add_child(block)
                
                # Store in map (Overwrite floor with objects/walls if same loc)
                # Prioritize objects/walls
                if (x, y) not in block_map or height > 0.1:
                    block_map[(x, y)] = block
                
                if is_solid and collision_world:
                    collision_world.add_static(block)

                # Special: Lights
                if "Lamp" in name or "Light" in name:
                    light = LightSource(f"Light_{x}_{y}", radius=150, color=(255, 255, 200), intensity=0.4)
                    block.add_child(light)

    def get_zone_id(self, gx, gy):
        """
        주어진 그리드 좌표 (gx, gy)에 해당하는 zone_id를 반환합니다.
        범위를 벗어나면 기본값 0을 반환합니다.
        """
        if 0 <= gy < self.height and 0 <= gx < self.width:
            return self.zone_map[gy][gx]
        return 0

