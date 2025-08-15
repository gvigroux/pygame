


import math
import random

import cairo
import numpy as np
import pygame

from object.arc import Arc
from object.object import Object
from object.inner_particle import InnerParticle


class Arcs(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)

        self.radius     = self.config("radius", 10)
        self.angle_start_deg = self.config("angle_start", 0)  # DEGRÉS FIXE
        self.angle_end_deg   = self.config("angle_end", 330)
        self.width      = self.config("width", 5)
        self.speed      = self.config("speed", random.uniform(-2, 2))
        self.objects    = []
        self._prepare()

    def _schema(self):
        return {
            "count": ("int", "Count"),
            "radius": ("floateval", "Radius"),
            "angle_start": ("floateval", "Angle start"),
            "angle_end": ("floateval", "Angle end"),
            "width": ("float", "Width"),
            "speed": ("float", "Speed"),
        }
    
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


    def _prepare(self):
        self.objects = [] 

        for i in range(self.count):
            object = Arc(self.data, self.window_size, self.count, i)
            object.parent_uid = self.uid
            self.objects.append(object)

