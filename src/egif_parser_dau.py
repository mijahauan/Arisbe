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
    ElementID, VertexSequence, RelationName, AlphabetDAU
)
from frozendict import frozendict


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
        """Validate a node (relation, cut, or isolated vertex)."""
        token = self._current_token()
        
        if token.type == TokenType.LPAREN:
            self._validate_relation()
        elif token.type == TokenType.LCUT:
            self._validate_cut()
        elif token.type == TokenType.LBRACKET:
            self._validate_variable_declaration()
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
    
    
    def _validate_variable_declaration(self):
        """Validate variable declaration [*x] syntax per Sowa's EGIF."""
        if self._current_token().type != TokenType.LBRACKET:
            raise ValueError("Expected '[' for variable declaration")
        self._advance()
        
        # Expect defining variable
        if self._current_token().type != TokenType.DEFINING_VAR:
            raise ValueError("Expected defining variable *x in variable declaration")
        self._advance()
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close variable declaration")
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
        self.text = self._preprocess_text(text)
        self.tokens = []
        self.position = 0
        self.graph = create_empty_graph()
        self.variable_map = {}  # Maps variable names to current (top) vertex IDs
        # Per Sowa: duplicates are only illegal within the same area; allow shadowing across areas
        self.defs_in_area: Dict[ElementID, Set[str]] = {}
        # Shadowing stack: var name -> list of (def_area, vertex_id) from outer to inner
        self.var_stack: Dict[str, List[Tuple[ElementID, ElementID]]] = {}
        # New: track definition context for each variable label
        self.var_def_context: Dict[str, ElementID] = {}
        # New: track occurrence contexts for LCA hoisting
        self.var_occ_contexts: Dict[str, Set[ElementID]] = {}
        self.const_occ_contexts: Dict[str, Set[ElementID]] = {}
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess EGIF text to handle comments and normalize whitespace."""
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Strip leading/trailing whitespace
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip comment lines (starting with #)
            if line.startswith('#'):
                continue
            
            # Remove inline comments (everything after # on a line)
            if '#' in line:
                line = line[:line.index('#')].strip()
                if not line:  # Skip if nothing left after removing comment
                    continue
            
            processed_lines.append(line)
        
        # Join with single spaces and normalize whitespace
        result = ' '.join(processed_lines)
        
        # Normalize multiple spaces to single spaces
        result = re.sub(r'\s+', ' ', result)
        
        return result.strip()

    def parse(self) -> RelationalGraphWithCuts:
        """Parse EGIF expression into Dau-compliant graph."""
        # Tokenize
        lexer = EGIFLexer(self.text)
        self.tokens = lexer.tokenize()

        # Validate syntax
        validator = EGIFSyntaxValidator(self.tokens)
        validator.validate()

        # Reset position for parsing
        self.position = 0
        self.graph = create_empty_graph()
        self.variable_map = {}
        self.defs_in_area = {}
        self.var_stack = {}
        self.constant_vertices = {}  # Track constant name -> vertex ID mapping
        self.var_def_context = {}
        self.var_occ_contexts = {}
        self.const_occ_contexts = {}

        # Parse the expression
        self._parse_eg()

        # Post-parse: hoist variables and constants to LCA of their occurrences
        self._hoist_vertices_to_lca()
        # Populate AlphabetDAU and rho mapping for constants
        self.graph = self._finalize_alphabet_and_rho(self.graph)

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
            self._parse_variable_declaration(context_id)
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
            # Initialize area set
            self.defs_in_area.setdefault(context_id, set())
            if var_name in self.defs_in_area[context_id]:
                raise ValueError(f"Duplicate defining label *{var_name} in same area")
            self.defs_in_area[context_id].add(var_name)
            vertex = create_vertex(label=None, is_generic=True)
            
            # Defining variables are assigned to the context where they are first defined
            self.graph = self.graph.with_vertex_in_context(vertex, context_id)
            # Push onto shadowing stack and update current mappings
            self.var_stack.setdefault(var_name, []).append((context_id, vertex.id))
            self.variable_map[var_name] = vertex.id
            self.var_def_context[var_name] = context_id
            self._advance()
            return vertex.id
            
        elif token.type == TokenType.BOUND_VAR:
            # Bound variable x
            var_name = token.value
            if var_name not in self.variable_map:
                raise ValueError(f"Undefined variable {var_name}")
            # Scope check: declaration context must be an ancestor of current context
            decl_ctx = self.var_def_context.get(var_name)
            if decl_ctx is None:
                raise ValueError(f"Variable {var_name} has no recorded declaration context")
            if not self._is_ancestor_context(decl_ctx, context_id):
                raise ValueError(f"Out-of-scope variable {var_name}: declared in unrelated context")
            # Track occurrence for LCA hoisting
            self.var_occ_contexts.setdefault(var_name, set()).add(context_id)
            self._advance()
            return self.variable_map[var_name]
            
        elif token.type == TokenType.CONSTANT:
            # Constant "Socrates" - reuse existing vertex if already created
            constant_value = token.value[1:-1]  # Remove quotes
            
            # Check if we already have a vertex for this constant
            if constant_value in self.constant_vertices:
                # Reuse existing vertex
                vertex_id = self.constant_vertices[constant_value]
                # Track occurrence for LCA hoisting
                self.const_occ_contexts.setdefault(constant_value, set()).add(context_id)
                self._advance()
                return vertex_id
            else:
                # Create new vertex for this constant
                vertex = create_vertex(label=constant_value, is_generic=False)
                self.graph = self.graph.with_vertex_in_context(vertex, context_id)
                self.constant_vertices[constant_value] = vertex.id
                # Track occurrence for LCA hoisting
                self.const_occ_contexts.setdefault(constant_value, set()).add(context_id)
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
        # Prepare area definition set for this cut
        self.defs_in_area.setdefault(cut.id, set())
        
        # Parse cut contents
        while self._current_token().type not in [TokenType.RBRACKET, TokenType.EOF]:
            self._parse_node(cut.id)
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close cut")
        self._advance()
        # On exiting the cut area, pop any shadowed variables defined in this area
        self._pop_area_vars(cut.id)
    
    
    def _parse_variable_declaration(self, context_id: ElementID):
        """Parse variable declaration [*x] syntax per Sowa's EGIF."""
        if self._current_token().type != TokenType.LBRACKET:
            raise ValueError("Expected '[' for variable declaration")
        self._advance()
        
        # Parse defining variable
        if self._current_token().type != TokenType.DEFINING_VAR:
            raise ValueError("Expected defining variable *x in variable declaration")
        
        var_name = self._current_token().value[1:]  # Remove *
        self.defs_in_area.setdefault(context_id, set())
        if var_name in self.defs_in_area[context_id]:
            raise ValueError(f"Duplicate defining label *{var_name} in same area")
        self.defs_in_area[context_id].add(var_name)
        vertex = create_vertex(label=None, is_generic=True)
        self.graph = self.graph.with_vertex_in_context(vertex, context_id)
        self.var_stack.setdefault(var_name, []).append((context_id, vertex.id))
        self.variable_map[var_name] = vertex.id
        self.var_def_context[var_name] = context_id
        self._advance()
        
        if self._current_token().type != TokenType.RBRACKET:
            raise ValueError("Expected ']' to close variable declaration")
        self._advance()
    
    def _parse_isolated_vertex(self, context_id: ElementID):
        """Parse isolated vertex (heavy dot)."""
        token = self._current_token()
        
        if token.type == TokenType.DEFINING_VAR:
            # Isolated defining variable *x
            var_name = token.value[1:]  # Remove *
            self.defs_in_area.setdefault(context_id, set())
            if var_name in self.defs_in_area[context_id]:
                raise ValueError(f"Duplicate defining label *{var_name} in same area")
            self.defs_in_area[context_id].add(var_name)
            vertex = create_vertex(label=None, is_generic=True)
            self.graph = self.graph.with_vertex_in_context(vertex, context_id)
            self.var_stack.setdefault(var_name, []).append((context_id, vertex.id))
            self.variable_map[var_name] = vertex.id
            self.var_def_context[var_name] = context_id
            self._advance()
            return vertex.id
            
        elif token.type == TokenType.BOUND_VAR:
            # Bound variable x
            var_name = token.value
            if var_name not in self.variable_map:
                raise ValueError(f"Undefined variable {var_name}")
            # Scope check: declaration context must be an ancestor of current context
            decl_ctx = self.var_def_context.get(var_name)
            if decl_ctx is None:
                raise ValueError(f"Variable {var_name} has no recorded declaration context")
            if not self._is_ancestor_context(decl_ctx, context_id):
                raise ValueError(f"Out-of-scope variable {var_name}: declared in unrelated context")
            # Track occurrence for LCA (symmetry with arguments; variables stay at def area)
            self.var_occ_contexts.setdefault(var_name, set()).add(context_id)
            vertex_id = self.variable_map[var_name]
            self._advance()
            return vertex_id
            
        elif token.type == TokenType.CONSTANT:
            # Isolated constant "Socrates"
            constant_value = token.value[1:-1]  # Remove quotes
            vertex = create_vertex(label=constant_value, is_generic=False)
            self.graph = self.graph.with_vertex_in_context(vertex, context_id)
            
            # Track constant occurrences for validation
            if constant_value not in self.const_occ_contexts:
                self.const_occ_contexts[constant_value] = set()
            self.const_occ_contexts[constant_value].add(context_id)
            self._advance()
            return vertex.id
            
        else:
            raise ValueError(f"Invalid isolated vertex token: {token.type}")

    def _pop_area_vars(self, area_id: ElementID) -> None:
        """Pop shadowed variable definitions that were defined in the given area, restoring outer bindings."""
        # Remove from defs_in_area
        # And unwind var_stack, variable_map, var_def_context appropriately
        to_remove: List[Tuple[str, ElementID]] = []
        area_defs = self.defs_in_area.get(area_id, set())
        for var_name in list(self.var_stack.keys()):
            stack = self.var_stack[var_name]
            while stack and stack[-1][0] == area_id:
                _, vid = stack.pop()
                to_remove.append((var_name, vid))
            if not stack:
                # No outer binding remains
                self.var_stack.pop(var_name, None)
                self.variable_map.pop(var_name, None)
                self.var_def_context.pop(var_name, None)
            else:
                # Restore outer binding
                outer_area, outer_vid = stack[-1]
                self.variable_map[var_name] = outer_vid
                self.var_def_context[var_name] = outer_area
        # Clear area defs set
        if area_id in self.defs_in_area:
            self.defs_in_area[area_id].clear()
    
    # --- helpers ---
    def _is_ancestor_context(self, ancestor_ctx: ElementID, ctx: ElementID) -> bool:
        """Return True if ancestor_ctx is the same as ctx or an ancestor (transitive parent) of ctx."""
        if ancestor_ctx == ctx:
            return True
        # Walk up parents using graph context links
        current = ctx
        seen = set()
        while current is not None and current not in seen:
            seen.add(current)
            if current == ancestor_ctx:
                return True
            # Stop at sheet which has parent None
            if current == self.graph.sheet:
                current = None
            else:
                current = self.graph.get_context(current)
        return False

    def _get_ancestor_chain(self, context_id: ElementID) -> List[ElementID]:
        """Return list from context up to sheet, inclusive: [ctx, parent, ..., sheet]."""
        chain = []
        current = context_id
        seen = set()
        while current is not None and current not in seen:
            chain.append(current)
            seen.add(current)
            if current == self.graph.sheet:
                current = None
            else:
                current = self.graph.get_context(current)
        return chain

    def _compute_lca(self, contexts: Set[ElementID]) -> ElementID:
        """Compute least common ancestor context of a non-empty set of contexts."""
        if not contexts:
            return self.graph.sheet
        # Build ancestor chains
        chains = [self._get_ancestor_chain(c) for c in contexts]
        # Intersect sets of ancestors
        common = set(chains[0])
        for ch in chains[1:]:
            common &= set(ch)
        if not common:
            # Should not happen; at minimum sheet is common
            return self.graph.sheet
        # Choose the deepest common ancestor (max depth)
        def depth(ctx: ElementID) -> int:
            d = 0
            current = ctx
            while current != self.graph.sheet:
                d += 1
                current = self.graph.get_context(current)
            return d
        return max(common, key=depth)

    def _hoist_vertices_to_lca(self):
        """After parsing, relocate constant vertices to the LCA of their occurrences.
        Variables remain at their defining context (quantifier area), so lines cross cuts as needed.
        """
        # Build ancestor chains for areas
        def ancestors(area_id: str) -> List[str]:
            chain = [area_id]
            cur = area_id
            while True:
                parent = self.graph.get_parent_area(cur)
                if not parent or parent == cur:
                    break
                chain.append(parent)
                cur = parent
            return chain

        # Constants
        for name, ctxs in self.const_occ_contexts.items():
            vertex_id = self.constant_vertices.get(name)
            if not vertex_id:
                continue
            target_ctx = self._compute_lca(ctxs)
            # Move if needed
            self.graph = self.graph.with_vertex_moved_to_context(vertex_id, target_ctx)

    def _finalize_alphabet_and_rho(self, graph: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
        """Compute AlphabetDAU (C,F,R,ar) and rho from the parsed graph, and return
        a new graph with these fields set. Functions (F) are not inferred from EGIF currently.
        """
        # Constants from non-generic vertices with labels
        constants: Set[str] = set()
        rho_map: Dict[str, Optional[str]] = {}
        for v in graph.V:
            if not getattr(v, 'is_generic', True) and getattr(v, 'label', None):
                constants.add(v.label)  # type: ignore
                rho_map[v.id] = v.label  # type: ignore
            else:
                rho_map[v.id] = None
        # Relation names and arities from rel and nu
        relation_names: Set[str] = set()
        ar_map: Dict[str, int] = {}
        for eid, name in graph.rel.items():
            relation_names.add(name)
            ar_map[name] = max(ar_map.get(name, 0), len(graph.nu.get(eid, tuple())))
        alphabet = AlphabetDAU(C=frozenset(constants), F=frozenset(), R=frozenset(relation_names), ar=frozendict(ar_map)).with_defaults()

        # Build and return new graph with alphabet and rho
        return RelationalGraphWithCuts(
            V=graph.V,
            E=graph.E,
            nu=graph.nu,
            sheet=graph.sheet,
            Cut=graph.Cut,
            area=graph.area,
            rel=graph.rel,
            alphabet=alphabet,
            rho=frozendict(rho_map),
        )


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

