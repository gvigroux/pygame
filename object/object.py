
import math
import random


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}


class Object:
    def __init__(self, data, window_size, amount =1, i = 1):
        cls = self.__class__
        if not hasattr(cls, "_count"):
            cls._count = 0
        cls._count += 1
        self.data   = data
        self.window_size = window_size
        self.index  = i
        self.amount = amount 
        self.age    = 0
        self.timer = self.config("timer", 1.0)
        self.color = self.config("color", (1.0, 0.0, 1.0, 1.0))
        self.fragments_explode = self.config("fragments_explode", 50)
        self.fragments_touch   = self.config("fragments_touch", 50)
        colors = self.config("colors", None)
        if( colors is not None ):
            # Update data object for next iteration
            data["colors"] = colors
            self.color = self.interpolate_color(colors[0], colors[1], (self.index) / (self.amount-1))
        self.particles = []
        self.alpha = 1.0

    def count(self):
        return self.__class__._count



    def eval_expr(self, expr):
        if isinstance(expr, str):
            return eval(expr, {"__builtins__": {}}, safe_globals)
        return expr

    def config(self, key, default=None):
        values = self.data.get(key, default)
        if( values == default ):
            return default
        
        safe_globals['total']   = self.count()
        safe_globals['i']       = self.index
        if isinstance(values, str):
            return eval(values, {"__builtins__": {}}, safe_globals)
        elif isinstance(values, int):
            return values
        else:
            return [self.eval_expr(v) for v in values]