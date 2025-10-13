#!/usr/bin/env python3
"""
Test Pass 0: Topological Analysis

Validates that the topology analyzer correctly identifies ligature structures.
"""
import sys
sys.path.insert(0, 'src')

from egi_io import load_egi_json
from ligature_topology import analyze_ligature_topology

def test_topology_analysis():
    """Test topology analysis on corpus graphs."""
    
    test_cases = [
        {
            'name': 'Simple - Man Mortal',
            'path': 'corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.egi.json',
            'expected_crossing': 0,
            'expected_branching': 0,
            'expected_simple': 2  # Man, Mortal
        },
        {
            'name': 'Nested - Shared Constant',
            'path': 'corpus/graphs/peirce_shared_constant/peirce_shared_constant.egi.json',
            'expected_crossing': 1,  # (Human "Socrates") crosses from sheet to cut
            'expected_branching': 0,
            'expected_simple': 1
        },
        {
            'name': 'Complex - P Q R',
            'path': 'corpus/graphs/peirce_three_predicates/peirce_three_predicates.egi.json',
            'expected_crossing': 2,  # Q and R cross from sheet to cut
            'expected_branching': 1,  # P connects to multiple vertices
            'expected_simple': 0
        },
    ]
    
    print("="*70)
    print("Testing Pass 0: Topological Analysis")
    print("="*70)
    print()
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"Testing: {test['name']}")
        print(f"  File: {test['path']}")
        
        try:
            # Load EGI
            egi = load_egi_json(test['path'])
            
            # Build element to cut mapping
            element_to_cut = {}
            
            # Map all vertices and edges to their areas
            def map_elements(area_id):
                for v in egi.V:
                    if v.id not in element_to_cut:
                        # Check if vertex is in this area
                        # For simplicity, assume all vertices start on sheet
                        element_to_cut[v.id] = egi.sheet
                
                for edge_id in egi.rel.keys():
                    if edge_id not in element_to_cut:
                        element_to_cut[edge_id] = egi.sheet
                
                # Recursively process child cuts
                for child_id in egi.area.get(area_id, []):
                    # Elements in child cuts
                    for v in egi.V:
                        # This is simplified - real implementation uses proper containment
                        pass
                    for edge_id in egi.rel.keys():
                        pass
                    map_elements(child_id)
            
            # Start from sheet
            map_elements(egi.sheet)
            
            # Perform topology analysis
            topology = analyze_ligature_topology(egi, element_to_cut)
            
            # Verify results
            crossing_count = len(topology.crossing_ligatures)
            branching_count = len(topology.branching_ligatures)
            simple_count = len(topology.simple_ligatures)
            
            print(f"  Results:")
            print(f"    Crossing:  {crossing_count} (expected {test.get('expected_crossing', '?')})")
            print(f"    Branching: {branching_count} (expected {test.get('expected_branching', '?')})")
            print(f"    Simple:    {simple_count} (expected {test.get('expected_simple', '?')})")
            
            # Check expectations
            success = True
            if 'expected_crossing' in test and crossing_count != test['expected_crossing']:
                print(f"    ❌ Crossing count mismatch")
                success = False
            if 'expected_branching' in test and branching_count != test['expected_branching']:
                print(f"    ❌ Branching count mismatch")
                success = False
            if 'expected_simple' in test and simple_count != test['expected_simple']:
                print(f"    ❌ Simple count mismatch")
                success = False
            
            if success:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                print(f"  ❌ FAILED")
                failed += 1
                
        except FileNotFoundError:
            print(f"  ⚠️  SKIPPED (file not found)")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        
        print()
    
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0

if __name__ == '__main__':
    success = test_topology_analysis()
    sys.exit(0 if success else 1)
