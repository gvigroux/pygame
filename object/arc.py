import math
import random
import moderngl
import numpy as np
import cairo
import pygame

import conf
from object.object import Object


def color_random():
    return random.randrange(0,100)/100


class Arc(Object):
    
    # VAO/VBO Shared by all arcs
    vao = None
    prog = None
    count = 0


    def __init__(self, context, vbo, radius, angle_start, angle_end):
        super().__init__(context, vbo)
        Arc.count += 1
        self.id = Arc.count
    
        self.window_size = conf.WINDOW_SIZE
        self.radius = radius
        r = color_random()
        g = color_random()
        b = min(1.25-r-g,1.0)
        self.color = (r, g, b, 1.0)
        self.angle_start = angle_start
        self.angle_end = angle_end
        self.angle = 0
        self.line_width = conf.ARC_WIDTH

        print("New ARC " , self.id , " from ", self.angle_start, " to ", self.angle_end)

        self.size = radius * 2 + 20
        data = np.zeros((self.size, self.size, 4), dtype=np.uint8)
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, self.size, self.size)
        ctx_cairo = cairo.Context(surface)
        ctx_cairo.set_antialias(cairo.ANTIALIAS_BEST)
        ctx_cairo.set_line_width(self.line_width)
        ctx_cairo.set_source_rgba(self.color[2], self.color[1], self.color[0], self.color[3])   #BGRA        
        ctx_cairo.arc(self.size // 2, self.size // 2, radius, math.radians(angle_start), math.radians(angle_end))
        ctx_cairo.stroke()
        self.texture = self.context.texture((self.size, self.size), 4, data.tobytes())
        self.texture.build_mipmaps()



        self.speed = random.uniform(*conf.ARC_ROTATION_SPEED_RANGE)

        self.exploding = False
        self.timer = 0
        self.position = np.array([0.0, 0.0], dtype=np.float32)

                
        # --- SHADERS (GPU) ---
        if Arc.vao is None:
            Arc.prog = context.program(
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
            Arc.vao = context.simple_vertex_array(Arc.prog, vbo, 'in_position', 'in_texcoord')


    def is_exploding(self):
        return self.exploding
    
    def is_destroyed(self):
        return self.exploding and self.timer >= 1.0
    
    def explode(self):
        self.exploding = True
        self.timer = 0.0

        
    def update(self, dt):
        if( self.is_destroyed() ):
            return        
        
        self.angle += self.speed #* dt

        if self.exploding:
            self.timer += 3/60
            alpha = max(0.0, 1.0 - self.timer)
        else:
            alpha = 1.0

        angle_rad = math.radians(self.angle)
        scale = self.size / self.window_size[0]
        cos_a = math.cos(angle_rad) * scale
        sin_a = math.sin(angle_rad) * scale

        # Matrice 4x4 pour OpenGL
        model = np.array([
            [cos_a, sin_a, 0.0, 0.0],
            [-sin_a, cos_a, 0.0, 0.0],
            [0.0,    0.0,  1.0, 0.0],
            [0.0,    0.0,  0.0, 1.0],
        ], dtype='f4')


        Arc.prog['model'].write(model.tobytes())
        Arc.prog['alpha'].value = alpha
        Arc.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.texture.use()        
        self.Render(Arc.vao, Arc.prog)

    def get_fragment_points(self, segments=conf.FRAGMENT_COUNT):
        """Renvoie une liste de points en coordonnées monde, pour générer les particules"""
        points = []

        # Angle de départ et de fin en degrés + rotation
        angle_start_deg = (self.angle_start + self.angle) % 360
        angle_end_deg = (self.angle_end + self.angle) % 360

        print(angle_start_deg)
        print(angle_end_deg)

        # Assure que l’arc tourne dans le bon sens
        if angle_end_deg < angle_start_deg:
            angle_end_deg += 360

        angle_step = (angle_end_deg - angle_start_deg) / segments

        for i in range(segments + 1):
            angle_deg = angle_start_deg + i * angle_step
            angle_rad = math.radians(angle_deg)

            x = math.cos(angle_rad) * self.radius
            y = math.sin(angle_rad) * self.radius / self.ratio

            # Appliquer la position de l’arc
            px = (self.window_size[0] // 2) + x
            py = (self.window_size[1] // 2) + y
            points.append((px, py))
        return points


    def get_fragment_pointsOLD(self, segments=conf.FRAGMENT_COUNT):
        """Renvoie une liste de points en coordonnées monde, pour générer les particules"""
        points = []
        
        # Angle de départ et de fin en degrés + rotation
        angle_start_deg = (self.angle_start + self.angle) % 360
        angle_end_deg = (self.angle_end + self.angle) % 360

        print(angle_start_deg)
        print(angle_end_deg)

        # Assure que l’arc tourne dans le bon sens
        if angle_end_deg < angle_start_deg:
            angle_end_deg += 360

        angle_step = (angle_end_deg - angle_start_deg) / segments

        for i in range(segments + 1):
            angle_deg = angle_start_deg + i * angle_step
            angle_rad = math.radians(angle_deg)

            x = math.cos(angle_rad) * self.radius
            y = math.sin(angle_rad) * self.radius

            # Appliquer la position de l’arc
            px = (self.window_size[0] // 2) + x
            py = (self.window_size[1] // 2) - y
            points.append((px, py))
        return points