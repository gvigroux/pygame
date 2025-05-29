


import math
import random

import cairo

from object.object import Object
from object.particle import Particle


class Counter(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id) 
        self.position   = (-1, -1)
        self.text       = "00"
    

    def _update(self, dt):
        minutes, self.seconds = divmod(int(self.age/1000), 60)
        self.text = f"{self.seconds:02d}"
        pass   

    def _draw(self, ctx):
        ctx.select_font_face("Wumpus Mono Pro")
        ctx.set_font_size(80)
        (x, y, width, height, dx, dy) = ctx.text_extents(self.text)        
        if self.position[0] == -1:
            self.position = (self.window_size[0]/2 - width/2, self.window_size[1]/2 + height/2)

        ### Dessin du contour noir (4 décalages pour effet "outline") ###
        ctx.set_source_rgb(0.2, 0.2, 0.2)  # Noir
        offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2)]  # Décalages autour de la position centrale
        for offset_x, offset_y in offsets:
            ctx.move_to(self.position[0] + offset_x, self.position[1] + offset_y)
            ctx.show_text(self.text)
            
         ### Dessin du texte rouge principal ###
        ctx.move_to( self.position[0], self.position[1])
        ctx.set_source_rgb(0, 0, 0.7)
        ctx.show_text(self.text)

 

        ctx.fill()

