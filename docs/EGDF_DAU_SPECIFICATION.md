# EGDF Dau-Compliant Specification

## Overview

This document defines the formal mapping from Graphviz xdot output to Dau-compliant EGDF (Existential Graph Diagram Format), ensuring precise correspondence between visual elements and EGI logical structure for both Warmup and Practice interaction modes.

## Core Principle

**Every visual element must have unambiguous semantic meaning and bidirectional correspondence with the EGI model.**

## 1. Dau-Compliant Visual Elements

### 1.1 Cuts (Negation Boundaries)
- **Visual**: Rounded rectangles (NOT ovals or circles)
- **xdot Source**: Graphviz cluster bounding boxes (`bb` attribute)
- **EGDF Mapping**: `CutPrimitive` with `shape="rounded_rectangle"`
- **EGI Correspondence**: Each cut maps to exactly one `Cut` object in EGI
- **Interactive Constraints**:
  - Cuts must contain all their logical children
  - Cuts cannot overlap with sibling cuts
  - Cut boundaries define containment for user interactions

### 1.2 Ligatures (Lines of Identity) - Dau Chapter 16 Specification

**Core Principle**: Ligatures are heavy, continuous lines that represent the identity of individuals across logical contexts.

#### 1.2.1 Visual Properties
- **Line Weight**: 8pt width (heavy lines per Dau convention)
- **Color**: Solid black (#000000)
- **Style**: Continuous, no breaks or gaps
- **Routing**: Prefer straight lines; use minimal curves only when necessary

#### 1.2.2 Geometric Specification
- **Junction Points**: When ≥3 ligature segments meet, use a single junction point
- **Branching**: T-junctions and Y-junctions for shared vertices
- **Attachment**: Lines terminate at predicate periphery (invisible hook)
- **Cut Crossing**: Ligatures may cross cut boundaries (identity transcends context)

#### 1.2.3 Routing Algorithm (Dau-Compliant)
1. **Primary Route**: Direct straight line from vertex to predicate periphery
2. **Obstacle Avoidance**: Minimal deviation to avoid predicate text intersection
3. **Cut Respect**: Maintain logical area assignment while allowing boundary crossing
4. **Junction Optimization**: Minimize total ligature length for shared vertices

#### 1.2.4 EGDF Mapping
- **xdot Source**: Graphviz edge spline paths + EGI ν mapping
- **Primitive Type**: `IdentityLinePrimitive`
- **Coordinates**: Continuous path as `List[Coordinate]`
- **Metadata**: Junction points, attachment points, routing constraints

#### 1.2.5 Interactive Constraints
- **Continuity**: Ligatures remain geometrically continuous during manipulation
- **Identity Preservation**: Vertex movement updates ligature geometry automatically
- **Attachment Integrity**: Predicate attachment points update with predicate movement
- **Cut Crossing**: Ligature-cut intersections update with cut resizing

### 1.3 Vertices (Identity Spots)
- **Visual**: Small filled circles (6pt radius) with optional constant names
- **xdot Source**: Computed from ligature intersections and EGI ν mapping
- **EGDF Mapping**: `VertexPrimitive` at precise ligature positions
- **EGI Correspondence**: Each vertex represents one individual in the EGI
- **Interactive Constraints**:
  - Vertices must lie exactly on their ligature
  - Vertex position determines logical area (cut containment)
  - Constant names appear adjacent to vertex spots

### 1.4 Predicates (Relations)
- **Visual**: Text labels with clear periphery boundaries
- **xdot Source**: Graphviz node positions and dimensions
- **EGDF Mapping**: `PredicatePrimitive` with precise text bounds
- **EGI Correspondence**: Each predicate maps to one `Edge` object in EGI
- **Interactive Constraints**:
  - Predicate boundaries define hook attachment points
  - Text must not be intersected by ligatures
  - Argument order preserved via ν mapping

## 2. Interactive Mapping Specification

### 2.1 User Actions → EGI Operations

| User Action | Visual Target | EGI Operation | Warmup Mode | Practice Mode |
|-------------|---------------|---------------|-------------|---------------|
| Move vertex | Vertex spot | Update vertex area | Allowed | Semantic check |
| Resize cut | Cut boundary | Update cut containment | Allowed | Meaning-preserving |
| Connect ligature | Vertex + Predicate | Update ν mapping | Allowed | Rule-based only |
| Add predicate | Empty area | Create new Edge | Allowed | Context-dependent |
| Delete element | Any element | Remove from EGI | Allowed | Transformation rule |

### 2.2 Constraint Enforcement

**Warmup Mode (Compositional)**:
- Syntactic constraints only
- Structural validity maintained
- Flexible composition allowed

**Practice Mode (Rule-Based)**:
- Semantic constraints enforced
- Only meaning-preserving transformations
- Formal calculus rules applied

## 3. Implementation Requirements

### 3.1 Formal Mapping Class
```python
class DauCompliantEGDFMapper:
    def xdot_to_egdf(self, xdot_data, egi_model) -> List[SpatialPrimitive]
    def egdf_to_egi_action(self, user_action, visual_target) -> EGIOperation
    def validate_correspondence(self, egdf_primitives, egi_model) -> bool
```

### 3.2 Constraint System
```python
class InteractionConstraints:
    def validate_warmup_action(self, action, selection) -> bool
    def validate_practice_action(self, action, selection) -> bool
    def enforce_dau_conventions(self, primitives) -> List[SpatialPrimitive]
```

This specification ensures that every user interaction maps precisely to EGI operations, enabling both compositional creativity (Warmup) and formal rigor (Practice) while maintaining Dau-compliant visual representation.
