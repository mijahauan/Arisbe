#!/usr/bin/env python3
"""
Test script for unified D3 layout engine.

Compares single-simulation approach to broken bottom-up approach.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_d3_engine import UnifiedD3Engine
from egi_io import load_egi_json
from style_loader import StyleLoader


def test_unified_engine():
    """Test unified engine on problematic graphs."""
    
    # Test graphs with known issues
    test_graphs = [
        'corpus/graphs/dau_2006_p112_ligature/dau_2006_p112_ligature.egi.json',
        'corpus/graphs/roberts_1973_p57_disjunction/roberts_1973_p57_disjunction.egi.json',
        'corpus/graphs/roberts_domain_modeling/roberts_domain_modeling.egi.json',
        'corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json',
    ]
    
    engine = UnifiedD3Engine()
    style = StyleLoader().load_default_style()
    
    for graph_path in test_graphs:
        print(f"\n{'='*80}")
        print(f"Testing: {graph_path}")
        print('='*80)
        
        try:
            egi = load_egi_json(graph_path)
            print(f"Graph: {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C")
            
            dto = engine.generate_layout(egi, style, 'test')
            
            print(f"\n✅ Success!")
            print(f"  Vertices: {len(dto.vertex_positions)}")
            print(f"  Predicates: {len(dto.predicate_positions)}")
            print(f"  Cuts: {len(dto.cut_bounds)}")
            print(f"  Ligatures: {len(dto.ligature_paths)}")
            
            # Show area sizes
            print(f"\n  Cut sizes:")
            for cut_id, bounds in dto.cut_bounds.items():
                depth = dto.containment_depth.get(cut_id, "?")
                print(f"    {cut_id}: {bounds.width:.0f} x {bounds.height:.0f} (depth={depth})")
            
            # Show element containment
            print(f"\n  Element containment:")
            for area_id, contents in dto.area_hierarchy.items():
                print(f"    {area_id} contains: {', '.join(contents)}")
                
        except Exception as ex:
            print(f"\n❌ Failed: {ex}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    test_unified_engine()
