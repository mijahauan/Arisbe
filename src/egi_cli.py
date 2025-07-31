"""
Immutable command-line interface for Existential Graphs.
Works with the new immutable architecture where transformations return new EGI instances.
"""

import argparse
import sys
import os
from typing import List, Optional, Dict, Any
import re

# Add src directory to path for imports when run as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try relative imports first (when used as module)
    from .egi_core import EGI, create_empty_egi, Alphabet
    from .egif_parser import parse_egif
    from .egif_generator import generate_egif
    from .egi_transformations import (
        apply_transformation, TransformationRule, TransformationError,
        can_erase, can_insert, can_iterate, can_de_iterate,
        can_add_double_cut, can_remove_double_cut,
        can_add_isolated_vertex, can_remove_isolated_vertex
    )
except ImportError:
    # Fall back to absolute imports (when run as script)
    from egi_core import EGI, create_empty_egi, Alphabet
    from egif_parser import parse_egif
    from egif_generator import generate_egif
    from egi_transformations import (
        apply_transformation, TransformationRule, TransformationError,
        can_erase, can_insert, can_iterate, can_de_iterate,
        can_add_double_cut, can_remove_double_cut,
        can_add_isolated_vertex, can_remove_isolated_vertex
    )


class MarkupParser:
    """Parser for markup annotations in EGIF expressions."""
    
    def __init__(self):
        self.markup_patterns = [
            (r'\^(\([^)]+\))\^', 'erase'),  # ^(relation args)^
            (r'\^~\[\[\^', 'remove_double_cut_start'),  # ^~[[^
            (r'\]\]', 'remove_double_cut_end'),  # ]]
        ]
    
    def parse_markup(self, egif_with_markup: str) -> List[Dict[str, Any]]:
        """Parse markup annotations and return list of instructions."""
        instructions = []
        
        for pattern, instruction_type in self.markup_patterns:
            matches = list(re.finditer(pattern, egif_with_markup))
            
            for match in matches:
                if instruction_type == 'erase':
                    element_text = match.group(1)
                    instructions.append({
                        'type': 'erase',
                        'element_text': element_text,
                        'position': match.start()
                    })
                elif instruction_type == 'remove_double_cut_start':
                    instructions.append({
                        'type': 'remove_double_cut',
                        'position': match.start()
                    })
        
        return instructions
    
    def clean_markup(self, egif_with_markup: str) -> str:
        """Remove markup annotations to get clean EGIF."""
        clean_egif = egif_with_markup
        
        # Remove erase markup: ^(relation)^ -> (relation)
        clean_egif = re.sub(r'\^(\([^)]+\))\^', r'\1', clean_egif)
        
        # Handle double cut removal
        clean_egif = re.sub(r'\^~\[\[\^', '~[ ', clean_egif)
        clean_egif = re.sub(r'\]\]', ' ]', clean_egif)
        
        return clean_egif.strip()


class EGICLIApplication:
    """Immutable CLI application for Existential Graphs."""
    
    def __init__(self):
        self.current_egi: Optional[EGI] = None
        self.history: List[EGI] = []
        self.markup_parser = MarkupParser()
    
    def load_egif(self, egif: str):
        """Load EGIF expression into current EGI."""
        try:
            self.current_egi = parse_egif(egif)
            self.history = [self.current_egi]  # Reset history
            print(f"Loaded: {egif}")
            print(f"Parsed: {len(self.current_egi.vertices)} vertices, "
                  f"{len(self.current_egi.edges)} edges, "
                  f"{len(self.current_egi.contexts)} cuts")
        except Exception as e:
            print(f"Failed to load EGIF: {e}")
    
    def show_current(self):
        """Show current EGI as EGIF."""
        if self.current_egi is None:
            print("No EGI loaded")
            return
        
        try:
            egif = generate_egif(self.current_egi)
            print(f"Current EGIF: {egif}")
            print(f"Structure: {len(self.current_egi.vertices)} vertices, "
                  f"{len(self.current_egi.edges)} edges, "
                  f"{len(self.current_egi.contexts)} cuts")
        except Exception as e:
            print(f"Error generating EGIF: {e}")
    
    def apply_transformation(self, egif_with_markup: str):
        """Apply transformation based on markup in EGIF."""
        if self.current_egi is None:
            print("No EGI loaded")
            return
        
        try:
            # Parse markup instructions
            clean_egif = self.markup_parser.clean_markup(egif_with_markup)
            instructions = self.markup_parser.parse_markup(egif_with_markup)
            
            print(f"Clean EGIF: {clean_egif}")
            print(f"Found {len(instructions)} markup instruction(s)")
            
            if not instructions:
                print("No markup instructions found")
                return
            
            # Apply each instruction
            new_egi = self.current_egi
            
            for instruction in instructions:
                if instruction['type'] == 'erase':
                    new_egi = self._apply_erasure_instruction(new_egi, instruction)
                elif instruction['type'] == 'remove_double_cut':
                    new_egi = self._apply_double_cut_removal_instruction(new_egi, instruction)
            
            # Update current EGI and add to history
            self.history.append(self.current_egi)
            self.current_egi = new_egi
            
            # Show result
            result_egif = generate_egif(self.current_egi)
            print(f"Result: {result_egif}")
            
        except Exception as e:
            print(f"Transformation failed: {e}")
    
    def _apply_erasure_instruction(self, egi: EGI, instruction: Dict[str, Any]) -> EGI:
        """Apply erasure instruction to EGI."""
        element_text = instruction['element_text']
        print(f"Applying erase...")
        
        # Find the element to erase
        element_id = self._find_element_by_text(egi, element_text)
        
        if not element_id:
            raise TransformationError(f"Element not found: {element_text}")
        
        if not can_erase(egi, element_id):
            raise TransformationError("Cannot erase from negative context")
        
        new_egi = apply_transformation(egi, TransformationRule.ERASURE, element_id=element_id)
        print(f"Erased element: {element_text}")
        
        return new_egi
    
    def _apply_double_cut_removal_instruction(self, egi: EGI, instruction: Dict[str, Any]) -> EGI:
        """Apply double cut removal instruction to EGI."""
        print(f"Applying double cut removal...")
        
        # Find empty double cuts
        for context in egi.contexts:
            if (len(context.children) == 1 and 
                len(context.enclosed_elements) == 0):
                
                child_id = next(iter(context.children))
                child_context = egi.get_context(child_id)
                
                if (len(child_context.enclosed_elements) == 0 and
                    len(child_context.children) == 0):
                    
                    # Found empty double cut
                    if can_remove_double_cut(egi, context.id):
                        new_egi = apply_transformation(
                            egi, TransformationRule.DOUBLE_CUT_REMOVAL, 
                            outer_cut_id=context.id
                        )
                        print(f"Removed double cut")
                        return new_egi
        
        raise TransformationError("No removable double cut found")
    
    def _find_element_by_text(self, egi: EGI, element_text: str) -> Optional[str]:
        """Find element ID by matching text representation."""
        # Simple text matching - in a full implementation this would be more sophisticated
        
        # Try to match edges by relation name
        for edge in egi.edges:
            if not edge.is_identity and edge.relation_name in element_text:
                # Check if this edge matches the pattern
                try:
                    # Generate the text for this edge and compare
                    try:
                        from egif_generator import EGIFGenerator
                    except ImportError:
                        from .egif_generator import EGIFGenerator
                    generator = EGIFGenerator(egi)
                    edge_text = generator._generate_relation(edge)
                    
                    if edge_text == element_text:
                        return edge.id
                except:
                    pass
        
        # Try to match vertices
        for vertex in egi.vertices:
            if vertex.is_constant and vertex.constant_name in element_text:
                return vertex.id
        
        return None
    
    def undo(self):
        """Undo last transformation."""
        if len(self.history) > 1:
            self.history.pop()  # Remove current state
            self.current_egi = self.history[-1]  # Restore previous state
            print("Undone. Current:", generate_egif(self.current_egi))
        else:
            print("Nothing to undo")
    
    def save_yaml(self, filename: str):
        """Save current EGI to YAML file."""
        if self.current_egi is None:
            print("No EGI loaded")
            return
        
        try:
            # For now, just save the EGIF representation
            # In a full implementation, this would use proper YAML serialization
            egif = generate_egif(self.current_egi)
            with open(filename, 'w') as f:
                f.write(f"# Existential Graph\n")
                f.write(f"egif: {egif}\n")
                f.write(f"vertices: {len(self.current_egi.vertices)}\n")
                f.write(f"edges: {len(self.current_egi.edges)}\n")
                f.write(f"contexts: {len(self.current_egi.contexts)}\n")
            print(f"Saved to {filename}")
        except Exception as e:
            print(f"Failed to save: {e}")
    
    def load_yaml(self, filename: str):
        """Load EGI from YAML file."""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            # Simple YAML parsing - look for egif line
            for line in lines:
                if line.startswith('egif:'):
                    egif = line[5:].strip()
                    self.load_egif(egif)
                    print(f"Loaded from {filename}")
                    return
            
            print("No EGIF found in file")
        except Exception as e:
            print(f"Failed to load: {e}")
    
    def interactive_mode(self):
        """Run interactive CLI mode."""
        print("Existential Graphs CLI (Immutable)")
        print("Type 'help' for commands, 'exit' to quit")
        
        while True:
            try:
                command = input("EG> ").strip()
                
                if not command:
                    continue
                
                if command == 'exit':
                    break
                elif command == 'help':
                    self._show_help()
                elif command == 'show':
                    self.show_current()
                elif command == 'undo':
                    self.undo()
                elif command.startswith('load '):
                    egif = command[5:].strip()
                    self.load_egif(egif)
                elif command.startswith('transform '):
                    markup_egif = command[10:].strip()
                    self.apply_transformation(markup_egif)
                elif command.startswith('save '):
                    filename = command[5:].strip()
                    self.save_yaml(filename)
                elif command.startswith('yaml'):
                    if self.current_egi:
                        # Show structure info
                        print(f"Current EGI structure:")
                        print(f"  Vertices: {len(self.current_egi.vertices)}")
                        print(f"  Edges: {len(self.current_egi.edges)}")
                        print(f"  Contexts: {len(self.current_egi.contexts)}")
                        print(f"  Alphabet relations: {list(self.current_egi.alphabet.relations)}")
                    else:
                        print("No EGI loaded")
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("""
Available commands:
  load <egif>              Load EGIF expression
  show                     Show current EGIF
  transform <markup_egif>  Apply transformation with markup
  undo                     Undo last transformation
  save <filename>          Save to file
  yaml                     Show EGI structure
  help                     Show this help
  exit                     Exit application

Markup syntax:
  ^(relation args)^        Mark relation for erasure
  ^~[[^]]                  Mark double cut for removal

Examples:
  load (man *x) (human x)
  transform ^(man *x)^ (human x)
  show
  undo
        """)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Existential Graphs CLI (Immutable)")
    parser.add_argument('--egif', help='EGIF expression to load')
    parser.add_argument('--transform', help='Apply transformation with markup')
    parser.add_argument('--yaml', help='Load from YAML file')
    
    args = parser.parse_args()
    
    app = EGICLIApplication()
    
    if args.yaml:
        app.load_yaml(args.yaml)
    elif args.egif:
        app.load_egif(args.egif)
        
        if args.transform:
            app.apply_transformation(args.transform)
        
        app.show_current()
    else:
        app.interactive_mode()


if __name__ == "__main__":
    main()

