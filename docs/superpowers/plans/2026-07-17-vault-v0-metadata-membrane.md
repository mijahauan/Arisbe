# Vault V0 — the Metadata Membrane: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stage V0 of the vault cycle (spec: `docs/superpowers/specs/2026-07-17-vault-cycle-design.md`) — the offline, deterministic metadata membrane over the author's Obsidian vault, with the journal's two-timeline reader, the horizon register, and the carried-to-vault fixes; fixture-verified in CI, real-vault launch (RUN 13) left as the author's action.

**Architecture:** extract the generic probe-feed mechanics into `src/probe_feed.py` (`ProbeDirectedFeedBase` — drain-refill propose, model-delta yield, journal, choosers, count-or-refuse dispatch); `src/arithmetic_world.py` refactors onto it with zero behavior change (its 20 tests are the gate); the horizon register joins `src/attention_economy.py`; `src/vault_world.py` provides `VaultWorld` (filesystem metadata reader + journal splitter, EGIF-safe emission) and `VaultFeed` (the socket's fourth consumer). All CI tests run against a synthetic fixture vault — the real vault is never touched by CI.

**Tech Stack:** Python 3.12, uv, pytest. Existing seams: `attention_economy.AttentionEconomy/Want`, `agon_evolution.run`, `egif_parser_dau.parse_egif`, `tomos_service.TomosService`. Sanitizer pattern mirrored from `wikidata_source._relation_name`/`_const` (do not import the private names — replicate the two small functions with a crediting comment).

## Global Constraints

- **Custody (the spec's guard):** nothing derived from the REAL vault enters git — CI uses only the fixture; the driver writes to `runs/run13/` which Task 7 adds to `.gitignore`; only author-reviewed aggregates ever get committed (to `runs/RUN_13_LOG.md`).
- **Metadata only:** V0 reads structure — paths, dates, links, tags, kinds, sizes, date-lines. It never emits note body text into facts. The journal reader reads lines only to find date-line boundaries; entry *content* is never emitted (entry length in lines is fine).
- **Determinism:** sorted directory walks, no RNG, no wall-clock; every emission parses under `parse_egif`; identical vault state → identical trajectories.
- **Bounded, counted:** every register/queue/horizon capped with drops counted; malformed date-lines flagged to the horizon, never silently mis-dated; the count-or-refuse dispatch rule (a want the feed cannot voice is *refused and counted*, never silently settled).
- **No changes** to protected modules, `agon_evolution.py`, `query_docket.py`. `src/arithmetic_world.py` changes ONLY as the Task 1 refactor (behavior-preserving; its existing 20 tests must pass unchanged except import-path-neutral edits are NOT allowed — tests stay byte-identical).
- Run tests `uv run pytest <file> -q`; imports flat; pre-commit hook runs on commit (~1 min); commit per task, plain-prose messages; do NOT push until the final review passes.
- The registered rung-1 criteria S1–S5 must remain green after the refactor (`tests/test_arithmetic_world.py` 20 passed, `tests/test_attention_economy.py` 16 passed).

---

### Task 1: extract `ProbeDirectedFeedBase` (behavior-preserving refactor + count-or-refuse)

**Files:**
- Create: `src/probe_feed.py`
- Modify: `src/arithmetic_world.py` (subclass the base; re-export moved names)
- Test: `tests/test_probe_feed.py` (new, small); gate = existing `tests/test_arithmetic_world.py` unchanged and green

**Interfaces:**
- Produces: `probe_feed.ProbeDirectedFeedBase(economy, *, chooser=None, probe_budget=1, journal=None)` with `propose(model, round_idx)` implementing: model-delta yield read (via `_model_signature`) → `economy.observe` → if queue empty: `self._seed(round_idx)` (once), `self._refill(round_idx)`, choose, execute each chosen via `self._execute(want) -> Optional[str]`, settle non-persistent kinds, queue non-empty emissions → pop-or-None. Hooks subclasses implement: `_seed(round_idx)`, `_refill(round_idx)`, `_execute(want)`, class attr `persistent_kinds: frozenset = frozenset()`.
- **Count-or-refuse:** in the base execute wrapper, a chosen want whose `_execute` returns `None`/`""` AND whose kind is not in `persistent_kinds` increments `self.refused` (public counter) and is settled — counted, never silent. (`confirm` re-probes legitimately emit their atoms again, so arithmetic sets `persistent_kinds = frozenset({"confirm"})` and its `_execute` always returns the conjunction — `refused` stays 0 there.)
- Moved verbatim into `probe_feed.py`: `_model_signature`, `_labels_of`, `fifo_chooser`, `scatter_chooser` (sha1 digest byte-identical — the golden test must still pass), `replay_choices`.
- `arithmetic_world.py` re-exports `fifo_chooser`, `scatter_chooser`, `replay_choices`, `_model_signature` so existing test imports work unchanged; `ProbeDirectedFeed(ArithmeticWorld, AttentionEconomy, ...)` keeps its exact constructor signature and behavior, now as a subclass.

- [ ] **Step 1: Write the new base + refactor** (this is a refactor task — the failing-test gate is the EXISTING suites; write `tests/test_probe_feed.py` with two tests):

```python
# tests/test_probe_feed.py
"""The generic probe-feed base (vault-cycle Task 1): mechanics shared by every
world; count-or-refuse is the new contract (carried from the rung-1 review)."""
from attention_economy import AttentionEconomy, Want
from probe_feed import ProbeDirectedFeedBase
from egif_parser_dau import parse_egif


class _VoicelessFeed(ProbeDirectedFeedBase):
    """A feed whose only want cannot be voiced — must be refused and counted."""
    def _seed(self, round_idx):
        self._economy.register(Want(kind="mute", key=("m",), payload=None))
    def _refill(self, round_idx):
        pass
    def _execute(self, want):
        return None


def test_unvoiceable_want_is_refused_and_counted():
    feed = _VoicelessFeed(AttentionEconomy())
    out = feed.propose(parse_egif('(even "0")'), 1)
    assert out is None
    assert feed.refused == 1
    assert feed._economy.wants() == []   # settled, not respinning


def test_base_is_abstractless_and_deterministic():
    a = _VoicelessFeed(AttentionEconomy()); b = _VoicelessFeed(AttentionEconomy())
    m = parse_egif('(even "0")')
    assert [a.propose(m, r) for r in (1, 2)] == [b.propose(m, r) for r in (1, 2)]
```

Then create `src/probe_feed.py` by MOVING the generic mechanics out of `src/arithmetic_world.py`'s `ProbeDirectedFeed` (read that class first; keep its logic byte-faithful where moved) and add the refuse counter:

```python
# src/probe_feed.py
"""The probe-feed socket base — the generic mechanics every world's feed shares
(vault-cycle Task 1; extracted from the rung-1 arithmetic feed per the final
review's carry list). Subclasses supply _seed/_refill/_execute; the base owns
the drain-refill propose loop, model-delta yield reading, the journal, the
baseline choosers, and the count-or-refuse dispatch rule: a chosen want the
feed cannot voice is refused and COUNTED (self.refused), never silently
dropped."""
from __future__ import annotations

import hashlib
from typing import List, Optional

from attention_economy import AttentionEconomy, Want
from world_scroll import m_view


def _labels_of(g, eid):
    out = []
    for vid in g.nu.get(eid, ()):
        v = g.get_vertex(vid)
        out.append(getattr(v, "label", None) if v is not None else None)
    return tuple(out)


def _model_signature(model) -> tuple:
    g = m_view(model)
    from eg_navigation import child_cuts, area_of
    atoms = frozenset(
        (g.rel[e.id], _labels_of(g, e.id))
        for e in g.E if e.id in g.rel and area_of(g, e.id) == g.sheet)
    return (atoms, len(child_cuts(g, g.sheet)))


def fifo_chooser(economy: AttentionEconomy, k: int, round_idx: int):
    ws = sorted(economy.wants(), key=lambda w: (w.created_round, w.kind, repr(w.key)))
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


def scatter_chooser(economy: AttentionEconomy, k: int, round_idx: int):
    ws = sorted(
        economy.wants(),
        key=lambda w: int(hashlib.sha1(
            f"{repr(w.key)}{round_idx}".encode()).hexdigest()[:8], 16) % 997)
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


def replay_choices(journal):
    return [j["chosen"] for j in journal]


class ProbeDirectedFeedBase:
    persistent_kinds: frozenset = frozenset()

    def __init__(self, economy: AttentionEconomy, *, chooser=None,
                 probe_budget: int = 1, journal=None):
        self._economy = economy
        self._chooser = chooser
        self._budget = probe_budget
        self._queue: List[str] = []
        self._last_chosen: List[Want] = []
        self._prev_sig = None
        self._seeded = False
        self.refused = 0
        self.journal: list = [] if journal is None else journal

    # -- world hooks ---------------------------------------------------------
    def _seed(self, round_idx: int) -> None: ...
    def _refill(self, round_idx: int) -> None: ...
    def _execute(self, want: Want) -> Optional[str]: ...

    # -- the round loop ------------------------------------------------------
    def propose(self, model, round_idx: int):
        sig = _model_signature(model)
        if self._prev_sig is not None and self._last_chosen:
            prev_atoms, prev_cuts = self._prev_sig
            atoms, cuts = sig
            # round-granular: the full delta credits every chosen want's kind
            events = len(atoms ^ prev_atoms) + abs(cuts - prev_cuts)
            self._economy.observe(round_idx, [(w, events) for w in self._last_chosen])
            self._last_chosen = []
        self._prev_sig = sig

        if not self._queue:
            if not self._seeded:
                self._seeded = True
                self._seed(round_idx)
            self._refill(round_idx)
            choose = self._chooser or (lambda e, k, r: e.choose(k, r))
            chosen = choose(self._economy, self._budget, round_idx)
            self._last_chosen = list(chosen)
            self.journal.append({
                "round": round_idx,
                "chosen": [(w.kind, repr(w.key)) for w in chosen],
                "snapshot": self._economy.snapshot(),
            })
            for w in chosen:
                egif = self._execute(w)
                if egif:
                    self._queue.append(egif)
                elif w.kind not in self.persistent_kinds:
                    self.refused += 1
                if w.kind not in self.persistent_kinds:
                    self._economy.settle(w.kind, w.key)

        return self._queue.pop(0) if self._queue else None
```

**Then refactor `src/arithmetic_world.py`**: delete its copies of the moved helpers and the loop body; `class ProbeDirectedFeed(ProbeDirectedFeedBase)` keeping its `__init__(world, economy, *, chooser=None, probe_budget=1, laws=(FERMAT_LAW,), confirm_lattice=60, musement=True, journal=None)` (call `super().__init__(economy, chooser=chooser, probe_budget=probe_budget, journal=journal)` then set world/lattice/laws/musement/extend state), move its seeding into `_seed`, extends into `_refill`, emission dispatch into `_execute` (returning the EGIF or `""`), and set `persistent_kinds = frozenset({"confirm"})`. Re-export at the bottom: `from probe_feed import fifo_chooser, scatter_chooser, replay_choices, _model_signature  # noqa: F401 — stable import surface for the rung-1 tests`. **Read the current class carefully before cutting; the arithmetic tests are the truth.**

- [ ] **Step 2: Run the gates**

Run: `uv run pytest tests/test_probe_feed.py tests/test_arithmetic_world.py tests/test_attention_economy.py -q`
Expected: 2 + 20 + 16 = 38 passed. Any arithmetic failure = the refactor changed behavior — fix the refactor, never the tests.

- [ ] **Step 3: Commit**

```bash
git add src/probe_feed.py src/arithmetic_world.py tests/test_probe_feed.py
git commit -m "Vault V0 task 1: the probe-feed base extracted; count-or-refuse dispatch; arithmetic feed re-seated unchanged"
```

---

### Task 2: the horizon register

**Files:**
- Modify: `src/attention_economy.py` (append)
- Test: `tests/test_attention_economy.py` (append)

**Interfaces:**
- Produces: `HorizonItem(kind, ref, size, reason, registered_round, attempts=0)` (dataclass) and `Horizon(max_items=2000)` with `register(item) -> bool` (dedup by `ref`; cap counted in `dropped`), `reattempt(round_idx, k=1) -> list[HorizonItem]` (oldest-first, fewest-attempts-first, deterministic; increments attempts), `settle(ref)`, `open_items() -> list`, `snapshot() -> dict` (counts by kind + reason, dropped). The register of the not-yet-legible: retained, counted, re-attemptable — never silently discarded (BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3 rung 1, deferred to this stage).

- [ ] **Step 1: Append the failing tests**

```python
class TestHorizon:
    def test_register_dedups_and_counts_cap_drops(self):
        from attention_economy import Horizon, HorizonItem
        h = Horizon(max_items=2)
        assert h.register(HorizonItem("pdf", "a.pdf", 100, "binary", 1))
        assert h.register(HorizonItem("pdf", "a.pdf", 100, "binary", 1)) is False
        assert h.dropped == 0
        assert h.register(HorizonItem("img", "b.png", 5, "binary", 1))
        assert h.register(HorizonItem("img", "c.png", 5, "binary", 2)) is False
        assert h.dropped == 1

    def test_reattempt_is_oldest_first_and_counts_attempts(self):
        from attention_economy import Horizon, HorizonItem
        h = Horizon()
        h.register(HorizonItem("canvas", "new.canvas", 1, "drawn", 5))
        h.register(HorizonItem("pdf", "old.pdf", 1, "binary", 1))
        first = h.reattempt(round_idx=9, k=1)
        assert [i.ref for i in first] == ["old.pdf"]
        assert first[0].attempts == 1
        h.settle("old.pdf")
        assert [i.ref for i in h.open_items()] == ["new.canvas"]

    def test_snapshot_counts_by_kind_and_reason(self):
        from attention_economy import Horizon, HorizonItem
        h = Horizon()
        h.register(HorizonItem("date", "j:L12", 1, "malformed_date_line", 1))
        s = h.snapshot()
        assert s["by_reason"]["malformed_date_line"] == 1 and s["open"] == 1
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_attention_economy.py::TestHorizon -q` → ImportError.

- [ ] **Step 3: Append the implementation to `src/attention_economy.py`**

```python
@dataclass
class HorizonItem:
    """One not-yet-legible thing: retained, counted, re-attemptable."""
    kind: str
    ref: str
    size: int
    reason: str
    registered_round: int
    attempts: int = 0


class Horizon:
    """The horizon register (BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3, built at the
    vault stage where illegibility is real): what came back not-yet-legible,
    kept with counted size and re-attempted as legibility improves — where
    tomorrow's sensor space waits. Bounded, dedup'd by ref, drops counted."""

    def __init__(self, max_items: int = 2000):
        self._max = max_items
        self._items: Dict[str, HorizonItem] = {}
        self.dropped = 0

    def register(self, item: HorizonItem) -> bool:
        if item.ref in self._items:
            return False
        if len(self._items) >= self._max:
            self.dropped += 1
            return False
        self._items[item.ref] = item
        return True

    def open_items(self) -> List[HorizonItem]:
        return sorted(self._items.values(),
                      key=lambda i: (i.attempts, i.registered_round, i.ref))

    def reattempt(self, round_idx: int, k: int = 1) -> List[HorizonItem]:
        out = self.open_items()[:k]
        for i in out:
            i.attempts += 1
        return out

    def settle(self, ref: str) -> None:
        self._items.pop(ref, None)

    def snapshot(self) -> dict:
        by_kind: Dict[str, int] = {}
        by_reason: Dict[str, int] = {}
        for i in self._items.values():
            by_kind[i.kind] = by_kind.get(i.kind, 0) + 1
            by_reason[i.reason] = by_reason.get(i.reason, 0) + 1
        return {"open": len(self._items), "dropped": self.dropped,
                "by_kind": dict(sorted(by_kind.items())),
                "by_reason": dict(sorted(by_reason.items()))}
```

(Also extend `__all__` with `"Horizon", "HorizonItem"`; `Dict` needs importing if not present.)

- [ ] **Step 4: Run** — `uv run pytest tests/test_attention_economy.py -q` → 19 passed.
- [ ] **Step 5: Commit** — `git add -u && git add tests/test_attention_economy.py && git commit -m "Vault V0 task 2: the horizon register - the not-yet-legible retained, counted, re-attemptable"`

---

### Task 3: the fixture vault + `VaultWorld` reader core

**Files:**
- Create: `tests/fixtures/vorago_fixture/` (the synthetic vault — commit it; it contains NO real vault content)
- Create: `src/vault_world.py` (reader half)
- Test: `tests/test_vault_world.py`

**Interfaces:**
- Fixture layout (create exactly; keep contents to a few lines each):
  - `Ideas/alpha.md`: frontmatter `---\ndate: 2025-03\ntags: [logic]\n---` + body containing `[[beta]]` and `#peirce`
  - `Ideas/beta.md`: plain body, no links
  - `Clippings/saved page.md`: any two lines (the collected prior)
  - `People/friend.md`: one line (third-party folder)
  - `Personal/Journal-x/Journal.md`: see Task 4 (create the file in THIS task with the Task 4 content so the fixture is complete once)
  - `attachments/scan.pdf`: empty file · `attachments/sketch.canvas`: empty file
- Produces: `VaultWorld(root)` with:
  - `notes() -> list[str]` — sorted relative md paths;
  - `note_id(relpath) -> str` — EGIF-safe constant (mirror `wikidata_source`'s `_const` pattern: strip quotes/backslashes, non-printables → space; keep case and slashes) and `labels: dict[id, relpath]`;
  - `note_facts(relpath) -> str` — EGIF conjunction: `(note "id")`, `(in_folder "id" "top_dir")`, `(kind "id" "md")`, `(modified "id" "YYYY-MM")` (frontmatter `date:` wins, else file mtime), `(links "id" "target_id")` per `[[wikilink]]` resolved case-insensitively against note stems (unresolved links → `(links_out "id" "raw")`), `(tagged "id" "tag")` per `#tag` and frontmatter tags, `(collected_prior "id")` iff top dir == `Clippings`;
  - `attachment_items(round_idx) -> list[HorizonItem]` — every non-md file as a HorizonItem (kind=extension, reason="binary", size=bytes);
  - `probe_cost(relpath) -> float` — `1.0 + size_bytes/20_000`;
  - every emission parses under `parse_egif`; walks sorted; no RNG/wall-clock (mtime is data, not clock).

- [ ] **Step 1: Create the fixture files** (exact small contents; journal content from Task 4's spec below).
- [ ] **Step 2: Write the failing tests**

```python
# tests/test_vault_world.py
"""Vault V0 — the metadata membrane's reader, against the synthetic fixture
(spec: docs/superpowers/specs/2026-07-17-vault-cycle-design.md). Metadata
only: no note body text ever appears in an emission."""
from pathlib import Path
from egif_parser_dau import parse_egif
from vault_world import VaultWorld

FIX = Path(__file__).parent / "fixtures" / "vorago_fixture"


class TestReader:
    def test_notes_sorted_and_ids_egif_safe(self):
        w = VaultWorld(FIX)
        assert w.notes() == sorted(w.notes())
        for n in w.notes():
            parse_egif(f'(note "{w.note_id(n)}")')

    def test_note_facts_carry_structure_not_content(self):
        w = VaultWorld(FIX)
        egif = w.note_facts("Ideas/alpha.md")
        parse_egif(egif)
        i = w.note_id("Ideas/alpha.md")
        assert f'(in_folder "{i}" "Ideas")' in egif
        assert f'(modified "{i}" "2025-03")' in egif      # frontmatter wins
        assert '(links ' in egif and '(tagged ' in egif
        assert "peirce" in egif.lower()
        # metadata only: no body words leak (alpha.md's body must carry a
        # sentinel word the test asserts absent — put the word `SENTINELBODY`
        # in the fixture body when creating it)
        assert "SENTINELBODY" not in egif

    def test_clippings_prior_and_wikilink_resolution(self):
        w = VaultWorld(FIX)
        c = w.note_id("Clippings/saved page.md")
        assert f'(collected_prior "{c}")' in w.note_facts("Clippings/saved page.md")
        a = w.note_facts("Ideas/alpha.md")
        assert f'(links "{w.note_id("Ideas/alpha.md")}" "{w.note_id("Ideas/beta.md")}")' in a

    def test_attachments_go_to_horizon_items(self):
        w = VaultWorld(FIX)
        items = w.attachment_items(round_idx=1)
        refs = {i.ref for i in items}
        assert any(r.endswith("scan.pdf") for r in refs)
        assert any(r.endswith("sketch.canvas") for r in refs)
        assert all(i.reason == "binary" for i in items)
```

- [ ] **Step 3: Run to verify failure**, **Step 4: implement the reader half of `src/vault_world.py`** (module docstring citing the spec + custody constraint; `_const`-style sanitizer with a comment crediting the `wikidata_source` precedent; frontmatter = the first `---` block parsed leniently for `date:` and `tags:`; wikilink regex `\[\[([^\]|#]+)`; tag regex `(?<!\S)#([A-Za-z][\w/-]*)`), **Step 5: run to green** (`uv run pytest tests/test_vault_world.py -q` → 4 passed), **Step 6: commit** — `Vault V0 task 3: the fixture vault + the metadata reader - structure in, content never`.

---

### Task 4: the journal reader — two timelines held apart

**Files:**
- Modify: `src/vault_world.py` (append), fixture `Personal/Journal-x/Journal.md` (created in Task 3 with THIS content):

```
1930-05-02
family record predating the author
1973-11-15
an early entry SENTINELBODY
1983-07
a heavy-eighties entry
2115-21
a malformed dateline that must be flagged
2023-11-26
the latest entry
```

**Interfaces:**
- Produces on `VaultWorld`: `journal_paths() -> list[str]` (files matching `Journal*.md`, sorted); `journal_entries(relpath) -> (entries, flagged)` where `entries` = list of `(event_date, line_no, n_lines)` for date-lines matching `^\d{4}([-/.]\d{1,2}){1,2}$` **with month ∈ 1..12 (and day ∈ 1..31 when present)** — a line matching the shape but failing the range check (the fixture's `2115-21`) goes to `flagged` (line_no + raw shape only, never the content); `journal_facts(relpath) -> str` — per entry: `(journal_entry "j:LINE")`, `(entry_date "j:LINE" "YYYY-MM")`, `(entry_lines "j:LINE" "N")` — **event-time only; writing-time is deliberately absent** (a hypothesis for V1/V2, per the spec's two-timeline rule); `journal_horizon_items(round_idx)` — one `HorizonItem(kind="date", reason="malformed_date_line")` per flagged line.

- [ ] **Step 1: Append the failing tests**

```python
class TestJournal:
    def test_entries_split_on_valid_datelines_only(self):
        w = VaultWorld(FIX)
        [j] = w.journal_paths()
        entries, flagged = w.journal_entries(j)
        dates = [e[0] for e in entries]
        assert dates == ["1930-05", "1973-11", "1983-07", "2023-11"]
        assert len(flagged) == 1                     # 2115-21: month 21 invalid

    def test_journal_facts_are_event_time_claims_without_content(self):
        w = VaultWorld(FIX)
        [j] = w.journal_paths()
        egif = w.journal_facts(j)
        parse_egif(egif)
        assert '(entry_date ' in egif and '"1930-05"' in egif
        assert "SENTINELBODY" not in egif            # content never leaks
        assert "writing" not in egif                 # writing-time absent by design

    def test_malformed_datelines_reach_the_horizon_counted(self):
        w = VaultWorld(FIX)
        [j] = w.journal_paths()
        items = w.journal_horizon_items(round_idx=1)
        assert len(items) == 1 and items[0].reason == "malformed_date_line"
```

- [ ] **Step 2–4:** RED → implement → `uv run pytest tests/test_vault_world.py -q` → 7 passed.
- [ ] **Step 5: Commit** — `Vault V0 task 4: the journal reader - event-time as claim, writing-time absent by design, malformed lines to the horizon`

---

### Task 5: `VaultFeed` — the socket's fourth consumer

**Files:**
- Modify: `src/vault_world.py` (append)
- Test: `tests/test_vault_world.py` (append)

**Interfaces:**
- Produces: `VaultFeed(world, economy, *, horizon=None, chooser=None, probe_budget=1, journal=None)` subclassing `probe_feed.ProbeDirectedFeedBase`:
  - `_seed`: one `Want(kind="scan", key=("scan", top_dir), cost=1.0)` per top-level dir (sorted); one `Want(kind="journal", key=("journal", path), cost=world.probe_cost(path), severity=8.0)` per journal file (the spine — the severity call mirrors the arithmetic hunts); attachments registered to the horizon at seed time.
  - `_refill`: for every note already *discovered* (its folder scanned) but not yet emitted, ensure a `Want(kind="read", key=("read", relpath), cost=world.probe_cost(relpath), severity=2.0 if the note has unresolved inbound links else 1.0)` — top up to a bounded window of 5 outstanding read wants (the Task-1 base makes the bounded-scan idiom available; drops counted via the economy cap).
  - `_execute`: `scan` → the folder's note-listing facts (one `(note "id") (in_folder ...)` pair per note, batched in one conjunction); `read` → `world.note_facts(relpath)`; `journal` → `world.journal_facts(path)`. Unknown kind → `None` (the base counts the refusal — this is the count-or-refuse rule live).
  - `persistent_kinds = frozenset()` (every vault want settles on execution; re-reads are only scheduled by decay pressure in later stages).
- The M this produces is **first-order activity evidence about the author** — no quoted cells yet (V1's job), so the polarity gate applies as usual.

- [ ] **Step 1: Append the failing tests**

```python
class TestFeed:
    def _feed(self):
        from attention_economy import AttentionEconomy, Horizon
        from vault_world import VaultWorld, VaultFeed
        w = VaultWorld(FIX)
        h = Horizon()
        return VaultFeed(w, AttentionEconomy(), horizon=h), w, h

    def test_journal_outranks_scans_and_lands_first(self):
        from egif_parser_dau import parse_egif
        feed, w, h = self._feed()
        first = feed.propose(parse_egif('(even "0")'), 1)
        assert "(journal_entry" in first        # severity 8 wins round 1

    def test_full_drive_discovers_reads_and_horizons(self):
        from egif_parser_dau import parse_egif
        from agon_evolution import run
        feed, w, h = self._feed()
        res = run('(even "0")', feed, rounds=25, uod_id="vault_fix",
                  name="vault fixture drive")
        final = res.uod.current_egi
        from agon_evolution import peel
        from semantic_game import Verdict3
        a = w.note_id("Ideas/alpha.md")
        assert peel(final, f'(note "{a}")').verdict is Verdict3.TRUE
        assert peel(final, f'(collected_prior "{w.note_id("Clippings/saved page.md")}")').verdict is Verdict3.TRUE
        assert peel(final, '(entry_date "j:L1" "1930-05")').verdict is not Verdict3.FALSE
        assert h.snapshot()["open"] >= 3        # pdf + canvas + malformed dateline
        assert feed.refused == 0

    def test_metadata_only_end_to_end(self):
        from egif_parser_dau import parse_egif
        feed, w, h = self._feed()
        m = parse_egif('(even "0")')
        emissions = [feed.propose(m, r) for r in range(1, 26)]
        assert all("SENTINELBODY" not in (e or "") for e in emissions)
```

(The `j:L1` id in the second test must match the reader's entry-id convention — adjust the literal to the convention Task 4 implemented; the assertion's substance is that a journal entry-date fact stands in M.)

- [ ] **Step 2–4:** RED → implement → `uv run pytest tests/test_vault_world.py -q` → 10 passed; also re-run `tests/test_arithmetic_world.py tests/test_attention_economy.py tests/test_probe_feed.py` (20 + 19 + 2 green).
- [ ] **Step 5: Commit** — `Vault V0 task 5: VaultFeed - the socket's fourth consumer; the journal is the severity spine`

---

### Task 6: determinism + replay

**Files:**
- Test: `tests/test_vault_world.py` (append)

- [ ] **Step 1: Append**

```python
class TestDeterminism:
    def test_identical_fixture_identical_trajectories(self):
        from probe_feed import replay_choices
        from agon_evolution import run
        def drive():
            from attention_economy import AttentionEconomy, Horizon
            from vault_world import VaultWorld, VaultFeed
            feed = VaultFeed(VaultWorld(FIX), AttentionEconomy(), horizon=Horizon())
            res = run('(even "0")', feed, rounds=20, uod_id="vfx", name="vfx")
            return replay_choices(feed.journal), [o.disposition for o in res.outcomes]
        assert drive() == drive()
```

- [ ] **Step 2: Run** — must pass; a failure is a real nondeterminism bug (unsorted walk, set iteration) — fix in `vault_world.py`.
- [ ] **Step 3: Commit** — `Vault V0 task 6: determinism pinned on the fixture`

---

### Task 7: the driver, custody, and the RUN 13 skeleton

**Files:**
- Create: `tools/run_vault_v0.py`
- Modify: `.gitignore` (add `runs/run13/`)
- Create: `runs/RUN_13_LOG.md` (priors only — no data)

**Interfaces:**
- `tools/run_vault_v0.py`: argparse — `--root` (default `/Users/mjh/Documents/Vorago`), `--rounds` (default 200), `--segments` (default 1), `--runs-dir` (default `runs/run13`), `--fixture` (flag: use the test fixture instead — the smoke path). Per segment: build `VaultWorld`/`VaultFeed`/`AttentionEconomy`/`Horizon`, drive `agon_evolution.run`, then `TomosService(runs_dir/"universes").save_uod_with_chain(res.uod, res.chain)`, and print an aggregate digest ONLY (counts: notes seen, entries dated per decade, horizon snapshot, ledger snapshot, |M|) — **never note ids/titles** (custody: even ids stay out of stdout captured in logs; the digest is numbers).
- `runs/RUN_13_LOG.md`: the P1¹³–P5¹³ priors copied from the spec verbatim + an empty findings section + the custody note (model artifacts live in `runs/run13/`, gitignored; only author-reviewed aggregates enter this log).

- [ ] **Step 1: Write the driver** (compact; reuse the segment pattern from the fixture tests; wire `--fixture` to `tests/fixtures/vorago_fixture`).
- [ ] **Step 2: Smoke it on the fixture** — `uv run python tools/run_vault_v0.py --fixture --rounds 25` → digest prints, a UoD lands under `runs/run13/universes`, exit 0. Then `git status --short` must show `runs/run13/` NOT listed (the .gitignore works).
- [ ] **Step 3: Commit** — `Vault V0 task 7: the driver, the custody boundary (runs/run13 gitignored), and RUN 13's pre-registered priors`

---

### Task 8: docs disposition + full suite

**Files:**
- Modify: `docs/superpowers/specs/2026-07-17-vault-cycle-design.md` (append a V0 build record: what was built, test counts, the count-or-refuse + horizon now real, refactor note), `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` (rung-1 §3: horizon register now BUILT at the vault stage — one sentence), `CLAUDE.md` (module lines: `probe_feed.py`, `vault_world.py`, the Horizon addition to the `attention_economy.py` line), `CURRENT_PLAN.md` (V0 built; RUN 13 awaits the author's launch), memory topic + MEMORY.md.

- [ ] **Step 1: Full suite** — `uv run pytest tests/ -q` (~25 min): expected all green (3691 + ~14 new ≈ 3705, 0 failed). Any new failure: diagnose before docs.
- [ ] **Step 2: Write the records** (honest counts from the actual runs).
- [ ] **Step 3: Commit** — `Vault V0 built: the metadata membrane fixture-verified; RUN 13 awaits the author` — do NOT push (the controller pushes after the final whole-branch review).

---

## Self-Review (plan-writing time)

- **Spec coverage:** carried fixes (T1) ✓ · horizon (T2) ✓ · reader + provenance prior + third-party-as-metadata (T3) ✓ · journal two-timeline (T4) ✓ · feed/socket (T5) ✓ · determinism/replay (T6) ✓ · custody + driver + priors (T7) ✓ · docs (T8) ✓. V1/V2 explicitly out of scope. The real-vault RUN 13 launch is the author's act, not a task.
- **Verification points flagged:** the arithmetic refactor's gate is its untouched test file; the `j:L1` id literal must match Task 4's convention; `_model_signature`'s `area_of/child_cuts` imports verified in rung 1.
- **Type consistency:** `ProbeDirectedFeedBase` hooks (`_seed/_refill/_execute`, `persistent_kinds`) used identically in T1 (arithmetic) and T5 (vault); `HorizonItem(kind, ref, size, reason, registered_round)` consistent across T2/T3/T4/T5.
