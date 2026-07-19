# Panel D brief — The One-Regime Discipline and the A3 Conservativity Claim
(verbatim from the independent panel, 2026-07-19)

**Examiner:** proof-theorist panel, charged to refute, not flatter. House standard: Examination III (`docs/ADVERSARIAL_EXAMINATION.md:1019`) — strongest charge in strongest form, the author's best answer classified ANSWERS/DEFLECTS, disposal by proof / runnable test / exact concession, confidence that the claim falls *as stated*.

**Headline results, before the details:**

1. **A live, empirically demonstrated A3 break** (not schematic — executed against the real engine on the real corpus exemplar): a licensed ERA of ordinary host ink, submitted through the engine's direct surface, silently **demotes a quotation oval to an asserted negation** — mention promoted to use. The refusal guard inspects the selection *before* closure expansion; the erasure then acts on the *expanded* set. §9-suspect and §10-suspect meet in this hole.
2. The corpus polarity gate verifies **annotations, not executions** — the F2¹³ docstring's defense ("the gate would refuse it") is true only for an *honest* forger.
3. V2a.2 quotation-cell banking (authorized 2026-07-19) is **mutually inconsistent with the loop that would carry it**, in three separately provable places.

---

## Suspect 9 — The F2¹³ side-store accommodation and m_view constant-sharing

### (a) The strongest charge

**Charge 9.1 — "One regime, corpus and loops" is false as a universal, and the accommodation is where it broke.** Sweep #2's claim (CLAUDE.md; `docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md` §9 status block: "the loop's chains satisfy the polarity gate natively (§8.1 discharged)") is now contradicted by the loops' own code: `agon_evolution._apply_decay` (src/agon_evolution.py:885–893) falls back to `_structural_retract_atom` (src/agon_evolution.py:800–852) — raw `without_element` surgery, `derivation: []`, no Dau rule. The defense that "a corpus chain carrying it would rightly be REFUSED by the gate" (commit 7299392; docstring lines 810–816) *concedes* that the gate's jurisdiction was narrowed from "corpus and loops" to "corpus" at exactly the moment the loops needed the exemption. The one-regime claim survives only by redefining the regime's extent.

**Charge 9.2 — the root cause is a correspondence failure, and it was accommodated rather than fixed.** F2¹³ is not an ERA boundary case. Its trigger, per the docstring itself (src/agon_evolution.py:819–836), is that the EGIF round-trip is **not structure-preserving on resident Ms**: `generate_egif` → `parse_egif` merges a constant shared by two cells into ONE vertex "homed in whichever cell's atom the parser meets first," breaking per-cell vertex privacy. Concrete construction:

```
M (drawn):   ~[  ~[ (dog "Q") ]   ~[ (cat "Q") ]   ~[ ] ]     — two "Q" vertices
M (carried): ~[  ~[ (dog "Q") … ] ~[ (cat —) ] ~[ ] ]         — ONE "Q" vertex,
             homed in the dog cell, its line of identity crossing into the cat cell
```

These are **not `same_graph`** (different vertex counts) — and `same_graph` is the project's own structural authority. This is the central invariant — linear and graphical form denoting the same mathematical object — failing on the residence shape at the segment-carry boundary (src/live_runner.py:393, `tools/run_vault_v0.py:117`). The sprint fixed the downstream symptom (the ERA refusal that crashed RUN 13) with unlicensed surgery, and left the invariant breach standing — indeed `world_scroll.m_view`'s docstring *accommodates* it as a feature (src/world_scroll.py:170–179, the shells-before-edges two-pass copy exists to keep reading a merged M "total").

**Charge 9.3 — the merge is, by the gate's own criterion, an unrecorded M-change hidden in the seam between chains.** `m_view(pre-carry M)` and `m_view(parse(generate(M)))` are not `same_graph`. The tripwire (`tests/test_corpus_polarity_discipline.py:212–233`) demands that any step where `m_view` before ≠ after carry an acknowledged act. But the segment carry is not a step: the old chain is dropped, the new chain is seeded from the parsed text (src/live_runner.py:393 onward). The discipline's four checks (shape inventory, act/derivation annotations, peel recomputation, tripwire) all quantify over *steps within a chain*; the carry lives *between* chains and is invisible to all four. An M-normalization happens once per segment, acknowledged nowhere. (Defense available: atom-level content — `sheet_atom_keys` — is preserved, and EGIF constants co-denote. But the discipline's own recognition doctrine is "structural, never annotational" (src/world_scroll.py:21–24); by that standard, M changed.)

**Charge 9.4 — the fallback's actual scope exceeds its advertisement.** `_structural_retract_atom` is documented as "erase one atom" but matches over **all of `g.E` with no area filter** (src/agon_evolution.py:838–842) and erases *every* match. The licensed path it replaces (`retract_from_m`, src/world_scroll.py:427: `if area not in scroll.cell_ids: continue`) is cell-scoped; the fallback is not. Constructions where this bites, all with `derivation: []`:

- **A standing ground denial**: M carries a cell holding `~[ (rel "A" "B") ]` (a sourced denial — the `ContradictionAgent`/wiki-membrane shape) plus the standing atom `(rel "A" "B")` in another cell. Fallback decay of the standing atom also erases the label-identical atom *inside the denial cut*, leaving `~[ ]` — **⊥ standing inside a cell** — and the peel never notices (the oracle reads sheet-level atoms only, src/domain_oracle.py:340–347; the materializer skips non-Horn cuts), so M becomes silently inconsistent.
- **An entertained exhibit**: the iterated M′ copies inside an episode exhibit are label-identical to the cell atoms; a fallback decay guts the exhibit so `_find_exhibit` (src/world_scroll.py:476–510) can no longer discharge or abandon it.

### (b) The most damaging charge the docs did not anticipate

**The gate verifies annotations, not executions.** `test_m_changes_are_explicit_rule_licensed_steps` (tests/test_corpus_polarity_discipline.py:124–157) reads `p.get("derivation")` — parameters written by the step-recorder. It never replays a derivation or checks that `to_state` is obtainable from `from_state` by the claimed rules. Contrast: PEEL verdicts *are* recomputed (:268–284). The in-process asserts (`derivation_seen == expected`, src/m_steps.py:193, 261, 300…) protect only chains built through `m_steps` *in the recording process*. Consequence: the F2¹³ docstring's defense is true only against an honest writer — a chain that performed structural surgery and *wrote* `derivation: ["ERA"]` passes every gate check (the tripwire is satisfied because the act label is present). The accommodation normalizes exactly the practice — wrapping a rule-refused transform in act/derivation params — whose honesty the gate cannot check. No document in this cluster states this limit; `m_steps.py`'s module docstring says the opposite in spirit ("earned at record time — … the parameters say what happened, they never merely assert it" — true at record time, unverifiable at gate time).

### (c) The author's best answer from the record

The record's answer is commit 7299392 plus the two docstrings: the fallback is *named* (F2¹³), *honest* (`derivation: []`, a visible `fallback_note`), *quarantined* (gitignored runs side-store; no mechanical promotion path from `runs/` to `tomos/` exists — verified), and the refusal that would meet it at the corpus "would be the gate working." **Verdict: ANSWERS the narrow question** (derivation-[] is refusable, and the debt-recording house practice was followed — this is the project at its best) **but DEFLECTS the wide ones**: (i) the round-trip non-isomorphism is treated as an accommodation target, not an invariant breach; (ii) the seam-change (9.3) is nowhere acknowledged; (iii) the annotation-depth of the gate (b) is nowhere acknowledged; (iv) later segments' recorded PEELs run against a state shaped by the unlicensed move — the verdicts recompute (they are earned *relative to their state*), but the state's pedigree is laundered by the chain drop.

### (d) Disposal

1. **Proof/fix obligation (the root):** *Proposition:* for every resident M, `parse_egif(generate_egif(M))` is `same_graph` to M. Currently **false**. The mechanical fix is to carry M structurally — the EGI JSON is already total and the checkpoint already persists state (`LiveRunConfig.state_path`); carry `to_dict(egi)` instead of EGIF text. That makes F2¹³'s trigger unreachable and the fallback deletable. Alternatively, concede with the exact sentence: *"The carried M is the resident form only up to EGIF constant-unification, which re-homes shared constants across cells and voids per-cell vertex privacy; every segment carry is an unrecorded structural normalization of M, invisible to the polarity gate's step-scoped checks."*
2. **Runnable test (gate depth):** extend the gate with derivation replay — for each `m_enlargement`/`m_retraction` step, re-execute `enlarge_m`/`retract_from_m` from `from_state` and assert `same_graph` with `to_state` (the peel-recomputation pattern, applied to derivations). Deterministic, offline, closes (b).
3. **Runnable test (fallback overreach):** resident M with a denial cell `~[ (rel "A" "B") ]` + standing atom `(rel "A" "B")`; force the fallback (round-trip the M first); assert the denial's interior survives decay. Currently fails by inspection of src/agon_evolution.py:838–852.

### (e) Confidence the claim falls as stated

- "One regime, corpus and loops" as a universal: **0.85**.
- "The F2¹³ accommodation is a lawful, fully-contained boundary case": **0.6** (containment is real for promotion; not real for seam-normalization, fallback overreach, or gate depth).
- "Side-store content can reach a *corpus-recorded* verdict undetected": **0.35** (no mechanical path found; requires a dishonest or careless promotion — but (b) shows the gate would not catch that promotion).

---

## Suspect 10 — The A3 scale claim: "quoted content licenses nothing"

### What the three tiers actually quantify over (verified)

- **Tier 1** (tests/test_second_order_conservativity.py:69–104): universal over the corpus — but only for the **unused** case (byte-identical re-save; allowlist of bearers). Proves invisibility, not opacity.
- **Tier 2** (:118–171): the licensing heart — tested on **two inline graphs of 1–2 atoms with one quotation each**, plus `swan_third_tense` (3 V / 3 E / 6 cuts / **1 quotation**) and `forcing_forces` (9 V / 6 E / 7 cuts / **3 quotations**) — measured from the corpus JSON. Maximum ever tested: 3 quotation cells, 9 vertices.
- **Tier 3** (:179–229): three exemplar chains replay; **one** INS refusal; linear-generator refusal.

So: the A3 argument is **structural at the six-rule level** — `_refuse_quotation_boundary` is called in all seven rule classes (src/formal_transformation_rules.py:333, 494, 610, 803, 1116, 1335, 1671 — DC+, DC−, INS, ERA, IT+, IT−, HeavyDot; verified) — and **structurally safe for the area-scoped interpreters** (the oracle reads sheet-level atoms, src/domain_oracle.py:346; quoted ink is inside a cut). But it is **enumerative at the interpreter level** (exactly three explicit opacity checks exist: src/semantic_game.py:263, src/model_materialization.py:254, src/modal_query.py:242; nothing enforces the check on a new consumer; `theory_query`/`m_render`/`agon_evolution`/`live_runner` carry none and are safe only by accident of area-scoping) — and, as demonstrated below, **false at the closure layer and in Chapter 16**.

### (a) The strongest charge — with the executed counterexample

**Charge 10.1 — DEMONSTRATED: a licensed erasure of ordinary host ink demotes a quotation to an asserted negation.** Executed in this examination against the real corpus:

```
egi   = swan_third_tense.current            # the blessed exemplar
sel   = the (superseded "M_swan_law" "Nox") edge   — ordinary host ink, positive area
ErasureRule.apply_transformation(ctx with raw selection {edge}) →
    success: True
    quotation after: {}                     # the map entry silently pruned
    oval survives as plain cut: True        # the quoted withdrawn law, now a NEGATION
    quoting name erased: True
```

Mechanism, by inspection: the guard (src/formal_transformation_rules.py:803–810) inspects `context.selected_subgraph` **before** the for-erasure closure expansion (:818–836); the expansion pulls in the private argument vertex — which *is* the quoting name (`quote_existing_name` explicitly supports "a constant argument of a host relation," src/quotation_overlay.py:400–404, and the swan exemplar is built that way); `apply_transformation` erases the **expanded** set without re-running the guard; `_rebuild_graph` then prunes the quotation entry because the name vanished while the cut survived (`if k in c_ids and v in v_ids`, src/formal_transformation_rules.py:101–107). Result: the oval — Peirce's mention — becomes a first-order negation. Had the quoted ink been Horn-shaped at the landing level (exactly the vault's banked-answer shape), the materializer would **fire it as a law**.

The blessed path (`proof_authoring.apply_rule` → `rule_interaction`) refuses this — but only because `rule_interaction` happens to pre-expand the selection to its closure *before* the rule sees it (src/rule_interaction.py:505, 753), so the guard meets the expanded set. The invariant survives on that path by an **ordering accident of one caller**, not by construction. Direct constructors of `TransformationContext` exist in-tree: `endoporeutic_game.py` (the Agon hot-seat engine), `ligature_manipulation_rules.py`, `vertex_splitting_merging_rules.py`, `proof_serializer.py`, `chapter17_soundness_evaluation.py`.

**Charge 10.2 — Chapter 16 strips the layer wholesale.** `ligature_manipulation_rules.py` and `vertex_splitting_merging_rules.py` build `RelationalGraphWithCuts(...)` raw (six construction sites) with **zero** quotation/sort forwarding — the maps default to empty. Any ligature manipulation of a quotation-bearing graph silently drops both maps; every surviving oval demotes to a negation. This is the exact "historical kwarg-omission wart" `_rebuild_graph`'s docstring says was repaired for the six rules (src/formal_transformation_rules.py:75–79) — still live, one chapter over, in a **protected core module**.

**Charge 10.3 — the structural-vs-enumerative question, answered:** A3 is structural *where the guard is in the loop*, enumerative everywhere else, and the "any scale by construction" reading fails at the two seams above. A vault-scale counterexample therefore does not need exotic size — it needs exactly the shapes V2a.2 will mass-produce: quoting names wired as arguments of host `asserted` atoms, at even depth, in a decaying M.

**Charge 10.4 — the vault-scale composition is untested and already broken in three provable places** (`docs/superpowers/specs/2026-07-17-vault-cycle-design.md:379–395`, authorized 2026-07-19):

1. **Carry crash:** `run_vault_v0.py:117` and `live_runner.py:393/417/518/556` carry M as `generate_egif(...)`; `refuse_second_order_in_linear_form` (src/second_order_limits.py) raises on **any** non-empty sort or quotation. The first banked quoted cell kills the run at the first segment boundary — or must be projected, which silently un-banks the answer. The A3 gate's own tier-3 test (`test_linear_generators_refuse_the_bearing_graph`) proves this collision.
2. **Decay × banking:** a banked `(asserted "author" ⌜q⌝)` atom is a standing cell-level fact, hence decay-eligible. The licensed ERA refuses (whole-unit guard — the quoting name is the atom's private vertex); the F2¹³ fallback then erases the edge and tries `without_element` on the orphaned quoting name, which the core **raises on** (src/egi_core_dau.py:1283–1287) — an uncaught exception inside `pc.apply_derived` — or, through the 10.1 bypass, demotes the oval to an asserted negation of the author's prose. Crash or corruption; no third outcome as built.
3. **Gate vocabulary:** scribing a quotation into a resident M changes `m_view` (the maps are carried, src/world_scroll.py:237–265, and `same_graph` distinguishes quoted twins — `test_second_order_core`), but `"quotation"` ∉ `M_ACTS` (tests/test_corpus_polarity_discipline.py:117–118) — the tripwire **refuses the very act V2a.2 authorizes**. No BANK/QUOTE M-act exists in `m_steps.py`.

### (b) The most damaging charge the docs did not anticipate

The guard-ordering bypass (10.1). The record treats opacity as settled by the rule-level refusals ("every opacity refusal" enumerated in `test_rules_second_order` TestOpacity — all of which submit the apparatus *in the selection*); nothing anticipates the for-erasure **closure** reaching the apparatus from outside the selection, nor that the guard's protection depends on which caller expands the closure. Second, unanticipated: Chapter 16 (10.2) — the B-min sweep audited the six rules and the interpreters, and never mentions the ligature/vertex rule modules.

### (c) The author's best answer from the record

The record can say: A3 was ratified as a **corpus-level gate**, delivered exactly as promised; the three tiers are real, adversarial at their scale, and self-checking (the bearer allowlist); the B-full prep already concedes reach is bounded ("B-full widens ν — 52 modules / 252 sites," memory record) — an implicit admission the layer's coverage is enumerative; and V2a.2's deferral was "named, not silently dropped." **Verdict: ANSWERS at the tested scale and on the blessed path; DEFLECTS on the construction claim** — "Dau remains the guarantor, made testable" is quietly stronger than what was built, since the guarantor's own erasure closure defeats the guard; and authorizing V2a.2 without a composition audit against the carry, the decay, and the gate vocabulary is precisely the untested assumption the mandate suspected.

### (d) Disposal

1. **Immediate fix + regression test (the bypass):** in `ErasureRule.check_preconditions`, re-run `_refuse_quotation_boundary` on `analysis.closed_subgraph` (and audit `DeiterationRule`'s closure path identically); regression-pin the executed construction — direct-engine ERA of the `superseded` atom on `swan_third_tense` must refuse. Small, provable by inspection afterward.
2. **Make the demotion unrepresentable (the elegant form):** change `_rebuild_graph`'s pruning so a quotation entry is dropped only when **both** cut and name are gone; exactly one surviving raises. Then no reconstruction path — six rules, Ch. 16 once routed through `_rebuild_graph`, or any future rule — can demote a mention silently. *Proposition to prove by inspection afterward:* "no engine-reachable transformation yields a graph in which a formerly-flagged cut survives unflagged."
3. **Chapter 16 obligation:** route `ligature_manipulation_rules` / `vertex_splitting_merging_rules` reconstructions through `_rebuild_graph`, or have them refuse quotation-bearing graphs outright (the `second_order_limits` idiom); add a test that a ligature move on a quotation-bearing graph either preserves the maps or refuses loudly.
4. **Generative A3 tier-2′ (scale):** deterministic property test — N quotation cells (N ≈ 50), shared constants between quoted and asserted ink, quoting names both isolated and host-wired, over all four verdict-computers (`evaluate`, `materialize_egi`, `entails`, `scribes_relation`): verdicts equal the projection's. Offline, seeded.
5. **Composition tests before V2a.2 builds:** (i) one banked quoted cell through one `live_runner` segment carry — pin the intended behavior (structural carry per Suspect 9 disposal 1 dissolves this too); (ii) decay over a banked cell — pin refusal-not-crash; (iii) extend `M_ACTS`/`m_steps` with the banking act so the tripwire licenses what the spec authorizes.
6. **Concession sentence if deferred:** *"A3 is proven for the corpus as it stands and for the blessed application path; it is not yet a guarantee by construction — a direct engine call or a Chapter-16 ligature move can demote a mention to an assertion, and the banking V2a.2 authorizes cannot yet survive the loop that would carry it."*

### (e) Confidence the claim falls as stated

**0.9** that "A3 guarantees quoted content licenses nothing" falls *as a scale/construction claim* — 10.1 is executed, 10.2 is by-inspection, 10.4(1) is proven by the gate's own test. Stated honestly: at the *tested* scale on the *blessed* path the claim held every probe; and one of the three vault-scale failure modes (the carry) fails **loud**, which is the house's preferred failure.

---

## Additional suspects found in this cluster

- **Suspect 9-bis (annotation-deep gate)** — filed at 9(b); deserves independent standing since it conditions every other "the gate re-asserts it" defense in §10.3 of M_RESIDENCE (ruling (b) enactments 2 and 3 are annotation-checks plus one genuine recomputation). Disposal: 9(d)2.
- **Suspect 10-bis (Chapter 16 map-stripping)** — filed at 10.2; independently a **protected-core** correctness issue (those modules also predate the rho/alphabet repair and likely still drop constants metadata).
- **Minor, named:** `quote_step` records `derivation: ["with_quotation_binding"]` (src/quotation_overlay.py:446) — a *constructor* wearing the derivation vocabulary of the rules. Harmless today (QUOTE is neutral) but it erodes the reader's ability to trust that a `derivation` list names licensed moves; recommend a distinct key (`construction:`) for non-rule transforms.

**Method note:** every claim above is grounded in code read this session or executed against the engine (`ErasureRule` bypass run live on `swan_third_tense`; the `apply_rule` path's refusal confirmed as the contrast case). No panel briefs were seen.
