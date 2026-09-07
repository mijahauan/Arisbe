"""
Endoporeutic Game Engine  (Dau Chapter 21 / Peirce)

The EPG is a specific **method of interpretation**, not a proof procedure. The
Graphist presents a whole proposed graph to the Grapheus for testing; the graph
is decomposed sub-graph by sub-graph, and each piece is put to a reference
domain model with one question — does this map, or could it be implied by or be
consistent with, what the model already holds? Where a piece maps, IT- applies:
the content is already accounted for. When IT- has applied to every considered
sub-graph the Graphist wins; if any sub-graph fails to map the Grapheus wins.

Like every graph transformation in Arisbe the method follows Dau's calculus,
but it uses only the eliminative part of it.

Players
-------
PROPOSER (Graphist)  Defends the proposal.  Moves in NEGATIVE (odd-depth) areas.
SKEPTIC  (Grapheus)  Challenges it.         Moves in POSITIVE (even-depth) areas.

Both play the same three rules: **IT-**, **INS** (only of a negation around a
negation), and **DC-**.

The game is scribed inside a **negative context**: the Graphist claims, in
effect, that if the domain model holds then the proposed graph is true, and an
implication is scribed in a negative area where one may scribe anything. That
is why INS is available throughout, and why ERA — licensed only in positive
areas — never appears in this game.

Play runs as peeling an onion, or pulling branches, twigs and leaves back to
the root. The exposed, unenclosed pieces are put to the domain model; those
that map are already accounted for and deiterate away by IT-. A player then
takes a remaining section that sits inside a cut and, since that cut already
sits in a negative area, scribes a doubly-negated copy beside it (INS) and
collapses it (DC-), exposing the interior. That is the player proposing the
opposite of what was scribed, and taking up the Graphist's part for the
sub-graph so exposed. At each crossing of a cut the roles switch.

If a counter-proposal maps in the domain model, the original Graphist loses.
If the entire graph is traversed without that happening, the Graphist wins.

The constructive rules — IT+, DC+ — are deliberately absent. They build,
and building belongs to Ergasterion, where an individual constructs, proves,
practises, speculates, imagines, replays with variations and adjusts the style.
When something there looks like a candidate worth testing, a Graphist carries
it to Agon and subjects it to this method.

Peeling a negative
------------------
Peeling is the **traversal**, not a move: descending into a cut is logically
equivalent to the Grapheus proposing the opposite of what the Graphist
proposed, so the players exchange roles and the method recurses on the
interior. No ink changes on the descent. Territory therefore follows from
depth rather than standing as a separate rule, and the recursion continues
until the whole tree of the graph has been traversed.

Turn structure
--------------
Players alternate.  A turn consists of exactly one rule application.
A player who cannot make any legal move in their territory loses.
Either player may concede at any time.

Win conditions
--------------
- A player concedes                    → opponent wins
- A player has no legal moves          → that player loses
- Goal EGI appears in current state    → Proposer wins
  (goal is optional; if absent the game continues until concede / no moves)

The second of those was unreachable while DC+ was available in every area, and
is reachable now: it is the ending in which the graph cannot be reduced
further. What a win or a loss then *means* for the domain model is a separate
question, and the Agonothetes sorts it (see web_api/services/agonothetes.py).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egi_transformation_history import EGITransformationHistory
from frozendict import frozendict
from rule_interaction import insert_from_egif

from formal_transformation_rules import (
    AreaPolarity,
    DeiterationRule,
    DoubleCutErasureRule,
    DoubleCutInsertionRule,
    ErasureRule,
    InsertionRule,
    IterationRule,
    TransformationContext,
    TransformationResult,
)
from graph_isomorphism_engine import GraphIsomorphismEngine


# ---------------------------------------------------------------------------
# Enumerations and lightweight descriptors
# ---------------------------------------------------------------------------

class Player(Enum):
    PROPOSER = "Proposer"
    SKEPTIC = "Skeptic"

    def opponent(self) -> "Player":
        return Player.SKEPTIC if self is Player.PROPOSER else Player.PROPOSER


class GameOutcome(Enum):
    ONGOING = "ongoing"
    PROPOSER_WINS = "proposer_wins"
    SKEPTIC_WINS = "skeptic_wins"
    DRAW = "draw"


@dataclass(frozen=True)
class MoveDescription:
    """Human-readable description of a legal move."""
    rule_name: str
    area_id: ElementID
    area_polarity: AreaPolarity
    nesting_depth: int
    hint: str  # one-line natural language description


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------

@dataclass
class GameState:
    """Complete, mutable state of one game."""

    initial_egi: RelationalGraphWithCuts
    current_egi: RelationalGraphWithCuts
    current_player: Player
    move_number: int
    history: EGITransformationHistory
    outcome: GameOutcome
    outcome_reason: str

    # Optional goal graph.  When set, Proposer wins if the goal appears
    # as a subgraph of the positive (sheet-level) area of current_egi.
    # The frame: the cut whose interior holds the Graphist's claim. The EPG
    # always happens inside a context — nothing is ever scribed at sheet level
    # — so this is established once at new_game and carried, never inferred
    # from the graph as it changes under play.
    frame_cut: Optional[ElementID] = None
    goal_egi: Optional[RelationalGraphWithCuts] = None

    # Human-readable log of completed moves
    move_log: List[str] = field(default_factory=list)

    @property
    def is_over(self) -> bool:
        return self.outcome is not GameOutcome.ONGOING

    @property
    def winner(self) -> Optional[Player]:
        if self.outcome is GameOutcome.PROPOSER_WINS:
            return Player.PROPOSER
        if self.outcome is GameOutcome.SKEPTIC_WINS:
            return Player.SKEPTIC
        return None


# ---------------------------------------------------------------------------
# Game engine
# ---------------------------------------------------------------------------

class EndoporeuticGame:
    """
    Manages game flow: move validation, application, and win detection.

    Usage::

        game = EndoporeuticGame()
        state = game.new_game(initial_egif, goal_egif=None)

        # Proposer's first move
        state = game.apply_move(
            state, "INS", "~[(Mortal *x)]", dest_area=inner_cut_id,
            selected_subgraph=frozenset(),
        )

        print(game.status_text(state))
    """

    # The EPG's repertoire. The game is scribed inside a **negative context**:
    # the Graphist claims, in effect, that if the domain model holds then the
    # proposed graph is true, and an implication is scribed in a negative area
    # where one may scribe anything. That is why INS is available throughout.
    #
    #   IT-  the exposed, unenclosed pieces that map to the domain model are
    #        already accounted for, so they deiterate away.
    #   INS  only of a negation around a negation: with the cut already sitting
    #        in a negative area, a doubly-negated copy may be scribed beside it
    #        (one may scribe anything in a negative area), which is the player
    #        proposing the opposite of what was scribed.
    #   DC-  collapses that double negation, exposing the interior — the onion
    #        peeled one layer, the branch pulled to root level.
    #
    # ERA is **not** used. Neither are the constructive rules IT+ and DC+: they
    # build, and building belongs to Ergasterion. A Graphist carries a
    # candidate to Agon only to subject it to this method. Their earlier
    # presence here made the game a proof workshop wearing the EPG's name, and
    # made the "no legal moves" ending unreachable, since DC+ is always
    # available in any area.
    #
    # Both players use the same three. At each crossing of a cut the roles
    # switch: the player who exposes an interior takes up the Graphist's part
    # for that sub-graph.
    _PROPOSER_RULES = {"IT-", "INS", "DC-"}
    _SKEPTIC_RULES  = {"IT-", "INS", "DC-"}
    # Shared repertoire; the territory check still applies per area polarity.
    _BOTH_RULES: set = set()

    def __init__(self):
        self._rules = {
            "INS": InsertionRule(),
            "ERA": ErasureRule(),
            "IT+": IterationRule(),
            "IT-": DeiterationRule(),
            "DC+": DoubleCutInsertionRule(),
            "DC-": DoubleCutErasureRule(),
        }
        self._iso_engine = GraphIsomorphismEngine()

    # ------------------------------------------------------------------
    # Game creation
    # ------------------------------------------------------------------

    def new_game(
        self,
        initial_egif: str,
        goal_egif: Optional[str] = None,
        first_player: Player = Player.PROPOSER,
    ) -> GameState:
        """
        Start a new game from EGIF strings.

        Args:
            initial_egif: Starting graph as EGIF text.
            goal_egif: Optional goal graph. Proposer wins if this appears.
            first_player: Who moves first (default: Proposer).
        """
        from egif_parser_dau import parse_egif

        initial_egi = parse_egif(initial_egif)
        goal_egi = parse_egif(goal_egif) if goal_egif else None
        frame_cut = self._establish_frame(initial_egi)

        history = EGITransformationHistory(initial_egi, "Game start")

        return GameState(
            initial_egi=initial_egi,
            current_egi=initial_egi,
            current_player=first_player,
            move_number=0,
            history=history,
            outcome=GameOutcome.ONGOING,
            outcome_reason="",
            frame_cut=frame_cut,
            goal_egi=goal_egi,
        )

    @staticmethod
    def _establish_frame(egi: RelationalGraphWithCuts) -> ElementID:
        """Identify the frame, and refuse a graph that has none.

        The EPG always happens in a context: the Graphist claims, in effect,
        that if the domain model holds then the proposed graph is true, and
        that implication is scribed in a negative area. So the opening graph is
        exactly one cut on the sheet, and nothing else. Sheet-level content is
        not a weaker start — it is not a game, because there is no claim under
        test and no level at which the roles could alternate.
        """
        sheet_contents = egi.area.get(egi.sheet, frozenset())
        cuts = {c.id for c in egi.Cut}
        stray = [e for e in sheet_contents if e not in cuts]
        if stray:
            raise ValueError(
                f"the EPG is played inside a context: {len(stray)} element(s) "
                f"sit at sheet level. Scribe the claim in a cut — "
                f"~[ model ~[ proposal ] ] — and play inside it."
            )
        frame_cuts = [e for e in sheet_contents if e in cuts]
        if len(frame_cuts) != 1:
            raise ValueError(
                f"the EPG needs exactly one frame cut on the sheet; found "
                f"{len(frame_cuts)}."
            )
        return frame_cuts[0]

    # ------------------------------------------------------------------
    # Move application
    # ------------------------------------------------------------------

    def apply_move(
        self,
        state: GameState,
        rule_name: str,
        selected_subgraph: FrozenSet[ElementID],
        target_area: ElementID,
        insert_egif: Optional[str] = None,  # required for INS
    ) -> Tuple[GameState, str]:
        """
        Apply a move for the current player.

        Returns:
            (updated_state, message) — message describes what happened.

        The state is updated in-place for the game log and history;
        the returned state is the same object.
        """
        if state.is_over:
            return state, "Game is already over."

        rule_name = rule_name.upper()

        # --- Permission check ---
        permission_error = self._check_permission(state, rule_name, target_area)
        if permission_error:
            return state, f"Illegal move: {permission_error}"

        polarity, depth = self._area_polarity(state.current_egi, target_area)

        # --- INS: merge parsed EGIF into target area ---
        if rule_name == "INS":
            if not insert_egif:
                return state, "INS requires insert_egif argument."
            result = insert_from_egif(
                state.current_egi, target_area, insert_egif
            )
        else:
            context = TransformationContext(
                source_egi=state.current_egi,
                target_area=target_area,
                selected_subgraph=selected_subgraph,
                area_polarity=polarity,
                nesting_depth=depth,
            )
            rule = self._rules[rule_name]
            result = rule.apply_transformation(context)

        if not result.success:
            return state, f"Rule failed: {result.error_message}"

        # --- Record in history ---
        stub_context = TransformationContext(
            source_egi=state.current_egi,
            target_area=target_area,
            selected_subgraph=selected_subgraph,
            area_polarity=polarity,
            nesting_depth=depth,
        )
        state.history.add_transformation(
            rule_name=f"{rule_name} ({state.current_player.value})",
            context=stub_context,
            result=result,
        )

        # --- Update state ---
        state.current_egi = result.result_egi
        state.move_number += 1
        msg = (
            f"Move {state.move_number}: {state.current_player.value} "
            f"applied {rule_name} in area {target_area}"
        )
        state.move_log.append(msg)

        # --- Win check ---
        outcome, reason = self._check_outcome(state)
        state.outcome = outcome
        state.outcome_reason = reason

        if not state.is_over:
            state.current_player = state.current_player.opponent()

        return state, msg

    def concede(self, state: GameState) -> Tuple[GameState, str]:
        """Current player concedes."""
        if state.is_over:
            return state, "Game is already over."
        winner = state.current_player.opponent()
        state.outcome = (
            GameOutcome.PROPOSER_WINS
            if winner is Player.PROPOSER
            else GameOutcome.SKEPTIC_WINS
        )
        state.outcome_reason = f"{state.current_player.value} conceded."
        msg = state.outcome_reason
        state.move_log.append(msg)
        return state, msg

    # ------------------------------------------------------------------
    # Move enumeration (for hints / automated play)
    # ------------------------------------------------------------------

    def legal_areas(self, state: GameState) -> List[Tuple[ElementID, AreaPolarity, int]]:
        """
        Return all areas where the current player has legal territory.

        Includes territory-specific areas (negative for Proposer, positive for
        Skeptic) plus all areas for DC+/DC- (available to both players).

        Returns list of (area_id, polarity, nesting_depth).
        """
        egi = state.current_egi
        player = state.current_player
        result = []

        for area_id in egi.area:
            polarity, depth = self._area_polarity(egi, area_id)
            # Areas shallower than the frame lie outside the game: the claim
            # under test is what was scribed in the negative context.
            if depth < self.frame_depth(state):
                continue
            if self.owner_of_depth(state, depth) is player:
                result.append((area_id, polarity, depth))

        return result

    def has_legal_moves(self, state: GameState) -> bool:
        """Return True if the current player has at least one legal move.

        Under the eliminative repertoire this is a real question, and its
        answer is the game's third ending: a player with nothing left to erase
        or deiterate in their own territory has run the graph as far down as it
        will go. Previously DC+ was available to both players in every area, so
        this could never be False and the "no legal moves" ending documented at
        the top of this module was unreachable.

        A player has a move when some area they own holds at least one element.
        ERA can take any element from a positive area and IT- any element with
        an accounted-for copy, so a non-empty owned area always admits a
        candidate; an owner with only empty areas has none.
        """
        egi = state.current_egi
        for area_id, _polarity, _depth in self.legal_areas(state):
            if egi.area.get(area_id):
                return True
        return False

    # ------------------------------------------------------------------
    # Status display
    # ------------------------------------------------------------------

    def status_text(self, state: GameState) -> str:
        """Multi-line status string for REPL display."""
        from egif_generator_dau import generate_egif

        lines = []
        lines.append(f"Move {state.move_number} — {state.current_player.value}'s turn")
        lines.append("")

        try:
            egif = generate_egif(state.current_egi)
        except Exception as exc:
            egif = f"<EGIF error: {exc}>"
        lines.append(f"  Current graph: {egif}")

        if state.goal_egi:
            try:
                goal = generate_egif(state.goal_egi)
            except Exception:
                goal = "<?>"
            lines.append(f"  Goal:          {goal}")

        lines.append("")
        lines.append("  Areas and polarity:")
        for area_id, contents in sorted(state.current_egi.area.items()):
            polarity, depth = self._area_polarity(state.current_egi, area_id)
            pol_str = "+" if polarity is AreaPolarity.POSITIVE else "−"
            marker = " ← your territory" if self._is_players_area(state, area_id) else ""
            lines.append(f"    [{pol_str}] depth={depth}  id={area_id}  ({len(contents)} items){marker}")

        if state.is_over:
            lines.append("")
            lines.append(f"  GAME OVER: {state.outcome_reason}")
            if state.winner:
                lines.append(f"  Winner: {state.winner.value}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _area_polarity(
        self,
        egi: RelationalGraphWithCuts,
        area_id: ElementID,
    ) -> Tuple[AreaPolarity, int]:
        """Compute the polarity and nesting depth of an area.

        Delegates to the canonical ``egi.area_polarity()`` method.
        """
        return egi.area_polarity(area_id)

    def _is_players_area(self, state: GameState, area_id: ElementID) -> bool:
        """True if area_id is in the current player's territory."""
        polarity, _ = self._area_polarity(state.current_egi, area_id)
        if state.current_player is Player.PROPOSER:
            return polarity is AreaPolarity.NEGATIVE
        return polarity is AreaPolarity.POSITIVE

    def _check_permission(
        self,
        state: GameState,
        rule_name: str,
        target_area: ElementID,
    ) -> Optional[str]:
        """Return error string if move is not permitted, else None."""
        if rule_name not in self._rules:
            return f"Unknown rule '{rule_name}'"

        # DC+ and DC- are always permitted for either player
        if rule_name in self._BOTH_RULES:
            return None

        polarity, depth = self._area_polarity(state.current_egi, target_area)
        player = state.current_player

        if player is Player.PROPOSER and rule_name not in self._PROPOSER_RULES:
            return (
                f"Proposer cannot use {rule_name}. "
                f"Proposer rules: {', '.join(sorted(self._PROPOSER_RULES))}"
            )
        if player is Player.SKEPTIC and rule_name not in self._SKEPTIC_RULES:
            return (
                f"Skeptic cannot use {rule_name}. "
                f"Skeptic rules: {', '.join(sorted(self._SKEPTIC_RULES))}"
            )
        # Territory is depth-relative, not absolute polarity. The game is
        # scribed inside a negative context, so an absolute test — Proposer in
        # negative areas, Skeptic in positive ones — leaves the Skeptic unable
        # to move anywhere in the frame. Roles switch at each crossing of a
        # cut, measured from the frame's own level: whoever holds the Graphist's
        # part for the sub-graph now exposed is the one who may act on it.
        if depth < self.frame_depth(state):
            return (
                f"Area {target_area!r} (depth {depth}) lies outside the game "
                f"frame, which begins at depth {self.frame_depth(state)}."
            )
        owner = self.owner_of_depth(state, depth)
        if player is not owner:
            return (
                f"{player.value} cannot move at depth {depth}: that level "
                f"belongs to {owner.value}. Roles switch at each crossing of a "
                f"cut, counted from the frame."
            )
        return None

    # ------------------------------------------------------------------
    # Depth-relative roles
    # ------------------------------------------------------------------

    def frame_depth(self, state: GameState) -> int:
        """The level at which play happens — the interior of the frame cut.

        Carried on the state, established once at ``new_game``, never inferred
        from the graph as it changes under play.
        """
        if state.frame_cut is None:
            raise ValueError("game state carries no frame; build it with new_game")
        return state.current_egi.area_polarity(state.frame_cut)[1]

    def owner_of_depth(self, state: GameState, depth: int) -> Player:
        """Who holds the Graphist's part at this level.

        The frame level is the Graphist's; each crossing of a cut hands the
        part to the other player, which is what "proposing the opposite of what
        was scribed" amounts to.
        """
        if (depth - self.frame_depth(state)) % 2 == 0:
            return Player.PROPOSER
        return Player.SKEPTIC

    def _check_outcome(
        self, state: GameState
    ) -> Tuple[GameOutcome, str]:
        """Evaluate win/loss/draw conditions after a move."""
        # Goal check: Proposer wins if goal appears
        if state.goal_egi:
            try:
                if self._goal_achieved(state.current_egi, state.goal_egi):
                    return GameOutcome.PROPOSER_WINS, "Goal graph achieved — Proposer wins!"
            except Exception:
                pass

        # No-move check: next player has no legal moves
        next_player_state = GameState(
            initial_egi=state.initial_egi,
            current_egi=state.current_egi,
            current_player=state.current_player.opponent(),
            move_number=state.move_number,
            history=state.history,
            outcome=GameOutcome.ONGOING,
            outcome_reason="",
            frame_cut=state.frame_cut,
            goal_egi=state.goal_egi,
        )
        if not self.has_legal_moves(next_player_state):
            loser = next_player_state.current_player
            winner = loser.opponent()
            outcome = (
                GameOutcome.PROPOSER_WINS
                if winner is Player.PROPOSER
                else GameOutcome.SKEPTIC_WINS
            )
            return outcome, f"{loser.value} has no legal moves — {winner.value} wins!"

        return GameOutcome.ONGOING, ""

    def _goal_achieved(
        self,
        current: RelationalGraphWithCuts,
        goal: RelationalGraphWithCuts,
    ) -> bool:
        """
        Return True if the goal graph appears (up to isomorphism) as a
        subgraph within the sheet-level (positive) area of current.
        """
        sheet_contents = current.area.get(current.sheet, frozenset())
        if not sheet_contents:
            return False
        goal_elements = (
            frozenset(v.id for v in goal.V)
            | frozenset(e.id for e in goal.E)
            | frozenset(c.id for c in goal.Cut)
        )
        if not goal_elements:
            return True
        matches = self._iso_engine.find_isomorphic_subgraphs(
            current, goal_elements, [current.sheet]
        )
        return bool(matches)
