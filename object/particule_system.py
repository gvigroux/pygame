import random
import numpy as np
import moderngl

import conf
from object.object import Object


class Particle:
    def __init__(self, position, velocity, color, lifetime):
        self.position = np.array(position, dtype='f4')
        self.velocity = np.array(velocity, dtype='f4')
        self.color = np.array(color, dtype='f4')  # RGBA
        self.lifetime = lifetime
        self.age = 0.0

    def update(self, dt):
        self.position += self.velocity * dt
        self.age += dt

    def is_alive(self):
        return self.age < self.lifetime


class ParticleSystem(Object):
    
    # VAO/VBO Shared by all instances
    vao     = None
    prog    = None

    def __init__(self, ctx, vbo):
        super().__init__(ctx, vbo)
        self.ctx = ctx
        self.screen_width, self.screen_height = conf.WINDOW_SIZE
        self.particles = []

        ctx.enable(moderngl.BLEND)
        ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        if ParticleSystem.vao is None:
            ParticleSystem.prog = ctx.program(
                vertex_shader="""
                    #version 330
                    in vec2 in_pos;
                    uniform mat4 model;
                    uniform mat4 projection;
                    void main() {
                        gl_Position = projection * model * vec4(in_pos, 0.0, 1.0);
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

            quad = np.array([
                [-0.01, -0.01],
                [ 0.01, -0.01],
                [-0.01,  0.01],
                [ 0.01,  0.01],
            ], dtype='f4')

            vbo = ctx.buffer(quad.tobytes())
            ParticleSystem.vao = ctx.vertex_array(ParticleSystem.prog, [(vbo, '2f', 'in_pos')])

    def warm_up(self,):
        for i in range(50):
            self.spawn((conf.WINDOW_SIZE[0]/2, conf.WINDOW_SIZE[1]/2), (0.1, 0.1), (1.0, 0.0, 0.0, 0.1))
        #self.update(0.01)
        #self.draw()

    def screen_to_clip(self, pos):
        x, y = pos
        clip_x = (x / self.screen_width) * 2.0 - 1.0
        clip_y = 1.0 - (y / self.screen_height) * 2.0
        return np.array([clip_x, clip_y], dtype='f4')

    def spawn(self, pixel_pos, pixel_velocity, color, lifetime=1.0):
        pos = self.screen_to_clip(pixel_pos)
        vel = np.array(pixel_velocity, dtype='f4') / [self.screen_width / 2, self.screen_height / 2]

        if( len(self.particles) >= conf.FRAGMENT_MAX ):
            selection = random.randint(0, len(self.particles)-1)
            self.particles.pop(selection)

        self.particles.append(Particle(pos, vel, color, lifetime))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]
    
    def clean(self):
        pass
        #self.particles = []

    def draw(self):
        for p in self.particles:
            model = np.eye(4, dtype='f4')
            model[3, 0] = p.position[0]
            model[3, 1] = p.position[1]
            model[:2, :2] *= 0.4  # Réduit la taille à 40%

            alpha = max(0.0, 1.0 - p.age / p.lifetime)
            color = np.copy(p.color)
            color[3] *= alpha

            ParticleSystem.prog['model'].write(model.tobytes())
            ParticleSystem.prog['color'].value = tuple(color)
            self.Render(ParticleSystem.vao, ParticleSystem.prog)
            #ParticleSystem.vao.render(moderngl.TRIANGLE_STRIP)
