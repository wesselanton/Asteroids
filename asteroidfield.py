"""Timed, population-capped asteroid spawning at screen seams."""

import random

import pygame

from asteroid import Asteroid
from constants import (
    ASTEROID_KINDS,
    ASTEROID_LUMPINESS,
    ASTEROID_MAX_ACTIVE,
    ASTEROID_MIN_RADIUS,
    ASTEROID_SPAWN_RATE_SECONDS,
    PLAYER_RESPAWN_SAFE_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from geometry import wrapped_delta


class AsteroidField(pygame.sprite.Sprite):
    """Spawn asteroids without exceeding the world's population cap."""

    edges = (
        (
            pygame.Vector2(1, 0),
            lambda y: pygame.Vector2(0, y * SCREEN_HEIGHT),
        ),
        (
            pygame.Vector2(-1, 0),
            lambda y: pygame.Vector2(SCREEN_WIDTH, y * SCREEN_HEIGHT),
        ),
        (
            pygame.Vector2(0, 1),
            lambda x: pygame.Vector2(x * SCREEN_WIDTH, 0),
        ),
        (
            pygame.Vector2(0, -1),
            lambda x: pygame.Vector2(x * SCREEN_WIDTH, SCREEN_HEIGHT),
        ),
    )

    def __init__(
        self,
        world,
        avoid_target=None,
    ):
        super().__init__()
        self.world = world
        self.avoid_target = avoid_target
        self.spawn_timer = 0.0
        self.world.add_field(self)

    def _spawn(
        self,
        radius,
        position,
        velocity,
    ):
        asteroid = Asteroid(
            position.x,
            position.y,
            radius,
            world=self.world,
        )
        asteroid.velocity = velocity

    def update(self, dt):
        self.spawn_timer = min(
            self.spawn_timer + dt,
            ASTEROID_SPAWN_RATE_SECONDS,
        )
        if self.spawn_timer < ASTEROID_SPAWN_RATE_SECONDS:
            return
        if len(self.world.asteroids) >= ASTEROID_MAX_ACTIVE:
            return

        # Try several seams so crossing an edge never causes an unavoidable hit.
        for _ in range(8):
            edge = random.choice(self.edges)
            speed = random.randint(40, 100)
            velocity = (edge[0] * speed).rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0.0, 1.0))
            asteroid_kind = random.randint(1, ASTEROID_KINDS)
            radius = ASTEROID_MIN_RADIUS * asteroid_kind

            if self.avoid_target is not None:
                separation = wrapped_delta(
                    self.avoid_target.position,
                    position,
                ).length()
                outer_radius = radius * (1.0 + ASTEROID_LUMPINESS)
                if separation < PLAYER_RESPAWN_SAFE_RADIUS + outer_radius:
                    continue

            self._spawn(radius, position, velocity)
            self.spawn_timer = 0.0
            return
