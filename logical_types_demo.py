#!/usr/bin/env python3
"""
EGRF v3.0 Logical Types Demonstration

Shows the new logical containment architecture in action.
"""

import json
from src.egrf.v3 import (
    create_logical_predicate, create_logical_context, create_logical_entity,
    LogicalLigature, ContainmentRelationship
)

def main():
    print("🎯 EGRF v3.0 Logical Types Demonstration")
    print("=" * 60)
    
    # Create a sheet of assertion (root context)
    sheet = create_logical_context(
        id="sheet_of_assertion",
        name="Sheet of Assertion",
        container="viewport",
        context_type="sheet_of_assertion",
        is_root=True,
        nesting_level=0
    )
    
    # Create predicates
    person_pred = create_logical_predicate(
        id="predicate-person",
        name="Person",
        container="sheet_of_assertion",
        arity=1,
        connected_entities=["entity-socrates-1"],
        semantic_role="assertion"
    )
    
    mortal_pred = create_logical_predicate(
        id="predicate-mortal", 
        name="Mortal",
        container="cut-implication",
        arity=1,
        connected_entities=["entity-socrates-2"],
        semantic_role="assertion"
    )
    
    # Create a cut (negation context)
    cut = create_logical_context(
        id="cut-implication",
        name="Implication Cut",
        container="sheet_of_assertion",
        context_type="cut",
        is_root=False,
        nesting_level=1
    )
    
    # Create entities (lines of identity)
    socrates_1 = create_logical_entity(
        id="entity-socrates-1",
        name="Socrates-1",
        connected_predicates=["predicate-person"],
        entity_type="constant",
        ligature_group="socrates_identity"
    )
    
    socrates_2 = create_logical_entity(
        id="entity-socrates-2", 
        name="Socrates-2",
        connected_predicates=["predicate-mortal"],
        entity_type="constant",
        ligature_group="socrates_identity"
    )
    
    # Create ligature connecting entities across cut boundary
    ligature = LogicalLigature(
        id="ligature-socrates",
        connects=["entity-socrates-1", "entity-socrates-2"],
        logical_properties={"identity_assertion": True, "crosses_contexts": True}
    )
    
    # Create containment relationships
    sheet_containment = ContainmentRelationship(
        container="sheet_of_assertion",
        contained_elements=["predicate-person", "cut-implication", "entity-socrates-1"],
        constraint_type="strict_containment",
        nesting_level=0,
        semantic_role="assertion"
    )
    
    cut_containment = ContainmentRelationship(
        container="cut-implication",
        contained_elements=["predicate-mortal", "entity-socrates-2"],
        constraint_type="strict_containment", 
        nesting_level=1,
        semantic_role="negation"
    )
    
    print("📋 Created Logical Elements:")
    print(f"   • {sheet.name} (root context)")
    print(f"   • {person_pred.name} predicate (arity {person_pred.logical_properties.arity})")
    print(f"   • {cut.name} (nested context, level {cut.logical_properties.nesting_level})")
    print(f"   • {mortal_pred.name} predicate (arity {mortal_pred.logical_properties.arity})")
    print(f"   • {socrates_1.name} entity (connects to {len(socrates_1.connection_points)} predicates)")
    print(f"   • {socrates_2.name} entity (connects to {len(socrates_2.connection_points)} predicates)")
    print(f"   • Ligature connecting {len(ligature.connects)} entities")
    print()
    
    print("🏗️  Containment Hierarchy:")
    print(f"   {sheet_containment.container} contains:")
    for elem in sheet_containment.contained_elements:
        print(f"      • {elem}")
    print(f"   {cut_containment.container} contains:")
    for elem in cut_containment.contained_elements:
        print(f"      • {elem}")
    print()
    
    print("🎮 Layout Constraints Examples:")
    print(f"   • {person_pred.name} predicate:")
    print(f"     - Moveable: {person_pred.layout_constraints.movement_constraints.moveable}")
    print(f"     - Container: {person_pred.layout_constraints.container}")
    print(f"     - Preferred size: {person_pred.layout_constraints.size_constraints.preferred.width}×{person_pred.layout_constraints.size_constraints.preferred.height}")
    print(f"     - Min spacing to siblings: {person_pred.layout_constraints.spacing_constraints.to_siblings.min}px")
    print()
    
    print(f"   • {cut.name}:")
    print(f"     - Auto-size: {cut.logical_properties.auto_size}")
    print(f"     - Shape: {cut.layout_constraints.shape}")
    print(f"     - Padding: {cut.logical_properties.padding.preferred}px")
    print(f"     - Moveable: {cut.layout_constraints.movement_constraints.moveable}")
    print()
    
    print(f"   • {socrates_1.name} entity:")
    print(f"     - Positioning: {socrates_1.layout_constraints.positioning_type.value}")
    print(f"     - Path type: {socrates_1.path_constraints.path_type}")
    print(f"     - Avoid overlaps: {socrates_1.path_constraints.avoid_overlaps}")
    print(f"     - Min length: {socrates_1.path_constraints.min_length}px")
    print()
    
    print("🔗 Cross-Context Ligature:")
    print(f"   • Connects: {' ↔ '.join(ligature.connects)}")
    print(f"   • Identity assertion: {ligature.logical_properties.get('identity_assertion')}")
    print(f"   • Routing: {ligature.layout_constraints.routing_algorithm}")
    print()
    
    print("📄 JSON Serialization Example:")
    print("-" * 40)
    
    # Show JSON serialization of predicate
    predicate_json = json.dumps(person_pred.to_dict(), indent=2)
    print("Person Predicate JSON:")
    print(predicate_json[:500] + "..." if len(predicate_json) > 500 else predicate_json)
    print()
    
    print("✅ Key Benefits of Logical Types:")
    print("   • Platform independence - no absolute coordinates")
    print("   • Automatic constraint validation")
    print("   • User movement freedom within logical bounds")
    print("   • Auto-sizing from content")
    print("   • Peirce's mathematical rules enforced by design")
    print("   • Clean separation of logic from presentation")
    print()
    
    print("🚀 Ready for next phase: Containment Hierarchy implementation!")

if __name__ == "__main__":
    main()

