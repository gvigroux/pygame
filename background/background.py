import moderngl
import numpy as np
import conf
from object.object import Object


class Background:
    def __init__(self, context, vbo):
        self.context = context
        self.vbo = vbo
        self.resize(conf.WINDOW_SIZE[0], conf.WINDOW_SIZE[1])

    def resize(self, width, height):
        aspect = width / height
        self.projection = np.array([
            [1.0,      0.0, 0.0, 0.0],
            [0.0, aspect, 0.0, 0.0],
            [0.0,     0.0, 1.0, 0.0],
            [0.0,     0.0, 0.0, 1.0],
        ], dtype='f4')

    def Render(self, vao, prog):
        #prog['bg_projection'].write(self.projection.tobytes())       
        vao.render(moderngl.TRIANGLE_STRIP) 

