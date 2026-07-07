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
        # browse facets (the corpus-browser shelving dimension + search fields)
        "kind",
        "cited",
        "description",
    ):
        assert required in sample, f"missing field on Organon list entry: {required}"


def test_list_uods_carries_browse_facets(client):
    """The list is enriched with provenance kind + cited flag from the cheap
    side-files (no load_uod), so the browser can group/facet without N fetches."""
    body = client.get("/organon/uods").json()["data"]
    by_id = {u["uod_id"]: u for u in body}
    # an imported ontology is kind=ontology and cited from its source vocabulary
    if "sumo_upper" in by_id:
        assert by_id["sumo_upper"]["kind"] == "ontology"
        assert by_id["sumo_upper"]["cited"] is True
    # a synthetic exemplar is authored-here (not cited)
    if "ternary_relation_challenge" in by_id:
        assert by_id["ternary_relation_challenge"]["cited"] is False


def test_list_uods_carries_standing(client):
    """Every list row carries a computed standing badge (posited/derived/...)."""
    body = client.get("/organon/uods").json()["data"]
    assert body, "corpus empty"
    keys = set()
    for u in body:
        st = u["standing"]
        assert {"key", "glyph", "label", "level", "meaning", "non_claim"} <= set(st.keys())
        keys.add(st["key"])
    # The corpus has both un-derived imports and worked proofs.
    assert "posited" in keys


def test_detail_carries_standing_with_the_non_claim(client, sample_uod_id):
    data = client.get(f"/organon/uods/{sample_uod_id}").json()["data"]
    st = data["standing"]
    assert st["key"] in {"posited", "derived", "withstood", "blank"}
    # The badge always carries its meaning + a non-claim string for the tooltip.
    assert st["meaning"] and st["non_claim"]


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


# --------------------------------------------------------------------------- #
# 6. Diachronic reading lenses — modal (◇/□) + audit (verdict trajectory)      #
# --------------------------------------------------------------------------- #
#
# These two routes surface the corpus's modality / model-revision exemplars
# (src/modal_query.py, src/model_revision.py) — read-only readings off a UoD's
# transformation chain. Neither runs a layout engine (attest=False); both are
# geometry-free and add no §3.3 obligation.


def test_modal_reading_off_branching_history(client):
    """GET /modal reads ◇/□ off the branching exemplar: (cold) is necessary (□ — on
    every reachable sheet), (cloudy)/(calm) are merely possible (◇ — on some)."""
    resp = client.get("/organon/uods/possible_and_necessary/modal")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_chain"] and data["branching"]
    assert data["world_count"] == 4
    by = {r["name"]: r for r in data["relations"]}
    assert by["cold"]["necessary"] is True and by["cold"]["possible"] is True
    assert by["cloudy"]["necessary"] is False and by["cloudy"]["possible"] is True
    assert by["calm"]["necessary"] is False and by["calm"]["possible"] is True
    # The worlds the modality ranges over carry their EGIF + leaf/initial flags.
    assert any(w["is_leaf"] and w["egif"].strip() == "(cold)" for w in data["worlds"])


def test_modal_reading_over_leaves_only(client):
    """over=leaves quantifies only over trajectory endpoints; both lines rest at
    (cold), so over the single leaf every scribed relation reads necessary."""
    resp = client.get("/organon/uods/possible_and_necessary/modal?over=leaves")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["over"] == "leaves" and data["world_count"] == 1
    by = {r["name"]: r for r in data["relations"]}
    assert by["cold"]["necessary"] is True


def test_modal_reading_absent_for_synchronic_uod(client, sample_uod_id):
    """A UoD with no chain has no frame to read ◇/□ off — has_chain False, no error."""
    resp = client.get(f"/organon/uods/{sample_uod_id}/modal")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    if not body["data"]["has_chain"]:
        assert body["data"]["relations"] == []


def test_modal_unknown_id_is_clean_error(client):
    resp = client.get("/organon/uods/no-such-uod/modal")
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "UOD_NOT_FOUND"


def test_audit_trajectory_flips_as_model_is_revised(client):
    """GET /audit peels the dialogue's declared proposal against each successive M;
    'every patient is insured' moves FALSE→TRUE→FALSE→TRUE as the dialogue admits
    Ben's insurance, a new patient Cal, then Cal's coverage."""
    resp = client.get("/organon/uods/dialogue_model_revision/audit")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_chain"]
    # The default proposal is the UoD's declared audit-proposal annotation.
    assert "patient" in data["proposal"] and "insured" in data["proposal"]
    verdicts = [f["verdict"] for f in data["frames"]]
    assert verdicts == ["false", "true", "false", "true"]
    # Each revision step is labelled by the fact the dialogue admitted.
    facts = [f["fact"] for f in data["frames"] if f["kind"] == "step"]
    assert any("Ben" in (f or "") for f in facts)


def test_audit_accepts_an_explicit_proposal(client):
    """A caller-supplied proposal overrides the declared default."""
    prop = '~[ (patient *x) ~[ (insured x) ] ]'
    resp = client.get("/organon/uods/dialogue_model_revision/audit",
                      params={"proposal": prop})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["proposal"] == prop
    assert [f["verdict"] for f in data["frames"]] == ["false", "true", "false", "true"]


def test_audit_without_a_declared_proposal_is_clean_error(client):
    """A chained UoD that declares no audit-proposal and gets none returns a clean
    NO_PROPOSAL, not a 500."""
    resp = client.get("/organon/uods/theorem_praeclarum/audit")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_PROPOSAL"


def test_audit_ill_formed_proposal_is_clean_error(client):
    """A malformed proposal EGIF is reported as an AUDIT_ERROR, never a stack-trace 500."""
    resp = client.get("/organon/uods/dialogue_model_revision/audit",
                      params={"proposal": "~[ (patient *x"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUDIT_ERROR"


def test_audit_surfaces_the_disposition_and_mode(client):
    """The swan exemplar walks the inning-outcome taxonomy: the audit frames carry
    each step's disposition + Peircean mode (induction → induction → abduction), and
    the verdict moves FALSE→TRUE→TRUE→TRUE→FALSE (a law absorbs the newcomer; the
    black swan revises M)."""
    resp = client.get("/organon/uods/dialogue_swan_revision/audit")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["has_chain"]
    assert [f["verdict"] for f in data["frames"]] == \
        ["false", "true", "true", "true", "false"]
    steps = [f for f in data["frames"] if f["kind"] == "step"]
    dispositions = [f["disposition"] for f in steps]
    assert dispositions == ["new_fact", "generalization", "new_fact", "challenge_to_M"]
    modes = {f["mode"] for f in steps}
    assert {"induction", "abduction"} <= modes
    # the challenge step carries the relinquished law / admitted anomaly as its payload
    assert any("black" in (f["fact"] or "") for f in steps)


# --- The accessible reading route (src/accessible_projection.py) ----------- #
# GET /accessible is a non-visual projection of the same graph the drawing
# shows — a sheet→cut→area→ligature tree + a spoken reading + the linear form.
# Synchronic (any UoD, no chain), geometry-free (attest=False, no §3.3 hook).

def test_accessible_reading_returns_tree_reading_and_linear_form(client, sample_uod_id):
    resp = client.get(f"/organon/uods/{sample_uod_id}/accessible")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    # The tree is rooted at the sheet; the spoken reading opens by asserting it.
    assert data["tree"]["kind"] == "sheet"
    assert data["reading"].startswith("The sheet asserts:")
    assert data["reading_lines"][0].strip() == "Sheet of assertion"
    # The canonical linear form travels with the reading as the cross-check.
    assert data["linear_forms"]["forms"]["egif"]["ok"] is True


def test_accessible_reading_beta_scroll_is_faithful(client, corpus_ids):
    """On the man→mortal scroll the reading names the negation and the shared
    line, so picture, reading, and proposition denote one graph."""
    if "peirce_cp_4_394_man_mortal" not in corpus_ids:
        pytest.skip("man-mortal exemplar not in this tomos")
    resp = client.get("/organon/uods/peirce_cp_4_394_man_mortal/accessible")
    data = resp.json()["data"]
    assert "it is not the case that:" in data["reading"]
    # The inner (double-negated) area's interior reads as asserted, the outer as denied.
    outer = data["tree"]["cuts"][0]
    assert outer["stance"] == "denied"


def test_accessible_reading_no_attest_hook(client, sample_uod_id, monkeypatch):
    """The projection is the ground truth (no drawing in between), so — like
    /modal and /audit — the route fires no §3.3 correspondence attestation."""
    calls = []
    monkeypatch.setattr(
        layout_service, "attest_correspondence",
        lambda *a, **k: calls.append(k.get("context", "?")))
    resp = client.get(f"/organon/uods/{sample_uod_id}/accessible")
    assert resp.status_code == 200 and resp.json()["success"] is True
    assert calls == []          # geometry-free — no layout, no attestation


def test_accessible_unknown_id_is_clean_error(client):
    resp = client.get("/organon/uods/no-such-uod/accessible")
    assert resp.json()["success"] is False
    assert resp.json()["error"]["code"] == "UOD_NOT_FOUND"
