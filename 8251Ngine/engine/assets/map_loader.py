import json
import os

class MapLoader:
    @staticmethod
    def load_map_data(path):
        """
        JSON 맵 파일을 파싱하여 전체 데이터 딕셔너리를 반환합니다.
        """
        if not os.path.exists(path):
            print(f"MapLoader: File not found {path}")
            return None

        with open(path, 'r') as f:
            data = json.load(f)

        print(f"MapLoader: Successfully parsed {path}")
        return data

    @staticmethod
    def save_map(path, scene, width=20, height=20):
        # 저장 로직은 EditorScene에서 사용하므로 유지
        from engine.graphics.block import Block3D
        data = {
            "width": width,
            "height": height,
            "blocks": []
        }
        for child in scene.children:
            if isinstance(child, Block3D):
                data["blocks"].append({
                    "name": child.name,
                    "pos": [child.position.x, child.position.y, child.position.z],
                    "size_z": child.size_z,
                    "color": list(child.color),
                    "zone_id": child.zone_id,
                    "interact_type": child.interact_type,
                    "tile_id": child.tile_id
                })
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
