"""
A bounded finite-model finder — the model-construction half of the FOLIO coverage lever.

The disjunctive case-split lever (``folio_native._refutes_cases``) raises the **refutation**
half: it proves more entailments (``True`` / ``False``). The dual question — *non*-entailment,
and the ``Uncertain`` verdict the native engine could never soundly emit — needs the opposite
capability: **exhibit an actual model**.

    M ⊭ C   is witnessed by a model of  M ∪ {¬C}   (premises hold, conclusion fails)
    M ⊭ ¬C  is witnessed by a model of  M ∪ { C}   (premises hold, conclusion holds)

If *both* models exist, neither C nor ¬C is entailed — the answer is genuinely ``Uncertain``,
and the two surviving models *prove* it. Finding a model is a **positive certificate**: it is
sound regardless of how incomplete the entailment prover is. (Failing to find one up to the
bound certifies nothing — so model-finding only ever yields non-entailment / ``Uncertain``,
never an entailment.)

FOLIO's fragment is function-free relational FOL (no equality), so a finite model is a finite
domain + an extension for each predicate. We find one the MACE way:

* **Domain** = the constants of M, C (taken **distinct** — a sound *unique-names* restriction:
  a model found over distinct constants is a real model; only models that *force* two
  constants equal are missed, lowering coverage, never soundness) + a few anonymous witnesses
  for existentials.
* **Ground** every quantifier over that finite domain (``∀`` → conjunction, ``∃`` → disjunction),
  leaving a purely propositional formula over ground atoms.
* **Tseitin → CNF → DPLL** (Arisbe's own small solver, *not* Z3 — this is the bounded native
  engine): a satisfying assignment is a model; its true ground atoms are the predicate extensions.

Bounded by an anonymous-witness cap and a DPLL node budget; on exhaustion it returns ``None``
(cannot certify → the caller abstains). Everything it *does* return is a genuine model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from folio_fol import Atom, BinOp, Formula, Not, Quant

# Bounds — FOLIO instances are small; these keep the search honest and quick.
MAX_ANON_WITNESSES = 2      # anonymous domain elements beyond the named constants
MAX_DOMAIN = 7             # absolute cap on |domain| (constants + witnesses)
DPLL_NODE_BUDGET = 40000   # per satisfiability call; exceeded ⇒ abstain (sound)


@dataclass
class Model:
    """A finite model: a domain, the constant→element map, and the true ground atoms."""
    domain_size: int
    constants: Dict[str, int]
    true_atoms: FrozenSet[Tuple[str, Tuple[int, ...]]]

    def describe(self, limit: int = 8) -> str:
        atoms = sorted(f"{p}({','.join(map(str, a))})" for p, a in self.true_atoms)
        shown = ", ".join(atoms[:limit]) + (" …" if len(atoms) > limit else "")
        return f"|D|={self.domain_size}; {{{shown}}}"


class _BudgetExceeded(Exception):
    """The DPLL search ran past its node budget — treated as 'no model found' (sound)."""


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------

def _signature(asts: List[Formula]) -> Tuple[List[str], Dict[str, int]]:
    """The constants (free terms) and predicate arities mentioned across ``asts``."""
    consts: Set[str] = set()
    preds: Dict[str, int] = {}

    def walk(a: Formula, bound: FrozenSet[str]) -> None:
        if isinstance(a, Atom):
            preds[a.pred] = len(a.args)
            for t in a.args:
                if t not in bound:
                    consts.add(t)
        elif isinstance(a, Not):
            walk(a.f, bound)
        elif isinstance(a, BinOp):
            walk(a.left, bound)
            walk(a.right, bound)
        elif isinstance(a, Quant):
            walk(a.body, bound | {a.var})

    for a in asts:
        walk(a, frozenset())
    return sorted(consts), preds


# ---------------------------------------------------------------------------
# Grounding: AST → a propositional formula over interned ground-atom variables
# ---------------------------------------------------------------------------
# A propositional node is one of:
#   ("atom", var:int)  ("not", node)  ("and", [node…])  ("or", [node…])
#   True / False  (constant truth, for degenerate empty conjunction/disjunction)

class _Grounder:
    def __init__(self, const_elem: Dict[str, int], domain: List[int]):
        self.const_elem = const_elem
        self.domain = domain
        self.atom_id: Dict[Tuple[str, Tuple[int, ...]], int] = {}
        self.id_atom: Dict[int, Tuple[str, Tuple[int, ...]]] = {}
        self._next = 1

    def _var(self, pred: str, elems: Tuple[int, ...]) -> int:
        key = (pred, elems)
        vid = self.atom_id.get(key)
        if vid is None:
            vid = self._next
            self._next += 1
            self.atom_id[key] = vid
            self.id_atom[vid] = key
        return vid

    def ground(self, a: Formula, env: Dict[str, int]):
        if isinstance(a, Atom):
            elems = tuple(env[t] if t in env else self.const_elem[t] for t in a.args)
            return ("atom", self._var(a.pred, elems))
        if isinstance(a, Not):
            return ("not", self.ground(a.f, env))
        if isinstance(a, BinOp):
            l = lambda: self.ground(a.left, env)
            r = lambda: self.ground(a.right, env)
            if a.op == "and":
                return ("and", [l(), r()])
            if a.op == "or":
                return ("or", [l(), r()])
            if a.op == "implies":                       # A→B ≡ ¬A ∨ B
                return ("or", [("not", l()), r()])
            if a.op == "iff":                           # A↔B ≡ (A∧B) ∨ (¬A∧¬B)
                ln, rn = l(), r()
                return ("or", [("and", [ln, rn]),
                               ("and", [("not", ln), ("not", rn)])])
            if a.op == "xor":                           # A⊕B ≡ (A∧¬B) ∨ (¬A∧B)
                ln, rn = l(), r()
                return ("or", [("and", [ln, ("not", rn)]),
                               ("and", [("not", ln), rn])])
            raise ValueError(f"unground-able op {a.op}")
        if isinstance(a, Quant):
            parts = [self.ground(a.body, {**env, a.var: d}) for d in self.domain]
            if a.kind == "forall":
                return ("and", parts) if parts else True
            return ("or", parts) if parts else False    # ∃ over empty domain = False
        raise ValueError(f"unground-able node {type(a).__name__}")


# ---------------------------------------------------------------------------
# Tseitin transform: propositional node → CNF clauses (lists of int literals)
# ---------------------------------------------------------------------------

class _Tseitin:
    def __init__(self, next_var: int):
        self._next = next_var
        self.clauses: List[List[int]] = []

    def _fresh(self) -> int:
        v = self._next
        self._next += 1
        return v

    def encode(self, node) -> int:
        """Return a literal equivalent to ``node``, appending its defining clauses."""
        if node is True:
            t = self._fresh(); self.clauses.append([t]); return t
        if node is False:
            f = self._fresh(); self.clauses.append([-f]); return f
        tag = node[0]
        if tag == "atom":
            return node[1]
        if tag == "not":
            return -self.encode(node[1])
        lits = [self.encode(c) for c in node[1]]
        g = self._fresh()
        if tag == "and":                                # g ↔ ⋀ lits
            for li in lits:
                self.clauses.append([-g, li])
            self.clauses.append([g] + [-li for li in lits])
        elif tag == "or":                               # g ↔ ⋁ lits
            for li in lits:
                self.clauses.append([-li, g])
            self.clauses.append([-g] + lits)
        else:
            raise ValueError(f"bad node tag {tag}")
        return g


# ---------------------------------------------------------------------------
# DPLL with unit propagation
# ---------------------------------------------------------------------------

def _simplify(clauses: List[List[int]], lit: int) -> Optional[List[List[int]]]:
    """Assert ``lit`` true: drop satisfied clauses, remove ``-lit`` from the rest.
    Returns ``None`` on conflict (an emptied clause)."""
    out: List[List[int]] = []
    for c in clauses:
        if lit in c:
            continue
        if -lit in c:
            nc = [x for x in c if x != -lit]
            if not nc:
                return None
            out.append(nc)
        else:
            out.append(c)
    return out


def _dpll(clauses: List[List[int]], assign: Dict[int, bool],
          budget: List[int]) -> Optional[Dict[int, bool]]:
    budget[0] -= 1
    if budget[0] < 0:
        raise _BudgetExceeded()
    assign = dict(assign)
    # Unit propagation to a fixpoint.
    while True:
        unit = next((c[0] for c in clauses if len(c) == 1), None)
        if unit is None:
            break
        assign[abs(unit)] = unit > 0
        simplified = _simplify(clauses, unit)
        if simplified is None:
            return None
        clauses = simplified
    if any(len(c) == 0 for c in clauses):
        return None
    if not clauses:
        return assign
    branch = clauses[0][0]
    for val in (branch, -branch):
        simplified = _simplify(clauses, val)
        if simplified is None:
            continue
        nxt = dict(assign)
        nxt[abs(val)] = val > 0
        res = _dpll(simplified, nxt, budget)
        if res is not None:
            return res
    return None


# ---------------------------------------------------------------------------
# Independent model checker — the soundness guard
# ---------------------------------------------------------------------------

def satisfies(asts: List[Formula], model: "Model") -> bool:
    """Does ``model`` satisfy every formula in ``asts``?  An evaluator written *independently*
    of the grounder/solver, so a found assignment is double-checked against the original FOL
    before it is ever trusted — the whole ``Uncertain`` verdict rests on this."""
    domain = range(model.domain_size)

    def ev(a: Formula, env: Dict[str, int]) -> bool:
        if isinstance(a, Atom):
            elems = tuple(env[t] if t in env else model.constants[t] for t in a.args)
            return (a.pred, elems) in model.true_atoms
        if isinstance(a, Not):
            return not ev(a.f, env)
        if isinstance(a, BinOp):
            l, r = ev(a.left, env), ev(a.right, env)
            return {"and": l and r, "or": l or r, "implies": (not l) or r,
                    "iff": l == r, "xor": l != r}[a.op]
        if isinstance(a, Quant):
            vals = (ev(a.body, {**env, a.var: d}) for d in domain)
            return all(vals) if a.kind == "forall" else any(vals)
        raise ValueError(f"uncheckable node {type(a).__name__}")

    return all(ev(a, {}) for a in asts)


# ---------------------------------------------------------------------------
# The model finder
# ---------------------------------------------------------------------------

def find_model(asts: List[Formula]) -> Optional[Model]:
    """A finite model of the conjunction ``asts``, or ``None`` if none is found within the
    bounds.  A returned model is genuine (sound); ``None`` certifies nothing."""
    asts = [a for a in asts if a is not None]
    consts, _preds = _signature(asts)
    base = len(consts)
    # Domain must hold the (distinct) constants; at least one element for a non-empty model.
    lo = max(1, base)
    for size in range(lo, min(MAX_DOMAIN, lo + MAX_ANON_WITNESSES) + 1):
        const_elem = {c: i for i, c in enumerate(consts)}
        domain = list(range(size))
        gnd = _Grounder(const_elem, domain)
        top = ("and", [gnd.ground(a, {}) for a in asts]) if asts else True
        ts = _Tseitin(gnd._next)
        top_lit = ts.encode(top)
        clauses = ts.clauses + [[top_lit]]
        try:
            assignment = _dpll(clauses, {}, [DPLL_NODE_BUDGET])
        except _BudgetExceeded:
            continue                       # too big at this size — try another / give up
        if assignment is not None:
            true_atoms = frozenset(
                key for vid, key in gnd.id_atom.items() if assignment.get(vid, False))
            model = Model(domain_size=size, constants=dict(const_elem),
                          true_atoms=true_atoms)
            # Soundness guard: trust a model only if it independently checks out.
            if satisfies(asts, model):
                return model
    return None


# ---------------------------------------------------------------------------
# The EPR (Bernays–Schönfinkel) complete decision — the universal case-split lever
# ---------------------------------------------------------------------------
# FOLIO is function-free relational FOL **without equality**.  A sentence whose prenex
# prefix is ∃*∀* (no existential in the scope of a universal — equivalently, Skolemization
# introduces no functions, only constants) is in the EPR / Bernays–Schönfinkel class: it has
# the **finite-model property** with a model of size ≤ |constants| + |∃-quantifiers|.  So
# grounding it over a domain of exactly that size is a *complete* decision:
#
#   grounded formula UNSAT (propositionally)  ⟺  the FOL sentence is unsatisfiable.
#
# That is the sound lever the top-level case-split misses: ``M ∪ {¬C}`` UNSAT ⇒ ``M ⊨ C``,
# even when the refutation requires reasoning by cases *under* a universal
# (``∀x(P(x)∨Q(x)), ∀x(P→R), ∀x(Q→R) ⊨ ∀x R``).  No-equality is what makes the grounder's
# unique-names assumption sound here too: a satisfiable no-equality sentence always has a
# model with all constants distinct (duplicate the shared element), so UNA-UNSAT ⟺ UNSAT.
#
# A budget cap on the domain size keeps it honest — beyond it (or on a non-EPR shape, where a
# Skolem function would make the Herbrand universe infinite) the function returns ``None`` and
# the caller falls back to the bounded pipeline.

EPR_MAX_DOMAIN = 12   # cap on |domain| for the complete EPR grounding; beyond ⇒ abstain


def _epr_scan(asts: List[Formula]) -> "Optional[int]":
    """If the conjunction of ``asts`` is EPR (no ∃-type quantifier under a ∀-type one, no
    quantifier under ↔/⊕), return the number of ∃-type quantifiers (for the domain bound);
    else ``None``.  A quantifier's *type* is by polarity: ``∃`` at + or ``∀`` at − is
    "∃-type" (Skolem witness); ``∀`` at + or ``∃`` at − is "∀-type" (ranges over the domain)."""
    exists_types = 0
    ok = True

    def walk(a: Formula, pol: int, under_universal: bool) -> None:
        nonlocal exists_types, ok
        if not ok:
            return
        if isinstance(a, Atom):
            return
        if isinstance(a, Not):
            walk(a.f, -pol, under_universal)
        elif isinstance(a, BinOp):
            if a.op in ("iff", "xor"):
                # Both polarities reachable; a quantifier here has no well-defined type.
                if _has_quant(a):
                    ok = False
                return
            if a.op == "implies":
                walk(a.left, -pol, under_universal)
                walk(a.right, pol, under_universal)
            else:                                   # and / or — polarity unchanged
                walk(a.left, pol, under_universal)
                walk(a.right, pol, under_universal)
        elif isinstance(a, Quant):
            exists_type = ((a.kind == "exists" and pol > 0)
                           or (a.kind == "forall" and pol < 0))
            if exists_type:
                if under_universal:
                    ok = False                      # ∃ under ∀ ⇒ Skolem function ⇒ not EPR
                    return
                exists_types += 1
            walk(a.body, pol, under_universal or not exists_type)

    for a in asts:
        walk(a, +1, False)
        if not ok:
            return None
    return exists_types


def _has_quant(a: Formula) -> bool:
    if isinstance(a, Quant):
        return True
    if isinstance(a, Not):
        return _has_quant(a.f)
    if isinstance(a, BinOp):
        return _has_quant(a.left) or _has_quant(a.right)
    return False


def decide_epr(asts: List[Formula]) -> "Optional[str]":
    """Decide satisfiability of the conjunction completely when it is EPR.

    Returns ``"unsat"`` / ``"sat"`` (a sound, *complete* verdict for the EPR fragment of
    function-free, equality-free FOL) or ``None`` when the shape is not EPR or the EPR
    domain bound / DPLL budget is exceeded (abstain — never guess)."""
    asts = [a for a in asts if a is not None]
    n_exists = _epr_scan(asts)
    if n_exists is None:
        return None
    consts, _preds = _signature(asts)
    size = max(1, len(consts) + n_exists)           # the EPR small-model bound
    if size > EPR_MAX_DOMAIN:
        return None
    const_elem = {c: i for i, c in enumerate(consts)}
    domain = list(range(size))
    gnd = _Grounder(const_elem, domain)
    top = ("and", [gnd.ground(a, {}) for a in asts]) if asts else True
    ts = _Tseitin(gnd._next)
    top_lit = ts.encode(top)
    clauses = ts.clauses + [[top_lit]]
    try:
        assignment = _dpll(clauses, {}, [DPLL_NODE_BUDGET])
    except _BudgetExceeded:
        return None
    return "sat" if assignment is not None else "unsat"


def certify_independent(
    prem_asts: List[Formula], concl_ast: Formula, neg_concl: Formula,
) -> Optional[Tuple[Model, Model]]:
    """If models of both ``M ∪ {¬C}`` and ``M ∪ {C}`` exist, return them (a sound
    certificate that the conclusion is **Uncertain** — neither entailed nor refuted);
    else ``None`` (abstain)."""
    model_not_c = find_model(prem_asts + [neg_concl])
    if model_not_c is None:
        return None
    model_c = find_model(prem_asts + [concl_ast])
    if model_c is None:
        return None
    return model_not_c, model_c
