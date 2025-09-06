# Annotation System Test Guide

## Overview
This guide provides comprehensive testing instructions for the new Existential Graph annotation system implemented in the Arisbe drawing editor.

## Features to Test

### 1. Double Cut Identification
**Purpose**: Highlight double cuts (nested cuts with only ligatures between them) in red.

**Test Files**:
- `test_double_cuts.egdf.json` - Contains a proper double cut structure
- `corpus/graphs/sowa_cat_on_mat/EGDF/diagram_20250902_202811.egdf.json` - No cuts (should show no double cuts)

**Test Steps**:
1. Launch drawing editor: `python tools/drawing_editor_refactored.py`
2. Load test file via "Load EGDF" button
3. Click "Double Cuts" toggle in Annotations toolbar
4. **Expected**: Nested cuts with only ligatures between them should turn red
5. Toggle off - cuts should return to normal color

### 2. Predicate Arity Annotations
**Purpose**: Display small numbers showing predicate arity near each predicate.

**Test Steps**:
1. Load `corpus/graphs/sowa_cat_on_mat/EGDF/diagram_20250902_202811.egdf.json`
2. Click "Arity" toggle in Annotations toolbar
3. **Expected**: 
   - "On" predicate shows "2" (binary relation)
   - "Mat" predicate shows "1" (unary relation)
   - "Cat" predicate shows "1" (unary relation)
4. Numbers should appear near predicates without interfering with ligatures

### 3. Vertex Variable Annotations
**Purpose**: Display linear form variable names (*x, *y, etc.) near vertices.

**Test Steps**:
1. Load EGDF file with rho mappings
2. Click "Variables" toggle in Annotations toolbar
3. **Expected**: Variable names appear near vertices (e.g., "*x", "*y")
4. For null rho mappings, no annotations should appear

### 4. Predicate Arity Specification
**Purpose**: Right-click context menu to specify predicate arity for nu mapping correspondence.

**Test Steps**:
1. Load any EGDF file with predicates
2. Right-click on a predicate
3. Select "Specify Arity" from context menu
4. **Expected**: Dialog shows current arity and connected vertices count
5. Change arity value and confirm
6. **Expected**: Nu mapping updates, new vertices created/removed as needed
7. File should be marked as modified (asterisk in title)

### 5. UI Integration
**Purpose**: Verify annotation toggles work correctly in both modes.

**Test Steps**:
1. Test all annotation toggles in Composition Mode
2. Switch to Practice Mode
3. Test all annotation toggles again
4. **Expected**: Annotations work consistently in both modes
5. Status bar should show feedback when toggling annotations

## Test Results Template

### Double Cut Identification
- [ ] Correctly identifies nested cuts with only ligatures
- [ ] Ignores cuts with vertices/predicates between them
- [ ] Red highlighting works
- [ ] Toggle on/off functions properly

### Predicate Arity Annotations
- [ ] Shows correct arity numbers from nu mapping
- [ ] Positioned near predicates without interference
- [ ] Updates when arity is modified
- [ ] Toggle on/off functions properly

### Vertex Variable Annotations
- [ ] Shows variable names from rho mapping
- [ ] Formatted as "*x", "*y", etc.
- [ ] Handles null rho mappings correctly
- [ ] Toggle on/off functions properly

### Predicate Arity Specification
- [ ] Right-click context menu appears
- [ ] Dialog shows current arity and vertex count
- [ ] Arity modification updates nu mapping
- [ ] Creates/removes vertices as needed
- [ ] Updates rho mapping for new vertices
- [ ] File marked as modified

### UI Integration
- [ ] Annotation toolbar appears
- [ ] All toggle buttons work
- [ ] Status bar provides feedback
- [ ] Works in both Composition and Practice modes
- [ ] Annotations persist across file loads

## Known Limitations
1. Variable annotations only show for non-null rho mappings
2. Double cut detection requires precise geometric containment
3. Arity specification creates vertices with default variable names

## Debugging Tips
1. Check console output for renderer debug messages
2. Verify EGI inline data structure in EGDF files
3. Use Qt Inspector for graphics item debugging
4. Check annotation_enabled flags in renderer

## Files Created for Testing
- `test_double_cuts.egdf.json` - Double cut test case
- This test guide document

## Architecture Components Tested
- `SharedDiagramRenderer` - Annotation rendering and double cut identification
- `DiagramCoordinator` - Predicate arity management and nu mapping updates
- `RefactoredDrawingEditor` - UI controls and context menus
- `ModularDrawingView` - Right-click context menu handling
