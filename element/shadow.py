class eShadow:
    def __init__(self, color = (0, 0, 0, 100), offset = 0):
        self.color = color
        if( isinstance(color, str) ):   
            self.color = eval(color)
        self.offset = offset

    def enabled(self):
        return self.offset > 0
