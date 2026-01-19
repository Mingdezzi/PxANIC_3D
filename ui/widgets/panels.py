import pygame
from ui.widgets.base import UIWidget
from settings import FPS

class EmotionPanelWidget(UIWidget):
    def __init__(self, game):
        super().__init__(game)
        self.width = 220
        self.height = 80
        self.panel_bg = self.create_panel_bg(self.width, self.height)

    def draw(self, screen):
        if self.game.player.role == "SPECTATOR": return

        w, h = screen.get_size()
        # Minimap Height is 220, Margin 20, Gap 10
        # Position: Above Minimap
        x = w - self.width - 20
        y = h - 220 - 20 - self.height - 10 
        
        screen.blit(self.panel_bg, (x, y))

        p = self.game.player
        active_statuses = []
        
        for emo, val in p.emotions.items():
            if val:
                if emo == 'FEAR': active_statuses.append(f"FEAR: Spd -30%")
                elif emo == 'RAGE': active_statuses.append(f"RAGE: Stam ∞")
                elif emo == 'PAIN': active_statuses.append(f"PAIN: Slow Lv.{val}")
                elif emo == 'HAPPINESS': active_statuses.append(f"HAPPY: Spd +10%")
                elif emo == 'ANXIETY': active_statuses.append(f"ANXTY: Heartbeat")
            
        if p.status_effects.get('FATIGUE'): active_statuses.append(f"FATIGUE: Spd -30%")
        if p.status_effects.get('DOPAMINE'): active_statuses.append(f"DOPA: Spd +20%")
        
        if not active_statuses:
            text = self.font_small.render("- Normal -", True, (150, 150, 150))
            screen.blit(text, (x + 15, y + 15))
        else:
            # Show up to 4 statuses (Height 80 is enough)
            y_offset = 12
            for i, status_str in enumerate(active_statuses[:4]):
                text = self.font_small.render(status_str, True, (255, 255, 255))
                screen.blit(text, (x + 15, y + y_offset))
                y_offset += 16
                if i >= 3 and len(active_statuses) > 4:
                    more = self.font_small.render("...", True, (200, 200, 200))
                    screen.blit(more, (x + self.width - 30, y + y_offset - 16))
                    break
