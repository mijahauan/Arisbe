"""
Minimal deterministic renderer for Dau-compliant cut layouts.
- Uses GraphvizLayoutEngine in no-post-processing mode as the single source of truth.
- Applies only a uniform scale + translate transform to fit canvas.
- Draws to SVG (no GUI dependencies, no padding, no clamping).
- Enforces invariant: final drawn bounds == transformed Graphviz bounds.
"""
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class UniformTransform:
    sx: float
    sy: float
    tx: float
    ty: float

    def apply_point(self, x: float, y: float) -> Tuple[float, float]:
        return (x * self.sx + self.tx, y * self.sy + self.ty)

    def apply_box(self, b: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        x1,y1,x2,y2 = b
        X1,Y1 = self.apply_point(x1,y1)
        X2,Y2 = self.apply_point(x2,y2)
        if X1 > X2: X1,X2 = X2,X1
        if Y1 > Y2: Y1,Y2 = Y2,Y1
        return (X1,Y1,X2,Y2)


def compute_uniform_transform(world: Tuple[float,float,float,float],
                               canvas: Tuple[int,int]) -> UniformTransform:
    wx1, wy1, wx2, wy2 = world
    cw, ch = canvas
    ww = max(1e-6, wx2 - wx1)
    wh = max(1e-6, wy2 - wy1)
    sx = cw / ww
    sy = ch / wh
    s = min(sx, sy)
    tx = -wx1 * s + (cw - (ww * s)) * 0.5
    ty = -wy1 * s + (ch - (wh * s)) * 0.5
    return UniformTransform(s, s, tx, ty)


def render_layout_to_svg(layout: Any,
                         svg_path: str,
                         canvas_px: Tuple[int,int]=(800,600),
                         stroke_width: float = 1.0,
                         cut_color: str = "#333",
                         fill_color: str = "none",
                         graph: Optional[Any] = None,
                         background_color: str = "#fafafa",
                         cut_corner_radius: float = 14.0,
                         pred_font_size: float = 12.0,
                         pred_char_width: float = 7.0,
                         pred_pad_x: float = 6.0,
                         pred_pad_y: float = 4.0) -> None:
    # Compute transform from layout.canvas_bounds to canvas_px
    world = layout.canvas_bounds
    T = compute_uniform_transform(world, canvas_px)

    # Prepare SVG header
    cw, ch = canvas_px
    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{cw}' height='{ch}' viewBox='0 0 {cw} {ch}'>",
        f"  <rect x='0' y='0' width='{cw}' height='{ch}' fill='{background_color}'/>",
        "  <g>"
    ]

    # Collect cut primitives and build bbox-based containment to color/label
    cuts: Dict[str, Tuple[float,float,float,float]] = {}
    for pid, prim in layout.primitives.items():
        if getattr(prim, 'element_type', None) == 'cut' and prim.bounds:
            cuts[pid] = prim.bounds

    def contains(a: Tuple[float,float,float,float], b: Tuple[float,float,float,float], tol: float=1e-6) -> bool:
        ax1,ay1,ax2,ay2 = a
        bx1,by1,bx2,by2 = b
        return (bx1 > ax1 + tol) and (by1 > ay1 + tol) and (bx2 < ax2 - tol) and (by2 < ay2 - tol)

    # Build parent map (smallest container)
    ids = list(cuts.keys())
    parent: Dict[str, Optional[str]] = {k: None for k in ids}
    for i in ids:
        best: Optional[str] = None
        best_area: Optional[float] = None
        bi = cuts[i]
        for j in ids:
            if i == j: continue
            bj = cuts[j]
            if contains(bj, bi):
                area = (bj[2]-bj[0])*(bj[3]-bj[1])
                if best_area is None or area < best_area:
                    best, best_area = j, area
        parent[i] = best

    # Compute depth per cut
    depth: Dict[str, int] = {}
    def get_depth(k: str) -> int:
        if k in depth: return depth[k]
        p = parent[k]
        d = 0 if p is None else get_depth(p) + 1
        depth[k] = d
        return d
    for k in ids: get_depth(k)

    # Simple palette per depth
    palette = ["#2c3e50", "#8e44ad", "#16a085", "#2980b9", "#c0392b", "#d35400"]
    # Matching low-alpha fills for visibility by depth
    fills = [
        "rgba(44,62,80,0.06)",   # depth 0
        "rgba(142,68,173,0.06)",
        "rgba(22,160,133,0.06)",
        "rgba(41,128,185,0.06)",
        "rgba(192,57,43,0.06)",
        "rgba(211,84,0,0.06)",
    ]

    # Precompute transformed centers
    centers: Dict[str, Tuple[float,float]] = {}
    for pid in ids:
        b = cuts[pid]
        cx = 0.5 * (b[0] + b[2])
        cy = 0.5 * (b[1] + b[3])
        centers[pid] = T.apply_point(cx, cy)

    # Draw cuts: depth-based fill (no fill for root), colored stroke by depth, labels (with parent), and raw-edge overlay
    for pid in ids:
        b = cuts[pid]
        X1,Y1,X2,Y2 = T.apply_box(b)
        inset = stroke_width * 0.5
        X1i, Y1i = X1 + inset, Y1 + inset
        X2i, Y2i = X2 - inset, Y2 - inset
        if X2i < X1i:
            midx = 0.5 * (X1 + X2)
            X1i = X2i = midx
        if Y2i < Y1i:
            midy = 0.5 * (Y1 + Y2)
            Y1i = Y2i = midy
        w = max(0.0, X2i - X1i)
        h = max(0.0, Y2i - Y1i)
        col = palette[depth[pid] % len(palette)]
        # Choose fill: no fill for root (to avoid "3-pane" effect), subtle fill otherwise
        is_root = parent[pid] is None
        this_fill = 'none' if is_root else fills[depth[pid] % len(fills)]
        # Main stroked rect with chosen fill for readability
        # Softened corners for visible cut boundary per Dau examples
        lines.append(
            f"    <rect x='{X1i:.3f}' y='{Y1i:.3f}' width='{w:.3f}' height='{h:.3f}' "
            f"fill='{this_fill}' stroke='{col}' stroke-width='{stroke_width}' rx='{cut_corner_radius:.1f}' ry='{cut_corner_radius:.1f}' shape-rendering='geometricPrecision'/>"
        )
        # Hairline raw-edge overlay (exact Graphviz bbox). Lighter for root, stronger for non-root
        Xw = max(0.0, X2 - X1)
        Yh = max(0.0, Y2 - Y1)
        hl_col = '#bdc3c7' if is_root else '#e74c3c'
        hl_sw = '0.4' if is_root else '0.6'
        lines.append(
            f"    <rect x='{X1:.3f}' y='{Y1:.3f}' width='{Xw:.3f}' height='{Yh:.3f}' "
            f"fill='none' stroke='{hl_col}' stroke-width='{hl_sw}' stroke-dasharray='2,2' shape-rendering='crispEdges'/>"
        )
        # Label in top-left (include parent id prefix if any)
        label_x = X1i + 4
        label_y = Y1i + 12
        ptxt = parent[pid][:10] + "/" if parent[pid] else ""
        # Text with halo for readability
        lines.append(
            f"    <text x='{label_x:.3f}' y='{label_y:.3f}' font-size='10' fill='{col}' stroke='white' stroke-width='1' paint-order='stroke fill'>{ptxt}{pid[:10]}</text>"
        )

    # Draw parent-child connectors (dashed) to make hierarchy explicit
    for pid in ids:
        p = parent[pid]
        if not p:
            continue
        cx, cy = centers[pid]
        px, py = centers[p]
        lines.append(
            f"    <line x1='{px:.3f}' y1='{py:.3f}' x2='{cx:.3f}' y2='{cy:.3f}' stroke='#7f8c8d' stroke-width='1' stroke-dasharray='3,3'/>"
        )

    # If a graph is provided, render predicates, vertices, and heavy identity lines deterministically
    if graph is not None:
        # Helper: transform a point and bounds
        def tpt(x: float, y: float) -> Tuple[float, float]:
            return T.apply_point(x, y)
        def tbox(b: Tuple[float,float,float,float]) -> Tuple[float,float,float,float]:
            return T.apply_box(b)

        # Prepare predicate bounds map (will be tightened per label metrics)
        pred_bounds: Dict[str, Tuple[float,float,float,float]] = {}

        # Draw predicate boxes first (invisible tight boundary) and center label
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'predicate' and prim.bounds:
                # Use layout bounds as initial box, then tighten around the label text metrics
                bx1,by1,bx2,by2 = tbox(prim.bounds)
                label = getattr(graph, 'rel', {}).get(pid, pid[:10])
                # Approximate text metrics for tight boundary (parameterized)
                font_size = float(pred_font_size)
                char_w = float(pred_char_width)
                pad_x = float(pred_pad_x)
                pad_y = float(pred_pad_y)
                text_w = max(1.0, len(label) * char_w)
                text_h = font_size * 1.2
                cx = (bx1 + bx2) * 0.5
                cy = (by1 + by2) * 0.5
                x1 = cx - text_w * 0.5 - pad_x
                x2 = cx + text_w * 0.5 + pad_x
                y1 = cy - text_h * 0.5 - pad_y
                y2 = cy + text_h * 0.5 + pad_y
                # Draw invisible tight boundary
                lines.append(
                    f"    <rect x='{x1:.3f}' y='{y1:.3f}' width='{(x2-x1):.3f}' height='{(y2-y1):.3f}' fill='none' stroke='none'/>"
                )
                # Center label
                lx = cx
                ly = cy
                lines.append(
                    f"    <text x='{lx:.3f}' y='{ly:.3f}' font-size='{font_size:.0f}' text-anchor='middle' dominant-baseline='middle' "
                    f"fill='#2c3e50' stroke='white' stroke-width='1' paint-order='stroke fill'>{label}</text>"
                )
                # Update predicate bounds map to use tight boundary for ligature termination and avoidance
                pred_bounds[pid] = (x1, y1, x2, y2)

        # Draw heavy identity lines from vertex centers to predicate box periphery per ν
        def rect_edge_intersection(x1: float, y1: float, x2: float, y2: float, px: float, py: float) -> Tuple[float,float]:
            # Ray from (px,py) to rect center; find intersection with rectangle border
            cx = (x1+x2)*0.5; cy=(y1+y2)*0.5
            dx = cx - px; dy = cy - py
            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                return cx, cy
            # Parametric intersection
            t_candidates: List[float] = []
            if abs(dx) > 1e-6:
                t_candidates.extend([(x1-px)/dx, (x2-px)/dx])
            if abs(dy) > 1e-6:
                t_candidates.extend([(y1-py)/dy, (y2-py)/dy])
            hit_x, hit_y = cx, cy
            best_t = None
            for t in t_candidates:
                if t <= 0:  # must move from point toward center
                    continue
                tx = px + t*dx; ty = py + t*dy
                if x1-1e-6 <= tx <= x2+1e-6 and y1-1e-6 <= ty <= y2+1e-6:
                    if best_t is None or t < best_t:
                        best_t = t; hit_x, hit_y = tx, ty
            return hit_x, hit_y

        # Index vertex positions
        vert_pos: Dict[str, Tuple[float,float]] = {}
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'vertex' and prim.position:
                vx, vy = prim.position
                vert_pos[pid] = tpt(vx, vy)

        # Utility: line vs rect intersection (with padding)
        def line_intersects_rect(x1: float, y1: float, x2: float, y2: float,
                                  rx1: float, ry1: float, rx2: float, ry2: float,
                                  pad: float = 4.0) -> bool:
            # Expand rect by pad
            rx1p, ry1p, rx2p, ry2p = rx1 - pad, ry1 - pad, rx2 + pad, ry2 + pad
            # Cohen–Sutherland or simple segment-rect test using Liang–Barsky approach
            # Quick reject if both points on one outside side
            if (x1 < rx1p and x2 < rx1p) or (x1 > rx2p and x2 > rx2p) or \
               (y1 < ry1p and y2 < ry1p) or (y1 > ry2p and y2 > ry2p):
                return False
            # If either endpoint is inside expanded rect, count as intersecting
            if (rx1p <= x1 <= rx2p and ry1p <= y1 <= ry2p) or (rx1p <= x2 <= rx2p and ry1p <= y2 <= ry2p):
                return True
            # Check intersection with 4 edges
            def segs_intersect(ax, ay, bx, by, cx, cy, dx, dy) -> bool:
                def orient(px, py, qx, qy, rx, ry):
                    return (qx - px) * (ry - py) - (qy - py) * (rx - px)
                o1 = orient(x1, y1, x2, y2, ax, ay)
                o2 = orient(x1, y1, x2, y2, bx, by)
                o3 = orient(ax, ay, bx, by, x1, y1)
                o4 = orient(ax, ay, bx, by, x2, y2)
                if o1 == 0 and min(x1, x2) - 1e-6 <= ax <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= ay <= max(y1, y2) + 1e-6:
                    return True
                if o2 == 0 and min(x1, x2) - 1e-6 <= bx <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= by <= max(y1, y2) + 1e-6:
                    return True
                return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)
            return (
                segs_intersect(rx1p, ry1p, rx2p, ry1p, x1, y1, x2, y2) or
                segs_intersect(rx2p, ry1p, rx2p, ry2p, x1, y1, x2, y2) or
                segs_intersect(rx2p, ry2p, rx1p, ry2p, x1, y1, x2, y2) or
                segs_intersect(rx1p, ry2p, rx1p, ry1p, x1, y1, x2, y2)
            )

        # Generate a curved path that detours around obstacles when needed
        def generate_path(vx: float, vy: float, hx: float, hy: float,
                          obstacles: List[Tuple[float,float,float,float]]) -> str:
            # if straight segment clear, draw straight
            clear = True
            for ox1, oy1, ox2, oy2 in obstacles:
                if line_intersects_rect(vx, vy, hx, hy, ox1, oy1, ox2, oy2):
                    clear = False; break
            if clear:
                return f"M {vx:.3f},{vy:.3f} L {hx:.3f},{hy:.3f}"
            # Otherwise, create a single-quadratic curve that bows around the nearest obstacle
            # Choose control point orthogonal to segment, offset away from obstacle center
            mx, my = 0.5*(vx+hx), 0.5*(vy+hy)
            dx, dy = hx - vx, hy - vy
            nx, ny = -dy, dx
            # Determine sign of normal by sampling which side reduces intersections
            def count_hits(cx: float, cy: float) -> int:
                hits = 0
                for ox1, oy1, ox2, oy2 in obstacles:
                    # Approximate by splitting curve as two segments
                    if line_intersects_rect(vx, vy, cx, cy, ox1, oy1, ox2, oy2) or \
                       line_intersects_rect(cx, cy, hx, hy, ox1, oy1, ox2, oy2):
                        hits += 1
                return hits
            # Normalization with guard
            nlen = (nx*nx + ny*ny) ** 0.5 or 1.0
            nxn, nyn = nx / nlen, ny / nlen
            scale = max(16.0, ((dx*dx + dy*dy) ** 0.5) * 0.25)
            c1x, c1y = mx + nxn * scale, my + nyn * scale
            c2x, c2y = mx - nxn * scale, my - nyn * scale
            if count_hits(c1x, c1y) <= count_hits(c2x, c2y):
                cx, cy = c1x, c1y
            else:
                cx, cy = c2x, c2y
            return f"M {vx:.3f},{vy:.3f} Q {cx:.3f},{cy:.3f} {hx:.3f},{hy:.3f}"

        # Obstacles: all predicate boxes except the target predicate itself
        all_pred_boxes = list(pred_bounds.values())

        # Draw ligatures (single continuous path per vertex-to-predicate connection)
        if hasattr(graph, 'nu'):
            for edge_id, vseq in graph.nu.items():
                if edge_id not in pred_bounds:
                    continue
                rx1, ry1, rx2, ry2 = pred_bounds[edge_id]
                # Obstacles exclude the destination predicate to allow attaching to its periphery
                obstacles = [b for b in all_pred_boxes if b is not pred_bounds[edge_id]]
                for vid in vseq:
                    if vid not in vert_pos:
                        continue
                    vx, vy = vert_pos[vid]
                    hx, hy = rect_edge_intersection(rx1, ry1, rx2, ry2, vx, vy)
                    d = generate_path(vx, vy, hx, hy, obstacles)
                    lines.append(
                        f"    <path d='{d}' fill='none' stroke='#111' stroke-width='3' stroke-linecap='round'/>"
                    )

        # Draw vertices last on top
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'vertex' and prim.position:
                vx, vy = tpt(*prim.position)
                r = 4.0
                lines.append(
                    f"    <circle cx='{vx:.3f}' cy='{vy:.3f}' r='{r:.3f}' fill='#111' stroke='none'/>"
                )
                # Constant label if any
                try:
                    vobj = graph._vertex_map.get(pid)
                    if vobj and getattr(vobj, 'label', None):
                        lx, ly = vx + 6, vy - 6
                        txt = vobj.label
                        lines.append(
                            f"    <text x='{lx:.3f}' y='{ly:.3f}' font-size='10' fill='#111' stroke='white' stroke-width='1' paint-order='stroke fill'>{txt}</text>"
                        )
                except Exception:
                    pass

    lines.append("  </g>")
    lines.append("</svg>")

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def transformed_bounds_map(layout: Any,
                            canvas_px: Tuple[int,int]=(800,600)) -> Dict[str, Tuple[float,float,float,float]]:
    T = compute_uniform_transform(layout.canvas_bounds, canvas_px)
    out: Dict[str, Tuple[float,float,float,float]] = {}
    for pid, prim in layout.primitives.items():
        if prim.bounds:
            out[pid] = T.apply_box(prim.bounds)
    return out
