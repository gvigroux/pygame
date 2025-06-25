

import math
import random
from element.position import ePosition
from element.step import eStep
from object.inner_particle import InnerParticle
from object.object import Object


class Explosion(Object):
    def __init__(self, data, pygame, screen,window_size, count, id):
        super().__init__(data, pygame, screen,window_size, count, id)        

        self.duration = self.config("duration", 10)
        self.first_draw = False

        
    def _update(self, dt, step):
        pass


    def _draw(self, ctx):
        if( not self.first_draw ):
            self.first_draw = True
            self.create_particles(lifetime=self.duration)

        
    def create_particles(self, count=10, color=None, lifetime=2):
        if( color is None ):
           color = self.color 
        r, g, b, a = self.normalize_color(color)
        for _ in range(count):
            # Position initiale : au centre de la balle
            x = self.position.x
            y = self.position.y

            # Angle aléatoire (360°)
            angle = random.uniform(0, 2 * math.pi)

            # Vitesse aléatoire dans cette direction
            speed = random.uniform(30, 70)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Taille aléatoire
            radius = random.uniform(1.5, 4.0)

            # Variation légère de couleur
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
                                radius=radius, lifetime=lifetime, color=particle_color)
            self.particles.append(particle)