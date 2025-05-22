import cairo
import numpy as np
import math
from object.object import Object  # ta classe mère

class Text(Object):
    vao = None
    prog = None

    def __init__(self, context, vbo, data,window_size=[800, 600]):
        super().__init__(context, vbo, data=data, window_size=window_size)

        

        self.text           = self.config("text", "N/A")
        self.font_size      = self.config("font_size", 40)
        self.font_family    = self.config("font_family", "Sans")
        self.position       = np.array(self.config("position", [0.0, 0.0]), dtype='f4')
        self.bg_color       = self.config("bg_color", (1.0, 1.0, 1.0))
        self.size           = self.config("size", [200,200])



        width = 200
        height = 100
        radius = 10
        padding = 10

        surface_width = width + 2 * padding
        surface_height = height + 2 * padding

        

        surface_size = self.font_size * len(self.text) + 2 * padding
        data = np.zeros((surface_size, surface_size, 4), dtype=np.uint8)
        #surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, surface_size, surface_size)
        
        ctx = cairo.Context(surface)

        width = surface_size
        height = surface_size

        # --- Dessin de la bulle arrondie ---
        ctx.set_source_rgba(1, 1, 1, 1)  # Fond blanc
        ctx.new_path()
        ctx.arc(radius, radius, radius, math.pi, 1.5 * math.pi)
        ctx.arc(width - radius, radius, radius, 1.5 * math.pi, 0)
        ctx.arc(width - radius, height - radius, radius, 0, 0.5 * math.pi)
        ctx.arc(radius, height - radius, radius, 0.5 * math.pi, math.pi)
        ctx.close_path()
        ctx.fill()

        # # --- (Optionnel) Bordure grise ---
        # ctx.set_source_rgba(0.8, 0.8, 0.8, 1)  # Gris clair
        # ctx.set_line_width(2)
        # ctx.stroke()

        # --- Texte ---
        ctx.set_source_rgba(0, 0, 0, 1)  # Texte noir
        ctx.select_font_face(self.font_family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(self.font_size)

        xbearing, ybearing, tw, th, xadvance, yadvance = ctx.text_extents(self.text)
        tx = (width - tw) / 2 - xbearing
        ty = (height + th) / 2 - ybearing

        ctx.move_to(tx, ty)
        ctx.show_text(self.text)

        # Création de la texture
        self.texture = context.texture((surface_size, surface_size), 4, data.tobytes())
        self.texture.build_mipmaps()

        # Shaders (1 fois pour tous)
        if Text.vao is None:
            Text.prog = context.program(
                vertex_shader="""
                    #version 330
                    in vec2 in_position;
                    in vec2 in_texcoord;
                    out vec2 v_texcoord;
                    uniform mat4 model;
                    uniform mat4 projection;
                    void main() {
                        gl_Position = projection * model * vec4(in_position, 0.0, 1.0);
                        v_texcoord = vec2(in_texcoord.x, 1.0 - in_texcoord.y);
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
                """
            )
            Text.vao = context.simple_vertex_array(Text.prog, vbo, 'in_position', 'in_texcoord')

    def draw(self):
        size = 0.9  # Ajuste la taille
        model = np.array([
            [size, 0.0, 0.0, 0.0],
            [0.0, size, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [self.position[0], self.position[1], 0.0, 1.0],
        ], dtype='f4')
        Text.prog['model'].write(model.tobytes())
        #Text.prog['projection'].write(self.projection_matrix)
        self.texture.use()
        self.Render(Text.vao, Text.prog)
