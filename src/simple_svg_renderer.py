"""
Simple SVG Renderer (LayoutDTO → SVG; ELK layout path)

Renders the new LayoutDTO format directly to SVG.
No adapters, no conversions - clean and simple.

Author: Refactored for architectural consistency
Date: 2025-10-12
"""

import math
import xml.etree.ElementTree as ET
from typing import Optional

import render_geometry as rg
from layout_dto import LayoutDTO
from egi_core_dau import RelationalGraphWithCuts


class SimpleSVGRenderer:
    """Renders LayoutDTO to SVG format."""
    
    def render_to_svg(
        self,
        dto: LayoutDTO,
        title: str = "",
        egif: str = "",
        egi: Optional[RelationalGraphWithCuts] = None
    ) -> str:
        """
        Convert LayoutDTO to SVG string.
        
        Args:
            dto: Layout data from unified D3 engine (includes style)
            title: Diagram title
            egif: EGIF linear form for display
            egi: EGI model for labels
        
        Returns:
            SVG string
        """
        
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
            if cut_shape in ("oval", "circle") and cut_wobble > 0:
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

        # Argument-order convention: under "numbered" (Dau §11.2) a small numeral
        # n is drawn on each line of an ≥2-ary relation, so the picture itself
        # carries ν's order (the eg_reader recovers it by reading the numeral —
        # which is LigaturePath.port_index).  Under "clockwise" (Peirce) the order
        # is read from the hooks' angular order instead; no numeral is drawn.
        order_convention = getattr(style, "argument_order_convention", "numbered")
        arity_by_pred = {}
        for _l in dto.ligature_paths:
            arity_by_pred[_l.predicate_id] = arity_by_pred.get(_l.predicate_id, 0) + 1
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

            # Numbered convention: the order numeral on this line (1-based), set
            # just off the predicate-end of the line.  Only for ≥2-ary relations.
            if order_convention == "numbered" and arity_by_pred.get(lig.predicate_id, 0) >= 2:
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
                num.text = str(lig.port_index + 1)

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
        
        for v_id, pos in dto.vertex_positions.items():
            cx = pos.x + offset_x
            cy = pos.y + offset_y

            # Get vertex label from EGI
            label = ""
            if egi:
                v = next((v for v in egi.V if v.id == v_id), None)
                if v and v.label:
                    label = v.label

            # Wrap in a named group so the frontend can detect clicks by element ID
            v_g = ET.SubElement(element_group, "g", {
                "id": v_id,
                "data-element-id": v_id,
                "data-element-type": "vertex",
                "cursor": "pointer",
            })

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

            # Label - shown in all modes except dot_only.  Default placement is
            # to the right of the dot; but if an incident line of identity leaves
            # eastward (e.g. a labeled vertex sitting on a horizontal thread —
            # tension layout), a right-placed label is overwritten by the line.
            # In that case place the label in the *freest* direction — the
            # bisector of the largest angular gap between incident ligatures.
            if label and style.vertex_rendering_mode != "dot_only":
                angs = []
                for lp in dto.ligature_paths:
                    if lp.vertex_id == v_id and len(lp.points) >= 2:
                        a, b = lp.points[-1], lp.points[-2]
                        angs.append(math.atan2(b.y - a.y, b.x - a.x))
                east_blocked = any(
                    abs(math.atan2(math.sin(a), math.cos(a))) < math.radians(50)
                    for a in angs
                )
                v_attrs = {
                    "text-anchor": "start",
                    "font-size": str(style.font_size),
                    "font-family": style.font_family,
                    "fill": vertex_label_color,
                    "font-weight": style.font_weight,
                }
                if font_style != "normal":
                    v_attrs["font-style"] = font_style
                if not east_blocked:
                    v_attrs["x"] = str(cx + style.vertex_radius + 8)
                    v_attrs["y"] = str(cy + 4)
                else:
                    angs.sort()
                    best_gap, ang = -1.0, -math.pi / 2  # default: above
                    for i in range(len(angs)):
                        a0 = angs[i]
                        a1 = angs[(i + 1) % len(angs)] + (
                            2 * math.pi if i + 1 == len(angs) else 0.0)
                        if a1 - a0 > best_gap:
                            best_gap, ang = a1 - a0, (a0 + a1) / 2
                    rr = style.vertex_radius + 8
                    v_attrs["x"] = str(cx + rr * math.cos(ang))
                    v_attrs["y"] = str(cy + rr * math.sin(ang))
                    cosv = math.cos(ang)
                    v_attrs["text-anchor"] = (
                        "start" if cosv > 0.3 else "end" if cosv < -0.3 else "middle")
                    v_attrs["dominant-baseline"] = "central"
                ET.SubElement(v_g, "text", v_attrs).text = label
        
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

            # Tight padding around text (Dau style)
            char_width = style.predicate_char_width
            padding_h = 2
            padding_v = 1
            text_width = len(label) * char_width + 2 * padding_h
            text_height = style.predicate_height + 2 * padding_v

            # Wrap in a named group so the frontend can detect clicks by element ID
            p_g = ET.SubElement(element_group, "g", {
                "id": p_id,
                "data-element-id": p_id,
                "data-element-type": "predicate",
                "cursor": "pointer",
            })

            # Background rectangle — always present as a clickable hit area.
            # Use the style colour if specified, otherwise transparent.
            bg_color = style.raw_style_data.get('predicate', {}).get('label_box_background', 'transparent')
            ET.SubElement(p_g, "rect", {
                "x": str(x - text_width / 2), "y": str(y - text_height / 2),
                "width": str(text_width), "height": str(text_height),
                "rx": "2", "ry": "2",
                "fill": bg_color,
                "stroke": "none",
            })

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
