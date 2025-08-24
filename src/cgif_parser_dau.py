"""
Dau-compliant CGIF (Conceptual Graph Interchange Format) parser.
Converts CGIF expressions to RelationalGraphWithCuts structures.

CGIF Syntax Overview (from ISO/IEC 24707:2007 Annex B):
- Concepts: [Type: *x], [: John], [*x]
- Relations: (Loves ?x John), (Go ?x)
- Contexts: [CG content]
- Coreference labels: *x (defining), ?x (bound)
- Universal quantifier: @every
- Negation: ~[CG content]

Maps to EGI as:
- Concepts -> Vertices with type relations
- Relations -> Edges
- Contexts -> Areas (cuts for negation)
- Coreference labels -> Variable bindings
"""

import re
from typing import List, Dict, Set, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut,
    create_empty_graph, ElementID, VertexSequence, RelationName
)


class CGIFTokenType(Enum):
    """Token types for CGIF lexical analysis."""
    LBRACKET = "LBRACKET"       # [
    RBRACKET = "RBRACKET"       # ]
    LPAREN = "LPAREN"           # (
    RPAREN = "RPAREN"           # )
    COLON = "COLON"             # :
    PIPE = "PIPE"               # |
    TILDE = "TILDE"             # ~
    ASTERISK = "ASTERISK"       # *
    QUESTION = "QUESTION"       # ?
    AT_EVERY = "AT_EVERY"       # @every
    IDENTIFIER = "IDENTIFIER"   # names, types
    NUMERAL = "NUMERAL"         # numbers
    STRING = "STRING"           # quoted strings
    SEQMARK = "SEQMARK"         # ...
    COMMENT = "COMMENT"         # /* comment */
    EOF = "EOF"


@dataclass
class CGIFToken:
    """CGIF lexical token."""
    type: CGIFTokenType
    value: str
    position: int


class CGIFLexer:
    """Lexical analyzer for CGIF expressions."""
    
    def __init__(self, text: str):
        self.text = text
        self.position = 0
        self.tokens = []
    
    def tokenize(self) -> List[CGIFToken]:
        """Tokenize CGIF text."""
        self.tokens = []
        self.position = 0
        
        while self.position < len(self.text):
            self._skip_whitespace()
            
            if self.position >= len(self.text):
                break
            
            char = self.text[self.position]
            
            if char == '[':
                self.tokens.append(CGIFToken(CGIFTokenType.LBRACKET, '[', self.position))
                self.position += 1
            elif char == ']':
                self.tokens.append(CGIFToken(CGIFTokenType.RBRACKET, ']', self.position))
                self.position += 1
            elif char == '(':
                self.tokens.append(CGIFToken(CGIFTokenType.LPAREN, '(', self.position))
                self.position += 1
            elif char == ')':
                self.tokens.append(CGIFToken(CGIFTokenType.RPAREN, ')', self.position))
                self.position += 1
            elif char == ':':
                self.tokens.append(CGIFToken(CGIFTokenType.COLON, ':', self.position))
                self.position += 1
            elif char == '|':
                self.tokens.append(CGIFToken(CGIFTokenType.PIPE, '|', self.position))
                self.position += 1
            elif char == '~':
                self.tokens.append(CGIFToken(CGIFTokenType.TILDE, '~', self.position))
                self.position += 1
            elif char == '*':
                self.tokens.append(CGIFToken(CGIFTokenType.ASTERISK, '*', self.position))
                self.position += 1
            elif char == '?':
                self.tokens.append(CGIFToken(CGIFTokenType.QUESTION, '?', self.position))
                self.position += 1
            elif char == '"':
                self._read_string()
            elif char == '/' and self.position + 1 < len(self.text) and self.text[self.position + 1] == '*':
                self._read_comment()
            elif char == '.' and self._check_sequence_marker():
                self._read_sequence_marker()
            elif char == '@' and self._check_at_every():
                self._read_at_every()
            elif char.isdigit() or (char == '-' and self.position + 1 < len(self.text) and self.text[self.position + 1].isdigit()):
                self._read_numeral()
            else:
                self._read_identifier()
        
        self.tokens.append(CGIFToken(CGIFTokenType.EOF, '', self.position))
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while (self.position < len(self.text) and 
               self.text[self.position] in ' \t\n\r'):
            self.position += 1
    
    def _read_string(self):
        """Read quoted string."""
        start = self.position
        self.position += 1  # Skip opening quote
        
        while (self.position < len(self.text) and 
               self.text[self.position] != '"'):
            if self.text[self.position] == '\\':
                self.position += 2  # Skip escaped character
            else:
                self.position += 1
        
        if self.position < len(self.text):
            self.position += 1  # Skip closing quote
        
        string_value = self.text[start:self.position]
        self.tokens.append(CGIFToken(CGIFTokenType.STRING, string_value, start))
    
    def _read_comment(self):
        """Read /* comment */"""
        start = self.position
        self.position += 2  # Skip /*
        
        while (self.position + 1 < len(self.text) and 
               not (self.text[self.position] == '*' and self.text[self.position + 1] == '/')):
            self.position += 1
        
        if self.position + 1 < len(self.text):
            self.position += 2  # Skip */
        
        comment_value = self.text[start:self.position]
        self.tokens.append(CGIFToken(CGIFTokenType.COMMENT, comment_value, start))
    
    def _check_sequence_marker(self) -> bool:
        """Check if current position starts sequence marker ..."""
        return (self.position + 2 < len(self.text) and 
                self.text[self.position:self.position + 3] == '...')
    
    def _read_sequence_marker(self):
        """Read sequence marker ..."""
        start = self.position
        self.position += 3  # Skip ...
        self.tokens.append(CGIFToken(CGIFTokenType.SEQMARK, '...', start))
    
    def _check_at_every(self) -> bool:
        """Check if current position starts @every."""
        return (self.position + 5 < len(self.text) and 
                self.text[self.position:self.position + 6] == '@every')
    
    def _read_at_every(self):
        """Read @every quantifier."""
        start = self.position
        self.position += 6  # Skip @every
        self.tokens.append(CGIFToken(CGIFTokenType.AT_EVERY, '@every', start))
    
    def _read_numeral(self):
        """Read numeric literal."""
        start = self.position
        
        if self.text[self.position] == '-':
            self.position += 1
        
        while (self.position < len(self.text) and 
               (self.text[self.position].isdigit() or self.text[self.position] == '.')):
            self.position += 1
        
        numeral_value = self.text[start:self.position]
        self.tokens.append(CGIFToken(CGIFTokenType.NUMERAL, numeral_value, start))
    
    def _read_identifier(self):
        """Read identifier (names, types)."""
        start = self.position
        
        # Read identifier characters
        while (self.position < len(self.text) and 
               self.text[self.position] not in ' \t\n\r[]():*?|~@"'):
            self.position += 1
        
        identifier = self.text[start:self.position]
        self.tokens.append(CGIFToken(CGIFTokenType.IDENTIFIER, identifier, start))


@dataclass
class CGIFParseNode:
    """Node in CGIF parse tree."""
    type: str
    value: Optional[str] = None
    children: List['CGIFParseNode'] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.attributes is None:
            self.attributes = {}


class CGIFParser:
    """Parser for CGIF expressions."""
    
    def __init__(self, text: str):
        self.text = text
        self.lexer = CGIFLexer(text)
        self.tokens = []
        self.position = 0
        self.current_token = None
        self.coreference_labels = {}  # Maps defining labels to bound labels
        
    def parse(self) -> RelationalGraphWithCuts:
        """Parse CGIF text into EGI structure."""
        self.tokens = self.lexer.tokenize()
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
        # Parse the CGIF expression
        parse_tree = self._parse_cg()
        
        # Convert parse tree to EGI (immutably)
        egi = create_empty_graph()
        egi = self._convert_to_egi(parse_tree, egi, egi.sheet)
        return egi
    
    def _advance(self):
        """Move to next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _expect(self, token_type: CGIFTokenType) -> CGIFToken:
        """Expect specific token type."""
        if self.current_token.type != token_type:
            raise ValueError(f"Expected {token_type}, got {self.current_token.type} at position {self.current_token.position}")
        token = self.current_token
        self._advance()
        return token
    
    def _parse_cg(self) -> CGIFParseNode:
        """Parse conceptual graph (sequence of concepts and relations)."""
        node = CGIFParseNode('cg')
        
        while (self.current_token.type in [CGIFTokenType.LBRACKET, CGIFTokenType.LPAREN, 
                                          CGIFTokenType.TILDE, CGIFTokenType.COMMENT]):
            if self.current_token.type == CGIFTokenType.COMMENT:
                self._advance()  # Skip comments
            elif self.current_token.type == CGIFTokenType.LBRACKET or self.current_token.type == CGIFTokenType.TILDE:
                concept = self._parse_concept()
                node.children.append(concept)
            elif self.current_token.type == CGIFTokenType.LPAREN:
                relation = self._parse_relation()
                node.children.append(relation)
        
        return node
    
    def _parse_concept(self) -> CGIFParseNode:
        """Parse concept [Type: *x], [: John], [*x], or ~[CG]."""
        if self.current_token.type == CGIFTokenType.TILDE:
            # Negated context
            self._advance()  # Skip ~
            self._expect(CGIFTokenType.LBRACKET)
            
            node = CGIFParseNode('negation')
            cg_content = self._parse_cg()
            node.children.append(cg_content)
            
            self._expect(CGIFTokenType.RBRACKET)
            return node
        
        self._expect(CGIFTokenType.LBRACKET)
        
        # Check for different concept types
        if self.current_token.type == CGIFTokenType.ASTERISK:
            # Existential concept [*x]
            self._advance()  # Skip *
            label_token = self._expect(CGIFTokenType.IDENTIFIER)
            self._expect(CGIFTokenType.RBRACKET)
            
            node = CGIFParseNode('existential_concept')
            node.value = label_token.value
            return node
            
        elif self.current_token.type == CGIFTokenType.COLON:
            # Coreference concept [: name] or context
            self._advance()  # Skip :
            
            if self.current_token.type == CGIFTokenType.RBRACKET:
                # Empty context [:]
                self._advance()
                return CGIFParseNode('context')
            else:
                # Coreference concept [: name]
                name_token = self._expect(CGIFTokenType.IDENTIFIER)
                self._expect(CGIFTokenType.RBRACKET)
                
                node = CGIFParseNode('coreference_concept')
                node.value = name_token.value
                return node
        
        else:
            # Type concept [Type: *x] or context [CG]
            if self.current_token.type == CGIFTokenType.IDENTIFIER:
                type_token = self.current_token
                self._advance()
                
                if self.current_token.type == CGIFTokenType.COLON:
                    # Type concept [Type: *x]
                    self._advance()  # Skip :
                    
                    node = CGIFParseNode('type_concept')
                    node.value = type_token.value
                    
                    # Parse referent (defining label or constant)
                    if self.current_token.type == CGIFTokenType.ASTERISK:
                        self._advance()  # Skip *
                        label_token = self._expect(CGIFTokenType.IDENTIFIER)
                        node.attributes['defining_label'] = label_token.value
                    elif self.current_token.type == CGIFTokenType.AT_EVERY:
                        self._advance()  # Skip @every
                        self._expect(CGIFTokenType.ASTERISK)
                        label_token = self._expect(CGIFTokenType.IDENTIFIER)
                        node.attributes['universal_label'] = label_token.value
                    else:
                        # Constant referent
                        const_token = self._expect(CGIFTokenType.IDENTIFIER)
                        node.attributes['constant'] = const_token.value
                    
                    self._expect(CGIFTokenType.RBRACKET)
                    return node
                else:
                    # This might be start of a context - backtrack and parse as CG
                    self.position -= 1
                    self.current_token = self.tokens[self.position]
                    
                    node = CGIFParseNode('context')
                    cg_content = self._parse_cg()
                    node.children.append(cg_content)
                    
                    self._expect(CGIFTokenType.RBRACKET)
                    return node
            else:
                # Context [CG]
                node = CGIFParseNode('context')
                cg_content = self._parse_cg()
                node.children.append(cg_content)
                
                self._expect(CGIFTokenType.RBRACKET)
                return node
    
    def _parse_relation(self) -> CGIFParseNode:
        """Parse relation (Type ?x ?y) or actor (Type ?x ?y | ?z)."""
        self._expect(CGIFTokenType.LPAREN)
        
        type_token = self._expect(CGIFTokenType.IDENTIFIER)
        
        node = CGIFParseNode('relation')
        node.value = type_token.value
        
        # Parse arguments
        while (self.current_token.type in [CGIFTokenType.QUESTION, CGIFTokenType.IDENTIFIER, 
                                          CGIFTokenType.NUMERAL, CGIFTokenType.STRING]):
            arg = self._parse_reference()
            node.children.append(arg)
            
            # Check for actor separator |
            if self.current_token.type == CGIFTokenType.PIPE:
                self._advance()  # Skip |
                node.type = 'actor'
                # Parse output argument
                output_arg = self._parse_reference()
                node.attributes['output'] = output_arg
                break
        
        self._expect(CGIFTokenType.RPAREN)
        return node
    
    def _parse_reference(self) -> CGIFParseNode:
        """Parse reference ?x, identifier, numeral, or string."""
        if self.current_token.type == CGIFTokenType.QUESTION:
            self._advance()  # Skip ?
            label_token = self._expect(CGIFTokenType.IDENTIFIER)
            
            node = CGIFParseNode('bound_label')
            node.value = label_token.value
            return node
        
        elif self.current_token.type == CGIFTokenType.IDENTIFIER:
            token = self.current_token
            self._advance()
            
            node = CGIFParseNode('constant')
            node.value = token.value
            return node
        
        elif self.current_token.type == CGIFTokenType.NUMERAL:
            token = self.current_token
            self._advance()
            
            node = CGIFParseNode('numeral')
            node.value = token.value
            return node
        
        elif self.current_token.type == CGIFTokenType.STRING:
            token = self.current_token
            self._advance()
            
            node = CGIFParseNode('string')
            node.value = token.value
            return node
        
        else:
            raise ValueError(f"Unexpected token {self.current_token.type} at position {self.current_token.position}")
    
    def _convert_to_egi(self, node: CGIFParseNode, egi: RelationalGraphWithCuts, area_id: str) -> RelationalGraphWithCuts:
        """Convert parse tree node to EGI elements immutably and return updated egi."""
        if node.type == 'cg':
            # Process all children in current area
            for child in node.children:
                egi = self._convert_to_egi(child, egi, area_id)
            return egi
        
        if node.type == 'type_concept':
            # Create vertex and type relation
            if 'defining_label' in node.attributes:
                # [Type: *x] - create vertex with defining label (generic)
                vertex_id = f"v_{node.attributes['defining_label']}"
                vertex = Vertex(id=vertex_id, label=None, is_generic=True)
                egi = egi.with_vertex_in_context(vertex, area_id)
                # Create type relation edge attached to the vertex
                type_edge_id = f"e_{node.value}_{len(egi.E)}"
                type_edge = Edge(id=type_edge_id)
                egi = egi.with_edge(type_edge, (vertex_id,), node.value, context_id=area_id)
                return egi
            
            if 'constant' in node.attributes:
                # [Type: John] - create constant vertex and type relation
                const_name = node.attributes['constant']
                vertex_id = f"v_{const_name}"
                vertex = Vertex(id=vertex_id, label=const_name, is_generic=False)
                egi = egi.with_vertex_in_context(vertex, area_id)
                # Create type relation edge
                type_edge_id = f"e_{node.value}_{len(egi.E)}"
                type_edge = Edge(id=type_edge_id)
                egi = egi.with_edge(type_edge, (vertex_id,), node.value, context_id=area_id)
                return egi
        
        if node.type == 'existential_concept':
            # [*x] - create generic vertex
            vertex_id = f"v_{node.value}"
            vertex = Vertex(id=vertex_id, label=None, is_generic=True)
            egi = egi.with_vertex_in_context(vertex, area_id)
            return egi
        
        if node.type == 'relation':
            # (Type ?x ?y) - create edge
            # Ensure constant vertices exist; bound labels reference existing by convention
            vertex_refs = []
            for arg in node.children:
                if arg.type == 'bound_label':
                    vertex_refs.append(f"v_{arg.value}")
                elif arg.type == 'constant':
                    vertex_id = f"v_{arg.value}"
                    if not any(v.id == vertex_id for v in egi.V):
                        vertex = Vertex(id=vertex_id, label=arg.value, is_generic=False)
                        egi = egi.with_vertex_in_context(vertex, area_id)
                    vertex_refs.append(vertex_id)
            edge_id = f"e_{node.value}_{len(egi.E)}"
            edge = Edge(id=edge_id)
            egi = egi.with_edge(edge, tuple(vertex_refs), node.value, context_id=area_id)
            return egi
        
        if node.type == 'negation':
            # ~[CG] - create cut
            cut_id = f"c_neg_{len(egi.Cut)}"
            cut = Cut(id=cut_id)
            egi = egi.with_cut(cut, context_id=area_id)
            # Process negated content in the new cut
            for child in node.children:
                egi = self._convert_to_egi(child, egi, cut_id)
            return egi
        
        if node.type == 'context':
            # [CG] - process content in current area
            for child in node.children:
                egi = self._convert_to_egi(child, egi, area_id)
            return egi
        
        return egi


# Factory function
def parse_cgif(cgif_text: str) -> RelationalGraphWithCuts:
    """Parse CGIF text into EGI structure."""
    parser = CGIFParser(cgif_text)
    return parser.parse()
