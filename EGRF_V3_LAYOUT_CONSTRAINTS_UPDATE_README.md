# EGRF v3.0 Layout Constraints Update

This package contains the latest implementation of the EGRF v3.0 layout constraints system, which provides a platform-independent layout system that enforces Peirce's logical containment rules while giving users freedom to move elements within their logical containers.

## Installation Instructions

1. Extract the zip file in your Arisbe repository root:
   ```bash
   unzip egrf_v3_layout_constraints_update.zip
   ```

2. The files will be placed in the correct directory structure:
   - `src/egrf/v3/layout_constraints.py` - Core layout constraints implementation
   - `tests/egrf/v3/test_layout_constraints.py` - Comprehensive tests
   - `layout_constraints_demo.py` - Demonstration of the layout constraints system
   - `EGRF_v3_Layout_Constraints_Design.md` - Design document
   - `EGRF_v3_Layout_Constraints_Implementation_Plan.md` - Implementation plan

## Known Issues

There are some technical issues with Python's dataclass ordering requirements that need to be resolved:

1. Python requires non-default parameters to come before parameters with default values in dataclass definitions
2. We need to restructure some of the constraint classes to ensure proper parameter ordering
3. Test cases need to be updated to match the new parameter order

## Next Steps

1. Fix the remaining dataclass issues
2. Complete the implementation of the layout constraints system
3. Integrate with the corpus-based testing approach
4. Create a comprehensive demonstration of the layout constraints system

## Key Benefits

- **Platform Independence:** No absolute coordinates, uses logical constraints
- **Containment Enforcement:** Elements stay within their logical containers
- **User Freedom:** Elements can be moved freely within constraints
- **Auto-Sizing:** Containers size themselves based on contents
- **Visual Rule Enforcement:** Peirce's conventions are maintained

