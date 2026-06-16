"""
FOLIO on Arisbe's *own* bounded engine — the soundness×coverage half of the "Both".

``folio_fol`` decides FOLIO entailment with Z3 (the authoritative, complete verdict).
This module answers the *companion* question the DL-ReasonSuite work posed:

    How much of FOLIO can Arisbe decide with its **own** bounded reasoner — the Horn
    materializer + the freeze-a-witness theory query + the denial-based consistency
    check — and does it ever get one *wrong*?

The honest stance is the DL one (``dl_reasoning`` / ``dl_benchmark``): a bounded reasoner
that abstains is not penalised for abstaining; it is penalised only for *deciding wrong*.
So the two headline numbers are **soundness** (1 − wrong/decided, must be 1.0) and
**coverage** (decided/total). FOLIO is full first-order and heavily non-Horn (disjunction,
⊕, negated heads), so coverage is bounded by construction — the point is that every
*decided* verdict is sound, reported beside Z3's complete one.

The decision, both directions reduced to one sound primitive:

    M ⊨ C   ⟺  M ∪ {¬C} is unsatisfiable          (predict True)
    M ⊨ ¬C  ⟺  M ∪ { C} is unsatisfiable          (predict False)

and unsatisfiability is detected *soundly but incompletely* by the bounded engine:
materialize the Horn fragment of the combined theory to its least Herbrand model and test
whether any **denial** (``~[ A… ]`` — a disjointness / negative constraint) fires. A denial
satisfied in the least model is violated in *every* model, so the inconsistency is genuine
(``dl_reasoning.check_consistency``). Because that uses only a *subset* of the axioms (the
Horn ones + the denials), an inconsistency it finds is a real inconsistency of the whole
combined theory — hence sound regardless of the non-Horn residue it had to skip.

Universal/subsumption conclusions (``∀x (B(x) → H(x))``) carry no denial to fire, so the
freeze-a-witness ``theory_query.entails`` recovers them — the same sound + Horn-complete
decision the DLCore subsumption track uses.

``Uncertain`` is certified by **model construction** (``folio_model_finder``): a finite model
of ``M ∪ {¬C}`` *and* one of ``M ∪ {C}`` together witness that neither is entailed (sound — two
real models prove independence). Where even the bounded model finder is exhausted, the engine
abstains (``Unknown``) — decide every entailment/contradiction/independence it can prove or
model, abstain on the rest. Soundness is judged against the FOL semantics (every decided
verdict agrees with the complete Z3 oracle on the FOLIO validation set), not the noisy gold.

The premises + conclusion are compiled to an EGI **directly** (not via CLIF/EGIF text):
``clif_parser_dau`` has no notion of a Dau constant — it reads every term as a generic line
of identity and unifies same-named terms across an ``(and …)``, which both collapses
distinct premises' ``∀x`` into one witness *and* lets an existential's generic witness
spuriously match a constant atom in a denial.  Building the graph here lets a FOLIO constant
become a shared ``is_generic=False`` vertex (matched only by itself) and gives each
quantifier its own line — the variable-collapse and false-match bugs simply cannot arise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from egi_core_dau import (
    RelationalGraphWithCuts,
    create_cut,
    create_edge,
    create_empty_graph,
    create_vertex,
)
from folio_fol import (
    Atom,
    BinOp,
    Formula,
    FolioParseError,
    Not,
    Quant,
    parse_fol,
)


@dataclass
class NativeResult:
    """One FOLIO verdict from Arisbe's bounded engine, with how it was reached."""

    verdict: str            # "True" | "False" | "Uncertain" | "Unknown" | "Unparsed"
    detail: str = ""
    parsed: bool = True
    via: str = ""           # "refutation" | "case_split" | "theory_query" | "model_construction" | "" (abstained)

    @property
    def decided(self) -> bool:
        # "Unknown" is a deliberate abstention; "Uncertain" is the third *decided* value —
        # a model-construction certificate that neither C nor ¬C is entailed.
        return self.verdict in ("True", "False", "Uncertain")


def _negate(ast: Formula) -> Formula:
    """¬φ, collapsing a leading negation so the result stays a flat shape the bounded
    engine can use (``¬¬A`` → ``A`` as a fact, not a double cut the denial scan skips)."""
    return ast.f if isinstance(ast, Not) else Not(ast)


def normalize(ast: Formula) -> Formula:
    """Rewrite to an equivalent formula that favours the bounded engine's recognised
    shapes — flat **denials** ``¬(A∧…)`` and **Horn rules** ``B→H`` — without changing
    meaning.  Three standard equivalences, applied to a fixpoint:

    * ``L → ¬R``        ≡ ``¬(L ∧ R)``           (the FOLIO disjointness idiom → a denial)
    * ``L → (R → S)``   ≡ ``(L ∧ R) → S``        (exportation → one Horn rule, conjunctive body)
    * ``L → (P ∧ Q)``   ≡ ``(L→P) ∧ (L→Q)``      (split a conjunctive head, then re-normalise)

    All three are exact equivalences, so the rewrite is sound: it only changes which
    fragment the engine can *see*, never what M means.  ``∀x (A(x)→¬B(x))`` thereby builds
    to ``~[ [*x] (A x)(B x) ]`` — a flat denial ``check_consistency`` fires on — rather than
    the double cut the materializer reads as negation-in-head and skips.
    """
    if isinstance(ast, Atom):
        return ast
    if isinstance(ast, Not):
        return Not(normalize(ast.f))
    if isinstance(ast, Quant):
        return Quant(ast.kind, ast.var, normalize(ast.body))
    if isinstance(ast, BinOp):
        if ast.op == "implies":
            head = normalize(ast.right)
            left = normalize(ast.left)
            if isinstance(head, Not):                       # L → ¬R  ≡  ¬(L ∧ R)
                return Not(BinOp("and", left, head.f))
            if isinstance(head, BinOp) and head.op == "implies":   # exportation
                return normalize(BinOp("implies", BinOp("and", left, head.left), head.right))
            if isinstance(head, BinOp) and head.op == "and":       # split conjunctive head
                return normalize(BinOp(
                    "and",
                    BinOp("implies", left, head.left),
                    BinOp("implies", left, head.right),
                ))
            return BinOp("implies", left, head)
        return BinOp(ast.op, normalize(ast.left), normalize(ast.right))
    return ast


# ---------------------------------------------------------------------------
# Direct AST → EGI compilation (constant-aware, scope-correct)
# ---------------------------------------------------------------------------

def _build(
    g: RelationalGraphWithCuts,
    ast: Formula,
    area: str,
    env: Dict[str, str],
    consts: Dict[str, str],
) -> RelationalGraphWithCuts:
    """Add ``ast`` to context ``area`` of ``g``, returning the new graph.

    ``env`` maps a quantifier-bound variable to its vertex id (scoped); ``consts`` maps a
    free term (a FOLIO constant) to a single shared ``is_generic=False`` vertex on the
    sheet (so a constant matches only itself).  The ``∀`` / ``¬`` cases cancel cuts the way
    ``clif_parser_dau`` does, so ``∀x ¬(A∧B)`` lands as the flat denial ``~[ [*x] A B ]``.
    """
    if isinstance(ast, Atom):
        seq: List[str] = []
        for a in ast.args:
            if a in env:
                seq.append(env[a])
            else:                                   # a constant: one shared sheet vertex
                if a not in consts:
                    v = create_vertex(label=a, is_generic=False)
                    g = g.with_vertex_in_context(v, g.sheet)
                    consts[a] = v.id
                seq.append(consts[a])
        return g.with_edge(create_edge(), tuple(seq), ast.pred, context_id=area)

    if isinstance(ast, Not):
        c = create_cut()
        g = g.with_cut(c, area)
        return _build(g, ast.f, c.id, env, consts)

    if isinstance(ast, BinOp):
        if ast.op == "and":
            g = _build(g, ast.left, area, env, consts)
            return _build(g, ast.right, area, env, consts)
        if ast.op == "or":                          # A ∨ B ≡ ~[ ~[A] ~[B] ]
            outer = create_cut(); g = g.with_cut(outer, area)
            cl = create_cut(); g = g.with_cut(cl, outer.id)
            g = _build(g, ast.left, cl.id, env, consts)
            cr = create_cut(); g = g.with_cut(cr, outer.id)
            return _build(g, ast.right, cr.id, env, consts)
        if ast.op == "implies":                     # A → B ≡ ~[ A ~[B] ]
            outer = create_cut(); g = g.with_cut(outer, area)
            g = _build(g, ast.left, outer.id, env, consts)
            inner = create_cut(); g = g.with_cut(inner, outer.id)
            return _build(g, ast.right, inner.id, env, consts)
        if ast.op == "iff":                         # A ↔ B ≡ (A→B) ∧ (B→A)
            g = _build(g, BinOp("implies", ast.left, ast.right), area, env, consts)
            return _build(g, BinOp("implies", ast.right, ast.left), area, env, consts)
        if ast.op == "xor":                         # A ⊕ B ≡ ¬(A↔B)
            return _build(g, Not(BinOp("iff", ast.left, ast.right)), area, env, consts)
        raise FolioParseError(f"unbuildable op {ast.op}")

    if isinstance(ast, Quant):
        if ast.kind == "exists":                    # ∃x φ ≡ [*x] φ  (define x here)
            v = create_vertex(is_generic=True)
            g = g.with_vertex_in_context(v, area)
            return _build(g, ast.body, area, {**env, ast.var: v.id}, consts)
        # ∀x φ ≡ ~[ [*x] ~[ φ ] ] — but cancel cuts when φ is a negation/implication so
        # disjointness (∀x ¬…) and Horn rules (∀x (A→B)) land flat for the materializer.
        outer = create_cut(); g = g.with_cut(outer, area)
        v = create_vertex(is_generic=True)
        g = g.with_vertex_in_context(v, outer.id)
        inner_env = {**env, ast.var: v.id}
        body = ast.body
        if isinstance(body, Not):                   # ∀x ¬ψ ≡ ~[ [*x] ψ ]
            return _build(g, body.f, outer.id, inner_env, consts)
        if isinstance(body, BinOp) and body.op == "implies":   # ∀x (A→B) ≡ ~[ [*x] A ~[B] ]
            g = _build(g, body.left, outer.id, inner_env, consts)
            inner = create_cut(); g = g.with_cut(inner, outer.id)
            return _build(g, body.right, inner.id, inner_env, consts)
        inner = create_cut(); g = g.with_cut(inner, outer.id)   # ∀x φ ≡ ~[ [*x] ~[ φ ] ]
        return _build(g, body, inner.id, inner_env, consts)

    raise FolioParseError(f"unbuildable node {type(ast).__name__}")


def _build_graph(asts: List[Formula]) -> RelationalGraphWithCuts:
    """Conjoin ``asts`` onto one sheet (juxtaposition = ∧), sharing constants."""
    g = create_empty_graph()
    consts: Dict[str, str] = {}
    for a in asts:
        g = _build(g, normalize(a), g.sheet, {}, consts)
    return g


# ---------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------

def _denial_reading_unsound(asts: List[Formula]) -> bool:
    """Would ``check_consistency`` read a denial *unsoundly* over this conjunction?

    The consistency check treats every sheet-level cut ``~[ A… ]`` as a **universal**
    constraint ``∀ ¬(A…)``.  That is correct only when the cut's lines are universally
    quantified.  But an **existential variable under a negation** — ``∃x (P(x) ∧ ¬Q(x))``
    — builds a cut ``~[ Q(x) ]`` whose ``x`` is a *witness*, not a universal; reading it
    as ``∀x ¬Q(x)`` lets it fire against an unrelated individual, a false inconsistency.

    Detect that shape by polarity: an atom at **negative** polarity carrying a variable
    that is *not* universally bound above it (a ∀ at + polarity, or a ∃ at − polarity).
    When present anywhere in the conjunction, the refutation primitive must abstain — the
    freeze-witness path (``theory_query``, which checks a derived head, never a denial) is
    unaffected and still applies.
    """
    def walk(a: Formula, pol: int, bound: frozenset, uni: frozenset) -> bool:
        if isinstance(a, Atom):
            if pol < 0:
                return any(t in bound and t not in uni for t in a.args)
            return False
        if isinstance(a, Not):
            return walk(a.f, -pol, bound, uni)
        if isinstance(a, BinOp):
            if a.op in ("iff", "xor"):              # both polarities reachable
                return any(walk(s, p, bound, uni)
                           for s in (a.left, a.right) for p in (+1, -1))
            if a.op == "implies":                   # A→B : A negative, B positive
                return walk(a.left, -pol, bound, uni) or walk(a.right, pol, bound, uni)
            return walk(a.left, pol, bound, uni) or walk(a.right, pol, bound, uni)
        if isinstance(a, Quant):
            universal = (a.kind == "forall" and pol > 0) or (a.kind == "exists" and pol < 0)
            nu = (uni | {a.var}) if universal else (uni - {a.var})
            return walk(a.body, pol, bound | {a.var}, nu)
        return False

    return any(walk(normalize(a), +1, frozenset(), frozenset()) for a in asts)


def _refutes(asts: List[Formula]) -> bool:
    """Does the conjunction's Horn fragment force a denial?  (A sound inconsistency.)

    Returns ``False`` (cannot prove) when the denial reading would be unsound — an
    existential variable under negation, where ``check_consistency`` would over-fire."""
    if _denial_reading_unsound(asts):
        return False
    from dl_reasoning import DLAnswer, check_consistency
    egi = _build_graph(asts)
    return check_consistency(egi).answer == DLAnswer.NO


def _universal_entails(prem_asts: List[Formula], concl_ast: Formula) -> bool:
    """Is the conclusion a theorem of M by freeze-a-witness?  (Recovers universal /
    subsumption conclusions that carry no denial to fire.)"""
    from theory_query import entails
    m_egi = _build_graph(prem_asts)
    c_egi = _build_graph([concl_ast])
    tq = entails(m_egi, c_egi)
    return tq.applicable and tq.verdict == "true"


# ---------------------------------------------------------------------------
# The disjunctive case-split lever — reasoning by cases over the non-Horn
# residue the bare denial check cannot reach (docs/FOLIO_EVALUATION.md).
# ---------------------------------------------------------------------------

MAX_CASE_SPLITS = 6   # bound on nested β-branches per refutation (2**6 leaves worst case)


def _flatten_and(asts: List[Formula]) -> List[Formula]:
    """Break top-level conjunctions into a flat conjunct list (juxtaposition = ∧), so a
    disjunction buried under ``∧`` becomes a splittable conjunct.  Also collapses ``¬¬φ``
    and pushes ``¬(A∨B)`` to the conjunction ``¬A ∧ ¬B`` (De Morgan) — both expose more
    top-level structure without changing meaning."""
    out: List[Formula] = []
    for a in asts:
        a = normalize(a)
        if isinstance(a, BinOp) and a.op == "and":
            out.extend(_flatten_and([a.left, a.right]))
        elif isinstance(a, Not) and isinstance(a.f, Not):           # ¬¬φ ≡ φ
            out.extend(_flatten_and([a.f.f]))
        elif (isinstance(a, Not) and isinstance(a.f, BinOp)
              and a.f.op == "or"):                                   # ¬(A∨B) ≡ ¬A ∧ ¬B
            out.extend(_flatten_and([Not(a.f.left), Not(a.f.right)]))
        else:
            out.append(a)
    return out


def _disjuncts(ast: Formula) -> "List[Formula] | None":
    """If ``ast`` is a **top-level** disjunction (a conjunct that is true in more than one
    irreducible way), return the case branches; else ``None``.  Splitting these — and only
    these, never a disjunction trapped under a ∀ (``∀x (P(x)∨Q(x))`` ≠ a top-level case
    split) — keeps the lever sound.

    * ``A ∨ B``   → ``[A, B]``
    * ``A ⊕ B``   → ``[A ∧ ¬B, ¬A ∧ B]``     (exactly one holds)
    * ``A ↔ B``   → ``[A ∧ B, ¬A ∧ ¬B]``     (both or neither)
    """
    if isinstance(ast, BinOp):
        if ast.op == "or":
            return [ast.left, ast.right]
        if ast.op == "xor":
            return [BinOp("and", ast.left, Not(ast.right)),
                    BinOp("and", Not(ast.left), ast.right)]
        if ast.op == "iff":
            return [BinOp("and", ast.left, ast.right),
                    BinOp("and", Not(ast.left), Not(ast.right))]
    return None


def _refute_rec(conjuncts: List[Formula], budget: int) -> bool:
    """Refute the conjunction by reasoning over cases.  Pick a top-level disjunctive
    conjunct and branch: the whole is unsatisfiable iff **every** branch is.  With no
    disjunction left to split (or the budget spent) fall to the sound Horn+denial
    primitive ``_refutes``.  ``all(...)`` short-circuits, so a branch that cannot be
    refuted stops the search at once."""
    if budget > 0:
        for i, c in enumerate(conjuncts):
            branches = _disjuncts(c)
            if branches is not None:
                rest = conjuncts[:i] + conjuncts[i + 1:]
                return all(
                    _refute_rec(_flatten_and(rest + [b]), budget - 1) for b in branches)
    return _refutes(conjuncts)


def _refutes_cases(asts: List[Formula]) -> "tuple[bool, bool]":
    """Sound refutation with the disjunctive case-split lever.  Returns
    ``(refuted, by_cases)`` — ``by_cases`` flags that a β-split (not the bare denial
    check) closed it, for the verdict's ``via``."""
    conjuncts = _flatten_and(asts)
    if not any(_disjuncts(c) is not None for c in conjuncts):
        return _refutes(conjuncts), False          # no disjunction → the base primitive
    return _refute_rec(conjuncts, MAX_CASE_SPLITS), True


def decide_native(premise_fols: List[str], conclusion_fol: str) -> NativeResult:
    """Decide FOLIO entailment with Arisbe's bounded engine — sound, abstaining.

    ``True`` if M entails the conclusion, ``False`` if M entails its negation (both proved
    by the Horn materializer / case-split / freeze-witness); ``Uncertain`` when a finite
    model of ``M ∪ {¬C}`` *and* one of ``M ∪ {C}`` are both found (a sound certificate that
    neither is entailed); ``Unknown`` when the bounded engine can certify none of the three
    (the honest abstention); ``Unparsed`` if any FOL is unreadable.
    """
    try:
        prem_asts = [parse_fol(p) for p in premise_fols if p and p.strip()]
        concl_ast = parse_fol(conclusion_fol)
    except FolioParseError as exc:
        return NativeResult("Unparsed", str(exc), parsed=False)

    try:
        neg_concl = _negate(concl_ast)
        prove_true_refut, true_by_cases = _refutes_cases(prem_asts + [neg_concl])   # M ∪ {¬C} ⊥ ⇒ M ⊨ C
        prove_false, false_by_cases = _refutes_cases(prem_asts + [concl_ast])       # M ∪ { C} ⊥ ⇒ M ⊨ ¬C
        prove_true_uni = _universal_entails(prem_asts, concl_ast)
    except Exception as exc:
        # The bounded engine could not build/decide this shape — abstain, never guess.
        return NativeResult("Unknown", f"engine could not address it: {exc}", via="")

    prove_true = prove_true_refut or prove_true_uni
    if prove_true and prove_false:
        # Both directions "prove" only if M is itself inconsistent in the Horn fragment —
        # a degenerate premise set; abstain rather than emit an arbitrary verdict.
        return NativeResult(
            "Unknown", "premises are inconsistent in the Horn fragment — abstaining")
    if prove_true:
        if prove_true_refut:
            via = "case_split" if true_by_cases else "refutation"
            detail = ("M ∪ {¬C} is inconsistent by cases — M entails C" if true_by_cases
                      else "M ∪ {¬C} is Horn-inconsistent — M entails C")
        else:
            via = "theory_query"
            detail = "the conclusion is a theorem of M (freeze-a-witness)"
        return NativeResult("True", detail, via=via)
    if prove_false:
        via = "case_split" if false_by_cases else "refutation"
        detail = ("M ∪ {C} is inconsistent by cases — M entails ¬C" if false_by_cases
                  else "M ∪ {C} is Horn-inconsistent — M entails ¬C")
        return NativeResult("False", detail, via=via)

    # Neither entailment proved.  Try to *certify* Uncertain by constructing a model of
    # M ∪ {¬C} and a model of M ∪ {C}: if both exist, neither is entailed (sound).
    try:
        from folio_model_finder import certify_independent
        certificate = certify_independent(prem_asts, concl_ast, neg_concl)
    except Exception:
        certificate = None
    if certificate is not None:
        m_not_c, m_c = certificate
        return NativeResult(
            "Uncertain",
            f"models of both M∪{{¬C}} ({m_not_c.describe()}) and M∪{{C}} "
            f"({m_c.describe()}) exist — neither C nor ¬C is entailed",
            via="model_construction")

    return NativeResult(
        "Unknown",
        "the bounded engine certifies none of True/False/Uncertain (residue beyond its bound)")
