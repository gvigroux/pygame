from element.fragment import eFragment
from element.sound import eSound


class eEvent:
    def __init__(self, pygame, fragment = {}, sound = {}, acceleration = (1, 1)):
        self.fragment = eFragment(**fragment)
        self.sound    = eSound(pygame, **sound)
        self.acceleration = acceleration

    def enabled(self):
        return self.fragment.enabled() or self.sound.enabled()

    def play(self):
        if( not self.enabled() ):
            return
        self.sound.play()