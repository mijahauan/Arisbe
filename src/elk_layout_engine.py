"""
ELK-based layout engine for Arisbe EGI diagrams.

Replaces the D3 force-directed engine with ELK's hierarchical compound
graph layout, which natively handles nested containment (cuts) and
cross-boundary edge routing (ligatures).
"""

import heapq
import json
import math
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_dto import LayoutDTO, Point, BoundingBox, LigaturePath
from natural_layout import authorized_crossings
from style_loader import StyleSpecification


class ELKLayoutEngine:
    """Compound graph layout via elkjs subprocess."""

    ELK_WORKER = Path(__file__).parent / "elk_worker.js"

    def generate_layout(
        self,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        layout_deltas: Optional[Dict] = None,
    ) -> LayoutDTO:
        """Generate positioned layout for an EGI diagram."""
        element_sizes = self._compute_element_sizes(egi, style)
        elk_graph = self._egi_to_elk_graph(egi, style, element_sizes)
        positioned = self._run_elk(elk_graph)
        return self._elk_result_to_dto(positioned, egi, style, element_sizes)

    # -------------------------------------------------------------------------
    # Phase 2: EGI → ELK translation
    # -------------------------------------------------------------------------

    def _egi_to_elk_graph(
        self,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        element_sizes: Dict[ElementID, Tuple[float, float]],
    ) -> dict:
        """Convert EGI to ELK JSON graph.

        The sheet becomes the root ELK node.  Each cut becomes a group node
        (compound node with children).  Vertices become leaf nodes.  Predicates
        (edges) become leaf nodes with ports.  ELK edges are included to
        influence node placement (proximity of connected elements) but their
        routing output is NOT used — ligature paths are computed geometrically
        after layout to respect EG area containment semantics.
        """

        # Collect ALL ELK edges here (placed at root = valid LCA for any pair).
        elk_edges: List[dict] = []

        # Build the children list for the sheet area recursively.
        sheet_children = self._build_area_children(
            egi.sheet, egi, style, element_sizes, elk_edges
        )

        root = {
            "id": egi.sheet,
            "layoutOptions": {
                "elk.algorithm": "layered",
                "elk.hierarchyHandling": "INCLUDE_CHILDREN",
                "elk.layered.spacing.nodeNodeBetweenLayers": str(
                    int(style.sibling_spacing)
                ),
                "elk.spacing.nodeNode": str(int(style.element_spacing)),
                "elk.padding": (
                    f"[top={int(style.cut_padding)},"
                    f"left={int(style.cut_padding)},"
                    f"bottom={int(style.cut_padding)},"
                    f"right={int(style.cut_padding)}]"
                ),
                "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
                "elk.direction": "RIGHT",
            },
            "children": sheet_children,
            "edges": elk_edges,
        }

        return root

    def _compute_element_sizes(
        self, egi: RelationalGraphWithCuts, style: StyleSpecification
    ) -> Dict[ElementID, Tuple[float, float]]:
        """Compute (width, height) for every vertex and predicate, matching the D3 engine."""
        sizes: Dict[ElementID, Tuple[float, float]] = {}

        for v in egi.V:
            radius = style.vertex_radius
            circle_size = radius * 2
            label = v.label or ""
            if label:
                text_width = len(label) * 6.2
                text_height = 14.0
                width = circle_size + 8 + text_width + 4
                height = max(circle_size, text_height)
            else:
                width = circle_size
                height = circle_size
            sizes[v.id] = (width, height)

        for e in egi.E:
            label = egi.get_relation_name(e.id)
            char_width = style.predicate_char_width
            text_height = style.predicate_height
            width = len(label) * char_width + 6
            height = text_height + 4
            sizes[e.id] = (width, height)

        return sizes

    def _build_area_children(
        self,
        area_id: ElementID,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        element_sizes: Dict[ElementID, Tuple[float, float]],
        elk_edges: List[dict],  # accumulated at root
    ) -> List[dict]:
        """Build the ELK children list for one area (sheet or cut interior).

        Each element in the area is classified as:
        - A cut  → group node, recurse into its area
        - A vertex → leaf node
        - A predicate (edge) → leaf node with ports; ELK edges are appended to elk_edges
        """
        area_contents: Set[ElementID] = egi.area.get(area_id, frozenset())
        cut_ids: Set[ElementID] = {c.id for c in egi.Cut}
        vertex_ids: Set[ElementID] = {v.id for v in egi.V}
        edge_ids: Set[ElementID] = {e.id for e in egi.E}

        children: List[dict] = []

        for elem_id in area_contents:
            if elem_id in cut_ids:
                # Recurse: this cut becomes a group node
                cut_children = self._build_area_children(
                    elem_id, egi, style, element_sizes, elk_edges
                )
                group_node = {
                    "id": elem_id,
                    "layoutOptions": {
                        "elk.padding": (
                            f"[top={int(style.cut_padding)},"
                            f"left={int(style.cut_padding)},"
                            f"bottom={int(style.cut_padding)},"
                            f"right={int(style.cut_padding)}]"
                        ),
                        "elk.algorithm": "layered",
                        "elk.spacing.nodeNode": str(int(style.element_spacing)),
                    },
                    "children": cut_children,
                }
                children.append(group_node)

            elif elem_id in vertex_ids:
                w, h = element_sizes[elem_id]
                vertex = next(v for v in egi.V if v.id == elem_id)
                node = {
                    "id": elem_id,
                    "width": w,
                    "height": h,
                }
                if vertex.label:
                    node["labels"] = [{"text": vertex.label}]
                children.append(node)

            elif elem_id in edge_ids:
                w, h = element_sizes[elem_id]
                relation_name = egi.get_relation_name(elem_id)
                vertex_seq = egi.nu.get(elem_id, ())

                ports = []
                for port_index, v_id in enumerate(vertex_seq):
                    ports.append({
                        "id": f"{elem_id}_port_{port_index}",
                        "layoutOptions": {
                            "port.side": "EAST" if port_index % 2 == 0 else "WEST"
                        },
                    })
                    elk_edges.append({
                        "id": f"lig|{elem_id}|{port_index}|{v_id}",
                        "source": elem_id,
                        "sourcePort": f"{elem_id}_port_{port_index}",
                        "target": v_id,
                    })

                pred_node = {
                    "id": elem_id,
                    "width": w,
                    "height": h,
                    "labels": [{"text": relation_name}],
                    "ports": ports,
                    "layoutOptions": {
                        "portConstraints": "FREE",
                    },
                }
                children.append(pred_node)

        return children

    # -------------------------------------------------------------------------
    # Subprocess call
    # -------------------------------------------------------------------------

    def _run_elk(self, elk_graph: dict) -> dict:
        """Call elkjs via Node.js subprocess."""
        result = subprocess.run(
            ["node", str(self.ELK_WORKER)],
            input=json.dumps(elk_graph),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ELK layout failed: {result.stderr}")
        return json.loads(result.stdout)

    # -------------------------------------------------------------------------
    # Phase 3: ELK result → LayoutDTO
    # -------------------------------------------------------------------------

    def _elk_result_to_dto(
        self,
        elk_result: dict,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        element_sizes: Dict[ElementID, Tuple[float, float]],
    ) -> LayoutDTO:
        """Convert positioned ELK result to LayoutDTO.

        ELK returns positions relative to the parent node.  We walk the tree
        recursively, accumulating absolute offsets as we descend.
        """
        vertex_positions: Dict[ElementID, Point] = {}
        predicate_positions: Dict[ElementID, Point] = {}
        cut_bounds: Dict[ElementID, BoundingBox] = {}

        cut_ids: Set[ElementID] = {c.id for c in egi.Cut}
        vertex_ids: Set[ElementID] = {v.id for v in egi.V}
        edge_ids: Set[ElementID] = {e.id for e in egi.E}

        def walk(node: dict, offset_x: float, offset_y: float):
            node_id = node["id"]
            nx = node.get("x", 0.0) + offset_x
            ny = node.get("y", 0.0) + offset_y
            nw = node.get("width", 0.0)
            nh = node.get("height", 0.0)

            if node_id in cut_ids or node_id == egi.sheet:
                # Group node / sheet — record bounding box
                if node_id != egi.sheet:
                    cut_bounds[node_id] = BoundingBox(nx, ny, nx + nw, ny + nh)
                # Recurse into children (their positions are relative to this node)
                for child in node.get("children", []):
                    walk(child, nx, ny)
            elif node_id in vertex_ids:
                vertex_positions[node_id] = Point(nx + nw / 2, ny + nh / 2)
            elif node_id in edge_ids:
                predicate_positions[node_id] = Point(nx + nw / 2, ny + nh / 2)

        # The root node's x/y are already absolute (0,0 typically)
        root_x = elk_result.get("x", 0.0)
        root_y = elk_result.get("y", 0.0)
        for child in elk_result.get("children", []):
            walk(child, root_x, root_y)

        # Build ligature paths geometrically from positioned elements.
        # We do NOT use ELK's edge routing — it doesn't understand EG
        # area containment semantics (Peirce's "excised plane" model).
        # Ligatures are routed to avoid unauthorized cut crossings.
        ligature_paths = self._build_ligature_paths(
            egi, vertex_positions, predicate_positions,
            element_sizes, cut_bounds,
        )

        # Area hierarchy
        area_hierarchy = {
            area_id: set(contents)
            for area_id, contents in egi.area.items()
        }

        # Viewport bounds from root node dimensions
        rw = elk_result.get("width", 800.0)
        rh = elk_result.get("height", 600.0)
        margin = style.diagram_margin
        viewport = BoundingBox(
            root_x - margin,
            root_y - margin,
            root_x + rw + margin,
            root_y + rh + margin,
        )

        return LayoutDTO(
            vertex_positions=vertex_positions,
            predicate_positions=predicate_positions,
            cut_bounds=cut_bounds,
            ligature_paths=ligature_paths,
            area_hierarchy=area_hierarchy,
            viewport_bounds=viewport,
            sheet_id=egi.sheet,
            style=style,
        )

    def _build_ligature_paths(
        self,
        egi: RelationalGraphWithCuts,
        vertex_positions: Dict[ElementID, Point],
        predicate_positions: Dict[ElementID, Point],
        element_sizes: Dict[ElementID, Tuple[float, float]],
        cut_bounds: Dict[ElementID, BoundingBox],
    ) -> List[LigaturePath]:
        """Build ligature paths that respect EG area containment.

        A ligature can only cross a cut boundary that lies on the area
        hierarchy path between the predicate's area and the vertex's area.
        All other cuts are obstacles the ligature must route around.
        """
        # Build area hierarchy helpers
        cut_ids = {c.id for c in egi.Cut}
        parent_map: Dict[ElementID, ElementID] = {}
        for area_id, contents in egi.area.items():
            for elem_id in contents:
                if elem_id in cut_ids:
                    parent_map[elem_id] = area_id

        elem_to_area: Dict[ElementID, ElementID] = {}
        for area_id, contents in egi.area.items():
            for elem_id in contents:
                if elem_id not in cut_ids:
                    elem_to_area[elem_id] = area_id

        ligature_paths: List[LigaturePath] = []

        for edge in egi.E:
            vertex_seq = egi.nu.get(edge.id, ())
            pred_center = predicate_positions.get(edge.id)
            if not pred_center:
                continue
            pred_w, pred_h = element_sizes.get(edge.id, (40.0, 16.0))
            pred_area = elem_to_area.get(edge.id)

            for port_index, v_id in enumerate(vertex_seq):
                vert_center = vertex_positions.get(v_id)
                if not vert_center:
                    continue
                vert_area = elem_to_area.get(v_id)

                hook = self._predicate_hook_point(
                    pred_center, pred_w, pred_h, vert_center
                )

                # Determine which cuts this ligature may cross
                authorized = self._authorized_cuts(
                    pred_area, vert_area, parent_map
                )

                # Unauthorized = every other cut that has spatial bounds
                unauthorized_bounds = [
                    cut_bounds[cid]
                    for cid in cut_bounds
                    if cid not in authorized
                ]

                path = self._route_avoiding_cuts(
                    hook, vert_center, unauthorized_bounds
                )

                ligature_paths.append(
                    LigaturePath(
                        predicate_id=edge.id,
                        vertex_id=v_id,
                        points=path,
                        port_index=port_index,
                    )
                )

        return ligature_paths

    # ------------------------------------------------------------------
    # Area hierarchy helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _authorized_cuts(
        pred_area: Optional[ElementID],
        vert_area: Optional[ElementID],
        parent_map: Dict[ElementID, ElementID],
    ) -> Set[ElementID]:
        """Return the cuts a ligature is allowed to cross.

        These are exactly the cuts on the path from *pred_area* up to
        *vert_area* (or vice-versa) in the area hierarchy.  Same-area
        ligatures return an empty set.

        Delegates to the single authoritative crossing computation
        (``natural_layout.authorized_crossings`` →
        ``presentation_ops.crossing_sequence``); the routing only needs
        the membership set, so the ordered sequence is collapsed here.
        """
        return set(authorized_crossings(pred_area, vert_area, parent_map))

    # ------------------------------------------------------------------
    # Predicate hook attachment
    # ------------------------------------------------------------------

    @staticmethod
    def _predicate_hook_point(
        pred_center: Point,
        pred_w: float,
        pred_h: float,
        target: Point,
    ) -> Point:
        """Intersection of ray pred_center→target with the predicate bbox."""
        dx = target.x - pred_center.x
        dy = target.y - pred_center.y

        if abs(dx) < 0.01 and abs(dy) < 0.01:
            return Point(pred_center.x + pred_w / 2, pred_center.y)

        half_w = pred_w / 2
        half_h = pred_h / 2
        t_min = float("inf")

        if dx != 0:
            for sign in (1, -1):
                t = sign * half_w / dx
                if t > 0 and abs(dy * t) <= half_h + 0.1:
                    t_min = min(t_min, t)
        if dy != 0:
            for sign in (1, -1):
                t = sign * half_h / dy
                if t > 0 and abs(dx * t) <= half_w + 0.1:
                    t_min = min(t_min, t)

        if t_min == float("inf"):
            return Point(pred_center.x + half_w, pred_center.y)

        return Point(
            pred_center.x + dx * t_min,
            pred_center.y + dy * t_min,
        )

    # ------------------------------------------------------------------
    # Cut-aware ligature routing
    # ------------------------------------------------------------------

    @classmethod
    def _route_avoiding_cuts(
        cls,
        start: Point,
        end: Point,
        obstacles: List[BoundingBox],
    ) -> Tuple[Point, ...]:
        """Route a polyline from *start* to *end* avoiding *obstacles*.

        Strategy:
        1. Straight line if no unauthorized crossings.
        2. Try four L-shaped detours around the combined bbox of
           crossed obstacles (left / right / top / bottom).
        3. Fall back to a visibility-graph shortest path through the
           padded corners of all obstacle rectangles.
        """
        if not obstacles:
            return (start, end)

        crossed = [b for b in obstacles if cls._seg_crosses_rect(start, end, b)]
        if not crossed:
            return (start, end)

        # --- quick L-shaped detour around combined bbox ---------------
        PAD = 12
        cmin_x = min(b.min_x for b in crossed) - PAD
        cmax_x = max(b.max_x for b in crossed) + PAD
        cmin_y = min(b.min_y for b in crossed) - PAD
        cmax_y = max(b.max_y for b in crossed) + PAD

        candidates = [
            [start, Point(cmin_x, start.y), Point(cmin_x, end.y), end],
            [start, Point(cmax_x, start.y), Point(cmax_x, end.y), end],
            [start, Point(start.x, cmin_y), Point(end.x, cmin_y), end],
            [start, Point(start.x, cmax_y), Point(end.x, cmax_y), end],
        ]

        def _path_ok(path):
            for i in range(len(path) - 1):
                for b in obstacles:
                    if cls._seg_crosses_rect(path[i], path[i + 1], b):
                        return False
            return True

        def _path_len(path):
            return sum(
                math.hypot(path[i + 1].x - path[i].x, path[i + 1].y - path[i].y)
                for i in range(len(path) - 1)
            )

        valid = [((_path_len(p), p)) for p in candidates if _path_ok(p)]
        if valid:
            valid.sort(key=lambda x: x[0])
            return tuple(valid[0][1])

        # --- full visibility-graph fallback ---------------------------
        return cls._route_via_visibility_graph(start, end, obstacles)

    @classmethod
    def _route_via_visibility_graph(
        cls,
        start: Point,
        end: Point,
        obstacles: List[BoundingBox],
    ) -> Tuple[Point, ...]:
        """Shortest obstacle-free path using a visibility graph."""
        PAD = 8
        waypoints: List[Point] = [start, end]
        for b in obstacles:
            waypoints.extend([
                Point(b.min_x - PAD, b.min_y - PAD),
                Point(b.max_x + PAD, b.min_y - PAD),
                Point(b.min_x - PAD, b.max_y + PAD),
                Point(b.max_x + PAD, b.max_y + PAD),
            ])

        n = len(waypoints)

        def _can_see(a: Point, b: Point) -> bool:
            return not any(cls._seg_crosses_rect(a, b, ob) for ob in obstacles)

        # Build adjacency list
        adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                if _can_see(waypoints[i], waypoints[j]):
                    d = math.hypot(
                        waypoints[j].x - waypoints[i].x,
                        waypoints[j].y - waypoints[i].y,
                    )
                    adj[i].append((j, d))
                    adj[j].append((i, d))

        # Dijkstra from 0 (start) to 1 (end)
        dist_arr = [float("inf")] * n
        dist_arr[0] = 0.0
        prev = [-1] * n
        pq: List[Tuple[float, int]] = [(0.0, 0)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist_arr[u]:
                continue
            if u == 1:
                break
            for v, w in adj[u]:
                nd = d + w
                if nd < dist_arr[v]:
                    dist_arr[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        if dist_arr[1] == float("inf"):
            return (start, end)  # no path found — straight line fallback

        path: List[Point] = []
        node = 1
        while node != -1:
            path.append(waypoints[node])
            node = prev[node]
        path.reverse()
        return tuple(path)

    # ------------------------------------------------------------------
    # Geometric primitives
    # ------------------------------------------------------------------

    @staticmethod
    def _seg_crosses_rect(p1: Point, p2: Point, rect: BoundingBox) -> bool:
        """True if segment (p1, p2) crosses *into or out of* rect."""

        def inside(p: Point) -> bool:
            return (
                rect.min_x <= p.x <= rect.max_x
                and rect.min_y <= p.y <= rect.max_y
            )

        p1_in, p2_in = inside(p1), inside(p2)
        if p1_in and p2_in:
            return False
        if p1_in or p2_in:
            return True

        # Both outside — check against four edges of the rect
        corners = [
            (Point(rect.min_x, rect.min_y), Point(rect.max_x, rect.min_y)),
            (Point(rect.max_x, rect.min_y), Point(rect.max_x, rect.max_y)),
            (Point(rect.max_x, rect.max_y), Point(rect.min_x, rect.max_y)),
            (Point(rect.min_x, rect.max_y), Point(rect.min_x, rect.min_y)),
        ]
        for c1, c2 in corners:
            if ELKLayoutEngine._segs_intersect(p1, p2, c1, c2):
                return True
        return False

    @staticmethod
    def _segs_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
        """True if segments (a1,a2) and (b1,b2) properly intersect."""

        def cross(o: Point, a: Point, b: Point) -> float:
            return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

        d1 = cross(b1, b2, a1)
        d2 = cross(b1, b2, a2)
        d3 = cross(a1, a2, b1)
        d4 = cross(a1, a2, b2)

        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
            (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
        ):
            return True
        return False
