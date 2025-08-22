#!/usr/bin/env python3
"""
Test the 9-phase pipeline output to verify it produces complete, logically correct primitives.
"""

import sys
import os
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

# Change to repo directory
os.chdir(REPO_ROOT)

def test_9phase_pipeline():
    """Test the 9-phase pipeline with the Socrates example."""
    
    print("Testing 9-phase pipeline output...")
    
    # Import required modules
    from egif_parser_dau import EGIFParser
    from layout_phase_implementations import (
        ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
        PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
        RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
        PhaseStatus
    )
    from spatial_awareness_system import SpatialAwarenessSystem
    
    # Parse the test EGIF
    egif_text = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
    print(f"Input EGIF: {egif_text}")
    
    parser = EGIFParser(egif_text)
    egi = parser.parse()
    
    print(f"\nParsed EGI:")
    print(f"  Vertices: {len(egi.V)} - {[v.id for v in egi.V]}")
    print(f"  Edges: {len(egi.E)} - {[e.id for e in egi.E]}")
    print(f"  Cuts: {len(egi.Cut)} - {[c.id for c in egi.Cut]}")
    print(f"  Nu mapping: {dict(egi.nu)}")
    print(f"  Rel mapping: {dict(egi.rel)}")
    
    # Initialize 9-phase pipeline
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
    
    # Execute pipeline
    context = {}
    print(f"\nExecuting 9-phase pipeline...")
    
    for i, phase in enumerate(phases):
        print(f"  Phase {i+1}: {phase.phase_name}")
        result = phase.execute(egi, context)
        print(f"    Status: {result.status}")
        if result.status != PhaseStatus.COMPLETED:
            print(f"    Error: {result.error_message}")
            break
    
    # Examine pipeline output
    print(f"\nPipeline context keys: {list(context.keys())}")
    
    vertex_positions = context.get('vertex_positions', {})
    edge_positions = context.get('edge_positions', {})
    cut_bounds = context.get('cut_bounds', {})
    ligature_paths = context.get('ligature_paths', {})
    
    print(f"\nPipeline Output:")
    print(f"  Vertex positions: {vertex_positions}")
    print(f"  Edge positions: {edge_positions}")
    print(f"  Cut bounds: {cut_bounds}")
    print(f"  Ligature paths: {ligature_paths}")
    
    # Check completeness
    missing_vertices = [v.id for v in egi.V if v.id not in vertex_positions]
    missing_edges = [e.id for e in egi.E if e.id not in edge_positions]
    missing_cuts = [c.id for c in egi.Cut if c.id not in cut_bounds]
    
    print(f"\nCompleteness Check:")
    print(f"  Missing vertices: {missing_vertices}")
    print(f"  Missing edges: {missing_edges}")
    print(f"  Missing cuts: {missing_cuts}")
    
    complete = not (missing_vertices or missing_edges or missing_cuts)
    print(f"  Pipeline output complete: {complete}")
    
    return complete, context, egi

if __name__ == "__main__":
    complete, context, egi = test_9phase_pipeline()
    if complete:
        print("\n✅ 9-phase pipeline produces complete output")
    else:
        print("\n❌ 9-phase pipeline has missing elements")
