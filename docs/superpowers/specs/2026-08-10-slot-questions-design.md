# The slot-question — C-series stage 4, part (a) (design)

**Design sitting, 2026-08-05 → 2026-08-10.** Held on the author's agreement to the
[tenability assessment](2026-08-05-the-tenability-assessment.md)'s recommendations. **Nothing
here is built.** Three decisions were ruled in the sitting and are marked **RULED** where
they appear.

Companions: [the stage-4 design](2026-07-28-community-scaling-experiment-design.md) §11 (the
three parts, authored 2026-07-30) · [Examination VII](../../ADVERSARIAL_EXAMINATION.md)
(which examined §11 and found slot-questions repair the real defect) ·
[FROM_THERMODYNAMICS_TO_SEMIOSIS](../../FROM_THERMODYNAMICS_TO_SEMIOSIS.md) §6, §6a (the five
standing rules) · `tests/test_c_speaker_variance.py` (which holds the pinned zero this build
is read against).

---

## 1 · What this builds, and what it does not

It builds **one change to the shape of a question**: a question may carry a free slot, and
the asker's uptake aperture widens from *the atom I named* to *one filler of the pattern I
asked*. That is the first occasion in this world on which a peer can tell a unit something
the unit did not already license.

It does **not** build stage 4's parts (b) or (c), a credential mark, a chooser beyond the
`typify` variable already built, an aperture filter, or a re-ask rule. §9 records each
refusal with its reason.

### 1.1 · Why part (a) alone — **RULED**

§11.2 states that the three parts "need each other" and that "each part alone reads null for
the reason its predecessor did." **That is a designer's claim which has never been
measured**, and this is the cheapest occasion to put it at risk. Part (a) is also the one the
assessment's five arrivals converge on, and it is minimal — two methods.

Under the newly adopted rule *attribution requires ablation*, one change costs one ablation
and three changes cost at least three. If part (a) alone reads null, the tree already says
what that means: `test_c_speaker_variance.py:201` pre-registers *"if typification is still
inert THERE, the defect is in typification and not in its world."*

### 1.2 · What reading the code changed about this build

`Unit.publish` already puts **every** held fact on the board, so a slot-question adds no
marks and carries no content that was not already available. What it changes is **uptake**:
today a unit adopts only the exact atom it named, which its own laws already licensed;
under a slot it may adopt a filler naming an individual it never met.

This matters for two reasons. It means the mechanism lives in `ask` / `answer_to` / `adopt`
and will show as *uptakes of new content*, not as more marks. And it means D-A2 —
`Unit.answer`'s output being a subset of `publish`'s — is **untouched by this build** and
remains open; the finding was always that `answer` is a redundant *minting* channel while the
targeting is what carries the effect.

## 2 · Architecture

### 2.1 · What a unit asks: `(body *x)`, not `(head *x)`

`Unit._wants()` yields a determined want `head(a)`: an atom the unit holds a law
`body → head` for, over an individual whose `body(a)` it holds and whose `head(a)` it does
not. The slot-want is derived from the same laws, and it asks about the **body**: for each
law `body → head` the unit holds, the candidate pattern is `(body *x)`. Which of them goes
out is decided by the ordering `_wants` already applies, and the once-ever key already
guarantees each pattern leaves a unit at most once.

The reason is §11.4's own, and it is decisive. Because `CONSEQUENT_LAG = 1`, an
opposite-parity peer holds exactly **the bodies the asker missed for heads the asker will
meet** — and a determined question can never reach them, because it names an atom the
asker's own record already licenses. A `head` pattern would return atoms already resolved or
unreachable. A `body` pattern returns precisely the news the asker can still place a stake
on.

Stated plainly so a null cannot later be explained away as *we asked the wrong pattern*:
**this is a choice, it is recorded in §8, and it is justified by the lag.**

### 2.2 · One variable, one question per round

`slots=False` is today's world, unchanged. `slots=True` makes the unit's single question a
pattern **instead of** a determined atom.

Not both, for two reasons. A rule deciding which of the two goes out first *is* a priority
claim, and "whoever fixes the attempt order fixes the priority" is the D-series' own ruling 1
refusal. And P-H2 is worded as a comparison — "the peer-channel carries more bits **with
slot-questions than without**" — which needs the two arms to differ in one thing.

`ask`'s existing capacity is untouched: at most one question per round, because attention is
bounded.

### 2.3 · Uptake is bounded at one, and `typify` chooses — **RULED**

A pattern may be answered by many fillers at once, so *how many the asker takes* becomes
unavoidable rather than a detail. It is bounded at **one per round**.

Three things fix this and none of them is taste:

- **Task 3 measured the alternative.** Indiscriminate uptake is *strictly harmful* — worse
  than silence, at every seed, four units going from positive to negative net scores.
- **`ask` already carries the same bound for the same stated reason.** A bound on uptake is
  the same capacity claim as the bound on asking.
- **Examination VII's ruling 2** makes a bound **capacity** (invariant, and a thing a
  designer may set) while *which filler* is **policy** (free, and a thing a designer may
  not). The policy is already built and already the measured variable: `typify=None` takes
  the first offered, exactly as today; `"prefer"` takes the preferred peer's; `"distrust"`
  refuses a peer whose testimony on that relation has already failed.

So the bound installs a capacity and the choice installs nothing.

### 2.4 · A slot-question stands — **RULED**

`MarkBoard.open_questions()` closes a question by content, and a fact's content never equals
a pattern's, so a slot-question is **never closed**. This falls out of the existing code with
no new rule, and it is true to the object: *who has body?* is not a request that gets
satisfied.

Volume stays bounded by what the community actually meets, because `Unit.answer`'s
`(FACT, content)` key already makes each peer mint each filler exactly once, ever.

**Named as a change in kind rather than left to arrive as a side effect:** today every
question closes, and this one does not. A unit's standing questions accumulate monotonically
over a run. The alternative — closing on first uptake — was refused in the sitting because
`_published` keys a question once-ever, so a closed pattern could never be re-asked and the
channel would carry at most one uptake per relation per unit for a whole run, which is less
than the determined channel carries now. Re-asking is the maintenance channel (§9b), still
unruled.

### 2.5 · Why typification finally has a job

Under determined questions, two answers are the same atom by construction, so preferring a
speaker decided nothing — which is the C-series' `occ_bite == 0`, measured at every level of
speaker unreliability.

Under slots, fillers differ **in usefulness**:

- a filler naming an individual **inside the asker's aperture** but missed through attendance
  parity is a stake the asker can still win;
- a filler naming an individual the asker **cannot observe** licenses a head that will never
  arrive at its membrane — task 3's guaranteed miss.

**We do not filter by aperture.** That would be the designer installing the answer. The
harmful case is allowed to happen and to be paid for, and `settle_credit`'s `(proved,
failed)` per peer is already the instrument that would discover which peers pay. **This is
the first time in this series that speakers differ in something a unit could learn** — which
is what `whom_to_ask` was built for and has never had.

## 3 · Implementation risks, to be checked rather than assumed

Named here so the build reports them rather than discovering them in a figure.

- **Mark validation.** `c_marks.py` requires a `QUESTION`'s content payload to be a tuple. A
  pattern is still a tuple, so it should validate — **verify, do not assume.**
- **`Unit.as_egi` refuses a non-constant individual** with an explicit error. A pattern is
  never held as a fact, so it should never reach there — **verify with a test that would
  fail if it did.**
- **Canonical ordering.** `_wants` sorts to make the choice a deterministic function of the
  unit's state; the slot-want must sort deterministically too.
- **The inquiry's own questions.** `dispose_challenges` publishes questions of its own
  (`out.asked`); those stay determined and must not be swept into the pattern path.

## 4 · Pre-registration

Committed before anything is built. **Each prior carries its question kind**, per the
convention adopted 2026-08-05: a sealed synthetic world answers *existence* questions
freely, *attribution* questions only with an ablation, and *magnitude* questions not at all.

- **P-S1 · existence — a peer can now tell the asker something new.** With `slots=True`, at
  least one uptake names an individual the asker's own record did not carry. **Fails** if
  every uptake is an individual already held, which would say the channel is still
  confirmation-only and the slot changed nothing.

- **P-S2 · attribution — typification stops being inert.** `occ_bite > 0`: the typified arm
  no longer reproduces the untargeted arm digit for digit. This is the falsifier **already
  pinned in the tree** at `test_c_speaker_variance.py`, whose baseline asserts
  `{"adopted_fabricated": 0, "occ_bite": 0}` so that the zero stands on the record before the
  mechanism that should move it exists. **Fails** if the arms stay identical — and the pinned
  claim already states the consequence: *the defect is in typification and not in its world.*

- **P-S3 · existence — a lie can be volunteered.** With one unreliable speaker
  (`ObserverNoise(spurious=0.9)`), fabricated adoptions rise above zero. Today they are zero
  with one liar and cross only when *every* unit is unreliable, and then only because an
  unreliable **asker** mis-observes a body and asks about it. **Fails** at zero, which would
  say the asker's end still blocks fabrication and the confirmation structure survives the
  slot.

- **P-S4 · attribution — the effect is the slot, not the bound.** An arm carrying the uptake
  bound with *determined* questions reproduces the determined baseline. **Fails** if it
  moves, in which case bounded-uptake and slot-question are confounded and P-S2 is
  unreadable. This arm exists because §2.3 introduces a second change alongside the first,
  and the assessment's own rule forbids crediting either without separating them.

- **Reported, never gated: bits.** P-H2's mutual information is reported **beside** true laws
  held, never instead of it. Examination VII's finding stands: bits are sign-free, and the
  measured **inert** arm carried 0.998 bits/question against the useful arm's 0.345 — nearly
  three times as much where the channel did nothing.

- **No magnitude prior is offered**, because none is available. This world's parameters are
  calibrated from itself.

## 5 · The cheat register — stated before building

1. **The uptake bound is a number we chose**, and the number is 1. It is a capacity rather
   than a policy (§2.3), which makes it legitimate to set — it does not make it measured.
2. **`(body *x)` rather than `(head *x)` is our design choice**, justified by
   `CONSEQUENT_LAG = 1` and recorded here so that a null cannot later be attributed to having
   asked the wrong pattern.
3. **No published C-series figure moves**, because `slots=False` is the default and every
   existing arm runs under it. The byte-identity of those arms is a test, not a hope (§6).
4. **The arms compare within one field and one aperture scheme.** Nothing here says anything
   about a world of different width.

## 6 · Testing

- **`slots=False` is byte-identical.** Every existing C-series arm reproduces its published
  figures exactly. This is the first gate and it is the reason the change is a variable.
- **The four priors are gates**, each written so it can fail.
- **The harness declares its channels** (`declares()`, rule 5) and every narrated figure is
  asserted or generated (rule 4). A slot arm that plays a channel which never runs fails
  before any figure is compared.
- **Any sentence attributing an effect to the slot carries an ablation** (rule 3) — which is
  what P-S4 is for.
- **The falsifier is watched to bite before it is trusted**, as the mortality guard and the
  channel guard both were: a run with the pattern deliberately degraded to a determined atom
  must fail P-S1.

## 7 · Refused, and why

Recorded so the next reader does not rediscover the hole and fill it.

- **Stage 4 parts (b) and (c)** — deferred, not refused, and deferred *in order to measure*
  §11.2's claim that neither can be omitted (§1.1).
- **The credential as a public mark** — deferred with them. It is the public half of
  Examination VII's two-layer ruling and it remains unbuilt; reliability still lives in the
  private `Unit.peers` dict.
- **An aperture filter on fillers** — this is where the designer would write the answer
  (§2.5). The harmful case must be able to happen.
- **A chooser beyond `typify`** — the policy is already built and already the measured
  variable.
- **Asking a determined question and a pattern in the same round** — the priority rule is a
  substantive claim nobody has argued for (§2.2).
- **A re-ask / maintenance rule** — §9b of the stage-4 spec, still unruled, and §2.4 makes it
  unnecessary for this build.
- **Closing a pattern on first uptake** — refused in the sitting; it would leave the channel
  carrying less than the determined channel does now (§2.4).
