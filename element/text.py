from element.background import eBackground
from element.font import eFont
from element.outline import eOutline
import pygame


class eText:
    def __init__(self, value= "", color = (255, 255, 255, 255), font= {}, outline = {}, padding= (0,0,0,0), margin= (0,0,0,0), background = {}, update= ""):
        self.value      = value
        self.color      = color
        self.update     = update 
        self.padding    = padding
        self.margin     = margin
        self.font       = eFont(**font)
        self.outline    = eOutline(**outline)
        self.background = eBackground(**background)
        self.prepare()


    def enabled(self):
        return len(self.value) > 0 or len(self.update) > 0

    def getColor(self, alpha):
        return (self.color[0], self.color[1], self.color[2],  min(alpha, self.color[3]))
    
    def prepare(self):
        if( isinstance(self.color, str) ):
            self.color = eval(self.color)
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)  
        if( isinstance(self.padding, str) ):
            self.padding = eval(self.padding)
        if( isinstance(self.padding, str) ):
            self.padding = eval(self.padding)
        if( isinstance(self.margin, str) ):
            self.margin = eval(self.margin)
    

    def schema(self):
        return {
            "value": ("str", "Value"),
            "color": ("str", "Color"),
            "font": ("dict", "Font"),
            "outline": ("dict", "Outline"),
            "padding": ("str", "Padding"),
            "margin": ("str", "Margin"),
            "background": ("dict", "Background"),
            "update": ("str", "Update"),
        }
    