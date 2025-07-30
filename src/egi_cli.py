"""
Command-line interface for the Existential Graphs application.
Supports markup parsing with "^" notation for transformation rule application.
"""

import argparse
import sys
import re
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

from egif_parser import parse_egif
from egif_generator import generate_egif
from egi_yaml import serialize_egi_to_yaml, deserialize_egi_from_yaml
from egi_transformations import EGITransformer, TransformationRule, TransformationError
from egi_core import EGI, ElementID


class MarkupType(Enum):
    """Types of markup annotations."""
    ERASE = "erase"
    INSERT = "insert"
    ITERATE = "iterate"
    DE_ITERATE = "de_iterate"
    DOUBLE_CUT_ADD = "double_cut_add"
    DOUBLE_CUT_REMOVE = "double_cut_remove"
    ISOLATED_VERTEX_ADD = "isolated_vertex_add"
    ISOLATED_VERTEX_REMOVE = "isolated_vertex_remove"


class MarkupParser:
    """Parses EGIF expressions with markup annotations."""
    
    def __init__(self):
        self.markup_patterns = {
            # Erasure: ^~[[^
            r'\^\~\[\[\^': MarkupType.ERASE,
            # Double cut removal: ^~[[^ ... ]]
            r'\^\~\[\[\^.*?\]\]': MarkupType.DOUBLE_CUT_REMOVE,
            # General markup: ^element^
            r'\^([^^\s]+)\^': MarkupType.ERASE,  # Default to erase for simple markup
        }
    
    def parse_markup(self, marked_egif: str) -> Tuple[str, List[Dict]]:
        """
        Parses marked EGIF and returns clean EGIF plus markup instructions.
        
        Args:
            marked_egif: EGIF expression with markup annotations
            
        Returns:
            Tuple of (clean_egif, markup_instructions)
        """
        clean_egif = marked_egif
        markup_instructions = []
        
        # Handle double cut removal markup: ^~[[^ ... ]]
        double_cut_pattern = r'\^\~\[\[\^(.*?)\]\]'
        matches = list(re.finditer(double_cut_pattern, marked_egif))
        
        for match in reversed(matches):  # Process from right to left
            full_match = match.group(0)
            inner_content = match.group(1).strip()
            
            # Replace with clean double cut
            if inner_content:
                replacement = f"~[ {inner_content} ]"
            else:
                replacement = "~[ ]"
            
            clean_egif = clean_egif[:match.start()] + replacement + clean_egif[match.end():]
            
            markup_instructions.append({
                'type': MarkupType.DOUBLE_CUT_REMOVE,
                'position': match.start(),
                'content': inner_content,
                'rule': TransformationRule.DOUBLE_CUT_REMOVAL
            })
        
        # Handle simple erasure markup: ^(relation ...)^ or ^element^
        # Updated pattern to handle parentheses and spaces
        simple_pattern = r'\^(\([^)]+\)|[^^\s]+)\^'
        matches = list(re.finditer(simple_pattern, clean_egif))
        
        for match in reversed(matches):  # Process from right to left
            full_match = match.group(0)
            element = match.group(1)
            
            # Remove markup, keep element
            clean_egif = clean_egif[:match.start()] + element + clean_egif[match.end():]
            
            markup_instructions.append({
                'type': MarkupType.ERASE,
                'element': element,
                'position': match.start(),
                'rule': TransformationRule.ERASURE
            })
        
        return clean_egif, markup_instructions
    
    def find_element_to_transform(self, egi: EGI, element_description: str) -> Optional[ElementID]:
        """
        Finds the element ID corresponding to the markup description.
        
        Args:
            egi: The EGI instance
            element_description: Description from markup (e.g., "(man *x)" or "man")
            
        Returns:
            ElementID if found, None otherwise
        """
        # Handle relation patterns like "(man *x)"
        if element_description.startswith('(') and element_description.endswith(')'):
            # Extract relation name from pattern
            content = element_description[1:-1].strip()
            parts = content.split()
            if parts:
                relation_name = parts[0]
                
                # Find edge with matching relation name
                for edge_id, edge in egi.edges.items():
                    if edge.relation_name == relation_name:
                        return edge_id
        
        # Try to find edge with exact relation name match
        for edge_id, edge in egi.edges.items():
            if edge.relation_name == element_description:
                return edge_id
        
        # Try to find vertex with matching constant name
        for vertex_id, vertex in egi.vertices.items():
            if vertex.is_constant and vertex.constant_name == element_description:
                return vertex_id
        
        # Try to find cut (for double cut operations)
        if element_description in ["cut", "~"]:
            if egi.cuts:
                return next(iter(egi.cuts.keys()))
        
        return None


class EGICLIApplication:
    """Main CLI application for Existential Graphs."""
    
    def __init__(self):
        self.markup_parser = MarkupParser()
        self.current_egi: Optional[EGI] = None
        self.history: List[EGI] = []
    
    def run(self):
        """Main application loop."""
        print("Existential Graphs CLI Application")
        print("Based on Frithjof Dau's formalism")
        print("Type 'help' for available commands.\n")
        
        while True:
            try:
                command = input("EG> ").strip()
                if not command:
                    continue
                
                if command.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                elif command.lower() == 'help':
                    self.show_help()
                elif command.startswith('load '):
                    self.load_egif(command[5:].strip())
                elif command.startswith('transform '):
                    self.apply_transformation(command[10:].strip())
                elif command.lower() == 'show':
                    self.show_current()
                elif command.lower() == 'yaml':
                    self.show_yaml()
                elif command.lower() == 'undo':
                    self.undo()
                elif command.lower() == 'history':
                    self.show_history()
                elif command.lower() == 'rules':
                    self.show_rules()
                elif command.startswith('save '):
                    self.save_yaml(command[5:].strip())
                elif command.startswith('load_yaml '):
                    self.load_yaml(command[10:].strip())
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def show_help(self):
        """Shows help information."""
        help_text = """
Available commands:

Basic Operations:
  load <egif>           - Load an EGIF expression
  show                  - Show current EGIF
  yaml                  - Show current EGI as YAML
  save <file>           - Save current EGI as YAML file
  load_yaml <file>      - Load EGI from YAML file

Transformations:
  transform <marked_egif> - Apply transformation using markup
  undo                    - Undo last transformation
  history                 - Show transformation history
  rules                   - Show available transformation rules

Markup Syntax:
  ^element^             - Mark element for erasure
  ^~[[^content]]        - Mark double cut for removal
  
Examples:
  load (man *x) (human x)
  transform ^(man *x)^ (human x)    # Erase (man *x)
  transform ^~[[^]]                 # Remove empty double cut
  
Other:
  help                  - Show this help
  exit, quit, q         - Exit application
"""
        print(help_text)
    
    def load_egif(self, egif: str):
        """Loads an EGIF expression."""
        try:
            self.current_egi = parse_egif(egif)
            self.history = [self.current_egi]
            print(f"Loaded: {egif}")
            print(f"Parsed: {len(self.current_egi.vertices)} vertices, {len(self.current_egi.edges)} edges, {len(self.current_egi.cuts)} cuts")
        except Exception as e:
            print(f"Failed to load EGIF: {e}")
    
    def apply_transformation(self, marked_egif: str):
        """Applies transformation based on marked EGIF."""
        if not self.current_egi:
            print("No EGI loaded. Use 'load <egif>' first.")
            return
        
        try:
            # Parse markup
            clean_egif, markup_instructions = self.markup_parser.parse_markup(marked_egif)
            
            if not markup_instructions:
                print("No markup found in expression.")
                return
            
            print(f"Clean EGIF: {clean_egif}")
            print(f"Found {len(markup_instructions)} markup instruction(s)")
            
            # Apply transformations
            transformer = EGITransformer(self.current_egi)
            
            for instruction in markup_instructions:
                print(f"Applying {instruction['type'].value}...")
                
                if instruction['type'] == MarkupType.ERASE:
                    element_id = self.markup_parser.find_element_to_transform(
                        transformer.egi, instruction['element']
                    )
                    if element_id:
                        transformer._apply_erasure(element_id)
                        print(f"Erased element: {instruction['element']}")
                    else:
                        print(f"Element not found: {instruction['element']}")
                
                elif instruction['type'] == MarkupType.DOUBLE_CUT_REMOVE:
                    # Find empty double cut to remove
                    outer_cut_id = self._find_empty_double_cut(transformer.egi)
                    if outer_cut_id:
                        transformer._apply_double_cut_removal(outer_cut_id)
                        print("Removed empty double cut")
                    else:
                        print("No empty double cut found")
            
            # Update current EGI and add to history
            self.current_egi = transformer.egi
            self.history.append(self.current_egi)
            
            # Show result
            result_egif = generate_egif(self.current_egi)
            print(f"Result: {result_egif}")
            
        except Exception as e:
            print(f"Transformation failed: {e}")
    
    def _find_empty_double_cut(self, egi: EGI) -> Optional[ElementID]:
        """Finds an empty double cut for removal."""
        for cut_id, cut in egi.cuts.items():
            if (len(cut.children) == 1 and 
                not cut.enclosed_elements):
                
                inner_cut_id = next(iter(cut.children))
                inner_cut = egi.cuts[inner_cut_id]
                
                if (not inner_cut.enclosed_elements and 
                    not inner_cut.children):
                    return cut_id
        
        return None
    
    def show_current(self):
        """Shows the current EGIF."""
        if not self.current_egi:
            print("No EGI loaded.")
            return
        
        egif = generate_egif(self.current_egi)
        print(f"Current EGIF: {egif}")
        print(f"Structure: {len(self.current_egi.vertices)} vertices, {len(self.current_egi.edges)} edges, {len(self.current_egi.cuts)} cuts")
    
    def show_yaml(self):
        """Shows the current EGI as YAML."""
        if not self.current_egi:
            print("No EGI loaded.")
            return
        
        yaml_str = serialize_egi_to_yaml(self.current_egi)
        print("Current EGI as YAML:")
        print(yaml_str)
    
    def save_yaml(self, filename: str):
        """Saves current EGI as YAML file."""
        if not self.current_egi:
            print("No EGI loaded.")
            return
        
        try:
            yaml_str = serialize_egi_to_yaml(self.current_egi)
            with open(filename, 'w') as f:
                f.write(yaml_str)
            print(f"Saved to {filename}")
        except Exception as e:
            print(f"Failed to save: {e}")
    
    def load_yaml(self, filename: str):
        """Loads EGI from YAML file."""
        try:
            with open(filename, 'r') as f:
                yaml_str = f.read()
            
            self.current_egi = deserialize_egi_from_yaml(yaml_str)
            self.history = [self.current_egi]
            print(f"Loaded from {filename}")
            
            egif = generate_egif(self.current_egi)
            print(f"EGIF: {egif}")
            
        except Exception as e:
            print(f"Failed to load: {e}")
    
    def undo(self):
        """Undoes the last transformation."""
        if len(self.history) <= 1:
            print("Nothing to undo.")
            return
        
        self.history.pop()  # Remove current
        self.current_egi = self.history[-1]  # Restore previous
        
        egif = generate_egif(self.current_egi)
        print(f"Undone. Current: {egif}")
    
    def show_history(self):
        """Shows transformation history."""
        if not self.history:
            print("No history.")
            return
        
        print(f"History ({len(self.history)} states):")
        for i, egi in enumerate(self.history):
            egif = generate_egif(egi)
            marker = " <-- current" if i == len(self.history) - 1 else ""
            print(f"  {i+1}. {egif}{marker}")
    
    def show_rules(self):
        """Shows available transformation rules."""
        rules_text = """
Available Transformation Rules:

1. Erasure (^element^)
   - Remove element from positive context
   - Example: ^(man *x)^ removes the relation

2. Insertion
   - Add element to negative context
   - (Not yet implemented in markup)

3. Iteration
   - Copy vertex from outer to inner context
   - (Not yet implemented in markup)

4. De-iteration
   - Remove copied vertex from inner context
   - (Not yet implemented in markup)

5. Double Cut Addition
   - Add nested empty cuts
   - (Not yet implemented in markup)

6. Double Cut Removal (^~[[^content]])
   - Remove nested empty cuts
   - Example: ^~[[^]] removes empty double cut

7. Isolated Vertex Addition
   - Add isolated vertex
   - (Not yet implemented in markup)

8. Isolated Vertex Removal
   - Remove isolated vertex
   - (Not yet implemented in markup)
"""
        print(rules_text)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Existential Graphs CLI Application')
    parser.add_argument('--egif', help='Initial EGIF expression to load')
    parser.add_argument('--yaml', help='YAML file to load')
    parser.add_argument('--transform', help='Apply transformation with markup')
    
    args = parser.parse_args()
    
    app = EGICLIApplication()
    
    # Handle command line arguments
    if args.yaml:
        app.load_yaml(args.yaml)
    elif args.egif:
        app.load_egif(args.egif)
    
    if args.transform:
        app.apply_transformation(args.transform)
        app.show_current()
    else:
        # Start interactive mode
        app.run()


if __name__ == "__main__":
    main()

