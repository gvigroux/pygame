class eBorder:
    def __init__(self, color = (0, 0, 0, 100), width = 1):
        self.color = color
        if( isinstance(color, str) ):   
            self.color = eval(color)
        self.width = width

    def enabled(self):
        return self.width > 0
