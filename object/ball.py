import math
import random
import cairo
import math


from object.object import Object

class Ball(Object):
    def __init__(self, data, window_size, count, id):
        super().__init__(data, window_size, count, id)
        self.id = id
        self.radius     = self.config("radius", 8)
        self.position   = self.config("position", [random.uniform(250, 290), random.uniform(460, 500)])
        self.velocity   = self.config("velocity", [random.uniform(-150, 150), random.uniform(-150, 150)])

    def update(self, dt):
        # Mise à jour de la position
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt

        # Rebond sur les bords
        #if self.position[0] - self.radius < 0 or self.position[0] + self.radius > self.window_width:
        #    self.velocity[0] *= -1
        #    self.position[0] = max(self.radius, min(self.position[0], self.window_width - self.radius))

        #if self.position[1] - self.radius < 0 or self.position[1] + self.radius > self.window_height:
        #    self.velocity[1] *= -1
        #    self.position[1] = max(self.radius, min(self.position[1], self.window_height - self.radius))

    def draw(self, ctx):
        ctx.set_source_rgba(*self.color)
        ctx.arc(self.position[0], self.position[1], self.radius, 0, 2 * math.pi)
        ctx.fill()

    def reflect_velocity(self, normal):
        # v' = v - 2 * (v · n) * n
        v_dot_n = self.velocity[0]*normal[0] + self.velocity[1]*normal[1]
        self.velocity[0] = self.velocity[0] - 2 * v_dot_n * normal[0]
        self.velocity[1] = self.velocity[1] - 2 * v_dot_n * normal[1]




    def ball_hits_arc(self, arc):
        if( arc.exploded ):
            return False
        dx = self.position[0] - arc.position[0] 
        dy = self.position[1] - arc.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        arc_dist = arc.radius - arc.width/2

        # Vérifie si la balle est proche du cercle (arc)
        if dist < arc_dist - self.radius:
            # Dans le "trou" central
            return "inside_hole"
        dy = self.position[1] - arc.position[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Vérifie si la balle est proche du cercle (arc)
        if dist < arc_dist - self.radius:
            # Dans le "trou" central
            return "inside_hole"
        if dist > arc_dist + self.radius:
            # Trop loin pour toucher
            return False
        
        # Calcul angle balle par rapport au centre arc
        angle = math.atan2(dy, dx)
        
        if angle < 0:
            angle += 2 * math.pi
        
        if self.angle_in_arc(angle, arc.start_angle, arc.visible_deg ):
                
            # Calcul normale (direction du centre vers la balle)
            # Rebond
            normal = (dx / dist, dy / dist)
            self.reflect_velocity(normal)
            return "hit_arc"
        else:
            arc.explode()
            return "hit_hole"
        
    def normalize_angle(self, angle):
        # Ramène un angle entre 0 et 2π
        return angle % (2 * math.pi)
    
    
    def angle_in_arc(self, angle, start, extent):
        # angle = position de la balle
        # start = angle de départ de l'arc
        # extent = taille visible de l’arc en radians
        angle = self.normalize_angle(angle)
        start = self.normalize_angle(start)
        end = self.normalize_angle(start + extent)

        if start < end:
            return start <= angle <= end
        else:
            # Cas où l’arc traverse 0°
            return angle >= start or angle <= end