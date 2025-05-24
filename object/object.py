import math
import random
import moderngl
import numpy as np



safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}

class Object:
    def __init__(self, context, vbo, data, window_size, amount =1, i = 1):
        cls = self.__class__
        if not hasattr(cls, "_count"):
            cls._count = 0
        cls._count += 1
    
        self.data   = data
        self.vbo    = vbo
        self.context = context
        self.window_size = window_size
        self.ratio = self.window_size[0] / self.window_size[1]
        self.projection_matrix = self.get_projection_matrix().tobytes()

        self.exploding = False
        self.exploding_timer = 0
        
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
        pass

    def interpolate_color(self,color1, color2, t):
        """Retourne une couleur intermédiaire entre color1 et color2 selon t ∈ [0.0, 1.0]"""
        return tuple(
            (1 - t) * c1 + t * c2
            for c1, c2 in zip(color1, color2)
        )

    def count(self):
        return self.__class__._count

    def Update(self):
        pass

    def Draw(self):
        pass

    def Config(self, key, default=None):
        pass

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

    def is_exploding(self):
        return self.exploding
    
    def is_destroyed(self):
        return self.exploding and self.exploding_timer >= 1.0
    
    def explode(self, particle_system):
        self.exploding = True
        self.exploding_timer = 0.0
    
        points = self.get_fragment_points()
        for pt in points: 
            angle = np.random.uniform(0, 2 * np.pi)
            speed = np.random.uniform(30, 80)  # pixels/sec
            vx = np.cos(angle) * speed
            vy = np.sin(angle) * speed
            particle_system.spawn(pt, (vx, vy), self.color, lifetime=1.0)

    def alpha(self, fragment = 3):
        if self.exploding:
            self.exploding_timer += fragment/60
            return max(0.0, 1.0 - self.exploding_timer)
        return 1.0

    def Render(self, vao, prog):
        prog['projection'].write(self.projection_matrix)
        vao.render(moderngl.TRIANGLE_STRIP)
  
    def get_projection_matrix(self):
        if self.ratio > 1.0:
            scale_x, scale_y = 1.0 / self.ratio, 1.0
        else:
            scale_x, scale_y = 1.0, self.ratio

        #scale_x = 1.0
        #scale_y = 1.0
        return np.array([
            [scale_x, 0.0,     0.0, 0.0],
            [0.0,     scale_y, 0.0, 0.0],
            [0.0,     0.0,     1.0, 0.0],
            [0.0,     0.0,     0.0, 1.0],
        ], dtype='f4')


    def gl_to_screen(self, gl_pos):
        """Convertit une position OpenGL (-1 à 1) en pixels écran (haut-gauche)"""
        x = int((gl_pos[0] + 1) * 0.5 * self.window_size[0])
        y = int((1 - (gl_pos[1] + 1) * 0.5) * self.window_size[1])
        return (x, y)

    def screen_to_gl(self, screen_pos):
        """Convertit une position en pixels écran vers OpenGL (-1 à 1)"""
        x = (screen_pos[0] / self.window_size[0]) * 2.0 - 1.0
        y = -((screen_pos[1] / self.window_size[1]) * 2.0 - 1.0)
        return (x, y)
    