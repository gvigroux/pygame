import math
import random
import moderngl
import numpy as np
import cairo
import pygame

from object.object import Object


def color_random():
    return random.randrange(0,100)/100


class Arc(Object):
    
    # VAO/VBO Shared by all arcs
    vao = None
    prog = None


    def __init__(self, context, vbo, json, window_size, amount =1, i = 1):
        super().__init__(context, vbo, json, window_size, amount, i)

        self.radius      = self.config("radius", 10)
        self.angle_start = self.config("angle_start", 0)
        self.angle_end   = self.config("angle_end", 330)
        self.width       = self.config("width", 5)
        self.speed       = self.config("speed", random.uniform(-2, 2))

        self.angle = 0

        self.size = self.radius * 2 + 20
        data = np.zeros((self.size, self.size, 4), dtype=np.uint8)
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, self.size, self.size)
        ctx_cairo = cairo.Context(surface)
        ctx_cairo.set_antialias(cairo.ANTIALIAS_BEST)
        ctx_cairo.set_line_width(self.width)
        ctx_cairo.set_source_rgba(self.color[2], self.color[1], self.color[0], self.color[3])   #BGRA        
        ctx_cairo.arc(self.size // 2, self.size // 2, self.radius, math.radians(self.angle_start), math.radians(self.angle_end))
        ctx_cairo.stroke()
        self.texture = self.context.texture((self.size, self.size), 4, data.tobytes())
        self.texture.build_mipmaps()
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


        
    def update(self, dt):
        if( self.is_destroyed() ):
            return
                
        self.angle += self.speed #* dt

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
        Arc.prog['alpha'].value = self.alpha()
        Arc.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.texture.use()        
        self.Render(Arc.vao, Arc.prog)

    def get_fragment_points(self):
        """Renvoie une liste de points en coordonnées monde, pour générer les particules"""
        points = []
        segments = self.fragments_explode

        # Angle de départ et de fin en degrés + rotation
        angle_start_deg = (self.angle_start + self.angle) % 360
        angle_end_deg = (self.angle_end + self.angle) % 360

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
