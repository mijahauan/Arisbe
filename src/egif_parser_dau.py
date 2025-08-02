"""
Dau-compliant EGIF parser that builds RelationalGraphWithCuts structures.
Supports isolated vertices, proper syntax validation, and Dau's 6+1 component model.

Key improvements over previous parser:
- Supports isolated vertices (*x, "Socrates") as per Dau's "heavy dot" rule
- Builds proper Dau-compliant structures with area/context distinction
- Comprehensive syntax validation before processing
- Proper handling of generic vs constant vertices
"""

import re
from typing import List, Dict, Set, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut,
    create_empty_graph, create_vertex, create_edge, create_cut,
    ElementID, VertexSequence, RelationName
)


class TokenType(Enum):
    """Token types for EGIF lexical analysis."""
    LPAREN = "LPAREN"           # (
    RPAREN = "RPAREN"           # )
    LBRACKET = "LBRACKET"       # [
    RBRACKET = "RBRACKET"       # ]
    LCUT = "LCUT"               # ~[
    RCUT = "RCUT"               # ]
    DEFINING_VAR = "DEFINING_VAR"  # *x
    BOUND_VAR = "BOUND_VAR"     # x
    CONSTANT = "CONSTANT"       # "Socrates"
    RELATION = "RELATION"       # man, loves, etc.
    WHITESPACE = "WHITESPACE"   # spaces, tabs
    EOF = "EOF"                 # end of input


@dataclass
class Token:
    """Token in EGIF expression."""
    type: TokenType
    value: str
    position: int


class EGIFLexer:
    """Lexical analyzer for EGIF expressions with isolated vertex support."""
    
    def __init__(self, text: str):
        self.text = text
        self.position = 0
        self.tokens = []
        
    def tokenize(self) -> List[Token]:
        """Tokenize EGIF expression."""
        self.tokens = []
        self.position = 0
        
        while self.position < len(self.text):
            self._skip_whitespace()
            
            if self.position >= len(self.text):
                break
                
            char = self.text[self.position]
            
            if char == '(':
                self.tokens.append(Token(TokenType.LPAREN, char, self.position))
                self.position += 1
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, char, self.position))
                self.position += 1
            elif char == '[':
                self.tokens.append(Token(TokenType.LBRACKET, char, self.position))
                self.position += 1
            elif char == ']':
                self.tokens.append(Token(TokenType.RBRACKET, char, self.position))
                self.position += 1
            elif char == '~' and self._peek() == '[':
                self.tokens.append(Token(TokenType.LCUT, '~[', self.position))
                self.position += 2
            elif char == '*':
                var_name = self._read_variable()
                self.tokens.append(Token(TokenType.DEFINING_VAR, var_name, self.position - len(var_name)))
            elif char == '"':
                constant = self._read_constant()
                self.tokens.append(Token(TokenType.CONSTANT, constant, self.position - len(constant)))
            elif char.isalpha():
                identifier = self._read_identifier()
                # Determine if it's a bound variable or relation
                if self._is_bound_variable(identifier):
                    self.tokens.append(Token(TokenType.BOUND_VAR, identifier, self.position - len(identifier)))
                else:
                    self.tokens.append(Token(TokenType.RELATION, identifier, self.position - len(identifier)))
            else:
                raise ValueError(f"Unexpected character '{char}' at position {self.position}")
        
        self.tokens.append(Token(TokenType.EOF, "", self.position))
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1
    
    def _peek(self, offset: int = 1) -> str:
        """Peek at character at offset."""
        pos = self.position + offset
        return self.text[pos] if pos < len(self.text) else ''
    
    def _read_variable(self) -> str:
        """Read variable name after *."""
        start = self.position
        self.position += 1  # Skip *
        
        if self.position >= len(self.text) or not self.text[self.position].isalpha():
            raise ValueError(f"Invalid variable at position {start}")
        
        while self.position < len(self.text) and (self.text[self.position].isalnum() or self.text[self.position] == '_'):
            self.position += 1
        
        return self.text[start:self.position]
    
    def _read_constant(self) -> str:
        """Read quoted constant."""
        start = self.position
        self.position += 1  # Skip opening quote
        
        while self.position < len(self.text) and self.text[self.position] != '"':
            if self.text[self.position] == '\\':
                self.position += 2  # Skip escaped character
            else:
                self.position += 1
        
        if self.position >= len(self.text):
            raise ValueError(f"Unterminated string at position {start}")
        
        self.position += 1  # Skip closing quote
        return self.text[start:self.position]
    
    def _read_identifier(self) -> str:
        """Read identifier (relation name or bound variable)."""
        start = self.position
        
        while (self.position < len(self.text) and 
               (self.text[self.position].isalnum() or self.text[self.position] in '_')):
            self.position += 1
        
        return self.text[start:self.position]
    
    def _is_bound_variable(self, identifier: str) -> bool:
        """Determine if identifier is a bound variable based on context."""
        # Simple heuristic: single lowercase letter is likely a bound variable
        # More sophisticated logic would track defining occurrences
        return len(identifier) == 1 and identifier.islower()


class EGIFSyntaxValidator:
    """Validates EGIF syntax before parsing."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
    
    def validate(self) -> bool:
        """Validate EGIF syntax."""
        try:
            self._validate_eg()
            return True
        except ValueError as e:
            print(f"Syntax error: {e}")
            return False
    
    def _current_token(self) -> Token:
        """Get current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]  # EOF
    
    def _advance(self):
        """Advance to next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
    
    def _validate_eg(self):
        """Validate existential graph."""
        while self._current_token().type != TokenType.EOF:
            self._validate_node()
    
    def _validate_node(self):
        """Validate a node (relation, cut, scroll, or isolated vertex)."""
        token = self._current_token()
        
        if token.type == TokenType.LPAREN:
            self._validate_relation()
        elif token.type == TokenType.LCUT:
            self._validate_cut()
        elif token.type == TokenType.LBRACKET:
            self._validate_scroll()
        elif token.type in [TokenType.DEFINING_VAR, TokenType.BOUND_VAR, TokenType.CONSTANT]:
            self._validate_isolated_vertex()
        else:
            raise ValueError(f"Unexpected token {token.type} at position {token.position}")
    
    def _validate_relation(self):
        """Validate relation syntax."""
        if self._current_token().type != TokenType.LPAREN:
            raise ValueError("Expected '(' for relation")
        self._advance()
        
        if self._current_token().type != TokenType.RELATION:
            raise ValueError("Expected relation name after '('")
        self._advance()
        
        # Validate arguments
        while self._current_token().type in [TokenType.DEFINING_VAR, TokenType.BOUND_VAR, TokenType.CONSTANT]:
            self._advance()
        
        if self._current_token().type != TokenType.RPAREN:
            raise ValueError("Expected ')' to close relation")
        self._advance()
    
    def _validate_cut(self):
        """Validate cut syntax."""
        if self._current_token().type != TokenType.LCUT:
            raise ValueError("Expected '~[' for cut")
        self._advance()
        
        # Validate cut contents
        while self._current_token().type not in [TokenType.RBRACKET, TokenType.EOF]:
            self._validate_node()
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close cut")
        self._advance()
    
    def _validate_scroll(self):
        """Validate scroll (existential quantification) syntax."""
        if self._current_token().type != TokenType.LBRACKET:
            raise ValueError("Expected '[' for scroll")
        self._advance()
        
        # Validate variable list
        while self._current_token().type == TokenType.DEFINING_VAR:
            self._advance()
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close scroll")
        self._advance()
    
    def _validate_isolated_vertex(self):
        """Validate isolated vertex (heavy dot)."""
        token = self._current_token()
        if token.type not in [TokenType.DEFINING_VAR, TokenType.BOUND_VAR, TokenType.CONSTANT]:
            raise ValueError(f"Invalid isolated vertex token: {token.type}")
        self._advance()


class EGIFParser:
    """Parser for EGIF expressions that builds Dau-compliant structures."""
    
    def __init__(self, text: str):
        self.text = text
        self.tokens = []
        self.position = 0
        self.graph = create_empty_graph()
        self.variable_map = {}  # Maps variable names to vertex IDs
        self.defining_labels = set()  # Track defining labels to prevent duplicates
        
    def parse(self) -> RelationalGraphWithCuts:
        """Parse EGIF expression into Dau-compliant graph."""
        # Tokenize
        lexer = EGIFLexer(self.text)
        self.tokens = lexer.tokenize()
        
        # Validate syntax
        validator = EGIFSyntaxValidator(self.tokens)
        if not validator.validate():
            raise ValueError("Invalid EGIF syntax")
        
        # Reset for parsing
        self.position = 0
        self.graph = create_empty_graph()
        self.variable_map = {}
        self.defining_labels = set()
        
        # Parse
        self._parse_eg()
        
        return self.graph
    
    def _current_token(self) -> Token:
        """Get current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]  # EOF
    
    def _advance(self):
        """Advance to next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
    
    def _parse_eg(self):
        """Parse existential graph."""
        while self._current_token().type != TokenType.EOF:
            self._parse_node(self.graph.sheet)
    
    def _parse_node(self, context_id: ElementID):
        """Parse a node in given context."""
        token = self._current_token()
        
        if token.type == TokenType.LPAREN:
            self._parse_relation(context_id)
        elif token.type == TokenType.LCUT:
            self._parse_cut(context_id)
        elif token.type == TokenType.LBRACKET:
            self._parse_scroll(context_id)
        elif token.type in [TokenType.DEFINING_VAR, TokenType.BOUND_VAR, TokenType.CONSTANT]:
            self._parse_isolated_vertex(context_id)
        else:
            raise ValueError(f"Unexpected token {token.type} at position {token.position}")
    
    def _parse_relation(self, context_id: ElementID):
        """Parse relation."""
        if self._current_token().type != TokenType.LPAREN:
            raise ValueError("Expected '(' for relation")
        self._advance()
        
        # Get relation name
        if self._current_token().type != TokenType.RELATION:
            raise ValueError("Expected relation name")
        relation_name = self._current_token().value
        self._advance()
        
        # Parse arguments
        vertex_ids = []
        while self._current_token().type in [TokenType.DEFINING_VAR, TokenType.BOUND_VAR, TokenType.CONSTANT]:
            vertex_id = self._parse_argument(context_id)
            vertex_ids.append(vertex_id)
        
        if self._current_token().type != TokenType.RPAREN:
            raise ValueError("Expected ')' to close relation")
        self._advance()
        
        # Create edge
        edge = create_edge()
        self.graph = self.graph.with_edge(edge, tuple(vertex_ids), relation_name, context_id)
    
    def _parse_argument(self, context_id: ElementID) -> ElementID:
        """Parse relation argument and return vertex ID."""
        token = self._current_token()
        
        if token.type == TokenType.DEFINING_VAR:
            # Defining variable *x
            var_name = token.value[1:]  # Remove *
            if var_name in self.defining_labels:
                raise ValueError(f"Duplicate defining label *{var_name}")
            
            self.defining_labels.add(var_name)
            vertex = create_vertex(label=None, is_generic=True)
            self.graph = self.graph.with_vertex(vertex)
            self.variable_map[var_name] = vertex.id
            self._advance()
            return vertex.id
            
        elif token.type == TokenType.BOUND_VAR:
            # Bound variable x
            var_name = token.value
            if var_name not in self.variable_map:
                raise ValueError(f"Undefined variable {var_name}")
            self._advance()
            return self.variable_map[var_name]
            
        elif token.type == TokenType.CONSTANT:
            # Constant "Socrates"
            constant_value = token.value[1:-1]  # Remove quotes
            vertex = create_vertex(label=constant_value, is_generic=False)
            self.graph = self.graph.with_vertex(vertex)
            self._advance()
            return vertex.id
            
        else:
            raise ValueError(f"Invalid argument token: {token.type}")
    
    def _parse_cut(self, context_id: ElementID):
        """Parse cut (negative context)."""
        if self._current_token().type != TokenType.LCUT:
            raise ValueError("Expected '~[' for cut")
        self._advance()
        
        # Create cut
        cut = create_cut()
        self.graph = self.graph.with_cut(cut, context_id)
        
        # Parse cut contents
        while self._current_token().type not in [TokenType.RBRACKET, TokenType.EOF]:
            self._parse_node(cut.id)
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close cut")
        self._advance()
    
    def _parse_scroll(self, context_id: ElementID):
        """Parse scroll (existential quantification)."""
        if self._current_token().type != TokenType.LBRACKET:
            raise ValueError("Expected '[' for scroll")
        self._advance()
        
        # Parse variable declarations
        scroll_vars = []
        while self._current_token().type == TokenType.DEFINING_VAR:
            var_name = self._current_token().value[1:]  # Remove *
            if var_name in self.defining_labels:
                raise ValueError(f"Duplicate defining label *{var_name}")
            
            self.defining_labels.add(var_name)
            vertex = create_vertex(label=None, is_generic=True)
            self.graph = self.graph.with_vertex(vertex)
            self.variable_map[var_name] = vertex.id
            scroll_vars.append(vertex.id)
            self._advance()
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close scroll")
        self._advance()
        
        # Note: In this implementation, scroll variables are just added to the context
        # More sophisticated handling would create explicit quantification structures
    
    def _parse_isolated_vertex(self, context_id: ElementID):
        """Parse isolated vertex (heavy dot)."""
        token = self._current_token()
        
        if token.type == TokenType.DEFINING_VAR:
            # Isolated defining variable *x
            var_name = token.value[1:]  # Remove *
            if var_name in self.defining_labels:
                raise ValueError(f"Duplicate defining label *{var_name}")
            
            self.defining_labels.add(var_name)
            vertex = create_vertex(label=None, is_generic=True)
            self.graph = self.graph.with_vertex_in_context(vertex, context_id)
            self.variable_map[var_name] = vertex.id
            
        elif token.type == TokenType.BOUND_VAR:
            # Isolated bound variable x
            var_name = token.value
            if var_name not in self.variable_map:
                raise ValueError(f"Undefined variable {var_name}")
            # Note: This creates a reference to existing vertex, not a new one
            
        elif token.type == TokenType.CONSTANT:
            # Isolated constant "Socrates"
            constant_value = token.value[1:-1]  # Remove quotes
            vertex = create_vertex(label=constant_value, is_generic=False)
            self.graph = self.graph.with_vertex_in_context(vertex, context_id)
            
        else:
            raise ValueError(f"Invalid isolated vertex token: {token.type}")
        
        self._advance()


def parse_egif(text: str) -> RelationalGraphWithCuts:
    """Parse EGIF expression into Dau-compliant graph."""
    parser = EGIFParser(text)
    return parser.parse()


if __name__ == "__main__":
    # Test the Dau-compliant parser
    print("=== Testing Dau-Compliant EGIF Parser ===")
    
    test_cases = [
        # Basic relation
        "(man *x)",
        
        # Isolated vertices (heavy dots)
        "*x",
        '"Socrates"',
        
        # Mixed
        "(man *x) *y",
        
        # Constants and variables
        '(loves "Socrates" *x)',
        
        # Simple cut
        "~[ (mortal *x) ]",
        
        # Nested cuts (testing area/context distinction)
        "~[ (man *x) ~[ (mortal x) ] ]",
        
        # Scroll
        "[*x] (man x)",
        
        # Complex example
        '(human "Socrates") ~[ (mortal "Socrates") ] *x',
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Testing: {test_case}")
            graph = parse_egif(test_case)
            
            print(f"   ✓ Parsed successfully")
            print(f"   - Vertices: {len(graph.V)}")
            print(f"   - Edges: {len(graph.E)}")
            print(f"   - Cuts: {len(graph.Cut)}")
            print(f"   - Isolated vertices: {len(graph.get_isolated_vertices())}")
            print(f"   - Has dominating nodes: {graph.has_dominating_nodes()}")
            
            # Test area vs context
            sheet_area = len(graph.get_area(graph.sheet))
            sheet_context = len(graph.get_full_context(graph.sheet))
            print(f"   - Sheet area: {sheet_area}, context: {sheet_context}")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print("\n=== Dau-Compliant Parser Test Complete ===")

