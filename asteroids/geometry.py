"""Toroidal screen and collision geometry helpers."""

import pygame

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH

_GEOMETRY_EPSILON = 1e-9


def wrap_position(
    position,
    width=SCREEN_WIDTH,
    height=SCREEN_HEIGHT,
):
    """Return ``position`` wrapped into the visible playfield."""
    return pygame.Vector2(position.x % width, position.y % height)


def wrapped_delta(
    start,
    end,
    width=SCREEN_WIDTH,
    height=SCREEN_HEIGHT,
):
    """Return the shortest vector from start to end on a toroidal field."""
    dx = (end.x - start.x + width / 2) % width - width / 2
    dy = (end.y - start.y + height / 2) % height - height / 2
    return pygame.Vector2(dx, dy)


def _point_in_triangle(point, triangle):
    a, b, c = triangle

    if abs((b - a).cross(c - a)) <= _GEOMETRY_EPSILON:
        return False

    def cross(p1, p2, p3):
        return (p2 - p1).cross(p3 - p1)

    d1 = cross(a, b, point)
    d2 = cross(b, c, point)
    d3 = cross(c, a, point)
    has_negative = d1 < 0 or d2 < 0 or d3 < 0
    has_positive = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_negative and has_positive)


def _distance_to_segment_squared(point, start, end):
    segment = end - start
    length_squared = segment.length_squared()
    if length_squared == 0:
        return (point - start).length_squared()
    t = max(0.0, min(1.0, (point - start).dot(segment) / length_squared))
    closest = start + segment * t
    return (point - closest).length_squared()


def circle_intersects_triangle(
    circle_center,
    circle_radius,
    triangle,
):
    """Test a filled circle against a filled triangle."""
    if _point_in_triangle(circle_center, triangle):
        return True

    radius_squared = circle_radius * circle_radius
    edges = (
        (triangle[0], triangle[1]),
        (triangle[1], triangle[2]),
        (triangle[2], triangle[0]),
    )
    return any(
        _distance_to_segment_squared(circle_center, start, end) <= radius_squared
        for start, end in edges
    )
