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
from pyside6_canvas import PySide6Canvas


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
        # Process cuts in hierarchical order (outermost first)
        cut_hierarchy = self._build_cut_hierarchy(graph)
        
        for cut in graph.Cut:
            if cut.id in layout_result.primitives:
                cut_primitive = layout_result.primitives[cut.id]
                
                # Determine cut boundaries from layout
                bounds = cut_primitive.bounds
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                
                # Render as fine-drawn closed curve (oval)
                canvas.draw_oval(
                    bounds[0], bounds[1], bounds[2], bounds[3],
                    {
                        'color': self.conv.cut_color,
                        'width': self.conv.cut_line_width,  # FIXED: API mismatch
                        'fill_color': None  # No fill - just the curve
                    }
                )
                
                # Add cut label (optional, for debugging)
                canvas.draw_text(
                    f"Cut {cut.id[:6]}",
                    (center_x, bounds[1] - 10),
                    {
                        'color': (100, 100, 100),
                        'font_size': 8
                    }
                )
    
    def _render_ligatures_and_identity_lines(self, canvas: PySide6Canvas, 
                                           graph: RelationalGraphWithCuts,
                                           layout_result: LayoutResult) -> None:
        """
        Draw ligatures and lines of identity as bold, continuous lines.
        
        Must handle branches, junctions, and connections to predicates correctly.
        """
        # For each vertex, draw a single ligature consistent with its degree
        for vertex_id, vertex in graph._vertex_map.items():
            if vertex_id not in layout_result.primitives:
                continue

            vprim = layout_result.primitives[vertex_id]
            vertex_pos = self._vertex_display_pos.get(vertex_id, vprim.position)

            # Collect predicate primitives attached to this vertex via nu, with multiplicity
            attached_predicates: List[SpatialPrimitive] = []
            for edge_id, seq in graph.nu.items():
                # Count how many times this vertex participates in the predicate's ν sequence
                multiplicity = sum(1 for v in seq if v == vertex_id)
                if multiplicity > 0:
                    pprim = layout_result.primitives.get(edge_id)
                    # Accept either predicate node primitive (canonical) or edge primitive (fallback)
                    if pprim and pprim.element_type in ('predicate', 'edge'):
                        # Append once per occurrence to create multiple hooks (e.g., reflexive)
                        attached_predicates.extend([pprim] * multiplicity)

            if not attached_predicates:
                continue

            # Compute periphery hook points on predicates
            hooks: List[Tuple[float, float]] = []
            if len(attached_predicates) == 2 and all(p.bounds for p in attached_predicates):
                p1, p2 = attached_predicates
                b1, b2 = p1.bounds, p2.bounds  # type: ignore
                c1 = ((b1[0] + b1[2]) * 0.5, (b1[1] + b1[3]) * 0.5)  # type: ignore
                c2 = ((b2[0] + b2[2]) * 0.5, (b2[1] + b2[3]) * 0.5)  # type: ignore

                if b1 == b2:
                    # Reflexive case: same predicate twice. Place two distinct hooks on the
                    # periphery along the side facing the vertex to avoid collapse.
                    x1, y1, x2, y2 = b1  # type: ignore
                    # Nearest point on periphery toward the vertex position
                    hv = predicate_periphery_point(b1, vertex_pos)
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
                    # For binary with distinct predicates: aim each hook toward the other predicate's center
                    h1 = predicate_periphery_point(b1, c2)  # type: ignore
                    h2 = predicate_periphery_point(b2, c1)  # type: ignore
                    # Inset hooks slightly toward predicate centers to keep lines inside cuts
                    inset = 4.0
                    def inset_point(h, c):
                        hx, hy = h
                        cx, cy = c
                        dx, dy = cx - hx, cy - hy
                        mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                        return (hx + dx / mag * inset, hy + dy / mag * inset)
                    hooks = [inset_point(h1, c1), inset_point(h2, c2)]
            else:
                for pprim in attached_predicates:
                    # Delegate to shared geometry helper for consistency across renderers/exporters
                    if pprim.bounds:
                        h = predicate_periphery_point(pprim.bounds, vertex_pos)
                        # Inset slightly toward predicate center
                        bx1, by1, bx2, by2 = pprim.bounds
                        pc = ((bx1 + bx2) * 0.5, (by1 + by2) * 0.5)
                        inset = 4.0
                        hx, hy = h
                        dx, dy = pc[0] - hx, pc[1] - hy
                        mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                        hooks.append((hx + dx / mag * inset, hy + dy / mag * inset))
                    else:
                        hooks.append(pprim.position)

            # Drawing style
            style = {
                'color': self.conv.line_color,
                'width': self.conv.identity_line_width
            }

            deg = len(hooks)
            if deg == 1:
                # Free endpoint: extend slightly from the predicate, but keep compact
                hx, hy = hooks[0]
                vx, vy = vertex_pos
                dx, dy = vx - hx, vy - hy
                mag = max((dx*dx + dy*dy) ** 0.5, 1e-6)
                ux, uy = dx / mag, dy / mag
                # Shorter free length to avoid overly long tails
                free_len = 14.0
                free_pt = (hx + ux * free_len, hy + uy * free_len)
                canvas.draw_line((hx, hy), free_pt, style)
                # Override displayed vertex position (do not mutate primitive)
                self._vertex_display_pos[vertex_id] = free_pt
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
                    self._vertex_display_pos[vertex_id] = (mx, my)
                else:
                    canvas.draw_line(h1, h2, style)
                    # Place the vertex spot on the ligature (midpoint of the segment)
                    mx = (h1[0] + h2[0]) * 0.5
                    my = (h1[1] + h2[1]) * 0.5
                    self._vertex_display_pos[vertex_id] = (mx, my)
            else:
                # Branching from junction at vertex position to each hook
                for hp in hooks:
                    canvas.draw_line(vertex_pos, hp, style)
    
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
            if vertex_id not in layout_result.primitives:
                continue

            vprim = layout_result.primitives[vertex_id]
            # Use display override if present (placed on ligature), else layout position
            vertex_pos = self._vertex_display_pos.get(vertex_id, vprim.position)

            # If constant label exists, draw the label; otherwise draw the identity spot
            if vertex.label:
                label_offset = (12.0, -12.0)
                label_pos = (vertex_pos[0] + label_offset[0], vertex_pos[1] + label_offset[1])
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
        transformed = {}
        for prim_id, primitive in layout_result.primitives.items():
            px, py = primitive.position
            bx1, by1, bx2, by2 = primitive.bounds
            new_position = (px * scale + offset_x, py * scale + offset_y)
            new_bounds = (
                bx1 * scale + offset_x,
                by1 * scale + offset_y,
                bx2 * scale + offset_x,
                by2 * scale + offset_y,
            )
            transformed[prim_id] = SpatialPrimitive(
                element_id=primitive.element_id,
                element_type=primitive.element_type,
                position=new_position,
                bounds=new_bounds,
                z_index=primitive.z_index
            )
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
            if not sprim:
                continue
            vpos = sprim.position
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
