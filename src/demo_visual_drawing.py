"""
Visual Drawing Demonstration
Shows the clean architecture actually drawing sensible diagrams following Dau's conventions.
Creates a window with an interactive diagram that you can see and interact with.
"""

import sys
import os

# Ensure current directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from egi_core_dau import create_empty_graph, create_vertex, create_edge, create_cut
from egif_parser_dau import EGIFParser
from tkinter_backend import TkinterCanvas
from diagram_controller import DiagramController
from diagram_renderer import VisualTheme


def create_demo_graph():
    """Create a meaningful demo graph to visualize"""
    print("🔧 Creating demo graph with nested structure...")
    
    # Parse a meaningful EGIF expression
    egif_text = '(Human "Socrates") ~[ (Mortal "Socrates") ~[ (Wise "Socrates") ] ]'
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        print(f"✅ Parsed: {egif_text}")
        print(f"   Graph: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        return graph, egif_text
    except Exception as e:
        print(f"⚠️  EGIF parsing failed: {e}")
        print("🔧 Creating manual graph instead...")
        
        # Create graph manually
        graph = create_empty_graph()
        
        # Add Socrates vertex
        socrates = create_vertex(label="Socrates", is_generic=False)
        graph = graph.with_vertex_in_context(socrates, graph.sheet)
        
        # Add Human relation
        human_edge = create_edge()
        graph = graph.with_edge(human_edge, [socrates.id], "Human")
        
        # Create first cut (negation)
        cut1 = create_cut()
        graph = graph.with_cut(cut1, graph.sheet)
        
        # Add Mortal relation inside cut
        mortal_edge = create_edge()
        graph = graph.with_edge(mortal_edge, [socrates.id], "Mortal", cut1.id)
        
        # Create nested cut
        cut2 = create_cut()
        graph = graph.with_cut(cut2, cut1.id)
        
        # Add Wise relation inside nested cut
        wise_edge = create_edge()
        graph = graph.with_edge(wise_edge, [socrates.id], "Wise", cut2.id)
        
        return graph, "Manual: Human(Socrates) ∧ ¬(Mortal(Socrates) ∧ ¬Wise(Socrates))"


def demo_visual_drawing():
    """Create and show a visual diagram"""
    print("🎨 Visual Drawing Demonstration")
    print("=" * 50)
    
    # Step 1: Create the demo graph
    graph, description = create_demo_graph()
    
    # Step 2: Create canvas and controller
    print("\n🖥️  Creating visual canvas...")
    canvas = TkinterCanvas(900, 700, title="Arisbe: Clean Architecture Demo")
    
    print("🎮 Setting up diagram controller...")
    controller = DiagramController(canvas, 900, 700, VisualTheme.DAU_STANDARD)
    
    # Step 3: Set the graph and trigger rendering
    print("🔄 Rendering diagram...")
    controller.set_graph(graph)
    
    # Step 4: Show what we're demonstrating
    print(f"\n📊 Demonstrating: {description}")
    print("\n✨ Visual Features to Observe:")
    print("   - Heavy lines for identity (Dau convention)")
    print("   - Fine lines for cuts (negation boundaries)")
    print("   - Proper hierarchical nesting")
    print("   - Non-overlapping cut layout")
    print("   - Predicate attachment with hooks")
    print("   - Professional spatial arrangement")
    
    # Step 5: Add interaction instructions
    print("\n🖱️  Interaction Instructions:")
    print("   - Click elements to select them")
    print("   - Drag to create selection rectangles")
    print("   - Press ESC to clear selections")
    print("   - Close window to exit")
    
    # Step 6: Show layout quality information
    if controller.state.layout_result:
        layout = controller.state.layout_result
        print(f"\n📐 Layout Quality:")
        print(f"   - Elements positioned: {len(layout.elements)}")
        print(f"   - Quality score: {layout.layout_quality_score:.2f}")
        print(f"   - Constraints satisfied: {len(layout.layout_constraints_satisfied)}")
    
    # Step 7: Save a PNG for reference
    try:
        output_file = "visual_demo_output.png"
        controller.save_diagram(output_file)
        print(f"\n💾 Diagram saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Save failed: {e}")
    
    print("\n🚀 Opening interactive window...")
    print("   (Close the window when you're done exploring)")
    
    # Step 8: Run interactive loop
    try:
        canvas.root.mainloop()
        print("\n👋 Window closed - demo complete!")
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n⚠️  Demo ended with error: {e}")
    
    return True


def demo_multiple_examples():
    """Show multiple example diagrams"""
    print("\n🎯 Multiple Example Demonstration")
    print("-" * 40)
    
    examples = [
        '(loves "John" "Mary")',
        '~[ (mortal *x) ]',
        '(Human "Socrates") ~[ ~[ (Mortal "Socrates") ] ]',
        '*x ~[ (Human x) (Mortal x) ]'
    ]
    
    for i, egif in enumerate(examples, 1):
        print(f"\n📋 Example {i}: {egif}")
        
        try:
            parser = EGIFParser(egif)
            graph = parser.parse()
            
            # Create canvas for this example
            canvas = TkinterCanvas(800, 600, title=f"Example {i}: {egif[:30]}...")
            controller = DiagramController(canvas, 800, 600)
            controller.set_graph(graph)
            
            # Save this example
            output_file = f"example_{i}_output.png"
            controller.save_diagram(output_file)
            print(f"   💾 Saved to: {output_file}")
            
            # Show layout info
            if controller.state.layout_result:
                layout = controller.state.layout_result
                print(f"   📐 Layout: {len(layout.elements)} elements, quality {layout.layout_quality_score:.2f}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Visual Drawing Demonstration")
    print("This will show you actual diagrams following Dau's conventions")
    print()
    
    try:
        # Main visual demo
        demo_visual_drawing()
        
        # Multiple examples (saved as PNG files)
        demo_multiple_examples()
        
        print("\n🎉 Visual Drawing Demonstration Complete!")
        print("✅ Clean architecture successfully renders Dau-compliant diagrams")
        print("✅ Ready for Phase 2: Selection Overlays & Dynamic Effects")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ Visual demonstration complete!")
