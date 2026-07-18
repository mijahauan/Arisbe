"""Vault World — World #2's reader: the metadata membrane over an Obsidian-style
vault (spec: docs/superpowers/specs/2026-07-17-vault-cycle-design.md, Stage V0).

Custody constraint (the author's ruling 2 + the vault's ``People/``/``Kith_Kin/``/
``Household/`` scope wrinkle): this module reads **structure only** — path, folder,
frontmatter date/tags, wikilinks, hashtags, file size/mtime. It never reads a note's
body content into an emission. The fixture's ``Ideas/alpha.md`` and journal carry the
sentinel word ``SENTINELBODY`` precisely so a body-content leak is test-detectable.

This is the READER half only (Task 3): ``notes``/``note_id``/``note_facts``/
``attachment_items``/``probe_cost``. Task 4 appends the journal reader
(``journal_paths``/``journal_entries``/``journal_facts``/``journal_horizon_items``).
The feed (``VaultSource``, a ``ProbeDirectedFeedBase`` subclass) is Task 5.

Every emission is an EGIF conjunction of ground atoms and must parse under
``parse_egif``; constants are sanitized by ``_const`` (below), mirroring
``wikidata_source._const`` — quotes/backslashes stripped, non-printables blanked —
credited to that precedent rather than imported (this module owns its own vault-shaped
sanitizer, kept independent of Wikidata's).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from attention_economy import HorizonItem

# -- id sanitizing -----------------------------------------------------------------
# Credited to wikidata_source._const's precedent: strip quotes/backslashes so the
# token can't break out of an EGIF double-quoted constant, and blank any
# non-printable character (raw newlines/tabs turn up in real filenames/paths) so the
# result stays a single well-formed line. Vault ids additionally keep case and slashes
# (a note's relative path IS its natural id), which _const's callers never needed.


def _const(value: str) -> str:
    cleaned = "".join(
        c if c.isprintable() else " "
        for c in value.replace('"', "").replace("\\", ""))
    return cleaned.strip() or "?"


_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_TAG_RE = re.compile(r"(?<!\S)#([A-Za-z][\w/-]*)")
_FRONTMATTER_DATE_RE = re.compile(r"^date:\s*(.+?)\s*$", re.MULTILINE)
_FRONTMATTER_TAGS_INLINE_RE = re.compile(r"^tags:\s*\[([^\]]*)\]\s*$", re.MULTILINE)
_MD_EXT = ".md"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _split_frontmatter(text: str) -> Tuple[Optional[str], str]:
    """The first ``---`` block, parsed leniently: returns (frontmatter_text, body).
    ``frontmatter_text`` is None when the file doesn't open with a fenced block."""
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1:])
            return fm, body
    return None, text


def _frontmatter_date(fm: str) -> Optional[str]:
    m = _FRONTMATTER_DATE_RE.search(fm)
    if not m:
        return None
    raw = m.group(1).strip()
    # accept YYYY-MM or YYYY-MM-DD; normalize to YYYY-MM
    dm = re.match(r"^(\d{4})-(\d{1,2})", raw)
    if not dm:
        return None
    return f"{dm.group(1)}-{int(dm.group(2)):02d}"


def _frontmatter_tags(fm: str) -> List[str]:
    """Inline ``tags: [a, b]`` form (the only form required by the fixture)."""
    m = _FRONTMATTER_TAGS_INLINE_RE.search(fm)
    if not m:
        return []
    return [t.strip() for t in m.group(1).split(",") if t.strip()]


def _mtime_month(path: Path) -> str:
    ts = path.stat().st_mtime
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}"


class VaultWorld:
    """Reads a vault rooted at ``root`` into metadata-only EGIF facts. Deterministic:
    all walks sorted; mtime is read as data (not the wall clock)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    # -- notes -----------------------------------------------------------------
    def notes(self) -> List[str]:
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("*" + _MD_EXT)
            if p.is_file()
        )

    def _stems(self) -> Dict[str, str]:
        """lowercase note stem -> relpath, for wikilink resolution."""
        out: Dict[str, str] = {}
        for n in self.notes():
            stem = Path(n).stem.lower()
            out.setdefault(stem, n)
        return out

    def note_id(self, relpath: str) -> str:
        return _const(relpath)

    def labels(self) -> Dict[str, str]:
        return {self.note_id(n): n for n in self.notes()}

    def _top_dir(self, relpath: str) -> str:
        parts = Path(relpath).parts
        return parts[0] if len(parts) > 1 else ""

    def note_facts(self, relpath: str) -> str:
        path = self.root / relpath
        text = _read_text(path)
        fm, body = _split_frontmatter(text)

        nid = self.note_id(relpath)
        atoms: List[str] = [f'(note "{nid}")']

        top = self._top_dir(relpath)
        if top:
            atoms.append(f'(in_folder "{nid}" "{_const(top)}")')

        atoms.append(f'(kind "{nid}" "md")')

        modified = None
        if fm:
            modified = _frontmatter_date(fm)
        if modified is None:
            modified = _mtime_month(path)
        atoms.append(f'(modified "{nid}" "{modified}")')

        stems = self._stems()
        for raw in _WIKILINK_RE.findall(body):
            target = raw.strip()
            target_relpath = stems.get(target.lower())
            if target_relpath is not None:
                tid = self.note_id(target_relpath)
                atoms.append(f'(links "{nid}" "{tid}")')
            else:
                atoms.append(f'(links_out "{nid}" "{_const(target)}")')

        tags = set(_TAG_RE.findall(body))
        if fm:
            tags.update(_frontmatter_tags(fm))
        for tag in sorted(tags):
            atoms.append(f'(tagged "{nid}" "{_const(tag)}")')

        if top == "Clippings":
            atoms.append(f'(collected_prior "{nid}")')

        return " ".join(atoms)

    # -- attachments (non-md files) -> horizon ----------------------------------
    def _attachment_paths(self) -> List[Path]:
        return sorted(
            (p for p in self.root.rglob("*")
             if p.is_file() and p.suffix.lower() != _MD_EXT),
            key=lambda p: str(p.relative_to(self.root)),
        )

    def attachment_items(self, round_idx: int) -> List[HorizonItem]:
        out: List[HorizonItem] = []
        for p in self._attachment_paths():
            relpath = str(p.relative_to(self.root))
            size = p.stat().st_size
            out.append(HorizonItem(
                kind="extension",
                ref=relpath,
                size=size,
                reason="binary",
                registered_round=round_idx,
            ))
        return out

    def probe_cost(self, relpath: str) -> float:
        size = (self.root / relpath).stat().st_size
        return 1.0 + size / 20_000


__all__ = ["VaultWorld"]
