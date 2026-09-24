"""The session serve paths re-attest what they hand out (docket 6f(ii) / 9a).

``CLAUDE.md`` has said that ``correspondence_attestation`` is "hooked into
``layout_service`` so **every served (EGI, drawing) pair is verified**". The
clause-3 audit found that untrue of three paths. One — the deltas path — was
fixed under the author's narrow ruling on 2026-09-22. These are the other two:

* ``POST /api/undo`` / ``POST /api/redo`` return a pair **stored earlier** in the
  session history, rendered with no re-attestation;
* ``GET /api/session/{id}`` renders ``current_layout_dto`` the same way.

Neither was *serving a violation* — they were **stale-attested**, which is a
different and quieter fault: the pair was checked when it was made, so a
mutation of the stored DTO afterwards would reach the client unchallenged. The
check is cheap and both halves are already in hand at the serve point, so the
gap was never about cost.

**Measured before the change, so that "safe" is a reading and not a hope:** real
sessions built from 8 corpus UoDs, undo and redo each exercised, all 16 served
pairs attest cleanly. Both writers into this store — ``diagrams.py`` on create
and ``transformations.py`` on apply — go through ``generate_layout``, which
attests before returning, and **neither passes** ``deltas=``, so no regime-3
geometry ever enters it. Presentation deltas live in the separate Ergasterion
and Agon stores, which do not use this session manager.

These routes had **no test of any kind** before this file — the same shape as
the INS defect, which sat in ``POST /transform/apply`` for exactly as long as
that route had no test.
"""

from __future__ import annotations

import dataclasses

import pytest

from egif_parser_dau import parse_egif

fastapi = pytest.importorskip("fastapi", reason="needs the 'web' extra")
from fastapi.testclient import TestClient  # noqa: E402

from web_api.main import app  # noqa: E402
from web_api.services.layout_service import generate_layout  # noqa: E402
from web_api.services.session_manager import get_session_manager  # noqa: E402

EGIF = '(Human "Socrates") ~[ (Mortal "Socrates") ]'


@pytest.fixture
def client():
    return TestClient(app)


def _live_session() -> tuple[str, object, object]:
    """A session whose stored pair is a real, attested (EGI, DTO)."""
    egi = parse_egif(EGIF)
    dto, _ = generate_layout(egi)
    manager = get_session_manager()
    session_id = manager.create_session(egi, dto)
    # A second state, so there is something to undo back from.
    dto2, _ = generate_layout(egi, previous_layout=dto)
    manager.update_session(session_id, egi, dto2, rule="noop", params={})
    return session_id, egi, dto


def _break_correspondence(dto):
    """Drop one vertex position: the drawing no longer places every element.

    This is §3.3's totality row, the cheapest property to violate without
    inventing geometry that might accidentally still correspond.
    """
    positions = dict(dto.vertex_positions)
    positions.pop(next(iter(positions)))
    return dataclasses.replace(dto, vertex_positions=positions)


def _corrupt_the_store(session_id):
    """Mutate every stored drawing, as a store corruption actually would.

    Two places need it, and finding that out is half of what these tests are
    for: ``current_layout_dto`` is its **own field** on ``Session``, not a view
    onto ``history`` — so ``GET /api/session`` and undo/redo genuinely serve
    from different places, and a fix to one does not cover the other.
    """
    session = get_session_manager().get_session(session_id)
    session.history[:] = [
        (egi, _break_correspondence(dto)) for egi, dto in session.history
    ]
    session.current_layout_dto = _break_correspondence(session.current_layout_dto)


class TestTheServePathsStillWork:
    """The fix must not cost a working route: measured 16/16 clean beforehand."""

    def test_undo_serves_the_previous_state(self, client):
        session_id, _, _ = _live_session()
        body = client.post("/api/undo", json={"session_id": session_id}).json()
        assert body["success"] is True, body.get("error")
        assert body["data"]["svg"], "a drawing was served"

    def test_redo_serves_the_state_again(self, client):
        session_id, _, _ = _live_session()
        client.post("/api/undo", json={"session_id": session_id})
        body = client.post("/api/redo", json={"session_id": session_id}).json()
        assert body["success"] is True, body.get("error")

    def test_the_session_diagram_is_served(self, client):
        session_id, _, _ = _live_session()
        body = client.get(f"/api/session/{session_id}").json()
        assert body["success"] is True, body.get("error")
        assert body["data"]["svg"]


class TestAStaleAttestationIsCaught:
    """The point of the change: a pair mutated after it was attested.

    Each of these passes today *because nothing looks*, which is what makes
    them the falsifiers rather than the coverage.
    """

    def test_undo_refuses_a_stored_pair_that_no_longer_corresponds(self, client):
        session_id, _, _ = _live_session()
        _corrupt_the_store(session_id)
        body = client.post("/api/undo", json={"session_id": session_id}).json()
        assert body["success"] is False, "a stale-attested pair was served"
        assert "correspond" in str(body["error"]).lower()

    def test_redo_refuses_a_stored_pair_that_no_longer_corresponds(self, client):
        session_id, _, _ = _live_session()
        client.post("/api/undo", json={"session_id": session_id})
        _corrupt_the_store(session_id)
        body = client.post("/api/redo", json={"session_id": session_id}).json()
        assert body["success"] is False, "a stale-attested pair was served"
        assert "correspond" in str(body["error"]).lower()

    def test_the_session_diagram_refuses_a_pair_that_no_longer_corresponds(self, client):
        session_id, _, _ = _live_session()
        _corrupt_the_store(session_id)
        body = client.get(f"/api/session/{session_id}").json()
        assert body["success"] is False, "a stale-attested pair was served"
        assert "correspond" in str(body["error"]).lower()
