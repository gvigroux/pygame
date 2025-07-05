from object.arc import Arc
from object.ball import Ball
from object.explosion import Explosion
from object.pytext import Text
from object.text_draw import TextDraw
from object.text_surface import TextSurface
from object.timer import Timer

OBJECT_CLASSES = {
    "explosion": Explosion,
    "arc": Arc,
    "ball": Ball,
    "textDraw": TextDraw,
    "text": TextSurface,
    "timer": Timer,
}

class ObjectFactory:
    @staticmethod
    def create(data, pygame, window_size, count, id):
        cls = OBJECT_CLASSES.get(data.get("type")) 
        return cls(data, pygame, window_size, count, id)
