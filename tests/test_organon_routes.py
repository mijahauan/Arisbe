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
