"""
EGRF v3.0 Logical Types

Core data structures for logical containment architecture.
Defines containment relationships, layout constraints, and logical elements
without specifying absolute coordinates.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json


# ============================================================================
# Basic Geometric Types (Logical, not pixel-specific)
# ============================================================================

@dataclass
class LogicalPoint:
    """A point in logical space (relative or constraint-based)."""
    x: float
    y: float
    coordinate_type: str = "relative"  # "relative", "constraint", "flexible"


@dataclass
class LogicalSize:
    """Size constraints for logical elements."""
    width: float
    height: float
    size_type: str = "preferred"  # "min", "preferred", "max"


@dataclass
class LogicalBounds:
    """Bounds definition for logical containers."""
    x: float
    y: float
    width: float
    height: float
    bounds_type: str = "auto"  # "auto", "fixed", "constraint"


@dataclass
class SpacingConstraint:
    """Spacing requirements between elements."""
    min: float
    preferred: float
    max: Optional[float] = None


# ============================================================================
# Layout Constraint Types
# ============================================================================

class PositioningType(Enum):
    """Types of positioning for logical elements."""
    CONSTRAINT_BASED = "constraint_based"
    CONNECTION_DRIVEN = "connection_driven"
    FLEXIBLE = "flexible"
    FIXED_RELATIVE = "fixed_relative"


class ContainerType(Enum):
    """Types of logical containers."""
    SHEET_OF_ASSERTION = "sheet_of_assertion"
    CUT = "cut"
    NESTED_CONTEXT = "nested_context"
    VIEWPORT = "viewport"


@dataclass
class SizeConstraints:
    """Size constraints for an element."""
    min: Optional[LogicalSize] = None
    preferred: Optional[LogicalSize] = None
    max: Optional[LogicalSize] = None
    auto_size: bool = False
    size_calculation: str = "content_driven"  # "content_driven", "fixed", "adaptive"


@dataclass
class SpacingConstraints:
    """Spacing constraints for an element."""
    to_siblings: Optional[SpacingConstraint] = None
    to_container_edge: Optional[SpacingConstraint] = None
    to_specific_elements: Dict[str, SpacingConstraint] = field(default_factory=dict)


@dataclass
class MovementConstraints:
    """Constraints on how an element can be moved."""
    moveable: bool = True
    movement_bounds: str = "container_interior"  # "container_interior", "global", "none"
    forbidden_areas: List[str] = field(default_factory=list)  # Element IDs to avoid
    snap_to_grid: bool = False
    grid_size: Optional[float] = None


@dataclass
class LayoutConstraints:
    """Complete layout constraints for a logical element."""
    container: str  # ID of containing element
    positioning_type: PositioningType = PositioningType.CONSTRAINT_BASED
    size_constraints: Optional[SizeConstraints] = None
    spacing_constraints: Optional[SpacingConstraints] = None
    movement_constraints: Optional[MovementConstraints] = None
    collision_avoidance: bool = True
    shape: str = "rectangle"  # "rectangle", "oval", "line"


# ============================================================================
# Containment Relationship Types
# ============================================================================

@dataclass
class ContainmentRelationship:
    """Defines what elements are contained within a container."""
    container: str  # ID of container element
    contained_elements: List[str]  # IDs of contained elements
    constraint_type: str = "strict_containment"  # "strict_containment", "loose_containment"
    nesting_level: int = 0
    semantic_role: Optional[str] = None  # "assertion", "negation", "implication"


# ============================================================================
# Logical Element Base Classes
# ============================================================================

@dataclass
class LogicalProperties:
    """Base class for logical properties of elements."""
    semantic_role: Optional[str] = None
    nesting_level: int = 0
    logical_type: Optional[str] = None


@dataclass
class LogicalElement:
    """Base class for all logical elements in EGRF v3.0."""
    id: str
    name: str
    element_type: str  # "predicate", "entity", "context"
    logical_properties: LogicalProperties
    layout_constraints: LayoutConstraints
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "element_type": self.element_type,
            "logical_properties": self._properties_to_dict(),
            "layout_constraints": self._constraints_to_dict()
        }
    
    def _properties_to_dict(self) -> Dict[str, Any]:
        """Convert logical properties to dictionary."""
        return {
            "semantic_role": self.logical_properties.semantic_role,
            "nesting_level": self.logical_properties.nesting_level,
            "logical_type": self.logical_properties.logical_type
        }
    
    def _constraints_to_dict(self) -> Dict[str, Any]:
        """Convert layout constraints to dictionary."""
        result = {
            "container": self.layout_constraints.container,
            "positioning_type": self.layout_constraints.positioning_type.value,
            "collision_avoidance": self.layout_constraints.collision_avoidance,
            "shape": self.layout_constraints.shape
        }
        
        if self.layout_constraints.size_constraints:
            result["size_constraints"] = self._size_constraints_to_dict()
        
        if self.layout_constraints.spacing_constraints:
            result["spacing_constraints"] = self._spacing_constraints_to_dict()
            
        if self.layout_constraints.movement_constraints:
            result["movement_constraints"] = self._movement_constraints_to_dict()
        
        return result
    
    def _size_constraints_to_dict(self) -> Dict[str, Any]:
        """Convert size constraints to dictionary."""
        sc = self.layout_constraints.size_constraints
        result = {
            "auto_size": sc.auto_size,
            "size_calculation": sc.size_calculation
        }
        
        if sc.min:
            result["min"] = {"width": sc.min.width, "height": sc.min.height}
        if sc.preferred:
            result["preferred"] = {"width": sc.preferred.width, "height": sc.preferred.height}
        if sc.max:
            result["max"] = {"width": sc.max.width, "height": sc.max.height}
            
        return result
    
    def _spacing_constraints_to_dict(self) -> Dict[str, Any]:
        """Convert spacing constraints to dictionary."""
        sc = self.layout_constraints.spacing_constraints
        result = {}
        
        if sc.to_siblings:
            result["to_siblings"] = {
                "min": sc.to_siblings.min,
                "preferred": sc.to_siblings.preferred,
                "max": sc.to_siblings.max
            }
        
        if sc.to_container_edge:
            result["to_container_edge"] = {
                "min": sc.to_container_edge.min,
                "preferred": sc.to_container_edge.preferred,
                "max": sc.to_container_edge.max
            }
            
        if sc.to_specific_elements:
            result["to_specific_elements"] = {
                elem_id: {
                    "min": constraint.min,
                    "preferred": constraint.preferred,
                    "max": constraint.max
                }
                for elem_id, constraint in sc.to_specific_elements.items()
            }
        
        return result
    
    def _movement_constraints_to_dict(self) -> Dict[str, Any]:
        """Convert movement constraints to dictionary."""
        mc = self.layout_constraints.movement_constraints
        return {
            "moveable": mc.moveable,
            "movement_bounds": mc.movement_bounds,
            "forbidden_areas": mc.forbidden_areas,
            "snap_to_grid": mc.snap_to_grid,
            "grid_size": mc.grid_size
        }


# ============================================================================
# Specific Logical Element Types
# ============================================================================

@dataclass
class PredicateProperties(LogicalProperties):
    """Logical properties specific to predicates."""
    arity: int = 1
    connected_entities: List[str] = field(default_factory=list)
    predicate_type: str = "relation"  # "relation", "property", "function"


@dataclass
class LogicalPredicate(LogicalElement):
    """Logical predicate element."""
    logical_properties: PredicateProperties
    
    def __post_init__(self):
        self.element_type = "predicate"
    
    def _properties_to_dict(self) -> Dict[str, Any]:
        """Convert predicate properties to dictionary."""
        base = super()._properties_to_dict()
        base.update({
            "arity": self.logical_properties.arity,
            "connected_entities": self.logical_properties.connected_entities,
            "predicate_type": self.logical_properties.predicate_type
        })
        return base


@dataclass
class EntityProperties(LogicalProperties):
    """Logical properties specific to entities."""
    entity_type: str = "constant"  # "constant", "variable", "function"
    connected_predicates: List[str] = field(default_factory=list)
    ligature_group: Optional[str] = None  # For identity lines


@dataclass
class PathConstraints:
    """Constraints for entity path routing."""
    path_type: str = "flexible"  # "flexible", "straight", "curved"
    avoid_overlaps: bool = True
    prefer_straight_lines: bool = True
    crossing_minimization: bool = True
    min_length: float = 10.0


@dataclass
class ConnectionPoint:
    """A connection point for an entity."""
    connects_to: str  # ID of element to connect to
    attachment: str = "flexible"  # "flexible", "fixed", "magnetic"
    priority: str = "normal"  # "low", "normal", "high"
    connection_type: str = "direct"  # "direct", "via_ligature"


@dataclass
class LogicalEntity(LogicalElement):
    """Logical entity element (line of identity)."""
    logical_properties: EntityProperties
    path_constraints: Optional[PathConstraints] = None
    connection_points: List[ConnectionPoint] = field(default_factory=list)
    
    def __post_init__(self):
        self.element_type = "entity"
        if self.path_constraints is None:
            self.path_constraints = PathConstraints()
    
    def _properties_to_dict(self) -> Dict[str, Any]:
        """Convert entity properties to dictionary."""
        base = super()._properties_to_dict()
        base.update({
            "entity_type": self.logical_properties.entity_type,
            "connected_predicates": self.logical_properties.connected_predicates,
            "ligature_group": self.logical_properties.ligature_group
        })
        return base
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary including path constraints."""
        result = super().to_dict()
        
        if self.path_constraints:
            result["path_constraints"] = {
                "path_type": self.path_constraints.path_type,
                "avoid_overlaps": self.path_constraints.avoid_overlaps,
                "prefer_straight_lines": self.path_constraints.prefer_straight_lines,
                "crossing_minimization": self.path_constraints.crossing_minimization,
                "min_length": self.path_constraints.min_length
            }
        
        if self.connection_points:
            result["connection_points"] = [
                {
                    "connects_to": cp.connects_to,
                    "attachment": cp.attachment,
                    "priority": cp.priority,
                    "connection_type": cp.connection_type
                }
                for cp in self.connection_points
            ]
        
        return result


@dataclass
class ContextProperties(LogicalProperties):
    """Logical properties specific to contexts."""
    context_type: str = "cut"  # "cut", "sheet_of_assertion"
    is_root: bool = False
    auto_size: bool = True
    padding: Optional[SpacingConstraint] = None


@dataclass
class LogicalContext(LogicalElement):
    """Logical context element (cuts, sheet of assertion)."""
    logical_properties: ContextProperties
    
    def __post_init__(self):
        self.element_type = "context"
        if self.logical_properties.padding is None:
            self.logical_properties.padding = SpacingConstraint(min=15.0, preferred=25.0, max=40.0)
    
    def _properties_to_dict(self) -> Dict[str, Any]:
        """Convert context properties to dictionary."""
        base = super()._properties_to_dict()
        base.update({
            "context_type": self.logical_properties.context_type,
            "is_root": self.logical_properties.is_root,
            "auto_size": self.logical_properties.auto_size
        })
        
        if self.logical_properties.padding:
            base["padding"] = {
                "min": self.logical_properties.padding.min,
                "preferred": self.logical_properties.padding.preferred,
                "max": self.logical_properties.padding.max
            }
        
        return base


# ============================================================================
# Ligature Types (Cross-Context Connections)
# ============================================================================

@dataclass
class CutCrossing:
    """Defines how a ligature crosses a cut boundary."""
    cut_id: str
    crossing_point: str = "gui_determined"  # "gui_determined", "fixed", "flexible"
    crossing_style: str = "perpendicular_preferred"  # "perpendicular_preferred", "tangent", "any"
    crossing_flexible: bool = True


@dataclass
class LigatureConstraints:
    """Constraints for ligatures that cross context boundaries."""
    path_type: str = "flexible"  # "flexible", "straight", "curved"
    cut_crossings: List[CutCrossing] = field(default_factory=list)
    avoid_overlaps: bool = True
    routing_algorithm: str = "shortest_path_with_constraints"


@dataclass
class LogicalLigature:
    """A ligature connecting entities across context boundaries."""
    id: str
    connects: List[str]  # IDs of entities to connect
    logical_properties: Dict[str, Any] = field(default_factory=dict)
    layout_constraints: Optional[LigatureConstraints] = None
    
    def __post_init__(self):
        if self.layout_constraints is None:
            self.layout_constraints = LigatureConstraints()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ligature to dictionary."""
        result = {
            "id": self.id,
            "connects": self.connects,
            "logical_properties": self.logical_properties
        }
        
        if self.layout_constraints:
            result["layout_constraints"] = {
                "path_type": self.layout_constraints.path_type,
                "avoid_overlaps": self.layout_constraints.avoid_overlaps,
                "routing_algorithm": self.layout_constraints.routing_algorithm
            }
            
            if self.layout_constraints.cut_crossings:
                result["layout_constraints"]["cut_crossings"] = [
                    {
                        "cut_id": cc.cut_id,
                        "crossing_point": cc.crossing_point,
                        "crossing_style": cc.crossing_style,
                        "crossing_flexible": cc.crossing_flexible
                    }
                    for cc in self.layout_constraints.cut_crossings
                ]
        
        return result


# ============================================================================
# Factory Functions
# ============================================================================

def create_logical_predicate(
    id: str,
    name: str,
    container: str,
    arity: int = 1,
    connected_entities: Optional[List[str]] = None,
    moveable: bool = True,
    semantic_role: Optional[str] = None
) -> LogicalPredicate:
    """Factory function to create a logical predicate with sensible defaults."""
    
    properties = PredicateProperties(
        arity=arity,
        connected_entities=connected_entities or [],
        semantic_role=semantic_role
    )
    
    size_constraints = SizeConstraints(
        min=LogicalSize(40.0, 20.0),
        preferred=LogicalSize(60.0, 30.0),
        max=LogicalSize(120.0, 60.0)
    )
    
    spacing_constraints = SpacingConstraints(
        to_siblings=SpacingConstraint(min=10.0, preferred=20.0),
        to_container_edge=SpacingConstraint(min=5.0, preferred=15.0)
    )
    
    movement_constraints = MovementConstraints(
        moveable=moveable,
        movement_bounds="container_interior"
    )
    
    layout_constraints = LayoutConstraints(
        container=container,
        positioning_type=PositioningType.CONSTRAINT_BASED,
        size_constraints=size_constraints,
        spacing_constraints=spacing_constraints,
        movement_constraints=movement_constraints,
        shape="rectangle"
    )
    
    return LogicalPredicate(
        id=id,
        name=name,
        element_type="predicate",
        logical_properties=properties,
        layout_constraints=layout_constraints
    )


def create_logical_context(
    id: str,
    name: str,
    container: str,
    context_type: str = "cut",
    is_root: bool = False,
    nesting_level: int = 1
) -> LogicalContext:
    """Factory function to create a logical context with sensible defaults."""
    
    properties = ContextProperties(
        context_type=context_type,
        is_root=is_root,
        auto_size=True,
        nesting_level=nesting_level,
        padding=SpacingConstraint(min=15.0, preferred=25.0, max=40.0)
    )
    
    spacing_constraints = SpacingConstraints(
        to_siblings=SpacingConstraint(min=20.0, preferred=40.0),
        to_container_edge=SpacingConstraint(min=10.0, preferred=20.0)
    )
    
    movement_constraints = MovementConstraints(
        moveable=not is_root,
        movement_bounds="container_interior" if not is_root else "none"
    )
    
    layout_constraints = LayoutConstraints(
        container=container,
        positioning_type=PositioningType.CONSTRAINT_BASED,
        size_constraints=SizeConstraints(auto_size=True, size_calculation="content_plus_padding"),
        spacing_constraints=spacing_constraints,
        movement_constraints=movement_constraints,
        shape="oval" if context_type == "cut" else "rectangle"
    )
    
    return LogicalContext(
        id=id,
        name=name,
        element_type="context",
        logical_properties=properties,
        layout_constraints=layout_constraints
    )


def create_logical_entity(
    id: str,
    name: str,
    connected_predicates: List[str],
    entity_type: str = "constant",
    ligature_group: Optional[str] = None
) -> LogicalEntity:
    """Factory function to create a logical entity with sensible defaults."""
    
    properties = EntityProperties(
        entity_type=entity_type,
        connected_predicates=connected_predicates,
        ligature_group=ligature_group
    )
    
    path_constraints = PathConstraints(
        path_type="flexible",
        avoid_overlaps=True,
        prefer_straight_lines=True,
        crossing_minimization=True,
        min_length=10.0
    )
    
    # Create connection points for each connected predicate
    connection_points = [
        ConnectionPoint(
            connects_to=pred_id,
            attachment="flexible",
            priority="high"
        )
        for pred_id in connected_predicates
    ]
    
    # Layout constraints for entities are connection-driven
    layout_constraints = LayoutConstraints(
        container="auto",  # Will be determined by connections
        positioning_type=PositioningType.CONNECTION_DRIVEN,
        shape="line"
    )
    
    return LogicalEntity(
        id=id,
        name=name,
        element_type="entity",
        logical_properties=properties,
        layout_constraints=layout_constraints,
        path_constraints=path_constraints,
        connection_points=connection_points
    )

