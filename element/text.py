from element.background import eBackground
from element.font import eFont
from element.outline import eOutline


class eText:
    def __init__(self, value= "", color = (255, 255, 255, 255), font= {}, outline = {}, padding= (0,0,0,0), margin= (0,0,0,0), background = {}, update= ""):
        self.value = value
        self.color = color
        if( isinstance(color, str) ):
            self.color = eval(color)
        if( len(self.color) == 3 ):
            self.color = (self.color[0], self.color[1], self.color[2], 255)
        self.padding   = padding
        if( isinstance(padding, str) ):
            self.padding = eval(padding)
        self.margin   = margin
        if( isinstance(margin, str) ):
            self.margin = eval(margin)
        self.update     = update 
        self.font       = eFont(**font)
        self.outline    = eOutline(**outline)
        self.background = eBackground(**background)


    def enabled(self):
        return len(self.value) > 0

    def getColor(self, alpha):
        return (self.color[0], self.color[1], self.color[2],  min(alpha, self.color[3]))
    

    