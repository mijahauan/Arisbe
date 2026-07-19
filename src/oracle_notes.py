"""Oracle notes — the V2a Obsidian-native surface (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2, ruled 2026-07-18). Arisbe writes
questions notes into exactly one vault folder (``Arisbe/``); the next poll reads
answers back through the same membrane.

**Stage split:** this module is the V2a.1 build — candidates, the seal, and the
note renderer, all offline and deterministic (no wall-clock/RNG; ``note_date``
is caller-supplied). Answer-parsing, forecast-scoring, and the reveal ledger are
Task 2; banking an answered forecast into M as a quoted attributed cell
(``(asserted "author" <quote> )``, provenance ``oracle-answer``) is V2a.2 and
out of scope here — V2a.1 only banks answers in the run's side-store with
marker facts.

**Seal-then-reveal:** ``seal(forecast)`` is the SHA-256 hex commitment; the
question block prints only the hash, never the plaintext. The plaintext lives
in the caller's gitignored side-store (``oracle/forecasts.jsonl``) and reaches
the note again only through a later ``## Reveals`` section, once the answer is
in hand.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional


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


def _select_within_budget(candidates: List[QuestionCandidate],
                           budget: dict) -> List[QuestionCandidate]:
    """At most ``budget['max']`` questions, at most ``budget['reflective']``
    of them reflective-tier; highest severity first, stable beyond that
    (Python's sort is stable, so equal-severity candidates keep their
    original relative order). A reflective candidate beyond the cap is
    skipped, not counted against the room left for lower-tier candidates."""
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
                 reveals: Optional[List[dict]]) -> str:
    """The note's markdown: frontmatter, an optional ``## Reveals`` section
    (the previous note's scored answers), a Conjectures section (Task 3, not
    yet wired here), then one block per budgeted question. Forecasts never
    appear as plaintext — only their seal."""
    parts: List[str] = [_frontmatter(note_date, run_id, segment, budget)]
    if reveals:
        parts.append(_render_reveals(reveals))
    for n, c in enumerate(_select_within_budget(candidates, budget), start=1):
        parts.append(_render_question_block(n, c))
    return "\n\n".join(parts) + "\n"


__all__ = ["QuestionCandidate", "seal", "candidates_from_run", "render_note"]
