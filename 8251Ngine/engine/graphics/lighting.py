import pygame
import random
import math
from engine.core.node import Node
from engine.core.math_utils import IsoMath

class LightSource(Node):
    def __init__(self, name="Light", radius=200, color=(255, 255, 200), intensity=1.0):
        super().__init__(name)
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self._cache_surf = None
        self._cache_key = None

    def get_light_surface(self):
        """Returns a cached light circle surface with smooth gradient"""
        key = (self.radius, self.color, self.intensity)
        if self._cache_surf and self._cache_key == key:
            return self._cache_surf
        
        size = int(self.radius * 2)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        
        steps = 20
        max_alpha = int(255 * self.intensity)
        for i in range(steps):
            r = self.radius * (1 - i/steps)
            progress = i / steps
            alpha = int(max_alpha * (1 - progress * progress)) 
            pygame.draw.circle(surf, (*self.color, alpha // steps), center, int(r))
            
        self._cache_surf = surf
        self._cache_key = key
        return surf

class DirectionalLight(Node):
    def __init__(self, name="Sun", direction=(1, 1), color=(255, 255, 255), intensity=0.0):
        super().__init__(name)
        self.direction = pygame.math.Vector2(direction).normalize()
        self.color = color
        self.intensity = intensity

class LightingManager:
    def __init__(self, width, height, ambient_color=(20, 20, 30)):
        self.width = width
        self.height = height
        self.ambient_color = ambient_color
        
        self.scale_factor = 0.5 
        self.lightmap_w = int(width * self.scale_factor)
        self.lightmap_h = int(height * self.scale_factor)
        
        self.lightmap = pygame.Surface((self.lightmap_w, self.lightmap_h))
        self.lights = [] # Point Lights
        self.directional_light = None # Single Sun/Moon
        
        # Weather & Environment
        self.weather_type = 'CLEAR' 
        self.weather_intensity = 0.0
        self.clarity = 255 
        self.particles = []

    def set_directional_light(self, light):
        self.directional_light = light

    def add_light(self, light):
        self.lights.append(light)

    def update_resolution(self, width, height):
        """Called when window is resized to update lightmap size"""
        self.width = width
        self.height = height
        self.lightmap_w = int(width * self.scale_factor)
        self.lightmap_h = int(height * self.scale_factor)
        self.lightmap = pygame.Surface((self.lightmap_w, self.lightmap_h))

    def update_weather(self, dt):
        """Update weather particles"""
        if self.weather_type == 'RAIN':
            if len(self.particles) < 100:
                self.particles.append([random.randint(0, self.width), -20, random.randint(5, 10)])
            for p in self.particles:
                p[1] += p[2] * 2 
                p[0] -= p[2] * 0.5 
                if p[1] > self.height:
                    p[1] = -20; p[0] = random.randint(0, self.width)
        elif self.weather_type == 'SNOW':
            if len(self.particles) < 50:
                self.particles.append([random.randint(0, self.width), -20, random.uniform(1, 3)])
            for p in self.particles:
                p[1] += p[2]
                p[0] += math.sin(pygame.time.get_ticks() * 0.005) * 0.5
                if p[1] > self.height:
                    p[1] = -20; p[0] = random.randint(0, self.width)
        else:
            self.particles.clear()

    def render(self, screen, camera, fov_polygon=None):
        self.lightmap.fill(self.ambient_color)
        
        if self.directional_light and self.directional_light.intensity > 0:
            r = int(self.directional_light.color[0] * self.directional_light.intensity)
            g = int(self.directional_light.color[1] * self.directional_light.intensity)
            b = int(self.directional_light.color[2] * self.directional_light.intensity)
            self.lightmap.fill((r, g, b), special_flags=pygame.BLEND_RGB_ADD)
        
        for light in self.lights:
            if not light.visible: continue
            gpos = light.get_global_position()
            sx, sy = camera.world_to_screen(*IsoMath.cart_to_iso(gpos.x, gpos.y, gpos.z))
            lx = int(sx * self.scale_factor)
            ly = int(sy * self.scale_factor)
            l_rad = light.radius * self.scale_factor
            if not (-l_rad < lx < self.lightmap_w + l_rad and -l_rad < ly < self.lightmap_h + l_rad): continue

            lsurf = light.get_light_surface()
            target_w = int(lsurf.get_width() * self.scale_factor)
            target_h = int(lsurf.get_height() * self.scale_factor)
            if target_w < 1 or target_h < 1: continue
            
            scaled_light = pygame.transform.smoothscale(lsurf, (target_w, target_h))
            dest_rect = scaled_light.get_rect(center=(lx, ly))
            self.lightmap.blit(scaled_light, dest_rect, special_flags=pygame.BLEND_RGB_ADD)

        if fov_polygon:
            mask_surf = pygame.Surface((self.lightmap_w, self.lightmap_h), pygame.SRCALPHA)
            screen_poly = []
            for px, py in fov_polygon:
                sx, sy = camera.world_to_screen(*IsoMath.cart_to_iso(px, py))
                screen_poly.append((int(sx * self.scale_factor), int(sy * self.scale_factor)))
            
            if len(screen_poly) > 2:
                pygame.draw.polygon(mask_surf, (255, 255, 255, self.clarity), screen_poly)
                pygame.draw.lines(mask_surf, (255, 255, 255, self.clarity // 2), True, screen_poly, width=6)
                self.lightmap.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        if self.weather_type == 'FOG':
            fog_surf = pygame.Surface((self.lightmap_w, self.lightmap_h))
            fog_surf.fill((100, 100, 110))
            self.lightmap.blit(fog_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        full_lightmap = pygame.transform.smoothscale(self.lightmap, (self.width, self.height))
        screen.blit(full_lightmap, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        if self.weather_type == 'RAIN':
            for p in self.particles:
                pygame.draw.line(screen, (150, 150, 200, 150), (p[0], p[1]), (p[0] - 2, p[1] + 10))
        elif self.weather_type == 'SNOW':
            for p in self.particles:
                pygame.draw.circle(screen, (255, 255, 255, 180), (int(p[0]), int(p[1])), int(p[2]))