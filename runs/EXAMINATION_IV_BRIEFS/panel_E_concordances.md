# Panel E brief — The Concordance Glosses as Intellectual History
(verbatim from the independent panel, 2026-07-19)

**Examiner:** independent, historian-of-ideas discipline. **Charge:** refute not flatter; separate "the gloss misstates the source" (a real charge) from "a fair analogy honestly marked" (not a charge — the house standard, per the docs' own repeated hedging: *"concordances, not lineage claims"*, *"assistant's readings, flagged"*, *"conjecture until measured"*).

**House-standard note up front.** This cluster is unusually well-defended by its own framing. CONTRIBUTION_AND_PRIOR_ART §"Concordances" opens by declaring these *"concordances — programs that arrived at structurally similar answers from independent starting points — not lineage claims and not prior art"* and closes with a confidence note that *"no claim is made that any of these programs influenced Arisbe's design."* That framing disposes of most "X anticipated Y" charges before they land. My charges therefore concentrate where the gloss **misstates what the source actually says or claims** — which the concordance frame does *not* license — rather than where it draws a marked analogy.

The one genuinely damaging finding is factual, not interpretive: **the Conway's Life "bounded plane" claim is wrong, and it is load-bearing** ("the decisive structural difference," elevated to "doctrine").

---

## (v-a) Conway's Game of Life — "the plane is bounded" — THE headline charge

**Doc text charged.** AUTOMATED_MODEL_DEVELOPMENT.md §1 (lines 66–69): *"**The decisive structural difference is the plane.** Conway's Life runs on a **bounded** plane: the boundary is itself a constraint — it makes the system finite and shapes the [emergence]… the sheet of assertion is **unbounded**."* Summarized into CONTRIBUTION_AND_PRIOR_ART §"Concordances" (Cellular automata entry): *"'the decisive structural difference is the plane' — Life's plane is **bounded** and its boundary shapes the emergence, while the sheet of assertion is **unbounded**."* And THE_KYTOS §3 leans on the same contrast for its halting-duals ("Conway's still-life").

**(a) Strongest charge.** This is a factual error about the object. Conway's Game of Life is canonically defined on the **infinite** two-dimensional integer lattice ℤ² — patterns are permitted to grow without bound (gliders, spacefills, Gosper's gun). *Bounded* grids (fixed-edge or toroidal) are **implementation approximations** forced by finite memory, explicitly noted as departures from the theoretical object. So the sentence "Conway's Life runs on a bounded plane: … it makes the system finite" mis-describes the canonical automaton; both Life and the sheet of assertion live on unbounded planes. The "decisive structural difference" as stated does not exist.

**(b) The damaging part the doc did not anticipate.** The boundedness contrast is not merely wrong — it is **unnecessary**, and its wrongness discredits an argument that was sound on other grounds. The *real* Life/Agon differences the same section states — Life is **monotone-deterministic under a fixed local rule** (a neighbour-count fires; "outcomes are determined, not negotiable") whereas the Agon's disposition is **negotiated and selected from outside** — fully carry the load. Life is "closed" because its **rule** is fixed and its dynamics deterministic, *not* because its plane has an edge. By resting the punchline on the plane, the doc invented a false empirical difference where a true structural one was already in hand.

**(c) Author's answer from the record.** DEFLECTS at best. Nothing in the record corrects it; the error is repeated verbatim across three docs and hardened into "doctrine" (THE_KYTOS §2 calls the Life differences "doctrine"). The surrounding true claims (monotone vs. negotiated) do not rescue the specific plane sentence — they replace it.

**(d) Disposal — TEXTUAL FIX (mandatory).** Replace the plane contrast. Corrected sentence:

> "The decisive structural difference is not the plane — Conway's Life is canonically defined on the *infinite* lattice ℤ², as unbounded as the sheet of assertion. The difference is **closure of the dynamics**: Life advances by a *fixed* local rule whose outcome is determined by a neighbour-count, so its growth, though spatially unbounded, is bounded *by the rule*; the sheet's growth is bounded only by **selection from outside** (the membrane, disuse-decay). Life is a closed determinism; the Agon loop is an open negotiation."

And strike "bounded plane"/"it makes the system finite" from the CONTRIBUTION concordance entry and any reliance in THE_KYTOS.

**(e) Confidence it falls as stated: 0.85.**

---

## (i) The Rorty reading

**Doc text charged.** CONTRIBUTION_AND_PRIOR_ART §"Concordances", Neo-pragmatism entry (lines 148–172): *"Rorty himself had little use for Peirce (in Consequences of Pragmatism he credits Peirce chiefly with naming pragmatism and stimulating James)"*; *"the correspondence-not-truth floor is anti-representationalism in practice … declining the Mirror of Nature exactly where Rorty says it must be declined"*; the ironist's *"radical and continuing doubts about the final vocabulary she is using"*; and the departure — *"a middle position Rorty's dichotomy of solidarity-or-objectivity does not name — solidarity supplies the warrant …, the calculus supplies validity."* Also BOOTSTRAP §4 ("the ironist's posture applied to the project itself").

**(a) Strongest charge (accuracy).** On the narrow historical facts the gloss is **accurate**. Rorty's *Consequences of Pragmatism* (Introduction) does say Peirce's contribution "was merely to have given [pragmatism] a name, and to have stimulated James" — the paraphrase is faithful, and secondary sources confirm Rorty "was unconvinced by Peirce's status as a pragmatist." The ironist definition is a **near-verbatim quote** from *Contingency, Irony, and Solidarity* ("radical and continuing doubts about the final vocabulary she currently uses"). "Solidarity or Objectivity?" is a real 1985 Rorty essay posing exactly that dichotomy. So there is no misquotation to charge here.

**(b) The charge the doc under-plays.** Two *transformations* are marked as departures but sit in sharper tension with Rorty than the prose admits. (1) Rorty's ironist is a deliberately **private, apolitical, non-methodical** figure; Rorty insists private irony must *not* be turned into a public method or a criterion. Casting irony as *"an invariant the gate checks"* (M resides only inside cuts) mechanizes and publicizes precisely what Rorty walled off as private — this is not a concordance but a reversal of the ironist's point, and it is presented first as agreement ("irony is an invariant the gate checks") before the departure is named. (2) The "middle position … the calculus supplies validity" claim is, on Rorty's own terms, *not* a third option his dichotomy fails to name — it is the **objectivity** horn (a tribunal answerable beyond the assembled peers), which Rorty argues is incoherent. The doc *does* flag this as a departure (structural realism "Rorty would refuse"), so it is honestly marked; but "a middle position Rorty's dichotomy does not name" overstates — Rorty would say his dichotomy names it fine, as the horn he rejects.

**(c) Author's answer.** ANSWERS. Both points are explicitly filed as *departures*, and the whole entry is prefaced "concordance of discipline, not lineage." The record already concedes the structural-realism break "Rorty would refuse."

**(d) Disposal — minor textual softening, optional.** Change *"a middle position Rorty's dichotomy of solidarity-or-objectivity does not name"* → *"a position that straddles Rorty's dichotomy — it keeps solidarity's warrant while re-admitting, at the validity layer, exactly the appeal-beyond-peers Rorty's 'objectivity' horn names and rejects."* This turns an overstatement into an honest self-location. The ironist-as-invariant line should add a half-clause noting Rorty confined irony to the private sphere.

**(e) Confidence it falls: 0.2** (survives as marked; the fixes are honesty-tightening, not refutation).

---

## (ii) "Economy of research ≟ active learning"

**Doc text charged.** BOOTSTRAP §2(b): *"Choosing which reach to make next … is the problem Peirce solved in outline in 'Note on the Theory of the Economy of Research' (1879): allocate inquiry by cost against expected reduction of doubt. This is the 19th-century statement of what the machine-learning literature now calls active learning / optimal experiment design."*

**(a) Strongest charge.** The 1879 "Note" is real and genuinely a value-of-information argument: Peirce asks how to allocate finite research *funds* to maximize the reduction of "probable error" per dollar — a marginal-utility-of-inquiry calculus. That is a true ancestor of **Bayesian optimal experimental design / value-of-information theory**. But "active learning" in ML is a narrower and distinct thing — *pool/stream-based selection of the most informative training instance to label*. Peirce's problem is portfolio allocation across research projects, not instance selection. Equating the two ("the 19th-century statement of what the ML literature now calls active learning") **stretches a family resemblance into an identity** and picks the less apt of the two ML cousins as the headline.

**(b) Under-anticipated.** The genuinely closer and *older* formal descendant is **Lindley (1956) / Raiffa & Schlaifer** value-of-information and the DeGroot tradition — none cited. Naming "active learning" (a 1990s ML coinage) as *the* thing Peirce stated risks the anachronism the historian-of-ideas discipline forbids: it reads a specific late-20th-century technique back into an 1879 funding-allocation note.

**(c) Author's answer.** PARTIALLY ANSWERS. The doc marks "the neighbors corroborate; Peirce mandates," and §5.1 flagged the framing as "assistant's reading … the author should ratify" (since ratified 2026-07-19). The hedge covers the *mandate* direction but not the *identity* claim.

**(d) Disposal — TEXTUAL FIX.** *"… what the machine-learning literature now calls active learning / optimal experiment design"* → *"… what statistics and machine learning now call **optimal experiment design and the value of information** (Lindley 1956), of which pool-based active learning is one modern instance."* Citation obligation: add Lindley, *On a Measure of the Information Provided by an Experiment* (1956) to the sources if the VoI lineage is asserted.

**(e) Confidence it falls: 0.3** (the identity clause falls; the underlying concordance survives).

---

## (iii) "TD-error-zero ≟ settled belief"

**Doc text charged.** CONTRIBUTION §"Concordances", RL entry: *"the TD error … its fixed point is Peircean: when the TD error is zero the agent stops learning, which is Peirce's settled belief (a habit no longer irritated)."* BOOTSTRAP §1 restates: *"TD error = 0 is Peirce's settled belief."*

**(a) Strongest charge.** Zero TD error means the value estimates satisfy the Bellman consistency condition — the *fixed point of the update rule*. In a stationary environment with a fixed policy this does entail value updates cease, so the analogy to "a habit no longer irritated" is decent. But the flat claim "when the TD error is zero the agent stops learning" is an **idealization that fails in the stochastic case**: with a stochastic environment only the *expected* TD error goes to zero at convergence; instantaneous TD errors keep firing sample-by-sample and never vanish. Zero TD error is also *local* (one state/transition can be consistent while others are not) — it is not a global cessation of inquiry the way "settled belief" reads.

**(b) Under-anticipated.** There is a sharper disanalogy the doc misses: TD's fixed point is fixed *relative to a frozen policy and stationary MDP*. Change the policy (as any learning agent does) and the "settled" value is instantly unsettled — TD convergence is settlement *of an estimate under an assumption*, not Peirce's *doubt-terminating habit of action*. The concordance flatters both sides by eliding this.

**(c) Author's answer.** ANSWERS weakly. It rides inside the concordance frame, and the entry's honest-differences paragraph ("RL's signal is a scalar folded into weights") does adjacent work, but does not qualify the "zero ⇒ stops learning" identity itself.

**(d) Disposal — TEXTUAL FIX (one word).** *"when the TD error is zero"* → *"when the **expected** TD error is zero (the update's fixed point)"*, in both CONTRIBUTION and BOOTSTRAP.

**(e) Confidence it falls: 0.3.**

---

## (iv) The Homeostat and free-energy castings

**Doc text charged.** Homeostat — CONTRIBUTION §"Concordances", Cybernetics entry: *"Ashby's Homeostat (1948; Design for a Brain, 1952) … when its variables were pushed out of bounds (its doubt), it **re-randomized its own internal wiring** until a configuration restored equilibrium — ultrastability."* Free energy — same doc: *"free energy ≈ surprisal ≈ doubt, minimized either by updating the model (perceptual inference) or by acting on the world (active inference)."* BOOTSTRAP §1 states it harder: *"Helmholtz's unconscious inference … through Friston's free-energy principle …: free energy **is** doubt."*

**(a) Strongest charges.**
- **Homeostat: substantially accurate, minor overstatement.** Dates are right (device 1948; *Design for a Brain* 1952). Mechanism: when an essential variable crossed its limit, a **uniselector** (stepping switch) advanced to a new set of randomly-preset feedback *coefficients*, re-searching until equilibrium returned — "ultrastability." The gloss "re-randomized its own internal wiring" is a fair popularization; strictly it re-selected feedback *parameters*, not topology. Not a charge worth pressing beyond a footnote.
- **Free energy: the BOOTSTRAP form overstates identity.** In Friston's framework, variational free energy is a **tractable upper bound on surprisal** (negative log model-evidence), *not* identical to it; the agent minimizes the bound because surprisal itself is intractable. CONTRIBUTION's "≈ surprisal ≈ doubt" is careful; BOOTSTRAP's flat "free energy **is** doubt" is wrong twice over (free energy ≠ surprisal; and surprisal is a *scalar surprise*, which the doc itself elsewhere insists doubt is richer than). The two docs disagree with each other on the same claim.
- **Requisite variety — a genuine inversion (the sharpest of this subsection).** CONTRIBUTION Cybernetics entry: *"the law of requisite variety explains a design fact Arisbe reached empirically: disuse-decay bounds M's variety to the engaged world-slice, because a model's variety **need only match** the variety of what it actually regulates."* Ashby's Law of Requisite Variety states a **lower bound** — "only variety can destroy variety," the regulator must have *at least* the disturbance's variety. The doc invokes it to justify an **upper** bound (don't carry more than the engaged slice). That inverts the law's logical direction: requisite variety never says a regulator "need only match"; it says it must "at least match." The upper-bound intuition is real but is an *economy* argument, not a requisite-variety consequence.

**(b) Under-anticipated.** The free-energy "is doubt" identity also silently commits Arisbe to the FEP's most contested claim — that a single scalar quantity governs both perception and action — which the CONTRIBUTION honest-differences paragraph elsewhere explicitly *rejects* ("a distinction a scalar surprisal collapses"). So the "is doubt" line is not just imprecise; it contradicts the doc's own stated departure two sentences later.

**(c) Author's answer.** MIXED. The "≈" version answers; the "is" version and the requisite-variety inversion deflect (no correction on record).

**(d) Disposal — TEXTUAL FIXES.**
1. BOOTSTRAP §1: *"free energy is doubt"* → *"free energy **bounds** surprisal, and minimizing it plays doubt's functional role"* (align with CONTRIBUTION's "≈").
2. CONTRIBUTION requisite-variety sentence → *"the law of requisite variety states the regulator must carry **at least** the variety it regulates; the economy of research supplies the complementary upper bound — carry **no more** than the engaged slice — which is what disuse-decay enforces."* (Attributes the upper bound to economy, not to Ashby's law.)
3. Homeostat: change "internal wiring" → "internal feedback parameters" (optional, footnote-grade).

**(e) Confidence it falls: 0.45** (the requisite-variety inversion and the BOOTSTRAP "is doubt" identity fall as stated; the Homeostat gloss survives).

---

## (v-b) Other attributions — shorter dispositions

**von Uexküll / biosemiotics lineage (real slip).** CONTRIBUTION Biosemiotics entry: *"biosemiotics is itself built on Peirce's sign theory, so the vocabulary transfers with least distortion,"* then leans on von Uexküll's Umwelt. Historically off: **von Uexküll (d. 1944) was not Peircean** — his Umwelt/Funktionskreis is an independent early-20th-century biology, retro-fitted to Peirce only later by Sebeok and Hoffmeyer. So "the Peirce-*native* bridge" over-claims for the specific figure the entry then uses. *Disposal (textual):* *"modern biosemiotics (Sebeok, Hoffmeyer) is built on Peirce's sign theory and **reads von Uexküll's Umwelt through it**; the vocabulary therefore transfers with least distortion."* Confidence 0.35.

**Maturana & Varela — concordance in tension with the source (the "inverts the source's position" case).** Autopoiesis theory is militantly **anti-representationalist** — Maturana denied that the nervous system builds "models" or "representations" of an external world. The entry invokes "structural coupling names what a long-running live membrane would become: model and source shaping each other's history" — importing exactly the *model-of-the-world* framing autopoiesis rejects. It is a real concordance (structural coupling is aptly named) but should be filed as an *instructive break*, like the Rorty and Life breaks, not a clean transfer. *Disposal:* add a one-clause break: "— with the instructive tension that Maturana rejected 'model'/'representation' talk, which Arisbe's M reinstates." Confidence 0.3.

**Noisy-TV term attribution (minor anachronism).** BOOTSTRAP §2(c) and CONTRIBUTION attribute the *"noisy-TV problem"* to *"Schmidhuber, Oudeyer."* The learning-progress *concept* (target the rate of improvement, not raw error) is genuinely theirs; the *term* "noisy-TV" was popularized by **Burda et al. 2018** (Random Network Distillation). *Disposal:* keep the concept attribution; either drop the coinage or credit it to Burda et al. Confidence 0.25.

**Rawls maximin — survives as marked.** §4.5 calls the docket "maximin-flavored," and §6 decision 4(b) *"ACCEPTED (a modest structural fact about attention, not a grand claim)."* Serving oldest/least-attempted-first is a priority-to-worst-off queue — maximin-*flavored* is exactly the right hedge. No charge. Confidence 0.12.

**Fricker — accurate, one nuance.** The uptake/testimonial-injustice reading (THE_MEASURE §4) is faithful to *Epistemic Injustice* (2007). One nuance: "the wrong of not even hearing someone out" is closer to Fricker's *pre-emptive* testimonial injustice than to the central *credibility-deficit* case (where you *do* hear them, then discount). Since the phrase is attributed to Arisbe's own Doubt 4, not to Fricker verbatim, it survives. Confidence 0.15.

**West scaling — survives as marked.** Both CONTRIBUTION and THE_KYTOS §4 explicitly mark the semiotic-scaling claim as *"a conjecture Arisbe is positioned to test, not assume"* / *"Conjecture until measured."* The quarter-power, city-superlinear, company-sublinear-and-mortal facts are accurately stated. The one soft spot — "companies die, cities don't" is itself an empirically contested West claim (definitional/survivorship objections) — but it is flagged conjecture downstream, so no charge lands. Confidence 0.1.

**Good-regulator theorem (Conant & Ashby 1970) — accurate.** Title and gist right. (A skeptic could note the theorem has been criticized as near-tautological / dependent on strong assumptions, but as a *concordance* citation it is sound.) Confidence 0.12.

**AGM / Doyle TMS / de Kleer ATMS — accurate.** Dates (AGM 1985, Doyle 1979, de Kleer 1986) and characterizations correct; "absorbs a contradiction" is a fair loose gloss of revision-under-inconsistency. No charge. Confidence 0.1.

**Sosa apt-performance / Gettier (THE_MEASURE §1) — flagged, but quick.** The claim that a record-based measure makes "Gettier-style luck cases lose their grip" is a substantive, arguably too-fast epistemology move (Gettier targets *single* justified-true-beliefs, not track records). It is explicitly "(Assistant's readings, flagged)," so it survives the intellectual-history standard, but the author should not let it harden without an epistemologist's check. Confidence 0.3.

---

## Summary ledger (what must change vs. what survives)

**Falls as stated — mandatory textual fix:**
1. **Conway's Life "bounded plane"** (0.85) — factually wrong (Life is on ℤ², infinite); replace the whole "decisive difference is the plane" argument with the closure/fixed-rule contrast. Appears in AUTOMATED_MODEL_DEVELOPMENT §1, CONTRIBUTION §Concordances, and load-bears in THE_KYTOS §3.

**Falls as stated — one-line fix each:**
2. **Requisite variety inverted** (0.45) — Ashby's law is a *lower* bound; the doc uses it for an upper bound. Re-attribute the upper bound to the economy of research.
3. **"free energy is doubt"** (0.45, BOOTSTRAP §1) — overstated identity that contradicts CONTRIBUTION's own "≈" and its scalar-surprisal departure. Use "bounds surprisal."
4. **"active learning" identity** (0.3) — narrow the claim to optimal experiment design / value of information; cite Lindley 1956 if asserted.
5. **"TD error is zero ⇒ stops learning"** (0.3) — insert "expected."

**Real but minor slips — add a clause:**
6. von Uexküll not himself Peircean (0.35); Maturana/Varela anti-representationalism as an instructive break (0.3); noisy-TV term is Burda et al. 2018 (0.25).

**Survives as marked (no charge):** the Rorty facts (0.2 — quotes and paraphrase accurate; only a self-location overstatement to soften), Rawls-maximin (0.12), Fricker (0.15), West (0.1), good-regulator (0.12), AGM/TMS (0.1).

**The through-line for the author:** the concordance *frame* is doing exactly the honest work it was built to do — nearly every "X anticipated Y" charge dies on the "concordance not lineage" hedge. What the frame does **not** protect is a wrong fact stated *inside* a concordance, and the docs have three of those (Life's plane, requisite-variety's direction, free-energy's identity) plus two lineage slips (Uexküll, Maturana). The Conway's Life error is the one that should embarrass, because it is (a) simply false, (b) repeated across three docs, (c) elevated to "doctrine," and (d) *unnecessary* — the correct closed-vs-open-negotiation contrast was already sitting in the same paragraph.

Sources consulted for fact-checks: LifeWiki (Conway's Game of Life); Medium (Conway's Game of Life: The Infinite Grid); IEP (Peirce's Pragmatism); SEP (Pragmatism).
