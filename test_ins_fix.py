#!/usr/bin/env python3
"""
Test the INS rule fix directly
"""

from src.egif_transformation_interface import EGIFTransformationInterface, TransformationRequest

# Create the interface
interface = EGIFTransformationInterface()

# Test the problematic transformation
request = TransformationRequest(
    source_egif="*x ~[ (P x) ] ~[ (Q x) ]",
    rule_name="INS",
    target_area_description="c_05706858",  # Use a cut area ID
    operation_details={"insert_content": "~[ (R x)]"},
    description="Test INS with variable reference"
)

print("Testing INS transformation with variable reference...")
try:
    response = interface.apply_transformation(request)
    if response.success:
        print("✓ Transformation succeeded!")
        print(f"Result: {response.result_egif}")
    else:
        print(f"✗ Transformation failed: {response.error_message}")
except Exception as e:
    print(f"✗ Exception: {e}")
