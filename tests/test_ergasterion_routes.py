"""
Tests for the Ergasterion (workshop) web routes.

Ergasterion is the composition mode in the Organon / Ergasterion /
Agon trio.  Unlike Organon (read-only) and the legacy transformations
route (snapshot-style undo/redo), an Ergasterion session carries a
**Peircean reasoning chain**: a base state (the chosen context) plus
an accumulating sequence of rule applications, each justified by a
Dau rule.  Everything here is regime 1 — drawn but not asserted — so
the §3.3 correspondence invariant is suspended at the corpus-record
boundary.  A graph leaves the workshop for the corpus only by being a
style-only reprojection of an attested graph, or by being tested
through Agon; there is **no direct workshop→corpus route** (the old
``/promote`` was retired 2026-06-06 — see memory
project-mode-contract-ergasterion-output).  The corpus-record §3.3
mechanism itself (``save_uod_with_chain``) is covered by
``tests/test_chain_persistence.py``.

This file pins down the contract:

1. **Session lifecycle** — open with empty_sheet, open with corpus
   UoD, invalid base refused, get/discard endpoints work.
2. **Rule application via RuleInteraction** — a valid rule advances
   the chain; an invalid rule returns the protocol's refusal cleanly.
3. **Chain accumulates** — multiple applies produce a chain whose
   step_count matches.
4. **Regime-1 drafts don't fire the corpus-record §3.3 hook** —
   during ``/apply``, the ``tomos_service.save_uod`` /
   ``tomos_service.load_uod`` boundary contexts are NOT observed in
   the attestation hook (only the per-render
   ``layout_service.generate_layout`` context, which is a separate
   render-time check).
5. **Move-by-move navigation** — a loaded UoD's worked sequence
   hydrates into the session; any state renders on demand.
6. **Branch-on-edit** — applying from an earlier state forks a branch
   (the original line is intact); branches are switchable.
7. **Scratch store** — a workshop line saves to / lists from / reopens
   from / deletes from the regime-1 scratch store (never the corpus).
8. **HTML viewer** — GET /ergasterion serves a workshop page.
"""

import sys
from pathlib import Path
from typing import List

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import correspondence_attestation
from layout_dto import LayoutDTO
import tomos_service
from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import ergasterion as ergasterion_route
from web_api.services import layout_service
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
def isolated_tomos(tmp_path, monkeypatch):
    """Redirect the Ergasterion route's TomosService singleton to a tmp dir.

    Without this, promote endpoints would write into the real corpus.
    We seed the temp tomos with a copy of one real UoD so we have a
    base-state-from-corpus to work with.
    """
    tmp_tomos = tmp_path / "tomos"
    tmp_tomos.mkdir(parents=True)
    fresh = TomosService(tmp_tomos)

    # Seed: load a small real UoD and re-save it into the tmp tomos.
    real_service = TomosService(TOMOS_ROOT)
    uod_ids = [u["uod_id"] for u in real_service.list_uods()]
    # Prefer a deliberately small one
    seed_candidates = ["alpha_man_mortal", "peirce_modus_ponens"]
    seed_id = next((c for c in seed_candidates if c in uod_ids), uod_ids[0])
    seed_uod = real_service.load_uod(seed_id)
    assert seed_uod is not None
    fresh.save_uod(seed_uod)

    # Reset the route's singleton + the session manager so each test
    # starts clean.  Bind a single manager instance so successive
    # calls within the test see the same sessions.
    isolated_manager = ErgasterionSessionManager()
    monkeypatch.setattr(ergasterion_route, "_tomos_service", fresh)
    monkeypatch.setattr(
        ergasterion_route,
        "get_ergasterion_session_manager",
        lambda: isolated_manager,
    )
    return {
        "service": fresh,
        "seed_id": seed_id,
        "tomos_root": tmp_tomos,
        "session_manager": isolated_manager,
    }


@pytest.fixture
def fresh_session_manager(monkeypatch):
    """For tests that don't need an isolated tomos, still reset the manager.

    Sessions persist across tests via a module-level singleton; this
    keeps tests independent.
    """
    fresh = ErgasterionSessionManager()
    monkeypatch.setattr(
        ergasterion_route,
        "get_ergasterion_session_manager",
        lambda: fresh,
    )
    return fresh


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _open_session(client, base_source: str):
    response = client.post(
        "/ergasterion/sessions", json={"base_source": base_source}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True, body.get("error")
    return body["data"]


# --------------------------------------------------------------------------- #
# 1. Session lifecycle                                                        #
# --------------------------------------------------------------------------- #


def test_open_session_with_empty_sheet(client, fresh_session_manager):
    """Opening with empty_sheet returns a session anchored at an empty graph."""
    data = _open_session(client, "empty_sheet")
    assert data["session_id"]
    assert data["base_source"] == "empty_sheet"
    assert data["base_source_uod_id"] is None
    assert data["egi_summary"]["vertex_count"] == 0
    assert data["egi_summary"]["edge_count"] == 0
    assert data["egi_summary"]["cut_count"] == 0
    assert data["chain"]["step_count"] == 0
    assert data["chain"]["initial_state_id"] == data["chain"]["current_state_id"]


def test_open_session_with_corpus_uod(client, isolated_tomos):
    """Opening with uod:<id> uses that UoD's current EGI as the base state."""
    seed_id = isolated_tomos["seed_id"]
    data = _open_session(client, f"uod:{seed_id}")
    assert data["base_source"] == f"uod:{seed_id}"
    assert data["base_source_uod_id"] == seed_id
    assert data["chain"]["step_count"] == 0
    # The base state's drawing was rendered — that means render-time
    # §3.3 attestation passed.  We just sanity-check it's non-trivial.
    assert data["egi_summary"]["vertex_count"] >= 0
    assert isinstance(data["svg"], str) and data["svg"].startswith("<")


# --------------------------------------------------------------------------- #
# Closure preview (2b)                                                        #
# --------------------------------------------------------------------------- #


def test_closure_preview_cut_pulls_in_contents(client, isolated_tomos):
    """Selecting a cut closes to include all its contents (the user's point:
    a cut travels with its enclosed sub-graph)."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    intro = data["introspection"]
    cuts = [eid for eid, e in intro["elements"].items() if e["type"] == "cut"]
    assert cuts, "seed UoD is expected to contain at least one cut"

    def has_direct_contents(cut):
        return any(e.get("area") == cut for e in intro["elements"].values())

    target = next((c for c in cuts if has_direct_contents(c)), cuts[0])
    resp = client.post(
        f"/ergasterion/sessions/{sid}/closure",
        json={"selected_elements": [target]},
    )
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert target in d["closed_subgraph"]
    assert set(d["selection"]).issubset(set(d["closed_subgraph"]))
    if has_direct_contents(target):
        assert len(d["added_elements"]) >= 1  # contents pulled in


def test_closure_preview_empty_selection_is_trivially_closed(client, isolated_tomos):
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    resp = client.post(
        f"/ergasterion/sessions/{sid}/closure", json={"selected_elements": []}
    )
    d = resp.json()["data"]
    assert d["closed_subgraph"] == [] and d["added_elements"] == []
    assert d["is_closed"] is True


def test_closure_preview_unknown_session_is_clean_error(client, fresh_session_manager):
    resp = client.post(
        "/ergasterion/sessions/no-such/closure", json={"selected_elements": []}
    )
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Deiteration-original justification (2c-ii)                                  #
# --------------------------------------------------------------------------- #


def test_deiteration_original_returns_justification_shape(client, isolated_tomos):
    """The IT- justification endpoint returns the governing-original contract
    (found / valid / original_elements / message) without changing state."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    intro = data["introspection"]
    edge = next((eid for eid, e in intro["elements"].items()
                 if e["type"] == "edge"), None)
    resp = client.post(
        f"/ergasterion/sessions/{sid}/deiteration-original",
        json={"selected_elements": [edge] if edge else []},
    )
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert {"found", "valid", "original_elements", "message"}.issubset(d.keys())
    assert isinstance(d["original_elements"], list)


def test_deiteration_original_unknown_session_is_clean_error(client, fresh_session_manager):
    resp = client.post(
        "/ergasterion/sessions/no-such/deiteration-original",
        json={"selected_elements": []},
    )
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_open_session_refuses_invalid_base(client, fresh_session_manager):
    """A bogus base_source returns INVALID_BASE_SOURCE, not a 500."""
    response = client.post(
        "/ergasterion/sessions", json={"base_source": "nonsense"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_BASE_SOURCE"


def test_open_session_with_unknown_uod(client, isolated_tomos):
    """Opening from a non-existent UoD returns UOD_NOT_FOUND cleanly."""
    response = client.post(
        "/ergasterion/sessions", json={"base_source": "uod:does-not-exist"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UOD_NOT_FOUND"


def test_get_session_returns_current_state(client, fresh_session_manager):
    """GET /ergasterion/sessions/{id} re-renders and returns the current state."""
    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    response = client.get(f"/ergasterion/sessions/{sid}")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["session_id"] == sid


def test_discard_session(client, fresh_session_manager):
    """DELETE removes the session; subsequent GET returns SESSION_NOT_FOUND."""
    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    delete_response = client.delete(f"/ergasterion/sessions/{sid}")
    assert delete_response.json()["success"] is True

    get_response = client.get(f"/ergasterion/sessions/{sid}")
    body = get_response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_NOT_FOUND"


# --------------------------------------------------------------------------- #
# 2. Rule application                                                         #
# --------------------------------------------------------------------------- #


def test_apply_dc_plus_on_empty_sheet(client, fresh_session_manager):
    """DC+ with no selection inserts an empty double cut on the sheet.

    This is the easiest happy-path rule application: ``RuleInteraction``
    accepts an empty selection and produces an empty double-cut on the
    sheet.  We use it to verify the apply pipeline works end-to-end
    without needing a real corpus subgraph.
    """
    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    response = client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={"rule": "DC+", "parameters": {"selected_elements": []}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True, body.get("error")

    data = body["data"]
    # A DC+ on empty creates two cuts (outer and inner) and no V/E.
    assert data["egi_summary"]["cut_count"] == 2
    assert data["chain"]["step_count"] == 1
    assert data["chain"]["steps"][0]["rule_name"] == "DC+"
    # The chain's current state advanced past initial.
    assert data["chain"]["initial_state_id"] != data["chain"]["current_state_id"]


def test_apply_unknown_rule(client, fresh_session_manager):
    """An unknown rule name returns UNKNOWN_RULE, not a 500."""
    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    response = client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={"rule": "WHACKY", "parameters": {}},
    )
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNKNOWN_RULE"


def test_apply_invalid_parameters_returns_precondition_failure(
    client, fresh_session_manager
):
    """Invalid parameters surface RuleInteraction's precondition message."""
    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    # DC- requires selecting exactly one cut that contains exactly one
    # inner cut.  On an empty graph, no such cut exists; the protocol
    # refuses cleanly.
    response = client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={
            "rule": "DC-",
            "parameters": {"selected_elements": ["nonexistent-cut-id"]},
        },
    )
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] in (
        "RULE_PRECONDITION_FAILED",
        "RULE_APPLY_FAILED",
    )
    assert body["error"]["rule"] == "DC-"


# --------------------------------------------------------------------------- #
# 3. Chain accumulates                                                        #
# --------------------------------------------------------------------------- #


def test_chain_accumulates_across_multiple_applies(client, fresh_session_manager):
    """Two successive applies leave the session with a 2-step chain."""
    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    # Step 1: DC+ on empty sheet → 2 cuts.
    r1 = client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={"rule": "DC+", "parameters": {"selected_elements": []}},
    )
    assert r1.json()["success"], r1.json().get("error")

    # Step 2: another DC+ on the same sheet → 4 cuts total.
    r2 = client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={"rule": "DC+", "parameters": {"selected_elements": []}},
    )
    body2 = r2.json()
    assert body2["success"], body2.get("error")

    assert body2["data"]["chain"]["step_count"] == 2
    assert [s["rule_name"] for s in body2["data"]["chain"]["steps"]] == ["DC+", "DC+"]
    assert body2["data"]["egi_summary"]["cut_count"] == 4


# --------------------------------------------------------------------------- #
# 4. Regime-1 drafts do NOT fire the corpus-record §3.3 hook                  #
# --------------------------------------------------------------------------- #


def test_apply_does_not_fire_corpus_record_attestation(
    client, fresh_session_manager, monkeypatch
):
    """During /apply, no ``tomos_service.save_uod`` attestation context fires.

    Regime-1 work means the chain is not yet a public corpus record —
    so the save-boundary §3.3 hook must not be triggered by apply.
    The render-time hook (``layout_service.generate_layout``) WILL
    fire because we still render the new state, but that's a separate
    correspondence check and does not constitute corpus assertion.
    """
    observed_contexts: List[str] = []
    real_attest = correspondence_attestation.attest_correspondence

    def _spy(egi, dto, *, context=None):
        observed_contexts.append(context or "")
        return real_attest(egi, dto, context=context)

    monkeypatch.setattr(tomos_service, "attest_correspondence", _spy)
    monkeypatch.setattr(layout_service, "attest_correspondence", _spy)

    opened = _open_session(client, "empty_sheet")
    sid = opened["session_id"]

    observed_contexts.clear()  # ignore open-time render attestation
    response = client.post(
        f"/ergasterion/sessions/{sid}/apply",
        json={"rule": "DC+", "parameters": {"selected_elements": []}},
    )
    assert response.json()["success"], response.json().get("error")

    save_ctxs = [c for c in observed_contexts if "tomos_service.save_uod" in c]
    load_ctxs = [c for c in observed_contexts if "tomos_service.load_uod" in c]
    render_ctxs = [
        c for c in observed_contexts if "layout_service.generate_layout" in c
    ]

    assert not save_ctxs, (
        f"regime-1 apply fired corpus-record save attestation: {save_ctxs}"
    )
    assert not load_ctxs, (
        f"regime-1 apply fired corpus-record load attestation: {load_ctxs}"
    )
    # Render-time attestation is expected — sanity check it ran so we
    # know the spy is wired correctly.
    assert render_ctxs, (
        f"render-time attestation did not fire on apply; spy may be miswired"
    )


# --------------------------------------------------------------------------- #
# Corpus assertion is no longer a workshop route                              #
# --------------------------------------------------------------------------- #
# The direct ``/promote`` route was retired (2026-06-06): a graph reaches the
# corpus only by being tested through Agon or as a style-only reprojection of an
# attested graph (§3.3 attests correspondence, not truth).  The corpus-record
# §3.3 mechanism (``save_uod_with_chain`` refusing a drifted final state with no
# files on disk) is covered by ``tests/test_chain_persistence.py``.  Workshop
# output paths are tested above (move navigation, branch-on-edit, scratch).


# --------------------------------------------------------------------------- #
# HTML viewer                                                                 #
# --------------------------------------------------------------------------- #


def test_ergasterion_index_serves_html(client):
    """GET /ergasterion serves the workshop page (which is the regime-1 UI)."""
    response = client.get("/ergasterion")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Ergasterion" in response.text


# --------------------------------------------------------------------------- #
# Manual Settle ④b — regime-3 presentation touch-up (/adjust)                 #
# --------------------------------------------------------------------------- #


def _adjust(client, sid, body):
    resp = client.post(f"/ergasterion/sessions/{sid}/adjust", json=body)
    assert resp.status_code == 200
    return resp.json()


def test_adjust_move_vertex_is_pure_presentation(client, isolated_tomos):
    """Moving a (sheet) vertex updates only the drawing: the EGI, the chain,
    and the rest of the graph are untouched, and the new position reflects the
    nudge exactly."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    vpos = data["layout_dto"]["vertex_positions"]
    vid, old = next(iter(vpos.items()))
    dx, dy = 37.0, -21.0

    out = _adjust(client, sid, {"operation": "move_vertex", "vertex_id": vid,
                                "dx": dx, "dy": dy})
    assert out["success"] is True, out.get("error")
    d = out["data"]

    new = d["layout_dto"]["vertex_positions"][vid]
    assert new["x"] == pytest.approx(old["x"] + dx)
    assert new["y"] == pytest.approx(old["y"] + dy)

    # Pure presentation: no chain step recorded, EGI summary unchanged.
    assert d["chain"]["step_count"] == data["chain"]["step_count"]
    assert d["egi_summary"] == data["egi_summary"]


def test_adjust_reshape_cut_to_equal_bounds_is_accepted(client, isolated_tomos):
    """A reshape that preserves the bounds is accepted and re-rendered — proves
    the reshape_cut dispatch + attest + render path end-to-end without relying
    on fragile geometry.  (Geometric reshape semantics are pinned in
    tests/test_presentation_ops.py.)"""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    cut_bounds = data["layout_dto"]["cut_bounds"]
    cid, b = next(iter(cut_bounds.items()))

    out = _adjust(client, sid, {"operation": "reshape_cut", "cut_id": cid,
                                "bounds": dict(b)})
    assert out["success"] is True, out.get("error")
    got = out["data"]["layout_dto"]["cut_bounds"][cid]
    for k in ("min_x", "min_y", "max_x", "max_y"):
        assert got[k] == pytest.approx(b[k])
    # Pure presentation: EGI unchanged.
    assert out["data"]["egi_summary"] == data["egi_summary"]


def test_adjust_reshape_that_breaks_correspondence_is_refused(client, isolated_tomos):
    """The attestation backstop: a reshape can satisfy presentation_ops' own
    membership guards yet still break §3.3 (e.g. enlarging a cut so a ligature
    newly crosses it).  attest_and_render catches that and the route refuses
    cleanly — either as a local Regime3Violation or as a correspondence
    violation.  Appearance is free; it may never change the logic."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    cut_bounds = data["layout_dto"]["cut_bounds"]
    intro = data["introspection"]["elements"]

    # A cut with contents on the sheet, grown by a large margin — big enough to
    # sweep across neighbouring geometry (a ligature and/or sibling element).
    cid = next(
        c for c in cut_bounds
        if any(e.get("area") == c for e in intro.values())
    )
    b = cut_bounds[cid]
    big = {"min_x": b["min_x"] - 400, "min_y": b["min_y"] - 400,
           "max_x": b["max_x"] + 400, "max_y": b["max_y"] + 400}

    out = _adjust(client, sid, {"operation": "reshape_cut", "cut_id": cid,
                                "bounds": big})
    assert out["success"] is False
    assert out["error"]["code"] in {"CORRESPONDENCE_VIOLATION", "REGIME3_VIOLATION"}
    # State preserved.
    after = client.get(f"/ergasterion/sessions/{sid}").json()["data"]
    assert after["egi_summary"] == data["egi_summary"]


def test_adjust_reshape_cut_refuses_expelling_contents(client, isolated_tomos):
    """Shrinking a cut to a pinpoint would push its contents out — refused as a
    Regime3Violation (appearance is free, but it may not change the logic)."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    cut_bounds = data["layout_dto"]["cut_bounds"]
    intro = data["introspection"]["elements"]

    # A cut that actually has contents.
    with_contents = next(
        cid for cid in cut_bounds
        if any(e.get("area") == cid for e in intro.values())
    )
    b = cut_bounds[with_contents]
    cx = (b["min_x"] + b["max_x"]) / 2
    cy = (b["min_y"] + b["max_y"]) / 2
    tiny = {"min_x": cx - 1, "min_y": cy - 1, "max_x": cx + 1, "max_y": cy + 1}

    out = _adjust(client, sid, {"operation": "reshape_cut",
                                "cut_id": with_contents, "bounds": tiny})
    assert out["success"] is False
    assert out["error"]["code"] == "REGIME3_VIOLATION"

    # State preserved: a fresh GET still renders the unshrunk graph.
    after = client.get(f"/ergasterion/sessions/{sid}").json()["data"]
    assert after["egi_summary"] == data["egi_summary"]


def test_adjust_unknown_operation_is_clean_error(client, isolated_tomos):
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    out = _adjust(client, sid, {"operation": "teleport_cut"})
    assert out["success"] is False
    assert out["error"]["code"] == "ADJUST_BAD_REQUEST"


def test_adjust_unknown_session_is_clean_error(client, fresh_session_manager):
    resp = client.post(
        "/ergasterion/sessions/no-such/adjust",
        json={"operation": "move_vertex", "vertex_id": "v", "dx": 1, "dy": 1},
    )
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_adjust_records_a_tagged_delta_in_the_payload(client, isolated_tomos):
    """A Settle ④b nudge is now *recorded* (not only applied to the live DTO):
    the session payload carries it as a tagged, replayable delta — the seed of
    persistence and of the delta-as-dataset study path."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    assert data["presentation_deltas"] == []  # none yet

    vid, _old = next(iter(data["layout_dto"]["vertex_positions"].items()))
    out = _adjust(client, sid, {"operation": "move_vertex", "vertex_id": vid,
                                "dx": 25.0, "dy": 10.0})
    deltas = out["data"]["presentation_deltas"]
    assert len(deltas) == 1
    rec = deltas[0]
    assert rec["op"] == "move_vertex"
    assert rec["params"]["vertex_id"] == vid
    # Tagged with the target's structural description (the generalization handle).
    assert rec["target"].get("kind") == "vertex"


def test_recorded_delta_survives_a_full_re_render(client, isolated_tomos):
    """The consumption side end-to-end: after a nudge, GET /sessions/{id}
    rebuilds the layout from scratch (a full ELK pass) yet replays the recorded
    delta over it, so the hand-adjustment is *not* lost to the re-layout."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    sid = data["session_id"]
    vid, old = next(iter(data["layout_dto"]["vertex_positions"].items()))
    dx, dy = 33.0, -18.0

    adjusted = _adjust(client, sid, {"operation": "move_vertex", "vertex_id": vid,
                                     "dx": dx, "dy": dy})
    moved = adjusted["data"]["layout_dto"]["vertex_positions"][vid]

    # Re-render from scratch (no client-supplied geometry).
    rer = client.get(f"/ergasterion/sessions/{sid}").json()
    assert rer["success"] is True, rer.get("error")
    after = rer["data"]["layout_dto"]["vertex_positions"][vid]

    # The delta replayed over the fresh base → same nudged position as the adjust.
    assert after["x"] == pytest.approx(moved["x"])
    assert after["y"] == pytest.approx(moved["y"])
    assert after["x"] == pytest.approx(old["x"] + dx)
    assert after["y"] == pytest.approx(old["y"] + dy)


# --------------------------------------------------------------------------- #
# Move-by-move navigation (load + step through a worked sequence)             #
# --------------------------------------------------------------------------- #


def _seed_chain_uod(isolated_tomos):
    """Build a real 2-step chain (beta modus ponens) and save it into the
    isolated tomos so a workshop can open it as a base with a sequence."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from build_beta_modus_ponens_chain import build_beta_modus_ponens_chain

    chain, uod = build_beta_modus_ponens_chain()
    isolated_tomos["service"].save_uod_with_chain(uod, chain)
    return uod.uod_id, chain


def test_open_uod_with_chain_hydrates_sequence(client, isolated_tomos):
    """Opening a UoD that carries a worked sequence loads the *whole* chain into
    the session (so it can be navigated), not just the final graph."""
    uod_id, chain = _seed_chain_uod(isolated_tomos)
    data = _open_session(client, f"uod:{uod_id}")
    # The session's chain mirrors the persisted sequence (2 moves).
    assert data["chain"]["step_count"] == len(chain.steps) == 2
    assert data["chain"]["initial_state_id"] == chain.initial_state_id
    # Canvas opens at the tip (the final graph).
    assert data["chain"]["current_state_id"] == chain.current_state_id


def test_open_uod_without_chain_starts_empty_sequence(client, isolated_tomos):
    """A synchronic UoD (no persisted chain) still opens with a fresh 0-move
    sequence anchored at its current EGI (unchanged behaviour)."""
    data = _open_session(client, f"uod:{isolated_tomos['seed_id']}")
    assert data["chain"]["step_count"] == 0
    assert data["chain"]["initial_state_id"] == data["chain"]["current_state_id"]


def test_render_any_state_in_sequence(client, isolated_tomos):
    """Each state in the loaded sequence renders on demand — the move-by-move
    navigator — with correct step_index / is_tip and a §3.3-attested drawing."""
    uod_id, chain = _seed_chain_uod(isolated_tomos)
    data = _open_session(client, f"uod:{uod_id}")
    sid = data["session_id"]

    # Base state (index 0) is not the tip.
    init = client.get(
        f"/ergasterion/sessions/{sid}/states/{chain.initial_state_id}"
    ).json()
    assert init["success"] is True, init.get("error")
    assert init["data"]["step_index"] == 0
    assert init["data"]["is_tip"] is False
    assert init["data"]["svg"].startswith("<")

    # The state after the first move.
    s1 = chain.steps[0].to_state_id
    mid = client.get(f"/ergasterion/sessions/{sid}/states/{s1}").json()["data"]
    assert mid["step_index"] == 1
    assert mid["is_tip"] is False

    # The tip.
    tip_id = chain.current_state_id
    tip = client.get(f"/ergasterion/sessions/{sid}/states/{tip_id}").json()["data"]
    assert tip["step_index"] == len(chain.steps)
    assert tip["is_tip"] is True


def test_render_unknown_state_is_clean_error(client, isolated_tomos):
    uod_id, _chain = _seed_chain_uod(isolated_tomos)
    data = _open_session(client, f"uod:{uod_id}")
    sid = data["session_id"]
    resp = client.get(f"/ergasterion/sessions/{sid}/states/no-such-state")
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "STATE_NOT_FOUND"


def test_render_state_unknown_session_is_clean_error(client, fresh_session_manager):
    resp = client.get("/ergasterion/sessions/no-such/states/s0")
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Branch-on-edit (the workshop is editable everywhere)                        #
# --------------------------------------------------------------------------- #


def _apply(client, sid, rule, parameters=None, from_state_id=None):
    body = {"rule": rule, "parameters": parameters or {}}
    if from_state_id is not None:
        body["from_state_id"] = from_state_id
    return client.post(f"/ergasterion/sessions/{sid}/apply", json=body).json()


def test_apply_at_tip_extends_active_line(client, fresh_session_manager):
    """A move applied at the tip extends the active line — no new branch."""
    data = _open_session(client, "empty_sheet")
    sid = data["session_id"]
    r1 = _apply(client, sid, "DC+")["data"]
    assert r1["chain"]["step_count"] == 1
    assert r1["branches"]["count"] == 1
    r2 = _apply(client, sid, "DC+")["data"]
    assert r2["chain"]["step_count"] == 2
    assert r2["branches"]["count"] == 1


def test_apply_from_earlier_state_forks_a_branch(client, fresh_session_manager):
    """Backing up and applying a move forks a new branch; the original line is
    left intact and the new branch becomes active."""
    data = _open_session(client, "empty_sheet")
    sid = data["session_id"]
    r1 = _apply(client, sid, "DC+")["data"]
    s1 = r1["chain"]["steps"][0]["to_state_id"]
    _apply(client, sid, "DC+")  # active line now 2 moves

    forked = _apply(client, sid, "DC+", from_state_id=s1)
    assert forked["success"] is True, forked.get("error")
    fd = forked["data"]
    assert fd["branches"]["count"] == 2
    # The new branch is active and has 2 moves (1 shared prefix + the new one).
    assert fd["branches"]["active_branch"] == 1
    assert fd["chain"]["step_count"] == 2
    # The original line (branch 0) is untouched — still 2 moves.
    assert fd["branches"]["branches"][0]["step_count"] == 2
    assert fd["branches"]["branches"][0]["active"] is False


def test_switch_branch_restores_a_line(client, fresh_session_manager):
    """Switching to another branch makes it active and re-renders its tip."""
    data = _open_session(client, "empty_sheet")
    sid = data["session_id"]
    r1 = _apply(client, sid, "DC+")["data"]
    s1 = r1["chain"]["steps"][0]["to_state_id"]
    _apply(client, sid, "DC+")
    _apply(client, sid, "DC+", from_state_id=s1)  # fork → active = branch 1

    sw = client.post(
        f"/ergasterion/sessions/{sid}/branches/switch", json={"branch_index": 0}
    ).json()
    assert sw["success"] is True
    assert sw["data"]["branches"]["active_branch"] == 0
    assert sw["data"]["chain"]["step_count"] == 2


def test_switch_unknown_branch_is_clean_error(client, fresh_session_manager):
    data = _open_session(client, "empty_sheet")
    sid = data["session_id"]
    resp = client.post(
        f"/ergasterion/sessions/{sid}/branches/switch", json={"branch_index": 9}
    )
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "BRANCH_NOT_FOUND"


def test_apply_from_unknown_state_is_clean_error(client, fresh_session_manager):
    data = _open_session(client, "empty_sheet")
    sid = data["session_id"]
    out = _apply(client, sid, "DC+", from_state_id="no-such-state")
    assert out["success"] is False
    assert out["error"]["code"] == "STATE_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Scratch store (regime-1 holding pen — not the corpus)                       #
# --------------------------------------------------------------------------- #


@pytest.fixture
def isolated_scratch(tmp_path, monkeypatch):
    """Redirect the route's scratch store to a tmp dir, with a fresh manager."""
    from web_api.services.scratch_store import ScratchStore
    store = ScratchStore(tmp_path / "scratch")
    monkeypatch.setattr(ergasterion_route, "_scratch_store", store)
    mgr = ErgasterionSessionManager()
    monkeypatch.setattr(
        ergasterion_route, "get_ergasterion_session_manager", lambda: mgr
    )
    return store


def test_scratch_save_list_open_delete_cycle(client, isolated_scratch):
    """A workshop line saves to scratch, lists, reopens as a session, deletes —
    regime-1 throughout (no §3.3 gate, never the corpus)."""
    data = _open_session(client, "empty_sheet")
    sid = data["session_id"]
    _apply(client, sid, "DC+")
    _apply(client, sid, "DC+")

    saved = client.post(
        f"/ergasterion/sessions/{sid}/save-to-scratch", json={"name": "my draft"}
    ).json()
    assert saved["success"] is True, saved.get("error")
    assert saved["data"]["step_count"] == 2
    scid = saved["data"]["scratch_id"]

    listing = client.get("/ergasterion/scratch").json()["data"]["drafts"]
    assert any(d["scratch_id"] == scid and d["name"] == "my draft" for d in listing)

    reopened = client.post(f"/ergasterion/scratch/{scid}/open").json()
    assert reopened["success"] is True
    assert reopened["data"]["base_source"] == f"scratch:{scid}"
    assert reopened["data"]["chain"]["step_count"] == 2

    deleted = client.delete(f"/ergasterion/scratch/{scid}").json()
    assert deleted["success"] is True
    assert client.get("/ergasterion/scratch").json()["data"]["drafts"] == []


def test_scratch_open_missing_is_clean_error(client, isolated_scratch):
    resp = client.post("/ergasterion/scratch/no-such/open")
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SCRATCH_NOT_FOUND"


def test_scratch_delete_missing_is_clean_error(client, isolated_scratch):
    resp = client.delete("/ergasterion/scratch/no-such")
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SCRATCH_NOT_FOUND"


def test_save_to_scratch_unknown_session_is_clean_error(client, isolated_scratch):
    resp = client.post(
        "/ergasterion/sessions/no-such/save-to-scratch", json={"name": "x"}
    )
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"
