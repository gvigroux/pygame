import math
import random
from element.fragment import eFragment
from element.position import ePosition
from element.size import eSize
from object.inner_particle import InnerParticle
from object.object import Object

class Spark(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)
        self.position   = ePosition(window_size, count, id, **self.config("position", {}))
        self.size       = eSize(window_size, count, id, **self.config("size", {}))
        self.fragment   = eFragment(**self.config("fragment", {}))
        
    def _update(self, dt, step, clock, blocked):
        self.create_spark(self.fragment)        

    def _draw(self, ctx):
        pass

    def _schema(self):
        return {
            "size": ("size", "Size"),
            "position": ("position", "Position"),
            "fragment": ("fragment", "Fragment")
        }

    def create_spark(self, fragment, color = None):
        
        points = self.get_points_spark(fragment)
        for i, point in enumerate(points):
            
           # Angle aléatoire (360°)
            angle = random.uniform(0, 2 * math.pi)

            # Vitesse aléatoire dans cette direction
            speed = random.uniform(30, 70)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Créer la particule
            particle = InnerParticle(position=(point[0], point[1]), velocity=(vx, vy),
                                radius=fragment.get_radius(), lifetime=fragment.get_lifetime(), color=fragment.get_color(color, self.color))
            self.particles.append(particle)


    def get_points_spark(self, fragment):
        points = []       
        text_x_start = self.position.x
        text_y_start = self.position.y
        for i in range(fragment.count):
            x = random.uniform(text_x_start, text_x_start +  self.size.width)
            y = random.uniform(text_y_start, text_y_start +  self.size.height)
            points.append((x, y))
        return points