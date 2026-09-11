"""Mechanism classifiers for the ledger (spec 2026-09-10 §6; Task 10 ruling 1).

A ledger entry names a *classifier*: a predicate over (record, failure detail)
that decides membership by mechanism rather than by instance key. The default
mode still lists instances (they are few); a mode too large to list —
exhaustive — is ledgered by a pinned count of distinct instance keys per
(entry, kind). The *kind* (``failure_kind``) is pinned beside the count, so a
failure that stays inside its mechanism but flips kind (INCOMPLETE → SEVERE,
NOT AN EQUIVALENCE → UNSOUND) moves one count down and another up, and fails.

Within a layer the predicates are mutually exclusive by construction; the
ledger check refuses a failure two entries claim. The adjudication scripts
(``tests/calculus_adjudication*.py``) classify through this module, so the
instance lists they write and the counts the run checks come from one place.
"""
from __future__ import annotations

from typing import Callable, Dict, Tuple

import eg_navigation as nav
from calculus_enum import edges_on
from calculus_expected import remove
from calculus_rules import expand, tops
from tarski import dominating_nodes

Pred = Callable[[object, str], bool]


# -- kinds --------------------------------------------------------------------

_SINGLE_KIND = {"core-dominating": "DISAGREE", "differential": "DISAGREE",
                "corpus-egi": "NOT AN EGI"}


def _structure_tag(clause: str) -> str:
    if "not an EGI" in clause:
        return "NOT AN EGI"
    if "licensed change" in clause:
        return "DIFFERS"
    return "MAPS:" + clause.split()[0]          # alphabet / rho / sort / quotation


def failure_kind(layer: str, detail: str) -> str:
    """What sort of failure a detail line reports, per layer."""
    if layer == "refusal":
        return detail.split()[0]                # SEVERE / INCOMPLETE / CRASH
    if layer == "soundness":
        return "UNSOUND" if detail.startswith("UNSOUND") else "NOT AN EQUIVALENCE"
    if layer == "structure":
        return "+".join(sorted({_structure_tag(c) for c in detail.split("; ")}))
    return _SINGLE_KIND[layer]


# -- helpers shared with the adjudication scripts ------------------------------

def orphans(g, X, c0=None) -> set:
    """Vertices outside X whose every edge lies in X (erasing X isolates them)
    — only those in context ``c0`` when given (the engine's closure looks
    there, and nowhere else)."""
    vs = {v.id for v in g.V}
    return {v for v in vs - set(X) if edges_on(g, v) and set(edges_on(g, v)) <= set(X)
            and (c0 is None or g.get_context(v) == c0)}


def closed(g, m, c0, for_erasure=False) -> set:
    """The engine's own closure of the selection (as ITPlus/ERAInteraction call it)."""
    from subgraph_closure_validator import SubgraphClosureValidator
    return set(SubgraphClosureValidator(g).analyze_closure(
        frozenset(m.selection), allow_expansion=True, context_area=c0,
        for_erasure=for_erasure).closed_subgraph)


def erased_constants(g, h) -> list:
    """Constant vertices of g that h no longer has."""
    kept = {v.id for v in h.V}
    return [v for v in g.V if v.label and v.id not in kept]


def moved_join(rec) -> bool:
    """MOVE_BRANCHES re-hooked exactly the identity edge joining the two selected vertices."""
    g, h = rec.g, rec.outcome.result
    changed = [e for e in g.nu if h.nu.get(e) != g.nu[e]]
    return len(changed) == 1 and g.rel[changed[0]] == "=" and \
        set(g.nu[changed[0]]) == set(rec.move.selection)


def join_deeper_than_its_vertices(g, sel) -> bool:
    """Some identity edge joining two selected vertices sits in a context
    deeper than a vertex it joins, so the two are not Θ-related through it
    (Def 24.9, p.269: ctx(e_i) = ctx(v_{i+1}))."""
    S = set(sel)
    return any(g.rel[e] == "=" and len(seq) == 2 and set(seq) <= S
               and any(g.get_context(e) != g.get_context(v) for v in seq)
               for e, seq in g.nu.items())


# -- refusal ------------------------------------------------------------------

def _named_apart(r) -> bool:
    return not r.outcome.applied and "must be in the same area" in r.outcome.message


def _rule(r, name) -> bool:
    return r.move.rule == name


REFUSAL: Dict[str, Pred] = {
    "heavy-dot-negative-only":
        lambda r, d: _rule(r, "VERTEX_INS") and not r.outcome.applied,
    "ins-mixes-arities-without-an-alphabet":
        lambda r, d: _rule(r, "INS") and r.outcome.applied and r.verdict is False
        and "another arity" in r.why,
    "vertex-era-positive-only":
        lambda r, d: _rule(r, "VERTEX_ERA") and not r.outcome.applied,
    "vertex-era-erases-a-line-with-its-edges":
        lambda r, d: _rule(r, "VERTEX_ERA") and r.outcome.applied,
    "era-auto-closes-a-vertex-selection":
        lambda r, d: _rule(r, "ERA") and r.outcome.applied and "leave an edge behind" in r.why,
    "era-refuses-a-cut-named-with-its-contents":
        lambda r, d: _rule(r, "ERA") and _named_apart(r),
    "era-closure-drags-a-quoting-name":
        lambda r, d: _rule(r, "ERA") and not r.outcome.applied and not r.outcome.crashed
        and "selected without its oval" in r.outcome.message,
    "it-plus-into-its-own-selection":
        lambda r, d: _rule(r, "IT+") and r.outcome.applied and "inside the selection" in r.why,
    "it-plus-refuses-a-cut-named-with-its-contents":
        lambda r, d: _rule(r, "IT+") and _named_apart(r),
    "it-minus-refuses-a-cut-named-with-its-contents":
        lambda r, d: _rule(r, "IT-") and _named_apart(r),
    "it-minus-strictly-enclosing-only":
        lambda r, d: _rule(r, "IT-") and not r.outcome.applied and not r.outcome.crashed and (
            "No enclosing areas" in r.outcome.message
            or "No isomorphic original" in r.outcome.message),
    "it-minus-erases-a-copy-of-another-line":
        lambda r, d: _rule(r, "IT-") and r.outcome.applied and r.verdict is False
        and "no source of which this is a copy" in r.why,
    "dc-plus-refuses-a-cut-named-with-its-contents":
        lambda r, d: _rule(r, "DC+") and _named_apart(r),
    "dc-plus-strands-a-vertex":
        lambda r, d: _rule(r, "DC+") and r.outcome.applied and not dominating_nodes(r.outcome.result),
    "dc-plus-ignores-target":
        lambda r, d: _rule(r, "DC+") and r.outcome.applied and dominating_nodes(r.outcome.result)
        and "not directly in the target" in r.why,
}


# -- structure ----------------------------------------------------------------

def _era_isolates(r, d) -> bool:
    if not (_rule(r, "ERA") and r.verdict):
        return False
    X = expand(r.g, r.move.selection)
    c0 = r.g.get_context(tops(r.g, X)[0])
    return nav.same_graph(remove(r.g, X | orphans(r.g, X, c0)), r.outcome.result)


def _it_plus_added(r):
    X = expand(r.g, r.move.selection)
    c0 = r.g.get_context(tops(r.g, X)[0])
    return X, c0, closed(r.g, r.move, c0) - X


def _it_plus_auto_closes(r, d) -> bool:
    if not (_rule(r, "IT+") and r.verdict):
        return False
    _, _, added = _it_plus_added(r)
    return any(a in r.g.nu for a in added)


def _it_plus_reuses(r, d) -> bool:
    """Deeper target, and the engine's closure added no EDGE (that is
    it-plus-auto-closes); it may add a vertex — the edge's own vertex when
    the selection names an edge with some other vertex (Task 10, exhaustive:
    {(P x), y} in *x *y (P x) ~[ ]) — and the engine reuses a vertex of the
    closed set that sits in the source context instead of copying it."""
    if not (_rule(r, "IT+") and r.verdict):
        return False
    X, c0, added = _it_plus_added(r)
    vs = {v.id for v in r.g.V}
    return not any(a in r.g.nu for a in added) and r.move.target != c0 and \
        any(x in vs and r.g.get_context(x) == c0 for x in X | added)


STRUCTURE: Dict[str, Pred] = {
    "dc-plus-result-not-an-egi":
        lambda r, d: _rule(r, "DC+") and not dominating_nodes(r.outcome.result),
    "era-also-erases-the-vertex-it-isolates": _era_isolates,
    "it-plus-auto-closes-a-vertex-selection": _it_plus_auto_closes,
    "it-plus-reuses-a-selected-vertex-in-a-deeper-context": _it_plus_reuses,
}


# -- soundness ----------------------------------------------------------------

SOUNDNESS: Dict[str, Pred] = {
    "it-plus-into-its-own-selection-changes-meaning":
        lambda r, d: _rule(r, "IT+") and r.verdict is not True and bool(r.move.selection)
        and r.move.target in expand(r.g, r.move.selection),
    "it-minus-erases-a-copy-of-another-line-changes-meaning":
        lambda r, d: _rule(r, "IT-") and r.verdict is False
        and "no source of which this is a copy" in r.why,
    "vertex-era-erases-a-line-not-an-equivalence":
        lambda r, d: _rule(r, "VERTEX_ERA") and r.verdict is False and "not isolated" in r.why,
    "merge-vertices-erases-a-constant-vertex":
        lambda r, d: _rule(r, "MERGE_VERTICES") and bool(erased_constants(r.g, r.outcome.result)),
    "retract-ligature-erases-a-constant-vertex":
        lambda r, d: _rule(r, "RETRACT_LIGATURE") and bool(erased_constants(r.g, r.outcome.result)),
    "move-branches-moves-the-identity-edge-it-moves-along":
        lambda r, d: _rule(r, "MOVE_BRANCHES") and moved_join(r),
    "ligature-rules-take-a-join-deeper-than-its-vertices":
        lambda r, d: r.move.rule in ("RETRACT_LIGATURE", "REARRANGE_LIGATURE")
        and not erased_constants(r.g, r.outcome.result)
        and join_deeper_than_its_vertices(r.g, r.move.selection),
}


CLASSIFIERS: Dict[str, Dict[str, Pred]] = {
    "refusal": REFUSAL, "structure": STRUCTURE, "soundness": SOUNDNESS,
}


def claims(layer: str, rec, detail: str) -> Tuple[str, ...]:
    """Every entry of ``layer`` whose classifier claims this failure (exclusive
    by construction: more than one is itself reported by the ledger check)."""
    return tuple(eid for eid, pred in CLASSIFIERS.get(layer, {}).items() if pred(rec, detail))


def classify(layer: str, rec, detail: str):
    """The one entry claiming this failure, or None; two claims are an error."""
    found = claims(layer, rec, detail)
    if len(found) > 1:
        raise ValueError(f"{rec.key}: claimed by {found}")
    return found[0] if found else None
