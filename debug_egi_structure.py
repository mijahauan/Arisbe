#!/usr/bin/env python3
"""
Debug EGI structure to understand Qt rendering issues.
"""

import sys
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from egif_parser_dau import EGIFParser
from layout_phase_implementations import ElementSizingPhase, PhaseStatus
from spatial_awareness_system import SpatialAwarenessSystem

def debug_egi_structure():
    print("=== DEBUGGING EGI STRUCTURE ===")
    
    # Test double cut example
    egif_text = '*x ~[ ~[ (P x) ] ]'
    print(f"EGIF: {egif_text}")
    
    try:
        parser = EGIFParser(egif_text)
        egi = parser.parse()
        
        print(f"\nParsed EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        print("\nVertices:")
        for v_id, vertex in egi.V.items():
            print(f"  {v_id}: {vertex}")
            print(f"    type: {type(vertex).__name__}")
            if hasattr(vertex, '__dict__'):
                for attr, value in vertex.__dict__.items():
                    print(f"    {attr}: {value}")
        
        print("\nEdges:")
        for e_id, edge in egi.E.items():
            print(f"  {e_id}: {edge}")
            print(f"    type: {type(edge).__name__}")
            if hasattr(edge, '__dict__'):
                for attr, value in edge.__dict__.items():
                    print(f"    {attr}: {value}")
        
        print("\nCuts:")
        for c_id, cut in egi.Cut.items():
            print(f"  {c_id}: {cut}")
            print(f"    type: {type(cut).__name__}")
            if hasattr(cut, '__dict__'):
                for attr, value in cut.__dict__.items():
                    print(f"    {attr}: {value}")
        
        # Test pipeline phase
        print("\n=== TESTING PIPELINE PHASE ===")
        phase = ElementSizingPhase()
        context = {}
        result = phase.execute(egi, context)
        
        print(f"Phase result: {result.status}")
        print(f"Context keys: {list(context.keys())}")
        
        if 'element_tracking' in context:
            print("\nElement tracking:")
            for container_id, elements in context['element_tracking'].items():
                print(f"  {container_id}: {elements}")
        
        if 'relative_bounds' in context:
            print("\nRelative bounds:")
            for element_id, bounds in context['relative_bounds'].items():
                print(f"  {element_id}: {bounds}")
        
        return egi, context
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    debug_egi_structure()
