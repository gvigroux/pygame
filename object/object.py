
import math
import random


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}


class Object:
    def __init__(self, data, pygame, window_size, amount =1, i = 1):
        cls = self.__class__
        if not hasattr(cls, "_count"):
            cls._count = 0
        cls._count += 1
        self.window_size = window_size
        self.data       = data
        self.index      = i
        self.amount     = amount
        self.freeze     = self.config("freeze", 3.0)
        self.lifetime   = self.config("lifetime", 1.0)
        self.timer      = self.config("timer", 1.0)
        self.color      = self.config("color", (1.0, 0.0, 1.0, 1.0))
        self.fragments_explode = self.config("fragments_explode", 50)
        self.fragments_touch   = self.config("fragments_touch", 50)

        colors = self.config("colors", None)
        if( colors is not None ):
            # Update data object for next iteration
            data["colors"] = colors
            self.color = self.interpolate_color(colors[0], colors[1], (self.index) / (self.amount-1))

        self.particles  = []
        self.alpha      = 1.0
        self.exploded   = False
        self.destroyed  = False
        self.pygame     = pygame
        self.fade_speed = 5.0  # vitesse de disparition (1.0 = lent, 5.0 = rapide)

    def count(self):
        return self.__class__._count
    
    @property
    def age(self):
        return self.pygame.time.get_ticks()
    
    def is_destroyed(self):
        return self.destroyed and len(self.particles) == 0
    
    
    def update(self, dt):        
        
        # Update particles
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.alpha > 0]

        if self.destroyed:
            return
        
        if self.exploded:         
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.destroyed = True

        self._update(dt)


    def draw(self, ctx):

        for particle in self.particles:
            particle.draw(ctx)

        r, g, b, a = self.color
        ctx.set_source_rgba(r, g, b, self.alpha)
        self._draw(ctx)


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
        
    def explode(self):
        if not self.exploded:
            self.exploded = True
            self.start_time = self.age
            self.end_time = self.age + self.lifetime
            self.create_particles()
