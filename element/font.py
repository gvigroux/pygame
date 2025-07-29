import time
from typing import Union
import pygame

FONT_CACHE = {}


def get_font(family, size, bold=False):
    key = (family, size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont(family, size, bold=bold)
    return FONT_CACHE[key]


class eFont:
    def __init__(self, bold = False, size= 12, family= "Anton Regular"):

        self.bold       = bold
        self.size       = size
        self.family     = family

        # Chargement de la police
        t0 = time.perf_counter()
        #self.sysFont    = pygame.font.SysFont(self.family, self.size, bold=self.bold
        self.sysFont = get_font(self.family, self.size, self.bold)
        t1 = time.perf_counter()
        self.point_size = self.sysFont.point_size
        if( t1 - t0 > 0.01 ):
            print(f"SLOW eFont.init: {(t1 - t0)*1000:.2f} ms")
    
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
    
    def schema(self):
        return {
            "bold": ("bool", "Bold"),
            "size": ("float", "Size"),
            "family": ("str", "Family"),
        }

    def __getstate__(self):
        # Exclut self.font de la sauvegarde
        state = self.__dict__.copy()
        del state["sysFont"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.sysFont = pygame.font.SysFont(self.family, self.size, bold=self.bold)