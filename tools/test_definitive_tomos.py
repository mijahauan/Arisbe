#!/usr/bin/env python3
"""
Test the definitive three-pass layout engine on the entire tomos.
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from entity_storage import EntityStorageManager
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader
import traceback

def main():
    """Test on entire tomos with debug output."""
    storage = EntityStorageManager(Path('tomos/graphs'))
    engine = DefinitiveThreePassEngine()
    style = StyleLoader().load_default_style()
    
    output_dir = Path('test_outputs/definitive_corpus')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all graphs (directories containing entity files)
    corpus_path = Path('tomos/graphs')
    all_graphs = sorted([p.name for p in corpus_path.iterdir() 
                        if p.is_dir() and not p.name.startswith('.')])
    
    print(f"Testing {len(all_graphs)} graphs from corpus")
    print("=" * 80)
    
    results = {
        'success': [],
        'failed': []
    }
    
    for graph_name in all_graphs:
        try:
            entity = storage.load_entity(graph_name)
            egi = entity.current_egi
            
            debug_prefix = str(output_dir / graph_name)
            dto = engine.generate_layout(egi, style, debug_prefix)
            
            results['success'].append({
                'name': graph_name,
                'vertices': len(dto.vertices),
                'edges': len(dto.edge_labels),
                'ligatures': len(dto.ligatures),
                'areas': len(dto.areas),
                'ports': len([p for p in engine.port_nodes.values()])
            })
            
            print(f"✅ {graph_name:40} {len(dto.vertices)}V {len(dto.edge_labels)}E {len(dto.ligatures)}L {len(dto.areas)}A {len(engine.port_nodes)}P")
            
        except Exception as e:
            results['failed'].append({
                'name': graph_name,
                'error': str(e)
            })
            print(f"❌ {graph_name:40} {str(e)[:40]}")
            if '--verbose' in sys.argv:
                traceback.print_exc()
    
    print()
    print("=" * 80)
    print(f"SUMMARY: {len(results['success'])} succeeded, {len(results['failed'])} failed")
    print("=" * 80)
    
    if results['failed']:
        print("\nFailed graphs:")
        for item in results['failed']:
            print(f"  ❌ {item['name']}: {item['error']}")
    
    print(f"\nDebug SVGs saved to: {output_dir}")
    print("\nSuccess rate: {:.1f}%".format(
        100 * len(results['success']) / len(all_graphs) if all_graphs else 0
    ))
    
    return len(results['failed']) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
