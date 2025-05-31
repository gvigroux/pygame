


import math
import random
import textwrap
import cairo

from object.object import Object
from object.particle import Particle


class Text(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)

        self.position    = self.config("position", (window_size[0]//2, window_size[1]//2))
        self.radius      = self.config("radius", 10)
        self.bg_color    = self.config("bg_color", (1.0, 1.0, 1.0, 1.0))
        self.bg_radius   = self.config("bg_radius", 5)
        self.bg_size     = self.config("bg_size", (480,10))
        self.text        = self.config("text", "N/A")
        self.title       = self.config("title", "N/A")

        


    def _update(self, dt):
        pass


    def _draw(self, ctx):
        x, y = (self.window_size[0]-self.bg_size[0])//2 , 20
        width, _ = self.bg_size
        max_text_width = width - 2 * self.bg_radius - 5

        # --- Titre ---
        ctx.select_font_face("TikTok Text", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        title_font_size = 24
        ctx.set_font_size(title_font_size)
        title_height = title_font_size + 10

        # --- Préparer texte multiligne ---
        body_font_size = 20
        ctx.set_font_size(body_font_size)

        def wrap_text(ctx, text, max_width):
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                xb, yb, w, h, xa, ya = ctx.text_extents(test_line)
                if w <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            return lines

        lines = wrap_text(ctx, self.text, max_text_width)
        line_height = body_font_size + 4
        text_height = len(lines) * line_height

        # --- Calcul de la hauteur totale ---
        padding = 20
        height = title_height + padding + text_height + padding
        self.bg_size = (width, height)  # Met à jour la hauteur du fond dynamiquement
        y  = self.window_size[1]//8 - height//2


        # --- Dessiner le fond arrondi ---
        ctx.set_source_rgba(*self.bg_color)
        ctx.new_sub_path()
        ctx.arc(x + self.bg_radius, y + self.bg_radius, self.bg_radius, math.pi, 3 * math.pi / 2)
        ctx.arc(x + width - self.bg_radius, y + self.bg_radius, self.bg_radius, 3 * math.pi / 2, 0)
        ctx.arc(x + width - self.bg_radius, y + height - self.bg_radius, self.bg_radius, 0, math.pi / 2)
        ctx.arc(x + self.bg_radius, y + height - self.bg_radius, self.bg_radius, math.pi / 2, math.pi)
        ctx.close_path()
        ctx.fill()

        # Activer l'antialiasing optimal pour le texte
        ctx.set_antialias(cairo.ANTIALIAS_NONE)

        # --- Titre ---
        ctx.set_font_size(title_font_size)
        ctx.set_source_rgb(0.11, 0.63, 0.95) 
        ctx.move_to(x + 10, y + title_font_size + 2)
        ctx.show_text(self.title)

        # --- Texte multiligne ---
        ctx.set_font_size(body_font_size)
        ctx.set_source_rgb(0, 0, 0)  # Noir
        for i, line in enumerate(lines):
            ctx.move_to(x + 10.5, y + padding + title_height + i * line_height + 10.5)
            ctx.show_text(line)
        
        # Forcer l'alignement aux pixels (important !)
        ctx.set_tolerance(0.1)



