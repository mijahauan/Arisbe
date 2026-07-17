# Where M Resides: the Validity Discipline

**Dev memo (design-of-record), 2026-07-15.** Records a foundations dialogue
(2026-07-14→15) between the author and the assistant on where a domain model M
resides, how it changes, and whether the resulting discipline departs from
Peirce. The verdict of §6 is the memo's headline: **this is not a new
departure — it is Departure II** (FIDELITY_AND_DEPARTURES §3, "nothing
contingent can be *said* at level 0"), re-derived from the mechanics, completed
operationally, and strengthened by the assertive-graphs literature the author
raised. Build status: §8's corpus half BUILT 2026-07-15; §9 (the second
relocation, cells at even depth) and §10 (the episode lifecycle + ruling (b))
BUILT 2026-07-16.

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

> *But see §9 (ratified 2026-07-16): housing the model's elements in cells at
> even depth inverts this asymmetry to the fallibilist pole — retraction one
> licensed ERA, admission one licensed INS — while the standing structure
> still asserts nothing.*

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
> the standing gate).
>
> **Status update (2026-07-16, sweep #2): the live-loop half is DISCHARGED —
> folded into the second relocation per verdict D4 (§9.10), the loops
> migrating straight to cells.** `agon_evolution.run` opens every chain with
> genuine DC+ · INS residence steps; `revise_with_disposition` dispatches to
> the licensed cell moves when M is resident (sheet-level fallback retained
> for bare fixtures); decay is the licensed ERA with its `pruned:disuse`
> flavor recorded; `live_runner` reads/decays/reseeds through the residence;
> `agon_evolution_swan` is a native chain (the post-hoc adapter deleted).
> §1 below is fully taken.

1. **Adopt the discipline for canonical regimes?** M relocates to level 1 of
   a standing world-scroll; the oracle/peel reads the antecedent area (verdict
   semantics unchanged — the episode was always "given M, then G");
   `assert_into`/`assert_fact` retired or re-derived as nesting/discharge;
   membranes INS into the world-scroll (free by rule; warrant justifies the
   *choice*). A decision on the order of the crossing decisions, not a patch.
   *(Corpus half done, above; the live-loop half is what remains of this item.)*
2. **Departure II appendix.** Fold §§2–5's new corollaries into
   FIDELITY_AND_DEPARTURES §3 (or cross-link this memo) so the register
   carries its operational completion. *(DONE 2026-07-15: FIDELITY_AND_DEPARTURES
   §3b — the five corollaries, the assertive-graphs bearing, and the
   enacted-in-corpus status, cross-linked back to this memo.)*
3. **Decision B** now has two nominees: `(forces s φ)` (imported, exact) and
   `(superseded ⌜M⌝ …)` (homegrown, from the revision workflow). The case for
   opening the door has a second, independent plaintiff. *(TAKEN 2026-07-16:
   the author affirmed B with **both nominees** — the door opens exemplar-first,
   B-min → B-full; see CROSSING_DECISION_BRIEFS. The third tense gets its
   machinery.)*

## 9. The second relocation: agreed content at even depth (PROPOSED 2026-07-16 — awaiting the author's verdicts)

> **Status: BUILT (sweep #2, 2026-07-16 — the same day the verdicts were
> taken; see §9.10).** The relocation is total: `world_scroll.py` recognizes
> and constructs the cells shape (`~[ ~[cell] … ~[ ] ]`; recognition = W
> holds only cuts, at least one empty; `m_view` = the union of the cells'
> interiors, ids preserved), `retract_from_m` is the licensed single-ERA
> retraction, `m_steps` gained `RETRACT_FROM_M` (`retract_step`, with the
> D6 `flavor` field — `pruned:disuse` = the *faded* tense) and the
> `challenge_step` composite (ONE recorded `REVISE_M`: ERA + INS — the swan
> relinquishment collapsed to one move, preserving the exemplar's state
> numbering), the world-withdrawal triple retired to the rare
> full-replacement case, **the §8.1 live-loop half folded in** (verdict D4:
> `agon_evolution.run` opens with genuine DC+ · INS residence steps and
> every disposition/decay lands as a licensed cell move with its executed
> derivation recorded; `revise_with_disposition` is residence-aware;
> `live_runner` counts/decays/reseeds through the residence;
> `agon_evolution_swan` is a native chain, the post-hoc adapter deleted),
> all 18 M-bearing corpus UoDs rebuilt in the new shape, and the polarity
> gate rewritten to the §9.3 inventory with `m_retraction ⇒ ERA(s)` and
> `m_revision ⇒ the executed ERA/INS list`. **Deferred, named:** D5's dusty
> rooms (multiple standing residences + designation-by-record) and D6's
> room-granularity pruning triggers (settlement-keyed / TTL / budget) —
> no dusty rooms exist yet to designate or prune; the recorded pruning
> disposition is in place.

### 9.1 The prompting observation

The discipline of §§3–4 rightly evicted M from depth 0. But it housed M at
**level 1 — the area where anything at all may be inserted**. The license
that made enlargement free (INS in a negative context) also made supposition
*cheap*: the standing record cannot distinguish an earned admission from an
arbitrary one by its drawn place. And the asymmetry of §4 — acquiring free,
shedding heavy — is **backwards for a fallibilist M**. On Peirce's own
account it is the *surprise* that dissolves a habit: when the black swan
arrives, the record should let the refuted fact die in one licensed move.
Instead, relinquishment costs the whole ERA·DC+·INS world-withdrawal, while
supposing more costs nothing.

The author's re-framing: a model — its facts, individuals, and relations —
is not a supposition heap. It is what the players have **agreed functions as
true in that context**. The proposal: the model's elements should reside,
*after* INS into a negative context, **in a positive context deeper than the
INS level** — even depth, where erasure is licensed, so that M-revision is
easy exactly when a new fact or realization forces it.

Behind the specific proposal stands a longer suspicion the author has now
named: a successful representation of *thought* needs much greater
contextual depth than one working level. The depth-0 discipline was the
prerequisite, not the destination — once nothing contingent stands exposed
at the world's level, the deeper levels are free to carry **epistemic
register**, not merely negation-count: depth 0 the world's own level (valid
by construction) · level 1 the challengeable membrane · level 2 the agreed ·
the dotted oval the mentioned (present without force, §5's third tense).
This is recognizably the territory Peirce reached for with the tinctures —
provinces of the sheet — but here it falls out of polarity and license, with
no new primitive.

### 9.2 The trap in the bare form

A positive context above the INS level, with nothing conditioning it, is a
**double cut**: `~[ ~[ M ] ]` ≡ M — the standing structure would *assert M
at depth 0*, precisely what the discipline forbids (§5 already proved this
blade: "a double cut around old-M still binds"). The obvious repair — a real
antecedent, `~[ C ~[ M ] ]`, "given the agreement C, M holds" — trades one
violation for another: now a **contingent conditional** stands asserted at
the world's level, and valid-by-construction is lost again. The current
scroll keeps its consequent *empty* for exactly this reason: `~[ M ~[ ] ]`
is vacuously true, so the standing record asserts nothing.

### 9.3 The realizable form: cells beside the hold

Keep the empty hold — it is what buys vacuity — and house the model's
elements in **cut-wrapped cells at level 2, siblings of the hold**:

```
~[   ~[ facts · individuals · laws … ]   ~[ facts … ]   ~[ ]   ]
      └─ a cell: level 2, POSITIVE        └─ another     └─ the hold
```

The outer negation is vacuously true so long as one empty cut stands among
its contents, so the standing structure asserts nothing — the same standing
status as today ("correspondence, not truth" untouched). And the licenses
now read:

| act | move | area | license | soundness |
|---|---|---|---|---|
| **enlarge M** | INS of a *closed cell* `~[ f … ]` | level 1 (odd, negative) | ✓ INS | sound (insertion in a negative area) |
| **retract a fact / law** | ERA of the element(s) *inside* a cell | level 2 (even, positive) | ✓ ERA | sound (erasure in a positive area, Dau's theorem) |
| **empty a cell wholesale** | ERA of all its contents | level 2 | ✓ ERA | sound; the emptied husk remains |
| **remove a cell's husk** | — (a cut at odd depth) | level 1 | ✗ not ERA-licensed | world-withdrawal only (§4's triple) |

Both acts of M-change become **single rule-licensed moves** — which neither
the current regime (retraction = the triple) nor the bare `~[ C ~[ M ] ]`
form (enlargement unlicensed) achieves. This is the author's proposal
precisiated, not an alternative to it: INS happens at the negative level;
the inserted ink *lands* at the positive level inside its own cut.

Notable corollaries:

- **The swan collapses to one move.** Relinquishing the over-general law is
  a single ERA of the law's subgraph inside its cell; the DAG keeps the
  prior state; ERA never denies the utterance (§5 tense 2 unchanged).
- **Scar tissue is honest.** An emptied cell's husk cannot be erased at odd
  depth, so it stands as a *visible* record that something was agreed here
  and withdrawn — audit-legible, and structurally indistinguishable from
  the hold (both are empty cuts in W), which is tolerable because any empty
  cut keeps the vacuity.
- **Laws keep their Horn shape.** A law's cut-structure inside a cell
  re-roots through `m_view` exactly as today (cell contents → the view's
  sheet; the law reads as a sheet-level cut to the materializer).

### 9.4 The register reading

Even depth is the Verifier's territory in the endoporeutic evaluation:
content there is *defended* — it functions as true under the enclosing
condition. "Agreed to function as true in that context" is what even
polarity *means* dialogically, so the drawn place follows the epistemic
register: level 1 was the right home for M-as-**supposition**; the cells are
the right home for M-as-**in-context agreement**. That is a genuine register
upgrade — admission stays deliberate (an INS recorded with its warrant, the
Agon's disposition), retraction becomes immediate (the fallibilist pole) —
and it amends the gloss of §§3–4, not their mechanics: everything contingent
still lives within a cut; depth 0 still carries only what the calculus
delivers; the standing structure still asserts nothing.

The episode-form is untouched: the arena scroll `~[ M ~[ G ] ]` of an EPG
episode is *different ink* — the tested conditional of a play, built and
peeled per episode — and must not be conflated with the residence structure.
Residence ≠ episode; the peel reads M through `m_view` regardless of where
it resides.

### 9.5 What adoption would touch (sweep #2)

`m_view` is the one shared read primitive, so the oracle, materializer,
theory query, and render-M follow a **single change** (union of cell
interiors, re-rooted). Beyond it: `world_scroll` recognition (W holds only
cuts; **at least one** empty — empty cells are scars indistinguishable from
the hold, so the hold loses uniqueness), `wrap_m`/`enlarge_m` (cell-wrapped
INS), `m_steps` (ADMIT_TO_M = INS-of-cell, derivation `["INS"]` unchanged in
kind; REVISE_M's relinquishment becomes a **single ERA** — the triple
retires to the rare husk-removal case), the standing polarity gate rewritten
to the new inventory, the 11 M-bearing corpus UoDs migrated with their
flip-trajectories re-derived, and the four loop docs' two-regimes notes
updated. The §8.1 live-loop half would migrate **straight to cells** rather
than to level-1 first — this proposal reshapes that open order rather than
adding to it.

### 9.6 The author's verdicts

1. **D1 — the register shift.** Adopt M-as-in-context-agreement (cells at
   even depth) as an amendment to the discipline's gloss, recorded as a
   corollary of Departure II? (§§3–4 stand; §4's asymmetry table gains the
   third column above.)
2. **D2 — cell granularity.** One cell per admission (each cell = one
   admitted batch; emptied cells = visible scars; the audit reads the
   history off the synchronic drawing) vs. one consolidated cell (tidier
   picture, history only in the DAG)?
3. **D3 — the hold's story.** Accept that empty cells and the hold are
   structurally indistinguishable (any empty cut keeps vacuity; "the
   committal area" story retold as "the committal *register*, of which the
   hold is the first cell")? Or must the hold stay unique (then recognition
   needs a marked hold — against the no-special-notation principle of §7b)?
4. **D4 — ordering.** Take this sweep before B-full (it is first-order,
   touches the corpus, and B-full's exemplars would otherwise be built on a
   residence about to move)? And fold the §8.1 live-loop migration into it?

### 9.7 Bearing on the third tense (the author's follow-up, same sitting)

The author asked whether the cells remove the need to bring a superseded M
forward as a *quoted* M — "we don't need to quote it but simply leave it
alone and let it fall out of sight when it no longer applies in habitual
use." The finding, which sharpens both proposals:

- **"Leave it alone" is not available at first order.** Standing ink in the
  committal register *binds* — the materializer fires a standing law, the
  peel applies it, however long unused (the picture-never-lies principle
  applied to force; §5's blade unblunted). The first-order trichotomy is
  exhaustive: **in force** (standing) / **absent** (erased; DAG-remembered) /
  present-without-force — which exists only one order up. The cells cheapen
  the *transitions*; they create no first-order middle state.
- **"Falling out of sight through disuse" is the decay path to absence —
  and the cells make decay itself rule-licensed.** The live loops' disuse
  mechanism currently retracts atoms by structural surgery
  (`retract_atom`, the legacy regime); under cells the fading of a habit
  through disuse becomes a licensed ERA at even depth — a legal move of the
  calculus, not maintenance beside it. (A corollary in the proposal's
  favor, to be added to any adoption order: refutation-driven retraction
  and disuse-driven fading become the *same licensed move*, distinguished
  by the step's recorded disposition — surprise vs. entropy.)
- **What quotation remains for: present discourse about absent content.**
  `(superseded ⌜M_swan_law⌝ "Nox")` is a *now*-assertion about a withdrawn
  habit — who killed it and why, in today's ink. The DAG cannot say that
  (memory, not recall); an emptied husk cannot (the scar is anonymous).
  So under this proposal the third tense re-glosses: it was never a stage
  of the **revision** workflow — revision needs only erase-and-remember,
  one move under cells — it is the register of **self-controlled
  criticism**: a past habit held before the mind as an *object*, to be
  judged. Decision B's case is not weakened: revision's plaintiff retires,
  but criticism's stands, and `(forces s φ)` + cross-UoD mention (the
  citation register) were always independent.

If D1 is adopted, §5's tense-3 paragraph should carry this re-gloss, and a
fourth tense-flavor should be named beside *withdrawn-remembered*:
**faded** — absence reached by disuse rather than refutation, same drawn
result, different recorded disposition.

### 9.8 The dusty room: abandonment without erasure (the author's second follow-up, same sitting)

The author corrected §9.7's over-reach: a whole abandoned M is **not in force
globally** — "were we to enter that 'dusty room' again, and reason with
what's there, then yes." The correction stands. §5's blade cuts against the
plain **double cut** (`~[~[M_old]]` — assertive); a whole abandoned M left
standing in its **vacuous standing form** asserts nothing, is consulted by
nothing, and its content functions as true only *within its own context* —
the endoporeutic reading exactly. §9.7's "standing ink binds" holds only
*inside the active residence* (the room the oracle reads), where a
superseded law does keep firing until erased.

**The presence-ladder for a whole M** (the author's hinge: *in the DAG only,
or still present in the UoD?*):

1. **active** — the designated residence; `m_view` reads it; its laws fire;
2. **dusty** — standing in the current UoD, vacuous, globally forceless,
   *enterable*: viewing an old M needs no quotation, because the ink is
   there; it falls out of sight through habitual disuse (nothing consults
   it) while remaining recoverable by walking in;
3. **erased** — the whole structure ERA'd at depth 0 (licensed; the
   withdraw half of §4's triple, without the resupply obligation); DAG
   only — memory, not presence;
4. **quoted** — recalled from absence into present discourse as an object
   (`UoDQuotationResolver` already addresses `uod_id@state_id` — a DAG
   state; the swan's mark resolves through the withdrawal step's record —
   "we still can use quotes to recover what we decide to erase").

**Quotation's irreducible remainder** narrows once more, to two acts:
recall of the *erased*, and **discourse-about** — the dusty room stands
mute about its own retirement (no special notation, honestly so);
`(superseded ⌜M⌝ reason)` is the only way today's ink can assert *that* a
habit was retired and *why*. Viewing never needed the quote; asserting-about
always will.

**Two consequences for the verdicts:**

- **Granularity — the proposals compose.** Dust works at whole-structure
  granularity because vacuity is structural; a single law inside the
  *active* M cannot go dusty in place (it fires until erased). So the cells
  (§9.3) make within-M revision one licensed move, and the dusty room makes
  whole-M abandonment free — don't even erase; just stop reading it.
- **Designation.** Recognition currently demands exactly one sheet scroll;
  rivals and dusty rooms need "*the* designated residence" answered without
  special notation — plausibly **by record** (the chain's last
  supply/admission names the room the practice reads), which is where this
  meets §5's tense-1 rivals pattern (several Ms standing, the ledger
  ranking; a dusty room is a rival nobody plays). Readers that scan raw ink
  (the modal lens's "scribed somewhere") will see dusty relations — a
  lens-semantics note to carry honestly: *scribed ≠ in force*.

5. **D5 — the dusty room.** Admit abandonment-without-erasure as a
   recognized standing state (several vacuous structures on the sheet, one
   designated active by record), with the designation convention to be
   fixed? Or keep the one-scroll discipline (abandonment always = whole-ERA,
   presence of the old M always via DAG/quotation)?

### 9.9 Presence and pruning: the memory economy (the author's third follow-up, same sitting)

The author's question: a dusty M has utility mostly *in the environs of model
revision*, and as the UoD matures — revision rarer, habits settled — that
utility fades; the old M remains in the DAG in any event. So how is the EGI
**pruned by ERA** — not merely tidied by the minimal in-view set — and how
does that eventually meet **resource budgeting** and the **outsourcing of
memories for recall by external calls**?

**Two economies, firmly distinct.** THE_MINIMAL_IN_VIEW_SET governs
*attention* (what is in view; folding changes no ink). Pruning governs
*presence* (what stands in the EGI at all; a real, recorded move). They
coordinate as a graded ladder in which each rung is cheaper to hold and
every rung is recoverable:

| rung | what it is | mechanism | recovery |
|---|---|---|---|
| **in view** | attended | the in-view set's rules (fold, DOI, chapters) | unfold |
| **active** | present, read | the designated residence; `m_view` | — |
| **dusty** | present, unread | §9.8's standing vacuous structure | enter the room |
| **pruned** | absent from the sheet; DAG only | **ERA of the whole structure at depth 0 (licensed)**, disposition recorded | quotation of a DAG address (`uod_id@state_id`), or re-supply |
| **offloaded** | DAG segment moved to cold/external storage | tiering (below) | resolver fetch by address — the external call |

**Pruning is epistemically free; only recall latency is spent.** ERA never
denies the utterance; the DAG keeps the withdrawn world; §2b's inventory
theorem is untouched (pruning *removes* sheet content, never adds). So the
pruning policy is purely an economy of presence — safe to automate under a
budget, because nothing knowable is lost, only the cost of getting it back
changes (immediate entry → DAG walk → external fetch).

**The clock should be habituation itself, and it is already measured.** The
author's "less and less frequently with model maturation" is an observable
the system computes: `agon_metalearning`'s settlement/stability/poise
metrics say when a territory has stopped being revised. So the natural
pruning triggers, in order of principle:

1. **settlement-keyed** — a dusty room is pruned after the successor M has
   *withstood* (no `challenge_to_M` touching that territory for k rounds;
   settled@k is already a computed quantity);
2. **disuse TTL** — the `UsageLedger` idiom at room granularity ("use" of a
   dusty room = entry / consultation / quotation-resolution; rooms nobody
   revisits age out) — the same habit-economy that already bounds |M| at
   atom level, one granularity up;
3. **budget caps** — the `live_runner` idiom (`max_m_relations`,
   `frontier_cap`): a sheet-size bound, oldest-dust-first when exceeded,
   drops *counted, never silent*.

Each firing is an explicit chain step — the same licensed ERA, with the
**disposition recorded** (`pruned:settled` / `pruned:disuse` /
`pruned:budget`), extending §9.7's rule that surprise and entropy are one
move distinguished by their recorded reasons.

**The real storage weight is the DAG, and pruning the sheet does not touch
it.** Chain states persist whole (`history/states/<id>.egi.json`); the
archive grows monotonically — that is its job. The budget question there is
**tiering**, and the seams exist: `live_runner` already segments,
checkpoints, and drops in-RAM chains (carrying only M forward); state
addresses (`uod_id@state_id`) are location-transparent; the MCP verifier's
content-addressed ids make cold segments dedupe- and offload-friendly. The
"outsourcing" rung is then additive: cold DAG segments move to external
storage, and **recall is an external call through the existing resolver
seam** — a remote `QuotationResolver` (kind-dispatched, exactly like
`UoDQuotationResolver`) fetches by address. Warrant note: recalling one's
*own* archived state is attested provenance (the chain vouches), not a
low-warrant import — the import floor applies to foreign content, not to
memory.

**What is genuinely the author's here (folds into D5's environs):**

6. **D6 — pruning policy.** Which triggers, in which regimes? A live loop
   needs automatic pruning (settlement-keyed + budget-capped, dispositions
   recorded); a scholarly/corpus UoD arguably prunes only by deliberate act
   (the author's ERA, never a daemon's). And the tiering order (when a DAG
   segment goes cold) is an operations knob (runs/OPERATIONS) rather than
   doctrine — but the *recall-is-a-licensed-quotation* principle is
   doctrine, and worth ruling with D1–D5.

### 9.10 The verdicts (the author, 2026-07-16 — all six as recommended)

*(§10 follows after these verdicts — the episode lifecycle under the cells
residence, proposed and ruled the same day.)*

1. **D1 — ADOPTED.** M-as-in-context-agreement: the model's elements reside
   in cells at even depth beside the hold; recorded as a corollary of
   Departure II. §§3–4's mechanics stand; their gloss amends (§9.4); §5
   gains the re-gloss of §9.7 and the fourth tense-flavor **faded**.
2. **D2 — PER-ADMISSION CELLS.** Each admitted batch its own erasable cell;
   emptied husks stand as visible scars — the synchronic drawing carries its
   own audit (the honest-picture principle applied to revision).
3. **D3 — INDISTINGUISHABILITY ACCEPTED.** Empty cells and the hold are one
   kind: the committal *register*, of which the hold is the first cell. No
   marked hold (per §7b's no-special-notation principle).
4. **D4 — THIS SWEEP BEFORE B-FULL.** The relocation (sweep #2) precedes the
   B-full core opening; §8.1's live-loop half folds in, the loops migrating
   straight to cells.
5. **D5 — THE DUSTY ROOM ADMITTED, designation by record.** Abandoned Ms may
   remain standing (vacuous, globally forceless, enterable); the designated
   active residence is named by the chain's record (the last supply /
   admission), never by special notation. The rivals pattern of §5 tense 1,
   made resident.
6. **D6 — PRUNING POLICY SPLIT.** Live loops prune automatically
   (settlement-keyed via the metalearning signal, then disuse TTL, then
   budget caps — every firing a licensed ERA with its disposition recorded:
   `pruned:settled` / `pruned:disuse` / `pruned:budget`); scholarly/corpus
   UoDs prune only by deliberate act. DAG tiering is an operations knob;
   **recall-is-a-licensed-quotation** (one's own archive = attested
   provenance, not low-warrant import) is doctrine.

## 10. The episode under the cells residence: entertain, confirm, discharge (the author, 2026-07-16 — BUILT the same sitting)

The author's construction, closing the loop the residence opened: how an
episode of the EPG — *given M, then P* — is conducted **wholly in ink**, and
how its result reaches M *derived, never inserted* (the outbound path §2b's
corollary 3 promised).

### 10.1 The lifecycle

With M's content standing at even depth *m* (the agreed context):

1. **ENTERTAIN** — in depth *m*, perform **DC+** (the outer cut's area is
   *m*+1, odd — the arena; its empty inner cut will be the **vacuity
   rider**); **IT+** M into the arena (inward — licensed; and because it is
   *iteration*, the premise is M's own ink, identity-preserved, not a
   lookalike supposition); **INS** `~[P]` into the arena (negative —
   unconditionally sound). The arena holds `{ M′, ~[P], ~[ ] }`: the scroll
   "if M then P", standing **vacuously** — the rider keeps the contingent
   conditional forceless while contested. (The naked scroll `~[ M′ ~[P] ]`
   cannot be built at even depth by rules at all — P cannot be INS'd into an
   even area — so the riderized form is the *only* rule-reachable episode
   ink: force never enters by rule.)
2. **Confirm** — the episode plays: the recorded **PEEL** (the semantic
   register), or the hot-seat contest / the reductio exhibit (derive P beside
   `~[P]`, deiterate — the `revision_episode` path). Either way a *recorded
   verdict*.
3. **DISCHARGE_TO_M** — drawn modus ponens: **IT−** the M′ copies (the
   warrant emptied against the original one level up), **IT−** the rider
   (licensed against the residence's standing hold — an identical empty cut
   in an enclosing area), **DC−** the now-clean double cut. **P's ink lands
   at the level of the original M**, in the agreed content. A refuted or
   withdrawn episode instead ends by **ABANDON** — one licensed ERA of the
   whole exhibit (it stands at even depth); the DAG keeps the entertained
   state.

Machinery: `world_scroll.entertain_episode` / `discharge_episode` /
`abandon_episode`; recorded by `m_steps.entertain_step` / `discharge_step` /
`abandon_step` (rules `ENTERTAIN` / `DISCHARGE_TO_M` / `ABANDON_EPISODE`).
Exemplar: `episode_discharge` (`tools/build_episode_discharge_demo.py`) — the
audited proposal moves *absent → derived-only → standing*.

### 10.2 The episode theorem

> **An EPG episode — entertain a proposal, identify its M, and handle the
> result — requires its DC+ in an even context at depth ≥ 2.**

Three clauses, with their epistemic status:

- **Parity (strict).** INS is licensed only in negative areas; a cut opened
  in an odd area has a *positive* interior — no arena. Only an even context
  yields the arena. A consequence of Dau's insertion rule and parity
  arithmetic alone.
- **Identifying M (relative to the residence).** Iteration carries ink only
  *inward* — into areas enclosed by the source's context. M's ink stands in
  the cells (even, depth ≥ 2), so an arena can receive *M itself* (identity
  of ink, which is what distinguishes IT+ from a lookalike INS) only if it is
  opened within M's area. A sheet-level arena can entertain a supposition
  contest, but never identify an M by rule.
- **Handling the result (strict — a corollary of soundness).** The discharge
  needs the vacuity rider deiterated against a standing empty cut in an
  *enclosing* area. Inside W the hold provides it. At depth 0 nothing can:
  a bare empty cut standing at the sheet's level is ⊥ asserted at the
  world's level, which **soundness forbids from ever arising** in a graph
  reachable from the blank sheet. So at depth 0 the DC− is unreachable and P
  can never land there — *"no unconditioned posit" enforced by
  rule-reachability, not vigilance.* (Machine-checked:
  `test_world_scroll.py::TestEpisode::test_the_episode_theorem_depth_zero_discharge_is_unreachable`
  — the engine refuses the rider's deiteration in a sheet-level arena.)

The theorem is a *meta*-theorem about the calculus (the register of Dau's
soundness results), demonstrated here as executable refusals rather than a
hand proof. "At least 2" also licenses nested episodes at deeper even
registers — an episode entertained inside an episode's exhibit — the
"greater contextual depth" of §9.1, recursively.

### 10.3 The ⊥-door, and ruling (b)

The same hold-deiteration that completes the discharge opens a door: the
standing hold is ⊥ among W's conjuncts, and ⊥ in scope trivializes local
consequence — **four licensed moves scribe arbitrary content into M with no
episode at all** (DC+ · INS `~[Q]` · IT− rider ⇠ hold · DC−). Ex falso
quodlibet, drawn: the structural price of the vacuity device. The calculus is
being honest — a context whose content includes ⊥ *has* trivial internal
consequence; that is exactly why the residence asserts nothing. And the door
is fenced by the very vacuity that creates it (§10.2's third clause): what
enters through it never gains force at the world's level.

So the discharge cannot certify the episode *by licence alone* — the
IT−·IT−·DC− sequence runs identically whether P was confirmed or refuted.
**The author's ruling (2026-07-16): keep the calculus pure; the earning rides
on the record.** Enacted three ways:

1. **`discharge_step` refuses to record** a discharge without a confirming
   `PEEL` of the same proposal (verdict *true*) in the chain to cite; the
   citation rides in `params["confirmed_by"]`.
2. **The gate re-asserts the citation** corpus-wide
   (`test_corpus_polarity_discipline.py::test_discharges_cite_a_confirming_peel`)
   — and every recorded peel already recomputes.
3. **The m_view tripwire**: any chain step that changes M's content
   (`m_view` before ≠ after) must carry an acknowledged act
   (`test_m_content_never_changes_silently`) — so no one reaches M through
   the ⊥-door *unrecorded*, whatever rules produced the change. The
   falsifier is in the gate: a hand-built silent ⊥-door chain is flagged.

The alternative — closing the door mechanically by making the hold opaque to
IT± (the quotation-boundary precedent) — was declined: it would give an empty
cut special behavior by rule, against D3 and the no-special-notation
principle (§7b). The house doctrine stands: *the licence makes the move
sound, never obligatory; the warrant rides on the step; §3.3 attests
correspondence, not truth.*

### 10.4 Character, and the registers

`proof_character` reads the lifecycle exactly as Peirce would: **ENTERTAIN is
the auxiliary line** (scribing the candidate into the exhibit is the
insertion that marks *theorematic* deduction — "experiment upon the
diagram"), and the discharge is its content-preserving follow-through — so a
discharged chain is **theorematic**, never ampliative (the whole point:
derived, not inserted) and never opaque (the executed derivations are
recorded). The semantic register (the peel over `m_view`) and the
demonstrative register (this lifecycle) are the two faces of one episode —
Level Zero's `cut[ M cut[P] ]`, finally structural, with every move licensed.

Under D2 (per-admission cells) the iterated premise is the **host cell's**
content: the episode names which agreed batch it draws on. Sibling-cell
content enters an episode only as fresh supposition (INS — same ink, identity
carried by the record, not the rule) or through the cell-blind semantic
register. And a discharge grows the *host* area rather than minting a new
cell — this admission's audit lives in the chain, accepted knowingly.
