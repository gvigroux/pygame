import math


class InnerParticle:
    def __init__(self, position, velocity, lifetime=0.5, radius=2, color=(1, 1, 1, 1)):
        self.position = list(position)
        self.velocity = velocity  # (vx, vy)
        self.lifetime = lifetime
        self.radius = radius
        self.age = 0.0
        self.alpha = 1.0
        self.color = color

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.alpha = 0.0
        else:
            self.position[0] += self.velocity[0] * dt
            self.position[1] += self.velocity[1] * dt
            self.alpha = 1.0 - self.age / self.lifetime

    def draw(self, ctx):
        if self.alpha <= 0:
            return
        r, g, b, a = self.color
        ctx.set_source_rgba(r, g, b, self.alpha)
        ctx.arc(self.position[0], self.position[1], self.radius, 0, 2 * math.pi)
        ctx.fill()
