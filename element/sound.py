import pygame

class eSound:
    def __init__(self, path = None, volume = 0.1, loop = False):
        self.path = path
        self.volume = volume
        self.loop = loop

        if( path is not None ):
            self.sound    = pygame.mixer.Sound(path)
            self.sound.set_volume(volume)

    def __getstate__(self):
        state = self.__dict__.copy()
        if "sound" in state:
            del state["sound"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if( self.path is not None ):
            self.sound    = pygame.mixer.Sound(self.path)
            self.sound.set_volume(self.volume)


    def enabled(self):
        return self.path is not None

    def play(self):
        if( not self.enabled() ):
            return
        self.sound.play(loops=self.loop)

    def stop(self):
        if( not self.enabled() ):
            return
        self.sound.stop()

    def schema(self):
        return {
            "path": ("str", "Path"),
            "volume": ("float", "Volume"),
            "loop": ("bool", "Loop"),
        }