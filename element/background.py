from element.element import Element


class eBackground(Element):
    def __init__(self, color = (0, 0, 0, 0), size = (0,0), radius= 5):
        self.color  = color
        self.size   = size
        self.radius = radius
        self.prepare()

    def enabled(self):
        return self.color[3] > 0

    def prepare(self):
        self.radius = self.eval(self.radius)
        self.size   = self.eval(self.size)
        self.color  = self.eval_color(self.color)

    def getColor(self, alpha):
        return (self.color[0], self.color[1], self.color[2],  min(alpha, self.color[3]))
    

    def schema(self):
        return {
            "color": ("str", "Color"),
            "size": ("str", "Size"),
            "radius": ("int", "Radius"),
        }