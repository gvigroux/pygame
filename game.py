import json
import os
import time
from background.backgrounds import BackgroundFactory
from object.arc import Arc
from object.ball import Ball
from object.pytext import Text
from object.object_factory import ObjectFactory


data_fps = json.loads('''{
      "type": "textDraw",
      "text": {
        "update": "f'F{fps:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "10%", "y": "90%", "justify": "none" }}''')

data_step = json.loads('''{
      "type": "textDraw",
      "text": {
        "update": "f'S{step:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "35%", "y": "90%", "justify": "none" }}''')


data_blocked = json.loads('''{
      "type": "textDraw",
      "text": {
        "update": "f'B{blocked:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "55%", "y": "90%", "justify": "none" }}''')

data_timing = json.loads('''{
      "type": "textDraw",
      "text": {
        "update": "f'{timing:.3f}s'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "75%", "y": "90%", "justify": "none" }}''')

data_mouse = json.loads('''{
      "type": "textDraw",
      "text": {
        "update": "f'{mouse}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 30, "family": "Wumpus Mono"}
      }, "position": { "x": "50%", "y": "70%", "justify": "H" }}''')



class Game:
    def __init__(self, pygame): 
        self.pygame = pygame

        self.start_delay = 0
                
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.2)  # 50% du volume

        self.objects = []
        self.has_music  = False

    
    def debug(self, value = False):        
        if( value ):
            self.objects.append(Text(data_fps, self.pygame, self.window_size,0,0))
            self.objects.append(Text(data_step,self.pygame, self.window_size,0,0))
            self.objects.append(Text(data_blocked,self.pygame, self.window_size,0,0))
            self.objects.append(Text(data_timing,self.pygame, self.window_size,0,0))
            self.objects.append(Text(data_mouse,self.pygame, self.window_size,0,0))
            
    def load(self, filename = "config.json"):

        file_path = os.path.dirname(os.path.realpath(__file__))
        file = os.path.join(file_path, filename)
        if( os.path.isfile(file) == False ):
            exit()

        # Lecture avec encodage UTF-8 explicite et gestion d'erreur
        with open(file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self._load_params()
        self._load_objects()
        self.start_delay = self.pygame.time.get_ticks()


    def _load_params(self):
        settings = self.config.get("settings", {})
        self.end_step = settings.get("end_step", -1)
        self.window_size = settings.get("window_size", [540, 960])
        if( settings.get("debug", False) ):
            self.debug(True)
        
        ############### Background ###############
        background_config = self.config.get("background", [])
        self.background = BackgroundFactory.create(self.pygame, background_config.get("type", "concentric_wave"),*self.window_size, background_config)

        while not self.background.ready:
            time.sleep(0.01)

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
        for data in self.config.get("objects", []):
            count = data.get("count", 1) 
            # Automatically split text
            if( data.get("type") == "text" ) and data.get("split", False):
                if( count > 1 ):
                    print(f"\033[38;5;208mWarning (Text): The count property is ignored for text objects!\033[0m")
                parts = data.get("text").get("value").split('\\n')
                count = len(parts)
                
            for i in range(count):

                # Update text value
                if( data.get("type") == "text" ) and data.get("split", False):
                    data["text"]["value"] = parts[i]

                object = ObjectFactory.create(data, self.pygame, self.window_size, count, i)
                if( isinstance(object, Ball) ):
                    if not any(object.check_ball_collision(other) for other in self.objects if isinstance(other, Ball)):
                        self.objects.append(object)
                else:
                    self.objects.append(object)

    @property
    def age(self):
        return (self.pygame.time.get_ticks() - self.start_delay)/ 1000

    def update(self, dt, current_step, clock, obj_block):

        for object in self.objects: 
            object.update(dt, current_step, clock, obj_block)

        # Start music
        if self.has_music and ( self.age >= self.music_delay ) and ( not self.music_stated ): 
            self.pygame.mixer.music.play(loops=self.music_loops, start=self.music_start, fade_ms=self.music_fade_ms)
            self.music_stated = True

        # New background if needed
        if( self.background.is_done() ):
            self.background = BackgroundFactory.create(self.pygame, "concentric_wave", self.window_size[0], self.window_size[1])
                
        # Check if we need to explose balls
        arcs_count = sum(1 for obj in self.objects if isinstance(obj, Arc) and obj.is_alive(current_step))
        if( arcs_count == 0 ):        
            for i, obj in enumerate(self.objects):
                if isinstance(obj, Ball) and obj.step.block == True:
                    obj.explode()


    def draw_on_context(self, ctx, current_time):

        self.background.draw(ctx, current_time)
        
        for object in self.objects:
            object.draw(ctx)

        

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

 