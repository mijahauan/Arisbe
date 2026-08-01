# Lessons

## 2026-07-15 — Do not re-litigate Departure II (the "SA = assertion at depth 0" gloss)

**The mistake, made recurrently across sessions:** when assertion/utterance came
up, the assistant repeatedly presented the textbook gloss — "residence at depth 0
is precisely what assertion is; Peirce's sheet holds asserted graphs bare; the
utterance is the act the calculus presupposes" — as if it were the project's
position, and defended it against the author.

**The fact:** that gloss is *the position Arisbe rejects* — registered as
**Departure II** in `docs/FIDELITY_AND_DEPARTURES.md` §3 ("nothing contingent can
be said at level 0; level zero bears form, not content"), tried in
`docs/ADVERSARIAL_EXAMINATION.md` (survives with amendment; firmest ground of the
three; the "one unconditioned posit of M" concession later *retracted* — the
gapless thesis stands: the blank alone is unconditioned, and it asserts nothing).

**The rule:** before arguing any question about assertion, utterance, warrant,
posits, or what depth 0 constitutes, read FIDELITY_AND_DEPARTURES §3 and
LEVEL_ZERO_AND_THE_REGISTERS first, and argue *from* the register. The settled
doctrines live in the fidelity/examination docs, not in the assistant's Peirce
scholarship. More generally: when a foundations discussion feels like the author
is proposing something new, check the departure register first — the author may
be applying their own settled doctrine that the code or the assistant has been
under-applying (here: `model_acts.assert_into` implements the forbidden move the
register names).

See `docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE.md` §6 for the full mapping.

## 2026-07-31 — Search by role, not by name; and prose figures are unprotected

**The mistake, made four times in one pass.** Sizing and verifying the
`net_score` retirement by `grep "assert.*net_score"`. Each search matched the
statistic's *name*; what mattered was its *role*. It missed (a) comparisons
whose `net_score` reads happen upstream — `live_pairs.append(sum(u.ledger.net_score …))`
feeding a later `assert sum(live_pairs) > sum(mute_pairs)`; (b) more of the same;
(c) `assert live_total > mute_total`, whose variables contain no "net" at all —
found only because a reviewer noticed the *corrected* grep had the same defect;
and (d) `shed_misses > shed_hits`, which is the forbidden comparison rearranged.
The `tasks/todo.md` sizing said "18 assertions" and the real surface was larger
and differently shaped.

**The rule.** To verify that a quantity no longer plays a role, enumerate every
**read** of it and trace each variable to every consuming assertion. Require each
consumer to fall in a named, closed set of permitted kinds. A grep over assertion
text is not a verification method for this class of question. And note (d)
separately: **unfolding an expression into its components does not remove it** —
a prohibition on a comparison is spelling-independent, so re-expressing
`a.net > b.net` as `(b.misses − a.misses) > (b.hits − a.hits)` needs annotating,
not claiming gone.

**The companion mistake.** Stale narration took four correction rounds in one
file, each round fixing only what the finding named. Figures moved by a change do
not cluster where the change happened: the window moved a number in
`test_c_channels.py`, and the *narration* of it lived in `test_c_stage_gates.py`,
whose tests all passed. **Only pinned assertions fail when the world moves;
every figure living in prose is unprotected**, and a passing test is no evidence
its docstring is true. When a change moves measured figures, audit *every numeral*
in the affected prose and classify each — invariant, moved, or cannot-determine —
rather than fixing what failed.

## 2026-07-31 — Do not build the observer's instrument beside the act

**The correction.** Asked for a per-unit cost component, the assistant designed a
new module (`src/c_score.py`) with thirteen hand-maintained act counters. The
author refused it: *"a symptom of our being in this territory — of thinking we can
get ahead … is how complicated we have gotten in this modelling in Python rather
than the understanding appropriate to a kytos."*

**The fact.** An act's effect resides in its **report** inside the membrane, in
**resources** outside it, and in the **shared reports** among kytē — and in none of
them does it reach the act's own decision (`docs/THE_KYTOS.md` §1.3). Two of the
three already existed: `MarkBoard` reports every channel act, attributed and dated;
`MembraneLedger` holds the bets. Only the denominator was missing, and it was one
integer. The elaborate instrument would have duplicated two residences in a
private register and invented the observer the doctrine refuses.

**The rule.** Before building machinery to measure the system, ask where the
quantity already resides. Prefer *reading* an existing residence to *instrumenting*
a new one; put an observer's reading in the tests, never in `src/`, where it would
hand a unit a faculty it does not have. And check the temporal direction: a report
is written after its act and read no earlier than the next occasion — an instrument
that changes the act it measures has got out in front of it, which is testable
exactly as it sounds (instrumenting must move no measured figure).
