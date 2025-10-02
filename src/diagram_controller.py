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
from definitive_egi_layout_engine import (
    DefinitiveEGILayoutEngine,
    LayoutDeltas,
    LayoutDelta,
    LayoutDTO,
    RenderableVertex,
    RenderableEdgeLabel,
    RenderableLigature
)

# Style system
from style_loader import StyleLoader, StyleSpecification

# Formal transformation rules
from formal_transformation_rules import (
    FormalTransformationRule,
    TransformationContext,
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


class DiagramController:
    """
    Central controller for EGI diagramming application.

    Manages the complete application state and coordinates between:
    - EGI model (logical structure)
    - Layout engine (visual layout with user constraints)
    - GUI (user interactions and rendering)
    """

    def __init__(self):
        """Initialize the diagram controller with default components."""
        self.layout_engine = DefinitiveEGILayoutEngine()
        self.style_loader = StyleLoader()
        self.current_style: Optional[StyleSpecification] = None
        self.layout_deltas: Dict[str, LayoutDelta] = {}
        self.current_dto: Optional[LayoutDTO] = None

        # EGI model state
        self.egi_model: Optional[RelationalGraphWithCuts] = None

        # Formal transformation rules
        self._transformation_rules: Dict[str, FormalTransformationRule] = {
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
            "INS": InsertionRule(),
            "ERA": ErasureRule(),
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
        }

    # === PUBLIC API: STATE & VIEW MANAGEMENT ===

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
            # Validate the EGI model
            if not self._validate_egi_model(egi):
                return False

            # Set the new model and style
            self.egi_model = egi
            self.current_style = style or self.style_loader.load_default_style()

            # Clear all user constraints (fresh start)
            self.layout_deltas = {}

            # Generate initial layout
            self._trigger_full_relayout()

            return True

        except Exception as e:
            print(f"Failed to load EGI: {e}")
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
        is_valid, error_msg = rule.check_preconditions(context)

        if not is_valid:
            print(f"Rule validation failed: {error_msg}")
            return False

        # Apply transformation
        result = rule.apply_transformation(context)

        if not result.success:
            print(f"Transformation failed: {result.error_message}")
            return False

        # Update model and trigger re-layout
        self.egi_model = result.result_egi

        # Preserve user constraints that are still valid after transformation
        self._preserve_valid_constraints()

        # Trigger full re-layout with preserved constraints
        self._trigger_full_relayout()

        print(f"Successfully applied {rule_name} transformation")
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
        """Trigger complete re-layout after logical changes."""
        if not self.egi_model or not self.current_style:
            return

        # Convert layout_deltas dict to LayoutDeltas object
        deltas_obj = LayoutDeltas()
        deltas_obj.deltas = self.layout_deltas
        deltas_obj.deterministic_seed = 42  # Consistent layouts

        # Generate new layout
        self.current_dto = self.layout_engine.generate_layout(
            self.egi_model,
            self.current_style,
            deltas_obj
        )

    def _trigger_fast_update(self):
        """Trigger fast update for aesthetic changes only."""
        if not self.current_dto:
            return

        # For now, we'll do a full re-layout for simplicity
        # In a more optimized implementation, we could selectively update only affected elements
        self._trigger_full_relayout()

    def _preserve_valid_constraints(self):
        """Preserve user constraints that are still valid after transformation."""
        if not self.current_dto:
            return

        valid_deltas = {}

        for element_id, delta in self.layout_deltas.items():
            # Check if element still exists in the new model
            if self._element_exists_in_model(element_id):
                valid_deltas[element_id] = delta

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

    def _validate_egi_model(self, egi: RelationalGraphWithCuts) -> bool:
        """Validate that EGI model is well-formed."""
        try:
            # The EGI constructor already validates most constraints
            # We just need to ensure it has the required components
            if not egi.V or not egi.E:
                print("EGI must contain vertices and edges")
                return False

            return True

        except Exception as e:
            print(f"EGI validation failed: {e}")
            return False

    def _calculate_area_polarity(self, area_id: ElementID) -> Tuple[AreaPolarity, int]:
        """Calculate polarity and nesting depth of an area."""
        if not self.egi_model:
            return AreaPolarity.POSITIVE, 0

        # Sheet is always level 0, positive
        if area_id == self.egi_model.sheet:
            return AreaPolarity.POSITIVE, 0

        # For cut areas, count how many cuts enclose this area
        enclosing_cuts = 0
        current_area = area_id

        while True:
            # Find which area contains current_area
            containing_area = None
            for area_candidate, contents in self.egi_model.area.items():
                if current_area in contents:
                    containing_area = area_candidate
                    break

            if containing_area is None or containing_area == self.egi_model.sheet:
                break

            if any(cut.id == containing_area for cut in self.egi_model.Cut):
                enclosing_cuts += 1
                current_area = containing_area
            else:
                break

        nesting_depth = enclosing_cuts + 1
        polarity = AreaPolarity.POSITIVE if nesting_depth % 2 == 0 else AreaPolarity.NEGATIVE

        return polarity, nesting_depth

    def _validate_element_position(self, element_id: str, new_position: Tuple[float, float]) -> ValidationResult:
        """Validate that a new element position is within logical bounds."""
        if not self.current_dto:
            return ValidationResult(False, "No current layout available")

        # Find the element in current DTO
        if self._is_vertex_element(element_id):
            element = next((v for v in self.current_dto.vertices if v.id == element_id), None)
            if not element:
                return ValidationResult(False, f"Vertex {element_id} not found in current layout")

            # Get the logical area containing this vertex
            logical_area = self._find_logical_area_for_element(element_id)
            if not logical_area:
                return ValidationResult(False, f"Cannot determine logical area for vertex {element_id}")

            # Check if new position is within the logical area's bounds (with some padding)
            padding = 50  # pixels
            if not self._point_in_rect_with_padding(new_position, logical_area.rect, padding):
                return ValidationResult(
                    False,
                    f"Position ({new_position[0]}, {new_position[1]}) is outside logical area bounds",
                    "Try moving the element closer to its original logical area"
                )

        elif self._is_edge_element(element_id):
            element = next((e for e in self.current_dto.edge_labels if e.id == element_id), None)
            if not element:
                return ValidationResult(False, f"Edge {element_id} not found in current layout")

            # Get the logical area containing this edge
            logical_area = self._find_logical_area_for_element(element_id)
            if not logical_area:
                return ValidationResult(False, f"Cannot determine logical area for edge {element_id}")

            # Check if new position is within the logical area's bounds (with some padding)
            padding = 30  # pixels
            if not self._point_in_rect_with_padding(new_position, logical_area.rect, padding):
                return ValidationResult(
                    False,
                    f"Position ({new_position[0]}, {new_position[1]}) is outside logical area bounds",
                    "Try moving the edge closer to its original logical area"
                )

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
