# EGI-Diagram Correspondence Specification

## Overview

This document specifies how diagrammatic manipulations in Existential Graphs correspond to atomic operations on the underlying EGI (Existential Graph Instance) data structure, following Dau's formalism.

## Core Principles

### 1. Edge as Generic Connection
- **Edge** (`E`): Abstract data structure representing connections
- **κ Labeling Function**: Determines edge meaning
  - Predicates: κ(e) = relation name (e.g., "Human", "Loves")
  - Identity Edges: κ(e) = "="
  - Medads: κ(e) = atomic proposition, arity = 0

### 2. Diagram-EGI Correspondence
Every visual manipulation maps to atomic EGI operations:
- **Drawing**: Creates new edges/vertices
- **Attaching**: Updates ν mapping
- **Merging**: Combines ligatures
- **Branching**: Extends existing ligatures

## Specific Mappings

### 1. Drawing Initial Structure (Double Cut)
**Diagrammatic Action**: Draw double negative (nested cuts)
**EGI Operation**: 
```python
# Create two Cut objects with proper nesting
cut_outer = Cut(id="cut_1")
cut_inner = Cut(id="cut_2")

# Update area mapping to reflect nesting
area_mapping = frozendict({
    "sheet": frozenset({"cut_1"}),
    "cut_1": frozenset({"cut_2"}),
    "cut_2": frozenset()
})
```
**Logical State**: EGI with nested cuts representing double negation

### 2. Inserting Predicates
**Diagrammatic Action**: Insert predicate text in specific area
**EGI Operation**:
```python
# Create edge with predicate label
edge_human = Edge(id="e_human")
rel_mapping["e_human"] = "Human"

# Place in appropriate area
area_mapping["cut_1"] = area_mapping["cut_1"] | {"e_human"}

# Initially arity 0 (medad) - no ν mapping yet
```
**Logical State**: Atomic proposition in specified context

### 3. Asserting Entity (Vertex)
**Diagrammatic Action**: Draw line of identity (LoI) in area
**EGI Operation**:
```python
# Create vertex
vertex_1 = Vertex(id="v_1", label=None, is_generic=True)

# Create identity edge for the LoI
identity_edge = Edge(id="loi_1")
rel_mapping["loi_1"] = "="

# Place vertex in area
area_mapping["cut_1"] = area_mapping["cut_1"] | {"v_1"}
```
**Logical State**: Assertion of existence in context

### 4. Attaching LoI to Predicate
**Diagrammatic Action**: Connect end of LoI to predicate hook
**EGI Operation**:
```python
# Update predicate's ν mapping to include vertex
nu_mapping["e_human"] = ("v_1",)

# The visual connection is now represented in the ν mapping
# The identity edge connects the vertex to the predicate
```
**Logical State**: Predicated assertion (e.g., "something is Human")

### 5. Extending LoI Across Cuts (Iteration)
**Diagrammatic Action**: Draw LoI from vertex across cut boundary to another predicate
**EGI Operation**:
```python
# This is Dau's Iteration rule
# Update second predicate's ν mapping
nu_mapping["e_mortal"] = ("v_1",)

# The same vertex is now connected to both predicates
# This creates a ligature: Human(x) → Mortal(x)
```
**Logical State**: Universal statement via iteration

### 6. Introducing Constant
**Diagrammatic Action**: Draw labeled LoI (e.g., "Socrates")
**EGI Operation**:
```python
# Create constant vertex
vertex_socrates = Vertex(id="v_socrates", label="Socrates", is_generic=False)

# Attach to predicate
nu_mapping["e_human"] = nu_mapping["e_human"] + ("v_socrates",)
```
**Logical State**: Specific assertion (e.g., "Socrates is Human")

## Ligature Operations

### End-to-End Connection
**Diagrammatic Action**: Connect two LoI endpoints
**EGI Operation**:
```python
# Merge two separate ligatures into one
# Update ν mappings to reference the same vertex
# Remove redundant vertices if necessary

# Before: v1 connects to pred1, v2 connects to pred2
# After: v1 connects to both pred1 and pred2, v2 removed
nu_mapping["pred1"] = ("v1",)
nu_mapping["pred2"] = ("v1",)
```
**Logical State**: Single entity with multiple properties

### Branching Point Connection
**Diagrammatic Action**: Attach new LoI to existing junction
**EGI Operation**:
```python
# Add new connection to existing ligature
# Create new vertex for the free end
new_vertex = Vertex(id="v_new")

# Create identity edge connecting to existing junction
identity_edge = Edge(id="loi_branch")
rel_mapping["loi_branch"] = "="
nu_mapping["loi_branch"] = ("v_existing_junction", "v_new")
```
**Logical State**: Extended ligature with new branch

## Implementation Requirements

### 1. DiagramController Operations
All user actions must map to EGI operations:
```python
class DiagramController:
    def attach_loi_to_predicate(self, loi_id: str, predicate_id: str, hook_position: int):
        """Attach LoI endpoint to predicate hook, updating ν mapping"""
        
    def detach_loi_from_predicate(self, loi_id: str, predicate_id: str):
        """Detach LoI from predicate, updating ν mapping"""
        
    def merge_ligatures(self, loi1_id: str, loi2_id: str):
        """Merge two ligatures end-to-end"""
        
    def branch_ligature(self, junction_vertex_id: str, new_loi_id: str):
        """Add new branch to existing ligature"""
```

### 2. Rendering Pipeline
The rendering must reflect current EGI state:
- **Predicates**: Text with hooks at boundary (no inherent lines)
- **LoI**: Heavy line segments based on identity edges
- **Connections**: Visual lines from LoI to predicate hooks based on ν mapping

### 3. Selection Model
- **Predicates**: Selectable as text entities
- **LoI**: Selectable as line segments
- **Hooks**: Selectable as attachment points
- **Ligatures**: Selectable as connected components

## Validation

Every diagram manipulation must:
1. Map to valid EGI transformation
2. Preserve EGI structural integrity
3. Maintain ν mapping consistency
4. Respect area containment rules
5. Follow Dau's transformation rules

This ensures mathematical rigor while supporting intuitive diagrammatic manipulation.
