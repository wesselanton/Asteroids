"""Player movement, weapons, power-ups, and collision geometry."""

import math

import pygame

from ..constants import (
    BOMB_COOLDOWN_SECONDS,
    BOMB_RADIUS,
    CYAN,
    LINE_WIDTH,
    ORANGE,
    PLAYER_ACCELERATION,
    PLAYER_DRAG,
    PLAYER_INVULNERABILITY_SECONDS,
    PLAYER_MAX_SPEED,
    PLAYER_RADIUS,
    PLAYER_RESPAWN_DELAY_SECONDS,
    PLAYER_REVERSE_ACCELERATION,
    PLAYER_TURN_SPEED,
    POWERUP_SHIELD,
    POWERUP_SHIELD_SECONDS,
    POWERUP_SPEED,
    POWERUP_SPEED_SECONDS,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_HIT_GRACE_SECONDS,
    SHOT_PLAYER_VELOCITY_FACTOR,
    SPEED_POWERUP_MULTIPLIER,
    WHITE,
)
from ..geometry import circle_intersects_triangle, wrapped_delta
from ..weapons import (
    WEAPON_BLASTER,
    WEAPON_RAPID,
    WEAPON_SPECS,
    WEAPON_SPREAD,
)
from .bomb import Bomb
from .circle_shape import CircleShape
from .shot import Shot


class Player(CircleShape):
    """The player ship.

    Movement uses acceleration and velocity instead of direct displacement.  A
    crashed player remains registered while inactive so one stable object can
    carry the respawn transition.
    """

    def __init__(self, x, y, *, world=None):
        super().__init__(x, y, PLAYER_RADIUS)
        self.world = world
        self.rotation = 0.0

        self.weapon_name = WEAPON_BLASTER
        self.shot_cooldown_timer = 0.0
        self.bomb_cooldown_timer = 0.0

        self.active = True
        self.respawn_timer = 0.0
        self.invulnerability_timer = 0.0
        self.shield_timer = 0.0
        self.speed_timer = 0.0

        self.thrusting = False
        if self.world is not None:
            self.world.add_player(self)

    @property
    def invulnerable(self):
        return self.active and self.invulnerability_timer > 0.0

    @property
    def shield_active(self):
        return self.active and self.shield_timer > 0.0

    @property
    def speed_boost_active(self):
        return self.active and self.speed_timer > 0.0

    def forward_vector(self):
        return pygame.Vector2(0, 1).rotate(self.rotation)

    def triangle(self, position=None):
        """Return the exact three vertices used for drawing and collision."""
        center = self.position if position is None else pygame.Vector2(position)
        forward = self.forward_vector()
        right = forward.rotate(90) * self.radius / 1.5
        nose = center + forward * self.radius
        rear_right = center - forward * self.radius - right
        rear_left = center - forward * self.radius + right
        return (nose, rear_right, rear_left)

    def draw(self, screen):
        if not self.active:
            return

        # The flame extends farther than the collision radius; using a wider
        # margin ensures it also receives a seam copy.
        for center in self.screen_positions(margin=self.radius * 2.0):
            if self.thrusting:
                self._draw_thrust(screen, center)

            ship_color = CYAN if self.invulnerable else WHITE
            pygame.draw.polygon(
                screen, ship_color, self.triangle(center), width=LINE_WIDTH
            )

            if self.shield_active:
                shield_radius = int(self.radius * 1.55)
                pygame.draw.circle(
                    screen,
                    CYAN,
                    center,
                    shield_radius,
                    width=LINE_WIDTH,
                )

    def _draw_thrust(self, screen, center):
        forward = self.forward_vector()
        right = forward.rotate(90)
        rear = center - forward * self.radius
        flame = [
            rear - right * self.radius * 0.28,
            center - forward * self.radius * 1.9,
            rear + right * self.radius * 0.28,
        ]
        pygame.draw.polygon(screen, ORANGE, flame)
        pygame.draw.line(
            screen,
            RED,
            rear,
            center - forward * self.radius * 1.65,
            width=max(1, LINE_WIDTH),
        )

    def collides_with(self, other):
        """Test another circular object against the ship's toroidal triangle."""
        if not self.active:
            return False
        nearest_center = self.position + wrapped_delta(self.position, other.position)
        return circle_intersects_triangle(
            nearest_center,
            other.collision_radius,
            self.triangle(),
        )

    def rotate(self, dt):
        self.rotation = (self.rotation + PLAYER_TURN_SPEED * dt) % 360.0

    def update(self, dt):
        dt = max(0.0, float(dt))
        self._tick_timers(dt)

        if not self.active:
            self.thrusting = False
            self.respawn_timer = max(0.0, self.respawn_timer - dt)
            if self.respawn_timer <= 0.0:
                self.respawn()
            return

        keys = pygame.key.get_pressed()
        self._select_weapon(keys)

        turn_input = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        if turn_input:
            self.rotate(dt * turn_input)

        forward_pressed = bool(keys[pygame.K_w])
        reverse_pressed = bool(keys[pygame.K_s])
        self.thrusting = forward_pressed and not reverse_pressed

        speed_multiplier = SPEED_POWERUP_MULTIPLIER if self.speed_boost_active else 1.0
        if forward_pressed != reverse_pressed:
            if forward_pressed:
                acceleration = PLAYER_ACCELERATION * speed_multiplier
                direction = 1.0
            else:
                acceleration = PLAYER_REVERSE_ACCELERATION * speed_multiplier
                direction = -1.0
            self.velocity += self.forward_vector() * acceleration * direction * dt

        # Exponential damping is frame-rate independent and preserves inertia.
        self.velocity *= math.exp(-PLAYER_DRAG * dt)
        max_speed = PLAYER_MAX_SPEED * speed_multiplier
        if self.velocity.length_squared() > max_speed * max_speed:
            self.velocity.scale_to_length(max_speed)

        self.position += self.velocity * dt
        self.wrap()

        if keys[pygame.K_SPACE]:
            self.shoot()

    def _tick_timers(self, dt):
        self.shot_cooldown_timer = max(0.0, self.shot_cooldown_timer - dt)
        self.bomb_cooldown_timer = max(0.0, self.bomb_cooldown_timer - dt)
        self.invulnerability_timer = max(0.0, self.invulnerability_timer - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.speed_timer = max(0.0, self.speed_timer - dt)

    def _select_weapon(self, keys):
        if keys[pygame.K_1]:
            self.weapon_name = WEAPON_BLASTER
        elif keys[pygame.K_2]:
            self.weapon_name = WEAPON_SPREAD
        elif keys[pygame.K_3]:
            self.weapon_name = WEAPON_RAPID

    def shoot(self):
        """Fire the selected weapon, returning the sprites that were created."""
        if not self.active or self.shot_cooldown_timer > 0.0:
            return []

        spec = WEAPON_SPECS[self.weapon_name]
        self.shot_cooldown_timer = spec.cooldown
        forward = self.forward_vector()
        muzzle = self.position + forward * (self.radius + 2.0)
        inherited_velocity = self.velocity * SHOT_PLAYER_VELOCITY_FACTOR
        return [
            Shot(
                muzzle.x,
                muzzle.y,
                forward.rotate(angle),
                spec.speed,
                radius=spec.radius,
                color=spec.color,
                inherited_velocity=inherited_velocity,
                lifetime=spec.lifetime,
                world=self.world,
            )
            for angle in spec.angles
        ]

    def drop_bomb(self):
        if not self.active or self.bomb_cooldown_timer > 0.0:
            return None
        self.bomb_cooldown_timer = BOMB_COOLDOWN_SECONDS
        drop_position = self.position - self.forward_vector() * (
            self.radius * 2.0 + BOMB_RADIUS + 5.0
        )
        return Bomb(
            drop_position.x,
            drop_position.y,
            self.velocity * 0.4,
            world=self.world,
        )

    def crash(self):
        """Enter the inactive respawn state; return whether a life was lost."""
        if not self.active or self.invulnerable:
            return False
        self.active = False
        self.thrusting = False
        self.velocity.update(0.0, 0.0)
        self.shield_timer = 0.0
        self.speed_timer = 0.0
        self.respawn_timer = PLAYER_RESPAWN_DELAY_SECONDS
        return True

    def respawn(self):
        self.position.update(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.velocity.update(0.0, 0.0)
        self.rotation = 0.0
        self.active = True
        self.respawn_timer = 0.0
        self.invulnerability_timer = PLAYER_INVULNERABILITY_SECONDS
        self.shot_cooldown_timer = 0.0
        self.bomb_cooldown_timer = 0.0
        self.thrusting = False

    def apply_powerup(self, kind):
        if kind == POWERUP_SHIELD:
            self.shield_timer = POWERUP_SHIELD_SECONDS
        elif kind == POWERUP_SPEED:
            self.speed_timer = POWERUP_SPEED_SECONDS
        else:
            raise ValueError(f"Unknown power-up kind: {kind!r}")

    def consume_shield(self):
        """Consume one active shield and grant time to clear the collision."""
        if not self.shield_active:
            return False
        self.shield_timer = 0.0
        self.invulnerability_timer = max(
            self.invulnerability_timer,
            SHIELD_HIT_GRACE_SECONDS,
        )
        return True
