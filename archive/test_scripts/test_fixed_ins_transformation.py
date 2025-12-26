#!/usr/bin/env python3
"""
Test the fixed INS transformation that was producing corrupted EGIF output.
"""

from src.egif_transformation_interface import EGIFTransformationInterface, TransformationRequest

def test_fixed_ins_transformation():
    """Test the INS transformation with the fixed Alphabet class."""
    print("=== Testing Fixed INS Transformation ===")
    
    interface = EGIFTransformationInterface()
    
    # Test the exact case that was failing
    original_egif = "~[ *x *y (Loves x y) ]"
    print(f"Original EGIF: {original_egif}")
    
    # Create transformation request
    request = TransformationRequest(
        source_egif=original_egif,
        rule_name="INS",
        target_area_description="first_cut",  # The cut area
        operation_details={
            "insert_content": "(Hates y x)"
        },
        description="Insert (Hates y x) into the negative area"
    )
    
    # Apply transformation
    response = interface.apply_transformation(request)
    
    if response.success:
        print(f"✅ Transformation successful!")
        print(f"Result EGIF: {response.result_egif}")
        
        # Verify no corruption
        if '{' in response.result_egif or '}' in response.result_egif:
            print("❌ CORRUPTION STILL PRESENT: Found braces in output")
        else:
            print("✅ No corruption detected - output looks clean")
            
        # Check for proper variable names
        import re
        variables = re.findall(r'\*([a-zA-Z][a-zA-Z0-9]*)', response.result_egif)
        print(f"Variables found: {variables}")
        
        # Expected result should be something like: ~[ *x *y (Loves x y) (Hates y x) ]
        # or with proper variable scoping
        
    else:
        print(f"❌ Transformation failed: {response.error_message}")

if __name__ == "__main__":
    test_fixed_ins_transformation()
