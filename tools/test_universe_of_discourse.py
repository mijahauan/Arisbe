"""
Test Suite for Universe of Discourse Model

Comprehensive tests demonstrating:
1. Static UoDs (literature imports)
2. Dynamic UoDs (active reasoning with history)
3. LayoutDeltas integration
4. Backward compatibility
5. Category system
6. Promotion and transformation tracking
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDMetadata,
    UoDType,
    UoDCategory,
)
from egi_core_dau import create_empty_graph, create_vertex
from formal_transformation_rules import IterationRule, TransformationContext


def test_static_uod_creation():
    """Test creating a static UoD (literature import)."""
    print("=" * 70)
    print("TEST 1: Static UoD Creation (Literature Import)")
    print("=" * 70)
    
    # Create empty EGI for testing
    egi = create_empty_graph()
    vertex = create_vertex(label="Human", is_generic=False)
    egi = egi.with_vertex(vertex)
    
    # Create static UoD metadata
    metadata = UoDMetadata(
        uod_id="peirce_human_001",
        uod_type=UoDType.STANDALONE,
        name="Peirce's Human Example",
        description="Simple graph from Peirce CP 4.394",
        category=UoDCategory.LITERATURE_EXAMPLE,
        created=datetime.now(),
        last_modified=datetime.now(),
        source_citation="Peirce CP 4.394",
        authors=["Charles S. Peirce"],
        tags={"peirce", "simple", "example"},
    )
    
    # Create UoD
    uod = UniverseOfDiscourse(
        metadata=metadata,
        current_egi=egi,
        history=None
    )
    
    # Verify properties
    assert uod.is_standalone, "Should be standalone"
    assert not uod.is_historical, "Should not be historical"
    assert uod.is_static, "Should be static (literature import)"
    assert not uod.is_dynamic, "Should not be dynamic"
    assert uod.name == "Peirce's Human Example"
    assert uod.uod_id == "peirce_human_001"
    
    print(f"✅ Created static UoD: {uod.name}")
    print(f"   - ID: {uod.uod_id}")
    print(f"   - Category: {uod.category.value}")
    print(f"   - Type: {uod.uod_type.value}")
    print(f"   - Source: {uod.metadata.source_citation}")
    print(f"   - is_standalone: {uod.is_standalone}")
    print(f"   - is_historical: {uod.is_historical}")
    print(f"   - is_static: {uod.is_static}")
    print(f"   - is_dynamic: {uod.is_dynamic}")
    print()
    
    return uod


def test_dynamic_uod_creation():
    """Test creating a dynamic UoD (active reasoning)."""
    print("=" * 70)
    print("TEST 2: Dynamic UoD Creation (Active Inquiry)")
    print("=" * 70)
    
    # Create EGI (generic vertices have no label)
    egi = create_empty_graph()
    vertex = create_vertex(label=None, is_generic=True)
    egi = egi.with_vertex(vertex)
    
    # Create dynamic UoD metadata
    metadata = UoDMetadata(
        uod_id="inquiry_001",
        uod_type=UoDType.STANDALONE,  # Will become HISTORICAL after promotion
        name="Investigation of Quantification",
        description="Exploring existential quantification in EG",
        category=UoDCategory.ACTIVE_INQUIRY,
        created=datetime.now(),
        last_modified=datetime.now(),
        authors=["Current User"],
        tags={"inquiry", "quantification", "active"},
        domain_contexts={"logic", "existential_graphs"},
    )
    
    # Create UoD
    uod = UniverseOfDiscourse(
        metadata=metadata,
        current_egi=egi,
        current_layout_deltas={"vertex_positions": {vertex.id: [100, 100]}},
        history=None
    )
    
    # Verify initial state
    assert uod.is_standalone, "Should start standalone"
    assert not uod.is_historical, "Should not be historical yet"
    assert not uod.is_static, "Should not be static"
    assert uod.is_dynamic, "Should be dynamic (inquiry)"
    
    print(f"✅ Created dynamic UoD: {uod.name}")
    print(f"   - ID: {uod.uod_id}")
    print(f"   - Category: {uod.category.value}")
    print(f"   - Type: {uod.uod_type.value}")
    print(f"   - Domain contexts: {uod.metadata.domain_contexts}")
    print(f"   - Layout deltas: {bool(uod.current_layout_deltas)}")
    print(f"   - is_dynamic: {uod.is_dynamic}")
    print()
    
    return uod


def test_promotion_to_historical():
    """Test promoting standalone UoD to historical."""
    print("=" * 70)
    print("TEST 3: Promotion to Historical (Diachronic Tracking)")
    print("=" * 70)
    
    # Create standalone UoD
    egi = create_empty_graph()
    vertex = create_vertex(label="Alice", is_generic=False)
    egi = egi.with_vertex(vertex)
    
    metadata = UoDMetadata(
        uod_id="theorem_proof_001",
        uod_type=UoDType.STANDALONE,
        name="Modus Ponens Proof",
        description="Formal proof of modus ponens",
        category=UoDCategory.THEOREM_PROOF,
        created=datetime.now(),
        last_modified=datetime.now(),
        authors=["Prover"],
    )
    
    uod = UniverseOfDiscourse(
        metadata=metadata,
        current_egi=egi,
        current_layout_deltas={"test": "data"},
        history=None
    )
    
    # Verify initial state
    print(f"Before promotion:")
    print(f"   - is_standalone: {uod.is_standalone}")
    print(f"   - is_historical: {uod.is_historical}")
    print(f"   - uod_type: {uod.uod_type.value}")
    
    # Promote to historical
    uod.promote_to_historical("Initial state of proof")
    
    # Verify after promotion
    print(f"\nAfter promotion:")
    print(f"   - is_standalone: {uod.is_standalone}")
    print(f"   - is_historical: {uod.is_historical}")
    print(f"   - uod_type: {uod.uod_type.value}")
    print(f"   - History states: {len(uod.history.states)}")
    print(f"   - Current state ID: {uod.metadata.current_state_id}")
    
    # Verify history was created
    assert uod.is_historical, "Should be historical after promotion"
    assert not uod.is_standalone, "Should not be standalone after promotion"
    assert uod.history is not None, "History should exist"
    assert len(uod.history.states) == 1, "Should have initial state"
    assert uod.metadata.uod_type == UoDType.HISTORICAL, "Type should be HISTORICAL"
    
    # Verify initial state includes layout deltas
    initial_state = uod.get_current_state()
    assert "layout_deltas" in initial_state.diagram_metadata, "Should have layout deltas"
    assert initial_state.diagram_metadata["layout_deltas"]["test"] == "data"
    
    print(f"\n✅ Promotion successful!")
    print(f"   - Initial state description: {initial_state.description}")
    print(f"   - Layout deltas preserved: {bool(initial_state.diagram_metadata.get('layout_deltas'))}")
    print()
    
    return uod


def test_transformation_recording():
    """Test recording transformations in UoD history."""
    print("=" * 70)
    print("TEST 4: Transformation Recording (Diachronic Evolution)")
    print("=" * 70)
    
    # Create historical UoD (generic vertices have no label)
    egi = create_empty_graph()
    vertex1 = create_vertex(label=None, is_generic=True)
    egi = egi.with_vertex(vertex1)
    
    metadata = UoDMetadata(
        uod_id="epg_session_001",
        uod_type=UoDType.HISTORICAL,
        name="Endoporeutic Game Session",
        description="Practice game session",
        category=UoDCategory.EPG_SESSION,
        created=datetime.now(),
        last_modified=datetime.now(),
        authors=["Player"],
    )
    
    uod = UniverseOfDiscourse(
        metadata=metadata,
        current_egi=egi,
        history=None
    )
    
    # Promote to start tracking history
    uod.promote_to_historical("Game start")
    
    print(f"Initial state:")
    print(f"   - States: {len(uod.history.states)}")
    print(f"   - Transformations: {len(uod.history.transformations)}")
    print(f"   - Vertices in EGI: {len(uod.current_egi.V)}")
    
    # Apply transformation (add another vertex via iteration)
    vertex2 = create_vertex(label=None, is_generic=True)
    new_egi = uod.current_egi.with_vertex(vertex2)
    
    # Record transformation manually (simplified - would use formal rules in practice)
    from egi_transformation_history import TransformationStep, TransformationStatus
    from formal_transformation_rules import TransformationResult
    import uuid
    
    # Create transformation result
    result = TransformationResult(
        success=True,
        result_egi=new_egi,
        error_message=None,
        changes_made={"added_vertices": [vertex2.id]}
    )
    
    # Create mock context (simplified)
    from formal_transformation_rules import AreaPolarity
    context = TransformationContext(
        source_egi=uod.current_egi,
        target_area="sheet",
        selected_subgraph=frozenset([vertex1.id]),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0
    )
    
    # Add transformation to history
    step_id = uod.history.add_transformation(
        rule_name="IT+",
        context=context,
        result=result,
        user_annotation="Iterated generic variable"
    )
    
    # Update current state
    uod.update_current_state(new_egi)
    
    print(f"\nAfter transformation:")
    print(f"   - States: {len(uod.history.states)}")
    print(f"   - Transformations: {len(uod.history.transformations)}")
    print(f"   - Vertices in EGI: {len(uod.current_egi.V)}")
    print(f"   - Transformation ID: {step_id}")
    
    # Verify
    assert len(uod.history.states) == 2, "Should have 2 states"
    assert len(uod.history.transformations) == 1, "Should have 1 transformation"
    assert len(uod.current_egi.V) == 2, "Should have 2 vertices"
    
    # Get transformation details
    step = uod.get_transformation(step_id)
    print(f"\nTransformation details:")
    print(f"   - Rule: {step.rule_name}")
    print(f"   - Status: {step.status.value}")
    print(f"   - Annotation: {step.user_annotation}")
    
    print(f"\n✅ Transformation recorded successfully!")
    print()
    
    return uod


def test_backward_compatibility():
    """Test backward compatibility with old naming."""
    print("=" * 70)
    print("TEST 5: Backward Compatibility (Old Import Names)")
    print("=" * 70)
    
    # Import using old names
    from graph_entity import (
        GraphEntity,
        EntityMetadata,
        EntityType,
        EntityCategory,
    )
    
    # Verify aliases work
    assert GraphEntity is UniverseOfDiscourse, "GraphEntity should be alias"
    assert EntityMetadata is UoDMetadata, "EntityMetadata should be alias"
    assert EntityType is UoDType, "EntityType should be alias"
    assert EntityCategory is UoDCategory, "EntityCategory should be alias"
    
    print(f"✅ Import aliases verified:")
    print(f"   - GraphEntity = {GraphEntity.__name__}")
    print(f"   - EntityMetadata = {EntityMetadata.__name__}")
    print(f"   - EntityType = {EntityType.__name__}")
    print(f"   - EntityCategory = {EntityCategory.__name__}")
    
    # Create using old names
    egi = create_empty_graph()
    
    metadata = EntityMetadata(
        uod_id="test_compat_001",
        uod_type=EntityType.STANDALONE,
        name="Compatibility Test",
        description="Testing old naming",
        category=EntityCategory.USER_CREATED,
        created=datetime.now(),
        last_modified=datetime.now(),
    )
    
    entity = GraphEntity(
        metadata=metadata,
        current_egi=egi,
        history=None
    )
    
    # Verify it's actually a UniverseOfDiscourse
    assert isinstance(entity, UniverseOfDiscourse), "Should be UniverseOfDiscourse"
    assert entity.name == "Compatibility Test"
    
    # Test property aliases
    assert hasattr(metadata, 'entity_id'), "Should have entity_id property"
    assert hasattr(metadata, 'entity_type'), "Should have entity_type property"
    assert metadata.entity_id == metadata.uod_id, "entity_id should map to uod_id"
    assert metadata.entity_type == metadata.uod_type, "entity_type should map to uod_type"
    
    print(f"\n✅ Old naming works correctly:")
    print(f"   - Created with GraphEntity name")
    print(f"   - Actually is: {type(entity).__name__}")
    print(f"   - metadata.entity_id: {metadata.entity_id}")
    print(f"   - metadata.entity_type: {metadata.entity_type.value}")
    print()
    
    return entity


def test_category_mapping():
    """Test category mapping from old to new values."""
    print("=" * 70)
    print("TEST 6: Category Mapping (Old → New)")
    print("=" * 70)
    
    # Test category mapping in from_dict
    old_metadata_dict = {
        "entity_id": "test_map_001",
        "entity_type": "standalone",
        "name": "Category Map Test",
        "description": "Testing category mapping",
        "category": "peirce",  # Old category name
        "created": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
    }
    
    metadata = UoDMetadata.from_dict(old_metadata_dict)
    
    # Verify mapping
    assert metadata.category == UoDCategory.LITERATURE_EXAMPLE, "peirce should map to LITERATURE_EXAMPLE"
    
    print(f"✅ Category mapping verified:")
    print(f"   - Input: 'peirce'")
    print(f"   - Output: {metadata.category.value}")
    
    # Test other mappings
    mappings = {
        "peirce": UoDCategory.LITERATURE_EXAMPLE,
        "scholars": UoDCategory.LITERATURE_EXAMPLE,
        "canonical": UoDCategory.CANONICAL_PATTERN,
        "user_created": UoDCategory.ACTIVE_INQUIRY,
        "epg": UoDCategory.EPG_SESSION,
    }
    
    print(f"\n   All category mappings:")
    for old, new in mappings.items():
        test_dict = {
            "entity_id": "test",
            "entity_type": "standalone",
            "name": "Test",
            "description": "Test",
            "category": old,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
        }
        result = UoDMetadata.from_dict(test_dict)
        assert result.category == new, f"{old} should map to {new.value}"
        print(f"      {old:15} → {new.value}")
    
    print()


def test_layout_deltas_workflow():
    """Test complete LayoutDeltas workflow."""
    print("=" * 70)
    print("TEST 7: LayoutDeltas Workflow (Visual Stability)")
    print("=" * 70)
    
    # Create UoD with initial layout deltas
    egi = create_empty_graph()
    vertex = create_vertex(label="Test", is_generic=False)
    egi = egi.with_vertex(vertex)
    
    initial_deltas = {
        "vertex_positions": {
            vertex.id: [150, 200]
        },
        "zoom_level": 1.5,
    }
    
    metadata = UoDMetadata(
        uod_id="layout_test_001",
        uod_type=UoDType.STANDALONE,
        name="Layout Test",
        description="Testing layout delta preservation",
        category=UoDCategory.PRACTICE_SESSION,
        created=datetime.now(),
        last_modified=datetime.now(),
    )
    
    uod = UniverseOfDiscourse(
        metadata=metadata,
        current_egi=egi,
        current_layout_deltas=initial_deltas,
        history=None
    )
    
    print(f"Initial layout deltas: {uod.current_layout_deltas}")
    
    # Promote to historical
    uod.promote_to_historical("Initial state with layout")
    
    # Verify deltas in history
    initial_state = uod.get_current_state()
    assert "layout_deltas" in initial_state.diagram_metadata
    assert initial_state.diagram_metadata["layout_deltas"] == initial_deltas
    
    print(f"✅ Layout deltas preserved in initial state")
    print(f"   - vertex_positions: {initial_state.diagram_metadata['layout_deltas']['vertex_positions']}")
    print(f"   - zoom_level: {initial_state.diagram_metadata['layout_deltas']['zoom_level']}")
    
    # Update with new deltas
    new_deltas = {
        "vertex_positions": {
            vertex.id: [200, 250]
        },
        "zoom_level": 2.0,
    }
    
    uod.update_current_state(egi, new_layout_deltas=new_deltas)
    
    print(f"\n✅ Layout deltas updated:")
    print(f"   - New position: {uod.current_layout_deltas['vertex_positions'][vertex.id]}")
    print(f"   - New zoom: {uod.current_layout_deltas['zoom_level']}")
    print()


def test_type_checking_properties():
    """Test all type checking properties."""
    print("=" * 70)
    print("TEST 8: Type Checking Properties")
    print("=" * 70)
    
    # Test static literature example
    lit_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="lit_001",
            uod_type=UoDType.STANDALONE,
            name="Literature",
            description="Test",
            category=UoDCategory.LITERATURE_EXAMPLE,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=create_empty_graph(),
        history=None
    )
    
    print(f"Literature Example:")
    print(f"   - is_standalone: {lit_uod.is_standalone}")
    print(f"   - is_historical: {lit_uod.is_historical}")
    print(f"   - is_static: {lit_uod.is_static}")
    print(f"   - is_dynamic: {lit_uod.is_dynamic}")
    assert lit_uod.is_static and not lit_uod.is_dynamic
    
    # Test dynamic inquiry
    inq_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="inq_001",
            uod_type=UoDType.STANDALONE,
            name="Inquiry",
            description="Test",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=create_empty_graph(),
        history=None
    )
    
    print(f"\nActive Inquiry:")
    print(f"   - is_standalone: {inq_uod.is_standalone}")
    print(f"   - is_historical: {inq_uod.is_historical}")
    print(f"   - is_static: {inq_uod.is_static}")
    print(f"   - is_dynamic: {inq_uod.is_dynamic}")
    assert inq_uod.is_dynamic and not inq_uod.is_static
    
    # Promote and test again
    inq_uod.promote_to_historical("Start")
    print(f"\nActive Inquiry (after promotion):")
    print(f"   - is_standalone: {inq_uod.is_standalone}")
    print(f"   - is_historical: {inq_uod.is_historical}")
    print(f"   - is_static: {inq_uod.is_static}")
    print(f"   - is_dynamic: {inq_uod.is_dynamic}")
    assert inq_uod.is_historical and inq_uod.is_dynamic
    
    print(f"\n✅ Type checking properties work correctly!")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("UNIVERSE OF DISCOURSE MODEL TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        # Run all tests
        uod1 = test_static_uod_creation()
        uod2 = test_dynamic_uod_creation()
        uod3 = test_promotion_to_historical()
        uod4 = test_transformation_recording()
        uod5 = test_backward_compatibility()
        test_category_mapping()
        test_layout_deltas_workflow()
        test_type_checking_properties()
        
        # Summary
        print("=" * 70)
        print("ALL TESTS PASSED! ✅")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"   ✅ Static UoD creation (literature imports)")
        print(f"   ✅ Dynamic UoD creation (active reasoning)")
        print(f"   ✅ Promotion to historical tracking")
        print(f"   ✅ Transformation recording in history")
        print(f"   ✅ Backward compatibility with old names")
        print(f"   ✅ Category mapping (old → new)")
        print(f"   ✅ LayoutDeltas workflow")
        print(f"   ✅ Type checking properties")
        print()
        print("The UniverseOfDiscourse model is working correctly!")
        print("Ready for Phase 3: Storage Migration")
        print()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
