import math
import cairo
import moderngl
import numpy as np
import pygame
from background.background import Background
import conf


class Red(Background):

    def __init__(self, context, vbo):
        super().__init__(context, vbo)
        self.prog = context.program(
            vertex_shader="""
                #version 330
                in vec2 in_position;
                in vec2 in_texcoord;
                out vec2 v_texcoord;

                void main() {
                    gl_Position = vec4(in_position, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader="""
                #version 330
                in vec2 v_texcoord;
                out vec4 fragColor;
                uniform sampler2D tex;

                void main() {
                    fragColor = texture(tex, v_texcoord);
                }
            """)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_position', 'in_texcoord') 


    def Draw(self):
        self.bg_frame_counter += 1
        if self.bg_frame_counter % 4 != 0:
            return
        t = pygame.time.get_ticks() / 1000.0  # temps en secondes
        background_tex = self.generate_background_texture(conf.WINDOW_SIZE, t)
        background_tex.use(0)
        self.prog['tex'] = 0
        self.vao.render(moderngl.TRIANGLE_STRIP)


    def generate_background_texture(self, size, t):
        """Crée une texture de fond animée (dégradé radial avec Cairo)."""
        width, height = size
        data = np.zeros((height, width, 4), dtype=np.uint8)
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        # Dégradé radial animé (ex : pulser la couleur centrale)
        radius = width * 0.5
        grad = cairo.RadialGradient(width/2, height/2, 100 + 30 * math.sin(t),
                                    width/2, height/2, radius)
        grad.add_color_stop_rgba(0.0, 0.1, 0.1, 0.4 + 0.3 * math.sin(t), 1.0)
        grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 1.0)

        ctx.set_source(grad)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        tex = self.context.texture(size, 4, data.tobytes())
        tex.build_mipmaps()
        return tex

