#!/usr/bin/env python3
"""
Focused Transformation Validation Test

Tests individual transformation rules with simple, well-formed EGIs
to validate the transformation logic is working correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_simple_erasure():
    """Test erasure with a simple, valid EGI."""
    print("🔍 Testing Simple Erasure")
    print("-" * 30)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Vertex, ElementID
    
    # Create simple EGI with one vertex on sheet (positive context)
    vertex = Vertex(ElementID("P"))
    sheet = ElementID("sheet")
    
    simple_egi = RelationalGraphWithCuts(
        V=frozenset([vertex]),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({
            sheet: frozenset([vertex.id])
        }),
        rel=frozendict()
    )
    
    print(f"  Original EGI: {len(simple_egi.V)} vertices, {len(simple_egi.Cut)} cuts")
    
    engine = TransformationSequenceEngine()
    seq_id = "simple_erasure_test"
    sequence = engine.create_sequence(simple_egi, seq_id)
    
    # Apply erasure to the vertex
    step = engine.add_transformation_step(
        seq_id,
        TransformationRuleType.ERASURE,
        {vertex.id}
    )
    
    print(f"  Erasure step result: {step.validation_result.value if step.validation_result else 'None'}")
    
    if step.target_egi:
        print(f"  Result EGI: {len(step.target_egi.V)} vertices, {len(step.target_egi.Cut)} cuts")
        return True
    else:
        print("  ❌ No result EGI produced")
        print(f"  Error: {step.error_message}")
        return False

def test_simple_insertion():
    """Test insertion with a simple EGI containing a cut."""
    print("\n🔍 Testing Simple Insertion")
    print("-" * 30)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Cut, ElementID
    
    # Create simple EGI with one cut (negative context for insertion)
    cut = Cut(ElementID("cut1"))
    sheet = ElementID("sheet")
    
    cut_egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset([cut]),
        area=frozendict({
            sheet: frozenset([cut.id]),
            cut.id: frozenset()
        }),
        rel=frozendict()
    )
    
    print(f"  Original EGI: {len(cut_egi.V)} vertices, {len(cut_egi.Cut)} cuts")
    
    engine = TransformationSequenceEngine()
    seq_id = "simple_insertion_test"
    sequence = engine.create_sequence(cut_egi, seq_id)
    
    # Apply insertion into the cut
    step = engine.add_transformation_step(
        seq_id,
        TransformationRuleType.INSERTION,
        set(),
        {"element_type": "vertex", "target_area": cut.id}
    )
    
    print(f"  Insertion step result: {step.validation_result.value if step.validation_result else 'None'}")
    
    if step.target_egi:
        print(f"  Result EGI: {len(step.target_egi.V)} vertices, {len(step.target_egi.Cut)} cuts")
        return True
    else:
        print("  ❌ No result EGI produced")
        print(f"  Error: {step.error_message}")
        return False

def test_simple_double_cut():
    """Test double cut elimination with nested cuts."""
    print("\n🔍 Testing Simple Double Cut")
    print("-" * 30)
    
    from chapter21_transformation_sequences import (
        TransformationSequenceEngine, TransformationRuleType
    )
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Cut, Vertex, ElementID
    
    # Create EGI with double cut pattern: sheet -> outer_cut -> inner_cut -> vertex
    vertex = Vertex(ElementID("P"))
    inner_cut = Cut(ElementID("inner"))
    outer_cut = Cut(ElementID("outer"))
    sheet = ElementID("sheet")
    
    double_cut_egi = RelationalGraphWithCuts(
        V=frozenset([vertex]),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset([inner_cut, outer_cut]),
        area=frozendict({
            sheet: frozenset([outer_cut.id]),
            outer_cut.id: frozenset([inner_cut.id]),
            inner_cut.id: frozenset([vertex.id])
        }),
        rel=frozendict()
    )
    
    print(f"  Original EGI: {len(double_cut_egi.V)} vertices, {len(double_cut_egi.Cut)} cuts")
    
    engine = TransformationSequenceEngine()
    seq_id = "simple_double_cut_test"
    sequence = engine.create_sequence(double_cut_egi, seq_id)
    
    # Apply double cut elimination
    step = engine.add_transformation_step(
        seq_id,
        TransformationRuleType.DOUBLE_CUT,
        {outer_cut.id, inner_cut.id}
    )
    
    print(f"  Double cut step result: {step.validation_result.value if step.validation_result else 'None'}")
    
    if step.target_egi:
        print(f"  Result EGI: {len(step.target_egi.V)} vertices, {len(step.target_egi.Cut)} cuts")
        print(f"  Vertex now in area: {[area for area, elements in step.target_egi.area.items() if vertex.id in elements]}")
        return True
    else:
        print("  ❌ No result EGI produced")
        return False

def test_validation_logic():
    """Test the validation logic directly."""
    print("\n🔍 Testing Validation Logic")
    print("-" * 30)
    
    from chapter21_transformation_sequences import TransformationSequenceEngine
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Cut, ElementID
    
    engine = TransformationSequenceEngine()
    
    # Test positive context detection
    vertex = Vertex(ElementID("P"))
    sheet = ElementID("sheet")
    
    sheet_egi = RelationalGraphWithCuts(
        V=frozenset([vertex]),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({
            sheet: frozenset([vertex.id])
        }),
        rel=frozendict()
    )
    
    positive_context = engine._elements_in_positive_context(sheet_egi, {vertex.id})
    print(f"  Vertex in positive context (sheet): {positive_context}")
    
    # Test negative context detection
    cut = Cut(ElementID("cut1"))
    cut_egi = RelationalGraphWithCuts(
        V=frozenset([vertex]),
        E=frozenset(),
        nu=frozendict(),
        sheet=sheet,
        Cut=frozenset([cut]),
        area=frozendict({
            sheet: frozenset([cut.id]),
            cut.id: frozenset([vertex.id])
        }),
        rel=frozendict()
    )
    
    negative_context = engine._elements_in_negative_context(cut_egi, {vertex.id})
    print(f"  Vertex in negative context (cut): {negative_context}")
    
    return positive_context and negative_context

def run_focused_validation_tests():
    """Run focused validation tests."""
    print("🧪 FOCUSED TRANSFORMATION VALIDATION TESTS")
    print("=" * 50)
    
    results = []
    
    # Test individual transformations
    try:
        results.append(("Erasure", test_simple_erasure()))
    except Exception as e:
        print(f"❌ Erasure test failed: {e}")
        results.append(("Erasure", False))
    
    try:
        results.append(("Insertion", test_simple_insertion()))
    except Exception as e:
        print(f"❌ Insertion test failed: {e}")
        results.append(("Insertion", False))
    
    try:
        results.append(("Double Cut", test_simple_double_cut()))
    except Exception as e:
        print(f"❌ Double cut test failed: {e}")
        results.append(("Double Cut", False))
    
    try:
        results.append(("Validation Logic", test_validation_logic()))
    except Exception as e:
        print(f"❌ Validation logic test failed: {e}")
        results.append(("Validation Logic", False))
    
    # Summary
    print(f"\n🎯 FOCUSED VALIDATION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 All focused validation tests PASSED!")
        print("✅ Transformation logic is working correctly")
    else:
        print("⚠️  Some validation tests failed")
        print("🔧 Transformation logic needs refinement")
    
    return results

if __name__ == "__main__":
    run_focused_validation_tests()
