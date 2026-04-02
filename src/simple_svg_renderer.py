"""
Simple SVG Renderer for Unified D3 Layout Engine

Renders the new LayoutDTO format directly to SVG.
No adapters, no conversions - clean and simple.

Author: Refactored for architectural consistency
Date: 2025-10-12
"""

import xml.etree.ElementTree as ET
from typing import Optional

from layout_dto import LayoutDTO
from egi_core_dau import RelationalGraphWithCuts


class SimpleSVGRenderer:
    """Renders LayoutDTO to SVG format."""
    
    def render_to_svg(
        self, 
        dto: LayoutDTO, 
        title: str, 
        egif: str, 
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
        
        # Title
        ET.SubElement(svg, "text", {
            "x": "10", "y": "25",
            "font-size": "16", "font-weight": "bold",
            "fill": "#333"
        }).text = title
        
        # Stats
        stats = f"Unified D3: {len(dto.vertex_positions)}V, {len(dto.predicate_positions)}P, {len(dto.cut_bounds)}C, {len(dto.ligature_paths)}L"
        ET.SubElement(svg, "text", {
            "x": "10", "y": "45",
            "font-size": "11", "fill": "#666"
        }).text = stats
        
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
            ET.SubElement(cut_g, "rect", {
                "x": str(x), "y": str(y),
                "width": str(width), "height": str(height),
                "rx": str(style.cut_corner_radius),
                "ry": str(style.cut_corner_radius),
                "fill": fill_color,
                "stroke": "#000000",
                "stroke-width": str(style.cut_line_width)
            })
        
        # ====================================================================
        # Render Ligatures (line of identity)
        # ====================================================================
        
        # Get cap style from style specification
        ligature_cap_style = style.raw_style_data.get('ligature', {}).get('cap_style', 'butt')
        
        for lig in dto.ligature_paths:
            if len(lig.points) < 2:
                continue
            
            # Build path
            path_d = f"M {lig.points[0].x + offset_x} {lig.points[0].y + offset_y}"
            for point in lig.points[1:]:
                path_d += f" L {point.x + offset_x} {point.y + offset_y}"
            
            # Main ligature line - no hooks, cap style from style spec
            ET.SubElement(ligature_group, "path", {
                "d": path_d,
                "stroke": "#000000",
                "stroke-width": str(style.ligature_line_width),
                "stroke-linecap": ligature_cap_style,
                "fill": "none"
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

            # Label - shown in all modes except dot_only
            if label and style.vertex_rendering_mode != "dot_only":
                label_x = cx + style.vertex_radius + 8
                label_y = cy + 4
                ET.SubElement(v_g, "text", {
                    "x": str(label_x), "y": str(label_y),
                    "text-anchor": "start",
                    "font-size": str(style.font_size),
                    "font-family": style.font_family,
                    "fill": "#000000",
                    "font-weight": style.font_weight
                }).text = label
        
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
            ET.SubElement(p_g, "text", {
                "x": str(x), "y": str(y + 5),
                "text-anchor": "middle",
                "font-size": str(style.font_size),
                "font-family": style.font_family,
                "fill": "#000000",
                "font-weight": style.font_weight
            }).text = label
        
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
