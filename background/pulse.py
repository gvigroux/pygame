import moderngl
import pygame
from background.background import Background



class Pulse(Background):

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
    // Coordonnées centrées (0,0 au centre de l'écran)
    vec2 uv = v_texcoord * 2.0 - 1.0;
    float dist = length(uv);

    // Onde pulsante
    float waves = sin(10.0 * dist - time * 4.0);

    // Atténuation avec la distance
    float intensity = 0.5 + 0.5 * waves;
    intensity *= exp(-3.0 * dist);  // adoucit loin du centre

    vec3 color = vec3(0.2, 0.5, 1.0) * intensity;

    fragColor = vec4(color, 1.0);
}

            """)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_position', 'in_texcoord') 


    def Draw(self):
        self.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.vao.render(moderngl.TRIANGLE_STRIP)
