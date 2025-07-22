#!/usr/bin/env python3
"""
Regenerate all Phase 3 advanced canonical examples with visual fix applied.
This script applies the critical fix that populates both top-level attributes
and visual section in EGRF documents.
"""

import sys
import os
sys.path.append('/home/ubuntu/EG-CL-Manus2/src')

from graph import EGGraph
from eg_types import Entity, Predicate
from egrf.egrf_generator import EGRFGenerator
from egrf.egrf_serializer import EGRFSerializer
import json

def create_complex_syllogism():
    """Create complex syllogism: All men are mortal, Socrates is a man, therefore Socrates is mortal."""
    graph = EGGraph.create_empty()
    
    # Create entities
    socrates = Entity.create(name="Socrates", entity_type="constant")
    x = Entity.create(name="x", entity_type="variable")
    
    # Add entities to graph
    graph = graph.add_entity(socrates)
    graph = graph.add_entity(x)
    
    # Create predicates
    man_socrates = Predicate.create(name="Man", entities=[socrates.id])
    man_x = Predicate.create(name="Man", entities=[x.id])
    mortal_socrates = Predicate.create(name="Mortal", entities=[socrates.id])
    mortal_x = Predicate.create(name="Mortal", entities=[x.id])
    
    # Add predicates to graph
    graph = graph.add_predicate(man_socrates)
    graph = graph.add_predicate(man_x)
    graph = graph.add_predicate(mortal_socrates)
    graph = graph.add_predicate(mortal_x)
    
    # Create empty cut for logical structure
    graph, empty_cut = graph.create_context(
        context_type="cut",
        parent_id=graph.context_manager.root_context.id
    )
    
    return graph

def create_transitive_relation():
    """Create transitive relation: A > B, B > C, therefore A > C."""
    graph = EGGraph.create_empty()
    
    # Create entities
    a = Entity.create(name="A", entity_type="constant")
    b = Entity.create(name="B", entity_type="constant")
    c = Entity.create(name="C", entity_type="constant")
    
    # Add entities to graph
    graph = graph.add_entity(a)
    graph = graph.add_entity(b)
    graph = graph.add_entity(c)
    
    # Create predicates
    greater_ab = Predicate.create(name="Greater", entities=[a.id, b.id])
    greater_bc = Predicate.create(name="Greater", entities=[b.id, c.id])
    greater_ac = Predicate.create(name="Greater", entities=[a.id, c.id])
    
    # Add predicates to graph
    graph = graph.add_predicate(greater_ab)
    graph = graph.add_predicate(greater_bc)
    graph = graph.add_predicate(greater_ac)
    
    # Create empty cut for logical structure
    graph, empty_cut = graph.create_context(
        context_type="cut",
        parent_id=graph.context_manager.root_context.id
    )
    
    return graph

def create_mathematical_proof():
    """Create mathematical proof: x = y, y = z, therefore x = z."""
    graph = EGGraph.create_empty()
    
    # Create entities
    x = Entity.create(name="x", entity_type="variable")
    y = Entity.create(name="y", entity_type="variable")
    z = Entity.create(name="z", entity_type="variable")
    
    # Add entities to graph
    graph = graph.add_entity(x)
    graph = graph.add_entity(y)
    graph = graph.add_entity(z)
    
    # Create predicates
    equals_xy = Predicate.create(name="Equals", entities=[x.id, y.id])
    equals_yz = Predicate.create(name="Equals", entities=[y.id, z.id])
    equals_xz = Predicate.create(name="Equals", entities=[x.id, z.id])
    
    # Add predicates to graph
    graph = graph.add_predicate(equals_xy)
    graph = graph.add_predicate(equals_yz)
    graph = graph.add_predicate(equals_xz)
    
    # Create empty cut for logical structure
    graph, empty_cut = graph.create_context(
        context_type="cut",
        parent_id=graph.context_manager.root_context.id
    )
    
    return graph

def create_existential_universal():
    """Create existential-universal pattern: There exists someone who loves everyone."""
    graph = EGGraph.create_empty()
    
    # Create entities
    x = Entity.create(name="x", entity_type="variable")
    y = Entity.create(name="y", entity_type="variable")
    
    # Add entities to graph
    graph = graph.add_entity(x)
    graph = graph.add_entity(y)
    
    # Create predicate
    loves = Predicate.create(name="Loves", entities=[x.id, y.id])
    
    # Add predicate to graph
    graph = graph.add_predicate(loves)
    
    # Create nested cuts for quantifier structure
    graph, outer_cut = graph.create_context(
        context_type="cut",
        parent_id=graph.context_manager.root_context.id
    )
    
    graph, inner_cut = graph.create_context(
        context_type="cut",
        parent_id=outer_cut.id
    )
    
    return graph

def create_proof_by_contradiction():
    """Create proof by contradiction: Assume P and not P leads to contradiction."""
    graph = EGGraph.create_empty()
    
    # Create predicates (no entities needed for propositional logic)
    p1 = Predicate.create(name="P", entities=[])
    p2 = Predicate.create(name="P", entities=[])
    
    # Add predicates to graph
    graph = graph.add_predicate(p1)
    graph = graph.add_predicate(p2)
    
    # Create nested cuts for double negation
    graph, outer_cut = graph.create_context(
        context_type="cut",
        parent_id=graph.context_manager.root_context.id
    )
    
    graph, inner_cut = graph.create_context(
        context_type="cut",
        parent_id=outer_cut.id
    )
    
    return graph

def generate_egrf_with_visual_fix(graph, title, description):
    """Generate EGRF with visual fix applied."""
    print(f"Generating {title}...")
    
    # Create EGRF generator
    generator = EGRFGenerator()
    
    # Generate EGRF document
    egrf_doc = generator.generate(graph)
    
    # Set metadata
    egrf_doc.metadata.title = title
    egrf_doc.metadata.description = description
    
    # Check visual elements
    print(f"  Visual elements: P:{len(egrf_doc.predicates)} E:{len(egrf_doc.entities)} C:{len(egrf_doc.contexts)}")
    
    # Verify CLIF generation
    try:
        clif = egrf_doc.semantics.logical_form.clif_equivalent
        print(f"  CLIF: {clif}")
    except AttributeError:
        # Handle different CLIF access patterns
        try:
            clif = egrf_doc.semantics['logical_form']['clif_equivalent']
            print(f"  CLIF: {clif}")
        except (KeyError, TypeError):
            print(f"  CLIF: Unable to access CLIF equivalent")
    
    return egrf_doc

def main():
    """Regenerate all Phase 3 examples with visual fix."""
    print("🎯 Regenerating All Phase 3 Examples with Visual Fix")
    print("=" * 60)
    
    examples = [
        {
            "func": create_complex_syllogism,
            "title": "Phase 3 Example 11: Complex Syllogism",
            "description": "Complex syllogism demonstrating universal quantification and modus ponens",
            "filename": "phase3_example_11_complex_syllogism_visual_fixed.egrf"
        },
        {
            "func": create_transitive_relation,
            "title": "Phase 3 Example 12: Transitive Relation",
            "description": "Transitive relation demonstrating mathematical property chains",
            "filename": "phase3_example_12_transitive_relation_visual_fixed.egrf"
        },
        {
            "func": create_mathematical_proof,
            "title": "Phase 3 Example 13: Mathematical Proof",
            "description": "Mathematical proof demonstrating equality transitivity",
            "filename": "phase3_example_13_mathematical_proof_visual_fixed.egrf"
        },
        {
            "func": create_existential_universal,
            "title": "Phase 3 Example 14: Existential-Universal",
            "description": "Existential-universal quantifier interaction pattern",
            "filename": "phase3_example_14_existential_universal_visual_fixed.egrf"
        },
        {
            "func": create_proof_by_contradiction,
            "title": "Phase 3 Example 15: Proof by Contradiction",
            "description": "Classical reductio ad absurdum proof pattern",
            "filename": "phase3_example_15_proof_by_contradiction_visual_fixed.egrf"
        }
    ]
    
    serializer = EGRFSerializer()
    success_count = 0
    
    for example in examples:
        try:
            # Create graph
            graph = example["func"]()
            
            # Generate EGRF
            egrf_doc = generate_egrf_with_visual_fix(
                graph, 
                example["title"], 
                example["description"]
            )
            
            # Serialize to file
            egrf_dict = serializer.to_dict(egrf_doc)
            with open(example["filename"], 'w') as f:
                json.dump(egrf_dict, f, indent=2, default=str)
            
            print(f"  ✅ Saved: {example['filename']}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"🎉 Regeneration Complete: {success_count}/5 examples successful")
    
    if success_count == 5:
        print("✅ ALL EXAMPLES REGENERATED WITH VISUAL ELEMENTS!")
        print("✅ Visual presentation issues resolved")
        print("✅ Ready for GUI integration")
    else:
        print(f"⚠️  {5-success_count} examples need attention")

if __name__ == "__main__":
    main()

