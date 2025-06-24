from typing import Union
import pygame


class eFont:
    def __init__(self, bold = False, size= 12, family= "Anton Regular"):
        self.bold       = bold
        self.size       = size
        self.family     = family

        # Chargement de la police        
        self.sysFont    = pygame.font.SysFont(self.family, self.size, bold=self.bold)
        self.point_size = self.sysFont.point_size
    
    def render(
        self,
        text: Union[str, bytes, None],
        antialias: bool,
        color,
        bgcolor = None,
        wraplength: int = 0,
    ):
        return self.sysFont.render(text, antialias, color, bgcolor, wraplength)
            

    def enabled(self):
        return True
