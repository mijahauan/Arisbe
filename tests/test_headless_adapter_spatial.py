import pytest

from egi_logical_areas import EGILogicalSystem, EGIGraph
from egi_adapter import logical_to_relational_graph
from egi_spatial_correspondence import SpatialCorrespondenceEngine, SpatialElement


def test_adapter_generates_spatial_layout_with_cut_vertex_edge_and_ligature():
    # Build logical system with one cut containing one vertex and one unary predicate
    sys = EGILogicalSystem(sheet_id="sheet_test")
    assert sys.sheet_id == "sheet_test"

    # Create a cut under the sheet
    created = sys.create_negation_area(cut_id="c1", parent_area_id=sys.sheet_id)
    assert created is True

    # Add a vertex graph inside the cut
    v_id = "v1"
    v_graph = sys.create_vertex_graph(v_id)
    ok_v = sys.add_graph_to_area(v_graph, target_area_id="c1")
    assert ok_v is True

    # Add a unary predicate edge incident to v1 inside the same cut
    e_id = "e1"
    e_graph = sys.create_edge_graph(e_id, relation_name="P", incident_vertices={v_id})
    ok_e = sys.add_graph_to_area(e_graph, target_area_id="c1")
    assert ok_e is True

    # Adapt to RelationalGraphWithCuts
    rgc = logical_to_relational_graph(sys)

    # Sanity of relational structure
    assert any(c.id == "c1" for c in rgc.Cut)
    assert any(v.id == v_id for v in rgc.V)
    assert any(e.id == e_id for e in rgc.E)
    assert tuple(sorted(rgc.nu.get(e_id, ()))) == (v_id,)
    assert rgc.rel.get(e_id) == "P"
    # c1 must contain v1 and e1 directly
    assert v_id in rgc.area.get("c1", frozenset())
    assert e_id in rgc.area.get("c1", frozenset())

    # Generate spatial layout
    engine = SpatialCorrespondenceEngine(rgc)
    layout = engine.generate_spatial_layout()

    # Assertions: cut, vertex, edge exist and are placed in the correct logical area
    assert "c1" in layout
    assert layout["c1"].element_type == "cut"

    assert v_id in layout
    assert layout[v_id].element_type == "vertex"
    assert layout[v_id].logical_area == "c1"

    assert e_id in layout
    assert layout[e_id].element_type == "edge"
    assert layout[e_id].logical_area == "c1"

    # There should be a ligature involving v1
    ligature_ids = [k for k, v in layout.items() if v.element_type == "ligature"]
    assert len(ligature_ids) >= 1
    # Check at least one ligature geometry mentions v1
    found_v1 = False
    for lid in ligature_ids:
        geom = layout[lid].ligature_geometry
        if geom and (v_id in geom.vertices):
            found_v1 = True
            break
    assert found_v1, "Expected a ligature geometry including vertex v1"
