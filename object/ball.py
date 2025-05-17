import moderngl
import numpy as np
import cairo
import random
import math

from pygame import Vector2

import conf
from object.object import Object

class Ball(Object):
    vao = None
    prog = None
    texture = None

    def __init__(self, context, vbo, radius=10):
        super().__init__(context, vbo)
        self.radius = radius
        self.size = radius * 2 + 4

        self.color = (1.0, 1.0, 1.0, 1.0)  # blanc opaque
        #self.position = np.array([random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)], dtype='f4')
        self.position = np.array(conf.BALL_START_POSITION, dtype='f4')
        self.velocity = np.array([random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)], dtype='f4')
        self.velocity = np.array(conf.BALL_VELOCITY, dtype='f4')

        # Texture Cairo (rond blanc)
        data = np.zeros((self.size, self.size, 4), dtype=np.uint8)
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, self.size, self.size)
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        ctx.set_source_rgba(self.color[2], self.color[1], self.color[0], self.color[3])  # BGRA
        ctx.arc(self.size // 2, self.size // 2, radius, 0, 2 * math.pi)
        ctx.fill()
        self.texture = self.context.texture((self.size, self.size), 4, data.tobytes())
        self.texture.build_mipmaps()

        # Shaders et VAO partagés
        if Ball.vao is None:
            Ball.prog = context.program(
                vertex_shader="""
                    #version 330
                    in vec2 in_position;
                    in vec2 in_texcoord;
                    out vec2 v_texcoord;
                    uniform mat4 model;
                    uniform mat4 projection;
                    void main() {
                        gl_Position = projection * model * vec4(in_position, 0.0, 1.0);
                        v_texcoord = in_texcoord;
                    }
                """,
                fragment_shader="""
                    #version 330
                    in vec2 v_texcoord;
                    out vec4 fragColor;
                    uniform sampler2D tex;
                    uniform float alpha;
                    uniform float time;
                    void main() {
                        vec4 color = texture(tex, v_texcoord);
                        fragColor = vec4(color.rgb, color.a * alpha);
                        fragColor += vec4(0.0, 0.0, 0.0, 0.0001 * time);
                    }
                """
            )
            Ball.vao = context.simple_vertex_array(Ball.prog, vbo, 'in_position', 'in_texcoord')

    def update(self, dt):

        self.position += self.velocity  # * dt * 60

        # Bords de l'écran (rebond)
        for i in range(2):
            if self.position[i] < -1.0 or self.position[i] > 1.0:
                self.velocity[i] *= -1.0
                self.position[i] = max(min(self.position[i], 1.0), -1.0)


    def collision_with_arc(self, arc):
        """Détecte une collision avec un arc et renvoie la direction du rebond"""
        # to_ball = np.array(self.position) - np.array(arc.position)
        # norm = to_ball / np.linalg.norm(to_ball)  # normalisée
        # v = np.array(self.velocity)
        # reflected = v - 2 * np.dot(v, norm) * norm
        # self.velocity = reflected

        delta = self.position - arc.position
        distance = np.linalg.norm(delta)
        direction = delta / (distance + 1e-6)
        self.velocity -= 2 * np.dot(self.velocity, direction) * direction



    def get_fragment_points(self, segments=conf.FRAGMENT_COUNT):
        """Renvoie une liste de points en coordonnées monde, pour générer les particules"""
        points = []
        
        # Position de la balle en pixels
        cx, cy = self.gl_to_screen(self.position)
        
        #for i in range(segments + 1):
        #    points.append((cx, cy))
        #return points

        # Rayon en pixels
        radius = self.radius

        # Angle entre chaque point
        angle_step = 2 * math.pi / segments

        for i in range(segments + 1):
            theta = i * angle_step

            dx = math.cos(theta) * radius
            dy = math.sin(theta) * radius

            x = cx + dx
            y = cy - dy
            points.append((x, y))

        return points


    
    def collision_zone(self, arc):

        """
        Retourne :
        - 'arc' si la balle touche l'arc visible
        - 'hole' si la balle est dans le trou
        - None si aucune collision
        """
        aspect_ratio = self.window_size[0] / self.window_size[1]
        dx = (self.position[0] - arc.position[0]) * self.window_size[0] / 2
        dy = (self.position[1] - arc.position[1]) * self.window_size[1] / 2
        # Corrige dy en appliquant l'aspect ratio
        dy *= aspect_ratio

        distance = math.hypot(dx, dy)
        angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        
        touch = ( distance >= (arc.radius - arc.line_width - self.radius) )
        if( not touch ):
            return None  

        # Angle effectif
        angle_start = (arc.angle_start + arc.angle) % 360
        angle_end = (arc.angle_end + arc.angle) % 360

        # Cercle
        if( angle_end == angle_start ):
            return 'arc'
        
        if angle_start <= angle_end:
            in_sector = angle_start <= angle <= angle_end
        else:
            in_sector = angle >= angle_start or angle <= angle_end
        return 'arc' if in_sector else 'hole'
     
        
        # # Vecteur centre_arc → balle
        # dx = self.position[0] -  arc.position[0]
        # dy = self.position[1] -  arc.position[1]

        # dx = dx * self.window_size[0] / 2
        # dy = dy * self.window_size[1] / 2

        # # Calcul de l’angle de la balle par rapport à l’arc
        # angle_to_ball = (math.degrees(math.atan2(dy, dx)) + 360) % 360


        # distance = math.hypot(dx, dy)
        # #in_ring = r_int <= distance <= r_ext
        # in_ring = ( distance >= (arc.radius - arc.line_width - self.radius) )

        # if( not in_ring ):
        #     return None       

        # # Corriger le secteur angulaire à cause de la rotation
        # effective_start = (arc.angle_start + arc.angle) % 360
        # effective_end = (arc.angle_end + arc.angle) % 360

        # # Vérifie si l'angle est dans le bon intervalle
        # if effective_start <= effective_end:
        #     in_angle = effective_start <= angle_to_ball <= effective_end
        # else:
        #     in_angle = angle_to_ball >= effective_start or angle_to_ball <= effective_end

        # if in_angle:
        #     return 'arc'
        # else:
        #     return 'hole'
    
    
    def draw(self):
        # Transformation
        scale = self.size / self.window_size[0]
        model = np.array([
            [scale, 0.0,   0.0, 0.0],
            [0.0,   scale, 0.0, 0.0],
            [0.0,   0.0,   1.0, 0.0],
            [self.position[0], self.position[1], 0.0, 1.0]
        ], dtype='f4')

        Ball.prog['model'].write(model.tobytes())
        Ball.prog['alpha'].value = 1.0
        self.texture.use()
        self.Render(Ball.vao, Ball.prog)
