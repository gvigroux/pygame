class eSound:
    def __init__(self, pygame, path = None, volume = 0.1, loop = False):
        self.path = path
        self.volume = volume
        self.loop = loop
        self.pygame = pygame

        if( path is not None ):
            self.sound    = self.pygame.mixer.Sound(path)
            self.sound.set_volume(volume)

    def enabled(self):
        return self.path is not None

    def play(self):
        if( not self.enabled() ):
            return
        self.sound.play(loops=self.loop)