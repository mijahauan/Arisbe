"""
In-memory session manager for the Agon arena (the Endoporeutic Game).

Agon is the *contest* mode in the Organon / Ergasterion / Agon trio.
Where Ergasterion records a solo Peircean reasoning chain, Agon records
a **dialogical episode**: a contest between the Graphist (who proposes
the graph G) and the Grapheus (the domain model M), presided over by the
Agonothetes (the interpretive function that, after the contest, decides
what the result *means* — see ``docs/ENDOPOREUTIC_GAME_GUIDE.md`` and
``docs/references/Signs_of_Logic.pdf``, Pietarinen 2006).

This manager wraps the headless engine (``endoporeutic_game.py``) — it
holds the engine's ``GameState`` per game id and, alongside it, a
structured **episode record** the engine does not keep: a typed move
log naming, for each move, the player, their Peircean role, the rule,
the area, and the resulting linear form.  That record is the dialogical
provenance — what makes a later "asserted" disposition mean *withstood
challenge* rather than merely *§3.3-attested*.

V1 is deliberately thin (see CURRENT_PLAN.md):

  * **Hot-seat**: one user drives both roles, alternating — the guide's
    own model (the same inquirer proposes and challenges, as in chess
    against oneself).  No automated Grapheus.
  * **Open disposition**: the terminal act is the Agonothetes choosing a
    disposition from the outcome taxonomy; nothing auto-asserts.  The
    engine's ``goal_egif`` win is only a *proxy* for the semantic-
    evaluation layer (not yet built); the disposition layer is where the
    real meaning is assigned.

Nothing here mutates the protected engine; it only observes its state.
"""

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from egi_core_dau import RelationalGraphWithCuts
from egif_generator_dau import generate_egif
from endoporeutic_game import EndoporeuticGame, GameState, Player
from layout_dto import LayoutDTO


# The Peircean role each engine player embodies (see the guide's
# "Three Roles" and "Agonothetes" sections).  The engine speaks of
# Proposer / Skeptic; the arena surfaces the semiotic roles.
PLAYER_ROLE = {
    Player.PROPOSER: "Graphist",  # produces the sign G (Firstness, present)
    Player.SKEPTIC: "Grapheus",   # the domain model M (Secondness, past)
}


def _safe_egif(egi: RelationalGraphWithCuts) -> str:
    try:
        return generate_egif(egi)
    except Exception as exc:  # pragma: no cover - defensive only
        return f"<EGIF error: {exc}>"


@dataclass(frozen=True)
class AgonMove:
    """One move in the dialogical episode.

    Richer than the engine's string ``move_log``: it names the player,
    their Peircean role, the rule, the area acted in, the rule
    parameters, and the resulting linear form — so the whole contest can
    be replayed and so an asserted disposition carries the dialogue as
    provenance.
    """

    move_number: int
    player: str          # engine player value ("Proposer" / "Skeptic")
    role: str            # Peircean role ("Graphist" / "Grapheus")
    rule: str
    target_area: Optional[str]
    parameters: Dict[str, Any]
    resulting_egif: str
    message: str
    timestamp: str


@dataclass
class AgonEpisode:
    """The dialogical record of one game.

    ``setup`` captures how the contest was framed (raw initial EGIF, an
    M/G frame, or a corpus UoD as M).  ``moves`` is the ordered dialogue.
    ``disposition`` is set once the Agonothetes acts (open taxonomy
    choice); until then the episode is in progress.

    ``initial_egi`` and ``move_egis`` keep faithful EGI snapshots (the
    base state and the state after each move) so an asserting disposition
    can build an exact ``TransformationChain`` without re-parsing the
    linear forms.  They are not part of the client payload.
    """

    setup: Dict[str, Any]
    moves: List[AgonMove] = field(default_factory=list)
    disposition: Optional[Dict[str, Any]] = None
    initial_egi: Optional[RelationalGraphWithCuts] = None
    move_egis: List[RelationalGraphWithCuts] = field(default_factory=list)


@dataclass
class AgonGame:
    """An in-progress Agon contest: engine state + dialogical episode."""

    game_id: str
    state: GameState
    episode: AgonEpisode
    current_layout_dto: LayoutDTO
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_egi(self) -> RelationalGraphWithCuts:
        return self.state.current_egi

    @property
    def is_over(self) -> bool:
        return self.state.is_over


class AgonSessionManager:
    """Tracks active Agon contests in memory.

    Like the Ergasterion manager, games are ephemeral — they live only
    while the contest is being played.  A disposition that writes an
    asserted record persists through the corpus boundary (firing §3.3);
    discarding a game removes it entirely.
    """

    def __init__(self) -> None:
        self._games: Dict[str, AgonGame] = {}
        self._engine = EndoporeuticGame()  # stateless across games

    @property
    def engine(self) -> EndoporeuticGame:
        return self._engine

    def create_game(
        self,
        *,
        state: GameState,
        layout_dto: LayoutDTO,
        setup: Dict[str, Any],
    ) -> AgonGame:
        """Open a new contest from an already-constructed engine state."""
        self.cleanup_expired()
        game_id = str(uuid.uuid4())
        game = AgonGame(
            game_id=game_id,
            state=state,
            episode=AgonEpisode(setup=setup, initial_egi=state.initial_egi),
            current_layout_dto=layout_dto,
        )
        self._games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[AgonGame]:
        game = self._games.get(game_id)
        if game is not None:
            game.last_accessed = datetime.now(timezone.utc)
        return game

    def record_move(
        self,
        game: AgonGame,
        *,
        player: Player,
        rule: str,
        target_area: Optional[str],
        parameters: Dict[str, Any],
        message: str,
        new_layout_dto: LayoutDTO,
    ) -> AgonMove:
        """Append a successful move to the episode and advance the layout.

        The engine has already validated and applied the move (mutating
        its ``GameState`` in place); this records the *dialogical* fact of
        it.  ``player`` is the player who made the move (captured before
        the engine flips ``current_player``).
        """
        move = AgonMove(
            move_number=game.state.move_number,
            player=player.value,
            role=PLAYER_ROLE[player],
            rule=rule,
            target_area=target_area,
            parameters=parameters,
            resulting_egif=_safe_egif(game.state.current_egi),
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        game.episode.moves.append(move)
        game.episode.move_egis.append(game.state.current_egi)
        game.current_layout_dto = new_layout_dto
        return move

    def discard_game(self, game_id: str) -> bool:
        if game_id in self._games:
            del self._games[game_id]
            return True
        return False

    def cleanup_expired(self, max_age_hours: int = 4) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        expired = [
            gid for gid, g in self._games.items() if g.last_accessed < cutoff
        ]
        for gid in expired:
            del self._games[gid]
        return len(expired)


# Module-level singleton.
_manager = AgonSessionManager()


def get_agon_session_manager() -> AgonSessionManager:
    """Return the global Agon session manager singleton."""
    return _manager
