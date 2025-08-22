"""
Canonical Qt renderer for Dau-compliant EG diagrams.
- Mirrors src/renderer_minimal_dau.py logic, but draws with QPainter.
- Applies uniform fit transform from layout.canvas_bounds to widget size.
- Draws: cuts, predicate labels with tight bounds, heavy identity lines
  as single continuous paths from vertex to predicate periphery, vertices
  and constant labels. No hook lines.
"""
from __future__ import annotations
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QFont
    from PySide6.QtCore import QRectF, Qt
except Exception:  # pragma: no cover
    QPainter = object  # type: ignore


# Removed deprecated UniformTransform class - using simple_transform instead


def _rect_edge_intersection(x1: float, y1: float, x2: float, y2: float, px: float, py: float) -> Tuple[float, float]:
    cx = (x1 + x2) * 0.5
    cy = (y1 + y2) * 0.5
    dx = cx - px
    dy = cy - py
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return cx, cy
    t_candidates: List[float] = []
    if abs(dx) > 1e-6:
        t_candidates.extend([(x1 - px) / dx, (x2 - px) / dx])
    if abs(dy) > 1e-6:
        t_candidates.extend([(y1 - py) / dy, (y2 - py) / dy])
    hit_x, hit_y = cx, cy
    best_t: Optional[float] = None
    for t in t_candidates:
        if t <= 0:
            continue
        tx = px + t * dx
        ty = py + t * dy
        if x1 - 1e-6 <= tx <= x2 + 1e-6 and y1 - 1e-6 <= ty <= y2 + 1e-6:
            if best_t is None or t < best_t:
                best_t = t
                hit_x, hit_y = tx, ty
    return hit_x, hit_y


def _rect_normal_at_point(x1: float, y1: float, x2: float, y2: float, hx: float, hy: float) -> Tuple[float, float]:
    """Compute outward normal of axis-aligned rectangle at boundary point (hx, hy).
    Returns a unit vector (nx, ny) pointing outward.
    """
    cx = (x1 + x2) * 0.5
    cy = (y1 + y2) * 0.5
    # Compare distances to edges to decide which side we're on
    dx_left = abs(hx - x1)
    dx_right = abs(x2 - hx)
    dy_top = abs(hy - y1)
    dy_bottom = abs(y2 - hy)
    m = min(dx_left, dx_right, dy_top, dy_bottom)
    if m == dx_left:
        return (-1.0, 0.0)
    if m == dx_right:
        return (1.0, 0.0)
    if m == dy_top:
        return (0.0, -1.0)
    return (0.0, 1.0)


def _line_intersects_rect(x1: float, y1: float, x2: float, y2: float,
                          rx1: float, ry1: float, rx2: float, ry2: float,
                          pad: float = 4.0) -> bool:
    rx1p, ry1p, rx2p, ry2p = rx1 - pad, ry1 - pad, rx2 + pad, ry2 + pad
    # quick reject
    if (x1 < rx1p and x2 < rx1p) or (x1 > rx2p and x2 > rx2p) or \
       (y1 < ry1p and y2 < ry1p) or (y1 > ry2p and y2 > ry2p):
        return False
    # endpoint inside
    if (rx1p <= x1 <= rx2p and ry1p <= y1 <= ry2p) or (rx1p <= x2 <= rx2p and ry1p <= y2 <= ry2p):
        return True

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


def _generate_path(vx: float, vy: float, hx: float, hy: float,
                   obstacles: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float]]:
    # Straight if no collision
    for ox1, oy1, ox2, oy2 in obstacles:
        if _line_intersects_rect(vx, vy, hx, hy, ox1, oy1, ox2, oy2):
            break
    else:
        return [(vx, vy), (hx, hy)]
    # simple curved mid control, choose normal that reduces hits
    mx, my = 0.5 * (vx + hx), 0.5 * (vy + hy)
    dx, dy = hx - vx, hy - vy
    nx, ny = -dy, dx
    nlen = (nx * nx + ny * ny) ** 0.5 or 1.0
    nxn, nyn = nx / nlen, ny / nlen
    scale = max(16.0, ((dx * dx + dy * dy) ** 0.5) * 0.25)
    c1x, c1y = mx + nxn * scale, my + nyn * scale
    c2x, c2y = mx - nxn * scale, my - nyn * scale

    def hits(cx: float, cy: float) -> int:
        h = 0
        for ox1, oy1, ox2, oy2 in obstacles:
            if _line_intersects_rect(vx, vy, cx, cy, ox1, oy1, ox2, oy2) or _line_intersects_rect(cx, cy, hx, hy, ox1, oy1, ox2, oy2):
                h += 1
        return h

    if hits(c1x, c1y) <= hits(c2x, c2y):
        return [(vx, vy), (c1x, c1y), (hx, hy)]
    else:
        return [(vx, vy), (c2x, c2y), (hx, hy)]


class CanonicalQtRenderer:
    def __init__(self, default_style=None):
        
        # Store pipeline components for rendering integration
        self._graphviz_renderer = None
        self._pipeline_phases = None
        self._spatial_system = None
        
        # Initialize with DauStyle if no style provided
        if default_style is None:
            from rendering_styles import DauStyle
            default_style = DauStyle()
        
        self.default_style = default_style
        # Add missing attributes from DauStyle for compatibility
        self.stroke_width = default_style.cut_line_width
        self.cut_corner_radius = 5.0  # Default corner radius for cuts
        self.vertex_radius = default_style.vertex_radius
        self.pred_font_family = default_style.font_family
        self.pred_font_size = 12
        self.pred_char_width = 8.0  # Estimated character width for text sizing
        self.pred_pad_x = default_style.predicate_padding_x
        self.pred_pad_y = default_style.predicate_padding_y
        self.draw_argument_markers = False  # Disable argument markers for now

    def render(self, painter: QPainter, layout: Any, graph: Any, canvas_px: Tuple[int, int]) -> None:
        cw, ch = canvas_px
        print(f"DEBUG: render() called with canvas_px: {canvas_px}")
        painter.fillRect(QRectF(0, 0, cw, ch), self.default_style.background_color)
        print(f"DEBUG: Filled background with color: {self.default_style.background_color}")
        
        if not hasattr(layout, 'canvas_bounds'):
            print("DEBUG: layout has no canvas_bounds - returning early")
            return
        
        if not hasattr(layout, 'primitives'):
            print("DEBUG: layout has no primitives - returning early")
            return
            
        # DEBUG: quick type counts vs graph sizes
        try:
            type_counts: Dict[str, int] = {}
            verts_preview: List[str] = []
            for pid, prim in layout.primitives.items():
                t = getattr(prim, 'element_type', None)
                type_counts[t] = type_counts.get(t, 0) + 1
                if t == 'vertex' and prim.position and len(verts_preview) < 6:
                    x, y = prim.position
                    verts_preview.append(f"{pid}@({x:.1f},{y:.1f})")
            v_count = len(getattr(graph, 'V', []))
            print(f"CANON DEBUG: graph |V|={v_count}, prim types={type_counts}, vertex prims sample={verts_preview}")
        except Exception as e:
            print(f"DEBUG: Error in primitive analysis: {e}")
        # Simple direct coordinate mapping instead of complex transform
        canvas_bounds = layout.canvas_bounds
        print(f"DEBUG: canvas_bounds: {canvas_bounds}, canvas_px: {canvas_px}")
        
        # Create a simple scaling transform that maps canvas_bounds to canvas_px
        cb_x1, cb_y1, cb_x2, cb_y2 = canvas_bounds
        canvas_w, canvas_h = canvas_px
        
        # Add margins
        margin = 50
        draw_w = canvas_w - 2 * margin
        draw_h = canvas_h - 2 * margin
        
        # Scale factors
        scale_x = draw_w / max(1, cb_x2 - cb_x1)
        scale_y = draw_h / max(1, cb_y2 - cb_y1)
        scale = min(scale_x, scale_y)  # Uniform scaling
        
        def simple_transform(bounds):
            x1, y1, x2, y2 = bounds
            # Translate to origin, scale, then translate to canvas center
            nx1 = margin + (x1 - cb_x1) * scale
            ny1 = margin + (y1 - cb_y1) * scale
            nx2 = margin + (x2 - cb_x1) * scale
            ny2 = margin + (y2 - cb_y1) * scale
            return (nx1, ny1, nx2, ny2)
        
        print(f"DEBUG: Using scale={scale:.2f}, margin={margin}")

        # Collect cut bounds and basic parent map for depth coloring
        cuts: Dict[str, Tuple[float, float, float, float]] = {}
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'cut' and prim.bounds:
                cuts[pid] = prim.bounds

        def contains(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float], tol: float = 1e-6) -> bool:
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            return (bx1 > ax1 + tol) and (by1 > ay1 + tol) and (bx2 < ax2 - tol) and (by2 < ay2 - tol)

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
                    area = (bj[2] - bj[0]) * (bj[3] - bj[1])
                    if best_area is None or area < best_area:
                        best, best_area = j, area
            parent[i] = best

        # Use DauStyle colors instead of hardcoded palette
        cut_color = self.default_style.cut_color
        cut_pen = QPen(cut_color, self.default_style.cut_line_width, Qt.PenStyle.SolidLine)

        # Draw cuts using simple transform
        for pid in ids:
            b = cuts[pid]
            X1, Y1, X2, Y2 = simple_transform(b)
            print(f"DEBUG: Drawing cut {pid} at bounds {b} -> screen ({X1:.1f},{Y1:.1f},{X2:.1f},{Y2:.1f})")
            inset = self.stroke_width * 0.5
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
            painter.setPen(cut_pen)
            painter.setBrush(QBrush())
            painter.drawRoundedRect(QRectF(X1i, Y1i, w, h), self.cut_corner_radius, self.cut_corner_radius)
            print(f"DEBUG: Drew cut rect ({X1i:.1f},{Y1i:.1f}) size {w:.1f}x{h:.1f}")
            # hairline overlay of raw bounds for debugging can be toggled if needed

        # Predicates: build tight bounds and draw centered label
        pred_bounds: Dict[str, Tuple[float, float, float, float]] = {}
        font = QFont(self.pred_font_family, pointSize=self.pred_font_size)
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'predicate' and prim.bounds:
                bx1, by1, bx2, by2 = simple_transform(prim.bounds)
                # Get proper predicate label from graph.rel mapping
                label = getattr(graph, 'rel', {}).get(pid, pid[:10])
                print(f"DEBUG: Predicate {pid} has label '{label}' from rel mapping")
                text_w = max(1.0, len(label) * self.pred_char_width)
                text_h = self.pred_font_size + 2.0
                cx = 0.5 * (bx1 + bx2)
                cy = 0.5 * (by1 + by2)
                x1 = cx - text_w * 0.5 - self.pred_pad_x
                y1 = cy - text_h * 0.5 - self.pred_pad_y
                x2 = cx + text_w * 0.5 + self.pred_pad_x
                y2 = cy + text_h * 0.5 + self.pred_pad_y
                pred_bounds[pid] = (x1, y1, x2, y2)
                painter.setPen(QPen(self.default_style.predicate_color, self.default_style.predicate_line_width, Qt.PenStyle.SolidLine))
                painter.setFont(font)
                painter.drawText(QRectF(x1 + self.pred_pad_x, y1 + self.pred_pad_y, text_w, text_h), Qt.AlignmentFlag.AlignCenter, label)
                print(f"DEBUG: Drew predicate {pid} '{label}' at ({cx:.1f},{cy:.1f})")

        # Vertex positions (with optional readability enhancement for degree-2)
        vert_pos: Dict[str, Tuple[float, float]] = {}
        # First pass: transformed original positions using simple transform
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'vertex' and prim.position:
                vx, vy = prim.position
                # Apply simple transform to point
                nx = margin + (vx - cb_x1) * scale
                ny = margin + (vy - cb_y1) * scale
                vert_pos[pid] = (nx, ny)
                print(f"DEBUG: Vertex {pid} at ({vx:.1f},{vy:.1f}) -> screen ({nx:.1f},{ny:.1f})")

        # Compute predicate centers in screen space for midpoint calculation
        pred_centers: Dict[str, Tuple[float, float]] = {}
        for eid, b in pred_bounds.items():
            rx1, ry1, rx2, ry2 = b
            pred_centers[eid] = ((rx1 + rx2) * 0.5, (ry1 + ry2) * 0.5)

        # Build inverse ν: vertex -> list of predicate ids it's connected to
        v_to_preds: Dict[str, List[str]] = {}
        if hasattr(graph, 'nu'):
            for edge_id, vseq in graph.nu.items():
                for vid in vseq:
                    v_to_preds.setdefault(vid, []).append(edge_id)

        # Helper to get the display bounds of the vertex's logical area (screen space)
        def _area_bounds_for_vertex(vid: str) -> Tuple[float, float, float, float]:
            # Default to full canvas using simple_transform
            canvas_w, canvas_h = canvas_px
            default_bounds = getattr(layout, 'canvas_bounds', (0.0, 0.0, float(canvas_w), float(canvas_h)))
            bx1, by1, bx2, by2 = simple_transform(default_bounds)
            # Try cut membership from graph.area
            try:
                area_map = getattr(graph, 'area', {})
                for area_id, members in area_map.items():
                    if vid in members:
                        if area_id == getattr(graph, 'sheet', None):
                            return bx1, by1, bx2, by2
                        # find cut primitive bounds
                        cut_prim = next((p for p in layout.primitives.values()
                                         if getattr(p, 'element_type', None) == 'cut' and getattr(p, 'element_id', None) == area_id and getattr(p, 'bounds', None)), None)
                        if cut_prim and cut_prim.bounds:
                            return simple_transform(cut_prim.bounds)
                        break
            except Exception:
                pass
            return bx1, by1, bx2, by2

        # Enhancement: if vertex has exactly two incident predicates, place spot at midpoint of predicate centers, clamped to its logical area
        for vid, preds in v_to_preds.items():
            if len(preds) == 2 and preds[0] in pred_centers and preds[1] in pred_centers:
                (c1x, c1y) = pred_centers[preds[0]]
                (c2x, c2y) = pred_centers[preds[1]]
                mx, my = (0.5 * (c1x + c2x), 0.5 * (c1y + c2y))
                ax1, ay1, ax2, ay2 = _area_bounds_for_vertex(vid)
                # Clamp with a small inset to avoid hugging borders
                inset = 6.0
                ax1i, ay1i, ax2i, ay2i = ax1 + inset, ay1 + inset, ax2 - inset, ay2 - inset
                Mx = min(max(mx, ax1i), ax2i)
                My = min(max(my, ay1i), ay2i)
                vert_pos[vid] = (Mx, My)

        # Obstacles: all predicate boxes
        all_pred_boxes = list(pred_bounds.values())

        # Draw arity markers near predicate boundary only if explicitly enabled
        if self.draw_argument_markers:
            arg_label_boxes: Dict[str, List[QRectF]] = {pid: [] for pid in pred_bounds.keys()}
            label_font = QFont(self.pred_font_family, pointSize=max(9, int(self.pred_font_size * 0.9)))
            for edge_id, vseq in getattr(graph, 'nu', {}).items():
                if edge_id not in pred_bounds:
                    continue
                rx1, ry1, rx2, ry2 = pred_bounds[edge_id]
                placed: List[QRectF] = arg_label_boxes[edge_id]
                for idx, vid in enumerate(vseq):
                    if vid not in vert_pos:
                        continue
                    vx, vy = vert_pos[vid]
                    hx, hy = _rect_edge_intersection(rx1, ry1, rx2, ry2, vx, vy)
                    nx, ny = _rect_normal_at_point(rx1, ry1, rx2, ry2, hx, hy)
                    base_x = hx + nx * 10.0
                    base_y = hy + ny * 10.0
                    tx, ty = -ny, nx
                    r = 8.0
                    rect = QRectF(base_x - r, base_y - r, 2 * r, 2 * r)
                    tries = 0
                    while any(rect.intersects(other) for other in placed) and tries < 6:
                        base_x += tx * 10.0
                        base_y += ty * 10.0
                        rect = QRectF(base_x - r, base_y - r, 2 * r, 2 * r)
                        tries += 1
                    placed.append(rect)
                    painter.setBrush(QBrush(QColor(44, 62, 80)))
                    painter.setPen(QPen(QColor(44, 62, 80)))
                    painter.drawEllipse(rect)
                    painter.setFont(label_font)
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    painter.drawText(rect, Qt.AlignCenter, str(idx + 1))

        # Rectilinear ligatures from ν (no hook lines per Dau specification)
        if hasattr(graph, 'nu'):
            ligature_pen = QPen(self.default_style.ligature_color, self.default_style.ligature_line_width, Qt.PenStyle.SolidLine)
            try:
                ligature_pen.setCapStyle(Qt.RoundCap)
            except Exception:
                pass
            
            for edge_id, vseq in graph.nu.items():
                if edge_id not in pred_bounds:
                    continue
                rx1, ry1, rx2, ry2 = pred_bounds[edge_id]
                
                # Draw rectilinear ligatures (right angles only, no curves)
                for vid in vseq:
                    if vid not in vert_pos:
                        continue
                    vx, vy = vert_pos[vid]
                    
                    # Find closest edge point on predicate rectangle
                    pred_cx = (rx1 + rx2) * 0.5
                    pred_cy = (ry1 + ry2) * 0.5
                    
                    # Create rectilinear path (horizontal then vertical, or vice versa)
                    painter.setPen(ligature_pen)
                    
                    # Choose path based on relative position
                    if abs(vx - pred_cx) > abs(vy - pred_cy):
                        # Horizontal first, then vertical
                        painter.drawLine(vx, vy, pred_cx, vy)
                        painter.drawLine(pred_cx, vy, pred_cx, pred_cy)
                    else:
                        # Vertical first, then horizontal  
                        painter.drawLine(vx, vy, vx, pred_cy)
                        painter.drawLine(vx, pred_cy, pred_cx, pred_cy)

        # Draw vertices on top
        dot_pen = QPen(Qt.NoPen)
        dot_brush = QBrush(QColor(17, 17, 17))
        painter.setPen(dot_pen)
        painter.setBrush(dot_brush)
        for pid, prim in layout.primitives.items():
            if getattr(prim, 'element_type', None) == 'vertex' and prim.position:
                # Use simple transform for fallback position
                if pid in vert_pos:
                    vx, vy = vert_pos[pid]
                else:
                    px, py = prim.position
                    vx = margin + (px - cb_x1) * scale
                    vy = margin + (py - cb_y1) * scale
                r = 4.0
                painter.drawEllipse(QRectF(vx - r, vy - r, 2 * r, 2 * r))
                # constant label if available
                try:
                    vobj = graph._vertex_map.get(pid)
                    if vobj and getattr(vobj, 'label', None):
                        label = vobj.label
                        # Determine average tangent direction from vertex to connected predicates
                        preds = v_to_preds.get(pid, []) if 'v_to_preds' in locals() else []
                        tx, ty = 1.0, 0.0  # default tangent to the right
                        if preds:
                            sx, sy = 0.0, 0.0
                            for eid in preds:
                                if eid in pred_centers:
                                    cx, cy = pred_centers[eid]
                                    dx, dy = (cx - vx), (cy - vy)
                                    L = (dx*dx + dy*dy) ** 0.5 or 1.0
                                    sx += dx / L
                                    sy += dy / L
                            mag = (sx*sx + sy*sy) ** 0.5
                            if mag > 1e-6:
                                tx, ty = sx / mag, sy / mag
                        # small normal offset away from the dot
                        nx, ny = -ty, tx
                        base_x = vx + tx * 12.0 + nx * 6.0
                        base_y = vy + ty * 12.0 + ny * 6.0
                        # Text metrics for tight rect
                        font = QFont(self.pred_font_family, pointSize=10)
                        painter.setFont(font)
                        fm = painter.fontMetrics()
                        tw = max(12, fm.horizontalAdvance(label))
                        th = fm.height()
                        rect = QRectF(base_x - tw * 0.5, base_y - th * 0.5, tw, th)
                        # Draw text with slight halo for readability
                        painter.setPen(QPen(QColor(17, 17, 17), 1))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawText(rect, Qt.AlignCenter, label)
                except Exception:
                    pass

    def create_canvas(self):
        """Create a Qt canvas widget for rendering EG diagrams."""
        try:
            from PySide6.QtWidgets import QWidget
            from PySide6.QtGui import QPaintEvent
            from PySide6.QtCore import QSize
            
            class EGCanvasWidget(QWidget):
                def __init__(self, renderer):
                    super().__init__()
                    self.renderer = renderer
                    self.current_layout = None
                    self.current_graph = None
                    self.current_pixmap = None
                    self.setMinimumSize(400, 300)
                
                def paintEvent(self, event: QPaintEvent):
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    print(f"DEBUG: paintEvent called - pixmap: {self.current_pixmap is not None}, layout: {self.current_layout is not None}, graph: {self.current_graph is not None}")
                    
                    if self.current_pixmap:
                        # Draw the PNG image
                        painter.fillRect(self.rect(), self.renderer.default_style.background_color)
                        # Scale pixmap to fit widget while maintaining aspect ratio
                        scaled_pixmap = self.current_pixmap.scaled(
                            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        # Center the image
                        x = (self.width() - scaled_pixmap.width()) // 2
                        y = (self.height() - scaled_pixmap.height()) // 2
                        painter.drawPixmap(x, y, scaled_pixmap)
                        print("DEBUG: Drew pixmap to canvas")
                    elif self.current_layout and self.current_graph:
                        canvas_size = (self.width(), self.height())
                        print(f"DEBUG: Calling renderer.render with canvas_size: {canvas_size}")
                        self.renderer.render(painter, self.current_layout, self.current_graph, canvas_size)
                        print("DEBUG: Finished renderer.render call")
                    else:
                        # Draw placeholder
                        painter.fillRect(self.rect(), self.renderer.default_style.background_color)
                        painter.setPen(QPen(QColor(100, 100, 100), 1))
                        painter.drawText(self.rect(), Qt.AlignCenter, "No graph loaded")
                        print("DEBUG: Drew placeholder text")
                
                def update_graph(self, layout, graph):
                    """Update the displayed graph and trigger repaint."""
                    self.current_layout = layout
                    self.current_graph = graph
                    self.current_pixmap = None  # Clear pixmap when using layout
                    self.update()
                
                def set_pixmap(self, pixmap):
                    """Set a pixmap to display (from PNG generation)."""
                    self.current_pixmap = pixmap
                    self.current_layout = None  # Clear layout when using pixmap
                    self.current_graph = None
                    self.update()
                
                def sizeHint(self):
                    return QSize(600, 400)
            
            return EGCanvasWidget(self)
            
        except ImportError:
            # Fallback for when PySide6 is not available
            return None

    # Removed deprecated render_to_png_pipeline - use proper EGDF rendering instead

    def render_egi_to_canvas(self, egi, layout_result, canvas_widget, style=None):
        """Render EGI directly to Qt canvas widget using layout primitives with style."""
        try:
            # Get canvas dimensions
            canvas_size = (canvas_widget.width(), canvas_widget.height())
            
            # Apply style if provided
            if style:
                from rendering_styles import get_style
                if isinstance(style, str):
                    style_instance = get_style(style)
                else:
                    style_instance = style
                
                # Transform EGDF primitives with style
                styled_primitives = style_instance.apply_style(layout_result.primitives)
                
                # Render with styled primitives
                self._render_styled_primitives(styled_primitives, canvas_widget, canvas_size)
            else:
                # Use existing render method for default Dau style
                from PySide6.QtGui import QPainter, QPixmap
                
                pixmap = QPixmap(canvas_size[0], canvas_size[1])
                pixmap.fill(self.default_style.background_color)
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                self.render(painter, layout_result, egi, canvas_size)
                painter.end()
                
                # Set pixmap to canvas
                if hasattr(canvas_widget, 'set_pixmap'):
                    canvas_widget.set_pixmap(pixmap)
                elif hasattr(canvas_widget, 'setPixmap'):
                    canvas_widget.setPixmap(pixmap)
                else:
                    print("DEBUG: Canvas widget has no pixmap method")
                
        except Exception as e:
            print(f"Direct Qt rendering error: {e}")
            import traceback
            traceback.print_exc()
    
    def _render_styled_primitives(self, styled_primitives, canvas_widget, canvas_size):
        """Render styled primitives to canvas."""
        from PySide6.QtGui import QPainter, QPixmap, QPen, QBrush
        
        pixmap = QPixmap(canvas_size[0], canvas_size[1])
        pixmap.fill(self.default_style.background_color)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Render each styled primitive
        for primitive_id, styled_primitive in styled_primitives.items():
            self._draw_styled_primitive(painter, styled_primitive)
        
        painter.end()
        
        # Set pixmap to canvas
        if hasattr(canvas_widget, 'set_pixmap'):
            canvas_widget.set_pixmap(pixmap)
        elif hasattr(canvas_widget, 'setPixmap'):
            canvas_widget.setPixmap(pixmap)
    
    def _draw_styled_primitive(self, painter, styled_primitive):
        """Draw a single styled primitive."""
        # This is a basic implementation - would be expanded based on primitive type
        # For now, fall back to existing render method
        pass
