
import math
import random
import time

from element.event import  eEvent
from element.fragment import eFragment
from element.position import ePosition
from element.shadow import eShadow
from element.sound import eSound
from element.step import eStep
from object.inner_particle import InnerParticle


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

        self.lifetime   = self.config("lifetime", 1.0)
        self.timer      = self.config("timer", 1.0)
        self.color      = self.config("color", (255, 255, 255, 255))
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)
        
        self.position       = ePosition(window_size, amount, i, **self.config("position", {"x": "50%","y": "50%"}))   
        self.shadow         = eShadow(**self.config("shadow", {}))
        self.step           = eStep(self, **self.config("step", {}))
   

        self.spawn              = eEvent(pygame, **self.config("on_spawn", {}))
        self.destroy            = eEvent(pygame, **self.config("on_destroy", {}))
        self.collision          = eEvent(pygame, **self.config("on_collision", {}))

        # Timing management
        self.enable     = self.config("enable", True)
        self.current_step = -1
        self.start_time = 0
        self.should_draw = False
        self.current_fade_in_time = 0.0
        self.current_fade_out_time = self.step.fade_out

        colors = self.config("colors", None)
        if( colors is not None ):
            # Update data object for next iteration
            data["colors"] = colors
            self.color = self.gradient_color(colors[0], colors[1], (self.index) / (self.amount-1))

        self.particles  = []
        self.alpha      = 1.0
        self.exploded   = False
        self.destroyed  = False
        self.first_draw = True
        self.pygame     = pygame
        self.fade_speed = 5.0  # vitesse de disparition (1.0 = lent, 5.0 = rapide)

        self.log_draw_durations = []
        self.t0 = 0
        self.t1 = 0

    def gradient_color(self,color1, color2, t):
        """Retourne une couleur intermédiaire entre color1 et color2 selon t ∈ [0.0, 1.0]"""
        return tuple(
            (1 - t) * c1 + t * c2
            for c1, c2 in zip(color1, color2)
        )


    def count(self):
        return self.__class__._count
    
    @property
    def age(self):
        return self.pygame.time.get_ticks() - self.start_time - self.step.delay * 1000
    
    def is_destroyed(self):
        return self.destroyed and len(self.particles) == 0

    def is_alive(self, step):
        if( self.is_destroyed() ):
            return False
        return self.step.start <= step and (self.step.stop >= step or self.step.stop == -1)

    def block(self, step):
        if( self.is_destroyed() ):
            return False
        if(( self.step.start <= step and (self.step.stop >= step or self.step.stop == -1)) == False ):
            return False
        if( self.step.block ):
            return True
        return False
    

    def update(self, dt, step, clock, blocked):

        if( self.enable == False ):
            return

        # Update particles
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.alpha > 0]

        if( self.step.start > step ):
            return
        
        if( self.current_step != self.step.start ):
            self.start_time     = self.pygame.time.get_ticks()
            self.current_step   = self.step.start

        # Delay
        if( (self.pygame.time.get_ticks() - self.start_time)/1000 < self.step.delay ): 
            return
        
        phase_out = False
        if( self.step.duration > 0 and self.age/1000 > self.step.duration ):
            phase_out = True
        
        self.should_draw    = True
        
        # Fade in
        if self.current_fade_in_time < self.step.fade_in:
            self.current_fade_in_time += dt
            self.alpha = min(self.current_fade_in_time / self.step.fade_in, 1.0)

        if( self.step.stop >= 0 and self.step.stop < step and self.step.fade_out > 0):
            phase_out = True

        if( phase_out ):
            if( self.step.fade_out <= 0 ):
                self.alpha = 0.0
            elif self.current_fade_out_time <= self.step.fade_out:
                self.current_fade_out_time -= dt
                self.alpha = max(self.current_fade_out_time / self.step.fade_out, 0.0) 

            if( self.alpha <= 0.0 ):
                self.destroyed = True
                #if( type(self).__name__ == "Arc" ):
                self.explode()

        if self.destroyed:
            self.should_draw = False
            self.explode()
            return
        
        if self.exploded:
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.destroyed = True
                self.should_draw = False

        if( self.age/1000 >= self.step.update_delay ):
            self._update(dt, step, clock, blocked)
        
    def _update(self, dt, step, clock, blocked):
        pass


    def draw(self, ctx):
        t0 = time.perf_counter()

        if( self.enable == False ):
            return

        for particle in self.particles:
            particle.draw(ctx)

        # Draw
        if( not self.should_draw ):
            return
    
        #r, g, b, a = self.color
        #ctx.set_source_rgba(r, g, b, self.alpha)
        if( self.shadow.enabled() ):
            #ctx.set_source_rgba(0, 0, 0, min(0.4, self.alpha))
            #self.set_color(ctx, (0, 0, 0, 100))
            self.set_color(ctx, self.shadow.color)
            self._draw_shadow(ctx)
        #self.color = (self.color[0], self.color[1], self.color[2], self.alpha)
        #ctx.set_source_rgba(*self.color)
        self.set_color(ctx, self.color)
        self._draw(ctx)
        self.log_draw_durations.append(time.perf_counter() - t0)
        #print(f"UPDATE: {(self.t1 - self.t0)*1000:.2f} ms | DRAW: {(self.t3 - self.t2)*1000:.2f} ms")



    def draw_surface(self, screen):
        t0 = time.perf_counter()

        if( self.enable == False ) or ( not self.should_draw ):
            return
        
        # Draw
        self._draw_surface(screen)
        self.log_draw_durations.append(time.perf_counter() - t0)
            
        if( self.first_draw ):
            self.first_draw = False
            self.create_particles(self.spawn.fragment)
            self.spawn.sound.play()

    def _draw_surface(self, screen):
        pass

    def set_color(self, ctx, color):
        color = self.normalize_color(color)
        color = (color[0], color[1], color[2], min(self.alpha, color[3]))
        ctx.set_source_rgba(*color)
            
    def normalize_color(self, color):
        return tuple(c / 255.0 for c in color)


    def stat(self):
        average  = 0
        if( len(self.log_draw_durations) > 0):       
            average = sum(self.log_draw_durations) / len(self.log_draw_durations)
        #print(f"{type(self)} : {average*1000:.2f} ms")    
        return average

    def eval_expr(self, expr):
        if isinstance(expr, str):
            return eval(expr, {"__builtins__": {}}, safe_globals)
        return expr


    def config(self, key, default=None):

        values = self.data.get(key, default)
        if( values == default ):
            return default
        if( isinstance(values, dict) ):
            return values
        
        safe_globals['total']   = self.count()
        safe_globals['i']       = self.index
        if isinstance(values, str):
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
            self.create_particles(self.destroy.fragment)
            self.destroy.sound.play()


    def get_points(self, fragment):
        points = []
        for i in range(fragment.count):
            x = self.position.x
            y = self.position.y
            points.append((x, y))
        return points
    

    def create_particles(self, fragment, color = None):
        
        points = self.get_points(fragment)
        for i, point in enumerate(points):
            
           # Angle aléatoire (360°)
            angle = random.uniform(0, 2 * math.pi)

            # Vitesse aléatoire dans cette direction
            speed = random.uniform(30, 70)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Créer la particule
            particle = InnerParticle(position=(point[0], point[1]), velocity=(vx, vy),
                                radius=fragment.get_radius(), lifetime=fragment.lifetime, color=fragment.get_color(color, self.color))
            self.particles.append(particle)