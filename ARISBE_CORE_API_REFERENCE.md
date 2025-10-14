# Arisbe Core API Reference

**Last Updated**: 2025-10-14 05:56:09  
**Auto-Generated**: This file is automatically regenerated when core modules change

---

## Overview

This document provides complete API documentation for Arisbe's protected core modules.
These modules form the mathematical foundation validated by 90 core tests.

**Protected Modules**: Changes require explicit authorization (`export ARISBE_CORE_OVERRIDE=true`)

---

## diagram_controller.py

**Path**: `src/diagram_controller.py`  
**Status**: Protected Core Module

### Module Description

DiagramController - Central coordinator for EGI diagramming application.

This controller implements the layered architecture separating "what" (use case logic)
from "how" (diagram manipulation). It manages state, validates operations, and
coordinates between the EGI model, layout engine, and GUI.

Architecture:
- DiagramController (The "How"): Low-level operations on EGI model and layout
- Use Case Logic (The "What"): High-level commands in Organon/Ergasterion/Agon

### Classes

#### `ValidationResult`

Result of validating a user action.


#### `DiagramState`

A single state in the diachronic sequence of a Universe of Discourse.

Each state is a pair: (EGI_n, LayoutDeltas_n)
- EGI_n: The logical structure at this point in the transformation sequence
- LayoutDeltas_n: User aesthetic constraints applied to this state

The deltas from state n become the starting point for state n+1 after reconciliation.


#### `DiagramController`

Central controller for EGI diagramming application.

Manages the complete application state and coordinates between:
- EGI model (logical structure)
- Layout engine (visual layout with user constraints)
- GUI (user interactions and rendering)

**Methods**:

- `__init__(self)`
  Initialize the diagram controller with default components.

- `enable_transformation_history(self, initial_description)`
  Enable transformation history tracking with layout deltas.
  
  This enables the diachronic workflow where each state is tracked as
  (EGI_n, LayoutDeltas_n) with delta reconciliation across transformations.

- `load_egi(self, egi, style)`
  Load a new EGI model and initialize the controller state.
  
  Args:
      egi: The EGI model to load
      style: Optional style specification (defaults to Dau style)
  
  Returns:
      True if successfully loaded, False otherwise

- `get_renderable_dto(self)`
  Get the current renderable layout for GUI display.
  
  Returns:
      Current LayoutDTO or None if no model loaded

- `get_egi_model(self)`
  Get the current EGI model.

- `get_layout_deltas(self)`
  Get current user-defined layout constraints.

- `apply_formal_rule(self, rule_name, selection_ids, target_area)`
  Apply a formal transformation rule to the current EGI.
  
  Args:
      rule_name: Name of the rule to apply (DC+, DC-, INS, ERA, IT+, IT-)
      selection_ids: List of element IDs selected for transformation
      target_area: Target area for the transformation (defaults to sheet)
  
  Returns:
      True if transformation applied successfully, False otherwise

- `update_element_position(self, element_id, new_position)`
  Update position of a vertex or edge label with validation.
  
  Args:
      element_id: ID of element to move
      new_position: New (x, y) position
  
  Returns:
      True if position updated, False if validation failed

- `update_ligature_path(self, ligature_key, new_path)`
  Update custom path for a ligature with validation.
  
  Args:
      ligature_key: Unique key identifying the ligature (format: "vertex_id_edge_id_hook_index")
      new_path: New path points for the ligature
  
  Returns:
      True if path updated, False if validation failed

- `_trigger_full_relayout(self)`
  Trigger complete re-layout after logical changes.
  
  SIMPLIFIED: Just call the unified D3 engine once with all context.
  The engine handles everything: sizing, positioning, containment.

- `_trigger_fast_update(self)`
  Fast path: Update DTO directly without re-layout.
  Only updates positions and recalculates affected ligatures.

- `_recalculate_ligatures_for_vertex(self, vertex_id)`
  Recalculate all ligatures connected to a vertex.

- `_recalculate_ligatures_for_predicate(self, predicate_id)`
  Recalculate all ligatures connected to a predicate.

- `_get_predicate_label(self, predicate_id)`
  Get the label text for a predicate.

- `_calculate_boundary_point(self, box_center, box_width, box_height, target_point)`
  Calculate the point on a box's boundary closest to a target point.
  Box is centered at box_center with given width and height.

- `_preserve_valid_constraints(self)`
  Preserve user constraints that are still valid after transformation.

- `_element_exists_in_model(self, element_id)`
  Check if element still exists in current EGI model.

- `_is_vertex_element(self, element_id)`
  Check if element is a vertex.

- `_record_transformation_with_deltas(self, rule_name, context, result, old_deltas, new_deltas)`
  Record transformation in history with layout delta information.
  
  This implements the diachronic workflow where each state includes both
  the logical structure (EGI) and aesthetic constraints (layout deltas).
  
  The history records:
  - State_n: (EGI_n, Deltas_n) - before transformation
  - State_n+1: (EGI_n+1, Deltas_n+1) - after transformation + reconciliation

- `_is_edge_element(self, element_id)`
  Check if element is an edge.

- `_is_cut_element(self, element_id)`
  Check if element is a cut.

- `_validate_egi_model(self, egi)`
  Validate that EGI model is well-formed.

- `_calculate_area_polarity(self, area_id)`
  Calculate polarity and nesting depth of an area.

- `_validate_element_position(self, element_id, new_position)`
  Validate that a new element position is within logical bounds.

- `_validate_ligature_path(self, ligature_key, new_path)`
  Validate that a custom ligature path is collision-free and logically valid.

- `_validate_area_containment(self, element_id, new_position, element_type)`
  Validate that element stays within its logical area (EGI.area mapping).
  
  This enforces Dau's iron-clad principle: elements cannot escape their assigned areas.

- `_find_logical_area_for_element(self, element_id)`
  Find the logical area containing an element.

- `_element_in_area_rect(self, element_id, area_rect)`
  Check if element is visually within an area rectangle.

- `_point_in_rect(self, point, rect)`
  Check if point is within rectangle.

- `_point_in_rect_with_padding(self, point, rect, padding)`
  Check if point is within rectangle with padding.

- `_rect_in_rect(self, inner_rect, outer_rect)`
  Check if inner rectangle is within outer rectangle.

- `_positions_approximately_equal(self, pos1, pos2, tolerance)`
  Check if two positions are approximately equal within tolerance.

- `_get_edge_label_center(self, edge_label)`
  Get center point of edge label.

- `_path_collides_with_obstacles(self, path, dto)`
  Check if path collides with any diagram elements.

- `_point_in_circle(self, point, center, radius)`
  Check if point is within circle.

- `_path_respects_logical_areas(self, path)`
  Check if path respects logical area boundaries (simplified).

- `_update_ligature_path_in_dto(self, ligature_key, new_path)`
  Update ligature path directly in current DTO.


#### `OrganonCommands`

High-level commands for Organon (Visualization & Exploration).

These commands manipulate view state without changing the underlying EGI model.

**Methods**:

- `zoom_to_element(controller, element_id, zoom_level)`
  Zoom camera to focus on specific element.
  
  This is a view-only operation that doesn't modify the EGI model.

- `pan_view(controller, delta_x, delta_y)`
  Pan the camera view.
  
  This is a view-only operation that doesn't modify the EGI model.

- `highlight_subgraph(controller, element_ids)`
  Highlight specific elements in the view.
  
  This modifies the style/appearance but not the underlying EGI model.

- `toggle_collapsed_view(controller, cut_id)`
  Toggle collapsed/expanded view of a cut area.
  
  This modifies view state, not the EGI model itself.


#### `ErgasterionCommands`

High-level commands for Ergasterion (Learning & Practice).

These commands apply formal transformation rules to modify the EGI model.

**Methods**:

- `create_practice_graph(controller, egif_string)`
  Create a new EGI from EGIF string for practice.
  
  This loads a new EGI model for learning exercises.

- `apply_practice_rule(controller, rule_name, selection_ids, target_area)`
  Apply a formal rule in practice mode.
  
  This is the core learning interaction - applying rules to practice EGIs.

- `validate_rule_application(controller, rule_name, selection_ids, target_area)`
  Validate if a rule can be applied without actually applying it.
  
  Useful for providing feedback during learning.


#### `AgonCommands`

High-level commands for Agon (Formal Interaction & Gameplay).

These commands implement Peirce's Endoporeutic Game and formal reasoning.

**Methods**:

- `assert_fact(controller, fact_egi, parent_area)`
  Assert a new fact by juxtaposing it with the main EGI.
  
  This adds a fact to the "Universe of Discourse" via juxtaposition.

- `propose_proof_step(controller, rule_name, selection_ids, target_area)`
  Propose a proof step in the Endoporeutic Game.
  
  This validates a rule application and provides strategic feedback.

- `check_endgame_condition(controller)`
  Check if the current EGI represents a completed proof or goal state.
  
  This analyzes the current state for endgame conditions in the Endoporeutic Game.


#### `Command`

Base class for all diagram commands in the layered architecture.

**Methods**:

- `execute(self, controller)`
  Execute the command on the controller.

- `undo(self, controller)`
  Undo the command (if supported).

- `get_description(self)`
  Get human-readable description of the command.


#### `LoadEGICommand`

Command to load a new EGI model.

**Methods**:

- `__init__(self, egi, style)`

- `execute(self, controller)`

- `undo(self, controller)`

- `get_description(self)`


#### `ApplyRuleCommand`

Command to apply a formal transformation rule.

**Methods**:

- `__init__(self, rule_name, selection_ids, target_area)`

- `execute(self, controller)`

- `undo(self, controller)`

- `get_description(self)`


#### `UpdatePositionCommand`

Command to update element position.

**Methods**:

- `__init__(self, element_id, new_position)`

- `execute(self, controller)`

- `undo(self, controller)`

- `get_description(self)`


#### `UpdatePathCommand`

Command to update ligature path.

**Methods**:

- `__init__(self, ligature_key, new_path)`

- `execute(self, controller)`

- `undo(self, controller)`

- `get_description(self)`


#### `CommandExecutor`

Executes commands and manages command history for undo/redo.

**Methods**:

- `__init__(self, controller)`

- `execute_command(self, command)`
  Execute a command and add to history.

- `undo_last_command(self)`
  Undo the last executed command.

- `redo_last_undo(self)`
  Redo the last undone command.

- `can_undo(self)`
  Check if undo is available.

- `can_redo(self)`
  Check if redo is available.


### Functions

#### `demonstrate_layered_architecture()`

Demonstrate how the layered architecture works with the Command pattern.


---

## egi_core_dau.py

**Path**: `src/egi_core_dau.py`  
**Status**: Protected Core Module

### Module Description

Dau-compliant Existential Graph Instance (EGI) core implementation.
Follows Frithjof Dau's exact 6+1 component definition from "Mathematical Logic with Diagrams".

This implementation replaces the previous "Context" model with Dau's formal:
- 6-component Relational Graph with Cuts: (V, E, ν, ⊤, Cut, area)
- 7th component: rel mapping for relation names
- Proper area/context distinction for diagram generation
- Support for isolated vertices ("heavy dots")

### Classes

#### `Vertex`

Vertex in Dau's formalism - can be generic (*x) or constant ("Socrates").

**Methods**:

- `__post_init__(self)`


#### `Edge`

Edge in Dau's formalism - represents a relation with incident vertices.


#### `Cut`

Cut in Dau's formalism - represents negation context.


#### `RelationalGraphWithCuts`

Dau's exact 6+1 component definition of Relational Graph with Cuts.

Components (Definition 12.1):
1. V - finite set of vertices
2. E - finite set of edges
3. ν - mapping from edges to vertex sequences
4. ⊤ - sheet of assertion (single element)
5. Cut - finite set of cuts
6. area - mapping defining containment
7. rel - mapping from edges to relation names (7th component)

Constraints:
- V, E, Cut are pairwise disjoint
- ⊤ ∉ V ∪ E ∪ Cut
- area satisfies all formal constraints from Definition 12.1

**Methods**:

- `__post_init__(self)`
  Validate Dau's formal constraints and build derived mappings.

- `_build_hierarchical_index(self, hierarchical_index)`
  Build hierarchical index from area mapping.

- `_validate_dau_constraints(self)`
  Validate all constraints from Dau's Definition 12.1.

- `_validate_area_constraints(self)`
  Validate area mapping constraints from Definition 12.1.

- `_has_area_cycle(self, start_context, visited)`
  Check if context has cycle in area containment.

- `_validate_alphabet_and_rho(self)`
  If an AlphabetDAU is provided, validate arities, membership, and rho labels.
  This keeps the core backward compatible by making these checks conditional.

- `get_vertex(self, vertex_id)`
  Get vertex by ID.

- `get_edge(self, edge_id)`
  Get edge by ID.

- `get_cut(self, cut_id)`
  Get cut by ID.

- `get_relation_name(self, edge_id)`
  Get relation name for edge.

- `get_incident_vertices(self, edge_id)`
  Get incident vertices for edge via ν mapping.

- `get_area(self, context_id)`
  Get area of context - direct contents only (non-recursive).

- `get_context(self, element_id)`
  Get the context that directly contains this element.

- `get_full_context(self, context_id)`
  Get full context of a cut - all elements it contributes to SoA (recursive).
  This is Dau's context concept: ⋃ area^n(c) for all n.

- `get_nesting_depth(self, element_id)`
  Get nesting depth of element (number of cuts enclosing it).

- `is_evenly_enclosed(self, element_id)`
  Check if element is evenly enclosed (Dau's Definition 12.4).

- `is_oddly_enclosed(self, element_id)`
  Check if element is oddly enclosed (Dau's Definition 12.4).

- `is_positive_context(self, context_id)`
  Check if context is positive (sheet or oddly enclosed cut).

- `is_negative_context(self, context_id)`
  Check if context is negative (evenly enclosed cut).

- `get_hooks(self, edge_id)`
  Get all hooks for an edge as (edge_id, position) pairs.

- `get_vertex_at_hook(self, edge_id, position)`
  Get vertex attached to hook (edge_id, position).

- `get_vertex_hooks(self, vertex_id)`
  Get all hooks that vertex is attached to.

- `is_branching_point(self, vertex_id)`
  Check if vertex is a branching point (attached to more than 2 hooks).

- `get_branch_count(self, vertex_id)`
  Get number of branches (hooks) for vertex.

- `get_all_elements(self)`
  Get all element IDs in the EGI (vertices, edges, cuts).

- `replace_vertex_on_hook(self, edge_id, position, new_vertex_id)`
  Replace vertex on hook (edge_id, position) with new vertex (Definition 12.9).

- `get_identity_edges(self)`
  Get all identity edges (edges with relation name '=').

- `get_ligature_graph(self)`
  Get ligature graph (V, Eid) as vertex set and edge pairs.

- `get_identity_edge_as_set(self, edge_id)`
  Get identity edge as unordered set {v1, v2} per Dau's suggestion.

- `get_ligatures(self)`
  Get all ligatures as connected components of identity edges.

- `get_vertex_ligature(self, vertex_id)`
  Get the ligature containing the specified vertex.

- `is_vertex_isolated(self, vertex_id)`
  Check if vertex is isolated (not incident to any edge).

- `get_isolated_vertices(self)`
  Get all isolated vertices.

- `has_dominating_nodes(self)`
  Check if graph has dominating nodes (Dau's Definition 12.5).

- `_context_dominates(self, context1, context2)`
  Check if context1 ≤ context2 in Dau's ordering.

- `with_vertex(self, vertex)`
  Create new graph with additional vertex in sheet of assertion.

- `with_vertex_in_context(self, vertex, context_id)`
  Create new graph with additional vertex in specified context.

- `with_edge(self, edge, vertex_sequence, relation_name, context_id)`
  Create new graph with additional edge.

- `apply_isomorphism(self, vertex_mapping, edge_mapping, cut_mapping)`
  Apply isomorphism transformation (Definition 12.14).

- `change_identity_edge_orientation(self, edge_id)`
  Change orientation of identity edge (Definition 12.14).

- `add_vertex_to_ligature(self, edge_id, hook_position, new_vertex, context_id)`
  Add vertex to ligature (Definition 12.14).

- `remove_vertex_from_ligature(self, vertex_id)`
  Remove vertex from ligature (reverse of add_vertex_to_ligature).

- `with_cut(self, cut, context_id)`
  Create new graph with additional cut.

- `with_vertex_moved_to_context(self, vertex_id, new_context_id)`
  Return a new graph with the given vertex relocated to a different context.
  Preserves all other components; validates that vertex exists and context exists.

- `without_element(self, element_id)`
  Create new graph without specified element.

- `_without_vertex(self, vertex_id)`
  Remove vertex and update area mappings.

- `_without_edge(self, edge_id)`
  Remove edge and update mappings.

- `_without_cut(self, cut_id)`
  Remove cut and redistribute its contents.


#### `Alphabet`

Manages variable naming for EGIF generation.

**Methods**:

- `__init__(self)`

- `get_fresh_name(self)`
  Get fresh variable name.

- `reserve_name(self, name)`
  Reserve a variable name.


#### `AlphabetDAU`

Dau's Alphabet (C, F, R, ar). Use with RelationalGraphWithCuts to enable
arity and membership validations. Set ar(c)=1 implicitly for c∈C unless provided.

**Methods**:

- `with_defaults(self)`
  Return a copy where all constants have arity 1 in ar if not already set.


### Functions

#### `create_empty_graph()`

Create empty graph (Dau's G_∅).


#### `create_vertex(label, is_generic)`

Create new vertex with unique ID.


#### `create_edge()`

Create new edge with unique ID.


#### `create_cut()`

Create new cut with unique ID.


---

## egi_io.py

**Path**: `src/egi_io.py`  
**Status**: Protected Core Module

### Module Description

EGI JSON serialization utilities.

Schema produced/consumed matches tools/migrate_corpus_to_egi.py 
egi_to_dict.

### Functions

#### `to_dict(egi)`


#### `from_dict(d)`


#### `load_egi_json(path)`


#### `save_egi_json(egi, path)`


---

## unified_d3_engine.py

**Path**: `src/unified_d3_engine.py`  
**Status**: Protected Core Module

### Module Description

Unified D3 Layout Engine - DEFINITIVE RECURSIVE ARCHITECTURE

PURE BOTTOM-UP RECURSION:
- Python orchestrates recursive traversal of cut hierarchy
- Each D3 call solves ONE cut's layout (simple, self-contained)
- Child cuts become fixed-size obstacles in parent simulations
- No post-processing, no multi-phase conflicts, pure separation

Author: Definitive architecture implementation
Date: 2025-10-12

### Classes

#### `Point`

2D point.


#### `BoundingBox`

Axis-aligned bounding box.

**Methods**:

- `width(self)`

- `height(self)`

- `center(self)`


#### `LigaturePath`

Path for a ligature connection.


#### `LayoutDTO`

Platform-independent layout result.


#### `UnifiedD3Engine`

Definitive Recursive Bottom-Up Layout Engine.

ARCHITECTURE:
1. Build cut hierarchy from EGI.area
2. Find leaf cuts (no child cuts)
3. Layout leaves first (call D3 with simple content only)
4. Work up hierarchy: layout each parent with child cuts as obstacles

**Methods**:

- `__init__(self)`
  Initialize layout engine.

- `generate_layout(self, egi, style, layout_deltas)`
  Generate layout using recursive bottom-up approach.
  
  Args:
      egi: The EGI model to layout
      style: Style specification
      layout_deltas: User-defined position overrides
  
  Returns:
      Complete LayoutDTO ready for rendering

- `_calculate_sizes(self, egi, style)`
  Calculate sizes for all non-cut elements.

- `_build_cut_hierarchy(self, egi)`
  Build cut hierarchy: which cuts are children of which cuts.
  
  Returns:
      Dict mapping cut_id -> list of child cut IDs

- `_print_hierarchy(self, hierarchy, egi)`
  Print cut hierarchy for debugging.

- `_layout_recursively(self, cut_id, egi, style, hierarchy, layout_deltas)`
  Recursively layout a cut and all its children (bottom-up).
  
  Base case: Leaf cut (no child cuts) - layout simple content
  Recursive case: Layout children first, then layout this cut with children as obstacles

- `_translate_cut_and_descendants(self, cut_id, offset_x, offset_y, egi)`
  Recursively translate a cut and all its descendants by (offset_x, offset_y).
  
  This is needed when a child cut is repositioned in parent layout - we must
  move the cut's content AND all its child cuts (and their content, recursively).

- `_layout_single_cut(self, cut_id, vertices, predicates, child_cut_ids, egi, style, layout_deltas)`
  Call D3 worker to layout ONE cut's contents.
  
  Returns:
      (positions dict, tight bounding box)

- `_call_d3_worker(self, payload)`
  Call D3 worker subprocess.

- `_circle_boundary_point(self, cx, cy, radius, target_x, target_y)`
  Calculate point on circle boundary toward target.

- `_rect_boundary_point(self, rect_cx, rect_cy, rect_w, rect_h, target_x, target_y)`
  Calculate point on rectangle boundary toward target (from center).

- `_build_dto(self, egi, style)`
  Build final LayoutDTO from recursively calculated positions.


---

## Usage Notes

### Import Patterns
```python
# Recommended import style
from module_name import function_name
from module_name import ClassName

# Not: from src.module_name import ...
```

### Immutability
EGI model is immutable. Use `.with_*()` methods:
```python
# Correct
new_egi = egi.with_vertex(vertex)

# Incorrect
egi.add_vertex(vertex)  # No such method
```

### Error Handling
Always check return values and handle None cases:
```python
result = transform_egi(egi, rule)
if result is None:
    # Handle transformation failure
    pass
```

---

*For usage examples, see `CORE_API_USAGE_GUIDE.md`*
