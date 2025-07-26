#!/usr/bin/env python3
"""
Test script for the integrated Peirce Layout Engine with GUI.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf
from gui.peirce_layout_engine import PeirceLayoutEngine
from gui.peirce_graphics_adapter import PeirceGraphicsAdapter

# Mock scene for testing
class MockScene:
    def __init__(self):
        self.items = []
    
    def addItem(self, item):
        self.items.append(item)
        print(f"Added item to scene: {type(item).__name__}")

def test_integrated_peirce_gui():
    """Test the integrated Peirce Layout Engine with graphics adapter."""
    
    # Initialize Qt application for graphics items (headless)
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Test examples
    examples = [
        ("Simple implication", "(if (Man Socrates) (Mortal Socrates))"),
        ("Existential", "(exists (x) (and (P x) (Q x)))"),
        ("Existential with negation", "(exists (x) (and (P x) (not (Q x))))"),
    ]
    
    parser = CLIFParser()
    layout_engine = PeirceLayoutEngine(viewport_width=800, viewport_height=600)
    
    for name, clif_text in examples:
        print(f"\n{'='*60}")
        print(f"TESTING INTEGRATED GUI: {name}")
        print(f"CLIF: {clif_text}")
        print(f"{'='*60}")
        
        try:
            # Parse CLIF to EG-HG
            parse_result = parser.parse(clif_text)
            print(f"✓ CLIF parsed successfully")
            
            # Convert to EGRF
            egrf_doc = convert_graph_to_egrf(parse_result.graph, {})
            print(f"✓ EGRF created with {len(egrf_doc.logical_elements)} elements")
            
            # Generate rendering instructions
            print(f"\n--- PEIRCE LAYOUT ENGINE ---")
            rendering_instructions = layout_engine.calculate_layout(egrf_doc)
            print(f"✓ Rendering instructions generated")
            print(f"  Elements: {len(rendering_instructions.get('elements', []))}")
            print(f"  Ligatures: {len(rendering_instructions.get('ligatures', []))}")
            
            # Test graphics adapter
            print(f"\n--- GRAPHICS ADAPTER ---")
            mock_scene = MockScene()
            graphics_adapter = PeirceGraphicsAdapter(mock_scene)
            
            graphics_items = graphics_adapter.create_graphics_from_instructions(rendering_instructions)
            print(f"✓ Graphics adapter created {len(graphics_items)} items")
            print(f"✓ Scene now has {len(mock_scene.items)} items")
            
            # Update element names
            graphics_adapter.update_element_names(egrf_doc)
            print(f"✓ Element names updated from EGRF data")
            
            # Validate graphics items
            print(f"\n--- GRAPHICS VALIDATION ---")
            context_items = 0
            predicate_items = 0
            ligature_items = 0
            
            for item_id, item in graphics_items.items():
                item_type = type(item).__name__
                if 'Rect' in item_type or 'Ellipse' in item_type:
                    context_items += 1
                elif 'Text' in item_type:
                    predicate_items += 1
                elif 'Line' in item_type:
                    ligature_items += 1
                print(f"  {item_id}: {item_type}")
            
            print(f"\n--- ITEM COUNTS ---")
            print(f"  Context items (cuts/sheet): {context_items}")
            print(f"  Predicate items (text): {predicate_items}")
            print(f"  Ligature items (lines): {ligature_items}")
            print(f"  Total graphics items: {len(graphics_items)}")
            
            # Check if we have the expected items
            expected_contexts = len([e for e in egrf_doc.logical_elements if e.logical_type in ['sheet', 'cut']])
            expected_predicates = len([e for e in egrf_doc.logical_elements if e.logical_type == 'relation'])
            expected_entities = len([e for e in egrf_doc.logical_elements if e.logical_type == 'individual'])
            
            print(f"\n--- EXPECTED vs ACTUAL ---")
            print(f"  Expected contexts: {expected_contexts}, Actual: {context_items}")
            print(f"  Expected predicates: {expected_predicates}, Actual: {predicate_items}")
            print(f"  Expected entities (as ligatures): {expected_entities}, Actual: {ligature_items}")
            
            if context_items == expected_contexts:
                print(f"  ✓ Context count matches")
            else:
                print(f"  ⚠️  Context count mismatch")
                
            if predicate_items == expected_predicates:
                print(f"  ✓ Predicate count matches")
            else:
                print(f"  ⚠️  Predicate count mismatch")
                
            # Note: Ligature count may be different as one entity can have multiple line segments
            print(f"  ℹ️  Ligature count may vary (one entity can have multiple lines)")
                
        except Exception as e:
            print(f"✗ Failed to process {name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_integrated_peirce_gui()

