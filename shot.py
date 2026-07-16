"""Player projectiles with finite lifetimes and toroidal wrapping."""

import pygame

from circleshape import CircleShape
from constants import (
    SHOT_LIFETIME_SECONDS,
    SHOT_RADIUS,
    WHITE,
)


class Shot(CircleShape):
    """A configurable projectile fired along a direction."""

    def __init__(
        self,
        x,
        y,
        direction,
        speed,
        *,
        radius=SHOT_RADIUS,
        color=WHITE,
        inherited_velocity=None,
        lifetime=SHOT_LIFETIME_SECONDS,
        world=None,
    ):
        super().__init__(x, y, radius)
        heading = pygame.Vector2(direction)
        if heading.length_squared() > 0:
            heading = heading.normalize()

        inherited = (
            pygame.Vector2(inherited_velocity)
            if inherited_velocity is not None
            else pygame.Vector2()
        )
        self.velocity = heading * speed + inherited
        self.color = pygame.Color(color)
        self.ttl = max(0.0, float(lifetime))
        if world is not None:
            world.add_shot(self)

    def draw(self, screen):
        trail_direction = pygame.Vector2()
        if self.velocity.length_squared() > 0:
            trail_direction = self.velocity.normalize()

        for position in self.screen_positions(self.radius + 8):
            center = (round(position.x), round(position.y))
            trail_end = position - trail_direction * max(6.0, self.radius * 2.5)
            pygame.draw.line(
                screen,
                self.color,
                center,
                (round(trail_end.x), round(trail_end.y)),
                max(1, round(self.radius / 2)),
            )
            pygame.draw.circle(screen, self.color, center, round(self.radius))
            if self.radius >= 3:
                pygame.draw.circle(
                    screen, WHITE, center, max(1, round(self.radius * 0.42))
                )

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap()
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
