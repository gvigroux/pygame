import math
import random
from element.sound import eSound


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}

class eFragment:
    def __init__(self, count = 0, radius = 4, radius_range = 2, lifetime = 1, color = None, color_range = 0.1):
        self.count = count
        self.radius = radius
        self.lifetime = lifetime
        self.radius_range = radius_range
        self.color_range = color_range
        self.color = color
      
    def enabled(self):
        return self.count > 0
    
    def prepare(self):
        # The color is not calculated at launhc, but at each call of get_color 
        #self.color = self.eval_color(self.color)
        #self.lifetime = self.eval(self.lifetime)
        self.radius = self.eval(self.radius)
        self.radius_range = self.eval(self.radius_range)
        self.count = self.eval(self.count)

    def get_color(self, main_color = None, backup_color = None):
        if( self.color is not None ):
            # Evaluate Color at each call
            color = self.eval_color(self.color)
            # color = self.color
            # if isinstance(self.color, str):
            #     color = eval(self.color, {"__builtins__": {}}, safe_globals)
            # if color is not None and len(color) == 3:
            #     color = color + (255,)  # 25
            return self.interpolate_color(color)
        if( main_color is not None ):
            return self.interpolate_color(main_color)
        return self.interpolate_color(backup_color)
    
    def get_lifetime(self):
        return self.eval(self.lifetime)

    def get_radius(self):
        return random.uniform(max(0.1,self.radius - self.radius_range), self.radius + self.radius_range)
    
    def schema(self):
        return {
            "count": ("int", "Count"),
            "radius": ("float", "Radius"),
            "radius_range": ("float", "Radius Range"),
            "lifetime": ("floateval", "Lifetime"),
            "color": ("str", "Color"),
            "color_range": ("float", "Color Range"),
        }