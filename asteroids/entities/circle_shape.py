"""Base class for moving, wrapping game objects."""

import pygame

from ..constants import SCREEN_HEIGHT, SCREEN_WIDTH
from ..geometry import wrap_position, wrapped_delta


class CircleShape(pygame.sprite.Sprite):
    def __init__(self, x, y, radius):
        super().__init__()

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2()
        self.radius = radius
        self.collision_radius = radius

    def draw(self, screen):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def wrap(self):
        self.position = wrap_position(self.position)

    def screen_positions(self, margin=None):
        """Return primary and seam-copy positions for smooth wrapping."""
        margin = self.radius if margin is None else margin
        x_offsets = [0.0]
        y_offsets = [0.0]
        if self.position.x < margin:
            x_offsets.append(float(SCREEN_WIDTH))
        elif self.position.x > SCREEN_WIDTH - margin:
            x_offsets.append(float(-SCREEN_WIDTH))
        if self.position.y < margin:
            y_offsets.append(float(SCREEN_HEIGHT))
        elif self.position.y > SCREEN_HEIGHT - margin:
            y_offsets.append(float(-SCREEN_HEIGHT))

        return [
            self.position + pygame.Vector2(x_offset, y_offset)
            for x_offset in x_offsets
            for y_offset in y_offsets
        ]

    def collides_with(self, other):
        delta = wrapped_delta(self.position, other.position)
        combined_radius = self.collision_radius + other.collision_radius
        return delta.length_squared() <= combined_radius * combined_radius

    def wrapped_distance_to(self, other):
        return wrapped_delta(self.position, other.position).length()
