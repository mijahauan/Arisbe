"""
Tests for the Agon (arena) web routes — the Endoporeutic Game as a route.

Agon is the *contest* mode in the Organon / Ergasterion / Agon trio.
Unlike Ergasterion's solo chain, an Agon session records a **dialogical
episode**: a contest between the Graphist (proposal G) and the Grapheus
(model M), with the **Agonothetes** assigning meaning afterward via an
*open* choice from the outcome taxonomy (deduction / induction /
abduction; assert / revise / fork / conjecture / reject).  See
``docs/ENDOPOREUTIC_GAME_GUIDE.md`` and Pietarinen 2006.

V1 is a thin, flexible slice (CURRENT_PLAN.md): hot-seat (one user drives
both roles), open disposition, nothing auto-asserts.  This file pins the
contract:

1. **Start** — raw initial_egif; M/G frame ``~[ M ~[ G ] ]``; invalid setup
   refused; the payload carries Task-1 introspection + legal_areas + role.
2. **Move** — a legal move advances the dialogical episode and flips the
   player; an out-of-territory move is refused with the engine's message;
   a move with no target_area is refused.
3. **Concede** — ends the contest and surfaces the disposition taxonomy.
4. **Disposition (open)** — a non-asserting choice records a judgment with
   no corpus write; an asserting choice without a target id is refused;
   an asserting choice persists the contest as a corpus record whose
   chain ``load_chain`` round-trips; §3.3 refusal at that boundary aborts
   cleanly with nothing on disk.
5. **Lifecycle/refs** — unknown game id refused; HTML served; taxonomy
   listed.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tomos_service
from layout_dto import LayoutDTO
from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import agon as agon_route
from web_api.services.agon_session_manager import AgonSessionManager


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

# A simple beta frame: "every human is mortal", goal "Mortal".
FRAME = "~[ (Human *x) ~[ (Mortal x) ] ]"
GOAL = "(Mortal *y)"


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def fresh_agon(monkeypatch):
    """Reset the Agon session-manager singleton so tests are independent."""
    manager = AgonSessionManager()
    monkeypatch.setattr(agon_route, "get_agon_session_manager", lambda: manager)
    return manager


@pytest.fixture
def isolated_tomos(tmp_path, monkeypatch):
    """Point the Agon route's TomosService at a tmp dir, seeded with one UoD."""
    tmp_tomos = tmp_path / "tomos"
    tmp_tomos.mkdir(parents=True)
    fresh = TomosService(tmp_tomos)

    real = TomosService(TOMOS_ROOT)
    uod_ids = [u["uod_id"] for u in real.list_uods()]
    seed_candidates = ["alpha_man_mortal", "peirce_modus_ponens"]
    seed_id = next((c for c in seed_candidates if c in uod_ids), uod_ids[0])
    fresh.save_uod(real.load_uod(seed_id))

    monkeypatch.setattr(agon_route, "_tomos_service", fresh)
    return {"service": fresh, "seed_id": seed_id, "tomos_root": tmp_tomos}


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _start(client, **payload):
    body = client.post("/agon/games", json=payload).json()
    return body


def _sheet_id(data):
    areas = data["introspection"]["areas"]
    return next(a for a, rec in areas.items() if rec["is_sheet"])


def _play_one_dc_plus(client, data):
    """Apply a DC+ (allowed for both players) on the sheet; return new data."""
    gid = data["game_id"]
    body = client.post(
        f"/agon/games/{gid}/move",
        json={"rule": "DC+", "parameters": {"selected_elements": [], "target_area": _sheet_id(data)}},
    ).json()
    return body


# --------------------------------------------------------------------------- #
# 1. Start                                                                     #
# --------------------------------------------------------------------------- #


def test_start_raw_initial_carries_introspection_and_role(client, fresh_agon):
    body = _start(client, initial_egif=FRAME, goal_egif=GOAL, first_player="Proposer")
    assert body["success"] is True, body.get("error")
    d = body["data"]
    assert d["game_id"]
    assert d["current_player"] == "Proposer"
    assert d["current_role"] == "Graphist"
    assert d["outcome"] == "ongoing"
    assert d["is_over"] is False
    # Task-1 introspection present, with a negative cut interior.
    assert "areas" in d["introspection"] and "elements" in d["introspection"]
    assert any(rec["polarity"] == "negative" for rec in d["introspection"]["areas"].values())
    # Graphist territory = negative areas; legal_areas should be non-empty.
    assert isinstance(d["legal_areas"], list)
    assert d["episode"]["moves"] == []


def test_start_model_proposal_builds_frame(client, fresh_agon):
    body = _start(
        client,
        model_egif="(Human *x) ~[ (Human x) ~[ (Mortal x) ] ]",
        proposal_egif="(Mortal *y)",
    )
    assert body["success"] is True, body.get("error")
    framed = body["data"]["episode"]["setup"]["framed_egif"]
    assert framed.startswith("~[") and framed.rstrip().endswith("]")
    # The proposal is nested one cut deeper than the model.
    assert "(Mortal" in framed


def test_start_invalid_setup_refused(client, fresh_agon):
    body = _start(client, first_player="Proposer")  # no graph at all
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_SETUP"


def test_start_from_corpus_uod_as_model(client, fresh_agon, isolated_tomos):
    body = _start(
        client,
        base_source=f"uod:{isolated_tomos['seed_id']}",
        proposal_egif="(Mortal *y)",
    )
    assert body["success"] is True, body.get("error")
    assert body["data"]["episode"]["setup"]["base_source"].startswith("uod:")


# --------------------------------------------------------------------------- #
# 2. Move                                                                      #
# --------------------------------------------------------------------------- #


def test_move_advances_episode_and_flips_player(client, fresh_agon):
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    assert d["current_role"] == "Graphist"
    body = _play_one_dc_plus(client, d)
    assert body["success"] is True, body.get("error")
    nd = body["data"]
    assert len(nd["episode"]["moves"]) == 1
    move = nd["episode"]["moves"][0]
    assert move["rule"] == "DC+"
    assert move["role"] == "Graphist"          # the player who moved
    assert nd["current_role"] == "Grapheus"    # turn flipped


def test_move_out_of_territory_refused(client, fresh_agon):
    """After Graphist's DC+, the Grapheus (Skeptic) cannot use INS."""
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    after = _play_one_dc_plus(client, d)["data"]
    assert after["current_role"] == "Grapheus"
    body = client.post(
        f"/agon/games/{after['game_id']}/move",
        json={"rule": "INS", "parameters": {"target_area": _sheet_id(after), "egif_content": "(Z *q)"}},
    ).json()
    assert body["success"] is False
    assert body["error"]["code"] == "ILLEGAL_MOVE"


def test_move_without_target_area_refused(client, fresh_agon):
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    body = client.post(
        f"/agon/games/{d['game_id']}/move",
        json={"rule": "DC+", "parameters": {"selected_elements": []}},
    ).json()
    assert body["success"] is False
    assert body["error"]["code"] == "MISSING_TARGET_AREA"


# --------------------------------------------------------------------------- #
# 3. Concede → dispositions surface                                            #
# --------------------------------------------------------------------------- #


def test_concede_ends_game_and_surfaces_dispositions(client, fresh_agon):
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    body = client.post(f"/agon/games/{d['game_id']}/concede").json()
    assert body["success"] is True
    nd = body["data"]
    assert nd["is_over"] is True
    assert nd["winner"] == "Skeptic"  # Graphist (first to move) conceded
    assert "available_dispositions" in nd
    keys = {x["key"] for x in nd["available_dispositions"]}
    assert {"theorem_registration", "abductive_hypothesis", "open_conjecture"} <= keys


# --------------------------------------------------------------------------- #
# 4. Disposition (open Agonothetes choice)                                     #
# --------------------------------------------------------------------------- #


def test_non_asserting_disposition_records_without_corpus_write(client, fresh_agon):
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    gid = d["game_id"]
    client.post(f"/agon/games/{gid}/concede")
    body = client.post(
        f"/agon/games/{gid}/disposition",
        json={"disposition": "open_conjecture", "notes": "interesting"},
    ).json()
    assert body["success"] is True
    assert body["data"]["asserted"] is False
    assert body["data"]["disposition"]["key"] == "open_conjecture"


def test_asserting_disposition_requires_target(client, fresh_agon):
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    gid = d["game_id"]
    client.post(f"/agon/games/{gid}/concede")
    body = client.post(
        f"/agon/games/{gid}/disposition",
        json={"disposition": "theorem_registration"},
    ).json()
    assert body["success"] is False
    assert body["error"]["code"] == "DISPOSITION_ERROR"


def test_asserting_disposition_persists_contest_chain(client, fresh_agon, isolated_tomos):
    """An asserting disposition writes a corpus record whose chain round-trips."""
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    gid = d["game_id"]
    # Play one move so the episode → chain has a step.
    moved = _play_one_dc_plus(client, d)
    assert moved["success"] is True, moved.get("error")
    client.post(f"/agon/games/{gid}/concede")

    target = "agon-contest-v1"
    body = client.post(
        f"/agon/games/{gid}/disposition",
        json={"disposition": "theorem_registration", "target_uod_id": target,
              "name": "Contest result"},
    ).json()
    assert body["success"] is True, body.get("error")
    assert body["data"]["asserted"] is True
    assert body["data"]["asserted_uod_id"] == target
    assert body["data"]["step_count"] == 1
    # The disposition surfaces the standing the asserted graph now carries — a
    # transformation-game episode is a sound chain, so ⛓ derived, with the
    # "correspondence, not truth" non-claim for the Agon UI to show.
    standing = body["data"]["standing"]
    assert standing["key"] == "derived" and standing["glyph"] == "⛓"
    assert "not truth" in standing["non_claim"]

    svc = isolated_tomos["service"]
    assert svc.uod_exists(target)
    chain = svc.load_chain(target)
    assert chain is not None
    assert len(chain.steps) == 1
    # The dialogical role is recorded in the step.
    assert "(Graphist)" in chain.steps[0].rule_name


def test_asserting_disposition_refuses_drifted_drawing_cleanly(
    client, fresh_agon, isolated_tomos, monkeypatch
):
    """§3.3 failure at the asserting boundary aborts with nothing on disk."""
    d = _start(client, initial_egif=FRAME, goal_egif=GOAL)["data"]
    gid = d["game_id"]
    _play_one_dc_plus(client, d)
    client.post(f"/agon/games/{gid}/concede")

    from elk_layout_engine import ELKLayoutEngine

    class _BrokenEngine:
        def generate_layout(self, egi, style, layout_deltas=None):
            real = ELKLayoutEngine().generate_layout(egi, style, layout_deltas)
            if not real.vertex_positions:
                return real
            victim = next(iter(real.vertex_positions))
            return LayoutDTO(
                vertex_positions={k: v for k, v in real.vertex_positions.items() if k != victim},
                predicate_positions=dict(real.predicate_positions),
                cut_bounds=dict(real.cut_bounds),
                ligature_paths=list(real.ligature_paths),
                area_hierarchy={k: set(v) for k, v in real.area_hierarchy.items()},
                viewport_bounds=real.viewport_bounds,
                sheet_id=real.sheet_id,
                style=real.style,
            )

    monkeypatch.setattr(tomos_service, "ELKLayoutEngine", lambda: _BrokenEngine())

    target = "should-not-persist"
    body = client.post(
        f"/agon/games/{gid}/disposition",
        json={"disposition": "theorem_registration", "target_uod_id": target},
    ).json()
    assert body["success"] is False
    assert body["error"]["code"] == "CORRESPONDENCE_VIOLATION"

    uod_dir = isolated_tomos["tomos_root"] / "universes" / target
    assert not uod_dir.exists() or not any(uod_dir.iterdir())
    assert not isolated_tomos["service"].uod_exists(target)


# --------------------------------------------------------------------------- #
# 5. Lifecycle / references                                                    #
# --------------------------------------------------------------------------- #


def test_unknown_game_refused(client, fresh_agon):
    body = client.get("/agon/games/nope").json()
    assert body["success"] is False
    assert body["error"]["code"] == "GAME_NOT_FOUND"


def test_dispositions_taxonomy_listed(client):
    body = client.get("/agon/dispositions").json()
    assert body["success"] is True
    keys = {d["key"] for d in body["data"]}
    # The three modes of inference are represented.
    modes = {d["mode"] for d in body["data"]}
    assert {"deduction", "induction", "abduction"} <= modes
    assert "theorem_registration" in keys


def test_html_served(client):
    resp = client.get("/agon")
    assert resp.status_code == 200
    assert "Agon" in resp.text
