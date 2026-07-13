import pygame
from circleshape import CircleShape
from constants import *


class Shot(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, SHOT_RADIUS)

    def draw(self, surface):
        pygame.draw.circle(surface, "white",
                           (int(self.position.x), int(self.position.y)), self.radius)

    def update(self, dt):
        self.position += self.velocity * dt
        if (self.position.x < 0 or self.position.x > SCREEN_WIDTH or
                self.position.y < 0 or self.position.y > SCREEN_HEIGHT):
            self.kill()
