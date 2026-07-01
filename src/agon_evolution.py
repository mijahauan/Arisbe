"""Automated model development — the Agon as the engine of change.

Design-of-record: ``docs/AUTOMATED_MODEL_DEVELOPMENT.md``. A *generation* is a
round of the Endoporeutic Game:

  ① **produce** a candidate graph G (the *membrane*) →
  ② **test** G against the developing model M (peel + materialize) →
  ③ **negotiate** a disposition of the outcome among several agents →
  ④ **inject** the chosen disposition's revision into M →
  ⑤ **decay** elements that have fallen from use.

Run K rounds and the M-states form a diachronic ``DOMAIN_MODEL`` UoD — the same
shape ``tools/build_swan_generalization.py`` builds *by hand*. This module
automates the *player*.

**Stage 0 (here): a CLOSED membrane.** Proposals are drawn from corpus material
(an explicit pool, or structural recombination of M) — no external dependency,
reproducible under a fixed order. The ``Proposer`` Protocol is the socket an open
membrane (LLM / human / online) plugs into later.

Conway's Life is bounded by its plane's edge; the Agon's sheet is *unbounded*, so
the only thing that bounds it — and shapes the emergence — is **selection from
outside**: the test (②), the disposition (③), and disuse-decay (⑤). This module is
that outside made operational.

Additive and geometry-free: it composes ``semantic_game`` / ``model_materialization``
/ ``model_revision`` / ``proof_authoring`` and touches no protected module's
internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set, Tuple

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from egi_core_dau import RelationalGraphWithCuts
from eg_navigation import area_of, child_cuts, same_graph
from domain_oracle import CorpusOracle
from semantic_game import Verdict3, evaluate, SemanticResult
from model_materialization import materialize_egi
from model_revision import (
    DISPOSITION_NEW_FACT,
    DISPOSITION_GENERALIZATION,
    DISPOSITION_CHALLENGE_M,
    retract_relation,
    revise_with_disposition,
    revision_taxonomy,
)
from proof_authoring import ProofChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory


# --------------------------------------------------------------------------- #
# ② Test — peel G against M (closed-world, laws forward-chained first)         #
# --------------------------------------------------------------------------- #

def peel(
    model: RelationalGraphWithCuts, proposal_egif: str, *, closed: bool = True
) -> SemanticResult:
    """Peel a proposal G against a model state, materializing M's Horn fragment
    first so any admitted *law* covers new individuals (mirrors the swan
    exemplar's ``_verdict``). M is the truth-teller — this is mechanical, not an
    opinion."""
    facts, _ = materialize_egi(model)
    oracle = CorpusOracle([("M", facts)], closed=closed)
    return evaluate(parse_egif(proposal_egif), oracle, closed=closed)


# --------------------------------------------------------------------------- #
# Small structural readers over an EGIF proposal                              #
# --------------------------------------------------------------------------- #

def _is_law(egif: str) -> bool:
    """A *law* (scroll ``~[ B ~[ H ] ]``): a sheet-level cut that itself holds a
    nested cut."""
    g = parse_egif(egif)
    for cut in child_cuts(g, g.sheet):
        if child_cuts(g, cut):
            return True
    return False


def _is_ground_positive(egif: str) -> bool:
    """No sheet-level cut at all — a conjunction of (possibly constant) atoms."""
    g = parse_egif(egif)
    return not child_cuts(g, g.sheet)


def _sheet_relations(model: RelationalGraphWithCuts) -> Set[str]:
    """Relation names occurring as *sheet-level* facts (the decayable units)."""
    return {
        model.rel[e.id]
        for e in model.E
        if area_of(model, e.id) == model.sheet and e.id in model.rel
    }


def _relations_of(egif: str) -> Set[str]:
    g = parse_egif(egif)
    return {g.rel[e.id] for e in g.E if e.id in g.rel}


def _antecedent_relation(law_egif: str) -> Optional[str]:
    """The relation named in a scroll's *body* (the antecedent ``B`` of
    ``~[ B ~[ H ] ]``) — used to require a law have ≥1 supporting instance."""
    g = parse_egif(law_egif)
    for cut in child_cuts(g, g.sheet):
        if not child_cuts(g, cut):
            continue
        for e in g.E:
            if area_of(g, e.id) == cut and e.id in g.rel:
                return g.rel[e.id]
    return None


def _already_holds(model: RelationalGraphWithCuts, ground_egif: str) -> bool:
    """Every atom of a ground proposal is already a sheet fact of M (with the
    same relation + constant arguments)."""
    existing = {
        (model.rel[e.id], tuple(_labels(model, e.id)))
        for e in model.E
        if area_of(model, e.id) == model.sheet and e.id in model.rel
    }
    g = parse_egif(ground_egif)
    for e in g.E:
        if e.id not in g.rel:
            return False
        if (g.rel[e.id], tuple(_labels(g, e.id))) not in existing:
            return False
    return True


def _labels(graph: RelationalGraphWithCuts, edge_id: str) -> List[Optional[str]]:
    return [graph.get_vertex(v).label for v in graph.nu.get(edge_id, ())]


# --------------------------------------------------------------------------- #
# ① Produce — the membrane (Stage 0: closed)                                  #
# --------------------------------------------------------------------------- #

class Proposer(Protocol):
    """The membrane. ``propose`` returns the next round's candidate graph as
    EGIF, or ``None`` when the membrane is exhausted (ends the run). An *open*
    membrane (LLM / human / online) implements this same shape."""

    def propose(
        self, model: RelationalGraphWithCuts, round_idx: int
    ) -> Optional[str]: ...


class CorpusProposer:
    """A closed membrane: hand the loop a fixed pool of EGIF proposals, one per
    round, in order. Reproducible. (The swan pool replayed through this proposer
    reproduces the hand-played swan trajectory.)"""

    def __init__(self, pool: Sequence[str]):
        self._pool = list(pool)

    def propose(self, model, round_idx):
        i = round_idx - 1
        return self._pool[i] if 0 <= i < len(self._pool) else None


class MutationProposer:
    """A closed membrane that *recombines* M instead of replaying a pool: it
    enumerates candidate unary subsumption laws ``~[ (R *x) ~[ (S x) ] ]`` over
    the unary relations present in the seed model, in a deterministic order. It
    invents no new vocabulary — so what it surfaces is the subsumption lattice
    the corpus *already commits to* (a law the Generalizer admits) versus the
    pairs it refutes (no agent fires → rejection). Stage-0 'discover the tensions
    latent in the corpus'."""

    def __init__(self, seed_model_egif: str):
        model = parse_egif(seed_model_egif)
        unary = sorted({
            model.rel[e.id]
            for e in model.E
            if e.id in model.rel and len(model.nu.get(e.id, ())) == 1
        })
        self._candidates = [
            f"~[ ({r} *x) ~[ ({s} x) ] ]"
            for r in unary for s in unary if r != s
        ]

    def propose(self, model, round_idx):
        i = round_idx - 1
        return self._candidates[i] if 0 <= i < len(self._candidates) else None


# --------------------------------------------------------------------------- #
# ③ Negotiate — the Agonothetes panel (where the emergence lives)             #
# --------------------------------------------------------------------------- #

@dataclass
class DeliberationContext:
    """What each policy-agent sees when it votes."""
    model: RelationalGraphWithCuts
    proposal_egif: str
    result: SemanticResult
    known_laws: Sequence[str]   # law EGIFs admitted so far and not yet relinquished
    round_idx: int = 0          # which round this deliberation belongs to (for logging)

    @property
    def verdict(self) -> Verdict3:
        return self.result.verdict


@dataclass
class Vote:
    agent: str
    disposition: str
    kwargs: Dict[str, str]
    rationale: str
    priority: int


class PolicyAgent(Protocol):
    def vote(self, ctx: DeliberationContext) -> Optional[Vote]: ...


class ObserverAgent:
    """Induction. A genuinely new, consistent ground observation → ``new_fact``.
    Abstains if the observation is redundant, or if it would refute a standing
    law (the Challenger handles that, with higher priority)."""

    name = "observer"
    priority = 10

    def vote(self, ctx):
        if not _is_ground_positive(ctx.proposal_egif):
            return None
        if _already_holds(ctx.model, ctx.proposal_egif):
            return None
        if _refuted_law(ctx) is not None:
            return None
        return Vote(
            self.name, DISPOSITION_NEW_FACT,
            {"fact_egif": ctx.proposal_egif},
            "observed and independent of M — admit it; M grows by induction.",
            self.priority,
        )


class GeneralizerAgent:
    """Induction — the most Peircean move. A proposed *law* that currently holds
    in M, has ≥1 supporting instance, and is not already on the sheet → admit it
    as a rule (``generalization``)."""

    name = "generalizer"
    priority = 20

    def vote(self, ctx):
        g = ctx.proposal_egif
        if not _is_law(g):
            return None
        if ctx.verdict is Verdict3.FALSE:
            return None
        if any(same_graph(parse_egif(g), parse_egif(l)) for l in ctx.known_laws):
            return None
        ante = _antecedent_relation(g)
        if ante is None or ante not in _sheet_relations(ctx.model):
            return None   # no supporting instance — refuse a vacuous law
        return Vote(
            self.name, DISPOSITION_GENERALIZATION,
            {"rule_egif": g},
            "the instances support it — leap to the law; M grows by induction.",
            self.priority,
        )


class ChallengerAgent:
    """Abduction — the irritation of doubt. A ground proposal that *refutes* a
    standing law in M → relinquish the impugned law and admit the anomaly
    (``challenge_to_M``). The black-swan move."""

    name = "challenger"
    priority = 30

    def vote(self, ctx):
        law = _refuted_law(ctx)
        if law is None:
            return None
        return Vote(
            self.name, DISPOSITION_CHALLENGE_M,
            {"subgraph_egif": law, "fact_egif": ctx.proposal_egif},
            "the proposal refutes a standing law — relinquish the over-general "
            "law and admit the anomaly; M is revised by abduction.",
            self.priority,
        )


class ContradictionAgent:
    """Relinquishment on a *sourced denial*. When a proposal is a bare sheet-level negation
    ``~[ (rel …) ]`` of an atom that currently stands on M's sheet, retract that specific atom
    (``retract_fact`` with atom-level ``labels``). This is the mechanical *source-conflict*
    move: a later, better-warranted source that denies a standing fact (e.g. a Wikidata
    statement deprecated, or a reliable source overturning a bare one) makes M *fall*, not just
    grow. Abstains on anything else. Not in ``DEFAULT_PANEL`` — opt in for the raise-only /
    wiki loops that need denials disposed without an LLM."""

    name = "contradiction"
    priority = 25

    def vote(self, ctx):
        g = parse_egif(ctx.proposal_egif)
        cuts = child_cuts(g, g.sheet)
        # exactly one sheet cut, no sheet-level positive atom (a pure denial)
        if len(cuts) != 1:
            return None
        if any(area_of(g, e.id) == g.sheet and e.id in g.rel for e in g.E):
            return None
        inside = [e for e in g.E if area_of(g, e.id) == cuts[0] and e.id in g.rel]
        if len(inside) != 1 or child_cuts(g, cuts[0]):
            return None
        e = inside[0]
        rel, labels = g.rel[e.id], tuple(_labels(g, e.id))
        standing = {
            (ctx.model.rel[x.id], tuple(_labels(ctx.model, x.id)))
            for x in ctx.model.E
            if area_of(ctx.model, x.id) == ctx.model.sheet and x.id in ctx.model.rel
        }
        if (rel, labels) not in standing:
            return None                          # nothing standing to contradict
        return Vote(
            self.name, "retract_fact",
            {"relation": rel, "labels": list(labels)},
            "a sourced denial contradicts a standing fact — relinquish it.",
            self.priority,
        )


def _refuted_law(ctx: DeliberationContext) -> Optional[str]:
    """The first standing law ``~[ (B *x) ~[ (H x) ] ]`` this proposal *refutes*,
    or ``None``. A Horn law is self-fulfilling under materialization (asserting
    ``B(c)`` merely derives ``H(c)``), so the only thing that refutes it is a
    **counterexample carrying the negation of the head** — ``(B c) ~[ (H c) ]``,
    a B that is *not* an H. We recognise that shape structurally (no disjointness
    axiom required): the proposal has a positive atom ``(B c)`` and a negated atom
    ``~[ (H c) ]`` over the same individual, matching some standing law's B, H."""
    g = parse_egif(ctx.proposal_egif)
    pos = _positive_atoms(g)
    neg = _negated_atoms(g)
    if not neg:
        return None
    for law in ctx.known_laws:
        rels = _law_relations(law)
        if rels is None:
            continue
        body, head = rels
        for rel, labels in pos:
            if rel == body and len(labels) == 1 and (head, labels) in neg:
                return law
    return None


def _positive_atoms(g: RelationalGraphWithCuts) -> Set[Tuple[str, Tuple]]:
    """Sheet-level positive atoms as ``(relation, (labels…))``."""
    return {
        (g.rel[e.id], tuple(_labels(g, e.id)))
        for e in g.E
        if area_of(g, e.id) == g.sheet and e.id in g.rel
    }


def _negated_atoms(g: RelationalGraphWithCuts) -> Set[Tuple[str, Tuple]]:
    """``(relation, (labels…))`` for each sheet cut ``~[ (rel …) ]`` that wraps a
    single atom and nothing else (an explicit negative literal)."""
    out: Set[Tuple[str, Tuple]] = set()
    for cut in child_cuts(g, g.sheet):
        if child_cuts(g, cut):
            continue
        inside = [e for e in g.E if area_of(g, e.id) == cut and e.id in g.rel]
        if len(inside) == 1:
            e = inside[0]
            out.add((g.rel[e.id], tuple(_labels(g, e.id))))
    return out


def _law_relations(law_egif: str) -> Optional[Tuple[str, str]]:
    """``(body_relation, head_relation)`` of a scroll ``~[ (B *x) ~[ (H x) ] ]``."""
    g = parse_egif(law_egif)
    for outer in child_cuts(g, g.sheet):
        inner = child_cuts(g, outer)
        if not inner:
            continue
        body = next((g.rel[e.id] for e in g.E
                     if area_of(g, e.id) == outer and e.id in g.rel), None)
        head = next((g.rel[e.id] for e in g.E
                     if area_of(g, e.id) == inner[0] and e.id in g.rel), None)
        if body and head:
            return body, head
    return None


DEFAULT_PANEL: Tuple[PolicyAgent, ...] = (
    ObserverAgent(), GeneralizerAgent(), ChallengerAgent(),
)


class Agonothetes:
    """The panel. Each agent votes (or abstains); the highest-priority vote
    resolves. The full slate is kept on the outcome (a future build can branch
    the DAG per dissenting disposition — the negotiation made first-class)."""

    def __init__(self, agents: Sequence[PolicyAgent] = DEFAULT_PANEL):
        self._agents = tuple(agents)

    def deliberate(self, ctx: DeliberationContext) -> List[Vote]:
        return [v for a in self._agents if (v := a.vote(ctx)) is not None]

    @staticmethod
    def resolve(votes: Sequence[Vote]) -> Optional[Vote]:
        return max(votes, key=lambda v: v.priority) if votes else None


# --------------------------------------------------------------------------- #
# ⑤ Decay — the only bound on an unbounded plane                              #
# --------------------------------------------------------------------------- #

class UsageLedger:
    """Tracks the round each sheet relation was last *invoked*. A relation idle
    for ``ttl`` rounds has fallen from use and is erased (relinquishment by
    attrition). This is the unbounded sheet's substitute for Life's plane edge —
    selection by use, not by a boundary."""

    def __init__(self, ttl: int):
        self.ttl = ttl
        self._last: Dict[str, int] = {}

    def seed(self, relations: Set[str], round_idx: int = 0) -> None:
        for r in relations:
            self._last.setdefault(r, round_idx)

    def touch(self, relations: Set[str], round_idx: int) -> None:
        for r in relations:
            self._last[r] = round_idx

    def stale(self, round_idx: int) -> List[str]:
        return sorted(
            r for r, last in self._last.items() if round_idx - last >= self.ttl
        )

    def forget(self, relation: str) -> None:
        self._last.pop(relation, None)


# --------------------------------------------------------------------------- #
# Outcomes, discoveries, and the round driver                                 #
# --------------------------------------------------------------------------- #

@dataclass
class RoundOutcome:
    round_idx: int
    proposal_egif: str
    verdict: str
    disposition: Optional[str]      # None ⇒ a non-revising round (M unchanged)
    mode: Optional[str]
    rationale: str
    votes: List[Tuple[str, str]]    # (agent, disposition) — the full slate
    decayed: List[str]              # relations erased by disuse this round
    standing_verdict: Optional[str] # the audited proposal's verdict after the round
    changed: bool
    branched: List[str] = field(default_factory=list)  # dispositions forked as DAG siblings


@dataclass
class Discovery:
    kind: str       # survivor_law | registered_theorem | productive_anomaly
    detail: str
    round_idx: int


@dataclass
class EvolutionResult:
    chain: object                   # TransformationChain
    uod: UniverseOfDiscourse
    outcomes: List[RoundOutcome]
    discoveries: List[Discovery]
    known_laws: List[str] = field(default_factory=list)


def run(
    model_egif: str,
    proposer: Proposer,
    *,
    rounds: int,
    uod_id: str,
    name: str,
    description: Optional[str] = None,
    panel: Optional[Agonothetes] = None,
    ttl: Optional[int] = None,
    standing_proposal: Optional[str] = None,
    seed_laws: Optional[Sequence[str]] = None,
) -> EvolutionResult:
    """Play ``rounds`` automated game rounds, developing M from ``model_egif``.

    Returns the trajectory as a ``TransformationChain`` + a ``DOMAIN_MODEL`` UoD
    (ready for ``TomosService.save_uod_with_chain``), the per-round outcomes, and
    a discovery digest. Deterministic given a deterministic proposer.

    ``ttl`` (optional) turns on disuse-decay; ``standing_proposal`` (optional,
    EGIF) is audited after each round so a verdict flip caused by growth or decay
    is *surfaced*, never silent. ``seed_laws`` (optional, EGIF) are standing laws
    M already carries on its sheet (e.g. from the corpus) that were *not* derived
    in a round — seeding them lets the Challenger recognise a later refutation of
    them (the raise-and-resolve membrane relies on this).
    """
    panel = panel or Agonothetes()
    pc = ProofChain.from_egif(model_egif)
    ledger: Optional[UsageLedger] = None
    if ttl:
        ledger = UsageLedger(ttl)
        ledger.seed(_sheet_relations(pc.current))

    outcomes: List[RoundOutcome] = []
    known_laws: List[str] = list(seed_laws or [])

    for r in range(1, rounds + 1):
        model = pc.current
        pre_id = pc.current_state_id            # the pre-round state a sibling forks from
        g_egif = proposer.propose(model, r)
        if g_egif is None:
            break   # the membrane is exhausted

        result = peel(model, g_egif)
        ctx = DeliberationContext(model, g_egif, result, list(known_laws), round_idx=r)
        votes = panel.deliberate(ctx)
        winner = panel.resolve(votes)
        slate = [(v.agent, v.disposition) for v in votes]

        decayed: List[str] = []
        if winner is None:
            outcomes.append(RoundOutcome(
                r, g_egif, result.verdict.value, None, None,
                "no agent moved — recorded judgment, M untouched.",
                slate, decayed,
                _verdict_or_none(pc.current, standing_proposal), False,
            ))
            continue

        spec = revision_taxonomy(winner.disposition)
        pc.apply_derived(
            "REVISE_M",
            lambda g, w=winner: revise_with_disposition(g, w.disposition, **w.kwargs),
            label=f"{r}·M", note=winner.rationale,
            params={"disposition": winner.disposition, "mode": spec["mode"],
                    "proposal": g_egif, **winner.kwargs},
        )
        _update_known_laws(known_laws, winner)

        if ledger is not None:
            ledger.touch(_relations_of(g_egif), r)
            decayed = _apply_decay(pc, ledger, r)

        # ⑤b — irreducible disagreement: fork the DAG (Stage 3). A judge (e.g. the LLM
        # Agonothetes) may name dissenting votes to carry forward as siblings; each is applied
        # from the *pre-round* state as an alternate reading, then the main line resumes.
        # Selection decides later; no agent must be right in the moment. (§5 of the design.)
        branched = _fork_siblings(pc, panel, votes, winner, pre_id, r)

        outcomes.append(RoundOutcome(
            r, g_egif, result.verdict.value, winner.disposition, spec["mode"],
            winner.rationale, slate, decayed,
            _verdict_or_none(pc.current, standing_proposal), True, branched,
        ))

    chain, uod = pc.to_uod(
        uod_id=uod_id, name=name,
        description=description or _default_description(name),
        category=UoDCategory.DOMAIN_MODEL,
    )
    return EvolutionResult(
        chain=chain, uod=uod, outcomes=outcomes,
        discoveries=_discoveries(outcomes), known_laws=known_laws,
    )


def _fork_siblings(
    pc: ProofChain,
    panel: "Agonothetes",
    votes: Sequence[Vote],
    winner: Vote,
    pre_id: str,
    round_idx: int,
) -> List[str]:
    """Fork a diachronic sibling for each dissenting vote a branch-aware judge flagged. Reads
    the optional ``panel.branch_votes`` hook (absent on the mechanical panel → no branching,
    fully backward compatible). Each sibling is a real fork off ``pre_id`` (two steps share a
    ``from_state_id``); the main line is restored afterwards. Best-effort — a sibling whose
    revision won't apply is skipped, never aborting the run."""
    branch_fn = getattr(panel, "branch_votes", None)
    if branch_fn is None:
        return []
    dissenters = [v for v in branch_fn(votes, winner) if v is not winner]
    if not dissenters:
        return []
    main_id = pc.current_state_id
    branched: List[str] = []
    for bv in dissenters:
        try:
            spec = revision_taxonomy(bv.disposition)
            pc.at(pre_id).apply_derived(
                "REVISE_M(sibling)",
                lambda g, w=bv: revise_with_disposition(g, w.disposition, **w.kwargs),
                label=f"{round_idx}·M~", note=f"dissenting reading (irreducible disagreement): "
                                              f"{bv.rationale}",
                params={"disposition": bv.disposition, "mode": spec["mode"],
                        "sibling": True, **bv.kwargs},
            )
            branched.append(bv.disposition)
        except Exception:
            continue
    pc.at(main_id)   # resume the main line
    return branched


def _update_known_laws(known_laws: List[str], winner: Vote) -> None:
    """Keep the live-laws registry in step with the revision just applied."""
    if winner.disposition == DISPOSITION_GENERALIZATION:
        known_laws.append(winner.kwargs["rule_egif"])
    elif winner.disposition == DISPOSITION_CHALLENGE_M:
        target = winner.kwargs.get("subgraph_egif")
        if target:
            known_laws[:] = [
                l for l in known_laws
                if not same_graph(parse_egif(l), parse_egif(target))
            ]


def _apply_decay(pc: ProofChain, ledger: UsageLedger, round_idx: int) -> List[str]:
    decayed: List[str] = []
    for rel in ledger.stale(round_idx):
        if rel not in _sheet_relations(pc.current):
            ledger.forget(rel)
            continue
        pc.apply_derived(
            "DECAY",
            lambda g, _r=rel: retract_relation(g, _r),
            label=f"{round_idx}·decay",
            note=f"'{rel}' fell from use — erased (disuse-decay).",
            params={"disposition": "retract_fact", "mode": "none", "relation": rel},
        )
        decayed.append(rel)
        ledger.forget(rel)
    return decayed


def _verdict_or_none(
    model: RelationalGraphWithCuts, proposal: Optional[str]
) -> Optional[str]:
    return peel(model, proposal).verdict.value if proposal else None


def _discoveries(outcomes: Sequence[RoundOutcome]) -> List[Discovery]:
    """Surface what the run *found*: laws that took hold and *stood* (never later
    relinquished), and anomalies that productively reshaped M (a challenge that
    relinquished a standing law)."""
    found: List[Discovery] = []

    challenged_rounds = {o.round_idx for o in outcomes
                         if o.disposition == DISPOSITION_CHALLENGE_M}
    for o in outcomes:
        if o.disposition == DISPOSITION_CHALLENGE_M:
            found.append(Discovery(
                "productive_anomaly",
                f"the anomaly {o.proposal_egif} relinquished a standing law "
                f"(round {o.round_idx})",
                o.round_idx,
            ))
    for o in outcomes:
        if o.disposition != DISPOSITION_GENERALIZATION:
            continue
        # a law is a survivor unless a *later* challenge round relinquished one.
        superseded = any(cr > o.round_idx for cr in challenged_rounds)
        found.append(Discovery(
            "survivor_law" if not superseded else "superseded_law",
            f"the law {o.proposal_egif} was admitted (round {o.round_idx})"
            + ("" if not superseded else " and later relinquished"),
            o.round_idx,
        ))
    return found


def _default_description(name: str) -> str:
    return (
        f"{name}. A domain model developed automatically by the Agon: each state "
        "is a round of the Endoporeutic Game (produce → test → negotiate → inject "
        "→ decay), enacted by src/agon_evolution.py over a closed membrane. The "
        "engine of change is the game's disposition taxonomy, not deterministic "
        "rules; selection from outside is the only bound on the unbounded sheet. "
        "See docs/AUTOMATED_MODEL_DEVELOPMENT.md. M carries its own diachronic "
        "history; every state is low warrant until tested."
    )


__all__ = [
    "peel", "Proposer", "CorpusProposer", "MutationProposer",
    "DeliberationContext", "Vote", "PolicyAgent",
    "ObserverAgent", "GeneralizerAgent", "ChallengerAgent", "ContradictionAgent",
    "Agonothetes", "DEFAULT_PANEL", "UsageLedger",
    "RoundOutcome", "Discovery", "EvolutionResult", "run",
]
