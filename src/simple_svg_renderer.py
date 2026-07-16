"""
Simple SVG Renderer (LayoutDTO → SVG; ELK layout path)

Renders the new LayoutDTO format directly to SVG.
No adapters, no conversions - clean and simple.

Author: Refactored for architectural consistency
Date: 2025-10-12
"""

import math
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

import render_geometry as rg
from layout_dto import LayoutDTO
from presentation_ops import place_label_boxes, predicate_label_box, vertex_label_box
from egi_core_dau import RelationalGraphWithCuts


class SimpleSVGRenderer:
    """Renders LayoutDTO to SVG format."""
    
    def render_to_svg(
        self,
        dto: LayoutDTO,
        title: str = "",
        egif: str = "",
        egi: Optional[RelationalGraphWithCuts] = None,
        reference_marks: Optional[Dict[str, int]] = None,
        quotation_marks: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
        """
        Convert LayoutDTO to SVG string.

        Args:
            dto: Layout data from unified D3 engine (includes style)
            title: Diagram title
            egif: EGIF linear form for display
            egi: EGI model for labels
            reference_marks: optional {predicate_id: horizon} — decorate those
                predicate spots as reference / transclusion nodes (a dashed spot +
                a "+N beyond view" badge), reusing the overview horizon idiom.
                Pure chrome: it reads the overlay (``reference_node.render_marks``),
                never the EGI, and changes no DTO geometry, so §3.3 (which reads the
                DTO) is untouched. Default ``None`` is byte-identical to before.
            quotation_marks: optional {element_id: {"sort", "horizon"}} — decorate
                those vertex spots as second-order quoting names (Peirce's device:
                a dotted oval around the name + a "⌜+N⌝" badge for the quoted
                graph's element count), fed by
                ``quotation_overlay.render_quotation_marks``. Same discipline as
                reference_marks: pure chrome, off by default, no DTO change —
                Stage ⓪'s glyph (the sort itself is overlay, not drawing; S3 is
                honestly not claimed by this ink).

        Returns:
            SVG string
        """
        reference_marks = reference_marks or {}
        quotation_marks = quotation_marks or {}
        
        # Use style from DTO (already contains Dau style specification)
        style = dto.style
        if style is None:
            from style_loader import StyleLoader
            style = StyleLoader().load_default_style()

        # Honor the declared style's ink, script, and ligature character.
        # Defaults reproduce Dau's hardcoded look exactly, so Dau output is
        # byte-identical; Peirce/Sowa supply their own values.  This is the
        # projection's *visual realization* layer (docs/MANIFEST_AND_MEANING):
        # manifest varies, meaning (and §3.3, which reads the DTO not the ink)
        # does not.
        _raw = style.raw_style_data
        cut_line_color = _raw.get("cut", {}).get("line_color", "#000000")
        ligature_color = _raw.get("ligature", {}).get("color", "#000000")
        predicate_label_color = _raw.get("predicate", {}).get("label_color", "#000000")
        vertex_label_color = _raw.get("vertex", {}).get("label_color", "#000000")
        # The reference-node accent (increment 1b): a distinct ink for a reference
        # spot's dashed box + its "+N beyond view" horizon badge.  Style-overridable;
        # the default is a neutral blue that reads as "pointer, not primitive".
        reference_accent = _raw.get("reference", {}).get("accent_color", "#7287fd")
        # The quotation accent (second-order Stage ⓪): a distinct ink for the
        # dotted oval + "⌜+N⌝" badge of a quoting name.  Style-overridable; the
        # default is a violet that reads as "mention, one order up".
        quotation_accent = _raw.get("quotation", {}).get("accent_color", "#ca9ee6")
        font_style = _raw.get("global", {}).get("font_style", "normal")
        ligature_routing = _raw.get("ligature", {}).get("routing_mode", "orthogonal")
        # A cut is drawn as an inscribed ellipse (Peirce/Sowa "oval") or a
        # rounded rectangle (Dau).  The layout engine has already grown an oval
        # cut's box so the inscribed ellipse contains its contents; the
        # axis-aligned bbox remains the §3.3 container either way.
        cut_shape = getattr(style, "cut_shape", "rounded_rectangle")
        # Hand-drawn quality (Peirce): a small, *deterministic* wobble applied
        # to the cut outline and the line of identity.  It perturbs only the
        # drawn stroke, never the DTO geometry §3.3 reads (which has already
        # been attested before the renderer runs) — exactly as Tier 1's curves.
        # Zero (Dau, Sowa) leaves a crisp ellipse/rect/line, byte-identical.
        cut_wobble = float(_raw.get("cut", {}).get("hand_drawn_variation", 0.0))
        lig_wobble = float(_raw.get("ligature", {}).get("hand_drawn_variation", 0.0))
        # Conventions.ligature_crossing_marks: when a style declares
        # "bridges" (Peirce's own device), two distinct lines of identity
        # that cross in this 2-D projection get a hop where one lifts over
        # the other — the §3.0 convention that recovers a distinction a
        # projection would otherwise collapse.  Default "none" leaves
        # crossings unmarked (Dau, Sowa), byte-identical to before.
        lig_crossing_marks = _raw.get("ligature", {}).get("crossing_marks", "none")
        
        # Calculate SVG dimensions from viewport (less padding for better fit)
        svg_width = int(dto.viewport_bounds.width + 80)
        svg_height = int(dto.viewport_bounds.height + 120)
        
        # Create SVG root with viewBox for proper scaling
        svg = ET.Element("svg", {
            "width": "100%",
            "height": "100%",
            "viewBox": f"0 0 {svg_width} {svg_height}",
            "preserveAspectRatio": "xMidYMid meet",
            "xmlns": "http://www.w3.org/2000/svg"
        })
        
        # Background
        ET.SubElement(svg, "rect", {
            "x": "0", "y": "0",
            "width": str(svg_width), "height": str(svg_height),
            "fill": "white", "stroke": "none"
        })
        
        # Title — only when a caller explicitly asks for one.  The default
        # render carries none: every drawing being an "Existential Graph" is
        # redundant chrome, and the page chrome already names the UoD.
        if title:
            ET.SubElement(svg, "text", {
                "x": "10", "y": "25",
                "font-size": "16", "font-weight": "bold",
                "fill": "#333"
            }).text = title
        
        # Content offset - shift viewport to canvas position
        # Viewport min_x/min_y tell us where diagram starts, so negate them
        # to bring it to origin, then add small margin
        offset_x = -dto.viewport_bounds.min_x + 40
        offset_y = -dto.viewport_bounds.min_y + 65
        
        # Compute cut nesting depths for polarity shading
        cut_depths = self._compute_cut_depths(egi) if egi else {}
        
        # Create groups for proper layering
        cut_group = ET.SubElement(svg, "g", {"id": "cuts"})
        ligature_group = ET.SubElement(svg, "g", {"id": "ligatures"})
        element_group = ET.SubElement(svg, "g", {"id": "elements"})
        
        # ====================================================================
        # Render Cuts (sorted by depth - sheet first, then nested)
        # ====================================================================
        
        # Sort cuts by nesting depth: shallowest first (bottom layer),
        # deepest last (top layer).  This ensures even-depth white fills
        # properly cover odd-depth gray fills beneath them.
        cuts_to_render = []
        for cut_id, bounds in dto.cut_bounds.items():
            is_sheet = (cut_id == dto.sheet_id)
            depth = cut_depths.get(cut_id, 0)
            cuts_to_render.append((cut_id, bounds, is_sheet, depth))
        
        cuts_to_render.sort(key=lambda x: (not x[2], x[3]))
        
        for cut_id, bounds, is_sheet, _ in cuts_to_render:
            # SKIP the sheet - it's invisible/infinite in Dau's formalism
            if is_sheet:
                continue

            # Regular cut - use Dau style
            x = bounds.min_x + offset_x
            y = bounds.min_y + offset_y
            width = bounds.width
            height = bounds.height

            # Polarity shading: odd depth (negative) → gray, even depth → opaque white
            # Even-depth fills MUST be opaque to cover the gray of their parent cut.
            depth = cut_depths.get(cut_id, 1)
            if style.alternating_shading_enabled:
                if depth % 2 == 1:
                    fill_color = style.odd_polarity_fill
                else:
                    fill_color = style.even_polarity_fill if style.even_polarity_fill != "transparent" else "#FFFFFF"
            else:
                fill_color = "none"

            # Wrap in a named group so the frontend can detect clicks by element ID
            cut_g = ET.SubElement(cut_group, "g", {
                "id": cut_id,
                "data-element-id": cut_id,
                "data-element-type": "cut",
                "cursor": "pointer",
            })
            freeform = (getattr(dto, "cut_boundary", None) or {}).get(cut_id)
            if freeform:
                # A human-drawn cut: draw its literal polyline (the curve §3.3 and
                # the browser both read for containment — one source of truth).
                d = "M " + " L ".join(
                    f"{pt.x + offset_x:.2f} {pt.y + offset_y:.2f}" for pt in freeform
                ) + " Z"
                ET.SubElement(cut_g, "path", {
                    "d": d,
                    "fill": fill_color,
                    "stroke": cut_line_color,
                    "stroke-width": str(style.cut_line_width),
                })
            elif cut_shape in ("oval", "circle") and cut_wobble > 0:
                # Peirce's hand: a slightly irregular closed loop instead of a
                # perfect ellipse.  Amplitude stays well under the Tier-2
                # containment margin, so contents remain enclosed.
                d = self._wobbled_oval_path(
                    x + width / 2, y + height / 2, width / 2, height / 2,
                    amplitude=cut_wobble * 3.0, seed=cut_id,
                )
                ET.SubElement(cut_g, "path", {
                    "d": d,
                    "fill": fill_color,
                    "stroke": cut_line_color,
                    "stroke-width": str(style.cut_line_width),
                })
            elif cut_shape in ("oval", "circle"):
                ET.SubElement(cut_g, "ellipse", {
                    "cx": str(x + width / 2), "cy": str(y + height / 2),
                    "rx": str(width / 2), "ry": str(height / 2),
                    "fill": fill_color,
                    "stroke": cut_line_color,
                    "stroke-width": str(style.cut_line_width)
                })
            else:
                ET.SubElement(cut_g, "rect", {
                    "x": str(x), "y": str(y),
                    "width": str(width), "height": str(height),
                    "rx": str(style.cut_corner_radius),
                    "ry": str(style.cut_corner_radius),
                    "fill": fill_color,
                    "stroke": cut_line_color,
                    "stroke-width": str(style.cut_line_width)
                })
        
        # ====================================================================
        # Render Ligatures (line of identity)
        # ====================================================================
        
        # Get cap style from style specification
        ligature_cap_style = style.raw_style_data.get('ligature', {}).get('cap_style', 'butt')

        # Argument-order numerals: a line carries a number iff its DTO sets
        # LigaturePath.order_label (eg_reader.assign_order_labels decides per the
        # style's convention — every ≥2-ary line under "numbered"/Dau §11.2; only
        # the lines a "clockwise"/Peirce placement can't disambiguate, the
        # Convention-13 override).  The renderer just draws what the DTO says, so
        # picture and reader agree on the same numeral.
        _an = style.raw_style_data.get("arity_numbers", {})
        num_font_size = _an.get("font_size", 8)
        num_color = _an.get("color", "#666666")

        for lig in dto.ligature_paths:
            if len(lig.points) < 2:
                continue

            # Build the path.  An "organic"/"natural" routing draws Peirce's
            # flowing line of identity (a smooth curve through the same layout
            # points); orthogonal/other draws Dau's straight segments.  A
            # non-zero ligature wobble (Peirce) first nudges the interior points
            # off the polyline for a hand-drawn waver, then smooths.  Both the
            # curve and the waver pass close to every authorized layout point —
            # endpoints are fixed and the amplitude stays under the routing
            # clearance — so §3.3 (which reads the DTO geometry, not the drawn
            # stroke) is unaffected.
            pts = lig.points
            if lig_wobble > 0:
                seed = f"{lig.predicate_id}|{lig.vertex_id}|{lig.port_index}"
                pts = self._hand_drawn_points(pts, lig_wobble * 2.0, seed)
            if ligature_routing in ("organic", "natural", "curved") or lig_wobble > 0:
                path_d = self._smooth_path(pts, offset_x, offset_y)
            else:
                path_d = f"M {pts[0].x + offset_x} {pts[0].y + offset_y}"
                for point in pts[1:]:
                    path_d += f" L {point.x + offset_x} {point.y + offset_y}"

            # Main ligature line - no hooks, cap style from style spec.
            # The (predicate, vertex, port) triple uniquely keys this path, so
            # the canvas can address it for a regime-3 reroute (Settle ④b).
            ET.SubElement(ligature_group, "path", {
                "d": path_d,
                "stroke": ligature_color,
                "stroke-width": str(style.ligature_line_width),
                "stroke-linecap": ligature_cap_style,
                "fill": "none",
                "class": "ligature-path",
                "data-predicate-id": str(lig.predicate_id),
                "data-vertex-id": str(lig.vertex_id),
                "data-port-index": str(lig.port_index),
            })

            # Argument-order numeral on this line (1-based), set just off the
            # predicate-end, drawn iff the DTO assigned one.
            if getattr(lig, "order_label", None) is not None:
                hook, nxt = pts[0], pts[1]
                dx, dy = nxt.x - hook.x, nxt.y - hook.y
                seg = math.hypot(dx, dy) or 1.0
                ux, uy = dx / seg, dy / seg
                lx = hook.x + ux * 15.0 - uy * 6.0 + offset_x
                ly = hook.y + uy * 15.0 + ux * 6.0 + offset_y
                num = ET.SubElement(ligature_group, "text", {
                    "x": f"{lx:.1f}", "y": f"{ly:.1f}",
                    "font-family": style.font_family,
                    "font-size": str(num_font_size),
                    "fill": num_color,
                    "text-anchor": "middle",
                    "dominant-baseline": "central",
                    "class": "arg-order-number",
                    "data-predicate-id": str(lig.predicate_id),
                    "data-port-index": str(lig.port_index),
                })
                num.text = str(lig.order_label)

        # ====================================================================
        # Bridge marks (Peirce's hop) at ligature crossings — drawn on top of
        # the ligatures so the over-line lifts cleanly over the under-line.
        # Stroke-only and convention-gated: nothing here touches DTO geometry,
        # and a style that doesn't declare "bridges" emits no <g id="bridges">.
        # ====================================================================
        crossings = rg.ligature_crossings(dto.ligature_paths) if lig_crossing_marks == "bridges" else []
        if crossings:
            bridges_group = ET.SubElement(svg, "g", {"id": "bridges"})
            radius = max(6.0, style.ligature_line_width * 2.5)
            for cr in crossings:
                br = rg.bridge_path(cr, radius)
                ax, ay = br.a[0] + offset_x, br.a[1] + offset_y
                bx, by = br.b[0] + offset_x, br.b[1] + offset_y
                # 1. erase the over-line's straight passage through the crossing
                ET.SubElement(bridges_group, "line", {
                    "x1": f"{ax:.2f}", "y1": f"{ay:.2f}",
                    "x2": f"{bx:.2f}", "y2": f"{by:.2f}",
                    "stroke": "#FFFFFF",
                    "stroke-width": f"{style.ligature_line_width + 1.0}",
                    "stroke-linecap": "round",
                })
                # 2. restore the under-line straight through the crossing
                uax, uay = br.under_a[0] + offset_x, br.under_a[1] + offset_y
                ubx, uby = br.under_b[0] + offset_x, br.under_b[1] + offset_y
                ET.SubElement(bridges_group, "line", {
                    "x1": f"{uax:.2f}", "y1": f"{uay:.2f}",
                    "x2": f"{ubx:.2f}", "y2": f"{uby:.2f}",
                    "stroke": ligature_color,
                    "stroke-width": str(style.ligature_line_width),
                    "stroke-linecap": "round",
                })
                # 3. the hop arc (the over-line lifting over)
                c1x, c1y = br.c1[0] + offset_x, br.c1[1] + offset_y
                c2x, c2y = br.c2[0] + offset_x, br.c2[1] + offset_y
                ET.SubElement(bridges_group, "path", {
                    "d": (f"M {ax:.2f} {ay:.2f} C {c1x:.2f} {c1y:.2f} "
                          f"{c2x:.2f} {c2y:.2f} {bx:.2f} {by:.2f}"),
                    "stroke": ligature_color,
                    "stroke-width": str(style.ligature_line_width),
                    "stroke-linecap": "round",
                    "fill": "none",
                })

        # ====================================================================
        # Render Vertices
        # ====================================================================

        # Global, sibling-aware label placement — the single source of truth the
        # §3.3 occlusion attest also reads (presentation_ops.place_label_boxes), so
        # a crowded pair of long labels is placed to avoid each other and the drawn
        # picture is exactly what attest verifies (docs/EXACT_CORRESPONDENCE.md
        # Phase 3b; the F1⁵ coin-flip fix, runs/RUN_5_LOG.md).
        _label_boxes = {}
        if egi is not None:
            _label_boxes = place_label_boxes(
                egi, dto.predicate_positions, dto.vertex_positions,
                dto.ligature_paths, dto.cut_bounds, style,
                show_vertex_labels=(style.vertex_rendering_mode != "dot_only"),
            )

        for v_id, pos in dto.vertex_positions.items():
            cx = pos.x + offset_x
            cy = pos.y + offset_y

            # Get vertex label from EGI
            label = ""
            if egi:
                v = next((v for v in egi.V if v.id == v_id), None)
                if v and v.label:
                    label = v.label

            # Is this vertex a second-order quoting name? (overlay, not the
            # EGI — chrome only, exactly as reference spots are.)
            quotation = quotation_marks.get(v_id)

            # Wrap in a named group so the frontend can detect clicks by element ID
            v_attrs_g = {
                "id": v_id,
                "data-element-id": v_id,
                "data-element-type": "vertex",
                "cursor": "pointer",
            }
            if quotation is not None:
                v_attrs_g["class"] = "quotation-spot"
                v_attrs_g["data-quotation"] = "true"
                v_attrs_g["data-quotation-sort"] = str(quotation.get("sort", ""))
                v_attrs_g["data-quotation-horizon"] = str(quotation.get("horizon", 0))
            v_g = ET.SubElement(element_group, "g", v_attrs_g)

            # Transparent hit area (larger than the dot) for easier clicking
            hit = style.vertex_radius + 6
            ET.SubElement(v_g, "rect", {
                "x": str(cx - hit), "y": str(cy - hit),
                "width": str(hit * 2), "height": str(hit * 2),
                "fill": "transparent", "stroke": "none",
            })

            # Vertex circle - only draw if rendering_mode includes "dot"
            show_dot = style.vertex_rendering_mode in ["dot_only", "dot_and_label"]
            if show_dot:
                ET.SubElement(v_g, "circle", {
                    "cx": str(cx), "cy": str(cy),
                    "r": str(style.vertex_radius),
                    "fill": style.vertex_fill_color,
                    "stroke": "none"  # No border - continuous with ligature
                })

            # Label - shown in all modes except dot_only.  Placement is owned by
            # presentation_ops.vertex_label_box: adjacent to the dot in the *freest*
            # angular gap between incident lines of identity (so a label never sits
            # on a ligature it is incident to — e.g. a labeled vertex on a horizontal
            # tension thread), defaulting to the right of the dot.  The text is drawn
            # centred in that box, so the drawn extent and the §3.3 occlusion test
            # read from one source of truth (`docs/EXACT_CORRESPONDENCE.md` Phase 3b).
            if label and style.vertex_rendering_mode != "dot_only":
                _vbox = _label_boxes.get(v_id)
                if _vbox is None:      # no egi (or unlabelled in the map) — fall back
                    _vbox = vertex_label_box(label, pos, style, dto.ligature_paths,
                                             v_id, egi=egi, cut_bounds=dto.cut_bounds)
                v_attrs = {
                    "x": str((_vbox.min_x + _vbox.max_x) / 2 + offset_x),
                    "y": str((_vbox.min_y + _vbox.max_y) / 2 + offset_y),
                    "text-anchor": "middle",
                    "dominant-baseline": "central",
                    "font-size": str(style.font_size),
                    "font-family": style.font_family,
                    "fill": vertex_label_color,
                    "font-weight": style.font_weight,
                }
                if font_style != "normal":
                    v_attrs["font-style"] = font_style
                ET.SubElement(v_g, "text", v_attrs).text = label

            # The quotation glyph — Peirce's dotted oval around the quoting
            # name, plus a "⌜+N⌝" horizon badge (the reference glyph's idiom,
            # one order up).  Pure decoration; drawn strokes only, no change to
            # any position §3.3 reads (the DTO was attested before rendering).
            if quotation is not None:
                q_min_x, q_max_x = cx - style.vertex_radius, cx + style.vertex_radius
                q_min_y, q_max_y = cy - style.vertex_radius, cy + style.vertex_radius
                if label and style.vertex_rendering_mode != "dot_only":
                    _qbox = _label_boxes.get(v_id)
                    if _qbox is None:
                        _qbox = vertex_label_box(label, pos, style, dto.ligature_paths,
                                                 v_id, egi=egi, cut_bounds=dto.cut_bounds)
                    q_min_x = min(q_min_x, _qbox.min_x + offset_x)
                    q_max_x = max(q_max_x, _qbox.max_x + offset_x)
                    q_min_y = min(q_min_y, _qbox.min_y + offset_y)
                    q_max_y = max(q_max_y, _qbox.max_y + offset_y)
                q_cx, q_cy = (q_min_x + q_max_x) / 2, (q_min_y + q_max_y) / 2
                q_rx = (q_max_x - q_min_x) / 2 + 6
                q_ry = (q_max_y - q_min_y) / 2 + 5
                ET.SubElement(v_g, "ellipse", {
                    "class": "quotation-oval",
                    "cx": str(q_cx), "cy": str(q_cy),
                    "rx": str(q_rx), "ry": str(q_ry),
                    "fill": "none",
                    "stroke": quotation_accent,
                    "stroke-width": "1",
                    "stroke-dasharray": "1,3",
                    "stroke-linecap": "round",
                })
                badge = ET.SubElement(v_g, "text", {
                    "class": "quotation-horizon",
                    "x": str(q_cx + q_rx + 2),
                    "y": str(q_cy - q_ry + 2),
                    "text-anchor": "start",
                    "font-size": str(max(8.0, float(style.font_size) * 0.7)),
                    "font-family": style.font_family,
                    "fill": quotation_accent,
                    "font-weight": "bold",
                })
                badge.text = f"⌜+{quotation.get('horizon', 0)}⌝"

        # ====================================================================
        # Render Predicates (Edge Labels)
        # ====================================================================
        
        for p_id, pos in dto.predicate_positions.items():
            x = pos.x + offset_x
            y = pos.y + offset_y

            # Get relation name from EGI
            label = "?"
            if egi:
                label = egi.get_relation_name(p_id)

            # The drawn label box is the single source of truth for the predicate's
            # extent — the same box §3.3 reads for containment (presentation_ops.
            # predicate_label_box). Draw from it so picture and test never diverge.
            _box = predicate_label_box(label, pos, style)
            text_width = _box.max_x - _box.min_x
            text_height = _box.max_y - _box.min_y

            # Is this predicate spot a reference / transclusion node? (overlay,
            # not the EGI — chrome only.)
            is_reference = p_id in reference_marks

            # Wrap in a named group so the frontend can detect clicks by element ID
            p_attrs_g = {
                "id": p_id,
                "data-element-id": p_id,
                "data-element-type": "predicate",
                "cursor": "pointer",
            }
            if is_reference:
                p_attrs_g["class"] = "reference-spot"
                p_attrs_g["data-reference"] = "true"
                p_attrs_g["data-reference-horizon"] = str(reference_marks[p_id])
            p_g = ET.SubElement(element_group, "g", p_attrs_g)

            # Background rectangle — always present as a clickable hit area.
            # Use the style colour if specified, otherwise transparent.  A
            # reference spot gets a dashed accent border so it reads as a pointer,
            # not a primitive relation (no extent change — same box §3.3 reads).
            bg_color = style.raw_style_data.get('predicate', {}).get('label_box_background', 'transparent')
            rect_attrs = {
                "x": str(x - text_width / 2), "y": str(y - text_height / 2),
                "width": str(text_width), "height": str(text_height),
                "rx": "2", "ry": "2",
                "fill": bg_color,
                "stroke": "none",
            }
            if is_reference:
                rect_attrs["stroke"] = reference_accent
                rect_attrs["stroke-width"] = "1"
                rect_attrs["stroke-dasharray"] = "3,2"
            ET.SubElement(p_g, "rect", rect_attrs)

            # Label text
            p_attrs = {
                "x": str(x), "y": str(y + 5),
                "text-anchor": "middle",
                "font-size": str(style.font_size),
                "font-family": style.font_family,
                "fill": predicate_label_color,
                "font-weight": style.font_weight,
            }
            if font_style != "normal":
                p_attrs["font-style"] = font_style
            ET.SubElement(p_g, "text", p_attrs).text = label

            # The "+N beyond view" horizon badge — top-right of the label box,
            # small accent text.  Pure decoration; sits outside the attested
            # predicate extent (the badge is not part of dto.predicate_positions).
            if is_reference:
                horizon = reference_marks[p_id]
                badge = ET.SubElement(p_g, "text", {
                    "class": "reference-horizon",
                    "x": str(x + text_width / 2 + 3),
                    "y": str(y - text_height / 2 + 2),
                    "text-anchor": "start",
                    "font-size": str(max(8.0, float(style.font_size) * 0.7)),
                    "font-family": style.font_family,
                    "fill": reference_accent,
                    "font-weight": "bold",
                })
                badge.text = f"+{horizon}"

        # EGIF at bottom
        if egif:
            egif_lines = egif.split('\n')[:3]  # First 3 lines
            egif_y = svg_height - 20
            for i, line in enumerate(egif_lines):
                ET.SubElement(svg, "text", {
                    "x": "10", "y": str(egif_y + i * 15),
                    "font-size": "10", "fill": "#7f8c8d",
                    "font-family": "monospace"
                }).text = line[:80]  # Truncate long lines
        
        # Convert to string
        return ET.tostring(svg, encoding='unicode')
    
    @staticmethod
    def _smooth_path(points, offset_x: float, offset_y: float) -> str:
        """A smooth SVG path (Catmull-Rom → cubic Bézier) through the layout
        points — Peirce's flowing line of identity.  Delegates the control
        points to ``render_geometry.catmull_rom_segments`` (the shared "hand"
        the TikZ renderer uses too); falls back to a straight segment for < 3
        points."""
        pts = [(p.x + offset_x, p.y + offset_y) for p in points]
        if len(pts) < 3:
            d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
            for x, y in pts[1:]:
                d += f" L {x:.2f} {y:.2f}"
            return d
        d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
        for c1, c2, p2 in rg.catmull_rom_segments(pts):
            d += f" C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
        return d

    @staticmethod
    def _jitter(seed: str, i: int) -> float:
        """Deterministic pseudo-random value in [-1, 1] — see
        ``render_geometry.jitter`` (the shared hash-seeded "hand")."""
        return rg.jitter(seed, i)

    @classmethod
    def _hand_drawn_points(cls, points, amplitude: float, seed: str):
        """Nudge each interior point perpendicular to the local direction by a
        deterministic amount ≤ ``amplitude`` — see
        ``render_geometry.hand_drawn_points`` (shared with the TikZ renderer)."""
        return rg.hand_drawn_points(points, amplitude, seed)

    @classmethod
    def _wobbled_oval_path(
        cls, cx: float, cy: float, rx: float, ry: float,
        amplitude: float, seed: str, n: int = 60,
    ) -> str:
        """A closed, smoothly-curved loop approximating the ellipse, with the
        radius perturbed by a *low-frequency* deterministic deviation —
        Peirce's hand-drawn cut (a few gentle bulges, not high-frequency
        noise).  Amplitude is also capped to a small fraction of the smaller
        radius so tight cuts stay legible.  Coordinates are already offset."""
        amp = min(amplitude, 0.08 * min(rx, ry))
        # Two integer harmonics (periodic over the loop, so it closes smoothly)
        # with hashed phases and counts — the "hand" varies per cut but is
        # stable across renders.
        phi1 = cls._jitter(seed, 1) * math.pi
        phi2 = cls._jitter(seed, 2) * math.pi
        k1 = 2 + int(round(abs(cls._jitter(seed, 3)) * 1.49))  # 2..3
        k2 = 4 + int(round(abs(cls._jitter(seed, 4)) * 1.49))  # 4..5
        pts = []
        for i in range(n):
            t = 2.0 * math.pi * i / n
            dev = amp * (0.6 * math.sin(k1 * t + phi1) + 0.4 * math.sin(k2 * t + phi2))
            pts.append((cx + (rx + dev) * math.cos(t), cy + (ry + dev) * math.sin(t)))
        # Closed Catmull-Rom → cubic Bézier (cyclic neighbours).
        d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"
        for i in range(n):
            p0, p1, p2, p3 = (
                pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
            )
            c1x = p1[0] + (p2[0] - p0[0]) / 6.0
            c1y = p1[1] + (p2[1] - p0[1]) / 6.0
            c2x = p2[0] - (p3[0] - p1[0]) / 6.0
            c2y = p2[1] - (p3[1] - p1[1]) / 6.0
            d += f" C {c1x:.2f} {c1y:.2f} {c2x:.2f} {c2y:.2f} {p2[0]:.2f} {p2[1]:.2f}"
        return d + " Z"

    @staticmethod
    def _compute_cut_depths(egi: RelationalGraphWithCuts) -> dict:
        """Compute nesting depth of each cut. Sheet=0, direct children=1, etc."""
        if egi is None:
            return {}
        cut_ids = {c.id for c in egi.Cut}
        # Build parent map: child_cut_id → parent_area_id
        child_to_parent = {}
        for area_id, contents in egi.area.items():
            for elem_id in contents:
                if elem_id in cut_ids:
                    child_to_parent[elem_id] = area_id
        
        depths = {}
        for cut_id in cut_ids:
            depth = 0
            current = cut_id
            while current in child_to_parent:
                depth += 1
                current = child_to_parent[current]
            depths[cut_id] = depth
        return depths
