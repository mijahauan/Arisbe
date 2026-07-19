# Panel C brief — Testimony, Self-Knowledge, and the Oracle Loop
(verbatim from the independent panel, 2026-07-19)

**Examiners:** a philosopher of testimony and self-knowledge; a privacy/consent-minded security reviewer. Charge: refute, not flatter. House standard applied: Examination III's form (`docs/ADVERSARIAL_EXAMINATION.md:1019–1129`) — strongest charge, unanticipated charge, does the record answer or deflect, exact disposal, confidence-that-it-falls-as-stated.

**Sources read in full:** `docs/superpowers/specs/2026-07-17-vault-cycle-design.md`; `src/oracle_notes.py`; `src/vault_world.py`; `tools/run_vault_v0.py`; `runs/RUN_13_LOG.md`; `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` §3–§5; `src/attention_economy.py` (verification greps).

---

## Suspect 4 — "Answers are ground truth about the author"

Spec text: *"Even the author's errors are veridical data: `(asserted "author" ⌜P⌝)` stays true-about-the-author regardless of P's fate. The author's answers are **ground truth about the author by construction**"* (spec:46–49); P4¹³: *"the author as ground truth about the author"* (RUN_13_LOG:23–26).

**(a) Strongest charge.** The doctrine equivocates between two roles an answer plays, and the guarantee covers only the one the code doesn't use. Role 1 (datum): "the author wrote string S at time t" — veridical under the quotation reading, granted. Role 2 (verdict): the answer as *gold label* that scores Arisbe's forecasts (K1, via `score`, `oracle_notes.py:447–457`) and adjudicates the loop's provenance verdicts (P4¹³). In Role 2 the answer is used **unquoted**, as a fact about the world-the-author-is — and there deception, self-misunderstanding (cryptomnesia is the textbook failure for exactly the authored-vs-collected question `_provenance_candidates` asks, `oracle_notes.py:95–112`), performativity, and drift all bite with full force. A miss in the ledger is scored as Arisbe's error; it may be the author's. The construction guarantees veridicality of the *assertion event*; K1 and P4¹³ spend it as veridicality of the *content*.

**(b) Unanticipated charges.**
1. **"By construction" is not yet constructed.** The quoted-attributed-cell machinery that grounds the guarantee is explicitly deferred: *"Deferred to V2a.2: banking an answered forecast into M as a quoted attributed cell… V2a.1 only banks answers in the run's side-store"* (spec:379–383). Today an answer is a raw string in `outcomes.jsonl` (`oracle_notes.py:516–521`) — no quotation, no A3 opacity, no attribution machinery. The doctrine's tense is wrong: the sentence should read *will be* ground truth by construction.
2. **No authentication of the asserter.** `parse_note` attributes every `**A:**` edit to "the author" (`oracle_notes.py:395–444`), but nothing verifies who edited the note. An Obsidian vault is a synced, plugin-hosting, multi-device folder; a sync-conflict artifact, a plugin, or another household member editing `Arisbe/Questions-*.md` becomes "the author's" ground truth. The attribution is an assumption about filesystem custody, nowhere stated as one.
3. **Ground truth never expires.** `asked_ever` (`oracle_notes.py:544–550`) suppresses a question *forever, in any run* ("regardless of how it was answered" — its own docstring). An answer given once in 2026 stands as the permanent fact; the model of a person is barred from ever re-checking it. Drift is thereby unmeasurable *by design*: K2's decay clock applies to observed facts, never to ledger outcomes. For a doctrine whose K2 half is "what survives decay is trait" (spec:50–54), permanently undecayable answers are an internal contradiction.
4. **Internal tension with ruling 5.** The spec's own ruling — *"Provenance is inquiry, not precondition… hypotheses carrying evidence, disposed through the loop like any claim"* (spec:32–36) — is contradicted by P4¹³, which makes the author's provenance judgment the *precondition* (the scoring standard) rather than one more hypothesis with evidence.

**(c) Does the record answer?** Partially answers, partially deflects. The thesis "carry no warrant about the world except what testing earns" (spec:48–49) genuinely anticipates the deception/error case *at the level of M's world-component* — that is an answer, and a good one. The "reflexive stream from day one" (spec:153–156) converts performativity from confound into object of study — a legitimate Peircean move, also an answer. But nothing in the record addresses the Role-2 use: `score` and P4¹³ are not covered by the quotation defense, and no author thesis touches drift or authentication. On those the record is silent, not deflecting — it simply hasn't seen the problem.

**(d) Disposal.**
- *Doc concession (exact sentence):* "An answer is ground truth about the **act of answering**, never about its content; where an answer is used as a scoring standard (K1 hits, P4¹³ agreement) it is a **fallible label** — revisable, re-askable, and datable — not ground truth."
- *Code obligation:* an expiry/re-ask parameter on `asked_ever` (e.g. re-eligible after N notes or on model-side contrary evidence), so drift is at least *observable*; a `provenance` field on outcome rows recording which device/mtime produced the edit.
- *Pre-registered criterion RUN 13 could measure:* re-ask one early question verbatim after ≥2 segments' gap; a changed answer is recorded as a **drift datum**, not overwritten — testable offline against the fixture today.

**(e) Confidence it falls as stated:** **0.75.** The narrow quotation-reading survives; the sentence as written ("ground truth by construction"), given that the construction is deferred and the code's actual uses are Role-2, falls.

---

## Suspect 5 — "Predict, never pre-empt"

Spec text: *"**predict, never pre-empt** (the new guard: the author-model may forecast the author's proposals but never pre-judge them — the method-gate stays blind to identity, including the modeled author's)"* (spec:55–59).

**(a) Strongest charge.** The guard has **no enforcement mechanism, no test, and no violation-detector**. Grep the tree: "pre-empt" occurs in this spec and nowhere in `src/` as a mechanism (verified; the only src hit is an unrelated UI comment, `ergasterion.html:2227`). What makes the method-gate "blind to identity" today is that **no identity channel exists** — proposals in `agon_evolution` carry no author field. Blindness-by-absence is not a guard; it is the absence of the thing the guard would guard. The moment V2a.2 banks `(asserted "author" ⌜P⌝)` cells into M — authorized 2026-07-19 (spec:389–395) — M itself becomes an identity channel readable by every M-scanning agent (`ContradictionAgent`, the Challenger, `attention_brief`), and nothing then distinguishes "forecasting the author" from "conditioning dispositions on the author-model." The guard is a property of a document, not of the architecture.

**(b) Unanticipated charges.**
1. **Pre-emption already happens one level down — at question selection.** The guard is framed for proposals, but the oracle loop *already* uses its author-model to decide what the author gets asked: `severity` ordering (`select_within_budget`, `oracle_notes.py:195–217`), `asked_ever` suppression, and the doctrine's own decline/silence decay ("a question-kind repeatedly yielding silence decays as a kind", spec:150–153). Choosing what never to ask *is* a pre-emption of the dialogue — the author-model forecloses lines of the author's own self-account. The guard as scoped ("proposals") does not cover the one interaction surface that exists.
2. **Forecast leakage steers the very behavior forecast.** The question templates embed the forecast as the *first-listed option* ("Is `X` collected from elsewhere, or your own writing?" — forecast `"collected"`, `oracle_notes.py:103–111`; "a genuine journal, or a fragment/copy" — forecast `"fragment"`, :127–136). Priming the predicted answer is a mild pre-emption of the answer itself, and it inflates K1. No guard, doc or code, addresses question-wording neutrality.
3. **The intended future enforcement is real but unwired for this use.** B-min's interpreter opacity (peel/materializer/modal skip quotation ovals — tested in `test_quotation_overlay.py`, per CLAUDE.md) and the A3 conservativity gate are exactly the right mechanism for "quoted author-content licenses nothing." But no test anywhere asserts the *guard's specific content*: that a disposition of a proposal is invariant to the presence of author-model cells in M.

**(c) Does the record answer?** The record is honest about staging in general (rung 2 "needs its own ethics-and-etiquette design before any build; nothing below rung 2 acts outside Arisbe's own polls", BOOTSTRAP:198–204) — but note the oracle **already acts outside Arisbe's own polls**: `_run_oracle` writes into the author's real vault (`run_vault_v0.py:143, 203`), acknowledged in the spec as "the first true action-arm act" (spec:137–139). So the rung-2 fence and the V2a build sit in visible tension: the first outward act shipped *before* the ethics pass that rung 2 was said to require, on the strength of consent alone. The five theses do not mention the guard at all. Verdict: **deflects by scoping** — the guard is stated where it cannot yet be violated, and the surface where model-conditioned selection already operates (questions) is outside its stated scope.

**(d) Disposal.**
- *Proof obligation (deterministic, offline, runnable now):* `test_predict_never_preempt.py` — build a fixture M twice, identical except one copy carries quoted `(asserted "author" ⌜P⌝)` cells; run the mechanical panel's disposition of a fixed proposal against both; assert byte-identical disposition and verdict. This turns the guard into a standing gate the way `test_second_order_conservativity.py` turned A3 into one.
- *Scope amendment (exact sentence):* "Pre-emption includes **selection**: what the author-model suppresses from being asked is recorded (counted, inspectable), so foreclosed question-lines are data, not silence."
- *Question-neutrality rider:* alternate or randomize (seeded) the option order in two-option templates; deterministic, one-line change.

**(e) Confidence it falls as stated:** **0.85** — as a *guard*, it is presently a promise; the architecture-level blindness it cites is an accident of the missing channel, and the shipped oracle already performs model-conditioned selection the guard's wording doesn't cover.

---

## Suspect 8 — The interlocutor criterion's operationalization (P2¹³)

Spec text: thesis 5 (spec:187–201); P2¹³: *"the docket generates questions about the author that the author rates non-trivial at better than **a stated base rate** (author-judged sample per segment)"* (RUN_13_LOG:18–20).

**(a) Strongest charge.** P2¹³ is **unfalsifiable as registered**: the "stated base rate" is never stated — not in the spec, not in the run log. A prior that defers its own threshold to a future statement is not pre-registered; it is a promissory note wearing pre-registration's clothes. Any positive-sounding outcome can be declared a pass by choosing the rate afterwards — exactly the failure mode the Pⁿ discipline exists to prevent, and the discipline the project elsewhere applies scrupulously (S1–S5 had numbers; BOOTSTRAP:218–228).

**(b) Unanticipated charges.**
1. **The "docket read aloud" is not wired to the docket.** Thesis 5's operationalization is *"the docket read aloud with its reasons"* (spec:190–191). But `candidates_from_run(world, horizon, known_laws, labels)` (`oracle_notes.py:179–189`) never touches the docket or the `AttentionEconomy` — the questions come from **four hardcoded template sources** (Clippings provenance, multi-journal, two largest horizon items, one standing reflective), and the "*Why asked*" reasons are fixed template strings, not the economy's actual severity/yield state. `wants_from_docket` exists (`attention_economy.py:200`) and is unused by the oracle. So what P2¹³ would measure is the author's rating of **template instantiations**, and even a clean pass would not evidence that *the docket* speaks meaningfully — the proxy is measuring a different mechanism than the criterion names. (`known_laws` is even accepted and explicitly "reserved, not wired", `oracle_notes.py:77–78`.)
2. **No measurement instrument exists.** There is no ratings capture anywhere — no `**R:**` line, no ratings file, no field in the ledger (verified by grep). P2¹³'s data can currently only be collected out-of-band, unblinded, by the interested party.
3. **Proxy failure would be invisible.** The plausible failure: the author — judge, subject, and project-principal at once, whose engagement thesis 4 says depends on his model of Arisbe — rates templated questions "non-trivial" because *anything about one's own 50-year journal is salient*. Personal salience mimics question quality perfectly. With no comparator arm (e.g., the same templates instantiated on *randomly chosen* notes instead of docket-chosen ones), no blinding, and no stated rate, the instruments could not distinguish "Arisbe wants to know" from "Arisbe fills a form with my file paths." The criterion would read as passed while the thing it proxies (meaningful wanting) is entirely absent.
4. **Doctrine-vs-code contradiction inside the same thesis-set.** Thesis 3: *"wants age but persist; silence lowers priority, **never deletes**"* (spec:176–178). Code: `asked_ever` filtering (`run_vault_v0.py:190`) **permanently deletes** every asked question from all future candidate lists, ignored or not; the docstring says so in terms ("drop… regardless of how it was answered", `oracle_notes.py:545–549`). The system *is* structurally incapable of impatience — because it is structurally incapable of persistence.

**(c) Does the record answer?** The record is unusually honest at the criterion's top: "meaningfully is P2¹³'s bar; equal stays inside Doubt 4's rail" (spec:191–193) correctly scopes the interlocutor criterion as a proxy, and the Rorty gloss deliberately deflates "equal" to solidarity-standing. So the *criterion as doctrine* is well-flagged — the charge targets over-reading it, per the house rule. But the *operationalization* neither answers nor deflects: it is missing (no rate, no instrument, no docket wiring). P2¹³ as it stands is the bar for "meaningfully" and the bar has no height.

**(d) Disposal.**
- *Pre-registration repair (must precede the first real questions note):* amend RUN_13_LOG with a number and a comparator, e.g.: "P2¹³ operational form: per segment, the note carries N docket-selected and N template-random questions in seeded random order, unlabeled; the author marks each `**R:** trivial|non-trivial`; pass iff docket-selected non-trivial rate exceeds random-instantiated by ≥25 points over ≥2 segments." All parts deterministic/offline except the author's marks — which is the point.
- *Code obligation:* (i) route candidates through `wants_from_docket` so the criterion measures its named object; (ii) add `**R:**` parsing to `parse_note` + a `ratings.jsonl`; (iii) reconcile thesis 3 with `asked_ever` (age/decay, not permanent suppression) or amend thesis 3.
- *Failure-mode canary:* if the author rates ≥90% of everything non-trivial (ceiling effect), the criterion is declared uninformative for that segment — pre-register that too.

**(e) Confidence:** **0.9** that P2¹³ *as registered* cannot do the work the interlocutor criterion assigns it (missing rate + missing instrument + wrong mechanism measured). The interlocutor criterion itself, as scoped doctrine, survives; the charge is against its operationalization, and there it lands.

---

## Added Suspect C-a — The seal that doesn't seal (security reviewer)

**(a) Charge.** `seal(forecast) = SHA256(forecast)` — **no salt, no nonce** (`oracle_notes.py:65–68`, verified by grep). The forecast vocabulary is tiny and public: `"collected"`, `"fragment"`, `"unknown"`, `"reconstructed"` are string literals in the source (`:110, :135, :157, :175`). An unsalted hash of a low-entropy value is a dictionary-checkable commitment: `sha256("collected")` is a constant anyone — including the author, in ten seconds — can compute. The hiding property the "seal-then-reveal" design claims (*"only its SHA-256 commitment appears… the seal is checkable, not promised"*, spec:146–150) **fails exactly for the forecasts in use**. The forecast is effectively plaintext-visible at ask time; ask-time and answer-time are *not* held apart; a K1 "hit" may be an author (consciously or not) echoing a forecast he could read. Binding holds (the hash in the author-custody note pins the ledger); hiding does not.

**(b) Unanticipated rider.** The reveal is also **never verified in code**: `build_reveals` reprints `forecast_plain` and `forecast_hash` from the mutable gitignored ledger (`oracle_notes.py:560–581`) without recomputing the hash or comparing it to the original note's printed seal. A rewritten ledger row (plaintext + recomputed hash) would reveal cleanly; tamper-evidence exists only if the author manually diffs hashes across notes. "Checkable, not promised" is accurate — but nothing checks.

**(c) Record.** The spec anticipated neither point. Silence, not deflection.

**(d) Disposal.** One-line fix + one test, offline: `seal(forecast, nonce)` with a per-question random nonce stored beside the plaintext in `forecasts.jsonl`, revealed with it; `build_reveals` recomputes `sha256(nonce‖plaintext)` and marks a mismatch `verdict: "seal-broken"`. Test: doctored ledger row → `seal-broken`.

**(e) Confidence:** **0.95** (the hiding failure is arithmetic, not interpretation).

---

## Added Suspect C-b — "Declined/silence are first-class" is mostly a label

**(a) Charge.** The spec claims decline/silence protection as a design feature (spec:151–156). In code: (i) `declined` requires the answer to be *exactly* `declined` case-insensitively (`oracle_notes.py:427`) — "Declined.", "I'd rather not", "pass" are recorded as **answers**, verbatim, in `outcomes.jsonl` and printed back in the next note's Reveals: the refusal's own wording becomes retained data, the opposite of what a refusal asks; (ii) the promised differential mechanics (declined → want decays; silence → ages; kind-level noisy-TV-inward decay) are **not built** — `asked_ever` suppresses everything identically, and no decline/silence signal reaches `AttentionEconomy` (verified: no such wiring). "First-class" currently means "given a status string."

**(b) Unanticipated.** A decline is itself banked as author-data (`record_outcome_once(qid,"declined",...)`) and, under V2a.2's authorization, is on the path into M. Declining a question about X still teaches the model "author declines questions about X" — meta-data the author was never told a refusal generates.

**(c) Record.** Anticipates the categories, not the mechanics. The build records honestly list what V2a.1 defers, but this specific gap (decline mechanics unimplemented while the doctrine claims them) is unnamed.

**(d) Disposal.** Concession sentence for the spec: "In V2a.1 declined/ignored are *recorded statuses only*; the differential decay the doctrine describes is unbuilt, and any `**A:**` text other than the bare word `declined` is treated as an answer." Plus: accept a small refusal synonym set or a `**A:** —` convention; add a test that a decline's text never appears in a subsequent note.

**(e) Confidence:** **0.8**.

---

## Added Suspect C-c — Consent laundering through the oracle (security reviewer)

**(a) Charge.** The consent boundary is *reading*: `People/`, `Kith_Kin/`, `Household/` are metadata-only (spec:17–20). But `attachment_items` registers **every** non-md file vault-wide to the horizon (`vault_world.py:301–321` — no folder exclusion; verified no `People`-aware code exists outside the docstring), and `_horizon_candidates` asks about the **two largest** horizon items by size (`oracle_notes.py:140–159`) — PDFs are the likely winners, and the real vault has 73 (spec:21–23). So the oracle can write, into `Arisbe/`, "What is `People/<third-party-file>.pdf`? One line is plenty" — **soliciting from the author, as answer-text, content about third parties that the reader is barred from reading directly**. The answer enters the ledger (and, post-V2a.2, M). The consent scope survives in the reader and is bypassed in the asker.

**(b) Unanticipated.** Entirely — the spec's third-party wrinkle governs V1's API reading only; no document considers the question channel as a content channel.

**(c) Record.** Silence.

**(d) Disposal.** One filter + one test, offline: horizon items whose ref's top dir is in the metadata-only set are excluded from `_horizon_candidates` (they remain on the horizon — counted, never dropped); test: a fixture `People/x.pdf` never yields a question candidate. Doc sentence: "Consent boundaries bind the *question generator* as they bind the reader: Arisbe never asks the author to voice what it may not read."

**(e) Confidence:** **0.85**.

---

## Added Suspect C-d — The inspection asymmetry of the person-model

**(a) Charge.** Arisbe builds a model of the author the author cannot inspect in the vocabulary it is built in: M lives as EGIF in gitignored run artifacts; what the author sees is ≤5 questions plus `conjectures_section` — which glosses **only `known_laws`** (`oracle_notes.py:318–332`), i.e., admitted generalizations, never the hundreds of ground atoms, provenance priors, or decayed/retained distinctions that constitute "the author according to Arisbe." Thesis 4 makes the author's engagement depend on "their model of Arisbe" and says Arisbe earns answers "by showing its conjectures" (spec:178–182) — but the shown surface is a strict, thin projection of the held model. A testimony-ethics point, not a custody point: the *subject* of a dossier has a claim to read it that a *custodian* framing (everything is local and gitignored — true, and verified in the build record, spec:262–270) does not discharge, since reading raw EGIF chains is not a real capacity of the modeled person.

**(b) Unanticipated rider.** The digest discipline (numbers-only stdout, `run_vault_v0.py:10–18`) — a privacy virtue — *worsens* legibility: even the author's own console shows counts, never claims.

**(c) Record.** Partially answers: conjectures-in-English is a genuine, built gesture at legibility, and the audit-lens/eg_to_english machinery exists elsewhere in the codebase for exactly this. Deflects insofar as "custody local-first" (spec:55–57) is offered where the issue is legibility, not possession.

**(d) Disposal.** A runnable obligation, mostly existing parts: an `## About-you` section (or standalone `Arisbe/Model-<date>.md`) rendering M's author-facts through `eg_to_english`, decade counts, and the current decayed/live split — the model shown *to its subject* in his own language, every cycle. Pre-registerable as a RUN 13 rider: the author confirms or corrects ≥1 model claim per segment (which would also feed Suspect 4's re-ask instrument).

**(e) Confidence:** **0.6** (the asymmetry is real but partially mitigated and easily repaired; falls as an omission, not a doctrine error).

---

## Summary table

| # | Suspect | Verdict sought | Conf. |
|---|---------|----------------|-------|
| 4 | Answers = ground truth | Falls as stated: veridical only of the *act*; code (`score`, P4¹³) spends it on *content*; "by construction" not yet constructed; no authentication; ground truth never expires | 0.75 |
| 5 | Predict-never-pre-empt | Falls as a *guard*: promise in a doc; blindness is absence-of-channel; selection-level pre-emption already live; forecast priming in templates; write the invariance test | 0.85 |
| 8 | P2¹³ / interlocutor proxy | Operationalization falls: base rate never stated, no rating instrument, oracle not wired to the docket it claims to read aloud; thesis-3 vs `asked_ever` contradiction | 0.90 |
| C-a | The seal | Hiding fails (unsalted hash of a 4-word vocabulary); reveal never verified in code | 0.95 |
| C-b | Declined/silence first-class | Mechanics unbuilt; refusal text retained as data; exact-match fragility | 0.80 |
| C-c | Consent laundering | Third-party folder boundary binds the reader, not the question generator | 0.85 |
| C-d | Inspection asymmetry | Model of the subject illegible to the subject; conjectures gloss is a thin projection | 0.60 |

**One structural observation across the cluster:** the project's own best discipline — pre-registration with numbers, adversarial custody verification, the m_view tripwire — was applied rigorously to *data flow* in this sprint and almost not at all to the *dialogical* claims (theses 3 and 5, the guard, P2¹³). Every disposal above is the existing discipline pointed at the layer it skipped; none requires new doctrine, and suspects 5, C-a, C-b, and C-c each reduce to a small deterministic test this repo could carry before RUN 13's first real questions note is written.
