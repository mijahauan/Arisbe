# Teaching Pack — running an Existential-Graphs course on Arisbe

> For the instructor. Arisbe began as a research instrument, but its grader,
> its challenge ladder, and its worked-chain exemplars add up to a genuine
> teaching surface. Students **draw** logic instead of typing it, and the engine
> **grades by meaning, not by pixels**. This page shows what exists today, the
> pedagogy it supports, how to author your own problem sets keyed to a syllabus,
> how to grade a stack of submissions, and, honestly, what an LMS would still
> have to add. It disposes documentation-gap **G6** of [STORM_DOCS_AUDIT.md](STORM_DOCS_AUDIT.md).

## The model of good teaching we're building toward

What does good EG teaching look like? The gold standard remains a worked,
step-by-step derivation where **each step applies exactly one permission and is
drawn on its own page** — an animation of thought. The finest example we know
comes from Dr. Marc Champagne's *"Thirty-Nine Exercises in Existential Graphs"*
(PHIL 1150), whose structure merits stealing wholesale:

- **A first hand-out states the arguments in words** — 20 of them, walking the
  propositional canon: modus ponens, modus tollens, double negation,
  conjunction intro/elim, disjunction, hypothetical syllogism, constructive and
  destructive dilemma, De Morgan.
- **A second hand-out redraws them as graphs** — premises and conclusion as
  ovals-and-letters; the student supplies the steps.
- **Each solution unfolds as an animation:** one graph per page, each captioned
  with the single permission applied — *Deiterate · Erase · Double cut ·
  Insert · Iterate*, ending in *Conclusion*.
- **Two registers:** *direct* derivations (transform premises into the
  conclusion) and *indirect* derivations (assume the conclusion **false**, then
  drive to a **contradiction** — Champagne's lovely coinage, a *"contrapiction"*:
  the same graph asserted and denied at once).

Arisbe's contribution makes those hand-drawn animations **machine-generated
and machine-checked**. Every step applies a sound Dau rule, every intermediate
graph is §3.3-attested (picture = proposition), and the whole chain replays as a
storyboard. What a professor draws by hand for one argument, Arisbe produces
from a proof script — correctly, and for any argument.

### One vocabulary note, up front (Peirce's five ↔ Dau's six)

Champagne (following Peirce) names **five permissions**: insertion, erasure,
iteration, deiteration, double-cut. Arisbe (following Dau, its guarantor of
correctness) uses **six rules** — the same moves, with the double-cut split by
direction:

| Peirce/Champagne permission | Arisbe/Dau rule(s) |
|---|---|
| Insertion (in a negative area) | **INS** |
| Erasure (from a positive area) | **ERA** |
| Iteration | **IT+** |
| Deiteration | **IT−** |
| Double-cut (draw / remove) | **DC+** / **DC−** |

Teach either vocabulary; they denote the same calculus. Point students at
[FIELD_GUIDE_AND_DRAGONS](FIELD_GUIDE_AND_DRAGONS.md) for the eight classic
pitfalls in Peirce's own terms.

## What Arisbe gives a teacher today

| Capability | What it does | Where |
|---|---|---|
| **Grade by meaning** | `grade(target, attempt) → DiffReport`: isomorphism (`same_graph`) for pass/fail, plus a **legible diff** in EG vocabulary (missing / extra / wrong scope / wrong incidence / wrong argument order) when it's wrong. Surface form counts for nothing — a student who draws the right graph a different way still passes. | `challenge_mode.py`, `egi_diff.py` |
| **A difficulty ladder** | A curated `CHALLENGE_BANK` of drawable targets, each introducing *exactly one* new correspondence skill, from `(man "Socrates")` up to a shared line of identity crossing a cut boundary. Each rung carries the *dragon* it trains + the antidote shown on a wrong grade. | `challenge_mode.py`; `GET /ergasterion/challenges` |
| **Draw-then-read composition** | Students place typed marks on a free canvas (no live EGI), then "fix" the drawing into a real EGI via `read-drawing`/`fix-drawing`. The grader runs on the fixed graph. | `drawing_to_egi.py`, `eg_reader.py`; the freeform canvas |
| **Worked-chain exemplars** | Real, replayable proofs seeded into the corpus — the propositional quartet (all six rules), Peirce's Law, Barbara, the *Praeclarum Theorema*. Each is a `ProofChain`: one captioned step per rule, every intermediate §3.3-attested. | `tools/build_*_chain.py`, `tools/build_propositional_exemplars.py`; [EXEMPLARS](EXEMPLARS.md) |
| **The animation lenses** | Organon's **Storyboard** lens draws one frame per state with the rule + legible diff between frames; the **Derivation-DAG** lens shows branch structure. This *is* Champagne's one-permission-per-page animation, generated and attested. | `web_viewer/js/storyboard-lens.js`, `derivation-dag-lens.js` |
| **Argument register** | The **Graph ↔ Argument** switch makes "unfixed sketch" vs "fixed graph" unmistakable and enforces the rule contract: no transformation rules on an unfixed graph, no meaning-change on a fixed one. | the Ergasterion workshop |

## Authoring your own problem set (keyed to a syllabus)

Today the challenge bank lives as a curated Python list (`CHALLENGE_BANK` in
`challenge_mode.py`) of ten hand-authored rungs, each a `Challenge` dataclass.
To build a set for *your* syllabus, add rows; the routes and the in-app ladder
follow automatically. The linear-format registry works the same way. Declare in
one place, and everything follows.

```python
Challenge(
    id="modus-tollens",
    title="Modus tollens",
    prompt_egif='~[ (P) ~[ (Q) ] ] ~[ (Q) ]',   # if P then Q; not-Q  ⊢  not-P (as a target to draw)
    difficulty=3,
    hint="A conditional is a nested double cut; the second premise denies the consequent.",
    dragon=2,                                     # trains the empty-cut / negation pitfall
    temptation="Reading the outer cut as 'or' instead of 'not'.",
    antidote="A cut denies its whole contents; nesting two makes 'if…then'.",
)
```

**Two disciplines when authoring targets:**

1. **One new skill per rung.** Champagne's exercises each add a single move;
   mirror that. Arisbe's bank comments each rung with the correspondence skill it
   introduces — keep that habit so a wrong grade points at exactly one thing.
2. **Always verify your target against the parser and FOPL.** A teaching EGIF
   that looks right can be subtly wrong. Round-trip it (`same_graph` after
   parse→generate) and check its FOL reading (`egi_to_fol`) before you assign it.
   The field guide teaches this as its standing lesson — *never hand a class an
   unverified graph.*

For a ready-made scaffold, the **20 Champagne arguments** map directly onto
Arisbe targets. Author them as a `difficulty`-ordered bank (propositional first,
then the dilemmas), attach the matching dragon/antidote, and you have a
correspondence-graded version of the classic hand-out. The propositional
exemplars (`tools/build_propositional_exemplars.py`) already cover the same rule
inventory — read them for the canonical worked solutions.

## Grading a stack of submissions

The grader works as a pure function, so batch grading amounts to a loop — no
session, no state:

```python
from challenge_mode import get_challenge, grade
from egif_parser_dau import parse_egif

target = parse_egif(get_challenge("modus-tollens").prompt_egif)
for student, submission_egif in submissions:          # submission = the fixed EGI's EGIF
    report = grade(target, parse_egif(submission_egif))
    passed = not report.findings                      # same_graph ⇒ no findings
    print(student, "PASS" if passed else "FAIL:",
          report.summary,                             # "denotes the same graph" / "N differences"
          [f.message for f in report.findings])       # the legible, per-difference feedback
```

Because grading rests on **content-aligned isomorphism**, two correct answers
that look nothing alike both pass, and a near-miss comes back with *why* in EG
terms ("Q is in the wrong cut" / "the argument order of `loves` is reversed"),
not a diff of coordinates. That legible-diff feedback carries the pedagogical
payload. Students learn from *how* they were wrong.

For freehand (drawn) submissions rather than typed EGIF, run each through
`fix-drawing` first (`drawing_to_egi.build_egi_from_drawing`) to recover the EGI,
then grade as above. An ill-formed drawing returns validity feedback
(`drawing_validity`) instead of a grade — and that feedback itself instructs.

## What a student hands in — the gradeable artifacts

| Artifact | Auto-checkable? | What it's good for |
|---|---|---|
| **A drawn/fixed graph** vs a target | **Yes** — `same_graph` + legible diff | "Represent this argument's conclusion." Objective, surface-independent. |
| **A `ProofChain`** (premises → conclusion, step by step) | **Yes** — every step is a sound Dau rule (`RuleInteraction` refuses an illegal move) and every state is §3.3-attested; replayable as a storyboard | "Derive it, showing your work." The machine confirms each step is legal; you assess strategy. |
| **A freehand drawing** (pre-fix) | **Partly** — `drawing_validity` flags dangling lines, overlapping cuts, straddles | "Draw it well." Catches malformed pictures before meaning is even read. |
| **An interpretation** ("in what world does G make sense?") | **No** (by design) — this is the interpretation register; the peel gives a verdict + witness, but the *choice of model* remains the student's argument | Seminar-style: assess reasoning, use the verdict as evidence. |

The division carries the point. **The machine grades formation and legal
transformation; a human grades interpretation and strategy** — and the tool
tells you honestly which is which (the soundness boundary again,
[SOUNDNESS_BOUNDARY](SOUNDNESS_BOUNDARY.md)).

## Direct and indirect derivations (Champagne's two registers) in Arisbe

- **Direct.** Author the premises as the starting EGI, then apply the six rules
  in a `ProofChain` (`proof_authoring.py`, driven by `tools/build_*_chain.py`)
  until you reach the conclusion. Each `ChainStep` records the rule and produces
  a §3.3-attested state; the Storyboard lens renders the animation.
- **Indirect (reductio / "contrapiction").** Add the **negated conclusion** to
  the premises and derive a contradiction — a graph that asserts and denies the
  same thing, which the calculus recognizes (an empty cut / a scroll collapse).
  The propositional exemplars include the reductio pattern; the empty-cut
  challenge rung teaches the underlying "a cut around nothing = the strongest
  denial" idea the contrapiction rests on.

Point students at [ENDOPOREUTIC_GAME_GUIDE](ENDOPOREUTIC_GAME_GUIDE.md) once they
can derive — the Agon turns "prove this" into a two-player dialogue, which is how
Peirce meant the graphs to be *lived*, not just written.

## Honest gaps (what an LMS still needs)

These stand named, not hidden. None touches the calculus, so all of them amount
to additive web-tier work:

- **No multi-user / roster / gradebook.** Sessions live in memory in a single
  process; no per-student identity exists, and no record persists of who
  submitted what. Grade in a batch script, or add a thin roster layer around the
  pure `grade()` function. See [DEPLOYMENT_AND_MULTIUSER](DEPLOYMENT_AND_MULTIUSER.md).
- **The bank is code, not a UI.** Authoring targets means editing
  `CHALLENGE_BANK` (or calling `grade()` directly with your own targets). A
  teacher-facing "author a problem set" screen does not exist yet.
- **No auto-generated syllabus.** The difficulty gradient comes hand-curated. A
  generator that emits a rung per skill from a spec remains a natural, unbuilt
  next step.
- **Submission collection is your job.** Arisbe grades what you hand it; getting
  N drawings *from* N students (upload, LMS integration) lies outside the tool.

The teaching primitives stand real and strong: surface-independent grading,
legible EG-vocabulary feedback, attested worked chains, the animation lenses.
The classroom *plumbing* around them remains a small, honest integration you
own.

---
*Related:* [EXEMPLARS](EXEMPLARS.md) (the worked chains to read) ·
[FIELD_GUIDE_AND_DRAGONS](FIELD_GUIDE_AND_DRAGONS.md) (the eight pitfalls) ·
[GETTING_STARTED](GETTING_STARTED.md) (the newcomer on-ramp) ·
[FREEFORM_COMPOSITION_AND_LEARNING](FREEFORM_COMPOSITION_AND_LEARNING.md) (draw-then-read + challenge mode) ·
[ENDOPOREUTIC_GAME_GUIDE](ENDOPOREUTIC_GAME_GUIDE.md) (logic as a two-player game).
