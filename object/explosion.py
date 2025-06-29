

import math
import random
from element.fragment import eFragment
from element.position import ePosition
from element.sound import eSound
from element.step import eStep
from object.inner_particle import InnerParticle
from object.object import Object


class Explosion(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)
        

    def _draw(self, ctx):
        if( self.first_draw ):
            self.explode()

