"""
Tests for projection conventions.

A ``Conventions`` object enumerates the free parameters of the
projection from the coordinate-free ``NaturalLayout`` into a concrete
2-D drawing. Two properties matter:

1. ``Conventions()`` faithfully describes current behavior — the
   defaults are the values in force, so constructing the engine with
   defaults changes nothing.
2. The **honored knobs** are actually wired: changing ``detour_pad``
   demonstrably changes a routed ligature's standoff. (The descriptive
   fields are documentation of fixed behavior and are not asserted to be
   knobs — see the module docstring.)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elk_layout_engine import ELKLayoutEngine
from layout_dto import BoundingBox, Point
from projection_conventions import Conventions, DEFAULT_CONVENTIONS


# --------------------------------------------------------------------------- #
# Defaults describe current behavior                                          #
# --------------------------------------------------------------------------- #


def test_defaults_match_behavior_in_force():
    c = Conventions()
    assert c.detour_pad == 12.0
    assert c.visibility_pad == 8.0
    assert c.cut_shape == "axis_aligned_rectangle"
    assert c.ligature_crossing_marks == "none"  # spec R6
    assert DEFAULT_CONVENTIONS == c


def test_engine_defaults_to_default_conventions():
    assert ELKLayoutEngine().conventions == DEFAULT_CONVENTIONS
    custom = Conventions(detour_pad=30.0)
    assert ELKLayoutEngine(custom).conventions is custom


# --------------------------------------------------------------------------- #
# The detour_pad knob is genuinely honored                                    #
# --------------------------------------------------------------------------- #


def test_visibility_pad_changes_route_standoff():
    """A larger visibility_pad routes the taut geodesic further from the
    obstacle's corner.

    Unit-tests the routing directly (no ELK dependency): a horizontal segment
    is blocked by a box straddling it; the taut-line router (visibility-graph
    shortest path — no more L-detour) skirts the box at a corner offset by the
    pad. The standoff must track the pad value, confirming visibility_pad is the
    honored routing knob.
    """
    start = Point(0.0, 0.0)
    end = Point(100.0, 0.0)
    box = BoundingBox(min_x=40.0, min_y=-10.0, max_x=60.0, max_y=10.0)

    def max_abs_y(pad):
        path = ELKLayoutEngine._route_avoiding_cuts(
            start, end, [box], visibility_pad=pad
        )
        return max(abs(p.y) for p in path)

    # The taut path skirts the box corner at edge (±10) + pad.
    assert max_abs_y(12.0) == 22.0
    assert max_abs_y(40.0) == 50.0
    # Strictly increasing in the pad — the knob is wired, not cosmetic.
    assert max_abs_y(40.0) > max_abs_y(12.0)


def test_taut_route_is_shorter_than_an_l_detour():
    """The taut router returns a geodesic, not a right-angle detour: a single
    corner skirt (3 points), strictly shorter than the L it replaced (4)."""
    import math
    start = Point(0.0, 0.0)
    end = Point(100.0, 0.0)
    box = BoundingBox(min_x=40.0, min_y=-10.0, max_x=60.0, max_y=10.0)
    path = ELKLayoutEngine._route_avoiding_cuts(start, end, [box], visibility_pad=12.0)

    def plen(p):
        return sum(math.hypot(p[i + 1].x - p[i].x, p[i + 1].y - p[i].y)
                   for i in range(len(p) - 1))
    # The old L-detour would have been [start,(cmin_x,0),(cmin_x,?),end] etc.;
    # the taut path is at most 3 points and shorter than going to both far
    # corners squared off.
    assert len(path) <= 3
    assert plen(path) < plen([start, Point(28.0, -22.0), Point(72.0, -22.0), end])


def test_no_obstacle_route_is_straight_regardless_of_pad():
    """With nothing to avoid, routing is the straight segment for any pad."""
    start, end = Point(0.0, 0.0), Point(50.0, 0.0)
    for pad in (8.0, 12.0, 40.0):
        assert ELKLayoutEngine._route_avoiding_cuts(
            start, end, [], visibility_pad=pad
        ) == (start, end)
