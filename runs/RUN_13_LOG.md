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

---

## Disposal (2026-07-26, the author's rulings; the assistant writes the log)

**The run being disposed:** three real-vault segments (seg1 2026-07-18, seg2
2026-07-20, seg3 2026-07-21 11:16), 200 rounds each, ttl 120, P2¹³ instrument
on. The F4¹³ journal-spine fix (commit `77b6521`) landed 2026-07-21 **16:39 —
after all three segments** — so every digest truthfully reads
`journal_entries: 0`; the fix never got a real-vault segment in this run.
Prior artifacts backed up to `runs/run13/_backup_run1_predisposal/` (inside the
gitignored tree) before any re-run touched the store.

- **P1¹³ (retrodiction) — NOT INSTRUMENTED AT V0 (ruled).** The V0 driver has
  no forecast-vs-frequency-baseline machinery; there is nothing to dispose
  against. The prior was pre-registered for the vault *cycle*, and V0 (the
  metadata membrane) never built that instrument. Carries forward to the stage
  that builds it — not held, not refuted, honestly unmeasured.

- **P2¹³ (legible questions) — pending the scoring pass (this sitting).** The
  run wrote one P2¹³-mode note (5 questions, sealed forecasts in the ledger; 0
  reveals / 0 answers / no ratings at run end). The author reports the note is
  now marked; a post-fix re-run (launched this sitting, below) parses the note
  first and records the marks. Note the criterion needs ≥2 segments of
  comparator marks — one marked note cannot yet clear the ≥25-point bar by
  itself; this sitting's scoring is the *first* of the two.

- **P3¹³ (bounds hold) — HELD (ruled).** Direct console evidence at full vault
  scale: |M| flat at 780 atoms across all three segments under real churn
  (~6.8k atoms added *and* removed per segment — decay doing real work), the
  horizon counted at 9,100 open / **0 dropped**, `max_const_len` pinned at 40,
  `digested_labels` stable at 1,780. Texture worth naming: the horizon is
  100% binary-extension items (9,100 of 9,100) — the not-yet-legible is
  entirely the binary-relation frontier at V0.

- **P4¹³ (provenance inquiry) — pending marks + a caveat.** The scheduling
  tension the operator note named bit as predicted: with P2¹³ default-on, the
  run's only note carried the 2+2 comparator questions *in place of* the V2a.1
  provenance mix, so no authored-vs-collected verdict was ever put to the
  author in note form this run. Disposing P4¹³ needs a `--no-p213` cycle (or
  the author judging the verdicts directly in the audit lens). Not disposable
  from this run's ink.

- **P5¹³ (diachrony / K2 showcase) — BLOCKED-IN-THAT-RUN (ruled) + short
  re-run authorized.** The segments predate the F4¹³ fix; the 50-year journal
  spine never survived to a digest, so disposition-vs-mood had nothing to
  measure. The fix is verified end-to-end at the exact repro regime on
  fixture (spine holds at 5 entries, decades 1930s–2020s separated). The
  author ruled: log as blocked, launch a short post-fix real-vault re-run
  (one segment × 200 rounds, defaults), dispose from its digest. Launched
  this sitting; digest to be appended below when it lands.

**The post-fix re-run digest (launched 2026-07-26 ~22:09, completed
2026-07-27 ~07:38 — a real-vault segment is ~9h, the "short" is one segment
not three):**

- **P5¹³'s substrate is NOW MEASURABLE — the journal spine held to the
  digest.** `journal_entries: 1477` (was 0 in every pre-fix segment), with
  the decades legibly separated: 1970s 37 · 1980s 271 · 1990s 111 · 2000s
  129 · 2010s 540 · 2020s 389. |M| = 5,202 atoms — the pinned bedrock tier
  (≈4,400 spine atoms, bounded by the journal's finite size, the intended
  F4¹³ split) riding above a decaying working set (`m_removed: 1960` — ttl
  still doing real work on the non-pinned tier); horizon 9,102 open /
  0 dropped; `max_const_len` 40 holding. The audit-lens reading
  (disposition-vs-mood on an author-picked topic) is the author's remaining
  act; the spine is there to read.
- **P2¹³/P4¹³ — the scoring pass found NO parseable marks.** The oracle
  parsed the prior note and read **all 5 questions as `ignored`** (5
  outcome rows, statuses {ignored: 5}; no ratings recorded; correctly wrote
  no new note — "previous note awaits answers"). The author reports having
  marked the note, so the likely story is mark format: the parser recovers
  only `**A:** <text on the same line>` answers (decline synonyms count;
  an empty `**A:**` = ignored) and `**R:** trivial` / `**R:** non-trivial`
  ratings (the unedited `**R:** (trivial | non-trivial)` template = no
  rating). Recovery path verified: `record_outcome_once` dedups on
  (status, answer), so ignored→answered records cleanly on a re-poll once
  the marks are in the recognized form. P2¹³/P4¹³ stay pending — honestly,
  on a format mismatch, not on absent marks.

**Scoring completed (2026-07-27, same sitting, two real-vault edit-pattern
findings fixed under it):**

- **The answers landed on the second pass** (author re-marked; rounds-0
  oracle-only invocation with the spine-bearing seg1 backed up and restored
  around it): 5/5 `answered`, 5 reveals, **5 banked** into
  `vault_v0_author_model`; a fresh 2-question note written.
- **F5¹³ (parser) — the placeholder-append edit pattern.** The author's
  `**R:**` marks read as unrated because the rating was appended AFTER the
  rendered placeholder (`**R:** (trivial | non-trivial) non-trivial`) — an
  edit the template itself invites. Fixed same sitting: `parse_note` strips
  the literal placeholder before matching (untouched placeholder still =
  unrated); regression test added; oracle suite 104/104.
- **P2¹³, segment 1 of ≥2 — NO SEPARATION:** docket 1/2 non-trivial (50%)
  vs template-random 1/2 (50%) — a 0-point gap against the ≥25-point bar;
  the fifth question rides outside the comparator arms. Ceiling canary
  clean (3/5 = 60% non-trivial overall < 90% — the segment is informative).
  The criterion needs a second comparator segment from a real (non-empty-
  economy) run before it can be disposed either way.
- **F6¹³ (instrument practicality) — the audit lens does not scale to a
  segment chain cold.** `/organon/uods/{id}/audit` materializes every state
  from scratch: measured ~53 s/state on seg1 (|V|≈3.5k, |E|≈6.4k) × 2,164
  steps ≈ 33 h for one ribbon. The live loop never pays this (its
  `IncrementalMaterializer` carries the fixpoint across rounds); the route
  has no such carry. Reading used instead: a **sampled headless ribbon**
  (17 states, materialization skipped — sound here because the vault M
  holds ground facts only, no Horn laws). Also found: the side-store's
  inner `universes/index.json` (2026-07-18, stale) points `vault_v0_seg1`
  at a dead nested artifact — the correct service root is `runs/run13`.
- **P5¹³ dry-run — the disposition half reads TRUE:** proposal
  `(links *x "People/Charles Sanders Peirce.md")` enters M at ~state 135
  and **holds through state 2,164** under live decay (the segment erased
  1,960 atoms; not these); `(links *x "Semiotics.md")` enters ~state 1,217
  and holds. The semiotics web (Concept.md, Abduction.md, Conceptual
  Graphs.md linking in) is a habit in the record's own terms.
- **F7¹³ (the content-distribution finding — the author's, verbatim
  concern):** the structural membrane's sensors are anti-correlated with
  where the life's evidence lives. The vault's Obsidian-native note-per-idea
  regions read well (the semiotics disposition above); but the **journal —
  decades of observation recorded sequentially, not broken into notes —
  holds the richest evidence of both exemplar topics, and at V0 its
  *content* is custody-invisible by design** (dates and line-spans only).
  Concretely: the mood exemplar (a worldview inhabited in youth, abandoned
  20–30 years ago) has **zero structural ink** — no match in M or in the
  1,785-label decode map after ~120 notes seen. The mood half of P5¹³
  cannot be read from structure alone; it waits on either a wider scan
  (if era-markers exist as files), an author-named structural marker, or a
  **content aperture the author has not yet authorized** (a V2b design
  decision, not a defect of the run). Disposition of P5¹³ pending the
  author's choice among those paths.
