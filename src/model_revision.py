"""
model_revision — the minimal step by which a reference model M *transforms
through ongoing dialog*.

An inning of the Endoporeutic Game is *given M, then G*: a proposal G is peeled
against the model M and disposed of (a theorem, a refutation, a new fact, …). What
the disposition taxonomy names but the engine did not yet enact is **revising M
itself** — the model is not frozen, and the dialogue is exactly how it grows and is
corrected. This module supplies that step.

Two moves, and they are the two the calculus already licenses on the sheet of a
model (docs/MANIFEST_AND_MEANING.md floor #1–#2; docs/LEVEL_ZERO_AND_THE_REGISTERS.md §5):

  * **Enlargement** — admit a new ground fact (the ``new_fact`` disposition: an
    *independent* proposal the dialogue accepts as evidence). The fact is juxtaposed
    onto M's sheet — a new posit, entering at **low warrant**, never asserted true.
  * **Relinquishment** — retract a fact (the dual: *free to demote*, ERA in the
    positive context M's facts inhabit). Nothing in a model is ever frozen; the only
    bedrock is the blank sheet.

A model so revised is a **diachronic UoD**: each revision is a recorded transition,
so M carries its own history (the ``ProofChain`` / ``save_uod_with_chain`` machinery),
and "how M came to be what it is" is replayable — the dialogue, drawn. The verdict a
later inning gives can flip as M grows, which is the whole point: *fact is the
defeasible status of the last-standing trajectory*, answerable to new evidence.

Geometry-free except for the §3.3 attestation that ``save`` already enforces on the
resulting model. Used by ``tools/build_dialog_model_evolution.py``.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from egi_core_dau import RelationalGraphWithCuts
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif

# --------------------------------------------------------------------------- #
# The inning-outcome taxonomy, scoped to the dispositions that *revise M*       #
# --------------------------------------------------------------------------- #
#
# An inning of the Endoporeutic Game ends in a disposition (the full taxonomy of
# 13 lives in ``web_api/services/agonothetes.py`` and
# ``docs/ENDOPOREUTIC_GAME_GUIDE.md`` §"Taxonomy of Game Outcomes"). Only a subset
# *transforms the model itself* — and those are exactly the model-revising moves
# this module enacts. Each carries a **Peircean mode of inference** (the guide §IV)
# and a structural **kind** (how it touches M's sheet):
#
#   enlargement  — juxtapose content onto M's sheet (a posit; INS at the sheet)
#   relinquishment — erase content from M's sheet (free to demote; ERA, positive ctx)
#
# The same structural move (juxtaposition) can carry *different* inferential
# warrant depending on the inning outcome — that distinction is the taxonomy's,
# not the geometry's, so it lives here as data and is recorded on the revision.
DISPOSITION_NEW_FACT = "new_fact"        # 3a — admit an observed independent proposal
DISPOSITION_RETRACT = "retract_fact"     # relinquish a sheet-level fact (free to demote)
DISPOSITION_ABDUCTIVE = "abductive_hypothesis"   # 3b — admit an explanatory hypothesis
DISPOSITION_DEFINITION = "definition"            # 3d — admit terminology by convention
DISPOSITION_CONDITIONAL = "conditional_acceptance"  # 3e — admit a rule P → G
DISPOSITION_GENERALIZATION = "generalization"    # Case 8 — admit an inductive law
DISPOSITION_REGISTRATION = "theorem_registration"  # 1a — admit a derived theorem
DISPOSITION_REDUCTIO = "reductio"        # 2d — admit ¬G as a constraint
DISPOSITION_CHALLENGE_M = "challenge_to_M"  # 2b — the refutation revises M (relinquish + admit)

# disposition key → its place in the taxonomy. ``content`` names which argument
# carries the move's payload: "fact" (a sheet atom), "rule" (a P→G / law cut),
# "constraint" (a ¬G cut), "relation" (the name to drop), or "both" (retract a
# rule/fact *and* admit the anomaly that refuted it).
REVISION_TAXONOMY: Dict[str, Dict[str, str]] = {
    DISPOSITION_NEW_FACT: {
        "mode": "induction", "kind": "enlargement", "content": "fact",
        "summary": "G is independent of M and observed — admit it; M grows by induction."},
    DISPOSITION_ABDUCTIVE: {
        "mode": "abduction", "kind": "enlargement", "content": "fact",
        "summary": "G explains something puzzling in M — admit it as a hypothesis, pending evidence."},
    DISPOSITION_GENERALIZATION: {
        "mode": "induction", "kind": "enlargement", "content": "rule",
        "summary": "an inductive leap from the instances to a law (the most Peircean move) — admit the rule."},
    DISPOSITION_CONDITIONAL: {
        "mode": "deduction", "kind": "enlargement", "content": "rule",
        "summary": "G holds under an added premise P — admit the rule P → G."},
    DISPOSITION_DEFINITION: {
        "mode": "convention", "kind": "enlargement", "content": "fact",
        "summary": "G introduces terminology/structure accepted by convention — admit it."},
    DISPOSITION_REGISTRATION: {
        "mode": "deduction", "kind": "enlargement", "content": "fact",
        "summary": "G is entailed by M — admit it as a derived theorem; M grows by deduction."},
    DISPOSITION_REDUCTIO: {
        "mode": "deduction", "kind": "enlargement", "content": "constraint",
        "summary": "the contradiction establishes ¬G as a theorem of M — admit that constraint."},
    DISPOSITION_RETRACT: {
        "mode": "none", "kind": "relinquishment", "content": "relation",
        "summary": "relinquish a sheet-level fact (the ERA dual) — free to demote."},
    DISPOSITION_CHALLENGE_M: {
        "mode": "abduction", "kind": "relinquishment", "content": "both",
        "summary": "G's refutation is evidence against M (the irritation of doubt) — relinquish the "
                   "impugned law/fact and admit the anomaly; M is revised."},
}


def revision_taxonomy(disposition: str) -> Dict[str, str]:
    """The taxonomy entry (mode / kind / content / summary) for a model-revising
    disposition. Raises if the disposition does not revise M (e.g. ``redundancy``,
    ``rejection``, ``open_conjecture``, ``tautology`` — recorded judgments that
    leave M untouched)."""
    try:
        return dict(REVISION_TAXONOMY[disposition])
    except KeyError:
        raise ValueError(
            f"disposition {disposition!r} does not revise M; the M-revising subset is "
            f"{sorted(REVISION_TAXONOMY)}")


def assert_fact(model: RelationalGraphWithCuts, fact_egif: str) -> RelationalGraphWithCuts:
    """**Enlargement.** Admit ``fact_egif`` into the model by juxtaposing it onto
    M's sheet (conjunction). The result is a new posit at low warrant — the model
    has *grown*, not been proven. Returns a fresh EGI (M ∧ fact).

    The same juxtaposition serves every *enlargement* disposition (a fact, a rule
    P→G, a ¬G constraint) — what differs is the inning's inferential mode and
    warrant, which the taxonomy records, not the geometry. ``add_rule`` is the
    rule-shaped alias."""
    base = generate_egif(model).strip()
    fact = fact_egif.strip()
    combined = f"{base} {fact}".strip() if base else fact
    return parse_egif(combined)


def add_rule(model: RelationalGraphWithCuts, rule_egif: str) -> RelationalGraphWithCuts:
    """**Enlargement by a rule** — admit a law / conditional ``~[ B ~[ H ] ]`` onto
    M's sheet (the structural twin of ``assert_fact``, named for the taxonomy). A
    range-restricted Horn rule is forward-chained by ``model_materialization`` at
    audit time, so the law *covers new individuals* (a generalization absorbs the
    newcomer an isolated fact-list could not). Used by the generalization (Case 8),
    conditional-acceptance (3e) and definition (3d) dispositions."""
    return assert_fact(model, rule_egif)


def retract_subgraph(
    model: RelationalGraphWithCuts, subgraph_egif: str
) -> RelationalGraphWithCuts:
    """**Relinquishment of a sheet-level subgraph** — a rule / negation *cut*, the
    structural generalization of ``retract_relation`` (which drops only sheet atoms).

    **On the rule status, precisely** (the opening line used to claim ERA and the
    closing paragraph to deny it — both were half right). M's laws sit on the
    **sheet**, which is *positive*, and ERA erases from a positive context — so
    relinquishing a law **is** a genuine Dau ERA, and it *is* sound (erasure weakens:
    M ⊨ M−X). ``model_acts.relinquish`` performs it that way and says so. This
    function removes the subtree **structurally** instead, for one operational reason
    recorded below — and the result is the same graph, and still a weakening; it is
    only the *licence* that differs. Use ``model_acts.relinquish`` when the record
    should say which it was.

    This is the move a **challenge-to-M** makes on an over-general law: the black
    swan refutes "all swans are white", so the law is relinquished.

    Structural (``_without_cut_subtree``), like ``retract_atom`` — *not* a Dau ERA.
    ERA's for-erasure closure rejects a sheet-level cut whose interior shares a line
    of identity across an area boundary ("elements not in target area"), and because
    the probe below ERAs *every* sheet cut, one such cut used to crash the whole
    retraction (RUN_8_LOG: the reseeded temp law after materialization). Removing the
    subtree structurally never raises, so a non-matching cut is simply skipped."""
    from eg_navigation import child_cuts, same_graph

    parse_egif(subgraph_egif)   # validate the target parses (raises early if not)
    for cut_id in child_cuts(model, model.sheet):
        erased = _without_cut_subtree(model, cut_id)   # remove the cut as a unit
        if same_graph(assert_fact(erased, subgraph_egif), model):
            return erased
    raise ValueError(
        f"no sheet-level subgraph matching {subgraph_egif!r} to retract")


def _without_cut_subtree(
    model: RelationalGraphWithCuts, cut_id: str
) -> RelationalGraphWithCuts:
    """Return ``model`` with ``cut_id`` and everything it transitively contains
    removed — erasing the cut *as a unit* structurally, without the ERA closure
    validator. Argument vertices still incident to a **surviving** edge are kept
    (not pruned), so relinquishing a law-cut never severs a sheet atom's line of
    identity. Nested cuts are removed deepest-first so each redistributes only
    already-emptied contents."""
    contained = set(model.get_full_context(cut_id))
    del_edges = contained & {e.id for e in model.E}
    del_cuts = (contained & {c.id for c in model.Cut}) | {cut_id}
    surviving_incidence = set()
    for e in model.E:
        if e.id not in del_edges:
            surviving_incidence.update(model.nu.get(e.id, ()))
    del_verts = (contained & {v.id for v in model.V}) - surviving_incidence

    def _depth(cid: str) -> int:
        d, cur = 0, cid
        while cur != model.sheet:
            cur = model.get_context(cur)
            d += 1
        return d

    g = model
    for eid in del_edges:
        g = g.without_element(eid)
    for vid in del_verts:
        g = g.without_element(vid)
    for cid in sorted(del_cuts, key=_depth, reverse=True):
        g = g.without_element(cid)
    return g


def _labels(model: RelationalGraphWithCuts, edge_id: str) -> List[Optional[str]]:
    return [model.get_vertex(v).label for v in model.nu.get(edge_id, ())]


def _atom_egif(model: RelationalGraphWithCuts, edge) -> str:
    """The EGIF of one ground-fact atom: relation name + its constant arguments."""
    name = model.rel.get(edge.id)
    args = []
    for v in model.nu.get(edge.id, ()):
        label = model.get_vertex(v).label
        args.append(f'"{label}"' if label else "*x")
    return f"({name} {' '.join(args)})" if args else f"({name})"


def retract_atom(
    model: RelationalGraphWithCuts, relation: str, labels: List[Optional[str]]
) -> RelationalGraphWithCuts:
    """**Relinquishment of one specific sheet atom** — drop the sheet-level fact whose relation
    name is ``relation`` and whose argument labels are exactly ``labels`` (finer than
    ``retract_relation``, which drops *every* fact of a name). Needed when a relation is
    multi-valued — e.g. a Wikidata property that holds several statements — and only the
    contradicted/deprecated value must go. Raises if no such atom is present.

    Structural (``without_element``), so everything else on the sheet — other atoms of the
    same name, standing *law cuts* — is preserved untouched. That matters because this is the
    erasure primitive of **atom-level disuse-decay** (the rulebook decision, 2026-07-03):
    decay fires per fact, routinely, on a sheet that may carry laws. An argument vertex left
    with no remaining incidence is pruned with its atom (the individual was only ever posited
    by the retracted habit)."""
    from eg_navigation import area_of
    want = tuple(labels)
    matches = [e for e in model.E
               if area_of(model, e.id) == model.sheet
               and model.rel.get(e.id) == relation and tuple(_labels(model, e.id)) == want]
    if not matches:
        raise ValueError(f"no sheet-level fact {relation}{want} to retract")
    g = model
    for e in matches:
        args = g.nu.get(e.id, ())
        g = g.without_element(e.id)
        for vid in dict.fromkeys(args):      # each argument once
            if not any(vid in incident for incident in g.nu.values()):
                g = g.without_element(vid)   # orphaned by the retraction — prune
    return g


def retract_relation(
    model: RelationalGraphWithCuts, relation: str
) -> RelationalGraphWithCuts:
    """**Relinquishment.** Drop every sheet-level fact named ``relation`` from M
    (the dual of enlargement — *free to demote*). Rebuilds M from its surviving
    atoms, so the model can fall as well as grow. Raises if no such fact is present
    (a retraction must have something to retract)."""
    from eg_navigation import area_of
    sheet_edges = [e for e in model.E if area_of(model, e.id) == model.sheet]
    if not any(model.rel.get(e.id) == relation for e in sheet_edges):
        raise ValueError(f"no sheet-level fact named {relation!r} to retract")
    keep = [e for e in sheet_edges if model.rel.get(e.id) != relation]
    return parse_egif(" ".join(_atom_egif(model, e) for e in keep))


def revise_with_disposition(
    model: RelationalGraphWithCuts,
    disposition: str,
    *,
    fact_egif: Optional[str] = None,
    relation: Optional[str] = None,
    rule_egif: Optional[str] = None,
    subgraph_egif: Optional[str] = None,
    labels: Optional[List[Optional[str]]] = None,
) -> RelationalGraphWithCuts:
    """Enact any **model-revising inning outcome** (the ``REVISION_TAXONOMY`` subset
    of the EPG disposition taxonomy), returning the revised M. The structural move
    follows the disposition's taxonomy ``kind``/``content``; the *mode* of inference
    (induction / deduction / abduction / convention) is the taxonomy's to record.

      enlargement (juxtapose a posit onto M's sheet) —
        * ``new_fact`` (3a, induction), ``abductive_hypothesis`` (3b, abduction),
          ``definition`` (3d, convention), ``theorem_registration`` (1a, deduction)
          — admit ``fact_egif``.
        * ``generalization`` (Case 8, induction), ``conditional_acceptance`` (3e,
          deduction) — admit a law ``rule_egif`` (forward-chained at audit time).
        * ``reductio`` (2d, deduction) — admit a ¬G ``fact_egif`` constraint.
      relinquishment (erase from M's sheet) —
        * ``retract_fact`` — drop every fact named ``relation``.
        * ``challenge_to_M`` (2b, abduction) — *the irritation of doubt*: relinquish
          the impugned law (``subgraph_egif``) and/or fact (``relation``), then admit
          the refuting anomaly (``fact_egif``). M is revised.

    Non-revising dispositions (``redundancy``, ``rejection``, ``open_conjecture``,
    ``tautology``, …) leave M untouched and are rejected here — they are recorded
    judgments, not model edits.
    """
    spec = revision_taxonomy(disposition)   # raises for a non-revising disposition

    # Enlargement family — the structural move is juxtaposition; ``content`` says
    # which argument carries it (a rule for laws, a fact/constraint otherwise).
    if spec["kind"] == "enlargement":
        if spec["content"] == "rule":
            payload = rule_egif or subgraph_egif
            if not payload:
                raise ValueError(f"{disposition} disposition requires rule_egif")
            return add_rule(model, payload)
        if not fact_egif:
            raise ValueError(f"{disposition} disposition requires fact_egif")
        return assert_fact(model, fact_egif)

    # Relinquishment family.
    if disposition == DISPOSITION_RETRACT:
        if not relation:
            raise ValueError("retract_fact disposition requires relation")
        if labels is not None:                       # atom-level: drop just this value
            return retract_atom(model, relation, labels)
        return retract_relation(model, relation)     # coarse: drop every fact of the name

    if disposition == DISPOSITION_CHALLENGE_M:
        revised = model
        if subgraph_egif:
            revised = retract_subgraph(revised, subgraph_egif)
        if relation:
            revised = retract_relation(revised, relation)
        if fact_egif:
            revised = assert_fact(revised, fact_egif)
        if revised is model:
            raise ValueError(
                "challenge_to_M requires something to relinquish (subgraph_egif / "
                "relation) and/or an anomaly to admit (fact_egif)")
        return revised

    raise ValueError(f"disposition {disposition!r} does not revise M")
