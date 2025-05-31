
import math
import random


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}


class Object:
    def __init__(self, data, pygame, screen, window_size, amount =1, i = 1):
        cls = self.__class__
        if not hasattr(cls, "_count"):
            cls._count = 0
        cls._count += 1
        self.screen     = screen
        self.window_size = window_size
        self.data       = data
        self.index      = i
        self.amount     = amount

        # Timing management
        self.delay      = self.config("delay", 0)
        self.step_delay = self.config("step_delay", 0)
        self.fade_in    = self.config("fade_in", 0)
        self.fade_out   = self.config("fade_out", 2)
        self.step       = self.config("step_start", 0)
        self.step_stop  = self.config("step_stop", -1)
        self.current_step = -1
        self.start_time = 0
        self.should_draw = False
        self.current_fade_in_time = 0.0
        self.current_fade_out_time = self.fade_out


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
        return self.pygame.time.get_ticks() - self.start_time - self.step_delay * 1000
    
    def is_destroyed(self):
        return self.destroyed and len(self.particles) == 0
    
    
    def update(self, dt, step):

        # Update particles
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.alpha > 0]

        if( self.step > step ):
            return
        
        if( self.current_step != self.step ):
            self.start_time     = self.pygame.time.get_ticks()
            self.current_step   = self.step

        # Delay
        if( (self.pygame.time.get_ticks() - self.start_time)/1000 < self.step_delay ): 
            return
        
        self.should_draw    = True
        
        # Fade in
        if self.current_fade_in_time < self.fade_in:
            self.current_fade_in_time += dt
            self.alpha = min(self.current_fade_in_time / self.fade_in, 1.0)

        if( self.step_stop >= 0 and self.step_stop < step and self.fade_out > 0):
            if self.current_fade_out_time <= self.fade_out:
                self.current_fade_out_time -= dt
                self.alpha = max(self.current_fade_out_time / self.fade_out, 0.0)       

        if self.destroyed:
            return
        
        if self.exploded:
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.destroyed = True

        if( self.age/1000 >= self.delay ):
            self._update(dt, step)
        


    def draw(self, ctx):

        for particle in self.particles:
            particle.draw(ctx)

        # Draw
        if( self.should_draw ):
            #r, g, b, a = self.color
            #ctx.set_source_rgba(r, g, b, self.alpha)
            self.color = (self.color[0], self.color[1], self.color[2], self.alpha)
            ctx.set_source_rgba(*self.color)
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
            #values = values.replace('\\n', '\n')
            try:
                return eval(values, {"__builtins__": {}}, safe_globals)
            except NameError as e:
                return values
            except SyntaxError as e:
                return values
        elif isinstance(values, int):
            return values
        elif isinstance(values, float):
            return values
        else:
            return [self.eval_expr(v) for v in values]
        
    def explode(self):
        if not self.exploded:
            self.exploded = True
            #self.start_time = self.age
            #self.end_time = self.age + self.lifetime
            self.create_particles()
