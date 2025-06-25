
import math
import random


safe_globals = {
    "random": random,
    "math": math,
    "total": 0,
    'i': 0
}

class eStep:
    def __init__(self, object, start = 0 , stop = -1, delay = 0, update_delay = 0, duration = -1, fade_in = 0, fade_out = 0, block = True):
        self.index = object.index
        self.count = object.amount
        self.start = start
        self.stop = stop
        self.delay = delay
        self.update_delay = update_delay
        self.duration = duration
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.block = block

        if( self.fade_out > 0 ):   
            self.duration -= self.fade_out

              
        safe_globals['total']   = object.amount
        safe_globals['i']       = object.index
        if isinstance(self.delay, str):
            self.delay = eval(self.delay, {"__builtins__": {}}, safe_globals)
        if isinstance(self.update_delay, str):
            self.update_delay = eval(self.update_delay, {"__builtins__": {}}, safe_globals)
        
        if( self.duration <= 0 ):
            print(f"\033[38;5;208mWarning ({object}): Invalid duration or fade_out!\033[0m")
        if( self.fade_in + self.fade_out > self.duration ):
            print(f"\033[38;5;208mWarning ({object}): Invalid fade_in & fade_out!\033[0m")



    def enabled(self):
        return True
