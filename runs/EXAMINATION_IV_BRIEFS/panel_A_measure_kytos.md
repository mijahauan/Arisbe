# Panel A brief — The Measure, the Kytos, and the Quantitative Frontier
(verbatim from the independent panel, 2026-07-19)

**Panel:** a measurement theorist / psychometrician, joined by a complexity scientist. Charge: refute, not flatter. Sources read in full; no other panel's brief seen.

**Preliminary note on the house standard.** Examination III's form is: strongest charge steelmanned; the author's best answer tested for ANSWER vs DEFLECT; verdict with an exact amendment; what is lost and what is kept. We follow it, adding the mandated disposal paths (proof obligation / runnable experiment / concession) and per-suspect confidence that the claim **falls as stated**.

**One convention.** "MEASURE" = `docs/THE_MEASURE_OF_KNOWLEDGE.md`; "KYTOS" = `docs/THE_KYTOS.md`; line numbers are current file lines.

---

## Suspect 1 — The measure's completeness, and K1 as an instrument

### (a) The strongest charge, steelmanned

MEASURE §2 presents "**The measure — four components**" and §6 decision 2 records it "**RATIFIED 2026-07-17** … All four components now instrumented." Two distinct failures hide in that sentence.

**1a. K1 is not an instrument; it is two instruments that do not join.** The K1 row (MEASURE §2) reads: "`PredictionLedger` (hits/misses/abstains) **× the severity term** (`attention_economy.Want.severity`) — the ledger half BUILT, the weighting a small join." Examination of the code shows the join is not "small"; it is **undefined and currently impossible**:

- `PredictionLedger` (`src/resolving_membrane.py:88–120`) scores `ScoreEntry(round_idx, claim_egif, predicted, happened, result)`; its aggregates are `hits`, `misses`, `net_score = hits − misses`, `accuracy`. **No severity field exists anywhere in the ledger schema.**
- `Want.severity` (`src/attention_economy.py:17–27`) lives on *probe candidates*, keyed by `(kind, key)`, and is consumed only by `_score` (line 74–77) to order *choices*. **There is no foreign key joining a `ScoreEntry` to a `Want`** — different modules, different identifiers (`claim_egif` vs `(kind, key)`), no shared reference.
- The "×" in the doc has no defined aggregation semantics. Severity-weighted *how*? Σ severity over hits minus Σ over misses? A weighted proper scoring rule? Nothing is stated, nowhere in docs or code.

So the ratified sentence "all four components now instrumented" is **false for K1 as defined** ("severity-weighted track record"): what is instrumented is an *unweighted* track record plus a severity term used for a different purpose (attention allocation, not scoring).

**1b. Even if joined, severity is an unvalidated scale.** The severity values in the codebase are hand-set constants: `1.0` default (`attention_economy.py:26`), `4.0` for frontier wants (line 214), `8.0` for journal probes (`arithmetic_world.py:130`), `3.0/2.0/1.0` in `oracle_notes.py:110–175`. These are ordinal judgments treated as ratio-scale multipliers. A measurement theorist's objection is standard (Stevens; Krantz–Luce–Suppes representational measurement): a statistic formed by multiplying an ordinal quantity into a count is **not meaningful** — its orderings are not invariant under admissible (monotone) rescalings of severity. Was journal-severity 8.0 or 5.0? Nothing in the record can say, and the resulting K1 ordering of knowledge-items would differ. No reliability study, no inter-rater agreement (there is one rater), no anchoring procedure, no invariance property claimed or proven.

**1c. No sufficiency argument exists, and the construct's own seed refutes sufficiency.** MEASURE §1 quotes the author's definition: knowledge exists when someone "reliably does something (**thinks, speaks, acts**) that works." The measure's four components cover forecasting (K1), survival under revision (K2), derivational compression (K3), and re-delivery (K4) — the *assertoric* fragment only. The author's own companion doc concedes "the missing fifth = the **action arm**" (BOOTSTRAP, and MEMORY.md's summary). So by the doc's own seed definition, **K1–K4 has a content-validity gap it never names**: successful *action* is in the construct and absent from the measure. Further candidate components a psychometrician would demand be argued in or out, none discussed: **calibration** (net = hits − misses is a crude score; no proper scoring rule, so boldness and accuracy are conflated), **internal coherence of M** (nothing in K1–K4 detects a mutually contradictory M), **coverage/addressability** (the "addressability gap" is named in `m_render`'s vocabulary_overlap but is not a K), **evidential independence** (N hits from one source vs N sources score identically), **fecundity** (Peirce's own economy-of-research criterion — surprising, given the project's provenance).

**1d. The components are not shown to be distinct.** K4 (use) and K2 (durability) are mechanically coupled — decay erases the unused, and stickiness reads `stuck=None` on decay (`agon_metalearning.py:162–198`); K1's record accrues only through use. No discriminant analysis, no factor structure, not even a verbal argument that the four are not two.

### (b) The most damaging charge the docs did NOT anticipate

Two, both documentary:

**The honesty-ledger inflation.** KYTOS §5, two days after MEASURE, lists under **Built**: "K1–K4 instruments incl. modal K2" (line 99–100). MEASURE §2's own table says the K1 weighting is *not* built ("the ledger half BUILT, the weighting a small join"). The project's flagship honesty device — the built/evidenced/conjectured ledger — **overstates K1's status within 48 hours of its ratification**. This is exactly the drift the author's mandate names, occurring inside the instrument meant to prevent it.

**The K3 instrument measures extension, not compression.** `KnowledgeCompression.ratio = derived ÷ (horn_laws + skipped_laws)` (`model_materialization.py:445–475`). This is *mean derivational yield per law*, and it is **confounded with domain size**: one law `man(x) → mortal(x)` over 2 men gives ratio 2.0 (the test's own case, `test_model_materialization.py:214–222`); the identical law over 200 men gives 200.0. Two Ms with the same laws and different extents differ 100× in "compression." No information-theoretic compression measure behaves this way (a real one would be something like derived/(explicit+derived), or MDL — description-length saved). Calling K3 "compression" and then teaching it ("teach generative rules … measure a lesson by its materialization ratio," MEASURE §5) transmits the confound into pedagogy: a lesson about a big domain "compresses" better than an identical lesson about a small one. The docs nowhere flag this. (It also poisons Suspect 12 — see there.)

### (c) The author's best answer, fairly constructed

*On 1a/1b:* "The measure was ratified as a *design*; the K1 row says in plain words the weighting is a join yet to be made. Severity already earned its keep operationally — S1 HELD: severity-ordering refuted Fermat at round 6 where FIFO/scatter never did (BOOTSTRAP §3 build record). The constants are admittedly conventional, but the measure is guarded: never truth, never a target, never a scalar over agents — it claims warranted reliability in context, not psychometric validity." *On 1c:* "The action arm is named as missing in the companion doc; the measure covers what is built, in the correspondence-not-truth register." *On 1d/K3:* "K3 was authorized as a ~ten-line first cut; the non-Horn-in-denominator clause shows the earned-record discipline was applied to its design."

**Verdict on the answer: DEFLECTS on 1a/1b, half-ANSWERS on 1c, DEFLECTS on the K3 confound.** The S1 result validates severity as an *attention* heuristic — a choice-ordering — not as a *scoring* weight; those are different constructs (an exploration bonus vs an evidential weight), and transporting validation from one to the other is precisely the untested assumption under examination. "Guarded, not psychometric" is a category retreat: the doc calls K1–K4 "the measure" and ratifies it; a measure whose first component has no defined formula is not a measure with modest ambitions, it is a name. The action-arm answer is honest but lives in a different doc; MEASURE §2 itself never carries the caveat. Nothing in the record answers the K3 confound at all.

### (d) Disposal path

- **D1.1 (K1, formal + concession pair).** Proof obligation: *state K1's formula* — propose: K1(item) = Σ_hits w(sev) − Σ_misses w(sev) under a **declared proper scoring rule**, with the proposition to prove: *K1's induced ordering over knowledge-items is invariant under any monotone rescaling of the severity anchors, OR the anchors are given an operational definition (severity = the measured refutation-power of the test class, e.g. prior probability of failure under the null feed) that makes them ratio-scaled.* Until one disjunct is discharged, MEASURE §2's K1 row must carry: **"K1 is a design: no join between severity and the ledger exists in code, and no aggregation formula has been stated; the S1 result validates severity as an attention heuristic only."** KYTOS §5 must move K1 from **Built** to **Partially evidenced**.
- **D1.2 (K1 join impossibility, runnable, deterministic, offline).** In a new test: build two `PredictionLedger`s from `ResolvingFeed` fixtures (reuse `test_resolving_membrane.py` items) with identical hit/miss counts but where one theory's hits came from severity-8-class claims and the other's from severity-1-class claims; assert `select_best` and every ledger property return identical rankings/values. **Sustains** the charge (current instruments are severity-blind) trivially — the point of running it is to pin the gap as a red test that the eventual join must flip. **Refutes** only if someone finds an existing code path that already weights — none exists.
- **D1.3 (K3 confound, runnable, ~15 lines).** `materialization_ratio(parse_egif('(man "a1") … (man "aN") ~[ (man *x) ~[ (mortal x) ] ]'))` for N ∈ {2, 20, 200}. **Sustains**: ratio ≈ N (measures extension). **Refutes**: ratio invariant in N. (It will sustain; the disposal is then either rename — "K3 = derivational yield per law," dropping the word *compression* — or re-derive: K3′ = derived/(explicit+derived) ∈ [0,1), and re-run the three existing tests.)
- **D1.4 (completeness, concession).** MEASURE §2 should carry: **"Sufficiency is not claimed: the four components cover the assertoric fragment of the seed definition; 'acts that work' awaits the action arm, and calibration, coherence, coverage, and evidential independence are named non-components until argued in or out."**

### (e) Confidence the claim falls as stated

**0.85** for "all four components now instrumented" / K1-as-instrument (documentary; the code is unambiguous). **0.7** for the completeness claim (the doc ratifies "the measure" without a sufficiency argument while its own seed names an unmeasured clause). **0.9** that K3-as-"compression" falls (the confound is arithmetic).

---

## Suspect 2 — Fractal transportability: "one ledger shape at every level"

### (a) The strongest charge, steelmanned

MEASURE §3: "each level's knowledge is measured by the *same ledger shape* (**K1–K4 transport across scales**)." KYTOS §2 tabulates seven levels; §5 concedes levels 5–7 are asserted. The steelmanned skeptic grants the concession and attacks what remains: **transportability is not established at levels 1–4 either.** "Instrumented at levels 1–4" (KYTOS §5) conflates *some instrument existing at each level* with *the same measure transporting*. Audit the 4×7 component-by-level matrix against code:

- **Atom (level 1):** K4 yes (`UsageLedger`, atom keys); K2 partially (decay/`mark_decayed_atoms`); K1 — an atom has no `PredictionLedger`; K3 — meaningless for a single atom (a lawless M "reads 0.0").
- **Law (level 2):** K2 yes (stickiness, `_stickiness` lines 162–198); K1 — no per-law severity-weighted record; K3 — the ratio is per-*model*, not per-law (a single `KnowledgeCompression` for all of M); K4 — laws are decayed only "when a name's *last* atom goes" (CLAUDE.md, live_runner) — a derivative, not a ledger.
- **Model (level 3):** the only level with three-plus components genuinely computed on the same object (ledger, stickiness-aggregate, K3, |M|-bounded use).
- **Mechanism (level 4):** KYTOS §5 itself: "the mechanism level has stick-rates but no K3/K4" — and no K1 either (`MechanismPrinciple` has `count`, `stick_rate`, `durable`; no severity, no forecast record).

So of 16 cells claimed instrumented, roughly **six** have code paths, and only level 3 approaches a full vector. "One ledger shape transports" is instantiated **once**.

### (b) The most damaging charge the docs did NOT anticipate

**The transport claim is homonymy dressed as self-similarity.** KYTOS §2's table maps "membrane" to: re-delivery (a counter), instances (data), run sources (APIs), runs-it-reads (files), the world, the author's vault, and other Arisbes. A genuine fractal/renormalization claim requires a **stated level-transition map** — a construction taking a level-n kytos to a level-n+1 kytos preserving the six anatomical components and the measure's semantics — under which "K2 at level 2" and "K2 at level 4" are *the same functional* evaluated at different scales. No such map is defined anywhere; what exists is a table of analogies. Without it, cross-level statements ("a teacher's model of the learner is level-4 knowledge," MEASURE §5) are unfalsifiable typology. Worse, the measure's own semantics **break under the only transport actually attempted**: stickiness at the law level is decay-aware (`stuck=None` on decay — carefully engineered, `agon_metalearning.py:83–96`), but at the mechanism level "superseded principles" (KYTOS §2's decay column) have no analogous None-vs-False discipline — a superseded `MechanismPrinciple` is simply recomputed away, unrecorded. The very distinction the project fought hardest to get right at level 2 (decay is not refutation) **does not transport** to level 4 in the current code. That is direct evidence against "one ledger shape suffices," found exactly where the doc invited attack but with a mechanism the doc did not name.

Secondary: **level 5's ledger is exempt from its own measure.** The Project level's "membrane" is the run-log discipline (Pⁿ/Fⁿ) — but priors carry no severity weights, findings no decay, designs no K3. The doc uses the run-log as *evidence for* the fractal reading while the run-log itself instantiates none of K1–K4. And the closure argument ("the loop closes when that model becomes an M inside Arisbe," MEASURE §3) concedes levels 4–5 are "held **outside** the system" — i.e., the fractal's upper levels are presently *the author and the assistant*, which is an observation about the humans, not the system.

### (c) The author's best answer, fairly constructed

"The doc flags exactly this: 'a skeptic should attack exactly here — flagged for the standing examination' (KYTOS §5). 'Partially evidenced' is the claim, and modal K2 (built 2026-07-19) is transport in progress — the *same* durability construct re-read over the DAG. The fractal is a research program, not a theorem; the A3 conservativity gate is a real, tested cross-level guarantee (no level corrupts the one beneath), which is more than analogy."

**Verdict: ANSWERS in part — and the part it answers must be recorded.** The self-flag is genuine and correctly scoped *for levels 5–7*; to that extent the charge is against over-reading, not the text. But the flag says "instrumented at levels 1–4," and (a)/(b) show that sub-claim is itself inflated: full-vector instrumentation exists at one level, and the one engineered transport (decay-awareness) demonstrably fails to reach level 4. The A3 gate is real but guards *conservativity of quotation*, not *measurement invariance* — citing it here is a DEFLECT (right property, wrong construct).

### (d) Disposal path

- **D2.1 (formal).** Proposition to be proven: *there exists a map T taking a level-n kytos (membrane, M, loop, horizon, budget, decay) to level n+1 such that K1–K4 computed at level n+1 equal the same functionals composed with T* — at minimum for the pair (law → mechanism), where both sides have code. Even a rigorous statement of T for one adjacent pair would convert the table from metaphor to claim.
- **D2.2 (runnable, deterministic, offline).** From the existing `_swan_run()` fixture (`test_agon_metalearning.py`): compute the full K-vector for (i) the swan law and (ii) the `reliable_source` mechanism *through the same code paths*. Expected result: (i) yields K2 only with K1/K3/K4 raising or undefined; (ii) yields stick_rate only. **Sustains**: the vector does not transport (cells empty by construction, not by accident). **Refutes**: someone exhibits the four calls at both levels. The sustained outcome converts KYTOS §5's line to the honest form below.
- **D2.3 (concession sentence, owed now regardless).** KYTOS §5 "Partially evidenced" should read: **"measure transportability — the full K-vector is computed only at the model level; levels 1, 2, and 4 each carry one to two components; the decay-vs-refutation distinction, load-bearing at the law level, has no mechanism-level counterpart; levels 5–7 asserted."**

### (e) Confidence the claim falls as stated

**0.75.** "As stated" = "instrumented at levels 1–4, one ledger shape transports." The self-flag saves the doc from the naive charge; the 4×7 audit and the decay-transport failure defeat the stated residue. (Confidence the *research program* is doomed: far lower, ~0.3 — not the question asked.)

---

## Suspect 7 — Poise as the observable of the rate ratios

### (a) The strongest charge, steelmanned

The claim appears twice, escalating: vault spec ("four rates … govern the regime; ttl and the budget are the two rate-matching knobs … **poise is the observable of their ratios**," `2026-07-17-vault-cycle-design.md` lines 181–184) and KYTOS §1 ("four rates (world change, processing, answering, decay) fix the regime, and **poise is their observable**") and §3 ("the balance of engagement, settlement, and absorption **that the rate ratios produce**").

The steelman: this is a **physics-shaped claim with no physics behind it**. "X is the observable of Y" asserts a functional dependence: vary Y, and X responds systematically. Examine the instrument: `poise_report` (`agon_metalearning.py:606–642`) reads engagement (revising rounds/rounds), thrash (inconsistent dispositions per situation), and stumble counts from an **episode trace**. It takes no rate as input. No function anywhere maps (world-change rate, processing rate, answer rate, decay rate) → poise reading. No run has varied the rate ratios and recorded poise's response — KYTOS §5's "Evidenced" row offers "rate-determinism (ttl tuned per membrane across RUNS 1–12…)," which evidences that *rates matter to run outcomes*, not that *poise is their observable*. The claim is a definitional decree: an unmeasured coupling between two instruments (knobs on one side, a trace-classifier on the other) asserted as an observable relation. And the instrument itself disclaims the authority the doctrine borrows from it: "The thresholds (`window`, `max_stumbles`) **belong to the observer** — the reading is perspectival and comparative, never absolute" (docstring, lines 606–612). An observer-relative binary classification with free parameters is not "the observable" of anything; at most it is *a* reading, one of many, and which one the rate ratios "produce" depends on two knobs the theory doesn't fix.

### (b) The most damaging charge the docs did NOT anticipate

**The instrument contradicts the doctrine on its central case.** The doctrine (section comment, `agon_metalearning.py:517–537`): "Competence, on this reading, is that **stumbles keep arriving AND keep being absorbed**: a run with no stumbles and no engagement is not poised, it is dead." But `_window_reading` (lines 578–593) marks a window **failed toward "thrash"** whenever `stumbles > max_stumbles` (default **1**) — *even with zero thrash situations, even when every stumble was cleanly absorbed*. Two absorbed stumbles in eight rounds — the doctrine's own picture of competence — reads **failure: "thrash"**, a label naming an event that did not occur. The live-stream variant is worse: `poise_from_digests` cannot compute thrash at all ("thrash is not computable from a digest," line 645–651) and the shipped test **pins the conflation as correct behavior**: a 25-round segment with 5 new_facts, 2 retractions, 1 challenge and 1 branch — stumbles arriving and being disposed — asserts `failure == "thrash"` (`test_agon_metalearning.py:274–284`). So there are **two instruments under one name measuring different constructs** (trace-poise with thrash; digest-poise without), no convergent-validity check between them, and both punish exactly what the doctrine praises once the arrival rate of irritation exceeds 1 per window. Under the rate-ratio framing this is fatal: a *higher world-change rate* mechanically produces more stumbles per window, so the instrument reads high-tempo health as pathology — poise readings are **confounded with the very rate they are claimed to observe**, in the wrong direction.

Secondary, unflagged: no invariance study. `poised_fraction` is a tumbling-window statistic; nothing reports how classifications move under window ∈ {4, 8, 16} or max_stumbles ∈ {1, 2, 3}. The flagship exemplar (`test_swan…poised`, line 233–241) is a **single window of three rounds** with `window=3` chosen to fit — n = 1.

### (c) The author's best answer, fairly constructed

"Poise was always hedged: 'no absolute frame,' 'an observable *shadow*,' 'perspectival by construction, comparative across ablation arms.' The section comment says exactly that; the Goodhart guard ('never a target') shows we know it's soft. `max_stumbles` is a knob precisely so an observer expecting a hot membrane can raise it. And the rate claim is a design commitment — the four rates are what a run *has*; poise is what we *watch* — not a fitted law."

**Verdict: DEFLECTS.** The hedges live in the code comment; the doctrine docs promoted the shadow to "**the** observable" that the rate ratios "**produce**" — a definite description and a causal verb, twice, in the two documents that graduate to the book's spine. "It's a knob" concedes the charge: if the reading flips with an observer knob, the rate ratios do not produce it; the observer does. And no answer exists for the thrash-label contradiction — it is a plain bug-or-doctrine-error pinned by a test.

### (d) Disposal path

- **D7.1 (runnable — the linkage experiment the claim owes; deterministic, offline).** Pre-register, then run: the arithmetic world (`arithmetic_world.ProbeDirectedFeed`, deterministic) or `ReplaySource` fixtures through `live_runner` across a grid — ttl ∈ {2, 5, 10, ∞} × feed tempo (items per segment) ∈ {low, high} — computing `poise_from_digests` and `poise_report` per arm. **Pre-registered expectation under the doctrine:** poised_fraction varies monotonically with the decay/world-change ratio, with rigidity at one pole (ttl ∞, feed exhausted) and thrash at the other (ttl ≪ tempo). **Sustains the doctrine** if the monotone response appears robustly under window ∈ {4, 8, 16}; **falls** if readings are flat, non-monotone, or knob-dominated (classification flips under threshold sweep exceed flips under rate sweep). This is feasible today with existing modules and no network.
- **D7.2 (repair-or-concede, the contradiction).** Either repair `_window_reading` so "thrash" requires `thrash_situations > 0` (absorbed stumbles beyond `max_stumbles` becoming a third, honestly-named reading — e.g. "storm: absorbing at rate" — and re-pin the digest test), or the docs carry: **"The instrument reads any window with more than `max_stumbles` irritations as failed, whatever their disposal; poise readings therefore penalize high-tempo membranes, and digest-poise and trace-poise are different instruments."**
- **D7.3 (concession sentence for the doctrine claim, owed unless D7.1 sustains).** KYTOS §1/§3 and the vault spec: replace "poise is the observable of their ratios / that the rate ratios produce" with **"poise is *a* trace-reading we conjecture responds to the rate ratios; the linkage is unmeasured (threshold-relative, and untested against any rate variation)."** Move poise's rate-linkage from KYTOS's implicit doctrine into §5 **Conjectured**.

### (e) Confidence the claim falls as stated

**0.8.** "As stated" — a definite, produced observable of the four rates — is contradicted by the instrument's inputs (no rates), its free parameters, its internal contradiction on high-tempo absorption, and the absence of any linkage run. The survivable transformed form (a candidate observable, pending D7.1) is genuinely promising — which is precisely why the overstated form should be retired before it hardens.

---

## Suspect 12 — The West scaling conjecture: label without a design

### (a) The strongest charge, steelmanned

KYTOS §4 is honestly labeled ("Conjecture until measured — see §5"), and §5 repeats it. **The charge is therefore against the one operative claim §4 does make:** "Empirical questions **the run corpus can already ask**, none yet answered." Steelmanned: *the run corpus cannot ask them, and as currently instrumented the questions are either unanswerable or answer themselves.*

1. **The system homeostatically clamps the regressor.** Every live run bounds |M| at ≈ttl by design — "disuse-decay bounds |M| … per-round cost/memory/disk stay flat" (live_runner doctrine); RUN 1's watched finding was "|M| held at ≈ttl." A scaling exponent requires the size variable to range over decades; the runs pin it to a design constant (≈25–250 across RUNS 1–13 — barely one decade, achieved by *changing the clamp*, i.e., the knob, not the growth). Fitting a power law across runs whose sizes were set by hand measures the hand. Power-law inference methodology (Clauset–Shalizi–Newman 2009) needs orders of magnitude and likelihood-ratio alternatives; n ≈ 13 runs over <1.5 decades cannot distinguish power law from exponential, lognormal, or nothing.
2. **The named exponent is arithmetic, not biology.** "The K3 exponent (derived atoms vs explicit atoms across runs)": derived is mechanically coupled to explicit through the Datalog chase, so the exponent is a **theorem of the rule shapes in M**, not an empirical discovery — a unary subsumption chain gives derived ≈ c·explicit (exponent 1); transitive closure over a k-clique gives ~explicit² (exponent 2). West's exponents are interesting *because* they are not derivable from the definitions of the measured quantities; this one is. Measuring it "discovers" the arity structure of the laws the runs happened to admit.
3. **The analogy lacks its engine.** West's ¾-power laws are derived from optimized space-filling transport networks; superlinear city scaling from interaction density. KYTOS §4 maps "deliverance throughput as metabolism, the membrane hierarchy as the distribution network" but states **no optimization principle and no interaction mechanism** from which any exponent would follow. Without a mechanism, "discoverable scaling relations" is an invitation to curve-fit residues of design choices.

### (b) The most damaging charge the docs did NOT anticipate

**The conjecture's headline dichotomy is unfalsifiable as posed.** "Whether open-membraned kytē scale superlinearly (city-shaped) while closed configurations stagnate (company-shaped, mortal)" — but *closed-proposer saturation* is already cited in §5 as **evidence** ("the halting duals … the closed-proposer saturations"), and open-membrane growth is *bounded by ttl by design*. So both arms of the dichotomy are **guaranteed by construction**: closed feeds exhaust (the pool is finite — `CorpusProposer` replays a pool), and open feeds are clamped. Any "measurement" would confirm the conjecture with probability 1 while measuring only the plumbing. The doc's honesty label ("conjecture until measured") does not anticipate that, under current instrumentation, *measurement cannot fail* — which is worse than being unmeasured: it is pre-confirmed. A conjecture that cannot lose is not on the quantitative frontier; it is décor.

### (c) The author's best answer, fairly constructed

"§4 is one paragraph, flagged twice as conjecture, listed under 'Conjectured, honestly' with an explicit invitation to attack. Naming a frontier is not claiming a result; West is a *pointer* ('the author's *Scale* pointer'), and the honest form — questions the corpus can ask, none answered — is exactly the pre-registration discipline's first step: name the question before the prior."

**Verdict: ANSWERS the naive charge — the label is honest, and to that extent this suspect is "already conceded; the charge is against over-reading."** But it DEFLECTS on the two specific counts: (i) "the run corpus **can already ask**" is a capability claim, and it is false as shown (clamped regressor, pre-confirmed dichotomy, coupled exponent); (ii) the house discipline the answer appeals to — Pⁿ/Fⁿ pre-registration — is precisely what §4 *lacks*: no priors, no refutation conditions, no design. The mandate's phrase fits exactly: it needs "a pre-registered measurement design, not just its label."

### (d) Disposal path

- **D12.1 (runnable, deterministic, offline — the null-model experiment that must precede any run-corpus fit).** Construct synthetic Ms (pure `parse_egif` + `materialize_egi`, no network): (i) unary subsumption ladder over N individuals, (ii) transitive relation over a chain of N, (iii) over a clique of N, for N ∈ {10¹, 10², 10³, 10⁴} (one-shot materialization; feasible — the chase is semi-naive). Fit log(derived) vs log(explicit) per shape. **Pre-registered null:** measured exponents equal the analytically predicted ones (1, ~1, ~2). **Sustains the charge** (the "K3 exponent" is chase arithmetic) if they match — expected. The surviving empirical question is then honestly restated: scaling of quantities **not** mechanically coupled — e.g., question-yield vs |M|, docket size vs deliverance rate — measured on runs where ttl is *swept* as the independent variable, with the CSN feasibility bar (≥2.5 decades or don't fit) written into the prior.
- **D12.2 (the design obligation).** Before any corpus fit: a pre-registered P-entry in the run-log stating (a) the two variables, (b) why they are not coupled by construction, (c) the range requirement, (d) the alternative models (exponential, lognormal) and the likelihood-ratio criterion, (e) what outcome *refutes* (exponent CI including the design-predicted null, or model non-selection). Without (b) and (e) no fit may be reported as a finding.
- **D12.3 (concession sentence, owed now).** KYTOS §4: replace "Empirical questions the run corpus can already ask" with **"Empirical questions a *future, designed* run corpus could ask — today's runs clamp |M| by ttl and close over finite pools, so both poles of the city/company dichotomy hold by construction, and the K3 exponent is analytically determined by rule shape; a measurement design (range, nulls, alternatives) is owed before any fit counts."**

### (e) Confidence the claim falls as stated

**0.65** — split verdict: the *conjecture qua conjecture* is honestly labeled and does not fall (charge against over-reading, ~0.2); the operative sub-claim "the run corpus can already ask" falls at ~0.85; blended for the suspect as assigned: 0.65.

---

## Added Suspect A-a — The vector-not-scalar guard is doctrine without a tripwire

### (a) Strongest charge

MEASURE §2 guard 3 / §6 decision 3 ratify: components "are never aggregated into a single number ranking *inquirers*" — "Doubt 4's enforcement clause inside the measure." KYTOS §3 extends it: "no kytos is reduced to a rank of its inhabitant." But: (i) `select_best` (`resolving_membrane.py:150`) **is** a scalar ranking (by `net_score`) — permitted over *theories*, but (ii) KYTOS §2 introduces the **Person-model** level (the-author-according-to-Arisbe), and **nothing in the code distinguishes a person-model from any other M**. `select_best` over two person-model ledgers is a two-line call that would rank persons-as-modeled by a scalar — the worth-ladder rebuilt by arithmetic, exactly what decision 3 forbids. The project's pattern elsewhere is *guards get gates* (the polarity discipline got a standing parametrized test; §3.3 got a runtime attestation). The measure's flagship ethical guard got a sentence.

### (b) Unanticipated charge

The agent/model boundary the guard depends on is **undefined at level 6 by the doctrine's own construction**: the kytos table makes the author's model a first-class M, and V2a's vault loop is *feeding* it. The guard's category-fact ("competence ≠ worth") is not representable in the type system that would have to enforce it — an M carries no "is-an-inhabitant-model" bit.

### (c) Author's best answer

"The guard is doctrine, like 'never a target' — some rules bind conduct, not code; and `select_best` ranks theories' *records in context*, which Doubt 4 expressly allows (warrant = in-context competence)." **Partially ANSWERS** — Doubt 4 does allow record-comparison of *claims and models*; but the record shows this project does not leave load-bearing rules as conduct when they can be gates (polarity, §3.3, A3). The absence of a tripwire here is a design inconsistency, not a philosophy.

### (d) Disposal

Runnable obligation: a standing test in the spirit of `test_corpus_polarity_discipline.py` — any UoD whose kind/annotation marks it a person-model (the marking must be added; V2a.2's "quoted attributed cell" is the natural carrier) is refused by `select_best`-class comparators, or at minimum the comparison emits the counted refusal the house style demands. Or the concession: **"The vector-not-scalar guard is unenforced doctrine: nothing in code prevents scalar ranking of person-models; enforcement awaits a person-model marking."**

### (e) Confidence: **0.7** (as a claim that the guard is *enforced within the measure* — it is not; as pure doctrine it stands).

---

## Added Suspect A-b — Modal K2 is vacuous on the corpus that exists

### (a) Strongest charge

MEASURE §3 (sense 2) and KYTOS §5 present modal K2 (`modal_query.durability_modality`, lines 271–300) as a built instrument reading durability "across the branching futures." But branches arise **only** from panel disagreement under `LLMAgonothetes.branch_votes` — "the mechanical panel has no such hook, so the closed loop stays linear" (CLAUDE.md, `agon_llm`). On a linear chain with one leaf, □ ⇔ ◇ over leaves: `durability_modality` collapses to "did the last state scribe it" — plain K2, no modal content. The mechanical loops, all thirteen runs, and the whole non-LLM corpus are linear; the instrument's discriminative range ("possible" ≠ "necessary") is reachable only on the handful of hand-built or key-gated LLM exemplars. "Modal K2 BUILT" is true as code and near-empty as measurement: an instrument whose middle category cannot fire on the data it is offered.

### (b) Unanticipated

Neither doc notes the dependency: modal K2's informativeness is conditional on a branching *source* (disagreeing panels), so citing it as fractal-sense-2 evidence ("the fractal in time") imports the LLM stage's availability into the measure's evidence base without saying so.

### (c) Author's best answer

"An instrument may lawfully await its data; `possible_and_necessary` exists as a real branching exemplar, and the tests cover both readings." **ANSWERS in part** — legitimate, if stated. It is not stated.

### (d) Disposal

Concession sentence in MEASURE §3: **"Modal K2 discriminates only on branched histories; all mechanical-loop histories are linear, where it reduces to plain K2 — its evidence base today is the hand-built branching exemplars."** Cheap sustaining check (offline): assert over the corpus's saved chains that every non-exemplar chain yields `durability_modality ∈ {"necessary","absent"}` only.

### (e) Confidence: **0.6** (the claim "built" is true; the fall is of its implied evidential weight).

---

## Summary table

| # | Suspect | Verdict sought | Confidence falls as stated |
|---|---|---|---|
| 1 | K1–K4 complete; K1 instrumented | K1 has no formula, no join, unvalidated scale; sufficiency unargued; K3 measures extension not compression; KYTOS §5 inflates K1 to "Built" | 0.85 (K1) / 0.7 (completeness) / 0.9 (K3-as-compression) |
| 2 | One ledger shape transports (levels 1–4 instrumented) | Full vector exists at one level; the decay-vs-refutation discipline fails to transport to level 4; no transition map stated; levels 5–7 honestly conceded already | 0.75 |
| 7 | Poise is the observable the rate ratios produce | No rate enters the instrument; observer-owned thresholds; two instruments under one name; the instrument punishes the doctrine's own picture of competence (>1 absorbed stumble ⇒ "thrash") | 0.8 |
| 12 | West conjecture (as "the corpus can already ask") | Honestly labeled conjecture (concession recorded); but the regressor is ttl-clamped, the dichotomy pre-confirmed by construction, and the K3 exponent is chase arithmetic — no pre-registered design exists | 0.65 |
| A-a | Vector-not-scalar guard enforced within the measure | Unenforced; person-models are unmarked Ms; `select_best` is two lines from the forbidden ranking | 0.7 |
| A-b | Modal K2 as fractal evidence | Vacuous on all linear (i.e., nearly all actual) histories; dependency unstated | 0.6 |

**Where the docs were already honest, said plainly:** KYTOS §5's flags on levels 5–7 and on the scaling conjecture are genuine and correctly scoped — those two charges, in their naive forms, are against over-reading, not the text. Every other charge above targets text or code the flags do not cover, and each carries a deterministic, offline disposal path executable in this repo (D1.2, D1.3, D2.2, D7.1, D7.2, D12.1) or an exact concession sentence.

*Filed for Examination IV by the measurement-theory/complexity panel, 2026-07-19. No other panel's brief was seen.*
