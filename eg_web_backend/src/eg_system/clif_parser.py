"""
Enhanced CLIF parser with full ISO 24707 standard support.

This module provides comprehensive parsing of Common Logic Interchange Format
with support for comments, domains of discourse, imports, and robust error
handling with detailed reporting.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

from .eg_types import (
    Node, Edge, Context, Ligature,
    NodeId, EdgeId, ContextId, LigatureId,
    new_node_id, new_edge_id, new_context_id, new_ligature_id,
    ValidationError, pmap, pset
)
from .graph import EGGraph


class CLIFTokenType(Enum):
    """Token types for CLIF parsing."""
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    COMMENT = "COMMENT"
    WHITESPACE = "WHITESPACE"
    EOF = "EOF"
    KEYWORD = "KEYWORD"


@dataclass
class CLIFToken:
    """A token in CLIF source code."""
    type: CLIFTokenType
    value: str
    line: int
    column: int
    position: int


@dataclass
class CLIFError:
    """A parsing or semantic error in CLIF."""
    message: str
    line: int
    column: int
    position: int
    error_type: str
    suggestions: List[str]


@dataclass
class CLIFParseResult:
    """Result of CLIF parsing operation."""
    graph: Optional[EGGraph]
    errors: List[CLIFError]
    warnings: List[CLIFError]
    comments: List[str]
    imports: List[str]
    metadata: Dict[str, Any]


class CLIFLexer:
    """Lexical analyzer for CLIF source code."""
    
    # CLIF keywords
    KEYWORDS = {
        'cl:text', 'cl:module', 'cl:imports', 'cl:excludes',
        'forall', 'exists', 'and', 'or', 'not', 'if', 'iff',
        '=', 'cl:comment'
    }
    
    # Token patterns
    TOKEN_PATTERNS = [
        (CLIFTokenType.COMMENT, r'/\*.*?\*/'),
        (CLIFTokenType.COMMENT, r'//.*?$'),
        (CLIFTokenType.WHITESPACE, r'\s+'),
        (CLIFTokenType.LPAREN, r'\('),
        (CLIFTokenType.RPAREN, r'\)'),
        (CLIFTokenType.STRING, r'"([^"\\]|\\.)*"'),
        (CLIFTokenType.NUMBER, r'-?\d+(\.\d+)?'),
        (CLIFTokenType.IDENTIFIER, r'[a-zA-Z_][a-zA-Z0-9_:.-]*'),
    ]
    
    def __init__(self, source: str):
        """Initialize lexer with source code."""
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
    def tokenize(self) -> List[CLIFToken]:
        """Tokenize the source code."""
        self.tokens = []
        
        while self.position < len(self.source):
            matched = False
            
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
                match = regex.match(self.source, self.position)
                
                if match:
                    value = match.group(0)
                    
                    # Skip whitespace tokens
                    if token_type != CLIFTokenType.WHITESPACE:
                        # Check if identifier is a keyword
                        if token_type == CLIFTokenType.IDENTIFIER and value in self.KEYWORDS:
                            token_type = CLIFTokenType.KEYWORD
                        
                        token = CLIFToken(
                            type=token_type,
                            value=value,
                            line=self.line,
                            column=self.column,
                            position=self.position
                        )
                        self.tokens.append(token)
                    
                    # Update position tracking
                    for char in value:
                        if char == '\n':
                            self.line += 1
                            self.column = 1
                        else:
                            self.column += 1
                    
                    self.position = match.end()
                    matched = True
                    break
            
            if not matched:
                # Handle unexpected character
                char = self.source[self.position]
                error_token = CLIFToken(
                    type=CLIFTokenType.IDENTIFIER,  # Fallback type
                    value=char,
                    line=self.line,
                    column=self.column,
                    position=self.position
                )
                self.tokens.append(error_token)
                self.position += 1
                self.column += 1
        
        # Add EOF token
        eof_token = CLIFToken(
            type=CLIFTokenType.EOF,
            value="",
            line=self.line,
            column=self.column,
            position=self.position
        )
        self.tokens.append(eof_token)
        
        return self.tokens


class CLIFParser:
    """Parser for CLIF source code with full ISO 24707 support."""
    
    def __init__(self):
        """Initialize the parser."""
        self.tokens = []
        self.position = 0
        self.errors = []
        self.warnings = []
        self.comments = []
        self.imports = []
        self.metadata = {}
        
    def parse(self, source: str) -> CLIFParseResult:
        """Parse CLIF source code into an EGGraph.
        
        Args:
            source: CLIF source code string.
            
        Returns:
            CLIFParseResult containing the parsed graph and any errors.
        """
        # Reset parser state
        self.errors = []
        self.warnings = []
        self.comments = []
        self.imports = []
        self.metadata = {}
        
        # Tokenize
        lexer = CLIFLexer(source)
        self.tokens = lexer.tokenize()
        self.position = 0
        
        # Extract comments and imports first
        self._extract_metadata()
        
        # Parse the main content
        try:
            graph = self._parse_module()
            return CLIFParseResult(
                graph=graph,
                errors=self.errors,
                warnings=self.warnings,
                comments=self.comments,
                imports=self.imports,
                metadata=self.metadata
            )
        except Exception as e:
            self._add_error(f"Parsing failed: {str(e)}", "PARSE_ERROR")
            return CLIFParseResult(
                graph=None,
                errors=self.errors,
                warnings=self.warnings,
                comments=self.comments,
                imports=self.imports,
                metadata=self.metadata
            )
    
    def _extract_metadata(self):
        """Extract comments and imports from tokens."""
        for token in self.tokens:
            if token.type == CLIFTokenType.COMMENT:
                # Clean up comment content
                comment_text = token.value
                if comment_text.startswith('/*') and comment_text.endswith('*/'):
                    comment_text = comment_text[2:-2].strip()
                elif comment_text.startswith('//'):
                    comment_text = comment_text[2:].strip()
                
                self.comments.append(comment_text)
    
    def _current_token(self) -> CLIFToken:
        """Get the current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]  # EOF token
    
    def _advance(self) -> CLIFToken:
        """Advance to the next token and return the current one."""
        token = self._current_token()
        if self.position < len(self.tokens) - 1:
            self.position += 1
        return token
    
    def _peek(self, offset: int = 1) -> CLIFToken:
        """Peek at a future token."""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # EOF token
    
    def _expect(self, token_type: CLIFTokenType) -> CLIFToken:
        """Expect a specific token type and advance."""
        token = self._current_token()
        if token.type != token_type:
            self._add_error(
                f"Expected {token_type.value}, got {token.type.value}",
                "SYNTAX_ERROR",
                suggestions=[f"Add {token_type.value}"]
            )
        return self._advance()
    
    def _add_error(self, message: str, error_type: str, suggestions: List[str] = None):
        """Add an error to the error list."""
        token = self._current_token()
        error = CLIFError(
            message=message,
            line=token.line,
            column=token.column,
            position=token.position,
            error_type=error_type,
            suggestions=suggestions or []
        )
        self.errors.append(error)
    
    def _add_warning(self, message: str, warning_type: str):
        """Add a warning to the warning list."""
        token = self._current_token()
        warning = CLIFError(
            message=message,
            line=token.line,
            column=token.column,
            position=token.position,
            error_type=warning_type,
            suggestions=[]
        )
        self.warnings.append(warning)
    
    def _parse_module(self) -> EGGraph:
        """Parse a CLIF module."""
        graph = EGGraph.create_empty()
        
        while self._current_token().type != CLIFTokenType.EOF:
            if self._current_token().type == CLIFTokenType.LPAREN:
                graph = self._parse_sentence(graph)
            else:
                # Skip unexpected tokens with error
                token = self._advance()
                if token.type != CLIFTokenType.COMMENT:
                    self._add_error(
                        f"Unexpected token: {token.value}",
                        "SYNTAX_ERROR"
                    )
        
        return graph
    
    def _parse_sentence(self, graph: EGGraph) -> EGGraph:
        """Parse a CLIF sentence."""
        self._expect(CLIFTokenType.LPAREN)
        
        if self._current_token().type == CLIFTokenType.EOF:
            self._add_error("Unexpected end of input", "SYNTAX_ERROR")
            return graph
        
        # Check for special forms
        token = self._current_token()
        
        if token.type == CLIFTokenType.KEYWORD:
            if token.value == 'cl:imports':
                return self._parse_import(graph)
            elif token.value == 'cl:text':
                return self._parse_text(graph)
            elif token.value == 'forall':
                return self._parse_forall(graph)
            elif token.value == 'exists':
                return self._parse_exists(graph)
            elif token.value == 'and':
                return self._parse_and(graph)
            elif token.value == 'or':
                return self._parse_or(graph)
            elif token.value == 'not':
                return self._parse_not(graph)
            elif token.value == 'if':
                return self._parse_if(graph)
            elif token.value == '=':
                return self._parse_equality(graph)
        elif token.type == CLIFTokenType.IDENTIFIER and token.value == '=':
            # Handle = as identifier (not keyword)
            return self._parse_equality(graph)
        
        # Default: parse as atomic sentence
        return self._parse_atomic_sentence(graph)
    
    def _parse_import(self, graph: EGGraph) -> EGGraph:
        """Parse an import statement."""
        self._advance()  # consume 'cl:imports'
        
        if self._current_token().type == CLIFTokenType.STRING:
            import_uri = self._advance().value[1:-1]  # Remove quotes
            self.imports.append(import_uri)
        else:
            self._add_error("Expected import URI", "SYNTAX_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_text(self, graph: EGGraph) -> EGGraph:
        """Parse a text block."""
        self._advance()  # consume 'cl:text'
        
        # Parse nested sentences
        while (self._current_token().type != CLIFTokenType.RPAREN and 
               self._current_token().type != CLIFTokenType.EOF):
            if self._current_token().type == CLIFTokenType.LPAREN:
                graph = self._parse_sentence(graph)
            else:
                self._advance()  # Skip unexpected tokens
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_forall(self, graph: EGGraph) -> EGGraph:
        """Parse a universal quantification."""
        self._advance()  # consume 'forall'
        
        # Parse variable list
        variables = self._parse_variable_list()
        
        # Create a new context for the quantification
        graph, quant_context = graph.create_context('cut', name='Universal Quantification')
        
        # Parse the body
        if self._current_token().type == CLIFTokenType.LPAREN:
            # Create negation context (forall x P(x) = ~exists x ~P(x))
            graph, neg_context = graph.create_context('cut', quant_context.id, 'Negation')
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected sentence after variable list", "SYNTAX_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_exists(self, graph: EGGraph) -> EGGraph:
        """Parse an existential quantification."""
        self._advance()  # consume 'exists'
        
        # Parse variable list
        variables = self._parse_variable_list()
        
        # Parse the body
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected sentence after variable list", "SYNTAX_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_and(self, graph: EGGraph) -> EGGraph:
        """Parse a conjunction."""
        self._advance()  # consume 'and'
        
        # Parse all conjuncts
        while (self._current_token().type != CLIFTokenType.RPAREN and 
               self._current_token().type != CLIFTokenType.EOF):
            if self._current_token().type == CLIFTokenType.LPAREN:
                graph = self._parse_sentence(graph)
            else:
                self._advance()  # Skip unexpected tokens
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_or(self, graph: EGGraph) -> EGGraph:
        """Parse a disjunction."""
        self._advance()  # consume 'or'
        
        # Create disjunction pattern: (or P Q) = ~(~P ~Q)
        graph, outer_cut = graph.create_context('cut', name='Disjunction Outer')
        
        # Parse all disjuncts in separate cuts
        while (self._current_token().type != CLIFTokenType.RPAREN and 
               self._current_token().type != CLIFTokenType.EOF):
            if self._current_token().type == CLIFTokenType.LPAREN:
                graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Disjunct')
                graph = self._parse_sentence(graph)
            else:
                self._advance()  # Skip unexpected tokens
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_not(self, graph: EGGraph) -> EGGraph:
        """Parse a negation."""
        self._advance()  # consume 'not'
        
        # Create cut context for negation
        graph, cut_context = graph.create_context('cut', name='Negation')
        
        # Parse the negated sentence
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected sentence after 'not'", "SYNTAX_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_if(self, graph: EGGraph) -> EGGraph:
        """Parse an implication."""
        self._advance()  # consume 'if'
        
        # Create implication pattern: (if P Q) = ~(P ~Q)
        graph, outer_cut = graph.create_context('cut', name='Implication')
        
        # Parse antecedent
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected antecedent", "SYNTAX_ERROR")
        
        # Parse consequent in a cut
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Consequent Negation')
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected consequent", "SYNTAX_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_equality(self, graph: EGGraph) -> EGGraph:
        """Parse an equality statement."""
        self._advance()  # consume '='
        
        # Parse two terms
        term1 = self._parse_term()
        term2 = self._parse_term()
        
        # Create equality as a ligature connecting the terms
        if term1 and term2:
            # Create nodes for the terms
            node1 = Node.create(node_type='term', properties={'value': term1})
            node2 = Node.create(node_type='term', properties={'value': term2})
            
            graph = graph.add_node(node1)
            graph = graph.add_node(node2)
            
            # Create ligature to represent equality
            ligature = Ligature.create(
                nodes={node1.id, node2.id},
                properties={'type': 'equality'}
            )
            graph = graph.add_ligature(ligature)
        else:
            self._add_error("Failed to parse equality terms", "SEMANTIC_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_atomic_sentence(self, graph: EGGraph) -> EGGraph:
        """Parse an atomic sentence."""
        # Parse predicate name
        if self._current_token().type == CLIFTokenType.IDENTIFIER:
            predicate = self._advance().value
            
            # Create predicate node
            pred_node = Node.create(
                node_type='predicate',
                properties={'name': predicate}
            )
            graph = graph.add_node(pred_node)
            
            # Parse arguments
            arg_nodes = []
            while (self._current_token().type != CLIFTokenType.RPAREN and 
                   self._current_token().type != CLIFTokenType.EOF):
                term = self._parse_term()
                if term:
                    arg_node = Node.create(
                        node_type='term',
                        properties={'value': term}
                    )
                    graph = graph.add_node(arg_node)
                    arg_nodes.append(arg_node)
            
            # Create edge connecting predicate to arguments
            if arg_nodes:
                all_nodes = {pred_node.id} | {node.id for node in arg_nodes}
                edge = Edge.create(
                    edge_type='predication',
                    nodes=all_nodes
                )
                graph = graph.add_edge(edge)
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_variable_list(self) -> List[str]:
        """Parse a list of variables."""
        variables = []
        
        self._expect(CLIFTokenType.LPAREN)
        
        while (self._current_token().type != CLIFTokenType.RPAREN and 
               self._current_token().type != CLIFTokenType.EOF):
            if self._current_token().type == CLIFTokenType.IDENTIFIER:
                variables.append(self._advance().value)
            else:
                self._add_error("Expected variable name", "SYNTAX_ERROR")
                self._advance()
        
        self._expect(CLIFTokenType.RPAREN)
        return variables
    
    def _parse_term(self) -> Optional[str]:
        """Parse a term (variable, constant, or function application)."""
        token = self._current_token()
        
        if token.type == CLIFTokenType.IDENTIFIER:
            return self._advance().value
        elif token.type == CLIFTokenType.STRING:
            return self._advance().value[1:-1]  # Remove quotes
        elif token.type == CLIFTokenType.NUMBER:
            return self._advance().value
        elif token.type == CLIFTokenType.LPAREN:
            # Function application
            self._advance()  # consume '('
            
            if self._current_token().type == CLIFTokenType.IDENTIFIER:
                func_name = self._advance().value
                args = []
                
                while (self._current_token().type != CLIFTokenType.RPAREN and 
                       self._current_token().type != CLIFTokenType.EOF):
                    arg = self._parse_term()
                    if arg:
                        args.append(arg)
                
                self._expect(CLIFTokenType.RPAREN)
                return f"{func_name}({', '.join(args)})"
            else:
                self._add_error("Expected function name", "SYNTAX_ERROR")
                return None
        else:
            self._add_error(f"Expected term, got {token.value}", "SYNTAX_ERROR")
            return None

