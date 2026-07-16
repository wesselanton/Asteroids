"""Collectible shield and speed power-ups."""

import math
import random

import pygame

from ..constants import (
    CYAN,
    ORANGE,
    POWERUP_LIFETIME_SECONDS,
    POWERUP_RADIUS,
    POWERUP_SHIELD,
    POWERUP_SPEED,
    WHITE,
)
from .circle_shape import CircleShape


class PowerUp(CircleShape):
    """A slowly drifting, time-limited collectible."""

    def __init__(
        self,
        x,
        y,
        kind,
        *,
        world=None,
    ):
        if kind not in (POWERUP_SHIELD, POWERUP_SPEED):
            raise ValueError(f"Unknown power-up kind: {kind!r}")

        super().__init__(x, y, POWERUP_RADIUS)
        self.kind = kind
        self.ttl = float(POWERUP_LIFETIME_SECONDS)
        self.age = 0.0
        self.velocity = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        self.velocity *= random.uniform(18.0, 34.0)
        if world is not None:
            world.add_powerup(self)

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap()
        self.age += dt
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()

    def draw(self, screen):
        # Flash during the final two seconds without disappearing for long stretches.
        if self.ttl < 2.0 and int(self.ttl * 8) % 2 == 0:
            return

        pulse = (math.sin(self.age * math.tau * 1.8) + 1.0) * 0.5
        outer_radius = round(self.radius + 2 + pulse * 2)
        color = CYAN if self.kind == POWERUP_SHIELD else ORANGE

        for position in self.screen_positions(outer_radius + 2):
            center = (round(position.x), round(position.y))
            pygame.draw.circle(screen, color, center, outer_radius, width=1)
            pygame.draw.circle(screen, (7, 18, 35), center, round(self.radius))
            pygame.draw.circle(screen, color, center, round(self.radius), width=2)

            if self.kind == POWERUP_SHIELD:
                self._draw_shield(screen, position, color)
            else:
                self._draw_speed(screen, position, color)

    def _draw_shield(
        self,
        surface,
        position,
        color,
    ):
        scale = self.radius * 0.62
        points = [
            position + pygame.Vector2(0, -scale),
            position + pygame.Vector2(scale * 0.72, -scale * 0.58),
            position + pygame.Vector2(scale * 0.58, scale * 0.22),
            position + pygame.Vector2(0, scale),
            position + pygame.Vector2(-scale * 0.58, scale * 0.22),
            position + pygame.Vector2(-scale * 0.72, -scale * 0.58),
        ]
        pygame.draw.polygon(surface, color, points, width=2)
        pygame.draw.line(
            surface,
            WHITE,
            position + pygame.Vector2(0, -scale * 0.64),
            position + pygame.Vector2(0, scale * 0.5),
            width=1,
        )

    def _draw_speed(
        self,
        surface,
        position,
        color,
    ):
        scale = self.radius * 0.58
        for x_offset in (-scale * 0.36, scale * 0.3):
            points = [
                position + pygame.Vector2(x_offset - scale * 0.42, -scale),
                position + pygame.Vector2(x_offset + scale * 0.42, 0),
                position + pygame.Vector2(x_offset - scale * 0.42, scale),
            ]
            pygame.draw.lines(surface, color, False, points, width=2)
