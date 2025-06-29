import json
from object.ball import Ball
from object.pytext import Text
from object.object_factory import ObjectFactory


data_fps = json.loads('''{
      "type": "text",
      "text": {
        "update": "f'{fps:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 40, "family": "Wumpus Mono"}
      }, "position": { "x": "20%", "y": "90%", "justify": "none" }}''')


data_step = json.loads('''{
      "type": "text",
      "text": {
        "update": "f'{step:02d}'",
        "color": "(255, 0, 0, 255)",
        "font": { "size": 40, "family": "Wumpus Mono"}
      }, "position": { "x": "80%", "y": "90%", "justify": "none" }}''')


class Game:
    def __init__(self, pygame, config , window_size): 
        self.pygame = pygame
        self.config = config
        self.window_size = window_size
        self.debug = True
        self.objects = []

            
    def load(self):

        if( self.debug ):
            self.objects.append(Text(data_fps, self.pygame, self.window_size,0,0))
            self.objects.append(Text(data_step,self.pygame, self.window_size,0,0))

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





    def block_count(self, step):
        return sum(1 for obj in self.objects if obj.block(0))
    
    def clean(self):
        # Nettoyage des objets détruits
        self.objects = [obj for obj in self.objects if not obj.is_destroyed()]


    def check_collisions(self):
        for i, obj in enumerate(self.objects):
            if isinstance(obj, Ball):
                for j, other in enumerate(self.objects):
                    if i != j:
                        obj.check_collision(other)