from object.ball import Ball
from object.object_factory import ObjectFactory


class Game:
    def __init__(self, pygame, config , window_size): 
        self.pygame = pygame
        self.config = config
        self.window_size = window_size
        self.objects = []

            
    def load(self):
            
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

                object = ObjectFactory.create(data, self.pygame, None, self.window_size, count, i)
                if( isinstance(object, Ball) ):
                    if not any(object.check_ball_collision(other) for other in object if isinstance(other, Ball)):
                        self.objects.append(object)
                else:
                    self.objects.append(object)

    def block_count(self, step):
        return sum(1 for obj in self.objects if obj.block(0))
    
    def clean(self):
        # Nettoyage des objets détruits
        self.objects = [obj for obj in self.objects if not obj.is_destroyed()]