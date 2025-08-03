"""
Debug script to trace exactly what's happening in the edge rendering pipeline.
Focuses on why edges are positioned but not visually rendered.
"""

import sys
import os

# Ensure current directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from egif_parser_dau import EGIFParser
from tkinter_backend import TkinterCanvas
from diagram_controller import DiagramController
from diagram_renderer import VisualTheme, RenderingContext, RenderingMode
from layout_engine import LayoutEngine


def debug_edge_rendering():
    """Debug the complete edge rendering pipeline step by step"""
    print("🔍 Edge Rendering Debug Pipeline")
    print("=" * 50)
    
    # Step 1: Parse a simple unary predicate
    egif_text = '(Human "Socrates")'
    print(f"📝 Testing: {egif_text}")
    
    try:
        parser = EGIFParser(egif_text)
        graph = parser.parse()
        
        print(f"\n📊 Parsed Graph Structure:")
        print(f"   Vertices: {len(graph.V)}")
        print(f"   Edges: {len(graph.E)}")
        print(f"   Cuts: {len(graph.Cut)}")
        
        # Step 2: Examine the edge object
        if graph.E:
            edge = list(graph.E)[0]
            print(f"\n🔍 Edge Object Details:")
            print(f"   Edge ID: {edge.id}")
            print(f"   Edge type: {type(edge)}")
            print(f"   Edge attributes: {dir(edge)}")
            if hasattr(edge, 'relation'):
                print(f"   Edge.relation: {edge.relation}")
            else:
                print(f"   ❌ Edge has NO 'relation' attribute!")
            
            # Check nu mapping
            if edge.id in graph.nu:
                print(f"   ν mapping: {graph.nu[edge.id]}")
            else:
                print(f"   ❌ Edge not in ν mapping!")
            
            # Check relation mapping (Dau's 7th component)
            if edge.id in graph.rel:
                print(f"   Relation name: {graph.rel[edge.id]}")
            else:
                print(f"   ❌ Edge not in rel mapping!")
        
        # Step 3: Test layout engine
        print(f"\n🎯 Layout Engine Test:")
        layout_engine = LayoutEngine(600, 400)
        layout_result = layout_engine.layout_graph(graph)
        
        print(f"   Elements positioned: {len(layout_result.elements)}")
        
        for element_id, layout_element in layout_result.elements.items():
            print(f"   - {layout_element.element_type}: {element_id[:8]}...")
            if layout_element.element_type == 'edge':
                print(f"     Position: {layout_element.position}")
                print(f"     Bounds: {layout_element.bounds}")
                print(f"     Attachment points: {layout_element.attachment_points}")
                print(f"     Curve points: {layout_element.curve_points}")
        
        # Step 4: Test rendering context
        print(f"\n🎨 Rendering Context Test:")
        canvas = TkinterCanvas(600, 400, title="Edge Debug")
        
        from diagram_renderer import DiagramRenderer, create_rendering_context
        renderer = DiagramRenderer(canvas, VisualTheme.DAU_STANDARD)
        context = create_rendering_context(RenderingMode.NORMAL)
        
        print(f"   Renderer created: {type(renderer)}")
        print(f"   Context created: {context}")
        
        # Step 5: Test edge rendering directly
        print(f"\n🔧 Direct Edge Rendering Test:")
        
        if graph.E:
            edge = list(graph.E)[0]
            if edge.id in layout_result.elements:
                layout_element = layout_result.elements[edge.id]
                
                print(f"   Calling render_edge directly...")
                print(f"   Layout element: {layout_element}")
                print(f"   Edge: {edge}")
                print(f"   Context: {context}")
                
                try:
                    # Clear canvas first
                    renderer.clear_canvas()
                    
                    # Try to render the edge directly
                    renderer.element_renderer.render_edge(layout_element, edge, context)
                    
                    print(f"   ✅ render_edge() called successfully")
                    
                    # Save the result
                    canvas.save_to_file("debug_edge_direct.png")
                    print(f"   💾 Saved direct edge rendering to: debug_edge_direct.png")
                    
                except Exception as e:
                    print(f"   ❌ render_edge() failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"   ❌ Edge not found in layout elements!")
        
        # Step 6: Test full diagram rendering
        print(f"\n🖼️  Full Diagram Rendering Test:")
        try:
            renderer.render_diagram(layout_result, graph, context)
            canvas.save_to_file("debug_full_diagram.png")
            print(f"   💾 Saved full diagram to: debug_full_diagram.png")
        except Exception as e:
            print(f"   ❌ Full diagram rendering failed: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Edge Rendering Debug")
    print("This will trace the complete edge rendering pipeline")
    print()
    
    success = debug_edge_rendering()
    
    if success:
        print("\n✅ Debug completed - check output files and logs above")
    else:
        print("\n❌ Debug failed - see error details above")
    
    print("\n📁 Generated debug files:")
    print("   - debug_edge_direct.png (direct edge rendering)")
    print("   - debug_full_diagram.png (full diagram)")
    print("\n🔍 Edge rendering debug complete!")
