# Analysis of Dau's Subgraph Definition 12.10

## Definition 12.10 Summary

Dau defines a **subgraph** of a relational graph with cuts G := (V,E,ν,>,Cut,area) as:

G' := (V',E',ν',>',Cut',area') is a subgraph of G in context >' iff:

### **Core Constraints**

1. **Subset Relations**: V' ⊆ V, E' ⊆ E, Cut' ⊆ Cut, >' ∈ Cut ∪ {>}

2. **Vertex Mapping Preservation**: ν' = ν|E' (restriction of ν to E')

3. **Area Mapping**: 
   - area'(>') = area(>') ∩ (V' ∪ E' ∪ Cut')
   - area'(c') = area(c') for each c' ∈ Cut'

4. **Context Consistency**: ctx(x) ∈ Cut' ∪ {>'} for each x ∈ V' ∪ E' ∪ Cut'

5. **Edge Completeness**: Ve' ⊆ V' for each edge e' ∈ E' (if edge included, all incident vertices must be included)

### **Closed Subgraphs**

A subgraph is **closed** if additionally:
- **Vertex Completeness**: Ev' ⊆ E' for each vertex v' ∈ V' (if vertex included, all incident edges must be included)

### **For EGIs**

For EGIs G := (V,E,ν,>,Cut,area,κ), a subgraph additionally requires:
- **Relation Labeling**: κ' = κ|E' (restriction of κ to E')

## Key Mathematical Properties

### **Context Placement**
- Every subgraph is placed in a specific context >'
- Subgraph is "directly enclosed" by >'
- Subgraph is "enclosed" by context c iff >' ≤ c

### **Structural Integrity**
- **Edge Completeness**: Cannot have "dangling edges" - if an edge is in the subgraph, all its incident vertices must be included
- **Context Consistency**: All elements in the subgraph must have their contexts either in the subgraph's cut set or be the subgraph's root context

### **Area Mapping Preservation**
- The area mapping of the original graph is preserved for cuts within the subgraph
- The root context's area is intersected with the subgraph's elements

## Implications for Our Implementation

### **Current Problem**
We've been using informal EGIF "probes" like `(P *x)` or `[*y]` as if they were subgraphs, but they lack:

1. **Formal context specification** - Where is the subgraph placed?
2. **Complete structural definition** - What vertices, edges, cuts are included?
3. **Area mapping consistency** - How do areas map in the subgraph?
4. **Context hierarchy preservation** - How does the subgraph fit in the context tree?

### **Required Implementation**

#### **1. Formal Subgraph Class**
```python
class DAUSubgraph:
    def __init__(self, V_prime, E_prime, Cut_prime, root_context, parent_graph):
        # Validate Definition 12.10 constraints
        # Build proper area mapping
        # Ensure context consistency
```

#### **2. Subgraph Identification from EGIF**
Instead of informal probe matching, we need:
- Parse EGIF probe into formal subgraph structure
- Identify root context >' where subgraph should be placed
- Build complete V', E', Cut' sets with proper constraints
- Validate all Definition 12.10 requirements

#### **3. Transformation Operations on Subgraphs**
- **Erasure**: Remove subgraph G' from parent graph G
- **Insertion**: Add subgraph G' to parent graph G in context >'
- **Iteration**: Copy subgraph G' to same or deeper context
- **De-iteration**: Remove subgraph copy that could have been created by iteration

#### **4. Subgraph Matching**
- Find all subgraphs in G that are isomorphic to a given pattern
- Respect context placement and structural constraints
- Handle closed vs. non-closed subgraph matching

## Critical Insight

**The current "probe" system is mathematically incomplete.** We need to replace it with Dau's formal subgraph model to achieve:

1. **Mathematical Rigor**: Proper Definition 12.10 compliance
2. **Structural Integrity**: No dangling edges or inconsistent contexts  
3. **Transformation Correctness**: Operations on well-defined mathematical objects
4. **Context Awareness**: Proper handling of positive/negative context rules

This is not just a refinement - it's a fundamental architectural requirement for mathematical correctness according to Dau's formalism.

