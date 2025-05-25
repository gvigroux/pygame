import moderngl
import numpy as np


class Particle:
    
    # VAO/VBO Shared by all instances
    vao = None
    prog = None

    def __init__(self, context, vbo, window_size, pos, velocity, lifetime, color):
        self.pos = np.array(pos, dtype=np.float32)
        self.vel = np.array(velocity, dtype=np.float32)
        self.lifetime = lifetime
        self.age = 0.0
        self.color = color  # RGBA


        if Particle.vao is None:
            Particle.prog = context.program(
                vertex_shader="""
                    #version 330
                    in vec2 in_position;
                    uniform vec2 offset;
                    uniform float scale;
                    void main() {
                        gl_Position = vec4(in_position * scale + offset, 0.0, 1.0);
                    }
                """, 
                fragment_shader="""
                    #version 330
                    uniform vec4 color;
                    out vec4 fragColor;
                    void main() {
                        fragColor = color;
                    }
                """
            )            
            Particle.vao = context.simple_vertex_array(self.prog, vbo, 'in_position')

    def update(self, dt):
        self.pos += self.vel * dt
        self.age += dt

    def is_alive(self):
        return self.age < self.lifetime

    def alpha(self):
        return max(0.0, 1.0 - self.age / self.lifetime)
    
    def draw(self):
        Particle.prog['offset'].value = tuple(self.pos)
        Particle.prog['scale'].value = 0.015
        Particle.prog['color'].value = (*self.color[:3], self.alpha())
        Particle.vao.render(moderngl.TRIANGLE_STRIP)
