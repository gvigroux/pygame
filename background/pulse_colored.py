import pygame
from background.background import Background



class PulseColored(Background):

    def __init__(self, context, vbo, window_size):
        super().__init__(context, vbo, window_size)
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
    uniform vec2 resolution;

    void main() {
        // Centrer les coordonnées
        vec2 uv = v_texcoord * 2.0 - 1.0;

        // Corriger l’aspect ratio (compresse horizontalement si écran large)
        uv.x *= resolution.x / resolution.y;

        float dist = length(uv);

        // Pulsation en fonction du temps et de la distance
        float wave = sin(10.0 * dist - time * 4.0);

        // Couleur en fonction de la distance et du temps (arc-en-ciel cyclique)
        float hue = fract(dist * 2.0 - time * 0.5);
        vec3 color = vec3(
            0.5 + 0.5 * sin(6.2831 * hue + 0.0),
            0.5 + 0.5 * sin(6.2831 * hue + 2.094),
            0.5 + 0.5 * sin(6.2831 * hue + 4.188)
        );

        // Intensité de l’onde avec atténuation
        float intensity = 0.5 + 0.5 * wave;
        intensity *= exp(-2.5 * dist);  // adoucissement vers l’extérieur

        fragColor = vec4(color * intensity, 1.0);
    }
"""
)
        self.vao = context.simple_vertex_array(self.prog, vbo, 'in_position', 'in_texcoord') 


    def Draw(self):
        self.prog['time'].value = pygame.time.get_ticks() / 1000.0
        self.prog['resolution'].value = conf.WINDOW_SIZE
        self.Render(self.vao, self.prog)
