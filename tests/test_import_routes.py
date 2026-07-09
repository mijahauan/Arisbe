"""
Tests for the Import doorway — admitting an external linear form.

Per docs/MANIFEST_AND_MEANING.md, an import is *admitted at low warrant*:
parsed (comprehended), attested for §3.3 correspondence, bibliographically
attributed, never asserted as true.  These tests pin the bibliographic
formatting, the check (grammar / round-trip / §3.3), and the admit
(low-warrant LITERATURE_EXAMPLE UoD, citation persisted, §3.3 at the
boundary, no overwrite), plus the Organon surfacing of provenance.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tomos_service
from layout_dto import LayoutDTO
from tomos_service import TomosService
from web_api import main as web_main
from web_api.routes import imports as imports_route
from web_api.routes import organon as organon_route
from web_api.services import bibliography


BOOK = {
    "type": "book",
    "author": "Charles S. Peirce",
    "title": "Collected Papers",
    "editor": "Hartshorne & Weiss",
    "publisher": "Harvard University Press",
    "publisher_place": "Cambridge",
    "year": "1933",
    "pages": "CP 4.394",
}
FORM = "(Human *x) ~[ (Mortal x) ]"


@pytest.fixture
def client():
    return TestClient(web_main.app)


@pytest.fixture
def isolated_tomos(tmp_path, monkeypatch):
    """Point the Import (and Organon) route TomosService at a tmp corpus."""
    tmp = tmp_path / "tomos"
    tmp.mkdir(parents=True)
    fresh = TomosService(tmp)
    monkeypatch.setattr(imports_route, "_tomos_service", fresh)
    monkeypatch.setattr(organon_route, "_tomos_service", fresh)
    return {"service": fresh, "root": tmp}


# --------------------------------------------------------------------------- #
# Bibliography                                                                 #
# --------------------------------------------------------------------------- #


def test_format_citation_book():
    s = bibliography.format_citation(BOOK)
    assert "Charles S. Peirce." in s
    assert "Collected Papers." in s
    assert "Harvard University Press" in s
    assert "1933" in s
    assert "CP 4.394" in s


def test_format_citation_article_and_webpage():
    art = bibliography.format_citation({
        "type": "article-journal", "author": "A. Author", "title": "On Graphs",
        "container_title": "J. Logic", "volume": "3", "issue": "2", "year": "2001", "pages": "1-20",
    })
    assert "“On Graphs.”" in art and "J. Logic 3" in art and "(2001)" in art
    web = bibliography.format_citation({
        "type": "webpage", "title": "EG Primer", "container_title": "Site",
        "url": "https://example.org/eg", "accessed": "2026-06-02",
    })
    assert "https://example.org/eg" in web and "accessed 2026-06-02" in web


def test_authors_list_semicolon_split():
    assert bibliography.authors_list({"author": "Peirce; Roberts"}) == ["Peirce", "Roberts"]
    assert bibliography.authors_list({}) == []


def test_validate_requires_fields():
    with pytest.raises(bibliography.BibliographyError):
        bibliography.validate({"type": "book", "author": "X"})  # no title


def test_citation_types_endpoint(client):
    body = client.get("/import/citation-types").json()
    assert body["success"] is True
    types = {t["type"] for t in body["data"]}
    assert {"book", "chapter", "article-journal", "webpage", "document"} <= types


# --------------------------------------------------------------------------- #
# Check                                                                        #
# --------------------------------------------------------------------------- #


def test_check_valid_egif(client):
    body = client.post("/import/check", json={"text": FORM, "notation": "egif"}).json()
    assert body["success"] is True
    d = body["data"]
    assert d["ok"] is True
    assert d["parsed"]["ok"] is True
    assert d["roundtrip"]["ok"] is True and d["roundtrip"]["stable"] is True
    assert d["correspondence"]["ok"] is True
    assert d["svg"] and d["svg"].startswith("<")
    assert d["linear_forms"]["forms"]["egif"]["ok"] is True


def test_check_bad_grammar(client):
    body = client.post("/import/check", json={"text": "(Human *x ~[", "notation": "egif"}).json()
    assert body["success"] is True  # the endpoint succeeds; the *check* reports failure
    d = body["data"]
    assert d["parsed"]["ok"] is False
    assert d["ok"] is False
    assert d["parsed"]["error"]


def test_check_unknown_notation(client):
    body = client.post("/import/check", json={"text": FORM, "notation": "xyz"}).json()
    assert body["success"] is True
    assert body["data"]["parsed"]["ok"] is False
    assert "Unknown notation" in body["data"]["parsed"]["error"]


def test_check_cgif_input(client):
    body = client.post("/import/check", json={"text": "[Human: *x]", "notation": "cgif"}).json()
    assert body["success"] is True
    assert body["data"]["parsed"]["ok"] is True


# --------------------------------------------------------------------------- #
# Admit                                                                        #
# --------------------------------------------------------------------------- #


def test_admit_creates_low_warrant_uod_with_provenance(client, isolated_tomos):
    body = client.post("/import/admit", json={
        "text": FORM, "notation": "egif", "bibliography": BOOK,
        "uod_id": "peirce-cp-4-394", "name": "Man-Mortal", "description": "From CP.",
        "tags": ["alpha"],
    }).json()
    assert body["success"] is True, body.get("error")
    assert body["data"]["uod_id"] == "peirce-cp-4-394"
    assert "Peirce" in body["data"]["source_citation"]

    svc = isolated_tomos["service"]
    assert svc.uod_exists("peirce-cp-4-394")
    # Bibliographic sidecar persisted, structured.
    biblio = svc.load_bibliography("peirce-cp-4-394")
    assert biblio is not None
    assert biblio["record"]["type"] == "book"
    assert biblio["formatted"].startswith("Charles S. Peirce.")
    # Low warrant + literature category carried in metadata/tags.
    uod = svc.load_uod("peirce-cp-4-394")
    assert uod.category.value == "literature_example"
    assert "warrant:low" in uod.metadata.tags
    assert uod.metadata.source_citation and "Peirce" in uod.metadata.source_citation
    assert uod.metadata.authors == ["Charles S. Peirce"]


def test_admit_refuses_duplicate(client, isolated_tomos):
    payload = {"text": FORM, "notation": "egif", "bibliography": BOOK, "uod_id": "dup-id"}
    first = client.post("/import/admit", json=payload).json()
    assert first["success"] is True
    second = client.post("/import/admit", json=payload).json()
    assert second["success"] is False
    assert second["error"]["code"] == "IMPORT_ERROR"
    assert "already exists" in second["error"]["message"]


def test_admit_refuses_missing_required_citation_field(client, isolated_tomos):
    body = client.post("/import/admit", json={
        "text": FORM, "notation": "egif",
        "bibliography": {"type": "book", "author": "X"},  # no title
        "uod_id": "missing-title",
    }).json()
    assert body["success"] is False
    assert body["error"]["code"] == "IMPORT_ERROR"
    assert "Title" in body["error"]["message"]
    assert not isolated_tomos["service"].uod_exists("missing-title")


def test_admit_refuses_drifted_drawing_cleanly(client, isolated_tomos, monkeypatch):
    """§3.3 failure at the corpus boundary aborts with nothing persisted."""
    from elk_layout_engine import ELKLayoutEngine

    class _BrokenEngine:
        def generate_layout(self, egi, style, layout_deltas=None):
            real = ELKLayoutEngine().generate_layout(egi, style, layout_deltas)
            if not real.vertex_positions:
                return real
            victim = next(iter(real.vertex_positions))
            return LayoutDTO(
                vertex_positions={k: v for k, v in real.vertex_positions.items() if k != victim},
                predicate_positions=dict(real.predicate_positions),
                cut_bounds=dict(real.cut_bounds),
                ligature_paths=list(real.ligature_paths),
                area_hierarchy={k: set(v) for k, v in real.area_hierarchy.items()},
                viewport_bounds=real.viewport_bounds,
                sheet_id=real.sheet_id,
                style=real.style,
            )

    monkeypatch.setattr(tomos_service, "ELKLayoutEngine", lambda: _BrokenEngine())
    body = client.post("/import/admit", json={
        "text": FORM, "notation": "egif", "bibliography": BOOK, "uod_id": "should-not-persist",
    }).json()
    assert body["success"] is False
    assert body["error"]["code"] == "CORRESPONDENCE_VIOLATION"
    assert not isolated_tomos["service"].uod_exists("should-not-persist")


# --------------------------------------------------------------------------- #
# Organon surfaces provenance                                                  #
# --------------------------------------------------------------------------- #


def test_organon_detail_surfaces_imported_provenance(client, isolated_tomos):
    client.post("/import/admit", json={
        "text": FORM, "notation": "egif", "bibliography": BOOK, "uod_id": "prov-shown",
        "name": "Provenance demo",
    })
    detail = client.get("/organon/uods/prov-shown").json()
    assert detail["success"] is True
    assert detail["data"]["bibliography"] is not None
    assert "Peirce" in detail["data"]["bibliography"]["formatted"]


# --------------------------------------------------------------------------- #
# Ontology file import (OWL / RDF / CLIF → kind=ontology UoD) — U1/U17/U22/U25  #
# --------------------------------------------------------------------------- #

_ZOO_OFN = (Path(__file__).parent / "fixtures" / "zoo.ofn").read_text()


def test_check_ontology_reports_skips_and_scale(client):
    body = client.post("/import/check-ontology", json={"text": _ZOO_OFN, "fmt": "owl"}).json()
    assert body["success"] is True, body.get("error")
    d = body["data"]
    assert d["parsed"]["ok"] is True
    # Counts translated, not silently dropped: the skip-report names each construct.
    assert d["counts"]["axioms"] > 0 and d["counts"]["types"] > 0
    assert any("skipped" in s for s in d["skipped_constructs"])
    # Scale assessment present; the zoo fixture draws (svg + §3.3) — not too large.
    assert d["scale"]["level"] in ("ok", "large")
    assert d["svg"] and d["correspondence"]["ok"] is True


def test_admit_ontology_shelves_as_ontology_with_skip_report(client, isolated_tomos):
    body = client.post("/import/admit-ontology", json={
        "text": _ZOO_OFN, "fmt": "owl", "uod_id": "zoo-onto", "name": "Zoo ontology",
    }).json()
    assert body["success"] is True, body.get("error")
    assert body["data"]["kind"] == "ontology"
    svc = isolated_tomos["service"]
    assert svc.uod_exists("zoo-onto")
    # Shelved as kind=ontology in provenance (the browse facet + Agon M-picker dim).
    prov = svc.load_provenance("zoo-onto")
    assert prov["kind"] == "ontology"
    # The construct-level skip-report is persisted (U17), not only logged at the CLI.
    assert prov["skipped_constructs"] and any("skipped" in s for s in prov["skipped_constructs"])
    # Organon detail surfaces the kind + the skip-report.
    detail = client.get("/organon/uods/zoo-onto").json()["data"]
    assert detail["provenance"]["kind"] == "ontology"
    assert detail["provenance"]["skipped_constructs"]
    # And the list facets it under kind=ontology.
    row = next(e for e in client.get("/organon/uods").json()["data"] if e["uod_id"] == "zoo-onto")
    assert row["kind"] == "ontology"


def test_admit_ontology_refuses_duplicate(client, isolated_tomos):
    payload = {"text": _ZOO_OFN, "fmt": "owl", "uod_id": "zoo-dup"}
    assert client.post("/import/admit-ontology", json=payload).json()["success"] is True
    second = client.post("/import/admit-ontology", json=payload).json()
    assert second["success"] is False
    assert second["error"]["code"] == "IMPORT_ERROR"


def test_check_ontology_unknown_format_is_a_clean_error(client):
    body = client.post("/import/check-ontology", json={"text": "x", "fmt": "manchester"}).json()
    assert body["success"] is False
    assert body["error"]["code"] == "IMPORT_ERROR"
