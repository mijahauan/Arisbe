#!/usr/bin/env python3
"""
DiagramRenderer for Existential Graphs (Dau's Formalism)

This module implements the visual presentation layer that takes layout coordinates
from the Graphviz layout engine and renders proper Existential Graph diagrams
according to Peirce's conventions as formalized by Frithjof Dau.

The DiagramRenderer is the visual bridge that makes the abstract EGI model
understandable by adhering to precise rules of visual representation.
"""

import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import LayoutResult, SpatialPrimitive
from render_geometry import predicate_periphery_point
from pipeline_contracts import (
    validate_relational_graph_with_cuts,
    validate_layout_result,
    ContractViolationError,
)
from pyside6_backend import PySide6Canvas


@dataclass
class VisualConvention:
    """Visual parameters for Peirce/Dau conventions."""
    # Line weights per Dau's formalism
    identity_line_width: float = 4.0      # Heavy lines of identity (thicker)
    cut_line_width: float = 1.5           # Fine-drawn cut curves
    # NOTE: Hook lines removed - hooks are invisible positions per Dau formalism
    
    # Sizes and spacing
    identity_spot_radius: float = 3.0     # Identity spots
    # NOTE: hook_length removed - connections are direct to predicate boundary
    argument_label_offset: float = 8.0    # Distance for argument numbers
    
    # Colors (all black per EG conventions)
    line_color: Tuple[int, int, int] = (0, 0, 0)
    text_color: Tuple[int, int, int] = (0, 0, 0)
    cut_color: Tuple[int, int, int] = (0, 0, 0)


class DiagramRendererDau:
    # Dau-compliant: render vertex spot in its own EGI context (area)
    spot_on_outermost: bool = False
    # Cut rendering mode: 'rect' guarantees strict containment; 'oval' is traditional
    cut_render_mode: str = 'rect'
    """
    DiagramRenderer implementing Peirce's conventions as formalized by Dau.
    
    Takes layout coordinates from Graphviz and renders proper EG diagrams
    with correct visual encoding of the abstract EGI model.
    """
    
    def __init__(self, conventions: VisualConvention = None):
        self.conv = conventions or VisualConvention()
        # Per-frame cache of vertex display positions (do not mutate layout primitives)
        self._vertex_display_pos: Dict[str, Tuple[float, float]] = {}
        
    def render_diagram(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts, 
                       layout_result: LayoutResult, selected_ids: Optional[Set[str]] = None) -> None:
        """
        Render complete EG diagram with Peirce/Dau visual conventions.
        
        Args:
            canvas: Drawing surface
            graph: EGI structure (logical truth)
            layout_result: Spatial coordinates from Graphviz layout engine
        """
        # Enforce API contracts upfront
        validate_relational_graph_with_cuts(graph)
        validate_layout_result(layout_result)
        canvas.clear()
        
        # Compute fit-to-screen transform (scale + offset) to ensure diagram fits the viewport
        scale, offset_x, offset_y = self._compute_fit_transform(canvas, layout_result)
        
        # Apply transform to all coordinates
        centered_layout = self._apply_transform(layout_result, scale, offset_x, offset_y)
        # Expose current layout for collision checks during rendering
        self.current_layout = centered_layout
        # Reset per-frame overrides
        self._vertex_display_pos.clear()
        
        # Render in proper layering order (background to foreground)
        self._render_cuts_as_fine_curves(canvas, graph, centered_layout)
        self._render_ligatures_and_identity_lines(canvas, graph, centered_layout)
        self._render_predicates_with_hooks(canvas, graph, centered_layout)
        self._render_identity_spots_and_constants(canvas, graph, centered_layout)
        # Selection overlay (drawn last)
        if selected_ids:
            self._render_selection_overlay(canvas, graph, centered_layout, selected_ids)
        
        # Add diagram metadata
        self._render_diagram_title(canvas, graph)

    def _render_selection_overlay(self, canvas: PySide6Canvas,
                                  graph: RelationalGraphWithCuts,
                                  layout_result: LayoutResult,
                                  selected_ids: Set[str]) -> None:
        """Render selection halos/boxes for currently selected elements.
        - Predicates: tight rectangle around text
        - Vertices: circular halo around vertex position
        - Cuts: brightened boundary (slightly thicker)
        """
        halo_style = {
            'color': (30, 144, 255),  # dodger blue
            'width': 2.0
        }
        for sid in selected_ids:
            sprim = layout_result.primitives.get(sid)
            if not sprim:
                # It may be a predicate edge id
                if sid in graph.nu:
                    # Compute predicate text bounds and draw rectangle halo
                    pname = graph.rel.get(sid, sid)
                    ppos = self._find_predicate_position(sid, layout_result)
                    if not ppos:
                        continue
                    pb = self._calculate_predicate_bounds(pname, ppos)
                    x1, y1, x2, y2 = pb
                    # draw as rectangular polyline (approx via curve polyline)
                    canvas.draw_curve([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)], halo_style, closed=False)
                continue
            if sprim.element_type == 'predicate' or sid in graph.nu:
                # Same as above, draw tight rectangle around text
                pname = graph.rel.get(sid, sid)
                ppos = self._find_predicate_position(sid, layout_result)
                if not ppos:
                    continue
                pb = self._calculate_predicate_bounds(pname, ppos)
                x1, y1, x2, y2 = pb
                canvas.draw_curve([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)], halo_style, closed=False)
            elif sprim.element_type == 'vertex':
                cx, cy = sprim.position
                radius = 14.0
                canvas.draw_circle((cx, cy), radius, halo_style)
            elif sprim.element_type == 'cut' and sprim.bounds:
                x1, y1, x2, y2 = sprim.bounds
                style = dict(halo_style)
                style['width'] = self.conv.cut_line_width + 1.0
                canvas.draw_oval(x1, y1, x2, y2, style)
    
    def _render_cuts_as_fine_curves(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts,
                                   layout_result: LayoutResult) -> None:
        """
        Render cuts as fine-drawn, closed curves with correct nesting.
        
        The nesting of curves must reflect the areaMap of the underlying EGI,
        ensuring that a cut's visual area correctly contains all its enclosed elements.
        """
        # Debug: validate containment relationships among cut rectangles
        try:
            self._validate_cut_containment(graph, layout_result)
        except Exception:
            pass
        # No clamping/parent-adjustment: Graphviz already guarantees containment for clusters

        # Render cuts outer-to-inner by area to maintain clear layering
        ordered_cuts = []
        for cut in graph.Cut:
            spr = layout_result.primitives.get(cut.id)
            if spr and spr.bounds:
                bx1, by1, bx2, by2 = spr.bounds
                area = (bx2 - bx1) * (by2 - by1)
                ordered_cuts.append((area, cut))
        ordered_cuts.sort(key=lambda t: t[0], reverse=True)

        for _, cut in ordered_cuts:
            if cut.id in layout_result.primitives:
                cut_primitive = layout_result.primitives[cut.id]

                # Use Graphviz-provided bounds directly
                bounds = list(cut_primitive.bounds)
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                
                # Render cuts from Graphviz cluster bounds.
                # Use rectangle to preserve strict containment guarantees from Graphviz.
                style = {
                    'color': self.conv.cut_color,
                    'width': self.conv.cut_line_width,
                    'fill_color': None
                }
                if getattr(self, 'cut_render_mode', 'rect') == 'oval':
                    canvas.draw_oval(bounds[0], bounds[1], bounds[2], bounds[3], style)
                else:
                    x1, y1, x2, y2 = bounds
                    rect_pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
                    canvas.draw_curve(rect_pts, style, closed=True)
                
                # No cut IDs in production rendering
                
    def _validate_cut_containment(self, graph: RelationalGraphWithCuts, layout_result: LayoutResult) -> None:
        """Log any cut containment violations using current primitive bounds.
        This uses center-in-rect to assign a likely parent and checks strict containment."""
        cuts = [(c.id, layout_result.primitives.get(c.id)) for c in graph.Cut]
        cuts = [(cid, spr) for cid, spr in cuts if spr and spr.bounds]
        if not cuts:
            return
        # Build simple parent by area
        areas = {cid: (spr.bounds[2]-spr.bounds[0])*(spr.bounds[3]-spr.bounds[1]) for cid, spr in cuts}
        # Sort small to large to find nearest enclosing rectangle for each
        ordered = sorted(cuts, key=lambda t: areas[t[0]])
        for cid, spr in ordered:
            x1, y1, x2, y2 = spr.bounds
            cx, cy = (x1+x2)/2.0, (y1+y2)/2.0
            parent = None
            parent_area = float('inf')
            for pid, pspr in cuts:
                if pid == cid:
                    continue
                px1, py1, px2, py2 = pspr.bounds
                if px1 <= cx <= px2 and py1 <= cy <= py2:
                    area = areas[pid]
                    if area < parent_area and area > areas[cid]:
                        parent = (pid, (px1, py1, px2, py2))
                        parent_area = area
            if parent is None:
                continue
            pid, (px1, py1, px2, py2) = parent
            # Check containment with tolerant padding to account for post-processing adjustments
            tol = 4.0
            if x1 < px1 - tol or y1 < py1 - tol or x2 > px2 + tol or y2 > py2 + tol:
                print(f"⚠️ Cut containment violation: child {cid} {spr.bounds} not inside parent {pid} {(px1, py1, px2, py2)}")
    def _render_ligatures_and_identity_lines(self, canvas: PySide6Canvas, 
                                           graph: RelationalGraphWithCuts,
                                           layout_result: LayoutResult) -> None:
        """
        Draw ligatures and lines of identity as bold, continuous lines.
        
        Must handle branches, junctions, and connections to predicates correctly.
        """
        # For each vertex, draw a single ligature consistent with its degree
        for vertex_id, vertex in graph._vertex_map.items():
            # We may not have a vertex primitive from Graphviz; don't skip rendering
            vprim = layout_result.primitives.get(vertex_id)

            # Collect predicate bounds attached to this vertex via nu, with multiplicity
            attached_predicate_bounds: List[Tuple[float, float, float, float]] = []
            for edge_id, seq in graph.nu.items():
                # Count how many times this vertex participates in the predicate's ν sequence
                multiplicity = sum(1 for v in seq if v == vertex_id)
                if multiplicity > 0:
                    # Get predicate position from layout by edge_id
                    pred_pos = self._find_predicate_position(edge_id, layout_result)
                    if pred_pos:
                        pred_name = graph.rel.get(edge_id, edge_id)
                        pb = self._calculate_predicate_bounds(pred_name, pred_pos)
                        attached_predicate_bounds.extend([pb] * multiplicity)

            if not attached_predicate_bounds:
                # No predicate attachments: nothing to draw yet, but keep/display a short stub for user editing
                if vprim:
                    raw_pos = self._vertex_display_pos.get(vertex_id, vprim.position)
                else:
                    raw_pos = self._vertex_display_pos.get(vertex_id, (0.0, 0.0))
                vertex_pos = self._ensure_vertex_in_area(vertex_id, raw_pos, graph, layout_result)
                self._vertex_display_pos[vertex_id] = vertex_pos
                continue

            # Establish any existing vertex base position (may be None if not laid out)
            base_pos = self._vertex_display_pos.get(vertex_id, vprim.position if vprim else None)

            # Compute periphery hook points on predicates
            hooks: List[Tuple[float, float]] = []
            if len(attached_predicate_bounds) == 2:
                b1, b2 = attached_predicate_bounds[0], attached_predicate_bounds[1]
                c1 = ((b1[0] + b1[2]) * 0.5, (b1[1] + b1[3]) * 0.5)  # type: ignore
                c2 = ((b2[0] + b2[2]) * 0.5, (b2[1] + b2[3]) * 0.5)  # type: ignore

                if b1 == b2:
                    # Reflexive case: same predicate twice. Place two distinct hooks on the
                    # periphery along the side facing the vertex to avoid collapse.
                    x1, y1, x2, y2 = b1  # type: ignore
                    toward = base_pos if base_pos is not None else self._default_toward_from_bounds(b1)
                    hv = predicate_periphery_point(b1, toward)
                    hx, hy = hv
                    eps = 1e-3
                    spread = 10.0  # separation along the side
                    # Determine side and create two points along that side
                    if abs(hy - y1) < eps:  # top edge
                        a = max(x1, min(x2, hx - spread))
                        b = max(x1, min(x2, hx + spread))
                        h1 = (a, y1)
                        h2 = (b, y1)
                    elif abs(hy - y2) < eps:  # bottom edge
                        a = max(x1, min(x2, hx - spread))
                        b = max(x1, min(x2, hx + spread))
                        h1 = (a, y2)
                        h2 = (b, y2)
                    elif abs(hx - x1) < eps:  # left edge
                        a = max(y1, min(y2, hy - spread))
                        b = max(y1, min(y2, hy + spread))
                        h1 = (x1, a)
                        h2 = (x1, b)
                    else:  # right edge (or fallback)
                        a = max(y1, min(y2, hy - spread))
                        b = max(y1, min(y2, hy + spread))
                        h1 = (x2, a)
                        h2 = (x2, b)
                    hooks = [h1, h2]
                else:
                    h1 = predicate_periphery_point(b1, c2)  # type: ignore
                    h2 = predicate_periphery_point(b2, c1)  # type: ignore
                    # Keep hook on periphery (slightly outside), not inside predicate text
                    def periphery_point_outward(h: Tuple[float, float], c: Tuple[float, float]) -> Tuple[float, float]:
                        hx, hy = h
                        dx, dy = c[0] - hx, c[1] - hy
                        mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                        eps = 1.0
                        return (hx - dx / mag * eps, hy - dy / mag * eps)
                    hooks = [periphery_point_outward(h1, c1), periphery_point_outward(h2, c2)]
            else:
                for pb in attached_predicate_bounds:
                    # Delegate to shared geometry helper for consistency across renderers/exporters
                    toward = base_pos if base_pos is not None else self._default_toward_from_bounds(pb)
                    h = predicate_periphery_point(pb, toward)
                    # Keep hook on periphery (slightly outside)
                    bx1, by1, bx2, by2 = pb
                    pc = ((bx1 + bx2) * 0.5, (by1 + by2) * 0.5)
                    hx, hy = h
                    dx, dy = pc[0] - hx, pc[1] - hy
                    mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                    eps = 1.0
                    hooks.append((hx - dx / mag * eps, hy - dy / mag * eps))

            # Drawing style
            style = {
                'color': self.conv.line_color,
                'width': self.conv.identity_line_width
            }

            # Decide vertex display position now that hooks are known
            # base_pos already computed above
            # Determine Dau target area depth for the vertex spot from the EGI itself:
            # use the vertex's own context nesting depth. This encodes its defining occurrence area.
            target_depth = 0
            try:
                target_depth = graph.get_nesting_depth(vertex_id)
            except Exception:
                # Fallback: if graph context lookup fails, keep prior heuristic (min depth of attached preds)
                def _depth_of_bounds(b: Tuple[float, float, float, float]) -> int:
                    cx, cy = (b[0] + b[2]) * 0.5, (b[1] + b[3]) * 0.5
                    return self._cut_depth_at_point((cx, cy), layout_result)
                if attached_predicate_bounds:
                    target_depth = min(_depth_of_bounds(b) for b in attached_predicate_bounds)
                else:
                    target_depth = 0

            deg = len(hooks)
            if deg == 1:
                # Draw a full heavy line from vertex to the predicate periphery (no stub)
                hx, hy = hooks[0]
                endpoint = (hx, hy)
                if base_pos is None:
                    # Place spot just outside all cuts along the ray from hook toward sheet
                    # Use a small outward offset
                    bx1, by1, bx2, by2 = attached_predicate_bounds[0]
                    pc = ((bx1 + bx2) * 0.5, (by1 + by2) * 0.5)
                    dx, dy = (endpoint[0] - pc[0]), (endpoint[1] - pc[1])
                    mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                    ux, uy = dx / mag, dy / mag
                    guess = (endpoint[0] + ux * 20.0, endpoint[1] + uy * 20.0)
                    vertex_pos = self._ensure_vertex_in_area(vertex_id, guess, graph, layout_result)
                else:
                    vertex_pos = self._ensure_vertex_in_area(vertex_id, base_pos, graph, layout_result)
                # Adjust spot to lie on desired Dau depth along the drawn segment
                vertex_pos = self._nearest_point_on_segment_with_depth(vertex_pos, endpoint, layout_result, target_depth)
                # Use collision-aware straight/curved draw to avoid predicate text
                if not self._segment_intersects_any_bounds(vertex_pos, endpoint, layout_result=self.current_layout,
                                                           exclude_ids=set()):
                    canvas.draw_line(vertex_pos, endpoint, style)
                else:
                    curve_pts = self._curved_avoidance(vertex_pos, endpoint, endpoint)
                    canvas.draw_curve(curve_pts, style, closed=False)
                # Final clamp: keep spot within intended area/canvas
                vertex_pos = self._finalize_spot_area(vertex_id, vertex_pos, [endpoint], graph, layout_result)
                self._vertex_display_pos[vertex_id] = vertex_pos
            elif deg == 2:
                # Single continuous shortest path between two predicate hooks with collision fallback
                h1, h2 = hooks[0], hooks[1]
                if self._segment_intersects_any_predicate(h1, h2, graph, layout_result):
                    # Draw a gentle single-arc curve: control point is midpoint offset along normal
                    mx = (h1[0] + h2[0]) * 0.5
                    my = (h1[1] + h2[1]) * 0.5
                    dx, dy = h2[0] - h1[0], h2[1] - h1[1]
                    seg_len = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                    nx, ny = -dy / seg_len, dx / seg_len  # unit normal
                    # Modest offset for arc height, proportional to segment length but capped
                    arc_h = min(18.0, seg_len * 0.15)
                    ctrl = (mx + nx * arc_h, my + ny * arc_h)
                    canvas.draw_curve([h1, ctrl, h2], style, closed=False)
                    # Place the spot on the rendered quadratic Bezier but ensure it lies inside the vertex area
                    area_id = graph.get_area(vertex_id)
                    area_prim = layout_result.primitives.get(area_id) if (area_id and area_id in layout_result.primitives) else None
                    def bez_point(t: float) -> Tuple[float, float]:
                        omt = 1.0 - t
                        bx = (omt*omt)*h1[0] + 2*omt*t*ctrl[0] + (t*t)*h2[0]
                        by = (omt*omt)*h1[1] + 2*omt*t*ctrl[1] + (t*t)*h2[1]
                        return (bx, by)
                    if area_prim and area_prim.bounds:
                        ax1, ay1, ax2, ay2 = area_prim.bounds
                        pad = 8.0
                        def inside_area(px: float, py: float) -> bool:
                            if getattr(area_prim, 'element_type', None) == 'cut':
                                ecx, ecy = (ax1 + ax2) * 0.5, (ay1 + ay2) * 0.5
                                rx = max((ax2 - ax1) * 0.5 - pad, 1.0)
                                ry = max((ay2 - ay1) * 0.5 - pad, 1.0)
                                nx = (px - ecx) / rx
                                ny = (py - ecy) / ry
                                return (nx*nx + ny*ny) <= 0.96
                            return (ax1 + pad) <= px <= (ax2 - pad) and (ay1 + pad) <= py <= (ay2 - pad)
                        # Choose endpoint inside the area (one hook must be inside the vertex's area)
                        t_in, t_out = (0.0, 1.0) if inside_area(*h1) else (1.0, 0.0)
                        best_t = t_in
                        # Binary search toward the outside endpoint to find the farthest inside point
                        lo, hi = t_in, t_out
                        for _ in range(16):
                            mid = (lo + hi) * 0.5
                            mx, my = bez_point(mid)
                            if inside_area(mx, my):
                                best_t = mid
                                lo, hi = (mid, hi) if t_out > t_in else (lo, mid)
                            else:
                                lo, hi = (lo, mid) if t_out > t_in else (mid, hi)
                        spot = bez_point(best_t)
                    else:
                        # Fallback to midpoint if area unknown
                        spot = bez_point(0.5)
                    # Final clamp: ensure spot lies inside the intended area
                    spot = self._finalize_spot_area(vertex_id, spot, hooks, graph, layout_result)
                    # Final clamp: keep spot within intended area/canvas
                    spot = self._finalize_spot_area(vertex_id, spot, [h1, h2], graph, layout_result)
                    self._vertex_display_pos[vertex_id] = spot
                else:
                    canvas.draw_line(h1, h2, style)
                    # Place the vertex spot on the straight segment, but ensure it lies inside the vertex area
                    area_id = graph.get_area(vertex_id)
                    area_prim = layout_result.primitives.get(area_id) if (area_id and area_id in layout_result.primitives) else None
                    if area_prim and area_prim.bounds:
                        ax1, ay1, ax2, ay2 = area_prim.bounds
                        pad = 8.0
                        def inside_area(px: float, py: float) -> bool:
                            if getattr(area_prim, 'element_type', None) == 'cut':
                                ecx, ecy = (ax1 + ax2) * 0.5, (ay1 + ay2) * 0.5
                                rx = max((ax2 - ax1) * 0.5 - pad, 1.0)
                                ry = max((ay2 - ay1) * 0.5 - pad, 1.0)
                                nx = (px - ecx) / rx
                                ny = (py - ecy) / ry
                                return (nx*nx + ny*ny) <= 0.96
                            return (ax1 + pad) <= px <= (ax2 - pad) and (ay1 + pad) <= py <= (ay2 - pad)
                        # Choose endpoint inside the area and search toward the other
                        def seg_point(t: float) -> Tuple[float, float]:
                            return (h1[0] + (h2[0] - h1[0]) * t, h1[1] + (h2[1] - h1[1]) * t)
                        t_in, t_out = (0.0, 1.0) if inside_area(*h1) else (1.0, 0.0)
                        best_t = t_in
                        lo, hi = t_in, t_out
                        for _ in range(16):
                            mid = (lo + hi) * 0.5
                            mx, my = seg_point(mid)
                            if inside_area(mx, my):
                                best_t = mid
                                lo, hi = (mid, hi) if t_out > t_in else (lo, mid)
                            else:
                                lo, hi = (lo, mid) if t_out > t_in else (mid, hi)
                        spot = seg_point(best_t)
                    else:
                        # Fallback to midpoint if area unknown
                        spot = ( (h1[0]+h2[0])*0.5, (h1[1]+h2[1])*0.5 )
                    self._vertex_display_pos[vertex_id] = spot
            else:
                # Branching from junction at vertex position to each hook
                # If no base position, pick the average of hooks as junction
                if base_pos is None:
                    ax = sum(h[0] for h in hooks) / len(hooks)
                    ay = sum(h[1] for h in hooks) / len(hooks)
                    vertex_pos = (ax, ay)
                else:
                    vertex_pos = self._ensure_vertex_in_area(vertex_id, base_pos, graph, layout_result)
                # Snap junction to Dau target depth area
                vertex_pos = self._nearest_point_on_segment_with_depth(vertex_pos, hooks[0], layout_result, target_depth)
                for hp in hooks:
                    canvas.draw_line(vertex_pos, hp, style)
                # Final clamp: ensure junction lies in intended area
                vertex_pos = self._finalize_spot_area(vertex_id, vertex_pos, hooks, graph, layout_result)
                self._vertex_display_pos[vertex_id] = vertex_pos
    
    def _render_predicates_with_hooks(self, canvas: PySide6Canvas,
                                    graph: RelationalGraphWithCuts,
                                    layout_result: LayoutResult) -> None:
        """
        Render predicates as textual signs with hooks and argument order labels.
        
        FIXED: Ensures predicate text never crosses cut boundaries and lines
        connect cleanly to predicate periphery per Dau's conventions.
        """
        for edge_id, vertex_sequence in graph.nu.items():
            predicate_name = graph.rel.get(edge_id, edge_id)
            
            # Find predicate position from layout
            pred_position = self._find_predicate_position(edge_id, layout_result)
            if not pred_position:
                continue
            
            # FIXED: Calculate predicate text bounds
            pred_bounds = self._calculate_predicate_bounds(predicate_name, pred_position)
            
            # FIXED: Ensure predicate stays within cut boundaries if inside a cut
            adjusted_position = self._ensure_predicate_within_area(edge_id, pred_bounds, graph, layout_result)
            
            # Render predicate name at adjusted position
            canvas.draw_text(
                predicate_name,
                adjusted_position,
                {
                    'color': self.conv.text_color,
                    'font_size': 12,
                    'bold': False
                }
            )
            
            # For multi-place predicates, add argument order labels
            if len(vertex_sequence) > 1:
                self._render_argument_order_labels(
                    canvas, pred_position, vertex_sequence, graph, layout_result, pred_bounds
                )
            
            # Draw hooks connecting to identity lines
            self._render_predicate_hooks(
                canvas, pred_position, vertex_sequence, graph, layout_result
            )
    
    def _render_identity_spots_and_constants(self, canvas: PySide6Canvas,
                                           graph: RelationalGraphWithCuts,
                                           layout_result: LayoutResult) -> None:
        """
        Render identity spots and constant names.
        
        When a vertex is labeled with a constant name, display the name near
        the vertex spot or use the name in place of the spot for direct representation.
        """
        for vertex_id, vertex in graph._vertex_map.items():
            vprim = layout_result.primitives.get(vertex_id)
            # Use display override if present (placed on ligature); else try primitive position
            raw_pos = self._vertex_display_pos.get(vertex_id, vprim.position if vprim else None)
            if raw_pos is None:
                # Fallback: estimate from connected predicate hooks midpoint
                connected = self._find_vertex_predicates(vertex_id, graph, layout_result)
                hooks = []
                for c in connected:
                    pb = self._calculate_predicate_bounds(c['name'], c['position'])
                    hooks.append(predicate_periphery_point(pb, c['position']))
                if hooks:
                    ax = sum(h[0] for h in hooks) / len(hooks)
                    ay = sum(h[1] for h in hooks) / len(hooks)
                    raw_pos = (ax, ay)
                else:
                    continue
            vertex_pos = self._ensure_vertex_in_area(vertex_id, raw_pos, graph, layout_result)
            # Persist in case not yet set
            self._vertex_display_pos[vertex_id] = vertex_pos

            # DEBUG: Report vertex logical area
            try:
                v_area = graph.get_area(vertex_id)
                if v_area and v_area in layout_result.primitives:
                    ab = layout_result.primitives[v_area].bounds
                    print(f"DEBUG: vertex-area id={vertex_id} area={v_area} bounds={ab} spot={vertex_pos}")
                else:
                    print(f"DEBUG: vertex-area id={vertex_id} area={v_area} (sheet or missing) spot={vertex_pos}")
            except Exception:
                pass

            # If constant label exists, draw the label; otherwise draw the identity spot
            if vertex.label:
                # Anchor constant text to the vertex spot with a tiny offset so it stays visually glued.
                # Compute a local normal from nearest branch if available; otherwise use a fixed offset.
                connected = self._find_vertex_predicates(vertex_id, graph, layout_result)
                # Compute hook points once for label clamping and offset
                hooks_local: List[Tuple[float, float]] = []
                for c in connected:
                    pb = self._calculate_predicate_bounds(c['name'], c['position'])
                    hooks_local.append(predicate_periphery_point(pb, vertex_pos))
                offset = ( -6.0, -10.0 )  # default small up-left offset in screen coords
                if hooks_local:
                    # If we have two or more hooks, place the label along the angle bisector between
                    # the two nearest hooks so it sits in the corridor between predicates.
                    if len(hooks_local) >= 2:
                        # Take two closest hooks to the spot
                        sorted_hooks = sorted(hooks_local, key=lambda h: (h[0]-vertex_pos[0])**2 + (h[1]-vertex_pos[1])**2)
                        hA, hB = sorted_hooks[0], sorted_hooks[1]
                        v1x, v1y = hA[0]-vertex_pos[0], hA[1]-vertex_pos[1]
                        v2x, v2y = hB[0]-vertex_pos[0], hB[1]-vertex_pos[1]
                        m1 = math.hypot(v1x, v1y) or 1.0
                        m2 = math.hypot(v2x, v2y) or 1.0
                        u1x, u1y = v1x/m1, v1y/m1
                        u2x, u2y = v2x/m2, v2y/m2
                        bisx, bisy = (u1x + u2x), (u1y + u2y)
                        bm = math.hypot(bisx, bisy) or 1.0
                        bisx, bisy = bisx/bm, bisy/bm
                        # Use small inward offset (<= 10px)
                        offset = (bisx * 8.0, bisy * 8.0)
                    else:
                        # Single hook: use local normal to the branch
                        nearest = hooks_local[0]
                        tx, ty = nearest[0] - vertex_pos[0], nearest[1] - vertex_pos[1]
                        mag = math.hypot(tx, ty) or 1.0
                        nx, ny = (-ty / mag, tx / mag)
                        offset = (nx * 8.0, ny * 8.0)
                # Start exactly next to the spot
                cand = [(vertex_pos[0] + offset[0], vertex_pos[1] + offset[1])]

                def clamp_to_area(pt: Tuple[float, float]) -> Tuple[Tuple[float, float], float]:
                    x, y = pt
                    area_id = graph.get_area(vertex_id)
                    # If vertex area is sheet/None, try least common enclosing cut of hooks
                    if (not area_id) or area_id == graph.sheet:
                        lcec = self._least_common_enclosing_cut_for_points(hooks_local, layout_result) if hooks_local else None
                        area_id = lcec
                    if area_id and area_id != graph.sheet:
                        sprim_area = layout_result.primitives.get(area_id)
                        if sprim_area and sprim_area.bounds:
                            ax1, ay1, ax2, ay2 = sprim_area.bounds
                            pad = 8.0
                            # Prefer ellipse-aware inclusion for cuts (prevents snapping to far boundary)
                            use_ellipse = False
                            try:
                                use_ellipse = getattr(sprim_area, 'element_type', None) == 'cut'
                            except Exception:
                                use_ellipse = False
                            if use_ellipse:
                                ecx, ecy = (ax1 + ax2) * 0.5, (ay1 + ay2) * 0.5
                                rx = max((ax2 - ax1) * 0.5 - pad, 1.0)
                                ry = max((ay2 - ay1) * 0.5 - pad, 1.0)
                                nx = (x - ecx) / rx
                                ny = (y - ecy) / ry
                                val = nx * nx + ny * ny
                                if val <= 1.0:
                                    cx, cy = x, y
                                else:
                                    # Move along the segment from spot -> candidate until just inside the ellipse
                                    sx, sy = vertex_pos
                                    lo, hi = 0.0, 1.0
                                    for _ in range(12):
                                        mid = (lo + hi) * 0.5
                                        mx = sx + (x - sx) * mid
                                        my = sy + (y - sy) * mid
                                        mnx = (mx - ecx) / rx
                                        mny = (my - ecy) / ry
                                        if (mnx * mnx + mny * mny) <= 0.96:  # slightly inside
                                            lo = mid
                                            cx, cy = mx, my
                                        else:
                                            hi = mid
                                    # cx, cy set by last inside mid; fallback to spot if undefined
                                    cx = cx if 'cx' in locals() else sx
                                    cy = cy if 'cy' in locals() else sy
                            else:
                                cx = min(max(x, ax1 + pad), ax2 - pad)
                                cy = min(max(y, ay1 + pad), ay2 - pad)
                            disp = math.hypot(cx - x, cy - y)
                            # If displacement is large, project from vertex toward centroid slightly to stay inside
                            if disp > 6.0:
                                # compute centroid of area for projection
                                cx0, cy0 = (ax1 + ax2) * 0.5, (ay1 + ay2) * 0.5
                                dirx, diry = cx0 - vertex_pos[0], cy0 - vertex_pos[1]
                                mag = math.hypot(dirx, diry) or 1.0
                                dirx, diry = dirx / mag, diry / mag
                                px, py = vertex_pos[0] + dirx * 10.0, vertex_pos[1] + diry * 10.0
                                cx = min(max(px, ax1 + pad), ax2 - pad)
                                cy = min(max(py, ay1 + pad), ay2 - pad)
                                disp = math.hypot(cx - x, cy - y)
                            # Debug log for diagnostics
                            try:
                                print(f'DEBUG: const-label area={area_id} bounds=({ax1:.1f},{ay1:.1f},{ax2:.1f},{ay2:.1f}) spot={vertex_pos} cand=({x:.1f},{y:.1f}) clamped=({cx:.1f},{cy:.1f}) disp={disp:.2f}')
                            except Exception:
                                pass
                            return (cx, cy), disp
                    # Sheet or no suitable area: keep within canvas bounds but very near the spot
                    cb = layout_result.canvas_bounds
                    padc = 6.0
                    sx, sy = vertex_pos
                    cx = min(max(x, cb[0] + padc), cb[2] - padc)
                    cy = min(max(y, cb[1] + padc), cb[3] - padc)
                    disp = math.hypot(cx - x, cy - y)
                    print(f"DEBUG: const-label area=sheet spot={vertex_pos} cand={(x, y)} clamped_canvas={(cx, cy)} disp={disp}")
                    return (cx, cy), disp

                best_pos, best_disp = None, None
                for pt in cand:
                    cp, d = clamp_to_area(pt)
                    if best_pos is None or d < best_disp:
                        best_pos, best_disp = cp, d
                # Keep label very close to spot (avoid large jumps); cap at 10px
                max_dist = 10.0
                vx, vy = vertex_pos
                dx, dy = best_pos[0] - vx, best_pos[1] - vy
                dist = math.hypot(dx, dy)
                if dist > max_dist and dist > 0:
                    scale = max_dist / dist
                    best_pos = (vx + dx * scale, vy + dy * scale)
                label_pos = best_pos
                try:
                    print(f'DEBUG: const-label final vertex={vertex_id} spot={vertex_pos} label={label_pos}')
                except Exception:
                    pass
                canvas.draw_text(
                    f'"{vertex.label}"',
                    label_pos,
                    {
                        'color': self.conv.text_color,
                        'font_size': 10,
                        'bold': False,
                        'draggable': True
                    }
                )
            else:
                # Draw identity spot at the display position
                canvas.draw_circle(vertex_pos, self.conv.identity_spot_radius, {
                    'color': self.conv.line_color,
                    'width': self.conv.identity_line_width
                })

    def _predicate_periphery_point(self, predicate_primitive: SpatialPrimitive, toward: Tuple[float, float]) -> Tuple[float, float]:
        """Deprecated: use render_geometry.predicate_periphery_point. Kept for backward compatibility."""
        if predicate_primitive.bounds:
            return predicate_periphery_point(predicate_primitive.bounds, toward)
        return predicate_primitive.position

    def _segment_intersects_any_predicate(self, a: Tuple[float, float], b: Tuple[float, float],
                                          graph: RelationalGraphWithCuts,
                                          layout_result: LayoutResult) -> bool:
        """Return True if segment AB intersects any predicate text rectangle (with small padding)."""
        for edge_id in graph.nu.keys():
            pname = graph.rel.get(edge_id, edge_id)
            ppos = self._find_predicate_position(edge_id, layout_result)
            if not ppos:
                continue
            x1, y1, x2, y2 = self._calculate_predicate_bounds(pname, ppos)
            pad = 4.0
            rect = (x1 - pad, y1 - pad, x2 + pad, y2 + pad)
            if self._segment_intersects_rect(a, b, rect):
                return True
        return False
    
    def _build_cut_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[str, List[str]]:
        """Build hierarchical structure of cuts for proper nesting."""
        hierarchy = {}
        
        # Build parent -> children mapping
        for cut in graph.Cut:
            parent_area = self._find_cut_parent_area(cut.id, graph)
            if parent_area not in hierarchy:
                hierarchy[parent_area] = []
            hierarchy[parent_area].append(cut.id)
        
        return hierarchy
    
    def _find_cut_parent_area(self, cut_id: str, graph: RelationalGraphWithCuts) -> str:
        """Find the parent area that contains this cut."""
        for area_id, contents in graph.area.items():
            if cut_id in contents:
                return area_id
        return graph.sheet  # Default to sheet level
    
    def _find_vertex_predicates(self, vertex_id: str, graph: RelationalGraphWithCuts,
                               layout_result: LayoutResult) -> List[Dict]:
        """Find all predicates connected to a vertex with their positions."""
        connected = []
        
        for edge_id, vertex_sequence in graph.nu.items():
            if vertex_id in vertex_sequence:
                predicate_name = graph.rel.get(edge_id, edge_id)
                pred_position = self._find_predicate_position(edge_id, layout_result)
                
                if pred_position:
                    connected.append({
                        'edge_id': edge_id,
                        'name': predicate_name,
                        'position': pred_position,
                        'vertex_sequence': vertex_sequence,
                        'argument_index': vertex_sequence.index(vertex_id)
                    })
        
        return connected
    
    def _find_predicate_position(self, edge_id: str, layout_result: LayoutResult) -> Optional[Tuple[float, float]]:
        """Find predicate position from layout result."""
        # Look for predicate node created by Graphviz
        pred_node_id = f"pred_{edge_id}"
        if pred_node_id in layout_result.primitives:
            return layout_result.primitives[pred_node_id].position
        
        # Fallback: look for edge primitive
        if edge_id in layout_result.primitives:
            return layout_result.primitives[edge_id].position
        
        return None
    
    def _calculate_predicate_bounds(self, predicate_name: str, position: Tuple[float, float], 
                                   font_size: int = 12) -> Tuple[float, float, float, float]:
        """Calculate the bounding box of predicate text."""
        # Estimate text dimensions (this should use actual font metrics)
        char_width = font_size * 0.6  # Approximate character width
        char_height = font_size * 1.2  # Approximate character height
        
        text_width = len(predicate_name) * char_width
        text_height = char_height
        
        # Calculate bounds (x1, y1, x2, y2) with a small padding margin
        padding = 6.0
        x1 = position[0] - text_width / 2 - padding
        y1 = position[1] - text_height / 2 - padding
        x2 = position[0] + text_width / 2 + padding
        y2 = position[1] + text_height / 2 + padding
        
        return (x1, y1, x2, y2)

    def _point_in_rect(self, pt: Tuple[float, float], rect: Tuple[float, float, float, float]) -> bool:
        x, y = pt
        x1, y1, x2, y2 = rect
        return (x1 <= x <= x2) and (y1 <= y <= y2)

    def _nudge_point_outside_rect(self, pt: Tuple[float, float], rect: Tuple[float, float, float, float], margin: float = 6.0) -> Tuple[float, float]:
        """Move point to nearest outside position of rect with a small margin."""
        x, y = pt
        x1, y1, x2, y2 = rect
        # Distances to each side
        d_left = abs(x - x1)
        d_right = abs(x2 - x)
        d_top = abs(y - y1)
        d_bottom = abs(y2 - y)
        # Choose smallest push
        dmin = min(d_left, d_right, d_top, d_bottom)
        if dmin == d_left:
            return (x1 - margin, y)
        if dmin == d_right:
            return (x2 + margin, y)
        if dmin == d_top:
            return (x, y1 - margin)
        return (x, y2 + margin)

    def _ensure_vertex_in_area(self, vertex_id: str, pos: Tuple[float, float],
                               graph: RelationalGraphWithCuts,
                               layout_result: LayoutResult) -> Tuple[float, float]:
        """Clamp/display vertex spot inside its logical EGI area from the graph model.
        Uses `graph.get_area(vertex_id)` (vertex context), not LCA of predicates nor sheet preference.
        """
        x, y = pos
        # Use the vertex's assigned logical area
        target_area = graph.get_area(vertex_id)
        if target_area and target_area != graph.sheet and target_area in layout_result.primitives:
            bx1, by1, bx2, by2 = layout_result.primitives[target_area].bounds
            pad = 8.0
            nx = min(max(x, bx1 + pad), bx2 - pad)
            ny = min(max(y, by1 + pad), by2 - pad)
            return (nx, ny)
        # Sheet-level fallback: ensure not inside any cut
        for pid, prim in layout_result.primitives.items():
            if prim.element_type == 'cut' and prim.bounds:
                if self._point_in_rect((x, y), prim.bounds):
                    return self._nudge_point_outside_rect((x, y), prim.bounds)
        return (x, y)

    def _rect_contains(self, outer: Tuple[float, float, float, float], inner: Tuple[float, float, float, float]) -> bool:
        ox1, oy1, ox2, oy2 = outer
        ix1, iy1, ix2, iy2 = inner
        return ox1 <= ix1 and oy1 <= iy1 and ox2 >= ix2 and oy2 >= iy2

    # --- New helpers: area-safe finalization of vertex spots ---
    def _least_common_enclosing_cut_for_points(self, pts: List[Tuple[float, float]],
                                               layout_result: LayoutResult) -> Optional[str]:
        """Return the smallest cut id that contains all given points (ellipse check).
        If none found, return None.
        """
        candidates: List[Tuple[str, float]] = []
        for cid, prim in layout_result.primitives.items():
            if getattr(prim, 'element_type', None) != 'cut' or not prim.bounds:
                continue
            x1, y1, x2, y2 = prim.bounds
            cx, cy = (x1 + x2) * 0.5, (y1 + y2) * 0.5
            rx, ry = max((x2 - x1) * 0.5, 1.0), max((y2 - y1) * 0.5, 1.0)
            def inside(p: Tuple[float, float]) -> bool:
                nx, ny = (p[0] - cx) / rx, (p[1] - cy) / ry
                return (nx*nx + ny*ny) <= 1.0
            if all(inside(p) for p in pts):
                area = (x2 - x1) * (y2 - y1)
                candidates.append((cid, area))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[1])
        return candidates[0][0]

    def _finalize_spot_area(self, vertex_id: str, spot: Tuple[float, float], hooks: List[Tuple[float, float]],
                             graph: RelationalGraphWithCuts, layout_result: LayoutResult) -> Tuple[float, float]:
        """Ensure the final spot is inside an appropriate area.
        Priority:
        1) Vertex's own logical area from graph.get_area(vertex_id) if it is a cut.
        2) Otherwise, least common enclosing cut of the hook points.
        3) As last resort, keep within canvas bounds.
        Uses ellipse-aware binary search from area centroid toward the candidate spot.
        """
        vx, vy = spot
        area_id = None
        try:
            area_id = graph.get_area(vertex_id)
        except Exception:
            area_id = None
        # Normalize sheet-area sentinels (e.g., frozenset(), empty values) to None for primitive lookup
        if not isinstance(area_id, str) or not area_id:
            area_id = None
        # Prefer the vertex's area when it's a cut with bounds
        prim = layout_result.primitives.get(area_id) if (area_id and area_id in layout_result.primitives) else None
        if not prim or getattr(prim, 'element_type', None) != 'cut' or not getattr(prim, 'bounds', None):
            # Fallback: smallest cut containing all hooks
            lcec = self._least_common_enclosing_cut_for_points(hooks, layout_result) if hooks else None
            prim = layout_result.primitives.get(lcec) if (lcec and lcec in layout_result.primitives) else None

        if prim and prim.bounds:
            x1, y1, x2, y2 = prim.bounds
            cx, cy = (x1 + x2) * 0.5, (y1 + y2) * 0.5
            rx, ry = max((x2 - x1) * 0.5 - 2.0, 1.0), max((y2 - y1) * 0.5 - 2.0, 1.0)
            nx, ny = (vx - cx) / rx, (vy - cy) / ry
            if (nx*nx + ny*ny) <= 0.98:
                return (vx, vy)
            # Project inward using binary search from centroid to spot
            lo, hi = 0.0, 1.0
            best = (vx, vy)
            for _ in range(18):
                mid = (lo + hi) * 0.5
                mx, my = cx + (vx - cx) * mid, cy + (vy - cy) * mid
                nnx, nny = (mx - cx) / rx, (my - cy) / ry
                if (nnx*nnx + nny*nny) <= 0.98:
                    best = (mx, my)
                    lo = mid
                else:
                    hi = mid
            try:
                print(f"DEBUG: spot-finalize vertex={vertex_id} area={getattr(prim,'element_id','?')} from={spot} to={best}")
            except Exception:
                pass
            return best

        # Canvas fallback
        cb = layout_result.canvas_bounds
        pad = 4.0
        fx = min(max(vx, cb[0] + pad), cb[2] - pad)
        fy = min(max(vy, cb[1] + pad), cb[3] - pad)
        return (fx, fy)

    def _build_cut_hierarchy(self, layout_result: LayoutResult) -> Dict[str, Optional[str]]:
        """Derive parent mapping for cuts by bounds containment. Returns {cut_id: parent_cut_or_sheet}.
        The sheet is represented by None.
        """
        cuts = [(pid, prim.bounds) for pid, prim in layout_result.primitives.items()
                if prim.element_type == 'cut' and prim.bounds]
        parent: Dict[str, Optional[str]] = {}
        for cid, cb in cuts:
            parent[cid] = None
        # For each cut, find the smallest other cut that contains it
        for cid, cb in cuts:
            best_parent = None
            best_area = None
            for oid, ob in cuts:
                if oid == cid:
                    continue
                if self._rect_contains(ob, cb):
                    # Choose the tightest container (minimal area)
                    area = (ob[2] - ob[0]) * (ob[3] - ob[1])
                    if best_area is None or area < best_area:
                        best_parent, best_area = oid, area
            parent[cid] = best_parent
        return parent

    def _area_ancestors(self, area_id: Optional[str], parent: Dict[str, Optional[str]], sheet_id: str) -> List[Optional[str]]:
        """Return chain from area_id up to sheet (None), including area_id."""
        chain: List[Optional[str]] = []
        cur: Optional[str] = area_id
        visited = set()
        # guard cycles just in case
        while cur is not None and cur not in visited:
            visited.add(cur)
            chain.append(cur)
            cur = parent.get(cur)
        chain.append(None)  # sheet terminator
        return chain

    def _least_common_area(self, areas: List[str], parent: Dict[str, Optional[str]]) -> Optional[str]:
        """Compute LCA of a list of areas using parent map. Returns None for sheet.
        If areas is empty, return None.
        """
        if not areas:
            return None
        # Build ancestor sets for first area
        first = areas[0]
        anc = set(self._area_ancestors(first, parent, sheet_id=""))
        lca: Optional[str] = first if first in anc else None
        for a in areas[1:]:
            chain = self._area_ancestors(a, parent, sheet_id="")
            # intersect: find first common in order of first's chain
            for candidate in chain:
                if candidate in anc:
                    lca = candidate
                    break
            # tighten anc to ancestors of lca for next iterations
            if lca is not None:
                anc = set(self._area_ancestors(lca, parent, sheet_id=""))
            else:
                anc = {None}
        return lca

    def _least_common_area_for_vertex(self, vertex_id: str,
                                       graph: RelationalGraphWithCuts,
                                       layout_result: LayoutResult) -> Optional[str]:
        """Collect all predicate areas where this vertex appears and return their LCA.
        Falls back to the vertex's assigned area if no predicates are found.
        """
        # Collect areas from connected predicates (edges)
        areas: List[str] = []
        for edge_id, vertex_sequence in graph.nu.items():
            if vertex_id in vertex_sequence:
                area = graph.get_area(edge_id)
                if area is not None:
                    areas.append(area)
        if not areas:
            return graph.get_area(vertex_id)
        parent = self._build_cut_hierarchy(layout_result)
        return self._least_common_area(areas, parent)

    def _generate_hook_points(self, predicate_bounds: Tuple[float, float, float, float], n_args: int) -> List[Tuple[float, float]]:
        """Generate evenly distributed hook points around a padded text oval.
        Hooks are placed on the rectangle oval approximation; will later map to a true oval.
        """
        x1, y1, x2, y2 = predicate_bounds
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        rx, ry = (x2 - x1) / 2.0, (y2 - y1) / 2.0
        hooks = []
        # Place from angle 0..2π clockwise, starting at rightmost
        for i in range(max(1, n_args)):
            theta = 2 * math.pi * (i / max(1, n_args))
            hx = cx + rx * math.cos(theta)
            hy = cy + ry * math.sin(theta)
            hooks.append((hx, hy))
        return hooks

    def _segment_intersects_any_bounds(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                       layout_result: LayoutResult,
                                       exclude_ids: Optional[set] = None) -> bool:
        """Check if segment intersects any predicate/cut bounds."""
        if exclude_ids is None:
            exclude_ids = set()
        for pid, prim in layout_result.primitives.items():
            if pid in exclude_ids:
                continue
            if prim.element_type in ('predicate', 'cut'):
                bx1, by1, bx2, by2 = prim.bounds
                if self._segment_intersects_rect(p1, p2, (bx1, by1, bx2, by2)):
                    return True
        return False

    def _segment_intersects_rect(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                 rect: Tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = rect
        # Quick reject
        minx, maxx = min(p1[0], p2[0]), max(p1[0], p2[0])
        miny, maxy = min(p1[1], p2[1]), max(p1[1], p2[1])
        if maxx < x1 or minx > x2 or maxy < y1 or miny > y2:
            # still could intersect if crossing rectangle area; use full test via Cohen–Sutherland
            pass
        # Use Liang–Barsky style: if any intersection exists within segment, return True
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        p = [-dx, dx, -dy, dy]
        q = [p1[0] - x1, x2 - p1[0], p1[1] - y1, y2 - p1[1]]
        u1, u2 = 0.0, 1.0
        for pi, qi in zip(p, q):
            if pi == 0:
                if qi < 0:
                    return False
                continue
            t = qi / pi
            if pi < 0:
                u1 = max(u1, t)
            else:
                u2 = min(u2, t)
            if u1 > u2:
                return False
        # If clipping survives, segment overlaps rect
        return True

    def _point_inside_any_cut(self, pt: Tuple[float, float], layout_result: LayoutResult) -> bool:
        x, y = pt
        for pid, prim in layout_result.primitives.items():
            if prim.element_type == 'cut' and prim.bounds:
                x1, y1, x2, y2 = prim.bounds
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return True
        return False

    def _nearest_point_on_segment_outside_cuts(self, a: Tuple[float, float], b: Tuple[float, float],
                                               layout_result: LayoutResult, start_t: float = 0.5) -> Tuple[float, float]:
        """Find nearest point along segment AB that lies outside all cuts, starting near start_t.
        Sample both directions with increasing radius until a valid point is found.
        """
        ax, ay = a
        bx, by = b
        def point_at(t: float) -> Tuple[float, float]:
            return (ax + (bx - ax) * t, ay + (by - ay) * t)
        # clamp
        start_t = max(0.0, min(1.0, start_t))
        if not self._point_inside_any_cut(point_at(start_t), layout_result):
            return point_at(start_t)
        # Expand search
        step = 0.02
        for k in range(1, 51):  # up to ~1.0 range
            for sign in (+1, -1):
                t = start_t + sign * k * step
                if 0.0 <= t <= 1.0:
                    p = point_at(t)
                    if not self._point_inside_any_cut(p, layout_result):
                        return p
        # Fallback to nearest endpoint outside
        if not self._point_inside_any_cut(a, layout_result):
            return a
        if not self._point_inside_any_cut(b, layout_result):
            return b
        # As last resort, nudge midpoint outside nearest cut
        mid = point_at(0.5)
        for pid, prim in layout_result.primitives.items():
            if prim.element_type == 'cut' and prim.bounds and self._point_in_rect(mid, prim.bounds):
                return self._nudge_point_outside_rect(mid, prim.bounds)
        return mid

    def _default_toward_from_bounds(self, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """Fallback 'toward' point for predicate periphery when no vertex position exists.
        Chooses a point slightly above the predicate center (toward sheet).
        """
        x1, y1, x2, y2 = bounds
        cx, cy = (x1 + x2) * 0.5, (y1 + y2) * 0.5
        return (cx, y1 - 40.0)

    def _cut_depth_at_point(self, pt: Tuple[float, float], layout_result: LayoutResult) -> int:
        """Return the number of enclosing cuts for a point using ellipse containment.
        Cuts are rendered as ovals; we treat bounds as the ellipse box.
        Sheet depth is 0.
        """
        x, y = pt
        depth = 0
        for prim in layout_result.primitives.values():
            if prim.element_type == 'cut' and prim.bounds:
                x1, y1, x2, y2 = prim.bounds
                cx = (x1 + x2) * 0.5
                cy = (y1 + y2) * 0.5
                rx = max((x2 - x1) * 0.5, 1e-6)
                ry = max((y2 - y1) * 0.5, 1e-6)
                nx = (x - cx) / rx
                ny = (y - cy) / ry
                if (nx * nx + ny * ny) <= 1.0:
                    depth += 1
        return depth

    def _nearest_point_on_segment_with_depth(self,
                                             a: Tuple[float, float],
                                             b: Tuple[float, float],
                                             layout_result: LayoutResult,
                                             target_depth: int,
                                             start_t: float = 0.5) -> Tuple[float, float]:
        """Find a point along segment AB whose cut-depth matches target_depth.
        If none exists, return the closest along-segment point whose depth is nearest to target.
        """
        ax, ay = a
        bx, by = b
        def point_at(t: float) -> Tuple[float, float]:
            return (ax + (bx - ax) * t, ay + (by - ay) * t)
        # Quick check at midpoint first
        start_t = max(0.0, min(1.0, start_t))
        best_p = point_at(start_t)
        best_diff = abs(self._cut_depth_at_point(best_p, layout_result) - target_depth)
        if best_diff == 0:
            return best_p
        # Expand search symmetrically
        step = 0.02
        for k in range(1, 51):
            for sign in (+1, -1):
                t = start_t + sign * k * step
                if 0.0 <= t <= 1.0:
                    p = point_at(t)
                    d = abs(self._cut_depth_at_point(p, layout_result) - target_depth)
                    if d == 0:
                        return p
                    if d < best_diff:
                        best_p, best_diff = p, d
        return best_p

    def _curved_avoidance(self, start: Tuple[float, float], end: Tuple[float, float],
                           obstacle_center: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Return a gentle polyline (to be rendered as curve) that bows around an obstacle."""
        sx, sy = start
        ex, ey = end
        cx, cy = obstacle_center
        mx, my = (sx + ex) / 2.0, (sy + ey) / 2.0
        # Vector from obstacle to midpoint, normalized
        vx, vy = mx - cx, my - cy
        norm = math.hypot(vx, vy) or 1.0
        vx, vy = vx / norm, vy / norm
        # Offset control point away from obstacle
        offset = 20.0
        ctrl = (mx + vx * offset, my + vy * offset)
        return [start, ctrl, end]
    
    def _ensure_predicate_within_area(self, edge_id: str, predicate_bounds: Tuple[float, float, float, float],
                                     graph: RelationalGraphWithCuts, layout_result: LayoutResult,
                                     margin: float = 5.0) -> Tuple[float, float]:
        """Ensure predicate stays within its designated area (cut or sheet) boundaries."""
        pred_x1, pred_y1, pred_x2, pred_y2 = predicate_bounds
        
        # Find which area this predicate belongs to
        predicate_area = graph.get_area(edge_id)
        
        # Get area bounds
        if predicate_area != graph.sheet and predicate_area in layout_result.primitives:
            # Predicate is inside a cut - enforce cut boundaries
            cut_primitive = layout_result.primitives[predicate_area]
            cut_bounds = cut_primitive.bounds
            
            # Adjust position to stay within cut boundaries
            return self._adjust_position_within_bounds(predicate_bounds, cut_bounds, margin)
        else:
            # Predicate is on sheet - use original position (no cut constraints)
            return ((pred_x1 + pred_x2) / 2, (pred_y1 + pred_y2) / 2)
    
    def _adjust_position_within_bounds(self, item_bounds: Tuple[float, float, float, float],
                                      container_bounds: Tuple[float, float, float, float],
                                      margin: float) -> Tuple[float, float]:
        """Adjust item position to ensure it stays within container boundaries."""
        item_x1, item_y1, item_x2, item_y2 = item_bounds
        container_x1, container_y1, container_x2, container_y2 = container_bounds
        
        # Calculate current center
        center_x = (item_x1 + item_x2) / 2
        center_y = (item_y1 + item_y2) / 2
        
        # Calculate item dimensions
        item_width = item_x2 - item_x1
        item_height = item_y2 - item_y1
        
        # Adjust if item extends beyond container boundaries
        if item_x1 < container_x1 + margin:
            center_x = container_x1 + margin + item_width / 2
        elif item_x2 > container_x2 - margin:
            center_x = container_x2 - margin - item_width / 2
            
        if item_y1 < container_y1 + margin:
            center_y = container_y1 + margin + item_height / 2
        elif item_y2 > container_y2 - margin:
            center_y = container_y2 - margin - item_height / 2
        
        return (center_x, center_y)
    
    def _calculate_line_connection_point(self, predicate_bounds: Tuple[float, float, float, float],
                                        vertex_position: Tuple[float, float],
                                        margin: float = 3.0) -> Tuple[float, float]:
        """Calculate the exact intersection of the vertex→predicate-center ray with the
        predicate's padded boundary, leaving a small collision margin."""
        pred_x1, pred_y1, pred_x2, pred_y2 = predicate_bounds
        vx, vy = vertex_position
        cx = (pred_x1 + pred_x2) / 2.0
        cy = (pred_y1 + pred_y2) / 2.0
        
        # Expand rectangle slightly to get a consistent visual gap
        rx1, ry1, rx2, ry2 = pred_x1 - margin, pred_y1 - margin, pred_x2 + margin, pred_y2 + margin
        
        # Liang–Barsky clipping to find first intersection of segment (v->c) with rect
        dx = cx - vx
        dy = cy - vy
        p = [-dx, dx, -dy, dy]
        q = [vx - rx1, rx2 - vx, vy - ry1, ry2 - vy]
        u1, u2 = 0.0, 1.0
        for pi, qi in zip(p, q):
            if pi == 0:
                if qi < 0:
                    # Parallel and outside — no intersection; fall back to closest point on rect center line
                    return (max(min(cx, rx2), rx1), max(min(cy, ry2), ry1))
                else:
                    continue
            t = qi / pi
            if pi < 0:
                if t > u2:
                    return (cx, cy)
                u1 = max(u1, t)
            else:
                if t < u1:
                    return (cx, cy)
                u2 = min(u2, t)
        # Intersection point at u1 along (v->c)
        ix = vx + u1 * dx
        iy = vy + u1 * dy
        return (ix, iy)
    
    def _draw_identity_line_to_predicate(self, canvas: PySide6Canvas, vertex_pos: Tuple[float, float],
                                        pred_info: Dict, line_index: int, total_lines: int) -> None:
        """Draw a heavy line of identity from vertex to predicate.
        
        CRITICAL: Line must pass through cuts to reach predicates inside cuts,
        as per Dau's formalism where lines of identity can cross cut boundaries.
        """
        pred_pos = pred_info['position']
        
        # Calculate line direction
        dx = pred_pos[0] - vertex_pos[0]
        dy = pred_pos[1] - vertex_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance == 0:
            return  # Skip zero-length lines
        
        # Apply angular separation for multiple lines
        if total_lines > 1:
            base_angle = math.atan2(dy, dx)
            separation = math.pi / 8  # 22.5 degrees
            angle_offset = (line_index - (total_lines - 1) / 2) * separation
            final_angle = base_angle + angle_offset
            
            # FIXED: Line extends ALL THE WAY to predicate (passes through cuts)
            line_length = distance * 0.9  # Almost to predicate (leave small gap for hook)
            end_pos = (
                vertex_pos[0] + math.cos(final_angle) * line_length,
                vertex_pos[1] + math.sin(final_angle) * line_length
            )
        else:
            # FIXED: Single line extends ALL THE WAY to predicate (passes through cuts)
            line_length = distance * 0.9  # Almost to predicate (leave small gap for hook)
            end_pos = (
                vertex_pos[0] + dx * 0.9,
                vertex_pos[1] + dy * 0.9
            )
        
        # Determine hook point for this argument (distribute evenly)
        predicate_name = pred_info['name']
        arg_idx = pred_info.get('argument_index', 0)
        n_args = len(pred_info.get('vertex_sequence', []))
        pred_bounds = self._calculate_predicate_bounds(predicate_name, pred_info['position'])
        hooks = self._generate_hook_points(pred_bounds, max(1, n_args))
        # Choose hook closest in direction to vertex
        vx, vy = vertex_pos
        cx = (pred_bounds[0] + pred_bounds[2]) / 2.0
        cy = (pred_bounds[1] + pred_bounds[3]) / 2.0
        # Prefer arg_idx but allow fallback to nearest free hook
        preferred = hooks[arg_idx % len(hooks)]
        chosen = preferred
        # If straight segment intersects predicate bounds (text) or other obstacles, keep chosen; we will curve
        # Compute final endpoint with tiny margin using periphery intersection toward center
        endpoint = self._calculate_line_connection_point(pred_bounds, vertex_pos, margin=4.0)
        
        # Draw heavy line: straight if collision-free, otherwise a gentle curve around the predicate
        # Exclude the target predicate primitive id from collision tests
        exclude = {f"pred_{pred_info.get('edge_id', '')}", pred_info.get('edge_id', '')}
        if not self._segment_intersects_any_bounds(vertex_pos, endpoint, layout_result=self.current_layout,
                                                   exclude_ids=exclude):
            canvas.draw_line(
                vertex_pos, endpoint,
                {
                    'color': self.conv.line_color,
                    'width': self.conv.identity_line_width
                }
            )
        else:
            curve_pts = self._curved_avoidance(vertex_pos, endpoint, (cx, cy))
            canvas.draw_curve(
                curve_pts,
                {
                    'color': self.conv.line_color,
                    'width': self.conv.identity_line_width
                },
                closed=False
            )

    def _compute_fit_transform(self, canvas: PySide6Canvas, layout_result: LayoutResult,
                               margin: float = 40.0) -> Tuple[float, float, float]:
        """Compute scale and offsets to fit the diagram within the canvas with margins."""
        if not layout_result.primitives:
            return (1.0, 0.0, 0.0)
        all_bounds = [p.bounds for p in layout_result.primitives.values() if hasattr(p, 'bounds')]
        if not all_bounds:
            return (1.0, 0.0, 0.0)
        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)
        diagram_w = max(1.0, max_x - min_x)
        diagram_h = max(1.0, max_y - min_y)
        scale_x = (canvas.width - 2 * margin) / diagram_w
        scale_y = (canvas.height - 2 * margin) / diagram_h
        scale = max(0.1, min(scale_x, scale_y))
        # Compute offset to center after scaling
        offset_x = (canvas.width - diagram_w * scale) / 2 - min_x * scale
        offset_y = (canvas.height - diagram_h * scale) / 2 - min_y * scale
        return (scale, offset_x, offset_y)

    def _apply_transform(self, layout_result: LayoutResult, scale: float,
                          offset_x: float, offset_y: float) -> LayoutResult:
        """Apply scale and translation to all primitives."""
        # No Y-flip: assume layout coordinates are already suitable for screen rendering
        # Only apply uniform scale and translation to fit the canvas

        transformed = {}
        for prim_id, primitive in layout_result.primitives.items():
            px, py = primitive.position
            bx1, by1, bx2, by2 = primitive.bounds
            # Direct scale + translate (no axis flip)
            new_position = (px * scale + offset_x, py * scale + offset_y)
            nbx1 = bx1 * scale + offset_x
            nby1 = by1 * scale + offset_y
            nbx2 = bx2 * scale + offset_x
            nby2 = by2 * scale + offset_y
            # Normalize bounds to ensure min<=max on both axes
            x1n, x2n = (nbx1, nbx2) if nbx1 <= nbx2 else (nbx2, nbx1)
            y1n, y2n = (nby1, nby2) if nby1 <= nby2 else (nby2, nby1)
            if (nbx1 > nbx2) or (nby1 > nby2):
                # Debug log once per primitive if normalization occurred
                try:
                    print(f"ℹ️  Normalized bounds for {prim_id}: ({nbx1}, {nby1}, {nbx2}, {nby2}) -> ({x1n}, {y1n}, {x2n}, {y2n})")
                except Exception:
                    pass
            new_bounds = (x1n, y1n, x2n, y2n)
            transformed[prim_id] = SpatialPrimitive(
                element_id=primitive.element_id,
                element_type=primitive.element_type,
                position=new_position,
                bounds=new_bounds,
                z_index=primitive.z_index
            )
        # No post-transform clamping or de-overlap: draw exactly what layout provides (scaled/translated)

        return LayoutResult(
            primitives=transformed,
            canvas_bounds=layout_result.canvas_bounds,
            containment_hierarchy=layout_result.containment_hierarchy
        )
    
    def _render_argument_order_labels(self, canvas: PySide6Canvas, pred_position: Tuple[float, float],
                                    vertex_sequence: List[str], graph: RelationalGraphWithCuts,
                                    layout_result: LayoutResult, pred_bounds: Tuple[float, float, float, float]) -> None:
        """Render argument order numbers near the predicate periphery hook points."""
        x1, y1, x2, y2 = pred_bounds
        for i, vertex_id in enumerate(vertex_sequence):
            sprim = layout_result.primitives.get(vertex_id)
            # Prefer current display position to avoid ambiguity
            vpos = self._vertex_display_pos.get(vertex_id, sprim.position if sprim else pred_position)
            # Periphery hook toward the vertex
            hook = predicate_periphery_point(pred_bounds, vpos)
            hx, hy = hook
            # Determine side and push slightly outward
            out = 6.0
            if abs(hx - x1) < 1e-3:
                label_pos = (hx - out, hy)
            elif abs(hx - x2) < 1e-3:
                label_pos = (hx + out, hy)
            elif abs(hy - y1) < 1e-3:
                label_pos = (hx, hy - out)
            else:  # bottom side
                label_pos = (hx, hy + out)
            canvas.draw_text(
                str(i + 1),
                label_pos,
                {
                    'color': self.conv.text_color,
                    'font_size': 9,
                    'bold': True
                }
            )
    
    def _render_predicate_hooks(self, canvas: PySide6Canvas, pred_position: Tuple[float, float],
                              vertex_sequence: List[str], graph: RelationalGraphWithCuts,
                              layout_result: LayoutResult) -> None:
        """Handle predicate attachment to identity lines.
        
        NOTE: In Dau's formalism, hooks are conceptual attachment points, not visible lines.
        The attachment is invisible but functional - predicates and lines move together.
        This method is kept for future interactive functionality but renders nothing visually.
        """
        # Hooks are invisible attachment points in Dau's formalism
        # The conceptual attachment is handled by the layout engine positioning
        # No visual rendering needed - predicates are positioned near line endpoints
        pass
    
    def _calculate_centering_offset(self, canvas: PySide6Canvas, layout_result: LayoutResult) -> Tuple[float, float]:
        """Calculate offset to center the diagram in the viewport."""
        if not layout_result.primitives:
            return (0, 0)
        
        # Find bounding box of all elements
        all_bounds = [p.bounds for p in layout_result.primitives.values() if hasattr(p, 'bounds')]
        if not all_bounds:
            return (0, 0)
        
        min_x = min(bounds[0] for bounds in all_bounds)
        min_y = min(bounds[1] for bounds in all_bounds)
        max_x = max(bounds[2] for bounds in all_bounds)
        max_y = max(bounds[3] for bounds in all_bounds)
        
        # Calculate diagram dimensions
        diagram_width = max_x - min_x
        diagram_height = max_y - min_y
        
        # Calculate canvas dimensions (assume standard size)
        canvas_width = canvas.width
        canvas_height = canvas.height
        
        # Calculate centering offset with title space
        title_space = 80  # Space for title and metadata
        offset_x = (canvas_width - diagram_width) / 2 - min_x
        offset_y = (canvas_height - diagram_height) / 2 - min_y + title_space
        
        return (offset_x, offset_y)
    
    def _apply_centering_offset(self, layout_result: LayoutResult, offset_x: float, offset_y: float) -> LayoutResult:
        """Apply centering offset to all primitives in the layout."""
        centered_primitives = {}
        
        for prim_id, primitive in layout_result.primitives.items():
            # Create new primitive with offset position and bounds
            new_position = (primitive.position[0] + offset_x, primitive.position[1] + offset_y)
            new_bounds = (
                primitive.bounds[0] + offset_x,
                primitive.bounds[1] + offset_y,
                primitive.bounds[2] + offset_x,
                primitive.bounds[3] + offset_y
            )
            
            centered_primitive = SpatialPrimitive(
                element_id=primitive.element_id,
                element_type=primitive.element_type,
                position=new_position,
                bounds=new_bounds,
                z_index=primitive.z_index
            )
            centered_primitives[prim_id] = centered_primitive
        
        return LayoutResult(
            primitives=centered_primitives,
            canvas_bounds=layout_result.canvas_bounds,
            containment_hierarchy=layout_result.containment_hierarchy
        )
    
    def _render_diagram_title(self, canvas: PySide6Canvas, graph: RelationalGraphWithCuts) -> None:
        """Add diagram title and structural information."""
        canvas.draw_text(
            "Existential Graph (Peirce/Dau Formalism)",
            (10, 20),
            {
                'color': self.conv.text_color,
                'font_size': 14,
                'bold': True
            }
        )
        
        # Structural summary
        vertices = len(graph._vertex_map)
        predicates = len(graph.nu)
        cuts = len(graph.Cut)
        
        canvas.draw_text(
            f"Structure: {vertices} vertices, {predicates} predicates, {cuts} cuts",
            (10, 40),
            {
                'color': (100, 100, 100),
                'font_size': 10
            }
        )


# Factory function
def create_dau_diagram_renderer(conventions: VisualConvention = None) -> DiagramRendererDau:
    """Create a DiagramRenderer with Peirce/Dau conventions."""
    return DiagramRendererDau(conventions)


if __name__ == "__main__":
    # Test the DiagramRenderer with proper architecture
    from egif_parser_dau import parse_egif
    from graphviz_layout_engine_v2 import create_graphviz_layout
    from pyside6_canvas import create_qt_canvas
    
    print("🎨 Testing DiagramRenderer (Peirce/Dau Formalism)")
    
    # Test case with clear EG structure
    test_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print(f"📝 Test EGIF: {test_egif}")
    
    try:
        # Step 1: Parse EGIF to EGI
        graph = parse_egif(test_egif)
        print(f"✅ EGI parsed: {len(graph._vertex_map)} vertices, {len(graph.nu)} predicates, {len(graph.Cut)} cuts")
        
        # Step 2: Generate layout coordinates with Graphviz
        layout_result = create_graphviz_layout(graph)
        print(f"✅ Layout generated: {len(layout_result.primitives)} spatial primitives")
        
        # Step 3: Create canvas and DiagramRenderer
        canvas = create_qt_canvas(800, 600, "DiagramRenderer Test - Peirce/Dau Formalism")
        renderer = create_dau_diagram_renderer()
        
        # Step 4: Render proper EG diagram
        renderer.render_diagram(canvas, graph, layout_result)
        print("✅ EG diagram rendered with Peirce/Dau conventions")
        
        # Step 5: Display result
        canvas.show()
        print("🖼️  Window displayed - should show proper EG with:")
        print("   • Heavy lines of identity connecting vertices to predicates")
        print("   • Fine-drawn cut oval containing negated content")
        print("   • Identity spots at vertex centers")
        print("   • Proper predicate attachment with hooks")
        print("   • Constant labels positioned correctly")
        
        canvas.app.exec()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
