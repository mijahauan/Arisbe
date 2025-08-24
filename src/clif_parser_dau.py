"""
Dau-compliant CLIF (Common Logic Interchange Format) parser.
Converts CLIF expressions to RelationalGraphWithCuts structures.

CLIF Syntax Overview:
- Atomic formulas: (P x y)
- Quantification: (forall (x) (P x))
- Negation: (not (P x))
- Conjunction: (and (P x) (Q y))
- Disjunction: (or (P x) (Q y))
- Comments: ;; comment text

Maps to EGI as:
- Atomic formulas -> Edges with vertices
- Negation -> Cuts containing negated content
- Quantification -> Variable scoping in areas
- Conjunction -> Multiple elements in same area
- Disjunction -> Requires transformation to negation normal form
"""

import re
from typing import List, Dict, Set, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut,
    create_empty_graph, create_vertex, create_edge, create_cut,
    ElementID, VertexSequence, RelationName
)


class CLIFTokenType(Enum):
    """Token types for CLIF lexical analysis."""
    LPAREN = "LPAREN"           # (
    RPAREN = "RPAREN"           # )
    IDENTIFIER = "IDENTIFIER"    # predicate names, variables
    FORALL = "FORALL"           # forall
    EXISTS = "EXISTS"           # exists  
    NOT = "NOT"                 # not
    AND = "AND"                 # and
    OR = "OR"                   # or
    IFF = "IFF"                 # iff
    IF = "IF"                   # if
    COMMENT = "COMMENT"         # ;; comment
    EOF = "EOF"


@dataclass
class CLIFToken:
    """CLIF token with type and value."""
    type: CLIFTokenType
    value: str
    position: int


class CLIFLexer:
    """Lexical analyzer for CLIF expressions."""
    
    def __init__(self, text: str):
        self.text = text.strip()
        self.position = 0
        self.tokens = []
        
    def tokenize(self) -> List[CLIFToken]:
        """Convert CLIF text into tokens."""
        self.tokens = []
        self.position = 0
        
        while self.position < len(self.text):
            self._skip_whitespace()
            
            if self.position >= len(self.text):
                break
                
            char = self.text[self.position]
            
            if char == '(':
                self.tokens.append(CLIFToken(CLIFTokenType.LPAREN, '(', self.position))
                self.position += 1
            elif char == ')':
                self.tokens.append(CLIFToken(CLIFTokenType.RPAREN, ')', self.position))
                self.position += 1
            elif char == ';' and self.position + 1 < len(self.text) and self.text[self.position + 1] == ';':
                self._read_comment()
            else:
                self._read_identifier()
        
        self.tokens.append(CLIFToken(CLIFTokenType.EOF, '', self.position))
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while (self.position < len(self.text) and 
               self.text[self.position] in ' \t\n\r'):
            self.position += 1
    
    def _read_comment(self):
        """Read comment starting with ;;"""
        start = self.position
        while (self.position < len(self.text) and 
               self.text[self.position] != '\n'):
            self.position += 1
        comment_text = self.text[start:self.position]
        self.tokens.append(CLIFToken(CLIFTokenType.COMMENT, comment_text, start))
    
    def _read_identifier(self):
        """Read identifier (predicate name, variable, keyword)."""
        start = self.position
        
        # Read identifier characters
        while (self.position < len(self.text) and 
               self.text[self.position] not in ' \t\n\r()'):
            self.position += 1
        
        identifier = self.text[start:self.position]
        
        # Check for keywords
        token_type = {
            'forall': CLIFTokenType.FORALL,
            'exists': CLIFTokenType.EXISTS,
            'not': CLIFTokenType.NOT,
            'and': CLIFTokenType.AND,
            'or': CLIFTokenType.OR,
            'iff': CLIFTokenType.IFF,
            'if': CLIFTokenType.IF
        }.get(identifier.lower(), CLIFTokenType.IDENTIFIER)
        
        self.tokens.append(CLIFToken(token_type, identifier, start))


@dataclass
class CLIFParseNode:
    """Node in CLIF parse tree."""
    type: str
    value: Optional[str] = None
    children: List['CLIFParseNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class CLIFParser:
    """Parser for CLIF expressions."""
    
    def __init__(self, text: str):
        self.text = text
        self.lexer = CLIFLexer(text)
        self.tokens = []
        self.position = 0
        self.current_token = None
        
    def parse(self) -> RelationalGraphWithCuts:
        """Parse CLIF text into EGI structure."""
        self.tokens = self.lexer.tokenize()
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
        # Parse the CLIF expression
        parse_tree = self._parse_expression()
        
        # Convert parse tree to EGI immutably
        egi = create_empty_graph()
        egi = self._convert_to_egi(parse_tree, egi, egi.sheet)
        return egi
    
    def _advance(self):
        """Move to next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _expect(self, token_type: CLIFTokenType) -> CLIFToken:
        """Expect specific token type."""
        if self.current_token.type != token_type:
            raise ValueError(f"Expected {token_type}, got {self.current_token.type} at position {self.current_token.position}")
        token = self.current_token
        self._advance()
        return token
    
    def _parse_expression(self) -> CLIFParseNode:
        """Parse a CLIF expression."""
        if self.current_token.type == CLIFTokenType.LPAREN:
            return self._parse_compound_expression()
        elif self.current_token.type == CLIFTokenType.IDENTIFIER:
            # Simple identifier (constant)
            token = self.current_token
            self._advance()
            return CLIFParseNode('constant', token.value)
        else:
            raise ValueError(f"Unexpected token {self.current_token.type} at position {self.current_token.position}")
    
    def _parse_compound_expression(self) -> CLIFParseNode:
        """Parse compound expression starting with (."""
        self._expect(CLIFTokenType.LPAREN)
        
        if self.current_token.type == CLIFTokenType.FORALL:
            return self._parse_quantification('forall')
        elif self.current_token.type == CLIFTokenType.EXISTS:
            return self._parse_quantification('exists')
        elif self.current_token.type == CLIFTokenType.NOT:
            return self._parse_negation()
        elif self.current_token.type == CLIFTokenType.AND:
            return self._parse_conjunction()
        elif self.current_token.type == CLIFTokenType.OR:
            return self._parse_disjunction()
        elif self.current_token.type == CLIFTokenType.IDENTIFIER:
            return self._parse_atomic_formula()
        else:
            raise ValueError(f"Unexpected token in compound expression: {self.current_token.type}")
    
    def _parse_quantification(self, quantifier: str) -> CLIFParseNode:
        """Parse forall or exists quantification."""
        self._advance()  # Skip quantifier
        
        # Parse variable list (x) or (x y z)
        self._expect(CLIFTokenType.LPAREN)
        variables = []
        while self.current_token.type == CLIFTokenType.IDENTIFIER:
            variables.append(self.current_token.value)
            self._advance()
        self._expect(CLIFTokenType.RPAREN)
        
        # Parse body
        body = self._parse_expression()
        
        self._expect(CLIFTokenType.RPAREN)
        
        node = CLIFParseNode(quantifier)
        node.children = [CLIFParseNode('variables', None, [CLIFParseNode('variable', var) for var in variables]), body]
        return node
    
    def _parse_negation(self) -> CLIFParseNode:
        """Parse negation (not ...)."""
        self._advance()  # Skip 'not'
        
        body = self._parse_expression()
        self._expect(CLIFTokenType.RPAREN)
        
        node = CLIFParseNode('not')
        node.children = [body]
        return node
    
    def _parse_conjunction(self) -> CLIFParseNode:
        """Parse conjunction (and ...)."""
        self._advance()  # Skip 'and'
        
        conjuncts = []
        while self.current_token.type != CLIFTokenType.RPAREN:
            conjuncts.append(self._parse_expression())
        
        self._expect(CLIFTokenType.RPAREN)
        
        node = CLIFParseNode('and')
        node.children = conjuncts
        return node
    
    def _parse_disjunction(self) -> CLIFParseNode:
        """Parse disjunction (or ...)."""
        self._advance()  # Skip 'or'
        
        disjuncts = []
        while self.current_token.type != CLIFTokenType.RPAREN:
            disjuncts.append(self._parse_expression())
        
        self._expect(CLIFTokenType.RPAREN)
        
        node = CLIFParseNode('or')
        node.children = disjuncts
        return node
    
    def _parse_atomic_formula(self) -> CLIFParseNode:
        """Parse atomic formula (P x y)."""
        predicate = self.current_token.value
        self._advance()
        
        arguments = []
        while self.current_token.type == CLIFTokenType.IDENTIFIER:
            arguments.append(self.current_token.value)
            self._advance()
        
        self._expect(CLIFTokenType.RPAREN)
        
        node = CLIFParseNode('atomic')
        node.value = predicate
        node.children = [CLIFParseNode('argument', arg) for arg in arguments]
        return node
    
    def _convert_to_egi(self, node: CLIFParseNode, egi: RelationalGraphWithCuts, area_id: str) -> RelationalGraphWithCuts:
        """Convert parse tree node to EGI elements immutably and return updated egi."""
        if node.type == 'atomic':
            # Create vertices for arguments
            vertex_ids = []
            for arg_node in node.children:
                vertex_id = f"v_{arg_node.value}"
                if not any(v.id == vertex_id for v in egi.V):
                    vertex = Vertex(id=vertex_id, label=arg_node.value, is_generic=False)
                    egi = egi.with_vertex_in_context(vertex, area_id)
                vertex_ids.append(vertex_id)
            # Create edge for predicate in same area
            edge_id = f"e_{node.value}_{len(egi.E)}"
            edge = Edge(id=edge_id)
            egi = egi.with_edge(edge, tuple(vertex_ids), node.value, context_id=area_id)
            return egi
        
        if node.type == 'not':
            # Create cut for negation
            cut_id = f"c_not_{len(egi.Cut)}"
            cut = Cut(id=cut_id)
            egi = egi.with_cut(cut, context_id=area_id)
            # Process negated content in cut
            for child in node.children:
                egi = self._convert_to_egi(child, egi, cut_id)
            return egi
        
        if node.type == 'and':
            # Conjunction - all children in same area
            for child in node.children:
                egi = self._convert_to_egi(child, egi, area_id)
            return egi
        
        if node.type == 'or':
            # Disjunction - convert to negation normal form using cuts
            outer_cut_id = f"c_or_outer_{len(egi.Cut)}"
            outer_cut = Cut(id=outer_cut_id)
            egi = egi.with_cut(outer_cut, context_id=area_id)
            # Create inner cuts for each disjunct
            for child in node.children:
                inner_cut_id = f"c_or_inner_{len(egi.Cut)}"
                inner_cut = Cut(id=inner_cut_id)
                egi = egi.with_cut(inner_cut, context_id=outer_cut_id)
                # Process child in inner cut
                egi = self._convert_to_egi(child, egi, inner_cut_id)
            return egi
        
        if node.type == 'forall':
            # Universal quantification - process variables and body (ignore variable scoping for now)
            for child in node.children:
                if child.type != 'variables':
                    egi = self._convert_to_egi(child, egi, area_id)
            return egi
        
        return egi


# Factory function
def parse_clif(clif_text: str) -> RelationalGraphWithCuts:
    """Parse CLIF text into EGI structure."""
    parser = CLIFParser(clif_text)
    return parser.parse()
