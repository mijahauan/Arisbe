"""
Layout DTO Adapter - Bridges new and old LayoutDTO formats

Converts from new layout_engine.LayoutDTO format to old definitive_three_pass_engine format
that GraphvizSVGRenderer expects.

This is a temporary adapter until we update the renderer.
"""

from typing import Dict, Optional
from dataclasses import dataclass

from layout_engine import LayoutDTO as NewLayoutDTO, Point, BoundingBox
from definitive_three_pass_engine import (
    LayoutDTO as OldLayoutDTO,
    RenderableVertex,
    RenderableEdgeLabel,
    RenderableArea,
    RenderableLigature,
    Rect
)
from egi_core_dau import RelationalGraphWithCuts


def adapt_layout_dto(new_dto: NewLayoutDTO, egi: RelationalGraphWithCuts) -> OldLayoutDTO:
    """
    Convert new LayoutDTO format to old format for rendering.
    
    Args:
        new_dto: LayoutDTO from unified_d3_engine (layout_engine.py format)
        egi: The EGI model (needed for labels)
    
    Returns:
        OldLayoutDTO that GraphvizSVGRenderer can render
    """
    
    if new_dto is None:
        print("ERROR: adapt_layout_dto received None for new_dto")
        raise ValueError("new_dto cannot be None")
    
    if egi is None:
        print("ERROR: adapt_layout_dto received None for egi")
        raise ValueError("egi cannot be None")
    
    print(f"Adapting DTO: {len(new_dto.vertex_positions)}V, {len(new_dto.predicate_positions)}P, {len(new_dto.cut_bounds)}C")
    
    vertices = []
    edge_labels = []
    areas = []
    ligatures = []
    
    # Convert vertices
    for v_id, point in new_dto.vertex_positions.items():
        # Find vertex in EGI to get label
        v = next((v for v in egi.V if v.id == v_id), None)
        label = v.label if v and v.label else ""
        
        # Find parent area
        parent_id = None
        for area_id, contents in new_dto.area_hierarchy.items():
            if v_id in contents:
                parent_id = area_id
                break
        
        vertices.append(RenderableVertex(
            id=v_id,
            parent_area_id=parent_id,
            pos=(point.x, point.y),
            label=label
        ))
    
    # Convert edge labels (predicates)
    for e_id, point in new_dto.predicate_positions.items():
        # Find edge in EGI to get relation name
        relation_name = egi.get_relation_name(e_id)
        
        # Estimate size (use simple defaults for now)
        width = max(40, len(relation_name) * 8 + 20)
        height = 25
        
        # Find parent area
        parent_id = None
        for area_id, contents in new_dto.area_hierarchy.items():
            if e_id in contents:
                parent_id = area_id
                break
        
        edge_labels.append(RenderableEdgeLabel(
            id=e_id,
            parent_area_id=parent_id,
            rect=Rect(point.x - width/2, point.y - height/2, width, height),
            label=relation_name,
            connection_ports=[]
        ))
    
    # Convert areas (cuts)
    for cut_id, bounds in new_dto.cut_bounds.items():
        is_sheet = cut_id == new_dto.area_hierarchy.get(cut_id, None)  # Simplified check
        
        # Find parent
        parent_id = None
        for area_id, contents in new_dto.area_hierarchy.items():
            if cut_id in contents and cut_id != area_id:
                parent_id = area_id
                break
        
        # Check if this is the sheet
        is_sheet = (cut_id in new_dto.area_hierarchy and 
                   cut_id not in [c for contents in new_dto.area_hierarchy.values() for c in contents])
        
        areas.append(RenderableArea(
            id=cut_id,
            parent_id=parent_id,
            rect=Rect(bounds.min_x, bounds.min_y, bounds.width, bounds.height),
            is_sheet=is_sheet
        ))
    
    # Convert ligatures
    for lig in new_dto.ligature_paths:
        path_points = [(p.x, p.y) for p in lig.points]
        
        ligatures.append(RenderableLigature(
            start_vertex_id=lig.vertex_id,
            end_edge_id=lig.predicate_id,
            end_hook_index=0,  # Default hook index
            path_points=path_points,
            style={}
        ))
    
    old_dto = OldLayoutDTO(
        vertices=vertices,
        edge_labels=edge_labels,
        areas=areas,
        ligatures=ligatures
    )
    
    print(f"Adapted DTO created: {len(old_dto.vertices)}V, {len(old_dto.edge_labels)}E, {len(old_dto.areas)}A, {len(old_dto.ligatures)}L")
    
    return old_dto
