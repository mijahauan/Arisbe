import random
import math

from src.egi_controller import EGIController
from src.egi_spatial_correspondence import SpatialElement, SpatialBounds


def center(bounds: SpatialBounds):
    return (bounds.x + bounds.width / 2, bounds.y + bounds.height / 2)


def make_edge(layout, area, x, y, w=80, h=20):
    se = SpatialElement(
        element_id=f'e_{x}_{y}',
        element_type='edge',
        logical_area=area,
        spatial_bounds=SpatialBounds(x, y, w, h),
        relation_name='R',
    )
    layout[se.element_id] = se
    return se.spatial_bounds


def make_vertex(layout, area, x, y, w=10, h=10):
    sv = SpatialElement(
        element_id=f'v_{x}_{y}',
        element_type='vertex',
        logical_area=area,
        spatial_bounds=SpatialBounds(x, y, w, h),
    )
    layout[sv.element_id] = sv
    return sv.spatial_bounds


def make_cut(layout, area, x, y, w, h, idx):
    sc = SpatialElement(
        element_id=f'c_{idx}',
        element_type='cut',
        logical_area=area,
        spatial_bounds=SpatialBounds(x, y, w, h),
    )
    layout[sc.element_id] = sc
    return sc.spatial_bounds


def rects_intersect(a: SpatialBounds, b: SpatialBounds) -> bool:
    return not (
        a.x + a.width <= b.x or b.x + b.width <= a.x or
        a.y + a.height <= b.y or b.y + b.height <= a.y
    )


def test_random_obstacles_with_reserved_corridor(seed: int = 1337, trials: int = 100):
    random.seed(seed)
    ctrl = EGIController()
    area = ctrl.egi_system.get_egi().sheet

    # Canvas bounds compatible with controller defaults
    canvas = SpatialBounds(50, 50, 700, 500)

    for t in range(trials):
        layout = {}

        # Reserve a horizontal corridor band free of cuts
        corridor_y = random.randint(int(canvas.y + 80), int(canvas.y + canvas.height - 80))
        corridor_h = 30  # keep this wider than router padding
        corridor_top = corridor_y - corridor_h // 2
        corridor_bottom = corridor_y + corridor_h // 2

        # Place start/end across canvas within corridor
        e = make_edge(layout, area, canvas.x + 60, corridor_y - 10)  # slightly off center
        v = make_vertex(layout, area, canvas.x + canvas.width - 110, corridor_y - 10)
        start, end = center(e), center(v)

        # Populate many random cuts avoiding the corridor band
        cuts = []
        for i in range(25):
            for _ in range(50):  # attempts to place
                w = random.randint(30, 120)
                h = random.randint(30, 120)
                x = random.randint(int(canvas.x + 80), int(canvas.x + canvas.width - 80 - w))
                # pick y above or below the corridor band, guarding against empty ranges
                placed = False
                top_low = int(canvas.y + 60)
                top_high = int(corridor_top - h - 5)
                bot_low = int(corridor_bottom + 5)
                bot_high = int(canvas.y + canvas.height - 60 - h)
                if random.random() < 0.5:
                    if top_low <= top_high:
                        y = random.randint(top_low, top_high)
                        placed = True
                    elif bot_low <= bot_high:
                        y = random.randint(bot_low, bot_high)
                        placed = True
                else:
                    if bot_low <= bot_high:
                        y = random.randint(bot_low, bot_high)
                        placed = True
                    elif top_low <= top_high:
                        y = random.randint(top_low, top_high)
                        placed = True
                if not placed:
                    continue
                candidate = SpatialBounds(x, y, w, h)
                if rects_intersect(candidate, e) or rects_intersect(candidate, v):
                    continue
                # keep a small margin between cuts to reduce degenerate slivers
                ok = True
                for cb in cuts:
                    grown = SpatialBounds(cb.x - 4, cb.y - 4, cb.width + 8, cb.height + 8)
                    if rects_intersect(candidate, grown):
                        ok = False
                        break
                if not ok:
                    continue
                cuts.append(candidate)
                make_cut(layout, area, x, y, w, h, idx=f'{t}_{i}')
                break

        # Ensure straight line hits something (or at least router runs)
        direct_hits = any(ctrl._line_intersects_rectangle(start, end, c) for c in cuts)

        path = ctrl._route_ligature_around_cuts(start, end, layout)
        assert len(path) >= 2
        # All segments must avoid all cuts
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            for c in cuts:
                assert not ctrl._line_intersects_rectangle(a, b, c)

        # If direct path was clear, router should typically return direct or near-direct
        if not direct_hits:
            # path is either start->end or a low-cost detour; at least check endpoints
            assert path[0] == start and path[-1] == end


def test_dense_sibling_barriers_leave_small_gap(seed: int = 4242):
    random.seed(seed)
    ctrl = EGIController()
    area = ctrl.egi_system.get_egi().sheet
    layout = {}

    # Start/end
    e = make_edge(layout, area, 80, 140)
    v = make_vertex(layout, area, 620, 140)
    start, end = center(e), center(v)

    # Build several vertical barrier cuts leaving a snaking corridor
    cuts = []
    x = 150
    step = 60
    for i in range(6):
        # alternate top/bottom gaps to cause a zig-zag
        if i % 2 == 0:
            # leave a gap at the top
            cuts.append(make_cut(layout, area, x, 160, 40, 180, idx=i))
        else:
            # leave a gap at the bottom
            cuts.append(make_cut(layout, area, x, 60, 40, 180, idx=i))
        x += step

    # Sanity: straight line intersects many cuts
    assert any(ctrl._line_intersects_rectangle(start, end, c.spatial_bounds) for c in layout.values() if c.element_type == 'cut')

    path = ctrl._route_ligature_around_cuts(start, end, layout)
    assert len(path) >= 2
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        for c in cuts:
            assert not ctrl._line_intersects_rectangle(a, b, c)
