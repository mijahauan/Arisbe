"""
The Agonothetes — the interpretive (telic) function of the Endoporeutic
Game.

Peirce's game has three roles, not two (see
``docs/ENDOPOREUTIC_GAME_GUIDE.md`` and Pietarinen 2006).  The Graphist
proposes the graph G; the Grapheus is the domain model M; the
**Agonothetes** is the *interpretant* — it presides over the contest and,
crucially, decides afterward what the result *means*.  A two-party duel
that outputs true/false is, in Peirce's own terms, a degenerate sign-
process.  The Agonothetes is where deduction, induction, and abduction
actually happen: the same boolean outcome can mean a theorem, a new fact,
an abductive hypothesis, a revision of M, a fork of the universe, or a
recorded conjecture.

This module makes that taxonomy **data**, not control flow.  V1 is
deliberately thin and *open* (CURRENT_PLAN.md): every taxonomic
disposition is enumerable and selectable, but only the well-understood
**asserting** dispositions actually write a corpus record (and fire §3.3
at that boundary).  The rest are recorded on the episode as the
Agonothetes' judgment without yet committing a bespoke corpus semantics —
so the structure is ready to grow as we play real games, and **nothing
auto-asserts**.

The disposition that asserts persists the whole contest as a
``TransformationChain`` (built from faithful per-move EGI snapshots), so
the corpus record carries the dialogue as provenance — "asserted =
withstood challenge", not merely §3.3-attested.  The chain naturally
holds both the initial thesis (its base state) and the final residue of
play (its current state), distinctly.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from tomos_service import ChainStep, TomosService, TransformationChain
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)

from web_api.services.agon_session_manager import AgonGame


# ---------------------------------------------------------------------------
# The outcome taxonomy (docs/ENDOPOREUTIC_GAME_GUIDE.md §"Taxonomy of Game
# Outcomes").  Enumerated as data so the arena surfaces the full space of
# meanings and the Agonothetes (the user) chooses — rather than the route
# hardcoding "win → assert".
#
#   key      : stable identifier
#   label    : human-facing name
#   mode     : Peirce's mode of inference this disposition embodies
#   asserts  : whether choosing it writes an asserted corpus record
#              (and therefore fires §3.3).  False = recorded judgment only.
#   summary  : one line on what it means / does
# ---------------------------------------------------------------------------

DISPOSITIONS: List[Dict[str, Any]] = [
    {"key": "theorem_registration", "label": "Register as theorem", "mode": "deduction",
     "asserts": True,
     "summary": "G is entailed by M; add it to the corpus as a derived theorem with its contest as proof."},
    {"key": "redundancy", "label": "Redundant (already in M)", "mode": "deduction",
     "asserts": False,
     "summary": "G was already entailed/equivalent; the contest is recorded as an alternative derivation."},
    {"key": "rejection", "label": "Reject", "mode": "none",
     "asserts": False,
     "summary": "G contradicts M and M stands; recorded (optionally to a rejected folio), not asserted."},
    {"key": "challenge_to_M", "label": "Challenge M (revision)", "mode": "abduction",
     "asserts": True,
     "summary": "G's refutation is evidence against M — the revolutionary case; assert the contest as grounds for revising M."},
    {"key": "fork", "label": "Fork the universe", "mode": "none",
     "asserts": True,
     "summary": "Both G and ¬G are defensible; branch the UoD, asserting this contest as one branch."},
    {"key": "reductio", "label": "Reductio resource", "mode": "deduction",
     "asserts": True,
     "summary": "The contradiction establishes ¬G as a theorem of M; assert that constraint."},
    {"key": "new_fact", "label": "Accept as new fact", "mode": "induction",
     "asserts": True,
     "summary": "G is independent of M and observed; assert it, growing M by induction."},
    {"key": "abductive_hypothesis", "label": "Accept as hypothesis", "mode": "abduction",
     "asserts": True,
     "summary": "G explains something puzzling in M; assert with a hypothesis marker, pending further evidence."},
    {"key": "open_conjecture", "label": "Record as conjecture", "mode": "abduction",
     "asserts": False,
     "summary": "G is interesting but unverified; recorded as a conjecture, neither asserted nor denied."},
    {"key": "definition", "label": "Accept as definition", "mode": "none",
     "asserts": True,
     "summary": "G introduces terminology/structure accepted by convention; assert it."},
    {"key": "conditional_acceptance", "label": "Accept conditionally", "mode": "deduction",
     "asserts": True,
     "summary": "G holds under an added premise P; assert P → G."},
    {"key": "tautology", "label": "Tautology (soundness check)", "mode": "deduction",
     "asserts": False,
     "summary": "G is trivially true; informative as a soundness check, not asserted."},
    {"key": "self_contradictory", "label": "Self-contradictory", "mode": "none",
     "asserts": False,
     "summary": "G is unsatisfiable — likely a formalization error; recorded, not asserted."},
]

_DISPOSITION_BY_KEY = {d["key"]: d for d in DISPOSITIONS}


# Which dispositions cohere with each semantic-game verdict (part 3 of the
# inning).  The list stays complete and selectable — the meaning is the
# Agonothetes' to assign, on collateral warrant the verdict cannot supply
# (the physician's FALSE means "complete M", the student's means "reject":
# same verdict, different judgment).  This only *annotates*; nothing narrows
# or auto-asserts.
_COHERENT_WITH = {
    "true": {"theorem_registration", "redundancy", "conditional_acceptance", "tautology"},
    "false": {"rejection", "challenge_to_M", "reductio", "fork", "self_contradictory"},
    "unknown": {"new_fact", "abductive_hypothesis", "open_conjecture", "definition", "fork"},
}


def available_dispositions(
    game: Optional[AgonGame] = None, verdict: Optional[str] = None
) -> List[Dict[str, Any]]:
    """The dispositions the Agonothetes may choose for this contest.

    Returns the whole taxonomy (the meaning is the user's to assign).  When a
    semantic-game ``verdict`` ("true" / "false" / "unknown") is supplied, each
    disposition is annotated with ``coherent_with_verdict`` — a hint, not a
    filter: the list stays complete and open, and nothing auto-asserts.  The
    disposition remains a judgment on collateral warrant the verdict alone
    cannot decide.
    """
    coherent = _COHERENT_WITH.get(verdict or "", set())
    return [
        {
            "key": d["key"],
            "label": d["label"],
            "mode": d["mode"],
            "asserts": d["asserts"],
            "summary": d["summary"],
            "coherent_with_verdict": (d["key"] in coherent) if verdict else None,
        }
        for d in DISPOSITIONS
    ]


def _episode_to_chain(game: AgonGame) -> TransformationChain:
    """Build a faithful ``TransformationChain`` from the contest episode.

    Uses the per-move EGI snapshots (not re-parsed linear forms), so the
    persisted chain is exact.  Each ``ChainStep`` records the rule, the
    player/role, the move parameters, and the engine's move message.
    """
    episode = game.episode
    initial_state_id = f"state-{uuid.uuid4().hex[:8]}"
    states = {initial_state_id: episode.initial_egi}
    steps: List[ChainStep] = []
    prev_id = initial_state_id

    for move, egi in zip(episode.moves, episode.move_egis):
        to_id = f"state-{uuid.uuid4().hex[:8]}"
        states[to_id] = egi
        params = dict(move.parameters)
        params.update({"player": move.player, "role": move.role,
                       "target_area": move.target_area})
        steps.append(
            ChainStep(
                step_id=f"step-{uuid.uuid4().hex[:8]}",
                rule_name=f"{move.rule} ({move.role})",
                from_state_id=prev_id,
                to_state_id=to_id,
                parameters=params,
                timestamp=move.timestamp,
                user_annotation=move.message,
            )
        )
        prev_id = to_id

    return TransformationChain(
        initial_state_id=initial_state_id,
        steps=steps,
        states=states,
    )


class DispositionError(Exception):
    """A disposition could not be applied for a non-§3.3 reason."""


def apply_disposition(
    game: AgonGame,
    *,
    disposition_key: str,
    tomos: TomosService,
    target_uod_id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    authors: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply the Agonothetes' chosen disposition to a finished contest.

    For an **asserting** disposition, the whole episode is persisted as a
    new ``EPG_SESSION`` UoD via ``save_uod_with_chain`` — which fires §3.3
    on the asserted final state before any disk write (clean refusal on
    drift).  For a **non-asserting** disposition, the judgment is recorded
    on the episode only; no corpus write, no §3.3.

    Nothing auto-asserts: this is only reached when the user (as
    Agonothetes) explicitly chooses a disposition.

    Returns a result dict; raises ``DispositionError`` for unknown keys /
    missing target / duplicate id, and propagates ``CorrespondenceViolation``
    from the corpus boundary unchanged.
    """
    spec = _DISPOSITION_BY_KEY.get(disposition_key)
    if spec is None:
        raise DispositionError(
            f"Unknown disposition '{disposition_key}'. "
            f"Valid: {sorted(_DISPOSITION_BY_KEY)}."
        )

    # Record the Agonothetes' judgment on the episode regardless of whether
    # it writes to the corpus — the interpretation is itself part of the
    # episode's record.
    judgment = {
        "key": spec["key"],
        "label": spec["label"],
        "mode": spec["mode"],
        "asserts": spec["asserts"],
        "notes": notes or "",
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }

    if not spec["asserts"]:
        judgment["asserted_uod_id"] = None
        game.episode.disposition = judgment
        return {
            "disposition": judgment,
            "asserted": False,
            "message": (
                f"Recorded disposition '{spec['label']}' (no corpus assertion)."
            ),
        }

    # Asserting disposition — requires an explicit, non-colliding target id.
    if not target_uod_id or not target_uod_id.strip():
        raise DispositionError(
            f"Disposition '{spec['label']}' asserts a corpus record and "
            f"requires a target_uod_id."
        )
    target_uod_id = target_uod_id.strip()
    if tomos.uod_exists(target_uod_id):
        raise DispositionError(
            f"UoD '{target_uod_id}' already exists; assertion never "
            f"overwrites. Choose a different id."
        )

    chain = _episode_to_chain(game)
    now = datetime.now(timezone.utc)
    tag_set = set(tags or [])
    tag_set.update({"agon", f"disposition:{spec['key']}", f"mode:{spec['mode']}"})

    metadata = UoDMetadata(
        uod_id=target_uod_id,
        uod_type=UoDType.HISTORICAL,
        name=name or target_uod_id,
        description=description or spec["summary"],
        category=UoDCategory.EPG_SESSION,
        created=now,
        last_modified=now,
        authors=list(authors or []),
        tags=tag_set,
        total_states=len(chain.states),
        total_transformations=len(chain.steps),
    )
    uod = UniverseOfDiscourse(metadata=metadata, current_egi=chain.current_egi)

    # §3.3 fires inside save_uod_with_chain → save_uod, BEFORE any disk
    # write.  A CorrespondenceViolation aborts cleanly (no half-saved
    # contest) and is surfaced by the route.
    tomos.save_uod_with_chain(uod, chain)

    judgment["asserted_uod_id"] = target_uod_id
    game.episode.disposition = judgment
    return {
        "disposition": judgment,
        "asserted": True,
        "asserted_uod_id": target_uod_id,
        "state_count": len(chain.states),
        "step_count": len(chain.steps),
        "message": f"Asserted contest as '{target_uod_id}' ({spec['label']}).",
    }
