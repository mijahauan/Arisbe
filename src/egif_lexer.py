"""
EGIF Lexer - Educational-First Design

This module provides lexical analysis for Existential Graph Interchange Format (EGIF)
with comprehensive tokenization designed to support educational use and provide
detailed feedback about the relationship between EGIF syntax and existential graphs.

The lexer prioritizes educational value over performance, providing detailed token
information that supports syntax highlighting, error reporting, and educational
feedback about how EGIF constructs map to graphical elements.

Author: Manus AI
Date: January 2025
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid


class EGIFTokenType(Enum):
    """Token types for EGIF lexical analysis.
    
    Each token type corresponds to a specific syntactic element in EGIF
    and maps to corresponding elements in existential graphs.
    """
    # Basic structural tokens
    LPAREN = "LPAREN"           # ( - Start of relation or function
    RPAREN = "RPAREN"           # ) - End of relation or function
    LBRACKET = "LBRACKET"       # [ - Start of coreference node or scroll
    RBRACKET = "RBRACKET"       # ] - End of coreference node or scroll
    TILDE = "TILDE"             # ~ - Negation (cut in graphical form)
    PIPE = "PIPE"               # | - Function separator
    ASTERISK = "ASTERISK"       # * - Defining label marker
    
    # Content tokens
    IDENTIFIER = "IDENTIFIER"    # Variable names, relation names
    QUOTED_NAME = "QUOTED_NAME"  # "Enclosed names with spaces"
    INTEGER = "INTEGER"          # Numeric constants
    
    # Special keywords
    IF = "IF"                   # If keyword for scroll notation
    THEN = "THEN"               # Then keyword for scroll notation
    IFF = "IFF"                 # Iff keyword for biconditional scroll
    UNLESS = "UNLESS"           # Unless keyword for negative conditional
    FORALL = "FORALL"           # Universal quantifier
    EXISTS = "EXISTS"           # Existential quantifier
    LAMBDA = "LAMBDA"           # Lambda abstraction
    
    # Advanced operators (Phase 2)
    ARROW = "ARROW"             # -> Function result indicator
    EQUALS = "EQUALS"           # = Equivalence in coreference
    
    # Whitespace and comments (preserved for educational feedback)
    WHITESPACE = "WHITESPACE"   # Spaces, tabs, newlines
    COMMENT = "COMMENT"         # Comments (if supported)
    
    # Special tokens
    EOF = "EOF"                 # End of input
    ERROR = "ERROR"             # Lexical error token


@dataclass
class EGIFToken:
    """A token in EGIF source code with educational metadata.
    
    Each token includes detailed position information and educational
    hints that can be used for syntax highlighting, error reporting,
    and explaining the relationship to existential graphs.
    """
    type: EGIFTokenType
    value: str
    line: int
    column: int
    position: int
    length: int
    
    # Educational metadata
    description: str = ""       # Human-readable description of token purpose
    eg_mapping: str = ""        # How this token maps to graphical EG elements
    context_hint: str = ""      # Contextual information for educational feedback
    
    def __str__(self) -> str:
        return f"{self.type.value}({self.value}) at {self.line}:{self.column}"
    
    def educational_description(self) -> str:
        """Return educational description of this token."""
        if self.description:
            return f"{self.description}"
        return f"{self.type.value} token: {self.value}"


@dataclass
class EGIFLexError:
    """A lexical error with educational feedback."""
    message: str
    line: int
    column: int
    position: int
    length: int
    error_type: str
    suggestions: List[str]
    educational_note: str = ""  # Educational explanation of the error


class EGIFLexer:
    """
    Lexical analyzer for EGIF with educational-first design.
    
    This lexer is designed to support educational use by providing:
    - Detailed token information with educational metadata
    - Clear error messages that explain EGIF syntax rules
    - Mapping information between EGIF tokens and EG graphical elements
    - Support for syntax highlighting and interactive editing
    """
    
    # Token patterns with educational descriptions
    TOKEN_PATTERNS = [
        # Comments (if we decide to support them)
        (EGIFTokenType.COMMENT, r'/\*.*?\*/', "Block comment"),
        (EGIFTokenType.COMMENT, r'//.*?$', "Line comment"),
        
        # Whitespace (preserved for formatting)
        (EGIFTokenType.WHITESPACE, r'\s+', "Whitespace"),
        
        # Structural tokens
        (EGIFTokenType.LPAREN, r'\(', "Left parenthesis - starts relation or function"),
        (EGIFTokenType.RPAREN, r'\)', "Right parenthesis - ends relation or function"),
        (EGIFTokenType.LBRACKET, r'\[', "Left bracket - starts coreference node or scroll"),
        (EGIFTokenType.RBRACKET, r'\]', "Right bracket - ends coreference node or scroll"),
        (EGIFTokenType.TILDE, r'~', "Tilde - negation (cut in graphical form)"),
        (EGIFTokenType.PIPE, r'\|', "Pipe - separates function inputs from output"),
        (EGIFTokenType.ASTERISK, r'\*', "Asterisk - marks defining label"),
        
        # Keywords (case-sensitive)
        (EGIFTokenType.IF, r'\bIf\b', "If keyword - starts conditional (scroll)"),
        (EGIFTokenType.THEN, r'\bThen\b', "Then keyword - separates condition from conclusion"),
        
        # Content tokens
        (EGIFTokenType.QUOTED_NAME, r'"([^"\\]|\\.)*"', "Quoted name - allows spaces and special characters"),
        (EGIFTokenType.INTEGER, r'-?\d+', "Integer constant"),
        (EGIFTokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_:.-]*', "Identifier - variable or relation name"),
    ]
    
    # Educational mappings from tokens to EG concepts
    EG_MAPPINGS = {
        EGIFTokenType.LPAREN: "Start of atomic graph (relation with pegs)",
        EGIFTokenType.RPAREN: "End of atomic graph",
        EGIFTokenType.LBRACKET: "Start of coreference (ligature) or scroll (double cut)",
        EGIFTokenType.RBRACKET: "End of coreference or scroll",
        EGIFTokenType.TILDE: "Cut (oval enclosure) for negation",
        EGIFTokenType.ASTERISK: "Beginning of line of identity (existential quantification)",
        EGIFTokenType.IDENTIFIER: "Relation name or line of identity label",
        EGIFTokenType.IF: "Start of scroll pattern (double cut for implication)",
        EGIFTokenType.THEN: "Inner cut of scroll pattern",
    }
    
    def __init__(self, source: str, educational_mode: bool = True):
        """
        Initialize the EGIF lexer.
        
        Args:
            source: EGIF source code to tokenize
            educational_mode: Whether to include educational metadata in tokens
        """
        self.source = source
        self.educational_mode = educational_mode
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.errors = []
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            (token_type, re.compile(pattern, re.MULTILINE | re.DOTALL), description)
            for token_type, pattern, description in self.TOKEN_PATTERNS
        ]
    
    def tokenize(self) -> Tuple[List[EGIFToken], List[EGIFLexError]]:
        """
        Tokenize the source code and return tokens and errors.
        
        Returns:
            Tuple of (tokens, errors) where tokens includes all recognized tokens
            and errors contains any lexical errors encountered.
        """
        self.tokens = []
        self.errors = []
        
        while self.position < len(self.source):
            if not self._try_match_token():
                # Handle unrecognized character
                self._handle_lexical_error()
        
        # Add EOF token
        self._add_eof_token()
        
        return self.tokens, self.errors
    
    def _try_match_token(self) -> bool:
        """
        Try to match a token at the current position.
        
        Returns:
            True if a token was matched, False otherwise.
        """
        for token_type, pattern, description in self.compiled_patterns:
            match = pattern.match(self.source, self.position)
            if match:
                value = match.group(0)
                
                # Create token with educational metadata
                token = self._create_token(
                    token_type, value, description, 
                    self.line, self.column, self.position, len(value)
                )
                
                # Skip whitespace and comments in normal mode, but preserve for educational feedback
                if token_type not in [EGIFTokenType.WHITESPACE, EGIFTokenType.COMMENT] or self.educational_mode:
                    if token_type not in [EGIFTokenType.WHITESPACE, EGIFTokenType.COMMENT]:
                        self.tokens.append(token)
                
                # Update position tracking
                self._update_position(value)
                return True
        
        return False
    
    def _create_token(self, token_type: EGIFTokenType, value: str, description: str,
                     line: int, column: int, position: int, length: int) -> EGIFToken:
        """Create a token with educational metadata."""
        token = EGIFToken(
            type=token_type,
            value=value,
            line=line,
            column=column,
            position=position,
            length=length,
            description=description
        )
        
        if self.educational_mode:
            # Add educational metadata
            token.eg_mapping = self.EG_MAPPINGS.get(token_type, "")
            token.context_hint = self._get_context_hint(token_type, value)
        
        return token
    
    def _get_context_hint(self, token_type: EGIFTokenType, value: str) -> str:
        """Generate contextual hints for educational feedback."""
        if token_type == EGIFTokenType.IDENTIFIER:
            if self._looks_like_relation_name(value):
                return "Likely relation name - will connect to lines of identity"
            else:
                return "Likely variable name - represents line of identity"
        elif token_type == EGIFTokenType.ASTERISK:
            return "Marks start of new line of identity (existential quantification)"
        elif token_type == EGIFTokenType.TILDE:
            return "Creates negative context - reverses truth conditions inside"
        elif token_type == EGIFTokenType.IF:
            return "Starts conditional pattern - equivalent to double cut in graphical form"
        return ""
    
    def _looks_like_relation_name(self, identifier: str) -> bool:
        """Heuristic to determine if identifier is likely a relation name."""
        # Simple heuristics: capitalized names often relations, lowercase often variables
        return identifier[0].isupper() if identifier else False
    
    def _update_position(self, value: str):
        """Update line and column tracking after consuming a token."""
        for char in value:
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.position += len(value)
    
    def _handle_lexical_error(self):
        """Handle an unrecognized character by creating an error token."""
        char = self.source[self.position]
        
        # Create educational error message
        error = EGIFLexError(
            message=f"Unrecognized character: '{char}'",
            line=self.line,
            column=self.column,
            position=self.position,
            length=1,
            error_type="INVALID_CHARACTER",
            suggestions=self._get_error_suggestions(char),
            educational_note=self._get_educational_error_note(char)
        )
        
        self.errors.append(error)
        
        # Create error token and advance
        error_token = EGIFToken(
            type=EGIFTokenType.ERROR,
            value=char,
            line=self.line,
            column=self.column,
            position=self.position,
            length=1,
            description=f"Lexical error: unrecognized character '{char}'"
        )
        
        self.tokens.append(error_token)
        self._update_position(char)
    
    def _get_error_suggestions(self, char: str) -> List[str]:
        """Generate helpful suggestions for lexical errors."""
        suggestions = []
        
        if char in '{}':
            suggestions.append("EGIF uses square brackets [ ] instead of curly braces")
        elif char in '<>':
            suggestions.append("EGIF uses parentheses ( ) for relations and square brackets [ ] for coreference")
        elif char == '&':
            suggestions.append("EGIF uses implicit conjunction - just place relations in the same context")
        elif char == '|' and self._not_in_function_context():
            suggestions.append("Pipe | is used only in function notation: (function inputs | output)")
        elif char == '!':
            suggestions.append("EGIF uses tilde ~ for negation instead of !")
        elif char == '@':
            suggestions.append("EGIF uses asterisk * to mark defining labels")
        
        return suggestions
    
    def _not_in_function_context(self) -> bool:
        """Check if we're not currently inside a function definition."""
        # Simple heuristic - look for recent opening parenthesis without closing
        recent_tokens = self.tokens[-10:] if len(self.tokens) >= 10 else self.tokens
        paren_count = 0
        for token in reversed(recent_tokens):
            if token.type == EGIFTokenType.RPAREN:
                paren_count += 1
            elif token.type == EGIFTokenType.LPAREN:
                paren_count -= 1
                if paren_count < 0:
                    return False  # We're inside parentheses
        return True
    
    def _get_educational_error_note(self, char: str) -> str:
        """Generate educational notes about lexical errors."""
        if char in '{}':
            return ("In existential graphs, cuts are represented by oval enclosures. "
                   "In EGIF, these become square brackets with tilde: ~[...]")
        elif char == '!':
            return ("Negation in existential graphs is represented by cuts (oval enclosures). "
                   "In EGIF, this becomes tilde followed by square brackets: ~[...]")
        elif char == '&':
            return ("Conjunction in existential graphs is implicit - multiple graphs drawn "
                   "in the same area are automatically conjoined. EGIF preserves this convention.")
        return f"The character '{char}' is not part of EGIF syntax."
    
    def _add_eof_token(self):
        """Add end-of-file token."""
        eof_token = EGIFToken(
            type=EGIFTokenType.EOF,
            value="",
            line=self.line,
            column=self.column,
            position=self.position,
            length=0,
            description="End of input"
        )
        self.tokens.append(eof_token)
    
    def get_educational_summary(self) -> str:
        """Generate an educational summary of the tokenization results."""
        if not self.educational_mode:
            return "Educational mode not enabled"
        
        summary = []
        summary.append("EGIF Tokenization Summary:")
        summary.append("=" * 30)
        
        # Count token types
        token_counts = {}
        for token in self.tokens:
            if token.type != EGIFTokenType.EOF:
                token_counts[token.type] = token_counts.get(token.type, 0) + 1
        
        # Educational interpretation
        if EGIFTokenType.TILDE in token_counts:
            summary.append(f"Found {token_counts[EGIFTokenType.TILDE]} negation(s) - these create cuts in the graphical form")
        
        if EGIFTokenType.ASTERISK in token_counts:
            summary.append(f"Found {token_counts[EGIFTokenType.ASTERISK]} defining label(s) - these start new lines of identity")
        
        if EGIFTokenType.LPAREN in token_counts:
            summary.append(f"Found {token_counts[EGIFTokenType.LPAREN]} relation(s) - these are atomic graphs with pegs")
        
        if EGIFTokenType.IF in token_counts:
            summary.append(f"Found {token_counts[EGIFTokenType.IF]} scroll pattern(s) - these represent double cuts (implications)")
        
        if self.errors:
            summary.append(f"\nFound {len(self.errors)} lexical error(s) - see error details for suggestions")
        
        return "\n".join(summary)


def tokenize_egif(source: str, educational_mode: bool = True) -> Tuple[List[EGIFToken], List[EGIFLexError]]:
    """
    Convenience function to tokenize EGIF source code.
    
    Args:
        source: EGIF source code
        educational_mode: Whether to include educational metadata
        
    Returns:
        Tuple of (tokens, errors)
    """
    lexer = EGIFLexer(source, educational_mode)
    return lexer.tokenize()


# Example usage and testing
if __name__ == "__main__":
    # Test cases for educational demonstration
    test_cases = [
        # Simple relation
        "(Person *x)",
        
        # Negation
        "~[(Person x)]",
        
        # Scroll notation
        "[If (Person *x) [Then (Mortal x)]]",
        
        # Coreference
        "(Person *x) (Mortal *y) [x y]",
        
        # Complex example
        "(Person *x) ~[(Mortal x)]",
        
        # Error cases for testing
        "(Person &x)",  # Invalid character
        "{Person x}",   # Wrong brackets
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("-" * 40)
        
        tokens, errors = tokenize_egif(test_case)
        
        print("Tokens:")
        for token in tokens:
            if token.type != EGIFTokenType.EOF:
                print(f"  {token}")
                if token.eg_mapping:
                    print(f"    -> {token.eg_mapping}")
        
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  {error.message} at {error.line}:{error.column}")
                if error.suggestions:
                    for suggestion in error.suggestions:
                        print(f"    Suggestion: {suggestion}")
                if error.educational_note:
                    print(f"    Note: {error.educational_note}")

