# Arisbe Pipeline API Contracts

This document defines the exact interfaces and data contracts between all pipeline components to prevent integration confusion.

## Core Data Types

### RelationalGraphWithCuts (EGI Core)
**Source**: `egi_core_dau.py`
**Purpose**: Immutable mathematical representation of Existential Graphs

```python
class RelationalGraphWithCuts:
    V: frozenset[ElementID]           # Vertices
    E: frozenset[ElementID]           # Edges (relations)
    Cut: frozenset[ElementID]         # Cuts
    sheet: ElementID                  # Sheet area ID
    # ... other fields
```

### LayoutResult (Layout Engine Output)
**Source**: `layout_engine_clean.py`
**Purpose**: Spatial positioning data for rendering

```python
@dataclass
class LayoutResult:
    primitives: Dict[str, SpatialPrimitive]  # Element ID → spatial data
    canvas_bounds: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    containment_hierarchy: Dict[str, Set[str]]  # Area → contained elements
```

### SpatialPrimitive (Layout Element)
**Source**: `layout_engine_clean.py`
**Purpose**: Individual element positioning and bounds

```python
@dataclass
class SpatialPrimitive:
    element_id: str
    element_type: str  # 'vertex', 'predicate', 'cut', 'identity_line'
    position: Tuple[float, float]  # (x, y) center
    bounds: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    # ... type-specific fields
```

## Pipeline Contracts

### 1. EGIF Parser → EGI Core
**Input**: EGIF string (e.g., `"*x (Human x) ~[ (Mortal x) ]"`)
**Output**: `RelationalGraphWithCuts`
**Contract**: `parse_egif(egif_string: str) -> RelationalGraphWithCuts`

### 2. Layout Engine → Renderer
**Input**: `RelationalGraphWithCuts`
**Output**: `LayoutResult`
**Contract**: `create_layout_from_graph(graph: RelationalGraphWithCuts) -> LayoutResult`

### 3. Renderer → Canvas
**Input**: `LayoutResult`, `RelationalGraphWithCuts`, Canvas
**Output**: Visual rendering on canvas
**Contract**: `render_diagram(canvas: Canvas, layout: LayoutResult, graph: RelationalGraphWithCuts) -> None`

## Specific Module APIs

### GraphvizLayoutEngine
```python
class GraphvizLayoutEngine:
    def create_layout_from_graph(self, graph: RelationalGraphWithCuts) -> LayoutResult:
        """
        GUARANTEED OUTPUT: LayoutResult with:
        - primitives: Dict[str, SpatialPrimitive] (never empty for valid graphs)
        - canvas_bounds: Tuple[float, float, float, float]
        - containment_hierarchy: Dict[str, Set[str]]
        """
```

### DiagramRendererDau
```python
class DiagramRendererDau:
    def render_diagram(self, canvas: Canvas, layout_result: LayoutResult, graph: RelationalGraphWithCuts) -> None:
        """
        REQUIRED INPUTS:
        - canvas: Must implement Canvas interface (draw_line, draw_circle, etc.)
        - layout_result: LayoutResult with populated primitives dict
        - graph: RelationalGraphWithCuts for logical structure reference
        
        GUARANTEED BEHAVIOR:
        - Renders heavy lines of identity per Dau's conventions
        - Draws fine-drawn cuts as closed curves
        - Ensures proper containment visualization
        - Respects nu mapping for argument order
        """
```

## Integration Test Requirements

Every pipeline integration must include:

1. **Type Validation**: Verify exact types at each handoff
2. **Data Completeness**: Ensure all required fields are populated
3. **Contract Compliance**: Test that outputs match documented contracts
4. **Error Handling**: Define behavior for invalid inputs

## Enforcement Mechanisms

### 1. Type Hints and Runtime Validation
All pipeline functions must use strict type hints and runtime type checking:

```python
from typing import TypeGuard

def validate_layout_result(obj: Any) -> TypeGuard[LayoutResult]:
    """Runtime validation of LayoutResult contract."""
    return (
        hasattr(obj, 'primitives') and
        isinstance(obj.primitives, dict) and
        hasattr(obj, 'canvas_bounds') and
        len(obj.canvas_bounds) == 4
    )
```

### 2. Integration Test Suite
Mandatory tests for every pipeline handoff:

```python
def test_egif_to_egi_contract():
    """Test EGIF parser output matches EGI contract."""
    
def test_egi_to_layout_contract():
    """Test layout engine output matches LayoutResult contract."""
    
def test_layout_to_render_contract():
    """Test renderer accepts LayoutResult and produces visual output."""
```

### 3. API Version Management
Each interface should be versioned and backward compatibility maintained:

```python
# In each module
API_VERSION = "1.0.0"
COMPATIBLE_VERSIONS = ["1.0.0"]
```

## Documentation Requirements

1. **Interface Documentation**: Every public method must document exact input/output types
2. **Contract Examples**: Working examples of each pipeline handoff
3. **Error Scenarios**: Documented behavior for edge cases and failures
4. **Version History**: Track API changes and compatibility

This eliminates the "what object am I receiving?" confusion by making every handoff explicit and verifiable.
