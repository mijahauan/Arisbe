import pytest

from src.egi_controller import EGIController
from src.egi_spatial_correspondence import SpatialElement, SpatialBounds


def segs(path):
    return list(zip(path, path[1:]))


def make_centers(bounds: SpatialBounds):
    return (bounds.x + bounds.width / 2, bounds.y + bounds.height / 2)


def base_layout_with_elements(ctrl: EGIController):
    return {}, ctrl.egi_system.get_egi().sheet


def add_cut(layout, element_id, area_id, x, y, w, h):
    layout[element_id] = SpatialElement(
        element_id=element_id,
        element_type='cut',
        logical_area=area_id,
        spatial_bounds=SpatialBounds(x, y, w, h),
    )
    return layout[element_id].spatial_bounds


def add_edge(layout, element_id, area_id, x, y, w=80, h=20):
    layout[element_id] = SpatialElement(
        element_id=element_id,
        element_type='edge',
        logical_area=area_id,
        spatial_bounds=SpatialBounds(x, y, w, h),
        relation_name='R',
    )
    return layout[element_id].spatial_bounds


def add_vertex(layout, element_id, area_id, x, y, w=10, h=10):
    layout[element_id] = SpatialElement(
        element_id=element_id,
        element_type='vertex',
        logical_area=area_id,
        spatial_bounds=SpatialBounds(x, y, w, h),
    )
    return layout[element_id].spatial_bounds


def test_nested_cuts_routing_avoids_both():
    ctrl = EGIController()
    layout, area = base_layout_with_elements(ctrl)

    # Edge on left, vertex on right
    e_bounds = add_edge(layout, 'e', area, 100, 95)
    v_bounds = add_vertex(layout, 'v', area, 320, 95)

    # Outer cut centered, inner cut inside
    outer = add_cut(layout, 'cut_outer', area, 180, 60, 80, 90)
    inner = add_cut(layout, 'cut_inner', area, 205, 85, 30, 40)

    start = make_centers(e_bounds)
    end = make_centers(v_bounds)

    # Straight line crosses both
    assert ctrl._line_intersects_rectangle(start, end, outer)
    assert ctrl._line_intersects_rectangle(start, end, inner)

    path = ctrl._route_ligature_around_cuts(start, end, layout)
    assert len(path) >= 2

    for a, b in segs(path):
        assert not ctrl._line_intersects_rectangle(a, b, outer)
        assert not ctrl._line_intersects_rectangle(a, b, inner)


def test_sibling_cuts_provide_corridor_path():
    ctrl = EGIController()
    layout, area = base_layout_with_elements(ctrl)

    e_bounds = add_edge(layout, 'e', area, 100, 95)
    v_bounds = add_vertex(layout, 'v', area, 320, 95)

    # Two sibling cuts with a small vertical gap between them (corridor)
    top = add_cut(layout, 'cut_top', area, 180, 60, 80, 35)     # y: 60-95
    bottom = add_cut(layout, 'cut_bottom', area, 180, 105, 80, 35)  # y: 105-140

    start = make_centers(e_bounds)
    end = make_centers(v_bounds)

    # Straight line passes through the gap y=100; but given padding, router likely goes above or below
    path = ctrl._route_ligature_around_cuts(start, end, layout)
    assert len(path) >= 2

    for a, b in segs(path):
        assert not ctrl._line_intersects_rectangle(a, b, top)
        assert not ctrl._line_intersects_rectangle(a, b, bottom)


def test_grazing_near_cut_edge_does_not_cross():
    ctrl = EGIController()
    layout, area = base_layout_with_elements(ctrl)

    # Place a cut; endpoints near the left edge but outside
    cut = add_cut(layout, 'cut', area, 200, 80, 60, 40)

    # Edge and vertex almost horizontally aligned, just above the cut top edge
    e_bounds = add_edge(layout, 'e', area, 120, 70)
    v_bounds = add_vertex(layout, 'v', area, 300, 70)

    start = make_centers(e_bounds)
    end = make_centers(v_bounds)

    # Sanity: straight line does not intersect (it runs above the cut)
    assert not ctrl._line_intersects_rectangle(start, end, cut)

    # Router should keep it straight or a slight detour, but still not intersect
    path = ctrl._route_ligature_around_cuts(start, end, layout)
    assert len(path) >= 2

    for a, b in segs(path):
        assert not ctrl._line_intersects_rectangle(a, b, cut)
