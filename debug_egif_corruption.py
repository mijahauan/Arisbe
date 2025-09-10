#!/usr/bin/env python3
"""
Debug script to identify and fix EGIF corruption issue.
The malformed output shows: ~[ *x *y *z *{ (Hates x y) (Loves z {) ]
This suggests variable name or string formatting corruption.
"""

from src.egif_parser_dau import parse_egif
from src.egif_generator_dau import EGIFGenerator
from src.egi_core_dau import Alphabet

def test_alphabet_generation():
    """Test if Alphabet class generates correct variable names."""
    print("=== Testing Alphabet Variable Generation ===")
    alphabet = Alphabet()
    
    for i in range(10):
        name = alphabet.get_fresh_name()
        print(f"Variable {i}: '{name}' (ord values: {[ord(c) for c in name]})")
        
        # Check for corruption
        if any(ord(c) < 32 or ord(c) > 126 for c in name):
            print(f"  ⚠️  CORRUPTION DETECTED in '{name}'")

def test_simple_egif_generation():
    """Test EGIF generation with a simple case."""
    print("\n=== Testing Simple EGIF Generation ===")
    
    # Parse the original EGIF
    original_egif = "~[ *x *y (Loves x y) ]"
    print(f"Original EGIF: {original_egif}")
    
    try:
        egi = parse_egif(original_egif)
        print(f"Parsed successfully: {len(egi.V)} vertices, {len(egi.E)} edges")
        
        # Generate EGIF back
        generator = EGIFGenerator(egi)
        result_egif = generator.generate()
        print(f"Generated EGIF: {result_egif}")
        
        # Check for corruption
        if '{' in result_egif or '}' in result_egif:
            print("  ⚠️  CORRUPTION DETECTED: Found unexpected braces")
            
        # Character analysis
        for i, char in enumerate(result_egif):
            if ord(char) < 32 or ord(char) > 126:
                print(f"  ⚠️  CORRUPTION at position {i}: '{char}' (ord {ord(char)})")
                
    except Exception as e:
        print(f"Error: {e}")

def test_ins_transformation_simulation():
    """Simulate the INS transformation that's causing corruption."""
    print("\n=== Testing INS Transformation Simulation ===")
    
    # Original EGIF from terminal output
    original_egif = "~[ *x *y (Loves x y) ]"
    insertion_content = "(Hates y x)"
    
    print(f"Original: {original_egif}")
    print(f"Inserting: {insertion_content}")
    
    try:
        # Parse original
        original_egi = parse_egif(original_egif)
        
        # Parse insertion content
        insertion_egi = parse_egif(insertion_content)
        
        # Manually create the expected result structure
        # This should be: ~[ *x *y (Loves x y) (Hates y x) ]
        # But we're getting: ~[ *x *y *z *{ (Hates x y) (Loves z {) ]
        
        print(f"Original vertices: {[str(v.id) for v in original_egi.V]}")
        print(f"Insertion vertices: {[str(v.id) for v in insertion_egi.V]}")
        
        # Generate EGIF for each
        gen1 = EGIFGenerator(original_egi)
        result1 = gen1.generate()
        print(f"Original regenerated: {result1}")
        
        gen2 = EGIFGenerator(insertion_egi)
        result2 = gen2.generate()
        print(f"Insertion regenerated: {result2}")
        
    except Exception as e:
        print(f"Error in simulation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_alphabet_generation()
    test_simple_egif_generation()
    test_ins_transformation_simulation()
