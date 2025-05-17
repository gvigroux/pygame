import math
import cairo
import moderngl
import numpy as np
import pygame
from background.background import Background
import conf


class Damier(Background):

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
    float scale = 10.0;
    float x = floor((v_texcoord.x + time * 0.05) * scale);
    float y = floor((v_texcoord.y + time * 0.05) * scale);
    float checker = mod(x + y, 2.0);
    float brightness = 0.2 + checker * 0.1;
    fragColor = vec4(vec3(brightness), 1.0);
}

            """)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_position', 'in_texcoord') 


    def Draw(self):
        self.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.vao.render(moderngl.TRIANGLE_STRIP)
