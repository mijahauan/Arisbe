"""
Route contract for the NL→logic front-end (``POST /agon/propose-nl``).

The LLM step is mocked by monkeypatching ``nl_to_logic._default_client`` to a fake client —
so the route's *real* wiring (resolve M → hint with M's signature → propose → reconcile →
peel) is exercised end to end with no network. What the tests pin:

* a well-formed proposal parses, reconciles against M, and returns the peel verdict;
* a predicate M cannot address surfaces as ``vocabulary.out_of_signature`` (vocabulary-miss);
* an ``unmappable`` sentence and a malformed candidate each return ``parsed: false`` with the
  reason — a successful response, not an error (the honest "can't say that here" surface).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient

import nl_to_logic
from web_api import main as web_main

client = TestClient(web_main.app)

TEACHER_M = '(mammal "Rex") (warmblooded "Rex") (mammal "Whale") (warmblooded "Whale")'


@pytest.fixture
def fake_llm(monkeypatch):
    """Install a fake LLM that returns whatever emit_fol payload the test sets."""
    state = {"payload": {}}

    def _client():
        block = SimpleNamespace(type="tool_use", name="emit_fol", input=state["payload"])
        resp = SimpleNamespace(content=[block])
        return SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: resp))

    monkeypatch.setattr(nl_to_logic, "_default_client", _client)
    return state


def _post(nl, **extra):
    body = {"nl": nl, "model_egif": TEACHER_M, "closed": True, **extra}
    return client.post("/agon/propose-nl", json=body).json()


def test_well_formed_proposal_interprets(fake_llm):
    fake_llm["payload"] = {
        "fol": "∀x (mammal(x) → warmblooded(x))",
        "predicates": {"mammal": 1, "warmblooded": 1}, "constants": [], "confidence": "high",
    }
    body = _post("Every mammal is warm-blooded")
    assert body["success"], body
    d = body["data"]
    assert d["parsed"] and d["egif"]
    assert d["vocabulary"]["fully_addressable"]
    assert d["interpretation"]["verdict"] == "true"


def test_vocabulary_miss_surfaced(fake_llm):
    fake_llm["payload"] = {
        "fol": 'flies("Rex")', "predicates": {"flies": 1}, "constants": ["Rex"]}
    d = _post("Rex flies")["data"]
    assert d["parsed"]
    assert d["vocabulary"]["out_of_signature"] == ["flies"]
    assert not d["vocabulary"]["fully_addressable"]
    # still interprets — closed world makes the un-addressable atom FALSE
    assert d["interpretation"]["verdict"] == "false"


def test_unmappable_returns_honest_proposal(fake_llm):
    fake_llm["payload"] = {
        "fol": "", "predicates": {}, "constants": [],
        "unmappable": "deontic 'ought' is outside first-order logic"}
    body = _post("One ought to keep promises")
    assert body["success"]            # not an error — a meaningful outcome
    d = body["data"]
    assert d["parsed"] is False
    assert "deontic" in d["unmappable"]
    assert "interpretation" not in d


def test_malformed_candidate_reported(fake_llm):
    fake_llm["payload"] = {"fol": "mammal(", "predicates": {"mammal": 1}, "constants": []}
    d = _post("broken")["data"]
    assert d["parsed"] is False and d["parse_error"]
    assert "interpretation" not in d


def test_missing_model_is_an_error(fake_llm):
    fake_llm["payload"] = {"fol": 'mammal("Rex")', "predicates": {"mammal": 1}, "constants": ["Rex"]}
    body = client.post("/agon/propose-nl", json={"nl": "Rex is a mammal"}).json()
    assert not body["success"]
    assert body["error"]["code"] == "INVALID_MODEL"
