from object.arc import Arc
from object.ball import Ball
from object.explosion import Explosion
from object.pytext import Text

OBJECT_CLASSES = {
    "explosion": Explosion,
    "arc": Arc,
    "ball": Ball,
    "text": Text,
}

class ObjectFactory:
    @staticmethod
    def create(data, pygame, clock, window_size, count, id):
        cls = OBJECT_CLASSES.get(data.get("type")) 
        return cls(data, pygame, clock, window_size, count, id)
