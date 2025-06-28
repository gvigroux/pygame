from element.font import eFont
from element.outline import eOutline


class eText:
    def __init__(self, value= "", color = (255, 255, 255, 255), font= {}, outline = {}, padding= (0,0,0,0), update= ""):
        self.value = value
        self.color = color
        if( isinstance(color, str) ):
            self.color = eval(color)
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)
        self.padding   = padding
        if( isinstance(padding, str) ):
            self.padding = eval(padding)
        self.update     = update 
        self.font       = eFont(**font)
        self.outline    = eOutline(**outline)


    def enabled(self):
        return len(self.value) > 0

    def getColor(self, alpha):
        return (self.color[0], self.color[1], self.color[2],  min(alpha, self.color[3]))
    

    