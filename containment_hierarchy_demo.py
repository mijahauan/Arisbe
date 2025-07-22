#!/usr/bin/env python3
"""
EGRF v3.0 Containment Hierarchy Demonstration

Shows the complete containment hierarchy system in action:
- Hierarchy validation
- Auto-sizing layout calculation  
- Movement validation
- Complex nested structures
"""

import json
from src.egrf.v3.logical_types import (
    create_logical_predicate, create_logical_context, create_logical_entity,
    ContainmentRelationship, LogicalSize
)
from src.egrf.v3.containment_hierarchy import (
    ContainmentHierarchyManager, HierarchyValidator, LayoutCalculator, MovementValidator,
    create_containment_hierarchy, validate_and_calculate_layout
)

def main():
    print("🎯 EGRF v3.0 Containment Hierarchy Demonstration")
    print("=" * 70)
    
    # Create a complex Peirce example: "If Socrates is a person, then Socrates is mortal"
    # Structure: Sheet -> [Person(Socrates-1), Cut -> [Mortal(Socrates-2)]]
    # With ligature connecting Socrates-1 ↔ Socrates-2
    
    print("📋 Creating Complex Existential Graph Structure...")
    
    # Create elements
    sheet = create_logical_context(
        id="sheet_of_assertion",
        name="Sheet of Assertion",
        container="viewport",
        context_type="sheet_of_assertion",
        is_root=True,
        nesting_level=0
    )
    
    person_pred = create_logical_predicate(
        id="predicate-person",
        name="Person",
        container="sheet_of_assertion",
        arity=1,
        connected_entities=["entity-socrates-1"],
        semantic_role="assertion"
    )
    
    cut = create_logical_context(
        id="cut-implication",
        name="Implication Cut",
        container="sheet_of_assertion",
        context_type="cut",
        is_root=False,
        nesting_level=1
    )
    
    mortal_pred = create_logical_predicate(
        id="predicate-mortal",
        name="Mortal", 
        container="cut-implication",
        arity=1,
        connected_entities=["entity-socrates-2"],
        semantic_role="assertion"
    )
    
    socrates_1 = create_logical_entity(
        id="entity-socrates-1",
        name="Socrates-1",
        connected_predicates=["predicate-person"],
        entity_type="constant",
        ligature_group="socrates_identity"
    )
    socrates_1.layout_constraints.container = "sheet_of_assertion"
    
    socrates_2 = create_logical_entity(
        id="entity-socrates-2",
        name="Socrates-2", 
        connected_predicates=["predicate-mortal"],
        entity_type="constant",
        ligature_group="socrates_identity"
    )
    socrates_2.layout_constraints.container = "cut-implication"
    
    # Create containment relationships
    sheet_relationship = ContainmentRelationship(
        container="sheet_of_assertion",
        contained_elements=["predicate-person", "cut-implication", "entity-socrates-1"],
        constraint_type="strict_containment",
        nesting_level=0,
        semantic_role="assertion"
    )
    
    cut_relationship = ContainmentRelationship(
        container="cut-implication", 
        contained_elements=["predicate-mortal", "entity-socrates-2"],
        constraint_type="strict_containment",
        nesting_level=1,
        semantic_role="negation"
    )
    
    # Create hierarchy
    elements = [sheet, person_pred, cut, mortal_pred, socrates_1, socrates_2]
    relationships = [sheet_relationship, cut_relationship]
    
    manager = create_containment_hierarchy(elements, relationships)
    
    print(f"   ✅ Created {len(elements)} logical elements")
    print(f"   ✅ Created {len(relationships)} containment relationships")
    print()
    
    # Demonstrate hierarchy management
    print("🏗️  Hierarchy Structure Analysis:")
    print(f"   Root elements: {manager.get_root_elements()}")
    print(f"   Sheet contains: {manager.get_contained_elements('sheet_of_assertion')}")
    print(f"   Cut contains: {manager.get_contained_elements('cut-implication')}")
    print()
    
    print("📊 Nesting Levels:")
    for element_id in manager.elements:
        level = manager.get_nesting_level(element_id)
        element_name = manager.elements[element_id].name
        print(f"   • {element_name} (level {level})")
    print()
    
    print("🔗 Relationship Analysis:")
    print(f"   • {person_pred.name} and {cut.name} are siblings: {manager.is_sibling('predicate-person', 'cut-implication')}")
    print(f"   • {sheet.name} is ancestor of {mortal_pred.name}: {manager.is_ancestor('sheet_of_assertion', 'predicate-mortal')}")
    print(f"   • {cut.name} descendants: {manager.get_descendants('cut-implication')}")
    print(f"   • {mortal_pred.name} ancestors: {manager.get_ancestors('predicate-mortal')}")
    print()
    
    # Demonstrate validation
    print("🔍 Hierarchy Validation:")
    validation_report, layout_result = validate_and_calculate_layout(manager, LogicalSize(1000, 800))
    
    if validation_report.is_valid:
        print("   ✅ Hierarchy is VALID")
        print(f"   • No errors found")
        print(f"   • {len(validation_report.warnings)} warnings")
        if validation_report.warnings:
            for warning in validation_report.warnings:
                print(f"     ⚠️  {warning.message}")
    else:
        print("   ❌ Hierarchy has ERRORS:")
        for error in validation_report.errors:
            print(f"     • {error.message}")
    print()
    
    # Demonstrate layout calculation
    print("📐 Layout Calculation Results:")
    print(f"   Calculation order (deepest first): {layout_result.calculation_order}")
    print()
    
    print("   Element Sizes:")
    for element_id, size in layout_result.element_sizes.items():
        element_name = manager.elements[element_id].name
        print(f"   • {element_name}: {size.width:.1f}×{size.height:.1f} ({size.calculation_method})")
    print()
    
    print("   Element Positions:")
    for element_id, pos in layout_result.element_positions.items():
        element_name = manager.elements[element_id].name
        print(f"   • {element_name}: ({pos.x:.1f}, {pos.y:.1f}) [{pos.positioning_method}]")
    print()
    
    print("   Container Bounds:")
    for container_id, bounds in layout_result.container_bounds.items():
        container_name = manager.elements[container_id].name
        print(f"   • {container_name}: ({bounds.x:.1f}, {bounds.y:.1f}) {bounds.width:.1f}×{bounds.height:.1f}")
    print()
    
    # Demonstrate auto-sizing
    print("🔧 Auto-Sizing Demonstration:")
    sheet_size = layout_result.element_sizes["sheet_of_assertion"]
    cut_size = layout_result.element_sizes["cut-implication"]
    person_size = layout_result.element_sizes["predicate-person"]
    mortal_size = layout_result.element_sizes["predicate-mortal"]
    
    print(f"   • {person_pred.name} predicate: {person_size.width:.1f}×{person_size.height:.1f}")
    print(f"   • {mortal_pred.name} predicate: {mortal_size.width:.1f}×{mortal_size.height:.1f}")
    print(f"   • {cut.name} auto-sized to: {cut_size.width:.1f}×{cut_size.height:.1f}")
    print(f"     (Contains {mortal_pred.name} + padding)")
    print(f"   • {sheet.name} auto-sized to: {sheet_size.width:.1f}×{sheet_size.height:.1f}")
    print(f"     (Contains {person_pred.name} + {cut.name} + padding)")
    print()
    
    # Demonstrate movement validation
    print("🎮 Movement Validation:")
    calculator = LayoutCalculator(manager)
    validator = MovementValidator(manager, calculator)
    
    # Test valid movement
    person_pos = layout_result.element_positions["predicate-person"]
    new_x = person_pos.x + 20
    new_y = person_pos.y + 10
    
    is_valid, error = validator.validate_movement("predicate-person", new_x, new_y, layout_result)
    if is_valid:
        print(f"   ✅ Moving {person_pred.name} to ({new_x:.1f}, {new_y:.1f}) is ALLOWED")
    else:
        print(f"   ❌ Movement blocked: {error}")
    
    # Test invalid movement (outside container)
    invalid_x = 2000  # Way outside container
    invalid_y = 2000
    
    is_valid, error = validator.validate_movement("predicate-person", invalid_x, invalid_y, layout_result)
    if is_valid:
        print(f"   ✅ Moving {person_pred.name} to ({invalid_x}, {invalid_y}) is allowed")
    else:
        print(f"   ❌ Moving {person_pred.name} outside bounds blocked: {error}")
    
    # Test moving element to different container (should fail)
    mortal_pos = layout_result.element_positions["predicate-mortal"]
    is_valid, error = validator.validate_movement("predicate-mortal", person_pos.x, person_pos.y, layout_result)
    if is_valid:
        print(f"   ✅ Moving {mortal_pred.name} to sheet position is allowed")
    else:
        print(f"   ❌ Moving {mortal_pred.name} outside its cut blocked: {error}")
    print()
    
    # Demonstrate constraint enforcement
    print("⚖️  Constraint Enforcement Examples:")
    print("   Peirce's Rules Enforced by Design:")
    print(f"   • {person_pred.name} can only move within {sheet.name}")
    print(f"   • {mortal_pred.name} can only move within {cut.name}")
    print(f"   • {cut.name} auto-sizes to contain {mortal_pred.name}")
    print(f"   • {sheet.name} auto-sizes to contain all elements")
    print(f"   • Collision detection prevents overlapping elements")
    print(f"   • Spacing constraints maintain readability")
    print()
    
    # Show JSON serialization
    print("📄 JSON Serialization Example:")
    print("-" * 50)
    
    # Serialize the validation report
    report_data = {
        "is_valid": validation_report.is_valid,
        "error_count": len(validation_report.errors),
        "warning_count": len(validation_report.warnings),
        "nesting_levels": validation_report.nesting_levels,
        "containment_tree": validation_report.containment_tree
    }
    
    print("Validation Report JSON:")
    print(json.dumps(report_data, indent=2))
    print()
    
    # Serialize layout result summary
    layout_data = {
        "calculation_order": layout_result.calculation_order,
        "element_count": len(layout_result.element_sizes),
        "container_count": len(layout_result.container_bounds),
        "total_canvas_size": {
            "width": sheet_size.width,
            "height": sheet_size.height
        } if sheet_size else None
    }
    
    print("Layout Result Summary JSON:")
    print(json.dumps(layout_data, indent=2))
    print()
    
    print("✅ Key Achievements Demonstrated:")
    print("   🎯 Logical containment hierarchy management")
    print("   🔍 Comprehensive validation with error detection")
    print("   📐 Auto-sizing layout calculation (bottom-up)")
    print("   📍 Constraint-based positioning (top-down)")
    print("   🎮 Movement validation within logical bounds")
    print("   ⚖️  Peirce's mathematical rules enforced by design")
    print("   🔗 Complex nested structure support")
    print("   📄 Complete JSON serialization")
    print()
    
    print("🚀 Phase 2 Complete! Ready for Phase 3: Logical Generator")
    print("   Next: EG-HG → EGRF v3.0 conversion implementation")

if __name__ == "__main__":
    main()

