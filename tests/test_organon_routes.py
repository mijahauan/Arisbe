"""
Tests for the Organon (archive) web routes.

Organon is the read-only mode (Organon / Ergasterion / Agon).  These
tests pin down the contract of ``src/web_api/routes/organon.py``:

1. **Corpus listing** — GET ``/organon/uods`` returns every UoD that
   ``TomosService.list_uods`` knows about, in JSON.
2. **UoD detail** — GET ``/organon/uods/{uod_id}`` returns an SVG, a
   serialised LayoutDTO, an EGI summary, and metadata.
3. **§3.3 boundary attestation fires twice** — a single detail request
   passes through two attest hooks:
       (a) ``TomosService.load_uod`` ⟶ ``tomos_service.load_uod(...)``
       (b) ``layout_service.generate_layout`` ⟶
           ``layout_service.generate_layout``
   The test monkeypatches the imported ``attest_correspondence``
   binding in each module to record the ``context`` label and
   asserts both labels are observed.
4. **Malformed routes raise cleanly** — unknown UoD id returns a
   success=False ``ApiResponse`` with an ``UOD_NOT_FOUND`` code, never
   a 500 with a stack trace leak.
5. **Organon index** — GET ``/organon`` serves the HTML viewer.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import correspondence_attestation
import tomos_service
from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import organon
from web_api.services import layout_service


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def client():
    return TestClient(web_main.app)


@pytest.fixture(scope="module")
def corpus_ids():
    return [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]


@pytest.fixture
def sample_uod_id(corpus_ids):
    """Prefer peirce_modus_ponens (a canonical Beta example) when present.

    Falls back to whatever the corpus has first so the suite still runs
    on a slimmer tomos.
    """
    preferred = "peirce_modus_ponens"
    if preferred in corpus_ids:
        return preferred
    assert corpus_ids, "tomos corpus is empty; cannot test Organon detail"
    return corpus_ids[0]


# --------------------------------------------------------------------------- #
# 1. Corpus listing                                                           #
# --------------------------------------------------------------------------- #


def test_list_uods_returns_every_corpus_entry(client, corpus_ids):
    """GET /organon/uods enumerates the full tomos corpus."""
    response = client.get("/organon/uods")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    returned = {item["uod_id"] for item in body["data"]}
    assert returned == set(corpus_ids), (
        f"Organon listing missing UoDs: {set(corpus_ids) - returned}; "
        f"extras: {returned - set(corpus_ids)}"
    )


def test_list_uods_entries_carry_archive_metadata(client):
    """Each list entry exposes the fields the archive UI needs."""
    response = client.get("/organon/uods")
    body = response.json()
    assert body["success"] is True
    assert body["data"], "tomos corpus is empty"
    sample = body["data"][0]
    for required in (
        "uod_id",
        "name",
        "category",
        "uod_type",
        "is_static",
        "created",
        "last_modified",
        "authors",
        "tags",
    ):
        assert required in sample, f"missing field on Organon list entry: {required}"


# --------------------------------------------------------------------------- #
# 2. UoD detail                                                               #
# --------------------------------------------------------------------------- #


def test_uod_detail_returns_drawing_and_metadata(client, sample_uod_id):
    """GET /organon/uods/{id} returns svg + layout_dto + metadata + summary."""
    response = client.get(f"/organon/uods/{sample_uod_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True, body.get("error")
    data = body["data"]

    assert data["uod_id"] == sample_uod_id
    assert isinstance(data["svg"], str) and data["svg"].startswith("<")
    assert "vertex_positions" in data["layout_dto"]
    assert "cut_bounds" in data["layout_dto"]
    assert "ligature_paths" in data["layout_dto"]
    assert "sheet_id" in data["layout_dto"]

    summary = data["egi_summary"]
    assert {"vertex_count", "edge_count", "cut_count"} <= set(summary.keys())

    meta = data["metadata"]
    assert meta["uod_id"] == sample_uod_id
    assert "category" in meta
    assert "created" in meta and "last_modified" in meta


# --------------------------------------------------------------------------- #
# 3. Both §3.3 attestation hooks fire on a detail request                     #
# --------------------------------------------------------------------------- #


def test_uod_detail_fires_both_attestation_hooks(
    client, sample_uod_id, monkeypatch
):
    """A single GET /organon/uods/{id} attests at load AND render boundaries.

    Records each call's ``context`` label so we can prove both
    boundary events ran for one user-visible request — the load-time
    hook in ``tomos_service`` and the render-time hook in
    ``layout_service``.  This pins the "no drawing leaves the system
    without being §3.3-checked twice" property end-to-end.
    """
    observed_contexts = []

    real_attest = correspondence_attestation.attest_correspondence

    def _spy(egi, dto, *, context=None):
        observed_contexts.append(context)
        return real_attest(egi, dto, context=context)

    # Each call site imported the function by name into its own
    # module — patch both module-level bindings, not just the
    # source.
    monkeypatch.setattr(tomos_service, "attest_correspondence", _spy)
    monkeypatch.setattr(layout_service, "attest_correspondence", _spy)

    # Bypass the route-module's singleton so the patched tomos_service
    # rebuilds rather than handing back a cached service that closed
    # over the un-patched function reference.  (The cached service is
    # safe to reset for the test — it is just a memoised constructor.)
    monkeypatch.setattr(organon, "_tomos_service", None)

    response = client.get(f"/organon/uods/{sample_uod_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True, body.get("error")

    load_ctxs = [c for c in observed_contexts if c and "tomos_service.load_uod" in c]
    render_ctxs = [c for c in observed_contexts if c and "layout_service.generate_layout" in c]

    assert load_ctxs, (
        f"load-boundary attestation hook did not fire on /organon/uods/{sample_uod_id}; "
        f"observed contexts: {observed_contexts}"
    )
    assert render_ctxs, (
        f"render-boundary attestation hook did not fire on /organon/uods/{sample_uod_id}; "
        f"observed contexts: {observed_contexts}"
    )


# --------------------------------------------------------------------------- #
# 4. Malformed routes                                                         #
# --------------------------------------------------------------------------- #


def test_uod_detail_unknown_id_returns_clean_error(client):
    """An unknown UoD id is reported as UOD_NOT_FOUND, not a 500."""
    response = client.get("/organon/uods/this-uod-does-not-exist")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UOD_NOT_FOUND"


def test_uods_path_without_id_lists_corpus(client):
    """``/organon/uods`` is the listing route; no id segment is needed."""
    response = client.get("/organon/uods")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_unknown_organon_subpath_is_not_swallowed_by_static(client):
    """A bogus ``/organon/foo`` path is a 404 (the route table refuses it)."""
    response = client.get("/organon/foo")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# 4b. Diachronic chain playback                                               #
# --------------------------------------------------------------------------- #


def test_chain_playback_returns_ordered_frames_for_a_worked_proof(client):
    """A UoD with a persisted chain plays through as base + one frame per step.

    ``theorem_praeclarum`` is the 7-step Praeclarum exemplar; its chain route
    must return 8 frames (base + 7), each carrying a rendered drawing and a
    linear form, in order, with the step frames naming their rule.
    """
    response = client.get("/organon/uods/theorem_praeclarum/chain")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["has_chain"] is True
    assert data["step_count"] == 7
    frames = data["frames"]
    assert len(frames) == 8
    # Frame 0 is the base; the rest are steps in order.
    assert frames[0]["kind"] == "base"
    assert [f["index"] for f in frames] == list(range(8))
    assert [f["kind"] for f in frames[1:]] == ["step"] * 7
    assert [f["rule"] for f in frames[1:]] == [
        "DC+", "INS", "IT+", "INS", "IT+", "IT-", "DC-"
    ]
    # Every frame carries a drawing it could play, attested at render.
    for f in frames:
        assert f["svg"] and "<svg" in f["svg"]
        assert "forms" in f["linear_forms"]
    # Step frames carry the readable "<peirce label>: <note>" annotation.
    assert frames[1]["annotation"] and "double cut" in frames[1]["annotation"]


def test_chain_playback_absent_for_synchronic_uod(client, sample_uod_id):
    """The synchronic majority of the corpus carries no chain — the route
    reports ``has_chain: False`` with no frames, not an error."""
    response = client.get(f"/organon/uods/{sample_uod_id}/chain")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["has_chain"] is False
    assert body["data"]["frames"] == []


def test_uod_detail_honors_view_style(client):
    """A UoD can be *viewed* in any style directly (not only via export).

    The Peirce style draws cuts as ovals/hand-drawn (``<path>``) where the Dau
    default uses rounded rectangles — so the styled render differs and §3.3
    still attests (no error)."""
    base = client.get("/organon/uods/peirce_modus_ponens")
    styled = client.get("/organon/uods/peirce_modus_ponens?style=peirce-authentic@1.0")
    assert base.status_code == 200 and styled.status_code == 200
    base_svg = base.json()["data"]["svg"]
    peirce_svg = styled.json()["data"]["svg"]
    assert base_svg != peirce_svg
    assert "<path" in peirce_svg  # oval / hand-drawn cuts


def test_uod_detail_honors_layout_engine(client):
    """A UoD can be *viewed* under either layout projection from the archive —
    ``engine=tension`` (the ligature-first reading) differs from the ELK default
    and still attests (§3.3 at the render boundary; tension falls back to ELK on
    anything it can't lay out, so the request never fails).  Uses a branch graph
    whose tension layout genuinely differs from ELK's two columns."""
    base = client.get("/organon/uods/dau_2006_p112_ligature")
    tens = client.get("/organon/uods/dau_2006_p112_ligature?engine=tension")
    assert base.status_code == 200 and tens.status_code == 200
    assert base.json()["success"] and tens.json()["success"]
    assert base.json()["data"]["svg"] != tens.json()["data"]["svg"]


def test_chain_playback_honors_view_style(client):
    """The chain player frames can be rendered in a chosen style too."""
    resp = client.get("/organon/uods/theorem_praeclarum/chain?style=peirce-authentic@1.0")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_chain"]
    assert any("<path" in f["svg"] for f in data["frames"])


def test_chain_playback_unknown_id_is_clean_error(client):
    """An unknown UoD id on the chain route is reported, not a 500."""
    response = client.get("/organon/uods/no-such-uod/chain")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UOD_NOT_FOUND"


# --------------------------------------------------------------------------- #
# 5. Organon HTML viewer                                                      #
# --------------------------------------------------------------------------- #


def test_organon_index_serves_html(client):
    """GET /organon returns the read-only viewer page."""
    response = client.get("/organon")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "Arisbe Organon" in html
    assert "organon-uod-list" in html
    # Read-only mode marker — transformation UI must not bleed in.
    assert "mode-btn" not in html
