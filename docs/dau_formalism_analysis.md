# Analysis of Dau's Formalism and EGIF

## Key Findings from Dau's "Mathematical Logic with Diagrams"

### 1. Existential Graph Instance (EGI) Definition

From Definition 12.7, an EGI is a structure:
```
G := (V, E, ν, >, Cut, area, κ)
```

Where:
- **V**: Set of vertices (finite)
- **E**: Set of edges (finite) 
- **ν**: Mapping from edges to sequences of vertices (E → ⋃ₖ∈ℕ₀ Vᵏ)
- **>**: Sheet of assertion (single element, not in V ∪ E ∪ Cut)
- **Cut**: Set of cuts (finite)
- **area**: Mapping from contexts to power set of elements (Cut ∪ {>} → P(V ∪ E ∪ Cut))
- **κ**: Mapping from edges to relation names (E → R)

### 2. Key Properties

1. **Dominating Nodes**: For every edge e ∈ E and vertex v ∈ Vₑ, we have ctx(e) ≤ ctx(v)
2. **Identity Edges**: Special edges with κ(e) = "=" and arity 2
3. **Contexts**: Cut ∪ {>} forms a tree structure with > as root
4. **Even/Odd Enclosure**: Determines positive/negative contexts

### 3. Ligatures

From Definition 12.8:
- Ligature-graph: Lig(G) := (V, Eᵢd) where Eᵢd are identity edges
- Ligature: Any connected subgraph of the ligature-graph
- Represents identity connections between vertices

### 4. The 8 Canonical Transformation Rules

From Chapter 15, the formal calculus includes:

1. **Erasure**: Remove edge/subgraph from positive context
2. **Insertion**: Add edge/subgraph to negative context  
3. **Iteration**: Copy subgraph to same or deeper context with ligature connections
4. **De-iteration**: Remove subgraph that could have been inserted by iteration
5. **Double Cut**: Insert/remove double negation (two cuts with nothing between)
6. **Isolated Vertex**: Insert/remove isolated vertex in any context
7. **Constant Vertex Separation**: Split constant vertex into generic vertex + identity link
8. **Constant Vertex Deseparation**: Reverse of separation

### 5. Constants and Functions (Chapter 23)

- Constants are special vertices with object names
- Functions extend the system beyond first-order logic
- Handled through extended labeling functions

## EGIF (Existential Graph Interchange Format) Analysis

### 1. Core Syntax Elements

From Sowa's specification:

- **Defining Labels**: `*x` - represents existential quantification
- **Bound Labels**: `x` - references to defining labels
- **Relations**: `(relation_name arg1 arg2 ...)` 
- **Negations**: `~[ ... ]` - represents cuts/negation
- **Coreference Nodes**: `[x y z]` - represents ligatures/identity
- **Scrolls**: `[If ... [Then ... ] ]` - alternative to double negation

### 2. Key EGIF Grammar Rules

```ebnf
EG = {Node};
Node = Coreference Node | Relation | Function | Negation | Scroll;
Relation = '(', Type Label, {Name}, ')';
Negation = '~', '[', EG, ']';
Coreference Node = '[', Name, {Name}, ']';
Defining Label = '*', identifier;
Bound Label = identifier;
```

### 3. Semantic Mapping

- EGIF defining label `*x` → EGI vertex with existential quantification
- EGIF relation `(P x y)` → EGI edge labeled P connecting vertices for x, y
- EGIF negation `~[...]` → EGI cut containing the subgraph
- EGIF coreference `[x y]` → EGI identity edges connecting vertices

## Implementation Strategy

### 1. Property Hypergraph Model

The EGI will be represented as a property hypergraph where:
- Vertices represent individuals/objects
- Hyperedges represent relations (can connect multiple vertices)
- Properties on edges store relation names and arities
- Cut structure maintains context hierarchy
- Identity edges form ligature subgraphs

### 2. Core Data Structures Needed

1. **Vertex**: ID, context, properties (for constants)
2. **Edge**: ID, relation name, arity, incident vertices, context
3. **Cut**: ID, parent context, enclosed elements
4. **Context**: Reference to cut or sheet of assertion
5. **Ligature**: Connected component of identity edges

### 3. Transformation Rule Implementation

Each rule will be implemented as:
1. Precondition checker (validates rule applicability)
2. Graph transformer (performs the actual transformation)
3. Post-condition validator (ensures result is well-formed EGI)

The markup system using `^` will be parsed to identify:
- Target subgraphs for transformation
- Insertion points for new elements
- Base graphs for de-iteration validation

