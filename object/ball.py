import math
import random
import cairo
import math


from object.arc import Arc
from object.object import Object
from object.inner_particle import InnerParticle

class Ball(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)
        self.radius     = self.config("radius", 8)
        self.velocity   = self.config("velocity", [random.uniform(-150, 150), random.uniform(-150, 150)])
        self.collision_margin = 1.5
        self.bounce_sound    = self.pygame.mixer.Sound("media/sound/retro/SoundJump2.wav")
        self.explosion_sound = self.pygame.mixer.Sound("media/sound/retro/SoundLand2.wav")
        self.bounce_sound.set_volume(0.1)
        self.explosion_sound.set_volume(0.1)
          

    def _update(self, dt, step, clock):

        self.position.x += self.velocity[0] * dt
        self.position.y += self.velocity[1] * dt

        # Rebond sur les bords
        #if self.position[0] - self.radius < 0 or self.position[0] + self.radius > self.window_width:
        #    self.velocity[0] *= -1
        #    self.position[0] = max(self.radius, min(self.position[0], self.window_width - self.radius))

        #if self.position[1] - self.radius < 0 or self.position[1] + self.radius > self.window_height:
        #    self.velocity[1] *= -1
        #    self.position[1] = max(self.radius, min(self.position[1], self.window_height - self.radius))

    def _draw(self, ctx):
        # BALL BASIC
        #ctx.arc(self.position[0], self.position[1], self.radius, 0, 2 * math.pi)
        #ctx.fill()
        #return 
        #if(  self.first_draw == False ):
            #bounce_sound    = self.pygame.mixer.Sound("media/sound/retro/SoundJump2.wav")
        #    self.bounce_sound.play()
    
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
                print("Hit & explose arc")
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
    
    # def ball_collision2(self, ball):
    #         v = self.velocity
    #         self.velocity = ball.velocity
    #         ball.velocity = v

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


        #self.create_particles(ball.collision.fragment.count, ball.collision.fragment.get_color(ball.color))
        ball.collision.play()
        

    def check_arc_collision(self, arc):

        if(arc.exploded):
            return False
        
        if(not arc.is_alive(self.current_step)):
            return False
        
        dx = self.position.x - arc.position.x
        dy = self.position.y - arc.position.y
        dist_sq = dx*dx + dy*dy
        
        # Calcul des rayons critiques
        inner = (arc.radius - arc.width/2) - self.radius
        outer = (arc.radius + arc.width/2) + self.radius
        
        # Vérification rapide des limites
        if dist_sq < inner*inner or dist_sq > outer*outer:
            return False
        
        # Calcul précis de l'angle
        angle = math.atan2(dy, dx) % (2*math.pi)
        arc_end = (arc.start_angle + arc.visible_rad) % (2*math.pi)
        
        # Gestion des angles croisant 0°
        if arc.start_angle > arc_end:
            in_arc = angle >= arc.start_angle or angle <= arc_end
        else:
            in_arc = arc.start_angle <= angle <= arc_end
        
        return "hit_arc" if in_arc else "hit_hole"



    def arc_collision(self, arc):
        # 1. Calcul vectoriel sécurisé
        dx = self.position.x - arc.position.x
        dy = self.position.y - arc.position.y
        dist = max(math.sqrt(dx*dx + dy*dy), 0.001)
        
        # 2. Vecteurs normal/tangentiel
        nx, ny = dx/dist, dy/dist  # Normal vers l'extérieur
        tx, ty = -ny, nx           # Tangentiel
        
        # 3. Réflexion physique réaliste (votre méthode conservée)
        self.reflect_velocity((nx, ny))
        
        # 4. Correction de position ANTI-TRAVERSEMENT (version corrigée)
        # collision_depth = (arc.radius + self.radius) - dist
        # if collision_depth > 0:
        #     # Pousse dans la direction NORMALE (nx, ny) uniquement
        #     push_distance = collision_depth * 1.05  # 5% de marge
        #     self.position[0] += nx * push_distance
        #     self.position[1] += ny * push_distance
        
        # 5. Effets secondaires        
        self.velocity[0] *= arc.collision.acceleration[0]
        self.velocity[1] *= arc.collision.acceleration[1]

        self.create_particles(arc.collision.fragment, arc.color)
        arc.collision.play()

        
    def normalize_angle(self, angle):
        # Ramène un angle entre 0 et 2π
        return angle % (2 * math.pi)
    
    
    def angle_in_arc(self, angle, start, extent):
        # angle = position de la balle
        # start = angle de départ de l'arc
        # extent = taille visible de l’arc en radians
        angle   = self.normalize_angle(angle)
        start   = self.normalize_angle(start)
        end     = self.normalize_angle(start + extent)

        if start < end:
            return start <= angle <= end
        else:
            # Cas où l’arc traverse 0°
            return angle >= start or angle <= end