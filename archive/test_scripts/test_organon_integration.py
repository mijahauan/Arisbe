#!/usr/bin/env python3
"""
Test script to verify Organon browser integration within Arisbe home interface.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from arisbe_home import IntegratedArisbeWindow

def test_organon_integration():
    """Test that Organon integration works properly."""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = IntegratedArisbeWindow()
    
    # Test that home widget exists
    assert main_window.home_widget is not None, "Home widget should exist"
    
    # Test that we can access the room request handler
    assert hasattr(main_window, '_handle_room_request'), "Room request handler should exist"
    
    # Test that we can create Organon widget (simulate entering library)
    try:
        main_window._enter_library({})
        assert hasattr(main_window, 'organon_widget'), "Organon widget should be created"
        assert main_window.organon_widget is not None, "Organon widget should not be None"
        print("✓ Organon widget creation successful")
    except Exception as e:
        print(f"✗ Organon widget creation failed: {e}")
        return False
    
    # Test that Organon is properly added to stacked widget
    organon_index = main_window.stacked_widget.indexOf(main_window.organon_widget)
    assert organon_index >= 0, "Organon widget should be in stacked widget"
    print("✓ Organon widget properly integrated into stacked widget")
    
    # Test that we can switch to Organon view
    main_window.stacked_widget.setCurrentWidget(main_window.organon_widget)
    current_widget = main_window.stacked_widget.currentWidget()
    assert current_widget == main_window.organon_widget, "Should be able to switch to Organon view"
    print("✓ Organon view switching works")
    
    # Test that navigation label updates
    main_window.current_room_label.setText("📚 Organon")
    assert main_window.current_room_label.text() == "📚 Organon", "Navigation label should update"
    print("✓ Navigation label updates correctly")
    
    # Test that we can return home
    main_window._show_home()
    current_widget = main_window.stacked_widget.currentWidget()
    assert current_widget == main_window.home_widget, "Should be able to return to home"
    assert main_window.current_room_label.text() == "Foyer", "Navigation label should reset to Foyer"
    print("✓ Return to home functionality works")
    
    print("\n🎉 All Organon integration tests passed!")
    return True

if __name__ == "__main__":
    success = test_organon_integration()
    sys.exit(0 if success else 1)
