"""
Tests for src/scholarly_citation.py — turning a UoD's provenance into a
publication citation (a human author-date line + a BibTeX entry).

The contract: faithful (every present field rendered), honest (nothing
fabricated — an absent field is omitted, a sourceless graph reports
``has_source: false``), and self-contained (no web/layout/tomos imports).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import scholarly_citation as sc


MS280 = {
    "type": "manuscript", "author": "Peirce, C. S.", "year": "1903",
    "title": "MS 280", "container_title": "Writings of Charles S. Peirce",
    "volume": "6", "page": "12", "bibkey": "peirceMS280",
}


def test_format_citation_renders_present_fields_in_order():
    c = sc.format_citation(MS280)
    assert c == ("Peirce, C. S. (1903). MS 280. "
                 "In Writings of Charles S. Peirce, Vol. 6, p. 12.")


def test_format_citation_omits_absent_fields_no_fabrication():
    c = sc.format_citation({"author": "Dau, F.", "title": "EGs with cuts"})
    assert "Dau, F." in c and "EGs with cuts" in c
    # No invented year / container / page.
    assert "()" not in c and "Vol." not in c and "p." not in c


def test_format_citation_empty_record_is_empty():
    assert sc.format_citation({}) == ""


def test_bibtex_entry_maps_type_and_emits_present_fields():
    bib = sc.bibtex_entry(MS280)
    assert bib.startswith("@unpublished{peirceMS280,")   # manuscript → @unpublished
    assert "author = {Peirce, C. S.}" in bib
    assert "title = {MS 280}" in bib
    assert "year = {1903}" in bib
    assert bib.rstrip().endswith("}")


def test_bibtex_type_mapping_book_and_article():
    book = sc.bibtex_entry({"type": "book", "author": "Dau", "year": "2003", "title": "T"})
    assert book.startswith("@book{")
    art = sc.bibtex_entry({"type": "article", "author": "X", "year": "2020",
                           "title": "T", "container_title": "J. Logic"})
    assert art.startswith("@article{")
    assert "journal = {J. Logic}" in art   # container → journal for an article


def test_bibtex_key_derives_from_author_year_when_no_bibkey():
    assert sc.bibtex_key({"author": "Peirce, C. S.", "year": "1903"}) == "peirce1903"
    assert sc.bibtex_key({"author": "Johan van Benthem", "year": "1976"}) == "benthem1976"


def test_citation_for_prefers_theorem_source():
    bundle = sc.citation_for(provenance={"theorem_source": MS280})
    assert bundle["has_source"] is True
    assert "MS 280" in bundle["citation"]
    assert bundle["bibtex"].startswith("@unpublished{peirceMS280")
    assert bundle["key"] == "peirceMS280"


def test_citation_for_falls_back_to_transcribed_proof_then_method():
    prov = {"proof_source": {"kind": "transcribed", "citation":
            {"author": "Sowa", "year": "2011", "title": "EG proof"}}}
    assert "Sowa" in sc.citation_for(provenance=prov)["citation"]
    prov2 = {"method_sources": [{"author": "Roberts", "year": "1973", "title": "EGs"}]}
    assert "Roberts" in sc.citation_for(provenance=prov2)["citation"]


def test_citation_for_free_text_fallback_when_no_record():
    b = sc.citation_for(provenance={}, source_citation="Peirce, MS 514 (1909).")
    assert b["has_source"] is True
    assert b["citation"] == "Peirce, MS 514 (1909)."
    assert b["bibtex"] == ""   # no structured record → no BibTeX, honestly


def test_citation_for_sourceless_graph_is_honest():
    b = sc.citation_for(provenance={}, name="my draft")
    assert b["has_source"] is False
    assert "my draft" in b["citation"] and "Arisbe" in b["citation"]
    assert b["bibtex"] == ""
