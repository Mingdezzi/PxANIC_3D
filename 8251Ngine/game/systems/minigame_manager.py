from game.systems.minigames.base_minigame import BaseMinigame

class MinigameManager:
    def __init__(self):
        self.active_minigame = None

    def start_minigame(self, minigame_instance, success_callback=None, fail_callback=None):
        if self.active_minigame and self.active_minigame.is_active:
            print("[MinigameManager] Another minigame is already active!")
            return False
        
        self.active_minigame = minigame_instance
        self.active_minigame.success_callback = success_callback
        self.active_minigame.fail_callback = fail_callback
        self.active_minigame.start()
        print(f"[MinigameManager] Started {type(minigame_instance).__name__}")
        return True

    def update(self, dt, services, game_state):
        if self.active_minigame and self.active_minigame.is_active:
            self.active_minigame.update(dt, services, game_state)

    def draw(self, screen, services):
        if self.active_minigame and self.active_minigame.is_active:
            self.active_minigame.draw(screen, services)

    def handle_event(self, event, services):
        if self.active_minigame and self.active_minigame.is_active:
            self.active_minigame.handle_event(event, services)

    def is_minigame_active(self):
        return self.active_minigame and self.active_minigame.is_active
