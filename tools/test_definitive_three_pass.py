#!/usr/bin/env python3
"""
Test the definitive three-pass layout engine.
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_three_pass_engine import DefinitiveThreePassEngine

def main():
    """Test on a few graphs with debug output."""
    storage = EntityStorageManager(Path('tomos/graphs'))
    engine = DefinitiveThreePassEngine()
    
    output_dir = Path('test_outputs/definitive_three_pass')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_graphs = [
        'peirce_modus_ponens',
        'peirce_cp_4_394_man_mortal',
        'roberts_1973_p57_disjunction',
        'roberts_domain_modeling'
    ]
    
    for graph_name in test_graphs:
        print(f"\n{'='*70}")
        print(f"Testing: {graph_name}")
        print('='*70)
        
        try:
            entity = storage.load_entity(graph_name)
            egi = entity.current_egi
            
            debug_prefix = str(output_dir / graph_name)
            dto = engine.generate_layout(egi, None, debug_prefix)
            
            print(f"\n✅ {graph_name}: {len(dto.vertices)}V, {len(dto.edge_labels)}E, {len(dto.ligatures)}L")
            print(f"   Debug SVGs: {debug_prefix}_pass*.svg")
            
        except Exception as e:
            print(f"\n❌ {graph_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("Test complete. Check debug SVGs in:")
    print(f"  {output_dir}")
    print('='*70)

if __name__ == '__main__':
    main()
