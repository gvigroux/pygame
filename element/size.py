


from element.element import Element


class eSize(Element):
    def __init__(self, window_size, total = 0, i = 0, width = "50%" , height = "50%"):
        self.window_size = window_size
        self.raw_width  = width
        self.raw_height = height
        self.total = total
        self.i = i
        self.width  = width
        self.height = height
       
    def __repr__(self):
        return f"eSize(width={self.width}, height={self.height})"
    
    def prepare(self):
        self.width  = self.eval(self.width, self.window_size[0])
        self.height = self.eval(self.height, self.window_size[1])
    
    def get(self):
        return (self.width, self.height)
    
    def enabled(self):
        return True

    def schema(self):
        return {
            "width": ("inteval", "Width"),
            "height": ("inteval", "Height"),
        }