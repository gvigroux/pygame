
import math
import random


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}

class eSize:
    def __init__(self, window_size, total = 0, i=0, width = "50%" , height = "50%"):
        self.window_size = window_size
        self.raw_width  = width
        self.raw_height = height
        safe_globals["total"] = total
        safe_globals["i"] = i
        self.width  = self._resolve_coord(width, window_size[0])
        self.height = self._resolve_coord(height, window_size[1])
       

    def _resolve_coord(self, val, total):
        if isinstance(val, str) and val.endswith("%"):
            try:
                pct = float(val.strip("%")) / 100.0
                return int(pct * total)
            except ValueError:
                return 0
        elif isinstance(val, str):
           return int(eval(val, {"__builtins__": {}}, safe_globals))
        return int(val)
    
    def get(self):
        return (self.width, self.height)
    
    def enabled(self):
        return True

    def schema(self):
        return {
            "width": ("float", "Width"),
            "height": ("float", "Height"),
        }