"""
Read an EGI as a first-order formula — the inverse of ``folio_native._build``.

``folio_native`` compiles a FOL AST *down* to an EGI (to draw it, and to reason over it
with the bounded native engine).  This module reads an EGI *up* to the same ``folio_fol``
AST, so the finite-model finder (``folio_model_finder``, which already speaks ``Formula``)
can be pointed at any EGI — in particular at a DLCore ontology M, to **certify
consistency** (exhibit a model of M) and **non-entailment** (exhibit a model of
``M ∪ {¬C(a)}``), the two things ``dl_reasoning``'s Horn engine can only ever abstain on.

This is the EGI-touching half of the coverage lever, and it is **strictly read-only**: it
*observes* the immutable graph (``area`` tree, ``nu`` incidence, vertex genericity) and
emits a separate ``Formula`` value.  It never calls a ``with_*`` builder, never mutates,
and is wholly outside the transformation calculus — the same posture ``model_materialization``
/ ``theory_query`` / ``semantic_game`` already take toward an EGI.

The reading is the standard endoporeutic (Φ) one:

* a **cut** is a negation (``~[ … ]`` → ``¬(…)``);
* **juxtaposition** in one area is conjunction;
* a **generic vertex** (a line of identity) is an existential, quantified at the *outermost*
  area its line reaches — which in the immutable model is exactly the area the vertex is
  placed in (``egi.area``); edges in deeper cuts that share the line read its bound variable;
* a **constant vertex** (``is_generic=False`` with a label) is a free term — a constant —
  so it lands in the model finder's domain and matches only itself.

An **empty area** reads as ⊤ (the empty conjunction); an empty cut is therefore ``¬⊤`` = ⊥.
The ``Formula`` AST has no truth constant, so ⊤ is encoded as a closed tautology over a
reserved 0-ary atom (``__taut__() ∨ ¬__taut__()``) — sound and self-contained (it never
constrains a real predicate).
"""

from __future__ import annotations

from typing import Dict, List, Set

from egi_core_dau import RelationalGraphWithCuts
from folio_fol import Atom, BinOp, Formula, Not, Quant

# A reserved 0-ary predicate used only to encode ⊤/⊥ for empty areas (see module docstring).
_TAUT = Atom("__taut__", ())
_TRUE: Formula = BinOp("or", _TAUT, Not(_TAUT))


def _conjoin(parts: List[Formula]) -> Formula:
    """Left-fold a conjunction; the empty conjunction is ⊤."""
    if not parts:
        return _TRUE
    body = parts[0]
    for p in parts[1:]:
        body = BinOp("and", body, p)
    return body


class _Reader:
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.vertices = {v.id: v for v in egi.V}
        self.edge_ids = {e.id for e in egi.E}
        self.cut_ids = {c.id for c in egi.Cut}
        # Generic vertices get fresh variable names guaranteed disjoint from every constant
        # label, so a generated variable can never be mistaken for a constant by the finder.
        const_labels: Set[str] = {
            v.label for v in egi.V if not v.is_generic and v.label
        }
        prefix = "_v"
        while any(lbl.startswith(prefix) for lbl in const_labels):
            prefix = "_" + prefix
        self._prefix = prefix
        self._n = 0
        self.var_of: Dict[str, str] = {}

    def _term(self, vid: str) -> str:
        """The term name for a vertex: its (fresh) variable if generic, its label if constant."""
        v = self.vertices[vid]
        if v.is_generic:
            name = self.var_of.get(vid)
            if name is None:
                name = f"{self._prefix}{self._n}"
                self._n += 1
                self.var_of[vid] = name
            return name
        return v.label  # a Dau constant — the label is the term

    def read_area(self, ctx: str) -> Formula:
        """The formula of one area: juxtaposition → ∧, nested cut → ¬, generic vertex → ∃."""
        contents = self.egi.area.get(ctx, frozenset())
        conjuncts: List[Formula] = []
        # Atoms (edges) directly in this area.
        for eid in contents:
            if eid in self.edge_ids:
                rel = self.egi.get_relation_name(eid)
                args = tuple(self._term(v) for v in self.egi.nu[eid])
                conjuncts.append(Atom(rel, args))
        # Nested cuts → negated sub-formulas.
        for cid in contents:
            if cid in self.cut_ids:
                conjuncts.append(Not(self.read_area(cid)))
        body = _conjoin(conjuncts)
        # Existentially quantify each generic vertex whose home area is this one.  (A constant
        # vertex carries no quantifier; its label is a free constant term.)
        for vid in contents:
            v = self.vertices.get(vid)
            if v is not None and v.is_generic:
                body = Quant("exists", self._term(vid), body)
        return body


def read_egi_to_fol(egi: RelationalGraphWithCuts) -> List[Formula]:
    """Read an EGI as a list holding its single closed first-order formula (the sheet's
    reading).  Returned as a list so it composes directly with the model finder's
    ``List[Formula]`` API — e.g. ``read_egi_to_fol(M) + [Not(Atom(C, (a,)))]`` to test
    non-entailment of ``C(a)``.  Read-only: ``egi`` is never modified."""
    return [_Reader(egi).read_area(egi.sheet)]
