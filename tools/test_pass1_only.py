#!/usr/bin/env python3
"""
Test Pass 1 only: Visualize what dot produces
Shows ONLY the structural layout without ligature routing
"""

import sys
from pathlib import Path
sys.path.insert(0, 'src')

from entity_storage import EntityStorageManager
from definitive_egi_layout_engine import (
    DefinitiveEGILayoutEngine, LayoutDTO, RenderableArea, 
    RenderableVertex, RenderableEdgeLabel, Rect
)
from style_loader import StyleLoader
from graphviz_svg_renderer import GraphvizSVGRenderer

# Test graphs
test_graphs = ['peirce_modus_ponens', 'mixed_quantifier_complex', 'dau_2006_p112_ligature']

storage = EntityStorageManager(Path('tomos/graphs'))
layout_engine = DefinitiveEGILayoutEngine()
style = StyleLoader().load_default_style()
renderer = GraphvizSVGRenderer()

output_dir = Path('test_outputs/pass1_only')
output_dir.mkdir(parents=True, exist_ok=True)

print("Testing Pass 1 ONLY (dot structural layout)")
print("=" * 60)
print()

for graph_name in test_graphs:
    print(f"Processing: {graph_name}")
    entity = storage.load_entity(graph_name)
    egi = entity.current_egi
    
    # Build hierarchy
    hierarchy = layout_engine._build_area_hierarchy_v2(egi)
    
    print(f"  Hierarchy:")
    for area_id, info in hierarchy.items():
        area_name = 'sheet' if area_id == egi.sheet else area_id[:8]
        print(f"    {area_name}: {len(info['vertices'])} vertices, {len(info['edges'])} edges, parent={info['parent'][:8] if info['parent'] else 'None'}")
    
    # Generate DOT string to see what we're sending to Graphviz
    print(f"  Generating DOT string...")
    
    # Build complete DOT digraph with ALL elements (copied from _complete_structural_layout)
    dot_lines = ["digraph Structure {"]
    dot_lines.append("  rankdir=TB;")
    dot_lines.append("  overlap=false;")
    
    def add_cluster_with_content(area_id, indent=1):
        indent_str = "  " * indent
        
        if area_id == egi.sheet:
            # Sheet is root - add children and content at root level
            for child_id in hierarchy[area_id]['children']:
                add_cluster_with_content(child_id, indent)
            
            # Add vertices directly on sheet
            for v_id in hierarchy[area_id]['vertices']:
                dot_lines.append(f'{indent_str}"{v_id}" [shape=point, width=0.1];')
            
            # Add edge labels directly on sheet
            for e_id in hierarchy[area_id]['edges']:
                rel_name = egi.rel.get(e_id, "?")
                dot_lines.append(f'{indent_str}"{e_id}" [shape=plaintext, label="{rel_name}"];')
                
        else:
            # Regular cut - create cluster
            dot_lines.append(f'{indent_str}subgraph cluster_{area_id} {{')
            dot_lines.append(f'{indent_str}  label="";')
            dot_lines.append(f'{indent_str}  style=rounded;')
            
            # Add child cuts recursively
            for child_id in hierarchy[area_id]['children']:
                add_cluster_with_content(child_id, indent + 1)
            
            # Add vertices in this cut
            for v_id in hierarchy[area_id]['vertices']:
                dot_lines.append(f'{indent_str}  "{v_id}" [shape=point, width=0.1];')
            
            # Add edge labels in this cut
            for e_id in hierarchy[area_id]['edges']:
                rel_name = egi.rel.get(e_id, "?")
                dot_lines.append(f'{indent_str}  "{e_id}" [shape=plaintext, label="{rel_name}"];')
            
            dot_lines.append(f'{indent_str}}}')
    
    # Build complete structure
    add_cluster_with_content(egi.sheet)
    dot_lines.append("}")
    dot_string = "\n".join(dot_lines)
    
    print(f"  DOT string:")
    print("  " + "-" * 50)
    for line in dot_string.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 50)
    
    # Run ONLY Pass 1
    global_positions, area_bounds = layout_engine._complete_structural_layout(
        egi, hierarchy, style, None
    )
    
    print(f"  Pass 1 results:")
    print(f"    Vertices positioned: {len(global_positions['vertices'])}")
    print(f"    Edges positioned: {len(global_positions['edge_labels'])}")
    print(f"    Areas with bounds: {len(area_bounds)}")
    
    # Check vertex containment
    print(f"  Vertex containment check:")
    for v_id, v_data in global_positions['vertices'].items():
        area_id = v_data['parent_area_id']
        v_pos = (v_data['x'], v_data['y'])
        
        if area_id in area_bounds:
            bounds = area_bounds[area_id]
            inside = (bounds.x <= v_pos[0] <= bounds.x + bounds.width and
                     bounds.y <= v_pos[1] <= bounds.y + bounds.height)
            status = "✅" if inside else "❌"
            print(f"    {status} {v_id[:8]} in {area_id[:8]}: pos={v_pos[0]:.1f},{v_pos[1]:.1f}, bounds=[{bounds.x:.1f},{bounds.y:.1f},{bounds.width:.1f},{bounds.height:.1f}]")
        else:
            print(f"    ⚠️  {v_id[:8]} parent {area_id[:8]} has no bounds!")
    
    # Create DTO for visualization (NO ligatures)
    dto = LayoutDTO()
    
    # Add areas
    for area_id, rect in area_bounds.items():
        # Determine parent
        parent_id = None
        for aid, info in hierarchy.items():
            if area_id in info['children']:
                parent_id = aid
                break
        
        area = RenderableArea(
            id=area_id,
            parent_id=parent_id,
            rect=rect,
            is_sheet=(area_id == egi.sheet)
        )
        dto.areas.append(area)
    
    # Add vertices
    for v_id, v_data in global_positions['vertices'].items():
        vertex = RenderableVertex(
            id=v_id,
            pos=(v_data['x'], v_data['y']),
            parent_area_id=v_data['parent_area_id']
        )
        dto.vertices.append(vertex)
    
    # Add edge labels
    for e_id, e_data in global_positions['edge_labels'].items():
        # Create rect centered at position
        rect = Rect(
            e_data['x'] - e_data['width'] / 2,
            e_data['y'] - e_data['height'] / 2,
            e_data['width'],
            e_data['height']
        )
        edge_label = RenderableEdgeLabel(
            id=e_id,
            parent_area_id=e_data['parent_area_id'],
            rect=rect,
            label=e_data['label'],
            connection_ports=[]
        )
        dto.edge_labels.append(edge_label)
    
    # NO LIGATURES - just Pass 1 structure
    
    # Apply aesthetic styles
    layout_engine._apply_aesthetic_styles(dto, egi, style)
    
    # Save SVG
    svg_path = renderer.save_svg(
        dto,
        f"{graph_name} (Pass 1 Only - dot output)",
        entity.get_current_egif(),
        graph_name,
        output_dir
    )
    
    print(f"  → {svg_path.name}")
    print()

print("=" * 60)
print(f"Pass 1 visualizations saved to: {output_dir.absolute()}")
print()
print("Review these to verify:")
print("  1. Are vertices inside their correct cuts?")
print("  2. Do cuts overlap?")
print("  3. Is the hierarchy correct?")
