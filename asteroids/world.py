"""Sprite groups owned by one game session."""

import pygame


class SpriteWorld:
    """Keep each kind of game object in the groups that use it."""

    def __init__(self):
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

    def add_player(self, player):
        self.updatable.add(player)
        self.drawable.add(player)

    def add_asteroid(self, asteroid):
        self.updatable.add(asteroid)
        self.drawable.add(asteroid)
        self.asteroids.add(asteroid)

    def add_field(self, field):
        self.updatable.add(field)

    def add_shot(self, shot):
        self.updatable.add(shot)
        self.drawable.add(shot)
        self.shots.add(shot)

    def add_bomb(self, bomb):
        self.updatable.add(bomb)
        self.drawable.add(bomb)
        self.bombs.add(bomb)

    def add_powerup(self, powerup):
        self.updatable.add(powerup)
        self.drawable.add(powerup)
        self.powerups.add(powerup)

    def add_explosion(self, explosion):
        self.updatable.add(explosion)
        self.drawable.add(explosion)
        self.explosions.add(explosion)

    def clear(self):
        """Remove every game object from all of its groups."""
        for sprite in self.updatable.sprites():
            sprite.kill()
