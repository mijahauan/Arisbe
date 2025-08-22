# Dau Style Consolidation - Deprecation Recommendations

## Summary
The canonical `DauStyle` class in `src/rendering_styles.py` consolidates all scattered Dau style fragments. The following code can now be deprecated or removed.

## Files for Deprecation/Removal

### 1. `src/egdf_canvas_renderer.py` - DauVisualStyle class
**Lines 22-46**: `class DauVisualStyle`
```python
class DauVisualStyle:
    """Dau-compliant visual styling for Existential Graphs."""
    # ... implementation
```
**Status**: DEPRECATED - Replace with `DauStyle` from `rendering_styles.py`
**Action**: Remove class, update imports in dependent code

### 2. `src/egdf_parser.py` - StyleTheme class  
**Lines 172-181**: `class StyleTheme`
```python
@dataclass
class StyleTheme:
    """Visual style theme for Dau conventions."""
    # ... implementation
```
**Status**: DEPRECATED - Values consolidated into `DauStyle`
**Action**: Remove class, update any references

### 3. `src/pyside6_rendering_contracts.py` - PySide6RenderingStyle class
**Lines 19-44**: `class PySide6RenderingStyle`
```python
@dataclass
class PySide6RenderingStyle:
    """Standardized rendering style for PySide6 canvas operations."""
    # ... implementation
```
**Status**: PARTIALLY DEPRECATED - Generic structure useful, but Dau-specific values moved
**Action**: Keep class for non-Dau styles, remove Dau-specific defaults

### 4. `src/canonical_qt_renderer.py` - Constructor parameters
**Lines 162-172**: Default style parameters in `__init__()`
```python
def __init__(self,
             stroke_width: float = 1.0,
             cut_color: Tuple[int, int, int] = (51, 51, 51),
             # ... other style parameters
```
**Status**: DEPRECATED - Style should come from `DauStyle` instance
**Action**: Refactor to accept `RenderingStyle` parameter instead of individual style values

## Migration Strategy

### Phase 1: Update Imports
Replace all imports of deprecated style classes:
```python
# OLD
from egdf_canvas_renderer import DauVisualStyle
from egdf_parser import StyleTheme

# NEW  
from rendering_styles import DauStyle
```

### Phase 2: Update Usage
Replace instantiation and usage:
```python
# OLD
style = DauVisualStyle()
line_width = style.identity_line_width

# NEW
style = DauStyle()
line_width = style.identity_line_width
```

### Phase 3: Remove Deprecated Code
After confirming no references remain:
1. Delete `DauVisualStyle` class from `egdf_canvas_renderer.py`
2. Delete `StyleTheme` class from `egdf_parser.py`  
3. Refactor `CanonicalQtRenderer` to use `RenderingStyle` parameter
4. Update `PySide6RenderingStyle` to be style-agnostic

## Benefits of Consolidation

1. **Single Source of Truth**: All Dau style values in one canonical location
2. **Consistency**: No more conflicting values across files (8.0 vs 6.0 vs 4.0 line widths)
3. **Extensibility**: Easy to add Peircean, Modern, and custom styles
4. **Maintainability**: Style changes only need to be made in one place
5. **Architecture Clarity**: Clean EGDF → Style → Output pipeline

## Testing Required

Before removing deprecated code:
1. Verify `DauStyle` works in Ergasterion rendering
2. Check all imports and references are updated
3. Confirm visual output matches expected Dau conventions
4. Test style switching between Dau/Peircean/Modern styles
