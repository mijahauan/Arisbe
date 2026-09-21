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

## 2026-08-01/02 — Examination VIII and the provenance build

**A pre-registered prior can be wrong in its SPECIFICATION, not only in its
prediction.** `P-W1` demanded conserved flow + branching topology + minimized
dissipation. That is right for West's metabolic family and over-demands for the
socioeconomic one, whose minimal premise is a scale-free accessibility gradient.
Pre-registration protects against motivated *reading* of results; it does not protect
against a mis-specified test. Only an adversary with primary sources caught it.
**Rule:** when mandating a defending panel, license it to correct the reading, not
only to contest the verdict.

**Search by role, not by name — again, and the failure mode was "the concept felt
new".** `src/provenance.py` already existed (bibliographic bundle) and the collision
surfaced only when `tests/test_provenance.py` refused to be overwritten. No grep was
run because the *idea* was new; the word was not. **Rule:** grep the vocabulary before
naming a module, especially when confident the concept is unprecedented.

**A reading no test can reach is not a reading.** The ◇/`possible` column of
`source_reliability` was dead code through every linear test — nothing in the suite
could produce it — and writing one branching test exposed a real bug (a source's
record depended on branch write order). Same shape as the examination's own finding
that a sweep capped at 4→6 units cannot measure invariance across an order of
magnitude. **Rule:** for every enumerated outcome a function can return, ask which
test produces it; an unreachable branch is untested, not merely uncovered.

**Prefer probing the running system to reasoning about it.** Three design defects —
generic antecedents over-firing, quotations silently breaking Horn recognition,
quotation-bearing graphs having no linear form — were found in four short probes
before a line of production code existed. Two of the three fail *silently*: the rule
stops firing and nothing raises. Argument would not have found them.

**Two defects can cancel, and fixing one alone reads as a regression.** Repairing the
materializer's quantification defect (a line's area *is* its quantification, Ψ/Φ
p.207–208) turned `test_clif_imported_names_with_hyphens_do_not_break` red — not
because the fix was wrong, but because that test's CLIF fixture reused one binder
name across two `forall`s, and the parser's binder-scoping defect (plan finding 3)
collapsed them into a single sheet-level line. The materializer then misread that
line as a universal variable, and the two wrongs produced the right answer. **Rule:**
when a correctness fix breaks a test, first ask whether the test was passing *because
of* a second defect — reproduce the fixture's intermediate form (here: generate the
EGIF the parser actually built) before touching the fix or the assertion. A masked
defect is the likeliest explanation when the fix is Dau-cited and the break is remote
from it.

**Check whether the module already disagrees with itself.** `model_materialization`
rendered a sheet-level line as a fixed individual `_i1` in its own output while its
rule extraction treated the same line as a universal variable. That internal
contradiction was the strongest single piece of evidence for which reading was
intended, and it argued for *grounding* the line rather than refusing the scroll —
the fix that preserved Peirce's modus ponens instead of losing it. **Rule:** before
choosing between "refuse it" and "read it correctly", look for a place where the
module has already committed to one of the two.

**A survey that contradicts the written plan gets verified before it gets relayed.**
A delegated survey reported that `theory_query` carried its own copy of the
quantification defect, contradicting the plan's claim that it "merely surfaces"
the materializer's. Re-running the two-graph discriminator directly confirmed it
(both readings gave the identical answer, so no area was consulted) — and also
refuted the plan's claim that `semantic_game` shared the defect, which it does not.
**Rule:** a subagent finding that revises a standing document is a claim, not a
result, until reproduced in the main session.

**I stopped maintaining this file halfway through a session, and never opened it at all.**
On 2026-09-19/21 three lessons landed here at the first commit, and everything learned
afterwards went into `CURRENT_PLAN.md` and `tasks/todo.md` instead, sorted by topic rather
than by kind. CLAUDE.md says "Review lessons at session start"; I did not. **Rule:** this
file is the long record, but the *load-bearing* cautions belong in `CLAUDE.md`, which
arrives in every session whether or not I remember to look — see its "Standing cautions".
Adding a lesson here and nowhere else is writing it into a drawer.

**Prose decays within hours; a test does not.** In one session I wrote "don't change a
tree under a running measurement" in a message and then broke it about an hour later, by
editing a JSON the suite reads at *runtime* rather than a module imported at collection.
In the same session, the lessons that held without any effort were the ones that had been
turned into instruments — `test_no_new_test_that_cannot_fail`,
`test_every_implemented_rule_is_judged`,
`test_every_recorded_act_is_reachable_by_this_gate`, `test_calculus_map.py`. **Rule:**
triage each lesson by whether it can be made to *fail*. If it can, build that and skip the
prose. Reserve writing for the ones that are genuinely judgment — "check whether the module
already disagrees with itself" cannot be a test, and paid off twice.

**The knowledge graph went four days stale while a hook reminded me about it on nearly
every command.** `graphify-out/GRAPH_REPORT.md` was last built 2026-09-17; I ran three
days of work without reading it, without a single `graphify query`, and without
`graphify update .` (which is AST-only and costs nothing). The PreToolUse hook printed the
reminder dozens of times. Every mapping error I made in those days was a *search* error —
finding the three copies of one semantic rule, locating callers of an engine entry point,
mapping modules to the suites that test them, and that last one I got wrong twice with
grep. **Rule:** for "where else does this live / who calls this / what tests this", the
graph is the tool, and a reminder that fires and is ignored is not a mechanism.

**A stale instrument is worse than none, because it still answers.** The graph would have
answered questions about a tree four days old with no indication it was doing so — the same
shape as a pinned extent nobody re-ran, or a test file pointing at a renamed directory.
**Rule:** anything that caches an answer needs its freshness visible at the point of use,
or a step that refreshes it as part of finishing work.
