"""
Tests for EGRF v3.0 Logical Types

Tests the core data structures for logical containment architecture.
"""

import pytest
import json
from src.egrf.v3.logical_types import (
    # Basic types
    LogicalPoint, LogicalSize, LogicalBounds, SpacingConstraint,
    
    # Constraint types
    PositioningType, ContainerType, SizeConstraints, SpacingConstraints,
    MovementConstraints, LayoutConstraints, ContainmentRelationship,
    
    # Element types
    LogicalProperties, LogicalElement, PredicateProperties, LogicalPredicate,
    EntityProperties, PathConstraints, ConnectionPoint, LogicalEntity,
    ContextProperties, LogicalContext,
    
    # Ligature types
    CutCrossing, LigatureConstraints, LogicalLigature,
    
    # Factory functions
    create_logical_predicate, create_logical_context, create_logical_entity
)


class TestBasicTypes:
    """Test basic geometric and constraint types."""
    
    def test_logical_point_creation(self):
        """Test LogicalPoint creation and properties."""
        point = LogicalPoint(x=50.0, y=75.0, coordinate_type="relative")
        
        assert point.x == 50.0
        assert point.y == 75.0
        assert point.coordinate_type == "relative"
    
    def test_logical_size_creation(self):
        """Test LogicalSize creation and properties."""
        size = LogicalSize(width=100.0, height=50.0, size_type="preferred")
        
        assert size.width == 100.0
        assert size.height == 50.0
        assert size.size_type == "preferred"
    
    def test_spacing_constraint_creation(self):
        """Test SpacingConstraint creation and properties."""
        spacing = SpacingConstraint(min=10.0, preferred=20.0, max=40.0)
        
        assert spacing.min == 10.0
        assert spacing.preferred == 20.0
        assert spacing.max == 40.0


class TestLayoutConstraints:
    """Test layout constraint types."""
    
    def test_size_constraints_creation(self):
        """Test SizeConstraints creation with different size types."""
        min_size = LogicalSize(40.0, 20.0)
        preferred_size = LogicalSize(60.0, 30.0)
        max_size = LogicalSize(120.0, 60.0)
        
        constraints = SizeConstraints(
            min=min_size,
            preferred=preferred_size,
            max=max_size,
            auto_size=False,
            size_calculation="fixed"
        )
        
        assert constraints.min == min_size
        assert constraints.preferred == preferred_size
        assert constraints.max == max_size
        assert constraints.auto_size is False
        assert constraints.size_calculation == "fixed"
    
    def test_spacing_constraints_creation(self):
        """Test SpacingConstraints creation."""
        sibling_spacing = SpacingConstraint(min=10.0, preferred=20.0)
        edge_spacing = SpacingConstraint(min=5.0, preferred=15.0)
        
        constraints = SpacingConstraints(
            to_siblings=sibling_spacing,
            to_container_edge=edge_spacing
        )
        
        assert constraints.to_siblings == sibling_spacing
        assert constraints.to_container_edge == edge_spacing
        assert len(constraints.to_specific_elements) == 0
    
    def test_movement_constraints_creation(self):
        """Test MovementConstraints creation."""
        constraints = MovementConstraints(
            moveable=True,
            movement_bounds="container_interior",
            forbidden_areas=["element-1", "element-2"],
            snap_to_grid=True,
            grid_size=10.0
        )
        
        assert constraints.moveable is True
        assert constraints.movement_bounds == "container_interior"
        assert constraints.forbidden_areas == ["element-1", "element-2"]
        assert constraints.snap_to_grid is True
        assert constraints.grid_size == 10.0
    
    def test_layout_constraints_creation(self):
        """Test complete LayoutConstraints creation."""
        size_constraints = SizeConstraints(auto_size=True)
        spacing_constraints = SpacingConstraints()
        movement_constraints = MovementConstraints(moveable=True)
        
        layout = LayoutConstraints(
            container="parent-context",
            positioning_type=PositioningType.CONSTRAINT_BASED,
            size_constraints=size_constraints,
            spacing_constraints=spacing_constraints,
            movement_constraints=movement_constraints,
            collision_avoidance=True,
            shape="rectangle"
        )
        
        assert layout.container == "parent-context"
        assert layout.positioning_type == PositioningType.CONSTRAINT_BASED
        assert layout.size_constraints == size_constraints
        assert layout.spacing_constraints == spacing_constraints
        assert layout.movement_constraints == movement_constraints
        assert layout.collision_avoidance is True
        assert layout.shape == "rectangle"


class TestContainmentRelationship:
    """Test containment relationship types."""
    
    def test_containment_relationship_creation(self):
        """Test ContainmentRelationship creation."""
        relationship = ContainmentRelationship(
            container="cut-1",
            contained_elements=["predicate-1", "entity-1"],
            constraint_type="strict_containment",
            nesting_level=1,
            semantic_role="negation"
        )
        
        assert relationship.container == "cut-1"
        assert relationship.contained_elements == ["predicate-1", "entity-1"]
        assert relationship.constraint_type == "strict_containment"
        assert relationship.nesting_level == 1
        assert relationship.semantic_role == "negation"


class TestLogicalElements:
    """Test logical element types."""
    
    def test_logical_predicate_creation(self):
        """Test LogicalPredicate creation and serialization."""
        properties = PredicateProperties(
            arity=2,
            connected_entities=["entity-1", "entity-2"],
            predicate_type="relation",
            semantic_role="assertion"
        )
        
        layout = LayoutConstraints(
            container="sheet_of_assertion",
            positioning_type=PositioningType.CONSTRAINT_BASED
        )
        
        predicate = LogicalPredicate(
            id="predicate-1",
            name="Teacher",
            element_type="predicate",
            logical_properties=properties,
            layout_constraints=layout
        )
        
        assert predicate.id == "predicate-1"
        assert predicate.name == "Teacher"
        assert predicate.element_type == "predicate"
        assert predicate.logical_properties.arity == 2
        assert predicate.logical_properties.connected_entities == ["entity-1", "entity-2"]
        
        # Test serialization
        predicate_dict = predicate.to_dict()
        assert predicate_dict["id"] == "predicate-1"
        assert predicate_dict["name"] == "Teacher"
        assert predicate_dict["element_type"] == "predicate"
        assert predicate_dict["logical_properties"]["arity"] == 2
        assert predicate_dict["logical_properties"]["connected_entities"] == ["entity-1", "entity-2"]
    
    def test_logical_entity_creation(self):
        """Test LogicalEntity creation and serialization."""
        properties = EntityProperties(
            entity_type="constant",
            connected_predicates=["predicate-1", "predicate-2"],
            ligature_group="socrates_identity"
        )
        
        path_constraints = PathConstraints(
            path_type="flexible",
            avoid_overlaps=True,
            prefer_straight_lines=True,
            min_length=15.0
        )
        
        connection_points = [
            ConnectionPoint(connects_to="predicate-1", attachment="flexible", priority="high"),
            ConnectionPoint(connects_to="predicate-2", attachment="flexible", priority="high")
        ]
        
        layout = LayoutConstraints(
            container="auto",
            positioning_type=PositioningType.CONNECTION_DRIVEN,
            shape="line"
        )
        
        entity = LogicalEntity(
            id="entity-1",
            name="Socrates",
            element_type="entity",
            logical_properties=properties,
            layout_constraints=layout,
            path_constraints=path_constraints,
            connection_points=connection_points
        )
        
        assert entity.id == "entity-1"
        assert entity.name == "Socrates"
        assert entity.element_type == "entity"
        assert entity.logical_properties.entity_type == "constant"
        assert entity.logical_properties.ligature_group == "socrates_identity"
        assert len(entity.connection_points) == 2
        assert entity.path_constraints.min_length == 15.0
        
        # Test serialization
        entity_dict = entity.to_dict()
        assert entity_dict["id"] == "entity-1"
        assert entity_dict["logical_properties"]["entity_type"] == "constant"
        assert entity_dict["logical_properties"]["ligature_group"] == "socrates_identity"
        assert len(entity_dict["connection_points"]) == 2
        assert entity_dict["path_constraints"]["min_length"] == 15.0
    
    def test_logical_context_creation(self):
        """Test LogicalContext creation and serialization."""
        properties = ContextProperties(
            context_type="cut",
            is_root=False,
            auto_size=True,
            nesting_level=1,
            padding=SpacingConstraint(min=15.0, preferred=25.0, max=40.0)
        )
        
        layout = LayoutConstraints(
            container="sheet_of_assertion",
            positioning_type=PositioningType.CONSTRAINT_BASED,
            shape="oval"
        )
        
        context = LogicalContext(
            id="cut-1",
            name="Negation Cut",
            element_type="context",
            logical_properties=properties,
            layout_constraints=layout
        )
        
        assert context.id == "cut-1"
        assert context.name == "Negation Cut"
        assert context.element_type == "context"
        assert context.logical_properties.context_type == "cut"
        assert context.logical_properties.is_root is False
        assert context.logical_properties.auto_size is True
        assert context.logical_properties.nesting_level == 1
        
        # Test serialization
        context_dict = context.to_dict()
        assert context_dict["id"] == "cut-1"
        assert context_dict["logical_properties"]["context_type"] == "cut"
        assert context_dict["logical_properties"]["is_root"] is False
        assert context_dict["logical_properties"]["auto_size"] is True


class TestLigatureTypes:
    """Test ligature types for cross-context connections."""
    
    def test_cut_crossing_creation(self):
        """Test CutCrossing creation."""
        crossing = CutCrossing(
            cut_id="cut-1",
            crossing_point="gui_determined",
            crossing_style="perpendicular_preferred",
            crossing_flexible=True
        )
        
        assert crossing.cut_id == "cut-1"
        assert crossing.crossing_point == "gui_determined"
        assert crossing.crossing_style == "perpendicular_preferred"
        assert crossing.crossing_flexible is True
    
    def test_ligature_constraints_creation(self):
        """Test LigatureConstraints creation."""
        crossings = [
            CutCrossing(cut_id="cut-1"),
            CutCrossing(cut_id="cut-2")
        ]
        
        constraints = LigatureConstraints(
            path_type="flexible",
            cut_crossings=crossings,
            avoid_overlaps=True,
            routing_algorithm="shortest_path_with_constraints"
        )
        
        assert constraints.path_type == "flexible"
        assert len(constraints.cut_crossings) == 2
        assert constraints.avoid_overlaps is True
        assert constraints.routing_algorithm == "shortest_path_with_constraints"
    
    def test_logical_ligature_creation(self):
        """Test LogicalLigature creation and serialization."""
        crossings = [CutCrossing(cut_id="cut-1")]
        constraints = LigatureConstraints(cut_crossings=crossings)
        
        ligature = LogicalLigature(
            id="ligature-1",
            connects=["entity-1", "entity-2"],
            logical_properties={"identity_assertion": True},
            layout_constraints=constraints
        )
        
        assert ligature.id == "ligature-1"
        assert ligature.connects == ["entity-1", "entity-2"]
        assert ligature.logical_properties["identity_assertion"] is True
        assert len(ligature.layout_constraints.cut_crossings) == 1
        
        # Test serialization
        ligature_dict = ligature.to_dict()
        assert ligature_dict["id"] == "ligature-1"
        assert ligature_dict["connects"] == ["entity-1", "entity-2"]
        assert ligature_dict["logical_properties"]["identity_assertion"] is True
        assert len(ligature_dict["layout_constraints"]["cut_crossings"]) == 1


class TestFactoryFunctions:
    """Test factory functions for creating logical elements."""
    
    def test_create_logical_predicate(self):
        """Test predicate factory function."""
        predicate = create_logical_predicate(
            id="predicate-1",
            name="Person",
            container="sheet_of_assertion",
            arity=1,
            connected_entities=["entity-1"],
            moveable=True,
            semantic_role="assertion"
        )
        
        assert predicate.id == "predicate-1"
        assert predicate.name == "Person"
        assert predicate.logical_properties.arity == 1
        assert predicate.logical_properties.connected_entities == ["entity-1"]
        assert predicate.logical_properties.semantic_role == "assertion"
        assert predicate.layout_constraints.container == "sheet_of_assertion"
        assert predicate.layout_constraints.movement_constraints.moveable is True
        
        # Check default size constraints
        assert predicate.layout_constraints.size_constraints.min.width == 40.0
        assert predicate.layout_constraints.size_constraints.preferred.width == 60.0
        assert predicate.layout_constraints.size_constraints.max.width == 120.0
    
    def test_create_logical_context(self):
        """Test context factory function."""
        context = create_logical_context(
            id="cut-1",
            name="Negation Cut",
            container="sheet_of_assertion",
            context_type="cut",
            is_root=False,
            nesting_level=1
        )
        
        assert context.id == "cut-1"
        assert context.name == "Negation Cut"
        assert context.logical_properties.context_type == "cut"
        assert context.logical_properties.is_root is False
        assert context.logical_properties.nesting_level == 1
        assert context.layout_constraints.container == "sheet_of_assertion"
        assert context.layout_constraints.shape == "oval"
        
        # Check auto-sizing
        assert context.logical_properties.auto_size is True
        assert context.layout_constraints.size_constraints.auto_size is True
        assert context.layout_constraints.size_constraints.size_calculation == "content_plus_padding"
    
    def test_create_logical_entity(self):
        """Test entity factory function."""
        entity = create_logical_entity(
            id="entity-1",
            name="Socrates",
            connected_predicates=["predicate-1", "predicate-2"],
            entity_type="constant",
            ligature_group="socrates_identity"
        )
        
        assert entity.id == "entity-1"
        assert entity.name == "Socrates"
        assert entity.logical_properties.entity_type == "constant"
        assert entity.logical_properties.connected_predicates == ["predicate-1", "predicate-2"]
        assert entity.logical_properties.ligature_group == "socrates_identity"
        assert entity.layout_constraints.positioning_type == PositioningType.CONNECTION_DRIVEN
        assert entity.layout_constraints.shape == "line"
        
        # Check connection points
        assert len(entity.connection_points) == 2
        assert entity.connection_points[0].connects_to == "predicate-1"
        assert entity.connection_points[1].connects_to == "predicate-2"
        
        # Check path constraints
        assert entity.path_constraints.path_type == "flexible"
        assert entity.path_constraints.avoid_overlaps is True
        assert entity.path_constraints.prefer_straight_lines is True


class TestSerialization:
    """Test JSON serialization of logical types."""
    
    def test_predicate_json_serialization(self):
        """Test that predicates can be serialized to valid JSON."""
        predicate = create_logical_predicate(
            id="predicate-1",
            name="Person",
            container="sheet_of_assertion",
            arity=1
        )
        
        predicate_dict = predicate.to_dict()
        json_str = json.dumps(predicate_dict, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "predicate-1"
        assert parsed["name"] == "Person"
        assert parsed["element_type"] == "predicate"
    
    def test_entity_json_serialization(self):
        """Test that entities can be serialized to valid JSON."""
        entity = create_logical_entity(
            id="entity-1",
            name="Socrates",
            connected_predicates=["predicate-1"]
        )
        
        entity_dict = entity.to_dict()
        json_str = json.dumps(entity_dict, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "entity-1"
        assert parsed["name"] == "Socrates"
        assert parsed["element_type"] == "entity"
    
    def test_context_json_serialization(self):
        """Test that contexts can be serialized to valid JSON."""
        context = create_logical_context(
            id="cut-1",
            name="Negation Cut",
            container="sheet_of_assertion"
        )
        
        context_dict = context.to_dict()
        json_str = json.dumps(context_dict, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "cut-1"
        assert parsed["name"] == "Negation Cut"
        assert parsed["element_type"] == "context"
    
    def test_ligature_json_serialization(self):
        """Test that ligatures can be serialized to valid JSON."""
        ligature = LogicalLigature(
            id="ligature-1",
            connects=["entity-1", "entity-2"],
            logical_properties={"identity_assertion": True}
        )
        
        ligature_dict = ligature.to_dict()
        json_str = json.dumps(ligature_dict, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["id"] == "ligature-1"
        assert parsed["connects"] == ["entity-1", "entity-2"]


class TestValidation:
    """Test validation of logical types."""
    
    def test_predicate_arity_validation(self):
        """Test that predicate arity matches connected entities."""
        predicate = create_logical_predicate(
            id="predicate-1",
            name="Teacher",
            container="sheet_of_assertion",
            arity=2,
            connected_entities=["entity-1", "entity-2"]
        )
        
        # Arity should match number of connected entities
        assert predicate.logical_properties.arity == len(predicate.logical_properties.connected_entities)
    
    def test_entity_connection_consistency(self):
        """Test that entity connections are consistent."""
        entity = create_logical_entity(
            id="entity-1",
            name="Socrates",
            connected_predicates=["predicate-1", "predicate-2"]
        )
        
        # Number of connection points should match connected predicates
        assert len(entity.connection_points) == len(entity.logical_properties.connected_predicates)
        
        # Connection point targets should match connected predicates
        connection_targets = [cp.connects_to for cp in entity.connection_points]
        assert set(connection_targets) == set(entity.logical_properties.connected_predicates)
    
    def test_context_nesting_level_consistency(self):
        """Test that context nesting levels are consistent."""
        root_context = create_logical_context(
            id="sheet_of_assertion",
            name="Sheet of Assertion",
            container="viewport",
            context_type="sheet_of_assertion",
            is_root=True,
            nesting_level=0
        )
        
        nested_context = create_logical_context(
            id="cut-1",
            name="Negation Cut",
            container="sheet_of_assertion",
            context_type="cut",
            is_root=False,
            nesting_level=1
        )
        
        # Root context should have nesting level 0
        assert root_context.logical_properties.nesting_level == 0
        assert root_context.logical_properties.is_root is True
        
        # Nested context should have higher nesting level
        assert nested_context.logical_properties.nesting_level > root_context.logical_properties.nesting_level
        assert nested_context.logical_properties.is_root is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

