import json
import os
import threading
import time

import cairo
from background.backgrounds import BackgroundFactory
from object.arc import Arc
from object.ball import Ball
from object.object_factory import ObjectFactory
from object.text_surface import TextSurface
from object.video import Video


data_fps = json.loads('''{
      "type": "textDraw",
      "label": "Debug - FPS",
      "text": {
        "update": "f'F{fps:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "10%", "y": "90%", "justify": "none" }}''')

data_step = json.loads('''{
      "type": "textDraw",
      "label": "Debug - Step",
      "text": {
        "update": "f'S{step:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "35%", "y": "90%", "justify": "none" }}''')


data_blocked = json.loads('''{
      "type": "textDraw",
      "label": "Debug - Blocked",
      "text": {
        "update": "f'B{blocked:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "55%", "y": "90%", "justify": "none" }}''')

data_timing = json.loads('''{
      "type": "textDraw",
      "label": "Debug - Timing",
      "text": {
        "update": "f'{timing:.3f}s'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "75%", "y": "90%", "justify": "none" }}''')

data_mouse = json.loads('''{
      "type": "textDraw",
      "label": "Debug - Mouse",
      "text": {
        "update": "f'{mouse}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "50%", "y": "70%", "justify": "H" }}''')



class Game:
    def __init__(self, pygame):
        pygame.init()
        self.pygame = pygame
        pygame.font.init()
        pygame.font.get_fonts()
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.2)  # 50% du volume

        self.objects = []
        self.has_music  = False
        self.background = None
        self.end_step   = 1
        self.debug      = False

    
    def deactivate_window(self):        
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        #self.pygame.quit()
        self.pygame.display.quit()
        self.pygame.init()

    def run(self):
        os.environ.pop("SDL_VIDEODRIVER", None)
        #self.pygame.quit()
        self.pygame.display.quit()
        self.pygame.init()
        self.pygame.font.init()
        self.pygame.font.get_fonts()

        self.start_time = time.time()        
        for object in self.objects:
            object.reset(time.time(), 0)
                
        # Cairo surface et contexte réutilisables
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *self.window_size)
        ctx     = cairo.Context(surface)
        screen  = self.pygame.display.set_mode((self.window_size[0], self.window_size[1]), self.pygame.DOUBLEBUF | self.pygame.SRCALPHA)
                
        dt_history = []
        clock = self.pygame.time.Clock()
        last_time = time.perf_counter()
        running = True
        current_step = 0
        obj_block = self.block_count(0)


        while running:
            t0 = time.perf_counter()

            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    running = False           
                    
                elif event.type == self.pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  
                        x, y = event.pos
                        print(f"{x*100/self.window_size[0]:.1f}% / {y*100/self.window_size[1]:.1f}% at {self.age:.1f}s")
                    
                elif event.type == self.pygame.KEYDOWN:
                    if event.key == self.pygame.K_c and (self.pygame.key.get_mods() & self.pygame.KMOD_CTRL):
                        print("Ctrl+C détecté via clavier (pas SIGINT)")
                        running = False

            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time

            # ajustement du dt pour éviter les dépassements
            dt_history.append(dt)
            if len(dt_history) > 5:
                dt_history.pop(0)
            dt = sum(dt_history) / len(dt_history)

            # End of game
            if( self.is_finished(current_step) ):
                running = False

            #self.clean()

            # Comptage des objets bloquants avant mise à jour
            prev_block_count = obj_block
            obj_block = self.block_count(current_step)

            # Avancement du step si plus de blocage
            if prev_block_count > 0 and obj_block == 0:
                current_step += 1

            #***********************************************************************
            # Check collisions 

            t1 = time.perf_counter()
            self.check_collisions()        
            self.update(dt, current_step, clock, obj_block)            
            t2 = time.perf_counter()

            #***********************************************************************
            # Cairo rendering

            ctx.save()
            ctx.set_operator(cairo.OPERATOR_CLEAR)
            ctx.paint()
            ctx.restore()
            
            t3 = time.perf_counter()

            #***********************************************************************
            # Draw

            self.draw(screen, ctx, current_time)
            t4 = time.perf_counter()

            # Step 3 : Cairo to Pygame
            raw_buf = surface.get_data()
            img     = self.pygame.image.frombuffer(raw_buf, self.window_size, "BGRA").convert_alpha()
        
            # Step 4 : Affichage
            screen.blit(img, (0, 0))

            self.pygame.display.flip()
            t5 = time.perf_counter()
            clock.tick(60)
        
            # Debug print
            #fps = clock.get_fps()
            #print(f"FIRST: {(t1 - t0)*1000:.2f} ms | UPDATE: {(t2 - t1)*1000:.2f} ms | BACK: {(t3 - t2)*1000:.2f} ms | DRAW {(t4 - t3)*1000:.2f} | BLIT {(t5 - t4)*1000:.2f} | TOTAL: {(t5 - t0)*1000:.2f} ms | dt={dt*1000:.2f}ms | FPS={fps:.2f}")
            #print(fps)
        self.pygame.display.quit()
        #self.pygame.quit()

    def reset(self):
        self.objects = []
        self.has_music  = False
        self.background = None
    
    def set_debug(self, value = False):        
        if( value ):
            self.objects.append(ObjectFactory.create(data_fps, self.window_size,0,0))
            self.objects.append(ObjectFactory.create(data_step, self.window_size,0,0))
            self.objects.append(ObjectFactory.create(data_mouse, self.window_size,0,0))
            self.objects.append(ObjectFactory.create(data_timing, self.window_size,0,0))
            self.objects.append(ObjectFactory.create(data_blocked, self.window_size,0,0))

    def get_settings(self):
        return {
                "end_step": self.end_step,
                "debug": self.debug,
                "window_size": self.window_size
        }
            
    def load(self, filepath = "C:\\Users\\gvigroux\\OneDrive - THALES SA\\Documents\\Projects\\pygame\\config.json", avoid_debug = False, load_background = True):

        # Lecture avec encodage UTF-8 explicite et gestion d'erreur
        with open(filepath, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self._load_params(avoid_debug, load_background)

    def load_objects(self, waitVideo = True):
        self._load_objects()

        self.start_lazy_loading()

        # Wait first video to be loaded
        for object in self.objects:
            if isinstance(object, Video):
                while not object.is_ready():
                    time.sleep(0.01)
                break

        self.start_time = time.time()


    def _load_params(self, avoid_debug, load_background):
        settings = self.config.get("settings", {})
        self.end_step = settings.get("end_step", -1)
        self.window_size = settings.get("window_size", [540, 960])
        self.debug = settings.get("debug", False)
        if( self.debug and not avoid_debug):
            self.set_debug(True)
        
        ############### Background ###############     
        if( load_background ):
            print("Load Background") 
            background_config = self.config.get("background", {})
            self.background = BackgroundFactory.create(self.pygame, background_config.get("type", "concentric_wave"),*self.window_size, background_config)

            while not self.background.ready:
                time.sleep(0.01)
            print("Background ready")

        ############### Music ###############
        self.music_stated = False
        self.music_delay = self.config.get("music", {}).get("delay", 0)
        music_detail = self.config.get("music", {})
        if( music_detail.get("file", False) ):
            self.has_music  = True
            self.pygame.mixer.music.load(music_detail.get("file"))
            self.music_start = music_detail.get("start", 0)
            self.music_fade_ms = music_detail.get("fade_ms", 0)
            self.music_loops = 0
            if( music_detail.get("loop", True) ):
                self.music_loops = 1


    def _load_objects(self):
        added_video_paths = set()

        for data in self.config.get("objects", []):
            count = data.get("count", 1) 
            # Automatically split text
            if( data.get("type", "").lower() == "text" ) and data.get("split", False):
                if( count > 1 ):
                    print(f"\033[38;5;208mWarning (Text): The count property is ignored for text objects!\033[0m")
                parts = data.get("text").get("value").split('\\n')
                count = len(parts)
                
            for i in range(count):

                # Update text value
                if( data.get("type", "").lower() == "text" ) and data.get("split", False):
                    data["text"]["value"] = parts[i]

                if( data.get("type", "").lower() == "video" and data.get("path") in added_video_paths ):
                    tmp = next((obj for obj in self.objects if getattr(obj, "path", None) == data.get("path")), None)
                    object = tmp.clone()
                    object.step.delay = data.get("step", {}).get("delay", 0)

                else:
                    object = ObjectFactory.create(data, self.window_size, count, i)

                if( isinstance(object, Ball) ):
                    if not any(object.check_ball_collision(other) for other in self.objects if isinstance(other, Ball)):
                        self.objects.append(object)
                elif( isinstance(object, Video) ):
                    added_video_paths.add(object.path)
                    self.objects.append(object)
                else:
                    self.objects.append(object)


    def start_lazy_loading(self):
        threading.Thread(target=self._load_videos_sequentially, args=(), daemon=True).start()


    def _on_video_ready(self, object):
        print(object.path)
        for _object in self.objects:
            if isinstance(_object, Video) and object.path == _object.path and object != _object:        
                _object.surface_frames = object.surface_frames
                _object._frames_ready.set()

    def _load_videos_sequentially(self):
        added_video_paths = set()
        for object in self.objects:
            if isinstance(object, Video) and object.path not in added_video_paths:
                object.load()
                object.on_ready_callbacks.append(self._on_video_ready)
                added_video_paths.add(object.path)
                while not object.is_ready():
                    time.sleep(0.1)
        

    def add_object_factory(self, data):
        object = ObjectFactory.create(data, self.window_size, 1, 0)
        self.objects.append(object)
        return object
    
    def add_object(self, object):
        self.objects.append(object)
    
    def remove_object(self, target):
        if target in self.objects:
            self.objects.remove(target)
            
    @property
    def age(self):
        return time.time() - self.start_time

    def update(self, dt, current_step, clock, obj_block):

        for object in self.objects: 
            object.update(dt, current_step, clock, obj_block)

        # Start music
        if self.has_music and ( self.age >= self.music_delay ) and ( not self.music_stated ): 
            self.pygame.mixer.music.play(loops=self.music_loops, start=self.music_start, fade_ms=self.music_fade_ms)
            self.music_stated = True

        # New background if needed
        if( self.background is not None and self.background.is_done() ):
            self.background = BackgroundFactory.create(self.pygame, "concentric_wave", self.window_size[0], self.window_size[1])
                
        # Check if we need to explose balls
        arcs_count = sum(1 for obj in self.objects if isinstance(obj, Arc) and obj.is_alive(current_step))
        if( arcs_count == 0 ):        
            for i, obj in enumerate(self.objects):
                if isinstance(obj, Ball) and obj.step.block == True:
                    obj.explode()


    def draw_on_context(self, ctx, current_time):

        if( self.background is not None):
           self.background.draw(ctx, current_time)
        
        for object in self.objects:
            object.draw(ctx)

    def draw(self, screen, ctx, current_time):

        #if( self.background is not None):
        #   self.background.draw(ctx, current_time)
        
        for object in self.objects:
            t0 = time.perf_counter()
            if( isinstance(object, Video) ):
                object.draw_surface(screen)
            elif( isinstance(object, TextSurface) ):
                object.draw_surface(screen)
            else:
                object.draw(ctx)
            t1 = time.perf_counter()
            if( t1 - t0 > 0.01 ):
                print(f"SLOW Draw {object.label}: {(t1 - t0)*1000:.2f} ms")

    def reorder_objects(self):
        print("Reorder objects")
        self.objects.sort(key=lambda obj: (-obj.track_id, obj.step.delay))

        
    def block_count(self, step):
        return sum(1 for obj in self.objects if obj.block(step))
    
    def clean(self):
        # Nettoyage des objets détruits
        self.objects = [obj for obj in self.objects if not obj.is_destroyed()]

    def is_finished(self,current_step):
        return current_step >= self.end_step

    def check_collisions(self):
        for i, obj in enumerate(self.objects):
            if isinstance(obj, Ball):
                for j, other in enumerate(self.objects):
                    if i != j:
                        obj.check_collision(other)

 