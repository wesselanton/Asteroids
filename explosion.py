"""Short-lived fragment bursts used for asteroid and bomb explosions."""

import random

import pygame

from circleshape import CircleShape
from constants import (
    ASTEROID_MAX_RADIUS,
    EXPLOSION_LIFETIME_SECONDS,
    EXPLOSION_PARTICLES_PER_RADIUS,
    WHITE,
)


class _Fragment:
    def __init__(self, offset, velocity, size):
        self.offset = offset
        self.velocity = velocity
        self.size = size


class Explosion(CircleShape):
    """A self-cleaning burst of small fragments centered on an impact."""

    def __init__(
        self,
        x,
        y,
        radius,
        *,
        color=WHITE,
        lifetime=EXPLOSION_LIFETIME_SECONDS,
        world=None,
    ):
        super().__init__(x, y, radius)
        self.color = pygame.Color(color)
        self.lifetime = max(0.0, float(lifetime))
        self.age = 0.0
        self.wrap()

        particle_count = min(
            42,
            max(6, round(radius * EXPLOSION_PARTICLES_PER_RADIUS)),
        )
        travel_distance = min(160.0, max(35.0, radius * 1.1))
        safe_lifetime = max(self.lifetime, 0.001)
        self._extent = max(radius, travel_distance)
        self._draw_ring = radius > ASTEROID_MAX_RADIUS
        self._fragments = []

        angle_step = 360.0 / particle_count
        for index in range(particle_count):
            angle = index * angle_step + random.uniform(
                -angle_step * 0.35, angle_step * 0.35
            )
            direction = pygame.Vector2(1, 0).rotate(angle)
            speed = travel_distance / safe_lifetime * random.uniform(0.65, 1.2)
            self._fragments.append(
                _Fragment(
                    offset=direction * random.uniform(0.0, min(5.0, radius * 0.12)),
                    velocity=direction * speed,
                    size=max(
                        1.25,
                        min(4.0, radius * random.uniform(0.025, 0.07)),
                    ),
                )
            )
        if world is not None:
            world.add_explosion(self)

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return

        damping = max(0.0, 1.0 - 2.2 * dt)
        for fragment in self._fragments:
            fragment.offset += fragment.velocity * dt
            fragment.velocity *= damping

    def draw(self, screen):
        progress = 1.0 if self.lifetime <= 0.0 else self.age / self.lifetime
        remaining = max(0.0, 1.0 - progress)
        brightness = remaining**1.25
        color = (
            int(self.color.r * brightness),
            int(self.color.g * brightness),
            int(self.color.b * brightness),
        )
        centers = self.screen_positions(self._extent)

        for center in centers:
            for fragment in self._fragments:
                tip = center + fragment.offset
                trail_direction = (
                    fragment.velocity.normalize()
                    if fragment.velocity.length_squared() > 0.0
                    else pygame.Vector2()
                )
                trail_length = fragment.size * (2.0 + remaining * 2.0)
                tail = tip - trail_direction * trail_length
                width = max(1, round(fragment.size * remaining))
                pygame.draw.line(screen, color, tail, tip, width=width)

        if self._draw_ring:
            ring_radius = max(1, round(self.radius * (1.0 - remaining * remaining)))
            ring_width = max(1, round(3.0 * remaining))
            for center in centers:
                pygame.draw.circle(screen, color, center, ring_radius, width=ring_width)
