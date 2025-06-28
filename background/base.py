import time as timestd

class BaseBackground:
    def __init__(self):
        self.log_draw_durations = []
        self.done = False  
        self.ready = True


    def ready(self):
        return self.ready
    
    def draw(self, ctx, time, width, height):
        t0 = timestd.perf_counter()
        if not self.done:
            self._draw(ctx, time, width, height)
            self.log_draw_durations.append(timestd.perf_counter() - t0)
    
    def is_done(self):
        return self.done

    def stat(self):            
        average = sum(self.log_draw_durations) / len(self.log_draw_durations)
        print(f"AVG {type(self)} : {average*1000:.2f} ms")    
        return average