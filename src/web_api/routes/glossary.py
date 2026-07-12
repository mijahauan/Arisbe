"""
Glossary route — the term definitions the UI shows on hover.

UI Transparency Charter P7 (help lives where the question arises): every
term the interface uses should resolve to a one-line definition within one
hover, with a "more" link into the book.  This route serves those
definitions by parsing ``docs/GLOSSARY.md`` **live** (mtime-cached), so the
glossary document stays the single source of truth — a definition edited
there is what the UI shows, with no build step and no drift.

Two entry shapes are parsed:

- ``### Heading`` entries (the *Abbreviations* and *Key terms* sections):
  the definition is the first paragraph under the heading; the book anchor
  is the heading's quarto slug.
- ``- **Term** — definition`` bullets (the *Terms* section): the anchor is
  the enclosing ``###`` heading's slug.

A term written "A / B" registers both A and B (ligature ↔ line of identity;
warrant ↔ standing); a parenthesized abbreviation ("Existential Graph (EG)")
registers the abbreviation too.  A handful of aliases map UI vocabulary onto
glossary entries (regime-1/2/3 → the three regimes; correspondence → §3.3).

Read-only and additive; consumed by ``web_viewer/js/term-help.js``.
"""

import re
import sys
from pathlib import Path

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import ApiResponse

router = APIRouter(prefix="/glossary")

_REPO_ROOT = Path(__file__).resolve().parents[3]
GLOSSARY_PATH = _REPO_ROOT / "docs" / "GLOSSARY.md"

# The sections whose ### headings are term entries (the others — reading
# order, notation registers — are navigation, not vocabulary).
_ENTRY_SECTIONS = {"Abbreviations", "Key terms"}
_BULLET_SECTION = "Terms"

# UI vocabulary → glossary entry (keys are emitted slugs; values must exist).
_ALIASES = {
    "regime-1": "the-three-regimes",
    "regime-2": "the-three-regimes",
    "regime-3": "the-three-regimes",
    "correspondence": "3.3",
    "s3.3": "3.3",
    "standing": "warrant",
    "corpus": "tomos",
    "iteration": "iteration-and-deiteration",
    "deiteration": "iteration-and-deiteration",
    "line-of-identity": "ligature",
}

_MAX_DEF = 240  # one-line card budget (chars)


def _slug(text: str) -> str:
    """A quarto-compatible anchor slug (lowercased, punctuation dropped)."""
    t = text.strip().lower()
    t = t.replace("①", "1").replace("②", "2").replace("§", "")
    t = re.sub(r"[^\w\s\.-]", "", t, flags=re.UNICODE)
    t = re.sub(r"[\s_]+", "-", t).strip("-")
    return t


def _strip_md(text: str) -> str:
    """Markdown → plain text for a tooltip card."""
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # links → text
    t = t.replace("**", "").replace("`", "")
    t = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", t)  # *emphasis* → plain
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _first_sentences(text: str, budget: int = _MAX_DEF) -> str:
    """Take whole sentences up to the budget (never a mid-word cut)."""
    if len(text) <= budget:
        return text
    out = ""
    for m in re.finditer(r"[^.!?]*[.!?]", text):
        if out and len(out) + len(m.group(0)) > budget:
            break
        out += m.group(0)
        if len(out) >= budget * 0.6:
            break
    return (out or text[:budget].rsplit(" ", 1)[0] + "…").strip()


def _term_keys(raw_term: str) -> list:
    """All slugs a term registers under: split "A / B", pull "(ABBR)"."""
    keys = []
    term = raw_term.strip()
    paren = re.search(r"\(([^)]{1,12})\)", term)
    if paren:
        keys.append(_slug(paren.group(1)))
        term = re.sub(r"\s*\([^)]{1,12}\)", "", term)
    for part in re.split(r"\s*/\s*| and ", term):
        if part.strip():
            keys.append(_slug(part))
    return [k for k in keys if k]


def _parse(md: str) -> dict:
    """GLOSSARY.md → {slug: {term, definition, anchor}}."""
    terms: dict = {}

    def register(raw_term: str, definition: str, anchor: str):
        d = _first_sentences(_strip_md(definition))
        if not d:
            return
        display = _strip_md(re.split(r"\s*/\s*", raw_term)[0])
        entry = {"term": display, "definition": d, "anchor": anchor}
        for key in _term_keys(raw_term):
            terms.setdefault(key, entry)

    section = None
    heading = None
    body: list = []
    pending = None  # (term, [def parts], anchor) — an open bullet entry

    def flush_heading():
        if heading and body and section in _ENTRY_SECTIONS:
            para = " ".join(body).strip()
            # "**Term** — definition" leads the paragraph; fall back to the
            # heading itself when the bold lead is absent.
            m = re.match(r"\*\*(.+?)\*\*\s*[—–-]\s*(.*)", para, re.S)
            if m:
                register(heading, m.group(2), _slug(heading))
                # The bold lead may carry aliases the heading lacks.
                head_key = _term_keys(heading)
                if head_key and head_key[0] in terms:
                    for k in _term_keys(m.group(1)):
                        terms.setdefault(k, terms[head_key[0]])
            else:
                register(heading, para, _slug(heading))

    def flush_bullet():
        nonlocal pending
        if pending:
            t, dparts, anchor = pending
            register(t, " ".join(dparts), anchor)
            pending = None

    for line in md.splitlines():
        h2 = re.match(r"##\s+(.*)", line)
        h3 = re.match(r"###\s+(.*)", line)
        if h3 and not line.startswith("####"):
            flush_heading()
            flush_bullet()
            heading, body = h3.group(1).strip(), []
            continue
        if h2 and not h3:
            flush_heading()
            flush_bullet()
            section, heading, body = h2.group(1).strip(), None, []
            continue
        if section in _ENTRY_SECTIONS and heading is not None:
            if line.strip():
                body.append(line.strip())
            elif body:
                flush_heading()
                heading = None
        elif section == _BULLET_SECTION:
            b = re.match(r"\s*-\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
            if b:
                flush_bullet()
                pending = (b.group(1), [b.group(2)],
                           _slug(heading) if heading else "")
            elif pending and line.strip() and not line.strip().startswith("- "):
                pending[1].append(line.strip())
            else:
                flush_bullet()
    flush_heading()
    flush_bullet()

    # Aliases (only where the target exists — a moved entry degrades softly).
    for alias, target in _ALIASES.items():
        if target in terms:
            terms.setdefault(alias, terms[target])
    return terms


_cache = {"mtime": None, "terms": None}


@router.get("")
@router.get("/")
async def get_glossary():
    """Serve the term → one-line-definition map for the hover cards."""
    try:
        mtime = GLOSSARY_PATH.stat().st_mtime
        if _cache["terms"] is None or _cache["mtime"] != mtime:
            _cache["terms"] = _parse(GLOSSARY_PATH.read_text(encoding="utf-8"))
            _cache["mtime"] = mtime
        return ApiResponse(
            success=True,
            data={"terms": _cache["terms"], "book": "/book/GLOSSARY.html"},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "GLOSSARY_ERROR", "message": str(exc)},
        )
