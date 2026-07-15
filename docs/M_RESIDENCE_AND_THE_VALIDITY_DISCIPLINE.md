# Where M Resides: the Validity Discipline

**Dev memo (design-of-record), 2026-07-15.** Records a foundations dialogue
(2026-07-14→15) between the author and the assistant on where a domain model M
resides, how it changes, and whether the resulting discipline departs from
Peirce. The verdict of §6 is the memo's headline: **this is not a new
departure — it is Departure II** (FIDELITY_AND_DEPARTURES §3, "nothing
contingent can be *said* at level 0"), re-derived from the mechanics, completed
operationally, and strengthened by the assertive-graphs literature the author
raised. Nothing here is built; §8 lists the implications awaiting direction.

Companion memos: FORCING_AND_THE_GAMMA_CROSSING (the first decision-B nominee),
SECOND_ORDER_CORE_OPENING (decision B itself), LEVEL_ZERO_AND_THE_REGISTERS
(§5, §8 — the blank as the only unconditioned thing). Modules touched by the
argument: `model_acts.py`, `contest_context.py`, `model_revision.py`.

---

## 1. The question, and the path the dialogue took

The author asked: *where does M reside — in what context, at what level? From an
empty sheet only DC+ applies; anything else arrives via INS in a negative
context. So how do we assemble M and leave it open to erasure and addition?*

The dialogue passed through five stations, each an author correction of the
assistant's first answer:

1. **"Utterance" is no license.** The assistant first defended contingent
   residence at depth 0 by distinguishing a *proposal* (ventures) from an
   *utterance* (commits). The author rejected the word-jump: commitment is
   constituted by the **act of scribing and its author** (recorded in the
   chain), not by the depth at which the ink lands.
2. **Depth 0 buys nothing derivational.** Peirce's rules are stated by
   *parity*, not absolute depth: every evenly-enclosed area supports the full
   derivational life (ERA, IT−, DC−, the whole discharge/modus-ponens
   two-step). The only unique power of depth-0 assertion is **detachment** —
   the categorical statement — and fallibilism denies us that right.
3. **The axiom.** The blank sheet — Dau's sole axiom — stands for *the
   existence and reality of the world beyond the membrane* (this ties
   Departure II to Departure I's membrane). Our statements are about that
   reality and never at its level: always contingent, always within a cut.
4. **The consequence, agreed and provable:** under the discipline every
   reachable EGI — and the whole UoD, each transition rule-licensed — **is
   valid by construction** (blank valid + six sound rules, induction over the
   chain). A false supposition in an odd context is *truly enabled*: INS-in-odd
   is unconditionally sound, so error is quarantined by the scroll and charged
   to the player's ledger, never to the sheet.
5. **Memory vs. exhibit** (§5 below): what "leave the old M behind" can and
   cannot mean at first order.

## 2. The mechanics established (verified against the engine)

**No rule puts a contingent atom at depth 0.** The rule-by-rule audit
(`model_acts.py`): INS reaches only negative contexts; IT+ copies
less-enclosed → more-enclosed; ERA/IT− remove; DC+ adds an inert double cut;
**DC− is the sole door into a positive context, and it only exposes what was
already enclosed**. Semantically: blank is valid, the rules preserve validity,
a contingent atom is not valid — so no pure-rule path exists (this is
Departure II's *level-0 theorem*).

**Where a pure-rule attempt sticks.** From blank: DC+ → INS `P` at depth 1 →
IT+ `P` into depth 2 yields the tautologous scroll `~[P ~[P]]` — and there it
stops. The antecedent cannot be emptied: ERA is illegal at odd depth, and IT−
needs a *dominating* copy at depth 0, which is exactly what does not exist.
The regress is visible in the mechanics and bottoms out where Peirce said:
at an act, not an inference.

**The discharge path** (run against the real engine, 2026-07-15): scribe the
warrant and trust-law — `(reported "s1") ~[ (reported "s1") ~[ (black "Nox") ] ]`
— then **IT−** deiterates the inner warrant (licensed by the depth-0 copy;
deiteration is an *equivalence*, polarity-indifferent, unlike ERA) and **DC−**
discharges. The fact lands at depth 0 *derived, never inserted*; the two-step
is classical modus ponens (`beta_modus_ponens` is this shape). Note this is
the *outbound* direction of Departure II's registered *inbound* construction
(DC+ · INS · IT+ nesting — how M enters as a defeasible given).

## 2b. The depth-0 inventory theorem, and the venue of discharge

Author follow-up (2026-07-15): *shouldn't we say explicitly that no path
discharges to depth 0 — that depth 0 can legitimately contain only nothing or
seps? What role does "contingent" play in "no pure-rule path to contingent
depth 0"?*

**The role of "contingent": it is the exact boundary of the theorem.** By
soundness *and completeness*, reachable-from-blank = **valid**. So depth 0
legitimately carries content all the time — every theorem of the calculus
stands there (a proof from the blank *ends* as a sheet-level graph:
`peirce_law`, `theorem_praeclarum`). Drop "contingent" and the claim is false;
keep it and the claim is gapless.

**The depth-0 inventory theorem.** What can a valid graph carry *uncircumscribed
in the sheet's own area*? Exactly three kinds of thing:

1. **nothing** (the blank);
2. **seps** (cuts — every *saying* at depth 0 lives inside one);
3. **heavy dots / lines of identity** — bare "something exists," which Dau's
   isolated-vertex rule inserts in arbitrary contexts
   (UNIVERSAL_GENERALIZATION_DAU_HOMEWORK) and which is valid because the
   universe of discourse is presupposed nonempty. This is the one refinement
   the author's "nothing or seps" formulation needs — and it is no
   counterexample in spirit: the dot *predicates nothing* (Peirce's pure
   demonstrative); it re-asserts only the presupposition the sheet itself
   makes by representing a universe.

**Never an uncircumscribed spot.** An uncircumscribed relation atom `P` at
depth 0 makes the graph entail `P`; `P` is falsifiable; the rules preserve
validity; the blank is valid — so no legitimate path from the blank sheet ever
exposes an uncircumscribed proposition on it. Stated as the author asked:
**explicitly, no such path exists.**

**The venue of discharge — reconciling this with §2's discharge path.** The §2
demonstration *presupposed the utterance*: warrant and trust-law already stood
at depth 0 (the old regime's act), and the discharge then computed *relative
consequence* — given contingent depth-0 content, more follows to depth 0. That
never breached the theorem (which concerns paths from the blank); it
propagated the act's contingency. Under the gapless discipline the same
mechanics can never fire at depth 0: with no contingent depth-0 copy, IT− is
never licensed inside a sheet-level scroll's ring, so a sheet-level antecedent
never empties, so DC− at depth 0 removes only genuinely inert double cuts —
**depth 0 is contingency-free by invariance, not by vigilance.** And DC−
loses nothing: all contingent discharge happens at even depths ≥ 2, under the
standing supposition — the modus-ponens two-step runs identically at level 2
(IT+ carries warrant and trust-law into the hold; IT− deiterates; DC−
discharges), and what it wins is *committed-under-M* — which is Level Zero's
form again. Deduction is untouched; only its venue is fixed.

## 3. The discipline

Everything contingent lives within a cut. Depth 0 is the world's level: it
carries only what the calculus itself delivers (theorems; discharges whose
warrants stand). The practical discourse lives in the **standing world-scroll**
`~[ M ~[ … ] ]`: level 1 (odd) is hypothesis — the arena, where positing is
free and fenced; level 2 (even) is committal-*under*-hypothesis, reached only
by rule. What the sheet ever asserts is "if your suppositions, then your
conclusions" — true however wrong the suppositions. The player's interest is
real (they scribed; the chain says who; the ledgers keep score) — but it is
borne by the *player*, not the sheet.

This makes Level Zero's episode-form (`cut[ M cut[P] ]`, "no unconditioned
posit") **structural rather than institutional**: the UoD boundary had been
doing the fence's job invisibly; the discipline says a boundary that does
logical work must be *drawn* (the sheet is a context but not a cut; only ink
does logical work — the picture-never-lies principle applied to force).

## 4. How M changes under the discipline: the asymmetry flips

Relocating M from depth 0 to level 1 inverts the change-asymmetry pole for
pole:

- **At depth 0** (the old `model_acts` picture): shedding free (ERA),
  acquiring impossible by rule — hence the "utterance" patch.
- **At level 1**: acquiring free (INS — you may always suppose more), but
  **piecemeal shedding is unsound** (erasing from an antecedent strengthens
  the conditional).

So revision is *world-withdrawal*: ERA the **whole** supposition-scroll (it
sits in the sheet's positive area — legal, sound, free), DC+ a fresh one, INS
the amended M. You cannot un-suppose a premise while keeping what you built on
it — the dependencies go with it — and the DAG keeps the withdrawn world as a
prior state. That is philosophically right (foundations-style belief
revision), and it answers the author's earlier question ("leave the first M
behind in the DAG?") in the strongest form: the calculus *forces* that shape.

## 5. Presence is play: the three tenses

The author proposed keeping the old M in view — rewrite the fixed M beside it,
DC+ around the old one, "label it left-behind" — and then caught the flaw
himself ("do we keep in play ideas we had better be rid of?"). The mechanics
confirm the worry: **the first-order sheet cannot hold ink without force.**
A double cut around old-M is *inert* — `~[~[M_old]]` still says `M_old`, so
the antecedent supposes `M_old ∧ M_fixed`, the retired law still binding,
while the ink *looks* fenced (an honest-picture violation). A denial-insertion
makes the antecedent contradictory. There is no third state at first order.

What the request actually needs splits into **three tenses**, each with its
own machinery:

1. **In force** — the current sheet. Keeping old-M deliberately in force is
   sometimes right: that is the **rivals** pattern (run 12 arm C — laws held
   verbatim, ranked by ledger, the world selecting).
2. **Withdrawn, remembered** — the DAG. ERA never denies the utterance: the
   act persists as a chain step, and erasure is a *further recorded act in*
   history, not an edit of it. Learning-from-mistakes is implemented here
   (audit lens, stickiness, `agon_metalearning`).
3. **Present without force — the labeled exhibit.** Expressible only one
   order up: a **quotation** of M_old is an object, not an assertion
   (`second_order_check` law S1 stratification = forcelessness below; S2
   quote-equals-quoted = the exhibit is faithful). "Pull it forward in quotes
   for consideration" = DAG-state → quote (mention) → optionally re-suppose in
   an arena (use, fenced). Only the middle step lacks machinery.

**This nominates `(superseded ⌜M_old⌝ reason)` as the second candidate**
(beside FORCING_AND_THE_GAMMA_CROSSING's `(forces s φ)`) for the first
asserted second-order claim that decision B waits for — and the more organic
one, since it arises from the revision workflow rather than an imported
mathematical dictionary. Peircean gloss: the DAG is *memory*; quotation is
*recall* — a past habit held before the mind without being exercised, which is
what self-controlled criticism requires.

## 6. Is this a departure from Peirce? — It is Departure II, already registered

The author asked whether the discipline departs from Peirce, noting the
assistant's recurrent argument ("residence at depth 0 is precisely what
assertion is; Peirce's sheet holds asserted graphs bare") and the
assertive-graphs literature. The finding:

**No new departure has occurred.** The discipline *is* Departure II —
"nothing contingent can be said at level 0; level zero bears form, not
content" — registered in FIDELITY_AND_DEPARTURES §3, tried in
ADVERSARIAL_EXAMINATION (verdict: **survives with amendment**, the firmest
ground of the three, judge confidence 0.82), and *strengthened* there when the
assertion-4 concession ("every scroll requires one unconditioned positing of
M") was retracted as an over-concession: M enters legally only by nesting
from the blank, so the thesis is **gapless** — the blank alone is
unconditioned, and it asserts nothing.

Mapping this dialogue onto the register:

| Dialogue result | Departure II status |
|---|---|
| No pure-rule path to contingent depth 0 | = the registered *level-0 theorem* |
| "Utterance is no license"; commitment = act + author | = the registered Phemic-Sheet analysis (assertion as normative act, interpretant- and act-side, never a feature of depth) |
| No unconditioned posit; M enters nested | = the registered gapless closure (DC+ · INS · IT+) |
| Whole-UoD validity by construction; mistakes quarantined | **new corollary**, in the register's favor |
| The discharge (outbound) path; IT− vs ERA | **new mechanics**, completing the registered inbound construction |
| Asymmetry flip at level 1; revision = withdraw-whole-scroll | **new consequence** |
| Presence-is-play; three tenses; quotation nominee | **new**, feeds decision B |

The assistant's recurrent counter-argument was the **textbook gloss that
Departure II names as "the position Arisbe rejects"** — re-litigated against
settled doctrine across several sessions. The register, not the gloss, is the
project's standing position. (Lesson recorded in `tasks/lessons.md`.)

**The standing code tension, named honestly:** `model_acts.assert_into` and
`model_revision.assert_fact` implement the gloss — juxtaposition of contingent
content at depth 0, warrant carried as chain metadata. The record is honest
(`is_rule: False`, warrant demanded, ○-posited standing = the operational
turnstile the register credits), but the *ink* performs Departure II's
"forbidden move." The ink-exact forms exist: `admit_by_discharge` (outbound)
and the nesting construction (inbound). Whether the live loops move to them
is §8's decision.

## 7. The assertive-graphs literature bears on the register — in its favor

Bellucci, F., Chiffi, D. & Pietarinen, A.-V. (2021), "Beta Assertive Graphs:
Proofs of Assertions with Quantification," *Journal of Applied Logics* 8(2),
353–376 (the paper the author raised; see also their Alpha-AGs 2018 and Chiffi
& Pietarinen 2020). Three bearings:

1. **The rejected gloss is the live standard reading, so the departure is
   real, not a strawman.** The paper states it plainly: EGs carry "an
   *embedded* sign of assertion in their fundamental notation of *the sheet of
   assertion*"; their Convention 2 remark: "Since graphs are scribed on the
   SA, anything on the SA is an assertion." Note Arisbe *keeps* this
   principle — SA-position is force — and draws the consequence: precisely
   because anything at depth 0 is asserted, nothing contingent may be placed
   there bare. What changes is *who may write there* (the calculus and the
   world), not what the position means.
2. **The cost of the alternative route.** AGs also organize logic around
   assertion, but implement it by changing the *notation and calculus*: cuts
   and polarities dropped, boxes deictic, negation defined via blot +
   cornering — and the logic comes out **intuitionistic**, with two
   non-interdefinable quantifier lines (barbed/unbarbed — Peirce's 1882
   "bonds," which his own invention of polarity had made superfluous) and a
   "more bountiful" rule set, a price the authors acknowledge. Arisbe's
   Departure II buys assertion-sensitivity **without touching the Dau-classical
   core**: the discipline is a regimen on *acts* (what may be scribed where,
   by whom), the seam marked operationally (warrant gradient, chain records),
   not a new consequence relation. This is the standing
   conservative-over-the-core invariant (SECOND_ORDER_LANDSCAPE §, "the
   crossing invariant") doing its work one more time.
3. **Their intuitionism is our K3, placed differently.** The Beta-AG
   non-theorem ¬∀xFx → ∃x¬Fx — "absence of an assertion is not an assertion
   of absence" — is exactly the Agon register's open-world UNKNOWN
   (`Verdict3` = Strong Kleene, per the landscape memo). Taking assertion
   seriously forces that caution *somewhere*; AGs put it in the object
   calculus, Arisbe puts it in the verdict semantics and keeps the calculus
   classical. Same instinct, different placement — and the placement is the
   design decision Arisbe has already made and defended.

So the "assertorial" literature does not indict the project's fidelity; it
documents that the question is live, confirms the reading Departure II departs
from, and exhibits the price of the road not taken.

## 7b. Coda — the no-special-notation principle (Departures II and III are one policy)

The author's closing observation (2026-07-15): the modality Peirce sought Gamma
notation for needs no special notation, and now assertion needs none either.
Stated precisely, with one correction each way: modality is not expressed *in*
a Beta graph — it is read off the **diachronic DAG** of ordinary Alpha/Beta
sheets (trajectory, not mark); and Peirce never had an assertion sign to lose —
the Beta-AG paper's own observation is that the SA *embeds* assertoric force
(the sign was Frege's), and the AG apparatus (boxes, cornerings, barbed lines)
is the price of making assertion the *object logic* after dropping polarity.

The unified principle both departures enact: **force and modality are not
pictured; they are carried by the architecture around the picture.** The graph
carries propositional content only. *Where* it sits (polarity/parity) gives
illocutionary force; *when* it sits (the DAG) gives modality; *who scribed it,
on what warrant* (the chain) gives responsibility. Gamma — broken cuts,
tinctures — was Peirce's attempt to push all three into notation, unfinished by
his own lights; Departures II and III decline that route identically.

The shared residue: both parallels bottom out at the **same second-order
frontier**. Departure III's register already names Gamma's irreducible
remainder second-order-not-modal; likewise assertion-as-*force* needs no mark,
but assertion-as-*subject-matter* (reasoning about acts of asserting) predicates
of graphs — quotation, the third tense of §5, decision B. Even the AG paper
brushes it: their boxes are explicitly *deictic* ("this is what I say: ___") —
mention straining to happen inside a first-order notation.

## 8. Implications awaiting the author's direction

> **Status update (2026-07-15): the corpus half of §8.1 was DIRECTED and is
> BUILT.** The author's pre-frontier sweep ("ensure the polarity shift for M
> and the explicit steps for the verdict and M modification have been
> provided") relocated every M-bearing corpus UoD (11; the 7 T-box ontologies
> deferred to phase 2 by decision, visibly allowlisted) into the standing
> world-scroll `~[ M ~[ ] ]` — recognition structural (`src/world_scroll.py`),
> the read path unified on `m_view` (oracle · materializer · theory query ·
> render-M), every M-change an explicit rule-licensed chain step
> (`src/m_steps.py`: ADMIT_TO_M = INS into the arena; REVISE_M = the executed
> ERA·DC+·INS world-withdrawal of §4) and every verdict a recorded PEEL step
> whose parameters recompute identically (`tests/test_corpus_polarity_discipline.py`,
> the standing gate). The **live loops** (`agon_evolution.run`, `live_runner`,
> the membranes) still run the old regime — `agon_evolution_swan` is wrapped
> post hoc with `earned: false` flags — so the *full* §8.1 order below (retire
> `assert_into`/`assert_fact` in the loops) remains open.

1. **Adopt the discipline for canonical regimes?** M relocates to level 1 of
   a standing world-scroll; the oracle/peel reads the antecedent area (verdict
   semantics unchanged — the episode was always "given M, then G");
   `assert_into`/`assert_fact` retired or re-derived as nesting/discharge;
   membranes INS into the world-scroll (free by rule; warrant justifies the
   *choice*). A decision on the order of the crossing decisions, not a patch.
   *(Corpus half done, above; the live-loop half is what remains of this item.)*
2. **Departure II appendix.** Fold §§2–5's new corollaries into
   FIDELITY_AND_DEPARTURES §3 (or cross-link this memo) so the register
   carries its operational completion.
3. **Decision B** now has two nominees: `(forces s φ)` (imported, exact) and
   `(superseded ⌜M⌝ …)` (homegrown, from the revision workflow). The case for
   opening the door has a second, independent plaintiff.
