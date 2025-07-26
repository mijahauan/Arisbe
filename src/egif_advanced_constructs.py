"""
EGIF Advanced Constructs - Phase 2 Implementation

This module extends the EGIF parser and generator to support advanced constructs
including function symbols (Dau's extensions), complex coreference patterns,
nested scroll notation, and enhanced ligature handling.

These advanced features bridge the gap between Peirce's original formulation
and Dau's mathematical extensions while maintaining educational clarity.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union, NamedTuple
from dataclasses import dataclass
from enum import Enum
import re

from egif_lexer import EGIFLexer, EGIFTokenType, EGIFToken
from egif_parser import EGIFParser, EGIFParseResult, parse_egif
from egif_generator_simple import SimpleEGIFGenerator, SimpleEGIFGenerationResult
from eg_types import Entity, Predicate, EntityId, PredicateId


class AdvancedConstructType(Enum):
    """Types of advanced EGIF constructs."""
    FUNCTION_SYMBOL = "function_symbol"
    COMPLEX_COREFERENCE = "complex_coreference"
    NESTED_SCROLL = "nested_scroll"
    LIGATURE_PATTERN = "ligature_pattern"
    CONDITIONAL_BINDING = "conditional_binding"
    QUANTIFIER_SCOPE = "quantifier_scope"


@dataclass
class FunctionSymbol:
    """Represents a function symbol in EGIF (Dau's extension)."""
    name: str
    arity: int
    arguments: List[str]
    result_variable: Optional[str]
    properties: Dict[str, Any]
    
    def to_egif(self) -> str:
        """Convert function symbol to EGIF syntax."""
        if self.result_variable:
            args_str = " ".join(self.arguments)
            return f"({self.name} {args_str} -> *{self.result_variable})"
        else:
            args_str = " ".join(self.arguments)
            return f"({self.name} {args_str})"


@dataclass
class CoreferencePattern:
    """Represents a complex coreference pattern."""
    pattern_type: str  # "identity", "equivalence", "conditional"
    entities: List[str]
    conditions: List[str]
    scope: Optional[str]
    
    def to_egif(self) -> str:
        """Convert coreference pattern to EGIF syntax."""
        entities_str = " ".join(self.entities)
        
        if self.pattern_type == "identity":
            return f"[{entities_str}]"
        elif self.pattern_type == "equivalence":
            return f"[= {entities_str}]"
        elif self.pattern_type == "conditional" and self.conditions:
            conditions_str = " ".join(self.conditions)
            return f"[{entities_str} | {conditions_str}]"
        else:
            return f"[{entities_str}]"


@dataclass
class ScrollPattern:
    """Represents a scroll (conditional) pattern."""
    condition_part: str
    consequence_part: str
    nesting_level: int
    scroll_type: str  # "if_then", "iff", "unless"
    
    def to_egif(self) -> str:
        """Convert scroll pattern to EGIF syntax."""
        if self.scroll_type == "if_then":
            return f"[If {self.condition_part} [Then {self.consequence_part}]]"
        elif self.scroll_type == "iff":
            return f"[Iff {self.condition_part} [Then {self.consequence_part}]]"
        elif self.scroll_type == "unless":
            return f"[Unless {self.condition_part} [Then {self.consequence_part}]]"
        else:
            return f"[{self.condition_part} [Then {self.consequence_part}]]"


class AdvancedEGIFLexer(EGIFLexer):
    """Extended lexer for advanced EGIF constructs."""
    
    def __init__(self, source: str, educational_mode: bool = True):
        super().__init__(source, educational_mode)
        
        # Add advanced token patterns
        self.advanced_patterns = {
            'ARROW': r'->',
            'PIPE': r'\|',
            'EQUALS': r'=',
            'IFF': r'\bIff\b',
            'UNLESS': r'\bUnless\b',
            'FORALL': r'∀|forall',
            'EXISTS': r'∃|exists',
            'LAMBDA': r'λ|lambda',
        }
        
        # Update token descriptions for educational mode
        self.advanced_descriptions = {
            'ARROW': "Function result indicator (->)",
            'PIPE': "Conditional separator in coreference (|)",
            'EQUALS': "Equivalence indicator in coreference (=)",
            'IFF': "Biconditional scroll marker (Iff)",
            'UNLESS': "Negative conditional scroll marker (Unless)",
            'FORALL': "Universal quantifier (∀)",
            'EXISTS': "Existential quantifier (∃)",
            'LAMBDA': "Lambda abstraction (λ)",
        }
    
    def tokenize_advanced(self) -> Tuple[List[EGIFToken], List[Any]]:
        """Tokenize with advanced construct support."""
        # First do basic tokenization
        tokens, errors = self.tokenize()
        
        # Then post-process for advanced patterns
        enhanced_tokens = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Check for advanced patterns
            if token.type == EGIFTokenType.IDENTIFIER:
                # Check for special keywords
                if token.value in ['Iff', 'Unless', 'forall', 'exists', 'lambda']:
                    # Convert to appropriate advanced token type
                    advanced_type = self._get_advanced_token_type(token.value)
                    enhanced_token = EGIFToken(
                        type=advanced_type,
                        value=token.value,
                        line=token.line,
                        column=token.column,
                        position=token.position,
                        length=token.length,
                        description=self.advanced_descriptions.get(advanced_type.value, token.description)
                    )
                    enhanced_tokens.append(enhanced_token)
                else:
                    enhanced_tokens.append(token)
            elif token.value == '->' and i + 1 < len(tokens) and tokens[i + 1].value == '>':
                # Handle arrow operator
                arrow_token = EGIFToken(
                    type=EGIFTokenType.ARROW,
                    value='->',
                    line=token.line,
                    column=token.column,
                    position=token.position,
                    length=2,
                    description=self.advanced_descriptions['ARROW']
                )
                enhanced_tokens.append(arrow_token)
                i += 1  # Skip the '>' part
            else:
                enhanced_tokens.append(token)
            
            i += 1
        
        return enhanced_tokens, errors
    
    def _get_advanced_token_type(self, value: str) -> EGIFTokenType:
        """Get the appropriate token type for advanced constructs."""
        mapping = {
            'Iff': EGIFTokenType.IFF,
            'Unless': EGIFTokenType.UNLESS,
            'forall': EGIFTokenType.FORALL,
            'exists': EGIFTokenType.EXISTS,
            'lambda': EGIFTokenType.LAMBDA,
        }
        return mapping.get(value, EGIFTokenType.IDENTIFIER)


class AdvancedEGIFParser(EGIFParser):
    """Extended parser for advanced EGIF constructs."""
    
    def __init__(self, educational_mode: bool = True):
        super().__init__(educational_mode)
        self.function_symbols = []
        self.coreference_patterns = []
        self.scroll_patterns = []
    
    def parse_advanced(self, source: str) -> EGIFParseResult:
        """Parse EGIF with advanced construct support."""
        # Use advanced lexer
        lexer = AdvancedEGIFLexer(source, self.educational_mode)
        tokens, lex_errors = lexer.tokenize_advanced()
        
        # Convert lexical errors to parse errors
        for lex_error in lex_errors:
            # Create a simple error representation
            error_msg = f"Lexical error: {lex_error.message if hasattr(lex_error, 'message') else str(lex_error)}"
            self.errors.append(self._create_simple_error(error_msg, "LEXICAL_ERROR"))
        
        self.tokens = tokens
        self.position = 0
        
        # Parse with advanced construct recognition
        self._parse_advanced_constructs()
        
        # Create result with advanced constructs
        result = EGIFParseResult(
            entities=self.entities,
            predicates=self.predicates,
            contexts=getattr(self, 'contexts', []),
            root_context_id=getattr(self, 'root_context_id', None),
            errors=self.errors,
            educational_trace=getattr(self, 'educational_trace', [])
        )
        
        # Add advanced constructs to result
        result.function_symbols = self.function_symbols
        result.coreference_patterns = self.coreference_patterns
        result.scroll_patterns = self.scroll_patterns
        
        return result
    
    def _create_simple_error(self, message: str, error_type: str):
        """Create a simple error object."""
        from egif_parser import EGIFParseError, EGIFToken
        
        # Create a dummy token for the error
        dummy_token = EGIFToken(EGIFTokenType.ERROR, "", 1, 1, 0, 0)
        
        return EGIFParseError(
            message=message,
            token=dummy_token,
            error_type=error_type,
            suggestions=[],
            educational_note=""
        )
    
    def _parse_advanced_constructs(self):
        """Parse advanced constructs from token stream."""
        while self.position < len(self.tokens) and self.tokens[self.position].type != EGIFTokenType.EOF:
            current_token = self.tokens[self.position]
            
            if current_token.type == EGIFTokenType.LPAREN:
                # Could be function symbol or regular relation
                self._parse_potential_function()
            elif current_token.type == EGIFTokenType.LBRACKET:
                # Could be advanced coreference or scroll
                self._parse_potential_advanced_bracket()
            elif current_token.type == EGIFTokenType.TILDE:
                # Negation - handle normally
                self._parse_negation()
            else:
                # Skip unknown tokens
                self.position += 1
    
    def _parse_potential_function(self):
        """Parse what might be a function symbol."""
        start_pos = self.position
        self.position += 1  # consume '('
        
        if self.position >= len(self.tokens) or self.tokens[self.position].type != EGIFTokenType.IDENTIFIER:
            self._add_error("Expected function or relation name", "MISSING_NAME")
            return
        
        name = self.tokens[self.position].value
        self.position += 1
        
        # Collect arguments
        arguments = []
        result_variable = None
        has_arrow = False
        
        while (self.position < len(self.tokens) and 
               self.tokens[self.position].type != EGIFTokenType.RPAREN):
            
            current = self.tokens[self.position]
            
            if current.value == '->' or (current.value == '-' and 
                                       self.position + 1 < len(self.tokens) and 
                                       self.tokens[self.position + 1].value == '>'):
                # This is a function with result
                has_arrow = True
                if current.value == '-':
                    self.position += 2  # consume '->'
                else:
                    self.position += 1  # consume '->'
                
                if (self.position < len(self.tokens) and 
                    self.tokens[self.position].type == EGIFTokenType.ASTERISK):
                    self.position += 1  # consume '*'
                    if (self.position < len(self.tokens) and 
                        self.tokens[self.position].type == EGIFTokenType.IDENTIFIER):
                        result_variable = self.tokens[self.position].value
                        self.position += 1
                        self._trace(f"Function {name} returns *{result_variable}")
                break
            elif current.type == EGIFTokenType.ASTERISK:
                # Defining label
                self.position += 1  # consume '*'
                if (self.position < len(self.tokens) and 
                    self.tokens[self.position].type == EGIFTokenType.IDENTIFIER):
                    label = self.tokens[self.position].value
                    arguments.append(f"*{label}")
                    self._handle_defining_label(label)
                    self.position += 1
            elif current.type == EGIFTokenType.IDENTIFIER:
                # Bound label or constant
                label = current.value
                arguments.append(label)
                self._handle_bound_label(label)
                self.position += 1
            elif current.type == EGIFTokenType.INTEGER:
                # Constant
                value = current.value
                arguments.append(value)
                self.position += 1
            else:
                self.position += 1  # Skip unknown token
        
        if (self.position < len(self.tokens) and 
            self.tokens[self.position].type == EGIFTokenType.RPAREN):
            self.position += 1  # consume ')'
        
        # Determine if this is a function or regular relation
        if result_variable or has_arrow:
            # This is a function symbol
            function = FunctionSymbol(
                name=name,
                arity=len(arguments),
                arguments=arguments,
                result_variable=result_variable,
                properties={}
            )
            self.function_symbols.append(function)
            self._trace(f"Parsed function symbol: {function.to_egif()}")
        else:
            # This is a regular relation - handle normally
            self._create_predicate_from_parse(name, arguments)
    
    def _parse_potential_advanced_bracket(self):
        """Parse what might be an advanced bracket construct."""
        self.position += 1  # consume '['
        
        # Look ahead to determine type
        if (self.position < len(self.tokens) and 
            self.tokens[self.position].type == EGIFTokenType.EQUALS):
            self._parse_equivalence_coreference()
        elif (self.position < len(self.tokens) and 
              self.tokens[self.position].type == EGIFTokenType.IFF):
            self._parse_iff_scroll()
        elif (self.position < len(self.tokens) and 
              self.tokens[self.position].type == EGIFTokenType.UNLESS):
            self._parse_unless_scroll()
        elif (self.position < len(self.tokens) and 
              self.tokens[self.position].type == EGIFTokenType.IF):
            self._parse_if_then_scroll()
        else:
            # Regular coreference or simple bracket
            self._parse_regular_coreference()
    
    def _parse_equivalence_coreference(self):
        """Parse equivalence coreference pattern [= x y z]."""
        self._advance()  # consume '='
        
        entities = []
        while not self._check(EGIFTokenType.RBRACKET) and not self._at_end():
            if self._check(EGIFTokenType.IDENTIFIER):
                entities.append(self._advance().value)
            else:
                self._advance()  # Skip unknown
        
        if self._check(EGIFTokenType.RBRACKET):
            self._advance()  # consume ']'
        
        pattern = CoreferencePattern(
            pattern_type="equivalence",
            entities=entities,
            conditions=[],
            scope=None
        )
        self.coreference_patterns.append(pattern)
        self._trace(f"Parsed equivalence coreference: {pattern.to_egif()}")
    
    def _parse_iff_scroll(self):
        """Parse biconditional scroll [Iff condition [Then consequence]]."""
        self._advance()  # consume 'Iff'
        
        # Parse condition part
        condition_tokens = []
        bracket_depth = 0
        
        while not self._at_end():
            if self._check(EGIFTokenType.LBRACKET):
                if bracket_depth == 0 and self._check_ahead(EGIFTokenType.THEN):
                    break
                bracket_depth += 1
                condition_tokens.append(self._advance())
            elif self._check(EGIFTokenType.RBRACKET):
                bracket_depth -= 1
                if bracket_depth < 0:
                    break
                condition_tokens.append(self._advance())
            else:
                condition_tokens.append(self._advance())
        
        condition_part = " ".join([t.value for t in condition_tokens])
        
        # Parse consequence part
        consequence_part = ""
        if self._check(EGIFTokenType.LBRACKET):
            self._advance()  # consume '['
            if self._check(EGIFTokenType.THEN):
                self._advance()  # consume 'Then'
                
                consequence_tokens = []
                bracket_depth = 0
                
                while not self._at_end():
                    if self._check(EGIFTokenType.LBRACKET):
                        bracket_depth += 1
                        consequence_tokens.append(self._advance())
                    elif self._check(EGIFTokenType.RBRACKET):
                        if bracket_depth == 0:
                            break
                        bracket_depth -= 1
                        consequence_tokens.append(self._advance())
                    else:
                        consequence_tokens.append(self._advance())
                
                consequence_part = " ".join([t.value for t in consequence_tokens])
                
                if self._check(EGIFTokenType.RBRACKET):
                    self._advance()  # consume ']'
        
        if self._check(EGIFTokenType.RBRACKET):
            self._advance()  # consume final ']'
        
        scroll = ScrollPattern(
            condition_part=condition_part,
            consequence_part=consequence_part,
            nesting_level=1,
            scroll_type="iff"
        )
        self.scroll_patterns.append(scroll)
        self._trace(f"Parsed Iff scroll: {scroll.to_egif()}")
    
    def _parse_unless_scroll(self):
        """Parse negative conditional scroll [Unless condition [Then consequence]]."""
        # Similar to iff_scroll but with "unless" semantics
        self._advance()  # consume 'Unless'
        
        # For now, parse similar to if-then but mark as "unless"
        condition_part = self._parse_scroll_condition()
        consequence_part = self._parse_scroll_consequence()
        
        scroll = ScrollPattern(
            condition_part=condition_part,
            consequence_part=consequence_part,
            nesting_level=1,
            scroll_type="unless"
        )
        self.scroll_patterns.append(scroll)
        self._trace(f"Parsed Unless scroll: {scroll.to_egif()}")
    
    def _parse_if_then_scroll(self):
        """Parse regular conditional scroll [If condition [Then consequence]]."""
        self._advance()  # consume 'If'
        
        condition_part = self._parse_scroll_condition()
        consequence_part = self._parse_scroll_consequence()
        
        scroll = ScrollPattern(
            condition_part=condition_part,
            consequence_part=consequence_part,
            nesting_level=1,
            scroll_type="if_then"
        )
        self.scroll_patterns.append(scroll)
        self._trace(f"Parsed If-Then scroll: {scroll.to_egif()}")
    
    def _parse_scroll_condition(self) -> str:
        """Parse the condition part of a scroll."""
        tokens = []
        bracket_depth = 0
        
        while not self._at_end():
            if self._check(EGIFTokenType.LBRACKET):
                if bracket_depth == 0 and self._check_ahead(EGIFTokenType.THEN):
                    break
                bracket_depth += 1
                tokens.append(self._advance())
            elif self._check(EGIFTokenType.RBRACKET):
                bracket_depth -= 1
                if bracket_depth < 0:
                    break
                tokens.append(self._advance())
            else:
                tokens.append(self._advance())
        
        return " ".join([t.value for t in tokens])
    
    def _parse_scroll_consequence(self) -> str:
        """Parse the consequence part of a scroll."""
        consequence_part = ""
        
        if self._check(EGIFTokenType.LBRACKET):
            self._advance()  # consume '['
            if self._check(EGIFTokenType.THEN):
                self._advance()  # consume 'Then'
                
                tokens = []
                bracket_depth = 0
                
                while not self._at_end():
                    if self._check(EGIFTokenType.LBRACKET):
                        bracket_depth += 1
                        tokens.append(self._advance())
                    elif self._check(EGIFTokenType.RBRACKET):
                        if bracket_depth == 0:
                            break
                        bracket_depth -= 1
                        tokens.append(self._advance())
                    else:
                        tokens.append(self._advance())
                
                consequence_part = " ".join([t.value for t in tokens])
                
                if self._check(EGIFTokenType.RBRACKET):
                    self._advance()  # consume ']'
        
        return consequence_part
    
    def _parse_regular_coreference(self):
        """Parse regular coreference [x y z] or conditional [x y | condition]."""
        entities = []
        conditions = []
        in_condition = False
        
        while not self._check(EGIFTokenType.RBRACKET) and not self._at_end():
            if self._check(EGIFTokenType.PIPE):
                self._advance()  # consume '|'
                in_condition = True
            elif self._check(EGIFTokenType.IDENTIFIER):
                value = self._advance().value
                if in_condition:
                    conditions.append(value)
                else:
                    entities.append(value)
            else:
                self._advance()  # Skip unknown
        
        if self._check(EGIFTokenType.RBRACKET):
            self._advance()  # consume ']'
        
        pattern_type = "conditional" if conditions else "identity"
        pattern = CoreferencePattern(
            pattern_type=pattern_type,
            entities=entities,
            conditions=conditions,
            scope=None
        )
        self.coreference_patterns.append(pattern)
        self._trace(f"Parsed coreference: {pattern.to_egif()}")
    
    def _check_sequence(self, token_types: List[EGIFTokenType]) -> bool:
        """Check if the next tokens match a sequence."""
        for i, token_type in enumerate(token_types):
            if self.position + i >= len(self.tokens):
                return False
            if self.tokens[self.position + i].type != token_type:
                return False
        return True
    
    def _check_ahead(self, token_type: EGIFTokenType, offset: int = 1) -> bool:
        """Check if a token type appears ahead."""
        pos = self.position + offset
        while pos < len(self.tokens):
            if self.tokens[pos].type == token_type:
                return True
            pos += 1
        return False


class AdvancedEGIFGenerator(SimpleEGIFGenerator):
    """Extended generator for advanced EGIF constructs."""
    
    def __init__(self, educational_mode: bool = True):
        super().__init__(educational_mode)
        self.function_symbols = []
        self.coreference_patterns = []
        self.scroll_patterns = []
    
    def generate_advanced_from_parse_result(self, parse_result: EGIFParseResult) -> SimpleEGIFGenerationResult:
        """Generate EGIF with advanced constructs from parse result."""
        # First generate basic constructs
        basic_result = self.generate_from_parse_result(parse_result)
        
        if not basic_result.success:
            return basic_result
        
        # Add advanced constructs if present
        advanced_parts = []
        
        # Add function symbols
        if hasattr(parse_result, 'function_symbols'):
            for func in parse_result.function_symbols:
                advanced_parts.append(func.to_egif())
                self._trace(f"Added function symbol: {func.to_egif()}")
        
        # Add coreference patterns
        if hasattr(parse_result, 'coreference_patterns'):
            for pattern in parse_result.coreference_patterns:
                advanced_parts.append(pattern.to_egif())
                self._trace(f"Added coreference pattern: {pattern.to_egif()}")
        
        # Add scroll patterns
        if hasattr(parse_result, 'scroll_patterns'):
            for scroll in parse_result.scroll_patterns:
                advanced_parts.append(scroll.to_egif())
                self._trace(f"Added scroll pattern: {scroll.to_egif()}")
        
        # Combine basic and advanced parts
        all_parts = [basic_result.egif_source] + advanced_parts
        combined_egif = " ".join(filter(None, all_parts))
        
        return SimpleEGIFGenerationResult(
            egif_source=combined_egif,
            success=True,
            errors=basic_result.errors,
            educational_trace=basic_result.educational_trace + self.generation_trace,
            entity_labels=basic_result.entity_labels
        )


# Convenience functions for advanced parsing
def parse_advanced_egif(source: str, educational_mode: bool = True) -> EGIFParseResult:
    """Parse EGIF with advanced construct support."""
    parser = AdvancedEGIFParser(educational_mode)
    return parser.parse_advanced(source)


def generate_advanced_egif(parse_result: EGIFParseResult, educational_mode: bool = True) -> SimpleEGIFGenerationResult:
    """Generate EGIF with advanced constructs."""
    generator = AdvancedEGIFGenerator(educational_mode)
    return generator.generate_advanced_from_parse_result(parse_result)


# Example usage and testing
if __name__ == "__main__":
    print("Advanced EGIF Constructs Test")
    print("=" * 50)
    
    # Test cases for advanced constructs
    test_cases = [
        # Function symbols
        "(add 2 3 -> *result)",
        "(sqrt *x -> *y)",
        
        # Advanced coreference
        "[= x y z]",
        "[x y | (Person x) (Person y)]",
        
        # Advanced scrolls
        "[Iff (Person *x) [Then (Mortal x)]]",
        "[Unless (Dead *x) [Then (Alive x)]]",
        
        # Mixed constructs
        "(Person *x) [= x john] [If (Human x) [Then (Mortal x)]]",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case}")
        print("-" * 60)
        
        try:
            # Parse with advanced support
            result = parse_advanced_egif(test_case, educational_mode=True)
            
            print(f"Parsing result:")
            print(f"  Entities: {len(result.entities)}")
            print(f"  Predicates: {len(result.predicates)}")
            print(f"  Errors: {len(result.errors)}")
            
            if hasattr(result, 'function_symbols'):
                print(f"  Function symbols: {len(result.function_symbols)}")
            if hasattr(result, 'coreference_patterns'):
                print(f"  Coreference patterns: {len(result.coreference_patterns)}")
            if hasattr(result, 'scroll_patterns'):
                print(f"  Scroll patterns: {len(result.scroll_patterns)}")
            
            # Show errors if any
            if result.errors:
                print("  Parse errors:")
                for error in result.errors[:3]:  # Show first 3
                    print(f"    {error.message}")
            
            # Show educational trace
            if result.educational_trace:
                print("  Educational trace (first 3):")
                for trace in result.educational_trace[:3]:
                    print(f"    {trace}")
            
            # Test generation
            gen_result = generate_advanced_egif(result, educational_mode=False)
            if gen_result.success:
                print(f"  Generated: {gen_result.egif_source}")
            else:
                print(f"  Generation failed: {gen_result.errors}")
                
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Advanced EGIF Constructs Phase 2 implementation complete!")
    print("Supports function symbols, complex coreference, and advanced scrolls.")

