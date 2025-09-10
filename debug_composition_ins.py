#!/usr/bin/env python3
"""
Debug script to test INS transformation in composition context.
"""

from src.egif_transformation_interface import EGIFTransformationInterface, TransformationRequest
from src.egif_parser_dau import parse_egif
from src.egif_generator_dau import generate_egif

def test_basic_ins():
    """Test basic INS transformation."""
    print("=== Testing Basic INS Transformation ===")
    
    interface = EGIFTransformationInterface()
    
    # Start with double cut context
    source_egif = "~[ ~[ ] ]"
    print(f"Source EGIF: {source_egif}")
    
    # Parse to get EGI and find composition area
    egi = parse_egif(source_egif)
    print(f"Parsed EGI - Cuts: {len(egi.Cut)}, Areas: {len(egi.area)}")
    
    # Find the innermost area (composition area)
    composition_area = None
    for cut in egi.Cut:
        cut_contents = egi.area.get(cut.id, frozenset())
        has_nested_cuts = any(other_cut.id in cut_contents for other_cut in egi.Cut if other_cut.id != cut.id)
        if not has_nested_cuts:
            composition_area = cut.id
            break
    
    print(f"Composition area: {composition_area}")
    
    # Test INS transformation
    request = TransformationRequest(
        source_egif=source_egif,
        rule_name="INS",
        target_area_description=str(composition_area),
        operation_details={"insert_content": '(Human "Socrates")'},
        description="Test insertion"
    )
    
    try:
        response = interface.apply_transformation(request)
        if response.success:
            print(f"✅ Success! Result: {response.result_egif}")
        else:
            print(f"❌ Failed: {response.error_message}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")
        import traceback
        traceback.print_exc()

def test_with_existing_egi():
    """Test INS with existing EGI parameter."""
    print("\n=== Testing INS with Existing EGI ===")
    
    interface = EGIFTransformationInterface()
    
    # Start with double cut context
    source_egif = "~[ ~[ ] ]"
    existing_egi = parse_egif(source_egif)
    
    # Find composition area
    composition_area = None
    for cut in existing_egi.Cut:
        cut_contents = existing_egi.area.get(cut.id, frozenset())
        has_nested_cuts = any(other_cut.id in cut_contents for other_cut in existing_egi.Cut if other_cut.id != cut.id)
        if not has_nested_cuts:
            composition_area = cut.id
            break
    
    print(f"Using existing EGI with composition area: {composition_area}")
    
    # Test INS transformation with existing EGI
    request = TransformationRequest(
        source_egif=source_egif,
        rule_name="INS",
        target_area_description=str(composition_area),
        operation_details={"insert_content": '(Human "Socrates")'},
        description="Test insertion with existing EGI"
    )
    
    try:
        response = interface.apply_transformation(request, existing_egi=existing_egi)
        if response.success:
            print(f"✅ Success! Result: {response.result_egif}")
        else:
            print(f"❌ Failed: {response.error_message}")
    except Exception as e:
        print(f"⚠️ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_ins()
    test_with_existing_egi()
