from pygame.math import Vector3

class Node:
    def __init__(self, name="Node"):
        self.name = name
        self.tag = name
        self.parent = None
        self.children = []
        self.components = []
        
        self.position = Vector3(0, 0, 0)
        self.scale = Vector3(1, 1, 1)
        self.visible = True
        self.z_index = 0

    def add_component(self, component):
        self.components.append(component)
        component._on_added(self)
        return component

    def get_component(self, component_type):
        for c in self.components:
            if isinstance(c, component_type):
                return c
        return None

    def add_child(self, node):
        if node.parent:
            node.parent.remove_child(node)
        node.parent = self
        self.children.append(node)
        node._ready()

    def remove_child(self, node):
        if node in self.children:
            self.children.remove(node)
            node.parent = None

    def get_global_position(self):
        if self.parent and isinstance(self.parent, Node):
            return self.parent.get_global_position() + self.position
        return self.position

    def _ready(self):
        pass

    def _update(self, dt, services, game_state):
        """핵심: 컴포넌트와 자식들에게 game_state를 누락 없이 전달"""
        for comp in self.components:
            comp.update(dt, services, game_state)
            
        for child in self.children:
            child._update(dt, services, game_state)
            
        self.update(dt, services, game_state)

    def _draw(self, services):
        if not self.visible: return
        renderer = services.get("renderer")
        if renderer:
            renderer.submit(self)
        for child in self.children:
            child._draw(services)

    def update(self, dt, services, game_state):
        pass

    def draw_gizmos(self, screen, camera):
        pass