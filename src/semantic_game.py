"""
The semantic game — evaluating a graph against a model M, outside-in.

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md`` §6 (the semantic-game seam) and
``docs/ENDOPOREUTIC_GAME_GUIDE.md`` Part II (the inner evaluation game).

Two games hide under "the Endoporeutic Game".  The **transformation game**
(``endoporeutic_game.py``) is proof-theoretic — Dau's six rules manipulate the
graph.  The **semantic game** here is the inner one: given a proposed graph G and a
domain model M, does G *hold* in M?  It reads G **endoporeutically** — from outside
in — and at each negation-free layer asks the domain, through a ``DomainOracle``,
whether the atoms map into M.  This is the seam that makes "test a graph against M"
real, and the place the oracle built in ``domain_oracle.py`` earns its keep.

The evaluation is three-valued, because M may be open-world:

* ``TRUE``    — G holds in M (the Verifier / Proposer wins).
* ``FALSE``   — G fails and M is complete enough to say so (the Skeptic wins).
* ``UNKNOWN`` — M neither confirms nor denies (the open-world horizon; the
  stalemate/independence case the guide makes first-class).

Whether a miss is ``FALSE`` or ``UNKNOWN`` is governed by the oracle's **closed**
flag (asserted-complete → negation-as-failure → ``FALSE``; sampled → ``UNKNOWN``).

The logic is **Kleene three-valued** evaluation read as a game — the sound,
tractable reading of open-world satisfaction.  A subgraph is a conjunction of its
atoms and the *negations* of its nested cuts; a line of identity defined in an area
is an existential the area's owner (Verifier on even depth, Falsifier on odd) gets to
witness.  Two open-world facts:

* An **absent atom** is ``UNKNOWN`` (open) — a larger M might assert it — not
  ``FALSE``.  Negation of an absent atom is therefore also ``UNKNOWN``; negation of a
  *present* atom is a definite ``FALSE`` (M only grows, so a present fact stays).
* An **existential** that no known individual satisfies is ``UNKNOWN`` (open) — a
  larger M might supply the witness.  This lift happens **only** at a line of
  identity (a real ∃), never on a ground formula, so a true ground implication like
  ``~[ (man "S") ~[ (mortal "S") ] ]`` with both facts present reads ``TRUE`` even
  open-world (man(S) and mortal(S) both hold, so man→mortal does too).

Kleene-TRUE / Kleene-FALSE are sound for supervaluation (true / false in *every*
completion of M); the residue is honestly ``UNKNOWN``.

Witnesses for the lines of identity range over ``oracle.individuals`` (small for a
corpus M), capped by ``MAX_BINDINGS``; on overflow the area returns ``UNKNOWN`` with
a transcript note rather than a silently-truncated verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import product
from typing import Dict, List, Optional, Tuple

from domain_oracle import DomainOracle
from egi_core_dau import ElementID, RelationalGraphWithCuts


MAX_BINDINGS = 5000   # backstop on the witness cartesian product (no silent cap)


# ---------------------------------------------------------------------------
# Three-valued (Kleene) logic
# ---------------------------------------------------------------------------

class Verdict3(Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


def _not3(v: Verdict3) -> Verdict3:
    if v is Verdict3.TRUE:
        return Verdict3.FALSE
    if v is Verdict3.FALSE:
        return Verdict3.TRUE
    return Verdict3.UNKNOWN


def _and3(values: List[Verdict3]) -> Verdict3:
    """FALSE if any FALSE, else UNKNOWN if any UNKNOWN, else TRUE."""
    if any(v is Verdict3.FALSE for v in values):
        return Verdict3.FALSE
    if any(v is Verdict3.UNKNOWN for v in values):
        return Verdict3.UNKNOWN
    return Verdict3.TRUE


def _or3(values: List[Verdict3]) -> Verdict3:
    """TRUE if any TRUE, else UNKNOWN if any UNKNOWN, else FALSE."""
    if any(v is Verdict3.TRUE for v in values):
        return Verdict3.TRUE
    if any(v is Verdict3.UNKNOWN for v in values):
        return Verdict3.UNKNOWN
    return Verdict3.FALSE


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class SemanticResult:
    """The outcome of evaluating G against M, with a legible outside-in transcript.

    ``winning_witness`` (present on a TRUE existential) names the assignment of
    lines of identity that made G hold; ``counterexample`` (present on a FALSE
    universal) names the individual that defeated it — the evidence the
    Agonothetes' decision rests on (the physician's Biscuit, the student's Whale).
    Each maps a line token (``x``, ``x2``, …) to an M individual's label.

    ``witness_vertex_ids`` maps the *same* line tokens to the **G vertex id** of
    the generic line they name — so a viewer can highlight the deciding line of
    identity *on the drawing of G* (the token→individual binding says who; this
    says where). Present whenever a decisive witness/counterexample is.
    """

    verdict: Verdict3
    transcript: List[str] = field(default_factory=list)
    winning_witness: Optional[Dict[str, str]] = None
    counterexample: Optional[Dict[str, str]] = None
    witness_vertex_ids: Optional[Dict[str, str]] = None

    @property
    def holds(self) -> bool:
        """True only when M *confirms* G (UNKNOWN and FALSE are not holds)."""
        return self.verdict is Verdict3.TRUE

    @property
    def summary(self) -> str:
        return {
            Verdict3.TRUE: "G holds in M (the Proposer wins).",
            Verdict3.FALSE: "G does not hold in M (the Skeptic wins).",
            Verdict3.UNKNOWN: "M neither confirms nor denies G (independent / open world).",
        }[self.verdict]


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------

class SemanticGame:
    """Evaluate an EGI against a model M reached through a ``DomainOracle``."""

    def __init__(self, oracle: DomainOracle, *, closed: bool = False):
        self.oracle = oracle
        # ``closed`` may be set explicitly or carried by the oracle.
        self.closed = bool(getattr(oracle, "_closed", False) or closed)

    # -- public ----------------------------------------------------------------

    def evaluate(self, egi: RelationalGraphWithCuts) -> SemanticResult:
        """Does ``egi`` (read on the sheet of assertion) hold in M?"""
        self._egi = egi
        self._v_by_id = {v.id: v for v in egi.V}
        self._const_label = {
            v.id: v.label for v in egi.V if not v.is_generic and v.label is not None
        }
        self._edge_ids = {e.id for e in egi.E}
        self._cut_ids = {c.id for c in egi.Cut}
        # Stable readable names for the generic lines of identity (x, x2, …).
        generics = sorted(v.id for v in egi.V if v.is_generic)
        self._gen_name = {
            vid: ("x" if len(generics) == 1 else f"x{i + 1}")
            for i, vid in enumerate(generics)
        }
        transcript: List[str] = []
        verdict, binding = self._holds(egi.sheet, {}, depth=0, transcript=transcript)
        decisive = self._render_binding(binding) if binding else None
        # The same decisive lines, keyed token→G vertex id, so the drawing of G
        # can be highlighted at the line that decided the verdict.
        decisive_ids = (
            {self._gen_name[vid]: vid for vid in binding if vid in self._gen_name}
            if binding else None
        ) or None
        return SemanticResult(
            verdict=verdict,
            transcript=transcript,
            winning_witness=decisive if verdict is Verdict3.TRUE else None,
            counterexample=decisive if verdict is Verdict3.FALSE else None,
            witness_vertex_ids=decisive_ids if verdict is not Verdict3.UNKNOWN else None,
        )

    def _render_binding(self, binding) -> Optional[Dict[str, str]]:
        """A decisive generic binding ({vid: mvid}) as {line token: individual}."""
        out = {
            self._gen_name.get(vid, "x"): self.oracle.individual_label(mvid)
            for vid, mvid in binding.items()
            if vid in self._gen_name
        }
        return out or None

    # -- recursion -------------------------------------------------------------

    def _holds(self, area_id, beta, *, depth, transcript):
        """Does the subgraph rooted at ``area_id`` hold in M under binding ``beta``?

        Returns ``(verdict, decisive_binding)`` where ``decisive_binding`` is the
        generic line assignment ({vid: mvid}) that determined the result — the
        witness on TRUE, the defeating individual on FALSE — or ``None``.

        The existential layer: witness this area's own lines of identity, then
        evaluate the matrix (atoms ∧ ¬cuts) under each witnessing.  ``beta`` maps
        already-fixed egi vertex ids to M vertex ids; ``depth`` parity is polarity
        (even = Verifier, odd = Falsifier), used for the transcript.
        """
        contents = self._egi.area.get(area_id, frozenset())
        local_generics = [
            vid for vid in contents
            if vid in self._v_by_id and self._v_by_id[vid].is_generic
            and vid not in beta
        ]
        pol = "verifier" if depth % 2 == 0 else "falsifier"

        if not local_generics:
            v, w = self._matrix(area_id, beta, depth=depth, transcript=transcript)
            self._note(transcript, depth, pol, area_id, beta, v)
            return v, w

        domain = self.oracle.individuals()
        if max(1, len(domain)) ** len(local_generics) > MAX_BINDINGS:
            transcript.append(
                f"{'  ' * depth}[{pol}] too many witness combinations — UNKNOWN")
            return Verdict3.UNKNOWN, None

        disjuncts: List[Verdict3] = []
        for combo in product(domain, repeat=len(local_generics)):
            b2 = dict(beta)
            b2.update(dict(zip(local_generics, combo)))
            mv, mw = self._matrix(area_id, b2, depth=depth, transcript=transcript)
            if mv is Verdict3.TRUE:
                # A winning witness: this layer's picks plus any from deeper.
                witness = {g: b2[g] for g in local_generics}
                witness.update(mw or {})
                self._note(transcript, depth, pol, area_id, beta, mv)
                return Verdict3.TRUE, witness
            disjuncts.append(mv)

        v = _or3(disjuncts)
        # Open world: an unsatisfied existential might be satisfied by a larger M.
        if v is not Verdict3.TRUE and not self.closed:
            v = Verdict3.UNKNOWN
        self._note(transcript, depth, pol, area_id, beta, v)
        return v, None

    def _matrix(self, area_id, beta, *, depth, transcript):
        """The conjunction at this area under a fully-witnessed ``beta``: every atom
        holds and every nested cut's interior does *not* hold.

        Returns ``(verdict, decisive_binding)``.  When the matrix is FALSE because a
        nested cut's interior *holds* (so its negation fails), that interior's
        witness is the counterexample — the individual that defeats the claim.
        """
        contents = self._egi.area.get(area_id, frozenset())
        atom_verdicts: List[Verdict3] = []
        for eid in contents:
            if eid in self._edge_ids:
                atom_verdicts.append(self._atom_verdict(eid, beta))
        # (negated interior verdict, the interior's own verdict, its witness)
        cut_parts: List[Tuple[Verdict3, Verdict3, Optional[dict]]] = []
        for cid in contents:
            if cid in self._cut_ids:
                cv, cw = self._holds(cid, beta, depth=depth + 1, transcript=transcript)
                cut_parts.append((_not3(cv), cv, cw))

        parts = atom_verdicts + [neg for neg, _cv, _cw in cut_parts]
        v = _and3(parts) if parts else Verdict3.TRUE

        if v is Verdict3.FALSE:
            # Prefer a counterexample: a cut whose interior holds (its negation
            # is what made the conjunction false) carries the defeating witness.
            for neg, cv, cw in cut_parts:
                if cv is Verdict3.TRUE:
                    return Verdict3.FALSE, cw
        return v, None

    def _atom_verdict(self, edge_id, beta) -> Verdict3:
        """A ground atom's verdict: TRUE if M asserts it; else FALSE (closed) /
        UNKNOWN (open)."""
        rel = self._egi.get_relation_name(edge_id)
        verts = tuple(self._egi.nu[edge_id])
        present = bool(self.oracle.match_atoms(
            [(rel, verts)], bound=beta, constants=self._const_label))
        if present:
            return Verdict3.TRUE
        return Verdict3.FALSE if self.closed else Verdict3.UNKNOWN

    # -- transcript ------------------------------------------------------------

    def _note(self, transcript, depth, pol, area_id, beta, verdict):
        where = "sheet" if area_id == self._egi.sheet else f"cut {area_id}"
        contents = self._egi.area.get(area_id, frozenset())
        atom_str = ", ".join(
            f"{self._egi.get_relation_name(eid)}("
            f"{', '.join(self._show(v, beta) for v in self._egi.nu[eid])})"
            for eid in contents if eid in self._edge_ids
        ) or "—"
        wit = ""
        picks = {
            self._show(vid, beta): self.oracle.individual_label(mvid)
            for vid, mvid in beta.items()
            if vid in self._v_by_id and self._v_by_id[vid].is_generic
        }
        if picks:
            wit = "  witnesses: " + ", ".join(f"{k}={v}" for k, v in picks.items())
        transcript.append(
            f"{'  ' * depth}[{pol}] {where}: {atom_str} → {verdict.value}{wit}")

    def _show(self, vid, beta) -> str:
        v = self._v_by_id.get(vid)
        if v is not None and not v.is_generic:
            return f'"{v.label}"'
        if vid in beta:
            return f"·{self.oracle.individual_label(beta[vid])}"
        return "x"


def evaluate(
    egi: RelationalGraphWithCuts,
    oracle: DomainOracle,
    *,
    closed: bool = False,
) -> SemanticResult:
    """Convenience: evaluate ``egi`` against M (via ``oracle``)."""
    return SemanticGame(oracle, closed=closed).evaluate(egi)
