import math
import random
import cairo
import math


from element.text import eText
from object.arc import Arc
from object.ball import Ball
from object.object import Object
from object.inner_particle import InnerParticle

class Balls(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)
        self.radius     = self.config("radius", 8)
        self.velocity   = self.config("velocity", [random.uniform(-150, 150), random.uniform(-150, 150)])
        self.text       = eText(**self.config("text", {}))
        self.objects    = []
        self._prepare()

    def _schema(self):
        return {
            "count": ("int", "Count"),
            "radius": ("floateval", "Radius"),
            "velocity": ("floateval", "Velocity"),
            "text": ("eText", "Text")
        }
    
    def _prepare(self):
        self.objects = []

        for i in range(self.count):
            object = Ball(self.data, self.window_size, self.count, i)
            object.parent_uid = self.uid
            self.objects.append(object)
     
    def reset(self, start_time, current_step=0):
        for object in self.objects:
            object.reset(start_time, current_step)
            
    def update(self, dt, step, clock, blocked):
        for object in self.objects:
            object.update(dt, step, clock, blocked)

    def draw(self, ctx): 
        for object in self.objects:
            object.draw(ctx)

    def draw_shadow(self, ctx):    
        for object in self.objects:
            object.draw_shadow(ctx)

    