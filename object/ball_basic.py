import math
import pygame
from pygame import Vector2


class Ball:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.position = Vector2( self.screen_width/2,  self.screen_height/2)
        self.color = (0,0,0)
        self.gravity = Vector2(0,0.32)
        self.velocity = Vector2(-7,-7)
        self.prevPos = Vector2(self.position.x,self.position.y)
        self.radius = 30

    def update(self, sound):
        self.prevPos = Vector2(self.position.x,self.position.y)

        # movement
        self.velocity += self.gravity
        self.position += self.velocity

        dirToCenter = Vector2(self.position.x - self.screen_width/2,self.position.y - self.screen_height/2)
        if self.isCollide():
            pygame.mixer.Sound.play(sound)
            self.radius += 1
            self.position = Vector2(self.prevPos.x,self.prevPos.y)
            v = math.sqrt(self.velocity.x * self.velocity.x + self.velocity.y * self.velocity.y)
            angleToCollisionPoint = math.atan2(-dirToCenter.y,dirToCenter.x)
            oldAngle = math.atan2(-self.velocity.y,self.velocity.x)
            newAngle = 2 * angleToCollisionPoint - oldAngle
            self.velocity = Vector2(-v * math.cos(newAngle),v * math.sin(newAngle))

    def isCollide(self):
        if self.distance(self.position.x,self.position.y,self.screen_width/2,self.screen_height/2) > self.screen_width/2 - self.radius:
            return True
        return False

    def distance(self, x1, y1, x2, y2):
        return math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2) * 1.0)

    def draw(self, surface):
        pygame.draw.circle(surface,self.color,(self.position.x,self.position.y),self.radius)
