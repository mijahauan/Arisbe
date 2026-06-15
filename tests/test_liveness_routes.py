"""Liveness routes — forward-facing provenance surfaced through Organon (+ Agon).

Manifest floor #7: opening a UoD or pressing it into service as a model M is a
*consultation* that keeps the telling alive; retiring is a deliberate, reversible
stance.  These pin the route contract without asserting accumulated counts (the real
store accrues across runs), by redirecting the shared log to a temp file.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import liveness  # noqa: E402
from tomos_service import TomosService  # noqa: E402
from web_api import main as web_main  # noqa: E402

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def client():
    return TestClient(web_main.app)


@pytest.fixture(scope="module")
def uod_id():
    return TomosService(TOMOS_ROOT).list_uods()[0]["uod_id"]


@pytest.fixture
def temp_log(tmp_path, monkeypatch):
    """Redirect the shared liveness log to a throwaway file (the routes resolve
    ``liveness.get_log`` at call time, so this captures both Organon and Agon)."""
    log = liveness.LivenessLog(tmp_path / ".liveness.json")
    monkeypatch.setattr(liveness, "get_log", lambda *a, **k: log)
    return log


def test_detail_records_a_view_and_returns_liveness(client, uod_id, temp_log):
    r = client.get(f"/organon/uods/{uod_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "liveness" in data
    assert data["liveness"]["status"] == "alive"
    assert data["liveness"]["count"] == 1
    # a second open accumulates
    r2 = client.get(f"/organon/uods/{uod_id}")
    assert r2.json()["data"]["liveness"]["count"] == 2


def test_list_carries_liveness_status(client, uod_id, temp_log):
    client.get(f"/organon/uods/{uod_id}")  # make it alive
    rows = client.get("/organon/uods").json()["data"]
    row = next(x for x in rows if x["uod_id"] == uod_id)
    assert row["liveness_status"] == "alive" and row["consult_count"] >= 1
    # an un-consulted row reports unconsulted
    other = next((x for x in rows if x["uod_id"] != uod_id), None)
    if other:
        assert other["liveness_status"] == "unconsulted"


def test_read_liveness_does_not_record(client, uod_id, temp_log):
    client.get(f"/organon/uods/{uod_id}")             # count -> 1 (records a view)
    before = client.get(f"/organon/uods/{uod_id}/liveness").json()["data"]
    after = client.get(f"/organon/uods/{uod_id}/liveness").json()["data"]
    assert before["count"] == after["count"] == 1     # the read route never increments


def test_retire_then_a_view_revives(client, uod_id, temp_log):
    client.get(f"/organon/uods/{uod_id}")             # alive
    r = client.post(f"/organon/uods/{uod_id}/liveness/retire", json={"retired": True})
    assert r.json()["data"]["status"] == "retired"
    # retirement is reversible; re-opening the UoD brings it back to life
    revived = client.get(f"/organon/uods/{uod_id}").json()["data"]["liveness"]
    assert revived["retired"] is False and revived["status"] == "alive"


def test_unknown_uod_liveness_is_unconsulted(client, temp_log):
    r = client.get("/organon/uods/__nope__/liveness")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "unconsulted"


def test_using_a_uod_as_model_M_records_a_consultation(uod_id, temp_log):
    """Agon's model-resolution chokepoint: a corpus UoD pressed into service as the
    model M is consulted (kind ``model``), keeping it alive — manifest floor #7."""
    from web_api.routes import agon
    agon._resolve_model_egif(None, uod_id)   # resolve a corpus UoD to M's EGIF
    s = temp_log.summary(uod_id)
    assert s.kinds.get("model") == 1 and s.status == "alive"
