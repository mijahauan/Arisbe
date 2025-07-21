# Peirce's Existential Graph Visual Conventions - Research Findings

## Key Visual Conventions Discovered

### 1. **Odd and Even Area Shading**

From John Sowa's tutorial and multiple sources:

> "Any area nested inside an odd number of ovals is shaded, and any area inside an even number of ovals (possibly zero) is unshaded."

**Implementation Rules**:
- **Even areas (0, 2, 4... cuts)**: Unshaded/light background
- **Odd areas (1, 3, 5... cuts)**: Shaded/dark background
- **Sheet of Assertion**: Considered even (level 0) - unshaded
- **First cut**: Odd (level 1) - shaded
- **Cut within cut**: Even (level 2) - unshaded
- **And so on...**

**Logical Significance**:
- **Positive areas** (even levels): Where assertions can be inserted
- **Negative areas** (odd levels): Where denials/negations are expressed

### 2. **Cut Construction Rules**

**From Peirce's original specifications**:
- Cuts are drawn as **ovals, circles, or closed curves**
- **No specific shape requirement** - flexibility in visual representation
- **Nesting determines logical meaning**, not shape

### 3. **Predicate Placement Rules**

**Key Findings**:
- **Predicates must be placed INSIDE their containing context**
- **Predicates cannot cross cut boundaries**
- **Visual positioning affects logical interpretation**

### 4. **Line of Identity (Entity) Conventions**

**From Beta graphs**:
- **Lines of identity** connect predicates that share entities
- **Lines can cross cut boundaries** (unlike predicates)
- **Endpoints determine quantifier scope**

## Visual Requirements for EGRF Implementation

### 1. **Area Shading System**
```
Level 0 (Sheet): Unshaded (white/light)
Level 1 (First cut): Shaded (gray/dark)  
Level 2 (Cut in cut): Unshaded (white/light)
Level 3 (Triple nested): Shaded (gray/dark)
...
```

### 2. **Predicate Visual Specifications**

**From user requirements**:
- **Transparent border around predicate**
- **Predicate hooks on the transparent border**
- **Predicate border remains inside containing area**
- **Predicate placement inside containing cut but outside any inner cuts**

### 3. **Cut Visual Specifications**
- **Closed curves** (ovals, circles, rectangles)
- **Clear boundaries** between areas
- **Proper nesting visualization**
- **Alternating shading** based on nesting level

## Academic Sources Confirming Conventions

### John Sowa's Tutorial
- Authoritative source on Peirce's visual conventions
- Confirms odd/even shading system
- Provides clear examples of proper construction

### Don Roberts' "The Existential Graphs of Charles S. Peirce"
- Comprehensive academic treatment
- Details on shading conventions
- Historical accuracy of visual representations

### Frithjof Dau's Mathematical Framework
- Modern formalization of Peirce's system
- Precise definitions of visual elements
- Compatibility with formal logic systems

## Implementation Strategy for EGRF

### 1. **Context Level Calculation**
```python
def calculate_context_level(context_id, context_manager):
    level = 0
    current = context_manager.contexts[context_id]
    while current.parent_id is not None:
        level += 1
        current = context_manager.contexts[current.parent_id]
    return level

def is_odd_level(context_id, context_manager):
    return calculate_context_level(context_id, context_manager) % 2 == 1
```

### 2. **Visual Styling Rules**
```python
def get_area_style(context_level):
    return {
        "fill": "rgba(128,128,128,0.3)" if context_level % 2 == 1 else "rgba(255,255,255,0.1)",
        "stroke": "black",
        "stroke-width": 2
    }

def get_predicate_style():
    return {
        "fill": "white",
        "stroke": "rgba(0,0,0,0.3)",  # Transparent border
        "stroke-width": 1,
        "hooks": True  # Enable predicate hooks
    }
```

### 3. **Placement Validation**
```python
def validate_predicate_placement(predicate, context_id, context_manager):
    # Predicate must be inside its containing context
    # Predicate must not overlap with inner cuts
    # Predicate border must remain within area bounds
    pass
```

## Next Steps for Implementation

1. **Update EGRF visual specification** with shading system
2. **Implement context level calculation** in EGRF generator
3. **Add predicate transparency and hooks** to visual styling
4. **Validate placement rules** during diagram construction
5. **Test with authentic Peirce examples** to ensure accuracy

This research provides the foundation for implementing authentic Peirce visual conventions in the EGRF diagram specification system.

