# Arisbe Pattern Catalog

## Performance Patterns
### Hierarchical Index O(1) Lookup
**Description**: Use HierarchicalIndex for constant-time polarity and nesting queries
**When to Use**: When you need polarity, nesting level, or containment information
**Implementation**: Build HierarchicalIndex from EGI, use get_polarity() and get_nesting_level()
**Examples**:
- hierarchical_index.py:90 - get_polarity()
- chapter21_diagram_engine.py:458 - _calculate_area_polarity_and_depth()
**Related Patterns**: egi_area_mapping, spatial_indexing
**Anti-Patterns to Avoid**: manual_traversal_polarity

### R-Tree Spatial Indexing
**Description**: Use R-tree for efficient spatial queries and containment checks
**When to Use**: When dealing with spatial relationships, cut containment, or region queries
**Implementation**: Use rtree_cut_tracker.py or hierarchical_view_system.py
**Examples**:
- legacy/rtree_cut_tracker.py:86 - RTreeNode
- legacy/hierarchical_view_system.py:431 - DynamicViewManager
**Related Patterns**: hierarchical_index_lookup
**Anti-Patterns to Avoid**: linear_spatial_search

## User Interface Patterns
### Step-by-Step Transformation Wizard
**Description**: Use modal wizard dialogs for complex multi-step transformations
**When to Use**: For transformation rules requiring user input or validation
**Implementation**: Create TransformationWizardDialog with step navigation and validation
**Examples**:
- gui/transformation_wizard_dialog.py:1 - TransformationWizardDialog
- chapter21_diagram_engine.py:352 - UniversalEGIEngine
**Related Patterns**: formal_rule_application
**Anti-Patterns to Avoid**: direct_transformation_execution

## Logic Patterns
### Formal Rule Application
**Description**: Apply transformation rules through formal validation and context
**When to Use**: For all Peirce-Dau transformation operations
**Implementation**: Use TransformationContext with rule validation and precondition checking
**Examples**:
- formal_transformation_rules.py:75 - calculate_area_polarity
- chapter21_diagram_engine.py:375 - apply_transformation
**Related Patterns**: transformation_wizard, hierarchical_index_lookup
**Anti-Patterns to Avoid**: direct_egi_manipulation

## Data Structure Patterns
### EGI Area Mapping
**Description**: Use frozendict area mapping for immutable containment relationships
**When to Use**: When representing cut containment and area relationships
**Implementation**: RelationalGraphWithCuts with area: frozendict[ElementID, frozenset[ElementID]]
**Examples**:
- egi_core_dau.py:128 - _build_hierarchical_index
- egi_core_dau.py:349 - get_nesting_depth
**Related Patterns**: hierarchical_index_lookup
**Anti-Patterns to Avoid**: mutable_area_mapping

## Architecture Patterns
### Signal-Based Tab Communication
**Description**: Use PySide6 signals for communication between GUI tabs
**When to Use**: For passing data between Organon, Ergasterion, and Agon tabs
**Implementation**: Define custom signals and connect them in main application
**Examples**:
- gui/arisbe_main_app_pyside6.py:170 - send_to_organon_signal
- gui/arisbe_main_app_pyside6.py:340 - receive_from_ergasterion
**Related Patterns**: transformation_wizard
**Anti-Patterns to Avoid**: direct_tab_coupling

## Anti-Pattern Patterns
### Manual Polarity Traversal (Anti-Pattern)
**Description**: Manually traversing containment hierarchy for polarity calculation
**When to Use**: NEVER - Use HierarchicalIndex instead
**Implementation**: DON'T: while current_area != egi.sheet: traverse...
**Examples**:
- chapter21_diagram_engine.py:438 - OLD _calculate_area_polarity_and_depth (fixed)

### Direct EGI Manipulation (Anti-Pattern)
**Description**: Directly modifying EGI structures without formal rule validation
**When to Use**: NEVER - Use formal transformation rules
**Implementation**: DON'T: egi.area[new_area] = contents
