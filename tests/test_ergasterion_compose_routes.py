"""
Tests for the Ergasterion composition workflow routes (spec
``docs/COMPOSITION_WORKFLOW_SPEC.md``, step 2 of §6).

The workshop now has three phases and two fixings:

    COMPOSE → [① fix the graph] → DERIVE → [② fix the chain] → DISPOSE

This file pins down the route contract:

1. **Phase at open** — an empty sheet opens *composing*; a corpus UoD's
   EGI opens *deriving* (it is already a fixed graph).
2. **Palette actions** — ``POST /compose`` lands each action as a typed
   ``compose.<action>`` chain step whose parameters carry the generated
   ids (replayable); refusals (Dau context condition, unknown ids,
   unknown action) come back as ``COMPOSE_REFUSED``.
3. **Gate ①** — ``/fix-graph`` flips composing → deriving, recorded as a
   ``compose.fix_graph`` identity step; after it ``/compose`` is refused
   with 409, before it ``/apply`` is refused with 409 (spec §4.3).
4. **Gate ②** — ``/fix-chain`` flips deriving → sealed; any further
   mutation (compose, apply, either gate again) is a 409.
5. **Fork-before-gate re-opens the clay** — composing from a pre-gate-①
   state forks a new branch whose tip is *composing* again, while the
   fixed line stays fixed (gates belong to a branch, not the session).
6. **Scratch round-trip** — a draft saved with its gate steps reopens in
   the right phase, and the reloaded chain replays exactly
   (``verify_chain_replay``).
7. **The §7 scenario over HTTP** — blank sheet → Human spot → cut →
   Mortal inside → attach across the cut boundary → fix graph → a rule
   → fix chain.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from composition_ops import verify_chain_replay
from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import ergasterion as ergasterion_route
from web_api.services.ergasterion_session_manager import (
    ErgasterionSessionManager,
)


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def manager(monkeypatch):
    """A fresh session manager bound for the whole test."""
    mgr = ErgasterionSessionManager()
    monkeypatch.setattr(
        ergasterion_route, "get_ergasterion_session_manager", lambda: mgr
    )
    return mgr


@pytest.fixture
def isolated_scratch(tmp_path, monkeypatch):
    from web_api.services.scratch_store import ScratchStore

    store = ScratchStore(tmp_path / "scratch")
    monkeypatch.setattr(ergasterion_route, "_scratch_store", store)
    return store


@pytest.fixture
def isolated_tomos(tmp_path, monkeypatch):
    """A tmp corpus seeded with one small real UoD (for uod-base tests)."""
    tmp_tomos = tmp_path / "tomos"
    tmp_tomos.mkdir(parents=True)
    fresh = TomosService(tmp_tomos)
    real_service = TomosService(TOMOS_ROOT)
    uod_ids = [u["uod_id"] for u in real_service.list_uods()]
    seed_candidates = ["alpha_man_mortal", "peirce_modus_ponens"]
    seed_id = next((c for c in seed_candidates if c in uod_ids), uod_ids[0])
    seed_uod = real_service.load_uod(seed_id)
    assert seed_uod is not None
    fresh.save_uod(seed_uod)
    monkeypatch.setattr(ergasterion_route, "_tomos_service", fresh)
    return {"seed_id": seed_id}


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _open(client, base_source: str = "empty_sheet"):
    body = client.post(
        "/ergasterion/sessions", json={"base_source": base_source}
    ).json()
    assert body["success"] is True, body.get("error")
    return body["data"]


def _compose(client, sid, action, parameters=None, from_state_id=None):
    payload = {"action": action, "parameters": parameters or {}}
    if from_state_id is not None:
        payload["from_state_id"] = from_state_id
    return client.post(f"/ergasterion/sessions/{sid}/compose", json=payload)


def _compose_ok(client, sid, action, parameters=None, from_state_id=None):
    resp = _compose(client, sid, action, parameters, from_state_id)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True, body.get("error")
    return body["data"]


def _fix(client, sid, gate: str):
    return client.post(f"/ergasterion/sessions/{sid}/{gate}", json={})


def _apply(client, sid, rule, parameters=None):
    return client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={"rule": rule, "parameters": parameters or {}},
    )


def _assert_phase_refused(resp):
    assert resp.status_code == 409
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "PHASE_REFUSED"
    return body["error"]


# --------------------------------------------------------------------------- #
# 1. Phase at open                                                            #
# --------------------------------------------------------------------------- #


def test_empty_sheet_opens_composing(client, manager):
    data = _open(client)
    assert data["phase"] == "composing"


def test_uod_base_opens_deriving_and_refuses_compose(
    client, manager, isolated_tomos
):
    data = _open(client, f"uod:{isolated_tomos['seed_id']}")
    assert data["phase"] == "deriving"
    err = _assert_phase_refused(
        _compose(client, data["session_id"], "add_cut")
    )
    assert err["phase"] == "deriving"


# --------------------------------------------------------------------------- #
# 2. Palette actions land as typed compose steps                              #
# --------------------------------------------------------------------------- #


def test_compose_records_typed_replayable_steps(client, manager):
    data = _open(client)
    sid = data["session_id"]

    r1 = _compose_ok(client, sid, "add_cut")
    assert r1["chain"]["steps"][-1]["rule_name"] == "compose.add_cut"
    cut_id = r1["compose_result"]["created"]["cut"]
    # The recorded step carries the generated id, so it replays exactly.
    assert r1["chain"]["steps"][-1]["rule_name"].startswith("compose.")
    step = manager.get_session(sid).chain.steps[-1]
    assert step.parameters["cut_id"] == cut_id

    r2 = _compose_ok(
        client, sid, "add_relation", {"name": "P", "context_id": cut_id}
    )
    assert r2["chain"]["steps"][-1]["rule_name"] == "compose.add_relation"
    assert r2["egi_summary"]["edge_count"] == 1
    assert r2["egi_summary"]["vertex_count"] == 1  # placeholder line
    assert r2["egi_summary"]["cut_count"] == 1
    # Linear mirror moves with the canvas.
    assert "P" in r2["linear_forms"]["forms"]["egif"]["text"]


def test_compose_namespaced_action_is_accepted(client, manager):
    data = _open(client)
    r = _compose_ok(client, data["session_id"], "compose.add_line")
    assert r["chain"]["steps"][-1]["rule_name"] == "compose.add_line"
    assert r["egi_summary"]["vertex_count"] == 1


def test_compose_refusals_are_clean(client, manager):
    data = _open(client)
    sid = data["session_id"]

    # Unknown action.
    bad = _compose(client, sid, "sprinkle_glitter").json()
    assert bad["success"] is False
    assert bad["error"]["code"] == "COMPOSE_REFUSED"

    # Dau context condition: a relation in the sheet may not hook a line
    # that lives deeper (inside a cut).
    cut = _compose_ok(client, sid, "add_cut")["compose_result"]["created"]["cut"]
    inner_line = _compose_ok(client, sid, "add_line", {"context_id": cut})[
        "compose_result"
    ]["created"]["vertex"]
    refused = _compose(
        client, sid, "add_relation", {"name": "Q", "hooks": [inner_line]}
    ).json()
    assert refused["success"] is False
    assert refused["error"]["code"] == "COMPOSE_REFUSED"

    # A refusal records no step.
    assert (
        manager.get_session(sid).chain.steps[-1].rule_name == "compose.add_line"
    )


# --------------------------------------------------------------------------- #
# 3 + 4. The two gates                                                        #
# --------------------------------------------------------------------------- #


def test_gate_one_flips_phase_and_guards_both_ways(client, manager):
    data = _open(client)
    sid = data["session_id"]

    # Before gate ①: the six rules are refused (the graph is still clay).
    err = _assert_phase_refused(_apply(client, sid, "DC+"))
    assert err["phase"] == "composing"

    _compose_ok(client, sid, "add_relation", {"name": "P"})
    fixed = _fix(client, sid, "fix-graph")
    assert fixed.status_code == 200
    fd = fixed.json()["data"]
    assert fd["phase"] == "deriving"
    assert fd["chain"]["steps"][-1]["rule_name"] == "compose.fix_graph"
    # The gate is an identity step on the graph.
    assert fd["egi_summary"]["edge_count"] == 1

    # After gate ①: the palette is refused; the rules apply.
    _assert_phase_refused(_compose(client, sid, "add_cut"))
    applied = _apply(client, sid, "DC+", {"selected_elements": []})
    assert applied.status_code == 200
    assert applied.json()["success"] is True

    # Gate ① cannot be crossed twice on one line.
    _assert_phase_refused(_fix(client, sid, "fix-graph"))


def test_gate_two_seals_the_line(client, manager):
    data = _open(client)
    sid = data["session_id"]
    _compose_ok(client, sid, "add_relation", {"name": "P"})

    # Gate ② needs a deriving line.
    _assert_phase_refused(_fix(client, sid, "fix-chain"))

    assert _fix(client, sid, "fix-graph").status_code == 200
    sealed = _fix(client, sid, "fix-chain")
    assert sealed.status_code == 200
    sd = sealed.json()["data"]
    assert sd["phase"] == "sealed"
    assert sd["chain"]["steps"][-1]["rule_name"] == "chain.fix"

    # Sealed: every mutation is refused.
    _assert_phase_refused(_compose(client, sid, "add_cut"))
    err = _assert_phase_refused(_apply(client, sid, "DC+"))
    assert err["phase"] == "sealed"
    _assert_phase_refused(_fix(client, sid, "fix-graph"))
    _assert_phase_refused(_fix(client, sid, "fix-chain"))


# --------------------------------------------------------------------------- #
# 5. Fork-before-gate re-opens the clay                                       #
# --------------------------------------------------------------------------- #


def test_fork_from_pre_gate_state_reopens_composition(client, manager):
    data = _open(client)
    sid = data["session_id"]

    r1 = _compose_ok(client, sid, "add_relation", {"name": "P"})
    pre_gate_state = r1["chain"]["steps"][-1]["to_state_id"]
    assert _fix(client, sid, "fix-graph").status_code == 200
    assert _fix(client, sid, "fix-chain").status_code == 200
    assert manager.get_session(sid).phase == "sealed"

    # Composing from the pre-gate state forks a branch whose tip is clay.
    forked = _compose_ok(
        client, sid, "add_cut", from_state_id=pre_gate_state
    )
    assert forked["phase"] == "composing"
    assert forked["branches"]["count"] == 2
    assert forked["branches"]["active_branch"] == 1
    # The sealed line is intact and still sealed.
    sw = client.post(
        f"/ergasterion/sessions/{sid}/branches/switch", json={"branch_index": 0}
    ).json()
    assert sw["data"]["phase"] == "sealed"


# --------------------------------------------------------------------------- #
# 6. Scratch round-trip + exact replay                                        #
# --------------------------------------------------------------------------- #


def test_scratch_round_trip_preserves_gates_and_replays(
    client, manager, isolated_scratch
):
    data = _open(client)
    sid = data["session_id"]
    cut = _compose_ok(client, sid, "add_cut")["compose_result"]["created"]["cut"]
    _compose_ok(client, sid, "add_relation", {"name": "P", "context_id": cut})
    assert _fix(client, sid, "fix-graph").status_code == 200
    applied = _apply(client, sid, "DC+", {"selected_elements": []})
    assert applied.json()["success"] is True
    assert _fix(client, sid, "fix-chain").status_code == 200

    saved = client.post(
        f"/ergasterion/sessions/{sid}/save-to-scratch",
        json={"name": "composed episode"},
    ).json()
    assert saved["success"] is True, saved.get("error")
    scid = saved["data"]["scratch_id"]

    reopened = client.post(f"/ergasterion/scratch/{scid}/open").json()
    assert reopened["success"] is True, reopened.get("error")
    rd = reopened["data"]
    assert rd["phase"] == "sealed"
    assert [s["rule_name"] for s in rd["chain"]["steps"]] == [
        "compose.add_cut",
        "compose.add_relation",
        "compose.fix_graph",
        "DC+",
        "chain.fix",
    ]

    # The reloaded chain replays end-to-end: compose steps exactly
    # (recorded ids), the rule step up to isomorphism, gates as identity.
    session = manager.get_session(rd["session_id"])
    assert verify_chain_replay(session.chain) == 5


# --------------------------------------------------------------------------- #
# 7. The spec-§7 scenario over HTTP                                           #
# --------------------------------------------------------------------------- #


def test_spec_scenario_human_mortal_episode(client, manager):
    """Blank sheet → Human spot (line minted) → cut → Mortal inside → attach
    Mortal's hook to the Human line across the boundary (legal: enclosing
    area) → ① → a derivation move → ②."""
    data = _open(client)
    sid = data["session_id"]
    assert data["phase"] == "composing"

    human = _compose_ok(client, sid, "add_relation", {"name": "Human"})
    human_line = human["compose_result"]["created"]["placeholders"][0]

    cut = _compose_ok(client, sid, "add_cut")["compose_result"]["created"]["cut"]
    mortal = _compose_ok(
        client, sid, "add_relation", {"name": "Mortal", "context_id": cut}
    )
    mortal_edge = mortal["compose_result"]["created"]["edge"]

    welded = _compose_ok(
        client,
        sid,
        "attach",
        {"edge_id": mortal_edge, "hook_index": 0, "vertex_id": human_line},
    )
    # The placeholder orphan was pruned: one shared line of identity.
    assert welded["egi_summary"]["vertex_count"] == 1
    assert welded["egi_summary"]["edge_count"] == 2
    assert welded["egi_summary"]["cut_count"] == 1
    egif = welded["linear_forms"]["forms"]["egif"]["text"]
    assert "Human" in egif and "Mortal" in egif

    assert _fix(client, sid, "fix-graph").status_code == 200
    applied = _apply(client, sid, "DC+", {"selected_elements": []}).json()
    assert applied["success"] is True, applied.get("error")
    assert _fix(client, sid, "fix-chain").status_code == 200
    assert manager.get_session(sid).phase == "sealed"
