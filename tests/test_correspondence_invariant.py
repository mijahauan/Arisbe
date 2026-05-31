"""
Linear-graphical correspondence invariant — property tests.

See docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md for the contract these tests
enforce. This file currently attacks four of the six test shapes listed in
§7 of the spec:

  - Totality:        every EGI element (V, E, Cut) is represented in the
                     rendered LayoutDTO.
  - Injectivity:     every LayoutDTO entry traces back to a known EGI element
                     (or to the sheet).
  - Containment:     cut bounds nest according to the EGI's `area` mapping.
  - Incidence:       LigaturePaths realise `ν` — for each predicate, the set
                     of ligature paths emitted matches the predicate's arity
                     and the multiset of vertices `ν` names.

Identity fidelity (W-partition realised by ligature paths *passing through
the right areas*) is the next layer — checking that a ligature's point
sequence actually traverses the areas given by `egi.area` for the connected
vertices.  That requires reasoning about point-in-bounds along the path and
is left for a follow-up.  Argument-order fidelity (which hook is arg 1 vs
arg 2) is also deferred: the current LigaturePath does not carry a port
index, so order is a renderer-level concern not visible at this layer.
"""

import sys
from pathlib import Path

import pytest

# Match the repo's test convention: prepend src/ so bare imports work.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style
from tomos_service import TomosService


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    return TomosService(TOMOS_ROOT)


@pytest.fixture(scope="module")
def engine():
    return ELKLayoutEngine()


@pytest.fixture(scope="module")
def style():
    return load_default_style()


def _uod_ids():
    """Enumerate UoD IDs from the tomos corpus at collection time."""
    service = TomosService(TOMOS_ROOT)
    return [u["uod_id"] for u in service.list_uods()]


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_render_round_trip_totality_and_injectivity(uod_id, tomos, engine, style):
    """Every EGI element appears in the LayoutDTO and vice versa.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Totality, Injectivity).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    egi_v_ids = {v.id for v in egi.V}
    egi_e_ids = {e.id for e in egi.E}
    egi_cut_ids = {c.id for c in egi.Cut}

    # Totality: every EGI element has structural data in the DTO.
    missing_v = egi_v_ids - dto.vertex_positions.keys()
    missing_e = egi_e_ids - dto.predicate_positions.keys()
    missing_cuts = egi_cut_ids - dto.cut_bounds.keys()
    assert not missing_v, (
        f"[{uod_id}] vertices in EGI missing from LayoutDTO.vertex_positions: "
        f"{sorted(missing_v)}"
    )
    assert not missing_e, (
        f"[{uod_id}] predicates in EGI missing from LayoutDTO.predicate_positions: "
        f"{sorted(missing_e)}"
    )
    assert not missing_cuts, (
        f"[{uod_id}] cuts in EGI missing from LayoutDTO.cut_bounds: "
        f"{sorted(missing_cuts)}"
    )

    # Injectivity: every DTO entry traces back to an EGI element (or the sheet).
    extra_v = dto.vertex_positions.keys() - egi_v_ids
    extra_e = dto.predicate_positions.keys() - egi_e_ids
    extra_cuts = dto.cut_bounds.keys() - egi_cut_ids - {egi.sheet}
    assert not extra_v, (
        f"[{uod_id}] LayoutDTO.vertex_positions contains unknown IDs: "
        f"{sorted(extra_v)}"
    )
    assert not extra_e, (
        f"[{uod_id}] LayoutDTO.predicate_positions contains unknown IDs: "
        f"{sorted(extra_e)}"
    )
    assert not extra_cuts, (
        f"[{uod_id}] LayoutDTO.cut_bounds contains IDs that are neither "
        f"cuts nor the sheet: {sorted(extra_cuts)}"
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_render_round_trip_containment_fidelity(uod_id, tomos, engine, style):
    """Cut bounds geometrically contain every element the EGI says lives inside.

    For each cut C, for each element X in egi.area[C]: the LayoutDTO must
    place X inside the bounds of C — a vertex/predicate position must lie
    within the bounds, a sub-cut's bounds must lie inside the parent's bounds.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Containment fidelity),
    §5.1 (Cut containment under regeneration), §5.5 (the structural basis
    of regime 3: objects are undefined outside their area).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    failures = []
    for cut in egi.Cut:
        cut_id = cut.id
        bounds = dto.cut_bounds.get(cut_id)
        if bounds is None:
            # Surfaced by the totality test; skip here to avoid duplicate noise.
            continue
        for elem_id in egi.area.get(cut_id, frozenset()):
            pos = dto.vertex_positions.get(elem_id) or dto.predicate_positions.get(elem_id)
            if pos is not None:
                inside = (
                    bounds.min_x <= pos.x <= bounds.max_x
                    and bounds.min_y <= pos.y <= bounds.max_y
                )
                if not inside:
                    failures.append(
                        f"  element {elem_id} (pos=({pos.x:.1f},{pos.y:.1f})) "
                        f"is in egi.area[{cut_id}] but lies outside cut bounds "
                        f"x∈[{bounds.min_x:.1f},{bounds.max_x:.1f}] "
                        f"y∈[{bounds.min_y:.1f},{bounds.max_y:.1f}]"
                    )
                continue
            child_bounds = dto.cut_bounds.get(elem_id)
            if child_bounds is None:
                continue
            contained = (
                bounds.min_x <= child_bounds.min_x
                and bounds.max_x >= child_bounds.max_x
                and bounds.min_y <= child_bounds.min_y
                and bounds.max_y >= child_bounds.max_y
            )
            if not contained:
                failures.append(
                    f"  sub-cut {elem_id} is in egi.area[{cut_id}] but its bounds "
                    f"x∈[{child_bounds.min_x:.1f},{child_bounds.max_x:.1f}] "
                    f"y∈[{child_bounds.min_y:.1f},{child_bounds.max_y:.1f}] "
                    f"are not fully inside parent bounds "
                    f"x∈[{bounds.min_x:.1f},{bounds.max_x:.1f}] "
                    f"y∈[{bounds.min_y:.1f},{bounds.max_y:.1f}]"
                )

    assert not failures, (
        f"[{uod_id}] containment fidelity violated:\n" + "\n".join(failures)
    )


@pytest.mark.parametrize("uod_id", _uod_ids())
def test_render_round_trip_incidence_fidelity(uod_id, tomos, engine, style):
    """LigaturePath set matches `ν` per predicate (count + vertex multiset).

    For each predicate E in egi.E, with `ν(E) = (v_1, ..., v_n)`:

      - The number of LigaturePath entries with `predicate_id == E.id` must
        equal `n` (the arity).
      - The multiset of `vertex_id` values across those LigaturePaths must
        equal the multiset `{v_1, ..., v_n}`.  Multiset, not set: a relation
        may reference the same vertex more than once (e.g. (Eq *x x)).

    Argument *order* (which hook is arg 1 vs arg 2) is not checked here —
    LigaturePath carries no port index, so order is a renderer-internal
    detail not visible at this fidelity layer.

    Spec: docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §3.3 (Incidence fidelity),
    §5.4 (Predicate hook order, deferred).
    """
    uod = tomos.load_uod(uod_id)
    egi = uod.current_egi
    dto = engine.generate_layout(egi, style)

    # Index ligature paths by predicate_id once.
    paths_by_predicate: dict = {}
    for path in dto.ligature_paths:
        paths_by_predicate.setdefault(path.predicate_id, []).append(path)

    failures = []
    for edge in egi.E:
        edge_id = edge.id
        nu_vertices = egi.nu.get(edge_id)
        if nu_vertices is None:
            failures.append(
                f"  predicate {edge_id} has no entry in egi.nu — "
                f"EGI itself is malformed"
            )
            continue
        expected_arity = len(nu_vertices)
        actual_paths = paths_by_predicate.get(edge_id, [])
        actual_arity = len(actual_paths)
        if actual_arity != expected_arity:
            failures.append(
                f"  predicate {edge_id}: arity mismatch — "
                f"ν says {expected_arity} arg(s) {tuple(nu_vertices)}, "
                f"LayoutDTO emits {actual_arity} ligature path(s)"
            )
            continue
        expected_vertices = sorted(nu_vertices)
        actual_vertices = sorted(p.vertex_id for p in actual_paths)
        if expected_vertices != actual_vertices:
            failures.append(
                f"  predicate {edge_id}: vertex multiset mismatch — "
                f"ν names {expected_vertices}, "
                f"LayoutDTO connects {actual_vertices}"
            )

    # Injectivity sweep on ligature paths themselves: every path must reference
    # a predicate that exists in the EGI and a vertex it actually names.
    egi_e_ids = {e.id for e in egi.E}
    egi_v_ids = {v.id for v in egi.V}
    for path in dto.ligature_paths:
        if path.predicate_id not in egi_e_ids:
            failures.append(
                f"  ligature path references unknown predicate "
                f"{path.predicate_id} (vertex={path.vertex_id})"
            )
        if path.vertex_id not in egi_v_ids:
            failures.append(
                f"  ligature path references unknown vertex "
                f"{path.vertex_id} (predicate={path.predicate_id})"
            )

    assert not failures, (
        f"[{uod_id}] incidence fidelity violated:\n" + "\n".join(failures)
    )
