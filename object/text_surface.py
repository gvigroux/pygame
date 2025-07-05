import math
import random
import cairo
import pygame
from element.background import eBackground
from element.text import eText
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

class TextSurface(Object):
    def __init__(self, data, pygame, window_size, count, id):
        super().__init__(data, pygame, window_size, count, id)

        self.text       = eText(**self.config("text", {}))
        self.title      = eText(**self.config("title", {}))
        self.background = eBackground(**self.config("background", {}))
        self.surfaces   = []

        self.font_emoji = pygame.font.SysFont("Segoe UI Emoji", self.text.font.point_size)

        self.line_height = self.text.font.point_size + 4
        self.surface_background = None
        self.surface_title = None
        self._prepare()
        

    def _prepare(self):
        
        # Clean surfaces
        self.surfaces = []
        self.background_surfaces = []

        # Padding: haut | droit | bas | gauche
        max_text_width = self.window_size[0] - self.text.padding[1] - self.text.padding[3] - self.text.outline.width*2 - self.text.margin[1] - self.text.margin[3]  
        
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
        self.position.y += self.text.margin[0]
        self.position.x += self.text.margin[1]

        if( "H" in self.position.justify ) :
            self.position.x = (self.window_size[0] - self.background.size[0]) // 2
        if( "V" in self.position.justify ) :
            self.position.y = (self.window_size[1] - self.background.size[1]) // 2 + self.text.margin[0]


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
            surface = self.render_text_with_outline(line, self.text.color, self.text.outline)
            surface.set_alpha(self.alpha * 255)
            self.surfaces.append(surface)
            

    def render_text_with_outline(self, text, text_color, outline):
   
        # Polices : self.text.font.sysFont = police normale
        #           self.font_emoji       = police emoji
        font_normal = self.text.font.sysFont
        font_emoji = self.font_emoji  # Assure-toi de l'avoir chargée dans __init__

        # Découpe le texte en blocs (texte ou emoji)
        surfaces = []
        buffer = ''
        current_is_emoji = None

        for char in text:
            char_is_emoji = self.is_emoji(char)
            if current_is_emoji is None:
                current_is_emoji = char_is_emoji

            if char_is_emoji == current_is_emoji:
                buffer += char
            else:
                font = font_emoji if current_is_emoji else font_normal
                surfaces.append((buffer, font))
                buffer = char
                current_is_emoji = char_is_emoji

        if buffer:
            font = font_emoji if current_is_emoji else font_normal
            surfaces.append((buffer, font))

        # Calcule la taille finale
        text_width = sum(font.size(part)[0] for part, font in surfaces)
        text_height = max(font.size(part)[1] for part, font in surfaces)

        surf_width  = text_width + self.text.padding[1] + self.text.padding[3] + outline.width * 2
        surf_height = text_height + self.text.padding[0] + self.text.padding[2] + outline.width * 2

        outline_surface = pygame.Surface((surf_width, surf_height), pygame.SRCALPHA)

        # Rendu du texte avec outline
        x_cursor = outline.width + self.text.padding[3]
        for part, font in surfaces:
            if part== '️':
                continue
            part_surface = font.render(part, True, text_color)
            text_x = x_cursor
            text_y = (surf_height - part_surface.get_height()) // 2

            if outline.width > 0:
                for dx in [-outline.width, 0, outline.width]:
                    for dy in [-outline.width, 0, outline.width]:
                        if dx != 0 or dy != 0:
                            outline_text = font.render(part, True, outline.color)
                            outline_surface.blit(outline_text, (text_x + dx, text_y + dy))

            outline_surface.blit(part_surface, (text_x, text_y))
            x_cursor += part_surface.get_width()

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


    def is_emoji(self, char):
        code = ord(char)
        return (
            code >= 0x1F300  # emojis modernes
            or 0x2600 <= code <= 0x27BF  # symboles divers : flake, heart, ☀️, ☂️ etc.
        )

    def render_mixed_text(self, text):
        surfaces = []
        buffer = ''
        current_is_emoji = None

        for char in text:
            char_is_emoji = self.is_emoji(char)

            if current_is_emoji is None:
                current_is_emoji = char_is_emoji

            if char_is_emoji == current_is_emoji:
                buffer += char
            else:
                font = self.font_emoji if current_is_emoji else self.font_normal
                surfaces.append(font.render(buffer, True, (255, 255, 255)))
                buffer = char
                current_is_emoji = char_is_emoji

        if buffer:
            font = self.font_emoji if current_is_emoji else self.font_normal
            surfaces.append(font.render(buffer, True, (255, 255, 255)))

        # Maintenant, assemble la ligne
        total_width = sum(s.get_width() for s in surfaces)
        height = max(s.get_height() for s in surfaces)
        result_surface = pygame.Surface((total_width, height), pygame.SRCALPHA)

        x = 0
        for s in surfaces:
            result_surface.blit(s, (x, 0))
            x += s.get_width()

        return result_surface


    def _draw(self, ctx):
        pass

    def _draw_surface(self, screen):

        if( self.surface_background is not None):
            screen.blit(self.surface_background , (self.position.x, self.position.y))

        i = 0
        for surface in self.background_surfaces:
            x =  self.position.x
            if( "H" in self.position.justify ) :
                x = (self.window_size[0] - surface.get_width()) // 2

            #TODO: do the setalpha in the surface and update the surface when the value change
            alpha = min(self.alpha*255 , self.text.color[3])
            surface.set_alpha(alpha)
            screen.blit(surface, (x, self.position.y + self.height_position + i * self.line_height))
            i += 1

        if( self.surface_title is not None):
            screen.blit(self.surface_title , (self.position.x + self.title.padding[1], self.position.y + self.title.padding[3] ))

        i = 0
        for surface in self.surfaces:
            x =  self.position.x
            if( "H" in self.position.justify ) :
                x = (self.window_size[0] - surface.get_width()) // 2

            #TODO: do the setalpha in the surface and update the surface when the value change
            alpha = min(self.alpha*255 , self.text.color[3])
            surface.set_alpha(alpha)
            screen.blit(surface, (x, self.position.y + self.height_position + i * self.line_height))
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
