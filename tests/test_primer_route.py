"""
Tests for the Primer route — the newcomer's "first graph" examples.

``src/web_api/routes/primer.py`` serves the worked first graphs for the in-app
primer (``web_viewer/js/primer.js``, the guided front door to the Field Guide).
Its contract:

1. **Examples are served and drawn** — GET ``/primer/examples`` returns the
   curated first graphs, each with its linear form, plain-English reading, the
   mark it teaches, and a real SVG rendered through ``generate_layout``.
2. **The scroll and the empty cut are present** — the two notation pivots the
   Field Guide turns on (implication = an outer cut; false = an empty cut) are
   in the set, so the primer can demonstrate them.
3. **Each example actually parses + draws** — the served EGIF round-trips
   through the parser and the SVG is non-empty (the picture↔proposition
   correspondence the primer claims is real, not described).
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from web_api.main import app

client = TestClient(app)


def test_examples_served_and_drawn():
    r = client.get("/primer/examples")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    examples = body["data"]["examples"]
    assert len(examples) >= 3
    for ex in examples:
        assert ex["egif"].strip()
        assert ex["meaning"].strip()
        assert ex["teaches"].strip()
        assert ex["svg"] and "<svg" in ex["svg"]


def test_scroll_and_empty_cut_present():
    """The two notation pivots the primer turns on must be in the set."""
    examples = client.get("/primer/examples").json()["data"]["examples"]
    egifs = [ex["egif"] for ex in examples]
    # the scroll (implication = an outer cut, conclusion nested deeper)
    assert any("~[" in e and "Human" in e and "Mortal" in e for e in egifs)
    # the empty cut (false)
    assert any(e.strip() == "~[ ]" for e in egifs)


def test_each_example_parses_and_renders():
    examples = client.get("/primer/examples").json()["data"]["examples"]
    for ex in examples:
        # the served linear form really parses (no error path was taken)
        egi = parse_egif(ex["egif"])
        assert egi is not None
        assert "error" not in ex
        assert ex["svg"].count("<svg") == 1
