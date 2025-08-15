import time

from object.arc import Arc
from object.arcs import Arcs
from object.ball import Ball
from object.balls import Balls
from object.explosion import Explosion
from object.sound import Sound
from object.spark import Spark
from object.text_draw import TextDraw
from object.text_surface import TextSurface
from object.timer import Timer
from object.video import Video
from object.voice import Voice

OBJECT_CLASSES = {
    "explosion": Explosion,
    "arc": Arc,
    "arcs": Arcs,
    "ball": Ball,
    "balls": Balls,
    "textDraw": TextDraw,
    "text": TextSurface,
    "TextSurface": TextSurface,
    "timer": Timer,
    "voice": Voice,
    "spark": Spark,
    "video": Video,
    "sound": Sound,
}

class ObjectFactory:
    @staticmethod
    def create(data, window_size, count, id): #, on_thumb_ready=None, on_ready=None
        type = data.get("type")
        t0 = time.perf_counter()
        cls = OBJECT_CLASSES.get(type) 
        if cls is None:
            cls = OBJECT_CLASSES.get(type[0].lower() + type[1:])            
        obj = cls(data, window_size, count, id)
        t1 = time.perf_counter()
        if( t1 - t0 > 0.01 ):
            print(f"SLOW Create {type}: {(t1 - t0)*1000:.2f} ms")
        return obj
