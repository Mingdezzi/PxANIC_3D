import json
import os
from engine.ui.gui import Control, Label, Panel, Button

class UILoader:
    @staticmethod
    def load_ui(path):
        if not os.path.exists(path): return None
        with open(path, 'r') as f:
            data = json.load(f)
        return UILoader.from_dict(data)

    @staticmethod
    def save_ui(path, root_control):
        data = root_control.to_dict()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def from_dict(data):
        ui_type = data.get("type")
        r = data.get("rect", [0, 0, 100, 50])
        
        ctrl = None
        if ui_type == "Label":
            ctrl = Label(data["text"], r[0], r[1], data["size"], tuple(data["color"]))
        elif ui_type == "Panel":
            ctrl = Panel(r[0], r[1], r[2], r[3], tuple(data["color"]))
        elif ui_type == "Button":
            ctrl = Button(data["text"], r[0], r[1], r[2], r[3], tuple(data["base_color"]), tuple(data["hover_color"]))
        else:
            ctrl = Control(r[0], r[1], r[2], r[3])

        for child_data in data.get("children", []):
            # Button의 경우 내부 Label은 자동 생성되므로 중복 방지
            if ui_type == "Button" and child_data["type"] == "Label": continue
            ctrl.add_child(UILoader.from_dict(child_data))
            
        return ctrl
