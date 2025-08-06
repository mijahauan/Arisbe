# Selectable Elements Specification

**Version:** 1.0  
**Date:** 2025-08-06  
**Purpose:** Define precisely what elements are selectable on the EG canvas and what actions can be taken on them.

## Core Principle

Selectable elements are the **visual counterparts to EGI components** on which legitimate actions can be taken according to Dau's transformation rules and EG formalism.

## Selectable Element Types

### 1. **Individual Vertices** (Lines of Identity/Heavy Dots)
**EGI Component:** `Vertex` objects in `graph.V`  
**Visual Representation:** Heavy line segments or isolated dots  
**Selection Target:** Individual vertex by ID

**Legitimate Actions:**
- **Erasure** (Rule 1): Remove from positive contexts only
- **Insertion** (Rule 2): Add to negative contexts only  
- **Iteration** (Rule 3): Copy to deeper/equal contexts
- **De-iteration** (Rule 4): Remove iterated copies
- **Isolated Vertex Addition** (Rule 7): Add isolated vertex to any context
- **Isolated Vertex Removal** (Rule 8): Remove isolated vertex from any context
- **Edit Properties**: Change vertex label (constant ↔ generic)
- **Move** (Layout only): Reposition within same logical area

### 2. **Individual Predicates** (Relations/Edges)
**EGI Component:** `Edge` objects in `graph.E`  
**Visual Representation:** Predicate text with hooks to vertices  
**Selection Target:** Individual edge by ID

**Legitimate Actions:**
- **Erasure** (Rule 1): Remove from positive contexts only
- **Insertion** (Rule 2): Add to negative contexts only
- **Iteration** (Rule 3): Copy to deeper/equal contexts  
- **De-iteration** (Rule 4): Remove iterated copies
- **Edit Properties**: Change relation name, arity, argument order
- **Connect/Disconnect**: Modify ν mapping (vertex connections)
- **Move** (Layout only): Reposition within same logical area

### 3. **Individual Cuts** (Negation Boundaries)
**EGI Component:** `Cut` objects in `graph.Cut`  
**Visual Representation:** Fine-drawn closed curves  
**Selection Target:** Individual cut by ID

**Legitimate Actions:**
- **Erasure** (Rule 1): Remove from positive contexts only
- **Insertion** (Rule 2): Add to negative contexts only
- **Double Cut Addition** (Rule 5): Add double cut around elements
- **Double Cut Removal** (Rule 6): Remove double cuts
- **Resize** (Layout only): Adjust cut boundary to fit contents
- **Move** (Layout only): Reposition cut and all contents together

### 4. **Subgraphs** (Logical Collections)
**EGI Component:** Sets of related elements `{vertices, edges, cuts}`  
**Visual Representation:** Multiple selected elements with shared context  
**Selection Target:** Set of element IDs forming logical unit

**Legitimate Actions:**
- **Erasure** (Rule 1): Remove entire subgraph from positive contexts
- **Insertion** (Rule 2): Add subgraph to negative contexts
- **Iteration** (Rule 3): Copy subgraph to deeper/equal contexts
- **De-iteration** (Rule 4): Remove iterated subgraph
- **Double Cut Addition** (Rule 5): Enclose subgraph in double cut
- **Move** (Layout only): Reposition subgraph within same logical area
- **Copy**: Create subgraph for insertion elsewhere

### 5. **Empty Areas** (Contexts for Insertion)
**EGI Component:** Context IDs (sheet, cut interiors)  
**Visual Representation:** Empty space within cuts or on sheet  
**Selection Target:** Context/area ID

**Legitimate Actions:**
- **Insertion** (Rule 2): Add elements to negative contexts only
- **Isolated Vertex Addition** (Rule 7): Add isolated vertex to any context
- **Double Cut Addition** (Rule 5): Add double cut in context
- **Paste Subgraph**: Insert copied subgraph into context

## Selection Validation Rules

### Context Polarity Constraints
- **Positive Contexts** (sheet, oddly-enclosed cuts): Allow erasure, prohibit insertion
- **Negative Contexts** (evenly-enclosed cuts): Allow insertion, prohibit erasure

### Logical Completeness
- **Subgraph selections** must include all logically connected elements
- **Vertex selections** must include all incident edges if moving across contexts
- **Edge selections** must include all incident vertices if moving across contexts

### Transformation Constraints
- **Iteration**: Target context must dominate or equal source context
- **Double Cut**: Elements must be in same context to be enclosed together
- **Isolated Vertex**: Must have no incident edges for Rules 7/8

## Selection Interaction Patterns

### Single Element Selection
- **Left Click**: Select individual vertex, predicate, or cut
- **Visual Feedback**: Highlight element with selection overlay
- **Context Menu**: Show valid actions based on element type and context polarity

### Multi-Element Selection  
- **Ctrl/Cmd + Click**: Add/remove elements from selection
- **Click + Drag**: Area selection for multiple elements
- **Visual Feedback**: Highlight all selected elements
- **Validation**: Check logical completeness for subgraph operations

### Area Selection
- **Click on Empty Space**: Select context/area for insertion
- **Visual Feedback**: Dotted outline showing selectable area
- **Context Menu**: Show insertion actions valid for context polarity

## Implementation Notes

### Selection State Management
```python
@dataclass
class SelectionState:
    selected_elements: Set[ElementID]
    selected_context: Optional[ElementID]  # For area selections
    selection_type: SelectionType  # SINGLE, MULTI, SUBGRAPH, AREA
    is_logically_complete: bool
    valid_actions: Set[ActionType]
```

### Action Validation
- All actions must validate against EGI constraints before execution
- Context polarity must be checked for erasure/insertion rules
- Logical completeness must be verified for subgraph operations
- Transformation constraints must be enforced (dominance, isolation, etc.)

### Visual Feedback Requirements
- **Selection Overlays**: Clear visual indication of selected elements
- **Context Highlighting**: Show positive/negative context polarity
- **Action Affordances**: Visual cues for valid actions (resize handles, connection points)
- **Validation Feedback**: Clear indication when selections are invalid

This specification ensures that all selectable elements correspond to legitimate EGI operations and maintain mathematical rigor throughout the interaction process.
