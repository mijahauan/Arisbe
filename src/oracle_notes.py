"""Oracle notes — the V2a Obsidian-native surface (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2, ruled 2026-07-18). Arisbe writes
questions notes into exactly one vault folder (``Arisbe/``); the next poll reads
answers back through the same membrane.

**Stage split:** Task 1 built candidates, the seal, and the note renderer, all
offline and deterministic given the caller's inputs (``note_date`` is
caller-supplied; every random draw — the P2^13 shuffle and random arm, the
per-question seal nonces, the note-facing qid aliases — enters only through
the injected ``rng``/``nonce_factory``, so tests seed them and only the live
driver draws fresh).
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

**Docket item 10 (P2^13 made falsifiable, this task):** the charge as
registered had no base rate, no rating instrument, and no comparator — a
docket that reads the author's own journal would pass vacuously. The
operational form built here: when a ``docket`` (an ``AttentionEconomy``-
ranked want pool, wrapped to the shape ``attention_economy.wants_from_docket``
reads) is supplied, ``candidates_from_run`` switches to the P2^13 instrument
mode — exactly ``N`` docket-selected (``arm="docket"``) and ``N`` template-
random (``arm="random"``) questions, rendered through the SAME identical
question template (:func:`_p213_question` — no per-arm wording of any kind),
in a seeded random order — instead of the V2a.1 provenance/journal/horizon
sources (``docket=None``, the default, is fully backward-compatible with
those). The ``arm`` never reaches the rendered note (only
``forecasts.jsonl``, via ``OracleLedger.record_asked``'s ``arm``/``segment``
fields); each question block also gains a ``**R:**`` prompt the author marks
``trivial``/``non-trivial``, recovered by ``parse_note`` and persisted via
``OracleLedger.record_rating`` to ``ratings.jsonl``. ``p2_13_report`` reads
both ledgers back into the pass/fail/ceiling verdict
(``runs/RUN_13_LOG.md``'s P2^13 amendment has the exact rule). Blinding is
now a template-level guarantee: strip the concrete backtick-quoted subject
from any P2^13 question and the two arms' remaining text is byte-identical
(``tests/test_oracle_notes.py``'s blinding test checks exactly this) — an
earlier version put a per-arm reason into the text and was a real,
reviewer-caught leak, fixed here by dropping the reason from the rendered
text entirely (see the P2^13 instrument section below).

**Seal-then-reveal:** ``seal(forecast, nonce)`` is the SALTED SHA-256 hex
commitment (docket item 8): the forecast vocabulary is closed and small, so an
unsalted hash is a precomputable dictionary — a per-question nonce from the
caller's injected ``nonce_factory`` is what makes the seal binding. The
question block prints only the hash, never the plaintext. The plaintext (and
its nonce) lives in the caller's gitignored side-store
(``oracle/forecasts.jsonl``) and reaches the note again only through a later
``## Reveals`` section, once the answer is in hand — ``build_reveals``
recomputing the salted hash first (``seal-broken`` on mismatch).

**Qid recovery (Task 2):** each rendered question block carries an invisible
``<!-- qid: ... -->`` HTML comment right under its header — Obsidian's preview
renderer hides HTML comments, so the author never sees it, but ``parse_note``
uses it to recover which question an ``**A:**`` line belongs to without relying
on question text (which the author might reasonably edit or quote back). For a
P2^13 question the comment carries an OPAQUE alias (:func:`opaque_note_qid` —
whole-branch review, 2026-07-19: the real qids are structurally
distinguishable by arm, and the author answers in source mode where comments
are visible); the ledger keeps the real qid and joins the alias back through
``forecasts.jsonl``'s ``note_qid`` field (:func:`resolve_note_qids`).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


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
    arm: Optional[str] = None
    """``"docket"`` / ``"random"`` for a P2^13 instrument candidate (docket
    item 10), ``None`` for every other source. Carried on the object only —
    ``render_note`` never prints it; it reaches persistence solely through
    ``OracleLedger.record_asked``'s ``arm`` argument."""


def seal(forecast: str, nonce: str = "") -> str:
    """The forecast's commitment: ``sha256(nonce + forecast)`` hex digest.
    Checkable later (recompute the same nonce+forecast and compare against
    the stored hash — see ``OracleLedger.build_reveals``). The forecast
    vocabulary is closed and small (``"collected"``, ``"fragment"``,
    ``"unknown"``, ``"reconstructed"``, …), so an UNSALTED hash is a
    precomputable four-entry dictionary — it hides nothing. A caller-supplied
    per-question ``nonce`` is what actually makes the seal non-dictionary-
    attackable; the default empty nonce recovers the legacy (unsalted,
    dictionary-guessable) value so pre-existing ``forecasts.jsonl`` rows
    written before this nonce was introduced still verify."""
    return hashlib.sha256((nonce + forecast).encode("utf-8")).hexdigest()


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


def _two_options(first: str, second: str, rng) -> Tuple[str, str]:
    """Docket item 11, charge 3 (the question-neutrality rider): a two-option
    template used to embed the forecast as the FIRST-listed option — a
    constant positional tell. With an injected ``rng`` the order is
    seed-alternated (one ``rng.random()`` draw per question); ``rng=None``
    keeps the historical canonical order, so direct library callers are
    byte-identical."""
    if rng is not None and rng.random() < 0.5:
        return second, first
    return first, second


def _provenance_candidates(world, decode: Dict[str, str],
                            rng=None) -> List[QuestionCandidate]:
    """Up to 3 notes bucketed ``collected_prior`` (top dir == ``Clippings``):
    is this the author's own writing, or something collected from elsewhere?
    Option order seed-alternated via ``rng`` (:func:`_two_options`); the
    forecast stays ``"collected"`` regardless of which option is listed
    first."""
    out: List[QuestionCandidate] = []
    clippings = [n for n in world.notes() if world._top_dir(n) == "Clippings"][:3]
    for relpath in clippings:
        nid = world.note_id(relpath)
        path = _decode(decode, nid, relpath)
        opt_a, opt_b = _two_options(
            "collected from elsewhere", "your own writing", rng)
        out.append(QuestionCandidate(
            qid=f"prov:{nid}", tier="quick",
            text=f"Is `{path}` {opt_a}, or {opt_b}?",
            why="its folder reads as a collected-prior bucket (Clippings), "
                "worth confirming rather than assuming",
            settles="whether this note counts as the author's own authored "
                    "voice or an imported clipping",
            forecast="collected", severity=3.0,
        ))
    return out


def _multi_journal_candidates(world, decode: Dict[str, str],
                               rng=None) -> List[QuestionCandidate]:
    """When more than one journal-shaped file exists, one question per extra
    file (up to 2, beyond the first/main): genuine journal, or a fragment/copy?
    Option order seed-alternated via ``rng`` (:func:`_two_options`); the
    forecast stays ``"fragment"`` regardless of which option is listed
    first."""
    paths = world.journal_paths()
    if len(paths) <= 1:
        return []
    main = paths[0]
    main_decoded = _decode(decode, world.note_id(main), main)
    out: List[QuestionCandidate] = []
    for relpath in paths[1:3]:
        nid = world.note_id(relpath)
        path = _decode(decode, nid, relpath)
        opt_a, opt_b = _two_options(
            "a genuine journal", f"a fragment/copy of `{main_decoded}`", rng)
        out.append(QuestionCandidate(
            qid=f"journal:{nid}", tier="quick",
            text=f"Is `{path}` {opt_a}, or {opt_b}?",
            why="more than one journal-shaped file exists; only one should "
                "carry the standing event-time record",
            settles="whether this file's entries double-count against the "
                    "main journal",
            forecast="fragment", severity=3.0,
        ))
    return out


def _consent_blocked(ref: str) -> bool:
    """The consent boundary's one predicate (docket item 9), shared by EVERY
    question source — the horizon questions and BOTH P2^13 arms (whole-branch
    review, 2026-07-19: the instrument arms used to bypass it, which made the
    filter dead on the default ``--p213`` path). True when ``ref``'s first
    path component is a metadata-only folder (``People/``, ``Kith_Kin/``,
    ``Household/``) — including the bare folder itself, since a
    ``("scan", "People")`` want's ref IS ``"People"``. A root-level file ref
    has no folder component in the set and passes through untouched."""
    from vault_world import METADATA_ONLY_DIRS
    parts = Path(ref).parts
    return bool(parts) and parts[0] in METADATA_ONLY_DIRS


def _consent_filtered(items):
    """The consent boundary (docket item 9) binds the question generator
    exactly as `vault_world`'s docstring binds the reader: an item whose ref
    sits under `People/`, `Kith_Kin/`, or `Household/` never becomes question
    text — it is still ON the horizon (registered, still counted in
    `horizon.snapshot()`); only its promotion here is suppressed."""
    return [item for item in items if not _consent_blocked(item.ref)]


def _horizon_candidates(horizon, decode: Dict[str, str]) -> List[QuestionCandidate]:
    """Up to 2 largest open horizon items (biggest first, ref as the
    deterministic tie-break) that also clear the consent boundary
    (`_consent_filtered` — People/Kith_Kin/Household never asked about):
    what is this not-yet-legible thing?"""
    if horizon is None:
        return []
    eligible = _consent_filtered(horizon.open_items())
    items = sorted(eligible, key=lambda i: (-i.size, i.ref))[:2]
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


# -- the P2^13 instrument (docket item 10) --------------------------------------
#
# Two arms, ONE question template (identical text, not just "similarly
# shaped") so the only thing that differs between them is WHICH note gets
# asked about — never how the question reads. Review finding (2026-07-19):
# an earlier version put a per-arm parenthetical reason into the question
# text ("flagged for a closer read" vs "sampled for this round's check"),
# which is a fixed tell — an author reading even one note could partition
# all four questions by phrasing alone, confounding the ratings. Fixed by
# dropping the reason from the rendered text entirely; the arm lives
# out-of-band, in ``forecasts.jsonl``, never in the note. The ``docket``
# argument is deliberately generic: anything exposing ``.open_entries``
# (each entry carrying ``.key``/``.age``/``.attempts``, the shape
# ``attention_economy.wants_from_docket`` reads, plus a ``.payload`` that is
# itself a ``(ref, reason)`` pair — ``reason`` kept in the payload for a
# future audit trail even though it no longer reaches the question text)
# qualifies — a real ``QueryDocket``, or (the vault loop's actual case,
# since Q1 entity-reach is a Wikidata-shaped vocabulary that doesn't fit a
# vault's note/journal/scan wants) the driver's ``EconomyDocket`` adapter
# wrapping an ``AttentionEconomy``'s own ranked want pool. This module never
# re-implements docket ranking — it calls the real ``wants_from_docket`` and
# takes the top ``n`` in whatever order the docket already offers them.

_P213_WHY = "this round's attention pass flagged it for a closer look"
_P213_SETTLES = "what this item actually is, in the author's own words"


def _p213_question(qid: str, ref: str, arm: str) -> QuestionCandidate:
    """The ONE template both arms render through — identical text shape for
    every P2^13 candidate regardless of arm; only ``ref`` (the concrete
    subject) and the out-of-band ``arm`` differ."""
    return QuestionCandidate(
        qid=qid, tier="quick",
        text=f"What is `{ref}`? One line is plenty.",
        why=_P213_WHY, settles=_P213_SETTLES,
        forecast="unknown", severity=2.5, arm=arm,
    )


def _docket_candidates(
        docket, n: int = 2, world=None) -> List[Tuple[QuestionCandidate, str]]:
    """The docket arm: the top ``n`` entries the docket offers, each turned
    into one concrete "what is this?" question via the shared
    :func:`_p213_question` template. Docket item 10's falsifiability
    requirement (d) — a docket want's key must be traceable from the
    candidate it produced — is met by folding ``entry.key`` into the qid, so
    a real ``AttentionEconomy`` want (or a test double) that reached the
    docket is verifiably the thing this candidate asked about. Returns
    ``(candidate, ref)`` pairs — ``ref`` (the human-legible subject, e.g. a
    note relpath) is what the random arm needs to exclude so the two arms
    never both ask about the same thing; it isn't otherwise recoverable from
    the candidate (the qid carries the want's *key*, not its ref, so
    provenance and the excludable subject are kept genuinely distinct).

    Both arms filter IDENTICALLY (whole-branch review, 2026-07-19): the
    consent boundary (docket item 9, :func:`_consent_blocked`) and the
    ``authored_by: arisbe`` exclusion each bind here exactly as in
    :func:`_random_candidates` — an asymmetric filter would make the two
    arms different samples of the vault and bias the docket-vs-random
    margin the instrument exists to measure. A blocked want stays on the
    docket (nothing is deleted); only its promotion to question text is
    suppressed, so the next-ranked eligible want takes the slot."""
    from attention_economy import wants_from_docket
    is_arisbe = getattr(world, "is_arisbe_note", None)
    # is_arisbe_note reads a note's frontmatter, so only ask it about refs
    # the world actually lists as notes (a scan want's ref is a folder; a
    # journal want's ref carries a "(batch N)" suffix — neither is a note).
    known_notes = (set(world.notes())
                   if world is not None and callable(getattr(world, "notes", None))
                   else set())
    out: List[Tuple[QuestionCandidate, str]] = []
    for dw in wants_from_docket(docket, round_idx=0):
        if len(out) >= n:
            break
        entry = dw.payload
        ref, _reason = entry.payload   # reason kept for provenance, not shown
        if _consent_blocked(ref):
            continue
        if is_arisbe and ref in known_notes and is_arisbe(ref):
            continue
        key_str = ":".join(str(part) for part in entry.key)
        cand = _p213_question(qid=f"p213:{key_str}", ref=ref, arm="docket")
        out.append((cand, ref))
    return out


def _random_candidates(world, rng, exclude: Set[str],
                        n: int = 2) -> List[QuestionCandidate]:
    """The random arm: ``n`` notes drawn uniformly (via the injected ``rng``,
    never the docket's ranking) from the notes the docket arm did NOT already
    pick (``exclude`` — keeps the comparator honest: a note that happened to
    be both docket-ranked and randomly drawn would double-count, and the two
    arms would no longer be disjoint samples), and never from a note
    ``authored_by: arisbe`` (a self-authored note — e.g. a prior
    ``Questions-*.md``) — reviewer's Minor 1: such a note reads as trivial
    almost by construction, which would inflate the docket-vs-random margin
    in the PASS direction, the wrong bias for a falsifiability instrument.
    Uses ``world.is_arisbe_note`` when the world exposes it (the real
    ``VaultWorld`` does); a world that doesn't (a test double) simply skips
    that filter rather than raising. Same template as the docket arm, and
    the SAME two filters as the docket arm (consent boundary + arisbe
    exclusion — see :func:`_docket_candidates` on why the arms must filter
    identically)."""
    is_arisbe = getattr(world, "is_arisbe_note", None)
    pool = [n_ for n_ in world.notes()
            if n_ not in exclude
            and not _consent_blocked(n_)
            and not (is_arisbe and is_arisbe(n_))]
    if not pool:
        return []
    chosen = rng.sample(pool, k=min(n, len(pool)))
    return [_p213_question(qid=f"p213:{relpath}", ref=relpath, arm="random")
            for relpath in chosen]


def _p213_candidates(world, docket, rng, n: int = 2) -> List[QuestionCandidate]:
    """Both arms combined, then shuffled in place with the injected ``rng``
    — the "seeded random order" the operational form requires: with equal
    severity (2.5) and ``select_within_budget``'s stable sort, this shuffle
    IS the note's final question order, so a fixed seed reproduces a fixed
    order and a fresh seed varies it, but the arm is never recoverable from
    position alone.

    Uneven arms (reviewer's Minor 3): all ``2n`` candidates share severity
    2.5, so a caller-supplied ``budget.max`` below ``2n`` (e.g. 3, vs. the
    default 4 for both arms plus 1 reflective) can select an uneven split
    between arms (2 docket + 1 random, or vice versa — whichever the shuffle
    happened to order first) rather than refusing outright; ``p2_13_report``
    already reads rates (non-trivial ÷ rated total per arm), which tolerate
    unequal ``n`` between arms and even between segments."""
    docket_pairs = _docket_candidates(docket, n=n, world=world)
    docket_cands = [c for c, _ref in docket_pairs]
    taken = {ref for _c, ref in docket_pairs}
    combined = docket_cands + _random_candidates(world, rng, taken, n=n)
    rng.shuffle(combined)
    return combined


def candidates_from_run(world, horizon, known_laws: List[str], labels: dict,
                         *, docket=None, rng=None) -> List[QuestionCandidate]:
    """The candidate list. With ``docket=None`` (the default), this is the
    V2a.1 list in the fixed source order above — fully backward-compatible.
    With a ``docket`` supplied, it switches to the P2^13 instrument mode
    (docket item 10): exactly the two-arm question set from
    ``_p213_candidates`` (default 2+2, matching the ruled 5-question budget
    with the standing reflective) REPLACES the provenance/journal/horizon
    sources for that cycle — the note becomes the falsifiability instrument,
    not a mixed bag competing for budget slots against it. The standing
    reflective question is offered either way. Tolerates ``horizon=None``
    (skip horizon questions entirely — no crash) in the non-docket path.
    ``rng`` is the injectable seeded ``random.Random`` (deterministic tests);
    ``None`` with a docket present falls back to a fresh, unseeded
    ``random.Random()`` — the real (non-test) default. In the non-docket
    (V2a.1) path, ``rng`` seed-alternates the two-option order of the
    provenance/journal templates (docket item 11, charge 3 — the forecast
    must not always sit first-listed); ``rng=None`` there keeps the
    historical canonical order, byte-identical for existing callers."""
    decode = _decode_map(world, labels)
    out: List[QuestionCandidate] = []
    if docket is not None:
        import random as _random_mod
        r = rng if rng is not None else _random_mod.Random()
        out.extend(_p213_candidates(world, docket, r))
    else:
        out.extend(_provenance_candidates(world, decode, rng=rng))
        out.extend(_multi_journal_candidates(world, decode, rng=rng))
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


def opaque_note_qid(qid: str, nonce: str) -> str:
    """The note-facing alias for a P2^13 qid (whole-branch review, 2026-07-19,
    IMPORTANT 3): the REAL qids are structurally distinguishable by arm
    (``p213:scan:...`` docket-want keys vs ``p213:<relpath>`` random draws),
    and the author answers in source mode where the ``<!-- qid: ... -->``
    comments are visible — a blinding leak. The alias keeps the namespace
    prefix (so ``_topic`` reads the same for both arms) and replaces the body
    with ``sha256(qid + nonce)[:12]`` — same shape for every P2^13 question
    regardless of arm. The LEDGER always keeps the real qid; the alias is
    stored beside it (``record_asked``'s ``note_qid``) and joined back at
    parse time via :func:`resolve_note_qids`."""
    digest = hashlib.sha256((qid + nonce).encode("utf-8")).hexdigest()[:12]
    return f"{_topic(qid)}:{digest}"


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
        # Prefer the note-facing alias: a Reveals line printing the REAL
        # P2^13 qid would leak the arm structure retroactively (the author
        # reads reveals while rating the next note's questions).
        shown = r.get("note_qid") or r["qid"]
        lines.append(
            f"- `{shown}`: forecast **{r['forecast_plain']}** "
            f"(`sha256:{r['forecast_hash']}`) — answer: \"{r['answer']}\" "
            f"→ **{r['verdict']}**"
        )
    return "\n".join(lines)


def _render_question_block(n: int, c: QuestionCandidate, nonce: str = "",
                            note_qid: Optional[str] = None) -> str:
    lines = [
        f"## Q{n} · {c.tier} — {_topic(c.qid)}",
        f"<!-- qid: {note_qid or c.qid} -->",
        "",
        c.text,
        "",
        f"*Why asked:* {c.why}",
        f"*Would settle:* {c.settles}",
        f"*Forecast (sealed):* `sha256:{seal(c.forecast, nonce)}`",
        "**A:**",
        "**R:** (trivial | non-trivial)",
    ]
    return "\n".join(lines)


def render_note(candidates: List[QuestionCandidate], *, note_date: str,
                 run_id: str, segment: int, budget: dict,
                 reveals: Optional[List[dict]],
                 conjectures: Optional[str] = None,
                 nonces: Optional[Dict[str, str]] = None,
                 note_qids: Optional[Dict[str, str]] = None) -> str:
    """The note's markdown: frontmatter, an optional ``## Reveals`` section
    (the previous note's scored answers), an optional ``## Conjectures``
    section (Task 3 — the caller passes the already-rendered string from
    ``conjectures_section``, or ``None``/``""`` to omit it), then one block
    per budgeted question. Forecasts never appear as plaintext — only their
    seal. ``nonces`` maps qid -> the per-question nonce the caller generated
    at candidate-selection time (the SAME nonce must reach ``record_asked``,
    so the note's printed seal and the ledger's stored seal agree); a missing
    qid or an absent ``nonces`` falls back to the empty-nonce legacy seal.
    ``note_qids`` maps qid -> the note-facing alias the block's comment
    prints instead of the real qid (:func:`opaque_note_qid` — the P2^13
    blinding fix); an absent mapping or missing qid renders the real qid,
    byte-identical for every existing caller."""
    nonces = nonces or {}
    note_qids = note_qids or {}
    parts: List[str] = [_frontmatter(note_date, run_id, segment, budget)]
    if reveals:
        parts.append(_render_reveals(reveals))
    if conjectures:
        parts.append(conjectures)
    for n, c in enumerate(select_within_budget(candidates, budget), start=1):
        parts.append(_render_question_block(n, c, nonces.get(c.qid, ""),
                                             note_qids.get(c.qid)))
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
#  - immediately after the answer region, a block ALSO carries a ``**R:**``
#    line (docket item 10) the author marks ``trivial``/``non-trivial``; the
#    answer capture stops there too (before it would ever have reached the
#    blank-line/next-header boundary), so an edited answer and an edited
#    rating never bleed into each other. An unedited ``**R:**`` line (still
#    the rendered placeholder ``(trivial | non-trivial)``) reads as no rating
#    at all — silence is first-class here exactly as it is for ``**A:**``.


@dataclass
class ParsedNote:
    """What `parse_note` recovers from one note's raw markdown, after the
    author has (possibly) edited it in place."""
    budget: dict
    answers: Dict[str, str] = field(default_factory=dict)
    declined: Set[str] = field(default_factory=set)
    ignored: Set[str] = field(default_factory=set)
    ratings: Dict[str, str] = field(default_factory=dict)
    """qid -> ``"trivial"``/``"non-trivial"``, recovered from that block's
    ``**R:**`` line (docket item 10). A qid with no recognized rating
    (blank, still the placeholder, or anything else) is simply absent —
    unrated is first-class, not an error."""
    stray: str = ""
    budget_parsed: bool = True
    """False when the ``budget: {...}`` line was missing/malformed and
    ``budget`` fell back to ``DEFAULT_BUDGET`` (Task 4's driver-side guard:
    print a warning rather than silently adopting defaults)."""


DEFAULT_BUDGET = {"max": 5, "reflective": 1}
"""The V2a ruling: at most 5 questions per note, at most 1 reflective — the
one source of truth for the ruled budget. Both ``parse_note``'s fallback
(below, when the prior note's budget knob is missing/malformed) and the
driver's first-ever note (no prior note to read an edited knob from) use this
same constant, so the ruled number lives in exactly one place."""

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
    r"(?P<answer>.*?)"
    # The rating line is OPTIONAL (older-format notes, or a caller-built
    # ``ParsedNote``-adjacent fixture, may not carry one) — when present it
    # must immediately follow the answer region (a single ``\n``, no blank
    # line between), so the non-greedy answer capture stops there rather
    # than swallowing the rating line as more "answer".
    r"(?:\n\*\*R:\*\*(?P<rating>[^\n]*))?"
    # The final block in a note has nothing after it but render_note's own
    # single trailing "\n" (no blank line, no next header) — ``\n\Z`` covers
    # that case; without it the rating line (or, pre-Task-10, the trailing
    # newline alone) has no reachable stopping point and gets pulled into
    # the answer/rating capture instead.
    r"(?=\n\n|\n## |\n\Z|\Z)",
    re.DOTALL,
)
_RATING_VALUES = {"trivial", "non-trivial"}

_DECLINE_MARKERS = frozenset({
    "declined", "decline", "pass", "—", "-", "rather not",
    "prefer not to say",
})
"""Docket item 11, charge 2: the recognized decline synonyms. Matched after
strip / ``rstrip(".")`` / casefold, so ``"Declined."``, ``"Pass."``, ``"—"``
all read as a decline — a refusal's own wording must never be banked verbatim
as an answer (and hence never reprinted in a later note's Reveals). A genuine
answer that merely *contains* a marker word is untouched: the whole normalized
answer must BE a marker, not include one."""


def parse_note(text: str) -> ParsedNote:
    """Recover the author's edits from a rendered-then-edited note's raw
    markdown: the (possibly edited) budget knob, each question's answer text
    (non-empty), the set of declined qids (an ``**A:**`` line whose content,
    after strip / ``rstrip(".")`` / casefold, is one of the
    ``_DECLINE_MARKERS`` synonyms — never banked as answer text), the set of ignored
    qids (an ``**A:**`` line left empty), each qid's ``**R:**`` rating
    (docket item 10 — only ``trivial``/``non-trivial`` count; anything else,
    including the unedited placeholder, is unrated and simply absent from
    ``ratings``), and any stray text the author wrote outside every
    recognized block (frontmatter / Reveals / question blocks) — kept
    verbatim as evidence, not interpreted."""
    m = _BUDGET_RE.search(text)
    budget = ({"max": int(m.group(1)), "reflective": int(m.group(2))}
              if m else dict(DEFAULT_BUDGET))
    budget_parsed = m is not None

    answers: Dict[str, str] = {}
    declined: Set[str] = set()
    ignored: Set[str] = set()
    ratings: Dict[str, str] = {}
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
        elif answer.rstrip(".").casefold() in _DECLINE_MARKERS:
            declined.add(qid)
        else:
            answers[qid] = answer
        rating = (qm.group("rating") or "").strip().lower()
        # Real-vault edit pattern (RUN 13, 2026-07-27): the author appended
        # their rating AFTER the rendered placeholder rather than replacing
        # it — "**R:** (trivial | non-trivial) non-trivial". The template
        # invites exactly that edit, so strip the literal placeholder
        # wherever it sits and read what remains; an untouched placeholder
        # still normalizes to "" = unrated, exactly as before.
        rating = rating.replace("(trivial | non-trivial)", "").strip()
        if rating in _RATING_VALUES:
            ratings[qid] = rating

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
                       ignored=ignored, ratings=ratings, stray=stray,
                       budget_parsed=budget_parsed)


def resolve_note_qids(parsed: ParsedNote,
                       mapping: Dict[str, str]) -> ParsedNote:
    """Translate a parsed note's note-facing qid aliases back to the real
    qids the ledger keys everything by (``mapping`` = alias -> real, from
    ``OracleLedger.note_qid_map``). A qid with no alias entry (every
    non-P2^13 question, and every note written before the blinding fix)
    passes through unchanged — identity on legacy notes."""
    tr = lambda q: mapping.get(q, q)                      # noqa: E731
    return ParsedNote(
        budget=parsed.budget,
        answers={tr(q): a for q, a in parsed.answers.items()},
        declined={tr(q) for q in parsed.declined},
        ignored={tr(q) for q in parsed.ignored},
        ratings={tr(q): r for q, r in parsed.ratings.items()},
        stray=parsed.stray,
        budget_parsed=parsed.budget_parsed,
    )


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


def _keyed_rows(ledger: "OracleLedger", rows: List[dict], *keys: str) -> List[dict]:
    """Filter ``rows`` (already JSON-parsed ledger dicts) to those carrying
    EVERY key in ``keys``, incrementing ``ledger.skipped_rows`` once per row
    dropped. Whole-branch review, 2026-07-19 (NEW-1): a torn/corrupt line
    was already survivable via ``_read_all``'s per-line guard, but a
    perfectly valid JSON row simply missing a key a caller needed (e.g. one
    ``qid``-less row hand-edited or half-written into ``outcomes.jsonl``)
    still crashed every keyed read downstream (``r["qid"]`` etc.) with a
    bare ``KeyError`` that poisoned every future pass. This is the one
    place every keyed ledger read — inside ``OracleLedger``'s own methods
    and the module-level helpers that read a ledger's rows directly
    (``reask_candidate``, ``p2_13_report``) — funnels through, so the
    counted-never-dropped rule holds uniformly rather than being
    reinvented (or missed) at each call site."""
    out: List[dict] = []
    for r in rows:
        if all(k in r for k in keys):
            out.append(r)
        else:
            ledger.skipped_rows += 1
    return out


class OracleLedger:
    """Append-only JSONL persistence for the ask/answer loop, under
    ``dir_path`` (created if absent). Three files, one concern each:
    ``forecasts.jsonl`` (one record per asked question — this is where the
    forecast plaintext actually lives; the note itself only ever carries the
    seal — plus, since docket item 10, the ``arm``/``segment`` a P2^13
    instrument candidate was asked under), ``outcomes.jsonl`` (one record
    per parsed answer/decline/ignore), and ``ratings.jsonl`` (one record per
    parsed ``**R:**`` triviality rating — docket item 10's instrument
    output). Nothing is cached in memory — each read re-scans its file, so a
    ledger opened fresh in a later process (a later run) sees everything an
    earlier one wrote.

    ``skipped_rows`` (whole-branch review, 2026-07-19, NEW-1): a running,
    observable count of every row this ledger has ever dropped rather than
    raised on — an unparseable/non-dict JSONL line (``_read_all``) or a
    structurally valid row missing a key some read needed (``_keyed_rows``).
    Counted-never-dropped, the house rule throughout this codebase: a torn
    line or a hand-edited row must never poison every subsequent pass, but
    it must also never vanish silently. It is a SKIP-EVENT count, not a
    distinct-bad-row count: since nothing is cached, one still-present bad
    row is re-counted on every read that rescans its file, so this number
    can grow across calls on this instance far past the number of rows
    actually damaged (review finding NEW-4, 2026-07-20 — see
    ``run_vault_v0._run_oracle``'s ``ledger_skip_events`` digest key,
    which surfaces this count as-is under a name that says so)."""

    def __init__(self, dir_path):
        self.dir_path = Path(dir_path)
        self.dir_path.mkdir(parents=True, exist_ok=True)
        self._forecasts_path = self.dir_path / "forecasts.jsonl"
        self._outcomes_path = self.dir_path / "outcomes.jsonl"
        self._ratings_path = self.dir_path / "ratings.jsonl"
        self.skipped_rows = 0

    @staticmethod
    def _append(path: Path, record: dict) -> None:
        """Append the fully-formed line and flush. This is append-only
        JSONL, not a whole-file checkpoint — the write-temp-then-
        ``os.replace`` idiom ``live_runner``/``wikidata_source`` use for
        their state files doesn't fit an append (renaming a temp file
        would clobber every other line already on disk instead of adding
        to it). A kill mid-``write()`` can still tear the line (no
        ``os.fsync``, and the explicit ``flush()`` here only forces the
        same buffered data the context manager would flush at close
        anyway — it buys no atomicity). The real tolerance for a torn
        tail lives one level up, in ``_read_all``'s
        ``json.JSONDecodeError`` guard: a partially-written line is
        skipped and counted rather than poisoning every later read."""
        line = json.dumps(record) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()

    def _read_all(self, path: Path) -> List[dict]:
        """Every well-formed JSON-object line in ``path``, in file order.
        A line that fails to parse (``json.JSONDecodeError`` — a torn
        write, hand-editing damage) or that parses to something other
        than a JSON object (a bare string/number/list/null) is skipped and
        counted in ``self.skipped_rows`` rather than raised — NEW-1: an
        unguarded ``json.loads`` here used to poison every future read of
        this file the moment one bad line existed, identically to the
        keyed-access hazard ``_keyed_rows`` guards below."""
        if not path.exists():
            return []
        out: List[dict] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    self.skipped_rows += 1
                    continue
                if not isinstance(row, dict):
                    self.skipped_rows += 1
                    continue
                out.append(row)
        return out

    def record_asked(self, note_date: str, qid: str, tier: str,
                      forecast_plain: str, forecast_hash: str,
                      nonce: str = "", arm: Optional[str] = None,
                      segment: Optional[int] = None,
                      text: str = "", note_qid: str = "") -> None:
        """``arm``/``segment`` (docket item 10): the P2^13 instrument's arm
        (``"docket"``/``"random"``) and the segment the question was asked
        in — recorded ONLY here, never in the note itself. Both default
        ``None`` for every non-instrument candidate (existing call sites
        need change nothing). ``text`` (docket item 11): the question's
        rendered wording, stored so a later drift re-ask
        (:func:`reask_candidate`) can repeat it VERBATIM rather than
        regenerate it; the empty default keeps legacy rows readable (a row
        without text is simply never re-asked). ``note_qid`` (the blinding
        fix, 2026-07-19): the opaque alias the NOTE printed for this
        question (:func:`opaque_note_qid`) — the join key
        ``resolve_note_qids`` translates parsed answers back through; empty
        for every question rendered under its real qid."""
        self._append(self._forecasts_path, {
            "note_date": note_date, "qid": qid, "tier": tier,
            "forecast_plain": forecast_plain, "forecast_hash": forecast_hash,
            "nonce": nonce, "arm": arm, "segment": segment, "text": text,
            "note_qid": note_qid,
        })

    def record_outcome(self, qid: str, status: str, answer_text: str,
                        answered_note_date: str) -> None:
        self._append(self._outcomes_path, {
            "qid": qid, "status": status, "answer_text": answer_text,
            "answered_note_date": answered_note_date,
        })

    def record_outcome_once(self, qid: str, status: str, answer_text: str,
                             answered_note_date: str) -> bool:
        """Idempotent ``record_outcome``: a note that sits partially answered
        gets re-polled by the driver on every invocation, and the append-only
        JSONL log has no dedup of its own — without this, every re-poll
        re-appends the same answer/decline/ignore row and pollutes the
        eventual K1 ledger. Reads the qid's latest recorded outcome; if its
        ``(status, answer_text)`` already matches, skips the append and
        returns ``False`` (nothing new happened). Otherwise appends (a
        genuinely CHANGED answer for the same qid — the author edited their
        reply — still lands as a new row, so progress is kept) and returns
        ``True``. A row missing ``qid``/``status``/``answer_text`` (NEW-1)
        is counted and excluded from the ``existing`` scan rather than
        raising."""
        existing = [r for r in _keyed_rows(
                        self, self._read_all(self._outcomes_path),
                        "qid", "status", "answer_text")
                    if r["qid"] == qid]
        if existing:
            latest = existing[-1]
            if latest["status"] == status and latest["answer_text"] == answer_text:
                return False
        self.record_outcome(qid, status, answer_text, answered_note_date)
        return True

    def has_prior_answer(self, qid: str) -> bool:
        """True if this qid was EVER previously recorded with an
        ``"answered"`` status — used to tell a fresh answer from a drift (a
        changed answer to an already-answered qid). Centralizes what
        ``run_vault_v0._run_oracle`` used to do inline with raw
        ``o["qid"]``/``o["status"]`` indexing on ``ledger.outcomes()`` —
        exactly the access the whole-branch review (2026-07-19, NEW-1)
        reproduced crashing on one hand-injected qid-less row in
        ``outcomes.jsonl`` (``KeyError: 'qid'``, poisoning every future
        pass). Rows missing ``qid``/``status`` are counted and skipped,
        never raised on, via :func:`_keyed_rows`."""
        rows = _keyed_rows(self, self._read_all(self._outcomes_path),
                            "qid", "status")
        return any(r["qid"] == qid and r["status"] == "answered" for r in rows)

    def record_rating(self, qid: str, rating: str, note_date: str) -> None:
        """Docket item 10: append one ``**R:**`` triviality rating
        (``"trivial"``/``"non-trivial"`` — ``parse_note`` already refuses
        anything else) to ``ratings.jsonl``."""
        self._append(self._ratings_path, {
            "qid": qid, "rating": rating, "note_date": note_date,
        })

    def record_rating_once(self, qid: str, rating: str, note_date: str) -> bool:
        """Idempotent ``record_rating`` — the same re-poll-pollution guard
        ``record_outcome_once`` gives outcomes, needed for the same reason:
        a partially-answered note is re-parsed on every driver invocation.
        A row missing ``qid``/``rating`` (NEW-1) is counted and excluded
        rather than raising."""
        existing = [r for r in _keyed_rows(
                        self, self._read_all(self._ratings_path), "qid", "rating")
                    if r["qid"] == qid]
        if existing and existing[-1]["rating"] == rating:
            return False
        self.record_rating(qid, rating, note_date)
        return True

    def forecasts(self) -> List[dict]:
        return self._read_all(self._forecasts_path)

    def note_qid_map(self) -> Dict[str, str]:
        """Note-facing alias -> real qid, from every forecasts row that
        stored one (the blinding fix, 2026-07-19). Aliases are
        nonce-derived and unique per asking, so later rows only add keys —
        no collision to resolve. A row missing ``qid`` (NEW-1) is counted
        and excluded rather than raising."""
        out: Dict[str, str] = {}
        for r in _keyed_rows(self, self._read_all(self._forecasts_path), "qid"):
            nq = r.get("note_qid")
            if nq and nq != r["qid"]:
                out[nq] = r["qid"]
        return out

    def ratings(self) -> List[dict]:
        return self._read_all(self._ratings_path)

    def asked_ever(self, qid: str,
                    within_last_n_notes: Optional[int] = None) -> bool:
        """The standing-question suppressor: has this qid been asked? With
        ``within_last_n_notes=None`` (the default) the answer is the
        historical forever-suppression — asked in any note, any run.

        Docket item 11, charge 1: forever-suppression contradicted spec
        thesis 3 ("wants age but persist; silence lowers priority, never
        deletes") and made drift unmeasurable by design. An int ``N`` means
        "asked within the last ``N`` **distinct note dates** recorded in
        ``forecasts.jsonl``" — a qid whose LATEST asking sits in an older
        note date reads ``False`` and becomes re-eligible. A qid never asked
        at all is ``False`` either way. A row missing ``qid``/``note_date``
        (NEW-1) is counted and excluded rather than raising."""
        all_rows = _keyed_rows(self, self._read_all(self._forecasts_path),
                                "qid", "note_date")
        rows = [r for r in all_rows if r["qid"] == qid]
        if not rows:
            return False
        if within_last_n_notes is None:
            return True
        all_dates = sorted({r["note_date"] for r in all_rows})
        window = set(all_dates[-within_last_n_notes:])
        latest_asked = max(r["note_date"] for r in rows)
        return latest_asked in window

    def outcomes(self) -> List[dict]:
        return self._read_all(self._outcomes_path)

    def _latest_forecast(self, qid: str) -> Optional[dict]:
        """A row missing ``qid`` (NEW-1) is counted and excluded rather
        than raising."""
        matches = [r for r in _keyed_rows(
                       self, self._read_all(self._forecasts_path), "qid")
                   if r["qid"] == qid]
        return matches[-1] if matches else None

    def build_reveals(self, parsed: ParsedNote) -> List[dict]:
        """Join this note's genuine answers (``parsed.answers`` — declines
        and silences carry no forecast to score) to the forecast this ledger
        recorded when the question was asked, producing the reveal dicts
        Task 1's renderer already knows how to print (``qid``,
        ``forecast_plain``, ``forecast_hash``, ``answer``, ``verdict``). A
        qid with no recorded forecast (asked outside this ledger, or never
        asked) is silently skipped — nothing to reveal against.

        Docket item 8: the stored hash is RECOMPUTED from the stored
        plaintext + nonce (``forecast.get("nonce", "")`` — an empty string
        for a legacy pre-nonce row) and compared to ``forecast_hash`` before
        scoring. A row doctored after the fact (plaintext swapped without
        updating the hash) fails that comparison and reveals as
        ``"seal-broken"`` instead of a silently-trusted score.

        NEW-1 (2026-07-19): a forecasts row missing ``forecast_plain``/
        ``forecast_hash`` (hand-edited or torn) is counted
        (``self.skipped_rows``) and skipped like any other malformed row,
        rather than raising on the bracket access below."""
        reveals: List[dict] = []
        for qid in sorted(parsed.answers):
            forecast = self._latest_forecast(qid)
            if forecast is None:
                continue
            forecast_plain = forecast.get("forecast_plain")
            forecast_hash = forecast.get("forecast_hash")
            if forecast_plain is None or forecast_hash is None:
                self.skipped_rows += 1
                continue
            answer = parsed.answers[qid]
            expected = seal(forecast_plain, forecast.get("nonce", ""))
            verdict = ("seal-broken" if expected != forecast_hash
                       else score(forecast_plain, answer))
            reveals.append({
                "qid": qid,
                # the note-facing alias (blinding fix): _render_reveals
                # prints this, so a real P2^13 qid never reaches a later
                # note's Reveals section either.
                "note_qid": forecast.get("note_qid") or qid,
                "forecast_plain": forecast_plain,
                "forecast_hash": forecast_hash,
                "answer": answer,
                "verdict": verdict,
            })
        return reveals


# -- the drift re-ask (docket item 11, charge 1) ----------------------------------


def reask_candidate(ledger: "OracleLedger") -> Optional[QuestionCandidate]:
    """Docket item 11's drift instrument: at most ONE early question re-asked
    VERBATIM (the ``text`` stored in ``forecasts.jsonl`` when it was asked —
    never regenerated from the world), so a changed answer becomes a measurable
    drift datum (``record_outcome_once`` appends the changed answer as a new
    outcome row; the first row stays intact).

    Eligibility — all three must hold, or the qid is skipped:

    * **aged**: at least 2 distinct note dates in ``forecasts.jsonl`` are
      LATER than the qid's latest asking (so a re-ask resets its own clock —
      the fresh forecasts row it produces makes the qid ineligible until two
      more notes pass; the 1-per-note cap is this function returning at most
      one candidate);
    * **answered**: the qid has an ``"answered"`` outcome row (drift is a
      *changed answer*; silence and declines have nothing to drift from);
    * **verbatim-able**: the latest forecasts row stored a non-empty
      ``text`` (a legacy pre-item-11 row did not — it is honestly skipped,
      never reconstructed).

    Among the eligible, the one whose latest asking is EARLIEST is chosen
    ("one early question"), deterministic tie-break by qid. Returns ``None``
    when nothing qualifies. NEW-1 (2026-07-19): every keyed read below goes
    through :func:`_keyed_rows` — a forecasts/outcomes row missing the key
    this function needs is counted (``ledger.skipped_rows``) and excluded,
    never raised on; a row that clears that gate but still lacks
    ``forecast_plain`` is likewise counted and the re-ask skipped rather
    than fabricated."""
    forecasts = _keyed_rows(ledger, ledger.forecasts(), "qid", "note_date")
    if not forecasts:
        return None
    all_dates = sorted({r["note_date"] for r in forecasts})
    answered = {r["qid"] for r in _keyed_rows(
                    ledger, ledger.outcomes(), "qid", "status")
                if r["status"] == "answered"}
    latest_row: Dict[str, dict] = {}
    for r in forecasts:                      # file order; last write wins below
        prev = latest_row.get(r["qid"])
        if prev is None or r["note_date"] >= prev["note_date"]:
            latest_row[r["qid"]] = r
    eligible = [
        r for r in latest_row.values()
        if r["qid"] in answered
        and r.get("text")
        and len([d for d in all_dates if d > r["note_date"]]) >= 2
    ]
    if not eligible:
        return None
    row = min(eligible, key=lambda r: (r["note_date"], r["qid"]))
    forecast_plain = row.get("forecast_plain")
    if forecast_plain is None:
        ledger.skipped_rows += 1
        return None
    return QuestionCandidate(
        qid=row["qid"], tier=row.get("tier", "quick"), text=row["text"],
        why="asked before; re-asked verbatim to detect a changed answer "
            "(drift)",
        settles="whether the earlier answer still stands",
        forecast=forecast_plain, severity=3.5,
    )


# -- the P2^13 verdict (docket item 10) -------------------------------------------


def p2_13_report(ledger: OracleLedger) -> dict:
    """The P2^13 falsifiability instrument's verdict, read entirely off the
    ledger — ``forecasts.jsonl`` (which segment/arm each qid was asked
    under) joined to ``ratings.jsonl`` (the author's ``**R:**`` marks) by
    qid. A qid rated more than once keeps its LATEST rating (a correction
    supersedes, exactly like ``build_reveals``' latest-forecast join). The
    forecasts join reads each qid's EARLIEST ARMED row (whole-branch
    review, 2026-07-19: last-write-wins let a drift re-ask row —
    ``arm=None`` — erase a qid's arm while its rating still inflated the
    ceiling; the earliest-armed join is read-side only, self-healing for
    ledgers already written, and pins a rating to the segment/arm the
    question was originally asked under). A qid that never carried an arm
    (the standing reflective, a pure re-ask, a legacy row) sits outside the
    instrument entirely: it reaches neither an arm's rate nor the ceiling
    canary's denominator.

    Per segment: the docket-arm and random-arm non-trivial RATE (rated
    non-trivial ÷ rated total for that arm in that segment). An arm with
    zero ratings that segment reads ``None`` — an honest "no data", never a
    fabricated 0.0. **Ceiling canary:** a segment where >=90% of its rated
    ARMED questions (either arm — the instrument's own discriminating power
    is what's in question, not one arm alone) are marked non-trivial is
    flagged ``"uninformative"`` and excluded from the pass/fail tally
    entirely — it can't speak for or against P2^13 either way, because the
    rating channel itself isn't discriminating that segment.

    Verdict: ``"pass"`` iff the docket rate exceeds the random rate by
    ``>= 0.25`` (25 points) in ``>= 2`` non-ceiling segments that have BOTH
    arms rated; ``"insufficient_data"`` when no segment qualifies to be
    compared at all; ``"fail"`` otherwise — this is the reading
    ``runs/RUN_13_LOG.md``'s P2^13 amendment names as the pre-registered
    rule. NEW-1 (2026-07-19): a forecasts/ratings row missing ``qid`` (or,
    for ratings, ``rating``) is counted (``ledger.skipped_rows``) and
    excluded via :func:`_keyed_rows` rather than raised on."""
    armed: Dict[str, dict] = {}
    for f in _keyed_rows(ledger, ledger.forecasts(), "qid"):
        if f.get("arm") in ("docket", "random") and f["qid"] not in armed:
            armed[f["qid"]] = f
    latest_rating: Dict[str, str] = {}
    for r in _keyed_rows(ledger, ledger.ratings(), "qid", "rating"):
        latest_rating[r["qid"]] = r["rating"]

    buckets: Dict[Optional[int], dict] = {}
    for qid, rating in latest_rating.items():
        fc = armed.get(qid)
        if fc is None:
            continue    # never armed: outside the instrument — no bucket at all
        seg = fc.get("segment")
        arm = fc["arm"]
        b = buckets.setdefault(seg, {
            "all_total": 0, "all_non_trivial": 0,
            "docket_total": 0, "docket_non_trivial": 0,
            "random_total": 0, "random_non_trivial": 0,
        })
        is_nt = rating == "non-trivial"
        b["all_total"] += 1
        b["all_non_trivial"] += int(is_nt)
        b[f"{arm}_total"] += 1
        b[f"{arm}_non_trivial"] += int(is_nt)

    segments: Dict[Optional[int], dict] = {}
    informative_segments = 0
    hits = 0
    for seg, b in sorted(buckets.items(), key=lambda kv: (kv[0] is None, kv[0])):
        uninformative = (b["all_total"] > 0
                          and b["all_non_trivial"] / b["all_total"] >= 0.9)
        docket_rate = (b["docket_non_trivial"] / b["docket_total"]
                       if b["docket_total"] else None)
        random_rate = (b["random_non_trivial"] / b["random_total"]
                       if b["random_total"] else None)
        segments[seg] = {
            "docket_rate": docket_rate, "docket_n": b["docket_total"],
            "random_rate": random_rate, "random_n": b["random_total"],
            "uninformative": uninformative,
        }
        if (not uninformative and docket_rate is not None
                and random_rate is not None):
            informative_segments += 1
            if docket_rate - random_rate >= 0.25:
                hits += 1

    if informative_segments == 0:
        verdict = "insufficient_data"
    elif hits >= 2:
        verdict = "pass"
    else:
        verdict = "fail"

    return {"segments": segments, "verdict": verdict,
            "informative_segments": informative_segments, "hits": hits}


# --------------------------------------------------------------------------- #
# V2a.2 item (2): quotation-cell banking (docs/superpowers/specs/              #
# 2026-07-17-vault-cycle-design.md, "V2a.2 — AUTHORIZED", item 2).            #
# An answer enters M as ``(asserted "author" <q>)`` with <q> a proposition-    #
# sorted name whose quotation oval holds the prose as one                     #
# ``(utterance "<label>")`` atom — banked unparsed, mention not use. The      #
# only asserted ink is the attribution: truth about the act of answering,     #
# never about its content (spec §"person-model", Examination IV Suspect 4).   #
#                                                                              #
# The label bound (the author's ruling, docket item on long answers): a       #
# vertex/constant label's drawn box width is                                  #
# ``len(label) * font_size * _VERTEX_CHAR_W_RATIO``                           #
# (``presentation_ops._vertex_label_dims``), so a raw-prose label wider than  #
# its residence cell fails §3.3 occlusion at save time — measured precisely   #
# (scratch-script binary search): 52 chars passes, 53 fails, independent of   #
# the surrounding M's size. Mirrors the ``vault_world._bounded``/            #
# ``_digest_id``/``long_labels`` precedent for the same shape of problem      #
# (an over-long vault constant): prose at or under the bound banks verbatim;  #
# longer prose banks a short, content-derived id instead, with the original  #
# recorded in a sidecar the caller persists (never in M, never on stdout).    #
# --------------------------------------------------------------------------- #

ATTRIBUTION_EGIF = '(asserted "author" *q)'

_MAX_ANSWER_LABEL = 40
"""Cap on verbatim prose length in a banked quotation vertex's label — matches
``vault_world._MAX_CONST``. The measured occlusion wall sits at 52/53 chars;
40 leaves deliberate margin below that wall (font-size/ratio tuning, or a
different renderer, could move the wall without warning — the cap should not
be sitting right at its edge)."""


def _answer_digest_id(answer_text: str) -> str:
    """A short, deterministic, content-derived id for prose too long to bank
    verbatim — the ``vault_world._digest_id`` idiom (truncated hash, not a
    counter/nonce/uuid): the standing polarity gate REPLAYS ``bank_answer``
    from recorded chain params (``tests/test_corpus_polarity_discipline.py``'s
    ``_replay_act``), so the same ``answer_text`` must always yield the same
    id, in any process, at any time."""
    return "ans_" + hashlib.sha256(answer_text.encode("utf-8")).hexdigest()[:10]


def answer_label(answer_text: str) -> Tuple[str, Dict[str, str]]:
    """The label a banked answer's quotation vertex should carry, plus the
    sidecar dict ``{id: original}`` the caller should fold into the
    gitignored custody sidecar (the ``vault_world.long_labels`` precedent —
    ``tools/run_vault_v0.py`` merges both into the same ``labels.json``).

    At or under ``_MAX_ANSWER_LABEL`` chars, ``answer_text`` banks verbatim
    (today's behavior, unchanged) and the sidecar is empty. Longer prose
    gets :func:`_answer_digest_id` in its place — pure function of
    ``answer_text`` alone, so two calls with the same prose always agree —
    and the sidecar carries the one entry mapping that id back to the
    original. The prose itself is never lost: it already lives in the
    ledger (``forecasts.jsonl``/``outcomes.jsonl``), verbatim, regardless of
    what the drawn label carries."""
    if len(answer_text) <= _MAX_ANSWER_LABEL:
        return answer_text, {}
    label = _answer_digest_id(answer_text)
    return label, {label: answer_text}


def _utterance_graph(label: str):
    """The quoted ink: one constant vertex carrying ``label`` verbatim, named
    by one ``utterance`` atom. Built structurally — ``label`` never meets a
    linear parser/generator, so newlines/quotes/brackets survive untouched.
    ``label`` is whatever :func:`answer_label` decided to draw (the verbatim
    answer, or its digest id) — this function has no opinion on the bound."""
    from uuid import uuid4
    from egi_core_dau import create_empty_graph, Vertex, Edge
    g = create_empty_graph()
    vid, eid = f"v_bank_{uuid4().hex[:8]}", f"e_bank_{uuid4().hex[:8]}"
    g = g.with_vertex_in_context(
        Vertex(id=vid, label=label, is_generic=False), g.sheet)
    g = g.with_edge(Edge(id=eid), (vid,), "utterance", g.sheet)
    return g


BANK_TO_M = "BANK_TO_M"


def bankable_outcomes(ledger: "OracleLedger") -> Tuple[List[dict], int]:
    """The rows the author-model checkpoint banks, plus a count of rows
    dropped for lacking ``qid``. Returns ``(rows, dropped)``.

    ``rows``: the LATEST ``answered`` outcome row per qid (a drift row —
    the author revising a previous answer — supersedes; the earlier row
    remains ledger history, untouched). Declines and ignores are never
    banked (spec ruling 4: a refusal is never banked back as answer-data —
    only a genuine answer is attributed content). Each row carries
    ``qid``/``status``/``answer_text``/``answered_note_date``
    (``OracleLedger.record_outcome``'s own keys).

    ``dropped``: a row with no ``qid`` (a hand-edited or legacy ledger
    line) can't be keyed at all, so it never reaches ``rows`` — but
    whole-branch review, 2026-07-19 (NEW-2): the previous cut here dropped
    such a row with NO count at all, which made the caller
    (``run_vault_v0._bank_author_model``)'s own ``if qid is None`` guard
    unreachable dead code (this function had already removed every
    qid-less row before the caller ever saw one) while the caller's
    docstring and the spec doc both still claimed the drop was "counted
    (``bank_malformed``)" — false. Returning the count here lets the
    caller fold it straight into ``bank_malformed`` instead of
    re-deriving a case that can no longer occur on its own side; a row
    missing ``answer_text`` (which CAN still occur — this function never
    filters on it) remains the caller's own check to make and count."""
    latest: Dict[str, dict] = {}
    dropped = 0
    for row in ledger.outcomes():
        if row.get("status") != "answered":
            continue
        qid = row.get("qid")
        if qid is None:
            dropped += 1
            continue
        latest[qid] = row       # file order — later rows win
    return list(latest.values()), dropped


def bank_answer_step(pc, answer_text: str, *, qid: str, note_date: str,
                     note: str = None):
    """Record banking as ONE composite chain step (the ``challenge_step``
    precedent: one act, the executed derivation list). Act ``"quotation"`` —
    the polarity gate's ``M_ACTS`` names it and its replayer re-executes
    ``bank_answer`` from these params (docket ⑤: the record is earned,
    permanently); gate acknowledgement additionally requires the
    ``provenance`` key to read ``"oracle-answer"``, not the act name alone."""
    params = {
        "act": "quotation",
        "earned": True,
        "derivation": ["INS", "with_quotation_binding"],
        "provenance": "oracle-answer",
        "attributed_to": "author",
        "fact_egif": ATTRIBUTION_EGIF,
        "answer_text": answer_text,
        "qid": qid,
        "note_date": note_date,
    }
    return pc.apply_derived(
        BANK_TO_M,
        lambda g: bank_answer(g, answer_text, qid=qid, note_date=note_date)[0],
        note=note or f"bank oracle answer {qid} ({note_date})",
        params=params)


def bank_answer(m, answer_text: str, *, qid: str, note_date: str):
    """Bank one answered oracle question into the resident M: one licensed
    INS-of-cell of ``ATTRIBUTION_EGIF`` (``enlarge_m``), then the fresh
    generic name gains its quotation oval holding the prose — verbatim at or
    under ``_MAX_ANSWER_LABEL`` chars, else a deterministic content-derived
    id (:func:`answer_label`; the author's ruling on the §3.3 occlusion wall
    measured in this module's docstring above) — as one ``utterance`` atom
    (``quote_existing_name`` — same-area attachment, inside the new cell).
    Returns ``(new_graph, quotation_cut_id)``. Raises ``ValueError`` when
    ``m`` carries no world-scroll (``enlarge_m``'s own refusal). ``qid`` and
    ``note_date`` are accepted here for signature stability with the step
    recorder and the gate's replayer, which re-executes from these params.
    A pure function of ``answer_text`` alone (plus ``m``): no counter,
    clock, or randomness enters the label choice, so a replay from recorded
    chain params reproduces the identical graph. The sidecar entry (when
    ``answer_text`` was long enough to need one) is NOT returned here — call
    :func:`answer_label` directly for that; keeping this function's return
    shape a stable 2-tuple is what the gate's replayer already depends on."""
    from world_scroll import enlarge_m, find_world_scroll
    from quotation_overlay import quote_existing_name
    scroll = find_world_scroll(m)
    before_cells = set(scroll.cell_ids) if scroll else set()
    m2 = enlarge_m(m, ATTRIBUTION_EGIF)
    scroll2 = find_world_scroll(m2)
    (new_cell,) = set(scroll2.cell_ids) - before_cells
    eid = next(e.id for e in m2.E
               if m2.get_context(e.id) == new_cell
               and m2.rel[e.id] == "asserted")
    q_vid = m2.nu[eid][1]
    label, _sidecar = answer_label(answer_text)
    m3, cut_id = quote_existing_name(m2, q_vid, _utterance_graph(label))
    return m3, cut_id


__all__ = [
    "QuestionCandidate", "seal", "candidates_from_run", "render_note",
    "select_within_budget", "DEFAULT_BUDGET", "ParsedNote", "parse_note",
    "score", "note_substantially_answered", "OracleLedger", "p2_13_report",
    "conjectures_section", "reask_candidate", "opaque_note_qid",
    "resolve_note_qids", "bank_answer", "ATTRIBUTION_EGIF",
    "bank_answer_step", "BANK_TO_M", "bankable_outcomes",
    "answer_label", "_MAX_ANSWER_LABEL",
]
