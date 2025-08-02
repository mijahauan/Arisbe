#!/usr/bin/env python3
"""
Demonstration of the Arisbe diagrammatic rendering system.
Shows how to create and visualize Existential Graph diagrams using Dau's formalism.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from egi_core_dau import RelationalGraphWithCuts, create_empty_graph, create_vertex, create_edge, create_cut
    from egif_parser_dau import parse_egif
    from diagram_canvas import DiagramCanvas
    from canvas_backend import get_available_backends
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory and have all dependencies installed.")
    sys.exit(1)


def create_simple_example():
    """Create a simple graph example: (man *x) (mortal x)"""
    print("Creating simple example: (man *x) (mortal x)")
    
    try:
        graph = parse_egif("(man *x) (mortal x)")
        return graph
    except Exception as e:
        print(f"Error parsing EGIF: {e}")
        # Fallback: create manually using Dau's formalism
        graph = create_empty_graph()
        
        # Add vertex for *x
        x_vertex = create_vertex(label=None, is_generic=True)
        graph = graph.with_vertex(x_vertex)
        
        # Add relations
        man_edge = create_edge()
        graph = graph.with_edge(man_edge, (x_vertex.id,), "man")
        
        mortal_edge = create_edge()
        graph = graph.with_edge(mortal_edge, (x_vertex.id,), "mortal")
        
        return graph


def create_cut_example():
    """Create an example with a cut: (man *x) ~[(mortal x)]"""
    print("Creating cut example: (man *x) ~[(mortal x)]")
    
    try:
        graph = parse_egif("(man *x) ~[(mortal x)]")
        return graph
    except Exception as e:
        print(f"Error parsing EGIF: {e}")
        # Fallback: create manually
        graph = create_empty_graph()
        
        # Add vertex for *x on sheet
        x_vertex = create_vertex(label=None, is_generic=True)
        graph = graph.with_vertex(x_vertex)
        
        # Add man relation on sheet
        man_edge = create_edge()
        graph = graph.with_edge(man_edge, (x_vertex.id,), "man")
        
        # Add cut (negative context)
        cut = create_cut()
        graph = graph.with_cut(cut)
        
        # Add vertex for x in cut (same logical individual)
        x_vertex_cut = create_vertex(label=None, is_generic=True)
        graph = graph.with_vertex(x_vertex_cut)
        
        # Add mortal relation in cut
        mortal_edge = create_edge()
        graph = graph.with_edge(mortal_edge, (x_vertex_cut.id,), "mortal", cut.id)
        
        return graph


def create_constant_example():
    """Create an example with constants: (man Socrates) (mortal Socrates)"""
    print("Creating constant example: (man Socrates) (mortal Socrates)")
    
    graph = create_empty_graph()
    
    # Add constant vertex for Socrates
    socrates_vertex = create_vertex(label="Socrates", is_generic=False)
    graph = graph.with_vertex(socrates_vertex)
    
    # Add relations
    man_edge = create_edge()
    graph = graph.with_edge(man_edge, (socrates_vertex.id,), "man")
    
    mortal_edge = create_edge()
    graph = graph.with_edge(mortal_edge, (socrates_vertex.id,), "mortal")
    
    return graph


def create_complex_example():
    """Create a more complex example with multiple cuts and relations"""
    print("Creating complex example with nested cuts")
    
    graph = create_empty_graph()
    
    # Add vertices on sheet
    x_vertex = create_vertex(label=None, is_generic=True)
    y_vertex = create_vertex(label=None, is_generic=True)
    graph = graph.with_vertex(x_vertex)
    graph = graph.with_vertex(y_vertex)
    
    # Add relation connecting them
    loves_edge = create_edge()
    graph = graph.with_edge(loves_edge, (x_vertex.id, y_vertex.id), "loves")
    
    # Add first cut
    cut1 = create_cut()
    graph = graph.with_cut(cut1)
    
    # Add vertices in first cut
    x_vertex_cut1 = create_vertex(label=None, is_generic=True)
    graph = graph.with_vertex(x_vertex_cut1)
    
    # Add relation in first cut
    happy_edge = create_edge()
    graph = graph.with_edge(happy_edge, (x_vertex_cut1.id,), "happy", cut1.id)
    
    # Add nested cut
    cut2 = create_cut()
    graph = graph.with_cut(cut2, cut1.id)
    
    # Add vertices in nested cut
    x_vertex_cut2 = create_vertex(label=None, is_generic=True)
    graph = graph.with_vertex(x_vertex_cut2)
    
    # Add relation in nested cut
    sad_edge = create_edge()
    graph = graph.with_edge(sad_edge, (x_vertex_cut2.id,), "sad", cut2.id)
    
    return graph


def demonstrate_backends():
    """Demonstrate available canvas backends"""
    print("\n" + "="*50)
    print("CANVAS BACKEND DEMONSTRATION")
    print("="*50)
    
    available = get_available_backends()
    print(f"Available backends: {available}")
    
    if not available:
        print("No canvas backends available! Please install pygame or ensure tkinter is available.")
        return False
    
    return True


def run_interactive_demo(graph: RelationalGraphWithCuts, title: str, backend_name: str = None):
    """Run an interactive diagram demo"""
    print(f"\nStarting interactive demo: {title}")
    print("Click on elements to select them, press Escape to deselect")
    print("Close the window to continue to next demo")
    
    try:
        canvas = DiagramCanvas(800, 600, backend_name)
        canvas.render_graph(graph)
        canvas.run()  # This will block until window is closed
    except Exception as e:
        print(f"Error running demo: {e}")
        print("This might be due to missing dependencies or display issues")


def save_diagram_examples():
    """Save diagram examples to files"""
    print("\n" + "="*50)
    print("SAVING DIAGRAM EXAMPLES")
    print("="*50)
    
    examples = [
        ("simple", create_simple_example()),
        ("cut", create_cut_example()),
        ("constants", create_constant_example()),
        ("complex", create_complex_example())
    ]
    
    for name, graph in examples:
        try:
            # Use tkinter backend explicitly for reliable saving
            canvas = DiagramCanvas(800, 600, "tkinter")
            canvas.render_graph(graph)
            filename = f"diagram_{name}.png"
            canvas.save_diagram(filename)
            print(f"Saved {filename}")
            canvas.close()
        except Exception as e:
            print(f"Error saving {name}: {e}")


def main():
    """Main demonstration function"""
    print("ARISBE DIAGRAMMATIC RENDERING DEMONSTRATION")
    print("=" * 50)
    
    # Check backends
    if not demonstrate_backends():
        return
    
    # Create examples
    examples = [
        ("Simple Relations", create_simple_example()),
        ("Cut (Negation)", create_cut_example()),
        ("Constants", create_constant_example()),
        ("Complex Nested", create_complex_example())
    ]
    
    print(f"\nCreated {len(examples)} example diagrams")
    
    # Show graph information
    for title, graph in examples:
        print(f"\n{title}:")
        print(f"  Vertices: {len(graph.V)}")
        print(f"  Edges: {len(graph.E)}")
        print(f"  Cuts: {len(graph.Cut)}")
    
    # Ask user what they want to do
    print("\n" + "="*50)
    print("DEMO OPTIONS")
    print("="*50)
    print("1. Run interactive demos (requires display)")
    print("2. Save diagrams to PNG files")
    print("3. Both")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice in ['1', '3']:
            print("\nRunning interactive demos...")
            for title, graph in examples:
                run_interactive_demo(graph, title)
        
        if choice in ['2', '3']:
            save_diagram_examples()
        
        if choice == '4':
            print("Exiting...")
            return
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error during demo: {e}")
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()
