# 🔒 ARISBE PROTECTED CORE API REFERENCE

**Generated:** 2025-01-19
**Status:** ✅ VALIDATED (87/87 core tests passing)
**Purpose:** Protected core API documentation

---

## 📊 **CORE API SUMMARY**

- **Total Modules:** 16
- **Total Classes:** 57
- **Total Functions:** 19
- **Validation Status:** 100% tested and validated

## 📦 **CORE MODULES INDEX**

- **`area_spatial_constraint_system`** - 2 classes, 0 functions
- **`cgif_generator_dau`** - 1 classes, 1 functions
- **`cgif_parser_dau`** - 5 classes, 1 functions
- **`egi_core_dau`** - 6 classes, 4 functions
- **`egi_io`** - 0 classes, 4 functions
- **`egif_generator_dau`** - 1 classes, 1 functions
- **`egif_parser_dau`** - 5 classes, 1 functions
- **`enhanced_ligature_algorithms`** - 3 classes, 1 functions
- **`formal_transformation_rules`** - 12 classes, 2 functions
- **`hierarchical_index`** - 2 classes, 0 functions
- **`ligature_aware_positioning_engine`** - 3 classes, 0 functions
- **`ligature_manipulation_rules`** - 5 classes, 1 functions
- **`ligature_optimization_engine`** - 5 classes, 0 functions
- **`obstacle_aware_ligature_router`** - 3 classes, 0 functions
- **`single_object_ligature_detector`** - 2 classes, 1 functions
- **`syntactic_equivalence_checker`** - 2 classes, 2 functions

---

## 📚 **DETAILED API DOCUMENTATION**

### 📦 `area_spatial_constraint_system`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/area_spatial_constraint_system.py`

**Description:** Area-Based Spatial Constraint System

Implements the fundamental principle that EGI areas define spatial extents
that constrain element positioning and ligature routing. This ensures that
the logical structure (EGI.area mappings) directly corresponds to spatial
boundaries that cannot be violated.

Key Principles:
- Each area has spatial extent = cut bounds minus nested cut bounds
- Elements can only exist within their area's spatial extent
- Ligatures can cross area boundaries only at connection endpoints
- Phase 2 optimization must respect these absolute spatial constraints

#### Classes

##### `AreaSpatialConstraintSystem`

Manages spatial constraints based on EGI area mappings.

Ensures that logical areas correspond to spatial extents that
absolutely constrain element positioning and ligature routing.

**Methods:**
- `__init__(self)`
- `calculate_area_extents(self, egi: egi_core_dau.RelationalGraphWithCuts, cut_bounds: Dict[str, containment_hierarchy_engine.ALURect]) -> Dict[str, area_spatial_constraint_system.AreaSpatialExtent]`
- `constrain_element_position(self, element_id: str, proposed_position: containment_hierarchy_engine.ALUPoint, egi: egi_core_dau.RelationalGraphWithCuts) -> containment_hierarchy_engine.ALUPoint`
- `get_area_extent(self, area_id: str) -> Optional[area_spatial_constraint_system.AreaSpatialExtent]`
- `get_available_positioning_space(self, area_id: str) -> Optional[containment_hierarchy_engine.ALURect]`
- `validate_ligature_path(self, start_pos: containment_hierarchy_engine.ALUPoint, end_pos: containment_hierarchy_engine.ALUPoint, start_area: str, end_area: str) -> bool`

##### `AreaSpatialExtent`

Spatial extent available for elements within an area.

**Methods:**
- `__init__(self, area_id: str, total_bounds: containment_hierarchy_engine.ALURect, available_bounds: containment_hierarchy_engine.ALURect, nested_cut_bounds: List[containment_hierarchy_engine.ALURect]) -> None`
- `__repr__(self)`
- `clamp_point_to_area(self, x: float, y: float) -> Tuple[float, float]`
- `contains_point(self, x: float, y: float) -> bool`

---

### 📦 `cgif_generator_dau`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/cgif_generator_dau.py`

**Description:** Dau-compliant CGIF (Conceptual Graph Interchange Format) generator.
Converts RelationalGraphWithCuts structures to CGIF expressions.

CGIF Generation Strategy:
- Vertices with type relations: [Type: *x] or [Type: John]
- Edges as relations: (Loves ?x John)
- Cuts as negation: ~[CG content]
- Generic vertices: [*x]
- Constants: [: John] or just John in relations
- Proper coreference label management

Maintains same rigor as EGIF and CLIF generators.

#### Classes

##### `CGIFGenerator`

Generates CGIF expressions from Dau-compliant graphs.

**Methods:**
- `__init__(self, graph: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
- `generate(self) -> str`
- `generate_cgif(self, graph: egi_core_dau.RelationalGraphWithCuts) -> str`

#### Functions

##### `generate_cgif(egi: egi_core_dau.RelationalGraphWithCuts) -> str`

Generate CGIF expression from EGI structure.

**Parameters:**
- `egi: <class 'egi_core_dau.RelationalGraphWithCuts'>`

**Returns:** `<class 'str'>`

---

### 📦 `cgif_parser_dau`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/cgif_parser_dau.py`

**Description:** Dau-compliant CGIF (Conceptual Graph Interchange Format) parser.
Converts CGIF expressions to RelationalGraphWithCuts structures.

CGIF Syntax Overview (from ISO/IEC 24707:2007 Annex B):
- Concepts: [Type: *x], [: John], [*x]
- Relations: (Loves ?x John), (Go ?x)
- Contexts: [CG content]
- Coreference labels: *x (defining), ?x (bound)
- Universal quantifier: @every
- Negation: ~[CG content]

Maps to EGI as:
- Concepts -> Vertices with type relations
- Relations -> Edges
- Contexts -> Areas (cuts for negation)
- Coreference labels -> Variable bindings

#### Classes

##### `CGIFLexer`

Lexical analyzer for CGIF expressions.

**Methods:**
- `__init__(self, text: str)`
- `tokenize(self) -> List[cgif_parser_dau.CGIFToken]`

##### `CGIFParseNode`

Node in CGIF parse tree.

**Methods:**
- `__init__(self, type: str, value: Optional[str] = None, children: List[ForwardRef('CGIFParseNode')] = None, attributes: Dict[str, Any] = None) -> None`
- `__repr__(self)`

##### `CGIFParser`

Parser for CGIF expressions.

**Methods:**
- `__init__(self, text: str)`
- `parse(self) -> egi_core_dau.RelationalGraphWithCuts`

##### `CGIFToken`

CGIF lexical token.

**Methods:**
- `__init__(self, type: cgif_parser_dau.CGIFTokenType, value: str, position: int) -> None`
- `__repr__(self)`

##### `CGIFTokenType`

Token types for CGIF lexical analysis.

#### Functions

##### `parse_cgif(cgif_text: str) -> egi_core_dau.RelationalGraphWithCuts`

Parse CGIF text into EGI structure.

**Parameters:**
- `cgif_text: <class 'str'>`

**Returns:** `<class 'egi_core_dau.RelationalGraphWithCuts'>`

---

### 📦 `egi_core_dau`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/egi_core_dau.py`

**Description:** Dau-compliant Existential Graph Instance (EGI) core implementation.
Follows Frithjof Dau's exact 6+1 component definition from "Mathematical Logic with Diagrams".

This implementation replaces the previous "Context" model with Dau's formal:
- 6-component Relational Graph with Cuts: (V, E, ν, ⊤, Cut, area)
- 7th component: rel mapping for relation names
- Proper area/context distinction for diagram generation
- Support for isolated vertices ("heavy dots")

#### Classes

##### `Alphabet`

Manages variable naming for EGIF generation.

**Methods:**
- `__init__(self)`
- `get_fresh_name(self) -> str`
- `reserve_name(self, name: str)`

##### `AlphabetDAU`

Dau's Alphabet (C, F, R, ar). Use with RelationalGraphWithCuts to enable
arity and membership validations. Set ar(c)=1 implicitly for c∈C unless provided.

**Methods:**
- `__init__(self, C: FrozenSet[str] = frozenset(), F: FrozenSet[str] = frozenset(), R: FrozenSet[str] = frozenset(), ar: frozendict.frozendict[str, int] = frozendict.frozendict({})) -> None`
- `__repr__(self)`
- `with_defaults(self) -> 'AlphabetDAU'`

##### `Cut`

Cut in Dau's formalism - represents negation context.

**Methods:**
- `__init__(self, id: str) -> None`
- `__repr__(self)`

##### `Edge`

Edge in Dau's formalism - represents a relation with incident vertices.

**Methods:**
- `__init__(self, id: str) -> None`
- `__repr__(self)`

##### `RelationalGraphWithCuts`

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

**Methods:**
- `__init__(self, V: FrozenSet[egi_core_dau.Vertex], E: FrozenSet[egi_core_dau.Edge], nu: frozendict.frozendict[str, typing.Tuple[str, ...]], sheet: str, Cut: FrozenSet[egi_core_dau.Cut], area: frozendict.frozendict[str, typing.FrozenSet[str]], rel: frozendict.frozendict[str, str], alphabet: Optional[ForwardRef('AlphabetDAU')] = None, rho: frozendict.frozendict[str, typing.Optional[str]] = frozendict.frozendict({}), variable_names: frozendict.frozendict[str, str] = frozendict.frozendict({}), hierarchical_index: Optional[ForwardRef('HierarchicalIndex')] = None, _vertex_map: frozendict.frozendict[str, egi_core_dau.Vertex] = None, _edge_map: frozendict.frozendict[str, egi_core_dau.Edge] = None, _cut_map: frozendict.frozendict[str, egi_core_dau.Cut] = None) -> None`
- `__repr__(self)`
- `add_vertex_to_ligature(self, edge_id: str, hook_position: int, new_vertex: egi_core_dau.Vertex, context_id: str) -> 'RelationalGraphWithCuts'`
- `apply_isomorphism(self, vertex_mapping: Dict[str, str], edge_mapping: Dict[str, str], cut_mapping: Dict[str, str]) -> 'RelationalGraphWithCuts'`
- `change_identity_edge_orientation(self, edge_id: str) -> 'RelationalGraphWithCuts'`
- `get_all_elements(self) -> FrozenSet[str]`
- `get_area(self, context_id: str) -> FrozenSet[str]`
- `get_branch_count(self, vertex_id: str) -> int`
- `get_context(self, element_id: str) -> str`
- `get_cut(self, cut_id: str) -> egi_core_dau.Cut`
- `get_edge(self, edge_id: str) -> egi_core_dau.Edge`
- `get_full_context(self, context_id: str) -> FrozenSet[str]`
- `get_hooks(self, edge_id: str) -> List[Tuple[str, int]]`
- `get_identity_edge_as_set(self, edge_id: str) -> FrozenSet[str]`
- `get_identity_edges(self) -> FrozenSet[str]`
- `get_incident_vertices(self, edge_id: str) -> Tuple[str, ...]`
- `get_isolated_vertices(self) -> FrozenSet[str]`
- `get_ligature_graph(self) -> Tuple[FrozenSet[str], FrozenSet[Tuple[str, str]]]`
- `get_ligatures(self) -> List[FrozenSet[str]]`
- `get_nesting_depth(self, element_id: str) -> int`
- `get_relation_name(self, edge_id: str) -> str`
- `get_vertex(self, vertex_id: str) -> egi_core_dau.Vertex`
- `get_vertex_at_hook(self, edge_id: str, position: int) -> str`
- `get_vertex_hooks(self, vertex_id: str) -> List[Tuple[str, int]]`
- `get_vertex_ligature(self, vertex_id: str) -> FrozenSet[str]`
- `has_dominating_nodes(self) -> bool`
- `is_branching_point(self, vertex_id: str) -> bool`
- `is_evenly_enclosed(self, element_id: str) -> bool`
- `is_negative_context(self, context_id: str) -> bool`
- `is_oddly_enclosed(self, element_id: str) -> bool`
- `is_positive_context(self, context_id: str) -> bool`
- `is_vertex_isolated(self, vertex_id: str) -> bool`
- `remove_vertex_from_ligature(self, vertex_id: str) -> 'RelationalGraphWithCuts'`
- `replace_vertex_on_hook(self, edge_id: str, position: int, new_vertex_id: str) -> 'RelationalGraphWithCuts'`
- `with_cut(self, cut: egi_core_dau.Cut, context_id: str = None) -> 'RelationalGraphWithCuts'`
- `with_edge(self, edge: egi_core_dau.Edge, vertex_sequence: Tuple[str, ...], relation_name: str, context_id: str = None) -> 'RelationalGraphWithCuts'`
- `with_vertex(self, vertex: egi_core_dau.Vertex) -> 'RelationalGraphWithCuts'`
- `with_vertex_in_context(self, vertex: egi_core_dau.Vertex, context_id: str) -> 'RelationalGraphWithCuts'`
- `with_vertex_moved_to_context(self, vertex_id: str, new_context_id: str) -> 'RelationalGraphWithCuts'`
- `without_element(self, element_id: str) -> 'RelationalGraphWithCuts'`

##### `Vertex`

Vertex in Dau's formalism - can be generic (*x) or constant ("Socrates").

**Methods:**
- `__init__(self, id: str, label: Optional[str] = None, is_generic: bool = True) -> None`
- `__repr__(self)`

#### Functions

##### `create_cut() -> egi_core_dau.Cut`

Create new cut with unique ID.

**Returns:** `<class 'egi_core_dau.Cut'>`

##### `create_edge() -> egi_core_dau.Edge`

Create new edge with unique ID.

**Returns:** `<class 'egi_core_dau.Edge'>`

##### `create_empty_graph() -> egi_core_dau.RelationalGraphWithCuts`

Create empty graph (Dau's G_∅).

**Returns:** `<class 'egi_core_dau.RelationalGraphWithCuts'>`

##### `create_vertex(label: Optional[str] = None, is_generic: bool = True) -> egi_core_dau.Vertex`

Create new vertex with unique ID.

**Parameters:**
- `label: typing.Optional[str] = None`
- `is_generic: <class 'bool'> = True`

**Returns:** `<class 'egi_core_dau.Vertex'>`

---

### 📦 `egi_io`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/egi_io.py`

**Description:** EGI JSON serialization utilities.

Schema produced/consumed matches tools/migrate_corpus_to_egi.py 
egi_to_dict.

#### Functions

##### `from_dict(d: 'Dict[str, Any]') -> 'RelationalGraphWithCuts'`

No function docstring

**Parameters:**
- `d: Dict[str, Any]`

**Returns:** `RelationalGraphWithCuts`

##### `load_egi_json(path: 'str | Path') -> 'RelationalGraphWithCuts'`

No function docstring

**Parameters:**
- `path: str | Path`

**Returns:** `RelationalGraphWithCuts`

##### `save_egi_json(egi: 'RelationalGraphWithCuts', path: 'str | Path') -> 'None'`

No function docstring

**Parameters:**
- `egi: RelationalGraphWithCuts`
- `path: str | Path`

**Returns:** `None`

##### `to_dict(egi: 'RelationalGraphWithCuts') -> 'Dict[str, Any]'`

No function docstring

**Parameters:**
- `egi: RelationalGraphWithCuts`

**Returns:** `Dict[str, Any]`

---

### 📦 `egif_generator_dau`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/egif_generator_dau.py`

**Description:** Fixed Dau-compliant EGIF generator with proper variable scoping.
Fixes the critical issue where variables defined in cuts were not marked as defining.

Key fix: Variables that first appear in any context (including cuts) are marked as defining (*x).

#### Classes

##### `EGIFGenerator`

Generates EGIF expressions from Dau-compliant graphs with proper variable scoping.

**Methods:**
- `__init__(self, graph: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
- `generate(self) -> str`
- `generate_egif(self, graph: egi_core_dau.RelationalGraphWithCuts) -> str`

#### Functions

##### `generate_egif(graph: egi_core_dau.RelationalGraphWithCuts) -> str`

Generate EGIF expression from Dau-compliant graph.

**Parameters:**
- `graph: <class 'egi_core_dau.RelationalGraphWithCuts'>`

**Returns:** `<class 'str'>`

---

### 📦 `egif_parser_dau`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/egif_parser_dau.py`

**Description:** Dau-compliant EGIF parser that builds RelationalGraphWithCuts structures.
Supports isolated vertices, proper syntax validation, and Dau's 6+1 component model.

Key improvements over previous parser:
- Supports isolated vertices (*x, "Socrates") as per Dau's "heavy dot" rule
- Builds proper Dau-compliant structures with area/context distinction
- Comprehensive syntax validation before processing
- Proper handling of generic vs constant vertices

#### Classes

##### `EGIFLexer`

Lexical analyzer for EGIF expressions with isolated vertex support.

**Methods:**
- `__init__(self, text: str)`
- `tokenize(self) -> List[egif_parser_dau.Token]`

##### `EGIFParser`

Parser for EGIF expressions that builds Dau-compliant structures.

**Methods:**
- `__init__(self, text: str)`
- `parse(self) -> egi_core_dau.RelationalGraphWithCuts`

##### `EGIFSyntaxValidator`

Validates EGIF syntax before parsing.

**Methods:**
- `__init__(self, tokens: List[egif_parser_dau.Token])`
- `validate(self) -> bool`

##### `Token`

Token in EGIF expression.

**Methods:**
- `__init__(self, type: egif_parser_dau.TokenType, value: str, position: int) -> None`
- `__repr__(self)`

##### `TokenType`

Token types for EGIF lexical analysis.

#### Functions

##### `parse_egif(text: str) -> egi_core_dau.RelationalGraphWithCuts`

Parse EGIF expression into Dau-compliant graph.

**Parameters:**
- `text: <class 'str'>`

**Returns:** `<class 'egi_core_dau.RelationalGraphWithCuts'>`

---

### 📦 `enhanced_ligature_algorithms`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/enhanced_ligature_algorithms.py`

**Description:** Enhanced Ligature Algorithms with Non-Transitive Θ Relation Support

Updates ligature manipulation algorithms to properly handle the non-transitive
nature of the Θ relation per Dau Definition 15.1. This affects:
- Ligature path traversal
- Identity network construction
- Branch moving operations
- Ligature extension/restriction

#### Classes

##### `EnhancedLigatureAlgorithms`

Enhanced ligature algorithms that properly handle non-transitive Θ relation.

Key differences from basic algorithms:
1. Cannot assume transitivity in ligature traversal
2. Must validate each Θ connection individually
3. Ligature networks may have multiple disconnected components
4. Branch moving must respect Θ path constraints

**Methods:**
- `__init__(self)`
- `analyze_ligature_network(self, egi: egi_core_dau.RelationalGraphWithCuts, vertices: Set[str]) -> enhanced_ligature_algorithms.LigatureNetwork`
- `enhanced_extend_ligature(self, egi: egi_core_dau.RelationalGraphWithCuts, existing_ligature: Set[str], new_vertices: Set[str], target_context: str) -> enhanced_ligature_algorithms.EnhancedLigatureResult`
- `enhanced_move_branches_along_ligature(self, egi: egi_core_dau.RelationalGraphWithCuts, source_vertex: str, target_vertex: str, ligature_context: str) -> enhanced_ligature_algorithms.EnhancedLigatureResult`
- `validate_ligature_consistency(self, egi: egi_core_dau.RelationalGraphWithCuts) -> Tuple[bool, List[str]]`

##### `EnhancedLigatureResult`

Result of enhanced ligature operation.

**Methods:**
- `__init__(self, success: bool, result_egi: Optional[egi_core_dau.RelationalGraphWithCuts], ligature_network: Optional[enhanced_ligature_algorithms.LigatureNetwork], theta_violations: List[str], error_message: Optional[str] = None) -> None`
- `__repr__(self)`

##### `LigatureNetwork`

A network of vertices connected by identity edges, respecting Θ relation.

**Methods:**
- `__init__(self, vertices: Set[str], identity_edges: Set[str], theta_paths: Dict[Tuple[str, str], List[theta_relation.ThetaPath]], is_connected: bool, components: List[Set[str]]) -> None`
- `__repr__(self)`

#### Functions

##### `demonstrate_enhanced_ligature_algorithms()`

Demonstrate enhanced ligature algorithms with Θ relation.

---

### 📦 `formal_transformation_rules`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/formal_transformation_rules.py`

**Description:** Formal EG transformation rules implementing precise Peirce-Dau formalism.
Each rule has clear preconditions, transformations, and postconditions.

#### Classes

##### `AreaPolarity`

Polarity of an area based on nesting depth of cuts.

##### `DeiterationRule`

IT- - Deiteration Rule

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
- `is_valid(self, egi: egi_core_dau.RelationalGraphWithCuts, selected_subgraph: FrozenSet[str]) -> bool`

##### `DoubleCutErasureRule`

DC- - Double Cut Erasure Rule

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `DoubleCutInsertionRule`

DC+ - Double Cut Insertion Rule

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `ErasureRule`

ERA - Erasure Rule

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `FormalTransformationEngine`

Engine for applying formal EG transformation rules.

**Methods:**
- `__init__(self)`
- `apply_rule(self, rule_name: str, source_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, selected_subgraph: FrozenSet[str]) -> formal_transformation_rules.TransformationResult`
- `describe_rule(self, rule_name: str) -> str`
- `get_available_rules(self) -> List[str]`

##### `FormalTransformationRule`

Abstract base class for formal EG transformation rules.

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `HeavyDotInsertionRule`

Heavy Dot Insertion Rule - Insert individual vertex in negative context

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `InsertionRule`

INS - Insertion Rule

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `IterationRule`

IT+ - Iteration Rule

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `TransformationContext`

Context information for applying a transformation.

**Methods:**
- `__init__(self, source_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, selected_subgraph: FrozenSet[str], area_polarity: formal_transformation_rules.AreaPolarity, nesting_depth: int) -> None`
- `__repr__(self)`

##### `TransformationResult`

Result of applying a transformation rule.

**Methods:**
- `__init__(self, success: bool, result_egi: Optional[egi_core_dau.RelationalGraphWithCuts], error_message: Optional[str], changes_made: Dict[str, Any]) -> None`
- `__repr__(self)`

#### Functions

##### `create_test_egi() -> egi_core_dau.RelationalGraphWithCuts`

Create a test EGI for demonstration purposes.

**Returns:** `<class 'egi_core_dau.RelationalGraphWithCuts'>`

##### `demonstrate_transformation_rules()`

Demonstrate each transformation rule with test sequences.

---

### 📦 `hierarchical_index`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/hierarchical_index.py`

**Description:** Hierarchical index for EGI cut nesting relationships.

This provides efficient O(1) lookup of nesting levels and containment relationships
that are fundamental to EGI logical semantics, not just spatial representation.
The hierarchical structure is core to transformation rules like IT+/IT-.

#### Classes

##### `HierarchicalIndex`

Efficient hierarchical index for EGI cut nesting relationships.

This is integral to EGI logic for:
- Polarity calculation (positive/negative areas)
- Transformation rule validation (IT+/IT- nesting requirements)
- Containment queries for logical operations

**Methods:**
- `__init__(self)`
- `add_area(self, area_id: str, parent_area: Optional[str] = None) -> bool`
- `get_ancestors(self, area_id: str) -> List[str]`
- `get_areas_at_level(self, level: int) -> List[str]`
- `get_children(self, area_id: str) -> Set[str]`
- `get_negative_areas(self) -> List[str]`
- `get_nesting_level(self, area_id: str) -> Optional[int]`
- `get_parent(self, area_id: str) -> Optional[str]`
- `get_polarity(self, area_id: str) -> Optional[str]`
- `get_positive_areas(self) -> List[str]`
- `get_statistics(self) -> Dict[str, <built-in function any>]`
- `is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool`
- `remove_area(self, area_id: str) -> bool`
- `validate_containment(self, container_id: str, contained_id: str) -> bool`

##### `NestingInfo`

Information about an area's position in the nesting hierarchy.

**Methods:**
- `__init__(self, area_id: str, nesting_level: int, parent_area: Optional[str], child_areas: Set[str]) -> None`
- `__repr__(self)`

---

### 📦 `ligature_aware_positioning_engine`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/ligature_aware_positioning_engine.py`

**Description:** Ligature-Aware Positioning Engine

Implements intelligent vertex positioning that minimizes ligature path lengths
while respecting area boundaries. This replaces the naive positioning in
Phase 2 with connection-aware optimization.

Key Principles:
- Vertices positioned optimally between connected predicates
- Ligature paths calculated as shortest valid routes
- Area boundaries absolutely respected
- Cross-cut connections handled with proper boundary logic
- Path length minimization as primary objective

#### Classes

##### `ConnectionInfo`

Information about a vertex's connections.

**Methods:**
- `__init__(self, vertex_id: str, vertex_area: str, connected_predicates: List[Tuple[str, str]], cross_cut_connections: int, same_area_connections: int) -> None`
- `__repr__(self)`

##### `LigatureAwarePositioningEngine`

Positions vertices optimally to minimize ligature path lengths
while absolutely respecting area boundaries.

**Methods:**
- `__init__(self, constraint_system: area_spatial_constraint_system.AreaSpatialConstraintSystem)`
- `optimize_predicate_positions(self, egi: egi_core_dau.RelationalGraphWithCuts, initial_positions: Dict[str, containment_hierarchy_engine.ALUPoint], area_bounds: Dict[str, containment_hierarchy_engine.ALURect]) -> Dict[str, containment_hierarchy_engine.ALUPoint]`
- `optimize_vertex_positions(self, egi: egi_core_dau.RelationalGraphWithCuts, predicate_positions: Dict[str, containment_hierarchy_engine.ALUPoint], area_bounds: Dict[str, containment_hierarchy_engine.ALURect]) -> Dict[str, containment_hierarchy_engine.ALUPoint]`

##### `OptimalPosition`

Optimal position calculation for a vertex.

**Methods:**
- `__init__(self, vertex_id: str, optimal_point: containment_hierarchy_engine.ALUPoint, total_path_length: float, constrained_point: containment_hierarchy_engine.ALUPoint, constraint_applied: bool) -> None`
- `__repr__(self)`

---

### 📦 `ligature_manipulation_rules`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/ligature_manipulation_rules.py`

**Description:** Chapter 16 Ligature Manipulation Rules implementing Dau's formalism.
These rules allow rearranging ligatures while preserving logical meaning.

#### Classes

##### `ExtendRestrictLigatureRule`

Lemma 16.2: Extending or Restricting a Ligature in a Context
Allows adding new identity networks to existing ligatures.

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `LigatureManipulationEngine`

Engine for applying ligature manipulation rules from Dau Chapter 16.

**Methods:**
- `__init__(self)`
- `apply_rule(self, rule_name: str, source_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, selected_subgraph: FrozenSet[str]) -> formal_transformation_rules.TransformationResult`
- `describe_rule(self, rule_name: str) -> str`
- `get_available_rules(self) -> List[str]`

##### `LigatureRearrangementRule`

Definition 16.4: Rearranging Ligatures in a Context
Replaces ligature (W,F) with new ligature (W',F') in same context.

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `MoveBranchesAlongLigatureRule`

Lemma 16.1: Moving Branches along a Ligature in a Context
Allows repositioning vertices along the same ligature while preserving identity.

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

##### `RetractLigatureRule`

Lemma 16.3: Retracting a Ligature in a Context
Collapses an entire ligature (W,F) to a single vertex w0.

**Methods:**
- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[formal_transformation_rules.AreaPolarity, int]`
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
- `get_rule_name(self) -> str`
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`

#### Functions

##### `demonstrate_ligature_manipulation()`

Demonstrate ligature manipulation rules.

---

### 📦 `ligature_optimization_engine`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/ligature_optimization_engine.py`

**Description:** Phase 2: Ligature Optimization Engine

Optimizes element positions within their allocated areas to minimize ligature
path lengths and avoid predicate text collisions. This is the second phase
of the two-phase layout system that fine-tunes positioning after the
containment hierarchy is established.

Key Principles:
- Elements stay within their allocated areas (from Phase 1)
- Minimize ligature path lengths between connected elements
- Avoid ligature collisions with predicate text
- Implement 8-point compass hook system for predicates
- Add bridge icons for unavoidable ligature crossings

#### Classes

##### `CompassDirection`

8-point compass directions for predicate hooks.

##### `ElementPosition`

Optimized position for an element within its area.

**Methods:**
- `__init__(self, element_id: str, area_id: str, position: containment_hierarchy_engine.ALUPoint, element_type: str) -> None`
- `__repr__(self)`

##### `LigatureConnection`

Connection between two elements via ligature.

**Methods:**
- `__init__(self, edge_id: str, vertex_ids: List[str], predicate_area: str, vertex_areas: List[str], crosses_cuts: bool) -> None`
- `__repr__(self)`

##### `LigatureOptimizationEngine`

Phase 2 of two-phase layout: Optimizes element positions for ligature routing
while respecting the containment hierarchy established in Phase 1.

**Methods:**
- `__init__(self)`
- `optimize_layout(self, egi: egi_core_dau.RelationalGraphWithCuts, area_bounds: Dict[str, containment_hierarchy_engine.ALURect], constraint_system: Optional[area_spatial_constraint_system.AreaSpatialConstraintSystem] = None) -> Dict[str, containment_hierarchy_engine.ALUPoint]`

##### `PredicateHook`

Hook point on a predicate for ligature connection.

**Methods:**
- `__init__(self, edge_id: str, direction: ligature_optimization_engine.CompassDirection, position: containment_hierarchy_engine.ALUPoint, vertex_id: str, argument_index: int) -> None`
- `__repr__(self)`

---

### 📦 `obstacle_aware_ligature_router`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/obstacle_aware_ligature_router.py`

**Description:** Obstacle-Aware Ligature Router using Shapely and A* Pathfinding

Implements spatial routing for ligatures that respects all spatial exclusivity constraints.

#### Classes

##### `LigatureRoute`

Represents a calculated route for a ligature.

**Methods:**
- `__init__(self, start_element: str, end_element: str, waypoints: List[containment_hierarchy_engine.ALUPoint], total_length: float) -> None`
- `__repr__(self)`

##### `Obstacle`

Represents a spatial obstacle as a shapely Polygon.

**Methods:**
- `__init__(self, id: str, polygon: shapely.geometry.polygon.Polygon) -> None`
- `__repr__(self)`

##### `ObstacleAwareLigatureRouter`

Routes ligatures around spatial obstacles using A* on a visibility graph.

**Methods:**
- `__init__(self)`
- `calculate_all_routes(self, egi: egi_core_dau.RelationalGraphWithCuts, element_positions: Dict[str, containment_hierarchy_engine.ALUPoint], element_sizes: Dict[str, containment_hierarchy_engine.ALURect]) -> Dict[Tuple[str, str], obstacle_aware_ligature_router.LigatureRoute]`
- `route_single_ligature(self, start_id: str, end_id: str, egi: egi_core_dau.RelationalGraphWithCuts, element_positions: Dict[str, containment_hierarchy_engine.ALUPoint], all_obstacles: List[obstacle_aware_ligature_router.Obstacle]) -> Optional[obstacle_aware_ligature_router.LigatureRoute]`

---

### 📦 `single_object_ligature_detector`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/single_object_ligature_detector.py`

**Description:** Definition 16.8: Single-Object Ligature Detection
Implements Dau's formal definition for identifying ligatures that represent single objects.

#### Classes

##### `LigatureAnalysis`

Analysis result for a ligature structure.

**Methods:**
- `__init__(self, vertices: Set[str], identity_edges: Set[str], is_single_object: bool, violation_reasons: List[str], context_mapping: Dict[str, str], cycles: List[List[str]]) -> None`
- `__repr__(self)`

##### `SingleObjectLigatureDetector`

Implements Dau's Definition 16.8 for detecting single-object ligatures.

A ligature (W,F) is single-object iff:
1. No identity-link f in F with w1 f w2 where f < w1 and f < w2
2. No vertices w1, w2, w in W and f1, f2 in F with w1 != w2, w1 f1 w f2 w2,
   where w < w1 and w < w2
3. No vertices w1, w2 in W in a cycle where w2 < w1

**Methods:**
- `__init__(self, egi: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
- `is_single_object_ligature(self, ligature_vertices: List[str]) -> Tuple[bool, List[str]]`
- `separate_into_single_object_components(self, ligature_vertices: List[str]) -> List[List[str]]`

#### Functions

##### `demonstrate_single_object_ligature_detection()`

Demonstrate single-object ligature detection.

---

### 📦 `syntactic_equivalence_checker`

**File:** `/Users/mjh/Sync/GitHub/Arisbe/src/syntactic_equivalence_checker.py`

**Description:** Syntactic Equivalence Checker for EG transformations per Dau's formalism.
Validates that transformations preserve logical meaning through syntactic equivalence.

#### Classes

##### `EquivalenceResult`

Result of syntactic equivalence checking.

**Methods:**
- `__init__(self, are_equivalent: bool, reason: Optional[str], structural_differences: List[str], transformation_sequence: List[str]) -> None`
- `__repr__(self)`

##### `SyntacticEquivalenceChecker`

Checker for syntactic equivalence between EGIs per Dau's Definition 15.3.
Two graphs G1, G2 are syntactically equivalent if G1 ⊢ G2 and G2 ⊢ G1.

**Methods:**
- `__init__(self)`
- `check_equivalence(self, egi1: egi_core_dau.RelationalGraphWithCuts, egi2: egi_core_dau.RelationalGraphWithCuts) -> syntactic_equivalence_checker.EquivalenceResult`

#### Functions

##### `demonstrate_syntactic_equivalence()`

Demonstrate syntactic equivalence checking.

##### `validate_transformation_preserves_meaning(original_egi: egi_core_dau.RelationalGraphWithCuts, transformed_egi: egi_core_dau.RelationalGraphWithCuts, transformation_name: str) -> syntactic_equivalence_checker.EquivalenceResult`

Validate that a transformation preserves logical meaning through syntactic equivalence.

Args:
    original_egi: EGI before transformation
    transformed_egi: EGI after transformation
    transformation_name: Name of the transformation applied

Returns:
    EquivalenceResult indicating whether transformation preserves meaning

**Parameters:**
- `original_egi: <class 'egi_core_dau.RelationalGraphWithCuts'>`
- `transformed_egi: <class 'egi_core_dau.RelationalGraphWithCuts'>`
- `transformation_name: <class 'str'>`

**Returns:** `<class 'syntactic_equivalence_checker.EquivalenceResult'>`

---
