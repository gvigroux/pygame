
import math
import random

from element.element import Element



class ePosition(Element):
    def __init__(self, window_size, total = 0, i=0, x = "50%" , y = "50%", justify = "H"):
        self.x  = x
        self.y  = y
        self.total         = total  
        self.i             = i
        self.window_size    = window_size
        self.justify        = justify
        self.prepare()

    def prepare(self):
        self.x          = self.eval(self.x, self.window_size[0])
        self.y          = self.eval(self.y, self.window_size[1])
        # TODO: check if self.justify is valid    
    
    def enabled(self):
        return True

    def schema(self):
        return {
            "x": ("floateval", "X"),
            "y": ("floateval", "Y"),
            "justify": ("str", "Justify"),
        }
    