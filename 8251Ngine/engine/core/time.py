import pygame

class TimeManager:
    PHASES = {
        'DAWN': {'duration': 20, 'ambient': (60, 60, 90)},
        'MORNING': {'duration': 40, 'ambient': (255, 255, 255)},
        'NOON': {'duration': 60, 'ambient': (255, 255, 240)},
        'AFTERNOON': {'duration': 40, 'ambient': (255, 240, 220)},
        'EVENING': {'duration': 30, 'ambient': (120, 100, 100)},
        'NIGHT': {'duration': 80, 'ambient': (10, 10, 25)}
    }
    
    PHASE_ORDER = ['DAWN', 'MORNING', 'NOON', 'AFTERNOON', 'EVENING', 'NIGHT']

    def __init__(self):
        self.global_time = 0.0
        self.day_count = 1
        self.current_phase_idx = 1 # Start at Morning
        self.phase_timer = 0.0
        self.time_scale = 1.0
        self.paused = False
        
        self.current_ambient = self.PHASES['MORNING']['ambient']
        self.target_ambient = self.current_ambient

    @property
    def current_phase(self):
        return self.PHASE_ORDER[self.current_phase_idx]

    def update(self, dt):
        if self.paused: return
        
        real_dt = dt * self.time_scale
        self.global_time += real_dt
        self.phase_timer += real_dt
        
        # Check Phase Transition
        phase_data = self.PHASES[self.current_phase]
        if self.phase_timer >= phase_data['duration']:
            self._next_phase()
            
        # Update Ambient Color (Lerp)
        self._lerp_ambient(dt)

    def _next_phase(self):
        self.phase_timer = 0
        self.current_phase_idx = (self.current_phase_idx + 1) % len(self.PHASE_ORDER)
        if self.current_phase == 'DAWN':
            self.day_count += 1
            print(f"[Time] Day {self.day_count} Started")
            
        # Set new target ambient
        new_phase = self.PHASES[self.current_phase]
        self.target_ambient = new_phase['ambient']
        print(f"[Time] Phase Changed: {self.current_phase}")

    def _lerp_ambient(self, dt):
        # Smooth transition speed
        speed = 0.5 * dt
        r = self._lerp(self.current_ambient[0], self.target_ambient[0], speed)
        g = self._lerp(self.current_ambient[1], self.target_ambient[1], speed)
        b = self._lerp(self.current_ambient[2], self.target_ambient[2], speed)
        self.current_ambient = (r, g, b)

    @property
    def sun_direction(self):
        """Calculates light direction vector based on time of day"""
        # Range: -1.0 to 1.0 based on phase progress
        progress = self.phase_timer / self.PHASES[self.current_phase]['duration']
        
        # Simple Left-to-Right (X changes)
        # Dawn/Morning: Sun rises from Left
        # Noon: Above
        # Evening: Sinks to Right
        
        if self.current_phase in ['DAWN', 'MORNING', 'NOON']:
            # Move from (-1, -1) to (0, 0)
            return pygame.math.Vector2(-1.0 + progress, -0.5)
        else:
            # Move from (0, 0) to (1, 1)
            return pygame.math.Vector2(progress, 0.5)

    def _lerp(self, start, end, t):
        return start + (end - start) * t
