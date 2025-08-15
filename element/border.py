from element.element import Element


class eBorder(Element):
    def __init__(self, color = (0, 0, 0, 100), width = 1):
        self.color = color
        self.width = width
        self.prepare()

    def enabled(self):
        return self.width > 0

    def schema(self):
        return {
            "color": ("str", "Color"),
            "width": ("float", "Width"),
        }
        
    def prepare(self):
        self.color = self.eval_color(self.color)
        self.width = self.eval(self.width)