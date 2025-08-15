from element.element import Element
from element.fragment import eFragment
from element.sound import eSound


class eEvent(Element):
    def __init__(self, fragment = {}, sound = {}, acceleration = (1, 1)):
        self.fragment       = eFragment(**fragment)
        self.sound          = eSound(**sound)
        self.acceleration   = acceleration
        self.prepare()

    def enabled(self):
        return self.fragment.enabled() or self.sound.enabled()
    
    def prepare(self):
        self.acceleration = self.eval(self.acceleration)

    def play(self):
        if( not self.enabled() ):
            return
        self.sound.play()

    def schema(self):
        return {
            "fragment": ("dict", "Fragment"),
            "sound": ("dict", "Sound"),
            "acceleration": ("str", "Acceleration"),
        }