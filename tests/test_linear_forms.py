"""
Tests for the linear-form view shared across diagram views.

Every view of an EGI's drawing can also show its linear form, in a
selectable notation (EGIF default, CGIF, CLIF, …).  The backing service
``linear_forms`` is the single source of truth, used by the Organon,
Ergasterion, and Agon diagram payloads.  These tests pin the service
shape, its defensive per-format generation, and the presence of the
block in each mode's payload.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from web_api import main as web_main
from web_api.services.linear_forms import (
    default_format,
    linear_formats,
    linear_forms,
)


@pytest.fixture
def client():
    return TestClient(web_main.app)


# --------------------------------------------------------------------------- #
# Service                                                                      #
# --------------------------------------------------------------------------- #


def test_default_is_egif_and_formats_listed():
    assert default_format() == "egif"
    keys = [f["key"] for f in linear_formats()]
    assert keys[0] == "egif"
    assert {"egif", "cgif", "clif"} <= set(keys)


def test_linear_forms_shape_and_egif_renders():
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    lf = linear_forms(egi)
    assert lf["default"] == "egif"
    assert [f["key"] for f in lf["formats"]][0] == "egif"
    forms = lf["forms"]
    assert set(forms.keys()) >= {"egif", "cgif", "clif"}
    # Every entry carries label/ok/text/error.
    for key, entry in forms.items():
        assert set(entry.keys()) == {"label", "ok", "text", "error"}
    # EGIF round-trips for sure; it must render.
    assert forms["egif"]["ok"] is True
    assert forms["egif"]["text"]
    assert "Human" in forms["egif"]["text"]


def test_linear_forms_all_three_render_for_simple_graph():
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    forms = linear_forms(egi)["forms"]
    # A simple alpha/beta graph renders in all three notations.
    for key in ("egif", "cgif", "clif"):
        assert forms[key]["ok"] is True, (key, forms[key]["error"])
        assert forms[key]["text"]


def test_linear_forms_failure_is_isolated(monkeypatch):
    """A failing generator is reported in its own entry, not raised, and
    does not affect the other notations."""
    import web_api.services.linear_forms as lfmod

    def _boom(_egi):
        raise RuntimeError("synthetic CGIF failure")

    # Replace just the CGIF generator in the registry.
    monkeypatch.setitem(lfmod._FORMATS[1], "generator", _boom)
    egi = parse_egif("(Human *x)")
    forms = lfmod.linear_forms(egi)["forms"]
    assert forms["cgif"]["ok"] is False
    assert "synthetic CGIF failure" in forms["cgif"]["error"]
    assert forms["cgif"]["text"] is None
    # EGIF unaffected.
    assert forms["egif"]["ok"] is True


# --------------------------------------------------------------------------- #
# Payload presence in each mode                                                #
# --------------------------------------------------------------------------- #


def _assert_linear_block(block):
    assert block["default"] == "egif"
    assert [f["key"] for f in block["formats"]][0] == "egif"
    assert "egif" in block["forms"]


def test_ergasterion_payload_includes_linear_forms(client):
    opened = client.post(
        "/ergasterion/sessions", json={"base_source": "empty_sheet"}
    ).json()
    assert opened["success"] is True
    data = opened["data"]
    assert "linear_forms" in data
    _assert_linear_block(data["linear_forms"])
    client.delete(f"/ergasterion/sessions/{data['session_id']}")


def test_agon_payload_includes_linear_forms(client):
    body = client.post(
        "/agon/games",
        json={"initial_egif": "~[ (Human *x) ~[ (Mortal x) ] ]"},
    ).json()
    assert body["success"] is True
    data = body["data"]
    assert "linear_forms" in data
    _assert_linear_block(data["linear_forms"])
    # The contest's current state renders as EGIF text.
    assert data["linear_forms"]["forms"]["egif"]["ok"] is True
    client.delete(f"/agon/games/{data['game_id']}")


def test_organon_detail_includes_linear_forms(client):
    listing = client.get("/organon/uods").json()
    assert listing["success"] is True
    uods = listing["data"]
    assert uods, "corpus listing is empty"
    uod_id = uods[0]["uod_id"]
    detail = client.get(f"/organon/uods/{uod_id}").json()
    assert detail["success"] is True
    assert "linear_forms" in detail["data"]
    _assert_linear_block(detail["data"]["linear_forms"])
