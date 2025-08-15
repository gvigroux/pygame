from element.border import eBorder


class eOutline(eBorder):
    def __init__(self, color = (0, 0, 0, 0), width = 0):
        super().__init__(color, width)