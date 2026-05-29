"""
DiagramController - Central coordinator for EGI diagramming application.

This controller implements the layered architecture separating "what" (use case logic)
from "how" (diagram manipulation). It manages state, validates operations, and
coordinates between the EGI model, layout engine, and GUI.

Architecture:
- DiagramController (The "How"): Low-level operations on EGI model and layout
- Use Case Logic (The "What"): High-level commands in Organon/Ergasterion/Agon
"""

import uuid
from typing import Dict, List, Optional, Tuple, Set, Any, FrozenSet
from dataclasses import dataclass, field

# Core EGI components
from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut

# Layout and styling
from unified_d3_engine import UnifiedD3Engine, LayoutDTO, Point, LigaturePath, BoundingBox


@dataclass
class LayoutDelta:
    """Represents a user-defined positional or path override for a single element."""
    element_id: str
    delta_type: str  # 'vertex_position', 'edge_position', 'cut_size', 'ligature_path'
    original_position: Optional[Tuple[float, float]] = None
    new_position: Optional[Tuple[float, float]] = None
    custom_path: Optional[List[Tuple[float, float]]] = None
    nu_mapping_key: Optional[str] = None


@dataclass
class LayoutDeltas:
    """Collection of user layout overrides for a single EGI state."""
    deltas: Dict[str, LayoutDelta] = field(default_factory=dict)
    deterministic_seed: Optional[int] = None

# Style system
from style_loader import StyleLoader, StyleSpecification

# Formal transformation rules
from formal_transformation_rules import (
    FormalTransformationRule,
    TransformationContext,
    TransformationResult,
    AreaPolarity,
    DoubleCutInsertionRule,
    DoubleCutErasureRule,
    InsertionRule,
    ErasureRule,
    IterationRule,
    DeiterationRule
)


@dataclass
class ValidationResult:
    """Result of validating a user action."""
    is_valid: bool
    error_message: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class DiagramState:
    """
    A single state in the diachronic sequence of a Universe of Discourse.
    
    Each state is a pair: (EGI_n, LayoutDeltas_n)
    - EGI_n: The logical structure at this point in the transformation sequence
    - LayoutDeltas_n: User aesthetic constraints applied to this state
    
    The deltas from state n become the starting point for state n+1 after reconciliation.
    """
    state_index: int
    egi: RelationalGraphWithCuts
    deltas: Dict[str, LayoutDelta]
    description: str = ""  # e.g., "Applied DC+ transformation"


class DiagramController:
    """
    Central controller for EGI diagramming application.

    Manages the complete application state and coordinates between:
    - EGI model (logical structure)
    - Layout engine (visual layout with user constraints)
    - GUI (user interactions and rendering)
    """

    def __init__(self):
        """Initialize the diagram controller."""
        self.egi_model: Optional[RelationalGraphWithCuts] = None
        self.current_dto: Optional[LayoutDTO] = None
        self.current_style: Optional[StyleSpecification] = None
        self.layout_deltas: Dict[str, LayoutDelta] = {}
        self.last_error: Optional[str] = None  # Store last error for UI display
        
        # Transformation history (diachronic workflow)
        self.transformation_history: Optional[Any] = None  # EGITransformationHistory when enabled
        
        # Initialize components
        self.layout_engine = UnifiedD3Engine()  # Using unified D3 engine (single simulation)
        self.style_loader = StyleLoader()
        
        # Initialize transformation rules
        self._transformation_rules: Dict[str, FormalTransformationRule] = {
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
            "INS": InsertionRule(),
            "ERA": ErasureRule(),
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
        }

    # === PUBLIC API: STATE & VIEW MANAGEMENT ===

    def enable_transformation_history(self, initial_description: str = "Initial state"):
        """
        Enable transformation history tracking with layout deltas.
        
        This enables the diachronic workflow where each state is tracked as
        (EGI_n, LayoutDeltas_n) with delta reconciliation across transformations.
        """
        from egi_transformation_history import EGITransformationHistory
        
        if not self.egi_model:
            print("Cannot enable history: No EGI model loaded")
            return False
        
        self.transformation_history = EGITransformationHistory(
            initial_egi=self.egi_model,
            description=initial_description
        )
        
        # Store initial layout deltas in the first state
        initial_state = self.transformation_history.get_current_state()
        if hasattr(initial_state, 'diagram_metadata'):
            initial_state.diagram_metadata['layout_deltas'] = {
                elem_id: {
                    'type': delta.delta_type,
                    'position': list(delta.new_position)
                }
                for elem_id, delta in self.layout_deltas.items()
            }
        
        print(f"✓ Transformation history enabled (State_0 with {len(self.layout_deltas)} deltas)")
        return True

    def load_egi(self, egi: RelationalGraphWithCuts, style: Optional[StyleSpecification] = None) -> bool:
        """
        Load a new EGI model and initialize the controller state.

        Args:
            egi: The EGI model to load
            style: Optional style specification (defaults to Dau style)

        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            print(f"DiagramController.load_egi: Starting with {len(egi.V)}V, {len(egi.E)}E, {len(egi.Cut)}C")
            
            # Validate the EGI model
            validation_error = self._validate_egi_model(egi)
            if validation_error:
                self.last_error = f"EGI validation failed: {validation_error}"
                print(f"DiagramController.load_egi: {self.last_error}")
                return False
            
            self.last_error = None  # Clear previous errors

            print("DiagramController.load_egi: Validation passed")

            # Set the new model and style
            self.egi_model = egi
            self.current_style = style or self.style_loader.load_default_style()

            # Clear all user constraints (fresh start)
            self.layout_deltas = {}

            print("DiagramController.load_egi: Calling _trigger_full_relayout")
            # Generate initial layout
            self._trigger_full_relayout()

            print(f"DiagramController.load_egi: SUCCESS, dto={self.current_dto is not None}")
            return True

        except Exception as e:
            self.last_error = f"Failed to load EGI: {str(e)}"
            print(f"DiagramController.load_egi: EXCEPTION - {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_renderable_dto(self) -> Optional[LayoutDTO]:
        """
        Get the current renderable layout for GUI display.

        Returns:
            Current LayoutDTO or None if no model loaded
        """
        return self.current_dto

    def get_egi_model(self) -> Optional[RelationalGraphWithCuts]:
        """Get the current EGI model."""
        return self.egi_model

    def get_layout_deltas(self) -> Dict[str, LayoutDelta]:
        """Get current user-defined layout constraints."""
        return self.layout_deltas.copy()

    # === PUBLIC API: LOGICAL TRANSFORMATION COMMANDS ===

    def apply_formal_rule(self, rule_name: str, selection_ids: List[str],
                         target_area: Optional[ElementID] = None) -> bool:
        """
        Apply a formal transformation rule to the current EGI.

        Args:
            rule_name: Name of the rule to apply (DC+, DC-, INS, ERA, IT+, IT-)
            selection_ids: List of element IDs selected for transformation
            target_area: Target area for the transformation (defaults to sheet)

        Returns:
            True if transformation applied successfully, False otherwise
        """
        if not self.egi_model:
            return False

        if rule_name not in self._transformation_rules:
            print(f"Unknown transformation rule: {rule_name}")
            return False

        # Convert to frozenset for consistency
        selected_subgraph = frozenset(selection_ids)
        
        print(f"=== APPLYING TRANSFORMATION ===")
        print(f"Rule: {rule_name}")
        print(f"Selection IDs: {list(selection_ids)}")
        print(f"Target area: {target_area}")

        # Determine target area
        if target_area is None:
            target_area = self.egi_model.sheet

        # Calculate area polarity and nesting depth
        polarity, nesting_depth = self._calculate_area_polarity(target_area)

        # Create transformation context
        context = TransformationContext(
            source_egi=self.egi_model,
            target_area=target_area,
            selected_subgraph=selected_subgraph,
            area_polarity=polarity,
            nesting_depth=nesting_depth
        )

        # Validate preconditions
        rule = self._transformation_rules[rule_name]
        print(f"=== Checking preconditions for {rule_name} ===")
        print(f"  Target area: {target_area}")
        print(f"  Area polarity: {polarity}")
        print(f"  Selection: {selection_ids}")
        
        is_valid, error_msg = rule.check_preconditions(context)

        if not is_valid:
            print(f"✗ Rule validation FAILED: {error_msg}")
            return False
        
        print(f"✓ Preconditions passed")

        # Apply transformation
        result = rule.apply_transformation(context)

        if not result.success:
            print(f"✗ Transformation failed: {result.error_message}")
            return False
        
        print(f"Successfully applied {rule_name} transformation")
        
        # DEBUG: Check EGI area mapping before/after
        print("=== EGI AREA MAPPING ===")
        print(f"BEFORE - Areas: {dict(self.egi_model.area)}")
        print(f"AFTER  - Areas: {dict(result.result_egi.area)}")
        
        # === DIACHRONIC DELTA WORKFLOW ===
        # CRITICAL: Deltas are RELATIVE to natural positions calculated by layout engine.
        # When transformation changes structure, natural positions change.
        # We must preserve ABSOLUTE positions, not relative deltas.
        
        # Step 1: Preserve deltas for elements that still exist
        # Simply filter out deltas for deleted elements
        print(f"=== DELTA PRESERVATION ===")
        print(f"Deltas before transformation: {list(self.layout_deltas.keys())}")
        
        old_deltas = dict(self.layout_deltas)
        
        # Step 2: Update EGI model
        self.egi_model = result.result_egi

        # Step 3: Filter deltas - keep only those for elements that still exist
        self._preserve_valid_constraints()
        
        print(f"Deltas after preservation: {list(self.layout_deltas.keys())}")
        
        # Step 4: Trigger layout with preserved deltas
        # The layout engine will:
        # - Position existing elements at their delta-specified positions
        # - Position new cuts (from DC+) to contain their contents
        # - Calculate natural positions for any new elements
        print(f"=== Triggering layout with {len(self.layout_deltas)} preserved deltas ===")
        self._trigger_full_relayout()
        
        # Step 6: Record transformation in history (if enabled)
        if self.transformation_history:
            self._record_transformation_with_deltas(
                rule_name, context, result, old_deltas, self.layout_deltas
            )

        print(f"✓ Transformation complete: preserved {len(self.layout_deltas)} absolute positions")
        return True

    # === PUBLIC API: AESTHETIC ADJUSTMENT COMMANDS ===

    def update_element_position(self, element_id: str, new_position: Tuple[float, float]) -> bool:
        """
        Update position of a vertex or edge label with validation.

        Args:
            element_id: ID of element to move
            new_position: New (x, y) position

        Returns:
            True if position updated, False if validation failed
        """
        if not self.current_dto:
            return False

        # Validate the new position
        validation = self._validate_element_position(element_id, new_position)
        if not validation.is_valid:
            print(f"Position validation failed: {validation.error_message}")
            if validation.suggested_fix:
                print(f"Suggested fix: {validation.suggested_fix}")
            return False

        # Update layout deltas
        self.layout_deltas[element_id] = LayoutDelta(
            element_id=element_id,
            delta_type='vertex_position' if self._is_vertex_element(element_id) else 'edge_position',
            new_position=new_position
        )

        # Trigger fast update (no full re-layout needed)
        self._trigger_fast_update()

        return True
    
    def update_cut_position(self, cut_id: str, delta: Tuple[float, float]) -> bool:
        """
        Update position of a cut and all its contents (container movement).
        
        This should ONLY be called for user-initiated drags, not layout engine repositioning.
        
        Args:
            cut_id: ID of cut to move
            delta: (dx, dy) movement delta
            
        Returns:
            True if position updated successfully
        """
        if not self.current_dto or not self.egi_model:
            return False
        
        dx, dy = delta
        
        print(f"=== Updating cut {cut_id} position by delta ({dx}, {dy}) ===")
        
        # Get all elements contained in this cut (recursively)
        def get_all_contents(area_id: str) -> set:
            """Recursively get all elements in an area and its sub-areas."""
            contents = set()
            area_contents = self.egi_model.area.get(area_id, frozenset())
            
            for elem_id in area_contents:
                contents.add(elem_id)
                # If element is a cut, recursively get its contents
                if any(c.id == elem_id for c in self.egi_model.Cut):
                    contents.update(get_all_contents(elem_id))
            
            return contents
        
        all_contents = get_all_contents(cut_id)
        print(f"  Moving {len(all_contents)} contained elements")
        
        # Apply delta to all contents
        for elem_id in all_contents:
            if elem_id in self.current_dto.vertex_positions:
                old_pos = self.current_dto.vertex_positions[elem_id]
                new_pos = (old_pos.x + dx, old_pos.y + dy)
                print(f"    Moving vertex {elem_id}: ({old_pos.x}, {old_pos.y}) → ({new_pos[0]}, {new_pos[1]})")
                # Update position without validation (container movement)
                self.layout_deltas[elem_id] = LayoutDelta(
                    element_id=elem_id,
                    delta_type='vertex_position',
                    new_position=new_pos
                )
            elif elem_id in self.current_dto.predicate_positions:
                old_pos = self.current_dto.predicate_positions[elem_id]
                new_pos = (old_pos.x + dx, old_pos.y + dy)
                print(f"    Moving predicate {elem_id}: ({old_pos.x}, {old_pos.y}) → ({new_pos[0]}, {new_pos[1]})")
                self.layout_deltas[elem_id] = LayoutDelta(
                    element_id=elem_id,
                    delta_type='edge_position',
                    new_position=new_pos
                )
            # Also handle nested cuts
            elif elem_id in self.current_dto.cut_bounds:
                # Cuts will be repositioned when layout is triggered
                print(f"    Moving nested cut {elem_id}")
                pass
        
        print(f"  Total layout deltas after cut move: {len(self.layout_deltas)}")
        
        # CRITICAL: Also update the cut bounds in the DTO
        # The cut rectangle itself needs to move by the same delta
        if cut_id in self.current_dto.cut_bounds:
            old_bounds = self.current_dto.cut_bounds[cut_id]
            new_bounds = BoundingBox(
                min_x=old_bounds.min_x + dx,
                min_y=old_bounds.min_y + dy,
                max_x=old_bounds.max_x + dx,
                max_y=old_bounds.max_y + dy
            )
            self.current_dto.cut_bounds[cut_id] = new_bounds
            print(f"  Updated cut bounds: {old_bounds} → {new_bounds}")
            
            # Also update any nested cut bounds recursively
            for nested_cut_id in all_contents:
                if nested_cut_id in self.current_dto.cut_bounds:
                    old_bounds = self.current_dto.cut_bounds[nested_cut_id]
                    new_bounds = BoundingBox(
                        min_x=old_bounds.min_x + dx,
                        min_y=old_bounds.min_y + dy,
                        max_x=old_bounds.max_x + dx,
                        max_y=old_bounds.max_y + dy
                    )
                    self.current_dto.cut_bounds[nested_cut_id] = new_bounds
                    print(f"  Updated nested cut {nested_cut_id} bounds")
        
        # Trigger fast update to apply all deltas
        self._trigger_fast_update()
        
        return True
    
    def update_cut_size(self, cut_id: str, new_size: Tuple[float, float]) -> bool:
        """
        Update the size of a cut after user resize.
        
        Validates that new size can contain all elements AND their ligatures.
        
        Args:
            cut_id: ID of cut to resize
            new_size: (width, height) new dimensions
            
        Returns:
            True if size updated successfully, False if resize would violate containment
        """
        if not self.current_dto or not self.egi_model:
            return False
        
        w, h = new_size
        print(f"=== Validating cut {cut_id} resize to ({w}, {h}) ===")
        
        # Get current cut bounds
        if cut_id not in self.current_dto.cut_bounds:
            print(f"  Cut {cut_id} not found in cut_bounds")
            return False
        
        old_bounds = self.current_dto.cut_bounds[cut_id]
        
        # Calculate new bounds - keep top-left corner, adjust bottom-right
        new_bounds = BoundingBox(
            min_x=old_bounds.min_x,
            min_y=old_bounds.min_y,
            max_x=old_bounds.min_x + w,
            max_y=old_bounds.min_y + h
        )
        
        # VALIDATION: Check that all contained elements fit within new bounds
        cut_contents = self.egi_model.area.get(cut_id, frozenset())
        
        # Add padding for visual clarity (elements shouldn't touch edges)
        padding = 10.0
        content_bounds = BoundingBox(
            min_x=new_bounds.min_x + padding,
            min_y=new_bounds.min_y + padding,
            max_x=new_bounds.max_x - padding,
            max_y=new_bounds.max_y - padding
        )
        
        # Check vertices
        for elem_id in cut_contents:
            if elem_id in self.current_dto.vertex_positions:
                pos = self.current_dto.vertex_positions[elem_id]
                if not (content_bounds.min_x <= pos.x <= content_bounds.max_x and
                        content_bounds.min_y <= pos.y <= content_bounds.max_y):
                    print(f"  REJECT: Vertex {elem_id} at ({pos.x}, {pos.y}) outside new bounds")
                    return False
            
            # Check predicates (edges)
            elif elem_id in self.current_dto.predicate_positions:
                pos = self.current_dto.predicate_positions[elem_id]
                # Predicates have width/height - check bounds
                pred_label = self._get_predicate_label(elem_id)
                pred_width = len(pred_label) * self.current_style.predicate_char_width
                pred_height = self.current_style.predicate_height
                
                if not (content_bounds.min_x <= pos.x and 
                        pos.x + pred_width <= content_bounds.max_x and
                        content_bounds.min_y <= pos.y and
                        pos.y + pred_height <= content_bounds.max_y):
                    print(f"  REJECT: Predicate {elem_id} at ({pos.x}, {pos.y}) outside new bounds")
                    return False
        
        # Check ligatures connecting elements inside this cut
        # Ligatures must be entirely within the cut bounds
        for lig_path in self.current_dto.ligature_paths:
            # Check if both endpoints are in this cut
            pred_in_cut = lig_path.predicate_id in cut_contents
            vertex_in_cut = lig_path.vertex_id in cut_contents
            
            if pred_in_cut and vertex_in_cut:
                # Both ends in cut - entire ligature must fit
                for point in lig_path.points:
                    if not (content_bounds.min_x <= point.x <= content_bounds.max_x and
                            content_bounds.min_y <= point.y <= content_bounds.max_y):
                        print(f"  REJECT: Ligature {lig_path.predicate_id}→{lig_path.vertex_id} extends outside new bounds")
                        return False
        
        print(f"  ✓ Validation passed - all contents fit within new bounds")
        
        # Update cut bounds
        self.current_dto.cut_bounds[cut_id] = new_bounds
        print(f"  Updated cut bounds: {old_bounds} → {new_bounds}")
        
        # Store cut size constraint in layout deltas (so layout engine respects it)
        self.layout_deltas[cut_id] = LayoutDelta(
            element_id=cut_id,
            delta_type='cut_size',
            new_position=None,  # Not used for cut size
            custom_data={'width': w, 'height': h}
        )
        
        return True

    def update_ligature_path(self, ligature_key: str, new_path: List[Tuple[float, float]]) -> bool:
        """
        Update custom path for a ligature with validation.

        Args:
            ligature_key: Unique key identifying the ligature (format: "vertex_id_edge_id_hook_index")
            new_path: New path points for the ligature

        Returns:
            True if path updated, False if validation failed
        """
        if not self.current_dto:
            return False

        # Validate the new path
        validation = self._validate_ligature_path(ligature_key, new_path)
        if not validation.is_valid:
            print(f"Path validation failed: {validation.error_message}")
            if validation.suggested_fix:
                print(f"Suggested fix: {validation.suggested_fix}")
            return False

        # Update layout deltas
        vertex_id, edge_id, hook_index = ligature_key.split('_', 2)
        self.layout_deltas[ligature_key] = LayoutDelta(
            element_id=ligature_key,
            delta_type='ligature_path',
            custom_path=new_path,
            nu_mapping_key=f"{edge_id}_{hook_index}"
        )

        # Update DTO directly (no re-layout needed for path changes)
        self._update_ligature_path_in_dto(ligature_key, new_path)

        return True

    # === INTERNAL METHODS ===

    def _trigger_full_relayout(self):
        """
        Trigger complete re-layout after logical changes.
        
        SIMPLIFIED: Just call the unified D3 engine once with all context.
        The engine handles everything: sizing, positioning, containment.
        """
        if not self.egi_model or not self.current_style:
            return

        try:
            # Single call to unified D3 engine - it does everything
            self.current_dto = self.layout_engine.generate_layout(
                egi=self.egi_model,
                style=self.current_style,
                layout_deltas=self.layout_deltas  # Pass user constraints
            )
            
            if self.current_dto is None:
                print("ERROR: Layout engine returned None")
                return
            
            # DEBUG: Check layout output
            print("=== LAYOUT ENGINE OUTPUT ===")
            print(f"Vertex positions: {self.current_dto.vertex_positions}")
            print(f"Predicate positions: {self.current_dto.predicate_positions}")
            print(f"Cut bounds: {self.current_dto.cut_bounds}")
            
        except Exception as e:
            print(f"ERROR in _trigger_full_relayout: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _trigger_fast_update(self):
        """
        Fast path: Update DTO directly without re-layout.
        Only updates positions and recalculates affected ligatures.
        """
        if not self.current_dto:
            print("WARNING: _trigger_fast_update called but current_dto is None")
            return
        
        if not self.egi_model:
            print("WARNING: _trigger_fast_update called but egi_model is None")
            return
        
        if not self.layout_deltas:
            print("INFO: _trigger_fast_update called but no layout_deltas to apply")
            return
        
        print(f"=== FAST PATH: Applying {len(self.layout_deltas)} layout deltas ===")
        
        # Update positions in DTO from layout_deltas
        for element_id, delta in self.layout_deltas.items():
            if delta.delta_type == 'vertex_position' and element_id in self.current_dto.vertex_positions:
                old_pos = self.current_dto.vertex_positions[element_id]
                new_pos = Point(x=delta.new_position[0], y=delta.new_position[1])
                self.current_dto.vertex_positions[element_id] = new_pos
                print(f"  Updated vertex {element_id}: {old_pos} -> {new_pos}")
                
                # Recalculate ligatures connected to this vertex
                self._recalculate_ligatures_for_vertex(element_id)
                
            elif delta.delta_type == 'edge_position' and element_id in self.current_dto.predicate_positions:
                old_pos = self.current_dto.predicate_positions[element_id]
                new_pos = Point(x=delta.new_position[0], y=delta.new_position[1])
                self.current_dto.predicate_positions[element_id] = new_pos
                print(f"  Updated predicate {element_id}: {old_pos} -> {new_pos}")
                
                # Recalculate ligatures connected to this predicate
                self._recalculate_ligatures_for_predicate(element_id)
        
        print("=== Fast update complete ===")
    
    def _recalculate_ligatures_for_vertex(self, vertex_id: str):
        """Recalculate all ligatures connected to a vertex."""
        vertex_pos = self.current_dto.vertex_positions.get(vertex_id)
        if not vertex_pos:
            return
        
        # Update ligature paths that connect to this vertex
        updated_paths = []
        for lig_path in self.current_dto.ligature_paths:
            if lig_path.vertex_id == vertex_id:
                # Recalculate: from predicate BOUNDARY to vertex center
                pred_pos = self.current_dto.predicate_positions.get(lig_path.predicate_id)
                if pred_pos:
                    # Calculate attachment point at predicate boundary
                    # Predicate text box dimensions from style
                    pred_label = self._get_predicate_label(lig_path.predicate_id)
                    char_width = self.current_style.predicate_char_width
                    pred_height = self.current_style.predicate_height
                    pred_width = len(pred_label) * char_width
                    
                    # Add small padding for visual breathing room (2px)
                    hook_padding = 2.0
                    
                    # Calculate boundary point on predicate box closest to vertex
                    boundary_point = self._calculate_boundary_point(
                        pred_pos, pred_width + hook_padding, pred_height + hook_padding, vertex_pos
                    )
                    
                    updated_path = LigaturePath(
                        predicate_id=lig_path.predicate_id,
                        vertex_id=vertex_id,
                        points=(boundary_point, vertex_pos)
                    )
                    updated_paths.append(updated_path)
                    print(f"    Rerouted ligature {lig_path.predicate_id} -> {vertex_id}")
            else:
                updated_paths.append(lig_path)
        
        self.current_dto.ligature_paths = updated_paths
    
    def _recalculate_ligatures_for_predicate(self, predicate_id: str):
        """Recalculate all ligatures connected to a predicate."""
        pred_pos = self.current_dto.predicate_positions.get(predicate_id)
        if not pred_pos:
            return
        
        # Get predicate dimensions
        pred_label = self._get_predicate_label(predicate_id)
        char_width = self.current_style.predicate_char_width
        pred_height = self.current_style.predicate_height
        pred_width = len(pred_label) * char_width
        
        # Add small padding for visual breathing room (2px)
        hook_padding = 2.0
        
        # Update ligature paths that connect from this predicate
        updated_paths = []
        for lig_path in self.current_dto.ligature_paths:
            if lig_path.predicate_id == predicate_id:
                # Recalculate: from predicate BOUNDARY to vertex center
                vertex_pos = self.current_dto.vertex_positions.get(lig_path.vertex_id)
                if vertex_pos:
                    # Calculate attachment point at predicate boundary
                    boundary_point = self._calculate_boundary_point(
                        pred_pos, pred_width + hook_padding, pred_height + hook_padding, vertex_pos
                    )
                    
                    updated_path = LigaturePath(
                        predicate_id=predicate_id,
                        vertex_id=lig_path.vertex_id,
                        points=(boundary_point, vertex_pos)
                    )
                    updated_paths.append(updated_path)
                    print(f"    Rerouted ligature {predicate_id} -> {lig_path.vertex_id}")
            else:
                updated_paths.append(lig_path)
        
        self.current_dto.ligature_paths = updated_paths
    
    def _get_predicate_label(self, predicate_id: str) -> str:
        """Get the label text for a predicate."""
        if not self.egi_model:
            return "?"
        return self.egi_model.get_relation_name(predicate_id)
    
    def _calculate_boundary_point(
        self, 
        box_center: Point, 
        box_width: float, 
        box_height: float, 
        target_point: Point
    ) -> Point:
        """
        Calculate the point on a box's boundary closest to a target point.
        Box is centered at box_center with given width and height.
        """
        # Calculate box boundaries
        left = box_center.x - box_width / 2
        right = box_center.x + box_width / 2
        top = box_center.y - box_height / 2
        bottom = box_center.y + box_height / 2
        
        # Direction from box center to target
        dx = target_point.x - box_center.x
        dy = target_point.y - box_center.y
        
        # Find intersection with box boundary
        # Calculate which edge the ray hits first
        if dx == 0 and dy == 0:
            # Target is at box center, use right edge
            return Point(x=right, y=box_center.y)
        
        # Calculate intersection with each edge
        t_left = (left - box_center.x) / dx if dx != 0 else float('inf')
        t_right = (right - box_center.x) / dx if dx != 0 else float('inf')
        t_top = (top - box_center.y) / dy if dy != 0 else float('inf')
        t_bottom = (bottom - box_center.y) / dy if dy != 0 else float('inf')
        
        # Find the closest positive intersection
        t = float('inf')
        if t_right > 0 and t_right < t:
            t = t_right
        if t_left > 0 and t_left < t:
            t = t_left
        if t_bottom > 0 and t_bottom < t:
            t = t_bottom
        if t_top > 0 and t_top < t:
            t = t_top
        
        if t == float('inf'):
            # Fallback to box center
            return box_center
        
        # Calculate intersection point
        return Point(
            x=box_center.x + t * dx,
            y=box_center.y + t * dy
        )

    def _preserve_valid_constraints(self):
        """Preserve user constraints that are still valid after transformation."""
        if not self.current_dto or not self.egi_model:
            return

        valid_deltas = {}

        for element_id, delta in self.layout_deltas.items():
            # Check if element still exists in the new model
            if self._element_exists_in_model(element_id):
                # PRESERVE ALL DELTAS - even if element moved to different area
                # The position constraint is still valid, just in a different context
                valid_deltas[element_id] = delta

        print(f"  Preserved {len(valid_deltas)} deltas")
        self.layout_deltas = valid_deltas

    def _element_exists_in_model(self, element_id: str) -> bool:
        """Check if element still exists in current EGI model."""
        if not self.egi_model:
            return False

        # Check vertices
        if any(v.id == element_id for v in self.egi_model.V):
            return True

        # Check edges
        if any(e.id == element_id for e in self.egi_model.E):
            return True

        # Check cuts
        if any(c.id == element_id for c in self.egi_model.Cut):
            return True

        return False

    def _is_vertex_element(self, element_id: str) -> bool:
        """Check if element is a vertex."""
        if not self.egi_model:
            return False
        return any(v.id == element_id for v in self.egi_model.V)
    
    def _record_transformation_with_deltas(
        self, 
        rule_name: str,
        context: TransformationContext,
        result: TransformationResult,
        old_deltas: Dict[str, LayoutDelta],
        new_deltas: Dict[str, LayoutDelta]
    ):
        """
        Record transformation in history with layout delta information.
        
        This implements the diachronic workflow where each state includes both
        the logical structure (EGI) and aesthetic constraints (layout deltas).
        
        The history records:
        - State_n: (EGI_n, Deltas_n) - before transformation
        - State_n+1: (EGI_n+1, Deltas_n+1) - after transformation + reconciliation
        """
        if not self.transformation_history:
            return
        
        # Serialize layout deltas for storage
        deltas_metadata = {
            'before_deltas': {
                elem_id: {
                    'type': delta.delta_type,
                    'position': list(delta.new_position)
                }
                for elem_id, delta in old_deltas.items()
            },
            'after_deltas': {
                elem_id: {
                    'type': delta.delta_type,
                    'position': list(delta.new_position)
                }
                for elem_id, delta in new_deltas.items()
            },
            'deltas_preserved': len(new_deltas),
            'deltas_discarded': len(old_deltas) - len(new_deltas),
            'affected_elements': list(result.changes_made.get('affected_elements', []))
        }
        
        # Add transformation to history
        # The EGITransformationHistory will store this in StateSnapshot.diagram_metadata
        self.transformation_history.add_transformation(
            rule_name=rule_name,
            context=context,
            result=result,
            user_annotation=f"Applied {rule_name} with {len(new_deltas)} layout constraints",
            logical_justification=None  # Could be added for proof tracking
        )
        
        # Update the current state's diagram metadata with layout deltas
        current_state = self.transformation_history.get_current_state()
        if hasattr(current_state, 'diagram_metadata'):
            current_state.diagram_metadata['layout_deltas'] = deltas_metadata['after_deltas']
            current_state.diagram_metadata['delta_reconciliation'] = {
                'preserved': deltas_metadata['deltas_preserved'],
                'discarded': deltas_metadata['deltas_discarded']
            }

    def _is_edge_element(self, element_id: str) -> bool:
        """Check if element is an edge."""
        if not self.egi_model:
            return False
        return any(e.id == element_id for e in self.egi_model.E)

    def _is_cut_element(self, element_id: str) -> bool:
        """Check if element is a cut."""
        if not self.egi_model:
            return False
        return any(c.id == element_id for c in self.egi_model.Cut)

    # === VALIDATION METHODS ===

    def _validate_egi_model(self, egi: RelationalGraphWithCuts) -> Optional[str]:
        """Validate that EGI model is well-formed.
        
        Returns:
            None if valid, error message string if invalid
        """
        try:
            # The EGI constructor already validates Dau's formal constraints in __post_init__
            # Empty graphs (no vertices/edges) are mathematically valid
            # A graph with just a sheet, or sheet + cuts, is valid for composition
            
            # Verify basic structure exists
            if not hasattr(egi, 'sheet'):
                return "EGI missing 'sheet' component"
            
            if not hasattr(egi, 'area'):
                return "EGI missing 'area' mapping"
            
            if not hasattr(egi, 'V'):
                return "EGI missing 'V' (vertices) component"
            
            if not hasattr(egi, 'E'):
                return "EGI missing 'E' (edges) component"
            
            if not hasattr(egi, 'Cut'):
                return "EGI missing 'Cut' component"
            
            # Verify sheet is in area mapping
            if egi.sheet not in egi.area:
                return f"Sheet '{egi.sheet}' not found in area mapping"

            return None  # Valid

        except Exception as e:
            return f"Validation exception: {str(e)}"

    def _calculate_area_polarity(self, area_id: ElementID) -> Tuple[AreaPolarity, int]:
        """Calculate polarity and nesting depth of an area.

        Delegates to the canonical ``egi.area_polarity()`` method.
        """
        if not self.egi_model:
            return AreaPolarity.POSITIVE, 0
        return self.egi_model.area_polarity(area_id)

    def _validate_element_position(self, element_id: str, new_position: Tuple[float, float]) -> ValidationResult:
        """Validate that a new element position is within logical bounds."""
        if not self.current_dto:
            return ValidationResult(False, "No current layout available")

        # Find the element in current DTO
        if self._is_vertex_element(element_id):
            # Check if vertex exists in LayoutDTO
            if element_id not in self.current_dto.vertex_positions:
                return ValidationResult(False, f"Vertex {element_id} not found in current layout")
            
            # Validate area containment
            return self._validate_area_containment(element_id, new_position, 'vertex')

        elif self._is_edge_element(element_id):
            # Check if predicate exists in LayoutDTO
            if element_id not in self.current_dto.predicate_positions:
                return ValidationResult(False, f"Edge {element_id} not found in current layout")
            
            # Validate area containment
            return self._validate_area_containment(element_id, new_position, 'predicate')

        else:
            return ValidationResult(False, f"Element {element_id} is not a movable element")

        return ValidationResult(True)

    def _validate_ligature_path(self, ligature_key: str, new_path: List[Tuple[float, float]]) -> ValidationResult:
        """Validate that a custom ligature path is collision-free and logically valid."""
        if not self.current_dto:
            return ValidationResult(False, "No current layout available")

        # Parse ligature key to get vertex and edge information
        try:
            vertex_id, edge_id, hook_index_str = ligature_key.split('_', 2)
            hook_index = int(hook_index_str)
        except (ValueError, IndexError):
            return ValidationResult(False, f"Invalid ligature key format: {ligature_key}")

        # Find the vertex and edge in current layout
        vertex = next((v for v in self.current_dto.vertices if v.id == vertex_id), None)
        edge_label = next((e for e in self.current_dto.edge_labels if e.id == edge_id), None)

        if not vertex or not edge_label:
            return ValidationResult(False, f"Vertex {vertex_id} or edge {edge_id} not found in current layout")

        # Check if path endpoints connect to correct elements
        start_pos = new_path[0] if new_path else None
        end_pos = new_path[-1] if new_path else None

        if not start_pos or not self._positions_approximately_equal(start_pos, vertex.pos):
            return ValidationResult(False, "Path start point must match vertex position")

        # For end position, we need to check if it connects to the correct port on the edge label
        # This is simplified - in full implementation we'd check specific port positions
        edge_center = self._get_edge_label_center(edge_label)
        if not end_pos or not self._positions_approximately_equal(end_pos, edge_center, tolerance=20):
            return ValidationResult(False, "Path end point must connect to edge label")

        # Check for collisions with other elements
        if self._path_collides_with_obstacles(new_path, self.current_dto):
            return ValidationResult(
                False,
                "Path collides with other diagram elements",
                "Try adjusting the path to avoid overlapping with vertices or other edges"
            )

        # Check logical area constraints (simplified)
        if not self._path_respects_logical_areas(new_path):
            return ValidationResult(
                False,
                "Path violates logical area boundaries",
                "Ensure the path stays within appropriate logical areas"
            )

        return ValidationResult(True)
    
    def _validate_area_containment(self, element_id: str, new_position: Tuple[float, float], 
                                   element_type: str) -> ValidationResult:
        """
        Validate that element stays within its logical area (EGI.area mapping).
        
        This enforces Dau's iron-clad principle: elements cannot escape their assigned areas.
        """
        if not self.egi_model or not self.current_dto:
            print(f"  [VALIDATION] No EGI or DTO - allowing move")
            return ValidationResult(True)  # Can't validate without EGI
        
        # Find which area this element belongs to in the EGI
        element_area_id = None
        for area_id, elements in self.egi_model.area.items():
            if element_id in elements:
                element_area_id = area_id
                break
        
        print(f"  [VALIDATION] Element {element_id} belongs to area: {element_area_id}")
        
        if not element_area_id:
            # Element not in any area (shouldn't happen, but allow it)
            print(f"  [VALIDATION] Element not in any area - allowing move")
            return ValidationResult(True)
        
        # Get the bounding box for this area from the DTO
        if element_area_id not in self.current_dto.cut_bounds:
            # Area has no bounds yet - allow movement
            print(f"  [VALIDATION] Area {element_area_id} has no bounds in DTO - allowing move")
            print(f"  [VALIDATION] Available cut_bounds: {list(self.current_dto.cut_bounds.keys())}")
            return ValidationResult(True)
        
        area_bounds = self.current_dto.cut_bounds[element_area_id]
        
        # Check if new position is within area bounds
        x, y = new_position
        
        # Sheet allows free movement (no boundary), but still check child cuts
        is_sheet = (element_area_id == self.current_dto.sheet_id)
        
        if not is_sheet:
            print(f"  [VALIDATION] Area bounds: ({area_bounds.min_x}, {area_bounds.min_y}) to ({area_bounds.max_x}, {area_bounds.max_y})")
            print(f"  [VALIDATION] New position: ({x}, {y})")
        else:
            print(f"  [VALIDATION] Element on sheet - checking child cuts only")
        
        # CRITICAL: Check if new position enters any child cuts (where element doesn't belong)
        # Find all child cuts of this area
        # Use a small inset tolerance to avoid blocking movements near cut boundaries
        boundary_tolerance = 2.0  # pixels of grace at cut boundaries
        
        child_cuts = self.egi_model.area.get(element_area_id, frozenset())
        print(f"  [VALIDATION] Checking {len([c for c in child_cuts if any(cut.id == c for cut in self.egi_model.Cut)])} child cuts")
        
        for child_id in child_cuts:
            # Is this a cut?
            if any(cut.id == child_id for cut in self.egi_model.Cut):
                # Check if new position is inside this child cut (with tolerance)
                if child_id in self.current_dto.cut_bounds:
                    child_bounds = self.current_dto.cut_bounds[child_id]
                    # Apply inward tolerance - only block if clearly inside the cut
                    inset_min_x = child_bounds.min_x + boundary_tolerance
                    inset_max_x = child_bounds.max_x - boundary_tolerance
                    inset_min_y = child_bounds.min_y + boundary_tolerance
                    inset_max_y = child_bounds.max_y - boundary_tolerance
                    
                    if (inset_min_x <= x <= inset_max_x and
                        inset_min_y <= y <= inset_max_y):
                        print(f"  [VALIDATION] BLOCKED: Position is inside child cut {child_id}")
                        print(f"     Child bounds: ({child_bounds.min_x}, {child_bounds.min_y}) to ({child_bounds.max_x}, {child_bounds.max_y})")
                        print(f"     Inset bounds (tolerance={boundary_tolerance}): ({inset_min_x}, {inset_min_y}) to ({inset_max_x}, {inset_max_y})")
                        return ValidationResult(
                            False,
                            f"Element cannot be moved into nested cut {child_id}",
                            f"Element must stay in its assigned area, not enter child cuts"
                        )
        
        # For vertices: point must be inside parent area (unless on sheet)
        if element_type == 'vertex' and not is_sheet:
            within_bounds = (area_bounds.min_x <= x <= area_bounds.max_x and
                           area_bounds.min_y <= y <= area_bounds.max_y)
            print(f"  [VALIDATION] Vertex within bounds: {within_bounds}")
            if not within_bounds:
                return ValidationResult(
                    False,
                    f"Vertex cannot be moved outside its logical area",
                    f"Keep vertex within the bounds of its containing cut"
                )
        
        # For predicates: center must be inside (with small tolerance for text width, unless on sheet)
        elif element_type == 'predicate' and not is_sheet:
            # Get predicate dimensions from style
            pred_label = self._get_predicate_label(element_id)
            char_width = self.current_style.predicate_char_width if self.current_style else 6.2
            pred_width = len(pred_label) * char_width
            pred_height = self.current_style.predicate_height if self.current_style else 14.0
            
            # Check if predicate box fits within area
            pred_min_x = x - pred_width / 2
            pred_max_x = x + pred_width / 2
            pred_min_y = y - pred_height / 2
            pred_max_y = y + pred_height / 2
            
            if not (area_bounds.min_x <= pred_min_x and pred_max_x <= area_bounds.max_x and
                    area_bounds.min_y <= pred_min_y and pred_max_y <= area_bounds.max_y):
                return ValidationResult(
                    False,
                    f"Predicate cannot be moved outside its logical area",
                    f"Keep predicate fully within the bounds of its containing cut"
                )
        
        return ValidationResult(True)

    def _find_logical_area_for_element(self, element_id: str) -> Optional[Any]:
        """Find the logical area containing an element."""
        if not self.current_dto:
            return None

        # Find which area contains this element based on current layout
        for area in self.current_dto.areas:
            # Check if element is in this area's rect (simplified containment check)
            # In a full implementation, we'd use the hierarchical index
            if self._element_in_area_rect(element_id, area.rect):
                return area

        return None

    def _element_in_area_rect(self, element_id: str, area_rect) -> bool:
        """Check if element is visually within an area rectangle."""
        # This is a simplified check - in full implementation we'd use proper spatial indexing
        if self._is_vertex_element(element_id):
            vertex = next((v for v in self.current_dto.vertices if v.id == element_id), None)
            if vertex:
                return self._point_in_rect(vertex.pos, area_rect)
        elif self._is_edge_element(element_id):
            edge = next((e for e in self.current_dto.edge_labels if e.id == element_id), None)
            if edge:
                return self._rect_in_rect(edge.rect, area_rect)

        return False

    def _point_in_rect(self, point: Tuple[float, float], rect) -> bool:
        """Check if point is within rectangle."""
        x, y = point
        return (rect.x <= x <= rect.x + rect.width and
                rect.y <= y <= rect.y + rect.height)

    def _point_in_rect_with_padding(self, point: Tuple[float, float], rect, padding: float) -> bool:
        """Check if point is within rectangle with padding."""
        x, y = point
        return (rect.x - padding <= x <= rect.x + rect.width + padding and
                rect.y - padding <= y <= rect.y + rect.height + padding)

    def _rect_in_rect(self, inner_rect, outer_rect) -> bool:
        """Check if inner rectangle is within outer rectangle."""
        return (inner_rect.x >= outer_rect.x and
                inner_rect.y >= outer_rect.y and
                inner_rect.x + inner_rect.width <= outer_rect.x + outer_rect.width and
                inner_rect.y + inner_rect.height <= outer_rect.y + outer_rect.height)

    def _positions_approximately_equal(self, pos1: Tuple[float, float], pos2: Tuple[float, float], tolerance: float = 5.0) -> bool:
        """Check if two positions are approximately equal within tolerance."""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        return (dx * dx + dy * dy) <= (tolerance * tolerance)

    def _get_edge_label_center(self, edge_label) -> Tuple[float, float]:
        """Get center point of edge label."""
        return (edge_label.rect.x + edge_label.rect.width / 2,
                edge_label.rect.y + edge_label.rect.height / 2)

    def _path_collides_with_obstacles(self, path: List[Tuple[float, float]], dto: LayoutDTO) -> bool:
        """Check if path collides with any diagram elements."""
        for point in path:
            # Check vertices
            for vertex in dto.vertices:
                if self._point_in_circle(point, vertex.pos, 8):  # 8px collision radius
                    return True

            # Check edge labels
            for label in dto.edge_labels:
                if self._point_in_rect(point, label.rect):
                    return True

        return False

    def _point_in_circle(self, point: Tuple[float, float], center: Tuple[float, float], radius: float) -> bool:
        """Check if point is within circle."""
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        return (dx * dx + dy * dy) <= (radius * radius)

    def _path_respects_logical_areas(self, path: List[Tuple[float, float]]) -> bool:
        """Check if path respects logical area boundaries (simplified)."""
        # In a full implementation, this would check that the path doesn't cross
        # forbidden cut boundaries according to Dau's formalism

        # For now, we'll just ensure the path doesn't go outside reasonable bounds
        # This is a simplified check - full implementation would use area-aware pathfinding
        if not self.current_dto:
            return True

        # Get overall diagram bounds
        all_areas = [area.rect for area in self.current_dto.areas]
        if not all_areas:
            return True

        # Find bounds of all areas
        min_x = min(rect.x for rect in all_areas)
        min_y = min(rect.y for rect in all_areas)
        max_x = max(rect.x + rect.width for rect in all_areas)
        max_y = max(rect.y + rect.height for rect in all_areas)

        # Allow some padding
        padding = 100
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        # Check if all path points are within bounds
        for point in path:
            if not (min_x <= point[0] <= max_x and min_y <= point[1] <= max_y):
                return False

        return True

    def _update_ligature_path_in_dto(self, ligature_key: str, new_path: List[Tuple[float, float]]):
        """Update ligature path directly in current DTO."""
        if not self.current_dto:
            return

        # Find the ligature in current DTO and update its path
        vertex_id, edge_id, hook_index_str = ligature_key.split('_', 2)
        hook_index = int(hook_index_str)

        for ligature in self.current_dto.ligatures:
            if (ligature.start_vertex_id == vertex_id and
                ligature.end_edge_id == edge_id and
                ligature.end_hook_index == hook_index):
                ligature.path_points = new_path
                break


# === ORGANON COMMANDS (Visualization & Exploration) ===

class OrganonCommands:
    """
    High-level commands for Organon (Visualization & Exploration).

    These commands manipulate view state without changing the underlying EGI model.
    """

    @staticmethod
    def zoom_to_element(controller: DiagramController, element_id: str, zoom_level: float = 2.0) -> bool:
        """
        Zoom camera to focus on specific element.

        This is a view-only operation that doesn't modify the EGI model.
        """
        # Implementation would depend on GUI framework
        # For now, this is a placeholder for the command pattern
        print(f"Zooming to element {element_id} at level {zoom_level}")
        return True

    @staticmethod
    def pan_view(controller: DiagramController, delta_x: float, delta_y: float) -> bool:
        """
        Pan the camera view.

        This is a view-only operation that doesn't modify the EGI model.
        """
        print(f"Panning view by ({delta_x}, {delta_y})")
        return True

    @staticmethod
    def highlight_subgraph(controller: DiagramController, element_ids: List[str]) -> bool:
        """
        Highlight specific elements in the view.

        This modifies the style/appearance but not the underlying EGI model.
        """
        if not controller.current_dto:
            return False

        # Update DTO styling to highlight elements
        highlight_style = {'stroke_width': 3.0, 'stroke_color': 'red'}

        for element_id in element_ids:
            # Find and highlight vertices
            for vertex in controller.current_dto.vertices:
                if vertex.id == element_id:
                    vertex.style.update(highlight_style)

            # Find and highlight edges
            for edge in controller.current_dto.edge_labels:
                if edge.id == element_id:
                    edge.style.update(highlight_style)

        print(f"Highlighted {len(element_ids)} elements")
        return True

    @staticmethod
    def toggle_collapsed_view(controller: DiagramController, cut_id: str) -> bool:
        """
        Toggle collapsed/expanded view of a cut area.

        This modifies view state, not the EGI model itself.
        """
        # Implementation would track collapsed state and modify DTO accordingly
        print(f"Toggling collapsed view for cut {cut_id}")
        return True


# === ERGASTERION COMMANDS (Learning & Practice) ===

class ErgasterionCommands:
    """
    High-level commands for Ergasterion (Learning & Practice).

    These commands apply formal transformation rules to modify the EGI model.
    """

    @staticmethod
    def create_practice_graph(controller: DiagramController, egif_string: str) -> bool:
        """
        Create a new EGI from EGIF string for practice.

        This loads a new EGI model for learning exercises.
        """
        try:
            # Parse EGIF string into EGI model
            from egif_parser_dau import parse_egif
            new_egi = parse_egif(egif_string)

            # Load into controller
            return controller.load_egi(new_egi)

        except Exception as e:
            print(f"Failed to create practice graph: {e}")
            return False

    @staticmethod
    def apply_practice_rule(controller: DiagramController, rule_name: str,
                          selection_ids: List[str], target_area: str = None) -> bool:
        """
        Apply a formal rule in practice mode.

        This is the core learning interaction - applying rules to practice EGIs.
        """
        return controller.apply_formal_rule(rule_name, selection_ids, target_area)

    @staticmethod
    def validate_rule_application(controller: DiagramController, rule_name: str,
                                selection_ids: List[str], target_area: str = None) -> Dict[str, Any]:
        """
        Validate if a rule can be applied without actually applying it.

        Useful for providing feedback during learning.
        """
        if not controller.egi_model:
            return {"valid": False, "error": "No EGI loaded"}

        if rule_name not in controller._transformation_rules:
            return {"valid": False, "error": f"Unknown rule: {rule_name}"}

        # Create context for validation
        selected_subgraph = frozenset(selection_ids)
        if target_area is None:
            target_area = controller.egi_model.sheet

        polarity, nesting_depth = controller._calculate_area_polarity(target_area)

        context = TransformationContext(
            source_egi=controller.egi_model,
            target_area=target_area,
            selected_subgraph=selected_subgraph,
            area_polarity=polarity,
            nesting_depth=nesting_depth
        )

        # Validate preconditions
        rule = controller._transformation_rules[rule_name]
        is_valid, error_msg = rule.check_preconditions(context)

        return {
            "valid": is_valid,
            "error": error_msg,
            "rule_name": rule_name,
            "selection": selection_ids,
            "target_area": target_area
        }


# === AGON COMMANDS (Formal Interaction & Gameplay) ===

class AgonCommands:
    """
    High-level commands for Agon (Formal Interaction & Gameplay).

    These commands implement Peirce's Endoporeutic Game and formal reasoning.
    """

    @staticmethod
    def assert_fact(controller: DiagramController, fact_egi: RelationalGraphWithCuts,
                   parent_area: str = None) -> bool:
        """
        Assert a new fact by juxtaposing it with the main EGI.

        This adds a fact to the "Universe of Discourse" via juxtaposition.
        """
        if not controller.egi_model:
            return False

        # Use juxtaposition to combine the fact EGI with the main EGI
        # This is a simplified implementation - full version would handle complex merging

        if parent_area is None:
            parent_area = controller.egi_model.sheet

        # For now, we'll use insertion rule to add the fact
        # In full implementation, this would be more sophisticated juxtaposition logic

        print(f"Asserting fact in area {parent_area}")
        return True

    @staticmethod
    def propose_proof_step(controller: DiagramController, rule_name: str,
                          selection_ids: List[str], target_area: str = None) -> Dict[str, Any]:
        """
        Propose a proof step in the Endoporeutic Game.

        This validates a rule application and provides strategic feedback.
        """
        # Validate the rule application
        validation = ErgasterionCommands.validate_rule_application(
            controller, rule_name, selection_ids, target_area
        )

        if validation["valid"]:
            # Apply the transformation
            success = controller.apply_formal_rule(rule_name, selection_ids, target_area)

            if success:
                validation.update({
                    "applied": True,
                    "step_type": "successful_proof_step"
                })
            else:
                validation.update({
                    "applied": False,
                    "step_type": "failed_proof_step"
                })
        else:
            validation.update({
                "applied": False,
                "step_type": "invalid_proof_step"
            })

        return validation

    @staticmethod
    def check_endgame_condition(controller: DiagramController) -> Dict[str, Any]:
        """
        Check if the current EGI represents a completed proof or goal state.

        This analyzes the current state for endgame conditions in the Endoporeutic Game.
        """
        if not controller.egi_model:
            return {"game_over": False, "reason": "No EGI loaded"}

        # Check for various endgame conditions
        # This is a simplified implementation - full version would have sophisticated logic

        # Example: Check if sheet of assertion is empty (all proven)
        sheet_contents = controller.egi_model.area.get(controller.egi_model.sheet, frozenset())
        if not sheet_contents:
            return {
                "game_over": True,
                "result": "proof_complete",
                "reason": "Sheet of assertion is empty - all assertions proven"
            }

        # Example: Check for contradictions or impossible states
        # This would involve sophisticated logical analysis

        return {
            "game_over": False,
            "result": "game_continues",
            "reason": "Game continues - no endgame condition met"
        }


# === COMMAND PATTERN INTEGRATION ===

class Command:
    """Base class for all diagram commands in the layered architecture."""

    def execute(self, controller: DiagramController) -> bool:
        """Execute the command on the controller."""
        raise NotImplementedError

    def undo(self, controller: DiagramController) -> bool:
        """Undo the command (if supported)."""
        raise NotImplementedError

    def get_description(self) -> str:
        """Get human-readable description of the command."""
        return f"{self.__class__.__name__}"


class LoadEGICommand(Command):
    """Command to load a new EGI model."""

    def __init__(self, egi: RelationalGraphWithCuts, style: Optional[StyleSpecification] = None):
        self.egi = egi
        self.style = style
        self.previous_egi = None
        self.previous_deltas = None

    def execute(self, controller: DiagramController) -> bool:
        # Save current state for undo
        self.previous_egi = controller.egi_model
        self.previous_deltas = controller.layout_deltas.copy()

        # Execute the load
        return controller.load_egi(self.egi, self.style)

    def undo(self, controller: DiagramController) -> bool:
        if self.previous_egi:
            controller.egi_model = self.previous_egi
            controller.layout_deltas = self.previous_deltas
            controller._trigger_full_relayout()
            return True
        return False

    def get_description(self) -> str:
        return f"Load EGI with {len(self.egi.V)} vertices and {len(self.egi.E)} edges"


class ApplyRuleCommand(Command):
    """Command to apply a formal transformation rule."""

    def __init__(self, rule_name: str, selection_ids: List[str], target_area: Optional[str] = None):
        self.rule_name = rule_name
        self.selection_ids = selection_ids
        self.target_area = target_area
        self.previous_egi = None
        self.previous_deltas = None

    def execute(self, controller: DiagramController) -> bool:
        # Save current state for undo
        self.previous_egi = controller.egi_model
        self.previous_deltas = controller.layout_deltas.copy()

        # Execute the rule
        return controller.apply_formal_rule(self.rule_name, self.selection_ids, self.target_area)

    def undo(self, controller: DiagramController) -> bool:
        if self.previous_egi:
            controller.egi_model = self.previous_egi
            controller.layout_deltas = self.previous_deltas
            controller._trigger_full_relayout()
            return True
        return False

    def get_description(self) -> str:
        return f"Apply {self.rule_name} rule to {len(self.selection_ids)} selected elements"


class UpdatePositionCommand(Command):
    """Command to update element position."""

    def __init__(self, element_id: str, new_position: Tuple[float, float]):
        self.element_id = element_id
        self.new_position = new_position
        self.old_position = None

    def execute(self, controller: DiagramController) -> bool:
        # Save old position for undo
        if controller.current_dto:
            if controller._is_vertex_element(self.element_id):
                vertex = next((v for v in controller.current_dto.vertices if v.id == self.element_id), None)
                if vertex:
                    self.old_position = vertex.pos
            elif controller._is_edge_element(self.element_id):
                edge = next((e for e in controller.current_dto.edge_labels if e.id == self.element_id), None)
                if edge:
                    self.old_position = (edge.rect.x, edge.rect.y)

        # Execute the position update
        return controller.update_element_position(self.element_id, self.new_position)

    def undo(self, controller: DiagramController) -> bool:
        if self.old_position:
            return controller.update_element_position(self.element_id, self.old_position)
        return False

    def get_description(self) -> str:
        return f"Move {self.element_id} to position {self.new_position}"


class UpdatePathCommand(Command):
    """Command to update ligature path."""

    def __init__(self, ligature_key: str, new_path: List[Tuple[float, float]]):
        self.ligature_key = ligature_key
        self.new_path = new_path
        self.old_path = None

    def execute(self, controller: DiagramController) -> bool:
        # Save old path for undo
        if controller.current_dto:
            vertex_id, edge_id, hook_index_str = self.ligature_key.split('_', 2)
            hook_index = int(hook_index_str)

            for ligature in controller.current_dto.ligatures:
                if (ligature.start_vertex_id == vertex_id and
                    ligature.end_edge_id == edge_id and
                    ligature.end_hook_index == hook_index):
                    self.old_path = ligature.path_points.copy()
                    break

        # Execute the path update
        return controller.update_ligature_path(self.ligature_key, self.new_path)

    def undo(self, controller: DiagramController) -> bool:
        if self.old_path:
            return controller.update_ligature_path(self.ligature_key, self.old_path)
        return False

    def get_description(self) -> str:
        return f"Update path for ligature {self.ligature_key}"


# === DIAGRAM CONTROLLER WITH COMMAND EXECUTOR ===

class CommandExecutor:
    """Executes commands and manages command history for undo/redo."""

    def __init__(self, controller: DiagramController):
        self.controller = controller
        self.command_history: List[Command] = []
        self.undo_stack: List[Command] = []
        self.max_history = 100

    def execute_command(self, command: Command) -> bool:
        """Execute a command and add to history."""
        if command.execute(self.controller):
            self.command_history.append(command)
            self.undo_stack.clear()  # Clear redo stack on new command

            # Limit history size
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)

            return True
        return False

    def undo_last_command(self) -> bool:
        """Undo the last executed command."""
        if not self.command_history:
            return False

        command = self.command_history.pop()
        if command.undo(self.controller):
            self.undo_stack.append(command)
            return True
        return False

    def redo_last_undo(self) -> bool:
        """Redo the last undone command."""
        if not self.undo_stack:
            return False

        command = self.undo_stack.pop()
        if command.execute(self.controller):
            self.command_history.append(command)
            return True
        return False

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.command_history) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.undo_stack) > 0


# === INTEGRATION EXAMPLE ===

def demonstrate_layered_architecture():
    """
    Demonstrate how the layered architecture works with the Command pattern.
    """
    from egif_parser_dau import parse_egif

    # Initialize controller
    controller = DiagramController()

    # Create command executor for undo/redo support
    executor = CommandExecutor(controller)

    # Example: Load an initial EGI (Organon command)
    initial_egif = """[*v1] (P v1)"""

    try:
        initial_egi = parse_egif(initial_egif)
        load_cmd = LoadEGICommand(initial_egi)
        executor.execute_command(load_cmd)
        print("✓ Loaded initial EGI")

        # Example: Apply a formal rule (Ergasterion command)
        rule_cmd = ApplyRuleCommand("DC+", ["v1", "e1"], "T")
        executor.execute_command(rule_cmd)
        print("✓ Applied DC+ rule")

        # Example: Update position (aesthetic command)
        pos_cmd = UpdatePositionCommand("v1", (100.0, 150.0))
        executor.execute_command(pos_cmd)
        print("✓ Updated vertex position")

        # Example: Undo the position change
        executor.undo_last_command()
        print("✓ Undid position change")

        # Example: Redo the position change
        executor.redo_last_undo()
        print("✓ Redid position change")

        print(f"\nFinal state: {len(controller.layout_deltas)} user constraints")
        print(f"Command history: {len(executor.command_history)} commands")
        print(f"Undo stack: {len(executor.undo_stack)} commands")

    except Exception as e:
        print(f"Demonstration failed: {e}")


if __name__ == "__main__":
    demonstrate_layered_architecture()
