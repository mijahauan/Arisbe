#!/usr/bin/env python3
"""
Test constraint system on actual 9-phase pipeline output format.
"""

import sys
import os
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

def test_pipeline_constraint_interaction():
    """Test constraint system on actual 9-phase pipeline output."""
    
    print("Testing constraint system on 9-phase pipeline output...")
    
    # Import required modules
    from egif_parser_dau import EGIFParser
    from layout_phase_implementations import (
        ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
        PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
        RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
        PhaseStatus
    )
    from spatial_awareness_system import SpatialAwarenessSystem
    from spatial_constraint_system import SpatialConstraintSystem
    
    # Parse test EGIF
    egif_text = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
    print(f"Input EGIF: {egif_text}")
    
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    print(f"EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
    
    # Execute 9-phase pipeline
    spatial_system = SpatialAwarenessSystem()
    phases = [
        ElementSizingPhase(),
        ContainerSizingPhase(spatial_system),
        CollisionDetectionPhase(spatial_system),
        PredicatePositioningPhase(spatial_system),
        VertexPositioningPhase(spatial_system),
        HookAssignmentPhase(),
        RectilinearLigaturePhase(),
        BranchOptimizationPhase(),
        AreaCompactionPhase()
    ]
    
    context = {}
    print("\nExecuting 9-phase pipeline...")
    
    for i, phase in enumerate(phases):
        result = phase.execute(egi, context)
        print(f"  Phase {i+1} ({phase.phase_name}): {result.status}")
        if result.status != PhaseStatus.COMPLETED:
            print(f"    Error: {result.error_message}")
            return False
    
    print(f"Pipeline context keys: {list(context.keys())}")
    
    # Extract pipeline output from element_tracking
    element_tracking = context.get('element_tracking', {})
    relative_bounds = context.get('relative_bounds', {})
    
    print(f"Element tracking: {element_tracking}")
    print(f"Relative bounds: {relative_bounds}")
    
    # Convert to absolute coordinates for constraint testing
    canvas_width, canvas_height = 400, 300  # Reasonable canvas size
    layout_data = {}
    
    # Process element_tracking data
    for container_id, elements in element_tracking.items():
        if isinstance(elements, list):
            for element in elements:
                if isinstance(element, dict):
                    # Convert relative position to absolute
                    rel_pos = element.get('relative_position', (0, 0))
                    abs_x = rel_pos[0] * canvas_width
                    abs_y = rel_pos[1] * canvas_height
                    
                    # Convert relative bounds to absolute
                    rel_bounds = element.get('relative_bounds', (0, 0, 0.1, 0.1))
                    abs_bounds = (
                        rel_bounds[0] * canvas_width,
                        rel_bounds[1] * canvas_height,
                        rel_bounds[2] * canvas_width,
                        rel_bounds[3] * canvas_height
                    )
                    
                    layout_data[element['element_id']] = {
                        'element_id': element['element_id'],
                        'element_type': element.get('element_type', 'unknown'),
                        'position': (abs_x, abs_y),
                        'bounds': abs_bounds
                    }
    
    # Add cuts from relative_bounds
    for cut_id, bounds in relative_bounds.items():
        if cut_id != 'sheet':  # Skip the sheet container
            abs_bounds = (
                bounds[0] * canvas_width,
                bounds[1] * canvas_height,
                bounds[2] * canvas_width,
                bounds[3] * canvas_height
            )
            center_x = (abs_bounds[0] + abs_bounds[2]) / 2
            center_y = (abs_bounds[1] + abs_bounds[3]) / 2
            
            layout_data[cut_id] = {
                'element_id': cut_id,
                'element_type': 'cut',
                'position': (center_x, center_y),
                'bounds': abs_bounds
            }
    
    print(f"\nConverted to absolute coordinates:")
    for elem_id, elem_data in layout_data.items():
        print(f"  {elem_id}: {elem_data['element_type']} at {elem_data['position']}")
    
    # Initialize constraint system
    constraint_system = SpatialConstraintSystem()
    constraint_system.set_egi_reference(egi)
    
    print("\n=== Testing Constraint Validation on Pipeline Output ===")
    
    # Test 1: Validate pipeline output
    violations = constraint_system.validate_layout(layout_data)
    print(f"Violations in pipeline output: {len(violations)}")
    for violation in violations:
        print(f"  - {violation.description}")
    
    # Test 2: Create dynamic constraint violation
    print("\n=== Testing Dynamic Constraint Enforcement ===")
    
    # Find a vertex to move
    vertex_id = None
    for elem_id, elem_data in layout_data.items():
        if elem_data.get('element_type') == 'vertex':
            vertex_id = elem_id
            break
    
    if vertex_id:
        original_pos = layout_data[vertex_id]['position']
        print(f"Moving vertex {vertex_id} from {original_pos} to outside cuts...")
        
        # Move vertex way outside
        layout_data[vertex_id]['position'] = (500, 500)
        layout_data[vertex_id]['bounds'] = (498, 498, 502, 502)
        
        # Check violations
        violations = constraint_system.validate_layout(layout_data)
        print(f"Violations after moving vertex: {len(violations)}")
        for violation in violations:
            print(f"  - {violation.description}")
            if violation.suggested_fix:
                print(f"    Suggested fix: {violation.suggested_fix}")
        
        # Apply fixes
        if violations:
            print("\n=== Testing Constraint Fix Application ===")
            fixed_layout = constraint_system.apply_constraint_fixes(violations, layout_data)
            
            # Check if fixes worked
            new_violations = constraint_system.validate_layout(fixed_layout)
            print(f"Violations after fixes: {len(new_violations)}")
            
            # Show position changes
            new_pos = fixed_layout[vertex_id]['position']
            print(f"Vertex position: {original_pos} → (500, 500) → {new_pos}")
            
            return len(new_violations) == 0
    else:
        print("No vertex found to test dynamic constraints")
        return len(violations) == 0
    
    return True

if __name__ == "__main__":
    success = test_pipeline_constraint_interaction()
    if success:
        print("\n✅ Pipeline constraint interaction test completed successfully")
    else:
        print("\n❌ Pipeline constraint interaction test failed")
