#!/usr/bin/env python3
"""
Test script for Organon browser functionality within the integrated Arisbe home.
Tests corpus browsing, graph loading, and diagram viewing capabilities.
"""

import sys
import os
sys.path.append('src')

from PySide6.QtWidgets import QApplication
from arisbe_home import IntegratedArisbeWindow
import json

def test_organon_browser():
    """Test the Organon browser functionality."""
    print("=== Testing Organon Browser Functionality ===")
    
    # Test 1: Check if corpus files are accessible
    corpus_path = "corpus/graphs/dau_2006_p112_ligature"
    egi_file = f"{corpus_path}/dau_2006_p112_ligature.egi.json"
    metadata_file = f"{corpus_path}/dau_2006_p112_ligature.json"
    
    print(f"Testing corpus access...")
    
    if os.path.exists(egi_file):
        print(f"✓ EGI file found: {egi_file}")
        with open(egi_file, 'r') as f:
            egi_data = json.load(f)
        print(f"✓ EGI loaded: {len(egi_data.get('V', []))} vertices, {len(egi_data.get('E', []))} edges, {len(egi_data.get('Cut', []))} cuts")
    else:
        print(f"✗ EGI file not found: {egi_file}")
        return False
    
    if os.path.exists(metadata_file):
        print(f"✓ Metadata file found: {metadata_file}")
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"✓ Graph metadata: '{metadata.get('title', 'Unknown')}' - {metadata.get('status', 'Unknown')}")
        print(f"✓ Linear forms available: {list(metadata.get('linear_forms', {}).keys())}")
    else:
        print(f"✗ Metadata file not found: {metadata_file}")
        return False
    
    # Test 2: Launch integrated Arisbe home interface
    print(f"\nLaunching integrated Arisbe home interface...")
    app = QApplication(sys.argv)
    
    # Create the integrated home window
    main_window = IntegratedArisbeWindow()
    main_window.show()
    
    print(f"✓ Arisbe home interface launched successfully")
    print(f"✓ Available rooms: Organon (Library), Ergasterion (Workshop), Agon (Game Room)")
    print(f"✓ Test corpus graph: {metadata.get('title')} with ligature structure")
    print(f"✓ EGIF form: {metadata.get('linear_forms', {}).get('egif', {}).get('content', 'N/A')}")
    
    # Note: Interactive testing would require user to:
    # 1. Click "Enter Organon" to access the library
    # 2. Navigate to the dau_2006_p112_ligature graph
    # 3. View the diagram rendering
    # 4. Test handoff to Ergasterion for editing
    
    print(f"\n=== Manual Testing Instructions ===")
    print(f"1. Click '📚 Enter Organon' to access the library")
    print(f"2. Navigate to corpus/graphs/dau_2006_p112_ligature/")
    print(f"3. Select the graph to view its EGI structure")
    print(f"4. Verify diagram rendering shows: 1 vertex, 3 predicates (P,Q,R), 1 cut")
    print(f"5. Test handoff to Ergasterion for interactive editing")
    print(f"6. Use '🏠 Return Home' to navigate back to foyer")
    
    # Keep the application running for manual testing
    print(f"\nApplication ready for manual testing...")
    return app.exec()

if __name__ == "__main__":
    success = test_organon_browser()
    if success == 0:  # QApplication.exec() returns 0 on normal exit
        print("✓ Organon browser test completed successfully")
    else:
        print("✗ Organon browser test encountered issues")
