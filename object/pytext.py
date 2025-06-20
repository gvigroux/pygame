import pygame
import pygame.gfxdraw
from object.object import Object

class Text(Object):
    def __init__(self, data, pygame, screen, window_size, count, id):
        super().__init__(data, pygame, screen, window_size, count, id)

        self.position = self.config("position", (window_size[0]//2, window_size[1]//2))
        self.radius = self.config("radius", 10)
        self.bg_color = self.config("bg_color", (0, 0, 255, 255))  # Changé en format RGBA 0-255
        self.bg_radius = self.config("bg_radius", 15)
        self.bg_size    = self.config("bg_size", (0, 0))
        self.text       = self.config("text", "")
        self.font_family = self.config("font_family", "Noto Sans")
        self.title      = self.config("title", "")
        self.center      = self.config("center", "")
        self.bold      = self.config("bold", False)
        self.font_size   = self.config("font_size", 30)
        self.show        = True

        self.outline_color = self.config("outline_color", (0, 0, 0, 0))
        self.outline_size = self.config("outline_size", 0)
        
        # Initialisation des policestiming
        self.title_font = pygame.font.SysFont("Noto Sans", 36, bold=False)
        self.body_font = pygame.font.SysFont(self.font_family, self.font_size, bold=self.bold)
             
        # Convertir la couleur de fond si nécessaire
        #if len(self.bg_color) == 4 and all(0 <= c <= 1 for c in self.bg_color):
        #    self.bg_color = tuple(int(c * 255) for c in self.bg_color[:3]) + (self.bg_color[3],)

    def _update(self, dt, step):
        pass


    def _draw(self, ctx):
        
        x, y = self.position
        if( self.center == "middle" and self.bg_size[1] > 0 ) :
            x = (self.window_size[0] - self.bg_size[0]) // 2
        elif( self.center == "middle" ) :
            x = (self.window_size[0] - self.bg_size[0]) // 2



        #width, _ = self.bg_size
        #max_text_width = width - 2 * self.bg_radius - 5
        max_text_width = self.screen.get_width() - 2 * self.bg_radius - 5
        
        # --- Préparer le texte multiligne ---
        lines, width = self._wrap_text(self.text, max_text_width)
        line_height = self.body_font.point_size + 4
        text_height = len(lines) * line_height
        
        # --- Calcul de la hauteur totale ---
        padding = 20
        title_height = self.title_font.point_size if len(self.title) > 0 else 0
        height = round(title_height + text_height + padding * 1.5)

        width += 2 * self.bg_radius + 5 
        self.bg_size = (width, height)  # Met à jour la hauteur du fond dynamiquement
        
        # --- Dessiner le fond arrondi ---
        bg_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # rect = pygame.Rect(0, 0, width, height)
        # pygame.draw.rect(bg_surface, self.bg_color, rect, border_radius=self.bg_radius)
        # screen.blit(bg_surface, (x, y))


    
        # Dessin avec antialiasing
        #pygame.gfxdraw.aacircle(bg_surface, self.bg_radius, self.bg_radius, self.bg_radius, self.bg_color)        
        #pygame.gfxdraw.aacircle(bg_surface, width - self.bg_radius - 1, self.bg_radius, self.bg_radius, self.bg_color)
        #pygame.gfxdraw.aacircle(bg_surface, width - self.bg_radius - 1, height - self.bg_radius - 1, self.bg_radius, self.bg_color)
        #pygame.gfxdraw.aacircle(bg_surface, self.bg_radius, height - self.bg_radius - 1, self.bg_radius, self.bg_color)
            
        #self.bg_color = (self.bg_color[0], self.bg_color[1], self.bg_color[2], min(self.alpha, self.bg_color[3]))
        #self.bg_color = (self.bg_color[0], self.bg_color[1], self.bg_color[2], min(self.alpha, self.bg_color[3]))
        # bg_color = (self.bg_color[0], self.bg_color[1], self.bg_color[2], 150)
        
        # # # Dessin des 4 coins arrondis
        # for corner_x, corner_y in [(0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1)]:
        #     pygame.gfxdraw.aacircle(bg_surface, 
        #                         corner_x + (self.bg_radius if corner_x == 0 else -self.bg_radius),
        #                         corner_y + (self.bg_radius if corner_y == 0 else -self.bg_radius),
        #                         self.bg_radius, self.bg_color)
        #     pygame.gfxdraw.filled_circle(bg_surface, 
        #                             corner_x + (self.bg_radius if corner_x == 0 else -self.bg_radius),
        #                             corner_y + (self.bg_radius if corner_y == 0 else -self.bg_radius),
        #                             self.bg_radius, self.bg_color)
            
        # # Remplissage des rectangles centraux
        # pygame.draw.rect(bg_surface, self.bg_color, (self.bg_radius, 0, width - 2*self.bg_radius, height))
        # pygame.draw.rect(bg_surface, self.bg_color, (0, self.bg_radius, width, height - 2*self.bg_radius))

        pygame.draw.rect(
            bg_surface,
             (self.bg_color[0], self.bg_color[1], self.bg_color[2], min(self.alpha*255, self.bg_color[3])),
            (0, 0, width, height),
            border_radius=self.bg_radius
        )
        
        self.screen.blit(bg_surface, (x, y))
            
        # --- Titre ---
        if( len(self.title) > 0 ):
            title_surface = self.title_font.render(self.title, True, (28, 161, 242)).convert_alpha()
            title_surface.set_alpha(self.alpha * 255)
            self.screen.blit(title_surface, (x + 10, y + 2 ))
        
        # --- Texte multiligne ---
        for i, line in enumerate(lines):
            #text_surface = self.body_font.render(line, True, self.color).convert_alpha()
            text_surface = self.render_text_with_outline(self.body_font, line, self.color, self.outline_color, self.outline_size)
            text_surface.set_alpha(self.alpha * 255)
            if( self.center == "middle" ) :
                # Calcul de la position x pour centrer le texte
                #text_width = text_surface.get_width()
                #screen_width = self.screen.get_width()
                #x_centered = (screen_width - text_width) // 2  # Centrage horizontal
                #self.screen.blit(text_surface, (x_centered, y + 2 + padding/2 + title_height + i * line_height))
                self.screen.blit(text_surface, (x + 10, y + 2 + padding/2 + title_height + i * line_height))
                pass
            else :
                self.screen.blit(text_surface, (x + 10, y + 2 + padding/2 + title_height + i * line_height))

    def render_text_with_outline(self, font, text, text_color, outline_color, outline_size=2):
        """Render text with outline effect"""
        # Render the outline (multiple passes)
        outline_surface = pygame.Surface((font.size(text)[0] + outline_size*2, 
                                        font.size(text)[1] + outline_size*2), pygame.SRCALPHA)
        
        # Draw outline in all directions
        for dx in [-outline_size, 0, outline_size]:
            for dy in [-outline_size, 0, outline_size]:
                if dx != 0 or dy != 0:  # Skip the center position
                    text_outline = font.render(text, True, outline_color)
                    outline_surface.blit(text_outline, (outline_size + dx, outline_size + dy))
        
        # Draw main text (centered over outline)
        text_surface = font.render(text, True, text_color)
        outline_surface.blit(text_surface, (outline_size, outline_size))
        
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
                test_width = self.body_font.size(test_line)[0]
                
                if test_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        current_width = self.body_font.size(current_line)[0]
                        max_line_width = max(max_line_width, current_width)
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                current_width = self.body_font.size(current_line)[0]
                max_line_width = max(max_line_width, current_width)
                lines.append(current_line)
            
            if not paragraph.strip():
                lines.append("")
                # Une ligne vide a une largeur de 0
                max_line_width = max(max_line_width, 0)
        
        return lines, max_line_width