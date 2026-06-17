"""
DLCore — the three Description-Logic reasoning services, on Arisbe's own engine.

The first track of a DL benchmark (DL-ReasonSuite's *DLCore*) asks three things of an
ontology M, all of which Arisbe already largely answers, here gathered behind one
fragment-honest, signature-aware façade:

* **subsumption** — is ``C ⊑ D`` a theorem of M?  Decided by ``theory_query.entails``
  (freeze a fresh witness, materialize M over it, check the head): sound + Horn-complete.
* **instance checking** — is the named individual ``a`` an instance of ``C``?  Decided by
  forward-chaining M's Horn fragment to the least Herbrand model and reading the closure.
* **consistency** — does M have a model at all?  Decided by materializing the Horn
  fragment and testing each **denial** (``~[ A… ]`` — a disjointness / negative
  constraint) against the closure: a denial satisfied in the *least* Herbrand model is
  violated in *every* model, so M is genuinely inconsistent (sound).

Three commitments make this honest rather than overclaiming, and they are exactly what a
benchmark should measure:

1. **Three-valued, not boolean.** Every service can answer ``UNKNOWN`` — the open-world
   horizon, or M's non-Horn residue the materializer left to the contest game.  A boolean
   reasoner that must guess here is the thing under test, not the oracle.
2. **Fragment-honest.** Arisbe models a bounded DL fragment (Horn rules + denials + the
   `owl_to_clif` class-expression set).  A construct outside it is reported ``UNSUPPORTED``,
   never silently mis-decided.  So a ``YES`` consistency verdict is only given when M lies
   wholly within the fragment; otherwise ``UNKNOWN`` (within-fragment consistent, but an
   unsupported axiom might bear).  An inconsistency, by contrast, is reliable whenever it
   is found.
3. **Signature-aware.** A query naming a class/relation M never defined is ``OUT_OF_SIGNATURE``
   — "M cannot even address that", distinct from "M cannot confirm that" (the
   vocabulary-miss vs. fact-miss distinction the NL-parse use case turns on).

This module adds no new reasoning power; it composes ``theory_query`` + ``model_materialization``
into the DLCore task shape and adds the consistency check + the signature/fragment classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts
from model_materialization import Fact, Key, _match_body, materialize_egi
from theory_query import entails


class DLAnswer(Enum):
    """A DLCore verdict — three-valued, plus two honest refusals."""
    YES = "yes"                        # entailed / consistent / is-an-instance (decided)
    NO = "no"                          # not entailed / inconsistent / not-an-instance (decided)
    UNKNOWN = "unknown"                # the fragment cannot decide it (non-Horn residue / open world)
    UNSUPPORTED = "unsupported"        # the task uses a construct outside Arisbe's DL fragment
    OUT_OF_SIGNATURE = "out_of_signature"  # the query names vocabulary M never defined


@dataclass
class DLResult:
    """One DLCore answer, with the evidence that produced it."""
    task: str                          # "subsumption" | "instance" | "consistency"
    answer: DLAnswer
    detail: str = ""
    query: str = ""                    # human-readable query (e.g. "Dog ⊑ Animal")
    derived: List[str] = field(default_factory=list)    # supporting facts / the violated denial
    missing: List[str] = field(default_factory=list)    # head atoms not derivable
    unsupported_axioms: int = 0        # non-Horn axioms M left to the contest game

    @property
    def decided(self) -> bool:
        return self.answer in (DLAnswer.YES, DLAnswer.NO)


# ---------------------------------------------------------------------------
# Signature + fragment helpers
# ---------------------------------------------------------------------------

def ontology_signature(egi: RelationalGraphWithCuts) -> Set[str]:
    """Every relation/class name M mentions (across all areas) — M's vocabulary."""
    return {egi.get_relation_name(e.id) for e in egi.E}


def _keyv(egi: RelationalGraphWithCuts, vid: str) -> Key:
    vmap = {v.id: v for v in egi.V}
    v = vmap[vid]
    return ("c", v.label) if (not v.is_generic and v.label) else ("g", vid)


def _ground_facts_by_key(
    facts_egi: RelationalGraphWithCuts,
) -> Tuple[Dict[Tuple[str, int], List[Tuple[Key, ...]]], Set[Tuple[str, Tuple[str, ...]]]]:
    """Index a materialized (ground) facts-EGI for matching + membership tests.

    Returns ``(facts_by_key, label_facts)``: the first for ``_match_body``; the second a
    plain ``(rel, (label, …))`` set for instance lookups.  Materialization grounds every
    line, so each fact's arguments are constants.
    """
    edge_ids = {e.id for e in facts_egi.E}
    facts_by_key: Dict[Tuple[str, int], List[Tuple[Key, ...]]] = {}
    label_facts: Set[Tuple[str, Tuple[str, ...]]] = set()
    for eid in facts_egi.area.get(facts_egi.sheet, ()):
        if eid not in edge_ids:
            continue
        rel = facts_egi.get_relation_name(eid)
        keys = tuple(_keyv(facts_egi, v) for v in facts_egi.nu[eid])
        facts_by_key.setdefault((rel, len(keys)), []).append(keys)
        label_facts.add((rel, tuple(k[1] for k in keys)))
    return facts_by_key, label_facts


def _sheet_denials(egi: RelationalGraphWithCuts) -> List[Tuple[List[Fact], str]]:
    """The sheet-level **denials** — cuts ``~[ A… ]`` with no nested cut (a disjointness /
    negative constraint).  Mirrors ``materialize_egi``'s 'denial' classification, but keeps
    the structured body so it can be matched against the closure."""
    edge_ids = {e.id for e in egi.E}
    cut_ids = {c.id for c in egi.Cut}
    out: List[Tuple[List[Fact], str]] = []
    for c1 in [x for x in egi.area.get(egi.sheet, ()) if x in cut_ids]:
        if any(x in cut_ids for x in egi.area.get(c1, ())):
            continue  # has a nested cut → a rule or a complex shape, not a flat denial
        body: List[Fact] = [
            (egi.get_relation_name(e), tuple(_keyv(egi, v) for v in egi.nu[e]))
            for e in egi.area.get(c1, ()) if e in edge_ids
        ]
        if body:
            # Readable description: distinct generic lines → x, y, z, …; constants verbatim.
            gen_names: Dict[Key, str] = {}
            def show(k: Key) -> str:
                if k[0] == "c":
                    return k[1]
                if k not in gen_names:
                    gen_names[k] = chr(ord("x") + len(gen_names) % 3) + (
                        str(len(gen_names) // 3) if len(gen_names) >= 3 else "")
                return gen_names[k]
            desc = " ".join(
                f"{rel}(" + ",".join(show(k) for k in args) + ")" for rel, args in body)
            out.append((body, desc))
    return out


# ---------------------------------------------------------------------------
# Model-construction backstop — the negative half (non-Horn residue)
# ---------------------------------------------------------------------------
# Where the Horn engine must abstain (a non-Horn axiom *might* bear), a positive
# model certificate decides soundly in the opposite direction: a finite model of M
# certifies M **consistent**; a model of ``M ∪ {¬C(a)}`` certifies ``a`` is **not** a
# ``C``.  The finder reads the *whole* EGI (Horn and non-Horn alike) via ``egi_to_fol``,
# so a model it returns satisfies every axiom — the certificate is sound regardless of
# what the Horn materializer skipped.  It works under a sound **unique-names** restriction
# (distinct constants): that can only *narrow* the search (→ abstain), never make a found
# model spurious, so soundness is preserved and the caveat is surfaced in the verdict.


def _find_model(theory: RelationalGraphWithCuts, extra=None):
    """A finite model of M (``extra`` conjoined, if given), or ``None`` if none is found
    within the finder's bounds.  Read-only on ``theory``."""
    from egi_to_fol import read_egi_to_fol
    from folio_model_finder import find_model
    asts = read_egi_to_fol(theory)
    if extra:
        asts = asts + list(extra)
    return find_model(asts)


_UNA_NOTE = "model exhibited under unique-names (distinct constants)"


# ---------------------------------------------------------------------------
# The three DLCore services
# ---------------------------------------------------------------------------

def check_subsumption(
    theory: RelationalGraphWithCuts, sub: str, sup: str,
) -> DLResult:
    """Is ``sub ⊑ sup`` (every ``sub`` a ``sup``) a theorem of M?  Decided by
    ``theory_query.entails`` over the universal ``~[ (sub *x) ~[ (sup x) ] ]``."""
    from egif_parser_dau import parse_egif
    q = f"{sub} ⊑ {sup}"
    sig = ontology_signature(theory)
    missing_sig = [name for name in (sub, sup) if name not in sig]
    if missing_sig:
        return DLResult(task="subsumption", answer=DLAnswer.OUT_OF_SIGNATURE, query=q,
                        detail=f"M does not define: {', '.join(missing_sig)}")

    query = parse_egif(f"~[ ({sub} *x) ~[ ({sup} x) ] ]")
    tq = entails(theory, query)
    if not tq.applicable:
        return DLResult(task="subsumption", answer=DLAnswer.UNSUPPORTED, query=q,
                        detail=tq.detail)
    answer = {"true": DLAnswer.YES, "false": DLAnswer.NO,
              "unknown": DLAnswer.UNKNOWN}[tq.verdict]
    return DLResult(task="subsumption", answer=answer, query=q, detail=tq.summary,
                    derived=tq.derived, missing=tq.missing,
                    unsupported_axioms=tq.skipped_in_theory)


def check_instance(
    theory: RelationalGraphWithCuts, individual: str, cls: str,
) -> DLResult:
    """Is the named individual ``individual`` an instance of ``cls`` in M?  Decided by
    forward-chaining M's Horn fragment and reading the least Herbrand model."""
    q = f'{individual} : {cls}'
    if cls not in ontology_signature(theory):
        return DLResult(task="instance", answer=DLAnswer.OUT_OF_SIGNATURE, query=q,
                        detail=f"M does not define the class {cls}")
    facts_egi, report = materialize_egi(theory)
    _by_key, label_facts = _ground_facts_by_key(facts_egi)
    if (cls, (individual,)) in label_facts:
        return DLResult(task="instance", answer=DLAnswer.YES, query=q,
                        detail=f"{cls}({individual}) is in the least Herbrand model",
                        derived=[f"{cls}({individual})"],
                        unsupported_axioms=len(report.skipped))
    # Not derived: a decided NO only if M is wholly Horn (nothing left that might add it).
    non_denial = [s for s in report.skipped if s.reason != "denial"]
    if non_denial:
        # The Horn engine must abstain — but a model of M ∪ {¬C(a)} decides NO soundly
        # (it exhibits a world where M holds and a is not a C → C(a) is not entailed).
        from folio_fol import Atom, Not
        model = _find_model(theory, extra=[Not(Atom(cls, (individual,)))])
        if model is not None:
            return DLResult(task="instance", answer=DLAnswer.NO, query=q,
                            detail=(f"a model of M with {cls}({individual}) false exists — "
                                    f"{cls}({individual}) is not entailed ({_UNA_NOTE}): "
                                    f"{model.describe()}"),
                            missing=[f"{cls}({individual})"],
                            derived=[model.describe()],
                            unsupported_axioms=len(report.skipped))
        return DLResult(task="instance", answer=DLAnswer.UNKNOWN, query=q,
                        detail=(f"{cls}({individual}) not derived from the Horn fragment; "
                                f"{len(non_denial)} non-Horn axiom(s) might bear "
                                f"(no countermodel found within the finder's bound)"),
                        missing=[f"{cls}({individual})"],
                        unsupported_axioms=len(report.skipped))
    return DLResult(task="instance", answer=DLAnswer.NO, query=q,
                    detail=f"{cls}({individual}) not derivable and M is wholly Horn",
                    missing=[f"{cls}({individual})"])


def check_consistency(theory: RelationalGraphWithCuts) -> DLResult:
    """Does M have a model?  Materialize the Horn fragment, then test each denial.

    A denial satisfied in the least Herbrand model is violated in *every* model (the least
    model embeds in all of them), so M is genuinely **inconsistent** (a sound NO).  A YES is
    given only when M is wholly within the fragment and no denial fires; otherwise UNKNOWN
    (within-fragment consistent, but an unsupported axiom might still bear)."""
    facts_egi, report = materialize_egi(theory)
    facts_by_key, _label = _ground_facts_by_key(facts_egi)
    for body, desc in _sheet_denials(theory):
        if _match_body(body, facts_by_key):
            return DLResult(task="consistency", answer=DLAnswer.NO,
                            detail=f"a disjointness/denial is violated in M's closure: ~[ {desc} ]",
                            derived=[desc])
    # No denial fired.  Honest YES only within the fragment.
    unsupported = [s for s in report.skipped
                   if s.reason in ("complex_body", "negation_in_head", "existential_head")]
    if unsupported:
        # The Horn check is silent on the non-Horn residue — but *exhibiting* a finite model
        # of the whole M certifies consistency soundly (a real model is a real model).
        model = _find_model(theory)
        if model is not None:
            return DLResult(task="consistency", answer=DLAnswer.YES,
                            detail=(f"a finite model of M exists — M is consistent "
                                    f"({_UNA_NOTE}): {model.describe()}"),
                            derived=[model.describe()],
                            unsupported_axioms=len(unsupported))
        return DLResult(task="consistency", answer=DLAnswer.UNKNOWN,
                        detail=(f"no modelled denial is violated, but {len(unsupported)} "
                                f"axiom(s) lie outside Arisbe's fragment, and no model was "
                                f"found within the finder's bound — consistency within the "
                                f"fragment only"),
                        unsupported_axioms=len(unsupported))
    return DLResult(task="consistency", answer=DLAnswer.YES,
                    detail="M is wholly within the fragment and no denial is violated")
