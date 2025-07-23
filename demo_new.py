#!/usr/bin/env python3
"""
EGRF v3.0 Layout Constraints Demonstration
"""

from src.egrf.v3.layout_constraints_new import (
    LayoutElement, Viewport, LayoutContext,
    SizeConstraint, PositionConstraint, SpacingConstraint, ContainmentConstraint,
    LayoutManager
)
import json


def create_demo_graph():
    """Create a demonstration graph with proper double-cut implication structure."""
    
    # Create viewport
    viewport = Viewport(id="viewport", width=800, height=600)
    
    # Create sheet of assertion
    sheet = LayoutElement(id="sheet", x=0, y=0, width=800, height=600)
    
    # Create outer cut (first cut of implication)
    outer_cut = LayoutElement(id="outer_cut", x=100, y=100, width=600, height=400)
    
    # Create Person(Socrates) predicate in outer cut
    person_predicate = LayoutElement(id="person_predicate", x=150, y=150, width=100, height=50)
    
    # Create Socrates-1 entity in outer cut
    socrates1 = LayoutElement(id="socrates1", x=200, y=220, width=10, height=10)
    
    # Create inner cut (second cut of implication)
    inner_cut = LayoutElement(id="inner_cut", x=300, y=150, width=300, height=200)
    
    # Create Mortal(Socrates) predicate in inner cut
    mortal_predicate = LayoutElement(id="mortal_predicate", x=350, y=200, width=100, height=50)
    
    # Create Socrates-2 entity in inner cut
    socrates2 = LayoutElement(id="socrates2", x=400, y=270, width=10, height=10)
    
    # Create elements dictionary
    elements = {
        "viewport": viewport,
        "sheet": sheet,
        "outer_cut": outer_cut,
        "person_predicate": person_predicate,
        "socrates1": socrates1,
        "inner_cut": inner_cut,
        "mortal_predicate": mortal_predicate,
        "socrates2": socrates2
    }
    
    # Create containment relationships
    containers = {
        "outer_cut": "sheet",
        "person_predicate": "outer_cut",
        "socrates1": "outer_cut",
        "inner_cut": "outer_cut",
        "mortal_predicate": "inner_cut",
        "socrates2": "inner_cut"
    }
    
    # Create layout context
    context = LayoutContext(
        elements=elements,
        containers=containers,
        viewport=viewport
    )
    
    # Create constraints
    constraints = []
    
    # Size constraints
    constraints.append(SizeConstraint(
        constraint_id="sheet_size",
        element_id="sheet",
        min_width=800,
        min_height=600
    ))
    
    constraints.append(SizeConstraint(
        constraint_id="outer_cut_size",
        element_id="outer_cut",
        min_width=400,
        min_height=300
    ))
    
    constraints.append(SizeConstraint(
        constraint_id="inner_cut_size",
        element_id="inner_cut",
        min_width=200,
        min_height=150
    ))
    
    constraints.append(SizeConstraint(
        constraint_id="person_predicate_size",
        element_id="person_predicate",
        preferred_width=100,
        preferred_height=50
    ))
    
    constraints.append(SizeConstraint(
        constraint_id="mortal_predicate_size",
        element_id="mortal_predicate",
        preferred_width=100,
        preferred_height=50
    ))
    
    # Containment constraints
    constraints.append(ContainmentConstraint(
        constraint_id="outer_cut_containment",
        element_id="outer_cut",
        padding=10
    ))
    
    constraints.append(ContainmentConstraint(
        constraint_id="inner_cut_containment",
        element_id="inner_cut",
        padding=10
    ))
    
    constraints.append(ContainmentConstraint(
        constraint_id="person_predicate_containment",
        element_id="person_predicate",
        padding=5
    ))
    
    constraints.append(ContainmentConstraint(
        constraint_id="mortal_predicate_containment",
        element_id="mortal_predicate",
        padding=5
    ))
    
    # Spacing constraints
    constraints.append(SpacingConstraint(
        constraint_id="person_predicate_spacing",
        element_id="person_predicate",
        reference_id="",  # Empty means container
        min_spacing=20
    ))
    
    constraints.append(SpacingConstraint(
        constraint_id="mortal_predicate_spacing",
        element_id="mortal_predicate",
        reference_id="",
        min_spacing=20
    ))
    
    # Add constraints to context
    context.constraints = constraints
    
    return context


def simulate_user_interaction(context, layout_manager):
    """Simulate user interactions with the graph."""
    print("\nSimulating user interactions...")
    
    # Try to move person_predicate outside its container (should fail)
    print("\nAttempting to move person_predicate outside outer_cut (should fail):")
    result = layout_manager.validate_user_interaction(
        context, "move", "person_predicate", new_x=-50, new_y=-50
    )
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}")
    
    # Try to move person_predicate within its container (should succeed)
    print("\nAttempting to move person_predicate within outer_cut (should succeed):")
    result = layout_manager.validate_user_interaction(
        context, "move", "person_predicate", new_x=150, new_y=200
    )
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}")
    
    # Try to resize inner_cut to be larger than outer_cut (should fail)
    print("\nAttempting to resize inner_cut larger than outer_cut (should fail):")
    result = layout_manager.validate_user_interaction(
        context, "resize", "inner_cut", new_width=700, new_height=500
    )
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}")
    
    # Try to resize inner_cut within its container (should succeed)
    print("\nAttempting to resize inner_cut within outer_cut (should succeed):")
    result = layout_manager.validate_user_interaction(
        context, "resize", "inner_cut", new_width=250, new_height=180
    )
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}")


def main():
    """Main function."""
    print("EGRF v3.0 Layout Constraints Demonstration")
    print("=========================================")
    print("\nCreating a Peirce's Existential Graph with proper double-cut implication structure:")
    print("  \"If Socrates is a person, then Socrates is mortal\"")
    print("  Logical form: ¬(Person(Socrates) ∧ ¬Mortal(Socrates))")
    
    # Create demo graph
    context = create_demo_graph()
    
    # Create layout manager
    layout_manager = LayoutManager()
    
    # Solve layout
    print("\nSolving layout constraints...")
    layout_manager.solve_layout(context)
    
    # Print element positions
    print("\nElement positions after layout:")
    for element_id, element in context.elements.items():
        if element_id != "viewport":
            print(f"  {element_id}: ({element.x}, {element.y}) {element.width}x{element.height}")
    
    # Simulate user interactions
    simulate_user_interaction(context, layout_manager)
    
    # Export to JSON
    print("\nExporting layout to JSON...")
    json_data = context.to_json()
    with open("layout_constraints_demo.json", "w") as f:
        json.dump(json_data, f, indent=2)
    print("  Saved to layout_constraints_demo.json")
    
    print("\nDemonstration complete!")
    print("\nKey features demonstrated:")
    print("  1. Platform-independent layout system")
    print("  2. Logical containment enforcement")
    print("  3. User interaction validation")
    print("  4. Constraint-based positioning")
    print("  5. Proper double-cut implication structure")


if __name__ == "__main__":
    main()

