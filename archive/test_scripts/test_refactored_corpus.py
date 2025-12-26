#!/usr/bin/env python3
"""
Test the refactored layout engine with the full corpus.
"""
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from egi_io import load_egi_json
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

def test_corpus():
    """Test refactored engine with full corpus."""
    corpus_dir = Path('corpus/graphs')
    
    # Get all graph directories
    graph_dirs = [d for d in corpus_dir.iterdir() if d.is_dir()]
    
    print("=" * 70)
    print("TESTING REFACTORED LAYOUT ENGINE WITH CORPUS")
    print("=" * 70)
    print(f"\nFound {len(graph_dirs)} graphs in corpus")
    print()
    
    style = StyleLoader().load_default_style()
    engine = DefinitiveThreePassEngine()
    
    results = []
    
    for graph_dir in sorted(graph_dirs):
        graph_name = graph_dir.name
        egi_file = graph_dir / f"{graph_name}.egi.json"
        
        if not egi_file.exists():
            continue
        
        print(f"Testing: {graph_name}")
        print("-" * 70)
        
        try:
            # Load EGI
            egi = load_egi_json(str(egi_file))
            
            # Generate layout
            dto = engine.generate_layout(egi, style)
            
            # Validate output
            success = True
            errors = []
            
            if len(dto.vertices) != len(egi.V):
                errors.append(f"Vertex count mismatch: {len(dto.vertices)} vs {len(egi.V)}")
                success = False
            
            if len(dto.edge_labels) != len(egi.rel):
                errors.append(f"Edge count mismatch: {len(dto.edge_labels)} vs {len(egi.rel)}")
                success = False
            
            # Check for valid positions
            for v in dto.vertices:
                if v.pos[0] is None or v.pos[1] is None:
                    errors.append(f"Invalid vertex position: {v.id}")
                    success = False
                    break
            
            for e in dto.edge_labels:
                if e.rect.x is None or e.rect.y is None:
                    errors.append(f"Invalid edge position: {e.id}")
                    success = False
                    break
            
            if success:
                print(f"  ✅ SUCCESS - V:{len(dto.vertices)} E:{len(dto.edge_labels)} L:{len(dto.ligatures)} A:{len(dto.areas)}")
                results.append({'name': graph_name, 'status': 'PASS', 'dto': dto})
            else:
                print(f"  ❌ FAILED - {', '.join(errors)}")
                results.append({'name': graph_name, 'status': 'FAIL', 'errors': errors})
        
        except Exception as e:
            print(f"  ❌ ERROR - {str(e)}")
            results.append({'name': graph_name, 'status': 'ERROR', 'error': str(e)})
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errored = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"\nTotal Graphs: {len(results)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  Errors: {errored}")
    print(f"\nSuccess Rate: {passed}/{len(results)} ({100*passed//len(results) if results else 0}%)")
    
    if failed > 0 or errored > 0:
        print("\nFailed/Errored Graphs:")
        for r in results:
            if r['status'] in ['FAIL', 'ERROR']:
                print(f"  - {r['name']}: {r['status']}")
    
    return results

if __name__ == '__main__':
    results = test_corpus()
    
    # Exit code based on results
    if all(r['status'] == 'PASS' for r in results):
        sys.exit(0)
    else:
        sys.exit(1)
