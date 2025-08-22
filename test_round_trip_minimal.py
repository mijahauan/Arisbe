#!/usr/bin/env python3
"""
Minimal Round-Trip Test - Direct validation without unittest framework
Tests: EGIF → EGI → EGDF → EGI → EGIF
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_round_trip():
    """Test basic round-trip functionality."""
    
    print("=== Minimal Round-Trip Test ===")
    
    try:
        # Import core components
        from egif_parser_dau import EGIFParser
        from egdf_parser import EGDFParser
        from egif_generator_dau import EGIFGenerator
        
        print("✅ Core imports successful")
        
        # Test cases
        test_cases = [
            '(Human "Socrates")',
            '*x (Human x)',
            '(Human "Socrates") (Mortal "Socrates")',
            '*x (Human x) ~[ (Mortal x) ]'
        ]
        
        egdf_parser = EGDFParser()
        
        for i, egif_text in enumerate(test_cases):
            print(f"\n--- Test Case {i+1}: {egif_text} ---")
            
            try:
                # Step 1: EGIF → EGI
                parser = EGIFParser(egif_text)
                original_egi = parser.parse()
                print(f"EGIF→EGI: {len(original_egi.V)}V {len(original_egi.E)}E {len(original_egi.Cut)}C")
                
                # Step 2: Create minimal spatial primitives
                spatial_primitives = []
                
                # Add vertices
                for j, vertex in enumerate(original_egi.V):
                    spatial_primitives.append({
                        'element_id': vertex.id,
                        'element_type': 'vertex',
                        'position': (100 + j * 50, 100),
                        'bounds': (90 + j * 50, 90, 110 + j * 50, 110)
                    })
                
                # Add predicates
                for j, edge in enumerate(original_egi.E):
                    spatial_primitives.append({
                        'element_id': edge.id,
                        'element_type': 'predicate',
                        'position': (200 + j * 50, 150),
                        'bounds': (180 + j * 50, 140, 220 + j * 50, 160)
                    })
                
                # Add cuts
                for j, cut in enumerate(original_egi.Cut):
                    spatial_primitives.append({
                        'element_id': cut.id,
                        'element_type': 'cut',
                        'position': (150 + j * 100, 200),
                        'bounds': (100 + j * 100, 150, 200 + j * 100, 250)
                    })
                
                print(f"Created {len(spatial_primitives)} spatial primitives")
                
                # Step 3: EGI → EGDF
                egdf_doc = egdf_parser.create_egdf_from_egi(original_egi, spatial_primitives)
                print("EGI→EGDF: Document created")
                
                # Step 4: EGDF → EGI
                recovered_egi = egdf_parser.extract_egi_from_egdf(egdf_doc)
                print(f"EGDF→EGI: {len(recovered_egi.V)}V {len(recovered_egi.E)}E {len(recovered_egi.Cut)}C")
                
                # Step 5: EGI → EGIF
                generator = EGIFGenerator(recovered_egi)
                recovered_egif = generator.generate()
                print(f"EGI→EGIF: '{recovered_egif}'")
                
                # Step 6: Validate structural integrity
                structure_preserved = (
                    len(original_egi.V) == len(recovered_egi.V) and
                    len(original_egi.E) == len(recovered_egi.E) and
                    len(original_egi.Cut) == len(recovered_egi.Cut)
                )
                
                if structure_preserved:
                    print("✅ ROUND-TRIP SUCCESS: Structure preserved")
                else:
                    print("❌ ROUND-TRIP FAILED: Structure mismatch")
                    print(f"   Original: {len(original_egi.V)}V {len(original_egi.E)}E {len(original_egi.Cut)}C")
                    print(f"   Recovered: {len(recovered_egi.V)}V {len(recovered_egi.E)}E {len(recovered_egi.Cut)}C")
                
                # Step 7: Test serialization formats
                try:
                    json_output = egdf_parser.egdf_to_json(egdf_doc)
                    yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
                    print(f"Serialization: JSON({len(json_output)} chars), YAML({len(yaml_output)} chars)")
                except Exception as e:
                    print(f"⚠️  Serialization issue: {e}")
                
            except Exception as e:
                print(f"❌ Test case failed: {e}")
                import traceback
                traceback.print_exc()
                
        print("\n=== Round-Trip Test Complete ===")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_basic_round_trip()
    sys.exit(0 if success else 1)
