"""
Endoporeutic Game Engine  (Dau Chapter 21 / Peirce)

Implements the two-player dialogical game on Existential Graphs.

Players
-------
PROPOSER  Defends the graph.  Moves in NEGATIVE (odd-depth) areas.
          Legal rules: INS, IT+, DC+
SKEPTIC   Attacks the graph.  Moves in POSITIVE (even-depth) areas.
          Legal rules: ERA, IT-, DC-

DC+/DC- are meaning-preserving in all contexts and are permitted for
both players in any area (they do not affect what can be proven).

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
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from egi_transformation_history import EGITransformationHistory
from frozendict import frozendict

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

    # Rules available to each player
    _PROPOSER_RULES = {"INS", "IT+", "DC+"}
    _SKEPTIC_RULES  = {"ERA", "IT-", "DC-"}
    # Either player may use DC+ / DC- (meaning-preserving in all contexts)
    _BOTH_RULES     = {"DC+", "DC-"}

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

        history = EGITransformationHistory(initial_egi, "Game start")

        return GameState(
            initial_egi=initial_egi,
            current_egi=initial_egi,
            current_player=first_player,
            move_number=0,
            history=history,
            outcome=GameOutcome.ONGOING,
            outcome_reason="",
            goal_egi=goal_egi,
        )

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

        # --- INS: merge parsed EGIF into target area directly ---
        if rule_name == "INS":
            if not insert_egif:
                return state, "INS requires insert_egif argument."
            result = self._apply_ins(
                state.current_egi, target_area, insert_egif, polarity, depth
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
            if player is Player.PROPOSER and polarity is AreaPolarity.NEGATIVE:
                result.append((area_id, polarity, depth))
            elif player is Player.SKEPTIC and polarity is AreaPolarity.POSITIVE:
                result.append((area_id, polarity, depth))

        return result

    def has_legal_moves(self, state: GameState) -> bool:
        """
        Return True if the current player has at least one legal move.

        DC+ is always available to both players in any area, so as long as
        any area exists (and the sheet always exists) there is always a legal
        move.  The game therefore only ends via concede or goal achievement.
        """
        return bool(state.current_egi.area)  # sheet is always present

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
        """Compute the polarity and nesting depth of an area."""
        depth = self._nesting_depth(egi, area_id)
        polarity = AreaPolarity.POSITIVE if depth % 2 == 0 else AreaPolarity.NEGATIVE
        return polarity, depth

    def _nesting_depth(self, egi: RelationalGraphWithCuts, area_id: ElementID) -> int:
        """Count how many cuts enclose area_id (0 for the sheet)."""
        if area_id == egi.sheet:
            return 0
        depth = 0
        current = area_id
        visited: set = set()
        while current != egi.sheet:
            if current in visited:
                break
            visited.add(current)
            parent = next(
                (pid for pid, contents in egi.area.items() if current in contents),
                None,
            )
            if parent is None:
                break
            depth += 1
            current = parent
        return depth

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
        if player is Player.PROPOSER and polarity is not AreaPolarity.NEGATIVE:
            return (
                f"Proposer can only move in NEGATIVE (odd-depth) areas. "
                f"Area {target_area!r} is positive (depth={depth})."
            )
        if player is Player.SKEPTIC and polarity is not AreaPolarity.POSITIVE:
            return (
                f"Skeptic can only move in POSITIVE (even-depth) areas. "
                f"Area {target_area!r} is negative (depth={depth})."
            )
        return None

    def _apply_ins(
        self,
        egi: RelationalGraphWithCuts,
        target_area: ElementID,
        insert_egif: str,
        polarity: AreaPolarity,
        depth: int,
    ) -> TransformationResult:
        """
        INS: parse insert_egif and merge all sheet-level elements into target_area.

        This is the correct game-level INS: the Proposer writes a new sub-graph
        into a negative area, exactly as Peirce described (any graph may be
        asserted in a negatively-enclosed area).
        """
        if polarity is not AreaPolarity.NEGATIVE:
            return TransformationResult(
                False, None,
                "INS only allowed in negative (odd-depth) areas.", {}
            )

        try:
            import uuid
            from egif_parser_dau import parse_egif

            insert_egi = parse_egif(insert_egif)

            # Collect top-level elements from the insert EGI (those on its sheet)
            src_sheet_contents = insert_egi.area.get(insert_egi.sheet, frozenset())

            # Assign fresh IDs to avoid collisions with the host EGI
            id_map: Dict[ElementID, ElementID] = {}

            def fresh_v() -> ElementID:
                return ElementID(f"v_{uuid.uuid4().hex[:8]}")
            def fresh_e() -> ElementID:
                return ElementID(f"e_{uuid.uuid4().hex[:8]}")
            def fresh_c() -> ElementID:
                return ElementID(f"c_{uuid.uuid4().hex[:8]}")

            new_V = set(egi.V)
            new_E = set(egi.E)
            new_Cut = set(egi.Cut)
            new_nu = dict(egi.nu)
            new_rel = dict(egi.rel)
            new_area = dict(egi.area)

            def _copy_element(elem_id: ElementID):
                """Recursively copy an element from insert_egi into host."""
                if elem_id in id_map:
                    return id_map[elem_id]

                v_match = next((v for v in insert_egi.V if v.id == elem_id), None)
                if v_match is not None:
                    nid = fresh_v()
                    id_map[elem_id] = nid
                    from egi_core_dau import Vertex
                    new_V.add(Vertex(id=nid, label=v_match.label, is_generic=v_match.is_generic))
                    return nid

                e_match = next((e for e in insert_egi.E if e.id == elem_id), None)
                if e_match is not None:
                    nid = fresh_e()
                    id_map[elem_id] = nid
                    from egi_core_dau import Edge
                    new_E.add(Edge(nid))
                    if elem_id in insert_egi.rel:
                        new_rel[nid] = insert_egi.rel[elem_id]
                    return nid

                c_match = next((c for c in insert_egi.Cut if c.id == elem_id), None)
                if c_match is not None:
                    nid = fresh_c()
                    id_map[elem_id] = nid
                    from egi_core_dau import Cut
                    new_Cut.add(Cut(nid))
                    # Recursively copy cut interior
                    inner_contents = insert_egi.area.get(elem_id, frozenset())
                    new_inner = set()
                    for inner_id in inner_contents:
                        copied = _copy_element(inner_id)
                        new_inner.add(copied)
                    new_area[nid] = frozenset(new_inner)
                    return nid

                return elem_id  # unknown: pass through

            # Copy all top-level elements
            top_level_new = set()
            for elem_id in src_sheet_contents:
                copied_id = _copy_element(elem_id)
                top_level_new.add(copied_id)

            # Fix nu mappings for all copied edges
            for orig_e_id, new_e_id in id_map.items():
                if any(new_e_id == e.id for e in new_E) and orig_e_id in insert_egi.nu:
                    new_nu[new_e_id] = tuple(
                        id_map.get(vid, vid) for vid in insert_egi.nu[orig_e_id]
                    )

            # Add top-level copies to target area
            existing = new_area.get(target_area, frozenset())
            new_area[target_area] = existing | frozenset(top_level_new)

            from egi_core_dau import RelationalGraphWithCuts
            result_egi = RelationalGraphWithCuts(
                V=frozenset(new_V),
                E=frozenset(new_E),
                nu=frozendict(new_nu),
                sheet=egi.sheet,
                Cut=frozenset(new_Cut),
                area=frozendict(new_area),
                rel=frozendict(new_rel),
            )
            return TransformationResult(
                success=True,
                result_egi=result_egi,
                error_message=None,
                changes_made={"rule": "INS", "inserted": list(top_level_new)},
            )
        except Exception as exc:
            return TransformationResult(False, None, str(exc), {})

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
