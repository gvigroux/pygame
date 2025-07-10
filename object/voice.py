from element.voice import eVoice
from object.object import Object

class Voice(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)     
        self.voice     = eVoice(pygame, **self.config("voice", {}))

    def _draw(self, ctx):
        if( self.first_draw ):
            self.voice.play()

    def _schema(self):
        return {
            "voice": ("voice", "Voice"),
            "volume": ("float", "Volume"),
        }



