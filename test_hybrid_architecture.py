#!/usr/bin/env python3
"""
Test Hybrid Architecture - 9-Phase Pipeline + EGDF Controller + Qt Integration

This demonstrates the complete hybrid architecture:
EGIF → EGI → 9-Phase Pipeline → EGDF Document → EGDF Controller → Qt Platform
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PySide6.QtCore import Qt

# Add src to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT / 'src'))
os.chdir(REPO_ROOT)

class HybridArchitectureWindow(QWidget):
    """Test window for hybrid architecture."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hybrid Architecture: 9-Phase Pipeline + EGDF Controller")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create layout
        layout = QHBoxLayout(self)
        
        # Left panel - controls
        controls = QVBoxLayout()
        
        # EGIF input
        controls.addWidget(QLabel("EGIF Input:"))
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(100)
        self.egif_input.setPlainText("*x ~[ ~[ (P x) ] ]")
        controls.addWidget(self.egif_input)
        
        # Process button
        self.process_btn = QPushButton("Process with Hybrid Architecture")
        self.process_btn.clicked.connect(self.process_hybrid)
        controls.addWidget(self.process_btn)
        
        # Status
        controls.addWidget(QLabel("Processing Status:"))
        self.status = QTextEdit()
        self.status.setMaximumHeight(400)
        controls.addWidget(self.status)
        
        # Example buttons
        controls.addWidget(QLabel("Examples:"))
        examples = [
            ("Simple", "*x (P x)"),
            ("Binary", "*x *y (Loves x y)"),
            ("Single Cut", "*x ~[ (P x) ]"),
            ("Double Cut", "*x ~[ ~[ (P x) ] ]"),
            ("Complex", "*x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]")
        ]
        
        for name, egif in examples:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, e=egif: self.load_example(e))
            controls.addWidget(btn)
        
        controls.addStretch()
        
        # Right panel - visualization
        viz_layout = QVBoxLayout()
        viz_layout.addWidget(QLabel("EGDF Controller Output:"))
        
        # Create simple visualization area
        self.viz_area = QTextEdit()
        self.viz_area.setReadOnly(True)
        viz_layout.addWidget(self.viz_area)
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(controls)
        left_widget.setMaximumWidth(400)
        
        right_widget = QWidget()
        right_widget.setLayout(viz_layout)
        
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        # Initialize systems
        self.egdf_controller = None
        self.initialize_systems()
        
        # Process default example
        self.process_hybrid()
    
    def initialize_systems(self):
        """Initialize EGDF Controller and platform adapter."""
        try:
            from egdf_controller import create_egdf_controller
            self.egdf_controller = create_egdf_controller()
            
            # Create mock platform adapter for testing
            self.platform_adapter = MockQtPlatformAdapter(self.viz_area)
            self.egdf_controller.register_platform_adapter("qt_mock", self.platform_adapter)
            
            self.status.append("✅ EGDF Controller initialized")
            self.status.append("✅ Mock Qt platform adapter registered")
            
        except Exception as e:
            self.status.append(f"❌ System initialization failed: {e}")
    
    def load_example(self, egif_text):
        """Load an example EGIF."""
        self.egif_input.setPlainText(egif_text)
        self.process_hybrid()
    
    def process_hybrid(self):
        """Process EGIF through hybrid architecture."""
        if not self.egdf_controller:
            self.status.setPlainText("❌ EGDF Controller not available")
            return
        
        egif_text = self.egif_input.toPlainText().strip()
        if not egif_text:
            self.status.setPlainText("❌ No EGIF input")
            return
        
        try:
            self.status.setPlainText("🔄 Processing through Hybrid Architecture...")
            
            # Step 1: Parse EGIF to EGI
            from egif_parser_dau import EGIFParser
            parser = EGIFParser(egif_text)
            egi = parser.parse()
            
            self.status.append(f"✅ Step 1 - EGIF→EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            # Step 2: Execute 9-phase pipeline with EGDF output
            from layout_phase_implementations import (
                ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
                PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
                RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
                PhaseStatus, PhaseResult
            )
            from spatial_awareness_system import SpatialAwarenessSystem
            
            # Create pipeline phases manually since LayoutPipeline doesn't exist
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
                AreaCompactionPhase()  # Generates EGDF document
            ]
            
            # Execute phases sequentially
            context = {}
            egdf_document = None
            
            for phase in phases:
                phase_result = phase.execute(egi, context)
                if phase_result.status != PhaseStatus.COMPLETED:
                    self.status.append(f"❌ Phase {phase.phase_name} failed: {phase_result.error_message}")
                    return
                
                # Update context with phase results
                context.update(phase_result.context if hasattr(phase_result, 'context') else {})
                
                # Check if this phase generated an EGDF document
                if hasattr(phase_result, 'egdf_document') and phase_result.egdf_document:
                    egdf_document = phase_result.egdf_document
                
                # Also check context for EGDF document
                if 'egdf_document' in context and context['egdf_document']:
                    egdf_document = context['egdf_document']
            
            # Step 3: Check for EGDF document from pipeline
            self.status.append(f"✅ Step 2 - Pipeline completed with {len(context.get('vertex_elements', {}))} vertices, {len(context.get('predicate_elements', {}))} predicates")
            
            if not egdf_document:
                self.status.append(f"❌ No EGDF document generated from pipeline")
                return
            
            self.status.append(f"✅ Step 3 - EGDF Document: {len(egdf_document.visual_layout.get('spatial_primitives', []))} spatial primitives")
            
            # Step 4: Direct platform rendering from EGDF
            # The EGDF document should contain everything needed for rendering
            self.status.append(f"✅ Step 4 - EGDF contains {len(egdf_document.visual_layout.get('spatial_primitives', []))} spatial primitives")
            
            # Show what's in the EGDF for verification
            spatial_primitives = egdf_document.visual_layout.get('spatial_primitives', [])
            for i, primitive in enumerate(spatial_primitives[:3]):  # Show first 3
                ptype = primitive.get('type', 'unknown')
                bounds = primitive.get('bounds', {})
                self.status.append(f"  Primitive {i+1}: {ptype} at {bounds}")
            
            # Step 5: Load EGDF into controller (should be simple)
            if self.egdf_controller.load_egdf_document(egdf_document):
                self.status.append("✅ Step 5 - EGDF Controller loaded document")
                
                # Step 6: Render to Qt platform (should just draw the primitives)
                if self.egdf_controller.render_to_platform("qt_mock"):
                    self.status.append("✅ Step 6 - Rendered to Qt platform")
                    
                    # Step 7: Validate platform output
                    validation_result = self.egdf_controller.validate_platform_output("qt_mock", tolerance=2.0)
                    if validation_result.is_valid:
                        self.status.append(f"✅ Step 7 - Platform validation passed ({validation_result.element_count} elements)")
                    else:
                        self.status.append(f"❌ Step 7 - Platform validation failed: {validation_result.error_message}")
                else:
                    self.status.append("❌ Step 6 - Qt platform rendering failed")
            else:
                self.status.append("❌ Step 5 - EGDF Controller failed to load document")
            else:
                self.status.append(f"⚠️ Step 6 - Platform validation issues: {len(validation_result.violations)} violations")
                for violation in validation_result.violations[:3]:  # Show first 3
                    self.status.append(f"   • {violation}")
            
            # Step 7: Export EGDF
            yaml_path = "test_output.yaml"
            if self.egdf_controller.export_egdf_yaml(yaml_path):
                self.status.append(f"✅ Step 7 - EGDF exported to {yaml_path}")
            
            # Summary
            self.status.append(f"\n🎯 HYBRID ARCHITECTURE COMPLETE")
            self.status.append(f"  • Pipeline: 9 phases with collision detection & constraints")
            self.status.append(f"  • EGDF: {len(egdf_document.visual_layout.get('spatial_primitives', []))} spatial primitives")
            self.status.append(f"  • Controller: Platform communication & validation")
            self.status.append(f"  • Ready for: Ergasterion real-time constraints")
            
        except Exception as e:
            self.status.append(f"❌ Hybrid architecture failed: {e}")
            import traceback
            self.status.append(f"Traceback: {traceback.format_exc()}")


class MockQtPlatformAdapter:
    """Mock platform adapter for testing EGDF Controller integration."""
    
    def __init__(self, viz_area):
        self.viz_area = viz_area
        self.rendered_elements = {}
    
    def render_spatial_primitive(self, primitive):
        """Mock rendering - just store the primitive."""
        element_id = primitive.get('element_id')
        if element_id:
            self.rendered_elements[element_id] = primitive
            
            # Update visualization
            element_type = primitive.get('element_type', 'unknown')
            position = primitive.get('position', (0, 0))
            bounds = primitive.get('bounds', (0, 0, 0, 0))
            
            self.viz_area.append(f"🎨 Rendered {element_type} {element_id}: pos={position}, bounds={bounds}")
            return True
        return False
    
    def get_rendered_bounds(self, element_id):
        """Return bounds of rendered element."""
        if element_id in self.rendered_elements:
            return self.rendered_elements[element_id].get('bounds')
        return None
    
    def clear_canvas(self):
        """Clear the mock canvas."""
        self.rendered_elements.clear()
        self.viz_area.clear()
        self.viz_area.append("🧹 Canvas cleared")


def main():
    app = QApplication(sys.argv)
    
    window = HybridArchitectureWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    result = main()
    print(f"Hybrid architecture test completed with exit code: {result}")
