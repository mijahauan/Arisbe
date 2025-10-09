#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

graphs_dir = Path('corpus/graphs')
storage = EntityStorageManager(graphs_dir)
style = StyleLoader().load_default_style()

print("CHECKING ALL GRAPHS FOR OVERLAPS:")
print("=" * 60)

for graph_file in sorted(graphs_dir.glob('*.json')):
    graph_name = graph_file.stem
    entity = storage.load_entity(graph_name)
    egi = entity.current_egi
    
    engine = DefinitiveThreePassEngine()
    output_dir = Path('test_outputs/definitive_corpus')
    dto = engine.generate_layout(egi, style, str(output_dir / graph_name))
    
    overlaps_found = []
    
    for elem_id, pos in engine.element_positions.items():
        cut_id = engine.element_to_cut.get(elem_id)
        if not cut_id:
            continue
        
        cut_bounds = engine.area_bounds[cut_id]
        
        # Get element dimensions
        if elem_id.startswith('v_'):
            elem_width = elem_height = style.vertex_radius * 2
            label = "*"
        else:
            label = egi.rel.get(elem_id, '?')
            elem_width = len(label) * style.predicate_char_width + 2 * style.text_margin
            elem_height = style.predicate_height
        
        # Check bounds
        elem_left = pos[0] - elem_width / 2
        elem_right = pos[0] + elem_width / 2
        elem_top = pos[1] - elem_height / 2
        elem_bottom = pos[1] + elem_height / 2
        
        cut_left = cut_bounds.x
        cut_right = cut_bounds.x + cut_bounds.width
        cut_top = cut_bounds.y
        cut_bottom = cut_bounds.y + cut_bounds.height
        
        if (elem_left < cut_left or elem_right > cut_right or 
            elem_top < cut_top or elem_bottom > cut_bottom):
            overlaps_found.append(f"{label} in {cut_id}")
    
    if overlaps_found:
        print(f"❌ {graph_name}: {', '.join(overlaps_found)}")
    else:
        print(f"✅ {graph_name}")
