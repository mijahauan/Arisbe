"""Route contract for ``POST /transform/apply`` — the engine path, end to end.

This route had **no test at all**, which is why a live defect sat in it: INS
reported success and changed nothing. The route parsed the user's EGIF, handed
the rule a ``selected_subgraph`` of ids belonging to that *parsed* graph, and
the engine's insertion only ever inserted ids literally prefixed
``"new_vertex_"`` or ``"inserted_"`` — so every real id fell through,
``inserted_elements`` stayed empty, and the API answered ``success: true`` over
an unchanged graph. Fixed 2026-09-20 by routing INS through
``rule_interaction.insert_from_egif``, the canonical implementation the
interaction protocol and the Endoporeutic Game engine already share.

The tests below assert on the graph the route actually produces, never on the
success flag alone — the flag was the thing that lied.
"""

from __future__ import annotations

import pytest

from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif

fastapi = pytest.importorskip("fastapi", reason="needs the 'web' extra")
from fastapi.testclient import TestClient  # noqa: E402

from web_api.main import app  # noqa: E402
from web_api.services.session_manager import get_session_manager  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def _session(egif: str) -> tuple[str, object]:
    """A session holding ``egif``; returns (session_id, egi)."""
    egi = parse_egif(egif)
    return get_session_manager().create_session(egi, None), egi


def _apply(client, session_id, rule, **params):
    return client.post("/api/transform/apply", json={
        "session_id": session_id, "rule": rule, "parameters": params,
    }).json()


def _current(session_id) -> str:
    return generate_egif(get_session_manager().get_session(session_id).current_egi)


def test_ins_actually_inserts_the_content_into_a_negative_area(client):
    """The headline: the graph must change, not merely be reported as changed."""
    sid, egi = _session('~[ (Q "b") ]')
    cut = sorted(c.id for c in egi.Cut)[0]
    before = _current(sid)

    body = _apply(client, sid, "INS", egif_content='(P "a")', target_area=cut)

    assert body["success"] is True, body.get("error")
    after = _current(sid)
    assert after != before, (
        f"the route reported success and the graph did not change: {after!r}")
    assert "(P " in after, f"inserted content missing from {after!r}"


def test_ins_into_a_positive_area_is_refused(client):
    """Insertion is weakening under a negation — the sheet is not negative."""
    sid, egi = _session('~[ (Q "b") ]')
    before = _current(sid)

    body = _apply(client, sid, "INS", egif_content='(P "a")', target_area=egi.sheet)

    assert body["success"] is False
    assert _current(sid) == before, "a refused move must not change the graph"


def test_ins_with_invalid_egif_is_refused_before_anything_changes(client):
    sid, _egi = _session('~[ (Q "b") ]')
    before = _current(sid)

    body = _apply(client, sid, "INS", egif_content="(((not egif")

    assert body["success"] is False
    assert body["error"]["code"] == "PARSE_ERROR"
    assert _current(sid) == before


def test_ins_with_no_content_is_refused_rather_than_a_silent_no_op(client):
    """The exact shape of the defect: no content used to read as success."""
    sid, egi = _session('~[ (Q "b") ]')
    cut = sorted(c.id for c in egi.Cut)[0]
    before = _current(sid)

    body = _apply(client, sid, "INS", egif_content="", target_area=cut)

    assert body["success"] is False, (
        "an INS with nothing to insert must refuse, not report success")
    assert _current(sid) == before


def test_dc_plus_wraps_the_sheet(client):
    """A second rule through the same route, so the fix is not INS-shaped luck."""
    sid, egi = _session('(P "a")')
    body = _apply(client, sid, "DC+", target_area=egi.sheet)
    assert body["success"] is True, body.get("error")
    assert _current(sid) == '~[ ~[ (P "a") ] ]'


def test_an_unknown_session_is_reported_not_crashed(client):
    body = _apply(client, "no-such-session", "DC+")
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_NOT_FOUND"
