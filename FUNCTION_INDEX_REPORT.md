# Arisbe Function Index Report

## O(1) Complexity Solutions
- **_load_tomos_index** (/Users/mjh/Sync/GitHub/Arisbe/src/corpus_integration.py:54)
  Load tomos items from the filesystem
- **_finalize_alphabet_and_rho** (/Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py:533)
  Compute AlphabetDAU (C,F,R,ar) and rho mapping from the parsed graph
- **_constant_name_for_vertex** (/Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:266)
  Resolve if a vertex is a constant and return its name
- **_format_constant** (/Users/mjh/Sync/GitHub/Arisbe/src/clif_generator_dau.py:290)
  Format a constant for CLIF output
- **create_insertion_subgraph** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:151)
  Create a subgraph for insertion based on specification
- **_is_constant_vertex** (/Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:153)
  Decide if vertex is a constant using rho when available, else legacy flags
- **_get_constant_name** (/Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:163)
- **_format_constant** (/Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py:171)
  Format constant for CGIF output: bare identifier if simple; otherwise quoted
- **_is_constant_vertex** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:362)
  Return True if the vertex is labeled as a constant via rho, or, for legacy graphs,
if the Vertex object is non-generic (has label/is_generic=False)
- **_constant_name** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py:375)
  Return the constant name for a vertex from rho if available, else from legacy Vertex
- **_build_hierarchical_index** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:128)
  Build hierarchical index from area mapping
- **with_defaults** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:1019)
  Return a copy where all constants have arity 1 in ar if not already set
- **load_index** (/Users/mjh/Sync/GitHub/Arisbe/src/tomos_index.py:48)
- **save_index** (/Users/mjh/Sync/GitHub/Arisbe/src/tomos_index.py:65)
- **_finalize_alphabet_and_rho** (/Users/mjh/Sync/GitHub/Arisbe/src/clif_parser_dau.py:373)
  Compute AlphabetDAU and rho from the graph, excluding relation-name collisions from constants
- **rename_vertex** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:557)
  Rename vertex and set/unset as constant with alphabet/rho updates
- **get_display_name** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_parsing_result.py:30)
  Get the display name for a vertex
- **_read_constant** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:127)
  Read quoted constant
- **_hoist_vertices_to_lca** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py:650)
  After parsing, relocate constant vertices to the LCA of their occurrences
- **create_focus_view** (/Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:164)
  Create a focused view showing elements around focus points
- **_build_hierarchical_index** (/Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:441)
  Build hierarchical index from EGI structure for O(1) lookups
- **_calculate_area_polarity_and_depth** (/Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:458)
  Calculate polarity and nesting depth using optimized hierarchical index
- **tagged_id** (/Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:30)
  Get the index-tagged element ID
- **lookup_concept** (/Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:101)
  Look up a concept by ID
- **lookup_concept_in_ontology** (/Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:409)
  Look up a concept in an external ontology
- **lookup_concept** (/Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:527)
- **lookup_concept** (/Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:542)
- **lookup_concept** (/Users/mjh/Sync/GitHub/Arisbe/src/domain_ontology_model.py:554)
- **add_area** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:43)
  Add an area to the hierarchical index
- **get_nesting_level** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:85)
  Get the nesting level of an area
- **get_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:90)
  Get the polarity of an area
- **get_parent** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:95)
  Get the parent area of an area
- **get_children** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:100)
  Get direct children of an area
- **get_statistics** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:182)
  Get statistics about the hierarchical index
- **load_corpus_data** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app_pyside6.py:220)
  Load tomos data from index into tree widget
- **load_index** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:55)
- **display_corpus_entry** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/arisbe_main_app.py:827)
  Display a tomos index entry
- **load_tomos_index** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:153)
  Load the tomos index from disk
- **save_tomos_index** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_navigator.py:184)
  Save the tomos index to disk
- **_load_corpus** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:100)
  Load tomos from index
- **_get_graph_type_from_entry** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:138)
  Determine graph type from index entry
- **_get_graph_status_from_entry** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:156)
  Determine graph status from index entry
- **add_graph_to_index** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/organon/corpus_panel.py:281)
  Add a new graph entry to the tomos index

## Polarity Calculation Functions
- **calculate_area_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:75)
  Calculate the polarity and nesting depth of an area
- **_calculate_area_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:107)
  Calculate polarity and nesting depth for an area
- **_calculate_area_polarity_and_depth** (/Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:458)
  Calculate polarity and nesting depth using optimized hierarchical index
- **polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:23)
  Calculate polarity from nesting level
- **get_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:90)
  Get the polarity of an area
- **get_positive_areas** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:130)
  Get all positive polarity areas
- **get_negative_areas** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:135)
  Get all negative polarity areas
- **get_current_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:592)
  Determine the polarity of the current context

## Hierarchical/Nesting Functions
- **_test_context_nesting_preservation** (/Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:443)
  Test Dau's Theorem: Context nesting is preserved by transformations

Reference: Dau Chapter 15, Context nesting constraints
Rationale: All transformations must preserve proper context nesting
- **_create_nested_context_test_egi** (/Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:603)
  Create EGI with nested contexts for nesting preservation testing
- **_compute_nesting_levels** (/Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:623)
  Compute nesting levels for all contexts in EGI
- **_validate_nesting_preservation** (/Users/mjh/Sync/GitHub/Arisbe/src/dau_theorem_correspondence_tests.py:640)
  Validate that nesting relationships are preserved
- **_cut_contains_cut** (/Users/mjh/Sync/GitHub/Arisbe/src/dau_diagram_correspondence.py:196)
  Check if outer_cut contains inner_cut in nesting hierarchy
- **calculate_area_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:75)
  Calculate the polarity and nesting depth of an area
- **_get_nesting_hierarchy** (/Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py:692)
  Get ordered list of areas from target_area up to sheet (nest of cuts)
- **_calculate_area_polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/egif_transformation_interface.py:107)
  Calculate polarity and nesting depth for an area
- **_has_area_cycle** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:236)
  Check if context has cycle in area containment
- **get_nesting_depth** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py:349)
  Get nesting depth of element (number of cuts enclosing it)
- **_is_odd_nesting_level** (/Users/mjh/Sync/GitHub/Arisbe/src/chapter21_transformation_sequences.py:645)
  Check if area is at odd nesting level (negative context)
- **can_apply** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:21)
  Insertion allowed in positive contexts (even nesting depth)
- **can_apply** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_transformation_pipeline.py:135)
  Erasure allowed in negative contexts (odd nesting depth)
- **_validate_cut_nesting** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:264)
  Validate cut nesting constraints per Dau's rules
- **_handle_resize_cut** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_system.py:698)
  Handle cut resizing (validate containment)
- **_validate_cut_nesting** (/Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:292)
  Validate cut nesting requirements
- **_get_nesting_hierarchy** (/Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:337)
  Get nesting hierarchy from target area to sheet
- **_calculate_cut_nesting_level** (/Users/mjh/Sync/GitHub/Arisbe/src/enhanced_dau_compliance_engine.py:357)
  Calculate nesting level of a cut
- **validate_deiteration_candidate** (/Users/mjh/Sync/GitHub/Arisbe/src/graph_isomorphism_engine.py:341)
  Validate IT- deiteration by finding isomorphic subgraph in nesting hierarchy
- **_calculate_area_polarity_and_depth** (/Users/mjh/Sync/GitHub/Arisbe/src/chapter21_diagram_engine.py:458)
  Calculate polarity and nesting depth using optimized hierarchical index
- **_find_theta_paths** (/Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:105)
  Find all valid Θ paths from start to end using breadth-first search
- **_satisfies_context_nesting** (/Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:178)
  Check if path satisfies context nesting constraint: ctx(v₁) ≥ ctx(v₂) ≥ 
- **_calculate_nesting_level** (/Users/mjh/Sync/GitHub/Arisbe/src/theta_relation.py:239)
  Calculate nesting level of a context (0 = sheet, higher = more nested)
- **_satisfies_context_nesting_constraint** (/Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:445)
  Check if target_context ≤ subgraph_context (nesting constraint)
- **_calculate_nesting_level** (/Users/mjh/Sync/GitHub/Arisbe/src/formal_iteration_rule.py:459)
  Calculate nesting level (0 = sheet, higher = more nested)
- **_build_area_hierarchy** (/Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:109)
  Build hierarchy of logical areas from EGI area mapping
- **_layout_cuts** (/Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:134)
  Layout all cuts spatially based on their logical hierarchy
- **_calculate_nesting_depths** (/Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:166)
  Calculate nesting depth for each cut
- **_validate_spatial_containment** (/Users/mjh/Sync/GitHub/Arisbe/src/cut_area_correspondence.py:331)
  Validate that all cuts are spatially contained within their parents
- **_calculate_max_nesting_depth** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:122)
  Calculate the maximum nesting depth of cuts
- **_check_area_containment** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:243)
  Check area containment rules and consistency
- **_check_cut_nesting** (/Users/mjh/Sync/GitHub/Arisbe/src/egi_validity_analyzer.py:280)
  Check cut nesting rules and detect cycles
- **polarity** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:23)
  Calculate polarity from nesting level
- **get_nesting_level** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:85)
  Get the nesting level of an area
- **get_areas_at_level** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:125)
  Get all areas at a specific nesting level
- **validate_containment** (/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py:171)
  Validate that container can contain the contained area
- **_is_context_accessible** (/Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py:343)
  Check if to_context is accessible from from_context (nesting-wise)
- **validate_semantic_constraints** (/Users/mjh/Sync/GitHub/Arisbe/src/controller/constraint_engine.py:261)
  Validate semantic constraints (only enforced in STRICT mode):
- Area containment (elements must be in assigned areas)
- Logical structure preservation
- **get_context_depth** (/Users/mjh/Sync/GitHub/Arisbe/src/gui/simple_diagram_editor.py:604)
  Get the nesting depth of the current context
