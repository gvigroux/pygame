class eBackground:
    def __init__(self, color = (0, 0, 0, 0), size = (0,0), radius= 5):
        self.color = color
        if( isinstance(color, str) ):   
            self.color = eval(color)
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)
        self.size   = size
        self.radius = radius

    def enabled(self):
        return self.color[3] > 0

    def getColor(self, alpha):
        return (self.color[0], self.color[1], self.color[2],  min(alpha, self.color[3]))
    

    