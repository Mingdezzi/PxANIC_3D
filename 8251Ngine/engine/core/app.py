import pygame
import sys
import random

# Ensure pygame is available globally
global pygame

from engine.graphics.renderer import Renderer
from engine.graphics.lighting import LightingManager
from engine.core.time import TimeManager
from engine.core.input import InputManager
from engine.net.network import NetworkManager
from engine.assets.loader import ResourceManager
from engine.audio.audio_manager import AudioManager
from engine.core.interaction import InteractionManager
from game.systems.minigame_manager import MinigameManager
from engine.systems.combat import CombatManager
from engine.ui.world_ui import WorldPopupManager
from engine.physics.navigation import NavigationManager

class App:
    instance = None

    def __init__(self, width=1280, height=720, title="8251Ngine", use_network=True):
        App.instance = self
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = True
        self.use_network = use_network
        
        # Core Engine Services
        self.services = {
            "input": InputManager(),
            "renderer": Renderer(self.screen),
            "lighting": LightingManager(width, height),
            "time": TimeManager(),
            "network": NetworkManager("ws://localhost:8765") if use_network else None,
            "assets": ResourceManager(),
            "audio": AudioManager(),
            "interaction": InteractionManager(),
            "minigame": MinigameManager(),
            "combat": CombatManager(),
            "popups": WorldPopupManager(),
            "nav": None,
            "app": self
        }
        
        self.ui_root = None
        self.root = None
        self.fov_polygon = None

    def set_ui(self, ui_root):
        self.ui_root = ui_root

    def set_scene(self, scene_root):
        self.root = scene_root
        if self.root:
            self.root._ready(self.services)

    def run(self):
        if self.use_network and self.services["network"]:
            self.services["network"].start()
            
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            
        if self.use_network and self.services["network"]:
            self.services["network"].stop()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.services["renderer"]._update_screen(self.screen)
                self.services["lighting"].update_resolution(event.w, event.h)
            
            if self.ui_root:
                if self.ui_root.handle_event(event):
                    if self.services["minigame"].is_minigame_active():
                        self.services["minigame"].handle_event(event, self.services)
                        return True
                    continue
            
            if self.services["minigame"].is_minigame_active():
                if self.services["minigame"].handle_event(event, self.services):
                    return

            if self.root and hasattr(self.root, 'handle_event'):
                self.root.handle_event(event)

    def _update(self, dt):
        self.services["input"].update()
        self.services["time"].update(dt)
        self.services["lighting"].ambient_color = self.services["time"].current_ambient
        self.services["lighting"].update_weather(dt)
        self.services["interaction"].update()
        
        # 전역 게임 상태 생성 (딕셔너리)
        game_state = {
            "current_phase": self.services["time"].current_phase,
            "is_blackout": (self.services["time"].current_phase == "NIGHT" and random.random() < 0.05),
            "player": self.root.player if hasattr(self.root, 'player') else None,
            "all_entities": self.root.children if hasattr(self.root, 'children') else [],
        }

        self.services["minigame"].update(dt, self.services, game_state)
        self.services["combat"].update(dt, self.services, game_state)
        self.services["popups"].update(dt)
        
        if self.root:
            self.root._update(dt, self.services, game_state)

    def _draw(self):
        self.screen.fill((20, 20, 25))
        renderer = self.services["renderer"]
        lighting = self.services["lighting"]
        interaction = self.services["interaction"]
        minigame = self.services["minigame"]
        combat = self.services["combat"]
        popups = self.services["popups"]
        
        if self.root:
            renderer.clear_queue()
            def _collect_nodes(node):
                if not node.visible: return
                renderer.submit(node)
                if hasattr(node, 'get_light_surface'):
                    if node not in lighting.lights: lighting.add_light(node)
                for child in node.children: _collect_nodes(child)
            _collect_nodes(self.root)
            
            self.root.draw_gizmos(self.screen, renderer.camera)
            renderer.flush(self.services)
            interaction.draw(self.screen, renderer.camera)
            combat.draw(self.screen, renderer.camera)
            popups.draw(self.screen, renderer.camera)
            lighting.render(self.screen, renderer.camera, self.fov_polygon)
            minigame.draw(self.screen, self.services)
            
        if self.ui_root:
            self.ui_root.draw(self.screen, self.services)
        pygame.display.flip()
