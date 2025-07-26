"""
EGIF Error Handling Framework - Educational-First Design

This module provides comprehensive error handling for EGIF processing with
educational feedback designed to help users understand EGIF syntax rules
and their relationship to existential graph principles.

The error handling framework integrates with both lexical and parsing
components to provide consistent, educational error reporting throughout
the EGIF processing pipeline.

Author: Manus AI
Date: January 2025
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import re

from egif_lexer import EGIFLexError, EGIFToken, EGIFTokenType
from egif_parser import EGIFParseError


class EGIFErrorSeverity(Enum):
    """Severity levels for EGIF errors."""
    INFO = "INFO"           # Informational messages
    WARNING = "WARNING"     # Potential issues that don't prevent parsing
    ERROR = "ERROR"         # Errors that prevent successful parsing
    CRITICAL = "CRITICAL"   # Critical errors that indicate system problems


class EGIFErrorCategory(Enum):
    """Categories of EGIF errors for educational organization."""
    LEXICAL = "LEXICAL"                 # Tokenization errors
    SYNTAX = "SYNTAX"                   # Grammar and structure errors
    SEMANTIC = "SEMANTIC"               # Meaning and logic errors
    CONTEXT = "CONTEXT"                 # Scoping and context errors
    EDUCATIONAL = "EDUCATIONAL"         # Educational guidance and tips
    SYSTEM = "SYSTEM"                   # Internal system errors


@dataclass
class EGIFErrorContext:
    """Context information for error reporting."""
    source_line: str = ""
    line_number: int = 0
    column_number: int = 0
    surrounding_context: List[str] = field(default_factory=list)
    parse_stack: List[str] = field(default_factory=list)
    available_labels: List[str] = field(default_factory=list)
    negation_depth: int = 0
    in_scroll: bool = False


@dataclass
class EGIFEducationalNote:
    """Educational information about EGIF concepts."""
    concept: str
    explanation: str
    examples: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    graphical_mapping: str = ""


@dataclass
class EGIFErrorReport:
    """Comprehensive error report with educational content."""
    severity: EGIFErrorSeverity
    category: EGIFErrorCategory
    message: str
    error_code: str
    context: EGIFErrorContext
    suggestions: List[str] = field(default_factory=list)
    educational_note: Optional[EGIFEducationalNote] = None
    quick_fixes: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    
    def format_for_display(self, include_educational: bool = True) -> str:
        """Format the error report for user display."""
        lines = []
        
        # Header
        lines.append(f"{self.severity.value}: {self.message}")
        lines.append(f"Error Code: {self.error_code}")
        
        # Context
        if self.context.line_number > 0:
            lines.append(f"Location: Line {self.context.line_number}, Column {self.context.column_number}")
        
        if self.context.source_line:
            lines.append(f"Source: {self.context.source_line}")
            if self.context.column_number > 0:
                pointer = " " * (self.context.column_number - 1) + "^"
                lines.append(f"        {pointer}")
        
        # Suggestions
        if self.suggestions:
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  • {suggestion}")
        
        # Quick fixes
        if self.quick_fixes:
            lines.append("Quick Fixes:")
            for fix in self.quick_fixes:
                lines.append(f"  → {fix}")
        
        # Educational content
        if include_educational and self.educational_note:
            lines.append("\nEducational Note:")
            lines.append(f"  Concept: {self.educational_note.concept}")
            lines.append(f"  {self.educational_note.explanation}")
            
            if self.educational_note.graphical_mapping:
                lines.append(f"  Graphical Mapping: {self.educational_note.graphical_mapping}")
            
            if self.educational_note.examples:
                lines.append("  Examples:")
                for example in self.educational_note.examples:
                    lines.append(f"    {example}")
        
        return "\n".join(lines)


class EGIFErrorHandler:
    """
    Comprehensive error handler for EGIF processing with educational focus.
    
    This handler provides:
    - Consistent error reporting across lexical and parsing phases
    - Educational explanations of EGIF concepts
    - Contextual suggestions based on error patterns
    - Integration with existing error handling frameworks
    """
    
    # Educational notes for common EGIF concepts
    EDUCATIONAL_NOTES = {
        "defining_labels": EGIFEducationalNote(
            concept="Defining Labels",
            explanation="Defining labels (*label) create new lines of identity, representing existential quantification in existential graphs.",
            examples=[
                "*x creates a new entity named 'x'",
                "(Person *john) introduces a new person",
                "*item can be referenced later as 'item'"
            ],
            graphical_mapping="Lines of identity that start at the relation and extend outward",
            related_concepts=["bound_labels", "existential_quantification", "lines_of_identity"]
        ),
        
        "bound_labels": EGIFEducationalNote(
            concept="Bound Labels",
            explanation="Bound labels (label without *) reference existing lines of identity created by defining labels.",
            examples=[
                "x references the entity created by *x",
                "(Mortal person) uses the entity from (Person *person)",
                "Labels must be defined before they can be referenced"
            ],
            graphical_mapping="Connections to existing lines of identity",
            related_concepts=["defining_labels", "coreference", "scoping"]
        ),
        
        "negation": EGIFEducationalNote(
            concept="Negation (Cuts)",
            explanation="Negation in EGIF uses ~[...] to represent cuts (oval enclosures) that reverse truth conditions.",
            examples=[
                "~[(Person x)] means 'x is not a person'",
                "~[~[(Mortal x)]] is double negation",
                "Cuts create new contexts with reversed truth values"
            ],
            graphical_mapping="Oval enclosures that reverse the truth of their contents",
            related_concepts=["contexts", "double_cuts", "truth_conditions"]
        ),
        
        "coreference": EGIFEducationalNote(
            concept="Coreference Nodes",
            explanation="Coreference nodes [label1 label2] establish identity between different lines of identity.",
            examples=[
                "[x y] means x and y refer to the same entity",
                "[person author] connects two different relations",
                "Establishes ligatures in the hypergraph representation"
            ],
            graphical_mapping="Ligatures that connect multiple lines of identity",
            related_concepts=["identity", "ligatures", "unification"]
        ),
        
        "scroll_notation": EGIFEducationalNote(
            concept="Scroll Notation",
            explanation="Scroll notation [If condition [Then conclusion]] represents implication using double cuts.",
            examples=[
                "[If (Person *x) [Then (Mortal x)]] means 'if x is a person, then x is mortal'",
                "Equivalent to ~[condition ~[conclusion]]",
                "Represents conditional relationships"
            ],
            graphical_mapping="Double cuts arranged to create implication pattern",
            related_concepts=["implication", "double_cuts", "conditionals"]
        ),
        
        "relations": EGIFEducationalNote(
            concept="Relations",
            explanation="Relations (name arg1 arg2...) represent atomic graphs with named predicates and arguments.",
            examples=[
                "(Person john) - unary relation",
                "(Loves mary john) - binary relation",
                "(Between x y z) - ternary relation"
            ],
            graphical_mapping="Atomic graphs with pegs connecting to lines of identity",
            related_concepts=["atomic_graphs", "predicates", "arity"]
        )
    }
    
    # Error code patterns and their educational mappings
    ERROR_PATTERNS = {
        "UNDEFINED_LABEL": {
            "concept": "bound_labels",
            "common_fixes": [
                "Define the label first with *{label}",
                "Check spelling of the label name",
                "Ensure the label is in scope"
            ]
        },
        
        "DUPLICATE_LABEL": {
            "concept": "defining_labels",
            "common_fixes": [
                "Use a different label name",
                "Reference the existing label without asterisk",
                "Check if you meant to create a coreference"
            ]
        },
        
        "MISSING_BRACKETS": {
            "concept": "negation",
            "common_fixes": [
                "Add square brackets after tilde: ~[...]",
                "Ensure proper nesting of brackets",
                "Check for matching opening and closing brackets"
            ]
        },
        
        "INVALID_COREFERENCE": {
            "concept": "coreference",
            "common_fixes": [
                "Ensure all labels in coreference are defined",
                "Use at least 2 labels in coreference nodes",
                "Check label spelling and availability"
            ]
        },
        
        "SCROLL_SYNTAX": {
            "concept": "scroll_notation",
            "common_fixes": [
                "Use proper scroll syntax: [If condition [Then conclusion]]",
                "Ensure nested brackets for Then clause",
                "Check for proper keyword capitalization"
            ]
        }
    }
    
    def __init__(self, educational_mode: bool = True):
        """
        Initialize the error handler.
        
        Args:
            educational_mode: Whether to include educational content in error reports
        """
        self.educational_mode = educational_mode
        self.error_history = []
        self.context_stack = []
    
    def handle_lexical_error(self, lex_error: EGIFLexError, source_lines: List[str]) -> EGIFErrorReport:
        """Convert a lexical error to a comprehensive error report."""
        context = self._build_context_from_position(
            lex_error.line, lex_error.column, source_lines
        )
        
        # Determine error category and educational content
        category = EGIFErrorCategory.LEXICAL
        educational_note = None
        
        if self.educational_mode:
            educational_note = self._get_educational_note_for_lexical_error(lex_error)
        
        # Generate quick fixes
        quick_fixes = self._generate_quick_fixes_for_lexical_error(lex_error)
        
        error_report = EGIFErrorReport(
            severity=EGIFErrorSeverity.ERROR,
            category=category,
            message=lex_error.message,
            error_code=lex_error.error_type,
            context=context,
            suggestions=lex_error.suggestions,
            educational_note=educational_note,
            quick_fixes=quick_fixes
        )
        
        self.error_history.append(error_report)
        return error_report
    
    def handle_parse_error(self, parse_error: EGIFParseError, source_lines: List[str]) -> EGIFErrorReport:
        """Convert a parse error to a comprehensive error report."""
        # Build context from token information
        if parse_error.token:
            context = self._build_context_from_position(
                parse_error.token.line, parse_error.token.column, source_lines
            )
        else:
            context = EGIFErrorContext()
        
        # Add parse-specific context
        context.parse_stack = self.context_stack.copy()
        
        # Determine severity and category
        severity = self._determine_error_severity(parse_error)
        category = self._determine_error_category(parse_error)
        
        # Get educational content
        educational_note = None
        if self.educational_mode:
            educational_note = self._get_educational_note_for_parse_error(parse_error)
        
        # Generate quick fixes
        quick_fixes = self._generate_quick_fixes_for_parse_error(parse_error)
        
        error_report = EGIFErrorReport(
            severity=severity,
            category=category,
            message=parse_error.message,
            error_code=parse_error.error_type,
            context=context,
            suggestions=parse_error.suggestions,
            educational_note=educational_note,
            quick_fixes=quick_fixes
        )
        
        self.error_history.append(error_report)
        return error_report
    
    def _build_context_from_position(self, line: int, column: int, source_lines: List[str]) -> EGIFErrorContext:
        """Build error context from position information."""
        context = EGIFErrorContext()
        context.line_number = line
        context.column_number = column
        
        if 0 < line <= len(source_lines):
            context.source_line = source_lines[line - 1]
            
            # Add surrounding context (2 lines before and after)
            start_line = max(0, line - 3)
            end_line = min(len(source_lines), line + 2)
            context.surrounding_context = source_lines[start_line:end_line]
        
        return context
    
    def _get_educational_note_for_lexical_error(self, lex_error: EGIFLexError) -> Optional[EGIFEducationalNote]:
        """Get educational note for lexical errors."""
        # Map common lexical errors to educational concepts
        if "bracket" in lex_error.message.lower():
            return self.EDUCATIONAL_NOTES.get("negation")
        elif "parenthes" in lex_error.message.lower():
            return self.EDUCATIONAL_NOTES.get("relations")
        elif "&" in lex_error.message:
            # Conjunction error - explain implicit conjunction
            return EGIFEducationalNote(
                concept="Implicit Conjunction",
                explanation="EGIF uses implicit conjunction - multiple relations in the same context are automatically conjoined.",
                examples=[
                    "(Person x) (Mortal x) means 'x is a person AND x is mortal'",
                    "No explicit conjunction operator is needed"
                ],
                graphical_mapping="Multiple atomic graphs drawn in the same area"
            )
        
        return None
    
    def _get_educational_note_for_parse_error(self, parse_error: EGIFParseError) -> Optional[EGIFEducationalNote]:
        """Get educational note for parse errors."""
        # Map error types to educational concepts
        for pattern, info in self.ERROR_PATTERNS.items():
            if pattern in parse_error.error_type:
                concept_key = info["concept"]
                return self.EDUCATIONAL_NOTES.get(concept_key)
        
        # Default educational notes for common error types
        if "UNDEFINED_LABEL" in parse_error.error_type:
            return self.EDUCATIONAL_NOTES.get("bound_labels")
        elif "DUPLICATE_LABEL" in parse_error.error_type:
            return self.EDUCATIONAL_NOTES.get("defining_labels")
        elif "NEGATION" in parse_error.error_type:
            return self.EDUCATIONAL_NOTES.get("negation")
        elif "COREFERENCE" in parse_error.error_type:
            return self.EDUCATIONAL_NOTES.get("coreference")
        elif "SCROLL" in parse_error.error_type:
            return self.EDUCATIONAL_NOTES.get("scroll_notation")
        
        return None
    
    def _generate_quick_fixes_for_lexical_error(self, lex_error: EGIFLexError) -> List[str]:
        """Generate quick fix suggestions for lexical errors."""
        quick_fixes = []
        
        if "{" in lex_error.message or "}" in lex_error.message:
            quick_fixes.append("Replace { } with [ ]")
        elif "&" in lex_error.message:
            quick_fixes.append("Remove & - use implicit conjunction")
        elif "!" in lex_error.message:
            quick_fixes.append("Replace ! with ~")
        elif "@" in lex_error.message:
            quick_fixes.append("Replace @ with *")
        
        return quick_fixes
    
    def _generate_quick_fixes_for_parse_error(self, parse_error: EGIFParseError) -> List[str]:
        """Generate quick fix suggestions for parse errors."""
        quick_fixes = []
        
        # Extract label name from error message if present
        label_match = re.search(r"'([^']+)'", parse_error.message)
        label_name = label_match.group(1) if label_match else None
        
        for pattern, info in self.ERROR_PATTERNS.items():
            if pattern in parse_error.error_type:
                for fix_template in info["common_fixes"]:
                    if label_name and "{label}" in fix_template:
                        fix = fix_template.format(label=label_name)
                    else:
                        fix = fix_template
                    quick_fixes.append(fix)
                break
        
        return quick_fixes
    
    def _determine_error_severity(self, parse_error: EGIFParseError) -> EGIFErrorSeverity:
        """Determine the severity of a parse error."""
        if "INTERNAL" in parse_error.error_type:
            return EGIFErrorSeverity.CRITICAL
        elif "UNDEFINED_LABEL" in parse_error.error_type:
            return EGIFErrorSeverity.ERROR
        elif "DUPLICATE_LABEL" in parse_error.error_type:
            return EGIFErrorSeverity.WARNING
        else:
            return EGIFErrorSeverity.ERROR
    
    def _determine_error_category(self, parse_error: EGIFParseError) -> EGIFErrorCategory:
        """Determine the category of a parse error."""
        if "UNDEFINED_LABEL" in parse_error.error_type or "DUPLICATE_LABEL" in parse_error.error_type:
            return EGIFErrorCategory.CONTEXT
        elif "SYNTAX" in parse_error.error_type or "MISSING" in parse_error.error_type:
            return EGIFErrorCategory.SYNTAX
        elif "SEMANTIC" in parse_error.error_type:
            return EGIFErrorCategory.SEMANTIC
        else:
            return EGIFErrorCategory.SYNTAX
    
    def generate_error_summary(self, errors: List[EGIFErrorReport]) -> str:
        """Generate a summary of all errors with educational insights."""
        if not errors:
            return "No errors found. EGIF expression parsed successfully!"
        
        summary = []
        summary.append(f"EGIF Error Summary: {len(errors)} error(s) found")
        summary.append("=" * 50)
        
        # Group errors by category
        by_category = {}
        for error in errors:
            category = error.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(error)
        
        # Report by category
        for category, category_errors in by_category.items():
            summary.append(f"\n{category} Errors ({len(category_errors)}):")
            for i, error in enumerate(category_errors, 1):
                summary.append(f"  {i}. {error.message}")
                if error.quick_fixes:
                    summary.append(f"     Quick fix: {error.quick_fixes[0]}")
        
        # Educational insights
        if self.educational_mode:
            summary.append("\nEducational Insights:")
            concepts_mentioned = set()
            for error in errors:
                if error.educational_note:
                    concepts_mentioned.add(error.educational_note.concept)
            
            if concepts_mentioned:
                summary.append("Key concepts involved in these errors:")
                for concept in sorted(concepts_mentioned):
                    summary.append(f"  • {concept}")
            else:
                summary.append("Review EGIF syntax rules and existential graph principles.")
        
        return "\n".join(summary)
    
    def push_context(self, context_name: str):
        """Push a parsing context onto the stack."""
        self.context_stack.append(context_name)
    
    def pop_context(self):
        """Pop a parsing context from the stack."""
        if self.context_stack:
            self.context_stack.pop()
    
    def clear_history(self):
        """Clear the error history."""
        self.error_history.clear()


# Integration functions for existing error handling
def integrate_with_clif_errors(egif_handler: EGIFErrorHandler, clif_errors: List[Any]) -> List[EGIFErrorReport]:
    """
    Integrate EGIF error handling with existing CLIF error handling.
    
    This function provides a bridge between EGIF and CLIF error handling
    to maintain consistency across the system.
    """
    integrated_reports = []
    
    for clif_error in clif_errors:
        # Convert CLIF error to EGIF error report format
        # This would need to be customized based on the actual CLIF error structure
        report = EGIFErrorReport(
            severity=EGIFErrorSeverity.ERROR,
            category=EGIFErrorCategory.SYSTEM,
            message=str(clif_error),
            error_code="CLIF_INTEGRATION",
            context=EGIFErrorContext(),
            suggestions=["Consider using EGIF format for better error reporting"]
        )
        integrated_reports.append(report)
    
    return integrated_reports


# Example usage and testing
if __name__ == "__main__":
    # Test the error handling framework
    handler = EGIFErrorHandler(educational_mode=True)
    
    # Simulate some errors
    from egif_lexer import EGIFLexError
    from egif_parser import EGIFParseError, EGIFToken
    
    # Test lexical error handling
    lex_error = EGIFLexError(
        message="Unrecognized character: '&'",
        line=1,
        column=9,
        position=8,
        length=1,
        error_type="INVALID_CHARACTER",
        suggestions=["EGIF uses implicit conjunction"],
        educational_note="Conjunction is implicit in EGIF"
    )
    
    source_lines = ["(Person &x)"]
    lex_report = handler.handle_lexical_error(lex_error, source_lines)
    
    print("Lexical Error Report:")
    print(lex_report.format_for_display())
    print("\n" + "="*60 + "\n")
    
    # Test parse error handling
    token = EGIFToken(
        type=EGIFTokenType.IDENTIFIER,
        value="y",
        line=1,
        column=15,
        position=14,
        length=1
    )
    
    parse_error = EGIFParseError(
        message="Undefined label 'y'",
        token=token,
        error_type="UNDEFINED_LABEL",
        suggestions=["Define the label first with *y"],
        educational_note="Labels must be defined before use"
    )
    
    source_lines = ["(Person *x) (Mortal y)"]
    parse_report = handler.handle_parse_error(parse_error, source_lines)
    
    print("Parse Error Report:")
    print(parse_report.format_for_display())
    print("\n" + "="*60 + "\n")
    
    # Test error summary
    summary = handler.generate_error_summary([lex_report, parse_report])
    print("Error Summary:")
    print(summary)

