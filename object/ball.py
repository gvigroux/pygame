import math
import random
import cairo
import math


from element.text import eText
from object.arc import Arc
from object.object import Object
from object.inner_particle import InnerParticle

class Ball(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)
        self.radius     = self.config("radius", 8)
        self.velocity   = self.config("velocity", [random.uniform(-150, 150), random.uniform(-150, 150)])
        self.text       = eText(**self.config("text", {}))
        self.collision_margin = 1.5
          

    def _update(self, dt, step, clock, blocked):

        self.position.x += self.velocity[0] * dt
        self.position.y += self.velocity[1] * dt

        # Rebond sur les bords
        if self.position.x - self.radius < 0 or self.position.x + self.radius > self.window_size[0]:
            self.velocity[0] *= -1
            self.position.x = max(self.radius, min(self.position.x, self.window_size[0] - self.radius))

        if self.position.y - self.radius < 0 or self.position.y + self.radius > self.window_size[1]:
            self.velocity[1] *= -1
            self.position.y = max(self.radius, min(self.position.y, self.window_size[1] - self.radius))

    def _draw(self, ctx):
        # BALL BASIC
        #ctx.arc(self.position[0], self.position[1], self.radius, 0, 2 * math.pi)
        #ctx.fill()
        #return 
    
        #BALL GRADIENT   
        gradient = cairo.RadialGradient(
            self.position.x, self.position.y, 0,                     # Centre du gradient
            self.position.x, self.position.y, self.radius            # Rayon du gradient
        )
        r, g, b, a = self.normalize_color(self.color)
        gradient.add_color_stop_rgba(0, min(r + 0.3, 1.0), min(g + 0.3, 1.0), min(b + 0.3, 1.0), self.alpha)
        gradient.add_color_stop_rgba(1, r * 0.4, g * 0.4, b * 0.4, self.alpha)


        ctx.arc(self.position.x, self.position.y, self.radius, 0, 2 * math.pi)
        ctx.set_source(gradient)
        ctx.fill()


        # ✅ Écriture du numéro au centre
        if self.text.enabled():
            ctx.save()
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(self.radius * 1.0)  # Taille relative au rayon

            text = str(self.text.value)
            # Obtenir la taille du texte
            xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(text)
            # Calcul pour centrer le texte
            x_text = self.position.x - width / 2 - xbearing
            y_text = self.position.y + height / 2

            ctx.set_source_rgba(1, 1, 1, 1)  # Blanc
            ctx.move_to(x_text, y_text)
            ctx.show_text(text)
            ctx.new_path()
            ctx.restore()
            
       
    def _draw_shadow(self, ctx): 
        ctx.arc(
            self.position.x + self.shadow_offset,
            self.position.y + self.shadow_offset,
            self.radius - 3, 0, 2 * math.pi
        )
        ctx.stroke()
        
    def reflect_velocity(self, normal):
        dot = 2 * (self.velocity[0]*normal[0] + self.velocity[1]*normal[1])
        self.velocity[0] -= dot * normal[0]
        self.velocity[1] -= dot * normal[1]


    def check_collision(self, object):
        if( isinstance(object, Ball) ):
            if( self.check_ball_collision(object) ):
                self.ball_collision(object)
        elif( isinstance(object, Arc) ):            
            zone = self.check_arc_collision(object)
            if( zone == "hit_hole" ):
                object.explode()
            elif( zone == "hit_arc" ):
                self.arc_collision(object)



    def check_ball_collision(self,ball):

        if ball.exploded:
            return False        
        
        dx = self.position.x - ball.position.x
        dy = self.position.y - ball.position.y
        dist_squared = dx*dx + dy*dy
        radius_sum = self.radius + ball.radius
        return dist_squared <= radius_sum * radius_sum
    


    def ball_collision(self, ball):
        # 1. Échange des vitesses (conservation de l'énergie cinétique)
        self.velocity, ball.velocity = ball.velocity, self.velocity
        
        # 2. Séparation physique pour éviter le collage
        dx = self.position.x - ball.position.x
        dy = self.position.y - ball.position.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Vecteur de direction normalisé
        nx = dx / distance
        ny = dy / distance
        
        # Décalage minimal pour séparer les balles
        min_separation = (self.radius + ball.radius) * 1.01  # 1% de marge
        
        # Ajustement des positions
        overlap = min_separation - distance
        self.position.x += nx * overlap * 0.5
        self.position.y += ny * overlap * 0.5
        ball.position.x -= nx * overlap * 0.5
        ball.position.y -= ny * overlap * 0.5 

        self.create_particles(self.collision.fragment, self.color)
        ball.create_particles(ball.collision.fragment, ball.color)

        self.accelerate(ball.collision.acceleration)
        ball.collision.play()
        

    def check_arc_collision(self, arc):
        if arc.exploded:
            return False

        if not arc.is_alive(self.current_step):
            return False
        
        if not arc.should_draw:
            return False

        dx = self.position.x - arc.position.x
        dy = self.position.y - arc.position.y
        dist_sq = dx * dx + dy * dy

        inner = (arc.radius - arc.width / 2) - self.radius
        outer = (arc.radius + arc.width / 2) + self.radius

        if dist_sq < inner * inner or dist_sq > outer * outer:
            return False

        angle = self.normalize_angle(math.atan2(dy, dx))

        arc_start = self.normalize_angle(arc.start_angle)
        arc_end = self.normalize_angle(arc.start_angle + arc.visible_rad)

        in_arc = self.is_angle_in_arc(angle, arc_start, arc_end)

        return "hit_arc" if in_arc else "hit_hole"


    def is_angle_in_arc(self, angle, arc_start, arc_end):
        """Retourne True si angle est dans l'arc [arc_start, arc_end] en gérant le passage par 0°."""
        if arc_start <= arc_end:
            return arc_start <= angle <= arc_end
        else:
            return angle >= arc_start or angle <= arc_end


    def arc_collision(self, arc):
        # 1. Calcul vectoriel sécurisé
        dx = self.position.x - arc.position.x
        dy = self.position.y - arc.position.y
        dist = max(math.sqrt(dx*dx + dy*dy), 0.001)
        
        # 2. Vecteurs normal
        nx, ny = dx/dist, dy/dist  # Normal vers l'extérieur
        
        # 3. Réflexion physique réaliste
        self.reflect_velocity((nx, ny))

        # 4. Effets secondaires       
        self.accelerate(arc.collision.acceleration)
        self.create_particles(arc.collision.fragment, arc.color)
        arc.collision.play()

    def accelerate(self, acceleration):
        self.velocity[0] *= acceleration[0]
        self.velocity[1] *= acceleration[1]


        
    def normalize_angle(self, angle):
        # Ramène un angle entre 0 et 2π
        return angle % (2 * math.pi)
    
    