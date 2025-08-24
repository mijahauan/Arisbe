import pytest

from src.egi_core_dau import create_empty_graph
from src.egi_system import InsertVertex, InsertEdge, InsertCut
from src.egi_spatial_correspondence import create_spatial_correspondence_engine, SpatialBounds


def _overlaps(a: SpatialBounds, b: SpatialBounds) -> bool:
    return not (a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y)


def _contains(inner: SpatialBounds, outer: SpatialBounds) -> bool:
    return outer.contains_bounds(inner)


def test_nested_cuts_spatial_exclusion_and_mapping():
    egi = create_empty_graph()
    # Create nested cuts: sheet -> C1 -> C2
    egi = InsertCut('C1', parent_area='sheet').apply(egi)
    egi = InsertCut('C2', parent_area='C1').apply(egi)

    # Vertex inside C1
    egi = InsertVertex('x', area_id='C1').apply(egi)

    # Predicates across areas
    egi = InsertEdge('P1', relation='P', vertices=['x'], area_id='C1').apply(egi)   # same area as vertex
    egi = InsertEdge('Q1', relation='Q', vertices=['x'], area_id='C2').apply(egi)  # deeper nested cut
    egi = InsertEdge('R1', relation='R', vertices=['x'], area_id='sheet').apply(egi)  # ancestor area

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    # Helpers should validate without errors
    assert engine.validate_mapping_consistency(layout) is True
    assert engine.validate_spatial_exclusion(layout) is True

    # Explicit spatial exclusion checks with bounds
    c1 = layout['C1'].spatial_bounds
    c2 = layout['C2'].spatial_bounds

    # Elements placed in sheet must not overlap C1 or C2 holes
    sheet_elems = [v for v in layout.values() if v.logical_area == 'sheet' and v.element_type in ('edge', 'vertex', 'ligature')]
    for se in sheet_elems:
        assert not _overlaps(se.spatial_bounds, c1)
        assert not _overlaps(se.spatial_bounds, c2)

    # Elements placed in C1 must be inside C1 and not overlap C2 (its child)
    c1_elems = [v for v in layout.values() if v.logical_area == 'C1' and v.element_type in ('edge', 'vertex', 'ligature')]
    for se in c1_elems:
        assert _contains(se.spatial_bounds, c1)
        assert not _overlaps(se.spatial_bounds, c2)

    # Elements placed in C2 must be inside C2
    c2_elems = [v for v in layout.values() if v.logical_area == 'C2' and v.element_type in ('edge', 'vertex', 'ligature')]
    for se in c2_elems:
        assert _contains(se.spatial_bounds, c2)


def test_multi_star_ligatures_with_sibling_cuts():
    egi = create_empty_graph()
    # Two vertices on sheet, each with multiple predicates (two separate stars)
    egi = InsertVertex('x', area_id='sheet').apply(egi)
    egi = InsertVertex('y', area_id='sheet').apply(egi)

    # Predicates for x
    egi = InsertEdge('Px1', relation='P', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertEdge('Qx1', relation='Q', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertEdge('Rx1', relation='R', vertices=['x'], area_id='sheet').apply(egi)

    # Predicates for y (place some in a cut)
    egi = InsertCut('C', parent_area='sheet').apply(egi)
    egi = InsertEdge('Py1', relation='P', vertices=['y'], area_id='sheet').apply(egi)
    egi = InsertEdge('Qy1', relation='Q', vertices=['y'], area_id='C').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    # Helpers should validate
    assert engine.validate_mapping_consistency(layout) is True
    assert engine.validate_spatial_exclusion(layout) is True

    # Ensure both ligatures exist (one for x, one for y)
    ligs = [k for k, v in layout.items() if v.element_type == 'ligature']
    assert len(ligs) >= 2

    # Star arms should respect same-area hole: choose the ligature in sheet area and verify
    # By construction, x's predicates are all in sheet; verify ligature bounds do not overlap cut C
    cut_bounds = layout['C'].spatial_bounds
    x_ligs = [v for v in layout.values() if v.element_type == 'ligature' and v.logical_area == 'sheet']
    for lg in x_ligs:
        assert not _overlaps(lg.spatial_bounds, cut_bounds)
