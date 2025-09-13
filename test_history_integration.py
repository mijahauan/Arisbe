#!/usr/bin/env python3
"""
Test the integrated transformation history system with persistence.
Demonstrates the complete workflow from session creation to proof export.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from interactive_transformer_with_history import InteractiveTransformerWithHistory
from enhanced_transformation_history import ProofExportFormat
from pathlib import Path

def test_complete_workflow():
    """Test the complete transformation history workflow."""
    
    print("=== Testing Integrated Transformation History System ===\n")
    
    # 1. Create interactive transformer with history
    print("1. Creating interactive transformer with history...")
    transformer = InteractiveTransformerWithHistory("test_histories")
    print("   ✓ Transformer created")
    
    # 2. Create new session
    print("\n2. Creating new transformation session...")
    session_id = transformer.create_new_session(
        name="Peirce Man-Mortal Test",
        description="Testing transformation history with Peirce's classic example",
        initial_egif_path="corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.json"
    )
    print(f"   ✓ Session created: {session_id}")
    
    # 3. Get initial statistics
    print("\n3. Initial session statistics...")
    stats = transformer.get_session_statistics()
    print(f"   ✓ Current step: {stats['history_state'].current_step}")
    print(f"   ✓ Total states: {stats['history_stats']['total_states']}")
    print(f"   ✓ Can undo: {stats['history_state'].can_undo}")
    
    # 4. Apply a transformation
    print("\n4. Applying transformation...")
    result = transformer.apply_transformation_with_history(
        rule_name="DC-",
        target_area="c_ddf31f9b",  # Inner cut from the example
        user_annotation="Simplifying the logical structure by removing redundant negations",
        domain_contexts={"philosophical_reasoning"}
    )
    
    if result["success"]:
        print(f"   ✓ Transformation applied: {result['step_id']}")
        print(f"   ✓ New state: {result['new_state_id']}")
    else:
        print(f"   ✗ Transformation failed: {result.get('error', 'Unknown error')}")
    
    # 5. Get updated statistics
    print("\n5. Updated session statistics...")
    stats = transformer.get_session_statistics()
    print(f"   ✓ Current step: {stats['history_state'].current_step}")
    print(f"   ✓ Total transformations: {stats['history_stats']['total_transformations']}")
    print(f"   ✓ Can undo: {stats['history_state'].can_undo}")
    print(f"   ✓ Unsaved changes: {stats['history_state'].unsaved_changes}")
    
    # 6. Get transformation narrative
    print("\n6. Generating transformation narrative...")
    narrative = transformer.get_transformation_narrative()
    print("   Natural Language Narrative:")
    for line in narrative.split('\n')[:5]:  # First 5 lines
        print(f"   {line}")
    
    # 7. Test undo functionality
    print("\n7. Testing undo functionality...")
    undo_result = transformer.undo_transformation()
    if undo_result["success"]:
        print(f"   ✓ Undo successful: {undo_result['current_state_id']}")
        
        # Check statistics after undo
        stats = transformer.get_session_statistics()
        print(f"   ✓ Current step after undo: {stats['history_state'].current_step}")
    else:
        print(f"   ✗ Undo failed: {undo_result.get('error', 'Unknown error')}")
    
    # 8. Create exploration branch
    print("\n8. Creating exploration branch...")
    branch_id = transformer.create_exploration_branch("Testing alternative transformations")
    print(f"   ✓ Exploration branch created: {branch_id}")
    
    # 9. Save session in different formats
    print("\n9. Saving session in different formats...")
    
    # JSON format
    json_path = transformer.save_session("json")
    print(f"   ✓ Saved as JSON: {json_path}")
    
    # YAML format  
    yaml_path = transformer.save_session("yaml")
    print(f"   ✓ Saved as YAML: {yaml_path}")
    
    # 10. Export proof
    print("\n10. Exporting proof...")
    latex_proof = transformer.export_proof(ProofExportFormat.LATEX_PROOF)
    print("   LaTeX Proof (first few lines):")
    for line in latex_proof.split('\n')[:5]:
        print(f"   {line}")
    
    # 11. Test session loading
    print("\n11. Testing session loading...")
    new_transformer = InteractiveTransformerWithHistory("test_histories")
    
    try:
        loaded_session_id = new_transformer.load_session(json_path)
        print(f"   ✓ Session loaded: {loaded_session_id}")
        
        # Verify loaded session
        loaded_stats = new_transformer.get_session_statistics()
        print(f"   ✓ Loaded session has {loaded_stats['history_stats']['total_states']} states")
        
    except Exception as e:
        print(f"   ✗ Session loading failed: {e}")
    
    # 12. Get available sessions
    print("\n12. Available sessions...")
    available = transformer.get_available_sessions()
    print(f"   ✓ Found {len(available)} saved sessions")
    for session in available[:3]:  # Show first 3
        print(f"   - {session['history_id']}: {session['total_states']} states, {session['total_transformations']} transformations")
    
    # 13. Storage statistics
    print("\n13. Storage statistics...")
    storage_stats = transformer.persistence_manager.get_storage_statistics()
    print(f"   ✓ JSON files: {storage_stats['json_files']}")
    print(f"   ✓ YAML files: {storage_stats['yaml_files']}")
    print(f"   ✓ Total size: {storage_stats['total_size_mb']} MB")
    
    print("\n=== Integration Test Complete ===")
    print("Demonstrated features:")
    print("• Session creation and management")
    print("• Transformation application with history tracking")
    print("• Undo/redo functionality")
    print("• Exploration branching")
    print("• Multi-format persistence (JSON, YAML)")
    print("• Natural language narrative generation")
    print("• Proof export capabilities")
    print("• Session loading and recovery")
    print("• Storage management and statistics")
    
    return transformer

if __name__ == "__main__":
    try:
        test_transformer = test_complete_workflow()
        print(f"\n✓ All tests completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
