"""
Tests for the Export arc — taking an EGI out of the corpus to the world,
in a chosen style and format (the return leg of world → Organon → world).

Covers the format registry, each format's output, style selection (a
styled drawing differs by style yet still §3.3-attests), the UoD and
inline-text sources, and the Ergasterion render-in-style path.
"""

import base64
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import export as export_route
from web_api.services import export_service

FORM = "(Human *x) ~[ (Mortal x) ]"
_HAS_RSVG = shutil.which("rsvg-convert") is not None


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def isolated_tomos(tmp_path, monkeypatch):
    tmp = tmp_path / "tomos"
    tmp.mkdir(parents=True)
    fresh = TomosService(tmp)
    real = TomosService(Path(__file__).parent.parent / "tomos")
    uod_ids = [u["uod_id"] for u in real.list_uods()]
    seed = next((c for c in ["alpha_man_mortal", "peirce_modus_ponens"] if c in uod_ids), uod_ids[0])
    fresh.save_uod(real.load_uod(seed))
    monkeypatch.setattr(export_route, "_tomos_service", fresh)
    return {"service": fresh, "seed_id": seed}


# --------------------------------------------------------------------------- #
# Service / formats                                                            #
# --------------------------------------------------------------------------- #


def test_formats_endpoint_lists_all(client):
    body = client.get("/export/formats").json()
    assert body["success"] is True
    fmts = {f["format"] for f in body["data"]}
    assert {"egif", "cgif", "clif", "svg", "tikz", "peirce-tikz", "png", "pdf"} == fmts
    # Linear / svg / tikz / peirce-tikz are always available.
    for f in body["data"]:
        if f["format"] in ("egif", "cgif", "clif", "svg", "tikz", "peirce-tikz"):
            assert f["available"] is True


def test_export_linear_and_svg_and_tikz_from_text(client):
    for fmt, needle in [("egif", "Human"), ("cgif", "Human"), ("clif", "Human"),
                        ("svg", "<svg"), ("tikz", "tikzpicture")]:
        body = client.post("/export", json={"text": FORM, "notation": "egif", "format": fmt}).json()
        assert body["success"] is True, (fmt, body.get("error"))
        d = body["data"]
        assert d["is_binary"] is False
        assert needle in d["content"]
        assert d["filename"].endswith("." + ("tex" if fmt == "tikz" else fmt))


def test_styled_svg_differs_by_style(client):
    dau = client.post("/export", json={"text": FORM, "format": "svg", "style_name": "dau-compliant@1.0"}).json()["data"]
    peirce = client.post("/export", json={"text": FORM, "format": "svg", "style_name": "peirce-authentic@1.0"}).json()["data"]
    assert dau["content"] != peirce["content"]


def test_tikz_honors_style(client):
    """Regression: TikZ export in the Peirce style must NOT come out as Dau —
    the chosen style reaches the exporter (the viewer's 'export what you see')."""
    dau = client.post("/export", json={"text": FORM, "format": "tikz", "style_name": "dau-compliant@1.0"}).json()["data"]
    peirce = client.post("/export", json={"text": FORM, "format": "tikz", "style_name": "peirce-authentic@1.0"}).json()["data"]
    assert dau["content"] != peirce["content"]
    assert "peirce-authentic" in peirce["content"]
    assert "dau-compliant" in dau["content"]


def test_export_honors_layout_engine(client):
    """The layout engine carries into export too, so an export reproduces the
    viewer's chosen projection (ELK vs tension), not just its style."""
    elk = client.post("/export", json={"text": FORM, "format": "tikz", "engine": "elk"}).json()["data"]
    tension = client.post("/export", json={"text": FORM, "format": "tikz", "engine": "tension"}).json()["data"]
    assert elk["content"] != tension["content"]


def test_export_from_uod(client, isolated_tomos):
    body = client.post("/export", json={"uod_id": isolated_tomos["seed_id"], "format": "svg"}).json()
    assert body["success"] is True
    assert body["data"]["filename"].startswith(isolated_tomos["seed_id"])
    assert "<svg" in body["data"]["content"]


def test_unknown_format_and_no_source(client):
    bad = client.post("/export", json={"text": FORM, "format": "docx"}).json()
    assert bad["success"] is False and bad["error"]["code"] == "EXPORT_ERROR"
    none = client.post("/export", json={"format": "svg"}).json()
    assert none["success"] is False and none["error"]["code"] == "NO_SOURCE"


def test_export_honors_regime3_deltas(client, isolated_tomos):
    """The /export route threads regime-3 presentation adjustments into the
    layout — "export what you adjusted to see" (the PEP transcribe-then-tune
    path).  A move_vertex delta changes the exported drawing.  Driven from a
    corpus UoD because stored ids are stable (parse_egif ids are randomized)."""
    uid = isolated_tomos["seed_id"]
    egi = isolated_tomos["service"].load_uod(uid).current_egi
    if not egi.V:
        pytest.skip(f"seed UoD '{uid}' has no vertex to nudge")
    vid = next(iter(egi.V)).id
    delta = {"op": "move_vertex", "params": {"vertex_id": vid, "dx": 40.0, "dy": 0.0}}

    plain = client.post("/export", json={"uod_id": uid, "format": "tikz"}).json()["data"]
    tuned = client.post(
        "/export", json={"uod_id": uid, "format": "tikz", "deltas": [delta]}
    ).json()
    assert tuned["success"] is True, tuned.get("error")
    assert tuned["data"]["content"] != plain["content"]  # the adjustment reached the drawing


def test_export_rejects_malformed_deltas(client):
    # No "op" key → deltas_from_list raises → BAD_DELTAS.
    bad = client.post(
        "/export", json={"text": FORM, "format": "tikz", "deltas": [{"params": {}}]}
    ).json()
    assert bad["success"] is False and bad["error"]["code"] == "BAD_DELTAS"


def test_export_chain_route(client, monkeypatch, tmp_path):
    """POST /export/chain exports a UoD's worked chain as one Peirce LaTeX doc."""
    from tomos_service import TomosService
    real = TomosService(Path(__file__).parent.parent / "tomos")
    # A corpus UoD that has a worked chain (history/chain.jsonl).
    chain_uid = "beta_modus_ponens"
    fresh = TomosService(tmp_path / "tomos")
    fresh.save_uod_with_chain(real.load_uod(chain_uid), real.load_chain(chain_uid))
    monkeypatch.setattr(export_route, "_tomos_service", fresh)

    ok = client.post("/export/chain", json={"uod_id": chain_uid, "title": "BMP"}).json()
    assert ok["success"] is True, ok.get("error")
    doc = ok["data"]["content"]
    assert "\\begin{tikzpicture}" in doc and "Initial graph" in doc and "Step 1:" in doc
    assert ok["data"]["filename"] == f"{chain_uid}-chain.tex"

    missing = client.post("/export/chain", json={"uod_id": "no_such_uod"}).json()
    assert missing["success"] is False and missing["error"]["code"] == "CHAIN_NOT_FOUND"


@pytest.mark.skipif(not _HAS_RSVG, reason="rsvg-convert not installed")
def test_export_png_and_pdf_binary(client):
    for fmt, sig in [("png", b"\x89PNG"), ("pdf", b"%PDF")]:
        body = client.post("/export", json={"text": FORM, "format": fmt}).json()
        assert body["success"] is True, (fmt, body.get("error"))
        d = body["data"]
        assert d["is_binary"] is True
        raw = base64.b64decode(d["content_base64"])
        assert raw.startswith(sig)


def test_png_reports_cleanly_when_tool_missing(monkeypatch):
    """If rsvg-convert is absent, PNG export raises a clean ExportError."""
    import web_api.services.export_service as es
    monkeypatch.setattr(es.shutil, "which", lambda name: None)
    from egif_parser_dau import parse_egif
    with pytest.raises(es.ExportError):
        es.export_egi(parse_egif(FORM), "png")


# --------------------------------------------------------------------------- #
# Ergasterion render-in-style                                                  #
# --------------------------------------------------------------------------- #


def test_ergasterion_renders_in_chosen_style(client):
    opened = client.post("/ergasterion/sessions", json={"base_source": "empty_sheet"}).json()
    assert opened["success"] is True
    sid = opened["data"]["session_id"]
    # Compose something so the drawing is non-trivial.
    sheet = next(a for a, r in opened["data"]["introspection"]["areas"].items() if r["is_sheet"])
    client.post(f"/ergasterion/sessions/{sid}/fix-graph", json={})  # gate ① → deriving
    client.post(f"/ergasterion/sessions/{sid}/apply",
                json={"rule": "DC+", "parameters": {"selected_elements": [], "target_area": sheet}})
    default_svg = client.get(f"/ergasterion/sessions/{sid}").json()["data"]["svg"]
    peirce = client.get(f"/ergasterion/sessions/{sid}?style=peirce-authentic@1.0").json()
    assert peirce["success"] is True
    assert peirce["data"]["svg"] != default_svg
    # The session remembers the style on a subsequent plain GET.
    again = client.get(f"/ergasterion/sessions/{sid}").json()["data"]["svg"]
    assert again == peirce["data"]["svg"]
    client.delete(f"/ergasterion/sessions/{sid}")


# --------------------------------------------------------------------------- #
# Scholarly citation + batch document (the Peirce-Edition publishing path)      #
# --------------------------------------------------------------------------- #
#
# A corpus UoD's provenance becomes a publication citation (a human line + BibTeX);
# the authentic-Peirce export can stamp it as a figure caption; and several UoDs
# assemble into one captioned "appendix of figures". See src/scholarly_citation.py.

CITED_UOD = "peirce_cp_4_394_man_mortal"   # carries a real theorem_source (CP 4.394)


def _has(client, uod_id):
    return client.get(f"/organon/uods/{uod_id}").json().get("success")


def test_citation_route_returns_citation_and_bibtex(client):
    if not _has(client, CITED_UOD):
        pytest.skip(f"{CITED_UOD} not in corpus")
    body = client.get("/export/citation", params={"uod_id": CITED_UOD}).json()
    assert body["success"]
    d = body["data"]
    assert d["has_source"] is True
    assert "Peirce" in d["citation"]
    assert d["bibtex"].startswith("@") and d["key"]


def test_citation_route_unknown_uod_is_clean_error(client):
    body = client.get("/export/citation", params={"uod_id": "no-such-uod"}).json()
    assert body["success"] is False
    assert body["error"]["code"] == "UOD_NOT_FOUND"


def test_peirce_export_with_cite_emits_a_caption(client):
    if not _has(client, CITED_UOD):
        pytest.skip(f"{CITED_UOD} not in corpus")
    plain = client.post("/export", json={
        "format": "peirce-tikz", "uod_id": CITED_UOD}).json()["data"]["content"]
    cited = client.post("/export", json={
        "format": "peirce-tikz", "uod_id": CITED_UOD, "cite": True}).json()["data"]["content"]
    assert "footnotesize" not in plain
    assert "footnotesize" in cited and "Peirce" in cited
    # The citation is ink *outside* the picture — the tikzpicture body is unchanged.
    body_of = lambda t: t.split("\\begin{tikzpicture}")[1].split("\\end{tikzpicture}")[0]
    assert body_of(plain) == body_of(cited)


def test_cite_is_noop_for_non_peirce_format(client):
    if not _has(client, CITED_UOD):
        pytest.skip(f"{CITED_UOD} not in corpus")
    tikz = client.post("/export", json={
        "format": "tikz", "uod_id": CITED_UOD, "cite": True}).json()
    assert tikz["success"]   # cite ignored for the geometric tikz path, no error


def test_export_document_assembles_a_captioned_appendix(client):
    ids = [u["uod_id"] for u in client.get("/organon/uods").json()["data"]][:2]
    body = client.post("/export/document", json={
        "uod_ids": ids, "title": "Appendix A", "cite": True}).json()
    assert body["success"]
    d = body["data"]
    assert d["format"] == "peirce-document"
    assert "Appendix A" in d["content"]
    # One captioned figure per UoD (each a centred tikzpicture).
    assert d["content"].count("\\begin{center}") >= len(ids)
    assert d["missing"] == []


def test_export_document_reports_missing_ids(client):
    ids = [u["uod_id"] for u in client.get("/organon/uods").json()["data"]][:1]
    body = client.post("/export/document", json={
        "uod_ids": ids + ["no-such-uod"], "cite": False}).json()
    assert body["success"]
    assert body["data"]["missing"] == ["no-such-uod"]


def test_export_document_all_missing_is_clean_error(client):
    body = client.post("/export/document", json={"uod_ids": ["no-such-uod"]}).json()
    assert body["success"] is False
    assert body["error"]["code"] == "UOD_NOT_FOUND"
