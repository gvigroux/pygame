


import math
import random

import cairo
import numpy as np
import pygame

from object.object import Object
from object.inner_particle import InnerParticle


class Arc(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)

        self.radius      = self.config("radius", 10)
        self.angle_start_deg = self.config("angle_start", 0)  # DEGRÉS FIXE
        self.angle_end_deg   = self.config("angle_end", 330)
        self.width       = self.config("width", 5)
        self.speed       = self.config("speed", random.uniform(-2, 2))


        self.current_angle_deg  = 0.0  # angle dynamique en DEGRÉS

        
        self.visible_rad    = math.radians(self.angle_end_deg - self.angle_start_deg) 

        # Initialiser
        self.start_angle = math.radians(self.angle_start_deg)
        self.end_angle   = self.start_angle + self.visible_rad

        
    def _update(self, dt, step, clock, blocked):
        # Angle tournant (ex: rotation)
        self.current_angle_deg  = (self.speed * self.age / 1000) % 360

        # Décale l’angle de départ par rapport à l’angle initial
        self.start_angle = math.radians(self.angle_start_deg + self.current_angle_deg)
        self.end_angle   = self.start_angle + self.visible_rad


    def _draw(self, ctx): 
        ctx.set_line_width(self.width)
        ctx.arc(self.position.x, self.position.y, self.radius, self.start_angle, self.end_angle)
        ctx.stroke()


    def _draw_shadow(self, ctx):    
        ctx.set_line_width(self.width)
        ctx.arc(self.position.x + self.shadow.offset, self.position.y + self.shadow.offset, self.radius, self.start_angle, self.end_angle)
        ctx.stroke()  
        pass


    def get_points(self, fragment):
        points = []
        for i in range(fragment.count):
            theta = random.uniform(self.start_angle, self.end_angle)
            # Angle aléatoire sur l’arc visible
            theta = random.uniform(self.start_angle, self.end_angle)

            # Position sur l’arc (bord visible)
            x = self.position.x + math.cos(theta) * self.radius
            y = self.position.y + math.sin(theta) * self.radius

            points.append((x, y))
        return points
