import math
import random
import cairo
import pygame
#import pygame.gfxdraw
from element.background import eBackground
from element.outline import eOutline
from element.text import eText
from object.inner_particle import InnerParticle
from object.object import Object


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    "fps": 0,
    "seconds": 0,
    'i': 0,
    "fps": 0,
    "step": 0,
    "timing": 0,
    "blocked": 0
}

class TextDraw(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)

        self.text       = eText(**self.config("text", {}))
        self.title      = eText(**self.config("title", {}))
        self.background = eBackground(**self.config("background", {}))
        self.surface_draw = self.config("surface_draw", True)
        self.surfaces   = []

        self.line_height = self.text.font.point_size + 4
        self.surface_background = None
        self.surface_title = None
        self._prepare()
        




    def _draw(self, ctx):
      

        ### Calcul with
        ctx.select_font_face(self.text.font.family)
        ctx.set_font_size(self.text.font.size)
        (x, y, self.text_width, self.text_height, dx, dy) = ctx.text_extents(self.text.value)        
    
        self.background.size = (self.text_width, self.text_height)

        # --- adjust position ---
        if( "H" in self.position.justify ) :
            self.position.x = (self.window_size[0] - self.background.size[0]) // 2
        if( "V" in self.position.justify ) :
            self.position.y = (self.window_size[1] - self.background.size[1]) // 2


        if( self.background.enabled() ):  
            self.set_color(ctx, self.background.color)
            ctx.rectangle(self.position.x, self.position.y,  self.background.size[0],  self.background.size[1])  # dessine le carré
            ctx.fill()  # remplit le carré

        aucune_idee = -5

        ### Dessin du contour noir (4 décalages pour effet "outline") ###
        if( self.text.outline.enabled() ):
            self.set_color(ctx, self.text.outline.color)
            offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2)]  # Décalages autour de la position centrale
            for offset_x, offset_y in offsets:
                ctx.move_to(self.position.x + offset_x + aucune_idee, self.position.y + self.text_height + offset_y)
                ctx.show_text(self.text.value)
            
         ### Dessin du texte rouge principal ###
        ctx.move_to( self.position.x + aucune_idee, self.position.y + self.text_height)
        self.set_color(ctx, self.text.color)
        ctx.show_text(self.text.value)
        ctx.fill()





    def get_points(self, fragment):
        points = []       
        text_x_start = self.position.x
        text_y_start = self.position.y
        for i in range(fragment.count):
            x = random.uniform(text_x_start, text_x_start +  self.background.size[0])
            y = random.uniform(text_y_start, text_y_start +  self.background.size[1])
            points.append((x, y))
        return points
