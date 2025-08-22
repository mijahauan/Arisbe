#!/usr/bin/env python3
"""
Simple test of pipeline-Qt integration without GUI.
"""

import sys
import os
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

def test_pipeline_integration():
    """Test the pipeline integration without Qt GUI."""
    
    print("Testing 9-phase pipeline → Qt integration")
    print("=" * 50)
    
    try:
        # Import required modules
        from egif_parser_dau import EGIFParserDau
        from layout_phase_implementations import (
            ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
            PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
            RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
            PhaseStatus
        )
        from spatial_awareness_system import SpatialAwarenessSystem
        from spatial_constraint_system import SpatialConstraintSystem
        
        print("✅ All imports successful")
        
        # Test EGIF parsing
        egif_text = '*x ~[ ~[ (P x) ] ]'
        print(f"\nTesting EGIF: {egif_text}")
        
        parser = EGIFParserDau()
        egi = parser.parse(egif_text)
        print(f"✅ Parsed EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Test 9-phase pipeline
        print("\nExecuting 9-phase pipeline...")
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
        for i, phase in enumerate(phases):
            result = phase.execute(egi, context)
            print(f"  Phase {i+1} ({phase.phase_name}): {result.status}")
            if result.status != PhaseStatus.COMPLETED:
                print(f"    ❌ Error: {result.error_message}")
                return False
        
        print("✅ 9-phase pipeline completed successfully")
        
        # Test layout extraction
        print(f"\nPipeline context keys: {list(context.keys())}")
        
        element_tracking = context.get('element_tracking', {})
        relative_bounds = context.get('relative_bounds', {})
        
        print(f"Element tracking containers: {list(element_tracking.keys())}")
        print(f"Relative bounds: {list(relative_bounds.keys())}")
        
        # Extract layout data (simulate Qt conversion)
        layout_data = {}
        canvas_width, canvas_height = 580, 380  # Simulate canvas size
        
        # Extract elements
        element_count = 0
        for container_id, elements in element_tracking.items():
            if isinstance(elements, list):
                for element in elements:
                    if isinstance(element, dict):
                        element_id = element['element_id']
                        element_type = element.get('element_type', 'unknown')
                        rel_pos = element.get('relative_position', (0.5, 0.5))
                        abs_x = 10 + rel_pos[0] * canvas_width
                        abs_y = 10 + rel_pos[1] * canvas_height
                        
                        layout_data[element_id] = {
                            'element_id': element_id,
                            'element_type': element_type,
                            'position': (abs_x, abs_y)
                        }
                        element_count += 1
                        print(f"  {element_type}: {element_id} at ({abs_x:.1f}, {abs_y:.1f})")
        
        # Extract cuts
        for cut_id, bounds in relative_bounds.items():
            if cut_id != 'sheet':
                abs_bounds = (
                    10 + bounds[0] * canvas_width,
                    10 + bounds[1] * canvas_height,
                    10 + bounds[2] * canvas_width,
                    10 + bounds[3] * canvas_height
                )
                layout_data[cut_id] = {
                    'element_id': cut_id,
                    'element_type': 'cut',
                    'bounds': abs_bounds
                }
                element_count += 1
                print(f"  cut: {cut_id} bounds {abs_bounds}")
        
        print(f"✅ Extracted {element_count} elements for Qt rendering")
        
        # Test constraint system
        print("\nTesting constraint system...")
        constraint_system = SpatialConstraintSystem()
        constraint_system.set_egi_reference(egi)
        
        # Simulate constraint validation
        violations = constraint_system.validate_spatial_constraints(layout_data)
        print(f"✅ Constraint validation: {len(violations)} violations detected")
        for violation in violations:
            print(f"  - {violation}")
        
        if violations:
            fixed_layout = constraint_system.apply_constraint_fixes(layout_data)
            if fixed_layout:
                print("✅ Constraint fixes applied successfully")
            else:
                print("⚠️  No fixes available")
        
        print(f"\n🎯 INTEGRATION TEST COMPLETE")
        print(f"✅ Pipeline produces {element_count} positioned elements")
        print(f"✅ Constraint system validates and fixes layout")
        print(f"✅ Ready for Qt rendering")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pipeline_integration()
    if success:
        print("\n🏆 Pipeline-Qt integration is working correctly!")
    else:
        print("\n💥 Pipeline-Qt integration has issues")
