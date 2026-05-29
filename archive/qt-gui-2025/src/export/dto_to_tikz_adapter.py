#!/usr/bin/env python3
"""
DTO to TikZ Adapter - Bridge between LayoutDTO and tikz_exporter

Converts the unified LayoutDTO format (from UnifiedD3Engine) into the 
render command format expected by tikz_exporter.py.

This enables LaTeX export workflow:
    LayoutDTO → render_commands → TikZ code → LaTeX document
"""
from typing import Dict, List, Any, Set
from dataclasses import dataclass


@dataclass
class Point:
    """2D point (matches unified_d3_engine)."""
    x: float
    y: float


@dataclass
class BoundingBox:
    """Bounding box (matches unified_d3_engine)."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float


@dataclass
class LigaturePath:
    """Ligature path (matches unified_d3_engine)."""
    predicate_id: str
    vertex_id: str
    points: tuple  # Tuple of Points


def convert_dto_to_render_commands(
    dto,  # LayoutDTO from unified_d3_engine
    egi   # RelationalGraphWithCuts
) -> List[Dict[str, Any]]:
    """
    Convert LayoutDTO to render command format for tikz_exporter.
    
    Args:
        dto: LayoutDTO from layout engine
        egi: The EGI model (needed for labels, element types, etc.)
    
    Returns:
        List of render command dicts compatible with tikz_exporter
    """
    commands: List[Dict[str, Any]] = []
    
    # Calculate area parities (for alternating shading)
    area_parities = _calculate_area_parities(dto, egi)
    
    # 1. Emit cuts (background layer)
    for cut_id, bbox in dto.cut_bounds.items():
        commands.append({
            "type": "cut",
            "element_id": cut_id,
            "bounds": {
                "x": bbox.min_x,
                "y": bbox.min_y,
                "width": bbox.max_x - bbox.min_x,
                "height": bbox.max_y - bbox.min_y,
            },
            "area_parity": area_parities.get(cut_id, 0),
        })
    
    # 2. Emit predicates (edges/relations)
    for pred_id, pos in dto.predicate_positions.items():
        # Get relation name from EGI
        relation_name = ""
        if pred_id in egi.E:
            edge_data = egi.E[pred_id]
            relation_name = edge_data.get('name', pred_id)
        
        # Estimate text bounds (simplified - TikZ will handle actual sizing)
        char_width = dto.style.predicate_char_width if hasattr(dto.style, 'predicate_char_width') else 6.5
        font_size = dto.style.predicate_label_font_size if hasattr(dto.style, 'predicate_label_font_size') else 11
        
        text_width = len(relation_name) * char_width
        text_height = font_size + 2
        
        # Calculate area parity for predicate background shading
        predicate_area = _find_element_area(pred_id, dto, egi)
        predicate_parity = area_parities.get(predicate_area, 0)
        
        commands.append({
            "type": "edge",
            "element_id": pred_id,
            "relation_name": relation_name,
            "bounds": {
                "x": pos.x - text_width / 2,
                "y": pos.y - text_height / 2,
                "width": text_width,
                "height": text_height,
            },
            "area_parity": predicate_parity,
        })
    
    # 3. Emit vertices
    for vertex_id, pos in dto.vertex_positions.items():
        # Get vertex name from EGI
        vertex_name = ""
        if vertex_id in egi.V:
            vertex_data = egi.V[vertex_id]
            vertex_name = vertex_data.get('name', vertex_id)
        
        # Vertex bounds (small circle + label)
        radius = dto.style.vertex_radius if hasattr(dto.style, 'vertex_radius') else 2.0
        
        # Get rendering mode from style
        rendering_mode = dto.style.vertex_rendering_mode if hasattr(dto.style, 'vertex_rendering_mode') else "dot_and_label"
        
        commands.append({
            "type": "vertex",
            "element_id": vertex_id,
            "vertex_name": vertex_name,
            "rendering_mode": rendering_mode,
            "bounds": {
                "x": pos.x - radius,
                "y": pos.y - radius,
                "width": radius * 2,
                "height": radius * 2,
            },
        })
    
    # 4. Emit ligatures (connections on top)
    for lig in dto.ligature_paths:
        # Convert Points to coordinate list
        path_coords = [(p.x, p.y) for p in lig.points]
        
        commands.append({
            "type": "ligature",
            "predicate_id": lig.predicate_id,
            "vertex_id": lig.vertex_id,
            "path": path_coords,
        })
    
    return commands


def _calculate_area_parities(dto, egi) -> Dict[str, int]:
    """
    Calculate area parity (even/odd depth) for alternating shading.
    
    Args:
        dto: LayoutDTO
        egi: EGI model
    
    Returns:
        Dict mapping area_id → parity (0=even, 1=odd)
    """
    parities = {dto.sheet_id: 0}  # Sheet starts at parity 0
    
    # Build hierarchy: child → parent mapping
    parent_map = {}
    for parent_id, children_set in dto.area_hierarchy.items():
        for child_id in children_set:
            parent_map[child_id] = parent_id
    
    # Traverse all areas and assign parities
    for area_id in dto.cut_bounds.keys():
        if area_id in parities:
            continue
        
        # Find parent chain to sheet
        chain = []
        current = area_id
        while current != dto.sheet_id and current in parent_map:
            chain.append(current)
            current = parent_map[current]
        
        # Assign parities from root down
        if current == dto.sheet_id:
            parent_parity = parities.get(current, 0)
            for depth, child in enumerate(reversed(chain)):
                parities[child] = (parent_parity + depth + 1) % 2
    
    return parities


def _find_element_area(element_id: str, dto, egi) -> str:
    """
    Find which area contains this element.
    
    Args:
        element_id: Element to search for
        dto: LayoutDTO
        egi: EGI model
    
    Returns:
        Area ID containing this element, or sheet_id if not found
    """
    # Check EGI.area function
    if hasattr(egi, 'area') and callable(egi.area):
        return egi.area(element_id)
    
    # Fallback: check area_hierarchy
    for area_id, children in dto.area_hierarchy.items():
        if element_id in children:
            return area_id
    
    return dto.sheet_id


# ============================================================================
# CONVENIENCE FUNCTION FOR DIRECT EXPORT
# ============================================================================

def export_dto_to_tikz(
    dto,
    egi,
    standalone: bool = True
) -> str:
    """
    One-step conversion: LayoutDTO → TikZ LaTeX code.
    
    Args:
        dto: LayoutDTO from layout engine
        egi: EGI model
        standalone: If True, return complete LaTeX document; 
                    if False, return only tikzpicture environment
    
    Returns:
        LaTeX/TikZ code string
    
    Example:
        >>> from unified_d3_engine import UnifiedD3Engine
        >>> from style_loader import StyleLoader
        >>> 
        >>> engine = UnifiedD3Engine()
        >>> style = StyleLoader().load_style("peirce-authentic@1.0")
        >>> dto = engine.generate_layout(egi, style)
        >>> 
        >>> latex_code = export_dto_to_tikz(dto, egi, standalone=True)
        >>> Path("diagram.tex").write_text(latex_code)
    """
    from export.tikz_exporter import generate_tikz
    
    # Convert DTO to render commands
    render_commands = convert_dto_to_render_commands(dto, egi)
    
    # Generate TikZ
    return generate_tikz(render_commands, standalone=standalone)
