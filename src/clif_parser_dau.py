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
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from frozendict import frozendict

from egi_core_dau import (
    AlphabetDAU,
    Cut,
    Edge,
    ElementID,
    RelationalGraphWithCuts,
    RelationName,
    Vertex,
    VertexSequence,
    create_cut,
    create_edge,
    create_empty_graph,
    create_vertex,
)


class CLIFTokenType(Enum):
    """Token types for CLIF lexical analysis."""

    LPAREN = "LPAREN"  # (
    RPAREN = "RPAREN"  # )
    IDENTIFIER = "IDENTIFIER"  # predicate names, variables
    FORALL = "FORALL"  # forall
    EXISTS = "EXISTS"  # exists
    NOT = "NOT"  # not
    AND = "AND"  # and
    OR = "OR"  # or
    IFF = "IFF"  # iff
    IF = "IF"  # if
    COMMENT = "COMMENT"  # ;; comment
    CL_TEXT = "CL_TEXT"  # cl-text
    CL_IMPORTS = "CL_IMPORTS"  # cl-imports
    CL_MODULE = "CL_MODULE"  # cl-module
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

            if char == "(":
                self.tokens.append(CLIFToken(CLIFTokenType.LPAREN, "(", self.position))
                self.position += 1
            elif char == ")":
                self.tokens.append(CLIFToken(CLIFTokenType.RPAREN, ")", self.position))
                self.position += 1
            elif (
                char == ";"
                and self.position + 1 < len(self.text)
                and self.text[self.position + 1] == ";"
            ):
                self._read_comment()
            elif char == '"':
                self._read_quoted_identifier()
            else:
                self._read_identifier()

        self.tokens.append(CLIFToken(CLIFTokenType.EOF, "", self.position))
        return self.tokens

    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while self.position < len(self.text) and self.text[self.position] in " \t\n\r":
            self.position += 1

    def _read_comment(self):
        """Read comment starting with ;;"""
        start = self.position
        while self.position < len(self.text) and self.text[self.position] != "\n":
            self.position += 1
        comment_text = self.text[start : self.position]
        self.tokens.append(CLIFToken(CLIFTokenType.COMMENT, comment_text, start))

    def _read_identifier(self):
        """Read identifier (predicate name, variable, keyword)."""
        start = self.position

        # Read identifier characters
        while (
            self.position < len(self.text)
            and self.text[self.position] not in " \t\n\r()"
        ):
            self.position += 1

        identifier = self.text[start : self.position]

        # Check for keywords
        token_type = {
            "forall": CLIFTokenType.FORALL,
            "exists": CLIFTokenType.EXISTS,
            "not": CLIFTokenType.NOT,
            "and": CLIFTokenType.AND,
            "or": CLIFTokenType.OR,
            "iff": CLIFTokenType.IFF,
            "if": CLIFTokenType.IF,
            "cl-text": CLIFTokenType.CL_TEXT,
            "cl-imports": CLIFTokenType.CL_IMPORTS,
            "cl-module": CLIFTokenType.CL_MODULE,
        }.get(identifier.lower(), CLIFTokenType.IDENTIFIER)

        self.tokens.append(CLIFToken(token_type, identifier, start))

    def _read_quoted_identifier(self):
        """Read a double-quoted identifier and unquote it (supports simple escape of \" inside)."""
        start = self.position
        # skip opening quote
        self.position += 1
        buf = []
        while self.position < len(self.text):
            ch = self.text[self.position]
            if (
                ch == "\\"
                and self.position + 1 < len(self.text)
                and self.text[self.position + 1] == '"'
            ):
                buf.append('"')
                self.position += 2
                continue
            if ch == '"':
                # closing quote
                self.position += 1
                break
            buf.append(ch)
            self.position += 1
        identifier = "".join(buf)
        self.tokens.append(CLIFToken(CLIFTokenType.IDENTIFIER, identifier, start))


@dataclass
class CLIFParseNode:
    """Node in CLIF parse tree."""

    type: str
    value: Optional[str] = None
    children: List["CLIFParseNode"] = None

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
        """Parse CLIF text into EGI structure.

        Handles single expressions, multiple top-level sentences
        (conjuncted on the sheet), and ``cl-text`` wrappers used
        by the COLORE repository.
        """
        self.tokens = self.lexer.tokenize()
        # Strip comment tokens so the parser never sees them
        self.tokens = [t for t in self.tokens if t.type != CLIFTokenType.COMMENT]
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else None

        # Parse all top-level expressions (multi-sentence support)
        sentences: List[CLIFParseNode] = []
        while self.current_token and self.current_token.type != CLIFTokenType.EOF:
            sentences.append(self._parse_expression())

        # Convert parse trees to EGI — all sentences conjuncted on sheet
        egi = create_empty_graph()
        for sentence in sentences:
            egi = self._convert_to_egi(sentence, egi, egi.sheet)
        # Populate AlphabetDAU and rho
        egi = self._finalize_alphabet_and_rho(egi)
        return egi

    def _advance(self):
        """Move to next token."""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]

    def _expect(self, token_type: CLIFTokenType) -> CLIFToken:
        """Expect specific token type."""
        if self.current_token.type != token_type:
            raise ValueError(
                f"Expected {token_type}, got {self.current_token.type} at position {self.current_token.position}"
            )
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
            return CLIFParseNode("constant", token.value)
        else:
            raise ValueError(
                f"Unexpected token {self.current_token.type} at position {self.current_token.position}"
            )

    def _parse_compound_expression(self) -> CLIFParseNode:
        """Parse compound expression starting with (."""
        self._expect(CLIFTokenType.LPAREN)

        if self.current_token.type == CLIFTokenType.FORALL:
            return self._parse_quantification("forall")
        elif self.current_token.type == CLIFTokenType.EXISTS:
            return self._parse_quantification("exists")
        elif self.current_token.type == CLIFTokenType.NOT:
            return self._parse_negation()
        elif self.current_token.type == CLIFTokenType.AND:
            return self._parse_conjunction()
        elif self.current_token.type == CLIFTokenType.OR:
            return self._parse_disjunction()
        elif self.current_token.type == CLIFTokenType.IF:
            return self._parse_conditional()
        elif self.current_token.type == CLIFTokenType.IFF:
            return self._parse_biconditional()
        elif self.current_token.type in (
            CLIFTokenType.CL_TEXT, CLIFTokenType.CL_MODULE,
        ):
            return self._parse_cl_text()
        elif self.current_token.type == CLIFTokenType.CL_IMPORTS:
            return self._parse_cl_imports()
        elif self.current_token.type == CLIFTokenType.IDENTIFIER:
            return self._parse_atomic_formula()
        else:
            raise ValueError(
                f"Unexpected token in compound expression: {self.current_token.type}"
            )

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
        node.children = [
            CLIFParseNode(
                "variables", None, [CLIFParseNode("variable", var) for var in variables]
            ),
            body,
        ]
        return node

    def _parse_negation(self) -> CLIFParseNode:
        """Parse negation (not ...)."""
        self._advance()  # Skip 'not'

        body = self._parse_expression()
        self._expect(CLIFTokenType.RPAREN)

        node = CLIFParseNode("not")
        node.children = [body]
        return node

    def _parse_conjunction(self) -> CLIFParseNode:
        """Parse conjunction (and ...)."""
        self._advance()  # Skip 'and'

        conjuncts = []
        while self.current_token.type != CLIFTokenType.RPAREN:
            conjuncts.append(self._parse_expression())

        self._expect(CLIFTokenType.RPAREN)

        node = CLIFParseNode("and")
        node.children = conjuncts
        return node

    def _parse_disjunction(self) -> CLIFParseNode:
        """Parse disjunction (or ...)."""
        self._advance()  # Skip 'or'

        disjuncts = []
        while self.current_token.type != CLIFTokenType.RPAREN:
            disjuncts.append(self._parse_expression())

        self._expect(CLIFTokenType.RPAREN)

        node = CLIFParseNode("or")
        node.children = disjuncts
        return node

    def _parse_conditional(self) -> CLIFParseNode:
        """Parse conditional (if P Q) — material implication."""
        self._advance()  # Skip 'if'

        antecedent = self._parse_expression()
        consequent = self._parse_expression()
        self._expect(CLIFTokenType.RPAREN)

        node = CLIFParseNode("if")
        node.children = [antecedent, consequent]
        return node

    def _parse_biconditional(self) -> CLIFParseNode:
        """Parse biconditional (iff P Q)."""
        self._advance()  # Skip 'iff'

        left = self._parse_expression()
        right = self._parse_expression()
        self._expect(CLIFTokenType.RPAREN)

        node = CLIFParseNode("iff")
        node.children = [left, right]
        return node

    def _parse_cl_text(self) -> CLIFParseNode:
        """Parse (cl-text name sentence...) — COLORE wrapper.

        Extracts the inner sentences and returns them as a conjunction.
        The name is stored as the node value for metadata purposes.
        """
        self._advance()  # Skip 'cl-text' / 'cl-module'

        # Optional name (identifier)
        name = None
        if self.current_token.type == CLIFTokenType.IDENTIFIER:
            name = self.current_token.value
            self._advance()

        # Parse inner sentences until closing paren
        sentences: List[CLIFParseNode] = []
        while self.current_token.type != CLIFTokenType.RPAREN:
            if self.current_token.type == CLIFTokenType.EOF:
                raise ValueError("Unexpected EOF inside cl-text block")
            sentences.append(self._parse_expression())

        self._expect(CLIFTokenType.RPAREN)

        if len(sentences) == 1:
            return sentences[0]
        node = CLIFParseNode("and", value=name)
        node.children = sentences
        return node

    def _parse_cl_imports(self) -> CLIFParseNode:
        """Parse (cl-imports uri) — skip import directives.

        Returns a no-op node; actual file loading is handled at a
        higher level by the ontology loader.
        """
        self._advance()  # Skip 'cl-imports'
        # Read and discard the URI or name
        if self.current_token.type == CLIFTokenType.IDENTIFIER:
            self._advance()
        self._expect(CLIFTokenType.RPAREN)
        return CLIFParseNode("noop")

    def _parse_atomic_formula(self) -> CLIFParseNode:
        """Parse atomic formula (P x y)."""
        predicate = self.current_token.value
        self._advance()

        arguments = []
        while self.current_token.type == CLIFTokenType.IDENTIFIER:
            arguments.append(self.current_token.value)
            self._advance()

        self._expect(CLIFTokenType.RPAREN)

        node = CLIFParseNode("atomic")
        node.value = predicate
        node.children = [CLIFParseNode("argument", arg) for arg in arguments]
        return node

    def _convert_to_egi(
        self, node: CLIFParseNode, egi: RelationalGraphWithCuts, area_id: str
    ) -> RelationalGraphWithCuts:
        """Convert parse tree node to EGI elements immutably and return updated egi."""
        if node.type == "atomic":
            # Create vertices for arguments
            vertex_ids = []
            for arg_node in node.children:
                vertex_id = f"v_{arg_node.value}"
                if not any(v.id == vertex_id for v in egi.V):
                    # Determine if this is a constant or variable
                    # In CLIF, quoted strings and capitalized identifiers are typically constants
                    # Lowercase identifiers are typically variables
                    is_constant = (
                        arg_node.value and 
                        (arg_node.value[0].isupper() or arg_node.value.startswith('"'))
                    )
                    
                    if is_constant:
                        # Constants have label and is_generic=False
                        vertex = Vertex(
                            id=vertex_id, label=arg_node.value, is_generic=False
                        )
                    else:
                        # Variables have label=None and is_generic=True
                        vertex = Vertex(
                            id=vertex_id, label=None, is_generic=True
                        )
                    egi = egi.with_vertex_in_context(vertex, area_id)
                vertex_ids.append(vertex_id)
            # Create edge for predicate in same area
            edge_id = f"e_{node.value}_{len(egi.E)}"
            edge = Edge(id=edge_id)
            egi = egi.with_edge(edge, tuple(vertex_ids), node.value, context_id=area_id)
            return egi

        if node.type == "not":
            # Create cut for negation
            cut_id = f"c_not_{len(egi.Cut)}"
            cut = Cut(id=cut_id)
            egi = egi.with_cut(cut, context_id=area_id)
            # Process negated content in the new cut's area
            for child in node.children:
                egi = self._convert_to_egi(child, egi, area_id=cut.id)
            return egi

        if node.type == "and":
            # Conjunction - all children in same area
            for child in node.children:
                egi = self._convert_to_egi(child, egi, area_id)
            return egi

        if node.type == "or":
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

        if node.type == "if":
            # Material conditional: (if P Q) = ~[ P ~[ Q ] ]
            antecedent, consequent = node.children
            outer_cut_id = f"c_if_outer_{len(egi.Cut)}"
            outer_cut = Cut(id=outer_cut_id)
            egi = egi.with_cut(outer_cut, context_id=area_id)
            # Antecedent goes in the outer cut
            egi = self._convert_to_egi(antecedent, egi, outer_cut_id)
            # Inner cut for consequent
            inner_cut_id = f"c_if_inner_{len(egi.Cut)}"
            inner_cut = Cut(id=inner_cut_id)
            egi = egi.with_cut(inner_cut, context_id=outer_cut_id)
            egi = self._convert_to_egi(consequent, egi, inner_cut_id)
            return egi

        if node.type == "iff":
            # Biconditional: (iff P Q) = (and (if P Q) (if Q P))
            left, right = node.children
            # Forward: ~[ P ~[ Q ] ]
            fwd_node = CLIFParseNode("if")
            fwd_node.children = [left, right]
            egi = self._convert_to_egi(fwd_node, egi, area_id)
            # Backward: ~[ Q ~[ P ] ]
            bwd_node = CLIFParseNode("if")
            bwd_node.children = [right, left]
            egi = self._convert_to_egi(bwd_node, egi, area_id)
            return egi

        if node.type == "forall":
            # Universal quantification: (forall (x⃗) body)  ≡  ¬∃x⃗ ¬body.
            #
            # A material-conditional or negation body already supplies the
            # enclosing negative context that makes a bound line read universally,
            # and places the bound line there:
            #   - (if A B) = ~[ A ~[ B ] ]: the consequent's cut nests inside the
            #     antecedent's, so a variable shared by A and B settles in the
            #     *outer* (negative) cut — the canonical subsumption scroll
            #     ~[ *x (A x) ~[ (B x) ] ].  Universal. ✓
            #   - (not P) = ~[ P ]: the variable settles in that cut.  Universal. ✓
            # We keep those established shapes untouched.
            #
            # Every *other* body fails to place the binder negatively, so the old
            # "implicit" handling (drop the binder, convert the body here) collapsed
            # the universal to an existential — a line whose shallowest occurrence
            # is positive IS ∃.  This bit not only positive atoms / conjunctions /
            # existentials but also (iff A B): its two scrolls are *siblings*, so a
            # variable shared across them settles at their least common ancestor —
            # the sheet (positive) — not in either cut.  For all of these, build the
            # double cut explicitly: ~[ *x⃗ ~[ body ] ].  The binder vertices in the
            # outer (negative) cut make the line universal; the body in the inner
            # cut keeps its own existentials existential (back to even depth).
            var_names: List[str] = []
            bodies: List[CLIFParseNode] = []
            for child in node.children:
                if child.type == "variables":
                    var_names.extend(vn.value for vn in child.children)
                else:
                    bodies.append(child)

            body_supplies_negation = (
                len(bodies) == 1 and bodies[0].type in ("if", "not")
            )
            if body_supplies_negation:
                for child in bodies:
                    egi = self._convert_to_egi(child, egi, area_id)
                return egi

            # ~[ *x⃗ ~[ body ] ]
            outer_cut_id = f"c_all_outer_{len(egi.Cut)}"
            outer_cut = Cut(id=outer_cut_id)
            egi = egi.with_cut(outer_cut, context_id=area_id)
            # The bound lines live in the outer (negative) cut — their universal
            # position.  Pre-create them here so the body's atoms in the inner cut
            # wire to these existing vertices rather than minting fresh ones.
            for name in var_names:
                vertex_id = f"v_{name}"
                if not any(v.id == vertex_id for v in egi.V):
                    egi = egi.with_vertex_in_context(
                        Vertex(id=vertex_id, label=None, is_generic=True),
                        outer_cut_id,
                    )
            inner_cut_id = f"c_all_inner_{len(egi.Cut)}"
            inner_cut = Cut(id=inner_cut_id)
            egi = egi.with_cut(inner_cut, context_id=outer_cut_id)
            for child in bodies:
                egi = self._convert_to_egi(child, egi, inner_cut_id)
            return egi

        if node.type == "exists":
            # Existential quantification: (exists (x) body)
            # In EG, existentials are the default — a generic vertex
            # on the sheet (or in the current area) IS the existential.
            for child in node.children:
                if child.type != "variables":
                    egi = self._convert_to_egi(child, egi, area_id)
            return egi

        if node.type == "noop":
            # Skip (e.g., cl-imports directives)
            return egi

        return egi

    def _finalize_alphabet_and_rho(
        self, graph: RelationalGraphWithCuts
    ) -> RelationalGraphWithCuts:
        """Compute AlphabetDAU and rho from the graph, excluding relation-name collisions from constants."""
        # Relation names and arities from edges
        relation_names: Set[str] = set()
        ar_map: Dict[str, int] = {}
        for eid, name in graph.rel.items():
            relation_names.add(name)
            ar_map[name] = max(ar_map.get(name, 0), len(graph.nu.get(eid, tuple())))

        # Candidate constants from non-generic vertex labels
        candidate_constants: Set[str] = set()
        for v in graph.V:
            if not getattr(v, "is_generic", True) and getattr(v, "label", None):
                candidate_constants.add(v.label)  # type: ignore[arg-type]

        # Disjoint constants
        constants: Set[str] = {
            c for c in candidate_constants if c not in relation_names
        }

        # rho: only map vertices labeled with names in constants; others None
        rho_map: Dict[str, Optional[str]] = {}
        for v in graph.V:
            if not getattr(v, "is_generic", True) and getattr(v, "label", None) and v.label in constants:  # type: ignore[attr-defined]
                rho_map[v.id] = v.label  # type: ignore[assignment]
            else:
                rho_map[v.id] = None

        # ar(c) = 1 for constants
        for c in constants:
            ar_map[c] = 1

        alphabet = AlphabetDAU(
            C=frozenset(constants),
            F=frozenset(),
            R=frozenset(relation_names),
            ar=frozendict(ar_map),
        ).with_defaults()

        return RelationalGraphWithCuts(
            V=graph.V,
            E=graph.E,
            Cut=graph.Cut,
            area=graph.area,
            nu=graph.nu,
            rel=graph.rel,
            sheet=graph.sheet,
            alphabet=alphabet,
            rho=frozendict(rho_map),
        )


# Factory function
def parse_clif(clif_text: str) -> RelationalGraphWithCuts:
    """Parse CLIF text into EGI structure."""
    parser = CLIFParser(clif_text)
    return parser.parse()
