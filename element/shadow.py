from element.element import Element


class eShadow(Element):
    def __init__(self, color = (0, 0, 0, 100), offset = 0):
        self.color  = color
        self.offset = offset
        self.prepare()

    def enabled(self):
        return self.offset > 0
        
    def prepare(self):
        self.color  = self.eval_color(self.color)
        self.offset = self.eval(self.offset)

    def schema(self):
        return {
            "color": ("str", "Color"),
            "offset": ("float", "Offset"),
        }
