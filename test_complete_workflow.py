#!/usr/bin/env python3
"""
Test script for complete de novo graph creation workflow:
Organon → Ergasterion → Save → Return

This script tests the integrated workflow for creating new existential graphs
from scratch, including:
1. Creating new graph in Organon
2. Launching Ergasterion for diagram creation
3. Manual element creation and constraint validation
4. Saving EGDF and generating EGI
5. Returning to Organon with updated corpus display

Usage:
    python test_complete_workflow.py

Manual Testing Steps:
1. Launch Arisbe home interface
2. Navigate to Organon (Library)
3. Click "New Graph" and enter a title
4. Verify automatic launch of Ergasterion
5. Create diagram elements via left-click context menu
6. Save diagram and verify return to Organon
7. Verify new graph appears in corpus with proper files
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_workflow():
    """Test the complete de novo workflow."""
    from PySide6.QtWidgets import QApplication
    from src.arisbe_home import IntegratedArisbeWindow
    
    print("=== Complete De Novo Workflow Test ===")
    print()
    print("This test launches the integrated Arisbe interface.")
    print("Follow these manual testing steps:")
    print()
    print("1. ORGANON - NEW GRAPH CREATION:")
    print("   - Click 'Enter Library (Organon)' from home")
    print("   - Click 'New Graph' button")
    print("   - Enter a descriptive title (e.g., 'Test Graph 1')")
    print("   - Verify automatic launch of Ergasterion")
    print()
    print("2. ERGASTERION - DIAGRAM CREATION:")
    print("   - Left-click on empty canvas to open context menu")
    print("   - Select 'Add Vertex' to create a vertex")
    print("   - Left-click elsewhere and select 'Add Predicate'")
    print("   - Create a ligature by selecting 'Add Ligature' and connecting elements")
    print("   - Verify constraint validation (no overlaps, proper connections)")
    print()
    print("3. SAVE AND RETURN:")
    print("   - Click 'Save EGDF' button")
    print("   - Verify save confirmation dialog")
    print("   - Click 'Yes' to return to Organon")
    print("   - Verify automatic navigation back to Organon")
    print()
    print("4. ORGANON - VERIFY RESULTS:")
    print("   - Verify new graph appears in corpus tree")
    print("   - Verify graph has both EGDF and EGI files")
    print("   - Verify diagram displays in read-only view")
    print("   - Check metadata shows linear forms")
    print()
    print("Expected Files Created:")
    print("   - corpus/<graph_name>/<graph_name>.json (metadata)")
    print("   - corpus/<graph_name>/<graph_name>.egi.json (logical structure)")
    print("   - corpus/<graph_name>/EGDF/<timestamp>_<id>.egdf.json (diagram)")
    print()
    print("Starting Arisbe interface...")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # Create and show the main Arisbe home interface
    home = IntegratedArisbeWindow()
    home.show()
    
    # Run the application
    return app.exec()

if __name__ == "__main__":
    try:
        exit_code = test_workflow()
        print("\n" + "=" * 50)
        print("Workflow test completed.")
        print("Check console output for any errors or warnings.")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error during workflow test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
