"""
Simple SVG Renderer for Unified D3 Layout Engine

Renders the new LayoutDTO format directly to SVG.
No adapters, no conversions - clean and simple.

Author: Refactored for architectural consistency
Date: 2025-10-12
"""

import xml.etree.ElementTree as ET
from typing import Optional

from unified_d3_engine import LayoutDTO
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
        
        # Create groups for proper layering
        cut_group = ET.SubElement(svg, "g", {"id": "cuts"})
        ligature_group = ET.SubElement(svg, "g", {"id": "ligatures"})
        element_group = ET.SubElement(svg, "g", {"id": "elements"})
        
        # ====================================================================
        # Render Cuts (sorted by depth - sheet first, then nested)
        # ====================================================================
        
        # Sort cuts by area (sheet has most elements, deepest cuts have least)
        cuts_to_render = []
        for cut_id, bounds in dto.cut_bounds.items():
            is_sheet = (cut_id == dto.sheet_id)
            num_contents = len(dto.area_hierarchy.get(cut_id, []))
            cuts_to_render.append((cut_id, bounds, is_sheet, num_contents))
        
        # Sheet first, then by number of contents (fewer = deeper)
        cuts_to_render.sort(key=lambda x: (not x[2], x[3]), reverse=True)
        
        for cut_id, bounds, is_sheet, _ in cuts_to_render:
            # SKIP the sheet - it's invisible/infinite in Dau's formalism
            if is_sheet:
                continue
            
            # Regular cut - use Dau style
            x = bounds.min_x + offset_x
            y = bounds.min_y + offset_y
            width = bounds.width
            height = bounds.height
            
            ET.SubElement(cut_group, "rect", {
                "x": str(x), "y": str(y),
                "width": str(width), "height": str(height),
                "rx": str(style.cut_corner_radius),
                "ry": str(style.cut_corner_radius),
                "fill": "none",
                "stroke": "#2c3e50",
                "stroke-width": str(style.cut_line_width)
            })
        
        # ====================================================================
        # Render Ligatures (simple straight lines for now)
        # ====================================================================
        
        for lig in dto.ligature_paths:
            if len(lig.points) < 2:
                continue
            
            path_d = f"M {lig.points[0].x + offset_x} {lig.points[0].y + offset_y}"
            for point in lig.points[1:]:
                path_d += f" L {point.x + offset_x} {point.y + offset_y}"
            
            ET.SubElement(ligature_group, "path", {
                "d": path_d,
                "stroke": "#34495e",
                "stroke-width": str(style.ligature_line_width),
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
            
            # Vertex circle (use Dau style)
            ET.SubElement(element_group, "circle", {
                "cx": str(cx), "cy": str(cy),
                "r": str(style.vertex_radius),
                "fill": style.vertex_fill_color,
                "stroke": "#2980b9",
                "stroke-width": "2"
            })
            
            # Label inside circle
            if label:
                ET.SubElement(element_group, "text", {
                    "x": str(cx), "y": str(cy + 5),
                    "text-anchor": "middle",
                    "font-size": str(style.font_size),
                    "font-family": style.font_family,
                    "fill": "white",
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
            
            # Estimate text size
            text_width = max(50, len(label) * 8 + 10)
            text_height = 25
            
            # Background rectangle
            ET.SubElement(element_group, "rect", {
                "x": str(x - text_width/2), "y": str(y - text_height/2),
                "width": str(text_width), "height": str(text_height),
                "rx": "5", "ry": "5",
                "fill": "#ecf0f1",
                "stroke": "#95a5a6",
                "stroke-width": "1.5"
            })
            
            # Text
            ET.SubElement(element_group, "text", {
                "x": str(x), "y": str(y + 5),
                "text-anchor": "middle",
                "font-size": str(style.font_size),
                "font-family": style.font_family,
                "font-weight": style.font_weight,
                "fill": "#2c3e50"
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
