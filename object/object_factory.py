from object.arc import Arc
from object.ball import Ball
from object.explosion import Explosion
from object.spark import Spark
from object.text_draw import TextDraw
from object.text_surface import TextSurface
from object.timer import Timer
from object.video import Video
from object.voice import Voice

OBJECT_CLASSES = {
    "explosion": Explosion,
    "arc": Arc,
    "ball": Ball,
    "textDraw": TextDraw,
    "text": TextSurface,
    "timer": Timer,
    "voice": Voice,
    "spark": Spark,
    "video": Video,
}

class ObjectFactory:
    @staticmethod
    def create(data, pygame, window_size, count, id):
        type = data.get("type")
        cls = OBJECT_CLASSES.get(type) 
        if cls is None:
            cls = OBJECT_CLASSES.get(type[0].lower() + type[1:])            
        return cls(data, pygame, window_size, count, id)
