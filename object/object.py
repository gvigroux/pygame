import moderngl
import numpy as np
import pygame
import conf


class Object:
    def __init__(self, context, vbo):
        self.context = context
        self.vbo = vbo
        self.window_size = conf.WINDOW_SIZE
        self.ratio = self.window_size[0] / self.window_size[1]
        self.projection_matrix = self.get_projection_matrix().tobytes()

    def Update(self):
        pass

    def Draw(self):
        pass


    def Render(self, vao, prog):
        prog['projection'].write(self.projection_matrix)
        vao.render(moderngl.TRIANGLE_STRIP)
  
    def get_projection_matrix(self):
        width, height = conf.WINDOW_SIZE
        aspect_ratio = width / height
        if aspect_ratio > 1.0:
            scale_x, scale_y = 1.0 / aspect_ratio, 1.0
        else:
            scale_x, scale_y = 1.0, aspect_ratio

        #scale_x = 1.0
        #scale_y = 1.0
        return np.array([
            [scale_x, 0.0,     0.0, 0.0],
            [0.0,     scale_y, 0.0, 0.0],
            [0.0,     0.0,     1.0, 0.0],
            [0.0,     0.0,     0.0, 1.0],
        ], dtype='f4')


    def gl_to_screen(self, gl_pos):
        """Convertit une position OpenGL (-1 à 1) en pixels écran (haut-gauche)"""
        x = int((gl_pos[0] + 1) * 0.5 * self.window_size[0])
        y = int((1 - (gl_pos[1] + 1) * 0.5) * self.window_size[1])
        return (x, y)

    def screen_to_gl(self, screen_pos):
        """Convertit une position en pixels écran vers OpenGL (-1 à 1)"""
        x = (screen_pos[0] / self.window_size[0]) * 2.0 - 1.0
        y = -((screen_pos[1] / self.window_size[1]) * 2.0 - 1.0)
        return (x, y)
    