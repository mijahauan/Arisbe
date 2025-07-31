# Immutable EGI Architecture Design

## Core Design Principles

1. **Pure Immutability**: All data structures are immutable after creation
2. **Functional Transformations**: All operations return new instances
3. **Structural Sharing**: Minimize copying through shared immutable structures
4. **Mathematical Soundness**: Clear separation between original and transformed graphs
5. **Type Safety**: Comprehensive type hints throughout

## Core Data Structures

### 1. Immutable Base Types

```python
from dataclasses import dataclass, field
from typing import FrozenSet, Tuple, Optional, Dict, Any
from frozendict import frozendict  # External dependency for immutable dicts

ElementID = str  # Unique identifier for elements

@dataclass(frozen=True)
class Alphabet:
    """Immutable alphabet defining available relations, constants, and variables."""
    relations: FrozenSet[str]
    constants: FrozenSet[str] 
    variables: FrozenSet[str]
    
    def with_relation(self, relation: str) -> 'Alphabet':
        return Alphabet(
            relations=self.relations | {relation},
            constants=self.constants,
            variables=self.variables
        )
```

### 2. Immutable Context

```python
@dataclass(frozen=True)
class Context:
    """Immutable context representing a cut or the sheet of assertion."""
    id: ElementID
    parent_id: Optional[ElementID]
    depth: int
    enclosed_elements: FrozenSet[ElementID]
    children: FrozenSet[ElementID]
    
    def is_positive(self) -> bool:
        """Returns True if context has even depth (positive)."""
        return self.depth % 2 == 0
    
    def is_negative(self) -> bool:
        """Returns True if context has odd depth (negative)."""
        return self.depth % 2 == 1
    
    def with_element(self, element_id: ElementID) -> 'Context':
        """Returns new context with additional enclosed element."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements | {element_id},
            children=self.children
        )
    
    def without_element(self, element_id: ElementID) -> 'Context':
        """Returns new context without specified element."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements - {element_id},
            children=self.children
        )
    
    def with_child(self, child_id: ElementID) -> 'Context':
        """Returns new context with additional child."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements,
            children=self.children | {child_id}
        )
```

### 3. Immutable Vertex

```python
@dataclass(frozen=True)
class Vertex:
    """Immutable vertex representing an individual (variable or constant)."""
    id: ElementID
    context_id: ElementID
    is_constant: bool
    constant_name: Optional[str] = None
    properties: frozendict = field(default_factory=frozendict)
    
    def __post_init__(self):
        """Validate vertex constraints."""
        if self.is_constant and not self.constant_name:
            raise ValueError("Constant vertex must have constant_name")
        if not self.is_constant and self.constant_name:
            raise ValueError("Variable vertex cannot have constant_name")
    
    def with_property(self, key: str, value: Any) -> 'Vertex':
        """Returns new vertex with additional property."""
        new_properties = dict(self.properties)
        new_properties[key] = value
        return Vertex(
            id=self.id,
            context_id=self.context_id,
            is_constant=self.is_constant,
            constant_name=self.constant_name,
            properties=frozendict(new_properties)
        )
    
    def in_context(self, context_id: ElementID) -> 'Vertex':
        """Returns new vertex in different context (for iteration)."""
        return Vertex(
            id=self.id,
            context_id=context_id,
            is_constant=self.is_constant,
            constant_name=self.constant_name,
            properties=self.properties
        )
```

### 4. Immutable Edge

```python
@dataclass(frozen=True)
class Edge:
    """Immutable edge representing a relation or identity."""
    id: ElementID
    context_id: ElementID
    relation_name: str
    incident_vertices: Tuple[ElementID, ...]
    is_identity: bool = False
    properties: frozendict = field(default_factory=frozendict)
    
    def __post_init__(self):
        """Validate edge constraints."""
        if self.is_identity and self.relation_name != "=":
            raise ValueError("Identity edge must have relation_name '='")
        if self.is_identity and len(self.incident_vertices) < 2:
            raise ValueError("Identity edge must have at least 2 vertices")
    
    def with_property(self, key: str, value: Any) -> 'Edge':
        """Returns new edge with additional property."""
        new_properties = dict(self.properties)
        new_properties[key] = value
        return Edge(
            id=self.id,
            context_id=self.context_id,
            relation_name=self.relation_name,
            incident_vertices=self.incident_vertices,
            is_identity=self.is_identity,
            properties=frozendict(new_properties)
        )
    
    def in_context(self, context_id: ElementID) -> 'Edge':
        """Returns new edge in different context."""
        return Edge(
            id=self.id,
            context_id=context_id,
            relation_name=self.relation_name,
            incident_vertices=self.incident_vertices,
            is_identity=self.is_identity,
            properties=self.properties
        )
```

### 5. Immutable EGI

```python
@dataclass(frozen=True)
class EGI:
    """Immutable Existential Graph Instance."""
    vertices: FrozenSet[Vertex]
    edges: FrozenSet[Edge]
    contexts: FrozenSet[Context]
    sheet_id: ElementID
    alphabet: Alphabet
    
    # Computed properties for efficient lookup
    _vertex_map: frozendict = field(init=False)
    _edge_map: frozendict = field(init=False)
    _context_map: frozendict = field(init=False)
    
    def __post_init__(self):
        """Build lookup maps for efficient access."""
        object.__setattr__(self, '_vertex_map', 
                          frozendict({v.id: v for v in self.vertices}))
        object.__setattr__(self, '_edge_map', 
                          frozendict({e.id: e for e in self.edges}))
        object.__setattr__(self, '_context_map', 
                          frozendict({c.id: c for c in self.contexts}))
        
        # Validate sheet exists
        if self.sheet_id not in self._context_map:
            raise ValueError(f"Sheet context {self.sheet_id} not found")
    
    @property
    def sheet(self) -> Context:
        """Returns the sheet of assertion."""
        return self._context_map[self.sheet_id]
    
    def get_vertex(self, vertex_id: ElementID) -> Vertex:
        """Get vertex by ID."""
        if vertex_id not in self._vertex_map:
            raise ValueError(f"Vertex {vertex_id} not found")
        return self._vertex_map[vertex_id]
    
    def get_edge(self, edge_id: ElementID) -> Edge:
        """Get edge by ID."""
        if edge_id not in self._edge_map:
            raise ValueError(f"Edge {edge_id} not found")
        return self._edge_map[edge_id]
    
    def get_context(self, context_id: ElementID) -> Context:
        """Get context by ID."""
        if context_id not in self._context_map:
            raise ValueError(f"Context {context_id} not found")
        return self._context_map[context_id]
    
    def with_vertex(self, vertex: Vertex) -> 'EGI':
        """Returns new EGI with additional vertex."""
        # Update context to include vertex
        context = self.get_context(vertex.context_id)
        updated_context = context.with_element(vertex.id)
        
        return EGI(
            vertices=self.vertices | {vertex},
            edges=self.edges,
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def without_vertex(self, vertex_id: ElementID) -> 'EGI':
        """Returns new EGI without specified vertex."""
        vertex = self.get_vertex(vertex_id)
        context = self.get_context(vertex.context_id)
        updated_context = context.without_element(vertex_id)
        
        return EGI(
            vertices=self.vertices - {vertex},
            edges=self.edges,
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def with_edge(self, edge: Edge) -> 'EGI':
        """Returns new EGI with additional edge."""
        context = self.get_context(edge.context_id)
        updated_context = context.with_element(edge.id)
        
        return EGI(
            vertices=self.vertices,
            edges=self.edges | {edge},
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def without_edge(self, edge_id: ElementID) -> 'EGI':
        """Returns new EGI without specified edge."""
        edge = self.get_edge(edge_id)
        context = self.get_context(edge.context_id)
        updated_context = context.without_element(edge_id)
        
        return EGI(
            vertices=self.vertices,
            edges=self.edges - {edge},
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def with_context(self, context: Context) -> 'EGI':
        """Returns new EGI with additional context."""
        # Update parent context if exists
        updated_contexts = self.contexts | {context}
        
        if context.parent_id:
            parent = self.get_context(context.parent_id)
            updated_parent = parent.with_child(context.id)
            updated_contexts = (updated_contexts - {parent}) | {updated_parent}
        
        return EGI(
            vertices=self.vertices,
            edges=self.edges,
            contexts=updated_contexts,
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
```

## Builder Pattern for Construction

```python
class EGIBuilder:
    """Builder for constructing EGI instances incrementally."""
    
    def __init__(self, alphabet: Alphabet, sheet_id: Optional[ElementID] = None):
        self._alphabet = alphabet
        self._sheet_id = sheet_id or self._generate_id()
        self._vertices: Dict[ElementID, Vertex] = {}
        self._edges: Dict[ElementID, Edge] = {}
        self._contexts: Dict[ElementID, Context] = {}
        
        # Create sheet context
        self._contexts[self._sheet_id] = Context(
            id=self._sheet_id,
            parent_id=None,
            depth=0,
            enclosed_elements=frozenset(),
            children=frozenset()
        )
    
    def add_vertex(self, context_id: ElementID, is_constant: bool = False, 
                   constant_name: Optional[str] = None, **properties) -> ElementID:
        """Add vertex and return its ID."""
        vertex_id = self._generate_id()
        vertex = Vertex(
            id=vertex_id,
            context_id=context_id,
            is_constant=is_constant,
            constant_name=constant_name,
            properties=frozendict(properties)
        )
        self._vertices[vertex_id] = vertex
        
        # Update context
        context = self._contexts[context_id]
        self._contexts[context_id] = context.with_element(vertex_id)
        
        return vertex_id
    
    def add_edge(self, context_id: ElementID, relation_name: str, 
                 incident_vertices: Tuple[ElementID, ...], 
                 is_identity: bool = False, **properties) -> ElementID:
        """Add edge and return its ID."""
        edge_id = self._generate_id()
        edge = Edge(
            id=edge_id,
            context_id=context_id,
            relation_name=relation_name,
            incident_vertices=incident_vertices,
            is_identity=is_identity,
            properties=frozendict(properties)
        )
        self._edges[edge_id] = edge
        
        # Update context
        context = self._contexts[context_id]
        self._contexts[context_id] = context.with_element(edge_id)
        
        return edge_id
    
    def add_context(self, parent_id: Optional[ElementID] = None) -> ElementID:
        """Add context and return its ID."""
        context_id = self._generate_id()
        parent_depth = 0 if parent_id is None else self._contexts[parent_id].depth
        
        context = Context(
            id=context_id,
            parent_id=parent_id,
            depth=parent_depth + 1,
            enclosed_elements=frozenset(),
            children=frozenset()
        )
        self._contexts[context_id] = context
        
        # Update parent
        if parent_id:
            parent = self._contexts[parent_id]
            self._contexts[parent_id] = parent.with_child(context_id)
        
        return context_id
    
    def build(self) -> EGI:
        """Build immutable EGI instance."""
        return EGI(
            vertices=frozenset(self._vertices.values()),
            edges=frozenset(self._edges.values()),
            contexts=frozenset(self._contexts.values()),
            sheet_id=self._sheet_id,
            alphabet=self._alphabet
        )
    
    def _generate_id(self) -> ElementID:
        """Generate unique element ID."""
        import uuid
        return f"elem_{uuid.uuid4().hex[:8]}"
```

## Functional Transformation Architecture

```python
# Pure functions for transformations
def apply_erasure(egi: EGI, element_id: ElementID) -> EGI:
    """Apply erasure transformation, returning new EGI."""
    
def apply_insertion(egi: EGI, element: Union[Vertex, Edge], context_id: ElementID) -> EGI:
    """Apply insertion transformation, returning new EGI."""
    
def apply_iteration(egi: EGI, vertex_id: ElementID, target_context_id: ElementID) -> EGI:
    """Apply iteration transformation, returning new EGI."""

def apply_double_cut_addition(egi: EGI, context_id: ElementID) -> EGI:
    """Apply double cut addition, returning new EGI."""

# Validation functions
def can_erase(egi: EGI, element_id: ElementID) -> bool:
    """Check if element can be erased (positive context)."""
    
def can_insert(egi: EGI, context_id: ElementID) -> bool:
    """Check if element can be inserted (negative context)."""
```

This architecture provides:
- **Complete Immutability**: All structures are immutable after creation
- **Efficient Operations**: Structural sharing minimizes copying
- **Type Safety**: Comprehensive type hints
- **Mathematical Soundness**: Clear functional transformations
- **Performance**: Optimized lookup maps and minimal copying
- **Extensibility**: Easy to add new transformation rules

