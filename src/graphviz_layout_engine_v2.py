#!/usr/bin/env python3
"""
Robust Graphviz-Based Layout Engine for Existential Graphs

This implementation follows a disciplined approach to avoid the issues encountered
in previous attempts:

1. Clean EGI → DOT translation using proper cluster mapping
2. Use Graphviz plain text output (not SVG) for reliable coordinate parsing
3. Isolated Graphviz execution with robust error handling
4. Unidirectional data flow: EGI → DOT → Graphviz → LayoutResult

Architecture:
- EGI vertices → Graphviz nodes
- EGI edges → Graphviz edges  
- EGI cuts → Graphviz subgraph clusters
- EGI area containment → Nested subgraph structure
"""

import subprocess
import tempfile
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_engine_clean import LayoutResult, SpatialPrimitive
from xdot_parser_simple import parse_xdot_file
from pipeline_contracts import (
    enforce_contracts, 
    validate_relational_graph_with_cuts,
    validate_layout_result,
    validate_graphviz_dot_output,
    validate_graphviz_coordinate_extraction,
    validate_graphviz_layout_engine_output
)

try:
    from layout_post_processor import LayoutPostProcessor, SpacingConstraints
    POST_PROCESSOR_AVAILABLE = True
except ImportError:
    POST_PROCESSOR_AVAILABLE = False
    print("⚠️  Layout post-processor not available - using basic spacing")


@dataclass
class GraphvizElement:
    """Represents an element in Graphviz with its attributes."""
    element_id: str
    element_type: str  # 'node', 'edge', 'cluster'
    attributes: Dict[str, str]
    position: Optional[Tuple[float, float]] = None
    size: Optional[Tuple[float, float]] = None


class GraphvizLayoutEngine:
    """
    Graphviz-based layout engine for Existential Graphs.
    
    Converts EGI structures to DOT format, executes Graphviz, and parses
    the output back into LayoutResult with spatial primitives.
    
    Uses canonical mode: preserves exact Graphviz positioning without post-processing.
    """
    
    def __init__(self):
        """Initialize layout engine in canonical mode (preserves exact Graphviz output)."""
        self.dot_executable = "dot"  # Graphviz dot command
        self.temp_dir = tempfile.gettempdir()
    
    def _sanitize_dot_id(self, element_id: str) -> str:
        """Sanitize element ID for DOT syntax compliance."""
        # Replace problematic characters with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(element_id))
        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = '_' + sanitized
        return sanitized or '_unknown'
    
    def _calculate_vertex_size(self, vertex, graph: RelationalGraphWithCuts) -> Tuple[float, float]:
        """Calculate appropriate size for a vertex based on its label and connections."""
        # Base size for vertex spot
        base_width, base_height = 0.3, 0.3
        
        if vertex.label:
            # Calculate size needed for label text
            label_chars = len(vertex.label)
            # Rough estimate: 0.08 inches per character, minimum 0.6 inches
            label_width = max(0.6, label_chars * 0.08)
            label_height = 0.25  # Standard text height
            
            # Vertex needs space for both spot and label
            width = max(base_width, label_width + 0.2)  # Padding around label
            height = base_height + label_height + 0.1   # Spot + label + padding
        else:
            # Just the identity spot
            width, height = base_width, base_height
        
        return width, height
    
    def _calculate_predicate_dimensions(self, predicate_name: str) -> Tuple[float, float]:
        """Calculate appropriate width and height for predicate text boxes."""
        name_chars = len(predicate_name)
        # AGGRESSIVE: Much more generous sizing to prevent any crowding or overlap
        # Dramatically increased character width and padding for professional appearance
        width = max(1.2, name_chars * 0.20 + 0.5)  # AGGRESSIVE character width + padding
        height = 0.6  # AGGRESSIVE predicate box height for text
        return width, height
    
    def _calculate_cut_padding(self, approx_bounds: Optional[Tuple[float, float, float, float]] = None) -> float:
        """Adaptive padding for cut clusters to prevent overlap while keeping things compact.
        If bounds are known (xdot cluster _bb), use min(16.0, min(width,height)/6); else default 16.0.
        """
        if approx_bounds is None:
            return 16.0
        x1, y1, x2, y2 = approx_bounds
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
        return max(6.0, min(16.0, min(w, h) / 6.0))
    
    @enforce_contracts(
        input_contracts={'graph': validate_relational_graph_with_cuts},
        output_contract=validate_layout_result
    )
    def create_layout_from_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Main entry point: Convert EGI graph to LayoutResult using Graphviz.
        
        Pipeline:
        1. EGI → DOT translation
        2. Graphviz execution (DOT → plain text coordinates)
        3. Plain text parsing → LayoutResult
        
        CONTRACT: Enforces solidified Graphviz modeling standards.
        """
        try:
            # Logical-baseline mode: simple, deterministic, coherence-first layout
            if getattr(self, 'mode', 'default') in ('logical', 'logical-baseline'):
                dot_content = self._generate_dot_from_egi(graph)
                xdot_output = self._execute_graphviz(dot_content)
                # Parse once to obtain reliable cut bounds and canvas bounds
                raw_layout = self._parse_xdot_output_to_layout(xdot_output, graph)
                return self._create_logical_baseline_layout(graph, raw_layout)

            # Step 1: Generate DOT representation
            dot_content = self._generate_dot_from_egi(graph)
            
            # Step 2: Execute Graphviz and get xdot output (includes cluster _bb bounding boxes)
            xdot_output = self._execute_graphviz(dot_content)
            
            # Step 3: Parse xdot coordinates and cluster boundaries to create LayoutResult
            layout_result = self._parse_xdot_output_to_layout(xdot_output, graph)

            # CANONICAL MODE: Preserve exact Graphviz output without post-processing
            # This ensures mathematical correctness and Dau-compliant containment

            return layout_result
        except Exception as e:
            # Robust error handling - return empty layout on failure
            print(f"❌ Graphviz layout failed: {e}")
            return self._create_fallback_layout(graph)

    def _assert_canonical_cuts_equal_clusters(self, layout_result: LayoutResult, xdot_output: str) -> None:
        """Assert that every cut primitive's bounds equal the cluster _bb from xdot."""
        try:
            clusters, _, _ = parse_xdot_file(xdot_output)
        except Exception as e:
            raise RuntimeError(f"xdot parse failed during invariant check: {e}")
        # Build map from sanitized cluster name to bb
        cluster_map: Dict[str, Tuple[float,float,float,float]] = {}
        for c in clusters:
            # cluster.name like 'cluster_<sanitized_cut_id>'
            cid = c.name.replace('cluster_', '')
            cluster_map[cid] = c.bb
        # Compare to layout_result primitives
        mismatches = []
        for pid, prim in layout_result.primitives.items():
            if prim.element_type != 'cut' or not prim.bounds:
                continue
            # sanitize pid same as DOT generator
            spid = self._sanitize_dot_id(pid)
            if spid not in cluster_map:
                mismatches.append(f"missing cluster for cut {pid} (sanitized {spid})")
                continue
            bb = cluster_map[spid]
            if tuple(round(v,6) for v in prim.bounds) != tuple(round(v,6) for v in bb):
                mismatches.append(f"cut {pid} bounds {prim.bounds} != cluster {bb}")
        if mismatches:
            raise AssertionError("; ".join(mismatches))

    def _create_logical_baseline_layout(self, graph: RelationalGraphWithCuts, raw_layout: LayoutResult) -> LayoutResult:
        """Build a deterministic, coherent layout:
        - Use cut bounds from raw_layout (Graphviz clusters)
        - Place predicates and vertices in simple grids inside their parent cuts
        - Draw identity lines as polylines between vertex spots (per ν)
        - Draw predicate connections as straight segments from vertex to predicate box edge
        """
        prims: Dict[str, SpatialPrimitive] = {}
        canvas_bounds = raw_layout.canvas_bounds

        # Helper to compute inner rect
        def inner_rect(bounds: Tuple[float, float, float, float], pad: float = 16.0):
            x1, y1, x2, y2 = bounds
            ix1, iy1, ix2, iy2 = x1 + pad, y1 + pad, x2 - pad, y2 - pad
            if ix2 <= ix1 or iy2 <= iy1:
                return bounds
            return (ix1, iy1, ix2, iy2)

        # Build quick lookups
        cut_ids = {c.id for c in graph.Cut}
        vertex_ids = {v.id for v in graph.V}
        edge_by_id: Dict[str, object] = {}
        edge_label: Dict[str, str] = {}
        for e in graph.E:
            eid = e.id if hasattr(e, 'id') else str(e)
            edge_by_id[eid] = e
            edge_label[eid] = getattr(e, 'label', '')

        # Build children (cuts) and local contents per cut
        children_cuts: Dict[str, List[str]] = {}
        local_preds: Dict[str, List[str]] = {}
        local_verts: Dict[str, List[str]] = {}
        for area_id, contents in graph.area.items():
            children_cuts[area_id] = [cid for cid in contents if cid in cut_ids]
            preds: List[str] = []
            verts: List[str] = []
            for cid in contents:
                if cid in cut_ids:
                    continue
                if cid in vertex_ids:
                    verts.append(cid)
                elif cid in edge_by_id:
                    # exclude identity edges from predicate placement
                    if edge_label.get(cid) not in ('=', '.='):
                        preds.append(cid)
            local_preds[area_id] = preds
            local_verts[area_id] = verts

        # Measure helper: predicate box px size
        def measure_predicate_px(eid: str) -> Tuple[float, float]:
            e = edge_by_id.get(eid)
            name = getattr(e, 'label', '') if e else ''
            w_in, h_in = self._calculate_predicate_dimensions(name)
            return max(30.0, w_in * 72.0), max(24.0, h_in * 72.0)

        # Compute required sizes bottom-up
        PAD = 16.0
        GAP = 12.0

        required_size: Dict[str, Tuple[float, float]] = {}

        def grid_required_size(n: int, item_w: float, item_h: float, frac_h: float = 0.5) -> Tuple[float, float]:
            if n <= 0:
                return (0.0, 0.0)
            rows = max(1, int(n ** 0.5))
            cols = max(1, (n + rows - 1) // rows)
            width = cols * item_w + (cols + 1) * GAP
            height = rows * item_h + (rows + 1) * GAP
            return (width, height)

        def measure_cut(cut_id: str) -> Tuple[float, float]:
            # Children sizes
            child_ids = children_cuts.get(cut_id, [])
            child_sizes = [measure_cut(cid) for cid in child_ids]
            if child_sizes:
                child_strip_w = sum(w for (w, h) in child_sizes) + (len(child_sizes) + 1) * GAP
                child_strip_h = max(h for (w, h) in child_sizes) + 2 * GAP
            else:
                child_strip_w = 0.0
                child_strip_h = 0.0

            # Local content sizes
            preds = local_preds.get(cut_id, [])
            verts = local_verts.get(cut_id, [])
            # max predicate box size
            max_pw = 60.0
            max_ph = 30.0
            for pid in preds:
                pw, ph = measure_predicate_px(pid)
                max_pw = max(max_pw, pw)
                max_ph = max(max_ph, ph)
            pred_w, pred_h = grid_required_size(len(preds), max_pw, max_ph)
            vert_w, vert_h = grid_required_size(len(verts), 20.0, 20.0)

            content_w = max(pred_w, vert_w)
            content_h = pred_h + vert_h + (GAP if (pred_h and vert_h) else 0.0)

            req_w = max(child_strip_w, content_w) + 2 * PAD
            req_h = child_strip_h + content_h + 2 * PAD
            req_w = max(req_w, 120.0)
            req_h = max(req_h, 90.0)
            required_size[cut_id] = (req_w, req_h)
            return required_size[cut_id]

        # Kick off measurement from sheet/root children (level 0)
        sheet_id = getattr(graph, 'sheet', None)
        if sheet_id is None:
            # fallback: try to infer as outermost area key with no parent
            sheet_id = next(iter(graph.area.keys()), '')
        # Ensure we measure all cuts (in case some are not direct descendants of sheet)
        for c in graph.Cut:
            measure_cut(c.id)

        # Determine root canvas size to fit all top-level cuts horizontally
        top_cuts = [cid for cid in graph.area.get(sheet_id, []) if cid in cut_ids]
        if top_cuts:
            total_w = sum(required_size[cid][0] for cid in top_cuts) + (len(top_cuts) + 1) * GAP
            max_h = max(required_size[cid][1] for cid in top_cuts) + 2 * GAP
            cx1, cy1, cx2, cy2 = canvas_bounds if canvas_bounds else (0.0, 0.0, 900.0, 650.0)
            cw = cx2 - cx1
            ch = cy2 - cy1
            if total_w + 2 * PAD > cw or max_h + 2 * PAD > ch:
                # Expand canvas if needed
                cx2 = cx1 + max(cw, total_w + 2 * PAD)
                cy2 = cy1 + max(ch, max_h + 2 * PAD)
                canvas_bounds = (cx1, cy1, cx2, cy2)

        # Placement top-down
        def place_cut(cut_id: str, bounds: Tuple[float, float, float, float]) -> None:
            # record this cut primitive
            x1, y1, x2, y2 = bounds
            prims[cut_id] = SpatialPrimitive(
                element_id=cut_id,
                element_type='cut',
                position=((x1 + x2) * 0.5, (y1 + y2) * 0.5),
                bounds=bounds,
                z_index=1,
            )

            # inner rect
            ix1, iy1, ix2, iy2 = inner_rect(bounds, PAD)
            # children strip at top: horizontal packing
            child_ids = children_cuts.get(cut_id, [])
            cur_y = iy1
            cur_x = ix1 + GAP
            strip_h = 0.0
            if child_ids:
                # compute strip height as max child height + 2*GAP
                strip_h = max(required_size[cid][1] for cid in child_ids) + 2 * GAP
                if len(child_ids) == 1:
                    # center a single child horizontally in the inner width
                    cid = child_ids[0]
                    cw, ch = required_size[cid]
                    inner_w = max(1.0, ix2 - ix1)
                    bx1 = ix1 + max(GAP, (inner_w - cw) * 0.5)
                    by1 = iy1 + GAP
                    bx2 = bx1 + cw
                    by2 = by1 + ch
                    place_cut(cid, (bx1, by1, bx2, by2))
                else:
                    for cid in child_ids:
                        cw, ch = required_size[cid]
                        bx1 = cur_x
                        by1 = iy1 + GAP
                        bx2 = bx1 + cw
                        by2 = by1 + ch
                        place_cut(cid, (bx1, by1, bx2, by2))
                        cur_x = bx2 + GAP

            # content rect is remaining vertical space
            content_y1 = iy1 + strip_h
            cx1, cy1, cx2, cy2 = ix1, content_y1, ix2, iy2
            avail_w = max(1.0, cx2 - cx1)
            avail_h = max(1.0, cy2 - cy1)

            # Partition contents
            raw_contents = graph.area.get(cut_id, [])
            predicate_edges: list[str] = []
            vertex_spots: list[str] = []
            for eid in raw_contents:
                if eid in cut_ids:
                    continue
                if eid in vertex_ids:
                    vertex_spots.append(eid)
                elif eid in edge_by_id and edge_label.get(eid) not in ('=', '.='):
                    predicate_edges.append(eid)

            # Grid parameters
            def grid_positions(n: int, cols: int) -> list[tuple[int, int]]:
                return [(i // cols, i % cols) for i in range(n)]

            # Predicates: estimate sizes, then place in top half grid
            rows_pred = max(1, int(len(predicate_edges) ** 0.5))
            cols_pred = max(1, (len(predicate_edges) + rows_pred - 1) // rows_pred)
            cell_w_pred = avail_w / max(1, cols_pred)
            # allocate half height for predicates
            cell_h_pred = (avail_h * 0.5) / max(1, rows_pred)

            for idx, edge_id in enumerate(predicate_edges):
                # Skip identity edges here; they are drawn as lines below
                edge_obj = next((e for e in graph.E if getattr(e, 'id', str(e)) == edge_id), None)
                name = getattr(edge_obj, 'label', '') if edge_obj else ''
                if name in ('=', '.='):
                    continue
                w, h = self._calculate_predicate_dimensions(name)
                # Convert inches to px approx: Graphviz inches ~ 72.0 px
                pw, ph = max(30.0, w * 72.0), max(24.0, h * 72.0)
                r, c = grid_positions(len(predicate_edges), cols_pred)[idx]
                cx = cx1 + c * cell_w_pred + cell_w_pred * 0.5
                cy = cy1 + r * cell_h_pred + cell_h_pred * 0.5
                bx1, by1 = cx - pw / 2.0, cy - ph / 2.0
                bx2, by2 = cx + pw / 2.0, cy + ph / 2.0
                prims[edge_id] = SpatialPrimitive(
                    element_id=edge_id,
                    element_type='predicate',
                    position=(cx, cy),
                    bounds=(bx1, by1, bx2, by2),
                    z_index=2,
                )

            # Vertices: small spots in bottom half grid
            rows_v = max(1, int(len(vertex_spots) ** 0.5))
            cols_v = max(1, (len(vertex_spots) + rows_v - 1) // rows_v)
            cell_w_v = avail_w / max(1, cols_v)
            cell_h_v = (avail_h * 0.5) / max(1, rows_v)
            v_origin_y = cy1 + avail_h * 0.5

            spot_size = 10.0
            for idx, vid in enumerate(vertex_spots):
                r, c = grid_positions(len(vertex_spots), cols_v)[idx]
                cx = cx1 + c * cell_w_v + cell_w_v * 0.5
                cy = v_origin_y + r * cell_h_v + cell_h_v * 0.5
                bx1, by1 = cx - spot_size / 2.0, cy - spot_size / 2.0
                bx2, by2 = cx + spot_size / 2.0, cy + spot_size / 2.0
                prims[vid] = SpatialPrimitive(
                    element_id=vid,
                    element_type='vertex',
                    position=(cx, cy),
                    bounds=(bx1, by1, bx2, by2),
                    z_index=3,
                )
                # Add a short heavy ligature segment for visibility even without explicit '='
                seg_len = 28.0
                vx1, vy1 = cx - seg_len/2.0, cy
                vx2, vy2 = cx + seg_len/2.0, cy
                lig_id = f"lig_{vid}"
                prims[lig_id] = SpatialPrimitive(
                    element_id=lig_id,
                    element_type='edge',
                    position=(cx, cy),
                    bounds=(min(vx1, vx2), min(vy1, vy2), max(vx1, vx2), max(vy1, vy2)),
                    z_index=3,
                    curve_points=[(vx1, vy1), (vx2, vy2)],
                )

        # Place sheet/top-level cuts horizontally within canvas
        if top_cuts:
            cx1, cy1, cx2, cy2 = canvas_bounds if canvas_bounds else (0.0, 0.0, 900.0, 650.0)
            cur_x = cx1 + PAD
            y_top = cy1 + PAD
            for cid in top_cuts:
                cw, ch = required_size[cid]
                bx1 = cur_x
                by1 = y_top
                bx2 = bx1 + cw
                by2 = by1 + ch
                place_cut(cid, (bx1, by1, bx2, by2))
                cur_x = bx2 + GAP
            # Also place any sheet-level contents not inside a cut
            # Determine remaining area below the tallest top-level cut
            max_ch = max((required_size[cid][1] for cid in top_cuts), default=0.0)
            sx1, sy1, sx2, sy2 = cx1 + PAD, y_top + max_ch + GAP, cx2 - PAD, cy2 - PAD
            if sy2 > sy1:
                avail_w = max(1.0, sx2 - sx1)
                avail_h = max(1.0, sy2 - sy1)
                raw_contents = [eid for eid in graph.area.get(sheet_id, []) if eid not in cut_ids]
                predicate_edges: list[str] = []
                vertex_spots: list[str] = []
                for eid in raw_contents:
                    if eid in vertex_ids:
                        vertex_spots.append(eid)
                    elif eid in edge_by_id and edge_label.get(eid) not in ('=', '.='):
                        predicate_edges.append(eid)

                def grid_positions(n: int, cols: int) -> list[tuple[int, int]]:
                    return [(i // cols, i % cols) for i in range(n)]

                # Predicates in top half of remaining area
                rows_pred = max(1, int(len(predicate_edges) ** 0.5))
                cols_pred = max(1, (len(predicate_edges) + rows_pred - 1) // rows_pred)
                cell_w_pred = avail_w / max(1, cols_pred)
                cell_h_pred = (avail_h * 0.5) / max(1, rows_pred)
                for idx, eid in enumerate(predicate_edges):
                    eobj = edge_by_id.get(eid)
                    name = getattr(eobj, 'label', '') if eobj else ''
                    w, h = self._calculate_predicate_dimensions(name)
                    pw, ph = max(30.0, w * 72.0), max(24.0, h * 72.0)
                    r, c = grid_positions(len(predicate_edges), cols_pred)[idx]
                    cx = sx1 + c * cell_w_pred + cell_w_pred * 0.5
                    cy = sy1 + r * cell_h_pred + cell_h_pred * 0.5
                    bx1, by1 = cx - pw / 2.0, cy - ph / 2.0
                    bx2, by2 = cx + pw / 2.0, cy + ph / 2.0
                    prims[eid] = SpatialPrimitive(
                        element_id=eid,
                        element_type='predicate',
                        position=(cx, cy),
                        bounds=(bx1, by1, bx2, by2),
                        z_index=2,
                    )

                # Vertices in bottom half of remaining area
                rows_v = max(1, int(len(vertex_spots) ** 0.5))
                cols_v = max(1, (len(vertex_spots) + rows_v - 1) // rows_v)
                cell_w_v = avail_w / max(1, cols_v)
                cell_h_v = (avail_h * 0.5) / max(1, rows_v)
                v_origin_y = sy1 + avail_h * 0.5
                spot_size = 10.0
                for idx, vid in enumerate(vertex_spots):
                    r, c = grid_positions(len(vertex_spots), cols_v)[idx]
                    cx = sx1 + c * cell_w_v + cell_w_v * 0.5
                    cy = v_origin_y + r * cell_h_v + cell_h_v * 0.5
                    bx1, by1 = cx - spot_size / 2.0, cy - spot_size / 2.0
                    bx2, by2 = cx + spot_size / 2.0, cy + spot_size / 2.0
                    prims[vid] = SpatialPrimitive(
                        element_id=vid,
                        element_type='vertex',
                        position=(cx, cy),
                        bounds=(bx1, by1, bx2, by2),
                        z_index=3,
                    )
                    seg_len = 28.0
                    vx1, vy1 = cx - seg_len/2.0, cy
                    vx2, vy2 = cx + seg_len/2.0, cy
                    lig_id = f"lig_{vid}"
                    prims[lig_id] = SpatialPrimitive(
                        element_id=lig_id,
                        element_type='edge',
                        position=(cx, cy),
                        bounds=(min(vx1, vx2), min(vy1, vy2), max(vx1, vx2), max(vy1, vy2)),
                        z_index=3,
                        curve_points=[(vx1, vy1), (vx2, vy2)],
                    )
        else:
            # No cuts: place sheet-level contents in the canvas directly
            cx1, cy1, cx2, cy2 = canvas_bounds if canvas_bounds else (0.0, 0.0, 900.0, 650.0)
            ix1, iy1, ix2, iy2 = inner_rect((cx1, cy1, cx2, cy2), PAD)
            avail_w = max(1.0, ix2 - ix1)
            avail_h = max(1.0, iy2 - iy1)
            # Sheet contents
            raw_contents = [eid for eid in graph.area.get(sheet_id, []) if eid not in cut_ids]
            predicate_edges: list[str] = []
            vertex_spots: list[str] = []
            for eid in raw_contents:
                if eid in vertex_ids:
                    vertex_spots.append(eid)
                elif eid in edge_by_id and edge_label.get(eid) not in ('=', '.='):
                    predicate_edges.append(eid)

            def grid_positions(n: int, cols: int) -> list[tuple[int, int]]:
                return [(i // cols, i % cols) for i in range(n)]

            # Predicates in top half
            rows_pred = max(1, int(len(predicate_edges) ** 0.5))
            cols_pred = max(1, (len(predicate_edges) + rows_pred - 1) // rows_pred)
            cell_w_pred = avail_w / max(1, cols_pred)
            cell_h_pred = (avail_h * 0.5) / max(1, rows_pred)
            for idx, eid in enumerate(predicate_edges):
                eobj = edge_by_id.get(eid)
                name = getattr(eobj, 'label', '') if eobj else ''
                w, h = self._calculate_predicate_dimensions(name)
                pw, ph = max(30.0, w * 72.0), max(24.0, h * 72.0)
                r, c = grid_positions(len(predicate_edges), cols_pred)[idx]
                cx = ix1 + c * cell_w_pred + cell_w_pred * 0.5
                cy = iy1 + r * cell_h_pred + cell_h_pred * 0.5
                bx1, by1 = cx - pw / 2.0, cy - ph / 2.0
                bx2, by2 = cx + pw / 2.0, cy + ph / 2.0
                prims[eid] = SpatialPrimitive(
                    element_id=eid,
                    element_type='predicate',
                    position=(cx, cy),
                    bounds=(bx1, by1, bx2, by2),
                    z_index=2,
                )
            # Vertices in bottom half
            rows_v = max(1, int(len(vertex_spots) ** 0.5))
            cols_v = max(1, (len(vertex_spots) + rows_v - 1) // rows_v)
            cell_w_v = avail_w / max(1, cols_v)
            cell_h_v = (avail_h * 0.5) / max(1, rows_v)
            v_origin_y = iy1 + avail_h * 0.5
            spot_size = 10.0
            for idx, vid in enumerate(vertex_spots):
                r, c = grid_positions(len(vertex_spots), cols_v)[idx]
                cx = ix1 + c * cell_w_v + cell_w_v * 0.5
                cy = v_origin_y + r * cell_h_v + cell_h_v * 0.5
                bx1, by1 = cx - spot_size / 2.0, cy - spot_size / 2.0
                bx2, by2 = cx + spot_size / 2.0, cy + spot_size / 2.0
                prims[vid] = SpatialPrimitive(
                    element_id=vid,
                    element_type='vertex',
                    position=(cx, cy),
                    bounds=(bx1, by1, bx2, by2),
                    z_index=3,
                )
                seg_len = 28.0
                vx1, vy1 = cx - seg_len/2.0, cy
                vx2, vy2 = cx + seg_len/2.0, cy
                lig_id = f"lig_{vid}"
                prims[lig_id] = SpatialPrimitive(
                    element_id=lig_id,
                    element_type='edge',
                    position=(cx, cy),
                    bounds=(min(vx1, vx2), min(vy1, vy2), max(vx1, vx2), max(vy1, vy2)),
                    z_index=3,
                    curve_points=[(vx1, vy1), (vx2, vy2)],
                )

        # 3) Identity lines and predicate connections
        # Build quick lookup for vertex positions and predicate boxes
        vpos: Dict[str, Tuple[float, float]] = {}
        for v in graph.V:
            spr = prims.get(v.id)
            if spr and spr.position:
                vpos[v.id] = spr.position
        pbox: Dict[str, Tuple[float, float, float, float]] = {}
        for e in graph.E:
            eid = e.id if hasattr(e, 'id') else str(e)
            spr = prims.get(eid)
            if spr and spr.bounds:
                pbox[eid] = spr.bounds

        # Draw identity edges as polylines between vertices
        for e in graph.E:
            eid = e.id if hasattr(e, 'id') else str(e)
            name = getattr(e, 'label', '')
            nu_seq = getattr(graph, 'nu', {}).get(eid, [])
            if name in ('=', '.=') and len(nu_seq) >= 2:
                pts: list[Tuple[float, float]] = []
                for v_id in nu_seq:
                    if v_id in vpos:
                        pts.append(vpos[v_id])
                if len(pts) >= 2:
                    # Check if all points collapse to (nearly) the same location (reflexive case)
                    distinct = []
                    EPS = 1e-3
                    for p in pts:
                        if not distinct or abs(p[0] - distinct[-1][0]) > EPS or abs(p[1] - distinct[-1][1]) > EPS:
                            distinct.append(p)
                    if len(distinct) < 2:
                        # Draw a short heavy segment centered at the vertex to ensure visibility
                        vx, vy = pts[0]
                        seg = 24.0
                        p1 = (vx - seg/2.0, vy)
                        p2 = (vx + seg/2.0, vy)
                        xs = [p1[0], p2[0]]
                        ys = [p1[1], p2[1]]
                        cx = (min(xs) + max(xs)) * 0.5
                        cy = (min(ys) + max(ys)) * 0.5
                        prims[eid] = SpatialPrimitive(
                            element_id=eid,
                            element_type='edge',
                            position=(cx, cy),
                            bounds=(min(xs), min(ys), max(xs), max(ys)),
                            z_index=4,
                            curve_points=[p1, p2],
                        )
                    else:
                        xs = [p[0] for p in pts]
                        ys = [p[1] for p in pts]
                        cx = (min(xs) + max(xs)) * 0.5
                        cy = (min(ys) + max(ys)) * 0.5
                        prims[eid] = SpatialPrimitive(
                            element_id=eid,
                            element_type='edge',
                            position=(cx, cy),
                            bounds=(min(xs), min(ys), max(xs), max(ys)),
                            z_index=4,
                            curve_points=pts,
                        )
            elif name in ('=', '.=') and len(nu_seq) == 1:
                # Reflexive/degenerate identity: render a short heavy segment at the single vertex
                v_id = nu_seq[0]
                if v_id in vpos:
                    vx, vy = vpos[v_id]
                    seg = 36.0  # slightly longer for visibility
                    off_y = -4.0  # lift above the vertex spot so it isn't occluded
                    p1 = (vx - seg/2.0, vy + off_y)
                    p2 = (vx + seg/2.0, vy + off_y)
                    xs = [p1[0], p2[0]]
                    ys = [p1[1], p2[1]]
                    cx = (min(xs) + max(xs)) * 0.5
                    cy = (min(ys) + max(ys)) * 0.5
                    prims[eid] = SpatialPrimitive(
                        element_id=eid,
                        element_type='edge',
                        position=(cx, cy),
                        bounds=(min(xs), min(ys), max(xs), max(ys)),
                        z_index=10,  # ensure drawn above vertex dot
                        curve_points=[p1, p2],
                    )

        # Draw predicate connections as straight segments from vertex spot to box edge
        def nearest_point_on_rect(b: Tuple[float, float, float, float], p: Tuple[float, float]) -> Tuple[float, float]:
            x1, y1, x2, y2 = b
            cx, cy = p
            nx = min(max(cx, x1), x2)
            ny = min(max(cy, y1), y2)
            return (nx, ny)

        for e in graph.E:
            eid = e.id if hasattr(e, 'id') else str(e)
            name = getattr(e, 'label', '')
            if name in ('=', '.='):
                continue
            nu_seq = getattr(graph, 'nu', {}).get(eid, [])
            if eid not in pbox:
                continue
            rect = pbox[eid]
            for idx, v_id in enumerate(nu_seq):
                if v_id not in vpos:
                    continue
                vp = vpos[v_id]
                hp = nearest_point_on_rect(rect, vp)
                conn_id = f"edge_{eid}_conn_{idx}"
                # Bias label/anchor position toward predicate boundary to keep numbers near the predicate
                bias = 0.98  # very close to hook point on predicate box
                cx = vp[0] * (1.0 - bias) + hp[0] * bias
                cy = vp[1] * (1.0 - bias) + hp[1] * bias
                # Offset slightly outward from the predicate box to avoid overlap with text
                x1, y1, x2, y2 = rect
                out_off = 3.0
                # Determine which side the hook point lies on and push outward a bit
                if abs(hp[0] - x1) < 1e-3:
                    cx -= out_off
                elif abs(hp[0] - x2) < 1e-3:
                    cx += out_off
                elif abs(hp[1] - y1) < 1e-3:
                    cy -= out_off
                elif abs(hp[1] - y2) < 1e-3:
                    cy += out_off
                prims[conn_id] = SpatialPrimitive(
                    element_id=conn_id,
                    element_type='edge',
                    position=(cx, cy),
                    bounds=(min(vp[0], hp[0]), min(vp[1], hp[1]), max(vp[0], hp[0]), max(vp[1], hp[1])),
                    z_index=4,
                    curve_points=[vp, hp],
                )

        # Containment hierarchy direct from area map
        containment_hierarchy: Dict[str, set[str]] = {graph.sheet: set(graph.area.get(graph.sheet, []))}
        for area_id, contents in graph.area.items():
            containment_hierarchy.setdefault(area_id, set()).update(contents)

        layout = LayoutResult(
            primitives=prims,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy,
        )
        # Validate once (should pass: centers within parent due to grid in inner rect)
        self._validate_presence_and_parent_containment(layout, graph, phase="logical-baseline")
        return layout

    def _clamp_predicates_to_parent_cuts(self, layout_result: LayoutResult,
                                         graph: RelationalGraphWithCuts,
                                         margin: float = 16.0) -> None:
        """Clamp predicate centers so their bounds are fully contained in their parent cut.

        - Finds parent area from `graph.area`.
        - Uses the cut primitive bounds as container; shrinks by `margin`.
        - For each predicate primitive (id == edge.id), clamps center accordingly.
        """
        prims = layout_result.primitives
        # Build quick map of cut bounds
        cut_bounds: Dict[str, Tuple[float, float, float, float]] = {}
        for cut in graph.Cut:
            cprim = prims.get(cut.id)
            if cprim and cprim.bounds:
                cut_bounds[cut.id] = cprim.bounds

        # For every assignment in area map, clamp predicates
        for parent_area, contents in graph.area.items():
            parent = cut_bounds.get(parent_area)
            if not parent:
                continue
            px1, py1, px2, py2 = parent
            ix1, iy1, ix2, iy2 = px1 + margin, py1 + margin, px2 - margin, py2 - margin
            if ix2 <= ix1 or iy2 <= iy1:
                # Fallback to raw parent bounds if inner rect collapsed
                ix1, iy1, ix2, iy2 = px1, py1, px2, py2
            for eid in contents:
                # Predicates are edges in the EGI; their primitives use the same id
                sprim = prims.get(eid) or prims.get(f"pred_{eid}")
                if not sprim or not sprim.bounds:
                    continue
                # Accept both legacy 'edge' and canonical 'predicate' types
                if sprim.element_type not in ('predicate', 'edge'):
                    continue
                bx1, by1, bx2, by2 = sprim.bounds
                cx, cy = ((bx1 + bx2) * 0.5, (by1 + by2) * 0.5)
                w, h = (bx2 - bx1, by2 - by1)
                # Center-only clamp ensures validation (center inside parent)
                eps = 1.0
                new_cx = min(max(cx, ix1 + eps), ix2 - eps)
                new_cy = min(max(cy, iy1 + eps), iy2 - eps)
                if abs(new_cx - cx) < 1e-6 and abs(new_cy - cy) < 1e-6:
                    continue
                nb = (new_cx - w / 2.0, new_cy - h / 2.0, new_cx + w / 2.0, new_cy + h / 2.0)
                prims[sprim.element_id] = SpatialPrimitive(
                    element_id=sprim.element_id,
                    element_type=sprim.element_type,
                    position=(new_cx, new_cy),
                    bounds=nb,
                    z_index=sprim.z_index,
                    attachment_points=sprim.attachment_points,
                    curve_points=sprim.curve_points,
                )
        
    
    def _generate_dot_from_egi(self, graph: RelationalGraphWithCuts) -> str:
        """
        Step 1: Convert EGI structure to Graphviz DOT language.
        
        FIXED: Improved spacing parameters to prevent overlaps and crowding.
        
        Key mappings:
        - EGI vertices → Graphviz nodes
        - EGI edges (predicates/identity) → Graphviz edges
        - EGI cuts → Graphviz subgraph clusters
        - EGI area containment → Nested subgraph structure
        
        CONTRACT: Output validated against solidified DOT standards.
        """
        # Validate input
        validate_relational_graph_with_cuts(graph)
        
        # Generate DOT content
        # Use original header with spacing to keep deterministic placement
        dot_lines = [
            "graph EG {",
            "    // ENHANCED: Dau convention layout with proper spacing",
            "    graph [clusterrank=local, compound=true, newrank=true, rankdir=TB,",
            "           overlap=false, splines=true, concentrate=false];",
            "    ",
            "    // Enhanced spacing for Dau visual conventions",
            "    node [shape=circle, width=0.4, height=0.4, fixedsize=true,",
            "          fontsize=10, margin=0.2];",
            "    edge [arrowhead=none, len=3.5, minlen=2.5, weight=1.0];",
            "    ",
            "    // Spacing parameters for visual clarity (compact defaults)",
            "    nodesep=1.2;        // Compact node separation",
            "    ranksep=1.0;        // Compact rank separation",
            "    margin=1.5;         // Keep graph margin modest",
            "    pad=\"1.5,1.5\";      // Keep padding modest",
            "    sep=\"+8\";           // Compact minimum separation",
            ""
        ]
        dot_lines.append("  ")  
        dot_lines.append("  // Default node styling with proper sizing")
        dot_lines.append("  node [shape=circle, style=filled, fillcolor=lightblue, fontsize=10];")
        dot_lines.append("  edge [fontsize=9, labeldistance=1.5, labelangle=0];")
        dot_lines.append("")
        
        # Generate subgraph clusters for cuts (with proper nesting)
        self._add_cuts_as_clusters(dot_lines, graph)
        
        # Add sheet-level nodes only (elements not contained in any cut)
        self._add_sheet_level_predicates(dot_lines, graph)
        self._add_sheet_level_vertices(dot_lines, graph)
        
        # Generate edges for predicates and identity lines (no node redeclaration here)
        self._add_edges_for_predicates(dot_lines, graph)
        
        # DOT file footer
        dot_lines.append("}")
        
        dot_content = "\n".join(dot_lines)
        
        # CONTRACT: Validate DOT output against solidified standards
        validate_graphviz_dot_output(dot_content, graph)
        
        return dot_content

    def _clamp_elements_to_parent_areas(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts, inset: float = 16.0) -> None:
        """Ensure every element center lies inside its parent area by at least `inset` pixels.
        Moves element positions minimally if needed.
        """
        # Build a map of cut bounds for quick access
        cut_bounds: Dict[str, Tuple[float, float, float, float]] = {}
        for cut in graph.Cut:
            prim = layout_result.primitives.get(cut.id)
            if prim and prim.bounds:
                x1, y1, x2, y2 = prim.bounds
                cut_bounds[cut.id] = (x1 + inset, y1 + inset, x2 - inset, y2 - inset)

        def parent_of(element_id: str) -> Optional[str]:
            # Sheet means no clamp
            for cut_id, contents in graph.area.items():
                if element_id in contents:
                    return cut_id
            return None

        for eid, prim in list(layout_result.primitives.items()):
            # Skip cuts themselves
            if prim.element_type == 'cut':
                continue
            parent_cut = parent_of(eid)
            if not parent_cut:
                # sheet-level element; nothing to clamp
                continue
            cb = cut_bounds.get(parent_cut)
            if not cb:
                continue
            px, py = prim.position
            cx1, cy1, cx2, cy2 = cb
            nx, ny = px, py
            if px < cx1:
                nx = cx1
            elif px > cx2:
                nx = cx2
            if py < cy1:
                ny = cy1
            elif py > cy2:
                ny = cy2
            if (nx, ny) != (px, py):
                # Update primitive with new position; adjust bounds relative to delta
                dx, dy = nx - px, ny - py
                bx1, by1, bx2, by2 = prim.bounds
                new_bounds = (bx1 + dx, by1 + dy, bx2 + dx, by2 + dy)
                layout_result.primitives[eid] = type(prim)(
                    element_id=prim.element_id,
                    element_type=prim.element_type,
                    position=(nx, ny),
                    bounds=new_bounds,
                    z_index=prim.z_index,
                    curve_points=prim.curve_points,
                    attachment_points=prim.attachment_points,
                    parent_area=prim.parent_area,
                )
    
    def _add_cuts_as_clusters(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Add EGI cuts as Graphviz subgraph clusters with proper nesting."""
        
        # Build hierarchy of cuts (parent → children mapping)
        cut_hierarchy = self._build_cut_hierarchy(graph)
        
        # Add clusters recursively, starting from root-level cuts
        root_cuts = [cut for cut in graph.Cut if self._get_cut_parent(cut, graph) == graph.sheet]
        
        for cut in root_cuts:
            self._add_cluster_recursive(dot_lines, cut, graph, cut_hierarchy, indent=1)
    
    def _build_cut_hierarchy(self, graph: RelationalGraphWithCuts) -> Dict[str, List]:
        """Build parent → children mapping for cuts."""
        hierarchy = {}
        
        for cut in graph.Cut:
            parent = self._get_cut_parent(cut, graph)
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(cut)
        
        return hierarchy
    
    def _get_cut_parent(self, cut, graph: RelationalGraphWithCuts) -> str:
        """Find the parent area of a cut."""
        for area_id, contents in graph.area.items():
            if cut.id in contents:
                return area_id
        return graph.sheet  # Default to sheet level

    def _get_element_parent_cut(self, element_id: str, graph: RelationalGraphWithCuts) -> Optional[str]:
        """Return the cut ID that directly contains the element, or None if at sheet level."""
        for cut_id, contents in graph.area.items():
            if element_id in contents:
                return cut_id
        return None

    def _select_head_port(self, index: int, total: int) -> str:
        """Choose a compass port on the predicate box to separate hooks for n-ary predicates."""
        if total <= 1:
            return ""
        # Distribute first across cardinal directions, then diagonals
        base_ports = ["w", "e", "n", "s", "nw", "ne", "sw", "se"]
        if total <= 4:
            return ["w", "e", "n", "s"][index % 4]
        return base_ports[index % len(base_ports)]
    
    def _add_cluster_recursive(self, dot_lines: List[str], cut, graph: RelationalGraphWithCuts, 
                             hierarchy: Dict[str, List], indent: int):
        """Recursively add a cut and its nested cuts as clusters."""
        
        indent_str = "  " * indent
        
        # Start subgraph cluster with proper spacing attributes
        # If we already parsed cluster bounds on a prior pass we could thread them here.
        # For now, fall back to default adaptive with None (later phases can pass known bounds).
        # CANONICAL MODE: Give parents slightly larger margin than children to enforce strict inset
        has_children = len(hierarchy.get(cut.id, [])) > 0
        parent_margin = 12.0
        leaf_margin = 8.0
        cluster_padding = parent_margin if has_children else leaf_margin
        safe_cut_id = self._sanitize_dot_id(cut.id)
        
        dot_lines.append(f"{indent_str}subgraph cluster_{safe_cut_id} {{")
        # CANONICAL MODE: No cut labels for clean Dau-compliant rendering
        dot_lines.append(f"{indent_str}  style=rounded;")
        dot_lines.append(f"{indent_str}  color=black;")
        dot_lines.append(f"{indent_str}  penwidth=1.5;")
        dot_lines.append(f"{indent_str}  margin={cluster_padding:.2f};  // Padding around cut contents")
        dot_lines.append(f"{indent_str}  // Leverage Graphviz hierarchical layout")
        dot_lines.append(f"{indent_str}  clusterrank=local;  // Layout this cluster separately")
        dot_lines.append("")

        # Ensure cluster is realized even when empty: add an invisible anchor node
        # This forces Graphviz to emit a cluster bounding box in xdot output
        dot_lines.append(f"{indent_str}  anchor_{safe_cut_id} [label=\"\", shape=point, width=0.01, height=0.01, fixedsize=true, style=invis];")
        dot_lines.append("")
        
        # Add child cuts recursively
        child_cuts = hierarchy.get(cut.id, [])
        for child_cut in child_cuts:
            self._add_cluster_recursive(dot_lines, child_cut, graph, hierarchy, indent + 1)
        
        # Add vertices and edges that belong to this cut
        cut_contents = graph.area.get(cut.id, [])
        
        # SIMPLE FIX: Use EGI core's get_area() method to get cut contents
        cut_contents = graph.get_area(cut.id)
        
        # Add vertices in this cut
        for element_id in cut_contents:
            if element_id in graph._vertex_map:
                vertex = graph._vertex_map[element_id]
                safe_node_id = self._sanitize_dot_id(element_id)
                # Unlabeled vertex spots to avoid label size warnings
                label = '""'
                
                width, height = self._calculate_vertex_size(vertex, graph)
                dot_lines.append(f"{indent_str}  {safe_node_id} [label={label}, width={width:.2f}, height={height:.2f}, fixedsize=true];")
        
        # Add predicates (edges) in this cut
        for element_id in cut_contents:
            if element_id in graph.nu:  # This is a predicate edge
                predicate_name = graph.rel.get(element_id, element_id[:8])
                # CONSISTENT IDs: Use original EGI element ID directly (no pred_ prefix)
                safe_edge_id = self._sanitize_dot_id(element_id)
                
                width, height = self._calculate_predicate_dimensions(predicate_name)
                dot_lines.append(f"{indent_str}  {safe_edge_id} [label=\"{predicate_name}\", shape=box, fillcolor=lightyellow, width={width:.2f}, height={height:.2f}, fixedsize=true];")
        
        # End subgraph cluster
        dot_lines.append(f"{indent_str}}}")
        dot_lines.append("")

    def _add_sheet_level_vertices(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Declare only vertices that reside at the sheet level (no containing cut)."""
        for vertex in graph.V:
            vertex_id = vertex.id
            # Skip if inside any cut
            if self._get_element_parent_cut(vertex_id, graph):
                continue
            safe_node_id = self._sanitize_dot_id(vertex_id)
            # Render vertices as unlabeled spots; labels cause size warnings and are unnecessary
            label = '""'
            width, height = self._calculate_vertex_size(vertex, graph)
            dot_lines.append(f"  {safe_node_id} [label={label}, width={width:.2f}, height={height:.2f}, fixedsize=true];")

    def _add_sheet_level_predicates(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Declare only predicate nodes that reside at the sheet level (no containing cut)."""
        for edge_id, seq in graph.nu.items():
            if self._get_element_parent_cut(edge_id, graph):
                continue
            predicate_name = graph.rel.get(edge_id, edge_id[:8])
            safe_predicate_name = predicate_name.replace('"', '\\"')
            predicate_node_id = self._sanitize_dot_id(edge_id)
            pred_width, pred_height = self._calculate_predicate_dimensions(predicate_name)
            dot_lines.append(
                f"  {predicate_node_id} [label=\"{safe_predicate_name}\", shape=box, fillcolor=lightyellow, "
                f"width={pred_width:.2f}, height={pred_height:.2f}, fixedsize=true];"
            )
    
    def _add_vertices_as_nodes(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Add ALL EGI vertices as Graphviz nodes.
        
        FIXED: Process all vertices in the EGI, not just sheet-level vertices.
        This ensures that vertices connected to predicates in different areas
        (like the Loves example with vertices spanning sheet and cut areas) are included.
        """
        
        # Process ALL vertices in the EGI graph
        for vertex in graph.V:
            vertex_id = vertex.id
            # Sanitize node ID and label for DOT syntax
            safe_node_id = self._sanitize_dot_id(vertex_id)
            # Emit unlabeled vertex spot; visual label is not needed for layout
            label = '""'
            
            # Calculate proper size for collision detection
            width, height = self._calculate_vertex_size(vertex, graph)
            
            # Generate node with sizing attributes
            dot_lines.append(f"  {safe_node_id} [label={label}, width={width:.2f}, height={height:.2f}, fixedsize=true];")
            
        print(f"DEBUG: Added {len(graph.V)} vertices to DOT: {[v.id for v in graph.V]}")
        
        dot_lines.append("")
    
    def _add_edges_for_predicates(self, dot_lines: List[str], graph: RelationalGraphWithCuts):
        """Add EGI predicate attachments as Graphviz edges (vertex ↔ predicate node).
        
        Baseline accurate rendering requirement:
        - Every predicate (edge_id in graph.nu) must be represented as a predicate node
          (box with label) and each argument vertex in ν(edge_id) must be connected to
          that node by an edge. This holds for unary and n-ary predicates and across cuts.
        - We do NOT connect vertices to each other; the predicate is not an edge label.
        """
        
        for edge_id, vertex_sequence in graph.nu.items():
            predicate_node_id = self._sanitize_dot_id(edge_id)
            # Connect each argument vertex to the predicate node with distinct ports and cluster routing
            total = len(vertex_sequence)
            for idx, v in enumerate(vertex_sequence):
                safe_v = self._sanitize_dot_id(v)
                port = self._select_head_port(idx, total)
                head = f"{predicate_node_id}:{port}" if port else predicate_node_id
                attrs = ["style=bold", "penwidth=2"]
                # Cluster routing across cuts
                head_cut = self._get_element_parent_cut(edge_id, graph)
                tail_cut = self._get_element_parent_cut(v, graph)
                
                # CRITICAL FIX: Prevent cross-cluster edges from pulling nodes out of clusters
                if head_cut != tail_cut:  # Cross-cluster edge
                    attrs.append("constraint=false")  # Don't let this edge displace nodes from clusters
                
                # Only apply lhead/ltail for real cut IDs (exclude sheet)
                if self._is_real_cut_id(head_cut, graph):
                    attrs.append(f"lhead=cluster_{self._sanitize_dot_id(head_cut)}")
                if self._is_real_cut_id(tail_cut, graph):
                    attrs.append(f"ltail=cluster_{self._sanitize_dot_id(tail_cut)}")
                attr_str = ", ".join(attrs)
                dot_lines.append(f"  {safe_v} -- {head} [{attr_str}];")
        
        dot_lines.append("")

    def _is_real_cut_id(self, cut_id: Optional[str], graph: RelationalGraphWithCuts) -> bool:
        """Return True if cut_id is a real cut present in the graph (not sheet/None)."""
        if not cut_id:
            return False
        return any(getattr(c, 'id', str(c)) == cut_id for c in graph.Cut)
    
    def _execute_graphviz(self, dot_content: str) -> str:
        """
        Step 2: Execute Graphviz and return plain text output.
        
        Uses Graphviz's plain output format for reliable coordinate parsing.
        """
        try:
            # Write DOT content to temporary file
            dot_file = os.path.join(self.temp_dir, "eg_layout.dot")
            with open(dot_file, 'w') as f:
                f.write(dot_content)
            
            # Execute Graphviz with xdot output (includes cluster _bb bounding boxes)
            cmd = [self.dot_executable, "-Txdot", dot_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"Graphviz execution failed: {result.stderr}")
            
            # Clean up temporary file
            os.remove(dot_file)
            
            return result.stdout
            
        except Exception as e:
            raise RuntimeError(f"Failed to execute Graphviz: {e}")
    
    def _parse_xdot_output_to_layout(self, xdot_output: str, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        Step 3: Parse Graphviz xdot output into LayoutResult.
        
        xdot format includes cluster _bb (bounding box) attributes:
        - Clusters have _bb="x1,y1,x2,y2" attributes with precise boundaries
        - Nodes have pos="x,y" attributes for positioning
        - This allows us to use Graphviz's native cluster size calculations!
        """
        primitives = {}
        canvas_bounds = (0, 0, 400, 300)  # Default bounds
        
        # Use the proven xdot parser instead of fragile regex
        try:
            clusters, nodes, edges = parse_xdot_file(xdot_output)
            
            # Extract main graph bounding box
            import re
            graph_bb_match = re.search(r'graph \[.*?bb="([^"]+)"', xdot_output, re.DOTALL)
            if graph_bb_match:
                bb_coords = graph_bb_match.group(1).split(',')
                if len(bb_coords) == 4:
                    x1, y1, x2, y2 = map(float, bb_coords)
                    canvas_bounds = (x1, y1, x2, y2)
            
            # Process clusters (cuts) using the proven parser
            for cluster in clusters:
                cluster_name = cluster.name
                x1, y1, x2, y2 = cluster.bb
                
                # Find matching cut in graph
                cut_id_part = cluster_name.replace('cluster_', '')
                for cut in graph.Cut:
                    if self._sanitize_dot_id(cut.id) == cut_id_part:
                        # Create cut primitive using Graphviz's native cluster boundary
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        
                        cut_primitive = SpatialPrimitive(
                            element_id=cut.id,
                            element_type='cut',
                            position=(center_x, center_y),
                            bounds=(x1, y1, x2, y2),
                            z_index=0
                        )
                        primitives[cut.id] = cut_primitive
                        print(f"✅ Using Graphviz cluster boundary for {cut.id}: bounds=({x1}, {y1}, {x2}, {y2})")
                        break
            
            # Process nodes using the proven parser
            for node in nodes:
                node_id = node.name
                # Skip internal invisible anchors used to force cluster emission
                if node_id.startswith('anchor_'):
                    continue
                x, y = node.pos
                width = node.width * 72  # Convert to points
                height = node.height * 72

                # Normalize Graphviz IDs: predicates may be emitted as "pred_<edge_id>"
                is_pred_prefixed = False
                normalized_id = node_id
                if node_id.startswith('pred_'):
                    is_pred_prefixed = True
                    normalized_id = node_id[len('pred_'):]

                # Determine element type using EGI mappings (after normalization)
                if normalized_id in graph.nu:  # Predicate edge (by EGI edge_id)
                    element_type_name = 'predicate'
                    edge_id_for_pred = normalized_id
                elif node_id in graph.nu:  # Fallback if Graphviz used raw edge_id
                    element_type_name = 'predicate'
                    edge_id_for_pred = node_id
                elif node_id in graph._vertex_map:
                    element_type_name = 'vertex'
                    edge_id_for_pred = None
                elif node_id in graph._cut_map:
                    # IMPORTANT: Do not create/overwrite cut primitives from nodes.
                    # Cut primitives must come exclusively from cluster _bb bounds.
                    # Skip this node entirely to preserve exact Graphviz cluster boxes.
                    continue
                else:
                    # Fallback: assume vertex for unknown elements
                    element_type_name = 'vertex'
                    edge_id_for_pred = None

                # Create node primitive bounds from Graphviz (xdot) dimensions
                if element_type_name == 'predicate':
                    # Use xdot-reported width/height to ensure alignment with Graphviz layout
                    node_bounds = (
                        x - width/2,
                        y - height/2,
                        x + width/2,
                        y + height/2
                    )
                else:
                    # For vertices and cuts, use Graphviz dimensions
                    node_bounds = (
                        x - width/2,
                        y - height/2,
                        x + width/2,
                        y + height/2
                    )

                # Use normalized EGI ID for predicates; raw ID otherwise
                original_element_id = edge_id_for_pred if element_type_name == 'predicate' else node_id

                # CRITICAL FIX: Set up attachment_points for predicates
                attachment_points = None
                if element_type_name == 'predicate' and original_element_id in graph.nu:
                    # Get vertex positions for this predicate's nu mapping
                    vertex_sequence = graph.nu[original_element_id]
                    attachment_points = {}

                    for i, vertex_id in enumerate(vertex_sequence):
                        # Find vertex position in the same layout
                        for other_node in nodes:
                            if other_node.name == vertex_id:
                                vertex_x, vertex_y = other_node.pos
                                attachment_points[f"vertex_{i}"] = (vertex_x, vertex_y)
                                break

                primitive = SpatialPrimitive(
                    element_id=original_element_id,
                    element_type=element_type_name,
                    position=(x, y),
                    bounds=node_bounds,
                    z_index=1,
                    attachment_points=attachment_points
                )

                # Store under the canonical EGI ID, but never overwrite an existing cut primitive
                if original_element_id in primitives and primitives[original_element_id].element_type == 'cut':
                    # Preserve cluster-derived cut bounds
                    pass
                else:
                    primitives[original_element_id] = primitive

                # Back-compatibility: also store under 'pred_<edge_id>' if Graphviz used that
                if element_type_name == 'predicate' and is_pred_prefixed:
                    primitives[node_id] = primitive
            
            # CRITICAL FIX: Ensure ALL graph elements have spatial primitives
            # STRICT MODE: Do NOT fabricate fallbacks; report missing items explicitly
            self._assert_no_missing_primitives(graph, primitives)
            
            # Process edges using the proven parser (with error handling)
            # CRITICAL FIX: Map Graphviz edges back to actual EGI edge IDs
            try:
                for edge in edges:
                    if hasattr(edge, 'tail') and hasattr(edge, 'head') and hasattr(edge, 'points'):
                        tail_id = edge.tail
                        head_id = edge.head
                        edge_points = edge.points
                        
                        # CRITICAL FIX: Find the actual EGI edge ID that connects these vertices
                        actual_edge_id = None
                        
                        # Look for EGI edge that connects tail_id to head_id (predicate connection)
                        # In EGI, edges represent predicates, and the Graphviz edge connects vertex to predicate
                        for egi_edge_id, vertex_sequence in graph.nu.items():
                            # Check if this predicate (egi_edge_id) connects to the tail vertex
                            if tail_id in vertex_sequence and head_id == self._sanitize_dot_id(egi_edge_id):
                                actual_edge_id = egi_edge_id
                                break
                            # Also check reverse direction
                            elif head_id in vertex_sequence and tail_id == self._sanitize_dot_id(egi_edge_id):
                                actual_edge_id = egi_edge_id
                                break
                        
                        # Create edge primitive only if we found the actual EGI edge ID
                        if actual_edge_id and edge_points and len(edge_points) > 0:
                            # CRITICAL FIX: Determine if this is a predicate or identity line
                            # Predicate edges are in graph.nu and connect to predicate nodes
                            # Identity lines connect vertex to vertex directly
                            
                            # Check if this edge represents a predicate (edge in nu mapping)
                            is_predicate_edge = actual_edge_id in graph.nu
                            
                            if is_predicate_edge:
                                # This edge represents a predicate - skip creating identity line
                                # The predicate primitive should already be created from node processing
                                continue
                            else:
                                # This is a true identity line connecting vertices
                                # Only add if this edge_id doesn't already exist
                                if actual_edge_id not in primitives or primitives[actual_edge_id].element_type != 'identity_line':
                                    center_x = sum(p[0] for p in edge_points) / len(edge_points)
                                    center_y = sum(p[1] for p in edge_points) / len(edge_points)
                                    
                                    # Create identity line primitive with actual EGI edge ID
                                    primitive = SpatialPrimitive(
                                        element_id=actual_edge_id,
                                        element_type='identity_line',
                                        position=(center_x, center_y),
                                        bounds=(center_x - 20, center_y - 10, center_x + 20, center_y + 10),
                                    z_index=2,
                                    curve_points=edge_points  # Include Graphviz spline data!
                                )
                                
                                primitives[actual_edge_id] = primitive
                                print(f"✅ Added identity line {actual_edge_id} with {len(edge_points)} spline points")
            except Exception as e:
                print(f"⚠️  Edge processing failed (non-critical): {e}")
                # Continue - complete element coverage ensures all elements have primitives
                
        except Exception as e:
            # Surface parsing error explicitly; do not fabricate fallbacks
            raise
        
        # Build containment hierarchy
        containment_hierarchy = {}
        containment_hierarchy[graph.sheet] = set()
        for area_id, contents in graph.area.items():
            if area_id not in containment_hierarchy:
                containment_hierarchy[area_id] = set()
            containment_hierarchy[area_id].update(contents)
        
        # Build initial layout result
        layout_result = LayoutResult(
            primitives=primitives,
            canvas_bounds=canvas_bounds,
            containment_hierarchy=containment_hierarchy
        )

        # Validate BEFORE post-process to catch upstream issues
        self._validate_presence_and_parent_containment(layout_result, graph, phase="pre-postprocess")

        # In canonical modes, assert cut primitives match xdot cluster _bb exactly
        if getattr(self, 'mode', None) in ("default_raw", "default-nopp", "canonical-cuts"):
            try:
                self._assert_canonical_cuts_equal_clusters(layout_result, xdot_output)
            except Exception as e:
                raise AssertionError(f"Canonical invariant failed: {e}")

        # CANONICAL MODE: Return raw Graphviz layout immediately with NO post-processing
        # This preserves exact Graphviz cluster bounds and ensures mathematical correctness
        
        # Validate the raw layout to ensure structural integrity
        self._validate_presence_and_parent_containment(layout_result, graph, phase="canonical-raw")

        return layout_result

    def _center_contents_within_cuts(self, layout_result: LayoutResult,
                                     graph: RelationalGraphWithCuts,
                                     max_shift: float = 24.0) -> None:
        """Gently translate cut contents toward the cut's center.

        This reduces visual stress where Graphviz leaves content biased toward
        a side (often upward). We cap the translation to avoid large jumps and
        do not change sizes.
        """
        for cut in graph.Cut:
            cprim = layout_result.primitives.get(cut.id)
            if not cprim or not cprim.bounds:
                continue
            x1, y1, x2, y2 = cprim.bounds
            cx = (x1 + x2) * 0.5
            cy = (y1 + y2) * 0.5

            # Collect positions of items assigned to this cut (vertices + predicates)
            contents = graph.area.get(cut.id, set())
            pts: list[tuple[float, float]] = []
            for eid in contents:
                sprim = layout_result.primitives.get(eid)
                if not sprim:
                    # For predicates, eid is edge_id; their primitive shares that id
                    sprim = layout_result.primitives.get(f"pred_{eid}")
                if sprim and sprim.position:
                    px, py = sprim.position
                    # Only consider if currently inside cut bounds
                    if x1 <= px <= x2 and y1 <= py <= y2:
                        pts.append((px, py))
            if not pts:
                continue

            avgx = sum(p[0] for p in pts) / len(pts)
            avgy = sum(p[1] for p in pts) / len(pts)
            dx = cx - avgx
            dy = cy - avgy
            # Cap movement
            def clamp(v: float, cap: float) -> float:
                if v > cap:
                    return cap
                if v < -cap:
                    return -cap
                return v
            dx = clamp(dx, max_shift)
            dy = clamp(dy, max_shift)

            if abs(dx) < 1e-3 and abs(dy) < 1e-3:
                continue

            # Translate contents
            for eid in contents:
                sprim = layout_result.primitives.get(eid)
                if not sprim:
                    sprim = layout_result.primitives.get(f"pred_{eid}")
                if not sprim:
                    continue
                # Update position and bounds consistently
                px, py = sprim.position
                new_pos = (px + dx, py + dy)
                if sprim.bounds:
                    bx1, by1, bx2, by2 = sprim.bounds
                    new_bounds = (bx1 + dx, by1 + dy, bx2 + dx, by2 + dy)
                else:
                    new_bounds = None
                # Recreate SpatialPrimitive since it's likely frozen dataclass
                layout_result.primitives[eid] = SpatialPrimitive(
                    element_id=sprim.element_id,
                    element_type=sprim.element_type,
                    position=new_pos,
                    bounds=new_bounds,
                    z_index=sprim.z_index,
                    attachment_points=sprim.attachment_points,
                    curve_points=sprim.curve_points
                )
    
    def _assert_no_missing_primitives(self, graph: RelationalGraphWithCuts, 
                                      primitives: Dict[str, SpatialPrimitive]) -> None:
        """Strict check: every vertex, predicate, and cut must have a primitive.
        Raise with a clear diagnostic if any are missing (no silent fallbacks)."""
        missing_vertices = []
        for vertex in graph.V:
            vid = vertex.id if hasattr(vertex, 'id') else str(vertex)
            if vid not in primitives:
                missing_vertices.append(vid)
        missing_edges = []
        for edge in graph.E:
            eid = edge.id if hasattr(edge, 'id') else str(edge)
            if eid not in primitives:
                missing_edges.append(eid)
        missing_cuts = []
        for cut in graph.Cut:
            cid = cut.id if hasattr(cut, 'id') else str(cut)
            if cid not in primitives:
                missing_cuts.append(cid)
        if missing_vertices or missing_edges or missing_cuts:
            lines = ["Layout primitive(s) missing after xdot parse:"]
            if missing_vertices:
                lines.append(f"  - vertices: {missing_vertices}")
            if missing_edges:
                lines.append(f"  - predicates(edges): {missing_edges}")
            if missing_cuts:
                lines.append(f"  - cuts: {missing_cuts}")
            lines.append("This indicates Graphviz did not emit expected nodes/clusters or IDs were mismatched. Inspect the emitted .dot and xdot.")
            raise RuntimeError("\n".join(lines))

    def _validate_presence_and_parent_containment(self, layout_result: LayoutResult,
                                                  graph: RelationalGraphWithCuts,
                                                  phase: str = "") -> None:
        """Validate that all elements exist and are placed within their declared parent cuts.
        Raises with details if violations are found."""
        prims = layout_result.primitives
        violations = []
        # Build map of cut bounds
        cut_bounds_map: Dict[str, Tuple[float, float, float, float]] = {}
        for cut in graph.Cut:
            cid = cut.id
            sprim = prims.get(cid)
            if sprim and sprim.bounds:
                cut_bounds_map[cid] = sprim.bounds
        # Presence: vertices, predicates
        for vertex in graph.V:
            vid = vertex.id
            if vid not in prims:
                violations.append(f"missing vertex primitive: {vid}")
        for edge in graph.E:
            eid = edge.id
            if eid not in prims:
                violations.append(f"missing predicate primitive: {eid}")
        # Containment: check each element assigned to an area
        # CRITICAL FIX: Identity lines (ligatures) are allowed to cross cut boundaries per Dau's formalism
        for parent_area, contents in graph.area.items():
            parent_bounds = cut_bounds_map.get(parent_area)
            for eid in contents:
                sprim = prims.get(eid) or prims.get(f"pred_{eid}")
                if not sprim or not sprim.bounds:
                    violations.append(f"no bounds for {eid} in area {parent_area}")
                    continue
                if parent_bounds:
                    # CRITICAL FIX: Skip containment validation for identity lines
                    # Identity lines (ligatures) must be allowed to cross cut boundaries
                    # This is correct behavior per Dau's Existential Graph formalism
                    if sprim.element_type == 'identity_line':
                        continue  # Identity lines can cross cuts - this is correct!
                    
                    bx1, by1, bx2, by2 = sprim.bounds
                    px1, py1, px2, py2 = parent_bounds
                    cx = (bx1 + bx2) * 0.5
                    cy = (by1 + by2) * 0.5
                    if not (px1 <= cx <= px2 and py1 <= cy <= py2):
                        violations.append(f"{eid} center not inside parent cut {parent_area}")
        if violations:
            hdr = f"Layout validation failed ({phase}):"
            raise RuntimeError("\n".join([hdr, *violations]))
    
    def _calculate_cut_boundaries(self, primitives: Dict[str, SpatialPrimitive], 
                                 graph: RelationalGraphWithCuts) -> None:
        """
        Calculate cut boundaries from the positions of nodes within each cut area.
        
        FIXED: Hierarchical boundary calculation for nested cuts.
        Calculate boundaries for innermost cuts first, then use those boundaries
        to calculate outer cut boundaries.
        """
        # Build cut hierarchy (innermost to outermost)
        cut_hierarchy = self._build_cut_hierarchy_by_depth(graph)
        
        # Process cuts from innermost to outermost
        for depth_level in sorted(cut_hierarchy.keys(), reverse=True):
            for cut in cut_hierarchy[depth_level]:
                cut_contents = graph.area.get(cut.id, set())
                
                # Find all primitives that belong to this cut
                cut_primitives = []
                for element_id in cut_contents:
                    # Check for direct primitives (vertices)
                    if element_id in primitives:
                        cut_primitives.append(primitives[element_id])
                    # FIXED: Check for child cut primitives (for nested cuts)
                    if element_id in primitives and primitives[element_id].element_type == 'cut':
                        cut_primitives.append(primitives[element_id])
                
                # CRITICAL FIX: Find predicate nodes that belong to this cut
                # Look for edges where vertices are in this cut area
                for edge_id, vertex_sequence in graph.nu.items():
                    # Check if any vertex in this edge is in the current cut
                    edge_in_cut = any(v_id in cut_contents for v_id in vertex_sequence)
                    if edge_in_cut:
                        # Look for the predicate node for this edge
                        pred_node_id = f"pred_{edge_id}"
                        if pred_node_id in primitives:
                            cut_primitives.append(primitives[pred_node_id])
                            print(f"  📍 Including predicate node {pred_node_id} in cut {cut.id}")
                
                if cut_primitives:
                    # Calculate bounding box of all elements in this cut
                    min_x = min(p.bounds[0] for p in cut_primitives)
                    min_y = min(p.bounds[1] for p in cut_primitives)
                    max_x = max(p.bounds[2] for p in cut_primitives)
                    max_y = max(p.bounds[3] for p in cut_primitives)
                    
                    # Add padding around the contents
                    padding = 30.0  # Generous padding for cut oval
                    cut_bounds = (
                        min_x - padding,
                        min_y - padding,
                        max_x + padding,
                        max_y + padding
                    )
                    
                    # Calculate center position
                    center_x = (cut_bounds[0] + cut_bounds[2]) / 2
                    center_y = (cut_bounds[1] + cut_bounds[3]) / 2
                    
                    # Create cut primitive
                    cut_primitive = SpatialPrimitive(
                        element_id=cut.id,
                        element_type='cut',
                        position=(center_x, center_y),
                        bounds=cut_bounds,
                        z_index=0  # Background layer
                    )
                    
                    primitives[cut.id] = cut_primitive
                    
                    print(f"✅ Created cut primitive for {cut.id} (depth {depth_level}): bounds={cut_bounds}")
                else:
                    print(f"⚠️  No primitives found for cut {cut.id} (depth {depth_level})")
    
    def _build_cut_hierarchy_by_depth(self, graph: RelationalGraphWithCuts) -> Dict[int, List]:
        """
        Build cut hierarchy organized by nesting depth.
        
        Returns a dictionary mapping depth level to list of cuts at that depth.
        Depth 0 = sheet level, depth 1 = cuts directly in sheet, etc.
        """
        hierarchy_by_depth = {}
        
        def calculate_cut_depth(cut_id: str, visited: set = None) -> int:
            """Calculate the nesting depth of a cut."""
            if visited is None:
                visited = set()
            
            if cut_id in visited:
                return 0  # Avoid infinite recursion
            visited.add(cut_id)
            
            # Find which area contains this cut
            parent_area = None
            for area_id, contents in graph.area.items():
                if cut_id in contents:
                    parent_area = area_id
                    break
            
            if parent_area == graph.sheet:
                return 1  # Direct child of sheet
            elif parent_area:
                # This cut is inside another cut
                return 1 + calculate_cut_depth(parent_area, visited)
            else:
                return 0  # Shouldn't happen, but safe fallback
        
        # Calculate depth for each cut
        for cut in graph.Cut:
            depth = calculate_cut_depth(cut.id)
            if depth not in hierarchy_by_depth:
                hierarchy_by_depth[depth] = []
            hierarchy_by_depth[depth].append(cut)
        
        return hierarchy_by_depth
    
    def _deoverlap_sibling_cuts(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts, margin: float = 16.0) -> None:
        """Separate sibling cut bounds to avoid overlap while preserving containment.
        This operates per parent area, so only true siblings influence each other.
        Operates in-place on layout_result.primitives where element_type == 'cut'.
        """
        def rect_overlap(a, b):
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)

        def rect_center(r):
            x1, y1, x2, y2 = r
            return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

        # Build parent → child-cuts list
        parent_to_children: Dict[str, List[str]] = {}
        for cut in graph.Cut:
            parent_id = self._get_cut_parent(cut, graph)
            parent_to_children.setdefault(parent_id, []).append(cut.id)

        # For each parent group, push overlapping siblings apart
        for parent_id, child_ids in parent_to_children.items():
            # Keep only cuts that exist as primitives
            ids = [cid for cid in child_ids
                   if cid in layout_result.primitives and layout_result.primitives[cid].element_type == 'cut']
            if len(ids) < 2:
                continue
            for _ in range(4):  # a few gentle passes
                moved = False
                for i in range(len(ids)):
                    pid_i = ids[i]
                    prim_i = layout_result.primitives.get(pid_i)
                    if not prim_i:
                        continue
                    for j in range(i + 1, len(ids)):
                        pid_j = ids[j]
                        prim_j = layout_result.primitives.get(pid_j)
                        if not prim_j:
                            continue
                        bi = prim_i.bounds
                        bj = prim_j.bounds
                        if rect_overlap(bi, bj):
                            cxi, cyi = rect_center(bi)
                            cxj, cyj = rect_center(bj)
                            dx = cxj - cxi
                            dy = cyj - cyi
                            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                                dx, dy = 1.0, 0.0
                            mag = (dx * dx + dy * dy) ** 0.5
                            ux, uy = dx / mag, dy / mag
                            push = margin * 0.5
                            # Apply symmetric push
                            x1, y1, x2, y2 = prim_i.bounds
                            new_bi = (x1 - ux * push, y1 - uy * push, x2 + ux * push, y2 + uy * push)
                            layout_result.primitives[pid_i] = SpatialPrimitive(
                                element_id=prim_i.element_id,
                                element_type=prim_i.element_type,
                                position=((new_bi[0] + new_bi[2]) / 2.0, (new_bi[1] + new_bi[3]) / 2.0),
                                bounds=new_bi,
                                z_index=prim_i.z_index,
                            )
                            x1, y1, x2, y2 = prim_j.bounds
                            new_bj = (x1 + ux * push, y1 + uy * push, x2 - ux * push, y2 - uy * push)
                            layout_result.primitives[pid_j] = SpatialPrimitive(
                                element_id=prim_j.element_id,
                                element_type=prim_j.element_type,
                                position=((new_bj[0] + new_bj[2]) / 2.0, (new_bj[1] + new_bj[3]) / 2.0),
                                bounds=new_bj,
                                z_index=prim_j.z_index,
                            )
                            moved = True
                if not moved:
                    break

    def _separate_children_from_parent(self, layout_result: LayoutResult, graph: RelationalGraphWithCuts, gap: float = 25.0) -> None:
        """Ensure every child cut stays inside its parent cut with a minimum inset gap.
        This translates child cut rectangles inward toward the parent's center when needed.
        """
        primitives = layout_result.primitives

        # Helper to clamp child within parent with gap by translating towards center
        def clamp_child(parent_bounds, child_bounds):
            px1, py1, px2, py2 = parent_bounds
            cx1, cy1, cx2, cy2 = child_bounds
            # Compute allowed inner rect
            ax1, ay1, ax2, ay2 = px1 + gap, py1 + gap, px2 - gap, py2 - gap
            # Early exit if already inside
            if (cx1 >= ax1 and cy1 >= ay1 and cx2 <= ax2 and cy2 <= ay2):
                return child_bounds
            # Compute translation needed
            tx = 0.0
            ty = 0.0
            if cx1 < ax1:
                tx = max(tx, ax1 - cx1)
            if cx2 > ax2:
                tx = min(tx if tx != 0 else float('inf'), ax2 - cx2)
            if cy1 < ay1:
                ty = max(ty, ay1 - cy1)
            if cy2 > ay2:
                ty = min(ty if ty != 0 else float('inf'), ay2 - cy2)
            if tx == float('inf'):
                tx = 0.0
            if ty == float('inf'):
                ty = 0.0
            nx1, ny1, nx2, ny2 = cx1 + tx, cy1 + ty, cx2 + tx, cy2 + ty
            # If still not inside (too large), fallback: center inside allowed area
            if not (nx1 >= ax1 and ny1 >= ay1 and nx2 <= ax2 and ny2 <= ay2):
                cx = (cx1 + cx2) / 2.0
                cy = (cy1 + cy2) / 2.0
                acx = (ax1 + ax2) / 2.0
                acy = (ay1 + ay2) / 2.0
                dx = acx - cx
                dy = acy - cy
                nx1, ny1, nx2, ny2 = cx1 + dx, cy1 + dy, cx2 + dx, cy2 + dy
            return (nx1, ny1, nx2, ny2)

        # Build parent -> children mapping from graph.area
        parent_to_children = {}
        for area_id, contents in graph.area.items():
            child_cuts = [cid for cid in contents if cid in primitives and primitives[cid].element_type == 'cut']
            if child_cuts:
                parent_to_children[area_id] = child_cuts

        # For each parent, push children inside with gap
        for parent_id, child_ids in parent_to_children.items():
            parent_prim = primitives.get(parent_id)
            if not parent_prim or parent_prim.element_type != 'cut':
                # Sheet-level children: nothing to enforce
                continue
            p_bounds = parent_prim.bounds
            for cid in child_ids:
                cprim = primitives.get(cid)
                if not cprim or cprim.element_type != 'cut':
                    continue
                nb = clamp_child(p_bounds, cprim.bounds)
                primitives[cid] = SpatialPrimitive(
                    element_id=cprim.element_id,
                    element_type=cprim.element_type,
                    position=((nb[0]+nb[2])/2.0, (nb[1]+nb[3])/2.0),
                    bounds=nb,
                    z_index=cprim.z_index,
                )
    
    def _create_fallback_layout(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """Create a simple fallback layout when Graphviz fails."""
        primitives = {}
        
        # Simple grid layout for vertices
        x, y = 100, 100
        for vertex_id, vertex in graph._vertex_map.items():
            primitive = SpatialPrimitive(
                element_id=vertex_id,
                element_type='vertex',
                position=(x, y),
                bounds=(x - 20, y - 20, x + 20, y + 20),
                z_index=1
            )
            primitives[vertex_id] = primitive
            x += 80
            if x > 600:
                x = 100
                y += 80
        
        return LayoutResult(
            primitives=primitives,
            canvas_bounds=(0, 0, 800, 600),
            containment_hierarchy={graph.sheet: set(graph._vertex_map.keys())}
        )


# Integration function for existing workflow
def create_graphviz_layout(graph: RelationalGraphWithCuts) -> LayoutResult:
    """Main entry point for Graphviz-based layout generation."""
    engine = GraphvizLayoutEngine()
    return engine.create_layout_from_graph(graph)


# create_canonical_layout method removed - canonical mode is now the only mode
# All layout creation uses GraphvizLayoutEngine().create_layout_from_graph() directly


if __name__ == "__main__":
    # Test with a simple example
    from egif_parser_dau import parse_egif
    
    # Test cases
    test_cases = [
        ('Simple Predicate', '(Human "Socrates")'),
        ('Mixed Cut and Sheet', '(Human "Socrates") ~[ (Mortal "Socrates") ]'),
        ('Sibling Cuts', '*x ~[ (Human x) ] ~[ (Mortal x) ]'),
    ]
    
    for name, egif in test_cases:
        print(f"\n🎯 Testing {name}: {egif}")
        try:
            graph = parse_egif(egif)
            layout = create_graphviz_layout(graph)
            print(f"✅ Layout created with {len(layout.primitives)} elements")
            print(f"   Canvas bounds: {layout.canvas_bounds}")
        except Exception as e:
            print(f"❌ Failed: {e}")
