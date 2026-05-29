"""
Tests for ELKLayoutEngine.

Covers:
- _egi_to_elk_graph: structural correctness of the ELK JSON for various EGI inputs
- generate_layout: full round-trip returning a complete LayoutDTO
- Backward compatibility: LayoutDTO fields match what the D3 engine produced
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style
from layout_dto import LayoutDTO, Point, BoundingBox, LigaturePath


@pytest.fixture(scope="module")
def style():
    return load_default_style()


@pytest.fixture(scope="module")
def engine():
    return ELKLayoutEngine()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _all_node_ids(node: dict) -> set:
    """Collect all node ids in an ELK graph recursively."""
    ids = {node["id"]}
    for child in node.get("children", []):
        ids |= _all_node_ids(child)
    return ids


def _all_edge_ids(node: dict) -> list:
    """Collect all edge dicts in an ELK graph recursively."""
    edges = list(node.get("edges", []))
    for child in node.get("children", []):
        edges.extend(_all_edge_ids(child))
    return edges


# ---------------------------------------------------------------------------
# Phase 2: _egi_to_elk_graph structural tests
# ---------------------------------------------------------------------------

class TestEgiToElkGraph:
    def test_empty_graph(self, engine, style):
        """Empty graph (just sheet) produces a root node with no children."""
        from egi_core_dau import RelationalGraphWithCuts
        from frozendict import frozendict
        egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="sheet",
            Cut=frozenset(),
            area=frozendict({"sheet": frozenset()}),
            rel=frozendict(),
        )
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        assert g["id"] == "sheet"
        assert g["children"] == []
        assert g["edges"] == []

    def test_single_predicate(self, engine, style):
        """Single predicate (Human *x) → one vertex node, one predicate node, one ELK edge."""
        egi = parse_egif("(Human *x)")
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        node_ids = _all_node_ids(g)
        assert len(egi.V) == 1, "should have 1 vertex"
        assert len(egi.E) == 1, "should have 1 predicate"
        # Both the vertex and predicate should appear as nodes
        for v in egi.V:
            assert v.id in node_ids
        for e in egi.E:
            assert e.id in node_ids
        # One ELK edge for the ligature
        edges = _all_edge_ids(g)
        assert len(edges) == 1

    def test_predicate_has_ports(self, engine, style):
        """Predicate node must have exactly arity-many ports."""
        egi = parse_egif("(On *x *y)")
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        # find the predicate node
        e_id = next(iter(egi.E)).id
        def find_node(node, target_id):
            if node["id"] == target_id:
                return node
            for c in node.get("children", []):
                found = find_node(c, target_id)
                if found:
                    return found
            return None
        pred_node = find_node(g, e_id)
        assert pred_node is not None
        arity = len(egi.nu[e_id])
        assert len(pred_node.get("ports", [])) == arity

    def test_nested_cuts(self, engine, style):
        """Nested cuts ~[ (Cat *x) ~[ (Animal x) ] ] → 2 group nodes, 2 predicates, 2 edges."""
        egi = parse_egif("~[ (Cat *x) ~[ (Animal x) ] ]")
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        node_ids = _all_node_ids(g)
        # Both cuts should appear as group nodes
        for c in egi.Cut:
            assert c.id in node_ids
        # Both predicates should appear
        for e in egi.E:
            assert e.id in node_ids
        # One vertex (shared *x / x)
        assert len(egi.V) == 1
        edges = _all_edge_ids(g)
        assert len(edges) == 2

    def test_cross_boundary_ligature_edges_at_root(self, engine, style):
        """All ELK edges are placed at root so cross-boundary routing is handled by ELK."""
        # ~[ (P *x) ] — vertex in cut, predicate could be outside depending on parse
        # Use a known cross-boundary: vertex defined in outer area, predicate in inner cut
        egi = parse_egif("*x ~[ (Mortal x) ]")
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        # All ligature edges must be at root level (not nested inside children)
        root_edge_count = len(g.get("edges", []))
        nested_edge_count = sum(
            len(_all_edge_ids(child)) for child in g.get("children", [])
        )
        # We expect all edges at root (the engine puts them there explicitly)
        assert root_edge_count > 0
        assert nested_edge_count == 0

    def test_constant_vertex_has_label(self, engine, style):
        """Constant vertex e.g. 'Socrates' should carry a label in the ELK node."""
        egi = parse_egif('(Human "Socrates")')
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        const_v = next(v for v in egi.V if not v.is_generic)
        def find_node(node, target_id):
            if node["id"] == target_id:
                return node
            for c in node.get("children", []):
                found = find_node(c, target_id)
                if found:
                    return found
            return None
        v_node = find_node(g, const_v.id)
        assert v_node is not None
        assert "labels" in v_node
        assert v_node["labels"][0]["text"] == "Socrates"

    def test_layout_options_on_root(self, engine, style):
        """Root node must carry ELK layout options."""
        egi = parse_egif("(Human *x)")
        sizes = engine._compute_element_sizes(egi, style)
        g = engine._egi_to_elk_graph(egi, style, sizes)
        opts = g.get("layoutOptions", {})
        assert opts.get("elk.algorithm") == "layered"
        assert "elk.hierarchyHandling" in opts


# ---------------------------------------------------------------------------
# Phase 3 + integration: generate_layout returns complete LayoutDTO
# ---------------------------------------------------------------------------

class TestGenerateLayout:
    def test_returns_layout_dto(self, engine, style):
        egi = parse_egif("(Human *x)")
        dto = engine.generate_layout(egi, style)
        assert isinstance(dto, LayoutDTO)

    def test_all_vertices_positioned(self, engine, style):
        egi = parse_egif("(On *x *y)")
        dto = engine.generate_layout(egi, style)
        for v in egi.V:
            assert v.id in dto.vertex_positions
            pt = dto.vertex_positions[v.id]
            assert isinstance(pt, Point)

    def test_all_predicates_positioned(self, engine, style):
        egi = parse_egif("(On *x *y)")
        dto = engine.generate_layout(egi, style)
        for e in egi.E:
            assert e.id in dto.predicate_positions

    def test_all_cuts_bounded(self, engine, style):
        egi = parse_egif("~[ (Cat *x) ~[ (Animal x) ] ]")
        dto = engine.generate_layout(egi, style)
        for c in egi.Cut:
            assert c.id in dto.cut_bounds
            bb = dto.cut_bounds[c.id]
            assert isinstance(bb, BoundingBox)
            assert bb.width > 0
            assert bb.height > 0

    def test_ligature_paths_populated(self, engine, style):
        egi = parse_egif("(Human *x)")
        dto = engine.generate_layout(egi, style)
        assert len(dto.ligature_paths) >= 1
        lp = dto.ligature_paths[0]
        assert isinstance(lp, LigaturePath)
        assert len(lp.points) >= 2

    def test_viewport_bounds_populated(self, engine, style):
        egi = parse_egif("(Human *x)")
        dto = engine.generate_layout(egi, style)
        vp = dto.viewport_bounds
        assert isinstance(vp, BoundingBox)
        assert vp.width > 0
        assert vp.height > 0

    def test_sheet_id_matches(self, engine, style):
        egi = parse_egif("(Human *x)")
        dto = engine.generate_layout(egi, style)
        assert dto.sheet_id == egi.sheet

    def test_nested_cuts_layout(self, engine, style):
        """Layout for nested cuts: both cuts bounded, inner cut inside outer cut."""
        egi = parse_egif("~[ (Cat *x) ~[ (Animal x) ] ]")
        dto = engine.generate_layout(egi, style)
        assert len(dto.cut_bounds) == 2
        # Both predicates and shared vertex positioned
        assert len(dto.predicate_positions) == 2
        assert len(dto.vertex_positions) == 1

    def test_no_overlapping_sibling_cuts(self, engine, style):
        """Two sibling cuts should not overlap significantly."""
        egi = parse_egif("~[ (Cat *x) ] ~[ (Dog *y) ]")
        dto = engine.generate_layout(egi, style)
        assert len(dto.cut_bounds) == 2
        bounds = list(dto.cut_bounds.values())
        a, b = bounds[0], bounds[1]
        # Check no significant overlap: the two cut bounding boxes should not
        # overlap in at least one axis
        x_overlap = (a.min_x < b.max_x) and (b.min_x < a.max_x)
        y_overlap = (a.min_y < b.max_y) and (b.min_y < a.max_y)
        assert not (x_overlap and y_overlap), (
            f"Sibling cuts overlap: {a} vs {b}"
        )

    def test_nested_cut_contained_in_parent_cut(self, engine, style):
        """A child cut's bounding box must lie inside its parent cut's bounding box.

        ELK's hierarchical compound graph layout is supposed to guarantee this,
        but it depends on (a) the EGI → ELK mapping marking cuts as containers
        with correct parent/child links, and (b) ELK respecting the padding
        spec. Regressions in either layer would produce diagrams where Dau's
        nesting semantics is visually violated."""
        egi = parse_egif("~[ (Cat *x) ~[ (Animal x) ] ]")
        dto = engine.generate_layout(egi, style)
        # Find parent → child cut relationship via area_hierarchy.
        outer_id = None
        inner_id = None
        for parent_id, children in dto.area_hierarchy.items():
            child_cuts = [c.id for c in egi.Cut if c.id in children]
            if parent_id != egi.sheet and child_cuts:
                outer_id = parent_id
                inner_id = child_cuts[0]
                break
        assert outer_id is not None, "expected a non-sheet cut with a child cut"
        assert inner_id is not None
        outer = dto.cut_bounds[outer_id]
        inner = dto.cut_bounds[inner_id]
        assert outer.min_x <= inner.min_x, f"inner.min_x={inner.min_x} escapes outer.min_x={outer.min_x}"
        assert outer.min_y <= inner.min_y, f"inner.min_y={inner.min_y} escapes outer.min_y={outer.min_y}"
        assert inner.max_x <= outer.max_x, f"inner.max_x={inner.max_x} escapes outer.max_x={outer.max_x}"
        assert inner.max_y <= outer.max_y, f"inner.max_y={inner.max_y} escapes outer.max_y={outer.max_y}"

    def test_intra_area_ligature_stays_inside_predicates_cut(self, engine, style):
        """For a predicate and its vertex both living in the same cut, the
        ligature path connecting them must stay within that cut's bounds.

        Cross-cut ligatures (Beta lines of identity) are intentional and
        excluded from this check — we only assert containment when both
        endpoints belong to the same enclosed area."""
        # Single predicate, single vertex, both inside one cut.
        egi = parse_egif("~[ (Cat *x) ]")
        dto = engine.generate_layout(egi, style)
        # The lone cut bounds.
        assert len(dto.cut_bounds) == 1
        cut_id, cut_bb = next(iter(dto.cut_bounds.items()))

        # Build vertex_id → area_id and predicate_id → area_id maps.
        elem_area: dict = {}
        for area_id, members in egi.area.items():
            for m in members:
                elem_area[m] = area_id

        checked = 0
        for lp in dto.ligature_paths:
            v_area = elem_area.get(lp.vertex_id)
            p_area = elem_area.get(lp.predicate_id)
            if v_area == p_area == cut_id:
                checked += 1
                for pt in lp.points:
                    # Allow a tiny tolerance for floating-point edge cases.
                    eps = 0.5
                    assert cut_bb.min_x - eps <= pt.x <= cut_bb.max_x + eps, (
                        f"ligature x={pt.x} outside cut [{cut_bb.min_x},{cut_bb.max_x}]"
                    )
                    assert cut_bb.min_y - eps <= pt.y <= cut_bb.max_y + eps, (
                        f"ligature y={pt.y} outside cut [{cut_bb.min_y},{cut_bb.max_y}]"
                    )
        assert checked >= 1, "expected at least one intra-cut ligature to check"

    def test_corpus_example(self, engine, style):
        """Load and layout a corpus EGI JSON example end-to-end."""
        corpus_path = (
            Path(__file__).parent.parent
            / "tomos"
            / "graphs"
            / "peirce_cp_4_394_man_mortal"
            / "peirce_cp_4_394_man_mortal.egi.json"
        )
        if not corpus_path.exists():
            pytest.skip("Corpus file not found")

        from egi_io import load_egi_json
        egi = load_egi_json(corpus_path)
        dto = engine.generate_layout(egi, style)

        assert isinstance(dto, LayoutDTO)
        assert len(dto.vertex_positions) == len(egi.V)
        assert len(dto.predicate_positions) == len(egi.E)
        assert len(dto.cut_bounds) == len(egi.Cut)


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    """LayoutDTO from ELK engine must be usable wherever the D3 LayoutDTO was."""

    def test_dto_fields_present(self, engine, style):
        egi = parse_egif("(Human *x)")
        dto = engine.generate_layout(egi, style)
        assert hasattr(dto, "vertex_positions")
        assert hasattr(dto, "predicate_positions")
        assert hasattr(dto, "cut_bounds")
        assert hasattr(dto, "ligature_paths")
        assert hasattr(dto, "area_hierarchy")
        assert hasattr(dto, "viewport_bounds")
        assert hasattr(dto, "sheet_id")
        assert hasattr(dto, "style")

    def test_area_hierarchy_populated(self, engine, style):
        egi = parse_egif("~[ (Cat *x) ~[ (Animal x) ] ]")
        dto = engine.generate_layout(egi, style)
        assert egi.sheet in dto.area_hierarchy

    def test_ligature_path_type(self, engine, style):
        egi = parse_egif("(Human *x)")
        dto = engine.generate_layout(egi, style)
        for lp in dto.ligature_paths:
            assert isinstance(lp, LigaturePath)
            assert all(isinstance(pt, Point) for pt in lp.points)
