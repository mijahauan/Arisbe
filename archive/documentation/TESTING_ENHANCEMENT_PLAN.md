# 🧪 Testing Enhancement Plan - Pre-GUI Preparation

**Date**: 2025-09-30  
**Status**: 📋 **PLANNING PHASE**  
**Goal**: Implement comprehensive 3-level testing strategy before GUI development

---

## **🎯 CURRENT STATE ASSESSMENT**

### **✅ What We Have (Good Foundation):**
- DiagramController basic functionality tests (11/11 passing)
- Command pattern validation
- Integration with real layout engine
- Validation system tests
- Undo/redo functionality tests

### **❌ Critical Gaps Identified:**
1. **No mock-based isolation testing** - Controller tested with real dependencies
2. **No EGI Core Model unit tests** - Transformation rules not tested in isolation
3. **No style variation testing** - Only default style tested
4. **No Golden Master testing** - No regression detection for layout outputs
5. **No user workflow simulations** - Individual operations only, not full scenarios

---

## **📋 ENHANCEMENT STRATEGY**

Following the 3-level testing strategy recommended:

### **Level 1: Unit Tests (Isolation) - 5 New Test Suites**

#### **1.1 EGI Core Model Tests** ⭐ HIGH PRIORITY
**File**: `tests/test_egi_transformation_rules_unit.py`

**What to Test:**
- Each transformation rule (DC+, DC-, INS, ERA, IT+, IT-) in complete isolation
- Direct EGI manipulation without any controller or layout involvement
- Precondition validation
- Post-condition verification

**Example Tests:**
```python
def test_double_cut_insertion_unit():
    """Test DC+ rule directly on EGI model."""
    # Create minimal EGI
    egi = create_empty_graph()
    vertex = create_vertex(label="Human", is_generic=False)
    egi = egi.with_vertex(vertex)
    
    # Apply DC+ transformation directly
    from formal_transformation_rules import DoubleNegationInsertionRule
    rule = DoubleNegationInsertionRule()
    context = TransformationContext(
        source_egi=egi,
        target_area=egi.sheet,
        elements=[vertex.id]
    )
    new_egi = rule.apply_transformation(context)
    
    # Assert EGI structure
    assert len(new_egi.Cut) == len(egi.Cut) + 2  # Two new cuts
    assert all(c in new_egi.area for c in new_egi.Cut)  # Cuts in area mapping
    # Verify nesting: inner cut contains vertex, outer contains inner
    
def test_erasure_preconditions_unit():
    """Test ERA rule precondition validation."""
    # Create EGI in negative context
    # Attempt erasure (should fail)
    # Assert precondition error raised
```

**Test Coverage Goals:**
- All 6 transformation rules
- Valid applications (positive tests)
- Invalid applications (precondition failures)
- Edge cases (empty graphs, complex nesting)

---

#### **1.2 DiagramController Unit Tests (with Mocks)** ⭐ HIGH PRIORITY
**File**: `tests/test_diagram_controller_unit_mocked.py`

**What to Test:**
- Controller logic in complete isolation using mocks
- State management without layout engine dependency
- Layout delta persistence across transformations

**Example Tests:**
```python
from unittest.mock import Mock, MagicMock

def test_controller_position_update_mocked():
    """Test position update logic without real layout engine."""
    # Create mock layout engine
    mock_layout_engine = Mock()
    mock_dto = Mock()
    mock_dto.vertices = [Mock(id='v1', pos=(50.0, 50.0))]
    mock_layout_engine.generate_layout.return_value = mock_dto
    
    # Initialize controller with mock
    controller = DiagramController(layout_engine=mock_layout_engine)
    controller.load_egi(simple_egi)
    
    # Update position
    success = controller.update_element_position('v1', (100.0, 100.0))
    
    # Assert only state changed, not EGI
    assert success
    assert 'v1' in controller.layout_deltas
    assert controller.layout_deltas['v1'].new_position == (100.0, 100.0)
    assert controller.egi_model == simple_egi  # EGI unchanged
    
def test_controller_formal_rule_state_management_mocked():
    """Test formal rule application state management."""
    mock_layout_engine = Mock()
    controller = DiagramController(layout_engine=mock_layout_engine)
    
    # Apply formal rule
    controller.apply_formal_rule('DC+', ['v1'], 'sheet_id')
    
    # Assert EGI was modified
    assert controller.egi_model != original_egi
    # Assert layout deltas were preserved/discarded correctly
    # Assert new DTO was generated
```

**Test Coverage Goals:**
- State management isolation
- Layout delta logic
- Transformation orchestration
- Validation without layout dependency

---

#### **1.3 Style Specification Unit Tests**
**File**: `tests/test_style_specification_unit.py`

**What to Test:**
- Style loading and validation
- Style merging and inheritance
- Style attribute access patterns

---

### **Level 2: Integration Tests - 3 New Test Suites**

#### **2.1 Style + Layout Engine Integration** ⭐ HIGH PRIORITY
**File**: `tests/test_style_layout_integration.py`

**What to Test:**
- Layout engine behavior with different style specifications
- Style attribute propagation through DTO
- Visual differences from style variations

**Example Tests:**
```python
def test_padding_variations():
    """Test that different padding styles produce different layouts."""
    egi = create_test_egi()
    layout_engine = DefinitiveEGILayoutEngine()
    
    # Style 1: Large padding
    style_large = create_style_from_json("styles/large_padding_test.json")
    dto_large = layout_engine.generate_layout(egi, style_large)
    
    # Style 2: Small padding
    style_small = create_style_from_json("styles/small_padding_test.json")
    dto_small = layout_engine.generate_layout(egi, style_small)
    
    # Assert different dimensions
    for area_id in dto_large.areas.keys():
        large_area = dto_large.areas[area_id]
        small_area = dto_small.areas[area_id]
        assert large_area.width > small_area.width
        
def test_polarity_styling():
    """Test that polarity affects cut rendering."""
    egi = create_nested_cuts_egi()  # Even and odd cuts
    layout_engine = DefinitiveEGILayoutEngine()
    dto = layout_engine.generate_layout(egi)
    
    # Find even and odd cuts
    even_cut = next(c for c in dto.cuts if c.polarity == 0)
    odd_cut = next(c for c in dto.cuts if c.polarity == 1)
    
    # Assert different styling
    assert even_cut.style['fill'] != odd_cut.style['fill']
    assert even_cut.style['opacity'] != odd_cut.style['opacity']
```

---

#### **2.2 Controller + Layout Engine Integration (Enhanced)**
**File**: `tests/test_controller_layout_integration.py`

**Current**: We test with real instances but not comprehensively  
**Enhanced**: Test full re-layout scenarios systematically

**Example Tests:**
```python
def test_relayout_after_transformation():
    """Test that formal transformations trigger full relayout."""
    controller = DiagramController()
    egi = create_test_egi()
    controller.load_egi(egi)
    
    # Capture initial layout
    initial_dto = controller.current_dto
    initial_positions = {v.id: v.pos for v in initial_dto.vertices}
    
    # Apply transformation
    controller.apply_formal_rule('DC+', ['v1', 'e1'], sheet_id)
    
    # Capture new layout
    new_dto = controller.current_dto
    
    # Assert DTO changed
    assert new_dto != initial_dto
    assert len(new_dto.cuts) == len(initial_dto.cuts) + 2
    
    # Assert positions may have changed (relayout occurred)
    # But user deltas should be preserved where possible
```

---

### **Level 3: End-to-End Tests - 2 New Test Suites** ⭐⭐ CRITICAL

#### **3.1 Golden Master Testing** ⭐⭐ HIGHEST PRIORITY
**File**: `tests/test_golden_master_layouts.py`  
**Directory**: `tests/golden_masters/`

**What to Test:**
- Deterministic layout output for known graphs
- Regression detection for layout changes
- Stability across code changes

**Implementation Strategy:**
```python
import json
import hashlib
from pathlib import Path

GOLDEN_DIR = Path("tests/golden_masters")

def serialize_dto_for_comparison(dto):
    """Serialize DTO to comparable JSON format."""
    return {
        'vertices': [
            {'id': v.id, 'pos': v.pos, 'label': v.label}
            for v in sorted(dto.vertices, key=lambda x: x.id)
        ],
        'edges': [
            {'id': e.id, 'vertices': e.vertex_ids, 'label': e.label}
            for e in sorted(dto.edge_labels, key=lambda x: x.id)
        ],
        'cuts': [
            {'id': c.id, 'polarity': c.polarity, 'bounds': c.bounds}
            for c in sorted(dto.cuts, key=lambda x: x.id)
        ],
        # ... other elements
    }

def test_golden_master_simple_graph():
    """Test layout stability for simple graph."""
    egi = load_egi_json("tomos/simple_example.json")
    controller = DiagramController()
    controller.load_egi(egi)
    
    dto = controller.current_dto
    serialized = serialize_dto_for_comparison(dto)
    
    golden_file = GOLDEN_DIR / "simple_example_golden.json"
    
    if not golden_file.exists():
        # First run: create golden master
        with open(golden_file, 'w') as f:
            json.dump(serialized, f, indent=2)
        pytest.skip("Golden master created")
    
    # Compare with golden master
    with open(golden_file, 'r') as f:
        golden_data = json.load(f)
    
    assert serialized == golden_data, (
        "Layout output differs from golden master! "
        "If this change is intentional, delete the golden master file."
    )

def test_golden_master_corpus():
    """Test all tomos graphs against golden masters."""
    for corpus_file in Path("corpus").glob("*.json"):
        # Load and test each tomos graph
        # Compare against golden master
        pass
```

**Golden Master Test Coverage:**
- Simple graphs (1-2 vertices, 1 predicate)
- Complex nested structures (3-4 levels of cuts)
- Large graphs (10+ vertices)
- All tomos examples (15 graphs)

---

#### **3.2 User Workflow Simulation** ⭐⭐ HIGHEST PRIORITY
**File**: `tests/test_user_workflows.py`

**What to Test:**
- Complete user session scenarios
- Multi-step interactions
- State persistence across operations
- Realistic usage patterns

**Example Tests:**
```python
def test_workflow_graph_construction():
    """Simulate user building a graph from scratch."""
    controller = DiagramController()
    
    # Step 1: Load empty graph
    empty_egi = create_empty_graph()
    controller.load_egi(empty_egi)
    assert len(controller.current_dto.vertices) == 0
    
    # Step 2: Add vertex (iteration of existence)
    # NOTE: This might require extending our API
    controller.apply_formal_rule('IT+', [...], sheet_id)
    dto_after_vertex = controller.current_dto
    assert len(dto_after_vertex.vertices) == 1
    v1_original_pos = dto_after_vertex.vertices[0].pos
    
    # Step 3: User repositions vertex (aesthetic)
    v1_id = dto_after_vertex.vertices[0].id
    controller.update_element_position(v1_id, (200.0, 200.0))
    dto_after_move = controller.current_dto
    assert dto_after_move.vertices[0].pos == (200.0, 200.0)
    
    # Step 4: Add double cut around vertex (DC+)
    controller.apply_formal_rule('DC+', [v1_id], sheet_id)
    dto_after_dc = controller.current_dto
    assert len(dto_after_dc.cuts) == 2
    # Assert vertex position preserved through transformation
    assert dto_after_dc.vertices[0].pos == (200.0, 200.0)
    
    # Step 5: Undo DC+
    controller.undo_last_command()
    dto_after_undo = controller.current_dto
    assert len(dto_after_undo.cuts) == 0
    # Assert vertex position still preserved
    assert dto_after_undo.vertices[0].pos == (200.0, 200.0)

def test_workflow_logical_proof():
    """Simulate user constructing a logical proof."""
    controller = DiagramController()
    
    # Load premises
    premises_egi = parse_egif("[*x] (Human x) ~[ (Mortal x) ]")
    controller.load_egi(premises_egi)
    
    # Step through proof transformations
    # 1. Insert new subgraph (INS in negative area)
    # 2. Apply iteration (IT+)
    # 3. Apply deiteration (IT-)
    # 4. Erase double negation (DC-)
    # 5. Erase conclusion (ERA in positive area)
    
    # Assert each step is valid
    # Assert final state is desired conclusion

def test_workflow_aesthetic_adjustments():
    """Simulate user making multiple aesthetic adjustments."""
    controller = DiagramController()
    egi = load_egi_json("tomos/complex_example.json")
    controller.load_egi(egi)
    
    initial_dto = controller.current_dto
    
    # User moves multiple elements
    for i, vertex in enumerate(initial_dto.vertices[:3]):
        new_pos = (100.0 + i*50, 150.0 + i*50)
        controller.update_element_position(vertex.id, new_pos)
    
    dto_after_moves = controller.current_dto
    
    # Verify all positions updated
    for i, vertex in enumerate(dto_after_moves.vertices[:3]):
        expected_pos = (100.0 + i*50, 150.0 + i*50)
        assert vertex.pos == expected_pos
    
    # Now apply logical transformation
    controller.apply_formal_rule('DC+', [dto_after_moves.vertices[0].id], sheet_id)
    
    dto_after_transform = controller.current_dto
    
    # User deltas should persist where valid
    # Check that moved elements maintained their positions if possible

def test_workflow_undo_redo_sequence():
    """Test complex undo/redo interactions."""
    executor = CommandExecutor(controller)
    
    # Perform sequence of operations
    # Mix logical and aesthetic changes
    # Undo several steps
    # Redo some steps
    # Continue with new operations
    
    # Assert state is always consistent
    # Assert command history is correct
```

**Workflow Test Coverage:**
- Graph construction from scratch
- Logical proof sequences
- Aesthetic adjustment sessions
- Mixed logical/aesthetic operations
- Undo/redo scenarios
- Error recovery scenarios

---

## **📊 IMPLEMENTATION PRIORITY**

### **Phase 1: Critical Foundation (Do First)** 🔥
1. **EGI Core Model Unit Tests** - Test transformation rules in isolation
2. **Golden Master Testing** - Establish layout regression detection
3. **User Workflow Simulations** - Validate realistic usage patterns

**Why First?** These catch fundamental logic errors and regressions.

### **Phase 2: Isolation Testing (Do Second)**
4. **Mock-based Controller Tests** - True unit testing of controller
5. **Style + Layout Integration Tests** - Validate style system

**Why Second?** These improve test quality and isolate dependencies.

### **Phase 3: Enhancement (Do Third)**
6. **Enhanced Integration Tests** - More comprehensive scenarios
7. **Additional Workflow Tests** - Cover more user patterns

---

## **🎯 SUCCESS CRITERIA**

Before GUI development begins, we should have:

### **Test Coverage Metrics:**
- ✅ All 6 transformation rules tested in isolation
- ✅ 15+ golden master tests (one per tomos graph + extras)
- ✅ 10+ user workflow simulations
- ✅ Controller unit tests with >90% code coverage (mocked)
- ✅ Style integration tests covering major variations

### **Quality Metrics:**
- ✅ 100% of tests passing
- ✅ Golden masters established for all tomos graphs
- ✅ No regressions detected
- ✅ All realistic user workflows validated

### **Documentation:**
- ✅ Test documentation updated
- ✅ Golden master maintenance guide
- ✅ Workflow test catalog

---

## **📁 NEW TEST FILE STRUCTURE**

```
tests/
├── unit/
│   ├── test_egi_transformation_rules_unit.py     [NEW]
│   ├── test_diagram_controller_unit_mocked.py    [NEW]
│   └── test_style_specification_unit.py          [NEW]
├── integration/
│   ├── test_style_layout_integration.py          [NEW]
│   └── test_controller_layout_integration.py     [ENHANCED]
├── end_to_end/
│   ├── test_golden_master_layouts.py             [NEW] ⭐⭐
│   └── test_user_workflows.py                    [NEW] ⭐⭐
├── golden_masters/
│   ├── simple_example_golden.json                [NEW]
│   ├── nested_cuts_golden.json                   [NEW]
│   ├── complex_graph_golden.json                 [NEW]
│   └── ... (15+ files)
└── fixtures/
    ├── test_egis.py                              [NEW]
    ├── test_styles.py                            [NEW]
    └── mock_helpers.py                           [NEW]
```

---

## **⚡ QUICK START: Minimum Viable Enhancement**

If we want to move forward with GUI but mitigate risk, implement **at minimum**:

1. **Golden Master Tests** (1-2 days)
   - Create golden masters for 15 tomos graphs
   - Detect layout regressions automatically

2. **Basic User Workflow Tests** (1 day)
   - Test 3-5 most common user scenarios
   - Validate multi-step interactions work

This gives us ~80% of the value with ~20% of the effort.

---

## **🚀 NEXT STEPS**

**Decision Point**: How comprehensive should we be before GUI?

**Option A - Thorough (Recommended)**: Implement all phases (~1-2 weeks)
- Complete test coverage
- High confidence for GUI development
- Regression detection infrastructure in place

**Option B - Pragmatic (Faster)**: Implement Phase 1 only (~3-4 days)
- Golden master tests
- Critical workflow tests
- Good enough confidence, fill gaps as needed

**Option C - Minimal (Risky)**: Just golden masters (~1-2 days)
- Basic regression detection
- Proceed to GUI with current test suite
- Accept some risk, iterate quickly

**Recommendation**: **Option A (Thorough)** - The time invested now will save weeks of debugging during GUI development.

---

**Created**: 2025-09-30  
**Status**: Planning - Awaiting user decision on approach
