from engine.core.app import App
from game.scenes.play_scene import PlayScene

if __name__ == "__main__":
    app = App(title="PxANIC! 3D - 8251Ngine", use_network=False)
    scene = PlayScene(name="MainScene")
    app.set_scene(scene)
    app.run()
