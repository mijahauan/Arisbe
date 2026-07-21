# Run 13 log — the vault cycle, World #2: the author according to Arisbe — PRE-REGISTERED 2026-07-18

**Pre-registration.** Priors below are copied **verbatim** from the design spec
(`docs/superpowers/specs/2026-07-17-vault-cycle-design.md`, "RUN 13 — pre-registered
priors"), before any run against the real vault. Stage V0 (the metadata membrane —
`src/vault_world.py`, `src/probe_feed.py`, the `Horizon` register in
`src/attention_economy.py`) is fixture-verified; the driver is `tools/run_vault_v0.py`.
Launching RUN 13 against the real vault (`/Users/mjh/Documents/Vorago`) is the author's
own act, not something CI or an agent does.

## Pre-registered priors (verbatim from the spec)

- **P1¹³ (retrodiction):** trained on notes through month *m*, the model's forecasts
  about month *m+1*'s activity (which clusters grow, which notes get revisited) beat
  a frequency baseline on a held-out slice — and, at the journal's scale, trained
  through year *y*, forecasts about year *y+1*'s entry rhythm and recurring themes
  beat the same baseline across at least two decades of held-out spans.
- **P2¹³ (legible questions):** the docket generates questions about the author that
  the author rates non-trivial at better than a stated base rate (author-judged
  sample per segment).

  > **P2¹³ operational form (amended 2026-07-19, pre-first-note).** Per segment the note
  > carries N docket-selected and N template-random questions in seeded random order,
  > unlabeled; the author marks each `**R:** trivial|non-trivial`; pass iff the
  > docket-selected non-trivial rate exceeds the template-random rate by ≥25 points over
  > ≥2 segments. Ceiling canary: if the author rates ≥90% of all questions non-trivial in
  > a segment, that segment is declared uninformative for P2¹³. All parts
  > deterministic/offline except the author's marks.
  >
  > **Operator note (2026-07-19, review fix).** `tools/run_vault_v0.py`'s P2¹³ instrument
  > is **ON BY DEFAULT** — the pre-registered launch command below carries no flag, so
  > defaulting off would have left the criterion silently unanswered again. A P2¹³-mode
  > note carries the 2+2 comparator questions **in place of**, not alongside, the standard
  > provenance/journal/horizon question mix for that note; `--no-p213` restores the V2a.1
  > mix instead. Scheduling tension, named honestly rather than resolved here: a single
  > note cannot exercise both P2¹³ and the standard sources at once, so a run that wants
  > both P2¹³ (this criterion) and P4¹³ (provenance inquiry, which needs the V2a.1
  > provenance questions) must alternate `--no-p213` on some invocations — which segments
  > run which mode is the author's call at launch, not something this driver decides for
  > them.
- **P3¹³ (bounds hold):** decay bounds |M| with per-round cost flat across the full
  vault scale; horizon counted, never silently dropped.
- **P4¹³ (provenance inquiry works):** the loop's authored-vs-collected verdicts
  agree with the author's own judgment on a sampled subset (the author as ground
  truth about the author), with `Clippings/` recovered without being told its
  meaning.
- **P5¹³ (diachrony legible):** a topic's treatment-over-time reads correctly in the
  audit lens for at least one exemplar topic the author picks — with the journal's
  50-year span as the K2 showcase: at least one **disposition** (a habit standing
  across decades) and one **mood** (a state that faded) legibly separated by the
  decay clock.

## Findings

**V2a.1 oracle loop landed (2026-07-18)** — `src/oracle_notes.py` +
`tools/run_vault_v0.py`'s `_run_oracle` wiring; the next real run may write
`Arisbe/Questions-<date>.md` into the vault.

*(no other findings yet — this section fills in only after a real-vault run the author has reviewed.)*

## Custody note

Model artifacts driven from the real vault (UoDs, chains, and anything else
`tools/run_vault_v0.py` writes) live under `runs/run13/`, which `.gitignore` excludes in
full — nothing derived from the real vault ever enters git. The driver's per-segment
stdout digest is numbers only (counts, snapshot dicts keyed by kind/reason, |M|) and
never carries a note id, title, or path, so even a captured console log stays
custody-safe. Only aggregates the author has personally reviewed are ever copied by
hand into this log — this file carries no data from an actual run yet.

---

## Findings

**F1¹³ (2026-07-18) — the §3.3 gate refused the first real segment save; root
cause long constants; fixed same day.** The author's first launch crashed at the
segment-1 `save_uod_with_chain` with `CorrespondenceViolation` — 53 occlusion
failures, all "vertex label box straddles out of its area cut." Diagnosis (repro
on the real vault at 60 rounds, numbers-only forensics): the straddling vertices
carried constants of **60–142 characters** (unresolved wikilink targets, long
filenames, journal entry ids) whose label boxes overflow their residence cells at
scale; invisible at fixture scale. A second, coupled finding: the driver never
wired **ttl/decay** (the spec's Bounds bullet and P3¹³ both expected it), so |M|
grew unboundedly and the save-time layout took ~36 minutes at |V|≈1,265.
**The discipline held**: §3.3 refused *before* any disk write — no corrupt
artifact exists; the crash is the gate working.
**Fix (same day):** (1) the bounded-constant invariant — no emitted constant
exceeds 40 chars; longer originals become opaque digest ids with the decode map
in the gitignored `labels.json` sidecar (custody *improves*: long paths/titles
now never enter M at all); the digest reports `max_const_len` and
`digested_labels` as standing observables. (2) `--ttl` (default 120 rounds)
wired into the driver, bounding |M| per P3¹³'s expectation. Four new tests
including the previously-missing fixture-scale save-attest end-to-end.
**Relaunch:** `uv run python tools/run_vault_v0.py --rounds 200 --segments 3`
(ttl defaults to 120; `--ttl 0` disables at your own save-time peril).

**F2¹³ (2026-07-18) — segment 2 crashed inside decay's licensed ERA; fixed
same day.** The relaunch's segment 2 raised `AssertionError: ERA apply
failed: ... Selected subgraph contains elements not in target area` out of
`_apply_decay` → `revise_with_disposition_recorded(DISPOSITION_RETRACT)` →
`world_scroll.retract_from_m` → `proof_authoring.apply_rule("ERA")`. Root
cause: the driver's segment carry round-trips M through
`generate_egif`/`parse_egif` between segments, and that round-trip **shares
an identical constant across sibling cells** into one vertex — documented
already in `world_scroll`'s own accommodation note ("an EGIF-round-trip-
shared constant in a sibling cell copies totally"). Reproduced in isolation
(`tests/test_agon_evolution.py::test_decay_falls_back_honestly_on_a_round_
tripped_resident_model`): two atoms of different relations sharing one
constant, homed in two different cells after a round-trip. Decaying the
first (whose cell owns the vertex) succeeds — the vertex is still
"semi-free" (its sibling atom keeps it connected), so the ordinary
closure-validator exemption applies and the licensed per-cell ERA goes
through clean. Decaying the *second* atom next is where it breaks: the
vertex is now orphaned in a cell with no edge left in it, so erasing the
second atom must pull the orphaned vertex into the erasure closure from a
*different* area — and `ErasureRule`'s own precondition check (rightly
strict for the ordinary case: every selected element must sit in the target
area or be reachable through it) refuses that as "elements not in target
area." **The discipline held here too**: this is an assertion inside the
*licensed-move machinery itself* — a rule correctly refusing a move it
cannot certify — not a silent corruption; nothing wrong was ever written to
M, the run just stopped.
**Fix (same day):** `agon_evolution._apply_decay` now tries the licensed
path first and, only on `AssertionError`/`ValueError`, falls back to
`_structural_retract_atom` — an honest **unlicensed** structural erasure
(`without_element`, generalizing `model_revision.retract_atom`'s approach
from *the sheet* to *any* area so it still finds a resident M's cell atom)
that removes just the matched edge and prunes the argument vertex only if
it is now truly unreferenced — preserving the world-scroll shape exactly,
mirroring the `live_runner` precedent (`retract_from_m`, fallback
`retract_atom`) for the one shape that precedent didn't anticipate. The
fallback step records `derivation: []` (no Dau rule licensed the move —
honest) and keeps `act: "m_retraction"`, so the m_view tripwire still sees
an acknowledged act. New test drives the exact failing sequence and pins
the pre-fix `AssertionError` as evidence before asserting the post-fix
no-crash + fallback-derivation behavior.

**F3¹³ (2026-07-18) — the journal spine was priced out and never read
(`journal_entries: 0` on the real vault); fixed same day.** The real
journal is ~2.4MB, so a single whole-file journal want priced at
`probe_cost` ≈120 — against every 1-cost scan want, no round's attention
budget ever chose it, so the journal (the K2 showcase, P5¹³'s 50-year span)
never entered M at all. A second, coupled problem: `journal_facts` emitted
*every* entry (1,583 of them) as one giant conjunction — a bad layout unit
even if it had been affordable. **Fix (same day):** the journal is now read
in **batches**. `VaultWorld._journal_entry_batches`/`journal_facts_batches`
split a journal's entries into groups of at most 40, each its own
parseable conjunction, computed with one file read; `VaultFeed._seed`
registers **one journal want per batch** (`key=("journal", relpath,
batch_idx)`, cost `1.0 + batch's line-span / 20_000` — affordable, the same
shape as `probe_cost`'s byte-based formula but for a batch with no file
size of its own — severity 8.0 unchanged, so the author's own datelined
voice still outranks generic listing, batch by batch); `_execute` looks up
the precomputed batch text. `journal_facts` (whole-file) stays as a
compatibility reader for existing tests/one-shot inspection, docstring
pointing at the batched path. New tests: batches parse and cover every
entry exactly once (synthetic 97-entry journal → 3 batches of 40/40/17);
per-batch cost stays well under 10 on both the fixture and a synthetic
~200-line journal; the feed registers one affordable want per batch; a
fixture drive reads `journal_entry` atoms within the first 10 rounds
(`probe_feed._model_signature`).

**Follow-ups landed in the sibling commit** (not this one): the horizon
registration cap raised, and the usage ledger made idempotent under
re-polling — see `V2a.1 follow-ups: ledger idempotent under re-polling, one
budget truth, clobber guard, horizon cap raised`.

**Relaunch:** `uv run python tools/run_vault_v0.py --rounds 200 --segments 3`
(ttl defaults to 120; `--ttl 0` disables at your own save-time peril) — the
same command as F1¹³'s relaunch; segment 2's crash and the journal's
starvation are both fixed underneath it, no new flags needed.

**F4¹³ (2026-07-21) — the journal spine is READ but does not PERSIST: it
decays out before the end-of-segment digest, so `journal_entries: 0`
survived F3¹³. Root cause found + reproduced; fix is an author design call
(unpatched).** The real run (`runs/run13_console.txt`, mtime 2026-07-21 —
post-F3¹³) still shows `journal_entries: 0` and `entries_per_decade: {}` in
**all three** segment digests, even though `ledger.kinds.journal ≈ 119.8`
is the *top* kind. F3¹³ fixed *pricing* (the journal is now affordable and
chosen); it did not make the journal *stick*.
- **What `journal_entries` measures:** `tools/run_vault_v0.py:170`,
  `tally.get("journal_entry", 0)` — a point-in-time count of `journal_entry`
  atoms *in M at the segment digest*. `0` is truthful: M holds no journal
  atoms at that instant. Not a reporting bug.
- **What `ledger.kinds.journal ≈ 119.8` means:** `attention_economy` line ~122,
  the per-kind **decayed yield** = round-granular M churn (`added + removed +
  |Δcuts|`) credited to the chosen kind. ≈120 ≈ a 40-entry batch × 3 atoms —
  so journal wants *are* chosen and *do* enter M. Read, not starved.
- **Why they vanish:** journal wants are **finite** (`VaultFeed._seed`,
  `src/vault_world.py:524-532` — ~40 batch wants, seeded once per segment;
  `_seed` guarded by `self._seeded`) and journal is **not a
  `persistent_kind`** (`VaultFeed.persistent_kinds = frozenset()`), so each
  batch executes once and settles, never re-proposed. `--rounds` is **per
  segment** and a **fresh `VaultFeed` is built per segment**
  (`_run_segment`, `run_vault_v0.py:188`), so within one 200-round segment the
  ~40 batches are chosen early (severity 8.0, rounds ~1-40), their atoms enter
  M, then **disuse-decay (ttl=120) erases them at rounds ~121-160 — before the
  end-of-segment digest at round 200** — and nothing replenishes them.
  Scan/read atoms persist only because `_refill` keeps discovering *new* notes,
  a fresh supply the finite journal has no analogue of.
- **Reproduced (fixture, decay forced):** `--fixture --rounds 30` →
  `journal_entries: 5` in every segment (M=54, `m_removed: 0`, no decay
  pressure — the F3¹³ test's regime, which is why it passed). `--fixture
  --rounds 120 --ttl 8` → **`journal_entries: 0`, `entries_per_decade: {}`**
  (`m_removed: 24`, journal yield 2.88 — read then decayed). The real
  vault's 200-rounds-vs-ttl-120 is the same regime at scale.
- **Consequence for P5¹³ (the K2 showcase):** it **cannot be disposed** as
  the log stands — the 50-year journal spine never survives to the digest to
  be read in the audit lens, so "a disposition standing across decades vs a
  mood that faded" has nothing to measure. F4¹³ blocks P5¹³.
- **Test-coverage gap (safe follow-up regardless of the fix chosen):** the
  F3¹³ regression test drives a short fixture run (rounds < ttl), so it
  never exercises decay and cannot catch a persistence regression. Extend it
  to run rounds ≫ ttl and assert `journal_entries > 0` at the digest.

**Fix is an author design call — three approaches, different K-measure
semantics (NOT patched, pending the author's ruling):**
  1. **Pin the journal spine from disuse-decay** (a protected/standing atom
     class exempt from ttl). Semantically the truest to intent — the journal
     *is* the standing longitudinal spine, K2's whole point is that it does
     *not* fade — but it makes the journal a privileged, non-decaying tier,
     which is a real statement about what the vault kytos treats as
     bedrock-vs-working-set. Touches the runner/agon_evolution decay pass.
  2. **Make journal a `persistent_kind`** (re-proposed each round → its atoms
     re-delivered → never disuse-decay). Keeps the spine alive through the
     ordinary use=re-delivery mechanism (no new decay tier), but journal
     (severity 8.0) would then dominate the proposal stream every round —
     a heavy, possibly starving change to the economy's balance.
  3. **Measure the journal where it lives, not at the digest** — accept that
     the working-set M is churn-bounded and read the journal spine from a
     separate standing structure (or a per-decade rollup captured at read
     time), leaving M's decay semantics untouched. Least invasive to the
     loop; changes what "journal_entries" reports rather than what M retains.

The recommendation, flagged as the assistant's: **(1)** best matches the
stated intent (the journal is the *retained* K2 spine, explicitly contrasted
with the mood-that-fades), and a decay *exemption for a declared standing
tier* is a cleaner K-measure story than a severity-8 want re-fired every
round — but it is a genuine statement about a bedrock/working-set split in
the vault kytos, which is the author's to make. Priors P1¹³–P4¹³ and the
P5¹³ disposition remain the author's.

**RESOLVED (2026-07-21, the author chose approach (1) + the test extension).**
The journal spine is now a **pinned bedrock tier exempt from disuse-decay**.
`agon_evolution.UsageLedger(ttl, pinned_relations=…)` never reports a pinned
relation's atoms stale (relation-level exemption via `parse_atom_key`;
`agon_evolution.run` gained a `pinned_relations` param, default `None` → the
`not self._pinned` short-circuit keeps every existing caller's decay
byte-identical); `vault_world.JOURNAL_SPINE_RELATIONS` =
`{journal_entry, entry_date, entry_lines}`; `tools/run_vault_v0.py`'s
`_run_segment` passes it. **Verified end-to-end:** the exact repro regime
(`--fixture --rounds 120 --ttl 8`) that read `journal_entries: 0` now reads
**`journal_entries: 5` with `entries_per_decade` populated** (1930s/1970s/1980s/
1990s/2020s — the decade separation P5¹³ needs), and across 3 segments the
spine holds at 5 with `m_atoms` stable (no cross-segment bloat/duplication;
`m_removed` fell 24→9, |M| bounded by the journal's finite size — the intended
bedrock). **Test extension (F4¹³'s coverage gap closed):**
`test_vault_world.py` now drives rounds ≫ ttl — a **control** asserting the
un-pinned spine decays to 0 (the bug bites in-test) and a **pinned** case
asserting it survives; `test_agon_evolution.py` adds the ledger-level pin unit
+ an end-to-end `run` pin. Full loop/decay/membrane/vault suite: 337 passed /
1 skipped. Priors P1¹³–P5¹³ still the author's — P5¹³ is now *measurable*
(the spine survives to the digest to be read in the audit lens).
