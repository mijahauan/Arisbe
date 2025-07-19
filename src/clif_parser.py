"""
Fixed CLIF parser with correct Entity-Predicate hypergraph architecture.

This module provides CLIF parsing that correctly maps:
- CLIF terms (variables, constants) → Entities (Lines of Identity)
- CLIF predicates → Predicates (hyperedges connecting entities)
- CLIF quantifiers → Entity scoping in contexts

Fixed to properly handle graph state management, context tracking, and equality operator tokenization.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

from eg_types import (
    Entity, Predicate, Context,
    EntityId, PredicateId, ContextId,
    new_entity_id, new_predicate_id, new_context_id,
    ValidationError, pmap, pset
)
from graph import EGGraph


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
    OPERATOR = "OPERATOR"


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
        'cl:comment'
    }
    
    # CLIF operators
    OPERATORS = {'='}
    
    # Token patterns (order matters - more specific patterns first)
    TOKEN_PATTERNS = [
        (CLIFTokenType.COMMENT, r'/\*.*?\*/'),
        (CLIFTokenType.COMMENT, r'//.*?$'),
        (CLIFTokenType.WHITESPACE, r'\s+'),
        (CLIFTokenType.LPAREN, r'\('),
        (CLIFTokenType.RPAREN, r'\)'),
        (CLIFTokenType.STRING, r'"([^"\\]|\\.)*"'),
        (CLIFTokenType.NUMBER, r'-?\d+(\.\d+)?'),
        (CLIFTokenType.OPERATOR, r'='),  # Add explicit pattern for =
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
                    
                    # Skip whitespace and comments
                    if token_type not in [CLIFTokenType.WHITESPACE, CLIFTokenType.COMMENT]:
                        # Check if identifier is a keyword
                        if token_type == CLIFTokenType.IDENTIFIER and value in self.KEYWORDS:
                            token_type = CLIFTokenType.KEYWORD
                        # Check if operator is a keyword (for backwards compatibility)
                        elif token_type == CLIFTokenType.OPERATOR and value in self.KEYWORDS:
                            token_type = CLIFTokenType.KEYWORD
                        
                        token = CLIFToken(
                            type=token_type,
                            value=value,
                            line=self.line,
                            column=self.column,
                            position=self.position
                        )
                        self.tokens.append(token)
                    
                    # Update position
                    self.position = match.end()
                    
                    # Update line and column
                    for char in value:
                        if char == '\n':
                            self.line += 1
                            self.column = 1
                        else:
                            self.column += 1
                    
                    matched = True
                    break
            
            if not matched:
                # Skip unknown character
                self.position += 1
                self.column += 1
        
        # Add EOF token
        self.tokens.append(CLIFToken(
            type=CLIFTokenType.EOF,
            value="",
            line=self.line,
            column=self.column,
            position=self.position
        ))
        
        return self.tokens


class CLIFParser:
    """Parser for CLIF (Common Logic Interchange Format) with Entity-Predicate architecture."""
    
    def __init__(self):
        """Initialize the parser."""
        self.lexer = None
        self.tokens = []
        self.position = 0
        self.errors = []
        self.warnings = []
        self.comments = []
        self.imports = []
        self.metadata = {}
        
        # Entity registry for tracking entities across the parse
        self.entity_registry = {}  # Dict[str, EntityId]
        self.current_context = None
    
    def parse(self, source: str) -> CLIFParseResult:
        """Parse CLIF source code into an existential graph."""
        try:
            # Initialize parser state
            self.lexer = CLIFLexer(source)
            self.tokens = self.lexer.tokenize()
            self.position = 0
            self.errors = []
            self.warnings = []
            self.comments = []
            self.imports = []
            self.metadata = {}
            self.entity_registry = {}
            
            # Parse the module
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
    
    def _expect(self, expected_type: CLIFTokenType) -> CLIFToken:
        """Expect a specific token type and advance."""
        token = self._current_token()
        if token.type != expected_type:
            self._add_error(
                f"Expected {expected_type.value}, got {token.type.value}: {token.value}",
                "SYNTAX_ERROR"
            )
        return self._advance()
    
    def _add_error(self, message: str, error_type: str, suggestions: List[str] = None):
        """Add an error to the error list."""
        if suggestions is None:
            suggestions = []
        
        token = self._current_token()
        error = CLIFError(
            message=message,
            line=token.line,
            column=token.column,
            position=token.position,
            error_type=error_type,
            suggestions=suggestions
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
        self.current_context = graph.root_context_id
        
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
        elif token.type == CLIFTokenType.OPERATOR and token.value == '=':
            # Handle = as operator
            return self._parse_equality(graph)
        elif token.type == CLIFTokenType.IDENTIFIER and token.value == '=':
            # Handle = as identifier (fallback)
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
        # Universal quantification: forall x P(x) = ~exists x ~P(x)
        graph, outer_cut = graph.create_context('cut', self.current_context, 'Universal Quantification')
        graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Existential Scope')
        
        # Set context for variable scoping
        old_context = self.current_context
        self.current_context = inner_cut.id
        
        # Add variables as entities in the inner context
        for var_name in variables:
            graph, entity = self._get_or_create_entity(graph, var_name, 'variable')
        
        # Parse the body
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected sentence after variable list", "SYNTAX_ERROR")
        
        # Restore context
        self.current_context = old_context
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_exists(self, graph: EGGraph) -> EGGraph:
        """Parse an existential quantification."""
        self._advance()  # consume 'exists'
        
        # Parse variable list
        variables = self._parse_variable_list()
        
        # Create a new context for the quantification
        graph, exist_context = graph.create_context('cut', self.current_context, 'Existential Quantification')
        
        # Set context for variable scoping
        old_context = self.current_context
        self.current_context = exist_context.id
        
        # Add variables as entities in the existential context
        for var_name in variables:
            graph, entity = self._get_or_create_entity(graph, var_name, 'variable')
        
        # Parse the body
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected sentence after variable list", "SYNTAX_ERROR")
        
        # Restore context
        self.current_context = old_context
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_and(self, graph: EGGraph) -> EGGraph:
        """Parse a conjunction."""
        self._advance()  # consume 'and'
        
        # Parse all conjuncts in the same context
        while (self._current_token().type != CLIFTokenType.RPAREN and 
               self._current_token().type != CLIFTokenType.EOF):
            if self._current_token().type == CLIFTokenType.LPAREN:
                graph = self._parse_sentence(graph)
            else:
                self._add_error("Expected sentence in conjunction", "SYNTAX_ERROR")
                break
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_or(self, graph: EGGraph) -> EGGraph:
        """Parse a disjunction."""
        self._advance()  # consume 'or'
        
        # Disjunction: (or P Q) = ~(~P ~Q)
        graph, outer_cut = graph.create_context('cut', self.current_context, 'Disjunction')
        
        old_context = self.current_context
        self.current_context = outer_cut.id
        
        # Parse all disjuncts, each in its own cut
        while (self._current_token().type != CLIFTokenType.RPAREN and 
               self._current_token().type != CLIFTokenType.EOF):
            if self._current_token().type == CLIFTokenType.LPAREN:
                graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Disjunct')
                self.current_context = inner_cut.id
                graph = self._parse_sentence(graph)
                self.current_context = outer_cut.id
            else:
                self._add_error("Expected sentence in disjunction", "SYNTAX_ERROR")
                break
        
        # Restore context
        self.current_context = old_context
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_not(self, graph: EGGraph) -> EGGraph:
        """Parse a negation."""
        self._advance()  # consume 'not'
        
        # Create a cut context for negation
        graph, cut_context = graph.create_context('cut', self.current_context, 'Negation')
        
        # Set context for the negated content
        old_context = self.current_context
        self.current_context = cut_context.id
        
        # Parse the negated sentence
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected sentence after 'not'", "SYNTAX_ERROR")
        
        # Restore context
        self.current_context = old_context
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_if(self, graph: EGGraph) -> EGGraph:
        """Parse an implication."""
        self._advance()  # consume 'if'
        
        # Create implication pattern: (if P Q) = ~(P ~Q)
        graph, outer_cut = graph.create_context('cut', self.current_context, 'Implication')
        
        # Parse antecedent in the outer cut
        old_context = self.current_context
        self.current_context = outer_cut.id
        
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected antecedent", "SYNTAX_ERROR")
        
        # Parse consequent in a nested cut (negated)
        if self._current_token().type == CLIFTokenType.LPAREN:
            graph, inner_cut = graph.create_context('cut', outer_cut.id, 'Consequent Negation')
            self.current_context = inner_cut.id
            graph = self._parse_sentence(graph)
        else:
            self._add_error("Expected consequent", "SYNTAX_ERROR")
        
        # Restore context
        self.current_context = old_context
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_equality(self, graph: EGGraph) -> EGGraph:
        """Parse an equality statement."""
        self._advance()  # consume '='
        
        # Parse two terms
        graph, term1_entity_id = self._parse_term(graph)
        graph, term2_entity_id = self._parse_term(graph)
        
        # Create entities for the terms and connect them
        if term1_entity_id and term2_entity_id:
            # Create an equality predicate
            equality_pred = Predicate.create(
                name='=',
                entities=[term1_entity_id, term2_entity_id],
                arity=2
            )
            graph = graph.add_predicate(equality_pred, self.current_context)
        else:
            self._add_error("Failed to parse equality terms", "SEMANTIC_ERROR")
        
        self._expect(CLIFTokenType.RPAREN)
        return graph
    
    def _parse_atomic_sentence(self, graph: EGGraph) -> EGGraph:
        """Parse an atomic sentence with correct Entity-Predicate architecture."""
        # Parse predicate name
        if self._current_token().type == CLIFTokenType.IDENTIFIER:
            predicate_name = self._advance().value
            
            # Parse arguments (terms)
            entity_ids = []
            while (self._current_token().type != CLIFTokenType.RPAREN and 
                   self._current_token().type != CLIFTokenType.EOF):
                graph, entity_id = self._parse_term(graph)
                if entity_id:
                    entity_ids.append(entity_id)
            
            # Create predicate connecting the entities
            if entity_ids:
                predicate = Predicate.create(
                    name=predicate_name,
                    entities=entity_ids,
                    arity=len(entity_ids)
                )
                graph = graph.add_predicate(predicate, self.current_context)
            else:
                # Zero-arity predicate
                predicate = Predicate.create(
                    name=predicate_name,
                    entities=[],
                    arity=0
                )
                graph = graph.add_predicate(predicate, self.current_context)
        else:
            self._add_error(f"Expected predicate name, got {self._current_token().value}", "SYNTAX_ERROR")
        
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
                break
        
        self._expect(CLIFTokenType.RPAREN)
        return variables
    
    def _parse_term(self, graph: EGGraph) -> Tuple[EGGraph, Optional[EntityId]]:
        """Parse a term (variable, constant, or function), returning updated graph and entity ID."""
        token = self._current_token()
        
        if token.type == CLIFTokenType.IDENTIFIER:
            term_name = self._advance().value
            graph, entity = self._get_or_create_entity(graph, term_name, self._get_term_type(term_name))
            return graph, entity.id
        elif token.type == CLIFTokenType.STRING:
            term_name = self._advance().value
            graph, entity = self._get_or_create_entity(graph, term_name, 'constant')
            return graph, entity.id
        elif token.type == CLIFTokenType.NUMBER:
            term_name = self._advance().value
            graph, entity = self._get_or_create_entity(graph, term_name, 'constant')
            return graph, entity.id
        elif token.type == CLIFTokenType.LPAREN:
            # Function term: (function_name arg1 arg2 ...)
            self._advance()  # consume '('
            
            if self._current_token().type != CLIFTokenType.IDENTIFIER:
                self._add_error("Expected function name", "SYNTAX_ERROR")
                return graph, None
            
            function_name = self._advance().value
            
            # Parse function arguments
            arg_entity_ids = []
            while (self._current_token().type != CLIFTokenType.RPAREN and 
                   self._current_token().type != CLIFTokenType.EOF):
                graph, arg_entity_id = self._parse_term(graph)
                if arg_entity_id:
                    arg_entity_ids.append(arg_entity_id)
            
            self._advance()  # consume ')'
            
            # Create a unique name for the result entity based on function and arguments
            result_entity_name = f"{function_name}({','.join(str(id) for id in arg_entity_ids)})"
            
            # Check if this functional term already exists
            if result_entity_name in self.entity_registry:
                # Reuse existing entity
                entity_id = self.entity_registry[result_entity_name]
                entity = graph.entities.get(entity_id)
                if entity is not None:
                    return graph, entity.id
            
            # Create new result entity
            graph, result_entity = self._get_or_create_entity(graph, result_entity_name, 'functional_term')
            
            # Create function predicate only if it doesn't already exist
            function_predicate = Predicate.create(
                name=function_name,
                entities=arg_entity_ids + [result_entity.id],
                arity=len(arg_entity_ids) + 1,
                predicate_type='function',
                return_entity=result_entity.id
            )
            graph = graph.add_predicate(function_predicate, self.current_context)
            
            return graph, result_entity.id
        else:
            self._add_error(f"Expected term, got {token.value}", "SYNTAX_ERROR")
            return graph, None
    
    def _get_or_create_entity(self, graph: EGGraph, name: str, entity_type: str) -> Tuple[EGGraph, Entity]:
        """Get existing entity or create new one, returning updated graph and entity."""
        # Check if entity already exists
        if name in self.entity_registry:
            entity_id = self.entity_registry[name]
            entity = graph.entities.get(entity_id)
            if entity is not None:
                return graph, entity
        
        # Create new entity
        entity = Entity.create(name=name, entity_type=entity_type)
        updated_graph = graph.add_entity(entity, self.current_context)
        
        # Register entity
        self.entity_registry[name] = entity.id
        
        return updated_graph, entity
    
    def _get_term_type(self, term: str) -> str:
        """Determine the type of a term (variable, constant, function)."""
        # Simple heuristic: lowercase single letters are variables
        if len(term) == 1 and term.islower():
            return 'variable'
        elif term.startswith('"') or term.replace('.', '').replace('-', '').isdigit():
            return 'constant'
        elif '(' in term:
            return 'function'
        else:
            # Default to constant for named entities
            return 'constant'

