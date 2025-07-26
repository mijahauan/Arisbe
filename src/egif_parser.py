"""
EGIF Parser - Educational-First Design

This module provides parsing capabilities for Existential Graph Interchange Format (EGIF)
with comprehensive educational feedback designed to help users understand the relationship
between EGIF syntax and existential graph structures.

The parser leverages EGIF's closer correspondence to existential graphs to provide more
direct and intuitive translations to the EG-HG representation than the current CLIF
implementation.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
import uuid

from egif_lexer import EGIFLexer, EGIFToken, EGIFTokenType, EGIFLexError
from eg_types import (
    Entity, Predicate, Context, EntityId, PredicateId, ContextId,
    new_entity_id, new_predicate_id, new_context_id,
    ValidationError
)


@dataclass
class EGIFParseError:
    """A parsing error with educational feedback."""
    message: str
    token: Optional[EGIFToken]
    error_type: str
    suggestions: List[str]
    educational_note: str = ""
    context_info: str = ""


@dataclass
class ParseContext:
    """Context information during parsing for educational feedback."""
    current_context_id: ContextId
    defining_labels: Dict[str, EntityId]  # Maps label names to entity IDs
    bound_labels: Set[str]  # Labels that have been referenced
    negation_depth: int = 0
    in_scroll: bool = False
    scroll_depth: int = 0
    
    def enter_negation(self) -> 'ParseContext':
        """Return new context with increased negation depth."""
        return ParseContext(
            current_context_id=new_context_id(),
            defining_labels=self.defining_labels.copy(),
            bound_labels=self.bound_labels.copy(),
            negation_depth=self.negation_depth + 1,
            in_scroll=self.in_scroll,
            scroll_depth=self.scroll_depth
        )
    
    def enter_scroll(self) -> 'ParseContext':
        """Return new context for scroll notation."""
        return ParseContext(
            current_context_id=new_context_id(),
            defining_labels=self.defining_labels.copy(),
            bound_labels=self.bound_labels.copy(),
            negation_depth=self.negation_depth,
            in_scroll=True,
            scroll_depth=self.scroll_depth + 1
        )


@dataclass
class EGIFParseResult:
    """Result of parsing an EGIF expression."""
    entities: List[Entity]
    predicates: List[Predicate]
    contexts: List[Context]
    root_context_id: ContextId
    errors: List[EGIFParseError]
    educational_trace: List[str]  # Step-by-step parsing explanation


class EGIFParser:
    """
    Parser for EGIF with educational-first design.
    
    This parser is designed to support educational use by providing:
    - Clear error messages that explain EGIF syntax rules
    - Educational trace of parsing decisions
    - Mapping information between EGIF constructs and EG structures
    - Detection of common errors with helpful suggestions
    """
    
    def __init__(self, educational_mode: bool = True):
        """
        Initialize the EGIF parser.
        
        Args:
            educational_mode: Whether to include educational feedback and tracing
        """
        self.educational_mode = educational_mode
        self.tokens = []
        self.position = 0
        self.errors = []
        self.educational_trace = []
        
        # Parse results
        self.entities = []
        self.predicates = []
        self.contexts = []
        
        # Current parsing state
        self.current_token = None
        self.parse_context = None
    
    def parse(self, source: str) -> EGIFParseResult:
        """
        Parse EGIF source code and return the result.
        
        Args:
            source: EGIF source code to parse
            
        Returns:
            EGIFParseResult containing entities, predicates, contexts, and any errors
        """
        # Initialize parsing state
        self._reset_state()
        
        # Tokenize the source
        lexer = EGIFLexer(source, self.educational_mode)
        tokens, lex_errors = lexer.tokenize()
        
        # Convert lexical errors to parse errors
        for lex_error in lex_errors:
            parse_error = EGIFParseError(
                message=lex_error.message,
                token=None,
                error_type="LEXICAL_ERROR",
                suggestions=lex_error.suggestions,
                educational_note=lex_error.educational_note
            )
            self.errors.append(parse_error)
        
        # Filter out whitespace tokens for parsing
        self.tokens = [token for token in tokens if token.type != EGIFTokenType.WHITESPACE]
        
        if not self.tokens:
            return self._create_result()
        
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
        # Create root context
        root_context_id = new_context_id()
        self.parse_context = ParseContext(
            current_context_id=root_context_id,
            defining_labels={},
            bound_labels=set()
        )
        
        self._trace("Starting EGIF parsing")
        self._trace(f"Root context created: {root_context_id}")
        
        try:
            # Parse the main expression
            self._parse_expression()
            
            # Check for unexpected tokens
            if self.current_token and self.current_token.type != EGIFTokenType.EOF:
                self._error(
                    f"Unexpected token: {self.current_token.value}",
                    "UNEXPECTED_TOKEN",
                    ["Check for missing brackets or parentheses"],
                    "All EGIF expressions should be properly closed"
                )
        
        except Exception as e:
            self._error(
                f"Internal parser error: {str(e)}",
                "INTERNAL_ERROR",
                ["Please report this error"],
                "This indicates a bug in the parser implementation"
            )
        
        return self._create_result()
    
    def _reset_state(self):
        """Reset parser state for a new parse."""
        self.tokens = []
        self.position = 0
        self.errors = []
        self.educational_trace = []
        self.entities = []
        self.predicates = []
        self.contexts = []
        self.current_token = None
        self.parse_context = None
    
    def _create_result(self) -> EGIFParseResult:
        """Create the final parse result."""
        root_context_id = self.parse_context.current_context_id if self.parse_context else new_context_id()
        
        return EGIFParseResult(
            entities=self.entities,
            predicates=self.predicates,
            contexts=self.contexts,
            root_context_id=root_context_id,
            errors=self.errors,
            educational_trace=self.educational_trace
        )
    
    def _advance(self):
        """Advance to the next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None
    
    def _peek(self, offset: int = 1) -> Optional[EGIFToken]:
        """Look ahead at future tokens without advancing."""
        peek_pos = self.position + offset
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return None
    
    def _expect(self, token_type: EGIFTokenType) -> bool:
        """Check if current token matches expected type."""
        if not self.current_token:
            return False
        return self.current_token.type == token_type
    
    def _consume(self, token_type: EGIFTokenType) -> bool:
        """Consume a token of the expected type."""
        if self._expect(token_type):
            self._advance()
            return True
        return False
    
    def _error(self, message: str, error_type: str, suggestions: List[str], educational_note: str = ""):
        """Record a parsing error with educational feedback."""
        error = EGIFParseError(
            message=message,
            token=self.current_token,
            error_type=error_type,
            suggestions=suggestions,
            educational_note=educational_note,
            context_info=self._get_context_info()
        )
        self.errors.append(error)
        
        if self.educational_mode:
            self._trace(f"ERROR: {message}")
            if educational_note:
                self._trace(f"Educational note: {educational_note}")
    
    def _trace(self, message: str):
        """Add a message to the educational trace."""
        if self.educational_mode:
            self.educational_trace.append(message)
    
    def _get_context_info(self) -> str:
        """Get current parsing context information for error reporting."""
        if not self.parse_context:
            return "No context available"
        
        info = []
        if self.parse_context.negation_depth > 0:
            info.append(f"Inside {self.parse_context.negation_depth} level(s) of negation")
        if self.parse_context.in_scroll:
            info.append("Inside scroll notation")
        if self.parse_context.defining_labels:
            labels = list(self.parse_context.defining_labels.keys())
            info.append(f"Available labels: {', '.join(labels)}")
        
        return "; ".join(info) if info else "Root context"
    
    def _parse_expression(self):
        """Parse a complete EGIF expression."""
        self._trace("Parsing expression")
        
        while self.current_token and self.current_token.type != EGIFTokenType.EOF and self.current_token.type != EGIFTokenType.RBRACKET:
            if self._expect(EGIFTokenType.LPAREN):
                self._parse_relation()
            elif self._expect(EGIFTokenType.TILDE):
                self._parse_negation()
            elif self._expect(EGIFTokenType.LBRACKET):
                self._parse_bracket_construct()
            else:
                # Check if we're at a valid stopping point
                if self.current_token.type in [EGIFTokenType.RBRACKET, EGIFTokenType.THEN]:
                    break
                self._error(
                    f"Unexpected token: {self.current_token.value}",
                    "UNEXPECTED_TOKEN",
                    [
                        "EGIF expressions should start with relations (parentheses), negations (tilde), or brackets",
                        "Check for missing opening parenthesis for relations"
                    ],
                    "EGIF expressions are built from relations, negations, and coreference/scroll constructs"
                )
                self._advance()  # Skip problematic token
    
    def _parse_relation(self):
        """Parse a relation: (relation_name arg1 arg2 ...)"""
        self._trace("Parsing relation")
        
        if not self._consume(EGIFTokenType.LPAREN):
            self._error(
                "Expected opening parenthesis for relation",
                "MISSING_LPAREN",
                ["Relations must start with ("],
                "Relations in EGIF correspond to atomic graphs in existential graphs"
            )
            return
        
        # Parse relation name
        if not self._expect(EGIFTokenType.IDENTIFIER):
            self._error(
                "Expected relation name after opening parenthesis",
                "MISSING_RELATION_NAME",
                ["Provide a relation name like 'Person' or 'Loves'"],
                "The relation name identifies what kind of atomic graph this represents"
            )
            return
        
        relation_name = self.current_token.value
        self._trace(f"Found relation: {relation_name}")
        self._advance()
        
        # Parse arguments
        argument_entities = []
        while self.current_token and not self._expect(EGIFTokenType.RPAREN):
            entity_id = self._parse_argument()
            if entity_id:
                argument_entities.append(entity_id)
        
        if not self._consume(EGIFTokenType.RPAREN):
            self._error(
                "Expected closing parenthesis for relation",
                "MISSING_RPAREN",
                ["Add closing parenthesis ) to end the relation"],
                "Relations must be properly closed to define their scope"
            )
            return
        
        # Create predicate
        predicate = Predicate.create(
            name=relation_name,
            entities=argument_entities,
            properties={"context_id": self.parse_context.current_context_id}
        )
        self.predicates.append(predicate)
        
        self._trace(f"Created predicate: {relation_name} with {len(argument_entities)} arguments")
    
    def _parse_argument(self) -> Optional[EntityId]:
        """Parse a relation argument (defining label, bound label, or constant)."""
        if self._expect(EGIFTokenType.ASTERISK):
            return self._parse_defining_label()
        elif self._expect(EGIFTokenType.IDENTIFIER):
            return self._parse_bound_label()
        elif self._expect(EGIFTokenType.INTEGER):
            return self._parse_constant()
        elif self._expect(EGIFTokenType.QUOTED_NAME):
            return self._parse_quoted_constant()
        else:
            self._error(
                f"Expected argument (defining label *, identifier, or constant), got {self.current_token.value if self.current_token else 'EOF'}",
                "INVALID_ARGUMENT",
                [
                    "Use *label for new entities (defining labels)",
                    "Use label for existing entities (bound labels)",
                    "Use constants like 42 or \"John\""
                ],
                "Arguments connect the relation to lines of identity (entities) in the graph"
            )
            return None
    
    def _parse_defining_label(self) -> Optional[EntityId]:
        """Parse a defining label: *label_name"""
        self._trace("Parsing defining label")
        
        if not self._consume(EGIFTokenType.ASTERISK):
            return None
        
        if not self._expect(EGIFTokenType.IDENTIFIER):
            self._error(
                "Expected identifier after asterisk",
                "MISSING_LABEL_NAME",
                ["Provide a label name like *x or *person"],
                "Defining labels create new lines of identity (existential quantification)"
            )
            return None
        
        label_name = self.current_token.value
        self._advance()
        
        # Check if label already defined in this context
        if label_name in self.parse_context.defining_labels:
            self._error(
                f"Label '{label_name}' already defined in this context",
                "DUPLICATE_LABEL",
                [f"Use a different label name or reference existing label without asterisk: {label_name}"],
                "Each defining label creates a unique line of identity within its context"
            )
            return None
        
        # Create new entity
        entity = Entity.create(
            name=label_name,
            entity_type='variable',
            properties={"context_id": self.parse_context.current_context_id}
        )
        self.entities.append(entity)
        
        # Register in context
        self.parse_context.defining_labels[label_name] = entity.id
        
        self._trace(f"Created defining label: *{label_name} -> {entity.id}")
        return entity.id
    
    def _parse_bound_label(self) -> Optional[EntityId]:
        """Parse a bound label: label_name (reference to existing entity)"""
        if not self._expect(EGIFTokenType.IDENTIFIER):
            return None
        
        label_name = self.current_token.value
        self._advance()
        
        # Check if label is defined
        if label_name not in self.parse_context.defining_labels:
            self._error(
                f"Undefined label '{label_name}'",
                "UNDEFINED_LABEL",
                [
                    f"Define the label first with *{label_name}",
                    "Check spelling of the label name"
                ],
                "Bound labels must reference lines of identity that were previously defined"
            )
            return None
        
        # Mark as used
        self.parse_context.bound_labels.add(label_name)
        entity_id = self.parse_context.defining_labels[label_name]
        
        self._trace(f"Referenced bound label: {label_name} -> {entity_id}")
        return entity_id
    
    def _parse_constant(self) -> Optional[EntityId]:
        """Parse an integer constant."""
        if not self._expect(EGIFTokenType.INTEGER):
            return None
        
        value = self.current_token.value
        self._advance()
        
        # Create constant entity
        entity = Entity.create(
            name=value,
            entity_type='constant',
            properties={
                "context_id": self.parse_context.current_context_id,
                "value": int(value),
                "type": "integer"
            }
        )
        self.entities.append(entity)
        
        self._trace(f"Created integer constant: {value}")
        return entity.id
    
    def _parse_quoted_constant(self) -> Optional[EntityId]:
        """Parse a quoted string constant."""
        if not self._expect(EGIFTokenType.QUOTED_NAME):
            return None
        
        value = self.current_token.value
        self._advance()
        
        # Remove quotes
        unquoted_value = value[1:-1] if len(value) >= 2 else value
        
        # Create constant entity
        entity = Entity.create(
            name=unquoted_value,
            entity_type='constant',
            properties={
                "context_id": self.parse_context.current_context_id,
                "value": unquoted_value,
                "type": "string"
            }
        )
        self.entities.append(entity)
        
        self._trace(f"Created string constant: {unquoted_value}")
        return entity.id
    
    def _parse_negation(self):
        """Parse a negation: ~[expression]"""
        self._trace("Parsing negation (cut)")
        
        if not self._consume(EGIFTokenType.TILDE):
            return
        
        if not self._consume(EGIFTokenType.LBRACKET):
            self._error(
                "Expected opening bracket after tilde",
                "MISSING_LBRACKET_AFTER_TILDE",
                ["Negations must be followed by [expression]"],
                "Tilde creates a cut (oval enclosure) that reverses truth conditions"
            )
            return
        
        # Enter negation context
        old_context = self.parse_context
        self.parse_context = old_context.enter_negation()
        
        self._trace(f"Entered negation context (depth {self.parse_context.negation_depth})")
        
        # Parse contents
        self._parse_expression()
        
        if not self._consume(EGIFTokenType.RBRACKET):
            self._error(
                "Expected closing bracket for negation",
                "MISSING_RBRACKET_FOR_NEGATION",
                ["Add closing bracket ] to end the negation"],
                "Negations must be properly closed to define their scope"
            )
        
        # Exit negation context
        self.parse_context = old_context
        self._trace("Exited negation context")
    
    def _parse_bracket_construct(self):
        """Parse bracket constructs: coreference nodes or scroll notation."""
        if not self._expect(EGIFTokenType.LBRACKET):
            return
        
        # Look ahead to determine type
        next_token = self._peek()
        if next_token and next_token.type == EGIFTokenType.IF:
            self._parse_scroll()
        else:
            self._parse_coreference()
    
    def _parse_coreference(self):
        """Parse a coreference node: [label1 label2 ...]"""
        self._trace("Parsing coreference node")
        
        if not self._consume(EGIFTokenType.LBRACKET):
            return
        
        # Collect labels
        labels = []
        while self.current_token and not self._expect(EGIFTokenType.RBRACKET):
            if self._expect(EGIFTokenType.IDENTIFIER):
                label_name = self.current_token.value
                labels.append(label_name)
                self._advance()
            else:
                self._error(
                    f"Expected label name in coreference, got {self.current_token.value}",
                    "INVALID_COREFERENCE_CONTENT",
                    ["Coreference nodes should contain only label names"],
                    "Coreference nodes establish identity between lines of identity"
                )
                self._advance()
        
        if not self._consume(EGIFTokenType.RBRACKET):
            self._error(
                "Expected closing bracket for coreference",
                "MISSING_RBRACKET_FOR_COREFERENCE",
                ["Add closing bracket ] to end the coreference"],
                "Coreference nodes must be properly closed"
            )
            return
        
        # Validate labels exist
        valid_labels = []
        for label in labels:
            if label in self.parse_context.defining_labels:
                valid_labels.append(label)
                self.parse_context.bound_labels.add(label)
            else:
                self._error(
                    f"Undefined label '{label}' in coreference",
                    "UNDEFINED_LABEL_IN_COREFERENCE",
                    [f"Define the label first with *{label}"],
                    "Coreference can only connect existing lines of identity"
                )
        
        if len(valid_labels) < 2:
            self._error(
                "Coreference needs at least 2 valid labels",
                "INSUFFICIENT_COREFERENCE_LABELS",
                ["Provide at least 2 defined labels to establish identity"],
                "Coreference establishes that multiple lines represent the same entity"
            )
        else:
            self._trace(f"Created coreference: {' = '.join(valid_labels)}")
            # TODO: Create ligature structure when implementing full EG-HG integration
    
    def _parse_scroll(self):
        """Parse scroll notation: [If condition [Then conclusion]]"""
        self._trace("Parsing scroll notation (conditional)")
        
        if not self._consume(EGIFTokenType.LBRACKET):
            return
        
        if not self._consume(EGIFTokenType.IF):
            self._error(
                "Expected 'If' keyword in scroll notation",
                "MISSING_IF_KEYWORD",
                ["Scroll notation must start with [If"],
                "Scroll notation represents implication using double cuts"
            )
            return
        
        # Enter scroll context for condition
        old_context = self.parse_context
        self.parse_context = old_context.enter_scroll()
        
        self._trace("Parsing scroll condition")
        
        # Parse condition
        self._parse_expression()
        
        # Expect [Then
        if not self._consume(EGIFTokenType.LBRACKET):
            self._error(
                "Expected opening bracket before 'Then'",
                "MISSING_LBRACKET_BEFORE_THEN",
                ["Add [ before Then keyword"],
                "Scroll notation requires nested brackets for the conclusion"
            )
        
        if not self._consume(EGIFTokenType.THEN):
            self._error(
                "Expected 'Then' keyword in scroll notation",
                "MISSING_THEN_KEYWORD",
                ["Add 'Then' keyword after condition"],
                "Scroll notation separates condition and conclusion with 'Then'"
            )
        
        self._trace("Parsing scroll conclusion")
        
        # Parse conclusion
        self._parse_expression()
        
        # Close conclusion bracket
        if not self._consume(EGIFTokenType.RBRACKET):
            self._error(
                "Expected closing bracket after conclusion",
                "MISSING_RBRACKET_AFTER_CONCLUSION",
                ["Add ] to close the conclusion"],
                "Scroll conclusions must be properly closed"
            )
        
        # Close scroll bracket
        if not self._consume(EGIFTokenType.RBRACKET):
            self._error(
                "Expected closing bracket for scroll",
                "MISSING_RBRACKET_FOR_SCROLL",
                ["Add ] to close the scroll notation"],
                "Scroll notation must be properly closed"
            )
        
        # Exit scroll context
        self.parse_context = old_context
        self._trace("Completed scroll notation")


def parse_egif(source: str, educational_mode: bool = True) -> EGIFParseResult:
    """
    Convenience function to parse EGIF source code.
    
    Args:
        source: EGIF source code
        educational_mode: Whether to include educational feedback
        
    Returns:
        EGIFParseResult containing the parsed structures and any errors
    """
    parser = EGIFParser(educational_mode)
    return parser.parse(source)


# Example usage and testing
if __name__ == "__main__":
    # Test cases for educational demonstration
    test_cases = [
        # Simple relation
        "(Person *x)",
        
        # Multiple relations with shared entity
        "(Person *x) (Mortal x)",
        
        # Negation
        "~[(Person x)]",
        
        # Scroll notation
        "[If (Person *x) [Then (Mortal x)]]",
        
        # Coreference
        "(Person *x) (Mortal *y) [x y]",
        
        # Complex example
        "(Person *x) ~[(Mortal x)]",
        
        # Error cases
        "(Person &x)",  # Lexical error
        "(Person *x) (Mortal y)",  # Undefined label
        "(Person *x *x)",  # Duplicate label
        "~(Person x)",  # Missing brackets after tilde
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("=" * 50)
        
        result = parse_egif(test_case)
        
        print("Educational Trace:")
        for trace_line in result.educational_trace:
            print(f"  {trace_line}")
        
        print(f"\nResults:")
        print(f"  Entities: {len(result.entities)}")
        for entity in result.entities:
            print(f"    {entity}")
        
        print(f"  Predicates: {len(result.predicates)}")
        for predicate in result.predicates:
            print(f"    {predicate}")
        
        if result.errors:
            print(f"\nErrors: {len(result.errors)}")
            for error in result.errors:
                print(f"  {error.message}")
                if error.educational_note:
                    print(f"    Note: {error.educational_note}")
                if error.suggestions:
                    for suggestion in error.suggestions:
                        print(f"    Suggestion: {suggestion}")

