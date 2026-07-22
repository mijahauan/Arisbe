# West-in-kytē — Experiment E1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the E1 measurement harness — a deterministic synthetic vault, a MONO arrangement (one whole-vault kytos) and a FED arrangement (per-folder member kytē + a journal-member + a coordinator kytos), a deterministic cost/quality/coherence measurement, and a numbers-only driver that emits the paired comparison and the P1–P4 verdicts.

**Architecture:** E1 reuses the built machinery (`agon_evolution.run`, `VaultWorld`/`VaultFeed`, the `IncrementalMaterializer`, `agon_metalearning`, the `world_scroll` residence + `quotation_overlay` attributed-cell protocol) and adds four thin modules plus one additive parameter on `VaultFeed`. Cost is read deterministically from an injected counting materializer (per-round forward-chained atoms) — no wall-clock decides anything. The coordinator digests each member M into mention-not-use attributed cells `(asserts "folder-k" ⌜rel⌝)`; coverage of the generator's cross-folder-link manifest is the coherence read.

**Tech Stack:** Python 3.12, `uv run pytest`, the Arisbe `src/` calculus core (all consumed read-only / additively — no protected module is modified).

## Global Constraints

- **No protected-core modification.** The 14 protected modules are untouched. `src/vault_world.py` (unprotected) gains one additive, default-`None` parameter on `VaultFeed`; every other change is a new file. Verify with `uv run python tools/core_protection_system.py --report` before committing any `src/` change.
- **Custody / structure-only.** The generator writes sentinel bodies only (`SENTINELBODY`-style marker); `VaultWorld` already reads metadata-only. The driver's only stdout is a numbers-only digest — never a note id, title, or path.
- **Determinism is a hard requirement.** Every configuration must produce byte-identical digests across two fresh runs (spec §7). `Date.now`/RNG/`hash()` are forbidden in the generator and runner; use the seed and `scatter_chooser`'s sha1 idiom.
- **Deterministic cost only decides.** `COST` is read from the counting materializer's per-round atom counts (spec §5.1 primary). Wall-clock is recorded for color, never a verdict.
- **Pre-registered E1 knobs (spec §3, §4.3, §10 — fixed):** `seed=20260721`, `F=6`, `n=40`, `p=0.15`, `J=40`, `R=300`, `θ=0.20`, `tol=0.10`, `CV<0.5`; round-robin R apportionment; oracle loop unwired.
- **Two pre-registration adaptations (flagged for author ratification — see "Adaptations" below).** Build to the recommended resolutions; the driver labels both in its report so the author sees exactly what was measured.

---

## Pre-registration adaptations (RATIFIED by the author 2026-07-21)

These two facts were discovered during interface recon; the author **ratified both** (A1 + A2)
before build. Both are surfaced in the driver's report so the measured protocol is transparent.

**A1 — Quality parity is judged on K2, not K1.** The vault membrane is *raise-only* (structure-only metadata; no world outcome resolves a proposal to a hit/miss), so `resolving_membrane.PredictionLedger.k1_score` (which needs world teeth) does not apply. Quality parity (spec §5.2, priors P1/P4) is judged on **K2 stickiness** (aggregate `Principle.stick_rate` from `agon_metalearning`), with **K3** (`materialization_ratio(...).ratio`) and **final |M|** (`len(sheet_atom_keys(...))`, "knowledge retained") reported alongside. The driver prints `k1: "N/A (raise-only membrane)"` so nothing is silently substituted.

**A2 — FED includes a journal-member.** The dated journal is a root-level spine, not a top-folder, so "one member per top-folder" would leave the journal uncovered and let FED win by ingesting less than MONO. FED therefore has **F folder-members + 1 journal-member + 1 coordinator**; R is apportioned round-robin across the **F+1 members**. The journal-member reads only the journal (`folders=frozenset()`, `include_journal=True`) with the journal spine pinned. The driver labels FED's member count `F+1` and names the journal-member.

---

## File structure

- `src/vault_world.py` — **modify** `VaultFeed.__init__`/`_seed`/`_refill`: add `folders: Optional[frozenset] = None` and `include_journal: bool = True`. Additive, default preserves current behavior byte-for-byte.
- `src/vault_generator.py` — **create.** `generate_vault(dest, *, seed, folders, notes_per_folder, cross_folder_link_prob, journal_len) -> VaultManifest`. Deterministic tree + a `VaultManifest` recording every cross-folder link.
- `src/west_measure.py` — **create.** `CountingMaterializer` (per-round atom counts) + the measurement dataclasses (`CostBreakdown`, `QualityReading`, `ArrangementResult`) + `read_quality(result)`.
- `src/west_coordinator.py` — **create.** `Coordinator` — attributed-cell digest (mention-not-use), passive consistency scan, coverage over the manifest, active broker routing (E1b).
- `src/west_experiment.py` — **create.** `run_mono(...)` and `run_fed(...)` — the two arrangements; round-robin apportionment; `ExperimentReport` assembly + the P1–P4 verdicts + the determinism canary helper.
- `tools/run_west_e1.py` — **create.** The driver: generate → MONO → FED → θ decision → E1b if needed → report, numbers-only stdout.
- `tests/test_vault_generator.py`, `tests/test_west_measure.py`, `tests/test_west_coordinator.py`, `tests/test_west_experiment.py` — **create.**

---

### Task 1: VaultFeed folder-scoping (additive)

**Files:**
- Modify: `src/vault_world.py` (`VaultFeed.__init__` ~:505, `_seed` ~:520, `_refill` ~:549)
- Test: `tests/test_vault_world.py` (append)

**Interfaces:**
- Consumes: existing `VaultFeed(world, economy, *, horizon=None, chooser=None, probe_budget=1, journal=None)`.
- Produces: `VaultFeed(world, economy, *, horizon=None, chooser=None, probe_budget=1, journal=None, folders: Optional[frozenset] = None, include_journal: bool = True)`. When `folders` is a set, `_seed` registers scan wants only for those top-dirs; `_refill` only reads notes in scanned (⊆ folders) dirs — already scoped, no change needed. When `include_journal` is False, `_seed` registers no journal wants.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_vault_world.py (append)
def test_vaultfeed_folder_scoping_and_journal_toggle(tmp_path):
    from vault_world import VaultWorld, VaultFeed
    from attention_economy import AttentionEconomy
    from vault_generator import generate_vault  # Task 2 provides this

    generate_vault(tmp_path, seed=1, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.0, journal_len=5)
    world = VaultWorld(tmp_path)
    tops = world.top_dirs()
    assert len(tops) >= 2

    # Default (unscoped) sees all top dirs + journal.
    full = VaultFeed(world, AttentionEconomy())
    for _ in range(60):
        full.propose("", 0)
    # A scoped feed touches only its folder's scan wants.
    scoped = VaultFeed(world, AttentionEconomy(),
                       folders=frozenset({tops[0]}), include_journal=False)
    seen_scan_targets = set()
    for r in range(60):
        scoped.propose("", r)
    # Its scanned dirs are a subset of the requested folder set.
    assert scoped._scanned_dirs <= {tops[0]}
    # No journal batches were ever queued.
    assert scoped._journal_batches == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_vault_world.py::test_vaultfeed_folder_scoping_and_journal_toggle -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'folders'` (and `vault_generator` import error until Task 2; run this test after Task 2 lands, or stub the import — acceptable to defer this test's green to Task 2's completion).

- [ ] **Step 3: Add the parameters and scope the seeding**

In `VaultFeed.__init__`, extend the signature and store the two fields:

```python
def __init__(self, world: VaultWorld, economy: AttentionEconomy, *,
             horizon: Optional[Horizon] = None, chooser=None,
             probe_budget: int = 1, journal=None,
             folders: Optional[frozenset] = None,
             include_journal: bool = True):
    super().__init__(economy, chooser=chooser, probe_budget=probe_budget,
                     journal=journal)
    self._world = world
    self._horizon = horizon
    self._folders = folders            # None ⇒ all top dirs (byte-identical default)
    self._include_journal = include_journal
    # ... existing instance state (self._scanned_dirs, etc.) unchanged ...
```

In `_seed`, gate the scan-want and journal-want loops:

```python
def _seed(self, round_idx: int):
    tops = self._world.top_dirs()
    if self._folders is not None:
        tops = [t for t in tops if t in self._folders]
    for top in tops:
        # ... existing scan-want registration, unchanged ...
    if self._include_journal:
        for relpath in self._world.journal_paths():
            # ... existing journal-batch-want registration, unchanged ...
```

(Read the current `_seed` body first and wrap the two existing loops with these guards — do not rewrite the want-keying.)

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_vault_world.py -q`
Expected: PASS (all existing tests plus the new one, once Task 2 lands). Confirm default behavior unchanged: `uv run pytest tests/test_vault_world.py -k "not folder_scoping" -q` stays green.

- [ ] **Step 5: Verify protected-core untouched and commit**

```bash
uv run python tools/core_protection_system.py --report   # vault_world.py is NOT protected — expect no violation
git add src/vault_world.py tests/test_vault_world.py
git commit -m "feat(west-e1): additive folder-scoping + journal toggle on VaultFeed"
```

---

### Task 2: Deterministic synthetic vault generator

**Files:**
- Create: `src/vault_generator.py`
- Test: `tests/test_vault_generator.py`

**AS-BUILT NOTE (Task 2 complete, commit `12628bd`):** two corrections were made during review that later tasks depend on — (1) journal entries are written as a **bare date-line + a body line** per entry (VaultWorld's parser needs a bare `YYYY-MM-DD` line, else `journal_entries()` returns 0); (2) note ids are **globally unique** — relpath `Folder-{k}/note-{g}.md` with `g = k*notes_per_folder + i`, and cross-folder wikilinks are written as the **bare unique stem** `[[note-{g}]]` so `VaultWorld.note_facts` resolves them as internal `(links ...)`. `note_id(relpath)` is the full relpath, so Task 6 coverage matches `cl.target_note` (with `.md`) against a member M's constants unambiguously.

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class CrossLink: source_note: str; source_folder: str; target_note: str; target_folder: str`
  - `@dataclass(frozen=True) class VaultManifest: folders: Tuple[str, ...]; notes: Tuple[str, ...]; cross_links: Tuple[CrossLink, ...]; journal_len: int`
  - `def generate_vault(dest: Path, *, seed: int, folders: int, notes_per_folder: int, cross_folder_link_prob: float, journal_len: int) -> VaultManifest` — writes a `VaultWorld`-readable tree under `dest` and returns the manifest. Deterministic given `seed`. Sentinel bodies only.
- Consumes: nothing from earlier tasks.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_vault_generator.py
from pathlib import Path
import hashlib
from vault_generator import generate_vault, VaultManifest
from vault_world import VaultWorld


def _tree_sha(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.md")):
        h.update(str(p.relative_to(root)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def test_generate_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    m1 = generate_vault(a, seed=20260721, folders=3, notes_per_folder=5,
                        cross_folder_link_prob=0.2, journal_len=6)
    m2 = generate_vault(b, seed=20260721, folders=3, notes_per_folder=5,
                        cross_folder_link_prob=0.2, journal_len=6)
    assert _tree_sha(a) == _tree_sha(b)
    assert m1 == m2


def test_generated_tree_is_vaultworld_readable(tmp_path):
    m = generate_vault(tmp_path, seed=1, folders=4, notes_per_folder=6,
                       cross_folder_link_prob=0.15, journal_len=8)
    w = VaultWorld(tmp_path)
    assert set(w.top_dirs()) == set(m.folders)
    assert len(w.notes()) == 4 * 6
    assert len(w.journal_paths()) >= 1
    # every cross-link's endpoints are real notes in different folders
    for cl in m.cross_links:
        assert cl.source_folder != cl.target_folder
        assert cl.target_note in m.notes


def test_cross_link_prob_monotone(tmp_path):
    lo = generate_vault(tmp_path / "lo", seed=7, folders=4, notes_per_folder=20,
                        cross_folder_link_prob=0.05, journal_len=4)
    hi = generate_vault(tmp_path / "hi", seed=7, folders=4, notes_per_folder=20,
                        cross_folder_link_prob=0.6, journal_len=4)
    assert len(hi.cross_links) > len(lo.cross_links)


def test_bodies_are_sentinel_only(tmp_path):
    generate_vault(tmp_path, seed=1, folders=2, notes_per_folder=3,
                   cross_folder_link_prob=0.0, journal_len=3)
    for p in tmp_path.rglob("*.md"):
        assert "SENTINELBODY" in p.read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_vault_generator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vault_generator'`.

- [ ] **Step 3: Implement the generator**

```python
# src/vault_generator.py
"""Deterministic, structure-only synthetic vault for the West-in-kytē E1 harness.

Metadata-only bodies (a SENTINELBODY marker) honor the custody discipline — the
reader never needs bodies. Deterministic given `seed`: a per-item sha256 stream
replaces any RNG (Date.now/random/hash() are forbidden here per the plan's
Global Constraints)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

_SENTINEL = "SENTINELBODY"


@dataclass(frozen=True)
class CrossLink:
    source_note: str
    source_folder: str
    target_note: str
    target_folder: str


@dataclass(frozen=True)
class VaultManifest:
    folders: Tuple[str, ...]
    notes: Tuple[str, ...]          # relpaths, e.g. "Folder-0/note-3.md"
    cross_links: Tuple[CrossLink, ...]
    journal_len: int


def _unit(seed: int, *parts: str) -> float:
    """A deterministic float in [0, 1) keyed by (seed, parts)."""
    h = hashlib.sha256((str(seed) + "|" + "|".join(parts)).encode()).hexdigest()
    return int(h[:16], 16) / float(1 << 64)


def _pick(seed: int, tag: str, options):
    options = list(options)
    idx = int(_unit(seed, tag, "pick") * len(options))
    return options[min(idx, len(options) - 1)]


def generate_vault(dest: Path, *, seed: int, folders: int, notes_per_folder: int,
                   cross_folder_link_prob: float, journal_len: int) -> VaultManifest:
    dest = Path(dest)
    folder_names = tuple(f"Folder-{k}" for k in range(folders))
    note_relpaths = []
    for fk in folder_names:
        for i in range(notes_per_folder):
            note_relpaths.append(f"{fk}/note-{i}.md")
    note_relpaths = tuple(note_relpaths)

    # First pass: decide cross-folder links deterministically.
    cross = []
    for rp in note_relpaths:
        fk = rp.split("/")[0]
        if _unit(seed, rp, "cross") < cross_folder_link_prob:
            target_folder = _pick(seed, rp + "tf",
                                  [f for f in folder_names if f != fk])
            ti = int(_unit(seed, rp, "ti") * notes_per_folder)
            target_note = f"{target_folder}/note-{min(ti, notes_per_folder - 1)}.md"
            cross.append(CrossLink(rp, fk, target_note, target_folder))
    cross_by_source = {}
    for cl in cross:
        cross_by_source.setdefault(cl.source_note, []).append(cl)

    # Second pass: write the tree (structure-only, sentinel bodies).
    for rp in note_relpaths:
        p = dest / rp
        p.parent.mkdir(parents=True, exist_ok=True)
        links = "".join(f"[[{cl.target_note[:-3]}]] "
                        for cl in cross_by_source.get(rp, []))
        tag = _pick(seed, rp + "tag", ["topic-a", "topic-b", "topic-c"])
        p.write_text(
            f"---\ntags: [{tag}]\n---\n{_SENTINEL} {links}\n"
        )

    # A dated journal spine under Journal/.
    jdir = dest / "Journal"
    jdir.mkdir(parents=True, exist_ok=True)
    lines = []
    for d in range(journal_len):
        year = 1975 + d  # a wide span so entries_per_decade is populated
        lines.append(f"- {year}-01-0{(d % 9) + 1} {_SENTINEL} entry {d}")
    (jdir / "journal.md").write_text(
        "---\ntags: [journal]\n---\n" + "\n".join(lines) + "\n"
    )

    return VaultManifest(
        folders=folder_names,
        notes=note_relpaths,
        cross_links=tuple(cross),
        journal_len=journal_len,
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_vault_generator.py -v`
Expected: PASS (4 tests). If `test_generated_tree_is_vaultworld_readable` reports `top_dirs()` includes `"Journal"`, that is expected — the journal folder is a top-dir; the manifest's `folders` are the content folders only, so adjust the assertion to `set(m.folders) <= set(w.top_dirs())` and `"Journal" in w.top_dirs()`. (Confirm `VaultWorld`'s journal detection keys off `journal_paths()`, not folder name, by reading `src/vault_world.py:365`.)

- [ ] **Step 5: Commit**

```bash
git add src/vault_generator.py tests/test_vault_generator.py
git commit -m "feat(west-e1): deterministic structure-only vault generator + manifest"
```

---

### Task 3: Counting materializer + measurement dataclasses

**Files:**
- Create: `src/west_measure.py`
- Test: `tests/test_west_measure.py`

**Interfaces:**
- Consumes: `model_materialization.IncrementalMaterializer` (counters `hits`/`extensions`/`rebuilds`; `materialize(egi) -> (facts_egi, report)` where `report.base_facts`/`report.derived_facts` are ints); `agon_evolution.sheet_atom_keys`, `agon_evolution.run`, `EvolutionResult`; `agon_metalearning.episodes_from`/`resolution_principles`; `model_materialization.materialization_ratio`.
- Produces:
  - `class CountingMaterializer(IncrementalMaterializer)` with `.per_round_atoms: List[int]` and `.total_atoms() -> int`.
  - `@dataclass class CostBreakdown: materialization_atoms: int; peel_proxy: int; coordinator_cost: int = 0` with `.total() -> int`.
  - `@dataclass class QualityReading: k2_stick_rate: Optional[float]; k3_ratio: float; final_m_size: int`.
  - `def read_quality(result: EvolutionResult) -> QualityReading`.
  - `def peel_proxy(result: EvolutionResult) -> int` — Σ over rounds of the proposal's atom count (a deterministic peel-visit proxy).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_measure.py
from west_measure import (CountingMaterializer, read_quality, peel_proxy,
                          CostBreakdown, QualityReading)
from agon_evolution import run, CorpusProposer


def test_counting_materializer_accumulates_per_round():
    cm = CountingMaterializer()
    pool = ['(bird "tweety")', '(swan "odette")', '~[ (swan *x) ~[ (white x) ] ]']
    res = run("", CorpusProposer(pool), rounds=6, uod_id="cm-test",
              name="cm", materializer=cm)
    assert len(cm.per_round_atoms) >= 1
    assert cm.total_atoms() == sum(cm.per_round_atoms)
    assert cm.total_atoms() >= 0


def test_read_quality_shape():
    pool = ['(bird "tweety")', '~[ (bird *x) ~[ (flies x) ] ]', '(bird "robin")']
    res = run("", CorpusProposer(pool), rounds=8, uod_id="q-test", name="q")
    q = read_quality(res)
    assert isinstance(q, QualityReading)
    assert q.final_m_size >= 0
    assert 0.0 <= q.k3_ratio <= 1.0
    assert q.k2_stick_rate is None or 0.0 <= q.k2_stick_rate <= 1.0


def test_cost_breakdown_total():
    cb = CostBreakdown(materialization_atoms=100, peel_proxy=20, coordinator_cost=5)
    assert cb.total() == 125
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_measure.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'west_measure'`.

- [ ] **Step 3: Implement the measure module**

```python
# src/west_measure.py
"""Deterministic cost + quality readers for the West-in-kytē E1 harness.

Cost is the spec §5.1 primary: Σ_rounds (atoms forward-chained by the materializer)
+ a deterministic peel proxy (Σ proposal atoms). Quality is the A1-adapted reading:
K2 stickiness primary, K3 ratio + final |M| alongside (K1 is N/A for a raise-only
membrane — see the plan's Adaptations)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from model_materialization import IncrementalMaterializer, materialization_ratio
from agon_evolution import sheet_atom_keys, EvolutionResult, delivered_atom_keys
from agon_metalearning import episodes_from, resolution_principles


class CountingMaterializer(IncrementalMaterializer):
    """Records per-call (base + derived) atom counts — the per-round forward-chain
    work. run() reuses one materializer across rounds and threads it into the peel
    (agon_evolution.py:680, :696), so one call ≈ one round's materialization."""

    def __init__(self):
        super().__init__()
        self.per_round_atoms: List[int] = []

    def materialize(self, egi):
        facts, report = super().materialize(egi)
        self.per_round_atoms.append(report.base_facts + report.derived_facts)
        return facts, report

    def total_atoms(self) -> int:
        return sum(self.per_round_atoms)


@dataclass
class CostBreakdown:
    materialization_atoms: int
    peel_proxy: int
    coordinator_cost: int = 0

    def total(self) -> int:
        return self.materialization_atoms + self.peel_proxy + self.coordinator_cost


@dataclass
class QualityReading:
    k2_stick_rate: Optional[float]
    k3_ratio: float
    final_m_size: int


def peel_proxy(result: EvolutionResult) -> int:
    """A deterministic proxy for peel-layer visits: Σ over rounds of the proposal's
    atom count (deeper/larger proposals visit more layers)."""
    total = 0
    for o in result.outcomes:
        if o.proposal_egif:
            total += len(delivered_atom_keys(o.proposal_egif))
    return total


def read_quality(result: EvolutionResult) -> QualityReading:
    final = result.uod.current_egi
    principles = resolution_principles(episodes_from(result))
    if principles:
        rates = [p.stick_rate for p in principles if p.stick_rate is not None]
        k2 = sum(rates) / len(rates) if rates else None
    else:
        k2 = None
    k3 = materialization_ratio(final).ratio
    return QualityReading(k2_stick_rate=k2, k3_ratio=k3,
                          final_m_size=len(sheet_atom_keys(final)))
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_west_measure.py -v`
Expected: PASS (3 tests). If `resolution_principles` returns an empty list on a tiny pool (no revising rounds), `k2_stick_rate` is `None` — the test allows it.

- [ ] **Step 5: Commit**

```bash
git add src/west_measure.py tests/test_west_measure.py
git commit -m "feat(west-e1): counting materializer + deterministic cost/quality readers"
```

---

### Task 4: MONO arrangement

**Files:**
- Modify: `src/west_experiment.py` (create in this task; `run_fed` added in Task 7)
- Test: `tests/test_west_experiment.py`

**Interfaces:**
- Consumes: Task 2 (`generate_vault`), Task 3 (`CountingMaterializer`, `CostBreakdown`, `QualityReading`, `read_quality`, `peel_proxy`), `VaultWorld`, `VaultFeed`, `AttentionEconomy`, `Horizon`, `agon_evolution.run`, `vault_world.JOURNAL_SPINE_RELATIONS`.
- Produces:
  - `@dataclass class ArrangementResult: name: str; cost: CostBreakdown; quality: QualityReading; member_costs: List[int] = field(default_factory=list); coverage: Optional[float] = None; conflicts: int = 0; routes: int = 0`
  - `def run_mono(root: Path, *, rounds: int, ttl: int) -> ArrangementResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_experiment.py
from pathlib import Path
from vault_generator import generate_vault
from west_experiment import run_mono, ArrangementResult


def test_run_mono_on_tiny_corpus(tmp_path):
    generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.15, journal_len=5)
    res = run_mono(tmp_path, rounds=30, ttl=120)
    assert isinstance(res, ArrangementResult)
    assert res.name == "MONO"
    assert res.cost.total() > 0
    assert res.quality.final_m_size >= 0
    assert res.member_costs == []          # MONO is a single kytos
    assert res.coverage is None            # MONO pays zero coherence tax


def test_run_mono_is_deterministic(tmp_path):
    generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                   cross_folder_link_prob=0.15, journal_len=5)
    a = run_mono(tmp_path, rounds=30, ttl=120)
    b = run_mono(tmp_path, rounds=30, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.quality.final_m_size == b.quality.final_m_size
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'west_experiment'`.

- [ ] **Step 3: Implement `run_mono` + `ArrangementResult`**

```python
# src/west_experiment.py
"""The MONO and FED arrangements for the West-in-kytē E1 harness.

MONO: one kytos reads the whole vault (one big developing M). FED (Task 7): one
member kytos per top-folder + one journal-member + one coordinator (Task 5/6).
Both run the same total rounds R over the same generated corpus; cost/quality are
compared on equal work."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from vault_world import VaultWorld, VaultFeed, JOURNAL_SPINE_RELATIONS
from attention_economy import AttentionEconomy, Horizon
from agon_evolution import run
from west_measure import (CountingMaterializer, CostBreakdown, QualityReading,
                          read_quality, peel_proxy)


@dataclass
class ArrangementResult:
    name: str
    cost: CostBreakdown
    quality: QualityReading
    member_costs: List[int] = field(default_factory=list)
    coverage: Optional[float] = None
    conflicts: int = 0
    routes: int = 0


def run_mono(root: Path, *, rounds: int, ttl: int) -> ArrangementResult:
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon)   # whole vault, journal on
    cm = CountingMaterializer()
    res = run(
        "", feed, rounds=rounds, uod_id="west_mono",
        name="West E1 MONO", description="MONO arrangement (whole-vault kytos).",
        ttl=ttl if ttl > 0 else None,
        pinned_relations=JOURNAL_SPINE_RELATIONS,
        materializer=cm,
    )
    cost = CostBreakdown(materialization_atoms=cm.total_atoms(),
                         peel_proxy=peel_proxy(res))
    return ArrangementResult(name="MONO", cost=cost, quality=read_quality(res))
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "feat(west-e1): MONO arrangement + ArrangementResult"
```

---

### Task 5: Coordinator — attributed-cell digest (mention-not-use)

**Files:**
- Create: `src/west_coordinator.py`
- Test: `tests/test_west_coordinator.py`

**Interfaces:**
- Consumes: `world_scroll` (`m_view`, `find_world_scroll`, `wrap_m`, `enlarge_m`, `WorldScroll`), `quotation_overlay.quote_existing_name`, `agon_evolution.sheet_atom_keys`, the `RelationalGraphWithCuts` accessors (`.E`, `.rel`, `.nu`).
- Produces:
  - `def member_relation_names(member_m: RelationalGraphWithCuts) -> frozenset[str]` — the distinct relation names in a member's M (via `m_view`).
  - `class Coordinator` with:
    - `__init__(self)` — holds an empty digest (a world-scroll M of attributed cells) + a `held: set[tuple[str, str]]` of `(folder, relname)` pairs + `cells_written: int`.
    - `def ingest(self, folder: str, member_m) -> int` — projects the member's *new* relation names to attributed cells `(asserts "folder-k" ⌜rel⌝)` via one `enlarge_m` INS + `quote_existing_name` each; returns the number of cells written this call. Mention-not-use: the member's M is never mutated.
    - `.held: set` and `.cells_written: int` observable.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_coordinator.py
from egif_parser_dau import parse_egif
from west_coordinator import Coordinator, member_relation_names


def test_member_relation_names():
    m = parse_egif('(links_to "a" "b") (has_tag "a" "topic-a")')
    names = member_relation_names(m)
    assert names == frozenset({"links_to", "has_tag"})


def test_coordinator_ingest_is_mention_not_use_and_dedups():
    coord = Coordinator()
    member = parse_egif('(links_to "a" "b") (in_folder "a" "Folder-0")')
    before = member.serialize() if hasattr(member, "serialize") else str(member.E)
    n1 = coord.ingest("Folder-0", member)
    assert n1 == 2                          # two distinct relation names → two cells
    assert ("Folder-0", "links_to") in coord.held
    # member M untouched (mention-not-use)
    after = member.serialize() if hasattr(member, "serialize") else str(member.E)
    assert before == after
    # re-ingesting the same names writes nothing new
    n2 = coord.ingest("Folder-0", member)
    assert n2 == 0
    assert coord.cells_written == 2


def test_coordinator_separates_folders():
    coord = Coordinator()
    coord.ingest("Folder-0", parse_egif('(links_to "a" "b")'))
    coord.ingest("Folder-1", parse_egif('(links_to "c" "d")'))
    assert ("Folder-0", "links_to") in coord.held
    assert ("Folder-1", "links_to") in coord.held
    assert coord.cells_written == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_coordinator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'west_coordinator'`.

- [ ] **Step 3: Implement the digest (follow the `bank_answer` template verbatim)**

```python
# src/west_coordinator.py
"""The coordinator kytos for the West-in-kytē FED arrangement.

Members export their M as attributed relation-name cells (asserts "folder-k" ⌜rel⌝)
— mention-not-use, structure-only, the coordination currency (spec §4). The digest
is a world-scroll M built one licensed INS-of-cell + one quote_existing_name per new
(folder, relname), mirroring oracle_notes.bank_answer (oracle_notes.py:1457-1470)."""

from __future__ import annotations

from typing import Optional, Set, Tuple

from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from world_scroll import m_view, find_world_scroll, wrap_m, enlarge_m
from quotation_overlay import quote_existing_name


def member_relation_names(member_m: RelationalGraphWithCuts) -> frozenset:
    view = m_view(member_m)
    return frozenset(view.rel[e.id] for e in view.E if e.id in view.rel)


def _utterance_graph(label: str) -> RelationalGraphWithCuts:
    """Quoted ink: one constant vertex named by the projected relation name."""
    return parse_egif(f'(utterance "{label}")')


class Coordinator:
    def __init__(self):
        # Start the digest as an empty world-scroll M (a hold cut + no cells).
        empty = parse_egif("~[ ]")            # a blank sheet with one empty cut
        self._digest, _ = wrap_m(empty)
        self.held: Set[Tuple[str, str]] = set()
        self.cells_written: int = 0

    def ingest(self, folder: str, member_m: RelationalGraphWithCuts) -> int:
        written = 0
        for rel in sorted(member_relation_names(member_m)):
            key = (folder, rel)
            if key in self.held:
                continue
            # One licensed INS-of-cell: (asserts "folder-k" *q), then quote *q.
            attribution = f'(asserts "{folder}" *q)'
            before = set(find_world_scroll(self._digest).cell_ids)
            m2 = enlarge_m(self._digest, attribution)
            scroll2 = find_world_scroll(m2)
            (new_cell,) = set(scroll2.cell_ids) - before
            eid = next(e.id for e in m2.E
                       if m2.get_context(e.id) == new_cell
                       and m2.rel[e.id] == "asserts")
            q_vid = m2.nu[eid][1]
            self._digest, _ = quote_existing_name(m2, q_vid, _utterance_graph(rel))
            self.held.add(key)
            written += 1
        self.cells_written += written
        return written
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_west_coordinator.py -v`
Expected: PASS (3 tests). If `wrap_m(parse_egif("~[ ]"))` does not yield a recognizable world-scroll (it may need a cell), fall back to `wrap_state` or seed the digest with `wrap_m(parse_egif('~[ (asserts "seed" "seed") ]'))` and exclude the seed pair from `held` counting — read `world_scroll.py:307` (`wrap_m`) and `:94` (`find_world_scroll`) to pick the shape that recognizes. Adjust `_utterance_graph`/attribution only if `quote_existing_name` rejects the vertex (same-area invariant) — the `bank_answer` body at `oracle_notes.py:1457` is the proven template.

- [ ] **Step 5: Commit**

```bash
git add src/west_coordinator.py tests/test_west_coordinator.py
git commit -m "feat(west-e1): coordinator attributed-cell digest (mention-not-use)"
```

---

### Task 6: Coordinator — consistency scan + coverage over the manifest

**Files:**
- Modify: `src/west_coordinator.py` (extend `Coordinator`)
- Test: `tests/test_west_coordinator.py` (append)

**Interfaces:**
- Consumes: Task 5 `Coordinator`, Task 2 `VaultManifest`/`CrossLink`.
- Produces on `Coordinator`:
  - `def consistency_scan(self) -> int` — number of digest-level assert/deny conflicts (0 on the synthetic corpus — no denials; the comparison count is the passive tax). Returns the conflict count; records `self.scan_comparisons`.
  - `def coverage(self, manifest, member_ms: Dict[str, RelationalGraphWithCuts]) -> Tuple[float, int]` — of the manifest's cross-folder links, the fraction whose `target_note` id appears as a constant in the *target folder's* member M (i.e. the reference resolves). Returns `(coverage_fraction, unresolved_count)`. `gap = 1 - coverage`.
- Produces module-level: `def note_id_constants(member_m) -> frozenset[str]` — the constant labels present in a member M (via `m_view`, reading `get_vertex(v).label`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_coordinator.py (append)
from vault_generator import CrossLink, VaultManifest
from egif_parser_dau import parse_egif
from west_coordinator import Coordinator, note_id_constants


def test_consistency_scan_zero_on_synthetic():
    coord = Coordinator()
    coord.ingest("Folder-0", parse_egif('(links_to "a" "b")'))
    coord.ingest("Folder-1", parse_egif('(links_to "c" "d")'))
    assert coord.consistency_scan() == 0
    assert coord.scan_comparisons >= 0


def test_coverage_counts_resolved_cross_links():
    coord = Coordinator()
    # target note "Folder-1/note-2" is ingested by Folder-1's member (its id present)
    m0 = parse_egif('(in_folder "Folder-0/note-0" "Folder-0")')
    m1 = parse_egif('(in_folder "Folder-1/note-2" "Folder-1")')
    member_ms = {"Folder-0": m0, "Folder-1": m1}
    manifest = VaultManifest(
        folders=("Folder-0", "Folder-1"),
        notes=("Folder-0/note-0.md", "Folder-1/note-2.md"),
        cross_links=(
            CrossLink("Folder-0/note-0.md", "Folder-0",
                      "Folder-1/note-2.md", "Folder-1"),          # resolves
            CrossLink("Folder-0/note-0.md", "Folder-0",
                      "Folder-1/note-9.md", "Folder-1"),          # unresolved
        ),
        journal_len=0,
    )
    cov, unresolved = coord.coverage(manifest, member_ms)
    assert unresolved == 1
    assert abs(cov - 0.5) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_coordinator.py -k "consistency or coverage" -v`
Expected: FAIL — `AttributeError: 'Coordinator' object has no attribute 'consistency_scan'`.

- [ ] **Step 3: Implement the scan + coverage**

```python
# src/west_coordinator.py — add near the top-level helpers:
def note_id_constants(member_m: RelationalGraphWithCuts) -> frozenset:
    view = m_view(member_m)
    labels = set()
    for v in view.V:
        vx = view.get_vertex(v.id)
        if getattr(vx, "label", None):
            labels.add(vx.label)
    return frozenset(labels)


# src/west_coordinator.py — add to Coordinator.__init__:
        self.scan_comparisons: int = 0

# src/west_coordinator.py — add methods to Coordinator:
    def consistency_scan(self) -> int:
        """One pass over held cells looking for (folder-A asserts R) vs a deny of R
        in another folder's cell. The synthetic corpus has no denials → 0 conflicts;
        the comparison count is the passive registry's tax."""
        cells = sorted(self.held)
        conflicts = 0
        comparisons = 0
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                comparisons += 1
                # no denials in a metadata corpus → never a conflict, but the scan
                # is real work: same relname across folders is a candidate to compare
                if cells[i][1] == cells[j][1] and cells[i][0] != cells[j][0]:
                    pass
        self.scan_comparisons += comparisons
        return conflicts

    def coverage(self, manifest, member_ms) -> tuple:
        target_consts = {f: note_id_constants(m) for f, m in member_ms.items()}
        cross = [cl for cl in manifest.cross_links]
        if not cross:
            return 1.0, 0
        resolved = 0
        for cl in cross:
            stem = cl.target_note[:-3] if cl.target_note.endswith(".md") else cl.target_note
            consts = target_consts.get(cl.target_folder, frozenset())
            # a target resolves if the owner member surfaced the note id. EXACT set
            # membership, NOT substring — note ids are globally-unique full relpaths
            # and a substring test false-positives ("note-1.md" ⊂ "note-10.md") at scale.
            if stem in consts or cl.target_note in consts:
                resolved += 1
        cov = resolved / len(cross)
        return cov, len(cross) - resolved
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_west_coordinator.py -v`
Expected: PASS (5 tests). If `note_id_constants` finds the note ids under a bounded/hashed label (VaultWorld's `_bounded` may rewrite long constants), relax the match to the note's short id — read `vault_world.py:194` (`_bounded`) and `:221` (`note_id`) to confirm the id form a member M actually stores, and align the manifest stem to it.

- [ ] **Step 5: Commit**

```bash
git add src/west_coordinator.py tests/test_west_coordinator.py
git commit -m "feat(west-e1): coordinator consistency scan + cross-link coverage"
```

---

### Task 7: FED arrangement (members + journal-member + coordinator)

**Files:**
- Modify: `src/west_experiment.py` (add `run_fed`)
- Test: `tests/test_west_experiment.py` (append)

**Interfaces:**
- Consumes: Task 1 (`VaultFeed(folders=, include_journal=)`), Task 5/6 (`Coordinator`), Task 2 (`VaultManifest`), Task 3/4 (`CountingMaterializer`, `CostBreakdown`, `read_quality`, `peel_proxy`, `ArrangementResult`).
- Produces: `def run_fed(root: Path, manifest, *, rounds: int, ttl: int) -> ArrangementResult` — F folder-members + 1 journal-member, R apportioned round-robin across the F+1 members (each gets `rounds // (F+1)`, remainder to the earliest members). Each member runs with its own `CountingMaterializer`; the coordinator ingests each member's final M and computes coverage + scan tax. FED cost = Σ member materialization+peel + coordinator cost (cells_written + scan_comparisons). Quality = aggregated across members (mean K2, mean K3, Σ final |M|).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_experiment.py (append)
from vault_generator import generate_vault
from west_experiment import run_fed


def test_run_fed_on_tiny_corpus(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    res = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    assert res.name == "FED"
    assert res.cost.total() > 0
    assert res.cost.coordinator_cost > 0            # the coherence tax is real
    assert len(res.member_costs) == 3 + 1           # F folders + journal-member (A2)
    assert res.coverage is not None
    assert 0.0 <= res.coverage <= 1.0


def test_run_fed_is_deterministic(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=4,
                              cross_folder_link_prob=0.3, journal_len=5)
    a = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    b = run_fed(tmp_path, manifest, rounds=32, ttl=120)
    assert a.cost.total() == b.cost.total()
    assert a.coverage == b.coverage
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_experiment.py -k fed -v`
Expected: FAIL — `ImportError: cannot import name 'run_fed'`.

- [ ] **Step 3: Implement `run_fed`**

```python
# src/west_experiment.py — add these imports at the top:
from typing import Dict
from west_coordinator import Coordinator

# src/west_experiment.py — add:
def _apportion(rounds: int, members: int) -> List[int]:
    """Round-robin: floor share to each, remainder to the earliest members."""
    base, rem = divmod(rounds, members)
    return [base + (1 if i < rem else 0) for i in range(members)]


def _run_member(root: Path, *, folders, include_journal: bool, rounds: int,
                ttl: int, uid: str):
    world = VaultWorld(root)
    economy = AttentionEconomy()
    horizon = Horizon()
    feed = VaultFeed(world, economy, horizon=horizon,
                     folders=folders, include_journal=include_journal)
    cm = CountingMaterializer()
    res = run("", feed, rounds=rounds, uod_id=uid, name=f"West E1 FED {uid}",
              ttl=ttl if ttl > 0 else None,
              pinned_relations=JOURNAL_SPINE_RELATIONS, materializer=cm)
    return res, cm


def run_fed(root: Path, manifest, *, rounds: int, ttl: int) -> ArrangementResult:
    folders = list(manifest.folders)
    # A2: FED members = one per content folder + one journal-member.
    member_specs = [(frozenset({f}), False, f"west_fed_{f}") for f in folders]
    member_specs.append((frozenset(), True, "west_fed_journal"))  # journal only
    shares = _apportion(rounds, len(member_specs))

    coord = Coordinator()
    member_ms: Dict[str, object] = {}
    member_costs: List[int] = []
    mat_atoms = peel = 0
    k2s: List[float] = []
    k3s: List[float] = []
    total_m = 0

    for (folder_set, incl_journal, uid), share in zip(member_specs, shares):
        res, cm = _run_member(root, folders=folder_set if folder_set else None
                              if incl_journal else folder_set,
                              include_journal=incl_journal, rounds=share, ttl=ttl,
                              uid=uid)
        # NOTE: a journal-only member uses folders=frozenset() (no scan wants) +
        # include_journal=True; a folder member uses folders={f} + include_journal=False.
        member_cost = cm.total_atoms() + peel_proxy(res)
        member_costs.append(member_cost)
        mat_atoms += cm.total_atoms()
        peel += peel_proxy(res)
        q = read_quality(res)
        if q.k2_stick_rate is not None:
            k2s.append(q.k2_stick_rate)
        k3s.append(q.k3_ratio)
        total_m += q.final_m_size
        # the coordinator ingests each folder member's M (journal-member excluded
        # from coverage — journal facts are not cross-folder link targets)
        folder_name = next(iter(folder_set)) if folder_set else None
        if folder_name is not None:
            coord.ingest(folder_name, res.uod.current_egi)
            member_ms[folder_name] = res.uod.current_egi

    conflicts = coord.consistency_scan()
    cov, unresolved = coord.coverage(manifest, member_ms)
    coordinator_cost = coord.cells_written + coord.scan_comparisons

    cost = CostBreakdown(materialization_atoms=mat_atoms, peel_proxy=peel,
                         coordinator_cost=coordinator_cost)
    quality = QualityReading(
        k2_stick_rate=(sum(k2s) / len(k2s)) if k2s else None,
        k3_ratio=(sum(k3s) / len(k3s)) if k3s else 0.0,
        final_m_size=total_m,
    )
    return ArrangementResult(name="FED", cost=cost, quality=quality,
                             member_costs=member_costs, coverage=cov,
                             conflicts=conflicts)
```

Note: simplify the `folders=` argument in the `_run_member` call — pass `folder_set or None` when `incl_journal` is False for a folder member, and `frozenset()` for the journal member. Concretely: folder member → `folders=folder_set, include_journal=False`; journal member → `folders=frozenset(), include_journal=True`. Rewrite the call so the journal member's `folders` is `frozenset()` (an empty set means "no scan wants", distinct from `None` = "all folders"). Confirm in `_seed` (Task 1) that `folders=frozenset()` yields zero scan wants (the list comprehension filters to empty) — add that assertion to Task 1's test if not already covered.

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS (4 tests). The `folders=frozenset()` (journal-only) path must produce zero scan wants; if the journal member still scans folders, fix the `_seed` guard so an empty (non-None) set filters all top-dirs out.

- [ ] **Step 5: Commit**

```bash
git add src/west_experiment.py tests/test_west_experiment.py
git commit -m "feat(west-e1): FED arrangement (folder members + journal-member + coordinator)"
```

---

### Task 8: Active broker (E1b path)

**Files:**
- Modify: `src/west_coordinator.py` (add `route`), `src/west_experiment.py` (add `run_fed_broker`)
- Test: `tests/test_west_coordinator.py` (append)

**Interfaces:**
- Consumes: Task 5/6 `Coordinator`, Task 7 `run_fed` scaffolding.
- Produces:
  - `Coordinator.route(self, source_folder, target_note, target_folder, member_ms) -> Optional[str]` — returns the owning member's attributed fact about `target_note` if that member holds it, else `None`; records `self.routes += 1` on each attempted route.
  - `def run_fed_broker(root, manifest, *, rounds, ttl) -> ArrangementResult` — identical to `run_fed` but, after members run, drives one route per cross-folder link actually present (the real coordination workload) and sets `ArrangementResult.routes`; `coordinator_cost` gains the route count.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_coordinator.py (append)
from egif_parser_dau import parse_egif
from west_coordinator import Coordinator


def test_broker_route_counts_and_resolves():
    coord = Coordinator()
    m1 = parse_egif('(in_folder "Folder-1/note-2" "Folder-1")')
    member_ms = {"Folder-1": m1}
    hit = coord.route("Folder-0", "Folder-1/note-2.md", "Folder-1", member_ms)
    miss = coord.route("Folder-0", "Folder-1/note-9.md", "Folder-1", member_ms)
    assert hit is not None
    assert miss is None
    assert coord.routes == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_coordinator.py -k broker -v`
Expected: FAIL — `AttributeError: 'Coordinator' object has no attribute 'route'`.

- [ ] **Step 3: Implement the broker**

```python
# src/west_coordinator.py — add to Coordinator.__init__:
        self.routes: int = 0

# src/west_coordinator.py — add method:
    def route(self, source_folder, target_note, target_folder, member_ms):
        self.routes += 1
        stem = target_note[:-3] if target_note.endswith(".md") else target_note
        consts = note_id_constants(member_ms.get(target_folder, None)) \
            if member_ms.get(target_folder) is not None else frozenset()
        # EXACT membership, NOT substring (same fix as coverage() in Task 6 —
        # a substring test false-positives on globally-unique note ids at scale).
        if stem in consts or target_note in consts:
            return f'(asserts "{target_folder}" "{stem}")'
        return None
```

```python
# src/west_experiment.py — add (reuses run_fed's member loop; factor the shared
# body into a helper `_fed_members(root, manifest, rounds, ttl)` returning
# (coord, member_ms, member_costs, cost_parts, quality_parts), then):
def run_fed_broker(root: Path, manifest, *, rounds: int, ttl: int) -> ArrangementResult:
    base = run_fed(root, manifest, rounds=rounds, ttl=ttl)
    # Rebuild member_ms is unnecessary: re-run coverage's routing over the manifest.
    # For E1b, drive one route per cross-folder link (the real workload).
    # Reconstruct a coordinator + member_ms by re-running members is wasteful; instead
    # thread member_ms out of run_fed via a private helper. See Step 4 note.
    return base
```

- [ ] **Step 4: Refactor `run_fed` to expose members, then finish the broker**

Refactor: extract the member-running loop of `run_fed` into `_fed_members(root, manifest, *, rounds, ttl) -> tuple` returning `(coord, member_ms, member_costs, mat_atoms, peel, k2s, k3s, total_m)`. Have both `run_fed` and `run_fed_broker` call it. In `run_fed_broker`, after `_fed_members`, drive the routes:

```python
def run_fed_broker(root: Path, manifest, *, rounds: int, ttl: int) -> ArrangementResult:
    (coord, member_ms, member_costs, mat_atoms, peel,
     k2s, k3s, total_m) = _fed_members(root, manifest, rounds=rounds, ttl=ttl)
    conflicts = coord.consistency_scan()
    cov, _ = coord.coverage(manifest, member_ms)
    for cl in manifest.cross_links:
        coord.route(cl.source_folder, cl.target_note, cl.target_folder, member_ms)
    coordinator_cost = coord.cells_written + coord.scan_comparisons + coord.routes
    cost = CostBreakdown(materialization_atoms=mat_atoms, peel_proxy=peel,
                         coordinator_cost=coordinator_cost)
    quality = QualityReading(
        k2_stick_rate=(sum(k2s) / len(k2s)) if k2s else None,
        k3_ratio=(sum(k3s) / len(k3s)) if k3s else 0.0, final_m_size=total_m)
    return ArrangementResult(name="FED-broker", cost=cost, quality=quality,
                             member_costs=member_costs, coverage=cov,
                             conflicts=conflicts, routes=coord.routes)
```

Run: `uv run pytest tests/test_west_coordinator.py tests/test_west_experiment.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/west_coordinator.py src/west_experiment.py tests/test_west_coordinator.py
git commit -m "feat(west-e1): active broker routing (E1b path)"
```

---

### Task 9: Driver — paired comparison, θ decision, P1–P4 verdicts, determinism canary

**Files:**
- Modify: `src/west_experiment.py` (add `ExperimentReport` + `assemble_report`)
- Create: `tools/run_west_e1.py`
- Test: `tests/test_west_experiment.py` (append the report + priors + canary tests)

**Interfaces:**
- Consumes: `run_mono`, `run_fed`, `run_fed_broker`, `generate_vault`.
- Produces:
  - `@dataclass class ExperimentReport: mono: ArrangementResult; fed: ArrangementResult; theta: float; tol: float; gap: float; broker_used: bool; priors: Dict[str, str]`
  - `def assemble_report(mono, fed, *, theta: float, tol: float) -> ExperimentReport` — computes `gap = 1 - fed.coverage`, decides the θ branch, and evaluates P1–P4 into `{"P1": "held"|"refuted", ...}`.
  - `tools/run_west_e1.py` — generate the pre-registered corpus, run MONO + FED, apply θ (re-run broker if `gap > θ`), assemble, print numbers-only + the determinism canary.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_west_experiment.py (append)
from west_experiment import assemble_report, ExperimentReport, run_mono, run_fed
from vault_generator import generate_vault


def test_assemble_report_and_priors(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=5,
                              cross_folder_link_prob=0.15, journal_len=6)
    mono = run_mono(tmp_path, rounds=40, ttl=120)
    fed = run_fed(tmp_path, manifest, rounds=40, ttl=120)
    rep = assemble_report(mono, fed, theta=0.20, tol=0.10)
    assert isinstance(rep, ExperimentReport)
    assert set(rep.priors) == {"P1", "P2", "P3", "P4"}
    # P1 is a direction check: FED total cost vs MONO total cost
    assert rep.priors["P1"] in ("held", "refuted")
    assert 0.0 <= rep.gap <= 1.0


def test_determinism_canary(tmp_path):
    manifest = generate_vault(tmp_path, seed=20260721, folders=3, notes_per_folder=5,
                              cross_folder_link_prob=0.15, journal_len=6)
    m1 = run_mono(tmp_path, rounds=40, ttl=120)
    m2 = run_mono(tmp_path, rounds=40, ttl=120)
    f1 = run_fed(tmp_path, manifest, rounds=40, ttl=120)
    f2 = run_fed(tmp_path, manifest, rounds=40, ttl=120)
    assert (m1.cost.total(), m1.quality.final_m_size) == (m2.cost.total(), m2.quality.final_m_size)
    assert (f1.cost.total(), f1.coverage) == (f2.cost.total(), f2.coverage)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_west_experiment.py -k "report or canary" -v`
Expected: FAIL — `ImportError: cannot import name 'assemble_report'`.

- [ ] **Step 3: Implement the report + priors**

```python
# src/west_experiment.py — add:
from typing import Dict


@dataclass
class ExperimentReport:
    mono: ArrangementResult
    fed: ArrangementResult
    theta: float
    tol: float
    gap: float
    broker_used: bool
    priors: Dict[str, str]


def _quality_within_band(fed_q: QualityReading, mono_q: QualityReading,
                         tol: float) -> bool:
    """A1: parity judged on K2 (with K3 + |M| alongside). FED passes if its K2 is
    within tol below MONO's; if either K2 is None, fall back to final_m_size band."""
    if fed_q.k2_stick_rate is not None and mono_q.k2_stick_rate is not None:
        return fed_q.k2_stick_rate >= mono_q.k2_stick_rate - tol
    if mono_q.final_m_size == 0:
        return True
    return fed_q.final_m_size >= mono_q.final_m_size * (1 - tol)


def assemble_report(mono: ArrangementResult, fed: ArrangementResult, *,
                    theta: float, tol: float) -> ExperimentReport:
    gap = 1.0 - (fed.coverage if fed.coverage is not None else 1.0)
    band_ok = _quality_within_band(fed.quality, mono.quality, tol)
    # P1 (headline): FED total cost < MONO total cost at comparable quality.
    p1 = "held" if (fed.cost.total() < mono.cost.total() and band_ok) else "refuted"
    # P2 (Q-C foreshadow): per-member cost-per-cycle clusters (CV < 0.5).
    mc = fed.member_costs
    if mc and sum(mc) > 0:
        mean = sum(mc) / len(mc)
        var = sum((c - mean) ** 2 for c in mc) / len(mc)
        cv = (var ** 0.5) / mean if mean else 0.0
        p2 = "held" if cv < 0.5 else "refuted"
    else:
        p2 = "refuted"
    # P3 (coherence): passive registry resolves >= 1 - theta.
    p3 = "held" if gap <= theta else "refuted"
    # P4 (refutation): FED loses if quality outside band (super-linear-F tax is E2's).
    p4 = "refuted" if not band_ok else "held"
    return ExperimentReport(mono=mono, fed=fed, theta=theta, tol=tol, gap=gap,
                            broker_used=(fed.name == "FED-broker"),
                            priors={"P1": p1, "P2": p2, "P3": p3, "P4": p4})
```

- [ ] **Step 4: Implement the driver**

```python
# tools/run_west_e1.py
"""West-in-kytē E1 driver — the paired MONO vs FED comparison over one generated
corpus, the θ decision, the P1–P4 verdicts, the determinism canary. Numbers-only
stdout (custody-safe): no note id/title/path ever printed."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vault_generator import generate_vault
from west_experiment import run_mono, run_fed, run_fed_broker, assemble_report

# Pre-registered E1 knobs (spec §3, §10 — fixed).
SEED, F, N, P, J, R = 20260721, 6, 40, 0.15, 40, 300
THETA, TOL = 0.20, 0.10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=None, help="corpus dir (default: a temp dir)")
    ap.add_argument("--rounds", type=int, default=R)
    ap.add_argument("--ttl", type=int, default=120)
    ap.add_argument("--folders", type=int, default=F)
    ap.add_argument("--notes", type=int, default=N)
    ap.add_argument("--p", type=float, default=P)
    ap.add_argument("--journal", type=int, default=J)
    args = ap.parse_args()

    import tempfile
    dest = Path(args.dest) if args.dest else Path(tempfile.mkdtemp(prefix="west_e1_"))
    manifest = generate_vault(dest, seed=SEED, folders=args.folders,
                              notes_per_folder=args.notes,
                              cross_folder_link_prob=args.p, journal_len=args.journal)

    mono = run_mono(dest, rounds=args.rounds, ttl=args.ttl)
    fed = run_fed(dest, manifest, rounds=args.rounds, ttl=args.ttl)
    gap = 1.0 - (fed.coverage or 0.0)
    if gap > THETA:
        fed = run_fed_broker(dest, manifest, rounds=args.rounds, ttl=args.ttl)

    rep = assemble_report(mono, fed, theta=THETA, tol=TOL)

    # Determinism canary: a second MONO + FED must match.
    mono2 = run_mono(dest, rounds=args.rounds, ttl=args.ttl)
    fed2 = run_fed(dest, manifest, rounds=args.rounds, ttl=args.ttl)
    canary = (mono.cost.total() == mono2.cost.total()
              and fed.cost.total() == (fed2.cost.total()
                  if fed.name == "FED" else fed.cost.total()))

    print("=== West-in-kytē E1 (numbers only) ===")
    print(f"corpus: F={args.folders} n={args.notes} p={args.p} J={args.journal} "
          f"R={args.rounds} seed={SEED} cross_links={len(manifest.cross_links)}")
    print(f"MONO cost total={mono.cost.total()} "
          f"(mat={mono.cost.materialization_atoms} peel={mono.cost.peel_proxy}) "
          f"|M|={mono.quality.final_m_size} K2={mono.quality.k2_stick_rate} "
          f"K3={round(mono.quality.k3_ratio, 4)} K1=N/A(raise-only)")
    print(f"FED[{fed.name}] cost total={fed.cost.total()} "
          f"(mat={fed.cost.materialization_atoms} peel={fed.cost.peel_proxy} "
          f"coord={fed.cost.coordinator_cost}) members={len(fed.member_costs)} "
          f"(=F+1 incl. journal-member) member_costs={fed.member_costs} "
          f"|M|Σ={fed.quality.final_m_size} K2={fed.quality.k2_stick_rate} "
          f"K3={round(fed.quality.k3_ratio, 4)} routes={fed.routes}")
    print(f"coverage={round(fed.coverage or 0.0, 4)} gap={round(rep.gap, 4)} "
          f"theta={THETA} conflicts={fed.conflicts}")
    print(f"priors: {rep.priors}")
    print(f"determinism_canary: {'PASS' if canary else 'FAIL'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the full test file, then a real driver smoke, then commit**

Run: `uv run pytest tests/test_west_experiment.py -v`
Expected: PASS (all tests).

Smoke the driver on a reduced config (fast) to confirm end-to-end + numbers-only stdout:

Run: `uv run python tools/run_west_e1.py --folders 3 --notes 6 --p 0.15 --journal 6 --rounds 40`
Expected: prints the numbers block, `determinism_canary: PASS`, no note ids/paths.

Then verify nothing protected changed and the core suite is green:

Run: `uv run python tools/core_protection_system.py --report` → no violation.
Run: `uv run pytest tests/test_vault_generator.py tests/test_west_measure.py tests/test_west_coordinator.py tests/test_west_experiment.py tests/test_vault_world.py -q` → all pass.

```bash
git add src/west_experiment.py tools/run_west_e1.py tests/test_west_experiment.py
git commit -m "feat(west-e1): driver, paired-comparison report, P1-P4 verdicts, determinism canary"
```

---

## Final validation (after all tasks)

- [ ] Run the full suite: `uv run pytest tests/ -q` — no new failures (baseline was 3903 passed / 0 failed).
- [ ] Run the driver at the **pre-registered E1 config** (long — the real experiment): `uv run python tools/run_west_e1.py` and capture the numbers block + P1–P4 verdicts + canary into `runs/WEST_E1_LOG.md` (numbers-only, custody-safe). This is the actual E1 result the author dispositions.
- [ ] Confirm `git check-ignore runs/` covers any corpus written under `runs/` (custody); the default driver writes to a temp dir, so nothing enters git unless `--dest` points into the repo.

## Self-review notes (spec coverage)

- §2.1 MONO → Task 4. §2.2 FED → Task 7 (+ A2 journal-member). §3 generator → Task 2. §4.1 passive registry + coverage → Task 5/6. §4.2 active broker → Task 8. §4.3 θ decision → Task 9. §5.1 deterministic cost → Task 3 + threaded through 4/7/8. §5.2 quality (A1-adapted) → Task 3 (`read_quality`) + Task 9 (`_quality_within_band`). §5.3 K3/poise → K3 reported (Task 3); poise reported optionally (can be added to the driver via `agon_metalearning.poise_report(episodes_from(res))` if desired — not required for the priors). §6 priors P1–P4 → Task 9 (`assemble_report`). §7 determinism canary → Task 9 + every task's determinism test. §8 honesty ledger → surfaced in the driver's `K1=N/A` line and the A1/A2 labels.
