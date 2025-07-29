
import copy
import math
import random
import time

import pygame

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
    def __init__(self, data, window_size, amount =1, i = 1):
        t0 = time.perf_counter()
        cls = self.__class__
        if not hasattr(cls, "_count"):
            cls._count = 0
        cls._count += 1
        self.window_size = window_size
        self.data       = data
        self.index      = i
        self.amount     = amount

        self.color      = self.config("color", (255, 255, 255, 255))
        self.label      = self.config("label", "")
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)
        
        self.position       = ePosition(window_size, amount, i, **self.config("position", {"x": "50%","y": "50%"}))   
        self.shadow         = eShadow(**self.config("shadow", {}))
        self.step           = eStep(self, **self.config("step", {}))
   

        self.on_spawn              = eEvent(**self.config("on_spawn", {}))
        self.on_destroy            = eEvent(**self.config("on_destroy", {}))
        self.on_collision          = eEvent(**self.config("on_collision", {}))
        t1 = time.perf_counter()

        # Timing management
        self.enable     = self.config("enable", True)
        self.current_step = -1
        self.start_time = 0
        self.start_time = time.time()
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
        #self.pygame     = pygame
        self.fade_speed = 5.0  # vitesse de disparition (1.0 = lent, 5.0 = rapide)
        self.track_id   = self.config("track_id", 0)

        self.log_draw_durations = []
        self.t0 = 0
        self.t1 = 0
        t2 = time.perf_counter()
        if( t1 - t0 > 0.01 ):
            print(f"SLOW Object.__init__1: {(t1 - t0)*1000:.2f} ms")
        if( t2 - t1 > 0.01 ):            
            print(f"SLOW Object.__init__2: {(t2 - t1)*1000:.2f} ms")
        if( t2 - t0 > 0.01 ):            
            print(f"SLOW Object.__init__total: {(t2 - t0)*1000:.2f} ms")

    def prepare(self):     
        self.color      = self.config("color", (255, 255, 255, 255))
        self.label      = self.config("label", "")
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)   
        self.position       = ePosition(self.window_size, self.amount, self.index, **self.config("position", {"x": "50%","y": "50%"}))   

    def enabled(self):
        return True

    def reset(self, start_time, current_step=0):
        self.start_time = start_time
        self.current_step = current_step
        self.destroyed  = False
        self.exploded   = False
        self.first_draw = True
        self.should_draw = False
        self.alpha      = 1.0
        self.particles  = []
        self.current_fade_in_time = 0.0
        self.current_fade_out_time = self.step.fade_out
        

    def schema(self):
        child_schema = self._schema()
        parent_schema = {
            "label": ("str", "Label"),
            "enable": ("bool", "Enable"),
            "color": ("str", "Color"),
            "position": ("position", "Position"),
            "shadow": ("shadow", "Shadow"),
            "step": ("step", "Step"),
            "on_spawn": ("event", "On Spawn"),
            "on_destroy": ("event", "On Destroy"),
            "on_collision": ("event", "On Collision"),
        }  
        return {**parent_schema, **child_schema}
     
    # def schema(self):
    #     return {
    #         "lifetime": ("float", "Lifetime"),
    #         "timer": ("float", "Timer"),
    #         "color": ("color", "Color"),
    #         "position": ("position", "Position"),
    #         "shadow": ("shadow", "Shadow"),
    #         "step": ("step", "Step"),
    #         "on_spawn": ("event", "On Spawn"),
    #         "on_destroy": ("event", "On Destroy"),
    #         "on_collision": ("event", "On Collision"),
    #         "enable": ("bool", "Enable"),
    #     }  

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
        return (time.time() - self.start_time - self.step.delay)
    
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
        
        # We move to current step
        if( self.current_step != self.step.start ):
            #self.start_time     = self.pygame.time.get_ticks()
            self.start_time     = time.time()
            self.current_step   = self.step.start

        # Delay
        #if( (self.pygame.time.get_ticks() - self.start_time)/1000 < self.step.delay ): 
        #    return
        
        if( (time.time() - self.start_time) < self.step.delay ): 
             return
        
        #phase_out = False
        #if( self.step.duration > 0 and self.age > self.step.duration ):
        #    phase_out = True
        
        self.should_draw    = True
    
        
        if self.age < self.step.fade_in:
            self.alpha = min(self.age / self.step.fade_in, 1.0)
        else:
            self.alpha = 1.0  # une fois le fade-in terminé

        #if( self.step.stop >= 0 and self.step.stop < step and self.step.fade_out > 0):
        #    phase_out = True

        # if( phase_out ):
        #     if( self.step.fade_out <= 0 ):
        #         self.alpha = 0.0
        #     elif self.current_fade_out_time <= self.step.fade_out:
        #         self.current_fade_out_time -= dt
        #         self.alpha = max(self.current_fade_out_time / self.step.fade_out, 0.0) 
        #         print("fadeout alpha", self.alpha)

        #     if( self.alpha <= 0.0 ):
        #         self.destroyed = True
        #         self.explode()

        if( self.age >= self.step.duration - self.step.fade_out ) and ( self.age < self.step.duration ):
            time_in_fade_out = self.age - (self.step.duration - self.step.fade_out)
            self.alpha = max(1.0 - (time_in_fade_out / self.step.fade_out), 0.0)
            

        if( self.age >= self.step.duration ) and ( self.step.duration >= 0):
            self.destroyed = True
            self.explode()

        # if (self.step.stop >= 0 and self.step.stop < step and self.step.fade_out > 0) or (self.step.duration > 0 and self.age > self.step.duration - self.step.fade_out):
        #     fade_out_start = self.age - self.step.duration - self.step.fade_out

        #     if( self.step.fade_out <= 0 ):
        #         self.alpha = 0.0

        #     elif self.age >= self.step.duration - fade_out_start:
        #         time_in_fade_out = self.age - fade_out_start
        #         self.alpha = max(1.0 - (time_in_fade_out / self.step.fade_out), 0.0)
            
        #     if( self.alpha <= 0.0 ):
        #         self.destroyed = True
        #         self.explode()

        if self.destroyed:
            self.should_draw = False
            self.explode()
            self.on_spawn.sound.stop()
            return
        
        if self.exploded:
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0.0:
                self.alpha = 0.0
                self.destroyed = True
                self.should_draw = False
                self.on_spawn.sound.stop()

        if( self.age >= self.step.update_delay ):
            self._update(dt, step, clock, blocked)
        
    def _update(self, dt, step, clock, blocked):
        pass


    
    def serialize_object(self, object = None):

        if( object == None ):
            object = self

        if not hasattr(self, "schema") or not callable(object.schema):
            raise ValueError("L'objet n'a pas de méthode .schema()")

        result = {}
        schema = object.schema()

        if( object == self ):
            result["type"] = object.__class__.__name__

        for key in schema:
            try:
                value = getattr(object, key)
            except AttributeError:
                continue

            if hasattr(value, "schema") and callable(value.schema):
                if( value.enabled()):
                    result[key] = self.serialize_object(value)  # appel récursif
            elif isinstance(value, (str, int, float, bool)): # or value is None:
                result[key] = value
            elif isinstance(value, list):
                # Liste d'objets ou de primitives
                serialized_list = []
                for item in value:
                    if hasattr(item, "schema") and callable(item.schema):
                        if( item.enabled()):
                            serialized_list.append(self.serialize_object(item))
                    elif isinstance(item, (str, int, float, bool)):
                        serialized_list.append(item)
                result[key] = serialized_list

            # On ignore les autres types (ex: objets non listés ou non sérialisables)

        return result


    def clone(self):
        try:
            obj = copy.deepcopy(self)
        except Exception as e:
            print(f"[clone] Failed to deepcopy': {e}")
        return obj
       
    
    def draw(self, ctx):
        t0 = time.perf_counter()

        if( self.enable == False ):
            return

        # Draw
        if( self.should_draw ):
        
            if( self.shadow.enabled() ):
                self.set_color(ctx, self.shadow.color)
                self._draw_shadow(ctx)
                
            self.set_color(ctx, self.color)
            self._draw(ctx)
        
        for particle in self.particles:
            particle.draw(ctx)
        self.log_draw_durations.append(time.perf_counter() - t0)
        


    def draw_surface(self, screen):
        t0 = time.perf_counter()

        if( self.enable == False ) or ( not self.should_draw ):
            return
        
        # Draw
        self._draw_surface(screen)
        self.log_draw_durations.append(time.perf_counter() - t0)
            
        if( self.first_draw ):
            self.first_draw = False
            self.create_particles(self.on_spawn.fragment)
            self.on_spawn.sound.play(self.age)

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
            self.create_particles(self.on_destroy.fragment)
            self.on_destroy.sound.play(0)


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


            lifetime = fragment.get_lifetime()

            # For TiktokMaker
            if( self.exploded ):
                lifetime = max(self.step.duration - self.age + lifetime, 0 )

            if( lifetime <= 0 ):
                continue

            # Créer la particule
            particle = InnerParticle(position=(point[0], point[1]), velocity=(vx, vy),
                                radius=fragment.get_radius(), lifetime=lifetime, color=fragment.get_color(color, self.color))
            self.particles.append(particle)