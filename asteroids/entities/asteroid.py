"""Asteroid sprite with a stable, rotating, irregular outline."""

import random

import pygame

from ..constants import (
    ASTEROID_LUMPINESS,
    ASTEROID_MIN_RADIUS,
    ASTEROID_VERTEX_COUNT_MAX,
    ASTEROID_VERTEX_COUNT_MIN,
    LINE_WIDTH,
    WHITE,
)
from .circle_shape import CircleShape


class Asteroid(CircleShape):
    def __init__(
        self,
        x,
        y,
        radius,
        *,
        world=None,
    ):
        super().__init__(x, y, radius)
        self.world = world
        self.rotation = random.uniform(0.0, 360.0)
        self.rotation_speed = random.choice((-1.0, 1.0)) * random.uniform(8.0, 28.0)
        self.vertices = self._make_vertices()
        self.collision_radius = max(vertex.length() for vertex in self.vertices)
        self._destroyed = False
        if self.world is not None:
            self.world.add_asteroid(self)

    def _make_vertices(self):
        """Generate local-space vertices once so the outline never jitters."""
        vertex_count = random.randint(
            ASTEROID_VERTEX_COUNT_MIN, ASTEROID_VERTEX_COUNT_MAX
        )
        angle_step = 360.0 / vertex_count
        angle_jitter = angle_step * 0.12
        vertices = []

        for index in range(vertex_count):
            angle = index * angle_step + random.uniform(-angle_jitter, angle_jitter)
            vertex_radius = self.radius * random.uniform(
                1.0 - ASTEROID_LUMPINESS, 1.0 + ASTEROID_LUMPINESS
            )
            vertices.append(pygame.Vector2(vertex_radius, 0.0).rotate(angle))

        return vertices

    def draw(self, screen):
        rotated_vertices = [vertex.rotate(self.rotation) for vertex in self.vertices]
        margin = self.radius * (1.0 + ASTEROID_LUMPINESS)

        for center in self.screen_positions(margin):
            points = [center + vertex for vertex in rotated_vertices]
            pygame.draw.polygon(screen, WHITE, points, width=LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt
        self.rotation = (self.rotation + self.rotation_speed * dt) % 360.0
        self.wrap()

    def split(self):
        """Destroy this asteroid once and return any spawned child asteroids."""
        if self._destroyed:
            return []

        self._destroyed = True
        self.kill()

        if self.radius <= ASTEROID_MIN_RADIUS:
            return []

        split_angle = random.uniform(20.0, 50.0)
        split_radius = self.radius - ASTEROID_MIN_RADIUS
        children = []

        for angle in (split_angle, -split_angle):
            child = Asteroid(
                self.position.x,
                self.position.y,
                split_radius,
                world=self.world,
            )
            child.velocity = self.velocity.rotate(angle)
            children.append(child)

        return children
