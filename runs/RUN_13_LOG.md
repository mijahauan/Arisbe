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
