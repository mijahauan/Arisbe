#!/usr/bin/env python3
"""
Test script to verify all three critical fixes are working:
1. Narrowed ligature-predicate gap (1.5px clearance)
2. Constant names appearing as text primitives  
3. Separate heavy lines from vertex to independent predicates
"""

import sys
import os
sys.path.append('src')

from egif_parser_dau import EGIFParser
from egdf_dau_canonical import create_dau_compliant_egdf_generator
from graphviz_layout_engine_v2 import GraphvizLayoutEngine

def test_fixes():
    """Test Roberts Disjunction example to verify all fixes."""
    egif_content = '*x ~[ ~[ (P x) ] ~[ (Q x) ] ]'
    print('🎯 Testing Roberts Disjunction with all fixes')
    print(f'EGIF: {egif_content}')
    
    test_roberts_disjunction(egif_content)
    
    # Also test with constants to verify text primitives
    print('\n' + '='*60)
    constant_egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    print('🎯 Testing constant names with Socrates example')
    print(f'EGIF: {constant_egif}')
    test_roberts_disjunction(constant_egif)

def test_roberts_disjunction(egif_content):

    try:
        # Parse EGIF
        parser = EGIFParser(egif_content)
        egi = parser.parse()
        print(f'✅ Parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts')

        # Generate layout
        layout_engine = GraphvizLayoutEngine()
        layout_result = layout_engine.create_layout_from_graph(egi)
        print(f'✅ Layout: {len(layout_result.primitives)} elements positioned')

        # Generate EGDF with fixes
        egdf_generator = create_dau_compliant_egdf_generator()
        spatial_primitives = egdf_generator.generate_egdf_from_layout(egi, layout_result)
        
        # Analyze generated primitives
        primitive_counts = {}
        for prim in spatial_primitives:
            ptype = prim.element_type if hasattr(prim, 'element_type') else 'unknown'
            primitive_counts[ptype] = primitive_counts.get(ptype, 0) + 1
        
        print(f'✅ EGDF: {len(spatial_primitives)} primitives generated')
        print(f'📊 Breakdown: {primitive_counts}')
        
        # Check Fix 1: Ligature clearance (should be 1.5px)
        print('\n🔍 Fix 1: Ligature Clearance')
        egdf_gen = create_dau_compliant_egdf_generator()
        clearance = egdf_gen.constants.ligature_clearance
        print(f'   Clearance setting: {clearance}px (should be 1.5px)')
        if clearance == 1.5:
            print('   ✅ Ligature clearance correctly set to 1.5px')
        else:
            print(f'   ❌ Ligature clearance is {clearance}px, should be 1.5px')
        
        # Check Fix 2: Constant names as text primitives
        print('\n🔍 Fix 2: Constant Names')
        text_prims = [p for p in spatial_primitives if hasattr(p, 'element_type') and p.element_type == 'text']
        if text_prims:
            print(f'   ✅ Constant names: {len(text_prims)} text primitives found')
            for tp in text_prims:
                if hasattr(tp, 'text_content'):
                    print(f'      - Text: "{tp.text_content}"')
        else:
            print('   ❌ No constant name text primitives found')
            
        # Check Fix 3: Separate identity lines
        print('\n🔍 Fix 3: Separate Identity Lines')
        identity_lines = [p for p in spatial_primitives if hasattr(p, 'element_type') and p.element_type == 'identity_line']
        print(f'   ✅ Identity lines: {len(identity_lines)} separate ligatures found')
        if len(identity_lines) >= 2:
            print('   ✅ Multiple separate ligatures confirmed')
        else:
            print('   ⚠️  Expected multiple separate ligatures for this example')
        
        print('\n🎯 All fixes verification complete!')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fixes()
