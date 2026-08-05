# Is this an untenable path? — the assessment

**Written 2026-08-05**, on the author's ruling at the close of the fourteenth arc:
*"a sober, critical assessment of whether we have taken an untenable path here."* Ruled to
come before the queued `c_unit.py` channel sitting and before anything else in
`CURRENT_PLAN.md`.

Nothing was built for this. Nothing under `src/` was touched. Every claim below is either a
citation to the record or a check run against the working tree today, and each is marked as
one or the other — because an assessment written in the same voice as the sentences it is
assessing would be worth nothing.

Companions: [the channel audit](2026-08-04-c-series-channel-audit-design.md) ·
[Examination VIII](2026-08-01-examination-viii-the-west-mapping-on-trial.md) ·
[the D-series design](2026-08-02-d-series-building-the-stake-design.md) ·
[the stage-4 design](2026-07-28-community-scaling-experiment-design.md) §11 ·
[runs/RUN_C_AUDIT_LOG.md](../../../runs/RUN_C_AUDIT_LOG.md) ·
[runs/RUN_D1_LOG.md](../../../runs/RUN_D1_LOG.md).

---

## 1 · What is on trial

The phrase "this path" needs a referent before it can be judged, and the honest one is
narrower than the whole project. Four things are running, and they are not in the same
condition.

| | What it asks | Condition |
|---|---|---|
| **The calculus** — EGI, correspondence, the three modes, the corpus | does picture equal proposition, always | **Not on trial.** It has its own suite and its own gates, it shares no module with the C/D stack, and if the research arms were abandoned this afternoon it would stand untouched. Its health is also not evidence *for* the arms. |
| **The West arm** — E1…E3c, the scaling correspondence | what is the exponent | **Closed, correctly, five days ago.** |
| **The emergence arm** — C stages 1–4 | does discrimination arise unless installed | **Open, and the subject of most of what follows.** |
| **The stake arm** — D-series | does anything change once something can be lost | **One run old, and the only arm with a positive result.** |

Treating these four as one path is itself part of what makes the situation look worse than
it is. Two of the three research arms are in defensible shape; one is finished; the trouble
is concentrated in exactly one, and it is nameable.

## 2 · The ground rules, made operational

The author fixed the ground rules and they are the right ones. Made checkable:

- **U1 · the instrument is unsound.** Would need a *published figure* falsified by a defect
  — not an attribution, a number. Evidence: `runs/c_audit/CALLS.txt`,
  `runs/c_audit/ABLATION.txt`, and the re-derivations in `RUN_C_AUDIT_LOG.md`.
- **U2 · the question is unanswerable with this instrument.** Would need a question whose
  answer requires a control the design's own premises forbid, or a mechanism the substrate
  cannot host. Evidence: the priors that read *not reached*, and the reason each gave.
- **U3 · the question is not worth answering.** Would need that no outcome of any arm would
  change any commitment. Evidence: whether findings have in fact moved doctrine.

Only U1 is a bug. U2 is a change of instrument. U3 is a change of subject.

## 3 · The finding that decides most of it

**Five independent measurements, taken across four arcs by four different instruments, have
all landed on one property of one method — and that property has a designed, ruled,
pre-registered repair that has never been built.**

The property: **a question in this world names the whole atom it wants, and is addressed to
nobody.** Verified in the tree today, not taken from the record:

- `Unit.ask` (`src/c_unit.py:1297`) publishes a fully determined want. Its own docstring
  says what that costs: *"WHAT A QUESTION CANNOT DO is choose whom to ask — it is published
  to the whole board."*
- `MarkBoard.answer_to` (`src/c_marks.py:309`) returns **the first** fact mark whose content
  equals the question's — author-blind and round-blind.

The five arrivals:

1. **C stage 3** — the ask channel is a confirmation channel, not a discovery channel: two
   answers to one question are the same atom by construction. 0 of 939 adoptions ever took
   up a fabricated fact.
2. **Speaker variance (`tests/test_c_speaker_variance.py`)** — the author's ruling gave the
   field unreliable speakers, and typification stayed *exactly* inert at every level of
   unreliability: `occ_bite == 0` in all three arms. The file's own diagnosis: *"a liar
   cannot get a lie into the channel at all, so there is nothing for the ledger to notice."*
3. **D-1's `P-D4`** — the priced world finally supplied two candidates on 26.6% of
   preference occasions, and nothing moved, because `whom_to_ask` has no consumer. *A unit
   cannot ask a wrong peer, because it cannot ask a peer at all.*
4. **The channel audit's D-A2** — `Unit.answer` mints 668 marks in K1 and moves not one of
   that arm's 43 figures, because `publish` already put the same content on the board and
   `answer_to` cannot tell the two apart.
5. **The channel audit's D-A1** — `corroborate` is dead in all twenty arms that play it,
   for the adjacent reason: it can only re-inscribe evidence some other act has already
   published.

Read as five defects, this is a bad five weeks. Read as five measurements, it is one
finding confirmed to a standard the project rarely reaches — by ablation, by re-measurement
under a changed field, by a priced world, and by two instruments built to refute it.

**And the repair was designed by the author himself, before four of the five arrived.**
`§11 · Stage 4 — one mechanism in three parts (author, 2026-07-30)` of the stage-4 spec
specifies three parts *"which need each other"*: **(a) slot-questions** `(R *x)`, so two
peers can return different fillers; **(b) a doubt metric** reordering a fixed budget; **(c)
alarm reliability**, the cry-wolf structure. §11.4 pre-registers `P-H1`/`P-H2`/`P-H3`
against them. Examination VII examined the design and found *"slot-questions repair the real
defect."* `tests/test_c_speaker_variance.py:201` pins the pre-slot-question baseline at zero
*specifically so the mechanism that should move it can be read against it.*

**Checked today: `grep -n slot src/c_unit.py src/c_marks.py` returns three hits, all in
unrelated prose about a challenger's slot. Part (a) does not exist.** Neither does the
public half of Examination VII's two-layer reliability ruling: a credential inscribed as a
mark has no mark kind — `src/c_marks.py:87–91` lists `FACT`, `LAW`, `QUESTION`, `CHALLENGE`,
`CORROBORATION` and nothing else. Reliability lives in `Unit.peers`, a private dict, which
is the objectivation defect the environment-first sitting named. Of the three parts, only
(c)'s raw material was built — `ObserverNoise` — and the arm run on it is the one that
measured the null this section is about.

### 3.1 · How it happened, stated fairly

This was not neglect, and the record should not be read as if it were. **Stage 4's own
§11.5 says what comes after it and why:** *"Mortality and regime shift move to stage 5. They
add stakes and urgency to a channel that must first be able to carry information; killing
units before the channel works would measure the killing."*

The next day, the thermodynamics thread reached a different and also correct diagnosis —
units have nothing at stake, and that one absence explains why every mechanism built in
abundance read inert. On its strength the author ruled the D-series next. **So stage 5 was
built before stage 4, against stage 4's own written reason for the order, on a ruling that
had good grounds.**

D-1 then settled the dispute empirically, and settled it in favour of *both*: the stake
bites (`P-D1` held at every seed; the ablation moved a number for the first time in the
project's history), **and** every channel prior came back not-reached, exactly as §11.5
predicted — `P-D4` could not be evaluated because the mechanism it tests cannot bite until
some stage gives a unit two answers to choose between, and that stage is the one that was
passed over.

That is the honest account of *"has the measurement outrun the thing measured?"* It has, and
the mechanism was not sloth or confusion. Two sound diagnoses specified opposite orders, one
was followed, it paid, and the other half is still standing there designed, pre-registered
and unbuilt — while five arcs of measurement and audit ran over worlds that could not
contain it.

## 4 · Three kinds of question, and which ones a sealed world can answer

The C/D world is **sealed**. `src/c_field.py:1–8` is a seeded synthetic field with hidden
unary laws; τ is calibrated from arm 0; `E0` from the measured learner; `N₀` derived;
community size derived (`U = 3D/w`); the field width is described in the D-spec as "the one
remaining outside choice." Checked today: the C/D stack imports **nothing** from the
project's open-membrane stack — no `live_runner`, no `wikidata_source`, no `vault_world`.
The single shared import is `resolving_membrane.classify`, a three-valued scoring predicate.

That discipline — almost no free parameters — is real and unusual. It also means the world
can only be internally consistent. It has no external referent, so nothing it reports can be
*wrong* about anything outside itself.

Which is fine, or fatal, depending entirely on the question:

- **Existence questions** — *can X arise without being installed?* A sealed synthetic world
  is the standard and correct instrument. Tierra, Avida and Life are all sealed. **D-1's
  `P-D1` is exactly this shape and it landed:** first death in round 5 or 6 of all eight
  seeds, with no `die()`, no TTL, no lifespan anywhere in `src/`.
- **Magnitude questions** — *what is β?* A sealed, self-calibrated world cannot answer
  these, because its magnitudes are its own. **This is what killed the West arm**, and it
  was killed correctly: Examination VIII regraded three mechanism rows down, and VIII.24
  found the ninth condition — a reach structure whose cost grows with extent — which is
  environment-side and absent, so β = 1 is predicted however well the other eight are met.
  Worth noting that the arm's own last hope was met and did not save it: the stage-4 spec
  §11.5 held that *"the C-series cannot answer the West question until units can die."* D-1
  gave them death. The mapping closed anyway, for an independent reason.
- **Attribution questions** — *which mechanism produced this figure?* Answerable, but only
  by ablation. **The programme published attributions for thirteen arcs and first ran an
  ablation in the fourteenth.** Every defect the audits found is of this kind.

The programme mixed the three kinds and did not label them. The audits are the bill for the
mixing. The rule that falls out, and it is cheap: **this world may be asked existence
questions freely, attribution questions only with an ablation, and magnitude questions not
at all.**

## 5 · Does the architecture invite the recurring defect?

The author's third bullet asks whether *"a docstring that asserts a property instead of
checking it"* is invited by the architecture or is ordinary carelessness. It is invited, and
the reason is precise enough to be actionable.

In this world **no act is conditioned on what is received.** `publish` publishes everything
held, `ask` and `challenge` fire on internal conditions, nothing is ever declined — that is
the D-series' ruling 1 and 2, and it was refused for a good reason (a chooser is where a
designer writes the answer and calls it emergent). But it has a consequence nobody wrote
down: **if nothing downstream depends on a channel firing, then a channel's death cannot
show up in any outcome.** Liveness becomes unobservable from behaviour. The only way to see
it is to count mints — which is what arc fourteen finally built.

So the absence that `FROM_THERMODYNAMICS_TO_SEMIOSIS` named at the level of the units
(*nothing is at stake*) reappears one level up at the level of the *instrument*: nothing
depends on a channel, so nothing detects its death. The high defect rate is not a separate
failure. It is the same finding, seen by the auditor instead of by the unit.

This matters for the verdict, because it means the defect rate is **diagnostic rather than
chronic**, and it predicts its own decline: in a world where acts are conditioned, a dead
channel starves something and somebody notices. D-1 is the first step (an inert channel now
*costs*), and the slot-question is the second (a channel that can carry something no other
channel carries can finally be load-bearing).

It is worth stating the counter-case plainly, because it is not weak: three of the audit
log's own sentences carried the same defect into review, and those were caught by a
reviewer, not by any structure. Some of this is ordinary carelessness. But carelessness
alone does not explain why the *same* defect recurs in the *same* shape in four independent
places, and structure does.

## 6 · The verdicts

**U1 — is the instrument unsound? NOT ESTABLISHED, with a named residue.**

No published figure has been falsified by a defect. Every figure the audit computes was
re-derived and matched; what was corrected was three *attributions* and five *stale narrated
numbers*. The residue, stated because the audit itself states it: three figure families sit
outside the audit's figure set (`corroboration_calls()`, `true_defeats`/`true_held`,
`witnesses`) and are carried by an argument that a dead channel is a pure no-op, not by
re-derivation. The new guard admits two blind spots — a channel never *called*, and a
channel live-but-inert — and one instance of each is standing in the tree right now
(`whom_to_ask`; `Unit.answer`). That is a real limitation and it is not an unsound
instrument. **Remedy: §7's R1–R3, all cheap, none touching subject matter.**

**U2 — is the question unanswerable with this instrument?**

- **West / magnitude: YES, ESTABLISHED, and already ruled.** The remedy is bookkeeping, not
  runs. Continuing to measure exponents here would be the untenable move, and the project
  has already stopped.
- **Emergence: NO — and this is the load-bearing correction.** It has *looked* established
  three times, and each time the blocker turned out to be a property of one method rather
  than a premise. Premise 3 was thought to forbid the twin control; ruling 2 (2026-07-30)
  showed premise 3 governs content divergence while the control probes policy divergence,
  and `apertures_for(twin_of=)` was built (`src/c_field.py:370`). "Nothing to sort" was
  thought to be the blocker; `ObserverNoise` was built and the arm re-run, and the blocker
  moved again. The current blocker is the shape of a question — two methods in one
  unprotected file — inside a stage that was designed, examined, pre-registered and then
  passed over. **Answerable. Unattempted.**
- **Stake: NO.** It was answered once already, positively.

**U3 — is the question not worth answering? REFUTED by the record.** Findings here have
moved doctrine repeatedly and against interest: Examination VIII regraded three published
rows down, D-1's mortality result changed what the D-series claims, the silence-window
finding survived as the one mechanism that ever discriminated on a law's truth, and three of
six pre-registered priors were refuted in print in the last arc alone. A programme whose
findings change its own commitments is answering questions that matter to it.

**The overall verdict, stated so it can be disagreed with: the path is not untenable. One
arm is finished and should stop being counted as live; one arm has spent four arcs
converging on a stage that was designed six days ago and never built, and should build it;
one arm is young, healthy, and has produced the project's first result that nothing was
installed to produce. What is untenable is the current *ratio*, and its cause is identified
in §3.1 — not carelessness, but a ruled re-ordering whose second half was never picked back
up.**

## 7 · What would have to be given up

Named, because "untenable" without a list of what dies is a mood.

**If U1 had been established** (a falsified figure), what dies is the C-series' published
figures and everything resting on them — the stage gates, the silence-window finding, and
D-1's calibration by way of the field it inherits. It was not established.

**If the emergence question were genuinely unanswerable**, these commitments would have to
go, in this order:

1. **"Install the problem, never the solution."** This is the one that would hurt, and it is
   worth being clear that **the queued change does not cost it.** A slot-question is a
   widening of what a channel can express — a general capacity — not a strategy. The rule's
   own wording permits it: *encode general capacities; let strategies be found.* A chooser
   would cost it. A credential mark would not (it is a public inscription; who earns one is
   still found).
2. **Premise 3**, units differing only by aperture — already partly amended by ruling 2.
3. **Rulings 1 and 2 of the D-series** (nothing declined, no chooser) — the source of
   deadness-invisibility, and *not* required for the queued change.
4. **"The repo evolves models, never modelers."** D-3 (habits as ink) gives this up in the
   sanctioned way: policy in the same medium as content, so it can spread and die, rather
   than a genome with a `typify` bit.

**Already given up, and correctly:** the West mechanism claims (three rows regraded,
Examination VIII §5.1), `net_score`, and the demand-normalised τ.

## 8 · What I recommend the author rule

**(a) Build stage 4 before any new measurement arm.** Its three parts and their priors were
settled by the author on 2026-07-30 and are still unbuilt: the slot-question (§11.2(a)), the
doubt metric reordering a fixed budget (§11.2(b)), alarm reliability (§11.2(c)) — plus the
public half of the two-layer reliability ruling, a credential as a mark. All of it is
already pre-registered against; `P-H1`, `P-H2`, `P-H3` and the pinned zero baseline exist
and can fail. **Stage 5 has now been built and has paid**, so the §11.5 ordering objection is
spent rather than outstanding. This *is* the queued `c_unit.py` sitting,
and §3 argues its scope should be stated as **the shape of a question**, not as three
channel defects: D-A1, D-A2 and `whom_to_ask` are three symptoms of the one property, and
scoping the sitting by the property makes the *retire it* branches legible (corroboration
may not deserve to be a distinct act; `answer` may not deserve to be a distinct method).

**(b) Adopt three prose disciplines, so audits become obligations at write time rather than
arcs after the fact.** All three are enforceable and none touches subject matter:

- **R1 · attribution requires ablation.** No sentence may credit a mechanism for a figure
  unless a muted arm moved that figure. Would have caught all three wrong attributions and
  D-1's false docstring.
- **R2 · a narrated number must be generated or asserted.** The five stale figures survived
  because *not one narrated count was checked* — every clause the gates assert is an
  inequality, a zero, or a cross-arm equality.
- **R3 · an arm declares the channels it plays.** This closes the guard's first blind spot,
  which the audit names and cannot fix: `ChannelTally.silent()` requires `calls > 0`, so a
  channel nobody invokes reads clean.

**(c) Label every prior by question kind** — existence, attribution, or magnitude — at
pre-registration. Magnitude priors are refused in this world by construction; §4 gives the
reason. This one line of bookkeeping is what would have prevented the West arm from
consuming six runs.

**(d) Retire the West arm from the live list.** Not the frontier — the *arm*. Examination
VIII priced the entry at nine conditions; the instrument cannot meet condition (3) and D-1
was designed on the explicit statement that it is not an attempt to recover the
correspondence. Keeping it on the roadmap as live is the same class of error as the wrong
attributions: a sentence outrunning its evidence.

## 9 · The limits of this assessment

Stated rather than implied, on the same principle the audit used.

- **It ran no experiment.** Every quantitative claim is a citation to `runs/` or to a
  docstring; the only things checked directly are structural facts about the current tree
  (which methods exist, which parameters are passed, which modules import which), and those
  are marked where they occur.
- **It did not re-derive any figure.** If a published number is wrong for a reason no
  channel touches — the class the audit found by accident — this assessment would not see
  it.
- **It is not adversarial.** No panel was mandated to refute it, and it was written by the
  same process that wrote the sentences it is judging. Its §3 finding in particular is the
  kind of tidy convergence that should be attacked before it is believed: five arrivals at
  one cause is either a real finding or a narrative imposed on five ordinary bugs, and the
  cheapest way to tell is to build the slot-question and watch whether `occ_bite` moves off
  zero. **That test already exists and is already pinned.**
- **It takes the C-series' figures as sound** on the strength of arc fourteen's audit, whose
  own universal rests on a no-op argument rather than on re-derivation for three figure
  families.
