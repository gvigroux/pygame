
import math
import random


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}

class ePosition:
    def __init__(self, window_size, x = "50%" , y = "50%", justify = "H"):
        self.window_size = window_size
        self.raw_x = x
        self.raw_y = y
        self.x = self._resolve_coord(x, window_size[0])
        self.y = self._resolve_coord(y, window_size[1])
        self.justify = justify

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
    
    
    def enabled(self):
        return True
