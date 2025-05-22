import math
import cairo
import moderngl
import numpy as np
import pygame
from background.background import Background

class Plasma(Background):

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
    float x = v_texcoord.x * 10.0;
    float y = v_texcoord.y * 10.0;
    float color = sin(x + time) + sin(y + time) + sin(x + y + time);
    color = 0.5 + 0.5 * sin(color);
    fragColor = vec4(vec3(color), 1.0);
}

            """)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_position', 'in_texcoord') 


    def Draw(self):
        self.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.vao.render(moderngl.TRIANGLE_STRIP)
