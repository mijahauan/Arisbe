import math
from typing import List, Tuple

from src.egi_core_dau import create_empty_graph
from src.egi_system import InsertVertex, InsertEdge, InsertCut
from src.egi_spatial_correspondence import create_spatial_correspondence_engine, SpatialBounds


def _segment_intersects_rect(p1: Tuple[float, float], p2: Tuple[float, float], rect: SpatialBounds) -> bool:
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    rx1, ry1, rx2, ry2 = x, y, x + w, y + h

    def orient(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    def on_seg(a, b, c):
        return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
                min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))

    # Rectangle edges
    edges = [((rx1, ry1), (rx2, ry1)), ((rx2, ry1), (rx2, ry2)), ((rx2, ry2), (rx1, ry2)), ((rx1, ry2), (rx1, ry1))]
    # Quick inside check
    if (rx1 <= p1[0] <= rx2 and ry1 <= p1[1] <= ry2) or (rx1 <= p2[0] <= rx2 and ry1 <= p2[1] <= ry2):
        return True
    for a, b in edges:
        o1 = orient(p1, p2, a)
        o2 = orient(p1, p2, b)
        o3 = orient(a, b, p1)
        o4 = orient(a, b, p2)
        if o1 == 0 and on_seg(p1, p2, a):
            return True
        if o2 == 0 and on_seg(p1, p2, b):
            return True
        if o3 == 0 and on_seg(a, b, p1):
            return True
        if o4 == 0 and on_seg(a, b, p2):
            return True
        if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
            return True
    return False


def _path_intersects_rect(path: List[Tuple[float, float]], rect: SpatialBounds) -> bool:
    for i in range(len(path) - 1):
        if _segment_intersects_rect(path[i], path[i+1], rect):
            return True
    return False


def _find_ligature_path(layout):
    lig = next(k for k, v in layout.items() if v.element_type == 'ligature')
    return layout[lig].ligature_geometry.spatial_path


def test_corridor_between_two_sibling_cuts_same_area():
    egi = create_empty_graph()
    # One shared vertex and two predicates on sheet
    egi = InsertVertex('x', area_id='sheet').apply(egi)
    egi = InsertEdge('P', relation='P', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertEdge('Q', relation='Q', vertices=['x'], area_id='sheet').apply(egi)

    # Two sibling cuts form a corridor
    egi = InsertCut('C_top', parent_area='sheet').apply(egi)
    egi = InsertCut('C_bottom', parent_area='sheet').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    path = _find_ligature_path(layout)
    top = layout['C_top'].spatial_bounds
    bottom = layout['C_bottom'].spatial_bounds

    # Same-area routing must not intersect either cut
    assert not _path_intersects_rect(path, top)
    assert not _path_intersects_rect(path, bottom)


def test_nested_cuts_same_area_avoids_both():
    egi = create_empty_graph()
    # Vertex and two preds on sheet
    egi = InsertVertex('x', area_id='sheet').apply(egi)
    egi = InsertEdge('P', relation='P', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertEdge('Q', relation='Q', vertices=['x'], area_id='sheet').apply(egi)

    # Parent and child cut nested
    egi = InsertCut('C_outer', parent_area='sheet').apply(egi)
    egi = InsertCut('C_inner', parent_area='C_outer').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    path = _find_ligature_path(layout)
    outer_b = layout['C_outer'].spatial_bounds
    inner_b = layout['C_inner'].spatial_bounds

    assert not _path_intersects_rect(path, outer_b)
    assert not _path_intersects_rect(path, inner_b)


def test_tiny_degenerate_cut_is_still_avoided_same_area():
    egi = create_empty_graph()
    egi = InsertVertex('x', area_id='sheet').apply(egi)
    egi = InsertEdge('P', relation='P', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertEdge('Q', relation='Q', vertices=['x'], area_id='sheet').apply(egi)

    # Add a very small cut; ensure router avoids intersecting even if tiny
    egi = InsertCut('C_tiny', parent_area='sheet').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    path = _find_ligature_path(layout)
    tiny = layout['C_tiny'].spatial_bounds

    assert not _path_intersects_rect(path, tiny)
