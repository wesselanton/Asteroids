"""Fuse-driven bombs dropped by the player."""

import math

import pygame

from circleshape import CircleShape
from constants import (
    BOMB_FUSE_SECONDS,
    BOMB_RADIUS,
    ORANGE,
    RED,
    WHITE,
)


class Bomb(CircleShape):
    """A moving bomb that asks the game loop to detonate when its fuse ends."""

    def __init__(
        self,
        x,
        y,
        velocity=None,
        *,
        world=None,
    ):
        super().__init__(x, y, BOMB_RADIUS)
        self.velocity = (
            pygame.Vector2(velocity) if velocity is not None else pygame.Vector2()
        )
        self.fuse_remaining = float(BOMB_FUSE_SECONDS)
        self.age = 0.0
        self.ready_to_detonate = False
        if world is not None:
            world.add_bomb(self)

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap()
        self.age += dt
        self.fuse_remaining = max(0.0, self.fuse_remaining - dt)
        if self.fuse_remaining <= 0:
            self.ready_to_detonate = True

    def draw(self, screen):
        # The pulse accelerates as the fuse runs down, providing readable warning.
        fuse_ratio = self.fuse_remaining / BOMB_FUSE_SECONDS
        pulse_frequency = 4.0 + (1.0 - fuse_ratio) * 9.0
        pulse = (math.sin(self.age * math.tau * pulse_frequency) + 1.0) * 0.5
        outer_radius = round(self.radius + 2 + pulse * 4)
        body_color = RED if fuse_ratio < 0.28 else ORANGE

        for position in self.screen_positions(outer_radius + 2):
            center = (round(position.x), round(position.y))
            pygame.draw.circle(screen, body_color, center, outer_radius, width=1)
            pygame.draw.circle(screen, (30, 20, 28), center, round(self.radius))
            pygame.draw.circle(screen, body_color, center, round(self.radius), width=2)
            pygame.draw.circle(screen, WHITE, center, max(2, round(self.radius * 0.3)))

            spark_start = position + pygame.Vector2(
                self.radius * 0.45, -self.radius * 0.7
            )
            spark_end = spark_start + pygame.Vector2(3 + pulse * 3, -3 - pulse * 2)
            pygame.draw.line(screen, ORANGE, spark_start, spark_end, width=2)
