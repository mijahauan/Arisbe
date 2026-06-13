"""
The automated Grapheus — the semantic game played as a move-by-move contest.

Design-of-record: ``docs/AUTOMATED_GRAPHEUS.md``.

``semantic_game.evaluate(G, oracle)`` runs the peel *once* and returns a Kleene
verdict.  This module turns that one-shot evaluation into an interactive
**extensive-form contest**: a human plays the **Graphist** (proposes G, defends it),
and the machine plays the **Grapheus** (the model side — Nature/Falsifier and the
adjudicator of atoms against M).  The key fact (doc §4) is that the contest needs
**no new search**: ``SemanticGame._holds`` already computes every subgame's value, so
a winning strategy is just *minimax over that valued tree*.  This driver is a thin
overlay that (a) tracks the single root-to-leaf play, (b) at each node names the
owner by polarity (doc §2–§3), and (c) lets that owner pick — the machine optimally,
the human by hand.

The play is a **single descending path** (game-theoretic semantics: choosing a
conjunct *commits* the play into it; choosing a witness fixes a line).  At every area:

* **existential phase** — the area's *defender* (Graphist at even depth, Grapheus at
  odd) witnesses each line of identity local to the area, picking the individual that
  **maximises** the area's local value (``_or3``);
* **conjunction phase** — the area's *challenger* (the other player) picks one
  conjunct (an atom, or a nested cut) that **minimises** the area's local value
  (``_and3``).  An atom ends the play (adjudicate against M); a cut descends one
  level, **swapping** Graphist↔Grapheus.

"Defender maximises, challenger minimises the *local* value" is uniform across the
swap: crossing a cut turns the parent's challenger into the interior's defender, and
the goal (maximise the interior's truth) is preserved — which is exactly why a single
value rule (the one ``_holds``/``_matrix`` already fold) drives both players.

The outcome is the root verdict the play realises: a terminal atom at depth *d* with
verdict *v* contributes ``v`` negated *d* times to the sheet.  Under optimal play this
equals ``evaluate(G, oracle).verdict`` (the increment-1 conformance invariant).  Open
world: a frontier the Grapheus owns where M can only return UNKNOWN is declined — the
inning is **independent** (doc §6), the Agonothetes' honest stalemate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from semantic_game import SemanticGame, Verdict3, _not3


# ---------------------------------------------------------------------------
# Players, outcomes, and the pieces of a play
# ---------------------------------------------------------------------------

class Player(Enum):
    GRAPHIST = "graphist"   # Myself / Verifier — the human; proposes and defends G
    GRAPHEUS = "grapheus"   # Nature / Falsifier — the machine; keeper of M


class Outcome(Enum):
    GRAPHIST_WINS = "graphist_wins"   # G holds in M (verdict TRUE)
    GRAPHEUS_WINS = "grapheus_wins"   # G fails in M (verdict FALSE)
    INDEPENDENT = "independent"       # M neither confirms nor denies (verdict UNKNOWN)

    @classmethod
    def of(cls, verdict: Verdict3) -> "Outcome":
        return {
            Verdict3.TRUE: cls.GRAPHIST_WINS,
            Verdict3.FALSE: cls.GRAPHEUS_WINS,
            Verdict3.UNKNOWN: cls.INDEPENDENT,
        }[verdict]


def _defender(depth: int) -> Player:
    """Who defends an area of this depth (even = positive = Graphist)."""
    return Player.GRAPHIST if depth % 2 == 0 else Player.GRAPHEUS


def _challenger(depth: int) -> Player:
    return Player.GRAPHEUS if depth % 2 == 0 else Player.GRAPHIST


# Kleene order for argmax / argmin (FALSE < UNKNOWN < TRUE).
_ORDER = {Verdict3.FALSE: 0, Verdict3.UNKNOWN: 1, Verdict3.TRUE: 2}


@dataclass
class Selective:
    """A line of identity given a value — the owner's existential pick."""
    line: str               # the line token (x, x2, …)
    individual: str         # the chosen M individual's label
    by: Player
    at_polarity: str        # "+" / "−" — polarity of the line's home area


@dataclass
class Choice:
    """A decision at a frontier — what the owner may pick, and (filled once made)
    what they did pick.  ``kind`` is ``"witness"`` (pick an individual for a line) or
    ``"conjunct"`` (pick a subgraph to pursue)."""
    kind: str
    owner: Player
    area_id: ElementID
    depth: int
    polarity: str
    options: List[dict]                     # [{key, label, value}] — value is the local Verdict3
    picked: Optional[str] = None            # the chosen option's key
    forced: bool = False                    # only one (distinctly-valued) option


@dataclass
class Move:
    """A completed decision, for the transcript / record."""
    kind: str
    owner: Player
    area_id: ElementID
    depth: int
    detail: str                             # human-readable ("x := Socrates", "pursue (man x)")


@dataclass
class Play:
    """The contest's primary artifact — the extensive-form play (doc §5).

    A game record (selectives + choices + payoff), distinct from a Dau
    ``TransformationChain``.  ``frontier`` is the next contested choice awaiting the
    human Graphist (``None`` when the contest is over or the machine is to move);
    ``outcome`` / ``verdict`` are set at termination.
    """
    history: List[Move] = field(default_factory=list)
    selectives: List[Selective] = field(default_factory=list)
    bindings: Dict[str, str] = field(default_factory=dict)   # line token → individual label
    transcript: List[str] = field(default_factory=list)
    frontier: Optional[Choice] = None
    verdict: Optional[Verdict3] = None
    outcome: Optional[Outcome] = None
    conceded: bool = False   # the Graphist gave up rather than reaching a terminal

    @property
    def is_over(self) -> bool:
        return self.outcome is not None

    @property
    def summary(self) -> str:
        if not self.is_over:
            return "contest in progress"
        return {
            Outcome.GRAPHIST_WINS: "Graphist wins — G holds in M.",
            Outcome.GRAPHEUS_WINS: "Grapheus wins — G fails in M.",
            Outcome.INDEPENDENT: "Independent — M neither confirms nor denies G.",
        }[self.outcome]


# ---------------------------------------------------------------------------
# The contest
# ---------------------------------------------------------------------------

class GrapheusContest:
    """An interactive semantic-game contest over ``egi`` against M (via ``oracle``).

    The machine plays the Grapheus; ``choose`` applies the human Graphist's pick and
    auto-advances through Grapheus moves and forced choices to the next contested
    frontier (or to termination).  ``autoplay`` plays *both* sides optimally — the
    self-play that reproduces ``evaluate``'s verdict.
    """

    def __init__(
        self,
        egi: RelationalGraphWithCuts,
        oracle,
        *,
        closed: bool = False,
    ):
        self.egi = egi
        # Prime a SemanticGame as the value oracle — evaluate() sets up the per-run
        # caches (_egi, _v_by_id, _gen_name, _edge_ids, _cut_ids, _const_label) that
        # _holds / _atom_verdict reuse for lookahead at arbitrary positions.
        self._sg = SemanticGame(oracle, closed=closed)
        self._root_result = self._sg.evaluate(egi)
        self.oracle = oracle

        self._play = Play()
        # The cursor — a single descending position (no stack: a play never returns).
        self._area: ElementID = egi.sheet
        self._depth: int = 0
        self._beta: Dict[ElementID, ElementID] = {}
        self._pending_generics: List[ElementID] = self._local_generics(egi.sheet, {})
        # Set once a challenger pursues an atom: that atom *is* the play's terminal
        # (game-theoretic semantics — choosing an atom conjunct ends the descent).
        self._terminal_atom: Optional[Tuple[Optional[ElementID], int, Verdict3]] = None

    # -- public ----------------------------------------------------------------

    @property
    def play(self) -> Play:
        """The live extensive-form play (the contest's primary artifact)."""
        return self._play

    def start(self) -> Play:
        """Begin the contest, auto-advancing to the first Graphist decision (or end)."""
        self._advance()
        return self._play

    def autoplay(self) -> Play:
        """Self-play: both sides optimal, straight to termination."""
        self.start()
        while not self._play.is_over:
            frontier = self._play.frontier
            assert frontier is not None, "non-terminal play with no frontier"
            self._apply(frontier, self._optimal(frontier))
            self._advance()
        return self._play

    def legal_choices(self) -> List[Choice]:
        """The choice awaiting the human Graphist (empty if over / machine to move)."""
        f = self._play.frontier
        return [f] if f is not None else []

    def choose(self, option_key: str) -> Play:
        """Apply the human Graphist's pick at the current frontier, then auto-advance."""
        f = self._play.frontier
        if f is None:
            raise ValueError("no contested frontier — the contest is over or not started")
        if f.owner is not Player.GRAPHIST:
            raise ValueError("the current frontier is not the Graphist's to choose")
        if option_key not in {o["key"] for o in f.options}:
            raise ValueError(f"illegal option {option_key!r} at this frontier")
        self._apply(f, option_key)
        self._advance()
        return self._play

    def concede(self) -> Play:
        """The human Graphist concedes — the contest ends in the Grapheus's favour.

        A concession is a *dialogical* termination, not a logical one: it records
        that the Graphist declined to defend G further, so the Grapheus (the model
        side) takes the inning.  The play's ``verdict`` stays ``None`` — no terminal
        atom was reached — but the ``outcome`` is ``GRAPHEUS_WINS`` and ``conceded``
        marks how it ended (distinct from a peeled FALSE).
        """
        if self._play.is_over:
            raise ValueError("the contest is already over")
        self._play.conceded = True
        self._play.outcome = Outcome.GRAPHEUS_WINS
        self._play.frontier = None
        self._play.transcript.append("→ graphist concedes (grapheus_wins)")
        return self._play

    # -- the driver loop -------------------------------------------------------

    def _advance(self) -> None:
        """Play forward until a contested Graphist frontier or termination.

        Auto-plays every Grapheus-owned decision and every *forced* decision (a single
        distinctly-valued option); pauses on a Graphist decision with a real choice.
        """
        while True:
            decision = self._decision_here()
            if decision is None:                       # terminal position reached
                self._terminate()
                return
            forced = self._is_forced(decision)
            if decision.owner is Player.GRAPHEUS or forced:
                decision.forced = forced
                self._apply(decision, self._optimal(decision))
                continue
            # A genuine Graphist choice — surface it and wait.
            self._play.frontier = decision
            return

    def _decision_here(self) -> Optional[Choice]:
        """The decision at the current cursor: witness a pending line, else pick a
        conjunct.  ``None`` when the area is an empty conjunction (terminal)."""
        depth, area = self._depth, self._area
        polarity = "+" if depth % 2 == 0 else "−"

        # A challenger already pursued an atom — that atom is the terminal; the play
        # does not return to re-offer this area's conjuncts.
        if self._terminal_atom is not None:
            return None

        if self._pending_generics:
            g = self._pending_generics[0]
            owner = _defender(depth)
            options = [
                {"key": mvid, "label": self.oracle.individual_label(mvid),
                 "value": self._sg._holds(area, {**self._beta, g: mvid},
                                          depth=depth, transcript=[])[0]}
                for mvid in self.oracle.individuals()
            ]
            # The open-world horizon (mirrors ``_holds`` lines 226–229).  The
            # evaluator's value for this whole existential already folds the
            # unknown-individual horizon; the single concrete play can only realise
            # the best *known* witness (Kleene ``max`` == ``_or3``).  When those
            # disagree — M's value is UNKNOWN but no known individual beats FALSE —
            # the defender cannot win the line concretely, so it **declines**: the
            # inning is independent (doc §6).  In a closed world there is no bump, so
            # ``area_v`` never exceeds the best option and this never fires.
            area_v = self._sg._holds(area, self._beta, depth=depth, transcript=[])[0]
            best = max((o["value"] for o in options),
                       key=lambda v: _ORDER[v], default=Verdict3.FALSE)
            if area_v is Verdict3.UNKNOWN and _ORDER[best] < _ORDER[Verdict3.UNKNOWN]:
                self._terminal_atom = (None, depth, Verdict3.UNKNOWN)
                self._play.transcript.append(
                    f"{'  ' * depth}[{owner.value}] declines — M can't settle this "
                    f"line (open-world horizon)")
                return None
            return Choice(kind="witness", owner=owner, area_id=area, depth=depth,
                          polarity=polarity, options=options)

        conjuncts = self._conjuncts(area, depth)
        if not conjuncts:
            return None                                # empty conjunction → terminal
        owner = _challenger(depth)
        return Choice(kind="conjunct", owner=owner, area_id=area, depth=depth,
                      polarity=polarity, options=conjuncts)

    def _apply(self, decision: Choice, option_key) -> None:
        """Commit ``option_key`` at ``decision`` — bind a line, or pursue a conjunct."""
        decision.picked = option_key
        if decision.kind == "witness":
            g = self._pending_generics.pop(0)
            self._beta[g] = option_key
            token = self._sg._gen_name.get(g, "x")
            label = self.oracle.individual_label(option_key)
            self._play.bindings[token] = label
            self._play.selectives.append(
                Selective(line=token, individual=label, by=decision.owner,
                          at_polarity=decision.polarity))
            self._play.history.append(
                Move(kind="witness", owner=decision.owner, area_id=decision.area_id,
                     depth=decision.depth, detail=f"{token} := {label}"))
            self._play.transcript.append(
                f"{'  ' * decision.depth}[{decision.owner.value}] witnesses {token} := {label}")
            return

        # conjunct
        opt = next(o for o in decision.options if o["key"] == option_key)
        self._play.history.append(
            Move(kind="conjunct", owner=decision.owner, area_id=decision.area_id,
                 depth=decision.depth, detail=f"pursue {opt['label']}"))
        self._play.transcript.append(
            f"{'  ' * decision.depth}[{decision.owner.value}] pursues {opt['label']}")
        if opt["is_cut"]:
            self._area = opt["key"]
            self._depth += 1
            self._pending_generics = self._local_generics(opt["key"], self._beta)
        else:
            # An atom was pursued — the play terminates here; record the deciding atom.
            self._terminal_atom = (opt["key"], decision.depth, opt["value"])

    def _terminate(self) -> None:
        """Set the play's verdict / outcome from the terminal position."""
        atom = getattr(self, "_terminal_atom", None)
        if atom is not None:
            _eid, depth, v = atom
        else:
            # Empty conjunction: the area's local value is TRUE (verum).
            depth, v = self._depth, Verdict3.TRUE
        # The local verdict at depth d contributes to the sheet negated d times.
        root_v = v
        for _ in range(depth):
            root_v = _not3(root_v)
        self._play.verdict = root_v
        self._play.outcome = Outcome.of(root_v)
        self._play.frontier = None
        self._play.transcript.append(
            f"→ {self._play.outcome.value} (verdict {root_v.value})")

    # -- strategy --------------------------------------------------------------

    def _optimal(self, decision: Choice) -> ElementID:
        """The owner's optimal pick: the defender maximises, the challenger minimises
        the option's local value (Kleene order FALSE < UNKNOWN < TRUE)."""
        defender = decision.owner is _defender(decision.depth)
        key = (lambda o: _ORDER[o["value"]])
        chosen = (max if defender else min)(decision.options, key=key)
        return chosen["key"]

    def _is_forced(self, decision: Choice) -> bool:
        """A decision with no real choice — one option, or all options the same value."""
        if len(decision.options) <= 1:
            return True
        return len({o["value"] for o in decision.options}) == 1

    # -- structure helpers (mirror SemanticGame's view of an area) --------------

    def _local_generics(self, area_id: ElementID, beta: Dict) -> List[ElementID]:
        contents = self.egi.area.get(area_id, frozenset())
        return sorted(
            vid for vid in contents
            if vid in self._sg._v_by_id and self._sg._v_by_id[vid].is_generic
            and vid not in beta
        )

    def _conjuncts(self, area_id: ElementID, depth: int) -> List[dict]:
        """The area's matrix conjuncts as choosable options: atoms (adjudicated) and
        nested cuts (value = ¬interior).  ``value`` is each conjunct's local verdict."""
        contents = self.egi.area.get(area_id, frozenset())
        out: List[dict] = []
        for eid in sorted(contents):
            if eid in self._sg._edge_ids:
                out.append({
                    "key": eid, "is_cut": False, "label": self._atom_label(eid),
                    "value": self._sg._atom_verdict(eid, self._beta),
                })
            elif eid in self._sg._cut_ids:
                interior = self._sg._holds(eid, self._beta, depth=depth + 1, transcript=[])[0]
                out.append({
                    "key": eid, "is_cut": True, "label": "a negation (cut)",
                    "value": _not3(interior),
                })
        return out

    def _atom_label(self, eid: ElementID) -> str:
        rel = self.egi.get_relation_name(eid)
        args = ", ".join(self._show(v) for v in self.egi.nu[eid])
        return f"{rel}({args})"

    def _show(self, vid: ElementID) -> str:
        v = self._sg._v_by_id.get(vid)
        if v is not None and not v.is_generic:
            return f'"{v.label}"'
        if vid in self._beta:
            return self.oracle.individual_label(self._beta[vid])
        return self._sg._gen_name.get(vid, "x")


def play(egi: RelationalGraphWithCuts, oracle, *, closed: bool = False) -> Play:
    """Convenience: run a full self-play contest and return the ``Play``."""
    return GrapheusContest(egi, oracle, closed=closed).autoplay()
