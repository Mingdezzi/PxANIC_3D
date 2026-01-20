class Component:
    """Base class for all components that can be attached to a Node"""
    def __init__(self):
        self.node = None

    def _on_added(self, node):
        self.node = node
        self.ready()

    def ready(self):
        pass

    def update(self, dt, services, game_state):
        """핵심: 모든 컴포넌트가 game_state를 받을 수 있도록 구조화"""
        pass