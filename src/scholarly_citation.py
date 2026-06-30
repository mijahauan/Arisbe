"""
scholarly_citation — turn a UoD's provenance into a **publication citation**.

A scholar reproducing a Peirce diagram for a paper needs the attribution in two
forms: a human-readable **author-date citation** ("Peirce, C. S. (1903). MS 280…")
and a **BibTeX entry** to drop into their `.bib`. The raw material already rides
alongside every imported UoD — the CSL-compatible records in
[provenance.py](provenance.py) (`theorem_source` = where the proposition comes
from, `method_sources`, `proof_source`) and the optional `bibliography.json`
side-file — but nothing rendered them *as a citation*. This module does.

It is **self-contained** (no web / layout / tomos imports), so the build tools,
`tomos_service`, and the export path can all call it; and it **fabricates
nothing** — an absent field is omitted, never invented (docs/MANIFEST_AND_MEANING.md:
no fabricated citation). When a UoD carries no source at all (an original Arisbe
graph), `citation_for` honestly reports that there is nothing to cite.

Used by the authentic-Peirce LaTeX export (a figure caption / `\\bibitem`) and the
`/export/citation` route.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# CSL record ``type`` → BibTeX entry type. Anything unmapped falls to ``@misc``,
# which is always valid.
_CSL_TO_BIBTEX = {
    "book": "book",
    "article": "article",
    "article-journal": "article",
    "article-magazine": "article",
    "chapter": "incollection",
    "paper-conference": "inproceedings",
    "manuscript": "unpublished",
    "thesis": "phdthesis",
    "report": "techreport",
    "webpage": "misc",
}


def _s(record: Dict[str, Any], *keys: str) -> str:
    """First non-empty stringified value among ``keys`` (stripped)."""
    for k in keys:
        v = record.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def format_citation(record: Dict[str, Any]) -> str:
    """A human-readable author-date citation for one CSL-compatible record.

    Omits every absent field (no fabrication). Handles the fields the corpus
    actually carries — author, year, title, container_title, volume, page, note —
    in a conventional order::

        Peirce, C. S. (1903). MS 280. In Collected Papers, Vol. 4, p. 12. [note]
    """
    if not record:
        return ""
    author = _s(record, "author")
    year = _s(record, "year", "issued")
    title = _s(record, "title")
    container = _s(record, "container_title", "journal", "booktitle")
    volume = _s(record, "volume")
    page = _s(record, "page", "pages")
    note = _s(record, "note")

    head = " ".join(x for x in [author, f"({year})" if year else ""] if x).strip()
    # "In <container>[, Vol. V][, p. P]" — the locator clause.
    loc_bits: List[str] = []
    if container:
        loc_bits.append(f"In {container}")
    if volume:
        loc_bits.append(f"Vol. {volume}")
    if page:
        loc_bits.append(("pp. " if "-" in page or "–" in page else "p. ") + page)
    locator = ", ".join(loc_bits)

    parts = [b for b in [head, title, locator] if b]
    citation = ". ".join(parts)
    if citation and not citation.endswith("."):
        citation += "."
    if note:
        citation = f"{citation} {note}".strip()
    return citation


def bibtex_key(record: Dict[str, Any], fallback: str = "arisbe") -> str:
    """A stable BibTeX key: the record's ``bibkey`` if present, else
    ``<surname><year>`` derived from author + year (alphanumerics only)."""
    explicit = _s(record, "bibkey", "id", "key")
    if explicit:
        return "".join(ch for ch in explicit if ch.isalnum() or ch in "-_:")
    author = _s(record, "author")
    # surname = last word of the first author (handles "Peirce, C. S." and "C. S. Peirce")
    first_author = author.split(";")[0].split(" and ")[0]
    surname = (first_author.split(",")[0].strip()
               if "," in first_author else first_author.split()[-1:] and
               first_author.split()[-1])
    surname = "".join(ch for ch in (surname or fallback) if ch.isalnum()).lower() or fallback
    year = "".join(ch for ch in _s(record, "year", "issued") if ch.isdigit())
    return f"{surname}{year}" if year else surname


def bibtex_entry(record: Dict[str, Any], key: Optional[str] = None) -> str:
    """A BibTeX entry for one CSL-compatible record. The entry type is mapped from
    the record's CSL ``type`` (``@misc`` for anything unmapped — always valid).
    Only present fields are emitted."""
    if not record:
        return ""
    entry_type = _CSL_TO_BIBTEX.get(_s(record, "type").lower(), "misc")
    key = key or bibtex_key(record)

    fields: List[tuple] = []
    def put(name: str, *source_keys: str) -> None:
        val = _s(record, *source_keys)
        if val:
            fields.append((name, val))

    put("author", "author")
    put("title", "title")
    put("year", "year", "issued")
    # container maps differently by entry type.
    container = _s(record, "container_title", "journal", "booktitle")
    if container:
        if entry_type == "article":
            fields.append(("journal", container))
        elif entry_type in ("incollection", "inproceedings"):
            fields.append(("booktitle", container))
        else:
            fields.append(("series", container))
    put("volume", "volume")
    put("number", "number")
    put("pages", "page", "pages")
    put("publisher", "publisher")
    put("address", "address", "publisher_place")
    put("note", "note")

    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
    return f"@{entry_type}{{{key},\n{body}\n}}"


def _primary_record(
    provenance: Optional[Dict[str, Any]],
    bibliography: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """The single best record to cite for a UoD's *proposition* — the scholarly
    locator a reader wants (e.g. Peirce's manuscript). Preference order:
    ``theorem_source`` (where the proposition comes from), then a *transcribed*
    proof's citation, then the first ``method_source``, then a standalone
    ``bibliography`` record. Returns ``None`` when nothing citable is recorded."""
    prov = provenance or {}
    theorem = prov.get("theorem_source") or {}
    if theorem:
        return theorem
    proof = prov.get("proof_source") or {}
    if proof.get("kind") == "transcribed" and proof.get("citation"):
        return proof["citation"]
    methods = prov.get("method_sources") or []
    if methods:
        return methods[0]
    if bibliography:
        # bibliography.json may itself be a CSL record or wrap one under "record".
        return bibliography.get("record", bibliography)
    return None


def citation_for(
    *,
    provenance: Optional[Dict[str, Any]] = None,
    bibliography: Optional[Dict[str, Any]] = None,
    source_citation: Optional[str] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """The citation bundle for a UoD: ``{citation, bibtex, key, has_source, note}``.

    Draws on the provenance bundle + the optional ``bibliography.json`` + the UoD's
    free-text ``source_citation`` (a last-resort human string). ``has_source`` is
    False — and ``citation`` falls back to a plain "Reproduced with Arisbe" line —
    when nothing citable is recorded (an original graph honestly has no source to
    cite; nothing is fabricated).
    """
    record = _primary_record(provenance, bibliography)
    if record:
        return {
            "has_source": True,
            "citation": format_citation(record),
            "bibtex": bibtex_entry(record),
            "key": bibtex_key(record),
            "note": None,
        }
    # No structured record. Fall back to the free-text citation if the UoD carries one.
    if source_citation and source_citation.strip():
        return {
            "has_source": True,
            "citation": source_citation.strip(),
            "bibtex": "",
            "key": "",
            "note": "free-text source_citation (no structured record to build BibTeX from)",
        }
    # Genuinely sourceless — an original Arisbe graph.
    label = (name or "this graph").strip()
    return {
        "has_source": False,
        "citation": f"{label} — reproduced with Arisbe (no external source).",
        "bibtex": "",
        "key": "",
        "note": "original graph; nothing external to cite",
    }
