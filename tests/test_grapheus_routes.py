"""
Route tests for the automated-Grapheus contest (``/agon/contests/*``).

docs/AUTOMATED_GRAPHEUS.md §9.2 — the start/get/choose/concede routes drive the
``grapheus`` driver as an interactive contest.  The load-bearing route invariant:
a contest played to termination (optimal both sides, ``autoplay``) reaches the same
verdict the one-shot peel ``/agon/interpret`` returns — the contest is the
*experience* of that verdict, not a different one.  Pinned here through HTTP:

- the five persona innings autoplay to the verdict ``/interpret`` gives;
- the real ``skos_core`` model: a derived broaderTransitive fact the Grapheus must
  concede (Graphist wins) once M is materialized;
- the interactive surface — the human Graphist witnesses a line and wins;
- concession ends the inning in the Grapheus's favour;
- ground atoms terminate with no Graphist frontier; unknown contest ids 404.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from web_api import main as web_main
from web_api.routes import agon as agon_route
from web_api.services.grapheus_session_manager import GrapheusSessionManager


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture(autouse=True)
def fresh_manager(monkeypatch):
    mgr = GrapheusSessionManager()
    monkeypatch.setattr(agon_route, "get_grapheus_session_manager", lambda: mgr)
    return mgr


def _ok(response):
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"], body
    return body["data"]


# --------------------------------------------------------------------------- #
# Conformance: autoplay reaches the verdict /interpret gives                   #
# --------------------------------------------------------------------------- #


def test_persona_innings_autoplay_match_interpret(client):
    """Each curated example model: the contest autoplays to /interpret's verdict."""
    examples = _ok(client.get("/agon/models"))["examples"]
    assert len(examples) >= 5
    for ex in examples:
        body = {"model_egif": ex["model_egif"],
                "proposal_egif": ex["sample_proposal"],
                "closed": ex["closed"]}
        peeled = _ok(client.post("/agon/interpret", json=body))["verdict"]
        contest = _ok(client.post("/agon/contests", json={**body, "autoplay": True}))
        assert contest["is_over"]
        assert contest["verdict"] == peeled, (
            f"{ex['id']}: contest {contest['verdict']} != interpret {peeled}\n"
            + "\n".join(contest["transcript"]))
        # The verdict-annotated disposition taxonomy comes back, nothing asserted.
        assert contest["available_dispositions"]


# --------------------------------------------------------------------------- #
# The real model — skos_core's materialised closure                           #
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def skos_theory_egif():
    from domain_model_importer import from_rdf_file
    from egif_generator_dau import generate_egif
    return generate_egif(
        from_rdf_file(ROOT / "corpus" / "ontologies" / "skos_core.ttl").egi)


def test_skos_grapheus_concedes_derived_fact(client, skos_theory_egif):
    """A fact M *derives* (broader ⊑ broaderTransitive, transitive): once M is
    materialized the Grapheus has no defeating move → the Graphist wins."""
    data = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(broaderTransitive "Dog" "Animal")',
        "model_egif": skos_theory_egif,
        "materialize": True,
        "autoplay": True,
    }))
    assert data["outcome"] == "graphist_wins"
    assert data["verdict"] == "true"
    assert data["materialization"]["derived_facts"] >= 1


def test_skos_open_world_independent(client, skos_theory_egif):
    """No path Dog ⊳ Cat, open world → the Grapheus declines → independent."""
    data = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(broaderTransitive "Dog" "Cat")',
        "model_egif": skos_theory_egif,
        "materialize": True,
        "autoplay": True,
    }))
    assert data["outcome"] == "independent"
    assert data["verdict"] == "unknown"


# --------------------------------------------------------------------------- #
# The interactive surface — the human Graphist makes a real choice             #
# --------------------------------------------------------------------------- #


def test_interactive_graphist_witnesses_and_wins(client):
    model = '(dog "Biscuit") (dog "Rex") (good "Rex")'
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog *x) (good x)', "model_egif": model}))
    assert not started["is_over"]
    frontier = started["frontier"]
    assert frontier is not None
    assert frontier["owner"] == "graphist"
    assert frontier["kind"] == "witness"

    rex = next(o["key"] for o in frontier["options"] if o["label"] == "Rex")
    data = _ok(client.post(f"/agon/contests/{started['contest_id']}/choose",
                           json={"option_key": rex}))
    assert data["is_over"]
    assert data["outcome"] == "graphist_wins"
    assert data["bindings"].get("x") == "Rex"


def test_choose_rejects_illegal_option(client):
    model = '(dog "Biscuit") (dog "Rex") (good "Rex")'
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog *x) (good x)', "model_egif": model}))
    r = client.post(f"/agon/contests/{started['contest_id']}/choose",
                    json={"option_key": "nonexistent"})
    body = r.json()
    assert not body["success"]
    assert body["error"]["code"] == "ILLEGAL_CHOICE"


# --------------------------------------------------------------------------- #
# Concession, get, ground atoms, and missing contests                         #
# --------------------------------------------------------------------------- #


def test_concede_hands_the_inning_to_the_grapheus(client):
    model = '(dog "Biscuit") (dog "Rex") (good "Rex")'
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog *x) (good x)', "model_egif": model}))
    cid = started["contest_id"]
    data = _ok(client.post(f"/agon/contests/{cid}/concede"))
    assert data["is_over"]
    assert data["conceded"] is True
    assert data["outcome"] == "grapheus_wins"
    assert data["available_dispositions"]
    # A second concession is refused — the contest is already over.
    r = client.post(f"/agon/contests/{cid}/concede")
    assert r.json()["error"]["code"] == "CONTEST_OVER"


def test_get_contest_round_trips(client):
    model = '(dog "Biscuit")'
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Biscuit")', "model_egif": model}))
    cid = started["contest_id"]
    fetched = _ok(client.get(f"/agon/contests/{cid}"))
    assert fetched["contest_id"] == cid
    assert fetched["is_over"]
    assert fetched["verdict"] == "true"


def test_ground_atom_has_no_graphist_frontier(client):
    """A present ground atom: the Grapheus adjudicates, no Graphist choice → over."""
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Biscuit")', "model_egif": '(dog "Biscuit")'}))
    assert started["is_over"]
    assert started["frontier"] is None
    assert started["outcome"] == "graphist_wins"


def test_missing_contest_404s(client):
    r = client.get("/agon/contests/does-not-exist")
    assert r.json()["error"]["code"] == "CONTEST_NOT_FOUND"


def test_discard_contest(client):
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Biscuit")', "model_egif": '(dog "Biscuit")'}))
    cid = started["contest_id"]
    assert _ok(client.delete(f"/agon/contests/{cid}"))["discarded"] is True
    assert client.get(f"/agon/contests/{cid}").json()["error"]["code"] == "CONTEST_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Increment 4 — the warrant: an asserting disposition mints "withstood Agon"   #
# --------------------------------------------------------------------------- #


@pytest.fixture
def warrant_tomos(tmp_path, monkeypatch):
    """Redirect the Agon route's TomosService to a fresh tmp corpus, so an
    asserting contest disposition writes there and never the real tomos/."""
    from tomos_service import TomosService
    tmp = tmp_path / "tomos"
    tmp.mkdir(parents=True)
    fresh = TomosService(tmp)
    monkeypatch.setattr(agon_route, "_tomos_service", fresh)
    return fresh


def test_won_contest_asserts_warrant_chain(client, warrant_tomos):
    """A Graphist win + an asserting disposition mints the warrant ChainStep: G is
    persisted with the Play as 'withstood Agon' provenance, and §3.3 fires on G."""
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Biscuit")', "model_egif": '(dog "Biscuit")'}))
    assert started["outcome"] == "graphist_wins"
    cid = started["contest_id"]

    data = _ok(client.post(f"/agon/contests/{cid}/disposition", json={
        "disposition": "theorem_registration",
        "target_uod_id": "contest-warrant-1",
        "name": "Biscuit is a dog (withstood Agon)",
    }))
    assert data["asserted"] is True
    assert data["asserted_uod_id"] == "contest-warrant-1"

    # The disposition surfaces the standing G now carries — ⚔ withstood Agon
    # (the fullest regime-2 standing), with the "correspondence, not truth"
    # non-claim, so the Agon UI can show what the contest earned.
    standing = data["standing"]
    assert standing["key"] == "withstood" and standing["glyph"] == "⚔"
    assert "not truth" in standing["non_claim"] or "truth-meter" in standing["non_claim"]

    # The persisted chain carries the warrant step + the Play provenance.
    chain = warrant_tomos.load_chain("contest-warrant-1")
    assert chain is not None and len(chain.steps) == 1
    step = chain.steps[0]
    assert step.rule_name.startswith("Agon warrant")
    assert step.parameters["warrant"] == "withstood_agon"
    assert step.parameters["outcome"] == "graphist_wins"
    assert step.parameters["transcript"]
    # The asserted graph is G itself.
    from egif_parser_dau import parse_egif as _pe
    from eg_navigation import same_graph
    assert same_graph(warrant_tomos.load_uod("contest-warrant-1").current_egi,
                      _pe('(dog "Biscuit")'))


def test_lost_contest_cannot_assert(client, warrant_tomos):
    """A Grapheus win blocks assertion — a lost inning cannot assert G."""
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '~[ (dog "Biscuit") ]', "model_egif": '(dog "Biscuit")'}))
    assert started["outcome"] == "grapheus_wins"
    r = client.post(f"/agon/contests/{started['contest_id']}/disposition", json={
        "disposition": "theorem_registration", "target_uod_id": "should-not-write"})
    body = r.json()
    assert not body["success"]
    assert body["error"]["code"] == "DISPOSITION_ERROR"
    assert not warrant_tomos.uod_exists("should-not-write")


def test_nonasserting_disposition_records_only(client, warrant_tomos):
    """A non-asserting disposition records the judgment; no corpus write."""
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Biscuit")', "model_egif": '(dog "Biscuit")'}))
    data = _ok(client.post(f"/agon/contests/{started['contest_id']}/disposition", json={
        "disposition": "open_conjecture"}))
    assert data["asserted"] is False
    assert data["disposition"]["asserted_uod_id"] is None


def test_asserting_disposition_requires_target_id(client, warrant_tomos):
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Biscuit")', "model_egif": '(dog "Biscuit")'}))
    r = client.post(f"/agon/contests/{started['contest_id']}/disposition", json={
        "disposition": "theorem_registration"})
    assert r.json()["error"]["code"] == "DISPOSITION_ERROR"


def test_independent_inning_can_assert_new_fact(client, warrant_tomos):
    """An independent (UNKNOWN) inning warrants e.g. 'accept as new fact'."""
    started = _ok(client.post("/agon/contests", json={
        "proposal_egif": '(dog "Rex")', "model_egif": '(dog "Biscuit")'}))
    assert started["outcome"] == "independent"
    data = _ok(client.post(f"/agon/contests/{started['contest_id']}/disposition", json={
        "disposition": "new_fact", "target_uod_id": "contest-newfact-1"}))
    assert data["asserted"] is True
    assert warrant_tomos.uod_exists("contest-newfact-1")
