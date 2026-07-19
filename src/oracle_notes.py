"""Oracle notes — the V2a Obsidian-native surface (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2, ruled 2026-07-18). Arisbe writes
questions notes into exactly one vault folder (``Arisbe/``); the next poll reads
answers back through the same membrane.

**Stage split:** Task 1 built candidates, the seal, and the note renderer, all
offline and deterministic (no wall-clock/RNG; ``note_date`` is caller-supplied).
Task 2 added the other half of the loop: ``parse_note`` (recovering the
author's edits from the raw markdown), ``score`` (the forecast-vs-answer
heuristic), and ``OracleLedger`` (JSONL persistence joining asked forecasts to
recorded outcomes). This task (Task 3) adds ``conjectures_section`` (a plain-
English gloss of each law the automated model-development loop has admitted,
so the author reads what Arisbe currently believes, not just ink) and wires it
into ``render_note``. Banking an answered forecast into M as a quoted
attributed cell (``(asserted "author" <quote> )``, provenance
``oracle-answer``) is V2a.2 and out of scope here — V2a.1 only banks answers in
the run's side-store with marker facts.

Task 4 (driver wiring, ``tools/run_vault_v0.py``) needed two small additions
here: ``select_within_budget`` made public (the driver records exactly the
selected candidates in the ledger, not just what got rendered) and
``ParsedNote.budget_parsed`` (a previous note's malformed budget knob must be
announced, never silently guessed).

**Seal-then-reveal:** ``seal(forecast)`` is the SHA-256 hex commitment; the
question block prints only the hash, never the plaintext. The plaintext lives
in the caller's gitignored side-store (``oracle/forecasts.jsonl``) and reaches
the note again only through a later ``## Reveals`` section, once the answer is
in hand.

**Qid recovery (Task 2):** each rendered question block carries an invisible
``<!-- qid: ... -->`` HTML comment right under its header — Obsidian's preview
renderer hides HTML comments, so the author never sees it, but ``parse_note``
uses it to recover which question an ``**A:**`` line belongs to without relying
on question text (which the author might reasonably edit or quote back).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


# -- the candidate -------------------------------------------------------------


@dataclass
class QuestionCandidate:
    """One question the docket could ask, forecast already attached (the
    resolving shape — Arisbe predicts, then asks, then scores the miss).
    ``qid`` is caller-supplied and deterministic (e.g. ``"prov:<note_id>"``),
    so the same run reproduces the same candidate identity."""
    qid: str
    tier: str          # "quick" | "short" | "reflective"
    text: str
    why: str
    settles: str
    forecast: str
    severity: float = 1.0


def seal(forecast: str) -> str:
    """The forecast's commitment: a SHA-256 hex digest of its UTF-8 bytes.
    Checkable later (recompute and compare), never itself revealing."""
    return hashlib.sha256(forecast.encode("utf-8")).hexdigest()


# -- candidate sources (V2a.1) --------------------------------------------------
# Four sources, in this fixed order (the plan's "deterministic order"):
#   1. provenance   — a Clippings-bucketed note, authored-vs-collected
#   2. multi-journal — more than one journal file, genuine-vs-fragment
#   3. horizon       — the largest not-yet-legible things
#   4. writing-time  — the one standing reflective question
# `known_laws` is accepted for interface symmetry with a later source (a law
# the docket wants confirmed) but has no V2a.1 use yet — reserved, not wired.


def _decode_map(world, labels: Optional[dict]) -> Dict[str, str]:
    """The id -> original-path decode table: whatever the caller passed in
    ``labels``, topped up from ``world.long_labels`` (the digested-constant
    registry) for any id the caller's map doesn't already cover."""
    merged: Dict[str, str] = dict(labels or {})
    for k, v in getattr(world, "long_labels", {}).items():
        merged.setdefault(k, v)
    return merged


def _decode(decode: Dict[str, str], key: str, fallback: str) -> str:
    return decode.get(key, fallback)


def _provenance_candidates(world, decode: Dict[str, str]) -> List[QuestionCandidate]:
    """Up to 3 notes bucketed ``collected_prior`` (top dir == ``Clippings``):
    is this the author's own writing, or something collected from elsewhere?"""
    out: List[QuestionCandidate] = []
    clippings = [n for n in world.notes() if world._top_dir(n) == "Clippings"][:3]
    for relpath in clippings:
        nid = world.note_id(relpath)
        path = _decode(decode, nid, relpath)
        out.append(QuestionCandidate(
            qid=f"prov:{nid}", tier="quick",
            text=f"Is `{path}` collected from elsewhere, or your own writing?",
            why="its folder reads as a collected-prior bucket (Clippings), "
                "worth confirming rather than assuming",
            settles="whether this note counts as the author's own authored "
                    "voice or an imported clipping",
            forecast="collected", severity=3.0,
        ))
    return out


def _multi_journal_candidates(world, decode: Dict[str, str]) -> List[QuestionCandidate]:
    """When more than one journal-shaped file exists, one question per extra
    file (up to 2, beyond the first/main): genuine journal, or a fragment/copy?"""
    paths = world.journal_paths()
    if len(paths) <= 1:
        return []
    main = paths[0]
    main_decoded = _decode(decode, world.note_id(main), main)
    out: List[QuestionCandidate] = []
    for relpath in paths[1:3]:
        nid = world.note_id(relpath)
        path = _decode(decode, nid, relpath)
        out.append(QuestionCandidate(
            qid=f"journal:{nid}", tier="quick",
            text=f"Is `{path}` a genuine journal, or a fragment/copy of "
                 f"`{main_decoded}`?",
            why="more than one journal-shaped file exists; only one should "
                "carry the standing event-time record",
            settles="whether this file's entries double-count against the "
                    "main journal",
            forecast="fragment", severity=3.0,
        ))
    return out


def _horizon_candidates(horizon, decode: Dict[str, str]) -> List[QuestionCandidate]:
    """Up to 2 largest open horizon items (biggest first, ref as the
    deterministic tie-break): what is this not-yet-legible thing?"""
    if horizon is None:
        return []
    items = sorted(horizon.open_items(), key=lambda i: (-i.size, i.ref))[:2]
    out: List[QuestionCandidate] = []
    for item in items:
        ref = _decode(decode, item.ref, item.ref)
        out.append(QuestionCandidate(
            qid=f"horizon:{item.ref}", tier="short",
            text=f"What is `{ref}` (a `{item.kind}` I can't read yet)? "
                 f"One line is plenty.",
            why="it sits on the horizon, registered but never resolved "
                "into a fact",
            settles="what this thing actually is, so a future pass can "
                    "read it properly",
            forecast="unknown", severity=2.0,
        ))
    return out


def _writing_time_candidate() -> QuestionCandidate:
    """The standing reflective question (contemporaneous-vs-reconstructed):
    offered until answered once. V2a.1 always offers it — the once-answered
    gate is the ledger's job (Task 2), not this source's."""
    return QuestionCandidate(
        qid="journal-timelines", tier="reflective",
        text="When you journal, are you usually writing about what's "
             "happening right now, or catching up on things after the fact?",
        why="the reader only ever sees event-time (the date-line); "
            "writing-time is a standing hypothesis this loop can't observe "
            "from the text alone",
        settles="whether journal entries should be read as contemporaneous "
                "or reconstructed",
        forecast="reconstructed", severity=1.0,
    )


def candidates_from_run(world, horizon, known_laws: List[str],
                         labels: dict) -> List[QuestionCandidate]:
    """The V2a.1 candidate list, in the fixed source order above. Tolerates
    ``horizon=None`` (skip horizon questions entirely — no crash)."""
    decode = _decode_map(world, labels)
    out: List[QuestionCandidate] = []
    out.extend(_provenance_candidates(world, decode))
    out.extend(_multi_journal_candidates(world, decode))
    out.extend(_horizon_candidates(horizon, decode))
    out.append(_writing_time_candidate())
    return out


# -- the note renderer -----------------------------------------------------------


def select_within_budget(candidates: List[QuestionCandidate],
                          budget: dict) -> List[QuestionCandidate]:
    """At most ``budget['max']`` questions, at most ``budget['reflective']``
    of them reflective-tier; highest severity first, stable beyond that
    (Python's sort is stable, so equal-severity candidates keep their
    original relative order). A reflective candidate beyond the cap is
    skipped, not counted against the room left for lower-tier candidates.
    Public (Task 4): the driver needs the exact selected set to record each
    asked question in the ledger, not just the rendered text."""
    max_q = budget.get("max", len(candidates))
    max_refl = budget.get("reflective", max_q)
    ordered = sorted(candidates, key=lambda c: -c.severity)
    selected: List[QuestionCandidate] = []
    refl_count = 0
    for c in ordered:
        if len(selected) >= max_q:
            break
        if c.tier == "reflective":
            if refl_count >= max_refl:
                continue
            refl_count += 1
        selected.append(c)
    return selected


def _topic(qid: str) -> str:
    """The header's topic label: the qid's namespace prefix (``"prov"`` from
    ``"prov:<id>"``), or the whole qid when it carries none (the standing
    ``"journal-timelines"``)."""
    return qid.split(":", 1)[0]


def _frontmatter(note_date: str, run_id: str, segment: int, budget: dict) -> str:
    lines = [
        "---",
        "authored_by: arisbe",
        f"run: {run_id}",
        f"segment: {segment}",
        f"date: {note_date}",
        f"budget: {{max: {budget['max']}, reflective: {budget['reflective']}}}",
        "---",
    ]
    return "\n".join(lines)


def _render_reveals(reveals: List[dict]) -> str:
    lines = ["## Reveals", ""]
    for r in reveals:
        lines.append(
            f"- `{r['qid']}`: forecast **{r['forecast_plain']}** "
            f"(`sha256:{r['forecast_hash']}`) — answer: \"{r['answer']}\" "
            f"→ **{r['verdict']}**"
        )
    return "\n".join(lines)


def _render_question_block(n: int, c: QuestionCandidate) -> str:
    lines = [
        f"## Q{n} · {c.tier} — {_topic(c.qid)}",
        f"<!-- qid: {c.qid} -->",
        "",
        c.text,
        "",
        f"*Why asked:* {c.why}",
        f"*Would settle:* {c.settles}",
        f"*Forecast (sealed):* `sha256:{seal(c.forecast)}`",
        "**A:**",
    ]
    return "\n".join(lines)


def render_note(candidates: List[QuestionCandidate], *, note_date: str,
                 run_id: str, segment: int, budget: dict,
                 reveals: Optional[List[dict]],
                 conjectures: Optional[str] = None) -> str:
    """The note's markdown: frontmatter, an optional ``## Reveals`` section
    (the previous note's scored answers), an optional ``## Conjectures``
    section (Task 3 — the caller passes the already-rendered string from
    ``conjectures_section``, or ``None``/``""`` to omit it), then one block
    per budgeted question. Forecasts never appear as plaintext — only their
    seal."""
    parts: List[str] = [_frontmatter(note_date, run_id, segment, budget)]
    if reveals:
        parts.append(_render_reveals(reveals))
    if conjectures:
        parts.append(conjectures)
    for n, c in enumerate(select_within_budget(candidates, budget), start=1):
        parts.append(_render_question_block(n, c))
    return "\n\n".join(parts) + "\n"


# -- the conjectures section (Task 3) --------------------------------------------
#
# A conjecture, here, is a law the automated model-development loop *admitted*
# (``EvolutionResult.known_laws`` — currently-standing generalizations, already
# pruned of anything a later challenge relinquished) — surfaced so the author
# can read what Arisbe has come to believe, in English, not just as ink. The
# gloss prefers ``eg_to_english.idiomatic_reading`` (it takes a real EGI and
# reads any admitted-law shape, not just the unary-subsumption one); a law
# that fails to parse or read falls back to a structural gloss keyed off the
# same unary-subsumption pattern ``arithmetic_world.test_law_instance`` uses
# (``~[ (P *x) ~[ (Q x) ] ]``), and anything stranger still gets the honest
# placeholder "a standing law" rather than a fabricated reading.

_LAW_RE = re.compile(r'~\[\s*\((\w+) \*x\)\s*~\[\s*\((\w+) x\)\s*\]\s*\]')


def _law_gloss(law_egif: str) -> str:
    try:
        from egif_parser_dau import parse_egif
        from eg_to_english import idiomatic_reading
        gloss = idiomatic_reading(parse_egif(law_egif))
        if gloss:
            return gloss
    except Exception:
        pass
    m = _LAW_RE.match(law_egif.strip())
    if m:
        p, q = m.group(1), m.group(2)
        return f"whenever ({p} x) holds, ({q} x) follows"
    return "a standing law"


def conjectures_section(known_laws: List[str], discoveries) -> str:
    """``"## Conjectures"`` — one bullet per currently admitted law
    (``known_laws``): a plain-English gloss (:func:`_law_gloss`) followed by
    the law's own EGIF in a code span. ``discoveries`` (an
    ``EvolutionResult.discoveries`` list) is accepted for interface symmetry
    with the run result the driver holds — a future pass may use it to
    annotate *when* a law was admitted or superseded — but has no V2a.1
    rendering use yet. Empty string (nothing to show) when ``known_laws`` is
    empty."""
    if not known_laws:
        return ""
    lines = ["## Conjectures", ""]
    for law in known_laws:
        lines.append(f"- {_law_gloss(law)} — the graph: `{law}`")
    return "\n".join(lines)


# -- the parser (Task 2) --------------------------------------------------------
#
# The rendered shape guarantees three structural facts a modest regex parser
# can lean on:
#  - the frontmatter is a single ``---`` … ``---`` block at the very start;
#  - an optional ``## Reveals`` section (if present) always precedes any
#    question block;
#  - each question block opens with ``## Q<n> · <tier> — <topic>`` followed
#    immediately by the invisible ``<!-- qid: ... -->`` comment, and its
#    answer region runs from ``**A:**`` to the FIRST of: a blank line (``\n\n``
#    — the natural paragraph break, which is also exactly what separates one
#    rendered block from the next), the next ``## `` header, or end of text.
#    That boundary choice is what lets an author leave a question blank *and*
#    append free-standing prose after it in the same edit: the blank line
#    between "nothing typed" and "unrelated musings below" is the same blank
#    line that already separates rendered blocks, so it reads as a genuine
#    paragraph break rather than as more of the (absent) answer. A genuinely
#    multi-paragraph answer that itself contains a blank line will only have
#    its first paragraph recovered — a documented limit of this heuristic
#    parser, not a claim of full prose understanding.


@dataclass
class ParsedNote:
    """What `parse_note` recovers from one note's raw markdown, after the
    author has (possibly) edited it in place."""
    budget: dict
    answers: Dict[str, str] = field(default_factory=dict)
    declined: Set[str] = field(default_factory=set)
    ignored: Set[str] = field(default_factory=set)
    stray: str = ""
    budget_parsed: bool = True
    """False when the ``budget: {...}`` line was missing/malformed and
    ``budget`` fell back to ``_DEFAULT_BUDGET`` (Task 4's driver-side guard:
    print a warning rather than silently adopting defaults)."""


_DEFAULT_BUDGET = {"max": 5, "reflective": 1}

_BUDGET_RE = re.compile(r"budget:\s*\{max:\s*(\d+),\s*reflective:\s*(\d+)\}")
_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---", re.DOTALL)
_REVEALS_RE = re.compile(r"## Reveals\n.*?(?=\n\n## |\Z)", re.DOTALL)
_QBLOCK_RE = re.compile(
    r"## Q\d+ · \S+ — \S+\n"
    # qid is NOT \S+: a real vault path (this fixture's own "Clippings/saved
    # page.md") can carry a space, so the id must be matched non-greedily up
    # to the literal " -->" rather than stopping at the first whitespace.
    r"<!-- qid: (?P<qid>[^\n]+?) -->\n"
    r"(?P<body>.*?)"
    r"\*\*A:\*\*"
    r"(?P<answer>.*?)(?=\n\n|\n## |\Z)",
    re.DOTALL,
)


def parse_note(text: str) -> ParsedNote:
    """Recover the author's edits from a rendered-then-edited note's raw
    markdown: the (possibly edited) budget knob, each question's answer text
    (non-empty), the set of declined qids (an ``**A:**`` line whose content,
    stripped, reads ``declined`` case-insensitively), the set of ignored
    qids (an ``**A:**`` line left empty), and any stray text the author wrote
    outside every recognized block (frontmatter / Reveals / question blocks)
    — kept verbatim as evidence, not interpreted."""
    m = _BUDGET_RE.search(text)
    budget = ({"max": int(m.group(1)), "reflective": int(m.group(2))}
              if m else dict(_DEFAULT_BUDGET))
    budget_parsed = m is not None

    answers: Dict[str, str] = {}
    declined: Set[str] = set()
    ignored: Set[str] = set()
    consumed: List[tuple] = []

    fm = _FRONTMATTER_RE.search(text)
    if fm:
        consumed.append(fm.span())

    rv = _REVEALS_RE.search(text)
    if rv:
        consumed.append(rv.span())

    for qm in _QBLOCK_RE.finditer(text):
        consumed.append(qm.span())
        qid = qm.group("qid")
        answer = qm.group("answer").strip()
        if not answer:
            ignored.add(qid)
        elif answer.lower() == "declined":
            declined.add(qid)
        else:
            answers[qid] = answer

    consumed.sort()
    stray_parts: List[str] = []
    cursor = 0
    for start, end in consumed:
        if start > cursor:
            stray_parts.append(text[cursor:start])
        cursor = max(cursor, end)
    if cursor < len(text):
        stray_parts.append(text[cursor:])
    stray = "\n".join(p.strip() for p in stray_parts if p.strip()).strip()

    return ParsedNote(budget=budget, answers=answers, declined=declined,
                       ignored=ignored, stray=stray, budget_parsed=budget_parsed)


def score(forecast_plain: str, answer: str) -> str:
    """Score a forecast against the author's answer. Deliberately modest: a
    case-insensitive substring test (does the forecast's own text appear
    somewhere inside the answer?), nothing more — no NL understanding, no
    negation handling, no paraphrase recognition. ``"unscored"`` when the
    forecast itself was ``"unknown"`` (the horizon questions never forecast
    an answer to check against, so there is nothing to score). V2a.2 is
    named as the place a real interpretation step would replace this."""
    if forecast_plain.strip().lower() == "unknown":
        return "unscored"
    return "hit" if forecast_plain.strip().lower() in answer.lower() else "miss"


def note_substantially_answered(parsed: ParsedNote) -> bool:
    """At least half of a note's questions were answered or declined
    (silence — ``ignored`` — doesn't count). A note with zero questions
    (e.g. every candidate was suppressed) is vacuously substantial; deciding
    what to do with an absent note entirely is the driver's job, not this
    predicate's."""
    total = len(parsed.answers) + len(parsed.declined) + len(parsed.ignored)
    if total == 0:
        return True
    resolved = len(parsed.answers) + len(parsed.declined)
    return resolved * 2 >= total


# -- the ledger (Task 2) ---------------------------------------------------------


class OracleLedger:
    """Append-only JSONL persistence for the ask/answer loop, under
    ``dir_path`` (created if absent). Two files, one concern each:
    ``forecasts.jsonl`` (one record per asked question — this is where the
    forecast plaintext actually lives; the note itself only ever carries the
    seal) and ``outcomes.jsonl`` (one record per parsed answer/decline/
    ignore). Nothing is cached in memory — each read re-scans its file, so a
    ledger opened fresh in a later process (a later run) sees everything an
    earlier one wrote."""

    def __init__(self, dir_path):
        self.dir_path = Path(dir_path)
        self.dir_path.mkdir(parents=True, exist_ok=True)
        self._forecasts_path = self.dir_path / "forecasts.jsonl"
        self._outcomes_path = self.dir_path / "outcomes.jsonl"

    @staticmethod
    def _append(path: Path, record: dict) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    @staticmethod
    def _read_all(path: Path) -> List[dict]:
        if not path.exists():
            return []
        out: List[dict] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def record_asked(self, note_date: str, qid: str, tier: str,
                      forecast_plain: str, forecast_hash: str) -> None:
        self._append(self._forecasts_path, {
            "note_date": note_date, "qid": qid, "tier": tier,
            "forecast_plain": forecast_plain, "forecast_hash": forecast_hash,
        })

    def record_outcome(self, qid: str, status: str, answer_text: str,
                        answered_note_date: str) -> None:
        self._append(self._outcomes_path, {
            "qid": qid, "status": status, "answer_text": answer_text,
            "answered_note_date": answered_note_date,
        })

    def asked_ever(self, qid: str) -> bool:
        """The standing-question suppressor: has this qid ever been asked
        (in any note, any run)? Callers use this to drop a question — most
        importantly the standing reflective one — from a fresh candidate
        list once it has been asked at all, regardless of how it was
        answered."""
        return any(r["qid"] == qid for r in self._read_all(self._forecasts_path))

    def outcomes(self) -> List[dict]:
        return self._read_all(self._outcomes_path)

    def _latest_forecast(self, qid: str) -> Optional[dict]:
        matches = [r for r in self._read_all(self._forecasts_path)
                   if r["qid"] == qid]
        return matches[-1] if matches else None

    def build_reveals(self, parsed: ParsedNote) -> List[dict]:
        """Join this note's genuine answers (``parsed.answers`` — declines
        and silences carry no forecast to score) to the forecast this ledger
        recorded when the question was asked, producing the reveal dicts
        Task 1's renderer already knows how to print (``qid``,
        ``forecast_plain``, ``forecast_hash``, ``answer``, ``verdict``). A
        qid with no recorded forecast (asked outside this ledger, or never
        asked) is silently skipped — nothing to reveal against."""
        reveals: List[dict] = []
        for qid in sorted(parsed.answers):
            forecast = self._latest_forecast(qid)
            if forecast is None:
                continue
            answer = parsed.answers[qid]
            reveals.append({
                "qid": qid,
                "forecast_plain": forecast["forecast_plain"],
                "forecast_hash": forecast["forecast_hash"],
                "answer": answer,
                "verdict": score(forecast["forecast_plain"], answer),
            })
        return reveals


__all__ = [
    "QuestionCandidate", "seal", "candidates_from_run", "render_note",
    "select_within_budget", "ParsedNote", "parse_note", "score",
    "note_substantially_answered", "OracleLedger", "conjectures_section",
]
