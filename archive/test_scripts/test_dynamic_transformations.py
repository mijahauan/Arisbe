#!/usr/bin/env python3
"""
Test Dynamic Transformation System

Tests the dynamic transformation tracking system for interactive diagram modifications.
"""

import sys
import os
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QTransform

from test_interactive_viewer import TestMainWindow
from dynamic_transformation_tracker import TransformationType
from egi_core_dau import Vertex, Edge, Cut


class TransformationTestWindow(TestMainWindow):
    """Extended test window with transformation testing capabilities."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Transformation Test")
        self.setup_transformation_controls()
        
    def setup_transformation_controls(self):
        """Add transformation test controls."""
        # Create transformation test buttons
        transform_layout = QHBoxLayout()
        
        # Test vertex insertion
        insert_vertex_btn = QPushButton("Insert Vertex")
        insert_vertex_btn.clicked.connect(self.test_vertex_insertion)
        transform_layout.addWidget(insert_vertex_btn)
        
        # Test vertex movement
        move_vertex_btn = QPushButton("Move Vertex")
        move_vertex_btn.clicked.connect(self.test_vertex_movement)
        transform_layout.addWidget(move_vertex_btn)
        
        # Test cut resizing
        resize_cut_btn = QPushButton("Resize Cut")
        resize_cut_btn.clicked.connect(self.test_cut_resizing)
        transform_layout.addWidget(resize_cut_btn)
        
        # Test area verification
        verify_areas_btn = QPushButton("Verify Areas")
        verify_areas_btn.clicked.connect(self.test_area_verification)
        transform_layout.addWidget(verify_areas_btn)
        
        # Get the central widget's layout and add transformation controls
        central_widget = self.centralWidget()
        if central_widget and central_widget.layout():
            central_widget.layout().addLayout(transform_layout)
    
    def test_vertex_insertion(self):
        """Test inserting a new vertex."""
        print("\n=== Testing Vertex Insertion ===")
        
        # Insert vertex in sheet area
        new_vertex_id = "v_new_1"
        position = QPointF(-50.0, -50.0)  # Should be in sheet area
        
        success = self.viewer.renderer.insert_vertex_at_position(new_vertex_id, position)
        print(f"Vertex insertion result: {success}")
        
        if success:
            # Verify the vertex was positioned correctly
            if self.viewer.renderer.spatial_manager:
                actual_area = self.viewer.renderer.spatial_manager.get_area_at_point(position)
                print(f"New vertex positioned in area: {actual_area}")
            
            # Print transformation tracker state
            if self.viewer.renderer.transformation_tracker:
                print(self.viewer.renderer.transformation_tracker.debug_spatial_state())
    
    def test_vertex_movement(self):
        """Test moving an existing vertex."""
        print("\n=== Testing Vertex Movement ===")
        
        # Move v1 to a different position
        element_id = "v1"
        new_position = QPointF(0.0, 0.0)  # Move to center (should be in cut)
        
        success = self.viewer.renderer.move_element_to_position(element_id, new_position)
        print(f"Vertex movement result: {success}")
        
        if success:
            # Verify the vertex was moved correctly
            if self.viewer.renderer.spatial_manager:
                actual_area = self.viewer.renderer.spatial_manager.get_area_at_point(new_position)
                print(f"Moved vertex now in area: {actual_area}")
            
            # Print transformation tracker state
            if self.viewer.renderer.transformation_tracker:
                print(self.viewer.renderer.transformation_tracker.debug_spatial_state())
    
    def test_cut_resizing(self):
        """Test resizing a cut."""
        print("\n=== Testing Cut Resizing ===")
        
        # Resize the cut to be larger
        cut_id = "c1"
        new_bounds = QRectF(-80.0, -60.0, 160.0, 120.0)  # Larger cut
        
        success = self.viewer.renderer.resize_cut(cut_id, new_bounds)
        print(f"Cut resizing result: {success}")
        
        if success:
            # Verify the cut was resized
            if self.viewer.renderer.spatial_manager:
                cut_item = self.viewer.renderer.spatial_manager.get_area_item(cut_id)
                if cut_item:
                    print(f"Cut new bounds: {cut_item.boundingRect()}")
            
            # Print transformation tracker state
            if self.viewer.renderer.transformation_tracker:
                print(self.viewer.renderer.transformation_tracker.debug_spatial_state())
    
    def test_area_verification(self):
        """Test area assignment verification."""
        print("\n=== Testing Area Verification ===")
        
        # Get current view result and verify assignments
        if self.viewer.renderer.current_view_result:
            self.viewer.renderer._verify_element_area_assignments(self.viewer.renderer.current_view_result)
        
        # Print spatial manager debug info
        if self.viewer.renderer.spatial_manager:
            print("\nSpatial Manager State:")
            print(self.viewer.renderer.spatial_manager.debug_area_info())
        
        # Print transformation tracker state
        if self.viewer.renderer.transformation_tracker:
            print("\nTransformation Tracker State:")
            print(self.viewer.renderer.transformation_tracker.debug_spatial_state())


def main():
    """Run transformation tests."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = TransformationTestWindow()
    
    # Load simple example
    window.load_simple_example()
    
    # Show window
    window.show()
    
    print("=== Dynamic Transformation Test Started ===")
    print("Use the buttons to test different transformation operations")
    print("Check console output for detailed results")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
