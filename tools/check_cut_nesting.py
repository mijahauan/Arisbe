#!/usr/bin/env python3
"""Check for cut overlap and illegal ligature crossings"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from style_loader import StyleLoader

storage = EntityStorageManager(Path('tomos/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
style_loader = StyleLoader()
style = style_loader.load_default_style()

def check_cut_nesting(egi, dto):
    """Check if child cuts are properly nested within parents"""
    issues = []
    
    # Build parent-child relationships
    cut_parents = {}
    for area_id, elements in egi.area.items():
        for elem_id in elements:
            if any(c.id == elem_id for c in egi.Cut):
                cut_parents[elem_id] = area_id
    
    # Check each cut
    for cut in egi.Cut:
        cut_area = next((a for a in dto.areas if a.id == cut.id), None)
        if not cut_area or cut_area.is_sheet:
            continue
        
        # Get parent area
        parent_id = cut_parents.get(cut.id)
        if not parent_id:
            continue
        
        parent_area = next((a for a in dto.areas if a.id == parent_id), None)
        if not parent_area or parent_area.is_sheet:
            continue
        
        # Check if cut is fully inside parent
        cut_left = cut_area.rect.x
        cut_right = cut_area.rect.x + cut_area.rect.width
        cut_top = cut_area.rect.y
        cut_bottom = cut_area.rect.y + cut_area.rect.height
        
        parent_left = parent_area.rect.x
        parent_right = parent_area.rect.x + parent_area.rect.width
        parent_top = parent_area.rect.y
        parent_bottom = parent_area.rect.y + parent_area.rect.height
        
        if (cut_left < parent_left or cut_right > parent_right or
            cut_top < parent_top or cut_bottom > parent_bottom):
            issues.append(
                f"Cut {cut.id[:8]} NOT fully inside parent {parent_id[:8]}: "
                f"Cut=({cut_left:.1f},{cut_top:.1f},{cut_right:.1f},{cut_bottom:.1f}) "
                f"Parent=({parent_left:.1f},{parent_top:.1f},{parent_right:.1f},{parent_bottom:.1f})"
            )
        else:
            # Check clearance
            clearance = min(
                cut_left - parent_left,
                parent_right - cut_right,
                cut_top - parent_top,
                parent_bottom - cut_bottom
            )
            if clearance < 10:
                issues.append(
                    f"Cut {cut.id[:8]} too close to parent boundary: {clearance:.1f}px"
                )
    
    return issues

def calculate_legal_corridor(vertex_area, edge_area, egi):
    """Calculate legal corridor between two areas (includes all ancestors)"""
    # Build parent relationships
    parents = {}
    for area_id, elements in egi.area.items():
        for elem_id in elements:
            if any(c.id == elem_id for c in egi.Cut):
                parents[elem_id] = area_id
    
    # Get path to root for each area
    def path_to_root(area_id):
        path = []
        current = area_id
        while current:
            path.append(current)
            current = parents.get(current)
        return path
    
    if vertex_area == edge_area:
        # Same area - include all ancestors (being inside parent cuts is legal)
        return set(path_to_root(vertex_area))
    
    path_v = path_to_root(vertex_area)
    path_e = path_to_root(edge_area)
    
    # Legal corridor is the union of both paths (includes all ancestors)
    return set(path_v) | set(path_e)

def check_ligature_crossings(egi, dto):
    """Check if ligatures illegally cross cut boundaries"""
    issues = []
    
    for lig in dto.ligatures:
        if len(lig.path_points) < 2:
            continue
        
        # Get the legal corridor for this ligature
        vertex_area = next((v.parent_area_id for v in dto.vertices if v.id == lig.start_vertex_id), None)
        edge_area = next((e.parent_area_id for e in dto.edge_labels if e.id == lig.end_edge_id), None)
        
        if not vertex_area or not edge_area:
            continue
        
        legal_corridor = calculate_legal_corridor(vertex_area, edge_area, egi)
        
        # Check each segment of the path
        for i in range(len(lig.path_points) - 1):
            x1, y1 = lig.path_points[i]
            x2, y2 = lig.path_points[i + 1]
            
            # Check each cut boundary
            for area in dto.areas:
                if area.is_sheet or area.id in legal_corridor:
                    continue  # Skip cuts in legal corridor
                
                # Check if segment crosses this cut boundary
                cut_left = area.rect.x
                cut_right = area.rect.x + area.rect.width
                cut_top = area.rect.y
                cut_bottom = area.rect.y + area.rect.height
                
                # Check if segment endpoints are on opposite sides of boundary
                start_inside = (cut_left <= x1 <= cut_right and cut_top <= y1 <= cut_bottom)
                end_inside = (cut_left <= x2 <= cut_right and cut_top <= y2 <= cut_bottom)
                
                if start_inside or end_inside:
                    # Path goes through a cut NOT in the legal corridor - illegal!
                    issues.append(
                        f"Ligature {lig.start_vertex_id[:8]}→{lig.end_edge_id[:8]} "
                        f"passes through cut {area.id[:8]} (not in legal corridor {[a[:8] for a in legal_corridor]})"
                    )
                    break
    
    return issues

# Test graphs
for entity_name in ['shared_constant_disjunction', 'peirce_modus_ponens', 'roberts_domain_modeling']:
    print(f"\n{'='*60}")
    print(f"{entity_name}")
    print(f"{'='*60}")
    
    entity = storage.load_entity(entity_name)
    egi = entity.current_egi
    dto = layout_engine.generate_layout(egi, style, None)
    
    # Check cut nesting
    nesting_issues = check_cut_nesting(egi, dto)
    if nesting_issues:
        print("\n❌ CUT NESTING ISSUES:")
        for issue in nesting_issues:
            print(f"   {issue}")
    else:
        print("\n✅ All cuts properly nested")
    
    # Check ligature crossings
    crossing_issues = check_ligature_crossings(egi, dto)
    if crossing_issues:
        print("\n❌ ILLEGAL LIGATURE CROSSINGS:")
        for issue in crossing_issues:
            print(f"   {issue}")
    else:
        print("\n✅ No illegal ligature crossings")
