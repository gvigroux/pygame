import cairo
import pygame
import pygame.gfxdraw
from element.background import eBackground
from element.outline import eOutline
from element.text import eText
from object.object import Object



class Text(Object):
    def __init__(self, data, pygame, screen, window_size, count, id):
        super().__init__(data, pygame, screen, window_size, count, id)

        self.position   = self.config("position", (window_size[0]//2, window_size[1]//2))
        self.center      = self.config("center", "")
        self.show        = True

        self.text       = eText(**self.config("text", {}))
        self.title      = eText(**self.config("title", {}))
        self.background = eBackground(**self.config("background", {}))

        self.surfaces = []
        self.line_height = self.text.font.point_size + 4
        self.surface_background = None
        self.surface_title = None
        self._prepare()
        

    def _prepare(self):

        max_text_width = self.screen.get_width() - 2 * self.background.radius - 5 - self.text.padding[0] - self.text.padding[2]
        
        # --- Préparer le texte multiligne ---
        lines, width = self._wrap_text(self.text.value, max_text_width)
        text_height = len(lines) * self.line_height
        
        # --- Calcul de la hauteur totale ---
        padding = 5
        if( self.title.enabled() ):
            title_height = self.title.font.point_size
            height = round(title_height + text_height + padding * 3)
        else:
            height = round(text_height + padding * 2 )


        width += 2 * self.background.radius + 5 
        self.background.size = (width, height)  # Met à jour la hauteur du fond dynamiquement
        
        # --- adjust position ---
        self.x, self.y = self.position
        if( self.center == "middle" ) :
            self.x = (self.window_size[0] - self.background.size[0]) // 2

        # --- Dessiner le fond arrondi ---
        self.surface_background  = pygame.Surface((width, height), pygame.SRCALPHA)

        print(str(self.background.size) + "-" + str(self.screen.get_width()) + "-" + str(self.line_height))
        print(width)
        print(height)

        # --- background --- 
        if( self.background.enabled() ):  
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
            #self.screen.blit(title_surface, (self.x + 10, self.y ))
            self.height_position = title_height + padding
        
        # --- Texte long > multiligne ---
        for i, line in enumerate(lines):
            surface = self.render_text_with_outline(self.text.font.sysFont, line, self.text.color, self.text.outline)
            surface.set_alpha(self.alpha * 255)
            self.surfaces.append(surface)
            
        


    def _update(self, dt, step):
        pass

    def _draw(self, ctx):

        if( self.surface_background is not None):
            self.screen.blit(self.surface_background , (self.x, self.y))

        if( self.surface_title is not None):
            self.screen.blit(self.surface_title , (self.x + 10, self.y ))

        i = 0
        for surface in self.surfaces:
            #TODO: do the setalpha in the surface and update the surface when the value change
            alpha = min(self.alpha*255 , self.text.color[3])
            surface.set_alpha(alpha)
            self.screen.blit(surface, (self.x + 10, self.y - 4 + self.height_position + i * self.line_height))
            i += 1


    # def draw_text_with_outline(self, ctx, text, x, y, font="Sans", size=32, fill_color=(1,1,1,1), outline_color=(0,0,0,1), outline_width=2):
    #     ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    #     ctx.set_font_size(size)

    #     # Génère le chemin du texte
    #     ctx.move_to(x, y)
    #     ctx.text_path(text)

    #     # Trace le contour (outline)
    #     ctx.set_line_width(outline_width)
    #     ctx.set_source_rgba(*outline_color)
    #     ctx.stroke_preserve()

    #     # Remplit le texte (centre)
    #     ctx.set_source_rgba(*fill_color)
    #     ctx.fill()


    def _drawold(self, ctx):

        
        x, y = self.position
        if( self.center == "middle" and self.background.size[1] > 0 ) :
            x = (self.window_size[0] - self.background.size[0]) // 2
        elif( self.center == "middle" ) :
            x = (self.window_size[0] - self.background.size[0]) // 2


        max_text_width = self.screen.get_width() - 2 * self.background.radius - 5 - self.text.padding[0] - self.text.padding[2]
        
        # --- Préparer le texte multiligne ---
        lines, width = self._wrap_text(self.text.value, max_text_width)
        line_height = self.text.font.point_size + 4
        text_height = len(lines) * line_height
        
        # --- Calcul de la hauteur totale ---
        padding = 5
        if( self.title.enabled() ):
            title_height = self.title.font.point_size
            height = round(title_height + text_height + padding * 3)
        else:
            height = round(text_height + padding * 2 )


        width += 2 * self.background.radius + 5 
        self.background.size = (width, height)  # Met à jour la hauteur du fond dynamiquement
        
        # --- Dessiner le fond arrondi ---
        bg_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Si la transparence n'est pas égale à 0, on dessine le fond
        if( self.background.enabled() ):  
            pygame.draw.rect(
                bg_surface,
                self.background.getColor(self.alpha*255),
                (0, 0, width, height),
                border_radius=self.background.radius
            )        
            self.screen.blit(bg_surface, (x, y))

        height_position = 0
            
        # --- Titre ---
        if( self.title.enabled() ):
            title_surface = self.title.font.render(self.title.value, True, (28, 161, 242)).convert_alpha()
            title_surface.set_alpha(self.alpha * 255)
            self.screen.blit(title_surface, (x + 10, y ))
            height_position = title_height + padding
        
        # --- Texte long > multiligne ---
        for i, line in enumerate(lines):
            text_surface = self.render_text_with_outline(self.text.font.sysFont, line, self.text.color, self.text.outline)
            text_surface.set_alpha(self.alpha * 255)
            self.screen.blit(text_surface, (x + 10, y - 4 + height_position + i * line_height))


    def render_text_with_outline(self, font, text, text_color, outline):
        """Render text with outline effect"""
        # Render the outline (multiple passes)
        outline_surface = pygame.Surface((font.size(text)[0] + outline.width*2, 
                                        font.size(text)[1] + outline.width*2), pygame.SRCALPHA)
        
        # Draw outline in all directions
        if( outline.width > 0 ):
             for dx in [-outline.width, 0, outline.width]:
                 for dy in [-outline.width, 0, outline.width]:
                     if dx != 0 or dy != 0:  # Skip the center position
                         text_outline = font.render(text, True, outline.color)
                         outline_surface.blit(text_outline, (outline.width + dx, outline.width + dy))


        #if( outline.width > 0 ):
        #    for dx, dy in [(1, 0), (0, 1), (1, 1)]:  # au lieu de 8 directions
        #       text_outline = font.render(text, True, outline.color)
        #        outline_surface.blit(text_outline, (outline.width + dx, outline.width + dy))
                    
        # Draw main text (centered over outline)
        text_surface = font.render(text, True, text_color)
        outline_surface.blit(text_surface, (outline.width, outline.width))
        
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