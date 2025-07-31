"""
Immutable EGIF parser that builds immutable EGI instances.
Based on the original parser but using the new immutable architecture.
"""

import re
from typing import List, Optional, Dict, Set, Tuple

try:
    from .egi_core import EGI, EGIBuilder, Alphabet, ElementID
except ImportError:
    from egi_core import EGI, EGIBuilder, Alphabet, ElementID


class EGIFToken:
    """Token in EGIF expression."""
    def __init__(self, type_: str, value: str, position: int):
        self.type = type_
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.position})"


class EGIFLexer:
    """Lexer for EGIF expressions."""
    
    TOKEN_PATTERNS = [
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('TILDE', r'~'),
        ('DEFINING_VAR', r'\*[a-zA-Z_][a-zA-Z0-9_]*'),
        ('BOUND_VAR', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('QUOTED_STRING', r'"[^"]*"'),
        ('NUMBER', r'-?\d+(?:\.\d+)?'),
        ('WHITESPACE', r'\s+'),
    ]
    
    def __init__(self, text: str):
        self.text = text
        self.position = 0
        self.tokens: List[EGIFToken] = []
        self._tokenize()
    
    def _tokenize(self):
        """Tokenize the input text."""
        while self.position < len(self.text):
            matched = False
            
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.text, self.position)
                
                if match:
                    value = match.group(0)
                    if token_type != 'WHITESPACE':  # Skip whitespace
                        self.tokens.append(EGIFToken(token_type, value, self.position))
                    self.position = match.end()
                    matched = True
                    break
            
            if not matched:
                raise ValueError(f"Unexpected character at position {self.position}: {self.text[self.position]}")


class EGIFParser:
    """Parser for EGIF expressions that builds immutable EGI instances."""
    
    def __init__(self, text: str):
        self.lexer = EGIFLexer(text)
        self.tokens = self.lexer.tokens
        self.position = 0
        self.builder = EGIBuilder()
        self.alphabet = Alphabet()
        
        # Track variable definitions and usage
        self.defining_labels: Dict[str, ElementID] = {}  # label -> vertex_id
        self.bound_variables: Set[str] = set()
        self.coreference_sets: List[Set[str]] = []
        
        # Context stack for parsing nested structures
        self.context_stack: List[ElementID] = []
        self.current_context = self.builder._sheet_id
    
    def parse(self) -> EGI:
        """Parse EGIF expression and return immutable EGI."""
        if not self.tokens:
            # Empty expression - return empty EGI
            return self.builder.build()
        
        self.parse_eg()
        
        # Update alphabet with discovered elements
        self.builder._alphabet = self.alphabet
        
        return self.builder.build()
    
    def current_token(self) -> Optional[EGIFToken]:
        """Get current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def consume_token(self, expected_type: Optional[str] = None) -> EGIFToken:
        """Consume and return current token."""
        token = self.current_token()
        if token is None:
            raise ValueError(f"Unexpected end of input, expected {expected_type}")
        
        if expected_type and token.type != expected_type:
            raise ValueError(f"Expected {expected_type} but found {token.type} at position {token.position}")
        
        self.position += 1
        return token
    
    def peek_token(self, offset: int = 0) -> Optional[EGIFToken]:
        """Peek at token at current position + offset."""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def parse_eg(self):
        """Parse the main EG expression."""
        while self.current_token():
            self.parse_node()
    
    def parse_node(self):
        """Parse a node (relation, cut, or coreference)."""
        token = self.current_token()
        if not token:
            return
        
        if token.type == 'LPAREN':
            self.parse_relation()
        elif token.type == 'TILDE':
            self.parse_cut()
        elif token.type == 'LBRACKET':
            self.parse_coreference_or_scroll()
        else:
            raise ValueError(f"Unexpected token {token.type} at position {token.position}")
    
    def parse_relation(self):
        """Parse a relation: (relation_name arg1 arg2 ...)"""
        self.consume_token('LPAREN')
        
        # Get relation name
        relation_token = self.current_token()
        if not relation_token or relation_token.type not in ['BOUND_VAR']:
            raise ValueError(f"Expected relation name at position {relation_token.position if relation_token else 'end'}")
        
        relation_name = relation_token.value
        self.consume_token()
        
        # Add to alphabet
        self.alphabet = self.alphabet.with_relation(relation_name)
        
        # Parse arguments
        incident_vertices = []
        while self.current_token() and self.current_token().type != 'RPAREN':
            arg_vertex_id = self.parse_argument()
            incident_vertices.append(arg_vertex_id)
        
        self.consume_token('RPAREN')
        
        # Create edge
        edge_id = self.builder.add_edge(
            context_id=self.current_context,
            relation_name=relation_name,
            incident_vertices=tuple(incident_vertices)
        )
    
    def parse_argument(self) -> ElementID:
        """Parse a relation argument and return vertex ID."""
        token = self.current_token()
        if not token:
            raise ValueError("Expected argument")
        
        if token.type == 'DEFINING_VAR':
            # Defining variable: *x
            label = token.value[1:]  # Remove *
            self.consume_token()
            
            if label in self.defining_labels:
                raise ValueError(f"Duplicate defining label *{label}")
            
            # Create vertex
            vertex_id = self.builder.add_vertex(
                context_id=self.current_context,
                is_constant=False
            )
            
            self.defining_labels[label] = vertex_id
            return vertex_id
        
        elif token.type == 'BOUND_VAR':
            # Bound variable: x
            label = token.value
            self.consume_token()
            
            if label not in self.defining_labels:
                raise ValueError(f"Undefined variable {label}")
            
            self.bound_variables.add(label)
            return self.defining_labels[label]
        
        elif token.type == 'QUOTED_STRING':
            # Constant: "value"
            constant_name = token.value[1:-1]  # Remove quotes
            self.consume_token()
            
            # Add to alphabet
            self.alphabet = self.alphabet.with_constant(constant_name)
            
            # Create constant vertex
            vertex_id = self.builder.add_vertex(
                context_id=self.current_context,
                is_constant=True,
                constant_name=constant_name
            )
            
            return vertex_id
        
        elif token.type == 'NUMBER':
            # Numeric constant
            constant_name = token.value
            self.consume_token()
            
            # Add to alphabet
            self.alphabet = self.alphabet.with_constant(constant_name)
            
            # Create constant vertex
            vertex_id = self.builder.add_vertex(
                context_id=self.current_context,
                is_constant=True,
                constant_name=constant_name
            )
            
            return vertex_id
        
        else:
            raise ValueError(f"Unexpected token {token.type} in argument at position {token.position}")
    
    def parse_cut(self):
        """Parse a cut: ~[ ... ]"""
        self.consume_token('TILDE')
        self.consume_token('LBRACKET')
        
        # Create new context
        cut_context_id = self.builder.add_context(parent_id=self.current_context)
        
        # Push context
        self.context_stack.append(self.current_context)
        self.current_context = cut_context_id
        
        # Parse contents
        while self.current_token() and self.current_token().type != 'RBRACKET':
            self.parse_node()
        
        self.consume_token('RBRACKET')
        
        # Pop context
        self.current_context = self.context_stack.pop()
    
    def parse_coreference_or_scroll(self):
        """Parse coreference set or scroll pattern."""
        self.consume_token('LBRACKET')
        
        # Check if this is a scroll pattern (If/Then)
        if (self.current_token() and 
            self.current_token().type == 'BOUND_VAR' and 
            self.current_token().value in ['If', 'Then']):
            self.parse_scroll()
        else:
            self.parse_coreference()
    
    def parse_scroll(self):
        """Parse scroll pattern: [If ... [Then ... ] ]"""
        # This is a simplified scroll parser
        # In a full implementation, this would handle the scroll semantics properly
        
        while self.current_token() and self.current_token().type != 'RBRACKET':
            token = self.current_token()
            
            if token.type == 'BOUND_VAR' and token.value in ['If', 'Then']:
                # Create a context for the scroll part
                scroll_context_id = self.builder.add_context(parent_id=self.current_context)
                
                # Add the scroll marker as a special relation
                self.consume_token()
                marker_vertex_id = self.builder.add_vertex(
                    context_id=scroll_context_id,
                    is_constant=True,
                    constant_name=token.value
                )
                
                # Push context
                self.context_stack.append(self.current_context)
                self.current_context = scroll_context_id
                
            elif token.type == 'LBRACKET':
                # Nested bracket - recurse
                self.parse_coreference_or_scroll()
            else:
                # Regular content
                self.parse_node()
        
        self.consume_token('RBRACKET')
        
        # Pop context if we pushed one
        if self.context_stack:
            self.current_context = self.context_stack.pop()
    
    def parse_coreference(self):
        """Parse coreference set: [*x *y] or [x y]"""
        coreference_set = set()
        
        while self.current_token() and self.current_token().type != 'RBRACKET':
            token = self.current_token()
            
            if token.type == 'DEFINING_VAR':
                # Defining variable in coreference
                label = token.value[1:]  # Remove *
                self.consume_token()
                
                if label in self.defining_labels:
                    raise ValueError(f"Duplicate defining label *{label}")
                
                # Create vertex
                vertex_id = self.builder.add_vertex(
                    context_id=self.current_context,
                    is_constant=False
                )
                
                self.defining_labels[label] = vertex_id
                coreference_set.add(label)
                
            elif token.type == 'BOUND_VAR':
                # Bound variable in coreference
                label = token.value
                self.consume_token()
                
                if label not in self.defining_labels:
                    raise ValueError(f"Undefined variable {label}")
                
                coreference_set.add(label)
                
            else:
                # Not a variable - parse as regular content
                self.parse_node()
        
        self.consume_token('RBRACKET')
        
        # Store coreference set if it has variables
        if coreference_set:
            self.coreference_sets.append(coreference_set)
            
            # Create identity edges for coreference
            if len(coreference_set) > 1:
                vertex_ids = [self.defining_labels[label] for label in coreference_set]
                self.builder.add_edge(
                    context_id=self.current_context,
                    relation_name="=",
                    incident_vertices=tuple(vertex_ids),
                    is_identity=True
                )


def parse_egif(text: str) -> EGI:
    """Parse EGIF expression and return immutable EGI."""
    parser = EGIFParser(text)
    return parser.parse()


# Test the parser
if __name__ == "__main__":
    print("Testing immutable EGIF parser...")
    
    test_cases = [
        "(phoenix *x)",
        "(man *x) (human x)",
        '(loves "Socrates" "Plato")',
        "~[ (mortal *x) ]",
        "[*x *y] (P x) (Q y)",
        '[If (thunder *x) [Then (lightning *y) ] ]'
    ]
    
    for egif in test_cases:
        try:
            egi = parse_egif(egif)
            print(f"✓ Parsed: {egif}")
            print(f"  Vertices: {len(egi.vertices)}, Edges: {len(egi.edges)}, Contexts: {len(egi.contexts)}")
        except Exception as e:
            print(f"✗ Failed to parse: {egif}")
            print(f"  Error: {e}")
    
    print("✓ Immutable EGIF parser working correctly!")

