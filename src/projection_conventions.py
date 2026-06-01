"""
Projection conventions — the free choices a projection makes when it
realizes the coordinate-free ``NaturalLayout`` into a concrete drawing.

The architecture (see ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md``
§3.1–§3.2 and the project memory
``project-render-as-projection-own-dimensionality``) splits layout into:

    EGI ──▶ NaturalLayout  (coordinate-free; what any faithful drawing
                            must realize: containment tree, per-ligature
                            crossing-sequence, incidence, ports)
        ──project──▶ LayoutDTO  (2-D geometry today)  ──▶ render

A **convention** is a free parameter of that projection step: something
the NaturalLayout does *not* determine, that a particular projection
must nonetheless choose. The §3.3 "convention compliance" row of the
correspondence contract is exactly the requirement that the conventions
*in force* are obeyed — but until now those choices lived as scattered
magic numbers and unstated heuristics in ``elk_layout_engine`` and the
SVG renderer. This object gives them a single enumerated home so
"which conventions are in force" is a question with a concrete answer.

Two kinds of field live here, and the distinction is deliberately
explicit:

- **Honored knobs** — wired through the projection today; changing them
  changes the drawing. (``detour_pad``, ``visibility_pad``.)
- **Descriptive** — they name the *current fixed behavior* of a choice
  that is not yet a knob. They make the enumeration complete and honest;
  turning one into a real parameter is future work, and the field is the
  placeholder that says so. (Everything else below.)

Defaults reproduce the behavior in force as of 2026-06-01, so
``Conventions()`` is a faithful description of the current projection.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Conventions:
    """The projection's free parameters. ``Conventions()`` = current behavior.

    See the module docstring for the natural-layout/projection split and
    the honored-knob vs. descriptive distinction.
    """

    # --- Honored knobs (wired through ELKLayoutEngine routing) -------------

    detour_pad: float = 12.0
    """Standoff (px) for the L-shaped detour around the combined bounding
    box of crossed obstacle cuts (``_route_avoiding_cuts``). How far a
    rerouted ligature stands clear of an unauthorized cut it must avoid."""

    visibility_pad: float = 8.0
    """Standoff (px) for the padded obstacle corners in the
    visibility-graph fallback router (``_route_via_visibility_graph``)."""

    # --- Descriptive: current fixed behavior, not yet a knob ---------------

    cut_shape: str = "axis_aligned_rectangle"
    """How a cut's region is drawn. The natural layer only knows
    *containment*; this is the 2-D realization of it. A 3-D projection
    would replace this (closed surface) without touching NaturalLayout."""

    hook_placement: str = "ray_to_bbox_intersection"
    """How a predicate's ligature hook is placed: the intersection of the
    ray from the predicate centre to its target with the predicate's
    bounding box (``_predicate_hook_point``)."""

    ligature_routing: str = "straight_then_L_then_visibility_graph"
    """The routing escalation: straight line if it crosses no unauthorized
    cut, else the shortest valid L-detour, else visibility-graph shortest
    path. Best-effort — correctness is the attestation's job (crossing
    equality), not the router's."""

    ligature_crossing_marks: str = "none"
    """Disambiguation of two ligatures crossing in the 2-D projection.
    Currently unmarked (spec R6): the visual ambiguity is accepted and
    the W-partition is recovered from the structural channel, not pixels.
    Bridge marks (Peirce's own device) would be an alternative value."""

    sibling_cut_ordering: str = "elk_emergent"
    """Left/right order of sibling cuts at the same depth — a pure
    projection artifact (siblings have no logical order; spec §5.3).
    Currently whatever ELK emits; not yet pinned to a canonical rule
    (cf. layout invariant L1 on cross-process determinism)."""


DEFAULT_CONVENTIONS = Conventions()
"""The conventions in force by default — current projection behavior."""


__all__ = ["Conventions", "DEFAULT_CONVENTIONS"]
