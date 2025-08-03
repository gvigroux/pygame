

import math
import random
from element.fragment import eFragment
from element.position import ePosition
from element.sound import eSound
from element.step import eStep
from object.inner_particle import InnerParticle
from object.object import Object


class Explosion(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)

    def _draw(self, ctx):
        if( self.first_draw ):
            self.explode()

    def _schema(self):
        return {}
    
    def _prepare(self):
        pass

