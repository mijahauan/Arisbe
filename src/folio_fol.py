"""
FOLIO first-order-logic: parse, and decide entailment via Z3.

FOLIO (Han et al. 2022, github.com/Yale-LILY/FOLIO) pairs natural-language premises +
conclusion with human-authored **FOL annotations** and a 3-valued label: ``True`` (the
conclusion is entailed by the premises), ``False`` (its negation is entailed — the
conclusion contradicts the premises), ``Uncertain`` (neither). That trichotomy is exactly
Arisbe's three-valued stance.

This module is the **authoritative-verdict** half of the FOLIO evaluation (the "Both" engine
decision): a small recursive-descent parser for FOLIO's FOL syntax and a direct compiler to
Z3 (full first-order: ``∀ ∃ ¬ ∧ ∨ → ↔ ⊕`` + constants + n-ary predicates). The verdict is
decided soundly:

    entailed   (True)      ⟺  (⋀premises ∧ ¬conclusion) is UNSAT
    contradicts(False)     ⟺  (⋀premises ∧  conclusion) is UNSAT
    otherwise  (Uncertain)

Compiling FOLIO's FOL **directly** to Z3 — rather than through Arisbe's EG→FOPL string,
which drops quantifier scope to free variables — is deliberate (see CURRENT_PLAN step 2): the
EG is for the *pictures* and round-trip fidelity (built separately, via CLIF), not the
verdict. Relation names become uninterpreted functions over one sort U; a term is a variable
iff a quantifier binds it in scope, else a constant — so a shared constant (``bonnie``) links
premises automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only where z3 is absent
    Z3_AVAILABLE = False


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Atom:
    pred: str
    args: Tuple[str, ...]


@dataclass(frozen=True)
class Not:
    f: "Formula"


@dataclass(frozen=True)
class BinOp:
    op: str               # "and" | "or" | "implies" | "iff" | "xor"
    left: "Formula"
    right: "Formula"


@dataclass(frozen=True)
class Quant:
    kind: str             # "forall" | "exists"
    var: str
    body: "Formula"


Formula = Union[Atom, Not, BinOp, Quant]


class FolioParseError(ValueError):
    """A FOLIO-FOL string Arisbe's parser could not read (reported, never guessed)."""


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Logical operators (single Unicode glyphs) + structural punctuation.
_OPS = {
    "∀": "FORALL", "∃": "EXISTS", "¬": "NOT",
    "∧": "AND", "∨": "OR", "→": "IMPLIES",
    "↔": "IFF", "⟷": "IFF", "⊕": "XOR",
    "(": "LP", ")": "RP", ",": "COMMA",
}
# Whitespace-like: spaces and a few stray separators seen in the corpus ('.'),
# which appear as sentence punctuation, never inside a logical token.
_SKIP = set(" \t\n\r.")


def tokenize(s: str) -> List[Tuple[str, str]]:
    toks: List[Tuple[str, str]] = []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch in _SKIP:
            i += 1
            continue
        if ch in _OPS:
            toks.append((_OPS[ch], ch))
            i += 1
            continue
        # An identifier: a run of anything that is not an operator/skip char.
        # Liberal on purpose — hyphenated predicate names ("Warm-blooded") and the
        # like are one name.
        j = i
        while j < n and s[j] not in _OPS and s[j] not in _SKIP:
            j += 1
        toks.append(("NAME", s[i:j]))
        i = j
    toks.append(("EOF", ""))
    return toks


# ---------------------------------------------------------------------------
# Parser (recursive descent; precedence iff/xor < implies < or < and < unary)
# ---------------------------------------------------------------------------

class _Parser:
    def __init__(self, toks: List[Tuple[str, str]]):
        self.toks = toks
        self.i = 0

    def _peek(self) -> Tuple[str, str]:
        return self.toks[self.i]

    def _eat(self, kind: Optional[str] = None) -> Tuple[str, str]:
        t = self.toks[self.i]
        if kind is not None and t[0] != kind:
            raise FolioParseError(f"expected {kind}, got {t[0]} {t[1]!r}")
        self.i += 1
        return t

    def parse(self) -> Formula:
        f = self._iff()
        if self._peek()[0] != "EOF":
            raise FolioParseError(f"trailing input at {self._peek()[1]!r}")
        return f

    def _iff(self) -> Formula:
        left = self._implies()
        while self._peek()[0] in ("IFF", "XOR"):
            op = "iff" if self._eat()[0] == "IFF" else "xor"
            left = BinOp(op, left, self._implies())
        return left

    def _implies(self) -> Formula:
        left = self._or()
        if self._peek()[0] == "IMPLIES":
            self._eat()
            return BinOp("implies", left, self._implies())   # right-assoc
        return left

    def _or(self) -> Formula:
        left = self._and()
        while self._peek()[0] == "OR":
            self._eat()
            left = BinOp("or", left, self._and())
        return left

    def _and(self) -> Formula:
        left = self._unary()
        while self._peek()[0] == "AND":
            self._eat()
            left = BinOp("and", left, self._unary())
        return left

    def _unary(self) -> Formula:
        t = self._peek()[0]
        if t == "NOT":
            self._eat()
            return Not(self._unary())
        if t in ("FORALL", "EXISTS"):
            kind = "forall" if self._eat()[0] == "FORALL" else "exists"
            var = self._eat("NAME")[1]
            # Quantifier scopes maximally to its right (the conventional reading;
            # FOLIO parenthesizes bodies, so this is unambiguous in practice).
            return Quant(kind, var, self._iff())
        return self._primary()

    def _primary(self) -> Formula:
        if self._peek()[0] == "LP":
            self._eat("LP")
            f = self._iff()
            self._eat("RP")
            return f
        name = self._eat("NAME")[1]
        self._eat("LP")
        args: List[str] = []
        if self._peek()[0] != "RP":
            args.append(self._eat("NAME")[1])
            while self._peek()[0] == "COMMA":
                self._eat("COMMA")
                args.append(self._eat("NAME")[1])
        self._eat("RP")
        return Atom(name, tuple(args))


def parse_fol(s: str) -> Formula:
    """Parse a FOLIO-FOL string to an AST; raise ``FolioParseError`` on failure."""
    return _Parser(tokenize(s)).parse()


# ---------------------------------------------------------------------------
# CLIF emission — the bridge to an EGI (the *picture*)
# ---------------------------------------------------------------------------
#
# The verdict goes straight to Z3 (above); the picture goes through CLIF, because
# clif_parser_dau is the constant-robust EGI front-end (the chapter18 FOPL parser rejects
# constants).  clif_parser_dau supports forall/exists/not/and/or/iff/if directly; only ⊕
# needs desugaring (a ⊕ b ≡ ¬(a ↔ b)).

_CLIF_KW = {"and": "and", "or": "or", "implies": "if", "iff": "iff"}


def ast_to_clif(f: Formula) -> str:
    """Render a FOLIO AST as a CLIF sentence (the input to ``clif_parser_dau``)."""
    if isinstance(f, Atom):
        return "(" + " ".join([f.pred, *f.args]) + ")"
    if isinstance(f, Not):
        return "(not " + ast_to_clif(f.f) + ")"
    if isinstance(f, BinOp):
        if f.op == "xor":                          # a ⊕ b ≡ ¬(a ↔ b)
            return "(not (iff " + ast_to_clif(f.left) + " " + ast_to_clif(f.right) + "))"
        return ("(" + _CLIF_KW[f.op] + " "
                + ast_to_clif(f.left) + " " + ast_to_clif(f.right) + ")")
    if isinstance(f, Quant):
        kw = "forall" if f.kind == "forall" else "exists"
        return "(" + kw + " (" + f.var + ") " + ast_to_clif(f.body) + ")"
    raise FolioParseError(f"uncliffable node {type(f).__name__}")


def folio_fol_to_egi(fol_str: str):
    """Parse a FOLIO-FOL string and build its EGI (the drawable graph) via CLIF."""
    from clif_parser_dau import parse_clif
    return parse_clif(ast_to_clif(parse_fol(fol_str)))


# ---------------------------------------------------------------------------
# Z3 compilation + the entailment decision
# ---------------------------------------------------------------------------

class _Z3Compiler:
    """Compile a FOLIO AST to Z3, sharing relation symbols + constants by name."""

    def __init__(self):
        self.U = z3.DeclareSort("U")
        self._funcs: Dict[Tuple[str, int], z3.FuncDeclRef] = {}
        self._consts: Dict[str, z3.ExprRef] = {}

    def _func(self, name: str, arity: int) -> z3.FuncDeclRef:
        key = (name, arity)
        if key not in self._funcs:
            self._funcs[key] = z3.Function(name, *([self.U] * arity), z3.BoolSort())
        return self._funcs[key]

    def _term(self, name: str, env: Dict[str, z3.ExprRef]) -> z3.ExprRef:
        if name in env:                       # bound by an enclosing quantifier
            return env[name]
        if name not in self._consts:          # a free term is a shared constant
            self._consts[name] = z3.Const(name, self.U)
        return self._consts[name]

    def compile(self, f: Formula, env: Dict[str, z3.ExprRef]) -> z3.ExprRef:
        if isinstance(f, Atom):
            return self._func(f.pred, len(f.args))(*[self._term(a, env) for a in f.args])
        if isinstance(f, Not):
            return z3.Not(self.compile(f.f, env))
        if isinstance(f, BinOp):
            l, r = self.compile(f.left, env), self.compile(f.right, env)
            return {"and": z3.And, "or": z3.Or, "implies": z3.Implies,
                    "iff": lambda a, b: a == b, "xor": z3.Xor}[f.op](l, r)
        if isinstance(f, Quant):
            v = z3.Const(f.var, self.U)
            body = self.compile(f.body, {**env, f.var: v})
            return z3.ForAll([v], body) if f.kind == "forall" else z3.Exists([v], body)
        raise FolioParseError(f"uncompilable node {type(f).__name__}")


@dataclass
class EntailmentResult:
    verdict: str            # "True" | "False" | "Uncertain" | "Unparsed" | "Unknown"
    detail: str = ""
    parsed: bool = True

    @property
    def decided(self) -> bool:
        return self.verdict in ("True", "False", "Uncertain")


def decide_entailment(
    premise_fols: List[str], conclusion_fol: str, *, timeout_ms: int = 5000,
) -> EntailmentResult:
    """Decide FOLIO entailment with Z3 — the authoritative verdict.

    ``True`` if the premises entail the conclusion, ``False`` if they entail its
    negation, ``Uncertain`` if neither (both branches sat). ``Unparsed`` if any formula
    is unreadable; ``Unknown`` if Z3 times out on a branch (full FOL is undecidable —
    rare for FOLIO's small instances).
    """
    if not Z3_AVAILABLE:
        raise ImportError("z3-solver is required for FOLIO entailment")
    try:
        prem_asts = [parse_fol(p) for p in premise_fols]
        concl_ast = parse_fol(conclusion_fol)
    except FolioParseError as exc:
        return EntailmentResult("Unparsed", str(exc), parsed=False)

    comp = _Z3Compiler()
    env: Dict[str, z3.ExprRef] = {}
    premises = z3.And(*[comp.compile(p, env) for p in prem_asts]) if prem_asts else z3.BoolVal(True)
    concl = comp.compile(concl_ast, env)

    def unsat_with(extra) -> Optional[bool]:
        s = z3.Solver()
        s.set("timeout", timeout_ms)
        s.add(premises, extra)
        r = s.check()
        return True if r == z3.unsat else (False if r == z3.sat else None)

    entailed = unsat_with(z3.Not(concl))      # premises ∧ ¬C unsat ⟺ entailed
    if entailed is None:
        return EntailmentResult("Unknown", "Z3 timeout on the entailment branch")
    if entailed:
        return EntailmentResult("True", "premises ∧ ¬conclusion is UNSAT")
    contradicts = unsat_with(concl)           # premises ∧ C unsat ⟺ contradicted
    if contradicts is None:
        return EntailmentResult("Unknown", "Z3 timeout on the contradiction branch")
    if contradicts:
        return EntailmentResult("False", "premises ∧ conclusion is UNSAT")
    return EntailmentResult("Uncertain", "neither the conclusion nor its negation is entailed")
