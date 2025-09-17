"""
Interaction Layer for EGI Diagrams

Bridges the gap between visual rendering and logical manipulation,
providing the architecture for Dau-compliant interactive transformations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from PySide6.QtCore import QObject, Signal, QPointF, QRectF
from PySide6.QtGui import QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from formal_transformation_rules import (
    FormalTransformationRule, 
    TransformationContext, 
    TransformationResult,
    AreaPolarity
)
from chapter21_diagram_engine import SubgraphSelection, SubgraphValidator


class InteractionState(Enum):
    """Current state of user interaction."""
    IDLE = "idle"
    SELECTING = "selecting" 
    DRAGGING = "dragging"
    TRANSFORMING = "transforming"
    VALIDATING = "validating"


class SelectionMode(Enum):
    """Methods for selecting diagram elements."""
    SINGLE_CLICK = "single_click"
    MULTI_SELECT = "multi_select"
    SUBGRAPH_LINE = "subgraph_line"  # Dau's dotted rectangle
    AREA_SELECT = "area_select"


@dataclass
class SpatialMapping:
    """Bidirectional mapping between screen coordinates and EGI elements."""
    element_id: ElementID
    element_type: str  # 'vertex', 'edge', 'cut'
    screen_bounds: QRectF
    hit_test_region: QRectF
    z_order: int = 0


@dataclass
class InteractionContext:
    """Context for current interaction session."""
    egi: RelationalGraphWithCuts
    spatial_mappings: Dict[ElementID, SpatialMapping]
    current_selection: SubgraphSelection
    interaction_state: InteractionState
    mode: str  # 'organon', 'ergasterion', 'agon'
    
    # Transformation context
    pending_transformation: Optional[FormalTransformationRule] = None
    transformation_preview: Optional[RelationalGraphWithCuts] = None
    validation_errors: List[str] = field(default_factory=list)


class InteractionManager(QObject):
    """
    Core manager for EGI diagram interactions.
    
    Maintains the connection between visual elements and logical structures,
    ensuring all interactions preserve Dau-compliant formal semantics.
    """
    
    # Signals for interaction events
    selection_changed = Signal(SubgraphSelection)
    transformation_requested = Signal(str, TransformationContext)
    validation_failed = Signal(list)  # List of error messages
    egi_updated = Signal(RelationalGraphWithCuts)
    
    def __init__(self):
        super().__init__()
        self.context: Optional[InteractionContext] = None
        self.validator = SubgraphValidator()
        self.transformation_rules: Dict[str, FormalTransformationRule] = {}
        
    def initialize_context(self, egi: RelationalGraphWithCuts, mode: str):
        """Initialize interaction context for a new EGI."""
        self.context = InteractionContext(
            egi=egi,
            spatial_mappings={},
            current_selection=SubgraphSelection(set(), set(), set()),
            interaction_state=InteractionState.IDLE,
            mode=mode
        )
        
    def register_spatial_mapping(self, element_id: ElementID, mapping: SpatialMapping):
        """Register spatial mapping for an EGI element."""
        if self.context:
            self.context.spatial_mappings[element_id] = mapping
            
    def hit_test(self, screen_point: QPointF) -> Optional[ElementID]:
        """Find EGI element at screen coordinates."""
        if not self.context:
            return None
            
        # Check mappings in z-order (highest first)
        candidates = []
        for element_id, mapping in self.context.spatial_mappings.items():
            if mapping.hit_test_region.contains(screen_point):
                candidates.append((mapping.z_order, element_id))
                
        if candidates:
            candidates.sort(reverse=True)  # Highest z-order first
            return candidates[0][1]
        return None
        
    def handle_mouse_press(self, event: QMouseEvent, scene_pos: QPointF):
        """Handle mouse press events for element selection."""
        if not self.context:
            return
            
        hit_element = self.hit_test(scene_pos)
        
        if event.modifiers() & Qt.ControlModifier:
            # Multi-select mode
            self._toggle_element_selection(hit_element)
        else:
            # Single select mode
            self._select_element(hit_element)
            
        self._validate_current_selection()
        
    def handle_mouse_drag(self, start_pos: QPointF, current_pos: QPointF):
        """Handle mouse drag for area selection or element movement."""
        if not self.context:
            return
            
        if self.context.interaction_state == InteractionState.SELECTING:
            # Area selection (subgraph line method)
            self._update_area_selection(start_pos, current_pos)
        elif self.context.interaction_state == InteractionState.DRAGGING:
            # Element dragging (if allowed by current mode)
            self._handle_element_drag(current_pos)
            
    def _select_element(self, element_id: Optional[ElementID]):
        """Select a single element, clearing previous selection."""
        if not self.context:
            return
            
        # Clear current selection
        self.context.current_selection = SubgraphSelection(set(), set(), set())
        
        if element_id:
            self._add_element_to_selection(element_id)
            
    def _toggle_element_selection(self, element_id: Optional[ElementID]):
        """Toggle element in current selection."""
        if not self.context or not element_id:
            return
            
        if self._is_element_selected(element_id):
            self._remove_element_from_selection(element_id)
        else:
            self._add_element_to_selection(element_id)
            
    def _add_element_to_selection(self, element_id: ElementID):
        """Add element to current selection based on its type."""
        if not self.context:
            return
            
        element_type = self._get_element_type(element_id)
        
        if element_type == 'vertex':
            self.context.current_selection.vertices.add(element_id)
        elif element_type == 'edge':
            self.context.current_selection.edges.add(element_id)
        elif element_type == 'cut':
            self.context.current_selection.cuts.add(element_id)
            
    def _remove_element_from_selection(self, element_id: ElementID):
        """Remove element from current selection."""
        if not self.context:
            return
            
        self.context.current_selection.vertices.discard(element_id)
        self.context.current_selection.edges.discard(element_id)
        self.context.current_selection.cuts.discard(element_id)
        
    def _is_element_selected(self, element_id: ElementID) -> bool:
        """Check if element is currently selected."""
        if not self.context:
            return False
            
        selection = self.context.current_selection
        return (element_id in selection.vertices or 
                element_id in selection.edges or 
                element_id in selection.cuts)
                
    def _get_element_type(self, element_id: ElementID) -> str:
        """Determine the type of an EGI element."""
        if not self.context:
            return "unknown"
            
        egi = self.context.egi
        if element_id in egi.V:
            return "vertex"
        elif element_id in egi.E:
            return "edge"
        elif element_id in egi.Cut:
            return "cut"
        return "unknown"
        
    def _validate_current_selection(self):
        """Validate current selection against Dau subgraph rules."""
        if not self.context:
            return
            
        # Use Chapter 21 validator
        validated_selection = self.validator.validate_subgraph(
            self.context.egi, 
            self.context.current_selection
        )
        
        self.context.current_selection = validated_selection
        
        if not validated_selection.is_valid:
            self.context.validation_errors = [validated_selection.validation_message]
            self.validation_failed.emit(self.context.validation_errors)
        else:
            self.context.validation_errors = []
            
        self.selection_changed.emit(self.context.current_selection)
        
    def _update_area_selection(self, start_pos: QPointF, current_pos: QPointF):
        """Update selection based on area rectangle (subgraph line method)."""
        if not self.context:
            return
            
        # Create selection rectangle
        selection_rect = QRectF(start_pos, current_pos).normalized()
        
        # Find all elements within rectangle
        selected_elements = []
        for element_id, mapping in self.context.spatial_mappings.items():
            if selection_rect.intersects(mapping.screen_bounds):
                selected_elements.append(element_id)
                
        # Update selection
        self.context.current_selection = SubgraphSelection(set(), set(), set())
        for element_id in selected_elements:
            self._add_element_to_selection(element_id)
            
        self._validate_current_selection()
        
    def request_transformation(self, rule_name: str):
        """Request application of a transformation rule to current selection."""
        if not self.context or not self.context.current_selection.is_valid:
            return
            
        # Create transformation context
        transform_context = TransformationContext(
            source_egi=self.context.egi,
            target_area=self._get_target_area(),
            selected_subgraph=frozenset(
                self.context.current_selection.vertices |
                self.context.current_selection.edges |
                self.context.current_selection.cuts
            ),
            area_polarity=self._determine_area_polarity(),
            nesting_depth=self._calculate_nesting_depth()
        )
        
        self.transformation_requested.emit(rule_name, transform_context)
        
    def apply_transformation_result(self, result: TransformationResult):
        """Apply the result of a transformation to update the EGI."""
        if not self.context or not result.success:
            return
            
        if result.result_egi:
            self.context.egi = result.result_egi
            self.egi_updated.emit(result.result_egi)
            
            # Clear selection after successful transformation
            self.context.current_selection = SubgraphSelection(set(), set(), set())
            self.selection_changed.emit(self.context.current_selection)
            
    def _get_target_area(self) -> ElementID:
        """Determine the target area for transformation."""
        # Implementation depends on selection and context
        # For now, return the outermost area
        return ElementID("sheet_of_assertion")
        
    def _determine_area_polarity(self) -> AreaPolarity:
        """Determine polarity of the target area."""
        # Implementation based on cut nesting analysis
        nesting_depth = self._calculate_nesting_depth()
        return AreaPolarity.POSITIVE if nesting_depth % 2 == 0 else AreaPolarity.NEGATIVE
        
    def _calculate_nesting_depth(self) -> int:
        """Calculate nesting depth of current selection."""
        # Implementation based on cut containment analysis
        return 0  # Placeholder
        
    def get_available_transformations(self) -> List[str]:
        """Get list of transformation rules applicable to current selection."""
        if not self.context or not self.context.current_selection.is_valid:
            return []
            
        # Filter rules based on selection and context
        available = []
        for rule_name, rule in self.transformation_rules.items():
            if self._is_rule_applicable(rule):
                available.append(rule_name)
                
        return available
        
    def _is_rule_applicable(self, rule: FormalTransformationRule) -> bool:
        """Check if a transformation rule is applicable to current context."""
        # Implementation depends on rule preconditions and current state
        return True  # Placeholder


class InteractionRenderer(ABC):
    """
    Abstract base for renderers that support interaction.
    
    Extends basic rendering to maintain spatial mappings and
    provide visual feedback for interactive operations.
    """
    
    @abstractmethod
    def render_with_interaction_support(
        self, 
        egi: RelationalGraphWithCuts, 
        scene: QGraphicsScene,
        interaction_manager: InteractionManager
    ):
        """Render EGI with interaction support, registering spatial mappings."""
        pass
        
    @abstractmethod
    def highlight_selection(self, selection: SubgraphSelection):
        """Provide visual feedback for current selection."""
        pass
        
    @abstractmethod
    def show_transformation_preview(self, preview_egi: RelationalGraphWithCuts):
        """Show preview of pending transformation."""
        pass
        
    @abstractmethod
    def show_validation_errors(self, errors: List[str]):
        """Display validation error feedback."""
        pass
