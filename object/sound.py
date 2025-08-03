from element.sound import eSound
from element.step import eStep
from object.object import Object

class Sound(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)     
        self.sound     = eSound(**self.config("sound", {}))

    def _draw(self, ctx):
        if( self.first_draw ):
            self.sound.play(self.age)

    def _schema(self):
        return {
            "sound": ("sound", "Sound")
        }
    
    def _prepare(self):
        pass
    
    @classmethod
    def parameter_fields(cls):
        return {
            "step": eStep.parameter_fields(),
            "sound": eSound.parameter_fields(),
        }