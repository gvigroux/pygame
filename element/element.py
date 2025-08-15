import math
import random
import re

safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}

class Element:
    def __init__(self):
        pass

    def eval(self, value, max = 0):
        safe_globals["i"]     = 0
        safe_globals["total"] = 0
        if hasattr(self, "total"):
            safe_globals["total"] = self.total
        if hasattr(self, "i"):
            safe_globals["i"] = self.i

        if isinstance(value, str):
            if( max > 0 ):
                def pct_replacer(match):
                    number = float(match.group(1))
                    return f"({number} / 100.0 * {max})"
                # Ex: "50% + 20" → "(50 / 100.0 * total) + 20"
                expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', pct_replacer, value)
                value = expr

            return eval(value, {"__builtins__": {}}, safe_globals)
        return value
    
    def eval_color(self, color):
        _color = color
        if( len(_color) == 0 ):
            _color = (255, 255, 255, 255)
        if isinstance(_color, str):
            _color = eval(_color, {"__builtins__": {}}, safe_globals)
        if( len(_color) == 3 ):
            _color = (_color[0], _color[1], _color[2], 255)
        return _color    
    
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
    
    def normalize_color(self, color):
        return tuple(c / 255.0 for c in color)
    