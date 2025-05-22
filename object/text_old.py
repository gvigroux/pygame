import math
import random
import moderngl
import numpy as np
import pygame


def color_random():
    return random.randrange(0,100)/100


class Text:

    # VAO/VBO Shared by all instances
    vao = None
    prog = None

    def __init__(self, context, vbo, font, window_size):
        self.window_size = window_size
        self.font = font
        self.context = context

        if Text.vao is None:
            Text.prog = context.program(
                vertex_shader="""
                    #version 330
                    in vec2 in_position;
                    in vec2 in_texcoord;
                    out vec2 v_texcoord;
                    uniform mat4 model;
                    void main() {
                        gl_Position = model * vec4(in_position, 0.0, 1.0);
                        v_texcoord = in_texcoord;
                    }
                """,
                fragment_shader="""
                    #version 330
                    in vec2 v_texcoord;
                    out vec4 fragColor;
                    uniform sampler2D tex;
                    uniform float alpha;
                    void main() {
                        vec4 c = texture(tex, v_texcoord);
                        fragColor = vec4(c.rgb, c.a * alpha);
                    }
                """
            )
            Text.vao = context.simple_vertex_array(Text.prog, vbo, 'in_position', 'in_texcoord')



    def update(self, text, pos, alpha=1.0, scale=1.0):
        surf = self.font.render(text, True, (255, 255, 255), (0, 0, 0))
        tex_data = pygame.image.tobytes(surf, "RGBA", True)
        tex = self.context.texture(surf.get_size(), 4, tex_data)
        tex.build_mipmaps()

        w, h = surf.get_size()
        px, py = pos
        sw, sh = self.window_size

        model = np.eye(4, dtype='f4')
        model[0][0] = scale * w / sw
        model[1][1] = scale * h / sh
        model[3][0] = (px / (sw / 2)) - 1.0
        model[3][1] = 1.0 - (py / (sh / 2))

        Text.prog['model'].write(model.tobytes())
        Text.prog['alpha'].value = alpha
        tex.use()
        Text.vao.render(moderngl.TRIANGLE_STRIP)