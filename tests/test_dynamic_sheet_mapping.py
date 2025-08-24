import pytest

from src.egi_core_dau import create_empty_graph, Vertex, Edge, Cut
from src.egi_system import InsertVertex, InsertEdge, InsertCut
from src.egi_spatial_correspondence import create_spatial_correspondence_engine


def test_inserts_map_literal_sheet_to_dynamic_sheet():
    egi = create_empty_graph()
    sheet_id = egi.sheet

    # Use literal 'sheet' in operations; they should resolve to egi.sheet
    egi = InsertVertex('v1', area_id='sheet').apply(egi)
    assert any(v.id == 'v1' for v in egi.V)
    assert 'v1' in egi.area[sheet_id]

    egi = InsertEdge('e1', relation='R', vertices=['v1'], area_id='sheet').apply(egi)
    assert any(e.id == 'e1' for e in egi.E)
    assert 'e1' in egi.area[sheet_id]

    egi = InsertCut('c1', parent_area='sheet').apply(egi)
    assert any(c.id == 'c1' for c in egi.Cut)
    assert 'c1' in egi.area[sheet_id]
    assert 'c1' in egi.area  # cut has its own area


def test_spatial_engine_uses_dynamic_sheet_defaults():
    egi = create_empty_graph()
    # Place vertex on sheet and create an edge
    egi = InsertVertex('Tom', area_id='sheet').apply(egi)
    egi = InsertEdge('eT', relation='Person', vertices=['Tom'], area_id='sheet').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    # Ligature created for Tom may or may not exist depending on edges, but vertex should be placed
    assert 'Tom' in layout
    v_bounds = layout['Tom'].spatial_bounds
    # Sheet has no explicit bounds; ensure we got a reasonable point
    assert isinstance(v_bounds.x, (int, float))
    assert isinstance(v_bounds.y, (int, float))
