


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
        self.angle_start = self.config("angle_start", 0)
        self.angle_end   = self.config("angle_end", 330)
        self.width       = self.config("width", 5)
        self.speed       = self.config("speed", random.uniform(-2, 2))


        self.current_angle  = 0.0  # angle accumulé
        self.start_angle    = math.radians(self.angle_start)
        self.end_angle      = self.start_angle + math.radians(self.angle_end-self.angle_start)
        self.visible_rad    = math.radians(self.angle_end - self.angle_start) 

        
    def _update(self, dt, step, clock):
        self.current_angle  = (self.speed * self.age / 1000) % 360  # Division par 1000 si total_time est en ms
        self.start_angle    = math.radians(self.current_angle)
        self.end_angle      = self.start_angle + self.visible_rad


    def _draw(self, ctx): 
        ctx.set_line_width(self.width)
        ctx.arc(self.position.x, self.position.y, self.radius, self.start_angle, self.end_angle)
        ctx.stroke()


    def _draw_shadow(self, ctx):    
        ctx.set_line_width(self.width)
        ctx.arc(self.position.x + self.shadow.offset, self.position.y + self.shadow.offset, self.radius, self.start_angle, self.end_angle)
        ctx.stroke()  
        pass

    # def create_particles_center(self, count=20):
    #     for _ in range(count):
    #         angle = random.uniform(0, 2 * math.pi)
    #         speed = random.uniform(50, 150)  # pixels/sec
    #         vx = math.cos(angle) * speed
    #         vy = math.sin(angle) * speed
    #         particle = Particle(self.position, (vx, vy))
    #         self.particles.append(particle)

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

    def create_particles_DELETE(self, count=100):
        r, g, b, a = self.color  # Couleur de base de l'arc
        for _ in range(count):
            # Angle aléatoire sur l’arc visible
            theta = random.uniform(self.start_angle, self.end_angle)

            # Position sur l’arc (bord visible)
            x = self.position.x + math.cos(theta) * self.radius
            y = self.position.y + math.sin(theta) * self.radius

            # Grand angle de dispersion : ±90° autour du theta
            spread_angle = random.uniform(-math.pi / 2, math.pi / 2)
            direction = theta + spread_angle

            # Vitesse plus lente
            speed = random.uniform(30, 70)
            vx = math.cos(direction) * speed
            vy = math.sin(direction) * speed

            # Taille variable
            radius = random.uniform(1.5, 4.0)

            # Légère variation de couleur
            dr = random.uniform(-0.1, 0.1)
            dg = random.uniform(-0.1, 0.1)
            db = random.uniform(-0.1, 0.1)
            particle_color = (
                min(max(r + dr, 0.0), 1.0),
                min(max(g + dg, 0.0), 1.0),
                min(max(b + db, 0.0), 1.0),
                1.0
            )

            # Créer la particule
            particle = InnerParticle(position=(x, y), velocity=(vx, vy),
                                radius=radius, lifetime=0.6, color=particle_color)
            self.particles.append(particle)
