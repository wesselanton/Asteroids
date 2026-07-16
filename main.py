"""Application entry point and authoritative game-session controller."""

import random
from enum import Enum, auto

import pygame

from asteroidfield import AsteroidField
from constants import (
    ASTEROID_MIN_RADIUS,
    BOMB_BLAST_RADIUS,
    FPS,
    GAME_TITLE,
    ORANGE,
    PLAYER_RESPAWN_SAFE_RADIUS,
    PLAYER_STARTING_LIVES,
    POWERUP_DROP_CHANCE,
    POWERUP_SHIELD,
    POWERUP_SPEED,
    RED,
    SCORE_BY_ASTEROID_KIND,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    VIOLET,
)
from explosion import Explosion
from player import Player
from powerup import PowerUp
from renderer import GameRenderer
from world import SpriteWorld


class DestructionCause(Enum):
    SHOT = auto()
    BOMB = auto()
    IMPACT = auto()


class Game:
    """Own one game session and resolve gameplay interactions exactly once."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen)
        self.world = SpriteWorld()

        self.score = 0
        self.lives = PLAYER_STARTING_LIVES
        self.game_over = False
        self.running = True
        self.new_session()

    def new_session(self):
        """Clear owned sprites and start a fresh score/lives session."""
        self.world.clear()
        self.score = 0
        self.lives = PLAYER_STARTING_LIVES
        self.game_over = False
        self.player = Player(
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            world=self.world,
        )
        self.asteroid_field = AsteroidField(self.world, self.player)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_r and self.game_over:
            self.new_session()
        elif event.key == pygame.K_b and not self.game_over:
            self.player.drop_bomb()

    def update(self, dt):
        dt = min(max(dt, 0.0), 0.05)
        if self.game_over:
            self.world.explosions.update(dt)
            return

        was_active = self.player.active
        self.world.updatable.update(dt)

        if not was_active and self.player.active:
            self._clear_respawn_zone()

        self._resolve_bombs()
        self._resolve_shots()
        self._resolve_powerups()
        self._resolve_player_collisions()

    def _resolve_shots(self):
        # Split children must survive until at least the next collision phase.
        targets = list(self.world.asteroids)
        for shot in list(self.world.shots):
            if not shot.alive():
                continue
            for asteroid in targets:
                if asteroid.alive() and asteroid.collides_with(shot):
                    self.destroy_asteroid(asteroid, DestructionCause.SHOT)
                    shot.kill()
                    break

    def _resolve_bombs(self):
        for bomb in list(self.world.bombs):
            if not bomb.ready_to_detonate:
                continue

            Explosion(
                bomb.position.x,
                bomb.position.y,
                BOMB_BLAST_RADIUS,
                color=VIOLET,
                lifetime=0.65,
                world=self.world,
            )
            for asteroid in list(self.world.asteroids):
                blast_distance = BOMB_BLAST_RADIUS + asteroid.collision_radius
                if bomb.wrapped_distance_to(asteroid) <= blast_distance:
                    self.destroy_asteroid(asteroid, DestructionCause.BOMB)
            bomb.kill()

    def _resolve_powerups(self):
        if not self.player.active:
            return
        for powerup in list(self.world.powerups):
            if self.player.collides_with(powerup):
                self.player.apply_powerup(powerup.kind)
                powerup.kill()

    def _resolve_player_collisions(self):
        if not self.player.active or self.player.invulnerability_timer > 0:
            return

        for asteroid in list(self.world.asteroids):
            if not asteroid.alive() or not self.player.collides_with(asteroid):
                continue

            if self.player.consume_shield():
                self.destroy_asteroid(asteroid, DestructionCause.IMPACT)
                return

            if not self.player.crash():
                return

            self.lives -= 1
            Explosion(
                self.player.position.x,
                self.player.position.y,
                48,
                color=RED,
                lifetime=0.8,
                world=self.world,
            )
            self.destroy_asteroid(asteroid, DestructionCause.IMPACT)

            if self.lives <= 0:
                self.game_over = True
                self.player.respawn_timer = float("inf")
                self.asteroid_field.kill()
            return

    def destroy_asteroid(self, asteroid, cause):
        """Resolve one asteroid destruction and its gameplay effects."""
        if asteroid not in self.world.asteroids:
            return

        position = asteroid.position.copy()
        radius = asteroid.radius
        Explosion(
            position.x,
            position.y,
            radius,
            color=ORANGE,
            world=self.world,
        )

        if cause is DestructionCause.SHOT:
            asteroid.split()
        else:
            asteroid.kill()

        if cause in (DestructionCause.SHOT, DestructionCause.BOMB):
            asteroid_kind = max(
                1,
                min(3, round(radius / ASTEROID_MIN_RADIUS)),
            )
            self.score += SCORE_BY_ASTEROID_KIND[asteroid_kind]

        if cause is DestructionCause.SHOT and random.random() < POWERUP_DROP_CHANCE:
            powerup_kind = random.choice((POWERUP_SHIELD, POWERUP_SPEED))
            PowerUp(
                position.x,
                position.y,
                powerup_kind,
                world=self.world,
            )

    def _clear_respawn_zone(self):
        for asteroid in list(self.world.asteroids):
            safe_distance = PLAYER_RESPAWN_SAFE_RADIUS + asteroid.collision_radius
            if self.player.wrapped_distance_to(asteroid) < safe_distance:
                self.destroy_asteroid(
                    asteroid,
                    DestructionCause.IMPACT,
                )

    def draw(self):
        self.renderer.draw(
            self.world.drawable,
            self.player,
            self.score,
            self.lives,
            self.game_over,
        )

    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            dt = self.clock.tick(FPS) / 1000
            self.update(dt)
            self.draw()

        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
