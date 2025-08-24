from src.egi_core_dau import create_empty_graph
from src.egi_system import InsertVertex, InsertEdge, InsertCut
from src.egi_spatial_correspondence import create_spatial_correspondence_engine


def test_cut_size_grows_with_contents():
    egi = create_empty_graph()
    # Create empty cut on sheet
    egi = InsertCut('C', parent_area='sheet').apply(egi)
    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()
    empty_bounds = layout['C'].spatial_bounds

    # Add content into the cut: a vertex and a predicate
    egi = InsertVertex('v1', area_id='C').apply(egi)
    egi = InsertEdge('e1', relation='R', vertices=['v1'], area_id='C').apply(egi)
    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()
    filled_bounds = layout['C'].spatial_bounds

    assert filled_bounds.width >= empty_bounds.width
    assert filled_bounds.height >= empty_bounds.height


def test_cut_size_grows_with_nested_cut():
    egi = create_empty_graph()
    # Parent cut
    egi = InsertCut('P', parent_area='sheet').apply(egi)
    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()
    parent_empty = layout['P'].spatial_bounds

    # Add child cut inside parent
    egi = InsertCut('Child', parent_area='P').apply(egi)
    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()
    parent_with_child = layout['P'].spatial_bounds

    assert parent_with_child.width >= parent_empty.width
    assert parent_with_child.height >= parent_empty.height
