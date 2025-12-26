#!/usr/bin/env python3
"""
Concrete Example: EGI Transformation History with Domain Model Integration

This example demonstrates the complete data model using Peirce's "man mortal" example,
showing how domain contexts, ontology mappings, and transformation history work together.

Scenario: Medical reasoning about mortality using both philosophical and medical ontologies.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timezone
from egi_io import load_egi_json
from enhanced_transformation_history import EnhancedEGITransformationHistory, ProofExportFormat
from domain_ontology_model import (
    DomainModelManager, OntologyReference, OntologyType, ConceptMapping, 
    ConceptType, WordNetConnector, OWLConnector
)
from formal_transformation_rules import (
    TransformationContext, AreaPolarity, DeiterationRule
)
from egi_transformation_history import LogicalProvenance
from egi_core_dau import ElementID

def create_concrete_example():
    """Create a concrete example of the transformation history system."""
    
    print("=== EGI Transformation History with Domain Model Integration ===")
    print("Example: Peirce's 'Man Mortal' with Medical and Philosophical Contexts\n")
    
    # 1. Load the initial EGI
    print("1. Loading initial EGI...")
    egif_path = "corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.egi.json"
    initial_egi = load_egi_json(egif_path)
    print(f"   ✓ Loaded EGI with {len(initial_egi.V)} vertices, {len(initial_egi.E)} edges, {len(initial_egi.Cut)} cuts")
    
    # 2. Create enhanced transformation history
    print("\n2. Creating enhanced transformation history...")
    history = EnhancedEGITransformationHistory(
        initial_egi=initial_egi,
        description="Peirce's man-mortal example with domain model integration"
    )
    print(f"   ✓ History created with ID: {history.history_id}")
    
    # 3. Set up domain contexts and ontologies
    print("\n3. Setting up domain contexts and ontologies...")
    
    # Register ontologies
    philosophical_ontology = OntologyReference(
        ontology_id="philosophical_concepts",
        ontology_type=OntologyType.LOCAL,
        name="Philosophical Concepts",
        version="1.0",
        uri="http://arisbe.org/ontologies/philosophical",
        description="Local ontology for philosophical reasoning concepts"
    )
    
    medical_ontology = OntologyReference(
        ontology_id="snomed_ct",
        ontology_type=OntologyType.SNOMED,
        name="SNOMED CT",
        version="2024",
        uri="http://snomed.info/sct",
        api_endpoint="https://browser.ihtsdotools.org/snowstorm/snomed-ct",
        description="SNOMED Clinical Terms medical ontology"
    )
    
    wordnet_ontology = OntologyReference(
        ontology_id="wordnet",
        ontology_type=OntologyType.WORDNET,
        name="Princeton WordNet",
        version="3.1",
        uri="http://wordnet.princeton.edu/",
        description="WordNet lexical database"
    )
    
    # Register ontologies with the domain model manager
    history.domain_model_manager.register_ontology(philosophical_ontology)
    history.domain_model_manager.register_ontology(medical_ontology)
    history.domain_model_manager.register_ontology(wordnet_ontology, WordNetConnector())
    
    print(f"   ✓ Registered {len(history.domain_model_manager.ontology_references)} ontologies")
    
    # 4. Create domain contexts
    print("\n4. Creating domain contexts...")
    
    # Philosophical context
    phil_context_id = history.domain_model_manager.create_domain_context(
        name="Classical Logic",
        description="Philosophical reasoning about logical relationships",
        primary_ontology_id="philosophical_concepts",
        secondary_ontologies=["wordnet"]
    )
    
    # Medical context  
    medical_context_id = history.domain_model_manager.create_domain_context(
        name="Medical Reasoning",
        description="Medical knowledge about human mortality",
        primary_ontology_id="snomed_ct",
        secondary_ontologies=["wordnet"]
    )
    
    print(f"   ✓ Created philosophical context: {phil_context_id}")
    print(f"   ✓ Created medical context: {medical_context_id}")
    
    # 5. Map EGI elements to ontological concepts
    print("\n5. Mapping EGI elements to ontological concepts...")
    
    # Find the Human and Mortal relations
    human_edge = None
    mortal_edge = None
    socrates_vertex = None
    
    for edge in initial_egi.E:
        relation_name = initial_egi.rel.get(edge.id)
        if relation_name == "Human":
            human_edge = edge.id
        elif relation_name == "Mortal":
            mortal_edge = edge.id
    
    for vertex in initial_egi.V:
        if initial_egi.rho.get(vertex.id) == "Socrates":
            socrates_vertex = vertex.id
    
    # Map Human concept
    if human_edge:
        # Philosophical mapping
        history.domain_model_manager.map_element_to_concept(
            element_id=human_edge,
            ontology_id="philosophical_concepts",
            concept_uri="http://arisbe.org/ontologies/philosophical#Human",
            concept_type=ConceptType.CLASS,
            confidence=1.0,
            natural_language="human being"
        )
        
        # Medical mapping
        history.domain_model_manager.map_element_to_concept(
            element_id=human_edge,
            ontology_id="snomed_ct",
            concept_uri="http://snomed.info/sct/734000001",  # Human structure
            concept_type=ConceptType.CLASS,
            confidence=0.9,
            natural_language="human organism"
        )
        
        # Add to contexts
        history.domain_model_manager.add_element_to_context(human_edge, phil_context_id)
        history.domain_model_manager.add_element_to_context(human_edge, medical_context_id)
        
        print(f"   ✓ Mapped Human relation to both philosophical and medical concepts")
    
    # Map Mortal concept
    if mortal_edge:
        # Philosophical mapping
        history.domain_model_manager.map_element_to_concept(
            element_id=mortal_edge,
            ontology_id="philosophical_concepts", 
            concept_uri="http://arisbe.org/ontologies/philosophical#Mortal",
            concept_type=ConceptType.PROPERTY,
            confidence=1.0,
            natural_language="subject to death"
        )
        
        # Medical mapping
        history.domain_model_manager.map_element_to_concept(
            element_id=mortal_edge,
            ontology_id="snomed_ct",
            concept_uri="http://snomed.info/sct/419099009",  # Dead
            concept_type=ConceptType.PROPERTY,
            confidence=0.8,
            natural_language="capable of dying"
        )
        
        # Add to contexts
        history.domain_model_manager.add_element_to_context(mortal_edge, phil_context_id)
        history.domain_model_manager.add_element_to_context(mortal_edge, medical_context_id)
        
        print(f"   ✓ Mapped Mortal relation to both philosophical and medical concepts")
    
    # Map Socrates
    if socrates_vertex:
        # Philosophical mapping
        history.domain_model_manager.map_element_to_concept(
            element_id=socrates_vertex,
            ontology_id="philosophical_concepts",
            concept_uri="http://arisbe.org/ontologies/philosophical#Socrates",
            concept_type=ConceptType.INDIVIDUAL,
            confidence=1.0,
            natural_language="the philosopher Socrates"
        )
        
        # Add to philosophical context only
        history.domain_model_manager.add_element_to_context(socrates_vertex, phil_context_id)
        
        print(f"   ✓ Mapped Socrates to philosophical context")
    
    # 6. Create semantic annotations
    print("\n6. Creating semantic annotations...")
    
    # Annotate the overall structure
    all_elements = {human_edge, mortal_edge, socrates_vertex} - {None}
    
    phil_annotation_id = history.add_semantic_annotation_to_state(
        state_id=history.current_state_id,
        target_elements=all_elements,
        domain_context_id=phil_context_id,
        natural_language="If Socrates is human, then Socrates is mortal",
        logical_forms={
            "clif": "(if (Human Socrates) (Mortal Socrates))",
            "fol": "Human(Socrates) → Mortal(Socrates)",
            "dl": "Human(Socrates) ⊑ Mortal(Socrates)"
        }
    )
    
    medical_annotation_id = history.add_semantic_annotation_to_state(
        state_id=history.current_state_id,
        target_elements={human_edge, mortal_edge} - {None},
        domain_context_id=medical_context_id,
        natural_language="All human organisms are subject to biological death",
        logical_forms={
            "clif": "(forall (x) (if (Human x) (Mortal x)))",
            "fol": "∀x (Human(x) → Mortal(x))"
        }
    )
    
    print(f"   ✓ Created philosophical annotation: {phil_annotation_id}")
    print(f"   ✓ Created medical annotation: {medical_annotation_id}")
    
    # 7. Demonstrate a transformation with domain context
    print("\n7. Demonstrating transformation with domain context...")
    
    # Create a logical provenance for a hypothetical transformation
    provenance = LogicalProvenance(
        rule_citation="Peirce Alpha.2 (Double Negation)",
        logical_equivalence="~~P ≡ P",
        semantic_interpretation="Removing double negation preserves logical meaning",
        proof_obligations=["Verify no free variables captured", "Maintain area polarity"],
        domain_assumptions=["Classical logic applies", "Excluded middle holds"],
        ontological_commitments=["Individuals exist in domain", "Properties are well-defined"]
    )
    
    # Simulate applying a transformation (we'll use a mock context)
    from formal_transformation_rules import TransformationResult
    from egi_core_dau import RelationalGraphWithCuts
    
    # For demonstration, we'll create a mock successful transformation
    mock_result = TransformationResult(
        success=True,
        result_egi=initial_egi,  # In reality, this would be the transformed EGI
        error_message=None,
        changes_made={"rule_applied": "Double Negation Elimination", "elements_affected": 1}
    )
    
    # Create transformation context
    mock_context = TransformationContext(
        source_egi=initial_egi,
        target_area=ElementID("c_ddf31f9b"),  # Inner cut from the example
        selected_subgraph=frozenset([mortal_edge]) if mortal_edge else frozenset(),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=2
    )
    
    # Add transformation with domain context
    step_id = history.add_transformation_with_domain_context(
        rule_name="Double Negation Elimination",
        context=mock_context,
        result=mock_result,
        domain_contexts={phil_context_id, medical_context_id},
        natural_language="Simplified the logical structure by removing redundant negations",
        logical_provenance=provenance,
        author_id="user_demo"
    )
    
    print(f"   ✓ Added transformation step: {step_id}")
    
    # 8. Generate natural language narrative
    print("\n8. Generating natural language narrative...")
    
    initial_state_id = history.state_sequence[0]
    current_state_id = history.current_state_id
    
    narrative = history.get_natural_language_narrative(initial_state_id, current_state_id)
    print("   Natural Language Narrative:")
    print("   " + "\n   ".join(narrative.split("\n")))
    
    # 9. Validate the transformation sequence
    print("\n9. Validating transformation sequence...")
    
    validation = history.validate_transformation_sequence(initial_state_id, current_state_id)
    print(f"   ✓ Sequence valid: {validation['is_valid']}")
    print(f"   ✓ Rule violations: {len(validation['rule_violations'])}")
    print(f"   ✓ Domain consistency issues: {len(validation['domain_consistency_issues'])}")
    
    # 10. Export proof in different formats
    print("\n10. Exporting proofs in different formats...")
    
    # Natural deduction export
    nd_proof = history.export_proof_sequence(
        from_state_id=initial_state_id,
        to_state_id=current_state_id,
        export_format=ProofExportFormat.NATURAL_DEDUCTION,
        include_domain_context=True
    )
    
    print("   Natural Deduction Proof:")
    print("   " + "\n   ".join(nd_proof.split("\n")[:10]))  # First 10 lines
    
    # LaTeX export
    latex_proof = history.export_proof_sequence(
        from_state_id=initial_state_id,
        to_state_id=current_state_id,
        export_format=ProofExportFormat.LATEX_PROOF,
        include_domain_context=True
    )
    
    print("\n   LaTeX Proof:")
    print("   " + "\n   ".join(latex_proof.split("\n")))
    
    # 11. Show domain model statistics
    print("\n11. Domain model statistics...")
    
    phil_context = history.domain_model_manager.domain_contexts[phil_context_id]
    medical_context = history.domain_model_manager.domain_contexts[medical_context_id]
    
    print(f"   Philosophical context: {len(phil_context.scoped_elements)} elements")
    print(f"   Medical context: {len(medical_context.scoped_elements)} elements")
    print(f"   Total concept mappings: {len(history.domain_model_manager.global_concept_mappings)}")
    print(f"   Total semantic annotations: {len(history.domain_model_manager.semantic_annotations)}")
    
    # 12. Show collaboration status
    print("\n12. Collaboration status...")
    
    collab_status = history.get_collaboration_status()
    print(f"   Session ID: {collab_status['session_id']}")
    print(f"   Active participants: {collab_status['active_participants']}")
    print(f"   Lock status: {collab_status['lock_status']}")
    
    # 13. Show history statistics
    print("\n13. History statistics...")
    
    stats = history.get_history_statistics()
    print(f"   Total states: {stats['total_states']}")
    print(f"   Total transformations: {stats['total_transformations']}")
    print(f"   Current step: {stats['current_step']}")
    print(f"   Success rate: {stats['successful_transformations']}/{stats['total_transformations']}")
    
    print("\n=== Example Complete ===")
    print("This demonstrates:")
    print("• Multi-domain contexts (philosophical + medical)")
    print("• Ontology integration (local + SNOMED + WordNet)")
    print("• Concept mappings with confidence scores")
    print("• Rich semantic annotations with multiple logical forms")
    print("• Transformation history with logical provenance")
    print("• Natural language generation")
    print("• Proof export in multiple formats")
    print("• Validation and integrity checking")
    print("• Collaboration support")
    
    return history

if __name__ == "__main__":
    try:
        example_history = create_concrete_example()
        print(f"\n✓ Example completed successfully!")
        print(f"History ID: {example_history.history_id}")
    except Exception as e:
        print(f"\n✗ Example failed: {e}")
        import traceback
        traceback.print_exc()
