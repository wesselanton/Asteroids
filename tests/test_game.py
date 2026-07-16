"""Headless regression tests for geometry and gameplay state transitions."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from asteroid import Asteroid
from asteroidfield import AsteroidField
from bomb import Bomb
from circleshape import CircleShape
from constants import (
    ASTEROID_MIN_RADIUS,
    BACKGROUND_IMAGE,
    BOMB_FUSE_SECONDS,
    PLAYER_MAX_SPEED,
    PLAYER_RESPAWN_DELAY_SECONDS,
    PLAYER_RESPAWN_SAFE_RADIUS,
    POWERUP_SHIELD,
    POWERUP_SHIELD_SECONDS,
    POWERUP_SPEED,
    POWERUP_SPEED_SECONDS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_HIT_GRACE_SECONDS,
)
from explosion import Explosion
from geometry import circle_intersects_triangle, wrap_position, wrapped_delta
from main import DestructionCause, Game
from player import Player
from powerup import PowerUp
from renderer import GameRenderer
from shot import Shot
from weapons import WEAPON_RAPID, WEAPON_SPREAD
from world import SpriteWorld


class DummyCircle(CircleShape):
    def draw(self, screen):
        pass

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap()


class FakeKeys:
    def __init__(self, *pressed):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


class GeometryTests(unittest.TestCase):
    def test_wrap_handles_exact_edges_and_large_overshoot(self):
        self.assertEqual(
            wrap_position(pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0)
        )
        self.assertEqual(wrap_position(pygame.Vector2(-2561, 1441)), (1279, 1))

    def test_wrapped_delta_uses_nearest_screen_image(self):
        delta = wrapped_delta(pygame.Vector2(2, 100), pygame.Vector2(1278, 100))
        self.assertEqual(delta, (-4, 0))

    def test_circle_collision_crosses_screen_seam(self):
        left = DummyCircle(3, 100, 3)
        right = DummyCircle(1279, 100, 3)
        self.assertTrue(left.collides_with(right))

    def test_exact_triangle_circle_rejects_old_circle_false_positive(self):
        player = Player(100, 100)
        outside_narrow_side = DummyCircle(115, 100, 1)
        self.assertFalse(player.collides_with(outside_narrow_side))

    def test_triangle_hitbox_includes_tail_corner(self):
        player = Player(100, 100)
        corner = player.triangle()[1]
        asteroid = DummyCircle(corner.x, corner.y, 0.1)
        self.assertTrue(player.collides_with(asteroid))

    def test_triangle_collision_crosses_screen_seam(self):
        player = Player(2, 100)
        asteroid = DummyCircle(1278, 100, 1)
        self.assertTrue(player.collides_with(asteroid))

    def test_triangle_circle_tangency_counts(self):
        triangle = (
            pygame.Vector2(100, 120),
            pygame.Vector2(86.6667, 80),
            pygame.Vector2(113.3333, 80),
        )
        self.assertTrue(
            circle_intersects_triangle(pygame.Vector2(100, 125), 5, triangle)
        )

    def test_degenerate_triangle_uses_its_segments_not_infinite_interior(self):
        triangle = (
            pygame.Vector2(0, 0),
            pygame.Vector2(10, 0),
            pygame.Vector2(20, 0),
        )
        self.assertFalse(
            circle_intersects_triangle(pygame.Vector2(10, 10), 1, triangle)
        )

    def test_seam_copy_positions_cover_a_corner(self):
        sprite = DummyCircle(2, 2, 5)
        self.assertEqual(len(sprite.screen_positions()), 4)


class EntityTests(unittest.TestCase):
    def setUp(self):
        self.world = SpriteWorld()

    def tearDown(self):
        self.world.clear()

    def test_shot_wraps_and_expires_by_lifetime(self):
        shot = Shot(
            1279,
            100,
            pygame.Vector2(1, 0),
            10,
            lifetime=0.5,
            world=self.world,
        )
        shot.update(0.2)
        self.assertAlmostEqual(shot.position.x, 1)
        self.assertTrue(shot.alive())
        shot.update(0.31)
        self.assertFalse(shot.alive())

    def test_smallest_asteroid_does_not_make_zero_radius_children(self):
        asteroid = Asteroid(
            100,
            100,
            ASTEROID_MIN_RADIUS,
            world=self.world,
        )
        self.assertEqual(asteroid.split(), [])
        self.assertEqual(len(self.world.asteroids), 0)

    def test_lumpy_outline_is_stable_between_frames(self):
        asteroid = Asteroid(100, 100, 40, world=self.world)
        original = [vertex.copy() for vertex in asteroid.vertices]
        asteroid.update(0.25)
        self.assertEqual(original, asteroid.vertices)

    def test_lumpy_outline_collision_covers_farthest_tip(self):
        asteroid = Asteroid(100, 100, 40, world=self.world)
        direction = max(
            asteroid.vertices, key=lambda vertex: vertex.length()
        ).normalize()
        tip = asteroid.position + direction * (asteroid.collision_radius + 0.5)
        touching = DummyCircle(
            tip.x,
            tip.y,
            1,
        )
        self.assertTrue(asteroid.collides_with(touching))

    def test_player_collision_uses_lumpy_asteroid_outer_radius(self):
        player = Player(100, 100)
        asteroid = Asteroid(100, 130, 8, world=self.world)
        asteroid.collision_radius = 11
        self.assertTrue(player.collides_with(asteroid))

    def test_spread_weapon_creates_three_distinct_shots(self):
        player = Player(100, 100)
        player.weapon_name = WEAPON_SPREAD
        shots = player.shoot()
        self.assertEqual(len(shots), 3)
        self.assertEqual(
            len({round(shot.velocity.angle_to((0, 1)), 3) for shot in shots}), 3
        )

    def test_powerups_reset_their_timers(self):
        player = Player(100, 100)
        player.shield_timer = 1
        player.speed_timer = 1
        player.apply_powerup(POWERUP_SHIELD)
        player.apply_powerup(POWERUP_SPEED)
        self.assertEqual(player.shield_timer, POWERUP_SHIELD_SECONDS)
        self.assertEqual(player.speed_timer, POWERUP_SPEED_SECONDS)

    def test_forward_input_accelerates_instead_of_teleporting(self):
        player = Player(100, 100)
        with patch("player.pygame.key.get_pressed", return_value=FakeKeys(pygame.K_w)):
            player.update(0.25)
        self.assertGreater(player.velocity.length(), 0)
        self.assertGreater(player.position.y, 100)

    def test_player_keeps_inertia_with_drag_and_a_speed_limit(self):
        player = Player(100, 100)
        with patch("player.pygame.key.get_pressed", return_value=FakeKeys(pygame.K_w)):
            for _ in range(100):
                player.update(0.1)

        thrust_speed = player.velocity.length()
        self.assertLessEqual(thrust_speed, PLAYER_MAX_SPEED)
        previous_position = player.position.copy()

        with patch("player.pygame.key.get_pressed", return_value=FakeKeys()):
            player.update(0.1)

        self.assertLess(player.velocity.length(), thrust_speed)
        self.assertGreater(
            wrapped_delta(previous_position, player.position).length(),
            0,
        )

    def test_speed_boost_increases_acceleration(self):
        normal = Player(100, 100)
        boosted = Player(100, 100)
        boosted.apply_powerup(POWERUP_SPEED)
        with patch("player.pygame.key.get_pressed", return_value=FakeKeys(pygame.K_w)):
            normal.update(0.25)
            boosted.update(0.25)
        self.assertGreater(boosted.velocity.length(), normal.velocity.length())

    def test_rapid_weapon_uses_small_short_lived_shots(self):
        blaster = Player(100, 100)
        rapid = Player(100, 100)
        rapid.weapon_name = WEAPON_RAPID
        blaster.shoot()
        shot = rapid.shoot()[0]
        self.assertLess(shot.radius, 4)
        self.assertLess(shot.ttl, 1.0)
        self.assertLess(rapid.shot_cooldown_timer, blaster.shot_cooldown_timer)
        self.assertEqual(rapid.shoot(), [])

    def test_temporary_sprites_register_and_expire(self):
        powerup = PowerUp(100, 100, POWERUP_SHIELD, world=self.world)
        explosion = Explosion(100, 100, 20, lifetime=0.05, world=self.world)
        powerup.ttl = 0.05

        self.assertIn(powerup, self.world.powerups)
        self.assertIn(explosion, self.world.explosions)
        self.world.updatable.update(0.06)
        self.assertFalse(powerup.alive())
        self.assertFalse(explosion.alive())

    def test_bomb_is_dropped_behind_ship_with_partial_momentum(self):
        player = Player(100, 100)
        player.velocity.update(100, 0)
        bomb = player.drop_bomb()
        self.assertIsNotNone(bomb)
        self.assertLess(bomb.position.y, player.position.y)
        self.assertAlmostEqual(bomb.velocity.x, 40)

    def test_two_worlds_do_not_cross_wire_spawned_sprites(self):
        other_world = SpriteWorld()
        player = Player(100, 100, world=self.world)
        Player(200, 200, world=other_world)

        player.shoot()
        parent = Asteroid(300, 300, 40, world=self.world)
        children = parent.split()

        self.assertEqual(len(self.world.shots), 1)
        self.assertEqual(len(other_world.shots), 0)
        self.assertEqual(len(children), 2)
        self.assertEqual(len(self.world.asteroids), 2)
        self.assertEqual(len(other_world.asteroids), 0)
        other_world.clear()

    def test_every_asteroid_field_spawn_is_on_a_seam(self):
        for _, factory in AsteroidField.edges:
            position = factory(0.37)
            self.assertTrue(
                position.x in (0, SCREEN_WIDTH) or position.y in (0, SCREEN_HEIGHT)
            )


class GameFlowTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.asteroid_field.kill()
        for asteroid in list(self.game.world.asteroids):
            asteroid.kill()

    def tearDown(self):
        self.game.world.clear()

    def test_destroying_asteroid_awards_stage_score_once(self):
        asteroid = Asteroid(100, 100, 60, world=self.game.world)
        self.game.destroy_asteroid(asteroid, DestructionCause.BOMB)
        self.game.destroy_asteroid(asteroid, DestructionCause.BOMB)
        self.assertEqual(self.game.score, 20)
        self.assertEqual(len(self.game.world.explosions), 1)
        explosion = self.game.world.explosions.sprites()[0]
        self.assertEqual(explosion.position, (100, 100))

    def test_shield_absorbs_collision_without_losing_life(self):
        self.game.player.invulnerability_timer = 0
        self.game.player.apply_powerup(POWERUP_SHIELD)
        asteroid = Asteroid(
            self.game.player.position.x,
            self.game.player.position.y,
            20,
            world=self.game.world,
        )
        self.game.update(0.0)
        self.assertEqual(self.game.lives, 3)
        self.assertEqual(self.game.player.shield_timer, 0)
        self.assertAlmostEqual(
            self.game.player.invulnerability_timer,
            SHIELD_HIT_GRACE_SECONDS,
        )
        self.assertFalse(asteroid.alive())

    def test_unshielded_collision_costs_life_then_respawns(self):
        self.game.player.invulnerability_timer = 0
        Asteroid(
            self.game.player.position.x,
            self.game.player.position.y,
            20,
            world=self.game.world,
        )
        self.game.update(0.0)
        self.assertEqual(self.game.lives, 2)
        self.assertFalse(self.game.player.active)

        frame_count = int(PLAYER_RESPAWN_DELAY_SECONDS / 0.05) + 2
        for _ in range(frame_count):
            self.game.update(0.05)
        self.assertTrue(self.game.player.active)
        self.assertGreater(self.game.player.invulnerability_timer, 0)

    def test_bomb_fuse_detonates_without_splitting(self):
        asteroid = Asteroid(200, 200, 60, world=self.game.world)
        Bomb(200, 200, world=self.game.world)
        frame_count = int(BOMB_FUSE_SECONDS / 0.05) + 2
        for _ in range(frame_count):
            self.game.update(0.05)
        self.assertFalse(asteroid.alive())
        self.assertEqual(self.game.score, 20)
        self.assertEqual(len(self.game.world.bombs), 0)

    def test_same_volley_cannot_chain_hit_new_split_children(self):
        Asteroid(200, 200, 40, world=self.game.world)
        Shot(200, 200, pygame.Vector2(0, 1), 0, world=self.game.world)
        Shot(200, 200, pygame.Vector2(0, 1), 0, world=self.game.world)
        self.game.update(0.0)
        self.assertEqual(self.game.score, 50)
        self.assertEqual(len(self.game.world.asteroids), 2)

    def test_bomb_uses_discrete_keydown_input(self):
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)
        self.game.handle_event(event)
        self.assertEqual(len(self.game.world.bombs), 1)

    def test_background_is_loaded_and_scaled_to_screen_size(self):
        source = pygame.Surface((16, 9))
        source.fill((20, 40, 60))
        with patch("renderer.pygame.image.load", return_value=source) as load:
            renderer = GameRenderer(self.game.screen)
        load.assert_called_once()
        self.assertEqual(renderer.background.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assertEqual(renderer.background.get_at((0, 0))[:3], (20, 40, 60))

    def test_shipped_background_asset_is_loadable(self):
        asset_path = Path(__file__).resolve().parents[1] / BACKGROUND_IMAGE
        self.assertTrue(asset_path.is_file())
        image = pygame.image.load(asset_path)
        self.assertGreater(image.get_width(), 0)
        self.assertGreater(image.get_height(), 0)

    def test_background_falls_back_to_a_plain_surface(self):
        with patch("renderer.pygame.image.load", side_effect=pygame.error("missing")):
            renderer = GameRenderer(self.game.screen)
        self.assertEqual(renderer.background.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assertEqual(renderer.background.get_at((0, 0))[:3], (2, 5, 14))

    def test_respawn_cleanup_uses_lumpy_outer_radius(self):
        asteroid = Asteroid(
            self.game.player.position.x + PLAYER_RESPAWN_SAFE_RADIUS + 22,
            self.game.player.position.y,
            20,
            world=self.game.world,
        )
        asteroid.collision_radius = 30
        self.game.player.active = False
        self.game.player.respawn_timer = 0.0
        self.game.update(0.0)
        self.assertFalse(asteroid.alive())

    def test_powerup_collision_applies_effect_and_removes_pickup(self):
        powerup = PowerUp(
            self.game.player.position.x,
            self.game.player.position.y,
            POWERUP_SPEED,
            world=self.game.world,
        )
        self.game.update(0.0)
        self.assertEqual(self.game.player.speed_timer, POWERUP_SPEED_SECONDS)
        self.assertFalse(powerup.alive())

    def test_destruction_causes_have_the_expected_effects(self):
        cases = (
            (DestructionCause.SHOT, 50, 2, 1),
            (DestructionCause.BOMB, 50, 0, 0),
            (DestructionCause.IMPACT, 0, 0, 0),
        )

        for cause, score, asteroids, powerups in cases:
            with self.subTest(cause=cause):
                self.game.new_session()
                self.game.asteroid_field.kill()
                asteroid = Asteroid(100, 100, 40, world=self.game.world)
                with patch("main.random.random", return_value=0.0):
                    self.game.destroy_asteroid(asteroid, cause)
                self.assertEqual(self.game.score, score)
                self.assertEqual(len(self.game.world.asteroids), asteroids)
                self.assertEqual(len(self.game.world.powerups), powerups)

    def test_last_life_game_over_then_restart_clears_world(self):
        self.game.lives = 1
        self.game.player.invulnerability_timer = 0
        Asteroid(
            self.game.player.position.x,
            self.game.player.position.y,
            20,
            world=self.game.world,
        )
        self.game.update(0.0)
        self.assertTrue(self.game.game_over)

        Shot(100, 100, (0, 1), 100, world=self.game.world)
        Bomb(100, 100, world=self.game.world)
        PowerUp(100, 100, POWERUP_SPEED, world=self.game.world)
        old_sprites = self.game.world.updatable.sprites()

        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.lives, 3)
        self.assertEqual(self.game.score, 0)
        self.assertTrue(all(not sprite.alive() for sprite in old_sprites))
        for group in (
            self.game.world.asteroids,
            self.game.world.shots,
            self.game.world.bombs,
            self.game.world.powerups,
            self.game.world.explosions,
        ):
            self.assertEqual(len(group), 0)
        self.assertEqual(len(self.game.world.updatable), 2)


def tearDownModule():
    pygame.quit()


if __name__ == "__main__":
    unittest.main()
