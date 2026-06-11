"""
Tests for the Agon interpretation register (the inning's part 2).

docs/GENERATION_AND_TESTING.md — an inning is: choose M (part 1) → peel G against M
(part 2, the semantic game) → decide what to do with the result (part 3, the
disposition taxonomy annotated by the verdict).  These pin the route wiring:

- A game framed with model_egif + proposal_egif carries M and G for interpretation.
- `POST /agon/games/{id}/interpret` runs the semantic game and returns the verdict,
  transcript, and deciding evidence; the disposition taxonomy comes back annotated.
- Interpretation is non-mutating, nothing auto-asserts, and the five persona innings
  reproduce through the route.
- `set-model` chooses / changes M; open vs closed flips the verdict.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from web_api import main as web_main
from web_api.routes import agon as agon_route
from web_api.services.agon_session_manager import AgonSessionManager


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture(autouse=True)
def fresh_manager(monkeypatch):
    mgr = AgonSessionManager()
    monkeypatch.setattr(agon_route, "get_agon_session_manager", lambda: mgr)
    return mgr


def _new_game(client, model_egif, proposal_egif, closed=False):
    r = client.post("/agon/games", json={
        "model_egif": model_egif,
        "proposal_egif": proposal_egif,
        "model_closed": closed,
    })
    assert r.status_code == 200, r.text
    assert r.json()["success"], r.text
    return r.json()["data"]["game_id"]


def _interpret(client, gid, **overrides):
    r = client.post(f"/agon/games/{gid}/interpret", json=overrides)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"], body
    return body["data"]


# ---------------------------------------------------------------------------
# The five persona innings, through the route
# ---------------------------------------------------------------------------

def test_teacher_theorem_of_the_model(client):
    gid = _new_game(
        client,
        '(mammal "Rex") (warmblooded "Rex") (mammal "Whale") (warmblooded "Whale")',
        '~[ (mammal *x) ~[ (warmblooded x) ] ]', closed=True)
    data = _interpret(client, gid)
    assert data["verdict"] == "true"
    assert data["holds"] is True


def test_student_refutation_names_counterexample(client):
    gid = _new_game(
        client,
        '(seacreature "Whale") (warmblooded "Whale") (seacreature "Cod") (coldblooded "Cod")',
        '~[ (seacreature *x) ~[ (coldblooded x) ] ]', closed=True)
    data = _interpret(client, gid)
    assert data["verdict"] == "false"
    assert data["counterexample"] == {"x": "Whale"}


def test_researcher_independent_is_unknown(client):
    gid = _new_game(
        client,
        '(wetland "Marsh") (sustains "Marsh" "CoastTown") (coastal "CoastTown")',
        '(coastal "CoastTown") (generates_tourism "CoastTown")', closed=False)
    data = _interpret(client, gid)
    assert data["verdict"] == "unknown"


def test_physician_counterexample_is_missing_fact(client):
    gid = _new_game(
        client,
        '(mammal "Biscuit") (mammal "Whale") (warmblooded "Whale")',
        '~[ (mammal *x) ~[ (warmblooded x) ] ]', closed=True)
    data = _interpret(client, gid)
    assert data["verdict"] == "false"
    assert data["counterexample"] == {"x": "Biscuit"}


# ---------------------------------------------------------------------------
# Open vs closed (the logician's horizon)
# ---------------------------------------------------------------------------

def test_open_vs_closed_flips_the_universal(client):
    facts = '(mammal "Rex") (warmblooded "Rex")'
    universal = '~[ (mammal *x) ~[ (warmblooded x) ] ]'
    gid_open = _new_game(client, facts, universal, closed=False)
    gid_closed = _new_game(client, facts, universal, closed=True)
    assert _interpret(client, gid_open)["verdict"] == "unknown"
    assert _interpret(client, gid_closed)["verdict"] == "true"


# ---------------------------------------------------------------------------
# Part 3: dispositions annotated by the verdict (a hint, not a filter)
# ---------------------------------------------------------------------------

def test_dispositions_annotated_but_complete(client):
    gid = _new_game(client, '(dog "Biscuit")', '(dog "Biscuit")', closed=True)
    data = _interpret(client, gid)
    disps = data["available_dispositions"]
    keys = {d["key"] for d in disps}
    # full taxonomy is still present (nothing narrowed away)
    assert {"theorem_registration", "rejection", "new_fact", "open_conjecture"} <= keys
    by_key = {d["key"]: d for d in disps}
    assert by_key["theorem_registration"]["coherent_with_verdict"] is True   # TRUE
    assert by_key["rejection"]["coherent_with_verdict"] is False


def test_false_verdict_marks_revision_dispositions(client):
    gid = _new_game(client, '(dog "Biscuit")', '(cat "Biscuit")', closed=True)
    data = _interpret(client, gid)
    assert data["verdict"] == "false"
    by_key = {d["key"]: d for d in data["available_dispositions"]}
    assert by_key["challenge_to_M"]["coherent_with_verdict"] is True
    assert by_key["rejection"]["coherent_with_verdict"] is True
    assert by_key["theorem_registration"]["coherent_with_verdict"] is False


# ---------------------------------------------------------------------------
# set-model, non-mutation, and error paths
# ---------------------------------------------------------------------------

def test_set_model_then_interpret(client):
    # Frame with a raw initial_egif (no M/G) → interpret needs a model first.
    r = client.post("/agon/games", json={"initial_egif": '~[ (dog "Biscuit") ]'})
    gid = r.json()["data"]["game_id"]
    miss = client.post(f"/agon/games/{gid}/interpret", json={}).json()
    assert miss["success"] is False
    assert miss["error"]["code"] == "NEEDS_M_AND_G"
    # Now choose M and supply G as an override.
    sm = client.post(f"/agon/games/{gid}/set-model",
                     json={"model_egif": '(dog "Biscuit")', "closed": True}).json()
    assert sm["success"], sm
    data = _interpret(client, gid, proposal_egif='(dog "Biscuit")')
    assert data["verdict"] == "true"


def test_interpretation_does_not_mutate_the_game(client):
    gid = _new_game(client, '(dog "Biscuit")', '(dog "Biscuit")', closed=True)
    before = client.get(f"/agon/games/{gid}").json()["data"]
    _interpret(client, gid)
    after = client.get(f"/agon/games/{gid}").json()["data"]
    assert before["move_number"] == after["move_number"]
    assert before["is_over"] == after["is_over"]


def test_interpret_unknown_game(client):
    r = client.post("/agon/games/nope/interpret", json={})
    assert r.json()["error"]["code"] == "GAME_NOT_FOUND"
