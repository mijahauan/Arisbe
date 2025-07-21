# Visual Rendering Tests

This directory contains comprehensive testing framework for validating the critical visual rendering fixes in the EG-CL-Manus2 EGRF system.

## Test Files

### Core Testing
- **`test_critical_fixes.py`** - Comprehensive testing suite for all three critical visual issues
- **`test_visual_improvements.py`** - Visual improvements testing framework

## Test Coverage

### Critical Issues Validation
1. **Predicate Containment Testing**
   - Safe positioning algorithm validation
   - Context boundary respect verification
   - Margin calculation accuracy

2. **Visual Artifacts Detection**
   - Style verification (should be "none")
   - Transparency validation (fill/stroke opacity)
   - Size verification (should be 0x0)
   - Text-only rendering confirmation

3. **Alternating Shading Consistency**
   - Level calculation verification
   - Odd/even pattern validation
   - Color scheme consistency

## Running Tests

### Individual Test Execution
```bash
# Test critical fixes
python3 test_critical_fixes.py

# Test visual improvements
python3 test_visual_improvements.py
```

### Expected Results

#### Successful Test Output
```
🎯 CRITICAL FIXES VALIDATION
============================================================
Predicate containment: ✅ WORKING
Visual artifacts eliminated: ✅ WORKING
Shading consistency: ✅ WORKING

🎉 ALL CRITICAL FIXES VALIDATED!
✅ Ready for production use
```

#### Test Validation Details
- **Predicate Analysis**: All predicates show "✅ CLEAN" status
- **Debug Output**: Shows proper positioning within context bounds
- **CLIF Generation**: Produces meaningful logical forms (not empty "()")

## Test Methodology

### Validation Approach
1. **Create Test Graph** - Multi-level context structure with predicates
2. **Generate EGRF** - Apply visual fixes and create EGRF document
3. **Analyze Results** - Check containment, artifacts, and shading
4. **Validate Semantics** - Ensure meaningful CLIF generation

### Test Data Structure
```
Level 0 (Sheet): Root context - transparent
├── Level 1 (Cut): First cut - gray shaded
│   ├── Level 2 (Cut): Second cut - transparent (even)
│   │   └── Level 3 (Cut): Third cut - gray shaded (odd)
│   └── Predicates: Positioned safely within cuts
└── Entities: Heavy lines connecting predicates
```

## Debugging Features

### Debug Output
Tests provide detailed debug information:
- Predicate positioning coordinates
- Context boundary calculations
- Safe area margins
- Level calculation traces

### Artifact Analysis
Comprehensive artifact detection:
- Visual style verification
- Fill/stroke transparency
- Size and positioning
- Text-only rendering status

## Integration with CI/CD

These tests can be integrated into continuous integration:
```bash
# Add to CI pipeline
cd tests/visual/
python3 test_critical_fixes.py
if [ $? -eq 0 ]; then
    echo "✅ Visual rendering tests passed"
else
    echo "❌ Visual rendering tests failed"
    exit 1
fi
```

## Troubleshooting

### Common Issues
1. **Import Errors** - Ensure `src/egrf/` is in Python path
2. **API Mismatches** - Run `tools/visual_fixes/fix_predicate_constructor.py`
3. **Context Issues** - Run `tools/visual_fixes/fix_containing_context_error.py`

### Test Failures
If tests fail, check:
- EGRFPredicate constructor parameters
- Context manager variable ordering
- Visual specification object types

---

**Test Framework Version**: 2.0  
**Last Updated**: July 21, 2025  
**Compatibility**: EG-CL-Manus2 with Visual Fixes

