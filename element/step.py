
import math
import random

from element.element import Element



class eStep(Element):
    def __init__(self, object, start = 0 , stop = -1, delay = 0, update_delay = 0, duration = -1, fade_in = 0, fade_out = 0, block = False, explode = False):
        #self.index = object.index
        #self.count = object.amount
        self.object = object
        self.start = start
        self.stop = stop
        self.delay = delay
        self.update_delay = update_delay
        self.duration = duration
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.block = block
        self.explode = explode
        self.prepare()


    # def float(self, value, default):
    #     if isinstance(value, int) or isinstance(value, float):
    #         return value
    #     safe_globals['total']   = self.amount
    #     safe_globals['i']       = self.index
    #     try:
    #         if isinstance(value, str):
    #             value = eval(value, {"__builtins__": {}}, safe_globals)
    #     except:
    #         value = default
    #     return value

    def prepare(self):
        
        self.start = self.eval(self.start)
        self.stop = self.eval(self.stop)
        self.delay = self.eval(self.delay)
        self.update_delay = self.eval(self.update_delay)
        self.duration = self.eval(self.duration)
        self.fade_in = self.eval(self.fade_in)
        self.fade_out = self.eval(self.fade_out)
    
        # self.start = self.float(self.start, 0)
        # self.stop = self.float(self.stop, -1)
        # self.delay = self.float(self.delay, 0)
        # self.update_delay = self.float(self.update_delay, 0)
        # self.duration = self.float(self.duration, -1)
        # self.fade_in = self.float(self.fade_in, 0)
        # self.fade_out = self.float(self.fade_out, 0)

        if( self.duration <= 0 ) and ( self.duration != -1):
            print(f"\033[38;5;208mWarning ({self.object}): Invalid duration or fade_out!\033[0m")
        if( self.fade_in + self.fade_out > self.duration ) and ( self.duration != -1):
            print(f"\033[38;5;208mWarning ({self.object}): Invalid fade_in & fade_out!\033[0m")

    def enabled(self):
        return True
    
    def schema(self):
        return {
            "start": ("float", "Start"),
            "stop": ("float", "End"),
            "duration": ("float", "Duration"),
            "fade_in": ("float", "Fade In"),
            "fade_out": ("float", "Fade Out"),
            "delay": ("float", "Delay"),
            "block": ("bool", "Block"),
            "explode": ("bool", "Explode"),
            "update_delay": ("float", "Update Delay")
        }

    @classmethod
    def parameter_fields(cls):
        return [
            {"name": "start", "type": "float", "default": 0},
            {"name": "stop", "type": "float", "default": -1}
        ]
        #{"name": "duration", "type": "float", "default": 0}