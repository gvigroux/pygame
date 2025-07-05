import math
import random
import cairo
import pygame

from element.background import eBackground
from element.border import eBorder
from element.fragment import eFragment
from object.inner_particle import InnerParticle
from object.object import Object

class Timer(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)

        self.duration = self.config("duration", 5) * 1000
        self.elapsed  = 0  # temps écoulé en ms

        size = self.config("size", (100, 100))
        self.width    = size[0]
        self.height   = size[1]

        self.border     = eBorder(**self.config("border", {}))
        self.background = eBackground(**self.config("background", {}))
        self.fragment   = eFragment(**self.config("fragment", {}))

        if( "H" in self.position.justify ) :
            self.position.x = (self.window_size[0] - self.width) // 2
        if( "V" in self.position.justify ) :
            self.position.y = (self.window_size[1] - self.height) // 2


    def _update(self, dt, step, clock, blocked):
        self.elapsed += dt*1000
        if self.elapsed > self.duration:
            self.elapsed = self.duration

    def _draw(self, ctx):
        x, y = self.position.x, self.position.y

        # Dessine le fond de la barre
        self.set_color(ctx, self.background.color)
        ctx.rectangle(x, y, self.width, self.height)
        ctx.fill()

        # Dessine la partie restante
        progress = self.elapsed / self.duration
        remaining = max(0.0, 1.0 - progress)

        self.set_color(ctx, self.color)
        ctx.rectangle(x, y, self.width * remaining, self.height)
        ctx.fill()

        # Dessine la bordure
        ctx.set_source_rgba(*self.border.color)
        ctx.set_line_width(self.border.width)
        ctx.rectangle(x, y, self.width, self.height)
        ctx.stroke()

        self.create_particles_timer(self.width * remaining, self.fragment, self.color)

    def _draw_shadow(self, ctx):
        #TODO: invisible
        offset = self.shadow.offset
        x, y = self.position.x + offset, self.position.y + offset

        # Dessine le fond de l’ombre
        #ctx.set_source_rgba(0, 0, 0, 0.5)
        ctx.rectangle(x, y, self.width, self.height)
        ctx.fill()

        # Dessine la partie restante de l’ombre
        progress = self.elapsed / self.duration
        remaining = max(0.0, 1.0 - progress)

        ctx.rectangle(x, y, self.width * remaining, self.height)
        ctx.fill()

        # Ombre de la bordure
        ctx.set_line_width(self.border.width)
        ctx.rectangle(x, y, self.width, self.height)
        ctx.stroke()


    def is_finished(self):
        return self.elapsed >= self.duration
    

    def create_particles_timer(self, position_width, fragment, color = None):
        
        points = self.get_points_timer(position_width, fragment)
        for i, point in enumerate(points):
            
           # Angle aléatoire (360°)
            angle = random.uniform(0, 2 * math.pi)

            # Vitesse aléatoire dans cette direction
            speed = random.uniform(30, 70)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Créer la particule
            particle = InnerParticle(position=(point[0], point[1]), velocity=(vx, vy),
                                radius=fragment.get_radius(), lifetime=fragment.lifetime, color=fragment.get_color(color, self.color))
            self.particles.append(particle)

    def get_points_timer(self, position_width, fragment):
        points = []       
        text_x_start = self.position.x
        text_y_start = self.position.y
        for i in range(fragment.count):
            x = text_x_start + position_width 
            y = random.uniform(text_y_start, text_y_start +  self.height)
            points.append((x, y))
        return points



    def get_points(self, fragment):
        points = []       
        text_x_start = self.position.x
        text_y_start = self.position.y
        for i in range(fragment.count):
            x = random.uniform(text_x_start, text_x_start +  self.width)
            y = random.uniform(text_y_start, text_y_start +  self.height)
            points.append((x, y))
        return points
