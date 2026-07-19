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

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set, Tuple, Union

from egif_parser_dau import parse_egif
from egif_generator_dau import generate_egif
from egi_core_dau import RelationalGraphWithCuts
from eg_navigation import area_of, child_cuts, same_graph
from domain_oracle import CorpusOracle
from semantic_game import Verdict3, evaluate, SemanticResult
from model_materialization import IncrementalMaterializer, materialize_egi
from model_revision import (
    DISPOSITION_NEW_FACT,
    DISPOSITION_GENERALIZATION,
    DISPOSITION_CHALLENGE_M,
    DISPOSITION_RETRACT,
    revise_with_disposition,
    revise_with_disposition_recorded,
    revision_taxonomy,
)
from proof_authoring import ProofChain
from universe_of_discourse import UniverseOfDiscourse, UoDCategory
from world_scroll import find_world_scroll, m_view


# --------------------------------------------------------------------------- #
# ② Test — peel G against M (closed-world, laws forward-chained first)         #
# --------------------------------------------------------------------------- #

def peel(
    model: RelationalGraphWithCuts, proposal_egif: str, *, closed: bool = True,
    materializer: Optional[IncrementalMaterializer] = None,
) -> SemanticResult:
    """Peel a proposal G against a model state, materializing M's Horn fragment
    first so any admitted *law* covers new individuals (mirrors the swan
    exemplar's ``_verdict``). M is the truth-teller — this is mechanical, not an
    opinion. ``materializer`` (optional) is a shared
    :class:`model_materialization.IncrementalMaterializer` — a caller peeling the
    same growing M round after round (the run loop) avoids re-materializing it
    from scratch each time (the F2⁗ semi-naive rider); the closure is identical."""
    if materializer is not None:
        facts, _ = materializer.materialize(model)
    else:
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
    """Relation names occurring as *standing* facts of M (the decayable units) —
    read through ``m_view``, so a resident M's cell atoms count (identity on a
    bare sheet-level graph)."""
    model = m_view(model)
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
    """Every atom of a ground proposal is already a standing fact of M (with the
    same relation + constant arguments) — M read through ``m_view``."""
    model = m_view(model)
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
# Atom keys — the identity of one habit (the atom-level decay rulebook,        #
# affirmed 2026-07-03: the habit is the fact, not the name)                    #
# --------------------------------------------------------------------------- #

def atom_key(relation: str, labels: Sequence[Optional[str]]) -> str:
    """The serialized identity of one sheet atom — relation name + argument labels.
    This is the unit the :class:`UsageLedger` tracks and disuse-decay erases:
    ``(place_of_birth Adam Cambridge)`` is the habit; ``place_of_birth`` is only
    vocabulary. JSON-encoded so it survives a runner-state round trip verbatim."""
    return json.dumps([relation, list(labels)], ensure_ascii=False,
                      separators=(",", ":"))


def parse_atom_key(key: str) -> Tuple[str, List[Optional[str]]]:
    """Inverse of :func:`atom_key` — ``(relation, labels)``."""
    relation, labels = json.loads(key)
    return relation, labels


def sheet_atom_keys(egi: RelationalGraphWithCuts) -> Set[str]:
    """The atom keys of every **standing** fact of M — the decayable units,
    read through ``m_view`` (a resident M's cell atoms are its standing facts;
    identity on a bare sheet-level graph, so a *proposal* parse is unaffected).
    Content inside a law/denial cut is not a standing habit."""
    egi = m_view(egi)
    return {
        atom_key(egi.rel[e.id], _labels(egi, e.id))
        for e in egi.E
        if e.id in egi.rel and area_of(egi, e.id) == egi.sheet
    }


def delivered_atom_keys(egif: str) -> Set[str]:
    """**Use = re-delivery** (the rulebook's first increment): the sheet-level atoms
    a proposal delivers, whether or not the round revises M — a redundant
    re-delivery refreshes the habit. A denial or a law delivers no standing atom,
    so it refreshes nothing (whether *inference*-use refreshes a habit is a later
    §6 question, deliberately not taken here)."""
    return sheet_atom_keys(parse_egif(egif))


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
        model = m_view(ctx.model)          # a resident M's standing facts
        standing = {
            (model.rel[x.id], tuple(_labels(model, x.id)))
            for x in model.E
            if area_of(model, x.id) == model.sheet and x.id in model.rel
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
    """The first standing law ``~[ (B x⃗) ~[ (H y⃗) ] ]`` this proposal *refutes*,
    or ``None``. A Horn law is self-fulfilling under materialization (asserting
    ``B(c⃗)`` merely derives ``H(…)``), so the only thing that refutes it is a
    **counterexample carrying the negation of the head** — ``(B c⃗) ~[ (H d⃗) ]``
    where ``d⃗`` is the head's projection of ``c⃗``. Recognised structurally, at
    **any arity** (generalized 2026-07-06 for the resolving membrane's laws, e.g.
    ``~[ (forecast_temp_band *s *t *b) ~[ (temp_band s t b) ] ]`` — the original
    matcher was unary, the swan shape): the head's argument positions within the
    body's argument tuple come from :func:`_law_signature`, so a permuted or
    projected head is matched faithfully, never guessed."""
    g = parse_egif(ctx.proposal_egif)
    pos = _positive_atoms(g)
    neg = _negated_atoms(g)
    if not neg:
        return None
    for law in ctx.known_laws:
        sig = _law_signature(law)
        if sig is None:
            continue
        body, head, positions = sig
        for rel, labels in pos:
            if rel != body or (positions and len(labels) <= max(positions)):
                continue
            head_labels = tuple(labels[j] for j in positions)
            if (head, head_labels) in neg:
                return law
    return None


def _law_signature(law_egif: str) -> Optional[Tuple[str, str, Tuple[int, ...]]]:
    """``(body_relation, head_relation, head_arg_positions)`` for a Horn scroll
    ``~[ (B x⃗) ~[ (H y⃗) ] ]`` where every head argument is a body argument
    (range-restricted). ``head_arg_positions[i]`` is the index in the body's
    argument tuple of the head's i-th argument — the projection a counterexample
    check must apply. ``None`` for any other shape (conservative: no match, no
    relinquishment on a shape we did not understand)."""
    g = parse_egif(law_egif)
    for outer in child_cuts(g, g.sheet):
        inner = child_cuts(g, outer)
        if not inner:
            continue
        body_e = next((e for e in g.E
                       if area_of(g, e.id) == outer and e.id in g.rel), None)
        head_e = next((e for e in g.E
                       if area_of(g, e.id) == inner[0] and e.id in g.rel), None)
        if body_e is None or head_e is None:
            continue
        body_args = list(g.nu.get(body_e.id, ()))
        head_args = list(g.nu.get(head_e.id, ()))
        try:
            positions = tuple(body_args.index(v) for v in head_args)
        except ValueError:
            continue                     # a head variable not bound in the body
        return g.rel[body_e.id], g.rel[head_e.id], positions
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
    """Tracks the round each standing **atom** was last *re-delivered* (keys are
    :func:`atom_key` strings; the class itself is key-agnostic). An atom idle for
    ``ttl`` rounds has fallen from use and is erased (relinquishment by
    attrition). This is the unbounded sheet's substitute for Life's plane edge —
    selection by use, not by a boundary.

    **Atom-level since 2026-07-03** (the rulebook decision RUN_4_LOG affirmed:
    the habit is the fact, not the name — F1″'s warm-name pinning dissolves
    because a warm re-delivery now keeps only the *re-delivered* atoms warm,
    while the name-level ledger let one hot name pin an unbounded atom pile)."""

    def __init__(self, ttl: int):
        self.ttl = ttl
        self._last: Dict[str, int] = {}

    def seed(self, keys: Set[str], round_idx: int = 0) -> None:
        for k in keys:
            self._last.setdefault(k, round_idx)

    def touch(self, keys: Set[str], round_idx: int) -> None:
        for k in keys:
            self._last[k] = round_idx

    def stale(self, round_idx: int) -> List[str]:
        return sorted(
            k for k, last in self._last.items() if round_idx - last >= self.ttl
        )

    def forget(self, key: str) -> None:
        self._last.pop(key, None)

    def snapshot(self) -> Dict[str, int]:
        """The ledger's state (atom key → last-delivered round) for a runner checkpoint."""
        return dict(self._last)

    def restore(self, last: Dict[str, int]) -> None:
        """Restore a :meth:`snapshot` — a resumed run's decay clock continues, not resets."""
        self._last = dict(last)


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
    decayed: List[str]              # atom keys erased by disuse this round (atom_key strings)
    standing_verdict: Optional[str] # the audited proposal's verdict after the round
    changed: bool
    branched: List[str] = field(default_factory=list)  # dispositions forked as DAG siblings
    decay_skipped: List[Tuple[str, str]] = field(default_factory=list)
    """``(atom_key, reason)`` for each decay the licensed ERA refused. The atom
    stands; nothing erases it unlicensed. Counted so a refusal is never silent."""


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
    model_egif: Union[str, RelationalGraphWithCuts],
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
    materializer: Optional[IncrementalMaterializer] = None,
) -> EvolutionResult:
    """Play ``rounds`` automated game rounds, developing M from ``model_egif``
    — given either as EGIF text or as a graph. A caller carrying M *between*
    runs (the ``LiveRunner``'s segments) must pass the graph: EGIF cannot
    express per-cell vertex privacy or the second-order sort, so a text carry
    silently merges a constant shared across sibling cells.

    The structural guarantee is on the **resident** carry. A graph seed that is
    *not* already resident in the standing world-scroll is housed below by a
    text round-trip (``generate_egif`` → ``INS`` of one cell), so at that one
    point a non-resident quotation-bearing seed raises the named limit
    (``SecondOrderNotInLinearForm``) and a non-resident seed's cross-cell shared
    constants merge. Once housed, every later carry is structural.

    Returns the trajectory as a ``TransformationChain`` + a ``DOMAIN_MODEL`` UoD
    (ready for ``TomosService.save_uod_with_chain``), the per-round outcomes, and
    a discovery digest. Deterministic given a deterministic proposer.

    ``ttl`` (optional) turns on **atom-level** disuse-decay (use = re-delivery;
    an atom idle ``ttl`` rounds is retracted by ``retract_atom``);
    ``standing_proposal`` (optional, EGIF) is audited after each round so a
    verdict flip caused by growth or decay is *surfaced*, never silent.
    ``seed_laws`` (optional, EGIF) are standing laws M already carries on its
    sheet (e.g. from the corpus) that were *not* derived in a round — seeding
    them lets the Challenger recognise a later refutation of them (the
    raise-and-resolve membrane relies on this). ``materializer`` (optional) is a
    shared :class:`IncrementalMaterializer` a caller (the ``LiveRunner``) keeps
    across segments; by default each run gets its own, so the per-round peel
    extends the previous round's closure instead of rebuilding it (F2⁗).
    """
    panel = panel or Agonothetes()
    # Ensure-residence (sweep #2): the loop plays over M resident in the
    # standing world-scroll. A bare sheet-level seed is housed by two genuine
    # recorded rule steps — DC+ opens the residence (the empty double cut
    # asserts nothing) and INS supplies the seed as one closed cell — so the
    # chain is rule-licensed from its first move (no post-hoc adapter). An
    # already-resident seed (a later segment's carry) continues as-is.
    seed = parse_egif(model_egif) if isinstance(model_egif, str) else model_egif
    if find_world_scroll(seed) is None:
        seed_egif = generate_egif(seed) if not isinstance(model_egif, str) else model_egif
        pc = ProofChain.from_blank()
        pc.apply("DC+", into=lambda g: g.sheet,
                 note="Open the standing residence: an empty double cut "
                      "asserts nothing, and until it exists there is nowhere "
                      "to hold a model that is not an assertion at the "
                      "world's level.")
        if seed_egif.strip():
            pc.apply("INS", insert=f"~[ {seed_egif} ]",
                     into=lambda g: child_cuts(g, g.sheet)[0],
                     note="Supply the seed M as one closed cell — insertion "
                          "is sound in the negative arena, and the content "
                          "lands at even depth where retraction is a "
                          "licensed ERA.")
            # the supply is the initial admission — acknowledged as an act so
            # the gate's m_view tripwire never reads it as a silent M-change
            pc.to_chain().steps[-1].parameters.update(
                {"act": "m_enlargement", "earned": True, "derivation": ["INS"]})
    else:
        pc = ProofChain(seed)
    mat = materializer if materializer is not None else IncrementalMaterializer()
    ledger: Optional[UsageLedger] = None
    if ttl:
        ledger = UsageLedger(ttl)
        ledger.seed(sheet_atom_keys(pc.current))

    outcomes: List[RoundOutcome] = []
    known_laws: List[str] = list(seed_laws or [])

    for r in range(1, rounds + 1):
        model = pc.current
        pre_id = pc.current_state_id            # the pre-round state a sibling forks from
        g_egif = proposer.propose(model, r)
        if g_egif is None:
            break   # the membrane is exhausted

        result = peel(model, g_egif, materializer=mat)
        ctx = DeliberationContext(model, g_egif, result, list(known_laws), round_idx=r)
        votes = panel.deliberate(ctx)
        winner = panel.resolve(votes)
        slate = [(v.agent, v.disposition) for v in votes]

        # ⑤a — use = re-delivery (the atom-level rulebook): every delivered standing
        # atom refreshes its habit, whether or not the round revises M (a redundant
        # warm re-delivery is exactly the habit holding).
        if ledger is not None:
            ledger.touch(delivered_atom_keys(g_egif), r)

        if winner is None:
            decayed, skipped = (_apply_decay(pc, ledger, r)
                                if ledger is not None else ([], []))
            outcomes.append(RoundOutcome(
                r, g_egif, result.verdict.value, None, None,
                "no agent moved — recorded judgment, M untouched.",
                slate, decayed,
                _verdict_or_none(pc.current, standing_proposal, mat), bool(decayed),
                decay_skipped=skipped,
            ))
            continue

        spec = revision_taxonomy(winner.disposition)
        # Dry-run against the pre-step state to learn the executed licensed
        # derivation (deterministic: apply_derived runs the same dispatch on
        # the same graph), so the step's params carry act + derivation and
        # the polarity gate can hold the loop's chains to the same standard
        # as the hand-built corpus.
        _, derivation = revise_with_disposition_recorded(
            pc.current, winner.disposition, **winner.kwargs)
        pc.apply_derived(
            "REVISE_M",
            lambda g, w=winner: revise_with_disposition(g, w.disposition, **w.kwargs),
            label=f"{r}·M", note=winner.rationale,
            params={"disposition": winner.disposition, "mode": spec["mode"],
                    "proposal": g_egif, "act": _act_for(winner.disposition),
                    "derivation": derivation, "earned": True, **winner.kwargs},
        )
        _update_known_laws(known_laws, winner)

        decayed, skipped = (_apply_decay(pc, ledger, r)
                            if ledger is not None else ([], []))

        # ⑤b — irreducible disagreement: fork the DAG (Stage 3). A judge (e.g. the LLM
        # Agonothetes) may name dissenting votes to carry forward as siblings; each is applied
        # from the *pre-round* state as an alternate reading, then the main line resumes.
        # Selection decides later; no agent must be right in the moment. (§5 of the design.)
        branched = _fork_siblings(pc, panel, votes, winner, pre_id, r)

        outcomes.append(RoundOutcome(
            r, g_egif, result.verdict.value, winner.disposition, spec["mode"],
            winner.rationale, slate, decayed,
            _verdict_or_none(pc.current, standing_proposal, mat), True, branched,
            decay_skipped=skipped,
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


def _act_for(disposition: str) -> str:
    """The recorded act a disposition performs on the residence: enlargements
    read ``m_enlargement``, a pure retraction ``m_retraction``, the challenge
    composite ``m_revision`` — the same vocabulary as ``m_steps``."""
    if disposition == DISPOSITION_CHALLENGE_M:
        return "m_revision"
    if disposition == DISPOSITION_RETRACT:
        return "m_retraction"
    return "m_enlargement"


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
            pc.at(pre_id)
            _, derivation = revise_with_disposition_recorded(
                pc.current, bv.disposition, **bv.kwargs)
            pc.apply_derived(
                "REVISE_M(sibling)",
                lambda g, w=bv: revise_with_disposition(g, w.disposition, **w.kwargs),
                label=f"{round_idx}·M~", note=f"dissenting reading (irreducible disagreement): "
                                              f"{bv.rationale}",
                params={"disposition": bv.disposition, "mode": spec["mode"],
                        "sibling": True, "act": _act_for(bv.disposition),
                        "derivation": derivation, "earned": True, **bv.kwargs},
                # Label the sibling line by its disposition so the history
                # navigation names it (the ⑂ strip / DAG legend) instead of a
                # bare "branch N".
                branch=bv.disposition,
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


def _apply_decay(
    pc: ProofChain, ledger: UsageLedger, round_idx: int
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """⑤b — erase each standing **atom** idle past ttl (atom-level decay: the habit
    is the fact, not the name). Under the residence the fading of a habit through
    disuse is a **licensed ERA at even depth** — the same move as refutation-driven
    retraction, distinguished by the recorded disposition/flavor (§9.7: the *faded*
    tense; D6: ``pruned:disuse``) — dispatched through the residence-aware
    ``revise_with_disposition``, which preserves every other atom of the name and
    any standing law cut. An atom already gone — retracted by a game move — is
    simply forgotten.

    Returns ``(decayed_keys, skipped)``. A retraction the licensed rule
    **refuses** is skipped and counted, never performed by structural surgery:
    no Dau rule licenses erasing M's ink by hand, and a fallback that matched
    by relation + labels over the whole graph reached into denial cells and
    episode exhibits. The refusal is reachable only on a legacy EGIF carry,
    whose text round-trip merges a constant shared across sibling cells and so
    orphans a vertex in a cell its atom no longer sits in. The skipped atom is
    forgotten rather than retried, so one refusal is counted once and does not
    accumulate a per-round refusal every round thereafter."""
    stale = ledger.stale(round_idx)
    if not stale:
        return [], []
    decayed: List[str] = []
    skipped: List[Tuple[str, str]] = []
    standing = sheet_atom_keys(pc.current)
    for key in stale:
        if key not in standing:
            ledger.forget(key)
            continue
        rel, labels = parse_atom_key(key)
        try:
            _, derivation = revise_with_disposition_recorded(
                pc.current, DISPOSITION_RETRACT, relation=rel, labels=list(labels))
        except (AssertionError, ValueError) as exc:
            skipped.append((key, str(exc)))
            ledger.forget(key)
            continue                        # the atom stands; the skip is recorded
        pc.apply_derived(
            "DECAY",
            lambda g, _r=rel, _l=labels: revise_with_disposition(
                g, DISPOSITION_RETRACT, relation=_r, labels=list(_l)),
            label=f"{round_idx}·decay",
            note=f"({rel} {' '.join(repr(l) for l in labels)}) fell from use — "
                 f"erased (disuse-decay).",
            params={"disposition": "retract_fact", "mode": "none",
                    "act": "m_retraction", "derivation": derivation,
                    "flavor": "pruned:disuse", "earned": True,
                    "relation": rel, "labels": list(labels)},
        )
        decayed.append(key)
        ledger.forget(key)
    return decayed, skipped


def _verdict_or_none(
    model: RelationalGraphWithCuts, proposal: Optional[str],
    materializer: Optional[IncrementalMaterializer] = None,
) -> Optional[str]:
    if not proposal:
        return None
    return peel(model, proposal, materializer=materializer).verdict.value


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
    "atom_key", "parse_atom_key", "sheet_atom_keys", "delivered_atom_keys",
    "RoundOutcome", "Discovery", "EvolutionResult", "run",
]
