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
        if isinstance(self.lifetime, str):
            self.lifetime = eval(self.lifetime, {"__builtins__": {}}, safe_globals)
        if isinstance(self.color, str):
            self.color = eval(self.color, {"__builtins__": {}}, safe_globals)

        if self.color is not None and len(self.color) == 3:
            self.color = self.color + (255,)  # 255 = opaque
      
    def enabled(self):
        return self.count > 0
    
    def get_color(self, main_color = None, backup_color = None):
        if( self.color is not None ):
            return self.interpolate_color(self.color)
        if( main_color is not None ):
            return self.interpolate_color(main_color)
        return self.interpolate_color(backup_color)
        
    def interpolate_color(self, color):
        r, g, b, a = self.normalize_color(color)
        dr = random.uniform(-self.color_range, self.color_range)
        dg = random.uniform(-self.color_range, self.color_range)
        db = random.uniform(-self.color_range, self.color_range)
        return (
            min(max(r + dr, 0.0), 1.0),
            min(max(g + dg, 0.0), 1.0),
            min(max(b + db, 0.0), 1.0),
            1.0
        )
    
    def get_radius(self):
        return random.uniform(max(0.1,self.radius - self.radius_range), self.radius + self.radius_range)

    def normalize_color(self, color):
        return tuple(c / 255.0 for c in color)