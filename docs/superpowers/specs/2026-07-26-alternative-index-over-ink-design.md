# AlternativeSet Re-Housing: Index-Over-Ink

**Status:** Pre-registered design spec (author-approved 2026-07-26)
**Date:** 2026-07-26
**Supersedes the engineering shape of:** Task 4 (`src/alternative_set.py`,
`src/alternative_inquiry.py`, commit `bd6bbab`) — the *philosophy* of
`docs/superpowers/specs/2026-07-25-alternative-set-inquiry-principle.md`
(never pre-filter; trace consequences; materiality discovered, not assumed;
bounded-heterogeneous-mortal kytes) remains governing and unamended.

**Frozen inputs:** Examination V (`docs/ADVERSARIAL_EXAMINATION.md` §V,
`90eab83`); the three author rulings of 2026-07-25/26 (index-over-ink ·
link-by-key · the membrane threat model); the inquiry-principle doc; the
Task 4 code as raw material.

**The proving rule (unchanged):** ONE complete producer→consumer loop on
Task 4's wire (peel-UNKNOWN → interrogative) before Tasks 5–6 unblock.

---

## §0 Rulings ledger

Decisions taken during this design session, in force for the build:

| # | Question | Ruling |
|---|----------|--------|
| R-A | How is the trace recorded on the chain? | **TRACE as PEEL-twin**: one identity-transform step, earned at record time, params carry the whole trace, gate recomputes it forever. Ascent into ink = the *existing* `entertain_episode`, cited not rebuilt. |
| R-B | How much of the threat model builds now? | **Taxonomy + seam now, registry later**: reception classification + routing (Horizon / quarantine) built; source track record behind an injectable `SourceRecord` protocol whose default answers "untracked"; the source-keyed ledger registry and vigilance-reserve economics are named follow-ons. |
| R-C | Which consumer proves the loop? | **Attention-economy severity wire**: `wants_from_alternatives`, severity from traced materiality, novelty damped against the S-register (its first reader). |
| R-D | What happens to the Task 4 modules? | **Clean re-house**: new `alternative_index.py` + reworked `alternative_trace.py`; `alternative_set.py`, `alternative_inquiry.py`, the `Doubt` alias, and the UoD's alternative methods/fields retired. No warrant-float namespace survives. |
| R-E | Pathologies of thought (author extension, this session) | Fact/rationale distinction; posture-only receptions counted and inert; recompute law as the anti-circularity invariant. Full Berger & Luckmann treatment (legitimation, "what's right" vs "what works") **queued for the commens rung** — hooks named here, doctrine not folded until examined. |
| R-F | The two apertures (author extension, this session) | The grounding of §5: both deviation sources are lawful apertures; **depth misrepresentation** is the *enforced* pathology class — under standing suspicion that other, non-depth pathology families exist (author's rider); claimed standing is **stripped at the membrane**; the reception taxonomy = contextualization adequacy. |

---

## §1 Shape and modules

The AlternativeSet stops *holding* evidence and starts **indexing** it — the
QuotationMark pattern applied to deliberation. Every evidentiary claim in a
record is a pointer to a real, gate-checked chain step; the record is an
overlay that can be **rebuilt from the chain** and is attested against it.
The register is a cache over the chain, never a second authority.

**New / reworked modules:**

- **`src/alternative_index.py`** (new): `alt_key` (content identity),
  `Materiality` (the vector), `Reception` (+ classification),
  `AlternativeRecord` (the index), `AlternativeRegister` (standing, bounded,
  snapshot/restore, settlement wire), the **AS1–AS4 law**,
  `attest_alternative_record` (raising) / `run_alternative_record`
  (reporting).
- **`src/alternative_trace.py`** (reworked from `alternative_inquiry.py`):
  the dry-run trace with the V.4 + escaping fixes, `trace_step` (the
  PEEL-twin chain step, rule `TRACE_ALTERNATIVES`, act
  `alternatives_traced`), `KyteProfile` (gains `alt_capacity`),
  `BoundedRegister` + snapshot/restore.

**Retired** (tests replaced by law tests): `src/alternative_set.py`,
`src/alternative_inquiry.py`, the `Doubt` alias,
`universe_of_discourse.select_alternative_at_state` /
`narrow_alternative_at_state` / `record_alternative_at_state` and the
`alternatives_by_state` / `all_alternatives` fields (+ the `doubts_*`
aliases). *Plan-time verification:* no corpus UoD carries an
`alternatives.jsonl` (nothing was live-wired; no data migration).

**Touched:** `semantic_game.py` (structured unknowns on `SemanticResult`),
`attention_economy.py` (`wants_from_alternatives`, `QuarantineRegister`),
`tomos_service.py` (sidecar = register snapshot; save failure **raises**),
`tests/test_corpus_polarity_discipline.py` (trace-recompute obligation).

**Not touched:** the protected core; `query_docket.py` (the live-run-proven
docket stands, per ruling 2 — the wire is by shared key, below); the episode
machinery (`world_scroll` / `m_steps`) — cited as the ascent path, unmodified.

---

## §2 Identity, the record, and the register

### Content key (ruling 2)

`alt_key(relation, labels) -> str` — canonical, content-derived, **arity
preserved**: a constant slot renders quoted, a generic slot (the V.4 `None`)
renders `*`. Examples: `white("Alba")`, `loves("Alba",*)`. The same doubt
seen twice **is the same record** — this kills V.8's positional-id defect at
the root ("standing question" now holds by construction).

**Docket wire:** a record key projects onto the docket's `(shape, grip)` key
by dropping generic slots: `loves("Alba",*)` → `("loves", ("Alba",))`. The
docket is not modified; identity is shared by projection, and settlement
meets in M (below).

### `AlternativeRecord` (frozen dataclass)

| Field | Type | Meaning |
|-------|------|---------|
| `key` | `str` | `alt_key(relation, labels)` — the identity |
| `relation`, `labels` | `str`, `Tuple[Optional[str], ...]` | the unknown atom, generic slots `None` |
| `kind` | literal | vocabulary kept from Task 4; **only `interrogative` is built**; every other kind is refused at construction until it can meet the same invariants (V.8 discipline) |
| `alternatives` | `Tuple[str, ...]` | EGIF propositions, **validated parseable at construction** — an opaque label is refused at birth |
| `emerged_from` | `Optional[str]` | step id of the PEEL that surfaced the unknown |
| `traced_by` | `Optional[str]` | step id of the TRACE_ALTERNATIVES step (`None` = honestly untraced) |
| `materiality` | `Optional[Materiality]` | the vector, `None` = untraced |
| `resolved_by` | `Optional[str]` | step id of the acknowledged M-act that resolved it |
| `selection` | `Optional[str]` | the chosen alternative (∈ `alternatives`) |
| `receptions` | `Tuple[Reception, ...]` | membrane input, §5 |
| `posture_pressure` | `int` | count of stance-only receptions (§5) — visible, inert |
| `emerged_round` / `last_touched_round` | `int` | LRU bookkeeping for the bounded register |

The record stores **no M snapshot** (Exam V amendable (c) dies here): the
key + step refs suffice; any needed context is the chain state itself,
recoverable by id.

### `Materiality` (frozen dataclass — the vector; V.1/V.2 dead)

`tier` (`"material"` | `"bare"` | `"spurious"`) + `diverging:
Tuple[str, ...]` (relations differing between branches) + `extra_true` /
`extra_false` (the branch-delta atom keys, deterministic order) + optional
`k3_true` / `k3_false` pairs (explicit, derived) when consulted. **No scalar
exists**; reception is *not* a component — a strongly-traced-but-disputed
record and a weakly-traced-uncontested one are structurally distinct, which
is exactly the pair Exam V.2 showed collapsing to `0.5 == 0.5`. **No field
in the new namespace is named `warrant`** — that word stays doctrinal
(○ / ⛓ / ⚔), per ruling 1.

### `AlternativeRegister`

Standing, content-keyed (`Dict[str, AlternativeRecord]`), bounded by
`KyteProfile.alt_capacity` (default 64) with **LRU displacement counted,
never silent** (`displaced_keys`, dedup'd — the docket's deferred-keys
discipline). Because records rebuild from the chain, displacement loses no
truth, only cache.

- `note(record, *, round_idx)` — admit/refresh by key; a re-arrival touches
  (`last_touched_round`), never forks.
- `settle_from_chain(chain)` — for each open record, scan forward from its
  `emerged_from` step for the **earliest step whose `to_state`'s `m_view`
  settles either branch** — holds a matching ground atom (generic slots
  match any binding → `selection = atom_egif`) or a subgraph
  `same_graph`-matching the denial (→ `selection = denial_egif`) — **and
  whose act is acknowledged** (the gate's `_acknowledged` list); the record
  resolves **citing that step**. Resolution is thus uniform: *every*
  resolution cites real licensed ink — whether chosen deliberately or
  observed to have settled. (The docket settles independently via its own
  `observe`; the wire is the shared key, no docket code changes.)
- `snapshot()` / `restore(state)` — full round-trip on the docket template
  (records + counters + displaced keys). **V.6 dead**: succession is
  engineering, and doubly so — `rebuild_from_chain(chain)` re-derives the
  register from TRACE/PEEL/M-act steps alone, proving the index never
  became an authority.

---

## §3 The chain discipline — trace as a PEEL twin (ruling R-A)

### `trace_step`

```
trace_step(pc, relation, labels, *, s_register, a_register,
           note=None, branch=None) -> Materiality
```

Identity transform via `pc.apply_derived(TRACE_ALTERNATIVES, lambda g: g, …)`
— the exact `peel_step` pattern: **earned at record time** (the dry-run trace
actually runs against `pc.current`), params carry the whole result,
re-checkable forever:

```python
{"act": "alternatives_traced", "earned": True,
 "relation": …, "labels": […, "*", …],          # generic slots as "*"
 "atom_egif": …, "denial_egif": …,
 "tier": …, "diverging": […],
 "extra_true": […], "extra_false": […],
 "s_admitted": […], "s_displaced": […],
 "a_admitted": […], "a_displaced": […]}
```

The S/A admissions ride in params, so the registers **fold from the chain**
— a second succession guarantee beyond snapshot/restore.

### The trace itself (V.4 dead)

- A generic slot becomes a **defining variable**, never a constant:
  `(loves "Alba" *x)` vs `~[ (loves "Alba" *x) ]` — "someone Alba loves"
  vs "Alba loves no one". The constant `"None"` is unconstructible.
- Labels are **EGIF-escaped** (embedded quotes/backslashes); an
  unrepresentable unknown is **refused and counted** (the count-or-refuse
  dispatch rule from `probe_feed`), never silently mangled.
- Mechanics otherwise as Task 4 proved them (dry-run `assert_fact` on
  `m_view` copies, `materialize_egi`, sheet-atom diff, the K3 honesty check
  for the empty-diff case) — the algorithm withstood examination; only its
  housing changes.
- **Trace budget:** eager tracing bounded per call (`budget` param, default
  8 per round); unbudgeted unknowns register **untraced**
  (`materiality=None`, AS4 names them) and are traceable later.

### Gate extension

`test_corpus_polarity_discipline.py` gains: **recorded traces recompute
identically** (the peel-verdict pattern — re-run the trace at `traced_by`'s
`from_state`, compare tier/diverging/extras) + a falsifier (a doctored tier
is flagged). No new acknowledged act is needed: `alternatives_traced` never
changes `m_view`, and the *existing* tripwire already flags any identity-act
step that does — automatic containment.

---

## §4 The law and the boundary (V.7 dead)

The overlay-discipline triad (law · attestation hook · ascent path), as
`ReferenceMark` carries R1–R4 and `QuotationMark` carries S1–S5:

- **AS1 — index resolves.** Every step ref (`emerged_from`, `traced_by`,
  `resolved_by`) resolves in the chain, and the step's recorded params match
  the record's content (relation/labels/alternatives). The
  `ChainStepQuotationResolver` precedent, applied to deliberation.
- **AS2 — trace recomputes.** Re-running the trace at `traced_by`'s
  `from_state` reproduces the `Materiality`. (With the gate's peel-recompute,
  this is the standing **anti-circularity / anti-lie invariant**: what cannot
  re-derive cannot stand as derivation.)
- **AS3 — resolution licensed.** A resolved record's `resolved_by` step is an
  acknowledged M-act whose ink introduces the selection;
  `selection ∈ alternatives`.
- **AS4 — honest horizon.** Untraced records, unresolvable refs, refused
  unknowns, quarantined receptions, displaced keys — all named and counted,
  never silently dropped.

`attest_alternative_record(record, chain, *, trace_fn)` raises
`AlternativeLawViolation` (an `AssertionError`, house style);
`run_alternative_record` returns the non-raising report.

**Ascent path (cited, not built):** a question that deserves to stand drawn
ascends by the *existing* `entertain_episode` / `discharge_step` /
`abandon_step` machinery — mention-first, vacuity rider, discharge only with
a confirming PEEL. This spec adds no ink machinery.

**Persistence boundary:** the sidecar stays `alternatives.jsonl`, now a
register snapshot, written atomically in sorted-key order.
`save_uod_with_alternatives` **attests each record against the persisted
chain** when one exists (the §3.3-at-the-boundary discipline, one floor up),
and a failed alternatives-save **raises** — the demotion-to-print dies
(Exam V amendable (f)).

---

## §5 Reception, the threat model, and the pathology hooks

### The two apertures (grounding — author, 2026-07-26)

Arisbe's transformation discipline — sound rule applications composing lines
of thought — is the **stability condition of thought**: the chain is the
context, and every standing element carries its replayable derivation. The
two lawful apertures through which deviation can enter:

1. **Inside — INS in a negative context.** The calculus licenses scribing
   *anything* at odd depth (the ⊥-door). This is not a defect: it is where
   hypothesis, imagination, and entertained contraries lawfully live, each
   held **from its context** (cells, cuts, DAG branches). Stability rests
   not on preventing this but on the **polarity discipline**: nothing
   crosses from odd to even depth except by a recorded, licensed,
   re-checkable move. The AlternativeRecord is the disciplined form of
   maintaining contradictory possibilities — it holds atom *and* denial
   while asserting neither; nothing contradictory ever stands at even depth.
2. **Outside — objectivated products arriving context-poor.** What crosses
   the membrane is thought-product stripped of the chain that earned it
   (Berger & Luckmann's objectivation, seen from the receiving side: the
   construction history invisible, the product presenting as bare
   facticity), with abbreviated or absent contextualization. The receiving
   kytos cannot check it by its internal constraints; it can only
   **re-contextualize at its own expense** (trace, peel, re-derive) or lean
   on **track record as compressed context** — partial, never a substitute.

**Depth misrepresentation — the enforced pathology class, not a definition
of pathology:** presenting content at, or as at, a polarity it has not
earned. A lie is entertained (or nowhere-standing) content presented as
discharged; a fallacy is an odd-depth move dressed as even-depth; the
internalized "ill rationale" is an arrival whose *claimed* standing was
taken at face value. An arrival that is merely *unaccompanied* — honest but
orphaned — is context-poverty, not pathology: it routes to the Horizon,
re-attemptable as context accrues.

**Standing suspicion (author's rider, 2026-07-26):** other pathology
families, originating from something besides depth, must be presumed to
exist — naming the class this machinery enforces against must not be read
as exhausting the genus. Concrete candidates already visible in the
system's own vocabulary, none depth-shaped: pathologies of **attention**
(agenda-setting by omission — controlling which questions ever get traced,
with no polarity misrepresented anywhere; noisy-TV capture), of
**identity** (equivocation — one word riding two content-keys), of
**pacing** (rumination/thrash — poise's named poles). The taxonomy of
pathologies is itself an open AlternativeSet, AS4-style: what this spec
cannot detect it must not silently define away.

**The boundary rule:** **claimed standing is stripped at the membrane.**
Whatever posture a product arrives with — expert confidence, agreement,
"everyone knows" — it enters at odd depth (mention / entertainment / index)
and re-earns standing inside through the same recorded disciplines as native
content. Ruling 3's "trust from track record, never content posture" is the
attention-side of this rule; polarity-stripping is the ink-side.

### The reception structure

`Reception(source, stance, classification, claim_egif, bears_evidence)` —
`stance ∈ {supports, disputes, novel}`; `claim_egif` optional (the checkable
content carried, if any); `bears_evidence = claim_egif is not None and it
parses`.

**Classification = contextualization adequacy** (the taxonomy re-derived,
not ad hoc), by a deterministic default classifier behind an injectable
seam:

| Class | Reading | Routing |
|-------|---------|---------|
| `legible-benign` | enough context arrived to check it | traceable like any content |
| `contested` | the context that arrived conflicts with what stands | held open; the contest is the docket/panel's to dispose |
| `illegible` | too little context to interpret | → `Horizon(reason="illegible-reception")`, re-attemptable |
| `adversarial` | context actively counterfeited (breakout patterns, flagged source) | → `QuarantineRegister` — bounded, counted, snapshot/restore, **never auto-reattempted** |

### Trust (ruling R-B)

The **`SourceRecord` protocol** (injectable): `track_record(source) ->
Optional[TrackRecord]` where `TrackRecord = (bets, hits, misses, accuracy)`.
The default implementation answers `None` for every source — **untracked**.
Reception influence is exactly this and no more:

- Materiality **never** moves on reception (it is trace-derived only).
- Want-severity may receive a **bounded** bonus only when the reception
  `bears_evidence` **and** the source has a positive track record.
- **Untracked + agrees earns exactly nothing** — Exam V.1's
  0.9-on-mere-agreement is structurally impossible, not merely avoided.

### Pathology hooks (ruling R-E)

- **Fact vs rationale:** a received *fact-claim* goes through the taxonomy
  above. A received *rationale* (an argument, a "because") can only enter as
  **mention** — ENTERTAIN ink, forceless — and lands in M only by DISCHARGE
  citing a confirming PEEL. The source argues; the calculus decides.
- **Circularity/fallacy:** AS2 + the gate's recompute obligations. Enforced,
  not aspirational.
- **The political play** (externalizing an "expert" rationale to tip an open
  question): a reception bearing on an **open** record with no new checkable
  content is **posture-only** — it increments `posture_pressure` and
  contributes nothing to materiality or severity. Visible and inert,
  whichever direction it pushes.
- **Deferred to the commens rung** (author's standing rule — queued, not
  folded): legitimation, universe-maintenance, "what's right" vs "what
  works", the sociology of the objectivated stock of knowledge. This
  section confines itself to what the specified machinery *enforces*.

---

## §6 The proven loop (ruling R-C — the unblocking condition)

**Producer** (V.5's missing caller, built): `SemanticResult` gains
`unknown_atoms: Tuple[Tuple[str, Tuple[Optional[str], ...]], ...]` —
collected during evaluation wherever an oracle answer or unwitnessed
existential yields UNKNOWN; deterministic order; generic slots `None`.
`peel_step` carries them in its params, so `emerged_from` points at real ink
from birth.

**Consumer** (V.5's write-only ledger, closed): `wants_from_alternatives
(register, *, round_idx, source_record=None) -> List[Want]` — `kind=
"alternative"`, `key=record.key`; severity from the tier table (one named
place, no magic floats in records): `material=8.0`, `untraced=4.0` (the
trace itself is a worthwhile reach), `bare=2.0`, `spurious` not emitted;
**novelty damping**: a distinction already standing in the S-register reads
at half severity — the S-register's first reader; reception bonus only as
gated in §5.

### Pre-registered acceptance criteria

- **AC1 (producer):** the peel over the fixture M yields deterministic
  `unknown_atoms`, including one existential UNKNOWN with a generic slot.
- **AC2 (trace):** TRACE steps recorded; the existential renders `*x` (the
  string `"None"` appears nowhere); an embedded-quote label round-trips
  escaped; the gate's recompute passes.
- **AC3 (identity):** the same unknown surfaced twice yields ONE record
  (touched, not forked); the register bounds with counted displacement.
- **AC4 (consumer):** on the same fixture, the economy arm provably asks the
  material question before the FIFO arm does — the principle doc's "the
  system uses learned distinctions next round," operational.
- **AC5 (reception):** scripted membrane — untracked-agrees changes nothing
  measurable; posture-only increments `posture_pressure` only; adversarial
  → quarantine (counted); illegible → Horizon.
- **AC6 (resolution):** the answer lands via `admit_step`/`discharge_step`;
  `settle_from_chain` resolves the record citing that step; AS3 holds; the
  docket settles by projected key.
- **AC7 (gate):** the full polarity gate passes over the produced chain,
  including the new trace-recompute obligation and its falsifier.
- **AC8 (succession):** snapshot/restore across a simulated segment boundary
  preserves registers and counters; `rebuild_from_chain` reproduces the
  register from the chain alone.
- **AC9 (law bites):** doctored step params (AS1), a doctored tier (AS2),
  and an unlicensed resolution (AS3) are each refused by
  `attest_alternative_record`.
- **AC10 (clean namespace):** retired modules/aliases/methods gone; no field
  named `warrant` or `external_warrant` in the new namespace; full suite
  green.

All ten deterministic and offline (CI-safe). **Tasks 5–6 remain blocked
until AC1–AC10 are green.**

---

## §7 Examination V disposition table

| Finding | Disposition in this design |
|---------|---------------------------|
| V.1 warrant corruption | No float named warrant exists; `Materiality` vector + `Reception`; the doctrinal gradient untouched. |
| V.2 scalar collapse | Vector + reception held separately; Exam V's two collapsing cases now structurally distinct. |
| V.3 field wiping | The wiping methods are retired; records are immutable; lifecycle moves live on the register and cite steps. |
| V.4 None-corruption | Generic slots → defining variables; escaping; refuse-and-count. AC2. |
| V.5 unplumbed / write-only | Producer built (`unknown_atoms` → peel params); consumer built (`wants_from_alternatives` reads tier + S-register). AC1/AC4. |
| V.6 fake succession | `BoundedRegister` + `AlternativeRegister` snapshot/restore **and** fold-from-chain. AC8. |
| V.7 unchecked overlay | AS1–AS4 + attestation hooks + gate extension + the ascent path cited (`entertain_episode`). AC7/AC9. |
| V.8 stringly disunity | Alternatives validated-parseable at construction; content-derived keys; non-interrogative kinds refused until they meet the same invariants. AC3/AC10. |
| (a) magic constants | Floats gone from records; the severity table is one named place; reception influence only via `SourceRecord`. |
| (b) state_id unvalidated | Step refs validated by AS1. |
| (c) context snapshot cost | Records store no M snapshot at all; context = the chain state, by id. |
| (d) false "EGI hashes" docstring | Identity is `alt_key` + validated EGIF strings; no hash claim. |
| (e) exclusivity/exhaustivity | The interrogative pair {atom, denial} is exhaustive and exclusive by construction; other kinds must declare their witness when built (deferred with them). |
| (f) save demoted to print | Raises. |

---

## §8 Out of scope (named follow-ons)

- Tasks 5–6 (thin spots; branch points) — blocked on AC1–AC10.
- The source-keyed track-record registry (persistent per-source ledgers) and
  the vigilance-reserve economics — wait for a live external producer to
  calibrate against.
- Entertain-in-ink for standing questions (the promotion threshold) — the
  ascent path exists; a policy for *when* to ascend is future work.
- The commens-rung examination of the queued threads (B&L legitimation,
  "what's right" vs "what works", the four-doubts set) — hooks named in §5,
  doctrine deferred per the author's standing rule.
- The open taxonomy of pathologies (the §5 standing-suspicion rider):
  non-depth families — attention, identity, pacing, and the not-yet-named —
  await their own examination; this spec enforces only the depth class.
