import math
import random
import cairo
import pygame
import pygame.gfxdraw
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

class Text(Object):
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
        

    def _prepare(self):
        if( not self.surface_draw ):
            return
        
        # Clean surfaces
        self.surfaces = []

        # Padding: haut | droit | bas | gauche
        max_text_width = self.window_size[0] - self.text.padding[1] - self.text.padding[3] - self.text.outline.width*2
        
        # --- Préparer le texte multiligne ---
        lines, width = self._wrap_text(self.text.value, max_text_width)
        text_height = len(lines) * self.line_height

        # --- Calcul de la hauteur totale ---
        height = text_height + self.text.padding[0] + self.text.padding[2] + self.text.outline.width*2
        if( self.title.enabled() ):
            height = round(self.title.font.point_size + self.title.padding[0] + self.title.padding[2])
        

        width += self.text.padding[1] + self.text.padding[3] + self.text.outline.width*2
        self.background.size = (width, height)  # Met à jour la hauteur du fond dynamiquement

        # --- adjust position ---
        if( "H" in self.position.justify ) :
            self.position.x = (self.window_size[0] - self.background.size[0]) // 2
        if( "V" in self.position.justify ) :
            self.position.y = (self.window_size[1] - self.background.size[1]) // 2

        # --- background --- 
        if( self.background.enabled() ):  
            self.surface_background  = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(
                self.surface_background,
                self.background.getColor(self.alpha*255),
                (0, 0, width, height),
                border_radius=self.background.radius
            )        

        self.height_position = 0
            
        # --- Titre ---
        if( self.title.enabled() ):
            title_surface = self.title.font.render(self.title.value, True, (28, 161, 242)).convert_alpha()
            title_surface.set_alpha(self.alpha * 255)
            self.height_position += self.title.font.point_size + self.title.padding[2] + self.title.padding[0]
        
        # --- Texte long > multiligne ---
        for i, line in enumerate(lines):
            surface = self.render_text_with_outline(self.text.font.sysFont, line, self.text.color, self.text.outline)
            surface.set_alpha(self.alpha * 255)
            self.surfaces.append(surface)
            
        
    def _update(self, dt, step, clock, blocked):

        if( step >= self.step.stop and self.step.explode ):
            self.explode()
            return

        if( len(self.text.update) > 0 ):
            safe_globals["seconds"] = int(self.age/1000)
            safe_globals["fps"] = int(clock.get_fps())
            safe_globals["step"] = int(step)
            safe_globals["blocked"] = int(blocked)
            safe_globals["timing"] = self.age/1000.0
            x, y = self.pygame.mouse.get_pos()
            safe_globals["mouse"] = f"{x*100/self.window_size[0]:.1f}% / {y*100/self.window_size[1]:.1f}%"

            val = str(eval(self.text.update, {"__builtins__": {}}, safe_globals))
            if( val != self.text.value ):
                self.text.value = val
                self._prepare()



    def _draw(self, ctx):

        if( self.surface_draw ):
            return        

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




    def _draw_surface(self, screen):
        if( not self.surface_draw ):
            return

        if( self.surface_background is not None):
            screen.blit(self.surface_background , (self.position.x, self.position.y))

        if( self.surface_title is not None):
            screen.blit(self.surface_title , (self.position.x + self.title.padding[1], self.position.y + self.title.padding[3] ))

        i = 0
        for surface in self.surfaces:
            #TODO: do the setalpha in the surface and update the surface when the value change
            alpha = min(self.alpha*255 , self.text.color[3])
            surface.set_alpha(alpha)
            screen.blit(surface, (self.position.x, self.position.y + self.height_position + i * self.line_height))
            i += 1


    def get_points(self, fragment):
        points = []       
        text_x_start = self.position.x
        text_y_start = self.position.y
        for i in range(fragment.count):
            x = random.uniform(text_x_start, text_x_start +  self.background.size[0])
            y = random.uniform(text_y_start, text_y_start +  self.background.size[1])
            points.append((x, y))
        return points



    def render_text_with_outline(self, font, text, text_color, outline):
       
        # La surface comprend le fond + l'outline autour
        surf_width  = self.background.size[0] #+ outline.width * 2
        surf_height = self.background.size[1] #+ outline.width * 2

        outline_surface = pygame.Surface((surf_width, surf_height), pygame.SRCALPHA)

        # Texte + outline
        text_surface = font.render(text, True, text_color)

        # Position du texte centrée sur la zone "background"
        text_x = (surf_width - text_surface.get_width()) // 2
        text_y = (surf_height - text_surface.get_height()) // 2

        # Outline = copies décalées autour
        if outline.width > 0:
            for dx in [-outline.width, 0, outline.width]:
                for dy in [-outline.width, 0, outline.width]:
                    if dx != 0 or dy != 0:
                        outline_text = font.render(text, True, outline.color)
                        outline_surface.blit(outline_text, (text_x + dx, text_y + dy))

        # Texte principal
        outline_surface.blit(text_surface, (text_x, text_y))

        return outline_surface


    def _wrap_text(self, text, max_width):
        """Version améliorée qui retourne :
        - les lignes découpées
        - la largeur maximale trouvée
        
        Gère à la fois les sauts de ligne manuels (\n) et le wrapping automatique"""
        
        paragraphs = text.split('\n')
        lines = []
        max_line_width = 0  # Variable pour stocker la largeur maximale
        
        for paragraph in paragraphs:
            words = paragraph.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_width = self.text.font.sysFont.size(test_line)[0]
                
                if test_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        current_width = self.text.font.sysFont.size(current_line)[0]
                        max_line_width = max(max_line_width, current_width)
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                current_width = self.text.font.sysFont.size(current_line)[0]
                max_line_width = max(max_line_width, current_width)
                lines.append(current_line)
            
            if not paragraph.strip():
                lines.append("")
                # Une ligne vide a une largeur de 0
                max_line_width = max(max_line_width, 0)
        
        return lines, max_line_width