"""
Structured bibliographic attribution for corpus imports.

An import is admitted at low warrant, and its **provenance is the trace of
the un-hosted dialogue it came from** (see docs/MANIFEST_AND_MEANING.md).
That trace deserves proper bibliographic standards, not a free-text blob.

This module models citations in a CSL-compatible vocabulary (the CSL-JSON
field names Zotero / Pandoc use), so a record can later be re-styled or
exported.  It provides, as data:

  * ``CITATION_TYPES`` — the supported source types and, for each, the
    fields a form should collect (so the UI is data-driven and extensible);
  * ``format_citation(record)`` — a readable citation string (author-date /
    Chicago-ish) for ``UoDMetadata.source_citation``;
  * ``authors_list(record)`` — the author names for ``UoDMetadata.authors``.

The structured record itself is persisted alongside the UoD (see
``tomos_service.save_bibliography``); the formatted string is the
human-readable face stored in the UoD metadata.
"""

from typing import Any, Dict, List


# Data-driven form spec.  Each type lists the fields a client should
# collect; ``key`` matches the record keys this module reads.  Extending
# the form (or adding a type) is a change here only.
_COMMON_TAIL = [
    {"key": "doi", "label": "DOI", "required": False, "hint": "10.xxxx/…"},
    {"key": "url", "label": "URL", "required": False, "hint": "https://…"},
    {"key": "accessed", "label": "Accessed", "required": False, "hint": "YYYY-MM-DD (for online)"},
    {"key": "note", "label": "Note", "required": False, "hint": "anything the fields above don't capture"},
]

CITATION_TYPES: List[Dict[str, Any]] = [
    {
        "type": "book",
        "label": "Book",
        "fields": [
            {"key": "author", "label": "Author(s)", "required": True, "hint": "semicolon-separated; ‘Family, Given’"},
            {"key": "title", "label": "Title", "required": True, "hint": "the book title"},
            {"key": "editor", "label": "Editor(s)", "required": False, "hint": "if an edited volume"},
            {"key": "edition", "label": "Edition", "required": False, "hint": "2nd, rev., …"},
            {"key": "publisher", "label": "Publisher", "required": False, "hint": ""},
            {"key": "publisher_place", "label": "Place", "required": False, "hint": "city"},
            {"key": "year", "label": "Year", "required": False, "hint": "publication year"},
            {"key": "pages", "label": "Page / locator", "required": False, "hint": "e.g. p. 48, or CP 4.394"},
        ] + _COMMON_TAIL,
    },
    {
        "type": "chapter",
        "label": "Book chapter",
        "fields": [
            {"key": "author", "label": "Author(s)", "required": True, "hint": "of the chapter"},
            {"key": "title", "label": "Chapter title", "required": True, "hint": ""},
            {"key": "container_title", "label": "Book title", "required": True, "hint": "the containing volume"},
            {"key": "editor", "label": "Editor(s)", "required": False, "hint": "of the volume"},
            {"key": "edition", "label": "Edition", "required": False, "hint": ""},
            {"key": "publisher", "label": "Publisher", "required": False, "hint": ""},
            {"key": "publisher_place", "label": "Place", "required": False, "hint": "city"},
            {"key": "year", "label": "Year", "required": False, "hint": ""},
            {"key": "pages", "label": "Pages", "required": False, "hint": "e.g. 120–145"},
        ] + _COMMON_TAIL,
    },
    {
        "type": "article-journal",
        "label": "Journal article",
        "fields": [
            {"key": "author", "label": "Author(s)", "required": True, "hint": ""},
            {"key": "title", "label": "Article title", "required": True, "hint": ""},
            {"key": "container_title", "label": "Journal", "required": True, "hint": "container title"},
            {"key": "volume", "label": "Volume", "required": False, "hint": ""},
            {"key": "issue", "label": "Issue", "required": False, "hint": ""},
            {"key": "year", "label": "Year", "required": False, "hint": ""},
            {"key": "pages", "label": "Pages", "required": False, "hint": ""},
        ] + _COMMON_TAIL,
    },
    {
        "type": "webpage",
        "label": "Online / website",
        "fields": [
            {"key": "author", "label": "Author(s)", "required": False, "hint": "person or organization"},
            {"key": "title", "label": "Title", "required": True, "hint": "of the page / resource"},
            {"key": "container_title", "label": "Site / container", "required": False, "hint": "the website name"},
            {"key": "year", "label": "Year", "required": False, "hint": "or date published"},
            {"key": "url", "label": "URL", "required": True, "hint": "https://…"},
            {"key": "accessed", "label": "Accessed", "required": False, "hint": "YYYY-MM-DD"},
            {"key": "note", "label": "Note", "required": False, "hint": ""},
        ],
    },
    {
        "type": "document",
        "label": "Generic / other",
        "fields": [
            {"key": "author", "label": "Author / source", "required": False, "hint": "manuscript, proceedings, personal communication…"},
            {"key": "title", "label": "Title", "required": True, "hint": ""},
            {"key": "container_title", "label": "Container", "required": False, "hint": "collection / proceedings"},
            {"key": "publisher", "label": "Publisher / institution", "required": False, "hint": ""},
            {"key": "year", "label": "Year", "required": False, "hint": ""},
            {"key": "pages", "label": "Locator", "required": False, "hint": ""},
        ] + _COMMON_TAIL,
    },
]

_TYPES_BY_KEY = {t["type"]: t for t in CITATION_TYPES}


class BibliographyError(Exception):
    """A bibliographic record is missing required fields or malformed."""


def _val(record: Dict[str, Any], key: str) -> str:
    v = record.get(key)
    return str(v).strip() if v is not None else ""


def authors_list(record: Dict[str, Any]) -> List[str]:
    """Author names for ``UoDMetadata.authors`` (semicolon-separated input)."""
    raw = _val(record, "author")
    if not raw:
        return []
    return [a.strip() for a in raw.split(";") if a.strip()]


def validate(record: Dict[str, Any]) -> None:
    """Raise ``BibliographyError`` if a required field for the type is missing."""
    ctype = _val(record, "type") or "document"
    spec = _TYPES_BY_KEY.get(ctype)
    if spec is None:
        raise BibliographyError(
            f"Unknown citation type '{ctype}'. Valid: {sorted(_TYPES_BY_KEY)}."
        )
    missing = [
        f["label"] for f in spec["fields"]
        if f.get("required") and not _val(record, f["key"])
    ]
    if missing:
        raise BibliographyError(
            f"Missing required field(s) for {spec['label']}: {', '.join(missing)}."
        )


def format_citation(record: Dict[str, Any]) -> str:
    """A readable citation string (author-date / Chicago-ish) for a record.

    Defensive: omits fields that are absent rather than emitting empty
    punctuation.  This is the human-readable face stored in
    ``UoDMetadata.source_citation``; the structured record is persisted
    separately for re-styling.
    """
    ctype = _val(record, "type") or "document"

    author = _val(record, "author").replace(";", ";")  # keep as given
    title = _val(record, "title")
    container = _val(record, "container_title")
    publisher = _val(record, "publisher")
    place = _val(record, "publisher_place")
    year = _val(record, "year")
    pages = _val(record, "pages")
    volume = _val(record, "volume")
    issue = _val(record, "issue")
    editor = _val(record, "editor")
    edition = _val(record, "edition")
    doi = _val(record, "doi")
    url = _val(record, "url")
    accessed = _val(record, "accessed")
    note = _val(record, "note")

    parts: List[str] = []

    def add(s: str) -> None:
        if s:
            parts.append(s)

    if ctype == "book":
        add(author + "." if author else "")
        add(f"{title}." if title else "")
        if edition:
            add(f"{edition} ed.")
        if editor:
            add(f"Edited by {editor}.")
        loc = ", ".join([p for p in [place, publisher] if p])
        tail = ": ".join([p for p in [place, publisher] if p]) if (place and publisher) else loc
        if tail and year:
            add(f"{tail}, {year}.")
        elif tail:
            add(f"{tail}.")
        elif year:
            add(f"{year}.")
        if pages:
            add(f"{pages}.")
    elif ctype == "chapter":
        add(author + "." if author else "")
        add(f"“{title}.”" if title else "")
        cont = f"In {container}" if container else ""
        if editor:
            cont += f", edited by {editor}" if cont else f"Edited by {editor}"
        if pages:
            cont += f", {pages}" if cont else pages
        if cont:
            add(cont + ".")
        tail = ": ".join([p for p in [place, publisher] if p]) if (place and publisher) else ", ".join([p for p in [place, publisher] if p])
        if tail and year:
            add(f"{tail}, {year}.")
        elif tail:
            add(f"{tail}.")
        elif year:
            add(f"{year}.")
    elif ctype == "article-journal":
        add(author + "." if author else "")
        add(f"“{title}.”" if title else "")
        jrnl = container
        if volume:
            jrnl += f" {volume}"
        if issue:
            jrnl += f", no. {issue}"
        if year:
            jrnl += f" ({year})"
        if pages:
            jrnl += f": {pages}"
        if jrnl:
            add(jrnl + ".")
    elif ctype == "webpage":
        add(author + "." if author else "")
        add(f"“{title}.”" if title else "")
        if container:
            add(f"{container}.")
        if year:
            add(f"{year}.")
        if url:
            add(url + (f" (accessed {accessed})." if accessed else "."))
    else:  # document / generic
        add(author + "." if author else "")
        add(f"{title}." if title else "")
        if container:
            add(f"In {container}.")
        if publisher:
            add(f"{publisher}.")
        if year:
            add(f"{year}.")
        if pages:
            add(f"{pages}.")

    if doi:
        add(f"https://doi.org/{doi}" if not doi.startswith("http") else doi)
    if note:
        add(note if note.endswith(".") else note + ".")

    return " ".join(parts).strip()
