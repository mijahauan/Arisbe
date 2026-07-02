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
from typing import Dict, List, Optional, Sequence, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts, ElementID
from layout_dto import LayoutDTO, Point, BoundingBox, LigaturePath
from natural_layout import authorized_crossings
from presentation_ops import predicate_label_box, vertex_label_box
from projection_conventions import Conventions, DEFAULT_CONVENTIONS
from tension_layout import sibling_order
from style_loader import StyleSpecification


class ELKLayoutEngine:
    """Compound graph layout via elkjs subprocess.

    The engine is a *projection* of the coordinate-free NaturalLayout
    into 2-D geometry; the free parameters of that projection live in a
    ``Conventions`` object (``projection_conventions``).  Defaults
    reproduce the behavior in force, so ``ELKLayoutEngine()`` is
    unchanged.
    """

    ELK_WORKER = Path(__file__).parent / "elk_worker.js"

    # Upper bound on the oval-cut refit iterations (see ``_refit_oval_cuts``).
    # Each pass propagates a grown cut up one nesting level, so this caps the
    # supported nesting depth before we accept a near-converged layout; the
    # padding margin keeps it visually safe if the cap is ever reached.
    MAX_OVAL_PASSES = 6

    # Minimum on-screen size for an *empty* cut.  ELK collapses a compound
    # node with no children to a zero-size point, which renders as nothing —
    # so an empty cut (``~[ ]``, and the inner cut of an empty double cut
    # ``~[ ~[ ] ]``) would be invisible despite being a real EG element. We
    # give a childless cut this minimum so it always draws as a visible
    # (small) region.
    EMPTY_CUT_MIN_SIZE = 32.0

    def __init__(self, conventions: Optional[Conventions] = None):
        self.conventions = conventions or DEFAULT_CONVENTIONS

    def generate_layout(
        self,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        layout_deltas: Optional[Dict] = None,
    ) -> LayoutDTO:
        """Generate positioned layout for an EGI diagram."""
        element_sizes = self._compute_element_sizes(egi, style)
        elk_graph = self._egi_to_elk_graph(egi, style, element_sizes)
        try:
            positioned = self._run_elk(elk_graph)
        except RuntimeError:
            # The tension-ordering convention sets ELK's considerModelOrder, which
            # has an elkjs bug on some hierarchical + ported graphs.  Retry once
            # without it: the tension order then degrades to ELK's emergent order
            # for this graph rather than failing.  (No-op when the convention is
            # off — the default — so normal layout never enters this path.)
            if (
                self.conventions.tension_sibling_order
                and not getattr(self, "_suppress_model_order", False)
            ):
                self._suppress_model_order = True
                try:
                    elk_graph = self._egi_to_elk_graph(egi, style, element_sizes)
                    positioned = self._run_elk(elk_graph)
                finally:
                    self._suppress_model_order = False
            else:
                raise
        # Oval cuts (cut_shape "oval"/"circle") need the inscribed ellipse to
        # contain its corner contents — a convention that *feeds the layout*
        # (extra, content-proportional padding), not a cosmetic.  The
        # axis-aligned bbox stays the §3.3 container.  The default
        # rounded-rectangle path skips this entirely and is byte-identical.
        if self._cut_is_oval(style):
            positioned = self._refit_oval_cuts(egi, style, element_sizes, positioned)
        return self._elk_result_to_dto(positioned, egi, style, element_sizes)

    # -------------------------------------------------------------------------
    # Oval-cut refit — feed cut_shape into the layout's padding
    # -------------------------------------------------------------------------

    @staticmethod
    def _cut_is_oval(style: StyleSpecification) -> bool:
        """Whether this style draws cuts as inscribed ellipses (Peirce/Sowa)."""
        return getattr(style, "cut_shape", "rounded_rectangle") in ("oval", "circle")

    @staticmethod
    def _oval_padding(content_w: float, content_h: float) -> Tuple[float, float]:
        """Per-side (horizontal, vertical) padding so an ellipse inscribed in
        the resulting node box contains the centered ``content_w × content_h``
        box.

        An ellipse with semi-axes (A, B) contains a centered axis-aligned box
        of half-extents (w/2, h/2) iff (w/2A)² + (h/2B)² ≤ 1.  Taking the node
        box (and thus the inscribed ellipse's bounding box) to be √2× the
        content in each dimension makes the content's corners lie exactly on
        the ellipse; a small additive margin then puts them strictly inside,
        which also absorbs minor ELK re-arrangement between refit passes.
        """
        k = (math.sqrt(2.0) - 1.0) / 2.0  # ≈ 0.2071: half of (√2 − 1)
        margin = 4.0
        return (content_w * k + margin, content_h * k + margin)

    def _measure_cut_contents(
        self, positioned: dict, cut_ids: Set[ElementID]
    ) -> Dict[ElementID, Tuple[float, float]]:
        """The (width, height) of each cut's *direct children* bounding box, in
        the cut's local coordinates — the content the inscribed ellipse must
        enclose.  Padding lives outside this box, so it is padding-agnostic and
        comparable across refit passes."""
        contents: Dict[ElementID, Tuple[float, float]] = {}

        def visit(node: dict):
            if node["id"] in cut_ids:
                children = node.get("children", [])
                if children:
                    min_x = min(c.get("x", 0.0) for c in children)
                    min_y = min(c.get("y", 0.0) for c in children)
                    max_x = max(c.get("x", 0.0) + c.get("width", 0.0) for c in children)
                    max_y = max(c.get("y", 0.0) + c.get("height", 0.0) for c in children)
                    contents[node["id"]] = (max_x - min_x, max_y - min_y)
                else:
                    contents[node["id"]] = (0.0, 0.0)
            for child in node.get("children", []):
                visit(child)

        visit(positioned)
        return contents

    @staticmethod
    def _contents_stable(
        a: Dict[ElementID, Tuple[float, float]],
        b: Dict[ElementID, Tuple[float, float]],
        tol: float = 2.0,
    ) -> bool:
        if a.keys() != b.keys():
            return False
        return all(
            abs(a[k][0] - b[k][0]) <= tol and abs(a[k][1] - b[k][1]) <= tol
            for k in a
        )

    def _refit_oval_cuts(
        self,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        element_sizes: Dict[ElementID, Tuple[float, float]],
        positioned: dict,
    ) -> dict:
        """Re-lay-out with content-proportional per-cut padding until cut
        contents stop changing.

        Growing one cut grows its parent's content, so a single pass would
        under-pad outer cuts; iterating propagates the growth outward one
        nesting level per pass and converges (deepest cuts stabilize first).
        ``MAX_OVAL_PASSES`` caps it; the margin in ``_oval_padding`` keeps the
        result safe if the cap is hit before exact convergence."""
        cut_ids: Set[ElementID] = {c.id for c in egi.Cut}
        if not cut_ids:
            return positioned

        contents = self._measure_cut_contents(positioned, cut_ids)
        for _ in range(self.MAX_OVAL_PASSES):
            overrides = {
                cid: self._oval_padding(w, h) for cid, (w, h) in contents.items()
            }
            elk_graph = self._egi_to_elk_graph(
                egi, style, element_sizes, pad_overrides=overrides
            )
            positioned = self._run_elk(elk_graph)
            new_contents = self._measure_cut_contents(positioned, cut_ids)
            stable = self._contents_stable(contents, new_contents)
            contents = new_contents
            if stable:
                break
        return positioned

    # -------------------------------------------------------------------------
    # Phase 2: EGI → ELK translation
    # -------------------------------------------------------------------------

    def _egi_to_elk_graph(
        self,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        element_sizes: Dict[ElementID, Tuple[float, float]],
        pad_overrides: Optional[Dict[ElementID, Tuple[float, float]]] = None,
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
            egi.sheet, egi, style, element_sizes, elk_edges, pad_overrides
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
                # Reading axis the layout develops along — honored style knob
                # (layout.direction), default left-to-right.
                "elk.direction": getattr(style, "layout_direction", "RIGHT"),
                **self._model_order_opts(),
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

    def _structural_key(
        self,
        egi: RelationalGraphWithCuts,
        elem_id: ElementID,
        cut_ids: Set[ElementID],
        vertex_ids: Set[ElementID],
        edge_ids: Set[ElementID],
    ):
        """An id-independent sort key describing *what an element is*, so that
        isomorphic subgraphs order their siblings identically.

        Ordered by type rank (edges, then cuts, then vertices), then by
        content: an edge by (relation, arity); a cut *recursively* by the
        sorted keys of its own contents; a vertex by label.  The leading rank
        is an int in every branch, so heterogeneous keys compare safely (the
        deeper, type-specific part is only reached between same-type siblings).
        """
        if elem_id in edge_ids:
            return (0, egi.get_relation_name(elem_id), len(egi.nu.get(elem_id, ())))
        if elem_id in cut_ids:
            child_keys = sorted(
                self._structural_key(egi, c, cut_ids, vertex_ids, edge_ids)
                for c in egi.area.get(elem_id, frozenset())
            )
            return (1, tuple(child_keys))
        # vertex
        v = next((vv for vv in egi.V if vv.id == elem_id), None)
        return (2, (getattr(v, "label", "") or "") if v else "")

    def _model_order_opts(self) -> Dict[str, str]:
        """ELK options that make the layered algorithm respect the *input* child
        order — so a tension-minimized ordering actually survives the layout.

        Applied at the **sheet (root) level only**.  elkjs's ``considerModelOrder``
        has a bug that crashes on nested *ported* groups (the cut interiors), so
        enabling it there fails on ~half the corpus; at the sheet level it is
        crash-free across the whole corpus, and the sheet is where free sibling
        ordering (disconnected sibling cuts) most commonly lives.  Nested-cut
        sibling order is still fed in tension order but left to ELK to honor or
        not (best-effort).  Empty unless the tension convention is on (default
        off → byte-identical output), or after a fallback (see generate_layout)."""
        if not self.conventions.tension_sibling_order:
            return {}
        if getattr(self, "_suppress_model_order", False):
            # A prior pass hit the elkjs considerModelOrder bug on this graph;
            # fall back to ELK's emergent order so layout still succeeds.
            return {}
        return {
            # Honor model (input) order for in-layer node placement...
            "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
            # ...and for the placement of disconnected components (sibling cuts
            # with no line of identity between them — the classic free choice).
            "elk.layered.considerModelOrder.components": "MODEL_ORDER",
        }

    def _build_area_children(
        self,
        area_id: ElementID,
        egi: RelationalGraphWithCuts,
        style: StyleSpecification,
        element_sizes: Dict[ElementID, Tuple[float, float]],
        elk_edges: List[dict],  # accumulated at root
        pad_overrides: Optional[Dict[ElementID, Tuple[float, float]]] = None,
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

        # Feed ELK the children in a deterministic, *structural* order (not the
        # frozenset's id-dependent iteration order).  Two isomorphic areas — a
        # subgraph and an IT+ copy of it — then lay out identically instead of
        # one appearing flipped relative to the other, preserving the visual
        # family resemblance a copy should have (TRANSFORMATION_WORKFLOW_SPEC
        # §2 IT+, §3a continuity).  It also makes layout reproducible across
        # runs regardless of element-id hashing.
        ordered_contents = sorted(
            area_contents,
            key=lambda eid: self._structural_key(
                egi, eid, cut_ids, vertex_ids, edge_ids
            ),
        )

        # Tension ordering (opt-in convention): reorder the area's sibling blocks
        # to minimize ligature tension, tie-broken toward the structural order
        # above (so isomorphic areas still match).  Correspondence-safe — a
        # crossing-sequence is order-independent.  ELK is told to respect model
        # order (see _model_order_opts) so this input order survives the layout.
        if self.conventions.tension_sibling_order:
            ordered_contents = sibling_order(egi, area_id, ordered_contents)

        for elem_id in ordered_contents:
            if elem_id in cut_ids:
                # Recurse: this cut becomes a group node
                cut_children = self._build_area_children(
                    elem_id, egi, style, element_sizes, elk_edges, pad_overrides
                )
                # An oval refit pass supplies content-proportional padding per
                # cut; without it (every Dau render, and the oval styles' first
                # pass) the uniform integer cut_padding is used verbatim, so the
                # rounded-rectangle output is byte-identical.
                if pad_overrides is not None and elem_id in pad_overrides:
                    ph, pv = pad_overrides[elem_id]
                    padding_str = (
                        f"[top={pv:.2f},left={ph:.2f},"
                        f"bottom={pv:.2f},right={ph:.2f}]"
                    )
                else:
                    padding_str = (
                        f"[top={int(style.cut_padding)},"
                        f"left={int(style.cut_padding)},"
                        f"bottom={int(style.cut_padding)},"
                        f"right={int(style.cut_padding)}]"
                    )
                group_layout_options = {
                    "elk.padding": padding_str,
                    "elk.algorithm": "layered",
                    "elk.spacing.nodeNode": str(int(style.element_spacing)),
                    # Nested cuts develop along the same reading axis as the root.
                    "elk.direction": getattr(style, "layout_direction", "RIGHT"),
                    # NOTE: model-order is intentionally NOT set on nested groups
                    # — elkjs's considerModelOrder crashes on ported cut interiors
                    # (see _model_order_opts).  Sibling order is enforced at the
                    # sheet level only; nested children are best-effort.
                }
                group_node = {
                    "id": elem_id,
                    "layoutOptions": group_layout_options,
                    "children": cut_children,
                }
                if not cut_children:
                    # An empty cut has no children to size it; ELK would
                    # collapse it to a zero-size point (invisible). Enforce a
                    # visible minimum so the cut still draws — covers ``~[ ]``
                    # and the inner cut of an empty double cut ``~[ ~[ ] ]``.
                    m = self.EMPTY_CUT_MIN_SIZE
                    group_node["width"] = m
                    group_node["height"] = m
                    group_layout_options["elk.nodeSize.constraints"] = "MINIMUM_SIZE"
                    group_layout_options["elk.nodeSize.minimum"] = f"({m},{m})"
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
            element_sizes, cut_bounds, style,
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
        style: Optional[StyleSpecification] = None,
    ) -> List[LigaturePath]:
        """Build ligature paths that respect EG area containment.

        A ligature can only cross a cut boundary that lies on the area
        hierarchy path between the predicate's area and the vertex's area.
        Those cuts are **hard** obstacles — never crossed (soundness).

        **Label boxes are soft obstacles.**  A line of identity running through
        a label box it is *not* incident to strikes the text out — a genuine
        occlusion (§3.3 occlusion check #3, ``correspondence_attestation``).  So
        the router also skirts every non-incident label box, but only when a
        detour exists that still avoids the forbidden cuts: legibility yields to
        soundness, never the reverse.  The motivating case is the shared-vertex
        fan-in after IT+ (N predicates → one vertex, the lines crossing
        intervening predicate boxes — ``roberts_domain_modeling``).

        ``style`` supplies the drawn label-box extents (the same
        ``predicate_label_box`` / ``vertex_label_box`` the §3.3 check reads, so
        what the router avoids is exactly what the check tests).  When ``style``
        is ``None`` no label boxes are avoided (cut-only routing, the old
        behavior).
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

        # Pass 1: provisional straight hook→vertex paths.  These pin the hooks
        # (reused below) and supply the incident directions that place vertex
        # labels — routing only bends a line's *middle*, so the endpoints, and
        # therefore the label placement, are stable across the real pass.
        hooks: Dict[Tuple[ElementID, int], Point] = {}
        provisional: List[LigaturePath] = []
        for edge in egi.E:
            pred_center = predicate_positions.get(edge.id)
            if not pred_center:
                continue
            pred_w, pred_h = element_sizes.get(edge.id, (40.0, 16.0))
            for port_index, v_id in enumerate(egi.nu.get(edge.id, ())):
                vert_center = vertex_positions.get(v_id)
                if not vert_center:
                    continue
                hook = self._predicate_hook_point(
                    pred_center, pred_w, pred_h, vert_center
                )
                hooks[(edge.id, port_index)] = hook
                provisional.append(
                    LigaturePath(
                        predicate_id=edge.id, vertex_id=v_id,
                        points=(hook, vert_center), port_index=port_index,
                    )
                )

        # Label boxes (owner-tagged soft obstacles).  Predicate boxes are fixed
        # on the predicate; vertex boxes are placed from the provisional
        # directions, exactly as the renderer and §3.3 do.
        label_boxes: List[Tuple[str, ElementID, BoundingBox]] = []
        if style is not None:
            show_vertex_labels = (
                getattr(style, "vertex_rendering_mode", "dot_and_label")
                != "dot_only"
            )
            for edge in egi.E:
                c = predicate_positions.get(edge.id)
                if c is None:
                    continue
                label_boxes.append((
                    "predicate", edge.id,
                    predicate_label_box(egi.get_relation_name(edge.id), c, style),
                ))
            if show_vertex_labels:
                for vertex in egi.V:
                    if not getattr(vertex, "label", None):
                        continue
                    c = vertex_positions.get(vertex.id)
                    if c is None:
                        continue
                    label_boxes.append((
                        "vertex", vertex.id,
                        vertex_label_box(
                            vertex.label, c, style, provisional, vertex.id,
                            egi=egi, cut_bounds=cut_bounds,
                        ),
                    ))

        # Pass 2: real routing — hard obstacles = forbidden cuts; soft = label
        # boxes this ligature is not incident to.
        ligature_paths: List[LigaturePath] = []
        for edge in egi.E:
            if predicate_positions.get(edge.id) is None:
                continue
            pred_area = elem_to_area.get(edge.id)

            for port_index, v_id in enumerate(egi.nu.get(edge.id, ())):
                vert_center = vertex_positions.get(v_id)
                hook = hooks.get((edge.id, port_index))
                if vert_center is None or hook is None:
                    continue
                vert_area = elem_to_area.get(v_id)

                authorized = self._authorized_cuts(
                    pred_area, vert_area, parent_map
                )
                hard = [
                    cut_bounds[cid]
                    for cid in cut_bounds
                    if cid not in authorized
                ]
                soft = [
                    box
                    for kind, owner, box in label_boxes
                    if not (
                        (kind == "predicate" and owner == edge.id)
                        or (kind == "vertex" and owner == v_id)
                    )
                ]

                path = self._route_avoiding_cuts(
                    hook, vert_center, hard, soft_obstacles=soft,
                    detour_pad=self.conventions.detour_pad,
                    visibility_pad=self.conventions.visibility_pad,
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
    # Re-derive ligature endpoints from element geometry (regime-3 edits)
    # ------------------------------------------------------------------

    def rebuild_ligature_anchors(
        self,
        egi: RelationalGraphWithCuts,
        dto: LayoutDTO,
    ) -> LayoutDTO:
        """Re-derive each ligature's *endpoints* from the current element
        geometry, preserving any interior waypoints.

        A ligature's attachment is a **floating/perimeter anchor**, not a stored
        pixel fact: the predicate-side endpoint is the point on the predicate's
        box facing the connected vertex (``_predicate_hook_point``), and the
        vertex-side endpoint is the vertex position.  The full ELK pass already
        computes these; the regime-3 edit ops (``move_vertex`` /
        ``move_predicate`` / ``move_cut``) only translate the old endpoints, so
        after a move the hook no longer faces the line's new incident direction.
        This recomputes both endpoints so the attachment *follows the geometry*
        — the same derive-don't-store discipline as the cold layout.

        It is **idempotent** on an unedited layout (the hook is computed toward
        the vertex centre, exactly as ``_build_ligature_paths`` does) and
        **interior-preserving** (an explicit ``reroute_ligature`` waypoint
        survives — only the endpoints are touched).  A move that would require a
        *new* cut detour is not re-routed here; the §3.3 attestation downstream
        refuses such a result, so correspondence still holds.

        Returns a new ``LayoutDTO``; the input is not mutated.
        """
        import dataclasses

        sizes = self._compute_element_sizes(egi, dto.style)
        new_paths: List[LigaturePath] = []
        for lp in dto.ligature_paths:
            pts = list(lp.points)
            pred_center = dto.predicate_positions.get(lp.predicate_id)
            vert_pos = dto.vertex_positions.get(lp.vertex_id)
            if len(pts) < 2 or pred_center is None or vert_pos is None:
                new_paths.append(lp)
                continue
            pw, ph = sizes.get(lp.predicate_id, (40.0, 16.0))
            pts[-1] = vert_pos
            pts[0] = self._predicate_hook_point(pred_center, pw, ph, vert_pos)
            new_paths.append(
                LigaturePath(
                    predicate_id=lp.predicate_id,
                    vertex_id=lp.vertex_id,
                    points=tuple(pts),
                    port_index=lp.port_index,
                )
            )
        return dataclasses.replace(dto, ligature_paths=new_paths)

    # ------------------------------------------------------------------
    # Cut-aware ligature routing
    # ------------------------------------------------------------------

    @classmethod
    def _route_avoiding_cuts(
        cls,
        start: Point,
        end: Point,
        obstacles: List[BoundingBox],
        soft_obstacles: Sequence[BoundingBox] = (),
        detour_pad: float = DEFAULT_CONVENTIONS.detour_pad,
        visibility_pad: float = DEFAULT_CONVENTIONS.visibility_pad,
    ) -> Tuple[Point, ...]:
        """Route a polyline from *start* to *end* avoiding *obstacles* — the
        **taut-line router**: a line of identity pulled taut, hugging the cuts it
        must skirt (the rubber-band-around-pegs of ``docs/TENSION_LAYOUT.md``).

        Two tiers of obstacle:

        - ``obstacles`` (**hard** — the forbidden cuts) must never be crossed.
          This is soundness: a ligature that dips into a cut off its area chain
          would change what the picture says.
        - ``soft_obstacles`` (the non-incident **label boxes**) are skirted for
          legibility — a line through a label box strikes the text out — but
          *only when a detour exists that still avoids every hard obstacle*.  If
          honouring a label would force a crossing of a forbidden cut, the label
          is given up and the sound hard-only route is kept.

        Strategy:
        1. Straight line if it crosses nothing (the shortest path there is).
        2. Otherwise the **visibility-graph shortest path** through the padded
           corners of hard ∪ soft.  A finite such path avoids every obstacle in
           the set — the hard cuts included — so it is sound by construction.
        3. If no path avoids hard ∪ soft (labels over-constrain), fall back to
           routing against the hard obstacles alone (still sound).

        ``detour_pad`` is retained for signature compatibility but no longer
        used; ``visibility_pad`` is the obstacle corner standoff convention.
        """
        hard = list(obstacles)
        soft = list(soft_obstacles)

        def _route(obs: List[BoundingBox]) -> Tuple[Point, ...]:
            if not obs:
                return (start, end)
            if not any(cls._seg_crosses_rect(start, end, b) for b in obs):
                return (start, end)
            return cls._route_via_visibility_graph(
                start, end, obs, pad=visibility_pad
            )

        if not soft:
            return _route(hard)

        # Try hard ∪ soft.  ``_route_via_visibility_graph`` returns the straight
        # ``(start, end)`` only when it finds *no* obstacle-free path (Dijkstra
        # exhausted); a genuine detour has interior waypoints.  So a returned
        # path that still crosses something signals over-constraint → fall back
        # to the sound hard-only route.
        combined = hard + soft
        path = _route(combined)
        if not any(
            cls._seg_crosses_rect(path[i], path[i + 1], b)
            for i in range(len(path) - 1)
            for b in combined
        ):
            return path
        return _route(hard)

    @classmethod
    def _route_via_visibility_graph(
        cls,
        start: Point,
        end: Point,
        obstacles: List[BoundingBox],
        pad: float = DEFAULT_CONVENTIONS.visibility_pad,
    ) -> Tuple[Point, ...]:
        """Shortest obstacle-free path using a visibility graph.

        ``pad`` is the obstacle-corner standoff convention."""
        PAD = pad
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
        # Exact quick reject: a segment wholly to one side of the rect cannot touch it.
        # (Pure prefilter — strict inequalities, so boundary-touching cases still take the
        # full test below and results are bit-identical.) The visibility-graph build tests
        # O(waypoints² × obstacles) segment/rect pairs, almost all far apart; without this
        # a checkpoint attest of a ~50-atom star-shaped M measured ~450 s (2026-07-02).
        if (
            (p1.x < rect.min_x and p2.x < rect.min_x)
            or (p1.x > rect.max_x and p2.x > rect.max_x)
            or (p1.y < rect.min_y and p2.y < rect.min_y)
            or (p1.y > rect.max_y and p2.y > rect.max_y)
        ):
            return False

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
