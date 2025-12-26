#!/usr/bin/env python3
"""
Test the force balance fix with the professor/student graph.
"""
import sys
sys.path.insert(0, 'src')

from egi_io import load_egi_json
from definitive_three_pass_engine import DefinitiveThreePassEngine
from style_loader import StyleLoader

print("Testing force balance fix with complex scope graph...")
print()

# Load a graph that shows the force balance issue
# This graph has nested cuts and spanning ligatures
graphs_to_test = [
    ('peirce_complex_scope', 'corpus/graphs/peirce_complex_scope/peirce_complex_scope.egi.json'),
    ('sowa_professor_student', 'corpus/graphs/sowa_2011_p356_quantification/sowa_2011_p356_quantification.egi.json'),
]

style = StyleLoader().load_default_style()
engine = DefinitiveThreePassEngine()

for name, path in graphs_to_test:
    try:
        print(f"\n{'='*70}")
        print(f"Testing: {name}")
        print('='*70)
        
        egi = load_egi_json(path)
        
        # Generate layout with debug output
        dto = engine.generate_layout(
            egi, 
            style, 
            debug_prefix=f'test_outputs/force_balance_{name}'
        )
        
        print(f"\n✅ Layout generated successfully!")
        print(f"   Vertices: {len(dto.vertices)}")
        print(f"   Edge Labels: {len(dto.edge_labels)}")
        print(f"   Ligatures: {len(dto.ligatures)}")
        print(f"   Areas: {len(dto.areas)}")
        print(f"\nDebug SVGs saved to:")
        print(f"   - test_outputs/force_balance_{name}_pass1_containers.svg")
        print(f"   - test_outputs/force_balance_{name}_pass2_content.svg")
        print(f"   - test_outputs/force_balance_{name}_pass3_final.svg")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("Testing complete!")
print("="*70)
print("\nOpen the SVG files to see the improved layouts.")
print("Look for:")
print("  - Connected elements (like *x and Professor) staying together")
print("  - Better spacing and organization")
print("  - Cleaner ligature routing")
