# Arisbe Core API Reference

**Last Generated**: 2026-05-30T08:02:09-05:00  
**Source of truth**: `tools/core_protection_system.py` (`protected_modules`)  
**Module count**: 17

---

## Overview

This document provides API documentation for Arisbe's protected core modules. These modules form the mathematical foundation validated by the core test suite. Modifying any module listed below requires explicit authorization (`touch .core_modification_authorized`).

To regenerate this file, run `python tools/extract_core_api.py`.

---

## cgif_generator_dau.py

**Path**: `src/cgif_generator_dau.py`  
**Status**: Protected Core Module

### Module Description

Dau-compliant CGIF (Conceptual Graph Interchange Format) generator.
Converts RelationalGraphWithCuts structures to CGIF expressions.

CGIF Generation Strategy:
- Vertices with type relations: [Type: *x] or [Type: John]
- Edges as relations: (Loves ?x John)
- Cuts as negation: ~[CG content]
- Generic vertices: [*x]
- Constants: [: John] or just John in relations
- Proper coreference label management

Maintains same rigor as EGIF and CLIF generators.

### Classes

#### `CGIFGenerator`

Generates CGIF expressions from Dau-compliant graphs.

**Methods**:

- `__init__(self, graph: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
  Initialize self.  See help(type(self)) for accurate signature.
- `generate(self) -> str`
  Generate CGIF expression from graph.
- `generate_cgif(self, graph: egi_core_dau.RelationalGraphWithCuts) -> str`
  Legacy API: cgif_gen.generate_cgif(graph) -> str

### Functions

#### `generate_cgif(egi: egi_core_dau.RelationalGraphWithCuts) -> str`

Generate CGIF expression from EGI structure.

---

## cgif_parser_dau.py

**Path**: `src/cgif_parser_dau.py`  
**Status**: Protected Core Module

### Module Description

Dau-compliant CGIF (Conceptual Graph Interchange Format) parser.
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

### Classes

#### `CGIFLexer`

Lexical analyzer for CGIF expressions.

**Methods**:

- `__init__(self, text: str)`
  Initialize self.  See help(type(self)) for accurate signature.
- `tokenize(self) -> List[cgif_parser_dau.CGIFToken]`
  Tokenize CGIF text.

#### `CGIFParseNode`

Node in CGIF parse tree.

**Methods**:

- `__init__(self, type: str, value: Optional[str] = None, children: List[ForwardRef('CGIFParseNode')] = None, attributes: Dict[str, Any] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__post_init__(self)`
- `__repr__(self)`
  Return repr(self).

#### `CGIFParser`

Parser for CGIF expressions.

**Methods**:

- `__init__(self, text: str)`
  Initialize self.  See help(type(self)) for accurate signature.
- `parse(self) -> egi_core_dau.RelationalGraphWithCuts`
  Parse CGIF text into EGI structure.

#### `CGIFToken`

CGIF lexical token.

**Methods**:

- `__init__(self, type: cgif_parser_dau.CGIFTokenType, value: str, position: int) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `CGIFTokenType`

Token types for CGIF lexical analysis.

### Functions

#### `parse_cgif(cgif_text: str) -> egi_core_dau.RelationalGraphWithCuts`

Parse CGIF text into EGI structure.

---

## clif_generator_dau.py

**Path**: `src/clif_generator_dau.py`  
**Status**: Protected Core Module

### Module Description

Dau-compliant CLIF (Common Logic Interchange Format) generator.
Converts RelationalGraphWithCuts structures to CLIF expressions.

CLIF Generation Strategy:
- Atomic formulas from edges: (P x y)
- Negation from cuts: (not ...)
- Conjunction from multiple elements in same area: (and ...)
- Variable scoping handled through quantification
- Proper parenthesization and formatting

Maintains same rigor as EGIF generator with proper variable management.

### Classes

#### `CLIFGenerator`

Generates CLIF expressions from Dau-compliant graphs.

**Methods**:

- `__init__(self, graph: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
  Initialize self.  See help(type(self)) for accurate signature.
- `generate(self) -> str`
  Generate CLIF expression from graph.
- `generate_clif(self, graph: egi_core_dau.RelationalGraphWithCuts) -> str`
  Legacy API: clif_gen.generate_clif(graph) -> str
- `generate_with_quantification(self) -> str`
  Generate CLIF with explicit quantification.

### Functions

#### `generate_clif(egi: egi_core_dau.RelationalGraphWithCuts) -> str`

Generate CLIF expression from EGI structure with quantification.

#### `generate_clif_with_quantification(egi: egi_core_dau.RelationalGraphWithCuts) -> str`

Generate CLIF expression with explicit quantification.

---

## clif_parser_dau.py

**Path**: `src/clif_parser_dau.py`  
**Status**: Protected Core Module

### Module Description

Dau-compliant CLIF (Common Logic Interchange Format) parser.
Converts CLIF expressions to RelationalGraphWithCuts structures.

CLIF Syntax Overview:
- Atomic formulas: (P x y)
- Quantification: (forall (x) (P x))
- Negation: (not (P x))
- Conjunction: (and (P x) (Q y))
- Disjunction: (or (P x) (Q y))
- Comments: ;; comment text

Maps to EGI as:
- Atomic formulas -> Edges with vertices
- Negation -> Cuts containing negated content
- Quantification -> Variable scoping in areas
- Conjunction -> Multiple elements in same area
- Disjunction -> Requires transformation to negation normal form

### Classes

#### `CLIFLexer`

Lexical analyzer for CLIF expressions.

**Methods**:

- `__init__(self, text: str)`
  Initialize self.  See help(type(self)) for accurate signature.
- `tokenize(self) -> List[clif_parser_dau.CLIFToken]`
  Convert CLIF text into tokens.

#### `CLIFParseNode`

Node in CLIF parse tree.

**Methods**:

- `__init__(self, type: str, value: Optional[str] = None, children: List[ForwardRef('CLIFParseNode')] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__post_init__(self)`
- `__repr__(self)`
  Return repr(self).

#### `CLIFParser`

Parser for CLIF expressions.

**Methods**:

- `__init__(self, text: str)`
  Initialize self.  See help(type(self)) for accurate signature.
- `parse(self) -> egi_core_dau.RelationalGraphWithCuts`
  Parse CLIF text into EGI structure.

#### `CLIFToken`

CLIF token with type and value.

**Methods**:

- `__init__(self, type: clif_parser_dau.CLIFTokenType, value: str, position: int) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `CLIFTokenType`

Token types for CLIF lexical analysis.

### Functions

#### `parse_clif(clif_text: str) -> egi_core_dau.RelationalGraphWithCuts`

Parse CLIF text into EGI structure.

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

#### `Alphabet`

Manages variable naming for EGIF generation.

**Methods**:

- `__init__(self)`
  Initialize self.  See help(type(self)) for accurate signature.
- `get_fresh_name(self) -> str`
  Get fresh variable name.
- `reserve_name(self, name: str)`
  Reserve a variable name.

#### `AlphabetDAU`

Dau's Alphabet (C, F, R, ar). Use with RelationalGraphWithCuts to enable
arity and membership validations. Set ar(c)=1 implicitly for c∈C unless provided.

**Methods**:

- `__init__(self, C: FrozenSet[str] = frozenset(), F: FrozenSet[str] = frozenset(), R: FrozenSet[str] = frozenset(), ar: frozendict.frozendict[str, int] = frozendict.frozendict({})) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).
- `with_defaults(self) -> 'AlphabetDAU'`
  Return a copy where all constants have arity 1 in ar if not already set.

#### `AreaPolarity`

Polarity of an area based on nesting depth of cuts.

Recto (positive): even nesting depth (0, 2, 4, ...) — the sheet and areas
enclosed by an even number of cuts.
Verso (negative): odd nesting depth (1, 3, 5, ...) — areas enclosed by
an odd number of cuts.

#### `Cut`

Cut in Dau's formalism - represents negation context.

**Methods**:

- `__init__(self, id: str) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `Edge`

Edge in Dau's formalism - represents a relation with incident vertices.

**Methods**:

- `__init__(self, id: str) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

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

- `__init__(self, V: FrozenSet[egi_core_dau.Vertex], E: FrozenSet[egi_core_dau.Edge], nu: frozendict.frozendict[str, typing.Tuple[str, ...]], sheet: str, Cut: FrozenSet[egi_core_dau.Cut], area: frozendict.frozendict[str, typing.FrozenSet[str]], rel: frozendict.frozendict[str, str], alphabet: Optional[ForwardRef('AlphabetDAU')] = None, rho: frozendict.frozendict[str, typing.Optional[str]] = frozendict.frozendict({}), variable_names: frozendict.frozendict[str, str] = frozendict.frozendict({}), hierarchical_index: Optional[ForwardRef('HierarchicalIndex')] = None, _vertex_map: frozendict.frozendict[str, egi_core_dau.Vertex] = None, _edge_map: frozendict.frozendict[str, egi_core_dau.Edge] = None, _cut_map: frozendict.frozendict[str, egi_core_dau.Cut] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__post_init__(self)`
  Validate Dau's formal constraints and build derived mappings.
- `__repr__(self)`
  Return repr(self).
- `add_vertex_to_ligature(self, edge_id: str, hook_position: int, new_vertex: egi_core_dau.Vertex, context_id: str) -> 'RelationalGraphWithCuts'`
  Add vertex to ligature (Definition 12.14).
- `apply_isomorphism(self, vertex_mapping: Dict[str, str], edge_mapping: Dict[str, str], cut_mapping: Dict[str, str]) -> 'RelationalGraphWithCuts'`
  Apply isomorphism transformation (Definition 12.14).
- `area_polarity(self, area_id: str) -> Tuple[ForwardRef('AreaPolarity'), int]`
  Canonical polarity and nesting depth for an area (sheet or cut).
- `change_identity_edge_orientation(self, edge_id: str) -> 'RelationalGraphWithCuts'`
  Change orientation of identity edge (Definition 12.14).
- `get_all_elements(self) -> FrozenSet[str]`
  Get all element IDs in the EGI (vertices, edges, cuts).
- `get_area(self, context_id: str) -> FrozenSet[str]`
  Get area of context - direct contents only (non-recursive).
- `get_branch_count(self, vertex_id: str) -> int`
  Get number of branches (hooks) for vertex.
- `get_context(self, element_id: str) -> str`
  Get the context that directly contains this element.
- `get_cut(self, cut_id: str) -> egi_core_dau.Cut`
  Get cut by ID.
- `get_edge(self, edge_id: str) -> egi_core_dau.Edge`
  Get edge by ID.
- `get_full_context(self, context_id: str) -> FrozenSet[str]`
  Get full context of a cut - all elements it contributes to SoA (recursive).
- `get_hooks(self, edge_id: str) -> List[Tuple[str, int]]`
  Get all hooks for an edge as (edge_id, position) pairs.
- `get_identity_edge_as_set(self, edge_id: str) -> FrozenSet[str]`
  Get identity edge as unordered set {v1, v2} per Dau's suggestion.
- `get_identity_edges(self) -> FrozenSet[str]`
  Get all identity edges (edges with relation name '=').
- `get_incident_vertices(self, edge_id: str) -> Tuple[str, ...]`
  Get incident vertices for edge via ν mapping.
- `get_isolated_vertices(self) -> FrozenSet[str]`
  Get all isolated vertices.
- `get_ligature_graph(self) -> Tuple[FrozenSet[str], FrozenSet[Tuple[str, str]]]`
  Get ligature graph (V, Eid) as vertex set and edge pairs.
- `get_ligatures(self) -> List[FrozenSet[str]]`
  Get all ligatures as connected components of identity edges.
- `get_nesting_depth(self, element_id: str) -> int`
  Get nesting depth of element (number of cuts enclosing it).
- `get_relation_name(self, edge_id: str) -> str`
  Get relation name for edge.
- `get_vertex(self, vertex_id: str) -> egi_core_dau.Vertex`
  Get vertex by ID.
- `get_vertex_at_hook(self, edge_id: str, position: int) -> str`
  Get vertex attached to hook (edge_id, position).
- `get_vertex_hooks(self, vertex_id: str) -> List[Tuple[str, int]]`
  Get all hooks that vertex is attached to.
- `get_vertex_ligature(self, vertex_id: str) -> FrozenSet[str]`
  Get the ligature containing the specified vertex.
- `has_dominating_nodes(self) -> bool`
  Check if graph has dominating nodes (Dau's Definition 12.5).
- `is_branching_point(self, vertex_id: str) -> bool`
  Check if vertex is a branching point (attached to more than 2 hooks).
- `is_evenly_enclosed(self, element_id: str) -> bool`
  Check if element is evenly enclosed (Dau's Definition 12.4).
- `is_negative_context(self, context_id: str) -> bool`
  Check if context is negative (evenly enclosed cut).
- `is_oddly_enclosed(self, element_id: str) -> bool`
  Check if element is oddly enclosed (Dau's Definition 12.4).
- `is_positive_context(self, context_id: str) -> bool`
  Check if context is positive (sheet or oddly enclosed cut).
- `is_vertex_isolated(self, vertex_id: str) -> bool`
  Check if vertex is isolated (not incident to any edge).
- `remove_vertex_from_ligature(self, vertex_id: str) -> 'RelationalGraphWithCuts'`
  Remove vertex from ligature (reverse of add_vertex_to_ligature).
- `replace_vertex_on_hook(self, edge_id: str, position: int, new_vertex_id: str) -> 'RelationalGraphWithCuts'`
  Replace vertex on hook (edge_id, position) with new vertex (Definition 12.9).
- `with_cut(self, cut: egi_core_dau.Cut, context_id: str = None) -> 'RelationalGraphWithCuts'`
  Create new graph with additional cut.
- `with_edge(self, edge: egi_core_dau.Edge, vertex_sequence: Tuple[str, ...], relation_name: str, context_id: str = None) -> 'RelationalGraphWithCuts'`
  Create new graph with additional edge.
- `with_vertex(self, vertex: egi_core_dau.Vertex) -> 'RelationalGraphWithCuts'`
  Create new graph with additional vertex in sheet of assertion.
- `with_vertex_in_context(self, vertex: egi_core_dau.Vertex, context_id: str) -> 'RelationalGraphWithCuts'`
  Create new graph with additional vertex in specified context.
- `with_vertex_moved_to_context(self, vertex_id: str, new_context_id: str) -> 'RelationalGraphWithCuts'`
  Return a new graph with the given vertex relocated to a different context.
- `without_element(self, element_id: str) -> 'RelationalGraphWithCuts'`
  Create new graph without specified element.

#### `Vertex`

Vertex in Dau's formalism - can be generic (*x) or constant ("Socrates").

**Methods**:

- `__init__(self, id: str, label: Optional[str] = None, is_generic: bool = True) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__post_init__(self)`
- `__repr__(self)`
  Return repr(self).

### Functions

#### `create_cut() -> egi_core_dau.Cut`

Create new cut with unique ID.

#### `create_edge() -> egi_core_dau.Edge`

Create new edge with unique ID.

#### `create_empty_graph() -> egi_core_dau.RelationalGraphWithCuts`

Create empty graph (Dau's G_∅).

#### `create_vertex(label: Optional[str] = None, is_generic: bool = True) -> egi_core_dau.Vertex`

Create new vertex with unique ID.

---

## egi_io.py

**Path**: `src/egi_io.py`  
**Status**: Protected Core Module

### Module Description

EGI JSON serialization utilities.

Schema produced/consumed matches tools/migrate_corpus_to_egi.py 
egi_to_dict.

### Functions

#### `from_dict(d: 'Dict[str, Any]') -> 'RelationalGraphWithCuts'`

#### `load_egi_json(path: 'str | Path') -> 'RelationalGraphWithCuts'`

#### `save_egi_json(egi: 'RelationalGraphWithCuts', path: 'str | Path') -> 'None'`

#### `to_dict(egi: 'RelationalGraphWithCuts') -> 'Dict[str, Any]'`

---

## egi_transformation_history.py

**Path**: `src/egi_transformation_history.py`  
**Status**: Protected Core Module

### Module Description

EGI Transformation History Data Model

Captures complete transformation sequences with state versioning, enabling:
- Recovery of any historical state
- Viewing transformation sequences between states
- Rollback and branching capabilities
- Provenance tracking for logical reasoning

### Classes

#### `EGITransformationHistory`

Complete transformation history for an EGI with versioning and branching.

Key capabilities:
- State snapshots at each transformation step
- Bidirectional transformation tracking
- Branch management for exploration and alternatives
- Efficient state recovery and sequence viewing
- Provenance tracking for logical reasoning

**Methods**:

- `__init__(self, initial_egi: egi_core_dau.RelationalGraphWithCuts, description: str = 'Initial state')`
  Initialize self.  See help(type(self)) for accurate signature.
- `add_transformation(self, rule_name: str, context: formal_transformation_rules.TransformationContext, result: formal_transformation_rules.TransformationResult, user_annotation: Optional[str] = None) -> str`
  Add a transformation step and create new state.
- `create_branch_from_state(self, source_state_id: str, branch_type: egi_transformation_history.HistoryBranchType = <HistoryBranchType.EXPLORATION: 'exploration'>, description: str = 'New exploration branch') -> str`
  Create a new branch from an existing state.
- `create_exploration_branch(self, description: str) -> str`
  Create a new exploration branch from current state.
- `export_history_data(self) -> Dict[str, Any]`
  Export complete history data for persistence.
- `get_active_branches(self) -> List[egi_transformation_history.HistoryBranch]`
  Get all active (non-merged) branches.
- `get_all_branches(self) -> List[egi_transformation_history.HistoryBranch]`
  Get all branches in the history.
- `get_all_paths_from_root(self, target_state_id: str) -> List[List[str]]`
  Get all paths from root to target state (supports multiple paths in DAG).
- `get_branch_points(self) -> List[str]`
  Get all branch point state IDs.
- `get_child_states(self, state_id: str) -> List[str]`
  Get all immediate child states (direct descendants in DAG).
- `get_current_state(self) -> egi_transformation_history.StateSnapshot`
  Get the current state.
- `get_dag_statistics(self) -> Dict[str, Any]`
  Get statistics about the DAG structure.
- `get_history_statistics(self) -> Dict[str, Any]`
  Get statistics about the transformation history.
- `get_state(self, state_id: str) -> Optional[egi_transformation_history.StateSnapshot]`
  Get a specific state snapshot.
- `get_transformation_sequence(self, from_state_id: str, to_state_id: str) -> egi_transformation_history.TransformationSequence`
  Get the sequence of transformations between two states using BFS.
- `is_branch_point(self, state_id: str) -> bool`
  Check if a state is a branch point (has multiple outgoing edges).
- `rollback_to_state(self, target_state_id: str, create_branch: bool = True) -> bool`
  Rollback to a previous state, optionally creating a branch.

#### `HistoryBranch`

A branch in the transformation history tree.

**Methods**:

- `__init__(self, branch_id: str, branch_type: egi_transformation_history.HistoryBranchType, parent_state_id: str, created_timestamp: datetime.datetime, description: str, is_active: bool = True, metadata: frozendict.frozendict[str, typing.Any] = <factory>) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `HistoryBranchType`

Type of branching in transformation history.

#### `LogicalProvenance`

Captures the logical reasoning and rule citations for a transformation.

**Methods**:

- `__init__(self, rule_citation: str, logical_equivalence: str, semantic_interpretation: str, proof_obligations: List[str] = <factory>, domain_assumptions: List[str] = <factory>, ontological_commitments: List[str] = <factory>) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `StateSnapshot`

Immutable snapshot of an EGI state with domain model integration.

**Methods**:

- `__init__(self, state_id: str, egi: egi_core_dau.RelationalGraphWithCuts, timestamp: datetime.datetime, step_number: int, description: str, domain_model: Optional[Any] = None, active_domain_contexts: Set[str] = <factory>, linear_forms: Dict[str, str] = <factory>, diagram_metadata: Dict[str, Any] = <factory>, natural_language_summary: Optional[str] = None, metadata: frozendict.frozendict[str, typing.Any] = <factory>) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__post_init__(self)`
- `__repr__(self)`
  Return repr(self).

#### `TransformationSequence`

A sequence of transformation steps between two states.

**Methods**:

- `__init__(self, from_state_id: str, to_state_id: str, steps: List[egi_transformation_history.TransformationStep], total_steps: int, is_valid_path: bool, logical_summary: Optional[str] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `TransformationStatus`

Status of a transformation step.

#### `TransformationStep`

Record of a single transformation step with rich semantic context.

**Methods**:

- `__init__(self, step_id: str, rule_name: str, from_state_id: str, to_state_id: str, context: formal_transformation_rules.TransformationContext, result: formal_transformation_rules.TransformationResult, timestamp: datetime.datetime, status: egi_transformation_history.TransformationStatus, logical_provenance: Optional[egi_transformation_history.LogicalProvenance] = None, affected_domain_contexts: Set[str] = <factory>, natural_language_description: Optional[str] = None, user_annotation: Optional[str] = None, author_id: Optional[str] = None, reviewer_ids: Set[str] = <factory>, approval_status: Optional[str] = None, metadata: frozendict.frozendict[str, typing.Any] = <factory>) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

---

## egif_generator_dau.py

**Path**: `src/egif_generator_dau.py`  
**Status**: Protected Core Module

### Module Description

Fixed Dau-compliant EGIF generator with proper variable scoping.
Fixes the critical issue where variables defined in cuts were not marked as defining.

Key fix: Variables that first appear in any context (including cuts) are marked as defining (*x).

### Classes

#### `EGIFGenerator`

Generates EGIF expressions from Dau-compliant graphs with proper variable scoping.

**Methods**:

- `__init__(self, graph: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
  Initialize self.  See help(type(self)) for accurate signature.
- `generate(self) -> str`
  Generate EGIF expression from graph.
- `generate_egif(self, graph: egi_core_dau.RelationalGraphWithCuts) -> str`
  Legacy API: egif_gen.generate_egif(graph) -> str

### Functions

#### `generate_egif(graph: egi_core_dau.RelationalGraphWithCuts) -> str`

Generate EGIF expression from Dau-compliant graph.

---

## egif_parser_dau.py

**Path**: `src/egif_parser_dau.py`  
**Status**: Protected Core Module

### Module Description

Dau-compliant EGIF parser that builds RelationalGraphWithCuts structures.
Supports isolated vertices, proper syntax validation, and Dau's 6+1 component model.

Key improvements over previous parser:
- Supports isolated vertices (*x, "Socrates") as per Dau's "heavy dot" rule
- Builds proper Dau-compliant structures with area/context distinction
- Comprehensive syntax validation before processing
- Proper handling of generic vs constant vertices

### Classes

#### `EGIFLexer`

Lexical analyzer for EGIF expressions with isolated vertex support.

**Methods**:

- `__init__(self, text: str)`
  Initialize self.  See help(type(self)) for accurate signature.
- `tokenize(self) -> List[egif_parser_dau.Token]`
  Scan the EGIF text and produce a flat list of Tokens.

#### `EGIFParser`

Parser for EGIF expressions that builds Dau-compliant structures.

**Methods**:

- `__init__(self, text: str)`
  Initialize self.  See help(type(self)) for accurate signature.
- `parse(self) -> egi_core_dau.RelationalGraphWithCuts`
  Parse EGIF expression into Dau-compliant graph.

#### `EGIFSyntaxValidator`

Validates EGIF syntax before parsing.

**Methods**:

- `__init__(self, tokens: List[egif_parser_dau.Token])`
  Initialize self.  See help(type(self)) for accurate signature.
- `validate(self) -> bool`
  Validate EGIF syntax.

#### `Token`

Token in EGIF expression.

**Methods**:

- `__init__(self, type: egif_parser_dau.TokenType, value: str, position: int) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `TokenType`

Token types for EGIF lexical analysis.

### Functions

#### `parse_egif(text: str) -> egi_core_dau.RelationalGraphWithCuts`

Parse EGIF expression into Dau-compliant graph.

---

## formal_transformation_rules.py

**Path**: `src/formal_transformation_rules.py`  
**Status**: Protected Core Module

### Module Description

Formal EG transformation rules implementing precise Peirce-Dau formalism.
Each rule has clear preconditions, transformations, and postconditions.

### Classes

#### `DeiterationRule`

IT- (Dau §14.4): Deiteration Rule.

The inverse of Iteration: a subgraph may be erased from an area if an
isomorphic copy of it exists in the same area or in any enclosing area
(i.e., the subgraph could have been placed there by IT+).  Logically this
removes a redundant repeated assertion, preserving truth.

Polarity: IT- may be applied in any polarity area (unlike ERA, which is
positive-only).

Preconditions (Dau §14.4):
    - ``context.selected_subgraph`` must be non-empty.
    - A structurally isomorphic copy of the subgraph must exist in the
      target area or in an enclosing area (the "nest of cuts").
      Structural identity is checked via ``IsomorphismValidator``.

Result: the selected subgraph is erased, delegating to ``ErasureRule``
with the polarity constraint overridden.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply IT- by erasing the selected (iterated) subgraph.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  IT- requires a selected subgraph to delete if there is an identical
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).
- `is_valid(self, egi: egi_core_dau.RelationalGraphWithCuts, selected_subgraph: FrozenSet[str]) -> bool`
  Check if deiteration is valid for the selected subgraph.

#### `DoubleCutErasureRule`

DC- (Dau §14.3): Double Cut Erasure Rule.

Removes a pair of adjacent nested cuts, releasing their contents into the
enclosing area.  Applicable in any polarity area (the double cut is
semantically transparent, so its removal is always valid).

Preconditions (Dau §14.3):
    - Exactly one cut must be selected (the outer cut).
    - That outer cut must contain exactly one element, which must itself
      be a cut (the inner cut).
    - The inner cut may contain arbitrary content.

Result: both cuts are removed and the inner cut's contents are placed
directly into the area that formerly contained the outer cut.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply DC- by removing the outer and inner cuts, merging contents upward.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  DC- requires identifying a subgraph that has a single cut enclosing
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `DoubleCutInsertionRule`

DC+ (Dau §14.3): Double Cut Insertion Rule.

Inserts a pair of nested cuts around any subgraph (or around nothing,
yielding two empty nested cuts) in any area regardless of polarity.
Because a double cut is semantically transparent — the two negations
cancel — the rule is truth-preserving in all polarities.

Preconditions (Dau §14.3):
    - The target area must exist in the EGI.
    - Every element of the selected subgraph must live directly in the
      target area (not inside a nested cut within that area).

Result: a new outer cut O and inner cut I are created; O lives in
target_area, I lives inside O, and the selected subgraph moves inside I.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply DC+ by inserting a pair of nested cuts around the selected elements.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  DC+ can be applied in any area to enclose any subgraph (including empty).
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `ErasureRule`

ERA (Dau §14.1): Erasure Rule.

Any closed subgraph may be erased from a positively-enclosed area (even
nesting depth).  Logically this is weakening in a positive context, which
is truth-preserving.

Preconditions (Dau §14.1):
    - The target area must have positive polarity (even nesting depth,
      including the sheet of assertion at depth 0).
    - The subgraph to erase must be *closed* per Dau's definition: no
      edge in the subgraph has an endpoint outside the subgraph.
    - All selected elements must reside directly in the target area.

Result: the selected closed subgraph (including any cuts and their
recursive contents) is removed from the EGI.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply ERA by removing the closed subgraph from the positive area.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  ERA requires a positively-enclosed area and a CLOSED subgraph therein to erase.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `FormalTransformationEngine`

Engine for applying formal EG transformation rules.

**Methods**:

- `__init__(self)`
  Initialize self.  See help(type(self)) for accurate signature.
- `apply_rule(self, rule_name: str, source_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, selected_subgraph: FrozenSet[str]) -> formal_transformation_rules.TransformationResult`
  Apply a transformation rule to an EGI.
- `describe_rule(self, rule_name: str) -> str`
  Get description of a transformation rule.
- `get_available_rules(self) -> List[str]`
  Get list of available transformation rules.

#### `FormalTransformationRule`

Abstract base class for formal EG transformation rules.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply the transformation rule to create a new EGI.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  Check if the rule can be applied in the given context.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `HeavyDotInsertionRule`

Heavy Dot Insertion Rule - Insert individual vertex in negative context

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply heavy dot insertion by adding a single vertex to the negative area.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  Heavy dot insertion requires a negatively-enclosed area.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `InsertionRule`

INS (Dau §14.2): Insertion Rule.

Any closed graph may be inserted into a negatively-enclosed area (odd
nesting depth).  Logically this corresponds to weakening inside a
negation, which is truth-preserving.

Preconditions (Dau §14.2):
    - The target area must have negative polarity (odd nesting depth).
    - The subgraph to insert must be *closed* per Dau's definition: no
      edge in the subgraph has an endpoint outside the subgraph.

Result: the closed subgraph (and any vertices needed to make it closed)
is added to the negative target area.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply INS by adding the specified closed subgraph to the negative area.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  INS requires a CLOSED graph to insert and a negatively-enclosed area to insert it.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `IterationRule`

IT+ (Dau §14.4): Iteration Rule.

A subgraph in area A may be copied into any area B that is enclosed by A
(i.e., B is a descendant of A in the cut hierarchy, or B == A).
Logically this is conjunction introduction — adding a repeated assertion
deeper in the graph — which is truth-preserving.

Preconditions (Dau §14.4):
    - ``context.selected_subgraph`` must be non-empty.
    - ``context.target_area`` must exist in the EGI.
    - The destination area must be enclosed by (or equal to) the source
      area that directly contains the selected elements.

Result: all selected elements (vertices, edges, cuts and their recursive
interiors) are deep-copied with fresh UUID-based IDs and the copies are
added to ``context.target_area``.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply IT+ by deep-copying the selected subgraph into the target area.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  IT+ requires:
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `TransformationContext`

Context information for applying a transformation.

**Methods**:

- `__init__(self, source_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, selected_subgraph: FrozenSet[str], area_polarity: egi_core_dau.AreaPolarity, nesting_depth: int, enclose_empty: bool = False) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `TransformationResult`

Result of applying a transformation rule.

**Methods**:

- `__init__(self, success: bool, result_egi: Optional[egi_core_dau.RelationalGraphWithCuts], error_message: Optional[str], changes_made: Dict[str, Any]) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

### Functions

#### `create_test_egi() -> egi_core_dau.RelationalGraphWithCuts`

Create a test EGI for demonstration purposes.

#### `demonstrate_transformation_rules()`

Demonstrate each transformation rule with test sequences.

---

## graph_isomorphism_engine.py

**Path**: `src/graph_isomorphism_engine.py`  
**Status**: Protected Core Module

### Module Description

Graph Isomorphism Engine for Existential Graphs

This module provides comprehensive graph isomorphism testing for EGI structures,
serving as the foundation for:
1. IT- (deiteration) transformation validation
2. Endoporeutic Game proof verification
3. General structural equivalence checking

Implementation uses NetworkX VF2 (Vento-Foggia) algorithm, which is polynomial
in the number of nodes in practice — replacing the previous O(n!) enumeration.

EGI subgraphs are encoded as NetworkX MultiDiGraphs:
  - Vertices     → nodes with ntype='v', label, is_generic
  - Edges (n-ary)→ nodes with ntype='e', rel, arity
  - Cuts         → nodes with ntype='c'
  - ν(e, pos)=v  → MultiDiGraph edge e→v with etype='nu', pos=pos
  - area(c) ∋ x  → MultiDiGraph edge c→x with etype='contains'

### Classes

#### `GraphIsomorphismEngine`

Engine for testing structural isomorphism between EGI subgraphs.

Uses NetworkX VF2 (polynomial) instead of O(n!) permutation enumeration.

Implements Dau's requirements for structural identity:
- Vertex identity: same label and generic status
- Edge identity: same relation name (κ) and ordered vertex sequence (ν)
- Cut identity: same containment structure recursively

**Methods**:

- `find_isomorphic_subgraphs(self, egi: egi_core_dau.RelationalGraphWithCuts, target_subgraph: FrozenSet[str], search_areas: List[str]) -> List[Tuple[str, FrozenSet[str], graph_isomorphism_engine.IsomorphismMapping]]`
  Find all subgraphs isomorphic to target_subgraph within specified areas.
- `test_cross_egi_isomorphism(self, egi1: egi_core_dau.RelationalGraphWithCuts, subgraph1: FrozenSet[str], egi2: egi_core_dau.RelationalGraphWithCuts, subgraph2: FrozenSet[str]) -> graph_isomorphism_engine.IsomorphismResult`
  Test isomorphism between subgraphs in different EGIs.
- `test_subgraph_isomorphism(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph1: FrozenSet[str], subgraph2: FrozenSet[str]) -> graph_isomorphism_engine.IsomorphismResult`
  Test if two subgraphs within the same EGI are structurally isomorphic.

#### `IsomorphismMapping`

Complete mapping between two isomorphic subgraphs.

**Methods**:

- `__init__(self, vertex_mapping: Dict[str, str], edge_mapping: Dict[str, str], cut_mapping: Dict[str, str]) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `IsomorphismResult`

Result of isomorphism testing.

**Methods**:

- `__init__(self, is_isomorphic: bool, mapping: Optional[graph_isomorphism_engine.IsomorphismMapping], reason: Optional[str]) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `IsomorphismValidator`

High-level validator for common isomorphism testing scenarios.
Provides convenient interfaces for IT- and Endoporeutic Game use cases.

**Methods**:

- `__init__(self)`
  Initialize self.  See help(type(self)) for accurate signature.
- `validate_deiteration_candidate(self, egi: egi_core_dau.RelationalGraphWithCuts, target_subgraph: FrozenSet[str], target_area: str, nesting_hierarchy: List[str]) -> Tuple[bool, Optional[str]]`
  Validate IT- deiteration by finding isomorphic subgraph in nesting hierarchy.
- `validate_endoporeutic_claim(self, domain_egi: egi_core_dau.RelationalGraphWithCuts, claim_egi: egi_core_dau.RelationalGraphWithCuts, domain_subgraph: FrozenSet[str], claim_subgraph: FrozenSet[str]) -> Tuple[bool, Optional[graph_isomorphism_engine.IsomorphismMapping]]`
  Validate Endoporeutic Game claim by testing cross-EGI isomorphism.

---

## hierarchical_index.py

**Path**: `src/hierarchical_index.py`  
**Status**: Protected Core Module

### Module Description

Hierarchical index for EGI cut nesting relationships.

This provides efficient O(1) lookup of nesting levels and containment relationships
that are fundamental to EGI logical semantics, not just spatial representation.
The hierarchical structure is core to transformation rules like IT+/IT-.

### Classes

#### `HierarchicalIndex`

Efficient hierarchical index for EGI cut nesting relationships.

This is integral to EGI logic for:
- Polarity calculation (positive/negative areas)
- Transformation rule validation (IT+/IT- nesting requirements)
- Containment queries for logical operations

**Methods**:

- `__init__(self)`
  Initialize self.  See help(type(self)) for accurate signature.
- `add_area(self, area_id: str, parent_area: Optional[str] = None) -> bool`
  Add an area to the hierarchical index.
- `get_ancestors(self, area_id: str) -> List[str]`
  Get all ancestors from area to sheet. Returns path from area to sheet.
- `get_areas_at_level(self, level: int) -> List[str]`
  Get all areas at a specific nesting level.
- `get_children(self, area_id: str) -> Set[str]`
  Get direct children of an area. O(1) lookup.
- `get_negative_areas(self) -> List[str]`
  Get all negative polarity areas.
- `get_nesting_level(self, area_id: str) -> Optional[int]`
  Get the nesting level of an area. O(1) lookup.
- `get_parent(self, area_id: str) -> Optional[str]`
  Get the parent area of an area. O(1) lookup.
- `get_polarity(self, area_id: str) -> Optional[str]`
  Get the polarity of an area. O(1) lookup.
- `get_positive_areas(self) -> List[str]`
  Get all positive polarity areas.
- `get_statistics(self) -> Dict[str, <built-in function any>]`
  Get statistics about the hierarchical index.
- `is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool`
  Check if ancestor_id is an ancestor of descendant_id.
- `remove_area(self, area_id: str) -> bool`
  Remove an area and update parent's children.
- `validate_containment(self, container_id: str, contained_id: str) -> bool`
  Validate that container can contain the contained area.

#### `NestingInfo`

Information about an area's position in the nesting hierarchy.

**Methods**:

- `__init__(self, area_id: str, nesting_level: int, parent_area: Optional[str], child_areas: Set[str]) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

---

## ligature_manipulation_rules.py

**Path**: `src/ligature_manipulation_rules.py`  
**Status**: Protected Core Module

### Module Description

Chapter 16 Ligature Manipulation Rules implementing Dau's formalism.
These rules allow rearranging ligatures while preserving logical meaning.

### Classes

#### `ExtendRestrictLigatureRule`

Lemma 16.2: Extending or Restricting a Ligature in a Context
Allows adding new identity networks to existing ligatures.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply ligature extension by adding new identity network.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  Requires a vertex on an existing ligature and specification of new identity network.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `LigatureManipulationEngine`

Engine for applying ligature manipulation rules from Dau Chapter 16.

**Methods**:

- `__init__(self)`
  Initialize self.  See help(type(self)) for accurate signature.
- `apply_rule(self, rule_name: str, source_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, selected_subgraph: FrozenSet[str]) -> formal_transformation_rules.TransformationResult`
  Apply a ligature manipulation rule to an EGI.
- `describe_rule(self, rule_name: str) -> str`
  Get description of a ligature manipulation rule.
- `get_available_rules(self) -> List[str]`
  Get list of available ligature manipulation rules.

#### `LigatureRearrangementRule`

Definition 16.4: Rearranging Ligatures in a Context
Replaces ligature (W,F) with new ligature (W',F') in same context.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply Dau Definition 16.4 ligature rearrangement.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  Requires selection of ligature vertices and specification of new structure.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `MoveBranchesAlongLigatureRule`

Lemma 16.1: Moving Branches along a Ligature in a Context
Allows repositioning vertices along the same ligature while preserving identity.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply branch moving by repositioning vertex on ligature.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  Requires two vertices on the same ligature in the same context.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

#### `RetractLigatureRule`

Lemma 16.3: Retracting a Ligature in a Context
Collapses an entire ligature (W,F) to a single vertex w0.

**Methods**:

- `apply_transformation(self, context: formal_transformation_rules.TransformationContext) -> formal_transformation_rules.TransformationResult`
  Apply ligature retraction by collapsing to single vertex.
- `calculate_area_polarity(self, egi: egi_core_dau.RelationalGraphWithCuts, area_id: str) -> Tuple[egi_core_dau.AreaPolarity, int]`
  Calculate the polarity and nesting depth of an area.
- `check_preconditions(self, context: formal_transformation_rules.TransformationContext) -> Tuple[bool, Optional[str]]`
  Requires selection of ligature vertices and specification of target vertex.
- `get_rule_name(self) -> str`
  Get the name of this transformation rule.
- `is_closed_subgraph(self, egi: egi_core_dau.RelationalGraphWithCuts, subgraph: FrozenSet[str]) -> bool`
  Check if subgraph is closed per Dau's Definition (no external connections).

### Functions

#### `demonstrate_ligature_manipulation()`

Demonstrate ligature manipulation rules.

---

## rule_interaction.py

**Path**: `src/rule_interaction.py`  
**Status**: Protected Core Module

### Module Description

Rule Interaction Protocol — headless, platform-independent bridge between
user actions and formal transformation rule application.

Each of Dau's six rules has a distinct interaction pattern:

    DC+  Subject + spot: select elements to enclose, or a spot (area) for an
                      empty double cut around nothing (both optional).
    DC-  Single-step: select the outer cut of a double-cut pair.
    ERA  Single-step: select a closed subgraph in a positive area.
    INS  Two-step:    (a) provide content to insert (EGIF or subgraph),
                      (b) select a negative target area.
    IT+  Two-step:    (a) select source subgraph,
                      (b) select destination area (more deeply nested).
    IT-  Single-step: select candidate copy (engine verifies isomorphism
                      with original in enclosing area).

This module provides a ``RuleInteraction`` for each rule that:
- Declares the required interaction steps
- Validates user input at each step
- Builds a valid ``TransformationContext`` when all steps are complete
- Applies the rule and returns the result

No GUI dependency — this is pure logic.

### Classes

#### `ApplyResult`

Result of applying a rule through the interaction protocol.

**Methods**:

- `__init__(self, success: bool, result_egi: Optional[egi_core_dau.RelationalGraphWithCuts] = None, rule_name: str = '', message: str = '', changes_made: Dict[str, Any] = <factory>, transformation_result: Optional[formal_transformation_rules.TransformationResult] = None, context: Optional[formal_transformation_rules.TransformationContext] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `DCMinusInteraction`

DC- (Double Cut Erasure): select the outer cut of a double-cut pair.

**Methods**:

- `apply(self, state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`
  Validate all steps, build context, apply rule.
- `build_context(self, state)`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step, user_input, state)`
  Validate user input for one step. Returns StepResult.

#### `DCPlusInteraction`

DC+ (Double Cut Insertion): enclose a subject, or a spot around nothing.

Two optional steps, following the Spot/Subject grammar:

- ``select`` (the Subject): the elements to enclose.  When non-empty, the
  double cut wraps exactly those elements (in their common area).
- ``select_area`` (the Spot): the area to place the double cut in.  When
  the Subject is empty but a Spot is given, an *empty* double cut is
  inserted there — a double negative around nothing, even in a non-empty
  area (``enclose_empty``).

With neither step provided, DC+ falls back to the convenience default:
enclose every element currently on the sheet.

**Methods**:

- `apply(self, state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`
  Validate all steps, build context, apply rule.
- `build_context(self, state)`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step, user_input, state)`
  Validate user input for one step. Returns StepResult.

#### `ERAInteraction`

ERA (Erasure): select a closed subgraph in a positive area.

**Methods**:

- `apply(self, state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`
  Validate all steps, build context, apply rule.
- `build_context(self, state)`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step, user_input, state)`
  Validate user input for one step. Returns StepResult.

#### `INSInteraction`

INS (Insertion): provide content + select a negative target area.

Content is provided as EGIF text.  The engine parses it, assigns fresh
IDs to avoid collisions, and merges the parsed graph's sheet-level
elements into the target area.

**Methods**:

- `apply(self, state)`
  Override apply to use the unified INS implementation.
- `build_context(self, state)`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step, user_input, state)`
  Validate user input for one step. Returns StepResult.

#### `ITMinusInteraction`

IT- (Deiteration): select candidate copy; engine verifies isomorphism.

**Methods**:

- `apply(self, state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`
  Validate all steps, build context, apply rule.
- `build_context(self, state)`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step, user_input, state)`
  Validate user input for one step. Returns StepResult.

#### `ITPlusInteraction`

IT+ (Iteration): copy subgraph to a more deeply nested area.

**Methods**:

- `apply(self, state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`
  Validate all steps, build context, apply rule.
- `build_context(self, state)`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step, user_input, state)`
  Validate user input for one step. Returns StepResult.

#### `InteractionState`

Tracks progress through a multi-step interaction.

**Methods**:

- `__init__(self, rule_name: str, egi: egi_core_dau.RelationalGraphWithCuts, completed_steps: Dict[str, rule_interaction.StepResult] = <factory>, is_complete: bool = False, error: Optional[str] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `InteractionStep`

One step in a rule's interaction workflow.

**Methods**:

- `__init__(self, step_id: str, kind: rule_interaction.StepKind, prompt: str, optional: bool = False) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `RuleInteraction`

Base class for rule-specific interaction workflows.

Subclasses override ``steps``, ``validate_step``, and ``build_context``.
The ``apply`` method is final — it validates all steps, builds the context,
checks preconditions, and applies the rule.

**Methods**:

- `apply(self, state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`
  Validate all steps, build context, apply rule.
- `build_context(self, state: rule_interaction.InteractionState) -> formal_transformation_rules.TransformationContext`
  Build a TransformationContext from completed steps.
- `steps(self) -> List[rule_interaction.InteractionStep]`
  Declare the interaction steps this rule requires.
- `validate_step(self, step: rule_interaction.InteractionStep, user_input: Any, state: rule_interaction.InteractionState) -> rule_interaction.StepResult`
  Validate user input for one step. Returns StepResult.

#### `StepKind`

Kind of user input a step requires.

#### `StepResult`

Validated result of one interaction step.

**Methods**:

- `__init__(self, step_id: str, valid: bool, data: Any = None, message: str = '', expanded_selection: Optional[FrozenSet[str]] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

### Functions

#### `advance_interaction(state: rule_interaction.InteractionState, user_input: Any) -> rule_interaction.StepResult`

Advance an interaction by providing input for the next incomplete step.

Finds the first step not yet in ``state.completed_steps`` and validates
``user_input`` against it.

#### `apply_interaction(state: rule_interaction.InteractionState) -> rule_interaction.ApplyResult`

Apply the rule after all interaction steps are complete.

#### `begin_interaction(rule_name: str, egi: egi_core_dau.RelationalGraphWithCuts) -> rule_interaction.InteractionState`

Start a new interaction session for a rule.

#### `get_interaction(rule_name: str) -> rule_interaction.RuleInteraction`

Get the interaction workflow for a rule by name.

#### `insert_from_egif(host_egi: egi_core_dau.RelationalGraphWithCuts, target_area: str, egif_text: str) -> formal_transformation_rules.TransformationResult`

Parse EGIF and merge its sheet-level elements into target_area.

This is the canonical insertion implementation, used by both the
interaction protocol (INSInteraction) and the Endoporeutic Game engine.

Fresh UUIDs are assigned to all inserted elements to avoid ID collisions.
Nested cuts and their contents are copied recursively.

Args:
    host_egi: The graph to insert into.
    target_area: The area (must be negative) to receive the new elements.
    egif_text: EGIF string describing the content to insert.

Returns:
    TransformationResult with the updated EGI on success.

---

## single_object_ligature_detector.py

**Path**: `src/single_object_ligature_detector.py`  
**Status**: Protected Core Module

### Module Description

Definition 16.8: Single-Object Ligature Detection
Implements Dau's formal definition for identifying ligatures that represent single objects.

### Classes

#### `LigatureAnalysis`

Analysis result for a ligature structure.

**Methods**:

- `__init__(self, vertices: Set[str], identity_edges: Set[str], is_single_object: bool, violation_reasons: List[str], context_mapping: Dict[str, str], cycles: List[List[str]]) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `SingleObjectLigatureDetector`

Implements Dau's Definition 16.8 for detecting single-object ligatures.

A ligature (W,F) is single-object iff:
1. No identity-link f in F with w1 f w2 where f < w1 and f < w2
2. No vertices w1, w2, w in W and f1, f2 in F with w1 != w2, w1 f1 w f2 w2,
   where w < w1 and w < w2
3. No vertices w1, w2 in W in a cycle where w2 < w1

**Methods**:

- `__init__(self, egi: Optional[egi_core_dau.RelationalGraphWithCuts] = None)`
  Initialize detector with optional EGI.
- `is_single_object_ligature(self, ligature_vertices: List[str]) -> Tuple[bool, List[str]]`
  Check if ligature represents a single object.
- `separate_into_single_object_components(self, ligature_vertices: List[str]) -> List[List[str]]`
  Separate ligature into single-object components.

### Functions

#### `demonstrate_single_object_ligature_detection()`

Demonstrate single-object ligature detection.

---

## subgraph_closure_validator.py

**Path**: `src/subgraph_closure_validator.py`  
**Status**: Protected Core Module

### Module Description

Subgraph closure validation for INS/ERA transformations.

Per Dau's formalism, INS and ERA only apply to CLOSED subgraphs - subgraphs with
no connections to elements outside the subgraph. This module provides:

1. Validation: Check if a selection forms a closed subgraph
2. Expansion: Automatically expand incomplete selections to achieve closure
3. Feedback: Detailed information about missing elements and closure violations

Beta graph support
------------------
In Beta graphs, lines of identity (vertices) can cross cut boundaries.  An edge
in area B may reference a vertex defined in an ancestor area A.  When computing
closure *relative to area B*, such vertices are **free** — they need not be
included in the subgraph.  Pass ``context_area`` to ``analyze_closure`` to
enable this Beta-aware behaviour.

### Classes

#### `ClosureAnalysis`

Result of analyzing subgraph closure.

**Methods**:

- `__init__(self, is_closed: bool, original_selection: FrozenSet[str], closed_subgraph: FrozenSet[str], violations: List[subgraph_closure_validator.ClosureViolation], added_elements: Set[str]) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).
- `get_summary(self) -> str`
  Get human-readable summary of closure analysis.

#### `ClosureViolation`

Describes why a subgraph is not closed.

**Methods**:

- `__init__(self, element_id: str, violation_type: str, missing_elements: Set[str], description: str) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).

#### `SubgraphClosureValidator`

Validates and expands subgraphs to ensure closure per Dau's requirements.

A closed subgraph must satisfy:
1. All edges in subgraph connect only to vertices in subgraph
   (Beta: vertices in ancestor areas of context_area are free)
2. All vertices in subgraph that have edges in the SAME area
   must have those edges in subgraph
3. All cuts in subgraph must have their full contents in subgraph
4. Ligatures connecting vertices must be fully contained

**Methods**:

- `__init__(self, egi: egi_core_dau.RelationalGraphWithCuts)`
  Initialize self.  See help(type(self)) for accurate signature.
- `analyze_closure(self, selection: FrozenSet[str], allow_expansion: bool = True, context_area: Optional[str] = None, for_erasure: bool = False) -> subgraph_closure_validator.ClosureAnalysis`
  Analyze if selection forms a closed subgraph.
- `get_expansion_description(self, analysis: subgraph_closure_validator.ClosureAnalysis) -> str`
  Get detailed description of what was added to achieve closure.
- `validate_for_transformation(self, selection: FrozenSet[str], rule_name: str, context_area: Optional[str] = None) -> Tuple[bool, str, FrozenSet[str]]`
  Validate selection for INS/ERA transformation.

### Functions

#### `create_validator(egi: egi_core_dau.RelationalGraphWithCuts) -> subgraph_closure_validator.SubgraphClosureValidator`

Factory function to create a closure validator.

---

## universe_of_discourse.py

**Path**: `src/universe_of_discourse.py`  
**Status**: Protected Core Module

### Module Description

Universe of Discourse - The Fundamental Entity

The Universe of Discourse (UoD) is the complete diachronic process of logical
reasoning. It captures both synchronic states (EGI snapshots) and diachronic
evolution (transformation history).

Key Insight:
- UoD = The entire film (diachronic process)
- EGI = A single frame (synchronic snapshot)
- Full meaning emerges from the sequence, not individual frames

Philosophical Foundation:
- Aligns with Peirce's pragmatism (meaning from transformations)
- Honors dialogical inquiry (justification through Endoporeutic Game)
- Captures fallibilism (knowledge evolves through inquiry)

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for complete philosophy

### Classes

#### `EntityCategory`

Category/provenance of Universe of Discourse.

Distinguishes between static imports (literature examples) and dynamic
reasoning sessions (user inquiry, proofs, games).

#### `EntityMetadata`

Metadata for a Universe of Discourse.

Captures identity, provenance, authorship, and temporal information
for both static and dynamic UoDs.

**Methods**:

- `__init__(self, uod_id: str, uod_type: universe_of_discourse.UoDType, name: str, description: str, category: universe_of_discourse.UoDCategory, created: datetime.datetime, last_modified: datetime.datetime, current_state_id: Optional[str] = None, total_states: int = 1, total_transformations: int = 0, authors: List[str] = <factory>, tags: Set[str] = <factory>, corpus_path: Optional[pathlib._local.Path] = None, source_citation: Optional[str] = None, related_uods: List[str] = <factory>, domain_contexts: Set[str] = <factory>, natural_language_summary: Optional[str] = None, style_name: str = 'dau-compliant@1.0') -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).
- `from_dict(data: dict) -> 'UoDMetadata'`
  Deserialize from dictionary.
- `to_dict(self) -> dict`
  Serialize to dictionary.

#### `EntityType`

Type of Universe of Discourse.

Distinguishes between static (single state) and dynamic (full history) UoDs.

#### `GraphEntity`

The fundamental entity: a diachronic process of logical reasoning.

A Universe of Discourse (UoD) is NOT a static EGI diagram, but the complete
evolving environment in which EGIs exist, make sense, and undergo justified
transformations.

Components:
1. Transformation History (the log): Recorded sequence of justified rule applications
2. Synchronic States (the frames): (EGI, LayoutDeltas) at each point in time
3. In-forming Events (the driver): User actions that drive evolution

Metaphor: 
- UoD = The entire film (diachronic process)
- EGI = A single frame or photograph (synchronic snapshot)
- Full meaning emerges from watching the sequence unfold

Can represent:
1. Static UoD: Single EGI state, no history (literature imports)
2. Dynamic UoD: Complete transformation history (active reasoning)

Usage Across Modules:
- Organon (Archive): Browse history, explore states, export proofs
- Ergasterion (Workshop): Practice transformations (ephemeral, no main UoD)
- Agon (Arena): Validate changes, record history, Endoporeutic Game

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for complete philosophy

**Methods**:

- `__init__(self, metadata: universe_of_discourse.UoDMetadata, current_egi: egi_core_dau.RelationalGraphWithCuts, current_layout_deltas: Optional[Dict[str, Any]] = None, history: Optional[egi_transformation_history.EGITransformationHistory] = None, _current_egif: Optional[str] = None, _current_cgif: Optional[str] = None, _current_clif: Optional[str] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).
- `get_current_cgif(self) -> Optional[str]`
  Get CGIF (Conceptual Graph Interchange Format) for current state.
- `get_current_clif(self) -> Optional[str]`
  Get CLIF (Common Logic Interchange Format) for current state.
- `get_current_egif(self) -> str`
  Get EGIF (Existential Graph Interchange Format) for current state.
- `get_current_state(self) -> egi_transformation_history.StateSnapshot`
  Get the current state snapshot.
- `get_state(self, state_id: str) -> egi_transformation_history.StateSnapshot`
  Get a specific historical state by ID.
- `get_state_range(self, from_state_id: str, to_state_id: str) -> List[egi_transformation_history.StateSnapshot]`
  Get sequence of states between two points in history.
- `get_transformation(self, step_id: str) -> egi_transformation_history.TransformationStep`
  Get a specific transformation step by ID.
- `promote_to_historical(self, initial_description: str = 'Initial state')`
  Promote standalone UoD to historical by creating initial snapshot.
- `update_current_state(self, new_egi: egi_core_dau.RelationalGraphWithCuts, new_layout_deltas: Optional[Dict[str, Any]] = None)`
  Update current state (invalidates caches).

#### `UniverseOfDiscourse`

The fundamental entity: a diachronic process of logical reasoning.

A Universe of Discourse (UoD) is NOT a static EGI diagram, but the complete
evolving environment in which EGIs exist, make sense, and undergo justified
transformations.

Components:
1. Transformation History (the log): Recorded sequence of justified rule applications
2. Synchronic States (the frames): (EGI, LayoutDeltas) at each point in time
3. In-forming Events (the driver): User actions that drive evolution

Metaphor: 
- UoD = The entire film (diachronic process)
- EGI = A single frame or photograph (synchronic snapshot)
- Full meaning emerges from watching the sequence unfold

Can represent:
1. Static UoD: Single EGI state, no history (literature imports)
2. Dynamic UoD: Complete transformation history (active reasoning)

Usage Across Modules:
- Organon (Archive): Browse history, explore states, export proofs
- Ergasterion (Workshop): Practice transformations (ephemeral, no main UoD)
- Agon (Arena): Validate changes, record history, Endoporeutic Game

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for complete philosophy

**Methods**:

- `__init__(self, metadata: universe_of_discourse.UoDMetadata, current_egi: egi_core_dau.RelationalGraphWithCuts, current_layout_deltas: Optional[Dict[str, Any]] = None, history: Optional[egi_transformation_history.EGITransformationHistory] = None, _current_egif: Optional[str] = None, _current_cgif: Optional[str] = None, _current_clif: Optional[str] = None) -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).
- `get_current_cgif(self) -> Optional[str]`
  Get CGIF (Conceptual Graph Interchange Format) for current state.
- `get_current_clif(self) -> Optional[str]`
  Get CLIF (Common Logic Interchange Format) for current state.
- `get_current_egif(self) -> str`
  Get EGIF (Existential Graph Interchange Format) for current state.
- `get_current_state(self) -> egi_transformation_history.StateSnapshot`
  Get the current state snapshot.
- `get_state(self, state_id: str) -> egi_transformation_history.StateSnapshot`
  Get a specific historical state by ID.
- `get_state_range(self, from_state_id: str, to_state_id: str) -> List[egi_transformation_history.StateSnapshot]`
  Get sequence of states between two points in history.
- `get_transformation(self, step_id: str) -> egi_transformation_history.TransformationStep`
  Get a specific transformation step by ID.
- `promote_to_historical(self, initial_description: str = 'Initial state')`
  Promote standalone UoD to historical by creating initial snapshot.
- `update_current_state(self, new_egi: egi_core_dau.RelationalGraphWithCuts, new_layout_deltas: Optional[Dict[str, Any]] = None)`
  Update current state (invalidates caches).

#### `UoDCategory`

Category/provenance of Universe of Discourse.

Distinguishes between static imports (literature examples) and dynamic
reasoning sessions (user inquiry, proofs, games).

#### `UoDMetadata`

Metadata for a Universe of Discourse.

Captures identity, provenance, authorship, and temporal information
for both static and dynamic UoDs.

**Methods**:

- `__init__(self, uod_id: str, uod_type: universe_of_discourse.UoDType, name: str, description: str, category: universe_of_discourse.UoDCategory, created: datetime.datetime, last_modified: datetime.datetime, current_state_id: Optional[str] = None, total_states: int = 1, total_transformations: int = 0, authors: List[str] = <factory>, tags: Set[str] = <factory>, corpus_path: Optional[pathlib._local.Path] = None, source_citation: Optional[str] = None, related_uods: List[str] = <factory>, domain_contexts: Set[str] = <factory>, natural_language_summary: Optional[str] = None, style_name: str = 'dau-compliant@1.0') -> None`
  Initialize self.  See help(type(self)) for accurate signature.
- `__repr__(self)`
  Return repr(self).
- `from_dict(data: dict) -> 'UoDMetadata'`
  Deserialize from dictionary.
- `to_dict(self) -> dict`
  Serialize to dictionary.

#### `UoDType`

Type of Universe of Discourse.

Distinguishes between static (single state) and dynamic (full history) UoDs.

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
The EGI model is immutable. Use `.with_*()` methods:

```python
# Correct
new_egi = egi.with_vertex(vertex)

# Incorrect
egi.add_vertex(vertex)  # No such method
```

### Error Handling
Check return values and handle ``None`` cases:

```python
result = transform_egi(egi, rule)
if result is None:
    # Handle transformation failure
    pass
```

---

*For usage examples, see [CORE_API_USAGE_GUIDE.md](CORE_API_USAGE_GUIDE.md).*
