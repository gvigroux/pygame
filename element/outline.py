class eOutline:
    def __init__(self, color = (0, 0, 0, 0), width = 0):
        self.color = color
        if( isinstance(color, str) ):   
            self.color = eval(color)
        self.width = width

    def enabled(self):
        return self.width > 0

    def schema(self):
        return {
            "color": ("str", "Color"),
            "width": ("float", "Width"),
        }