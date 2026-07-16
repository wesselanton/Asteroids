"""Weapon names and firing settings."""

from .constants import (
    CYAN,
    SHOT_LIFETIME_SECONDS,
    SHOT_RADIUS,
    VIOLET,
    WHITE,
)

WEAPON_BLASTER = "Blaster"
WEAPON_SPREAD = "Spread"
WEAPON_RAPID = "Rapid"


class WeaponSpec:
    def __init__(self, angles, speed, cooldown, radius, color, lifetime):
        self.angles = angles
        self.speed = speed
        self.cooldown = cooldown
        self.radius = radius
        self.color = color
        self.lifetime = lifetime


WEAPON_SPECS = {
    WEAPON_BLASTER: WeaponSpec(
        angles=(0.0,),
        speed=560,
        cooldown=0.28,
        radius=SHOT_RADIUS,
        color=WHITE,
        lifetime=SHOT_LIFETIME_SECONDS,
    ),
    WEAPON_SPREAD: WeaponSpec(
        angles=(-13.0, 0.0, 13.0),
        speed=500,
        cooldown=0.48,
        radius=SHOT_RADIUS,
        color=VIOLET,
        lifetime=1.05,
    ),
    WEAPON_RAPID: WeaponSpec(
        angles=(0.0,),
        speed=680,
        cooldown=0.11,
        radius=2.5,
        color=CYAN,
        lifetime=0.72,
    ),
}
