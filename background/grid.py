import math
import cairo
import moderngl
import numpy as np
import pygame
from background.background import Background
import conf


class Grid(Background):

    def __init__(self, context, vbo):
        super().__init__(context, vbo)
        self.prog = context.program(
            vertex_shader="""
                #version 330
                in vec2 in_position;
                in vec2 in_texcoord;
                out vec2 v_texcoord;

                void main() {
                    gl_Position = vec4(in_position, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader="""
#version 330
in vec2 v_texcoord;
out vec4 fragColor;

uniform float time;

void main() {
    float x = mod(v_texcoord.x * 20.0 + time, 1.0);
    float y = mod(v_texcoord.y * 20.0 + time, 1.0);
    float line = step(0.95, x) + step(0.95, y);
    fragColor = mix(vec4(0.05, 0.05, 0.1, 1.0), vec4(0.2, 0.6, 1.0, 1.0), line);
}

            """)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_position', 'in_texcoord') 


    def Draw(self):
        self.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.vao.render(moderngl.TRIANGLE_STRIP)
