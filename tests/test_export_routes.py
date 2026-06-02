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
    assert {"egif", "cgif", "clif", "svg", "tikz", "png", "pdf"} == fmts
    # Linear / svg / tikz are always available.
    for f in body["data"]:
        if f["format"] in ("egif", "cgif", "clif", "svg", "tikz"):
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
