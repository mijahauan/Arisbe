"""
Dau-compliant CLI for Existential Graphs with comprehensive transformation support.
Integrates all components: parser, generator, transformations, and Dau's 6+1 model.

Key features:
- All 8 canonical transformation rules accessible
- Isolated vertex support
- Proper area/context distinction
- Interactive and command-line modes
- Comprehensive error handling
"""

import argparse
import sys
from typing import Optional, Dict, List, Set
try:
    # Try relative imports first (when used as module)
    from egi_core_dau import RelationalGraphWithCuts, ElementID
    from egif_parser_dau import parse_egif
    from egif_generator_dau import generate_egif
    from egi_transformations_dau import (
        apply_erasure, apply_insertion, apply_iteration, apply_de_iteration,
        apply_double_cut_addition, apply_double_cut_removal,
        apply_isolated_vertex_addition, apply_isolated_vertex_removal,
        TransformationError
    )
except ImportError:
    # Fall back to absolute imports (when run as script)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from egi_core_dau import RelationalGraphWithCuts, ElementID
    from egif_parser_dau import parse_egif
    from egif_generator_dau import generate_egif
    from egi_transformations_dau import (
        apply_erasure, apply_insertion, apply_iteration, apply_de_iteration,
        apply_double_cut_addition, apply_double_cut_removal,
        apply_isolated_vertex_addition, apply_isolated_vertex_removal,
        TransformationError
    )


class EGICLIApplication:
    """Command-line interface for Existential Graphs."""
    
    def __init__(self):
        self.current_graph: Optional[RelationalGraphWithCuts] = None
        self.history: List[RelationalGraphWithCuts] = []
        self.max_history = 50
    
    def run_interactive(self):
        """Run interactive CLI mode."""
        print("=== Dau-Compliant Existential Graphs CLI ===")
        print("Type 'help' for available commands, 'quit' to exit")
        
        while True:
            try:
                command = input("\nEG> ").strip()
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                self._process_command(command)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def run_command_line(self, args):
        """Run single command from command line."""
        try:
            if args.egif:
                self._load_egif(args.egif)
                print(f"Loaded: {args.egif}")
                self._show_graph_info()
            
            if args.transform:
                if not self.current_graph:
                    print("Error: No graph loaded")
                    return
                
                self._apply_transformation_command(args.transform)
                print(f"Transformed: {generate_egif(self.current_graph)}")
                self._show_graph_info()
            
        except Exception as e:
            print(f"Error: {e}")
    
    def _process_command(self, command: str):
        """Process a single command."""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == 'help':
            self._show_help()
        elif cmd == 'load':
            if len(parts) < 2:
                print("Usage: load <EGIF expression>")
                return
            egif = ' '.join(parts[1:])
            self._load_egif(egif)
        elif cmd == 'show':
            self._show_current_graph()
        elif cmd == 'info':
            self._show_graph_info()
        elif cmd == 'erase':
            self._apply_erasure(parts[1:])
        elif cmd == 'insert':
            self._apply_insertion(parts[1:])
        elif cmd == 'iterate':
            self._apply_iteration(parts[1:])
        elif cmd == 'deiterate':
            self._apply_de_iteration(parts[1:])
        elif cmd == 'addcut':
            self._apply_double_cut_addition(parts[1:])
        elif cmd == 'removecut':
            self._apply_double_cut_removal(parts[1:])
        elif cmd == 'addvertex':
            self._apply_isolated_vertex_addition(parts[1:])
        elif cmd == 'removevertex':
            self._apply_isolated_vertex_removal(parts[1:])
        elif cmd == 'undo':
            self._undo()
        elif cmd == 'history':
            self._show_history()
        elif cmd == 'clear':
            self._clear()
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
Available Commands:

Graph Operations:
  load <EGIF>          Load EGIF expression
  show                 Show current graph as EGIF
  info                 Show graph structure information
  clear                Clear current graph
  
Transformation Rules (Dau's 8 Canonical Rules):
  erase <element>      Erase element from positive context
  insert <type> <args> Insert element into negative context
  iterate <args>       Iterate subgraph to deeper context
  deiterate <element>  De-iterate element
  addcut <elements>    Add double cut around elements
  removecut <cut>      Remove double cut
  addvertex [label]    Add isolated vertex (heavy dot)
  removevertex <vertex> Remove isolated vertex
  
Utility:
  undo                 Undo last transformation
  history              Show transformation history
  help                 Show this help
  quit                 Exit application

Examples:
  load (man *x)
  load *x "Socrates"
  load ~[ (mortal *x) ]
  addvertex
  addvertex "Plato"
  erase edge_123
  removevertex vertex_456
"""
        print(help_text)
    
    def _load_egif(self, egif: str):
        """Load EGIF expression."""
        try:
            self._save_to_history()
            self.current_graph = parse_egif(egif)
            print(f"Loaded: {egif}")
            self._show_graph_info()
        except Exception as e:
            print(f"Failed to load EGIF: {e}")
    
    def _show_current_graph(self):
        """Show current graph as EGIF."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        egif = generate_egif(self.current_graph)
        print(f"Current EGIF: {egif}")
    
    def _show_graph_info(self):
        """Show graph structure information."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        graph = self.current_graph
        print(f"Structure: {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        isolated = graph.get_isolated_vertices()
        if isolated:
            print(f"Isolated vertices: {len(isolated)}")
        
        # Show context information
        sheet_area = len(graph.get_area(graph.sheet))
        sheet_context = len(graph.get_full_context(graph.sheet))
        print(f"Sheet area: {sheet_area}, context: {sheet_context}")
        
        print(f"Has dominating nodes: {graph.has_dominating_nodes()}")
    
    def _apply_erasure(self, args: List[str]):
        """Apply erasure transformation."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        if not args:
            print("Usage: erase <element_id>")
            self._list_elements()
            return
        
        element_id = args[0]
        try:
            self._save_to_history()
            self.current_graph = apply_erasure(self.current_graph, element_id)
            print(f"Erased element {element_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"Erasure failed: {e}")
    
    def _apply_insertion(self, args: List[str]):
        """Apply insertion transformation."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        if len(args) < 2:
            print("Usage: insert <type> <context_id> [args...]")
            print("Types: vertex, edge, cut")
            return
        
        element_type = args[0]
        context_id = args[1]
        
        try:
            self._save_to_history()
            
            if element_type == "vertex":
                label = args[2] if len(args) > 2 else None
                is_generic = label is None or not label.startswith('"')
                self.current_graph = apply_insertion(
                    self.current_graph, "vertex", context_id,
                    label=label, is_generic=is_generic
                )
            elif element_type == "cut":
                self.current_graph = apply_insertion(
                    self.current_graph, "cut", context_id
                )
            else:
                print(f"Unsupported insertion type: {element_type}")
                return
            
            print(f"Inserted {element_type} into {context_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"Insertion failed: {e}")
    
    def _apply_iteration(self, args: List[str]):
        """Apply iteration transformation."""
        print("Iteration not fully implemented yet")
    
    def _apply_de_iteration(self, args: List[str]):
        """Apply de-iteration transformation."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        if not args:
            print("Usage: deiterate <element_id>")
            return
        
        element_id = args[0]
        try:
            self._save_to_history()
            self.current_graph = apply_de_iteration(self.current_graph, element_id)
            print(f"De-iterated element {element_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"De-iteration failed: {e}")
    
    def _apply_double_cut_addition(self, args: List[str]):
        """Apply double cut addition."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        if not args:
            print("Usage: addcut <context_id> [element_ids...]")
            return
        
        context_id = args[0]
        element_ids = set(args[1:]) if len(args) > 1 else set()
        
        # If no elements specified, use all elements in context
        if not element_ids:
            element_ids = self.current_graph.get_area(context_id)
        
        try:
            self._save_to_history()
            self.current_graph = apply_double_cut_addition(
                self.current_graph, element_ids, context_id
            )
            print(f"Added double cut around elements in {context_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"Double cut addition failed: {e}")
    
    def _apply_double_cut_removal(self, args: List[str]):
        """Apply double cut removal."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        if not args:
            print("Usage: removecut <outer_cut_id>")
            return
        
        cut_id = args[0]
        try:
            self._save_to_history()
            self.current_graph = apply_double_cut_removal(self.current_graph, cut_id)
            print(f"Removed double cut {cut_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"Double cut removal failed: {e}")
    
    def _apply_isolated_vertex_addition(self, args: List[str]):
        """Apply isolated vertex addition."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        context_id = args[0] if args else self.current_graph.sheet
        label = args[1] if len(args) > 1 else None
        is_generic = label is None or not (label.startswith('"') and label.endswith('"'))
        
        if label and label.startswith('"') and label.endswith('"'):
            label = label[1:-1]  # Remove quotes
        
        try:
            self._save_to_history()
            self.current_graph = apply_isolated_vertex_addition(
                self.current_graph, context_id, label, is_generic
            )
            print(f"Added isolated vertex to {context_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"Isolated vertex addition failed: {e}")
    
    def _apply_isolated_vertex_removal(self, args: List[str]):
        """Apply isolated vertex removal."""
        if not self.current_graph:
            print("No graph loaded")
            return
        
        if not args:
            print("Usage: removevertex <vertex_id>")
            isolated = self.current_graph.get_isolated_vertices()
            if isolated:
                print(f"Isolated vertices: {list(isolated)}")
            return
        
        vertex_id = args[0]
        try:
            self._save_to_history()
            self.current_graph = apply_isolated_vertex_removal(self.current_graph, vertex_id)
            print(f"Removed isolated vertex {vertex_id}")
            self._show_current_graph()
        except TransformationError as e:
            print(f"Isolated vertex removal failed: {e}")
    
    def _apply_transformation_command(self, transform_cmd: str):
        """Apply transformation from command line."""
        # Simple transformation parsing for command line
        if transform_cmd.startswith("addvertex"):
            self._apply_isolated_vertex_addition([self.current_graph.sheet])
        else:
            print(f"Unsupported transformation: {transform_cmd}")
    
    def _list_elements(self):
        """List all elements in the graph."""
        if not self.current_graph:
            return
        
        print("Available elements:")
        for vertex in self.current_graph.V:
            print(f"  Vertex: {vertex.id}")
        for edge in self.current_graph.E:
            print(f"  Edge: {edge.id}")
        for cut in self.current_graph.Cut:
            print(f"  Cut: {cut.id}")
    
    def _save_to_history(self):
        """Save current graph to history."""
        if self.current_graph:
            self.history.append(self.current_graph)
            if len(self.history) > self.max_history:
                self.history.pop(0)
    
    def _undo(self):
        """Undo last transformation."""
        if not self.history:
            print("No history to undo")
            return
        
        self.current_graph = self.history.pop()
        print("Undone last transformation")
        self._show_current_graph()
    
    def _show_history(self):
        """Show transformation history."""
        if not self.history:
            print("No history")
            return
        
        print(f"History ({len(self.history)} entries):")
        for i, graph in enumerate(self.history[-5:], 1):  # Show last 5
            egif = generate_egif(graph)
            print(f"  {i}. {egif}")
    
    def _clear(self):
        """Clear current graph and history."""
        self.current_graph = None
        self.history.clear()
        print("Cleared graph and history")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dau-compliant Existential Graphs CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python egi_cli_dau.py                           # Interactive mode
  python egi_cli_dau.py --egif "(man *x)"        # Load graph
  python egi_cli_dau.py --egif "*x" --transform addvertex  # Transform
        """
    )
    
    parser.add_argument(
        '--egif', 
        help='EGIF expression to load'
    )
    
    parser.add_argument(
        '--transform',
        help='Transformation to apply'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Force interactive mode'
    )
    
    args = parser.parse_args()
    
    app = EGICLIApplication()
    
    if args.interactive or (not args.egif and not args.transform):
        app.run_interactive()
    else:
        app.run_command_line(args)


if __name__ == "__main__":
    main()

