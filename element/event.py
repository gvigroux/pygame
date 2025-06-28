from element.fragment import eFragment
from element.sound import eSound


class eEvent:
    def __init__(self, pygame, fragment = {}, sound = {}):
        self.fragment = eFragment(**fragment)
        self.sound    = eSound(pygame, **sound)

    def enabled(self):
        return self.fragment.enabled() or self.sound.enabled()

    def play(self):
        if( not self.enabled() ):
            return
        self.sound.play()