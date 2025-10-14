# Coverage Baseline Report

**Generated**: 2025-10-14 06:25:54

## Overall Coverage

**Total Coverage**: 11.0%

### Coverage Distribution

- **Excellent (≥80%)**: 4 modules
- **Good (50-79%)**: 5 modules
- **Fair (20-49%)**: 26 modules
- **Poor (1-19%)**: 31 modules
- **None (0%)**: 67 modules

## Well-Tested Modules (≥80%)

- src/egi_spatial_correspondence.py: 100%
- src/gui_clean/agon/__init__.py: 100%
- src/gui_clean/common/__init__.py: 100%
- src/gui_clean/organon/__init__.py: 100%

## Modules Without Tests (0%)

**Count**: 67 modules

**Examples** (first 10):

- src/abstract_layout_engine.py
- src/alu_coordinate_system.py
- src/alu_svg_renderer.py
- src/area_aware_astar.py
- src/arisbe_home.py
- src/authoritative_layout_coordinator.py
- src/balanced_position_optimizer.py
- src/bottom_up_d3_engine.py
- src/chapter18_improved_translation.py
- src/chapter18_refined_translation.py
- *... and 57 more*

## Recommendations

### Short Term (Next Sprint)
1. Focus on core modules with 0% coverage
2. Target: Bring total coverage from 11% to 20%
3. Prioritize modules in protected core

### Medium Term (Next Month)
1. Achieve 40% total coverage
2. All protected modules > 50% coverage
3. Integration tests for GUI components

### Long Term (Next Quarter)
1. Target 70% total coverage
2. All production modules > 80% coverage
3. Full regression test suite

## Next Steps

1. Review modules with 0% coverage
2. Write tests for high-priority modules first
3. Re-run baseline measurement monthly
4. Track progress in session state
