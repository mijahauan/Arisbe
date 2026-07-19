# V2a.1 — the Obsidian Oracle Notes: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The vault-native oracle loop per the V2a ruling (spec: `docs/superpowers/specs/2026-07-17-vault-cycle-design.md`, "Stage V2"): after a run, a questions note (≤5 questions, ≤1 reflective, sealed forecasts, a Conjectures section) is written into the vault's `Arisbe/` folder; the next run parses answers/declines/silence + the budget knob, scores forecasts, writes the Reveals section, and excludes Arisbe-authored notes from author-evidence. **V2a.1 banks answers in the run's side-store with marker facts; quotation-cell banking into M is V2a.2 (out of scope, flagged).**

**Architecture:** one new module `src/oracle_notes.py` (candidates → note rendering; note parsing; seal/reveal; the answer ledger) + a provenance-exclusion rule in `src/vault_world.py` (an `authored_by: arisbe` note never emits author-evidence facts) + driver wiring in `tools/run_vault_v0.py` (read-previous → reveals → write-next; fixture/test mode writes under `--runs-dir`, never into a real vault). Fixture-verified in CI; the first real note comes from the author's next real run.

**Tech Stack:** Python 3.12, uv, pytest. Existing seams: `vault_world.VaultWorld` (incl. `long_labels`), `attention_economy.Horizon`, the driver's `_digest`/`_run_segment`, `agon_evolution.EvolutionResult` (`known_laws`, `discoveries`).

## Global Constraints

- **Custody:** the questions note is written into the author's vault ONLY on a real-vault run (`--root` mode); in `--fixture`/test mode it lands under `--runs-dir`/`tmp_path`. Forecast plaintexts + the answer ledger live in the gitignored runs dir. Note content may carry real vault paths (it lives IN the author's vault — the custody boundary is git/stdout, not the author's own Obsidian); stdout still prints counts + the note's relative path only.
- **Pull-only:** no notification of any kind; the console line + the note's existence are the only signals.
- **Budget:** ≤5 questions, ≤1 reflective per note, read from the PREVIOUS note's frontmatter knob when present (`budget: {max: N, reflective: M}`); a new note is written only if the previous note is substantially answered (≥half its questions answered/declined) or absent/waved-off (deleted).
- **Seal-then-reveal:** forecast plaintext in the side-store (`oracle/forecasts.jsonl`), SHA-256 hex in the note; the Reveals section prints plaintext + hash + hit/miss/unscored.
- **Decline/silence:** `declined` (case-insensitive, alone on the answer line) = declined; empty `**A:**` = ignored. Both first-class in the ledger.
- **Determinism:** no RNG; no wall-clock EXCEPT the note filename date, which the driver passes in explicitly (`note_date` argument — testable, injectable).
- Every EGIF emission parses; all suites green; pre-commit hook runs per commit; do NOT push until the final review passes. No changes to protected modules or `agon_evolution.py`.
- Commit messages plain prose, per repo style.

---

### Task 1: `oracle_notes.py` — candidates, seal, and the note renderer

**Files:**
- Create: `src/oracle_notes.py`
- Test: `tests/test_oracle_notes.py`

**Interfaces (produces):**
- `QuestionCandidate(qid: str, tier: str, text: str, why: str, settles: str, forecast: str, severity: float = 1.0)` — tiers `"quick" | "short" | "reflective"`. `qid` deterministic (caller-supplied, e.g. `"prov:<id>"`).
- `seal(forecast: str) -> str` — SHA-256 hexdigest of the UTF-8 forecast text.
- `candidates_from_run(world, horizon, known_laws: list[str], labels: dict) -> list[QuestionCandidate]` — the V2a.1 sources, deterministic order:
  1. **Provenance** (`qid="prov:<note_id>"`, tier quick): for up to 3 `collected_prior`-bucketed notes (i.e., notes whose top dir is `Clippings`), "Is `<decoded path>` collected from elsewhere, or your own writing?"; forecast "collected" (the prior).
  2. **Multi-journal** (`qid="journal:<id>"`, tier quick): when `world.journal_paths()` has >1 file, one question per extra file (up to 2): "Is `<path>` a genuine journal, or a fragment/copy of `<main>`?"; forecast "fragment".
  3. **Horizon** (`qid="horizon:<ref>"`, tier short): up to 2 largest open `HorizonItem`s: "What is `<decoded ref>` (a `<kind>` I can't read yet)? One line is plenty."; forecast "unknown" (unscored).
  4. **Writing-time** (`qid="journal-timelines"`, tier reflective, standing): the contemporaneous-vs-reconstructed question; offered until answered once, then never again (the ledger records it).
  Decoded paths come from `labels` (id→original merged from `world.labels()` + `world.long_labels`).
- `render_note(candidates, *, note_date: str, run_id: str, segment: int, budget: dict, reveals: list[dict] | None) -> str` — the markdown: frontmatter (`authored_by: arisbe`, run, segment, `budget: {max: N, reflective: M}`), optional `## Reveals` section (each dict: qid, forecast_plain, forecast_hash, answer, verdict `hit|miss|unscored`), optional `## Conjectures` section (see Task 3), then per-question blocks exactly in the V2a walkthrough's shape: `## Q<n> · <tier> — <topic-from-qid>`, the text, `*Why asked:* …`, `*Would settle:* …`, `*Forecast (sealed):* \`sha256:<hash>\``, `**A:**`. Budget enforced here: at most `max` questions, at most `reflective` reflective-tier, highest severity first, stable order.

- [ ] **Step 1: failing tests** — write `tests/test_oracle_notes.py`:

```python
"""V2a.1 — the Obsidian oracle notes (spec: docs/superpowers/specs/
2026-07-17-vault-cycle-design.md, Stage V2). Render/seal half."""
from pathlib import Path
from oracle_notes import QuestionCandidate, candidates_from_run, render_note, seal

FIX = Path(__file__).parent / "fixtures" / "vorago_fixture"


def _world():
    from vault_world import VaultWorld
    return VaultWorld(FIX)


class TestCandidates:
    def test_sources_fire_on_the_fixture(self):
        from attention_economy import Horizon, HorizonItem
        w = _world()
        h = Horizon()
        for i in w.attachment_items(1):
            h.register(i)
        cands = candidates_from_run(w, h, known_laws=[], labels=w.labels())
        qids = [c.qid for c in cands]
        assert any(q.startswith("prov:") for q in qids)      # Clippings note
        assert any(q.startswith("journal:") for q in qids)   # two journals in fixture
        assert any(q.startswith("horizon:") for q in qids)
        assert "journal-timelines" in qids
        assert [c.qid for c in cands] == qids                # deterministic order

    def test_reflective_is_exactly_the_standing_question(self):
        cands = candidates_from_run(_world(), None, known_laws=[], labels={})
        refl = [c for c in cands if c.tier == "reflective"]
        assert [c.qid for c in refl] == ["journal-timelines"]


class TestRender:
    def test_note_shape_and_budget(self):
        cands = [QuestionCandidate(f"q{i}", "quick", f"Question {i}?", "w", "s",
                                    forecast=f"f{i}", severity=float(i))
                 for i in range(8)]
        cands.append(QuestionCandidate("r1", "reflective", "Reflect?", "w", "s",
                                        forecast="deep", severity=9.0))
        cands.append(QuestionCandidate("r2", "reflective", "Reflect more?", "w", "s",
                                        forecast="deeper", severity=8.0))
        text = render_note(cands, note_date="2026-07-18", run_id="run13",
                           segment=3, budget={"max": 5, "reflective": 1},
                           reveals=None)
        assert text.count("## Q") == 5                       # max enforced
        assert text.count("· reflective") == 1               # reflective cap
        assert "authored_by: arisbe" in text
        assert "budget: {max: 5, reflective: 1}" in text
        assert f"sha256:{seal('deep')}"[:20] in text          # sealed, not plaintext
        assert "deep" == "deep" and "*Forecast (sealed):*" in text
        assert "\ndeep\n" not in text                         # plaintext absent

    def test_reveals_section_renders(self):
        text = render_note([], note_date="2026-07-18", run_id="r", segment=1,
                           budget={"max": 5, "reflective": 1},
                           reveals=[{"qid": "q1", "forecast_plain": "collected",
                                      "forecast_hash": seal("collected"),
                                      "answer": "yes, clipped", "verdict": "hit"}])
        assert "## Reveals" in text and "collected" in text and "hit" in text
```

- [ ] **Step 2:** RED (`ModuleNotFoundError`) → **Step 3:** implement (module docstring cites the spec + the V2a.1/V2a.2 stage split; `candidates_from_run` tolerates `horizon=None`; renderer writes the exact block shapes above) → **Step 4:** `uv run pytest tests/test_oracle_notes.py -q` → 4 passed → **Step 5:** commit `V2a.1 task 1: oracle question candidates, the seal, and the note renderer`.

---

### Task 2: the parser + ledger + reveals computation

**Files:**
- Modify: `src/oracle_notes.py` (append)
- Test: `tests/test_oracle_notes.py` (append)

**Interfaces (produces):**
- `parse_note(text: str) -> ParsedNote` — dataclass: `budget: dict` (the knob as edited), `answers: dict[qid, str]` (non-empty answer text), `declined: set[qid]`, `ignored: set[qid]`, `stray: str` (any text outside recognized blocks — kept verbatim as evidence). Qid recovery: embed `<!-- qid: … -->` HTML comments in the rendered blocks (invisible in Obsidian preview) — adjust Task 1's renderer accordingly in this task and update its tests if needed.
- `score(forecast_plain: str, answer: str) -> str` — `"hit"` if the forecast string appears case-insensitively in the answer (a deliberately modest heuristic, named in the docstring; V2a.2 refines), `"unscored"` if forecast is `"unknown"`, else `"miss"`.
- `OracleLedger(dir_path)` — JSONL persistence in the runs dir: `record_asked(note_date, qid, tier, forecast_plain, forecast_hash)`, `record_outcome(qid, status, answer_text, answered_note_date)`, `asked_ever(qid) -> bool` (the standing-question suppressor), `outcomes() -> list[dict]`, `build_reveals(parsed: ParsedNote) -> list[dict]` (joins answers to recorded forecasts → the reveal dicts of Task 1).
- `note_substantially_answered(parsed) -> bool` — ≥ half of its questions answered or declined.

- [ ] Steps: failing tests (round-trip: render → simulate author edits (answer q1, decline q2, leave q3 blank, change budget max to 3, add stray prose) → parse recovers all five facts; ledger round-trips asked/outcome; `build_reveals` yields hit/miss/unscored correctly; `asked_ever` suppresses the standing question) → implement → green (expect 8–9 total in the file) → commit `V2a.1 task 2: the answer parser, the oracle ledger, and reveals`.

---

### Task 3: the Conjectures section + vault-reader exclusion

**Files:**
- Modify: `src/oracle_notes.py`, `src/vault_world.py`
- Test: `tests/test_oracle_notes.py`, `tests/test_vault_world.py` (append)

**Interfaces:**
- `conjectures_section(known_laws: list[str], discoveries) -> str` — "## Conjectures" listing each admitted law as a plain-English gloss line (use `eg_to_english` if its API fits a bare law EGIF — check `grep -n "def " src/eg_to_english.py`; if not, a structural gloss "whenever (P x) holds, (Q x) follows" derived from the law regex used in `arithmetic_world.test_law_instance`) + the EGIF in a code span; empty string when nothing to show. Wire into `render_note(..., conjectures=...)`.
- **Reader exclusion** in `vault_world.py`: `_frontmatter_authored_by(fm)` helper; `note_facts` for a note whose frontmatter says `authored_by: arisbe` emits ONLY `(arisbe_note "id")` — no links/tags/modified/collected (Arisbe-ink never becomes author-evidence); `folder_listing_facts` likewise lists it only as `(arisbe_note …)`. Tests: a fixture note `Arisbe/Questions-2026-07-01.md` (synthetic, with the full rendered shape incl. one answered question) emits only the marker; the feed drive still `refused == 0`.

- [ ] Steps: RED → implement → green (`tests/test_vault_world.py` grows to 21; oracle file ~11) → commit `V2a.1 task 3: conjectures shown, Arisbe-ink excluded from author-evidence`.

---

### Task 4: driver wiring + end-to-end + docs

**Files:**
- Modify: `tools/run_vault_v0.py`
- Test: `tests/test_oracle_notes.py` (append an end-to-end class)
- Docs: spec V2a block (build record), `CLAUDE.md` (one module line), `runs/RUN_13_LOG.md` (one line: the oracle loop lands with V2a.1), memory.

**Driver flow (after the LAST segment only):**
1. Resolve the oracle dir: real-vault mode → `<root>/Arisbe/`; fixture mode → `<runs_dir>/arisbe_notes/`. Create it if absent.
2. Find the newest prior `Questions-*.md` there; if present, `parse_note` → `OracleLedger.record_outcome` per answer/decline/ignore → `build_reveals`; adopt its edited budget knob. If it is <substantially answered and not waved off, print `oracle: previous note awaits answers — no new note` and skip 3.
3. `candidates_from_run` (+ suppress `asked_ever` qids) → `render_note` with reveals + conjectures (from the final segment's `res.known_laws`/`res.discoveries`) → write `Questions-<note_date>.md` (note_date = the driver's `--note-date` flag, default today's ISO date computed once in `main` — the single sanctioned wall-clock read, injectable for tests) → `OracleLedger.record_asked` per question → print `questions_written: N → Arisbe/Questions-<date>.md`.
4. Digest gains `"oracle": {"questions_written": N, "reveals": M, "answers_recorded": K}`.

- [ ] Steps: end-to-end test (tmp vault copy of the fixture: run driver in fixture mode twice via `main([...])` — first invocation writes a note; simulate author answers by editing the file; second invocation records outcomes, writes reveals + a new note; assert the ledger + both notes' shapes; assert nothing was written outside `runs_dir` in fixture mode) → implement → green → run the three vault-adjacent suites (`test_oracle_notes.py`, `test_vault_world.py`, `test_attention_economy.py`, `test_probe_feed.py`) → docs (spec V2a.1 build record with honest counts; the V2a.2 remainder named: quotation-cell banking + answer NL interpretation) → commit `V2a.1 built: the oracle notes loop - render, answer, parse, seal, reveal, ledger` → full suite once (`uv run pytest tests/ -q`, foreground, ~25 min) before handing to the final review.

---

## Self-Review (plan-writing time)

- Spec coverage: all four V2a ruling points land (surface/one-folder/provenance-exclusion T3-T4; budget knob T1-T2-T4; seal-then-reveal T1-T2-T4; decline/silence + noisy-TV-inward T2 ledger + candidates suppression). Conjectures per the author's ask (T3). V2a.2 exclusions named. Custody: fixture mode never touches a real vault (T4 test asserts).
- Consistency: `QuestionCandidate`/`ParsedNote`/`OracleLedger` names used identically across tasks; the qid HTML-comment convention introduced in T2 amends T1's renderer (called out explicitly).
- Wall-clock: confined to one injectable site (T4).
