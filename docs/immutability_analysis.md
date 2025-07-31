# EGI Immutability Implementation Plan

## Current Mutability Issues

### 1. EGI Class Mutability
**File**: `egi_core.py`
**Issues**:
- `add_vertex()`, `add_edge()`, `add_cut()` methods modify the EGI in place
- Direct manipulation of `vertices`, `edges`, `cuts` dictionaries
- Context relationships are modified directly

### 2. Transformation Methods Mutability  
**File**: `egi_transformations.py`
**Issues**:
- `_apply_erasure()` removes elements from original EGI
- `_apply_insertion()` adds elements to original EGI
- `_apply_iteration()` modifies vertex collections
- All transformation methods work on `self.egi` directly

### 3. Context and Element Mutability
**File**: `egi_core.py`
**Issues**:
- `Context.enclosed_elements` is a mutable set
- `Context.children` is a mutable set
- `Vertex.incident_edges` is a mutable set
- Element properties are mutable dictionaries

### 4. Deep Copy Issues
**File**: `egi_transformations.py`
**Issues**:
- Current `_deep_copy_egi()` uses YAML serialization (inefficient)
- Element IDs change during copy, breaking references
- Context relationships not properly preserved

## Immutability Implementation Plan

### Phase 1: Core Data Structure Changes

#### 1.1 Make EGI Immutable
- Remove mutating methods (`add_vertex`, `add_edge`, `add_cut`)
- Make collections read-only (use `frozenset` where appropriate)
- Add factory methods for creating new EGI instances

#### 1.2 Make Context Immutable
- Convert `enclosed_elements` and `children` to `frozenset`
- Remove mutating methods
- Add factory methods for creating new contexts

#### 1.3 Make Vertex/Edge Immutable
- Convert `incident_edges` to `frozenset`
- Make properties immutable (use `frozendict` or similar)
- Remove mutating methods

### Phase 2: Transformation Method Changes

#### 2.1 Builder Pattern Implementation
- Create `EGIBuilder` class for constructing new EGI instances
- Implement proper deep copying with ID preservation
- Add methods for incremental construction

#### 2.2 Transform Methods Refactoring
- Change all `_apply_*` methods to return new EGI instances
- Implement proper element copying and relationship preservation
- Ensure mathematical correctness of transformations

### Phase 3: Supporting Infrastructure

#### 3.1 Deep Copy Implementation
- Implement proper deep copy that preserves element IDs
- Maintain context hierarchy relationships
- Preserve all mathematical properties

#### 3.2 Factory Methods
- Add `EGI.create()` factory method
- Add `Context.create()` factory method
- Add `Vertex.create()` and `Edge.create()` factory methods

### Phase 4: API Compatibility

#### 4.1 Update Public API
- Ensure `EGITransformer.apply_transformation()` returns new EGI
- Update CLI to work with immutable pattern
- Maintain backward compatibility where possible

#### 4.2 Update Tests
- Modify tests to expect new instances from transformations
- Add immutability validation tests
- Ensure all existing functionality still works

## Implementation Strategy

### Step 1: Immutable Data Structures
```python
# Before (mutable)
class EGI:
    def add_vertex(self, ...):
        # Modifies self
        
# After (immutable)
class EGI:
    @classmethod
    def create_with_vertex(cls, original_egi, ...):
        # Returns new EGI instance
```

### Step 2: Builder Pattern
```python
class EGIBuilder:
    def __init__(self, original_egi=None):
        # Initialize from original or empty
        
    def add_vertex(self, ...):
        # Add to builder state
        return self
        
    def build(self):
        # Return immutable EGI
```

### Step 3: Transformation Updates
```python
# Before (mutating)
def _apply_erasure(self, element_id):
    del self.egi.edges[element_id]  # Mutates original
    
# After (immutable)
def _apply_erasure(self, element_id):
    builder = EGIBuilder(self.egi)
    builder.remove_edge(element_id)
    return builder.build()  # Returns new EGI
```

## Mathematical Correctness Preservation

### 1. Element Identity
- Preserve element IDs across transformations
- Maintain referential integrity
- Ensure context relationships are preserved

### 2. Transformation Validity
- All validation logic remains the same
- Mathematical constraints still enforced
- Dau's formalism rules still apply

### 3. Performance Considerations
- Minimize copying overhead
- Use structural sharing where possible
- Optimize for common transformation patterns

## Testing Strategy

### 1. Immutability Tests
- Verify original EGI unchanged after transformations
- Test that modifications to returned EGI don't affect original
- Validate deep immutability of nested structures

### 2. Correctness Tests
- All existing tests should pass with new implementation
- Mathematical properties preserved
- Transformation rules still valid

### 3. Performance Tests
- Measure transformation performance
- Compare memory usage
- Ensure acceptable overhead

## Migration Path

### 1. Backward Compatibility
- Maintain existing public API where possible
- Add deprecation warnings for mutating methods
- Provide migration guide for users

### 2. Incremental Implementation
- Implement immutability in phases
- Test each phase thoroughly
- Maintain working system throughout

### 3. Documentation Updates
- Update all documentation to reflect immutable nature
- Add examples of new usage patterns
- Explain benefits of immutable design

This plan ensures that EGI transformations will produce new instances while maintaining mathematical rigor and preserving all existing functionality.

