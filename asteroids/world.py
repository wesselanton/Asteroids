"""Sprite groups owned by one game session."""

import pygame


class SpriteWorld:
    """Keep each kind of game object in the groups that use it."""

    def __init__(self):
        self.all_sprites = pygame.sprite.Group()
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

    def register(self, sprite, *roles):
        """Own ``sprite`` and add it to each gameplay role group."""
        self.all_sprites.add(sprite)
        for group in roles:
            group.add(sprite)

    def add_player(self, player):
        self.register(player, self.updatable, self.drawable)

    def add_asteroid(self, asteroid):
        self.register(
            asteroid,
            self.updatable,
            self.drawable,
            self.asteroids,
        )

    def add_field(self, field):
        self.register(field, self.updatable)

    def add_shot(self, shot):
        self.register(shot, self.updatable, self.drawable, self.shots)

    def add_bomb(self, bomb):
        self.register(bomb, self.updatable, self.drawable, self.bombs)

    def add_powerup(self, powerup):
        self.register(
            powerup,
            self.updatable,
            self.drawable,
            self.powerups,
        )

    def add_explosion(self, explosion):
        self.register(
            explosion,
            self.updatable,
            self.drawable,
            self.explosions,
        )

    def clear(self):
        """Remove every game object from all of its groups."""
        for sprite in self.all_sprites.sprites():
            sprite.kill()
