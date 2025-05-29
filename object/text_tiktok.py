


import math
import random

import cairo

from object.object import Object
from object.particle import Particle


class TextTikTok(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)

        self.position    = self.config("position", (window_size[0]//2, window_size[1]//2))
        self.radius      = self.config("radius", 10)
        self.bg_color    = self.config("bg_color", (1.0, 1.0, 1.0, 1.0))
        self.bg_radius   = self.config("bg_radius", 5)
        self.bg_size     = self.config("bg_size", (500,50))
        self.text        = self.config("text", "N/A")
        self.title       = self.config("title", "N/A")
        self.position    = self.config("position", "center")
        self.font_large = pygame.font.SysFont("Impact", 48)  # Police épaisse comme TikTok
        self.font_small = pygame.font.SysFont("Arial", 24, bold=True)
        self.colors = {
            'text': (255, 255, 255),  # Blanc
            'background': (0, 0, 0, 128),  # Noir semi-transparent
            'accent': (254, 44, 85)  # Rose TikTok
        }


    def _update(self, dt):
        pass

    def _draw(self, ctx):
        """Dessine une question style TikTok avec Cairo (ctx)"""
        # Paramètres visuels
        bg_color = (0, 0, 0, 0.7)  # Noir semi-transparent
        text_color = (1, 1, 1)      # Blanc
        accent_color = (0.99, 0.16, 0.33)  # Rose TikTok (#FD2D55)
        border_radius = 25.0
        padding = 30
        
        # Dimensions
        max_width = self.window_size[0] - 40
        text_height = 60
        
        # Positionnement
        if self.position == "center":
            y_pos = self.window_size[1] // 2
        elif self.position == "bottom":
            y_pos = self.window_size[1] - 100
        else:  # top par défaut
            y_pos = 100
        
        # --- Fond arrondi ---
        ctx.new_path()
        
        # Rectangle avec coins arrondis
        x, y = 20, y_pos - text_height - padding//2
        width, height = max_width, text_height + padding
        
        # Dessin des coins arrondis
        ctx.arc(x + border_radius, y + border_radius, border_radius, math.pi, 3*math.pi/2)
        ctx.arc(x + width - border_radius, y + border_radius, border_radius, 3*math.pi/2, 2*math.pi)
        ctx.arc(x + width - border_radius, y + height - border_radius, border_radius, 0, math.pi/2)
        ctx.arc(x + border_radius, y + height - border_radius, border_radius, math.pi/2, math.pi)
        ctx.close_path()
        
        # Remplissage semi-transparent
        ctx.set_source_rgba(*bg_color)
        ctx.fill_preserve()
        
        # Bordure rose
        ctx.set_source_rgb(*accent_color)
        ctx.set_line_width(3)
        ctx.stroke()
        
        # --- Texte ---
        # Configuration de la police (style Impact)
        ctx.select_font_face("Impact", 
                        cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(48)
        
        # Effet de contour noir
        text_extents = ctx.text_extents(self.text)
        text_x = (self.window_size[0] - text_extents.width) / 2
        text_y = y_pos
        
        # Contour noir (4 fois décalé)
        ctx.set_source_rgb(0, 0, 0)
        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            ctx.move_to(text_x + dx, text_y + dy)
            ctx.show_text(self.text)
        
        # Texte principal blanc
        ctx.set_source_rgb(*text_color)
        ctx.move_to(text_x, text_y)
        ctx.show_text(self.text)
        
        # Hashtag optionnel en bas
        ctx.select_font_face("Arial", 
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24)
        ctx.set_source_rgb(*accent_color)
        ctx.move_to(x + width - 100, y + height - 15)
        ctx.show_text("#Question")


    def drawdd(self, ctx, surface, question):
#        Positionnement
        if self.position == "center":
            pos = (self.window_size[0]//2, self.window_size[1]//2)
        elif self.position == "top":
            pos = (self.window_size[0]//2, 100)
        else:  # bottom
            pos = (self.window_size[0]//2, self.window_size[1] - 100)
        
        # Fond arrondi
        rect = self.pygame.Rect(0, 0, min(600, self.window_size[0]-40), 120)
        rect.center = pos
        
        # Fond semi-transparent avec bordure rose
        shape_surf = self.pygame.Surface((rect.w, rect.h), self.pygame.SRCALPHA)
        self.pygame.draw.rect(shape_surf, self.colors['background'], 
                            (0, 0, rect.w, rect.h), border_radius=25)
        self.pygame.draw.rect(shape_surf, self.colors['accent'], 
                            (0, 0, rect.w, rect.h), width=3, border_radius=25)
        
        surface.blit(shape_surf, rect.topleft)
        
        # Texte avec contour (effet "Impact")
        text = self.font_large.render(self.text, True, self.colors['text'])
        text_rect = text.get_rect(center=pos)
        
        # Contour noir pour meilleure lisibilité
        for offset in [(-2,0),(2,0),(0,-2),(0,2)]:
            surface.blit(self.font_large.render(self.text, True, (0,0,0)), 
                        (text_rect.x+offset[0], text_rect.y+offset[1]))
        
        surface.blit(text, text_rect)
        
        # Petit hashtag en bas (optionnel)
        tag = "#Question"
        tag_text = self.font_small.render(tag, True, self.colors['accent'])
        surface.blit(tag_text, (rect.right-100, rect.bottom-30))



