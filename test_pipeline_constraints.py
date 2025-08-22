#!/usr/bin/env python3
"""
Test constraint system directly on 9-phase pipeline output to validate dynamic interaction.
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
    
    # Extract pipeline output
    vertex_positions = context.get('vertex_positions', {})
    edge_positions = context.get('edge_positions', {})
    cut_bounds = context.get('cut_bounds', {})
    
    print(f"\nPipeline Output:")
    print(f"  Vertex positions: {vertex_positions}")
    print(f"  Edge positions: {edge_positions}")
    print(f"  Cut bounds: {cut_bounds}")
    
    # Create layout data in EGDF primitive format
    layout_data = {}
    
    # Add vertices
    for vertex_id, position in vertex_positions.items():
        layout_data[vertex_id] = {
            'element_id': vertex_id,
            'element_type': 'vertex',
            'position': position,
            'bounds': (position[0]-2, position[1]-2, position[0]+2, position[1]+2)
        }
    
    # Add predicates
    for edge_id, position in edge_positions.items():
        layout_data[edge_id] = {
            'element_id': edge_id,
            'element_type': 'predicate',
            'position': position,
            'bounds': (position[0]-20, position[1]-10, position[0]+20, position[1]+10)
        }
    
    # Add cuts
    for cut_id, bounds in cut_bounds.items():
        center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
        layout_data[cut_id] = {
            'element_id': cut_id,
            'element_type': 'cut',
            'position': center,
            'bounds': bounds
        }
    
    print(f"\nCreated layout data with {len(layout_data)} elements")
    
    # Initialize constraint system
    constraint_system = SpatialConstraintSystem()
    constraint_system.set_egi_reference(egi)
    
    print("\n=== Testing Constraint Validation on Pipeline Output ===")
    
    # Test 1: Validate pipeline output
    violations = constraint_system.validate_layout(layout_data)
    print(f"Violations in pipeline output: {len(violations)}")
    for violation in violations:
        print(f"  - {violation.description}")
    
    # Test 2: Modify layout to create violations
    print("\n=== Testing Dynamic Constraint Enforcement ===")
    
    # Move a vertex outside its cut
    if layout_data:
        vertex_id = next((k for k, v in layout_data.items() if v.get('element_type') == 'vertex'), None)
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
    
    return True

if __name__ == "__main__":
    success = test_pipeline_constraint_interaction()
    if success:
        print("\n✅ Pipeline constraint interaction test completed successfully")
    else:
        print("\n❌ Pipeline constraint interaction test failed")
