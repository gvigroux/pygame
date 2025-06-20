


import math
import random

import cairo

from object.object import Object
from object.particle import Particle


class Counter(Object):
    def __init__(self, data, pygame, screen, window_size, count, id):
        super().__init__(data, pygame, screen, window_size, count, id) 
        self.position   = (-1, -1)
        self.text       = "00"
        self.start_step             = self.config("start_step", 0)
        self.end_step               = self.config("end_step", 3)
        self.stop_incrementing_step = self.config("stop_incrementing_step", 2)
        self.color      = (0.0, 0.0, 7.0, 1.0)
        self.text_width = 85
        self.text_height = 60
        self.fade_speed = 10.0 
    

    def _update(self, dt, step):
        if( step < self.start_step ):
            return
        if( step >= self.end_step ):
            self.position = (227,510)
            self.explode()
            return
        if( step >= self.stop_incrementing_step ):
            return
        minutes, self.seconds = divmod(int(self.age/1000), 60)
        self.text = f"{self.seconds:02d}"   

    def _draw(self, ctx):
           
        ctx.select_font_face("Wumpus Mono Pro")
        ctx.set_font_size(80)
        (x, y, self.text_width, self.text_height, dx, dy) = ctx.text_extents(self.text)        
        if self.position[0] == -1:
            self.position = (self.window_size[0]/2 - self.text_width/2, self.window_size[1]/2 + self.text_height/2)

        ### Dessin du contour noir (4 décalages pour effet "outline") ###
        ctx.set_source_rgba(0.2, 0.2, 0.2, self.alpha)  # Noir
        offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2)]  # Décalages autour de la position centrale
        for offset_x, offset_y in offsets:
            ctx.move_to(self.position[0] + offset_x, self.position[1] + offset_y)
            ctx.show_text(self.text)
            
         ### Dessin du texte rouge principal ###
        ctx.move_to( self.position[0], self.position[1])
        ctx.set_source_rgba(0, 0, 0.7, self.alpha)
        ctx.show_text(self.text)

        ctx.fill()



    def create_particles(self, count=200):
        r, g, b, a = self.color  # Couleur de base du texte


        # Position de départ : dans le rectangle du texte (en partant de self.position)
        # self.position correspond au point d’ancrage (baseline left), on ajuste pour couvrir tout le texte
        text_x_start = self.position[0]
        text_y_start = self.position[1] -  self.text_height  # remonter pour le haut du texte

        for _ in range(count):
            # Position aléatoire dans le rectangle du texte
            px = random.uniform(text_x_start, text_x_start +  self.text_width)
            py = random.uniform(text_y_start, text_y_start +  self.text_height)

            # Direction aléatoire autour (360°)
            direction = random.uniform(0, 2 * math.pi)

            # Vitesse variable
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

            particle = Particle(position=(px, py), velocity=(vx, vy),
                                radius=radius, lifetime=5, color=particle_color)
            self.particles.append(particle)
