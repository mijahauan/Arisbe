"""
Tests for the EGRF v3.0 Layout Constraints System.

This module tests the platform-independent layout system for Existential Graph Rendering Format (EGRF).
"""

import unittest
import math
from egrf.v3.layout_constraints_new import (
    LayoutElement, Viewport, LayoutContext,
    LayoutConstraint, SizeConstraint, PositionConstraint,
    SpacingConstraint, AlignmentConstraint, ContainmentConstraint,
    CollisionDetector, ConstraintSolver, VisualRuleEnforcer,
    UserInteractionValidator, LayoutManager
)


class TestLayoutElement(unittest.TestCase):
    """Test the LayoutElement class."""
    
    def test_get_bounds(self):
        """Test getting element bounds."""
        element = LayoutElement(id="test", x=10, y=20, width=30, height=40)
        self.assertEqual(element.get_bounds(), (10, 20, 30, 40))
    
    def test_get_center(self):
        """Test getting element center."""
        element = LayoutElement(id="test", x=10, y=20, width=30, height=40)
        self.assertEqual(element.get_center(), (25, 40))
    
    def test_contains_point(self):
        """Test if element contains a point."""
        element = LayoutElement(id="test", x=10, y=20, width=30, height=40)
        self.assertTrue(element.contains_point(15, 25))
        self.assertTrue(element.contains_point(10, 20))
        self.assertTrue(element.contains_point(40, 60))
        self.assertFalse(element.contains_point(5, 25))
        self.assertFalse(element.contains_point(15, 15))
        self.assertFalse(element.contains_point(45, 25))
        self.assertFalse(element.contains_point(15, 65))
    
    def test_intersects(self):
        """Test if element intersects with another element."""
        element1 = LayoutElement(id="test1", x=10, y=20, width=30, height=40)
        element2 = LayoutElement(id="test2", x=15, y=25, width=10, height=10)
        element3 = LayoutElement(id="test3", x=50, y=20, width=30, height=40)
        
        self.assertTrue(element1.intersects(element2))
        self.assertTrue(element2.intersects(element1))
        self.assertFalse(element1.intersects(element3))
        self.assertFalse(element3.intersects(element1))
    
    def test_contains_element(self):
        """Test if element contains another element."""
        element1 = LayoutElement(id="test1", x=10, y=20, width=30, height=40)
        element2 = LayoutElement(id="test2", x=15, y=25, width=10, height=10)
        element3 = LayoutElement(id="test3", x=5, y=25, width=10, height=10)
        
        self.assertTrue(element1.contains_element(element2))
        self.assertFalse(element2.contains_element(element1))
        self.assertFalse(element1.contains_element(element3))
    
    def test_to_json(self):
        """Test converting element to JSON."""
        element = LayoutElement(id="test", x=10, y=20, width=30, height=40)
        json_data = element.to_json()
        
        self.assertEqual(json_data["id"], "test")
        self.assertEqual(json_data["x"], 10)
        self.assertEqual(json_data["y"], 20)
        self.assertEqual(json_data["width"], 30)
        self.assertEqual(json_data["height"], 40)
    
    def test_from_json(self):
        """Test creating element from JSON."""
        json_data = {
            "id": "test",
            "x": 10,
            "y": 20,
            "width": 30,
            "height": 40
        }
        
        element = LayoutElement.from_json(json_data)
        
        self.assertEqual(element.id, "test")
        self.assertEqual(element.x, 10)
        self.assertEqual(element.y, 20)
        self.assertEqual(element.width, 30)
        self.assertEqual(element.height, 40)


class TestViewport(unittest.TestCase):
    """Test the Viewport class."""
    
    def test_scale_to_device(self):
        """Test scaling logical value to device pixels."""
        viewport = Viewport(id="viewport", width=800, height=600, scale_factor=2.0)
        self.assertEqual(viewport.scale_to_device(100), 200)
    
    def test_scale_from_device(self):
        """Test scaling device pixels to logical units."""
        viewport = Viewport(id="viewport", width=800, height=600, scale_factor=2.0)
        self.assertEqual(viewport.scale_from_device(200), 100)
    
    def test_to_json(self):
        """Test converting viewport to JSON."""
        viewport = Viewport(id="viewport", width=800, height=600, scale_factor=2.0)
        json_data = viewport.to_json()
        
        self.assertEqual(json_data["id"], "viewport")
        self.assertEqual(json_data["width"], 800)
        self.assertEqual(json_data["height"], 600)
        self.assertEqual(json_data["scale_factor"], 2.0)
    
    def test_from_json(self):
        """Test creating viewport from JSON."""
        json_data = {
            "id": "viewport",
            "width": 800,
            "height": 600,
            "scale_factor": 2.0
        }
        
        viewport = Viewport.from_json(json_data)
        
        self.assertEqual(viewport.id, "viewport")
        self.assertEqual(viewport.width, 800)
        self.assertEqual(viewport.height, 600)
        self.assertEqual(viewport.scale_factor, 2.0)


class TestLayoutContext(unittest.TestCase):
    """Test the LayoutContext class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.element1 = LayoutElement(id="element1", x=10, y=20, width=30, height=40)
        self.element2 = LayoutElement(id="element2", x=50, y=60, width=70, height=80)
        
        self.elements = {
            "element1": self.element1,
            "element2": self.element2
        }
        
        self.containers = {
            "element2": "element1"  # element2 is contained in element1
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
    
    def test_get_element(self):
        """Test getting element by ID."""
        self.assertEqual(self.context.get_element("element1"), self.element1)
        self.assertEqual(self.context.get_element("element2"), self.element2)
        self.assertIsNone(self.context.get_element("nonexistent"))
    
    def test_get_container(self):
        """Test getting container of an element."""
        self.assertEqual(self.context.get_container("element2"), self.element1)
        self.assertIsNone(self.context.get_container("element1"))
        self.assertIsNone(self.context.get_container("nonexistent"))
    
    def test_get_contained_elements(self):
        """Test getting elements contained in a container."""
        contained = self.context.get_contained_elements("element1")
        self.assertEqual(len(contained), 1)
        self.assertEqual(contained[0], self.element2)
        
        self.assertEqual(self.context.get_contained_elements("element2"), [])
        self.assertEqual(self.context.get_contained_elements("nonexistent"), [])
    
    def test_to_json(self):
        """Test converting context to JSON."""
        json_data = self.context.to_json()
        
        self.assertIn("elements", json_data)
        self.assertIn("containers", json_data)
        self.assertIn("viewport", json_data)
        
        self.assertEqual(len(json_data["elements"]), 2)
        self.assertIn("element1", json_data["elements"])
        self.assertIn("element2", json_data["elements"])
        
        self.assertEqual(json_data["containers"], self.containers)
    
    def test_from_json(self):
        """Test creating context from JSON."""
        json_data = {
            "elements": {
                "element1": {
                    "id": "element1",
                    "x": 10,
                    "y": 20,
                    "width": 30,
                    "height": 40
                },
                "element2": {
                    "id": "element2",
                    "x": 50,
                    "y": 60,
                    "width": 70,
                    "height": 80
                }
            },
            "containers": {
                "element2": "element1"
            },
            "viewport": {
                "id": "viewport",
                "width": 800,
                "height": 600
            }
        }
        
        context = LayoutContext.from_json(json_data)
        
        self.assertEqual(len(context.elements), 2)
        self.assertIn("element1", context.elements)
        self.assertIn("element2", context.elements)
        
        self.assertEqual(context.elements["element1"].x, 10)
        self.assertEqual(context.elements["element2"].x, 50)
        
        self.assertEqual(context.containers, {"element2": "element1"})


class TestSizeConstraint(unittest.TestCase):
    """Test the SizeConstraint class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.element = LayoutElement(id="element", x=10, y=20, width=30, height=40)
        
        self.elements = {
            "element": self.element
        }
        
        self.containers = {}
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
    
    def test_validate_min_size(self):
        """Test validating minimum size constraint."""
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            min_width=20,
            min_height=30
        )
        
        self.assertTrue(constraint.validate(self.context))
        
        constraint = SizeConstraint(
            constraint_id="size2",
            element_id="element",
            min_width=40,
            min_height=30
        )
        
        self.assertFalse(constraint.validate(self.context))
    
    def test_validate_max_size(self):
        """Test validating maximum size constraint."""
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            max_width=40,
            max_height=50
        )
        
        self.assertTrue(constraint.validate(self.context))
        
        constraint = SizeConstraint(
            constraint_id="size2",
            element_id="element",
            max_width=20,
            max_height=50
        )
        
        self.assertFalse(constraint.validate(self.context))
    
    def test_validate_aspect_ratio(self):
        """Test validating aspect ratio constraint."""
        # Element is 30x40, ratio is 0.75
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            aspect_ratio=0.75,
            maintain_aspect_ratio=True
        )
        
        self.assertTrue(constraint.validate(self.context))
        
        constraint = SizeConstraint(
            constraint_id="size2",
            element_id="element",
            aspect_ratio=1.0,
            maintain_aspect_ratio=True
        )
        
        self.assertFalse(constraint.validate(self.context))
    
    def test_apply_preferred_size(self):
        """Test applying preferred size constraint."""
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            preferred_width=50,
            preferred_height=60
        )
        
        constraint.apply(self.context)
        
        self.assertEqual(self.element.width, 50)
        self.assertEqual(self.element.height, 60)
    
    def test_apply_min_size(self):
        """Test applying minimum size constraint."""
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            min_width=40,
            min_height=50
        )
        
        constraint.apply(self.context)
        
        self.assertEqual(self.element.width, 40)
        self.assertEqual(self.element.height, 50)
    
    def test_apply_max_size(self):
        """Test applying maximum size constraint."""
        self.element.width = 100
        self.element.height = 120
        
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            max_width=80,
            max_height=90
        )
        
        constraint.apply(self.context)
        
        self.assertEqual(self.element.width, 80)
        self.assertEqual(self.element.height, 90)
    
    def test_apply_aspect_ratio(self):
        """Test applying aspect ratio constraint."""
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            aspect_ratio=1.0,
            maintain_aspect_ratio=True
        )
        
        constraint.apply(self.context)
        
        self.assertEqual(self.element.width, 30)
        self.assertEqual(self.element.height, 30)
    
    def test_to_json(self):
        """Test converting size constraint to JSON."""
        constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            min_width=20,
            min_height=30,
            max_width=40,
            max_height=50,
            preferred_width=35,
            preferred_height=45,
            aspect_ratio=0.75,
            maintain_aspect_ratio=True
        )
        
        json_data = constraint.to_json()
        
        self.assertEqual(json_data["constraint_id"], "size1")
        self.assertEqual(json_data["element_id"], "element")
        self.assertEqual(json_data["min_width"], 20)
        self.assertEqual(json_data["min_height"], 30)
        self.assertEqual(json_data["max_width"], 40)
        self.assertEqual(json_data["max_height"], 50)
        self.assertEqual(json_data["preferred_width"], 35)
        self.assertEqual(json_data["preferred_height"], 45)
        self.assertEqual(json_data["aspect_ratio"], 0.75)
        self.assertEqual(json_data["maintain_aspect_ratio"], True)
    
    def test_from_json(self):
        """Test creating size constraint from JSON."""
        json_data = {
            "constraint_id": "size1",
            "element_id": "element",
            "min_width": 20,
            "min_height": 30,
            "max_width": 40,
            "max_height": 50,
            "preferred_width": 35,
            "preferred_height": 45,
            "aspect_ratio": 0.75,
            "maintain_aspect_ratio": True,
            "type": "SizeConstraint"
        }
        
        constraint = SizeConstraint.from_json(json_data)
        
        self.assertEqual(constraint.constraint_id, "size1")
        self.assertEqual(constraint.element_id, "element")
        self.assertEqual(constraint.min_width, 20)
        self.assertEqual(constraint.min_height, 30)
        self.assertEqual(constraint.max_width, 40)
        self.assertEqual(constraint.max_height, 50)
        self.assertEqual(constraint.preferred_width, 35)
        self.assertEqual(constraint.preferred_height, 45)
        self.assertEqual(constraint.aspect_ratio, 0.75)
        self.assertEqual(constraint.maintain_aspect_ratio, True)


class TestPositionConstraint(unittest.TestCase):
    """Test the PositionConstraint class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.element1 = LayoutElement(id="element1", x=10, y=20, width=30, height=40)
        self.element2 = LayoutElement(id="element2", x=50, y=60, width=70, height=80)
        
        self.elements = {
            "element1": self.element1,
            "element2": self.element2
        }
        
        self.containers = {}
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
    
    def test_validate_center_position(self):
        """Test validating center position constraint."""
        # element1 center: (25, 40)
        # element2 center: (85, 100)
        # offset: (60, 60)
        constraint = PositionConstraint(
            constraint_id="pos1",
            element_id="element2",
            reference_id="element1",
            reference_point="center",
            element_point="center",
            offset_x=60,
            offset_y=60
        )
        
        self.assertTrue(constraint.validate(self.context))
        
        constraint = PositionConstraint(
            constraint_id="pos2",
            element_id="element2",
            reference_id="element1",
            reference_point="center",
            element_point="center",
            offset_x=0,
            offset_y=0
        )
        
        self.assertFalse(constraint.validate(self.context))
    
    def test_apply_center_position(self):
        """Test applying center position constraint."""
        constraint = PositionConstraint(
            constraint_id="pos1",
            element_id="element2",
            reference_id="element1",
            reference_point="center",
            element_point="center",
            offset_x=0,
            offset_y=0
        )
        
        constraint.apply(self.context)
        
        # element1 center: (25, 40)
        # element2 size: (70, 80)
        # element2 should be at: (-10, 0) to center at (25, 40)
        self.assertEqual(self.element2.x, -10)
        self.assertEqual(self.element2.y, 0)
    
    def test_apply_top_left_position(self):
        """Test applying top-left position constraint."""
        constraint = PositionConstraint(
            constraint_id="pos1",
            element_id="element2",
            reference_id="element1",
            reference_point="top-left",
            element_point="top-left",
            offset_x=0,
            offset_y=0
        )
        
        constraint.apply(self.context)
        
        # element1 top-left: (10, 20)
        self.assertEqual(self.element2.x, 10)
        self.assertEqual(self.element2.y, 20)
    
    def test_to_json(self):
        """Test converting position constraint to JSON."""
        constraint = PositionConstraint(
            constraint_id="pos1",
            element_id="element2",
            reference_id="element1",
            reference_point="center",
            element_point="center",
            offset_x=60,
            offset_y=60
        )
        
        json_data = constraint.to_json()
        
        self.assertEqual(json_data["constraint_id"], "pos1")
        self.assertEqual(json_data["element_id"], "element2")
        self.assertEqual(json_data["reference_id"], "element1")
        self.assertEqual(json_data["reference_point"], "center")
        self.assertEqual(json_data["element_point"], "center")
        self.assertEqual(json_data["offset_x"], 60)
        self.assertEqual(json_data["offset_y"], 60)
    
    def test_from_json(self):
        """Test creating position constraint from JSON."""
        json_data = {
            "constraint_id": "pos1",
            "element_id": "element2",
            "reference_id": "element1",
            "reference_point": "center",
            "element_point": "center",
            "offset_x": 60,
            "offset_y": 60,
            "type": "PositionConstraint"
        }
        
        constraint = PositionConstraint.from_json(json_data)
        
        self.assertEqual(constraint.constraint_id, "pos1")
        self.assertEqual(constraint.element_id, "element2")
        self.assertEqual(constraint.reference_id, "element1")
        self.assertEqual(constraint.reference_point, "center")
        self.assertEqual(constraint.element_point, "center")
        self.assertEqual(constraint.offset_x, 60)
        self.assertEqual(constraint.offset_y, 60)


class TestSpacingConstraint(unittest.TestCase):
    """Test the SpacingConstraint class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.container = LayoutElement(id="container", x=0, y=0, width=100, height=100)
        self.element = LayoutElement(id="element", x=10, y=10, width=30, height=30)
        
        self.elements = {
            "container": self.container,
            "element": self.element
        }
        
        self.containers = {
            "element": "container"
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
    
    def test_validate_container_spacing(self):
        """Test validating spacing to container edges."""
        # element is at (10, 10) with size (30, 30)
        # container is at (0, 0) with size (100, 100)
        # spacing to left edge: 10
        # spacing to top edge: 10
        # spacing to right edge: 60
        # spacing to bottom edge: 60
        
        constraint = SpacingConstraint(
            constraint_id="spacing1",
            element_id="element",
            reference_id="",  # Empty means container
            min_spacing=5
        )
        
        self.assertTrue(constraint.validate(self.context))
        
        constraint = SpacingConstraint(
            constraint_id="spacing2",
            element_id="element",
            reference_id="",
            min_spacing=15
        )
        
        self.assertFalse(constraint.validate(self.context))
    
    def test_apply_container_spacing(self):
        """Test applying spacing to container edges."""
        constraint = SpacingConstraint(
            constraint_id="spacing1",
            element_id="element",
            reference_id="",
            min_spacing=20
        )
        
        constraint.apply(self.context)
        
        # element should be moved to have 20px spacing from all edges
        self.assertEqual(self.element.x, 20)
        self.assertEqual(self.element.y, 20)
    
    def test_to_json(self):
        """Test converting spacing constraint to JSON."""
        constraint = SpacingConstraint(
            constraint_id="spacing1",
            element_id="element",
            reference_id="",
            min_spacing=10,
            max_spacing=20,
            preferred_spacing=15,
            edge="left"
        )
        
        json_data = constraint.to_json()
        
        self.assertEqual(json_data["constraint_id"], "spacing1")
        self.assertEqual(json_data["element_id"], "element")
        self.assertEqual(json_data["reference_id"], "")
        self.assertEqual(json_data["min_spacing"], 10)
        self.assertEqual(json_data["max_spacing"], 20)
        self.assertEqual(json_data["preferred_spacing"], 15)
        self.assertEqual(json_data["edge"], "left")
    
    def test_from_json(self):
        """Test creating spacing constraint from JSON."""
        json_data = {
            "constraint_id": "spacing1",
            "element_id": "element",
            "reference_id": "",
            "min_spacing": 10,
            "max_spacing": 20,
            "preferred_spacing": 15,
            "edge": "left",
            "type": "SpacingConstraint"
        }
        
        constraint = SpacingConstraint.from_json(json_data)
        
        self.assertEqual(constraint.constraint_id, "spacing1")
        self.assertEqual(constraint.element_id, "element")
        self.assertEqual(constraint.reference_id, "")
        self.assertEqual(constraint.min_spacing, 10)
        self.assertEqual(constraint.max_spacing, 20)
        self.assertEqual(constraint.preferred_spacing, 15)
        self.assertEqual(constraint.edge, "left")


class TestAlignmentConstraint(unittest.TestCase):
    """Test the AlignmentConstraint class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.element1 = LayoutElement(id="element1", x=10, y=20, width=30, height=40)
        self.element2 = LayoutElement(id="element2", x=50, y=60, width=70, height=80)
        
        self.elements = {
            "element1": self.element1,
            "element2": self.element2
        }
        
        self.containers = {}
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
    
    def test_validate_center_alignment(self):
        """Test validating center alignment constraint."""
        # element1 center: (25, 40)
        # element2 center: (85, 100)
        
        constraint = AlignmentConstraint(
            constraint_id="align1",
            element_id="element2",
            reference_id="element1",
            alignment="center",
            offset=0
        )
        
        self.assertFalse(constraint.validate(self.context))
        
        # Move element2 to align with element1
        # For centers to align: element2.x = 25 - 70/2 = -10, element2.y = 40 - 80/2 = 0
        self.element2.x = -10
        self.element2.y = 0
        
        self.assertTrue(constraint.validate(self.context))
    
    def test_apply_center_alignment(self):
        """Test applying center alignment constraint."""
        constraint = AlignmentConstraint(
            constraint_id="align1",
            element_id="element2",
            reference_id="element1",
            alignment="center",
            offset=0
        )
        
        constraint.apply(self.context)
        
        # element1 center: (25, 40)
        # element2 size: (70, 80)
        # element2 should be at: (-10, 0) to center at (25, 40)
        self.assertEqual(self.element2.x, -10)
        self.assertEqual(self.element2.y, 0)
    
    def test_apply_left_alignment(self):
        """Test applying left alignment constraint."""
        constraint = AlignmentConstraint(
            constraint_id="align1",
            element_id="element2",
            reference_id="element1",
            alignment="left",
            offset=0
        )
        
        constraint.apply(self.context)
        
        # element1 left: 10
        self.assertEqual(self.element2.x, 10)
    
    def test_to_json(self):
        """Test converting alignment constraint to JSON."""
        constraint = AlignmentConstraint(
            constraint_id="align1",
            element_id="element2",
            reference_id="element1",
            alignment="center",
            offset=10
        )
        
        json_data = constraint.to_json()
        
        self.assertEqual(json_data["constraint_id"], "align1")
        self.assertEqual(json_data["element_id"], "element2")
        self.assertEqual(json_data["reference_id"], "element1")
        self.assertEqual(json_data["alignment"], "center")
        self.assertEqual(json_data["offset"], 10)
    
    def test_from_json(self):
        """Test creating alignment constraint from JSON."""
        json_data = {
            "constraint_id": "align1",
            "element_id": "element2",
            "reference_id": "element1",
            "alignment": "center",
            "offset": 10,
            "type": "AlignmentConstraint"
        }
        
        constraint = AlignmentConstraint.from_json(json_data)
        
        self.assertEqual(constraint.constraint_id, "align1")
        self.assertEqual(constraint.element_id, "element2")
        self.assertEqual(constraint.reference_id, "element1")
        self.assertEqual(constraint.alignment, "center")
        self.assertEqual(constraint.offset, 10)


class TestContainmentConstraint(unittest.TestCase):
    """Test the ContainmentConstraint class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.container = LayoutElement(id="container", x=0, y=0, width=100, height=100)
        self.element = LayoutElement(id="element", x=10, y=10, width=30, height=30)
        
        self.elements = {
            "container": self.container,
            "element": self.element
        }
        
        self.containers = {
            "element": "container"
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
    
    def test_validate_containment(self):
        """Test validating containment constraint."""
        constraint = ContainmentConstraint(
            constraint_id="contain1",
            element_id="element",
            padding=5
        )
        
        self.assertTrue(constraint.validate(self.context))
        
        # Move element outside container
        self.element.x = -10
        self.element.y = -10
        
        self.assertFalse(constraint.validate(self.context))
    
    def test_apply_containment(self):
        """Test applying containment constraint."""
        # Move element outside container
        self.element.x = -10
        self.element.y = -10
        
        constraint = ContainmentConstraint(
            constraint_id="contain1",
            element_id="element",
            padding=5
        )
        
        constraint.apply(self.context)
        
        # element should be moved inside container with padding
        self.assertEqual(self.element.x, 5)
        self.assertEqual(self.element.y, 5)
    
    def test_to_json(self):
        """Test converting containment constraint to JSON."""
        constraint = ContainmentConstraint(
            constraint_id="contain1",
            element_id="element",
            padding=5
        )
        
        json_data = constraint.to_json()
        
        self.assertEqual(json_data["constraint_id"], "contain1")
        self.assertEqual(json_data["element_id"], "element")
        self.assertEqual(json_data["padding"], 5)
    
    def test_from_json(self):
        """Test creating containment constraint from JSON."""
        json_data = {
            "constraint_id": "contain1",
            "element_id": "element",
            "padding": 5,
            "type": "ContainmentConstraint"
        }
        
        constraint = ContainmentConstraint.from_json(json_data)
        
        self.assertEqual(constraint.constraint_id, "contain1")
        self.assertEqual(constraint.element_id, "element")
        self.assertEqual(constraint.padding, 5)


class TestCollisionDetector(unittest.TestCase):
    """Test the CollisionDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.element1 = LayoutElement(id="element1", x=10, y=20, width=30, height=40)
        self.element2 = LayoutElement(id="element2", x=50, y=60, width=70, height=80)
        self.element3 = LayoutElement(id="element3", x=15, y=25, width=10, height=10)
        
        self.elements = {
            "element1": self.element1,
            "element2": self.element2,
            "element3": self.element3
        }
        
        self.containers = {
            "element3": "element1"  # element3 is contained in element1
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
        
        self.detector = CollisionDetector()
    
    def test_detect_collisions(self):
        """Test detecting collisions between elements."""
        collisions = self.detector.detect_collisions(self.context)
        
        # element1 and element3 are in a container relationship, so no collision
        # element1 and element2 don't intersect
        # element2 and element3 don't intersect
        self.assertEqual(len(collisions), 0)
        
        # Move element2 to intersect with element1
        self.element2.x = 20
        self.element2.y = 30
        
        collisions = self.detector.detect_collisions(self.context)
        # Should detect 2 collisions: element1-element2 and element2-element3
        # (element1-element3 is skipped due to container relationship)
        self.assertEqual(len(collisions), 2)
        self.assertIn(("element1", "element2"), collisions)
    
    def test_resolve_collisions(self):
        """Test resolving collisions between elements."""
        # Move element2 to intersect with element1
        self.element2.x = 20
        self.element2.y = 30
        
        self.assertTrue(self.element1.intersects(self.element2))
        
        self.detector.resolve_collisions(self.context)
        
        self.assertFalse(self.element1.intersects(self.element2))


class TestConstraintSolver(unittest.TestCase):
    """Test the ConstraintSolver class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.element = LayoutElement(id="element", x=10, y=20, width=30, height=40)
        
        self.elements = {
            "element": self.element
        }
        
        self.containers = {}
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
        
        self.solver = ConstraintSolver()
    
    def test_solve_constraints(self):
        """Test solving constraints."""
        # Add a size constraint
        size_constraint = SizeConstraint(
            constraint_id="size1",
            element_id="element",
            preferred_width=50,
            preferred_height=60
        )
        
        self.context.constraints.append(size_constraint)
        
        self.solver.solve(self.context)
        
        self.assertEqual(self.element.width, 50)
        self.assertEqual(self.element.height, 60)


class TestVisualRuleEnforcer(unittest.TestCase):
    """Test the VisualRuleEnforcer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.container = LayoutElement(id="container", x=0, y=0, width=100, height=100)
        self.element = LayoutElement(id="element", x=10, y=10, width=30, height=30)
        
        self.elements = {
            "container": self.container,
            "element": self.element
        }
        
        self.containers = {
            "element": "container"
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
        
        self.enforcer = VisualRuleEnforcer()
    
    def test_enforce_nesting_rules(self):
        """Test enforcing nesting rules."""
        # Move element outside container
        self.element.x = -10
        self.element.y = -10
        
        self.assertFalse(self.container.contains_element(self.element))
        
        self.enforcer.enforce_rules(self.context)
        
        self.assertTrue(self.container.contains_element(self.element))


class TestUserInteractionValidator(unittest.TestCase):
    """Test the UserInteractionValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.container = LayoutElement(id="container", x=0, y=0, width=100, height=100)
        self.element = LayoutElement(id="element", x=10, y=10, width=30, height=30)
        
        self.elements = {
            "container": self.container,
            "element": self.element
        }
        
        self.containers = {
            "element": "container"
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
        
        self.validator = UserInteractionValidator()
    
    def test_validate_move(self):
        """Test validating move interaction."""
        # Valid move within container
        self.assertTrue(self.validator.validate_move(self.context, "element", 20, 20))
        
        # Invalid move outside container
        self.assertFalse(self.validator.validate_move(self.context, "element", -10, -10))
    
    def test_validate_resize(self):
        """Test validating resize interaction."""
        # Valid resize within container
        self.assertTrue(self.validator.validate_resize(self.context, "element", 20, 20))
        
        # Invalid resize (too large for container)
        self.assertFalse(self.validator.validate_resize(self.context, "element", 120, 120))


class TestLayoutManager(unittest.TestCase):
    """Test the LayoutManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.viewport = Viewport(id="viewport", width=800, height=600)
        self.container = LayoutElement(id="container", x=0, y=0, width=100, height=100)
        self.element1 = LayoutElement(id="element1", x=10, y=10, width=30, height=30)
        self.element2 = LayoutElement(id="element2", x=50, y=50, width=30, height=30)
        
        self.elements = {
            "container": self.container,
            "element1": self.element1,
            "element2": self.element2
        }
        
        self.containers = {
            "element1": "container",
            "element2": "container"
        }
        
        self.context = LayoutContext(
            elements=self.elements,
            containers=self.containers,
            viewport=self.viewport
        )
        
        self.manager = LayoutManager()
    
    def test_solve_layout(self):
        """Test solving layout."""
        # Add a containment constraint
        containment = ContainmentConstraint(
            constraint_id="contain1",
            element_id="element1",
            padding=5
        )
        
        self.context.constraints.append(containment)
        
        # Move element outside container
        self.element1.x = -10
        self.element1.y = -10
        
        self.assertFalse(self.container.contains_element(self.element1))
        
        self.manager.solve_layout(self.context)
        
        self.assertTrue(self.container.contains_element(self.element1))
    
    def test_auto_layout(self):
        """Test auto layout."""
        # Reset element positions
        self.element1.x = 0
        self.element1.y = 0
        self.element2.x = 0
        self.element2.y = 0
        
        self.manager.auto_layout(self.context)
        
        # Elements should be positioned in a grid (1 column, 2 rows)
        # They will have the same x position but different y positions
        self.assertEqual(self.element1.x, self.element2.x)  # Same column
        self.assertNotEqual(self.element1.y, self.element2.y)  # Different rows
    
    def test_validate_user_interaction(self):
        """Test validating user interaction."""
        # Valid move within container
        self.assertTrue(self.manager.validate_user_interaction(
            self.context, "move", "element1", new_x=20, new_y=20
        ))
        
        # Invalid move outside container
        self.assertFalse(self.manager.validate_user_interaction(
            self.context, "move", "element1", new_x=-10, new_y=-10
        ))


if __name__ == "__main__":
    unittest.main()

