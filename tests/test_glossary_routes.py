"""GET /glossary — the term definitions the UI shows on hover (charter P7).

The route parses docs/GLOSSARY.md live, so these tests pin the contract the
hover cards depend on: every term the three modes place a ``data-term`` on
resolves to a non-empty one-line definition with a book anchor, and the
aliases (ligature ↔ line of identity, correspondence ↔ §3.3, regimes,
warrant ↔ standing) land on the same entries.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from web_api import main as web_main


@pytest.fixture()
def client():
    return TestClient(web_main.app)


# Every slug a mode page currently places (plus the plan's minimum set) —
# a missing term here means a dotted underline with no card behind it.
REQUIRED = [
    # abbreviations
    "uod", "egi", "egif", "cgif", "clif", "fopl", "t-box",
    # marks + calculus vocabulary
    "cut", "polarity", "ligature", "line-of-identity", "scroll",
    "closure", "deiteration", "iteration",
    # the game
    "peel", "graphist", "grapheus", "agonothetes", "disposition",
    "horn-rule", "materialize", "closed-world",
    # architecture + floors
    "3.3", "correspondence", "regime-1", "regime-3", "warrant", "standing",
    "recto", "verso", "gate-1", "gate-2", "tomos", "corpus", "dragon",
]


def test_glossary_serves_every_required_term(client):
    body = client.get("/glossary").json()
    assert body["success"] is True
    terms = body["data"]["terms"]
    missing = [t for t in REQUIRED if t not in terms]
    assert not missing, f"glossary is missing UI terms: {missing}"
    for slug in REQUIRED:
        entry = terms[slug]
        assert entry["term"], slug
        assert entry["definition"], slug
        assert len(entry["definition"]) < 400, f"{slug} definition not one-line-card sized"


def test_anchors_are_book_fragment_shaped(client):
    body = client.get("/glossary").json()
    terms = body["data"]["terms"]
    assert body["data"]["book"] == "/book/GLOSSARY.html"
    import re
    for slug in REQUIRED:
        anchor = terms[slug]["anchor"]
        assert re.fullmatch(r"[a-z0-9][a-z0-9.-]*", anchor), (slug, anchor)


def test_aliases_resolve_to_identical_entries(client):
    terms = client.get("/glossary").json()["data"]["terms"]
    assert terms["ligature"] == terms["line-of-identity"]
    assert terms["correspondence"] == terms["3.3"]
    assert terms["standing"] == terms["warrant"]
    assert terms["corpus"] == terms["tomos"]
    assert terms["regime-1"] == terms["the-three-regimes"]


def test_definitions_are_plain_text(client):
    """Markdown chrome (links, bold, backticks) is stripped for the card."""
    terms = client.get("/glossary").json()["data"]["terms"]
    for slug in REQUIRED:
        d = terms[slug]["definition"]
        assert "](" not in d and "**" not in d and "`" not in d, (slug, d)
