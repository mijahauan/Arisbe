"""
Agon (arena) routes — the Endoporeutic Game as a route over the corpus.

Agon is the *contest* mode in the Organon / Ergasterion / Agon trio.
Where Organon reads the archive and Ergasterion composes a solo chain,
Agon hosts the **dialogical** test of a proposal G against a domain model
M, presided over by the Agonothetes (the interpretive function that
assigns meaning to the result).  See ``docs/ENDOPOREUTIC_GAME_GUIDE.md``
and ``docs/references/Signs_of_Logic.pdf`` (Pietarinen 2006).

V1 is a deliberately thin, flexible slice (CURRENT_PLAN.md):

  * **Hot-seat** — one user drives both the Graphist (Proposer) and the
    Grapheus (Skeptic); the engine enforces territory and polarity.  No
    automated opponent.
  * **Open disposition** — when the contest ends the user, *as
    Agonothetes*, chooses a disposition from the outcome taxonomy.
    Nothing auto-asserts; only an asserting disposition writes a corpus
    record (and fires §3.3 there).

The selection-heavy UI leans on the Task-1 additions: per-element area +
polarity introspection in every payload, and ``/rules`` for each rule's
required inputs.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter
from fastapi.responses import FileResponse

from web_api.models.api_models import (
    AgonContestChooseRequest,
    AgonContestStartRequest,
    AgonDispositionRequest,
    AgonInterpretRequest,
    AgonInverseRequest,
    AgonModelTestRequest,
    AgonMoveRequest,
    AgonNewGameRequest,
    AgonSetModelRequest,
    ApiResponse,
)
from web_api.services.agon_session_manager import (
    PLAYER_ROLE,
    AgonGame,
    get_agon_session_manager,
)
from web_api.services.agonothetes import (
    DispositionError,
    apply_disposition,
    available_dispositions,
)
from web_api.services.grapheus_session_manager import get_grapheus_session_manager
from web_api.services.introspection import egi_introspection
from web_api.services.layout_service import generate_layout, layout_dto_to_dict
from web_api.services.linear_forms import linear_forms

from correspondence_attestation import CorrespondenceViolation
from domain_oracle import CorpusOracle
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from endoporeutic_game import Player
from grapheus import GrapheusContest
from model_materialization import materialize_egi
from semantic_game import evaluate as evaluate_semantic
from theory_query import entails as theory_entails
from tomos_service import TomosService


router = APIRouter(prefix="/agon")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")
VIEWER_DIR = Path(__file__).parent.parent.parent / "web_viewer"

_tomos_service: Optional[TomosService] = None


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


def _player_from_name(name: Optional[str]) -> Player:
    if name and name.strip().lower() in ("skeptic", "grapheus"):
        return Player.SKEPTIC
    return Player.PROPOSER


def _egi_summary(egi) -> dict:
    return {
        "vertex_count": len(egi.V),
        "edge_count": len(egi.E),
        "cut_count": len(egi.Cut),
    }


def _legal_areas(game: AgonGame) -> List[dict]:
    """The current player's territory (area, polarity, depth)."""
    engine = get_agon_session_manager().engine
    out = []
    for area_id, polarity, depth in engine.legal_areas(game.state):
        out.append({"area_id": area_id, "polarity": polarity.value, "depth": depth})
    return out


def _episode_payload(game: AgonGame) -> dict:
    return {
        "setup": game.episode.setup,
        "moves": [
            {
                "move_number": m.move_number,
                "player": m.player,
                "role": m.role,
                "rule": m.rule,
                "target_area": m.target_area,
                "parameters": m.parameters,
                "resulting_egif": m.resulting_egif,
                "message": m.message,
                "timestamp": m.timestamp,
            }
            for m in game.episode.moves
        ],
        "disposition": game.episode.disposition,
    }


def _game_payload(game: AgonGame, svg: str) -> dict:
    """Standard response shape for any endpoint returning a contest state."""
    state = game.state
    current_player = state.current_player
    payload = {
        "game_id": game.game_id,
        "svg": svg,
        "layout_dto": layout_dto_to_dict(game.current_layout_dto),
        "egi_summary": _egi_summary(state.current_egi),
        # Task-1 introspection: per-element area + polarity, so the
        # selection-heavy arena UI can show whose territory each element
        # is in without inferring from geometry.
        "introspection": egi_introspection(state.current_egi),
        # Linear form(s) of the contest's current state, beside its drawing.
        "linear_forms": linear_forms(state.current_egi),
        "current_player": current_player.value,
        "current_role": PLAYER_ROLE[current_player],
        "move_number": state.move_number,
        "outcome": state.outcome.value,
        "outcome_reason": state.outcome_reason,
        "winner": state.winner.value if state.winner else None,
        "is_over": state.is_over,
        "legal_areas": _legal_areas(game),
        "episode": _episode_payload(game),
    }
    # When the contest is over, surface the open disposition taxonomy so
    # the Agonothetes (the user) can assign meaning to the result.
    if state.is_over:
        payload["available_dispositions"] = available_dispositions(game)
    return payload


# --------------------------------------------------------------------------- #
# HTML viewer                                                                 #
# --------------------------------------------------------------------------- #


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def agon_index():
    """Serve the Agon arena HTML page."""
    return FileResponse(str(VIEWER_DIR / "agon.html"))


# --------------------------------------------------------------------------- #
# Game lifecycle                                                              #
# --------------------------------------------------------------------------- #


def _build_initial_egif(request: AgonNewGameRequest):
    """Resolve a contest's framing into ``(framed_egif, model_egif, proposal_egif)``.

    Frame construction (``~[ M ~[ G ] ]``) is a convenience for the common M → G
    contest; the resolved M and G are returned alongside (``None`` for the raw
    ``initial_egif`` escape hatch) so the **interpretation register** can peel G
    against M.  (Caveat: naive M/G framing concatenates linear forms — beta label
    scoping across M and G is the caller's responsibility; use ``initial_egif``
    for shared ligatures.)
    """
    if request.initial_egif is not None:
        return request.initial_egif, None, None

    proposal = (request.proposal_egif or "").strip()

    if request.base_source and request.base_source.startswith("uod:"):
        if not proposal:
            raise ValueError("base_source requires a proposal_egif (the graph G).")
        uod_id = request.base_source[len("uod:"):]
        tomos = _get_tomos()
        uod = tomos.load_uod(uod_id, attest=False)  # M read as data, not drawn
        if uod is None or uod.current_egi is None:
            raise ValueError(f"UoD '{uod_id}' not found or has no current EGI.")
        from egif_generator_dau import generate_egif
        model = generate_egif(uod.current_egi)
        return f"~[ {model} ~[ {proposal} ] ]", model, proposal

    if request.model_egif is not None:
        if not proposal:
            raise ValueError("model_egif requires a proposal_egif (the graph G).")
        model = request.model_egif.strip()
        return f"~[ {model} ~[ {proposal} ] ]", model, proposal

    raise ValueError(
        "Provide initial_egif, or model_egif + proposal_egif, or "
        "base_source 'uod:<id>' + proposal_egif."
    )


@router.post("/games")
async def new_game(request: AgonNewGameRequest):
    """Start a new contest.

    Renders the starting graph through ``layout_service`` (which attests
    §3.3 at the render boundary — confirming the framed graph is in
    correspondence before play begins).
    """
    try:
        try:
            initial_egif, model_egif, proposal_egif = _build_initial_egif(request)
            setup: Dict[str, Any] = {
                "initial_egif": request.initial_egif,
                "model_egif": model_egif,
                "proposal_egif": proposal_egif,
                "base_source": request.base_source,
                "goal_egif": request.goal_egif,
                "framed_egif": initial_egif,
                "model_closed": request.model_closed,
                "first_player": _player_from_name(request.first_player).value,
            }
        except ValueError as exc:
            return ApiResponse(
                success=False,
                error={"code": "INVALID_SETUP", "message": str(exc)},
            )

        manager = get_agon_session_manager()
        state = manager.engine.new_game(
            initial_egif=initial_egif,
            goal_egif=request.goal_egif,
            first_player=_player_from_name(request.first_player),
        )

        dto, svg = generate_layout(state.current_egi)
        game = manager.create_game(
            state=state, layout_dto=dto, setup=setup,
            model_egif=model_egif, proposal_egif=proposal_egif,
            model_closed=request.model_closed,
        )
        return ApiResponse(success=True, data=_game_payload(game, svg))

    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
                   "context": getattr(exc, "context", None)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "NEW_GAME_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Return the current state of a contest (re-renders, attests §3.3)."""
    try:
        manager = get_agon_session_manager()
        game = manager.get_game(game_id)
        if game is None:
            return ApiResponse(
                success=False,
                error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
            )
        dto, svg = generate_layout(game.current_egi)
        game.current_layout_dto = dto
        return ApiResponse(success=True, data=_game_payload(game, svg))
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "GET_GAME_ERROR", "message": str(exc)},
        )


@router.delete("/games/{game_id}")
async def discard_game(game_id: str):
    """Discard a contest and its in-memory episode."""
    manager = get_agon_session_manager()
    found = manager.discard_game(game_id)
    if not found:
        return ApiResponse(
            success=False,
            error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
        )
    return ApiResponse(success=True, data={"game_id": game_id})


# --------------------------------------------------------------------------- #
# Moves                                                                       #
# --------------------------------------------------------------------------- #


@router.post("/games/{game_id}/move")
async def apply_move(game_id: str, request: AgonMoveRequest):
    """Apply one move for the current player.

    The engine enforces the player's territory (Graphist in negative
    areas, Grapheus in positive areas; DC+/DC- for both) and the rule
    preconditions.  A rejected move returns the engine's message; a
    successful one appends to the dialogical episode and re-renders.
    """
    try:
        manager = get_agon_session_manager()
        game = manager.get_game(game_id)
        if game is None:
            return ApiResponse(
                success=False,
                error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
            )
        if game.state.is_over:
            return ApiResponse(
                success=False,
                error={"code": "GAME_OVER",
                       "message": "The contest is over; choose a disposition."},
            )

        params = request.parameters or {}
        selected = frozenset(params.get("selected_elements", []) or [])
        target_area = params.get("target_area")
        insert_egif = params.get("egif_content") or params.get("insert_egif")

        if target_area is None:
            return ApiResponse(
                success=False,
                error={"code": "MISSING_TARGET_AREA",
                       "message": "A target_area is required for a move."},
            )

        mover = game.state.current_player
        before = game.state.move_number

        # Engine mutates state in place and returns (state, message).
        _state, message = manager.engine.apply_move(
            game.state,
            request.rule,
            selected,
            target_area,
            insert_egif=insert_egif,
        )

        if game.state.move_number <= before:
            # No advance → the move was rejected (illegal / precondition).
            return ApiResponse(
                success=False,
                error={"code": "ILLEGAL_MOVE", "message": message, "rule": request.rule},
            )

        new_dto, svg = generate_layout(
            game.current_egi, previous_layout=game.current_layout_dto
        )
        manager.record_move(
            game,
            player=mover,
            rule=request.rule,
            target_area=target_area,
            parameters=params,
            message=message,
            new_layout_dto=new_dto,
        )
        return ApiResponse(success=True, data=_game_payload(game, svg))

    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
                   "context": getattr(exc, "context", None)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "MOVE_ERROR", "message": str(exc), "type": type(exc).__name__},
        )


@router.post("/games/{game_id}/concede")
async def concede(game_id: str):
    """The current player concedes; the opponent wins."""
    try:
        manager = get_agon_session_manager()
        game = manager.get_game(game_id)
        if game is None:
            return ApiResponse(
                success=False,
                error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
            )
        manager.engine.concede(game.state)
        dto, svg = generate_layout(game.current_egi)
        game.current_layout_dto = dto
        return ApiResponse(success=True, data=_game_payload(game, svg))
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "CONCEDE_ERROR", "message": str(exc)},
        )


# --------------------------------------------------------------------------- #
# Reference models — what M can be chosen (the inning's part 1)               #
# --------------------------------------------------------------------------- #


@router.get("/models")
async def list_models():
    """Reference models a contest can be tested against (part 1: choose M).

    Two sources: curated **example** scenarios (ready-to-play, one per outcome) and
    the **corpus** UoDs (any asserted graph can serve as a model M). The frontend
    populates its model picker from this.
    """
    from agon_models import list_example_models

    examples = [
        {"id": e.id, "title": e.title, "model_egif": e.model_egif,
         "closed": e.closed, "sample_proposal": e.sample_proposal, "note": e.note}
        for e in list_example_models()
    ]
    corpus = []
    try:
        for entry in _get_tomos().list_uods():
            uid = entry.get("uod_id") or entry.get("id")
            if uid:
                corpus.append({"uod_id": uid,
                               "title": entry.get("name") or entry.get("title") or uid})
    except Exception:
        corpus = []  # corpus listing is best-effort; examples always work
    return ApiResponse(success=True, data={"examples": examples, "corpus": corpus})


def _resolve_model_egif(model_egif: Optional[str], model_uod: Optional[str]) -> str:
    """Resolve a chosen model M to its EGIF (raw facts or a corpus UoD's atoms)."""
    if model_uod:
        uod = _get_tomos().load_uod(model_uod, attest=False)  # M read as data
        if uod is None or uod.current_egi is None:
            raise ValueError(f"Model UoD '{model_uod}' not found or has no current EGI.")
        from egif_generator_dau import generate_egif
        return generate_egif(uod.current_egi)
    if model_egif and model_egif.strip():
        return model_egif.strip()
    raise ValueError("Provide model_egif or model_uod (a corpus UoD id).")


def _materialization_dict(rep, facts_egi) -> dict:
    """The materialization report as a client payload (shared by the peel + the
    automated-Grapheus contest)."""
    return {
        "summary": rep.summary,
        "base_facts": rep.base_facts,
        "derived_facts": rep.derived_facts,
        "rules_applied": rep.rules_applied,
        "materialized_egif": generate_egif(facts_egi),
        "skipped": [{"reason": s.reason, "description": s.description}
                    for s in rep.skipped],
    }


def _interpret_payload(
    model_egif: str, proposal_egif: str, closed: bool, materialize: bool = False
) -> dict:
    """Run the peel and shape the result (shared by the standalone + game routes).

    When ``materialize`` is set, M's Horn rules are forward-chained to the least
    Herbrand model first (the syllogism works; a model authored as facts + rules
    becomes testable), and the materialization report is returned alongside.
    """
    materialization = None
    theorem = None
    if materialize:
        theory_egi = parse_egif(model_egif)
        facts_egi, rep = materialize_egi(theory_egi)
        oracle = CorpusOracle([("M", facts_egi)], closed=closed)
        materialization = _materialization_dict(rep, facts_egi)
        # When G is a universal subsumption/typing rule, model-checking it against an
        # empty or sparse A-box reads *vacuously* — so decide it as a **theorem of the
        # theory M** instead (freeze a fresh witness, materialize, check the head).
        # This is what makes a real T-box ontology (SUMO, Porphyry, FOAF) testable.
        tq = theory_entails(theory_egi, parse_egif(proposal_egif))
        if tq.applicable:
            theorem = {
                "verdict": tq.verdict,
                "summary": tq.summary,
                "body_egif": tq.body_egif,
                "head_egif": tq.head_egif,
                "witnesses": [w.constant for w in tq.witnesses],
                "derived": tq.derived,
                "missing": tq.missing,
                "skipped_in_theory": tq.skipped_in_theory,
            }
    else:
        oracle = CorpusOracle.from_egif({"M": model_egif}, closed=closed)
    result = evaluate_semantic(parse_egif(proposal_egif), oracle)
    verdict = result.verdict.value
    return {
        "model_egif": model_egif,
        "proposal_egif": proposal_egif,
        "closed": closed,
        "materialization": materialization,
        "theorem": theorem,
        "verdict": verdict,
        "holds": result.holds,
        "summary": result.summary,
        "transcript": result.transcript,
        "winning_witness": result.winning_witness,
        "counterexample": result.counterexample,
        "available_dispositions": available_dispositions(verdict=verdict),
    }


def _g_sheet_atoms(g_egi):
    """G's sheet-level atoms as (relation, arg-vertex-tuple, display) — the
    negation-free pieces whose individual fit measures a partial map."""
    vmap = {v.id: v for v in g_egi.V}
    edge_ids = {e.id for e in g_egi.E}
    out = []
    for eid in g_egi.area.get(g_egi.sheet, ()):
        if eid in edge_ids:
            verts = tuple(g_egi.nu[eid])
            args = " ".join(
                ('"' + vmap[v].label + '"'
                 if (not vmap[v].is_generic and vmap[v].label) else "*")
                for v in verts)
            disp = "(" + g_egi.get_relation_name(eid) + ((" " + args) if args else "") + ")"
            out.append((g_egi.get_relation_name(eid), verts, disp))
    return out


def _candidate_fit(kind, cid, title, model_egif, closed, g_egi, g_consts,
                   g_atoms, materialize):
    """Evaluate G against one candidate model M and describe the relationship."""
    if materialize:
        facts_egi, _rep = materialize_egi(parse_egif(model_egif))
        oracle = CorpusOracle([("M", facts_egi)], closed=closed)
    else:
        oracle = CorpusOracle.from_egif({"M": model_egif}, closed=closed)
    result = evaluate_semantic(g_egi, oracle)
    verdict = result.verdict.value

    # Partial map: which of G's sheet atoms individually hold (coarse — each atom's
    # lines treated independently; the whole-graph verdict carries joint satisfaction).
    held, residue = [], []
    for rel, verts, disp in g_atoms:
        ok = bool(oracle.match_atoms([(rel, verts)], constants=g_consts))
        (held if ok else residue).append(disp)
    fit = (len(held) / len(g_atoms)) if g_atoms else (1.0 if result.holds else 0.0)

    if verdict == "true":
        relationship = "holds"          # at home — a theorem of this model
    elif verdict == "false":
        relationship = "contradicts"    # alien
    elif held:
        relationship = "partial"        # some of G at home; residue is the contribution
    else:
        relationship = "independent"    # consistent but unrelated

    return {
        "kind": kind, "id": cid, "title": title,
        "verdict": verdict, "holds": result.holds, "summary": result.summary,
        "relationship": relationship, "fit": round(fit, 3),
        "residue": residue,
        "winning_witness": result.winning_witness,
        "counterexample": result.counterexample,
    }


@router.post("/where-it-holds")
async def where_it_holds(request: AgonInverseRequest):
    """The inverse pivot: in what domain does G hold? (non-mutating, nothing asserted)

    Ranges the peel across candidate models — the curated examples and the corpus
    UoDs — and ranks them by how G relates to each: **holds** (at home / a theorem),
    **partial** (some of G at home; the residue is its contribution), **independent**,
    or **contradicts**. Abductive context-retrieval (docs/DOMAIN_ORACLE_AND_M.md §7).
    """
    try:
        from agon_models import list_example_models

        if not (request.proposal_egif or "").strip():
            return ApiResponse(success=False, error={
                "code": "NO_PROPOSAL", "message": "Provide a proposal_egif (the graph G)."})
        g_egi = parse_egif(request.proposal_egif.strip())
        g_consts = {v.id: v.label for v in g_egi.V if not v.is_generic and v.label}
        g_atoms = _g_sheet_atoms(g_egi)

        candidates = []  # (kind, id, title, model_egif, closed)
        if request.include_examples:
            for e in list_example_models():
                candidates.append(("example", e.id, e.title, e.model_egif, e.closed))
        if request.include_corpus:
            try:
                for entry in _get_tomos().list_uods()[: request.limit]:
                    uid = entry.get("uod_id") or entry.get("id")
                    if not uid:
                        continue
                    uod = _get_tomos().load_uod(uid, attest=False)  # candidate M read as data
                    if uod is not None and uod.current_egi is not None:
                        candidates.append(("corpus", uid,
                                           entry.get("name") or entry.get("title") or uid,
                                           generate_egif(uod.current_egi), request.closed))
            except Exception:
                pass  # corpus sweep is best-effort

        results = []
        for kind, cid, title, model_egif, closed in candidates:
            try:
                results.append(_candidate_fit(
                    kind, cid, title, model_egif, closed, g_egi, g_consts,
                    g_atoms, request.materialize))
            except Exception:
                continue  # a malformed candidate model shouldn't sink the sweep

        rank = {"holds": 0, "partial": 1, "independent": 2, "contradicts": 3}
        results.sort(key=lambda r: (rank.get(r["relationship"], 9), -r["fit"]))
        return ApiResponse(success=True, data={
            "proposal_egif": request.proposal_egif.strip(),
            "materialized": request.materialize,
            "results": results,
            "counts": {k: sum(1 for r in results if r["relationship"] == k)
                       for k in ("holds", "partial", "independent", "contradicts")},
        })
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "INVERSE_ERROR", "message": str(exc), "type": type(exc).__name__})


@router.post("/interpret")
async def interpret_standalone(request: AgonModelTestRequest):
    """A standalone inning: choose M, test G — *given M, then G* — no contest needed.

    The simplest path to the interpretation register: resolve the chosen model M
    (raw facts or a corpus UoD), peel the proposal G against it, and return the
    verdict, the outside-in transcript, the deciding evidence, and the disposition
    taxonomy annotated by the outcome. Nothing is asserted or persisted.
    """
    try:
        model_egif = _resolve_model_egif(request.model_egif, request.model_uod)
        if not (request.proposal_egif or "").strip():
            return ApiResponse(success=False, error={
                "code": "NO_PROPOSAL", "message": "Provide a proposal_egif (the graph G)."})
        return ApiResponse(success=True, data=_interpret_payload(
            model_egif, request.proposal_egif.strip(), request.closed, request.materialize))
    except ValueError as exc:
        return ApiResponse(success=False, error={"code": "INVALID_MODEL", "message": str(exc)})
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "INTERPRET_ERROR", "message": str(exc), "type": type(exc).__name__})


# --------------------------------------------------------------------------- #
# Interpretation register — peel G against M (the inning's part 2)            #
# docs/GENERATION_AND_TESTING.md                                              #
# --------------------------------------------------------------------------- #


@router.post("/games/{game_id}/set-model")
async def set_model(game_id: str, request: AgonSetModelRequest):
    """Choose / change the model M for the interpretation register (part 1).

    M is the reference world G is peeled against; ``closed`` sets its regime
    (asserted-complete → a miss is FALSE; sampled → a miss is UNKNOWN).  This does
    not touch the transformation game's state.
    """
    try:
        manager = get_agon_session_manager()
        game = manager.get_game(game_id)
        if game is None:
            return ApiResponse(
                success=False,
                error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
            )

        model_egif = request.model_egif
        if request.base_source and request.base_source.startswith("uod:"):
            uod_id = request.base_source[len("uod:"):]
            uod = _get_tomos().load_uod(uod_id, attest=False)  # M read as data
            if uod is None or uod.current_egi is None:
                return ApiResponse(
                    success=False,
                    error={"code": "INVALID_SETUP",
                           "message": f"UoD '{uod_id}' not found or has no current EGI."},
                )
            from egif_generator_dau import generate_egif
            model_egif = generate_egif(uod.current_egi)

        if not model_egif:
            return ApiResponse(
                success=False,
                error={"code": "NO_MODEL",
                       "message": "Provide model_egif or base_source 'uod:<id>'."},
            )

        game.model_egif = model_egif.strip()
        game.model_closed = request.closed
        return ApiResponse(success=True, data={
            "game_id": game_id,
            "model_egif": game.model_egif,
            "closed": game.model_closed,
        })
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "SET_MODEL_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


@router.post("/games/{game_id}/interpret")
async def interpret(game_id: str, request: AgonInterpretRequest):
    """Peel the proposal G against the model M — the inning's part 2 (non-mutating).

    Runs the semantic game (``semantic_game.evaluate``): reads G outside-in, asking
    the model M (a ``CorpusOracle``) at each negation-free layer, and returns the
    three-valued verdict (TRUE / FALSE / UNKNOWN), the outside-in transcript, and
    the deciding evidence (``winning_witness`` / ``counterexample``).  The
    disposition taxonomy is returned annotated by the verdict (part 3) — a hint,
    never a filter; nothing auto-asserts and the game state is untouched.
    """
    try:
        manager = get_agon_session_manager()
        game = manager.get_game(game_id)
        if game is None:
            return ApiResponse(
                success=False,
                error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
            )

        model_egif = request.model_egif or game.model_egif
        proposal_egif = request.proposal_egif or game.proposal_egif
        closed = request.closed if request.closed is not None else game.model_closed

        if not model_egif or not proposal_egif:
            return ApiResponse(
                success=False,
                error={"code": "NEEDS_M_AND_G",
                       "message": ("Interpretation needs a separate model M and "
                                   "proposal G. Frame the game with model_egif + "
                                   "proposal_egif, or call set-model first.")},
            )

        data = _interpret_payload(model_egif, proposal_egif, closed,
                                  bool(request.materialize))
        data["game_id"] = game_id
        return ApiResponse(success=True, data=data)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "INTERPRET_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


# --------------------------------------------------------------------------- #
# Agonothetes disposition                                                     #
# --------------------------------------------------------------------------- #


@router.post("/games/{game_id}/disposition")
async def disposition(game_id: str, request: AgonDispositionRequest):
    """Apply the Agonothetes' chosen disposition to a finished contest.

    This is the regime-1 → regime-2 boundary for Agon — but, unlike
    Ergasterion's single promotion, it is an *open* choice from the
    outcome taxonomy.  An asserting disposition writes a corpus record
    (firing §3.3 on the asserted state before any disk write); a
    non-asserting one records the judgment on the episode only.  Nothing
    auto-asserts.
    """
    try:
        manager = get_agon_session_manager()
        game = manager.get_game(game_id)
        if game is None:
            return ApiResponse(
                success=False,
                error={"code": "GAME_NOT_FOUND", "message": f"Game '{game_id}' not found."},
            )

        result = apply_disposition(
            game,
            disposition_key=request.disposition,
            tomos=_get_tomos(),
            target_uod_id=request.target_uod_id,
            name=request.name,
            description=request.description,
            authors=request.authors,
            tags=request.tags,
            notes=request.notes,
        )
        return ApiResponse(success=True, data=result)

    except DispositionError as exc:
        return ApiResponse(
            success=False,
            error={"code": "DISPOSITION_ERROR", "message": str(exc)},
        )
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
                   "context": getattr(exc, "context", None)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "DISPOSITION_APPLY_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


# --------------------------------------------------------------------------- #
# Static helpers                                                              #
# --------------------------------------------------------------------------- #


@router.get("/dispositions")
async def list_dispositions():
    """The full outcome taxonomy (mode-independent reference for clients)."""
    from web_api.services.agonothetes import DISPOSITIONS
    return ApiResponse(success=True, data=DISPOSITIONS)


# --------------------------------------------------------------------------- #
# The automated-Grapheus contest (the interpretation register, move-by-move)  #
# --------------------------------------------------------------------------- #
#
# Where /interpret peels G against M in one shot, these routes drive the *same*
# semantic game as an interactive extensive-form contest (docs/AUTOMATED_GRAPHEUS.md):
# the human plays the Graphist (witnesses positive lines, pursues conjuncts the
# defence chooses); the machine plays the Grapheus optimally and auto-advances to
# the next contested Graphist frontier.  Under optimal play the contest's verdict
# equals /interpret's (increment-1 conformance) — the contest is the *experience*
# of that verdict, not a different one.


def _build_contest_oracle(model_egif: str, closed: bool, materialize: bool):
    """Resolve M to a contest oracle (mirrors ``_interpret_payload``'s M-side).

    Returns ``(oracle, materialization_dict_or_None)``.  When ``materialize`` is set,
    M's Horn rules are forward-chained to the least Herbrand model first so the
    Grapheus is armed with the derived facts (the syllogism's conclusion).
    """
    if materialize:
        facts_egi, rep = materialize_egi(parse_egif(model_egif))
        oracle = CorpusOracle([("M", facts_egi)], closed=closed)
        return oracle, _materialization_dict(rep, facts_egi)
    return CorpusOracle.from_egif({"M": model_egif}, closed=closed), None


def _frontier_payload(choice) -> Optional[dict]:
    """The pending contested decision, as options the human Graphist may pick."""
    if choice is None:
        return None
    options = []
    for o in choice.options:
        opt = {"key": o["key"], "label": o["label"], "value": o["value"].value}
        if "is_cut" in o:
            opt["is_cut"] = o["is_cut"]
        options.append(opt)
    return {
        "kind": choice.kind,
        "owner": choice.owner.value,
        "area_id": choice.area_id,
        "depth": choice.depth,
        "polarity": choice.polarity,
        "forced": choice.forced,
        "options": options,
    }


def _contest_payload(session) -> dict:
    """Standard response shape for any endpoint returning a contest state."""
    play = session.contest.play
    return {
        "contest_id": session.contest_id,
        "setup": session.setup,
        "materialization": session.materialization,
        "is_over": play.is_over,
        "summary": play.summary,
        "verdict": play.verdict.value if play.verdict is not None else None,
        "outcome": play.outcome.value if play.outcome is not None else None,
        "conceded": play.conceded,
        "to_move": play.frontier.owner.value if play.frontier is not None else None,
        "frontier": _frontier_payload(play.frontier),
        "bindings": dict(play.bindings),
        "selectives": [
            {"line": s.line, "individual": s.individual, "by": s.by.value,
             "at_polarity": s.at_polarity}
            for s in play.selectives
        ],
        "history": [
            {"kind": m.kind, "owner": m.owner.value, "area_id": m.area_id,
             "depth": m.depth, "detail": m.detail}
            for m in play.history
        ],
        "transcript": list(play.transcript),
        # When the contest is over, surface the disposition taxonomy (verdict-
        # annotated) — the Agonothetes assigns meaning, exactly as in /interpret.
        "available_dispositions": (
            available_dispositions(
                verdict=(play.verdict.value if play.verdict is not None else None))
            if play.is_over else None
        ),
    }


@router.post("/contests")
async def start_contest(request: AgonContestStartRequest):
    """Open an automated-Grapheus contest and advance to the first Graphist move.

    Resolves M (raw EGIF or a corpus UoD, optionally materialized), builds the
    driver over G, and either pauses at the first contested Graphist frontier or —
    when ``autoplay`` is set — plays both sides optimally straight to the verdict.
    """
    try:
        proposal_egif = (request.proposal_egif or "").strip()
        if not proposal_egif:
            raise ValueError("proposal_egif (the graph G) is required.")
        model_egif = _resolve_model_egif(request.model_egif, request.model_uod)
        oracle, materialization = _build_contest_oracle(
            model_egif, request.closed, request.materialize)
        contest = GrapheusContest(parse_egif(proposal_egif), oracle, closed=request.closed)
        if request.autoplay:
            contest.autoplay()
        else:
            contest.start()
        setup = {
            "proposal_egif": proposal_egif,
            "model_egif": model_egif,
            "model_uod": request.model_uod,
            "closed": request.closed,
            "materialize": request.materialize,
        }
        session = get_grapheus_session_manager().create(
            contest=contest, setup=setup, materialization=materialization)
        return ApiResponse(success=True, data=_contest_payload(session))
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "CONTEST_START_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


@router.get("/contests/{contest_id}")
async def get_contest(contest_id: str):
    """The current state of an automated-Grapheus contest."""
    session = get_grapheus_session_manager().get(contest_id)
    if session is None:
        return ApiResponse(
            success=False,
            error={"code": "CONTEST_NOT_FOUND", "message": f"No contest '{contest_id}'."},
        )
    return ApiResponse(success=True, data=_contest_payload(session))


@router.post("/contests/{contest_id}/choose")
async def choose_in_contest(contest_id: str, request: AgonContestChooseRequest):
    """Apply the human Graphist's pick at the current frontier, then auto-advance
    through Grapheus + forced moves to the next contested frontier (or termination)."""
    session = get_grapheus_session_manager().get(contest_id)
    if session is None:
        return ApiResponse(
            success=False,
            error={"code": "CONTEST_NOT_FOUND", "message": f"No contest '{contest_id}'."},
        )
    try:
        session.contest.choose(request.option_key)
        return ApiResponse(success=True, data=_contest_payload(session))
    except ValueError as exc:
        return ApiResponse(
            success=False,
            error={"code": "ILLEGAL_CHOICE", "message": str(exc)},
        )


@router.post("/contests/{contest_id}/concede")
async def concede_contest(contest_id: str):
    """The human Graphist concedes — the contest ends in the Grapheus's favour."""
    session = get_grapheus_session_manager().get(contest_id)
    if session is None:
        return ApiResponse(
            success=False,
            error={"code": "CONTEST_NOT_FOUND", "message": f"No contest '{contest_id}'."},
        )
    try:
        session.contest.concede()
        return ApiResponse(success=True, data=_contest_payload(session))
    except ValueError as exc:
        return ApiResponse(
            success=False,
            error={"code": "CONTEST_OVER", "message": str(exc)},
        )


@router.delete("/contests/{contest_id}")
async def discard_contest(contest_id: str):
    """Discard an automated-Grapheus contest (ephemeral; touches no corpus)."""
    discarded = get_grapheus_session_manager().discard(contest_id)
    return ApiResponse(success=True, data={"discarded": discarded})
