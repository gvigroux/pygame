import time
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
        t0 = time.perf_counter()
        self.font       = eFont(**font)
        t1 = time.perf_counter()
        self.outline    = eOutline(**outline)
        t2 = time.perf_counter()
        self.background = eBackground(**background)
        t3 = time.perf_counter()
        self.prepare()
        if( t1 - t0 > 0.01 ):
            print(f"SLOW eText.init1: {(t1 - t0)*1000:.2f} ms")
        if( t2 - t1 > 0.01 ):            
            print(f"SLOW eText.init2: {(t2 - t1)*1000:.2f} ms")
        if( t3 - t2 > 0.01 ):            
            print(f"SLOW eText.init3: {(t3 - t2)*1000:.2f} ms")


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
    