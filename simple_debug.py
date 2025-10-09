#!/usr/bin/env python3
import sys, json
sys.path.insert(0, 'src')
from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

storage = EntityStorageManager(Path('corpus/graphs'))
entity = storage.load_entity('dau_theorem_proving')
egi = entity.current_egi

engine = DefinitiveThreePassEngine()
style = StyleLoader().load_default_style()

# Monkey patch to capture payload
original_layout_cut = engine._layout_cut

def debug_layout_cut(egi, cut_id, hierarchy):
    result = original_layout_cut(egi, cut_id, hierarchy)
    print(f"\\n=== D3 PAYLOAD FOR CUT {cut_id} ===")
    print(f"Bounds: {engine.area_bounds[cut_id]}")
    print(f"Nodes: {egi.area.get(cut_id, [])}")
    print(f"Ports: {[p for p in engine.port_nodes.values() if p.cut_id == cut_id or p.cut_id in hierarchy[cut_id]['children']]}")
    return result

engine._layout_cut = debug_layout_cut

output_dir = Path('test_outputs/definitive_corpus')
dto = engine.generate_layout(egi, style, str(output_dir / 'dau_theorem_proving'))
