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

**Reader exclusion** (docs/superpowers/plans/2026-07-18-v2a-oracle-notes.md,
Task 3): a note whose frontmatter declares ``authored_by: arisbe`` — Arisbe's
own oracle notes, written into ``Arisbe/`` by ``oracle_notes.render_note`` —
emits only ``(arisbe_note "id")`` from both ``note_facts`` and
``folder_listing_facts``: no links/tags/modified/collected/in_folder.
Arisbe-ink must never become author-evidence about its own author.

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

from attention_economy import AttentionEconomy, Horizon, HorizonItem, Want
from probe_feed import ProbeDirectedFeedBase

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


# The bound below is the RUN 13 F1¹³ fix (2026-07-18): at real-vault scale,
# constants of 60–142 chars (links_out targets, long filenames, journal eids)
# produced label boxes wider than their residence cells — 53 §3.3 occlusion
# failures at the segment save. The invariant: NO emitted constant exceeds
# _MAX_CONST chars. A longer value becomes an opaque digest id ("x" + 10 hex,
# deterministic) and its original is registered in the world's ``long_labels``
# (the custody-safe decode map the driver writes to the gitignored side-store —
# the original never enters M).
_MAX_CONST = 40


def _digest_id(value: str) -> str:
    import hashlib
    return "x" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_TAG_RE = re.compile(r"(?<!\S)#([A-Za-z][\w/-]*)")
_FRONTMATTER_DATE_RE = re.compile(r"^date:\s*(.+?)\s*$", re.MULTILINE)
_FRONTMATTER_TAGS_INLINE_RE = re.compile(r"^tags:\s*\[([^\]]*)\]\s*$", re.MULTILINE)
_MD_EXT = ".md"

# A root-level note (no containing folder) still needs a real scan-unit bucket —
# "" is falsy and was silently filtered out of top_dirs(), so root notes were never
# scanned, never read, never horizoned: a silent drop. ROOT_BUCKET gives them a
# genuine (non-empty) bucket name that flows uniformly through every _top_dir
# consumer (top_dirs/_seed/_refill/_execute/folder_listing_facts/note_facts).
ROOT_BUCKET = "(root)"

# -- journal date-lines --------------------------------------------------------------
# Shape per the vault spec's two-timeline rule: a bare date-line is an event-time
# claim (year, month, optional day). Year is deliberately NOT range-checked (a
# pre-birth family record with year 1930 is a legitimate entry); month/day ARE
# range-checked, so a shape-matching but out-of-range line (e.g. "2115-21") is
# malformed and goes to the horizon rather than becoming a fact.
_DATE_LINE_SHAPE_RE = re.compile(r"^\d{4}([-/.]\d{1,2}){1,2}$")
_DATE_SPLIT_RE = re.compile(r"[-/.]")


def _parse_date_line(line: str) -> Optional[Tuple[str, bool]]:
    """``None`` if ``line`` doesn't even match the date-line shape. Otherwise
    ``(normalized, valid)`` where ``normalized`` is ``"YYYY-MM"`` (meaningful only
    when ``valid`` is True) and ``valid`` reflects the month/day range check."""
    if not _DATE_LINE_SHAPE_RE.match(line):
        return None
    parts = _DATE_SPLIT_RE.split(line)
    year, month = parts[0], int(parts[1])
    day = int(parts[2]) if len(parts) > 2 else None
    valid = 1 <= month <= 12 and (day is None or 1 <= day <= 31)
    return f"{year}-{month:02d}", valid


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


_FRONTMATTER_AUTHORED_BY_RE = re.compile(r"^authored_by:\s*(.+?)\s*$", re.MULTILINE)


def _frontmatter_authored_by(fm: Optional[str]) -> Optional[str]:
    """The frontmatter's ``authored_by:`` value, or ``None`` if absent/no
    frontmatter — the reader-exclusion test (``== "arisbe"``, case-sensitive:
    the note renderer always writes the literal lowercase token)."""
    if not fm:
        return None
    m = _FRONTMATTER_AUTHORED_BY_RE.search(fm)
    return m.group(1) if m else None


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
        # id → original for every constant that had to be digested to hold the
        # _MAX_CONST bound (F1¹³). Custody: originals live here (and in the
        # driver's gitignored sidecar), never in M.
        self.long_labels: Dict[str, str] = {}

    def _bounded(self, value: str) -> str:
        """An EGIF constant guaranteed ≤ _MAX_CONST chars — the F1¹³ invariant.
        Short values pass through ``_const`` unchanged (fixture-legible); long
        ones become opaque digest ids, originals registered in ``long_labels``."""
        c = _const(value)
        if len(c) <= _MAX_CONST:
            return c
        d = _digest_id(value)
        self.long_labels[d] = value
        return d

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
        return self._bounded(relpath)

    def _is_arisbe_note(self, relpath: str) -> bool:
        """True when ``relpath``'s frontmatter declares ``authored_by: arisbe``
        — the reader-exclusion test (docs/superpowers/plans/
        2026-07-18-v2a-oracle-notes.md, Task 3): Arisbe's own oracle notes must
        never become author-evidence (a link/tag/modified-date reader would
        otherwise happily read Arisbe's own ink back as the author's)."""
        fm, _body = _split_frontmatter(_read_text(self.root / relpath))
        return _frontmatter_authored_by(fm) == "arisbe"

    def labels(self) -> Dict[str, str]:
        return {self.note_id(n): n for n in self.notes()}

    def _top_dir(self, relpath: str) -> str:
        parts = Path(relpath).parts
        return parts[0] if len(parts) > 1 else ROOT_BUCKET

    def top_dirs(self) -> List[str]:
        """Sorted top-level directories that actually hold notes — the vault's
        scan units. An attachment-only directory (e.g. ``attachments/``) has
        nothing to list here; its files reach the horizon via
        ``attachment_items`` instead, never a scan want of their own. Root-level
        notes get the real ``ROOT_BUCKET`` sentinel, not a falsy "" that would
        silently drop out of this set."""
        return sorted({self._top_dir(n) for n in self.notes()})

    def note_facts(self, relpath: str) -> str:
        path = self.root / relpath
        text = _read_text(path)
        fm, body = _split_frontmatter(text)

        nid = self.note_id(relpath)

        # Reader exclusion (Task 3): a note Arisbe itself authored (the oracle
        # notes it writes into Arisbe/) must never become author-evidence —
        # no links/tags/modified/collected/in_folder, only the marker fact.
        if _frontmatter_authored_by(fm) == "arisbe":
            return f'(arisbe_note "{nid}")'

        atoms: List[str] = [f'(note "{nid}")']

        top = self._top_dir(relpath)
        atoms.append(f'(in_folder "{nid}" "{self._bounded(top)}")')

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
                atoms.append(f'(links_out "{nid}" "{self._bounded(target)}")')

        tags = set(_TAG_RE.findall(body))
        if fm:
            tags.update(_frontmatter_tags(fm))
        for tag in sorted(tags):
            atoms.append(f'(tagged "{nid}" "{self._bounded(tag)}")')

        if top == "Clippings":
            atoms.append(f'(collected_prior "{nid}")')

        return " ".join(atoms)

    def folder_listing_facts(self, top_dir: str) -> str:
        """The discovery-only facts a folder scan yields: which notes live here,
        nothing about their content — one ``(note "id") (in_folder "id" top)``
        pair per note, batched in one conjunction (the ``scan`` want's payload).
        An Arisbe-authored note (Task 3's reader exclusion) lists only as
        ``(arisbe_note "id")`` — it is discovered, never folder-evidenced."""
        atoms: List[str] = []
        for n in self.notes():
            if self._top_dir(n) == top_dir:
                nid = self.note_id(n)
                if self._is_arisbe_note(n):
                    atoms.append(f'(arisbe_note "{nid}")')
                    continue
                atoms.append(f'(note "{nid}")')
                atoms.append(f'(in_folder "{nid}" "{_const(top_dir)}")')
        return " ".join(atoms)

    # -- attachments (non-md files) -> horizon ----------------------------------
    # The exclusion is case-SENSITIVE (only the exact ".md" suffix is a note) so
    # a case-variant markdown file (e.g. "Note.MD") — invisible to notes()'s
    # rglob("*.md"), which is itself case-sensitive on a case-sensitive
    # filesystem — still lands somewhere: on the horizon, counted, never
    # silently absent from both registers at once.
    def _attachment_paths(self) -> List[Path]:
        return sorted(
            (p for p in self.root.rglob("*")
             if p.is_file() and p.suffix != _MD_EXT),
            key=lambda p: str(p.relative_to(self.root)),
        )

    def attachment_items(self, round_idx: int) -> List[HorizonItem]:
        out: List[HorizonItem] = []
        for p in self._attachment_paths():
            relpath = str(p.relative_to(self.root))
            size = p.stat().st_size
            is_case_variant_md = p.suffix.lower() == _MD_EXT
            out.append(HorizonItem(
                kind="extension",
                ref=relpath,
                size=size,
                reason="case_variant_md" if is_case_variant_md else "binary",
                registered_round=round_idx,
            ))
        return out

    def probe_cost(self, relpath: str) -> float:
        size = (self.root / relpath).stat().st_size
        return 1.0 + size / 20_000

    # -- journal (two timelines held apart) -------------------------------------
    # A journal is a flat file of bare date-lines followed by free-text entry
    # bodies. Only the date-line is a fact-bearing claim, and only about
    # EVENT time — when the entry says it happened. Writing time (when the
    # words were actually typed) is deliberately absent from V0's facts; it's
    # a hypothesis for a later stage, not something this reader can observe
    # from the text alone. Entry bodies are never read into an emission
    # (custody constraint), only counted (`entry_lines`).

    def journal_paths(self) -> List[str]:
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.rglob("Journal*" + _MD_EXT)
            if p.is_file()
        )

    def journal_entries(
        self, relpath: str
    ) -> Tuple[List[Tuple[str, int, int]], List[Tuple[int, str]]]:
        """Splits the file into ``(event_date, line_no, n_lines)`` entries at each
        VALID date-line. A shape-matching but out-of-range date-line (flagged) does
        NOT start a new entry — its line (and any following body text) stays part
        of whichever entry is currently open, and its ``(line_no, raw)`` — the
        date-line's shape only, never surrounding content — is returned as a
        second list."""
        path = self.root / relpath
        raw_lines = _read_text(path).split("\n")
        if raw_lines and raw_lines[-1] == "":
            raw_lines = raw_lines[:-1]  # trailing blank from the final newline

        entries: List[Tuple[str, int, int]] = []
        flagged: List[Tuple[int, str]] = []
        cur_date: Optional[str] = None
        cur_line_no = 0
        cur_n = 0

        for i, raw in enumerate(raw_lines, start=1):
            line = raw.strip()
            parsed = _parse_date_line(line) if line else None
            if parsed is not None:
                norm, valid = parsed
                if valid:
                    if cur_date is not None:
                        entries.append((cur_date, cur_line_no, cur_n))
                    cur_date, cur_line_no, cur_n = norm, i, 0
                    continue
                flagged.append((i, line))
            if cur_date is not None:
                cur_n += 1

        if cur_date is not None:
            entries.append((cur_date, cur_line_no, cur_n))

        return entries, flagged

    def journal_facts(self, relpath: str) -> str:
        """**Whole-file journal reader** — every entry in one conjunction.

        Kept as a compatibility reader (existing tests, one-shot inspection);
        at real-vault scale it is unaffordable AND unwieldy (F3¹³, RUN 13): a
        1,583-entry journal (~2.4MB) priced its single want at ``probe_cost``
        ≈120 — no round's attention budget ever chose it next to any 1-cost
        scan want, so the journal never got read — and one 1,583-entry
        conjunction is a bad layout unit regardless. The feed path is
        :meth:`journal_facts_batches` (via :meth:`_journal_entry_batches`),
        one affordable want per ≤40-entry batch.
        """
        entries, _flagged = self.journal_entries(relpath)
        atoms: List[str] = []
        for event_date, line_no, n_lines in entries:
            eid = self._bounded(f"{relpath}#L{line_no}")
            atoms.append(f'(journal_entry "{eid}")')
            atoms.append(f'(entry_date "{eid}" "{event_date}")')
            atoms.append(f'(entry_lines "{eid}" "{n_lines}")')
        return " ".join(atoms)

    def _journal_entry_batches(
        self, relpath: str, batch_size: int = 40
    ) -> List[Tuple[str, int]]:
        """Groups ``relpath``'s entries into batches of at most ``batch_size``,
        each rendered to its own parseable EGIF conjunction (the batch's
        ``journal_entry``/``entry_date``/``entry_lines`` atoms) alongside its
        **line-span** (the last line the batch's entries cover minus the
        first) — the feed's affordable per-batch cost proxy (F3¹³), the same
        shape as :meth:`probe_cost`'s byte-based formula but for a batch that
        has no file size of its own. One call to :meth:`journal_entries`
        (one file read) regardless of how many batches result; batches cover
        every entry exactly once, in file order."""
        entries, _flagged = self.journal_entries(relpath)
        out: List[Tuple[str, int]] = []
        for i in range(0, len(entries), batch_size):
            group = entries[i:i + batch_size]
            atoms: List[str] = []
            for event_date, line_no, n_lines in group:
                eid = self._bounded(f"{relpath}#L{line_no}")
                atoms.append(f'(journal_entry "{eid}")')
                atoms.append(f'(entry_date "{eid}" "{event_date}")')
                atoms.append(f'(entry_lines "{eid}" "{n_lines}")')
            first_line = group[0][1]
            last_date, last_line_no, last_n = group[-1]
            span = (last_line_no + last_n) - first_line
            out.append((" ".join(atoms), span))
        return out

    def journal_facts_batches(self, relpath: str, batch_size: int = 40) -> List[str]:
        """**Batched journal reader** (F3¹³, RUN 13): ``relpath``'s entries
        split into groups of at most ``batch_size``, each its own parseable
        EGIF conjunction — batches cover every entry exactly once, in file
        order. Where :meth:`journal_facts` prices and emits the whole file as
        one unaffordable, unwieldy unit, this is what the feed wants
        instead: one small, affordable want per batch (see
        :meth:`VaultFeed._seed`)."""
        return [text for text, _span in self._journal_entry_batches(relpath, batch_size)]

    def journal_horizon_items(self, round_idx: int) -> List[HorizonItem]:
        out: List[HorizonItem] = []
        for relpath in self.journal_paths():
            _entries, flagged = self.journal_entries(relpath)
            for line_no, raw in flagged:
                out.append(HorizonItem(
                    kind="date",
                    ref=f"{_const(relpath)}#L{line_no}",
                    size=len(raw),
                    reason="malformed_date_line",
                    registered_round=round_idx,
                ))
        return out


# --------------------------------------------------------------------------- #
# The feed (Task 5) — the socket's fourth consumer. Generic drain-refill      #
# mechanics (AttentionEconomy + chooser/journal + the round loop) live in     #
# probe_feed.ProbeDirectedFeedBase; VaultFeed supplies only the              #
# vault-specific seeding/refill/dispatch, with the journal as the severity   #
# spine: a journal want's severity 8.0 outranks a folder scan's default 1.0, #
# so the author's own datelined voice lands before generic listing.          #
# --------------------------------------------------------------------------- #

_LINKS_FACT_RE = re.compile(r'\(links "[^"]*" "([^"]*)"\)')


class VaultFeed(ProbeDirectedFeedBase):
    """agon_evolution.Proposer over the vault's metadata membrane. Every vault
    want settles on execution (``persistent_kinds`` is empty) — a note is
    re-read only if a later stage's decay pressure re-wants it, not by this
    feed re-proposing it itself."""

    persistent_kinds: frozenset = frozenset()

    def __init__(self, world: VaultWorld, economy: AttentionEconomy, *,
                 horizon: Optional[Horizon] = None, chooser=None,
                 probe_budget: int = 1, journal=None):
        super().__init__(economy, chooser=chooser, probe_budget=probe_budget,
                          journal=journal)
        self._world = world
        self._horizon = horizon if horizon is not None else Horizon()
        self._scanned_dirs: set = set()   # top dirs whose scan want has executed
        self._read_notes: set = set()     # relpaths whose read want has executed
        self._link_targets: set = set()   # note ids seen as a `links` target so far
        # relpath -> batch texts, computed once at seed time (F3¹³) so each
        # journal want's _execute is a plain lookup, not a re-read/re-split.
        self._journal_batches: Dict[str, List[str]] = {}

    # -- intake -----------------------------------------------------------------
    def _seed(self, round_idx: int):
        for top in self._world.top_dirs():
            self._economy.register(Want(
                kind="scan", key=("scan", top), payload=top,
                cost=1.0, created_round=round_idx))
        # F3¹³ (RUN 13): one journal want per BATCH, not per file — a real
        # journal (~1,583 entries, ~2.4MB) priced as a single want costs
        # ~120, unaffordable next to any 1-cost scan want, so it never got
        # read; batching also keeps each want's emission a reasonable layout
        # unit. Batches are computed once here (one file read); severity
        # stays 8.0 so the author's own datelined voice still outranks
        # generic listing, batch by batch.
        for relpath in self._world.journal_paths():
            batches = self._world._journal_entry_batches(relpath)
            self._journal_batches[relpath] = [text for text, _span in batches]
            for idx, (_text, span) in enumerate(batches):
                self._economy.register(Want(
                    kind="journal", key=("journal", relpath, idx),
                    payload=(relpath, idx),
                    cost=1.0 + span / 20_000, severity=8.0,
                    created_round=round_idx))
        # Attachments and malformed journal date-lines never become facts —
        # they're registered to the horizon once, at seed time, where they
        # wait to be re-attempted as legibility improves in a later stage.
        for item in self._world.attachment_items(round_idx):
            self._horizon.register(item)
        for item in self._world.journal_horizon_items(round_idx):
            self._horizon.register(item)

    def _refill(self, round_idx: int):
        outstanding = sum(1 for w in self._economy.wants() if w.kind == "read")
        candidates = [
            n for n in self._world.notes()
            if self._world._top_dir(n) in self._scanned_dirs
            and n not in self._read_notes
        ]
        for relpath in candidates:            # bounded scan — finite discovered set
            if outstanding >= 5:
                break
            severity = 2.0 if self._world.note_id(relpath) in self._link_targets else 1.0
            before = self._economy.dropped
            registered = self._economy.register(Want(
                kind="read", key=("read", relpath), payload=relpath,
                cost=self._world.probe_cost(relpath), severity=severity,
                created_round=round_idx))
            if registered:
                outstanding += 1
            elif self._economy.dropped > before:
                break                          # pool at cap; the drop is counted

    # -- emission dispatch --------------------------------------------------------
    def _execute(self, w: Want):
        if w.kind == "scan":
            top = w.payload
            facts = self._world.folder_listing_facts(top)
            self._scanned_dirs.add(top)
            return facts or None
        elif w.kind == "read":
            relpath = w.payload
            facts = self._world.note_facts(relpath)
            self._read_notes.add(relpath)
            self._link_targets.update(_LINKS_FACT_RE.findall(facts))
            return facts or None
        elif w.kind == "journal":
            relpath, idx = w.payload
            batch = self._journal_batches.get(relpath, [])
            text = batch[idx] if 0 <= idx < len(batch) else None
            return text or None
        else:
            return None


__all__ = ["VaultWorld", "VaultFeed"]
