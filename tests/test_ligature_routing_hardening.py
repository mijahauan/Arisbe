import pytest

from src.egi_controller import EGIController
from src.egi_spatial_correspondence import SpatialElement, SpatialBounds


def segments(path):
    return list(zip(path, path[1:]))


def test_same_area_ligature_routes_around_cut():
    ctrl = EGIController()

    # Minimal layout: one edge box, one vertex dot, one cut rectangle between them
    layout = {}

    edge_id = 'edge_A'
    vertex_id = 'v_A'
    cut_id = 'cut_block'
    area_id = ctrl.egi_system.get_egi().sheet

    # Place edge left, vertex right, cut in the middle
    edge_bounds = SpatialBounds(100, 90, 80, 20)  # center ~ (140, 100)
    vertex_bounds = SpatialBounds(300, 95, 10, 10)  # center ~ (305, 100)
    cut_bounds = SpatialBounds(180, 60, 40, 80)     # spans y=[60,140], sits between

    layout[edge_id] = SpatialElement(
        element_id=edge_id,
        element_type='edge',
        logical_area=area_id,
        spatial_bounds=edge_bounds,
        relation_name='R'
    )
    layout[vertex_id] = SpatialElement(
        element_id=vertex_id,
        element_type='vertex',
        logical_area=area_id,
        spatial_bounds=vertex_bounds,
    )
    layout[cut_id] = SpatialElement(
        element_id=cut_id,
        element_type='cut',
        logical_area=area_id,
        spatial_bounds=cut_bounds,
    )

    start = (
        edge_bounds.x + edge_bounds.width / 2,
        edge_bounds.y + edge_bounds.height / 2,
    )
    end = (
        vertex_bounds.x + vertex_bounds.width / 2,
        vertex_bounds.y + vertex_bounds.height / 2,
    )

    # Sanity: straight line crosses the cut
    assert ctrl._line_intersects_rectangle(start, end, cut_bounds)

    # Routed path should avoid the cut
    path = ctrl._route_ligature_around_cuts(start, end, layout)
    assert len(path) >= 2

    # Validate every segment avoids the cut rectangle
    for a, b in segments(path):
        assert not ctrl._line_intersects_rectangle(a, b, cut_bounds)
