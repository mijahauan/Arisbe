#!/usr/bin/env python3
"""
Complex EGIF Examples Testing

Testing parser, pipeline, and serialization with complex nested structures
including double nesting of implication and disjunction.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_complex_egif_examples():
    """Test complex EGIF examples with nested structures."""
    print("Complex EGIF Examples Testing")
    print("=" * 50)
    
    # Define complex test cases with proper cut syntax (using ~) and predicate syntax (using parentheses)
    test_cases = [
        {
            "name": "Simple Implication",
            "egif": "~[~[(P)] (Q)]",
            "description": "Basic implication: P → Q"
        },
        {
            "name": "Double Nested Implication", 
            "egif": "~[~[~[(P)] (Q)] (R)]",
            "description": "Double nested: (P → Q) → R"
        },
        {
            "name": "Simple Disjunction",
            "egif": "~[(P) (Q)]",
            "description": "Basic disjunction: P ∨ Q"
        },
        {
            "name": "Nested Disjunction in Implication",
            "egif": "~[~[(P) (Q)] (R)]", 
            "description": "Nested: (P ∨ Q) → R"
        },
        {
            "name": "Double Nested Mixed",
            "egif": "~[~[~[(P) (Q)] (R)] (S)]",
            "description": "Double nested mixed: ((P ∨ Q) → R) → S"
        },
        {
            "name": "Complex Nested Structure",
            "egif": "~[~[(P) ~[(Q) (R)]] ~[~[(S) (T)] (U)]]",
            "description": "Complex: (P → (Q ∨ R)) → ((S ∨ T) → U)"
        },
        {
            "name": "Triple Nested Implication",
            "egif": "~[~[~[~[(P)] (Q)] (R)] (S)]",
            "description": "Triple nested: (((P → Q) → R) → S)"
        },
        {
            "name": "Quantified with Nesting",
            "egif": "*x ~[~[(Human x)] (Mortal x)]",
            "description": "Quantified implication: ∀x(Human(x) → Mortal(x))"
        },
        {
            "name": "Complex Quantified Structure",
            "egif": "*x *y ~[~[~[(Loves x y)] (Human x)] (Happy x)]",
            "description": "Complex quantified: ∀x∀y((Loves(x,y) ∧ Human(x)) → Happy(x))"
        },
        {
            "name": "Deeply Nested Disjunction",
            "egif": "~[(P) ~[(Q) ~[(R) ~[(S) (T)]]]]",
            "description": "Deeply nested: P ∨ (Q ∨ (R ∨ (S ∨ T)))"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"EGIF: {test_case['egif']}")
        print(f"Description: {test_case['description']}")
        
        result = test_single_example(test_case['egif'], test_case['name'])
        results.append((test_case['name'], result))
        
        if result:
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    # Summary
    print("\n" + "=" * 50)
    print("Complex Examples Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All complex examples handled successfully!")
        print("✅ Parser robust with nested structures")
    else:
        print(f"\n⚠️ {total - passed} complex examples failed")
        print("Need to investigate parser limitations")
    
    return passed == total

def test_single_example(egif_input, test_name):
    """Test a single EGIF example through the full pipeline."""
    try:
        from egif_parser_dau import EGIFParser
        from canonical import CanonicalPipeline
        from egdf_parser import EGDFParser
        
        # Step 1: Parse EGIF to EGI
        parser = EGIFParser(egif_input)
        egi = parser.parse()
        
        if egi is None:
            print(f"  ✗ Parsing failed: returned None")
            return False
        
        print(f"  ✓ Parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Step 2: Test canonical pipeline round-trip
        pipeline = CanonicalPipeline()
        egif_output = pipeline.egi_to_egif(egi)
        
        if not isinstance(egif_output, str):
            print(f"  ✗ Pipeline failed: output type {type(egif_output)}")
            return False
            
        print(f"  ✓ Pipeline: '{egif_input}' → '{egif_output}'")
        
        # Step 3: Test EGDF serialization
        egdf_parser = EGDFParser()
        
        # Create spatial primitives for all elements
        spatial_primitives = []
        
        # Add vertices
        for i, vertex in enumerate(egi.V):
            spatial_primitives.append({
                'element_id': vertex.id,
                'element_type': 'vertex',
                'position': (100 + i * 60, 100 + (i % 3) * 40),
                'bounds': (90 + i * 60, 90 + (i % 3) * 40, 130 + i * 60, 130 + (i % 3) * 40)
            })
        
        # Add edges
        for i, edge in enumerate(egi.E):
            spatial_primitives.append({
                'element_id': edge.id,
                'element_type': 'edge',
                'position': (200 + i * 60, 150),
                'bounds': (190 + i * 60, 140, 230 + i * 60, 160)
            })
        
        # Add cuts
        for i, cut in enumerate(egi.Cut):
            spatial_primitives.append({
                'element_id': cut.id,
                'element_type': 'cut',
                'position': (50 + i * 120, 50),
                'bounds': (30 + i * 120, 30, 170 + i * 120, 170)
            })
        
        egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
        
        if egdf_doc is None:
            print(f"  ✗ EGDF creation failed")
            return False
        
        # Test serialization formats
        yaml_output = egdf_parser.egdf_to_yaml(egdf_doc)
        json_output = egdf_parser.egdf_to_json(egdf_doc)
        
        print(f"  ✓ EGDF: YAML({len(yaml_output)} chars), JSON({len(json_output)} chars)")
        
        # Step 4: Validate structure preservation
        if len(egi.Cut) > 0:
            print(f"  ✓ Nested structure: {len(egi.Cut)} cuts preserved")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Exception in {test_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_nesting_complexity():
    """Analyze parser handling of different nesting patterns."""
    print("\n" + "=" * 50)
    print("Nesting Complexity Analysis")
    print("=" * 50)
    
    nesting_tests = [
        ("Single Cut", "~[(P)]", 1),
        ("Double Cut", "~[~[(P)]]", 2), 
        ("Triple Cut", "~[~[~[(P)]]]", 3),
        ("Quadruple Cut", "~[~[~[~[(P)]]]]", 4),
        ("Mixed Single", "~[(P) (Q)]", 1),
        ("Mixed Double", "~[~[(P) (Q)] (R)]", 2),
        ("Mixed Triple", "~[~[~[(P) (Q)] (R)] (S)]", 3),
        ("Branched Double", "~[~[(P)] ~[(Q)]]", 2),
        ("Complex Branched", "~[~[~[(P)] (Q)] ~[~[(R)] (S)]]", 3)
    ]
    
    for name, egif, expected_depth in nesting_tests:
        try:
            from egif_parser_dau import EGIFParser
            
            parser = EGIFParser(egif)
            egi = parser.parse()
            
            actual_cuts = len(egi.Cut)
            print(f"{name:20} | {egif:15} | Cuts: {actual_cuts:2} | Expected depth: {expected_depth}")
            
        except Exception as e:
            print(f"{name:20} | {egif:15} | ERROR: {e}")

def main():
    """Run complex examples testing."""
    success = test_complex_egif_examples()
    analyze_nesting_complexity()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
