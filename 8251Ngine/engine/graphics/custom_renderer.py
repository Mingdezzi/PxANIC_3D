from engine.core.component import Component

class CustomizationComponent(Component):
    def __init__(self, skin_color=(255, 220, 180), clothes_color=(50, 100, 200), hat_type=None):
        super().__init__()
        self.skin_color = skin_color
        self.clothes_color = clothes_color
        self.hat_type = hat_type

    def update(self, dt, services, game_state):
        pass # No dynamic updates needed for now

    def get_colors(self):
        return {
            'skin': self.skin_color,
            'clothes': self.clothes_color
        }
