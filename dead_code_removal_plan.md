# Dead Code Removal Plan for drawing_editor.py

## Analysis Results
- **Total lines:** 6,334
- **Executed during EGDF loading:** 21% (941 lines)
- **Dead code:** 79% (3,482 lines)

## Phase 1: Safe Removals (Immediate)
✅ Remove unused imports (Set, Union, QKeySequence, QGraphicsLineItem, QStatusBar)
- Remove unused variables identified by vulture
- Remove redundant if-conditions

## Phase 2: Function-Level Analysis (Next)
Based on coverage, these function ranges are NEVER executed:
- Lines 62-119: Likely unused utility functions
- Lines 123-125, 130-132: Small unused blocks
- Lines 422-564: Large unused block (~140 lines)
- Lines 852-906: Another large unused section
- Lines 1147-1199: Unused functionality
- Lines 3601-3841: Massive unused block (~240 lines)

## Phase 3: Feature Removal (Careful Review)
Large unused sections suggest entire features that can be removed:
- Lines 4053-4099: Unused feature block
- Lines 4264-4313: Another feature block
- Lines 5542-5615: Large unused section
- Lines 6039-6092: End-of-file unused code

## Phase 4: Modularization
After removal, split remaining ~1,500 lines into focused modules:
- `egdf_loader.py` - EGDF loading and layout
- `graphics_items.py` - Custom graphics item classes  
- `interaction_handlers.py` - Mouse/keyboard handling
- `drawing_core.py` - Core drawing operations

## Validation Strategy
1. Run coverage after each phase
2. Test EGDF loading functionality
3. Ensure no regression in working features
4. Use git to track changes and enable rollback

## Expected Result
- Reduce from 6,334 lines to ~1,500 lines (76% reduction)
- Improve maintainability and debugging
- Faster load times and reduced memory usage
