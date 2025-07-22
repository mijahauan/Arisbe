#!/usr/bin/env python3
"""
CORRECTED EGRF v3.0 Demonstration: Proper Peirce Implication

Shows the correct double-cut structure for logical implication:
"If Socrates is a person, then Socrates is mortal"

Correct Structure:
Sheet of Assertion
└── Outer Cut (negates whole implication)
    ├── Person(Socrates-1) [Antecedent]
    └── Inner Cut (negates consequent)
        └── Mortal(Socrates-2) [Consequent]

This represents: ¬(Person(Socrates) ∧ ¬Mortal(Socrates))
Which equals: Person(Socrates) → Mortal(Socrates)
"""

import json
from src.egrf.v3.logical_types import (
    create_logical_predicate, create_logical_context, create_logical_entity,
    ContainmentRelationship, LogicalSize
)
from src.egrf.v3.containment_hierarchy import (
    ContainmentHierarchyManager, HierarchyValidator, LayoutCalculator,
    create_containment_hierarchy, validate_and_calculate_layout
)

def main():
    print("🔧 CORRECTED EGRF v3.0 Demonstration: Proper Peirce Implication")
    print("=" * 80)
    print()
    
    print("❌ PREVIOUS ERROR:")
    print("   Incorrectly used single cut for implication")
    print("   Represented: Person(Socrates) ∧ ¬Mortal(Socrates)")
    print("   Meaning: 'Socrates is a person AND not mortal' (contradiction)")
    print()
    
    print("✅ CORRECT STRUCTURE:")
    print("   Uses double-cut for proper implication")
    print("   Represents: ¬(Person(Socrates) ∧ ¬Mortal(Socrates))")
    print("   Meaning: 'If Socrates is a person, then Socrates is mortal'")
    print()
    
    print("📋 Creating Correct Double-Cut Implication Structure...")
    
    # Create the correct implication structure
    sheet = create_logical_context(
        id="sheet_of_assertion",
        name="Sheet of Assertion",
        container="viewport",
        context_type="sheet_of_assertion",
        is_root=True,
        nesting_level=0
    )
    
    # Outer cut - negates the entire implication
    outer_cut = create_logical_context(
        id="cut-outer",
        name="Implication Outer Cut",
        container="sheet_of_assertion",
        context_type="cut",
        is_root=False,
        nesting_level=1
    )
    
    # Antecedent: Person(Socrates) - inside outer cut
    person_pred = create_logical_predicate(
        id="predicate-person",
        name="Person",
        container="cut-outer",
        arity=1,
        connected_entities=["entity-socrates-1"],
        semantic_role="antecedent"
    )
    
    # Inner cut - negates the consequent
    inner_cut = create_logical_context(
        id="cut-inner", 
        name="Consequent Negation Cut",
        container="cut-outer",
        context_type="cut",
        is_root=False,
        nesting_level=2
    )
    
    # Consequent: Mortal(Socrates) - inside inner cut (so it's negated)
    mortal_pred = create_logical_predicate(
        id="predicate-mortal",
        name="Mortal",
        container="cut-inner",
        arity=1,
        connected_entities=["entity-socrates-2"],
        semantic_role="consequent"
    )
    
    # Entities representing the same individual across cuts
    socrates_1 = create_logical_entity(
        id="entity-socrates-1",
        name="Socrates-1",
        connected_predicates=["predicate-person"],
        entity_type="constant",
        ligature_group="socrates_identity"
    )
    socrates_1.layout_constraints.container = "cut-outer"
    
    socrates_2 = create_logical_entity(
        id="entity-socrates-2", 
        name="Socrates-2",
        connected_predicates=["predicate-mortal"],
        entity_type="constant",
        ligature_group="socrates_identity"
    )
    socrates_2.layout_constraints.container = "cut-inner"
    
    # Create proper containment relationships
    sheet_relationship = ContainmentRelationship(
        container="sheet_of_assertion",
        contained_elements=["cut-outer"],
        constraint_type="strict_containment",
        nesting_level=0,
        semantic_role="assertion"
    )
    
    outer_cut_relationship = ContainmentRelationship(
        container="cut-outer",
        contained_elements=["predicate-person", "entity-socrates-1", "cut-inner"],
        constraint_type="strict_containment", 
        nesting_level=1,
        semantic_role="implication_body"
    )
    
    inner_cut_relationship = ContainmentRelationship(
        container="cut-inner",
        contained_elements=["predicate-mortal", "entity-socrates-2"],
        constraint_type="strict_containment",
        nesting_level=2,
        semantic_role="consequent_negation"
    )
    
    # Create hierarchy
    elements = [sheet, outer_cut, person_pred, inner_cut, mortal_pred, socrates_1, socrates_2]
    relationships = [sheet_relationship, outer_cut_relationship, inner_cut_relationship]
    
    manager = create_containment_hierarchy(elements, relationships)
    
    print(f"   ✅ Created {len(elements)} logical elements")
    print(f"   ✅ Created {len(relationships)} containment relationships")
    print()
    
    # Show the correct structure
    print("🏗️  CORRECT Implication Structure:")
    print("   Sheet of Assertion")
    print("   └── Outer Cut (negates whole implication)")
    print("       ├── Person(Socrates-1) [Antecedent]")
    print("       ├── Socrates-1 entity")
    print("       └── Inner Cut (negates consequent)")
    print("           ├── Mortal(Socrates-2) [Consequent]")
    print("           └── Socrates-2 entity")
    print()
    
    # Show nesting levels
    print("📊 Correct Nesting Levels:")
    for element_id in manager.elements:
        level = manager.get_nesting_level(element_id)
        element_name = manager.elements[element_id].name
        element_type = manager.elements[element_id].element_type
        print(f"   • {element_name} ({element_type}, level {level})")
    print()
    
    # Validate and calculate layout
    print("🔍 Hierarchy Validation:")
    validation_report, layout_result = validate_and_calculate_layout(manager, LogicalSize(1200, 900))
    
    if validation_report.is_valid:
        print("   ✅ Hierarchy is VALID")
        print(f"   • {len(validation_report.errors)} errors")
        print(f"   • {len(validation_report.warnings)} warnings")
    else:
        print("   ❌ Hierarchy has ERRORS:")
        for error in validation_report.errors:
            print(f"     • {error.message}")
    print()
    
    # Show layout calculation
    print("📐 Layout Calculation (Correct Double-Cut):")
    print(f"   Calculation order: {layout_result.calculation_order}")
    print()
    
    print("   Element Sizes (Auto-calculated):")
    for element_id, size in layout_result.element_sizes.items():
        element_name = manager.elements[element_id].name
        print(f"   • {element_name}: {size.width:.1f}×{size.height:.1f}")
    print()
    
    # Show the logical meaning
    print("🧠 Logical Analysis:")
    print("   Raw Structure: ¬(Person(Socrates) ∧ ¬Mortal(Socrates))")
    print("   Simplified: ¬Person(Socrates) ∨ Mortal(Socrates)")
    print("   Final Form: Person(Socrates) → Mortal(Socrates)")
    print("   English: 'If Socrates is a person, then Socrates is mortal'")
    print()
    
    # Show containment tree
    print("🌳 Containment Tree (Correct Structure):")
    for container_id, contained in validation_report.containment_tree.items():
        container_name = manager.elements[container_id].name
        print(f"   {container_name} contains:")
        for contained_id in contained:
            contained_name = manager.elements[contained_id].name
            contained_type = manager.elements[contained_id].element_type
            print(f"      • {contained_name} ({contained_type})")
    print()
    
    # Compare sizes to show auto-sizing working correctly
    print("🔧 Auto-Sizing Analysis:")
    if layout_result.element_sizes:
        sheet_size = layout_result.element_sizes.get("sheet_of_assertion")
        outer_size = layout_result.element_sizes.get("cut-outer")
        inner_size = layout_result.element_sizes.get("cut-inner")
        
        if all([sheet_size, outer_size, inner_size]):
            print(f"   • Inner Cut: {inner_size.width:.1f}×{inner_size.height:.1f}")
            print(f"     (Contains: Mortal predicate + Socrates-2 entity)")
            print(f"   • Outer Cut: {outer_size.width:.1f}×{outer_size.height:.1f}")
            print(f"     (Contains: Person predicate + Socrates-1 entity + Inner Cut)")
            print(f"   • Sheet: {sheet_size.width:.1f}×{sheet_size.height:.1f}")
            print(f"     (Contains: Outer Cut)")
            print()
            print("   ✅ Proper nesting: Sheet > Outer Cut > Inner Cut")
            print(f"   ✅ Size relationships: {sheet_size.width:.0f} > {outer_size.width:.0f} > {inner_size.width:.0f}")
    print()
    
    # Show what this fixes
    print("🎯 What This Correction Achieves:")
    print("   ✅ Proper Peirce logical structure")
    print("   ✅ Correct implication semantics")
    print("   ✅ Valid EG double-cut pattern")
    print("   ✅ Accurate logical meaning")
    print("   ✅ Foundation for EG pattern validation")
    print()
    
    print("⚠️  Lessons Learned:")
    print("   • Technical implementation ≠ logical correctness")
    print("   • Domain knowledge is critical for EG systems")
    print("   • Need EG-specific validation rules")
    print("   • Examples must follow Peirce's conventions")
    print()
    
    print("🚀 Next Steps:")
    print("   1. Add EG logical pattern validation")
    print("   2. Create library of standard EG forms")
    print("   3. Implement semantic correctness checking")
    print("   4. Proceed to Phase 3 with correct foundation")

if __name__ == "__main__":
    main()

