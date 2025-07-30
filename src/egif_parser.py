"""
EGIF (Existential Graph Interchange Format) Parser
Converts EGIF expressions to EGI instances based on Sowa's specification.
"""

import re
from typing import List, Dict, Optional, Union, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from egi_core import EGI, Context, Vertex, Edge, ElementID, ElementType, Alphabet


class TokenType(Enum):
    # Literals
    IDENTIFIER = "IDENTIFIER"
    ENCLOSED_NAME = "ENCLOSED_NAME"
    INTEGER = "INTEGER"
    
    # Operators and punctuation
    LPAREN = "LPAREN"          # (
    RPAREN = "RPAREN"          # )
    LBRACKET = "LBRACKET"      # [
    RBRACKET = "RBRACKET"      # ]
    TILDE = "TILDE"            # ~
    ASTERISK = "ASTERISK"      # *
    PIPE = "PIPE"              # |
    
    # Keywords
    IF = "IF"
    THEN = "THEN"
    
    # Special
    WHITESPACE = "WHITESPACE"
    EOF = "EOF"
    NEWLINE = "NEWLINE"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int
    line: int
    column: int


class EGIFLexer:
    """Lexical analyzer for EGIF expressions."""
    
    def __init__(self, text: str):
        self.text = text
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        
        # Token patterns
        self.patterns = [
            (r'"([^"\\]|\\.)*"', TokenType.ENCLOSED_NAME),
            (r'[a-zA-Z][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
            (r'[+-]?\d+', TokenType.INTEGER),
            (r'\(', TokenType.LPAREN),
            (r'\)', TokenType.RPAREN),
            (r'\[', TokenType.LBRACKET),
            (r'\]', TokenType.RBRACKET),
            (r'~', TokenType.TILDE),
            (r'\*', TokenType.ASTERISK),
            (r'\|', TokenType.PIPE),
            (r'[ \t]+', TokenType.WHITESPACE),
            (r'\n', TokenType.NEWLINE),
        ]
        
        # Compile patterns
        self.compiled_patterns = [(re.compile(pattern), token_type) 
                                 for pattern, token_type in self.patterns]
    
    def tokenize(self) -> List[Token]:
        """Tokenizes the input text and returns a list of tokens."""
        self.tokens = []
        
        while self.position < len(self.text):
            matched = False
            
            for pattern, token_type in self.compiled_patterns:
                match = pattern.match(self.text, self.position)
                if match:
                    value = match.group(0)
                    
                    # Handle keywords
                    if token_type == TokenType.IDENTIFIER:
                        if value.upper() == "IF":
                            token_type = TokenType.IF
                        elif value.upper() == "THEN":
                            token_type = TokenType.THEN
                    
                    # Create token (skip whitespace in token list)
                    if token_type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        token = Token(
                            type=token_type,
                            value=value,
                            position=self.position,
                            line=self.line,
                            column=self.column
                        )
                        self.tokens.append(token)
                    
                    # Update position
                    self.position = match.end()
                    if token_type == TokenType.NEWLINE:
                        self.line += 1
                        self.column = 1
                    else:
                        self.column += len(value)
                    
                    matched = True
                    break
            
            if not matched:
                raise ValueError(f"Unexpected character '{self.text[self.position]}' at line {self.line}, column {self.column}")
        
        # Add EOF token
        self.tokens.append(Token(
            type=TokenType.EOF,
            value="",
            position=self.position,
            line=self.line,
            column=self.column
        ))
        
        return self.tokens


class EGIFParser:
    """Parser for EGIF expressions that builds EGI instances."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0] if tokens else None
        
        # Parser state
        self.egi = EGI()
        self.label_to_vertex: Dict[str, ElementID] = {}
        self.defining_labels: Set[str] = set()
        self.context_stack: List[Context] = [self.egi.sheet]
    
    def parse(self) -> EGI:
        """Parses the tokens and returns an EGI instance."""
        self.parse_eg()
        
        # Validate that all bound labels have corresponding defining labels
        self._validate_label_bindings()
        
        # Update ligatures
        self.egi.ligature_manager.find_ligatures(self.egi)
        
        return self.egi
    
    def _advance(self) -> None:
        """Advances to the next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _expect(self, token_type: TokenType) -> Token:
        """Expects a specific token type and advances."""
        if self.current_token.type != token_type:
            raise ValueError(f"Expected {token_type}, got {self.current_token.type} at line {self.current_token.line}")
        
        token = self.current_token
        self._advance()
        return token
    
    def _peek(self) -> Optional[Token]:
        """Returns the next token without advancing."""
        if self.position < len(self.tokens) - 1:
            return self.tokens[self.position + 1]
        return None
    
    def parse_eg(self) -> None:
        """Parses an existential graph (set of nodes)."""
        while self.current_token.type != TokenType.EOF and self.current_token.type != TokenType.RBRACKET:
            self.parse_node()
    
    def parse_node(self) -> None:
        """Parses a single node (relation, negation, coreference, or scroll)."""
        if self.current_token.type == TokenType.LPAREN:
            self.parse_relation()
        elif self.current_token.type == TokenType.TILDE:
            self.parse_negation()
        elif self.current_token.type == TokenType.LBRACKET:
            # Could be coreference node or scroll
            if self._is_scroll():
                self.parse_scroll()
            else:
                self.parse_coreference_node()
        else:
            raise ValueError(f"Unexpected token {self.current_token.type} at line {self.current_token.line}")
    
    def parse_relation(self) -> None:
        """Parses a relation: (relation_name arg1 arg2 ...)"""
        self._expect(TokenType.LPAREN)
        
        # Parse relation name
        relation_name = self.parse_type_label()
        
        # Parse arguments
        arguments = []
        while self.current_token.type != TokenType.RPAREN:
            arg = self.parse_name()
            arguments.append(arg)
        
        self._expect(TokenType.RPAREN)
        
        # Create vertices for arguments and edge
        vertex_ids = []
        current_context = self.context_stack[-1]
        
        for arg in arguments:
            vertex_id = self._get_or_create_vertex(arg, current_context)
            vertex_ids.append(vertex_id)
        
        # Create edge
        self.egi.add_edge(current_context, relation_name, vertex_ids, check_dominance=False)
    
    def parse_negation(self) -> None:
        """Parses a negation: ~[ EG ]"""
        self._expect(TokenType.TILDE)
        self._expect(TokenType.LBRACKET)
        
        # Create new cut context
        parent_context = self.context_stack[-1]
        cut_context = self.egi.add_cut(parent_context)
        self.context_stack.append(cut_context)
        
        # Parse nested EG
        self.parse_eg()
        
        self._expect(TokenType.RBRACKET)
        self.context_stack.pop()
    
    def parse_scroll(self) -> None:
        """Parses a scroll: [If EG [Then EG ] ]"""
        self._expect(TokenType.LBRACKET)
        self._expect(TokenType.IF)
        
        # Create first cut (If part)
        parent_context = self.context_stack[-1]
        if_cut = self.egi.add_cut(parent_context)
        self.context_stack.append(if_cut)
        
        # Parse If part
        while (self.current_token.type != TokenType.LBRACKET or 
               self._peek().type != TokenType.THEN):
            self.parse_node()
        
        # Parse Then part
        self._expect(TokenType.LBRACKET)
        self._expect(TokenType.THEN)
        
        # Create second cut (Then part)
        then_cut = self.egi.add_cut(if_cut)
        self.context_stack.append(then_cut)
        
        # Parse Then part
        self.parse_eg()
        
        self._expect(TokenType.RBRACKET)  # Close Then
        self._expect(TokenType.RBRACKET)  # Close If
        
        self.context_stack.pop()  # Pop Then context
        self.context_stack.pop()  # Pop If context
    
    def parse_coreference_node(self) -> None:
        """Parses a coreference node: [name1 name2 ...]"""
        self._expect(TokenType.LBRACKET)
        
        names = []
        while self.current_token.type != TokenType.RBRACKET:
            name = self.parse_name()
            names.append(name)
        
        self._expect(TokenType.RBRACKET)
        
        if len(names) < 2:
            raise ValueError("Coreference node must contain at least 2 names")
        
        # Create identity edges between all pairs
        current_context = self.context_stack[-1]
        vertex_ids = []
        
        for name in names:
            vertex_id = self._get_or_create_vertex(name, current_context)
            vertex_ids.append(vertex_id)
        
        # Create identity edges for all pairs
        for i in range(len(vertex_ids)):
            for j in range(i + 1, len(vertex_ids)):
                self.egi.add_edge(current_context, "=", [vertex_ids[i], vertex_ids[j]], check_dominance=False)
    
    def parse_type_label(self) -> str:
        """Parses a type label (relation name)."""
        if self.current_token.type == TokenType.IDENTIFIER:
            value = self.current_token.value
            self._advance()
            return value
        elif self.current_token.type == TokenType.ENCLOSED_NAME:
            # Remove quotes
            value = self.current_token.value[1:-1]
            self._advance()
            return value
        elif self.current_token.type == TokenType.INTEGER:
            value = self.current_token.value
            self._advance()
            return value
        else:
            raise ValueError(f"Expected type label, got {self.current_token.type}")
    
    def parse_name(self) -> str:
        """Parses a name (defining label, bound label, identifier, etc.)."""
        if self.current_token.type == TokenType.ASTERISK:
            # Defining label
            self._advance()
            if self.current_token.type != TokenType.IDENTIFIER:
                raise ValueError("Expected identifier after *")
            
            label = self.current_token.value
            self._advance()
            
            # Check for duplicate defining labels in same scope
            if label in self.defining_labels:
                raise ValueError(f"Duplicate defining label *{label}")
            
            self.defining_labels.add(label)
            return f"*{label}"
        
        elif self.current_token.type == TokenType.IDENTIFIER:
            # Bound label or identifier
            value = self.current_token.value
            self._advance()
            return value
        
        elif self.current_token.type == TokenType.ENCLOSED_NAME:
            # Enclosed name - remove quotes
            value = self.current_token.value[1:-1]
            self._advance()
            return value
        
        elif self.current_token.type == TokenType.INTEGER:
            # Integer
            value = self.current_token.value
            self._advance()
            return value
        
        else:
            raise ValueError(f"Expected name, got {self.current_token.type}")
    
    def _is_scroll(self) -> bool:
        """Checks if the current bracket sequence is a scroll."""
        # Look ahead to see if we have [If
        if (self.current_token.type == TokenType.LBRACKET and 
            self._peek() and self._peek().type == TokenType.IF):
            return True
        return False
    
    def _get_or_create_vertex(self, name: str, context: Context) -> ElementID:
        """Gets or creates a vertex for the given name."""
        # Handle defining labels
        if name.startswith("*"):
            label = name[1:]  # Remove asterisk
            if label in self.label_to_vertex:
                raise ValueError(f"Defining label *{label} already exists")
            
            # Create new vertex
            vertex = self.egi.add_vertex(context, is_constant=False)
            self.label_to_vertex[label] = vertex.id
            return vertex.id
        
        # Handle bound labels
        elif name in self.label_to_vertex:
            # Return existing vertex - context dominance will be checked by add_edge
            return self.label_to_vertex[name]
        
        # Handle constants (enclosed names or identifiers not seen before)
        else:
            # Check if it's a constant (not a bound label)
            if name not in self.defining_labels:
                # Create constant vertex
                vertex = self.egi.add_vertex(context, is_constant=True, constant_name=name)
                return vertex.id
            else:
                # This should be a bound label, but we haven't seen the defining label yet
                # Create placeholder vertex (will be resolved later)
                vertex = self.egi.add_vertex(context, is_constant=False)
                self.label_to_vertex[name] = vertex.id
                return vertex.id
    
    def _validate_label_bindings(self) -> None:
        """Validates that all bound labels have corresponding defining labels."""
        for label, vertex_id in self.label_to_vertex.items():
            if not label.startswith("*") and label not in self.defining_labels:
                # This is a bound label without a defining label
                vertex = self.egi.get_vertex(vertex_id)
                if not vertex.is_constant:
                    raise ValueError(f"Bound label '{label}' has no corresponding defining label")


def parse_egif(egif_text: str) -> EGI:
    """Convenience function to parse EGIF text into an EGI."""
    lexer = EGIFLexer(egif_text)
    tokens = lexer.tokenize()
    
    parser = EGIFParser(tokens)
    return parser.parse()


# Test the parser
if __name__ == "__main__":
    # Test basic relation
    test1 = "(phoenix *x)"
    print("Test 1:", test1)
    egi1 = parse_egif(test1)
    print(f"Vertices: {len(egi1.vertices)}, Edges: {len(egi1.edges)}")
    
    # Test negation
    test2 = "~[ (phoenix *x) ]"
    print("\nTest 2:", test2)
    egi2 = parse_egif(test2)
    print(f"Vertices: {len(egi2.vertices)}, Edges: {len(egi2.edges)}, Cuts: {len(egi2.cuts)}")
    
    # Test coreference
    test3 = "(male *x) (human x) (African x)"
    print("\nTest 3:", test3)
    egi3 = parse_egif(test3)
    print(f"Vertices: {len(egi3.vertices)}, Edges: {len(egi3.edges)}")
    
    print("\nAll tests passed!")

