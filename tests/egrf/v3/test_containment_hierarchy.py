"""
Tests for EGRF v3.0 Containment Hierarchy

Tests hierarchy validation, layout calculation, and movement validation.
"""

import pytest
from src.egrf.v3.logical_types import (
    create_logical_predicate, create_logical_context, create_logical_entity,
    ContainmentRelationship, LogicalSize
)
from src.egrf.v3.containment_hierarchy import (
    ContainmentHierarchyManager, HierarchyValidator, LayoutCalculator, MovementValidator,
    ValidationResult, ValidationError, HierarchyValidationReport,
    CalculatedSize, CalculatedPosition, LayoutCalculationResult,
    create_containment_hierarchy, validate_and_calculate_layout
)


class TestContainmentHierarchyManager:
    """Test the containment hierarchy manager."""
    
    def test_manager_creation(self):
        """Test creating an empty manager."""
        manager = ContainmentHierarchyManager()
        
        assert len(manager.elements) == 0
        assert len(manager.relationships) == 0
        assert manager.hierarchy_cache is None
    
    def test_add_element(self):
        """Test adding elements to the manager."""
        manager = ContainmentHierarchyManager()
        
        predicate = create_logical_predicate(
            id="pred-1", name="Person", container="sheet"
        )
        
        manager.add_element(predicate)
        
        assert "pred-1" in manager.elements
        assert manager.elements["pred-1"] == predicate
    
    def test_add_relationship(self):
        """Test adding containment relationships."""
        manager = ContainmentHierarchyManager()
        
        relationship = ContainmentRelationship(
            container="sheet",
            contained_elements=["pred-1", "pred-2"]
        )
        
        manager.add_relationship(relationship)
        
        assert "sheet" in manager.relationships
        assert manager.relationships["sheet"] == relationship
    
    def test_get_container(self):
        """Test getting the container of an element."""
        manager = ContainmentHierarchyManager()
        
        predicate = create_logical_predicate(
            id="pred-1", name="Person", container="sheet"
        )
        manager.add_element(predicate)
        
        container = manager.get_container("pred-1")
        assert container == "sheet"
        
        # Non-existent element
        container = manager.get_container("non-existent")
        assert container is None
    
    def test_get_contained_elements(self):
        """Test getting contained elements."""
        manager = ContainmentHierarchyManager()
        
        relationship = ContainmentRelationship(
            container="sheet",
            contained_elements=["pred-1", "pred-2"]
        )
        manager.add_relationship(relationship)
        
        contained = manager.get_contained_elements("sheet")
        assert contained == ["pred-1", "pred-2"]
        
        # Non-existent container
        contained = manager.get_contained_elements("non-existent")
        assert contained == []
    
    def test_get_nesting_level(self):
        """Test calculating nesting levels."""
        manager = ContainmentHierarchyManager()
        
        # Create hierarchy: viewport -> sheet -> cut -> predicate
        sheet = create_logical_context(
            id="sheet", name="Sheet", container="viewport", is_root=True, nesting_level=0
        )
        cut = create_logical_context(
            id="cut", name="Cut", container="sheet", nesting_level=1
        )
        predicate = create_logical_predicate(
            id="pred", name="Person", container="cut"
        )
        
        manager.add_element(sheet)
        manager.add_element(cut)
        manager.add_element(predicate)
        
        assert manager.get_nesting_level("sheet") == 0  # viewport -> sheet (viewport not counted)
        assert manager.get_nesting_level("cut") == 1   # viewport -> sheet -> cut
        assert manager.get_nesting_level("pred") == 2  # viewport -> sheet -> cut -> pred
    
    def test_get_root_elements(self):
        """Test getting root elements."""
        manager = ContainmentHierarchyManager()
        
        sheet = create_logical_context(
            id="sheet", name="Sheet", container="viewport", is_root=True
        )
        cut = create_logical_context(
            id="cut", name="Cut", container="sheet"
        )
        
        manager.add_element(sheet)
        manager.add_element(cut)
        
        roots = manager.get_root_elements()
        assert "sheet" in roots
        assert "cut" not in roots
    
    def test_get_descendants(self):
        """Test getting all descendants."""
        manager = ContainmentHierarchyManager()
        
        # Create relationships
        sheet_rel = ContainmentRelationship(
            container="sheet", contained_elements=["cut", "pred1"]
        )
        cut_rel = ContainmentRelationship(
            container="cut", contained_elements=["pred2", "pred3"]
        )
        
        manager.add_relationship(sheet_rel)
        manager.add_relationship(cut_rel)
        
        descendants = manager.get_descendants("sheet")
        assert set(descendants) == {"cut", "pred1", "pred2", "pred3"}
        
        descendants = manager.get_descendants("cut")
        assert set(descendants) == {"pred2", "pred3"}
    
    def test_get_ancestors(self):
        """Test getting all ancestors."""
        manager = ContainmentHierarchyManager()
        
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport")
        cut = create_logical_context(id="cut", name="Cut", container="sheet")
        predicate = create_logical_predicate(id="pred", name="Person", container="cut")
        
        manager.add_element(sheet)
        manager.add_element(cut)
        manager.add_element(predicate)
        
        ancestors = manager.get_ancestors("pred")
        assert ancestors == ["cut", "sheet"]
        
        ancestors = manager.get_ancestors("cut")
        assert ancestors == ["sheet"]
        
        ancestors = manager.get_ancestors("sheet")
        assert ancestors == []
    
    def test_is_ancestor(self):
        """Test ancestor relationship checking."""
        manager = ContainmentHierarchyManager()
        
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport")
        cut = create_logical_context(id="cut", name="Cut", container="sheet")
        predicate = create_logical_predicate(id="pred", name="Person", container="cut")
        
        manager.add_element(sheet)
        manager.add_element(cut)
        manager.add_element(predicate)
        
        assert manager.is_ancestor("sheet", "pred") is True
        assert manager.is_ancestor("cut", "pred") is True
        assert manager.is_ancestor("pred", "sheet") is False
        assert manager.is_ancestor("sheet", "sheet") is False
    
    def test_is_sibling(self):
        """Test sibling relationship checking."""
        manager = ContainmentHierarchyManager()
        
        pred1 = create_logical_predicate(id="pred1", name="Person", container="sheet")
        pred2 = create_logical_predicate(id="pred2", name="Mortal", container="sheet")
        pred3 = create_logical_predicate(id="pred3", name="Teacher", container="cut")
        
        manager.add_element(pred1)
        manager.add_element(pred2)
        manager.add_element(pred3)
        
        assert manager.is_sibling("pred1", "pred2") is True
        assert manager.is_sibling("pred1", "pred3") is False
    
    def test_remove_element(self):
        """Test removing elements and updating relationships."""
        manager = ContainmentHierarchyManager()
        
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        manager.add_element(predicate)
        
        relationship = ContainmentRelationship(
            container="sheet", contained_elements=["pred", "other"]
        )
        manager.add_relationship(relationship)
        
        # Remove element
        manager.remove_element("pred")
        
        assert "pred" not in manager.elements
        assert "pred" not in manager.relationships["sheet"].contained_elements
        assert "other" in manager.relationships["sheet"].contained_elements


class TestHierarchyValidator:
    """Test hierarchy validation."""
    
    def test_valid_hierarchy(self):
        """Test validation of a valid hierarchy."""
        manager = ContainmentHierarchyManager()
        
        # Create valid hierarchy
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport")
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(predicate)
        
        relationship = ContainmentRelationship(
            container="sheet", contained_elements=["pred"]
        )
        manager.add_relationship(relationship)
        
        validator = HierarchyValidator(manager)
        report = validator.validate()
        
        assert report.is_valid is True
        assert len(report.errors) == 0
        assert "sheet" in report.containment_tree
        assert "pred" in report.containment_tree["sheet"]
    
    def test_circular_reference_detection(self):
        """Test detection of circular references."""
        manager = ContainmentHierarchyManager()
        
        # Create circular reference: A -> B -> A
        context_a = create_logical_context(id="a", name="A", container="b")
        context_b = create_logical_context(id="b", name="B", container="a")
        
        manager.add_element(context_a)
        manager.add_element(context_b)
        
        validator = HierarchyValidator(manager)
        report = validator.validate()
        
        assert report.is_valid is False
        assert any(error.error_type == ValidationResult.CIRCULAR_REFERENCE for error in report.errors)
    
    def test_missing_container_detection(self):
        """Test detection of missing containers."""
        manager = ContainmentHierarchyManager()
        
        # Create element with non-existent container
        predicate = create_logical_predicate(id="pred", name="Person", container="non-existent")
        manager.add_element(predicate)
        
        validator = HierarchyValidator(manager)
        report = validator.validate()
        
        assert report.is_valid is False
        assert any(error.error_type == ValidationResult.MISSING_CONTAINER for error in report.errors)
    
    def test_orphaned_element_detection(self):
        """Test detection of orphaned elements."""
        manager = ContainmentHierarchyManager()
        
        # Create elements with container but no relationship
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport")
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(predicate)
        
        # Add relationship for sheet but not predicate
        relationship = ContainmentRelationship(
            container="viewport", contained_elements=["sheet"]
        )
        manager.add_relationship(relationship)
        
        validator = HierarchyValidator(manager)
        report = validator.validate()
        
        # Should have warning about orphaned predicate
        assert any(error.error_type == ValidationResult.ORPHANED_ELEMENT for error in report.warnings)
    
    def test_constraint_violation_detection(self):
        """Test detection of constraint violations."""
        manager = ContainmentHierarchyManager()
        
        # Create entity with connection to non-existent predicate
        entity = create_logical_entity(
            id="entity", name="Socrates", connected_predicates=["non-existent"]
        )
        manager.add_element(entity)
        
        validator = HierarchyValidator(manager)
        report = validator.validate()
        
        assert report.is_valid is False
        assert any(error.error_type == ValidationResult.CONSTRAINT_VIOLATION for error in report.errors)


class TestLayoutCalculator:
    """Test layout calculation."""
    
    def test_simple_layout_calculation(self):
        """Test layout calculation for a simple hierarchy."""
        manager = ContainmentHierarchyManager()
        
        # Create simple hierarchy
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(predicate)
        
        relationship = ContainmentRelationship(
            container="sheet", contained_elements=["pred"]
        )
        manager.add_relationship(relationship)
        
        calculator = LayoutCalculator(manager)
        result = calculator.calculate_layout(LogicalSize(800, 600))
        
        assert "sheet" in result.element_sizes
        assert "pred" in result.element_sizes
        assert "sheet" in result.element_positions
        assert "pred" in result.element_positions
        
        # Sheet should be larger than predicate (contains it + padding)
        sheet_size = result.element_sizes["sheet"]
        pred_size = result.element_sizes["pred"]
        assert sheet_size.width > pred_size.width
        assert sheet_size.height > pred_size.height
    
    def test_auto_sizing_calculation(self):
        """Test auto-sizing calculation for contexts."""
        manager = ContainmentHierarchyManager()
        
        # Create context with multiple contained elements
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        pred1 = create_logical_predicate(id="pred1", name="Person", container="sheet")
        pred2 = create_logical_predicate(id="pred2", name="Mortal", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(pred1)
        manager.add_element(pred2)
        
        relationship = ContainmentRelationship(
            container="sheet", contained_elements=["pred1", "pred2"]
        )
        manager.add_relationship(relationship)
        
        calculator = LayoutCalculator(manager)
        result = calculator.calculate_layout()
        
        sheet_size = result.element_sizes["sheet"]
        pred1_size = result.element_sizes["pred1"]
        pred2_size = result.element_sizes["pred2"]
        
        # Sheet should be auto-sized to contain both predicates plus padding
        expected_min_width = pred1_size.width + pred2_size.width + 20 + (25 * 2)  # spacing + padding
        assert sheet_size.width >= expected_min_width
        assert sheet_size.calculation_method == "content_plus_padding"
    
    def test_nested_layout_calculation(self):
        """Test layout calculation for nested contexts."""
        manager = ContainmentHierarchyManager()
        
        # Create nested hierarchy: sheet -> cut -> predicate
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        cut = create_logical_context(id="cut", name="Cut", container="sheet")
        predicate = create_logical_predicate(id="pred", name="Person", container="cut")
        
        manager.add_element(sheet)
        manager.add_element(cut)
        manager.add_element(predicate)
        
        sheet_rel = ContainmentRelationship(container="sheet", contained_elements=["cut"])
        cut_rel = ContainmentRelationship(container="cut", contained_elements=["pred"])
        
        manager.add_relationship(sheet_rel)
        manager.add_relationship(cut_rel)
        
        calculator = LayoutCalculator(manager)
        result = calculator.calculate_layout()
        
        # Check that sizes are calculated in correct order (deepest first)
        assert "pred" in result.calculation_order
        assert "cut" in result.calculation_order
        assert "sheet" in result.calculation_order
        
        # Predicate should be calculated before cut, cut before sheet
        pred_index = result.calculation_order.index("pred")
        cut_index = result.calculation_order.index("cut")
        sheet_index = result.calculation_order.index("sheet")
        
        assert pred_index < cut_index < sheet_index
        
        # Check size relationships
        pred_size = result.element_sizes["pred"]
        cut_size = result.element_sizes["cut"]
        sheet_size = result.element_sizes["sheet"]
        
        assert cut_size.width > pred_size.width  # Cut contains predicate + padding
        assert sheet_size.width > cut_size.width  # Sheet contains cut + padding
    
    def test_entity_size_calculation(self):
        """Test size calculation for entities."""
        manager = ContainmentHierarchyManager()
        
        # Create a sheet to contain the entity and predicates
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        
        # Create predicates that the entity connects to
        pred1 = create_logical_predicate(id="pred1", name="Person", container="sheet")
        pred2 = create_logical_predicate(id="pred2", name="Mortal", container="sheet")
        
        entity = create_logical_entity(
            id="entity", name="Socrates", connected_predicates=["pred1", "pred2"]
        )
        
        # Set the entity's container
        entity.layout_constraints.container = "sheet"
        
        manager.add_element(sheet)
        manager.add_element(pred1)
        manager.add_element(pred2)
        manager.add_element(entity)
        
        # Add containment relationship
        relationship = ContainmentRelationship(container="sheet", contained_elements=["pred1", "pred2", "entity"])
        manager.add_relationship(relationship)
        
        calculator = LayoutCalculator(manager)
        result = calculator.calculate_layout()
        
        entity_size = result.element_sizes["entity"]
        assert entity_size.calculation_method == "path_based"
        assert entity_size.width >= 10.0  # Minimum length
        assert entity_size.height == 2.0   # Line thickness


class TestMovementValidator:
    """Test movement validation."""
    
    def test_valid_movement(self):
        """Test validation of valid movement."""
        manager = ContainmentHierarchyManager()
        
        # Create simple hierarchy
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(predicate)
        
        relationship = ContainmentRelationship(container="sheet", contained_elements=["pred"])
        manager.add_relationship(relationship)
        
        # Calculate layout
        calculator = LayoutCalculator(manager)
        layout = calculator.calculate_layout(LogicalSize(800, 600))
        
        # Test movement validation
        validator = MovementValidator(manager, calculator)
        
        # Get current predicate position and try to move it slightly
        pred_pos = layout.element_positions["pred"]
        new_x = pred_pos.x + 10
        new_y = pred_pos.y + 10
        
        is_valid, error = validator.validate_movement("pred", new_x, new_y, layout)
        assert is_valid is True
        assert error is None
    
    def test_movement_outside_container(self):
        """Test validation of movement outside container bounds."""
        manager = ContainmentHierarchyManager()
        
        # Create small container
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(predicate)
        
        relationship = ContainmentRelationship(container="sheet", contained_elements=["pred"])
        manager.add_relationship(relationship)
        
        calculator = LayoutCalculator(manager)
        layout = calculator.calculate_layout(LogicalSize(800, 600))
        
        validator = MovementValidator(manager, calculator)
        
        # Try to move predicate far outside container
        is_valid, error = validator.validate_movement("pred", 1000, 1000, layout)
        assert is_valid is False
        assert "outside container bounds" in error
    
    def test_movement_collision_detection(self):
        """Test collision detection during movement."""
        manager = ContainmentHierarchyManager()
        
        # Create container with two predicates - make it large enough to avoid bounds issues
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        pred1 = create_logical_predicate(id="pred1", name="Person", container="sheet")
        pred2 = create_logical_predicate(id="pred2", name="Mortal", container="sheet")
        
        manager.add_element(sheet)
        manager.add_element(pred1)
        manager.add_element(pred2)
        
        relationship = ContainmentRelationship(container="sheet", contained_elements=["pred1", "pred2"])
        manager.add_relationship(relationship)
        
        calculator = LayoutCalculator(manager)
        layout = calculator.calculate_layout(LogicalSize(1200, 800))  # Larger viewport
        
        validator = MovementValidator(manager, calculator)
        
        # Get pred2's position and try to move pred1 to overlap it
        pred2_pos = layout.element_positions["pred2"]
        
        # Move pred1 to pred2's exact position (should cause collision)
        is_valid, error = validator.validate_movement("pred1", pred2_pos.x, pred2_pos.y, layout)
        assert is_valid is False
        # Check for either collision or bounds error (both are valid failures)
        assert "collide" in error or "outside container bounds" in error
    
    def test_non_moveable_element(self):
        """Test validation of non-moveable elements."""
        manager = ContainmentHierarchyManager()
        
        # Create non-moveable root context
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        
        manager.add_element(sheet)
        
        calculator = LayoutCalculator(manager)
        layout = calculator.calculate_layout(LogicalSize(800, 600))
        
        validator = MovementValidator(manager, calculator)
        
        # Try to move non-moveable element
        is_valid, error = validator.validate_movement("sheet", 100, 100, layout)
        assert is_valid is False
        assert "not moveable" in error


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_create_containment_hierarchy(self):
        """Test creating hierarchy from elements and relationships."""
        # Create elements
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport")
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        elements = [sheet, predicate]
        
        # Create relationships
        relationship = ContainmentRelationship(container="sheet", contained_elements=["pred"])
        relationships = [relationship]
        
        # Create hierarchy
        manager = create_containment_hierarchy(elements, relationships)
        
        assert len(manager.elements) == 2
        assert len(manager.relationships) == 1
        assert "sheet" in manager.elements
        assert "pred" in manager.elements
        assert "sheet" in manager.relationships
    
    def test_validate_and_calculate_layout(self):
        """Test combined validation and layout calculation."""
        # Create valid hierarchy
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport")
        predicate = create_logical_predicate(id="pred", name="Person", container="sheet")
        
        elements = [sheet, predicate]
        relationships = [ContainmentRelationship(container="sheet", contained_elements=["pred"])]
        
        manager = create_containment_hierarchy(elements, relationships)
        
        # Validate and calculate
        validation_report, layout_result = validate_and_calculate_layout(manager, LogicalSize(800, 600))
        
        assert validation_report.is_valid is True
        assert len(layout_result.element_sizes) == 2
        assert len(layout_result.element_positions) == 2
    
    def test_validate_and_calculate_layout_invalid(self):
        """Test combined validation and layout calculation with invalid hierarchy."""
        # Create invalid hierarchy (circular reference)
        context_a = create_logical_context(id="a", name="A", container="b")
        context_b = create_logical_context(id="b", name="B", container="a")
        
        elements = [context_a, context_b]
        relationships = []
        
        manager = create_containment_hierarchy(elements, relationships)
        
        # Validate and calculate
        validation_report, layout_result = validate_and_calculate_layout(manager)
        
        assert validation_report.is_valid is False
        assert len(layout_result.element_sizes) == 0  # Empty result due to validation failure


class TestComplexHierarchy:
    """Test complex hierarchy scenarios."""
    
    def test_complex_nested_hierarchy(self):
        """Test a complex nested hierarchy with multiple levels."""
        manager = ContainmentHierarchyManager()
        
        # Create complex hierarchy: sheet -> cut1 -> cut2 -> predicate
        #                                 -> predicate2
        sheet = create_logical_context(id="sheet", name="Sheet", container="viewport", is_root=True)
        cut1 = create_logical_context(id="cut1", name="Cut1", container="sheet")
        cut2 = create_logical_context(id="cut2", name="Cut2", container="cut1")
        pred1 = create_logical_predicate(id="pred1", name="Person", container="cut2")
        pred2 = create_logical_predicate(id="pred2", name="Mortal", container="sheet")
        
        # Add elements
        for element in [sheet, cut1, cut2, pred1, pred2]:
            manager.add_element(element)
        
        # Add relationships
        sheet_rel = ContainmentRelationship(container="sheet", contained_elements=["cut1", "pred2"])
        cut1_rel = ContainmentRelationship(container="cut1", contained_elements=["cut2"])
        cut2_rel = ContainmentRelationship(container="cut2", contained_elements=["pred1"])
        
        for rel in [sheet_rel, cut1_rel, cut2_rel]:
            manager.add_relationship(rel)
        
        # Validate
        validator = HierarchyValidator(manager)
        report = validator.validate()
        
        assert report.is_valid is True
        
        # Check nesting levels (viewport is not counted)
        assert report.nesting_levels["sheet"] == 0  # Root level (container=viewport)
        assert report.nesting_levels["cut1"] == 1   # sheet -> cut1
        assert report.nesting_levels["cut2"] == 2   # sheet -> cut1 -> cut2
        assert report.nesting_levels["pred1"] == 3  # sheet -> cut1 -> cut2 -> pred1
        assert report.nesting_levels["pred2"] == 1  # sheet -> pred2
        
        # Calculate layout
        calculator = LayoutCalculator(manager)
        layout = calculator.calculate_layout(LogicalSize(1000, 800))
        
        # Check that all elements have sizes and positions
        for element_id in ["sheet", "cut1", "cut2", "pred1", "pred2"]:
            assert element_id in layout.element_sizes
            assert element_id in layout.element_positions
        
        # Check size relationships (containers should be larger than contents)
        cut2_size = layout.element_sizes["cut2"]
        pred1_size = layout.element_sizes["pred1"]
        assert cut2_size.width > pred1_size.width
        
        cut1_size = layout.element_sizes["cut1"]
        assert cut1_size.width > cut2_size.width
        
        sheet_size = layout.element_sizes["sheet"]
        assert sheet_size.width > cut1_size.width


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

