import random

import pygame
from constants import *
from circleshape import CircleShape
from logger import log_event


class Asteroid(CircleShape):
    def __init__(self, x: float, y: float, radius: float) -> None:
        super().__init__(x, y, radius)

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, "white", self.position,
                           self.radius, width=LINE_WIDTH)

    def update(self, dt: float) -> None:
        self.position += self.velocity * dt

    def split(self) -> None:
        self.kill()

        if self.radius < ASTEROID_MIN_RADIUS:
            return

        log_event("asteroid_split")

        split_angle = random.uniform(20, 50)

        split_velocity_a = self.velocity.rotate(split_angle)
        split_velocity_b = self.velocity.rotate(-split_angle)
        split_radius = self.radius - ASTEROID_MIN_RADIUS

        split_asteroid_a = Asteroid(
            self.position.x, self.position.y, split_radius)
        split_asteroid_b = Asteroid(
            self.position.x, self.position.y, split_radius)
        split_asteroid_a.velocity = split_velocity_a
        split_asteroid_b.velocity = split_velocity_b
