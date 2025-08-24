import math
from typing import List, Tuple

from src.egi_core_dau import create_empty_graph
from src.egi_system import InsertVertex, InsertEdge, InsertCut
from src.egi_spatial_correspondence import create_spatial_correspondence_engine, SpatialElement, SpatialBounds


def _segment_intersects_rect(p1: Tuple[float, float], p2: Tuple[float, float], rect: SpatialBounds) -> bool:
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    rx1, ry1, rx2, ry2 = x, y, x + w, y + h

    def orient(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    def on_seg(a, b, c):
        return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
                min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))

    # Check segment against each rectangle edge
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


def test_same_area_ligature_avoids_cut():
    egi = create_empty_graph()
    # Add vertex and two predicates all on sheet
    egi = InsertVertex('x', area_id='sheet').apply(egi)
    egi = InsertEdge('P1', relation='P', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertEdge('P2', relation='Q', vertices=['x'], area_id='sheet').apply(egi)
    # Add a sibling cut on sheet (acts as obstacle in same-area)
    egi = InsertCut('C', parent_area='sheet').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    # Find the ligature
    lig = next(k for k, v in layout.items() if v.element_type == 'ligature')
    lig_path = layout[lig].ligature_geometry.spatial_path
    cut_bounds = layout['C'].spatial_bounds

    # Same-area path should avoid the cut rectangle
    assert not _path_intersects_rect(lig_path, cut_bounds)


def test_cross_area_ligature_may_cross_cut():
    egi = create_empty_graph()
    # Add sheet vertex and two edges; put one predicate into a child cut
    egi = InsertVertex('x', area_id='sheet').apply(egi)
    egi = InsertEdge('P1', relation='P', vertices=['x'], area_id='sheet').apply(egi)
    egi = InsertCut('C', parent_area='sheet').apply(egi)
    # Cross-area: predicate inside cut C
    egi = InsertEdge('P2', relation='Q', vertices=['x'], area_id='C').apply(egi)

    engine = create_spatial_correspondence_engine(egi)
    layout = engine.generate_spatial_layout()

    lig = next(k for k, v in layout.items() if v.element_type == 'ligature')
    lig_path = layout[lig].ligature_geometry.spatial_path
    cut_bounds = layout['C'].spatial_bounds

    # Cross-area: obstacles are disabled; path is allowed to cross the cut
    assert _path_intersects_rect(lig_path, cut_bounds)
