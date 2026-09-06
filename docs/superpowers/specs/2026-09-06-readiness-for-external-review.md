# Readiness for external review: the three modes assessed

**Date:** 2026-09-06 · **Status:** assessment + proposal, nothing built · **Ruling required**

The author asked, before any further work on the West concordance or the Life
comparison, whether Organon, Ergasterion and Agon cohere well enough in
appearance, function and original purpose to put in front of John Sowa,
Frithjof Dau, or Ahti-Veikko Pietarinen. This is the answer, and what follows
from it.

---

## 1. The judgment, in one paragraph

The engine is ready and the front door is not. Every route layer passes:
Organon 30/30, Ergasterion 82/82, Agon 184/184, and the six pages all serve
200 with no console errors in Ergasterion or Agon. The correspondence
machinery — the thing the project exists for — is built, guarded and running
on all 52 corpus universes. But a scholar who follows a link to the landing
page reads text at roughly 1.3:1 contrast and **cannot reach any of the three
modes**, because the cards sit below a fold the page refuses to scroll past.
Everything else in this document is smaller than that.

The shortfall is not in the calculus. It sits in the first five minutes.

## 2. What was actually measured

Four parallel assessments, each required to distinguish what it ran from what
it read, plus independent re-verification by the author's assistant of every
claim this document rests on.

| Surface | Result | How |
|---|---|---|
| Organon routes | 30 passed, 0 failed | ran |
| Ergasterion routes + freeform + challenge | 82 passed, 0 failed, 0 skipped | ran |
| Agon (12 files) | 184 passed, 0 failed, 0 skipped | ran |
| Quality gate | core protection + 152 core tests + syntax, exit 0 | ran |
| Server | `/` `/organon` `/ergasterion` `/agon` `/import` `/book/` all 200 | ran |
| Corpus | 52 UoDs, 34 with real chains, 6 genuinely branching | ran |
| Full suite | **4614 passed, 217 skipped, 1 xfailed, 0 failed, 0 errors** (41m23s) | ran |
| End-to-end (browser) | 17 passed once the Chromium binary was present | ran |

## 3. The findings, ranked by first contact

**F1 — The landing page cannot reach the three modes.** `index.html:9` sets
`background: var(--canvas-bg, #1e1e2e)`; `styles.css:17` defines
`--canvas-bg: #ffffff`. The dark fallback was written for a dark page and the
loaded stylesheet overrides it white, leaving light-grey text on white.
Separately `styles.css:32-37` sets `html,body{height:100%;overflow:hidden}`,
which `index.html` never overrides. Measured: viewport 896px, content 1533px,
`scrollable false`. The Organon, Ergasterion and Agon cards all sit at 929px.
`index.html` is the one page loading neither `design-system.css` nor
`mode-nav.js`. **Two CSS lines.**

**F2 — The examples named for these three reviewers are the corpus's
weakest.** All 14 literature UoDs carry a slug as their title: Sowa's own
example renders as "Sowa Cat On Mat", Dau's as "Dau 2006 P112 Ligature",
Peirce's as "Peirce Cp 4 394 Man Mortal". None has a chain, annotations, or
linear forms on disk, so the lens rack collapses and the chain player hides.
Rich CSL records already sit in each `provenance.json` and already render
lower on the page — the slug is only what the eye meets first. **No code; an
hour of curation.**

**F3 — Two letter claims are false, and no letter carries a URL.**
`LETTER_SOWA_DRAFT.md:16-18` claims round-trip "against some ninety canonical
examples"; the corpus holds 52. `LETTER_PIETARINEN_DRAFT.md:61` says MS 514
"renders here through the real engine"; MS 514 is not in the corpus. All four
letters promise "links you can walk" and cite nothing. Sowa and Pietarinen are
precisely the readers who check.

**F4 — One-line arity bug silently disarms the ontology guard.**
`agon.py:463` calls `_browse_facets(entry)`; the function takes
`(entry, tomos_root)` (`organon.py:98`). The `TypeError` is swallowed by a bare
`except` two lines down, so `kind` is `None` for all 52 rows. Consequently the
model picker's provenance grouping collapses to one flat list, and the guard
that turns materialization on for a T-box never fires — all 7 ontologies
(SUMO, FOAF, Porphyry) peel **vacuously**. The comment immediately above the
broken call names this exact trap. This is Sowa's first click.

**F5 — Vacuous satisfaction is ranked as holding.** `/agon/where-it-holds`
returns a model containing zero mammals as satisfying "every mammal is
warm-blooded" with `verdict: true, fit: 1.0, residue: []`, ranked beside the
model where it genuinely holds. Three logicians will find this in one sitting.

**F6 — The game states a win condition it cannot reach.**
`endoporeutic_game.py:26` lists "a player has no legal moves → that player
loses"; `_check_outcome:456` implements it; `has_legal_moves:329` returns
`bool(state.current_egi.area)`, which the sheet makes permanently true — and
that function's own docstring says so. One file asserts a rule and refutes it
300 lines later. Pietarinen will ask what makes this the Endoporeutic Game.

**F7 — The end-to-end guard tests for the wrong thing, so a fresh clone sees
errors instead of skips.** Every E2E guard is `pytest.importorskip("playwright")`
— the *package*, which the project installs; the browser binary, which it does
not. On a machine without that binary each test dies in `chromium.launch()`
rather than skipping: 14 in Organon, 3 in Ergasterion, 12 in Agon. The
Ergasterion failure additionally leaves a uvicorn running on port 8137, because
teardown never runs on an errored test. CLAUDE.md's claim that these skip
cleanly is false.

*Correction, recorded because it changes the finding's weight:* during this
assessment one of the investigating agents ran
`playwright install chromium-headless-shell`. The binary is therefore now
present on this machine, and the 17 Organon + Ergasterion E2E tests **pass**
(verified: 17 passed in 72.69s), as does the full suite. The defect is real but
its scope is narrower than first reported — it is a fresh-clone and
continuous-integration condition, not a permanent local one. The fix is to probe
for the binary rather than the package, and to add `try/finally` teardown.

**F8 — The named guard for linear-format round-trip does not run.**
`test_tomos_parsing.py:11` points `CORPUS_ROOT` at `corpus/corpus`, which does
not exist; all 3 tests skip silently. CLAUDE.md names this file as the guard
for EGIF/CGIF/CLIF round-trip across "87+ tomos examples". Other tests may
cover the same ground, but the guard the documentation names is dead.

**F9 — Prototype tells in the flagship demo.** The freeform canvas raises a
blocking native `window.prompt()` for every name (`freeform-canvas.js:288,
295, 390, 393`), so drawing a five-predicate graph means five OS dialogs.
Argument order is assigned by creation order (`:406`) with no reorder
affordance — get `(loves *x *y)` backwards and you erase and redraw. For this
audience argument order is not a detail. Agon prints raw UUIDs beside the
diagram (`agon.html:279`).

## 4. A methodological note the author will want

My first draft of this section claimed the browser layer never runs, and that
the three modes' SHIPPED status was therefore asserted rather than generated.
That claim is wrong, and the correction is more interesting than the error.

The browser layer does run, and it is green: 17 end-to-end tests pass, and the
full suite is 4614 passed with no failures and no errors. What F1 shows is not
an unrun suite but a **coverage hole in a green one**. Every E2E test enters a
mode directly by URL. Not one of them asks whether a visitor arriving at `/`
can reach a mode at all. So the suite verifies the three rooms in detail and
never checks that the front door opens.

That is the sharper version of the standing rule about generated versus
asserted numbers. The number here was generated. It simply measured something
adjacent to the thing that was broken — which is the failure mode that a
passing suite is least able to warn you about, and the reason F1 survived to be
found by pointing a browser at the page and reading the pixel positions.

The cheap durable guard: one E2E test that loads `/`, asserts a contrast ratio,
and asserts that each of the three mode links is reachable at a standard
viewport.

## 5. The author's rulings (2026-09-06)

- **Q1 — Tier 0 *and* Tier 1 before any letter.** No letter goes out until all
  three recipients can find satisfaction, because each will explore the whole
  rather than only his own area.
- **Q2 — the taxonomy presupposes the naive outcome.** Confirmed against the
  docs, and the diagnosis is sharper than the question assumed. See §6.
- **Q3 — build substantive exemplars**, two or more, matched to the three
  authorities' expertise, together covering the diachronic UoD, the calculus,
  ontology development, and the EPG.
- **Q4 — letters carry plain text plus attached artifacts** (the calculus in
  steps; ontology and domain modelling; alternative paths and their
  resolution; the EPG's effect on model evolution), plus a **functional URL**
  for direct interaction. A greenfield checkout path follows if interest lands.

## 6. Q2/Q5 resolved: a misplaced module, not a missing register

**Superseded 2026-09-06 by the author's clarification.** An earlier draft of
this section concluded that the eliminative EPG "has no move-level
implementation at all" and recommended building one. That was wrong, and the
correction matters because it removes work rather than adding it.

### The author's doctrine

> The EPG proper does not involve proofs or constructions of theoremata — the
> application of the full range of transformation rules. It takes an existing,
> proposed graph and considers its meaning, its interpretation against an
> agreed domain model, to check if it matches. That is the EPG proper that Agon
> exists to play. The construction of proofs properly belongs in Ergasterion,
> where speculation, experimentation, abduction and induction are exercised;
> and when one looks like a candidate of interest to present for testing in
> Agon, a Graphist moves it there to subject it to the EPG.

This is already the stated mode contract (CLAUDE.md: *Ergasterion — transformation
practice*; *Agon — Endoporeutic Game engine*). The code, not the doctrine, is
what drifted.

### The EPG proper is built and correct

`grapheus.py` is a genuine move-by-move extensive-form contest, not a one-shot
evaluation: ownership by polarity, Graphist↔Grapheus swapping on each cut
crossing, an existential phase where the defender witnesses lines and a
conjunction phase where the challenger picks, terminal atoms adjudicated
against M. It applies **zero transformation rules**. Its outcome enum carries
all three exits of the Logical Classification, the stalemate included:

```python
GRAPHIST_WINS  # G holds in M          (TRUE)
GRAPHEUS_WINS  # G fails in M          (FALSE)
INDEPENDENT    # M neither confirms nor denies (UNKNOWN)
```

Its docstring names the third exit in the author's own terms: a frontier the
Grapheus owns where M can only return UNKNOWN "is declined — the inning is
independent, the Agonothetes' honest stalemate."

So stratum 1 of §5's table has no hole. Strata 2 and 3 were already built. The
whole EPG column is done.

### What is actually wrong

`endoporeutic_game.py` implements the **constructive proof game** —
`_PROPOSER_RULES = {INS, IT+, DC+}` against `_SKEPTIC_RULES = {ERA, IT−, DC−}`,
the guide's *proof* table — and is therefore Ergasterion's business by the
doctrine above. Three consequences:

1. **It is misnamed.** It is not the Endoporeutic Game.
2. **Its docstring claims EPG win conditions it cannot reach.** "A player who
   cannot make any legal move loses" is unreachable there because DC+ is always
   available; in the EPG proper that outcome exists and is called
   `INDEPENDENT`. Correct doctrine, wrong module.
3. **Agon's UI exposes it.** `POST /agon/games` + `/move` + `/concede` offers a
   hot-seat *transformation* game in the mode reserved for interpretation.

### Ruling required (Q5, restated)

Not "build or retire", but **where does the constructive game live**:

- **(a) Relocate.** Move the transformation game to Ergasterion as a two-player
  practice register — territories, alternating turns — and rename the module
  (`proof_game.py` / `ProofGame`). Agon keeps interpretation only.
- **(b) Retire.** Ergasterion already applies all six rules through
  `RuleInteraction` across 28 routes. The constructive game's distinct content
  is only the polarity/territory constraint and turn alternation. If that is
  not wanted as a practice mode, drop it and let Ergasterion's existing rule
  machinery stand.

Either way the docstring's win conditions move to where they are true, and
Agon's page loses a register that does not belong to it.

**Consequence for the exemplar arc:** E6, the two-player EPG inning, is
*unblocked*. It wants an inning of the contest, which exists — not a register
that needed building. Open question X3 is withdrawn.

## 7. The defect class this review actually found

Three independent findings share one shape. Each green number is real; each
measures a path no visitor walks.

| Green signal | What it measures | What a visitor meets |
|---|---|---|
| 17 E2E tests pass | each mode entered by direct URL | `/` — three doors below an unscrollable fold |
| Suite passes locally | a browser installed out of band mid-assessment | fresh clone — 29 errors, one leaking a server |
| CI passes | CI runs `npm install` (`canonical.yml:32,37`) | documented steps — **nothing renders** |

`node_modules/` is gitignored and `elkjs` is tracked zero times; `elk_worker.js:7`
requires it; the six human-facing install documents mention npm and Node.js
**zero times** between them. A scholar following the instructions gets a server
in which every graph fails with `Cannot find module 'elkjs'`, and
`TROUBLESHOOTING.md` has no entry for it.

The remedy is not more tests. It is one test per untaken path: a landing-page
reachability check, a binary-probing E2E guard, and a cold-clone install job
that runs only what the docs say.

## 8. The revised plan

### Tier 0 — reachable and installable (hours)

1. **Landing page** (F1): give `index.html` the design system, or override
   `overflow`/`height` and the background token. Verify at 1440×896 that all
   three doors are reachable.
2. **Document Node.js + `npm install`** in README, `install.qmd`,
   `GETTING_STARTED.md`; add the `elkjs` symptom to `TROUBLESHOOTING.md`.
   Without this nothing else in this document matters to a remote reader.
3. **`agon.py:463` arity bug** (F4): pass `tomos_root`; narrow the bare `except`.
4. **E2E honesty**: probe for the browser binary, not the package; `try/finally`
   teardown; add the landing-page reachability test from §7.
5. **Cold-clone CI job** that follows only the documented steps and renders one
   graph. This is the guard that keeps §7 from recurring.
6. **Move PySide6 to a `qt` extra.** Qt is already gone from the product: `src/`
   and `tests/` import PySide6 zero times, and the GUI lives in
   `archive/qt-gui-2025/`. What remained was a stale line in the mandatory
   dependency list, plus four orphaned Qt-era scripts in `tools/`
   (`agon.py`, `ergasterion.py`, `drawing_editor_dto_clean.py`,
   `constraint_mode_system.py`) that nothing references. The line carried
   1.1 GB of a 1.5 GB install. **Done: 1.5 GB → 374 MB.**
7. `.python-version` pinning 3.12; correct the test-count figures in
   `install.qmd` ("roughly a thousand") and README (4,125) to the real number.

### Tier 1 — all three recipients satisfied (the Q1 bar)

**Exemplars (Q3) — the largest block, and the one that inverts the earlier
recommendation.** The calculus exemplars are the *thinnest*, not the
strongest:

8. **A single six-rule derivation.** Nothing today exercises ERA, INS, IT±, DC±
   in one chain; `theorem_praeclarum` reaches 5 of 6.
9. **A substantive ligature / Ch. 16–17 exemplar for Dau**, and real chains +
   real metadata for `dau_2006_p112_ligature` and `dau_theorem_proving`, today
   bare graphs with auto-generated titles.
10. **Surface the derived-rule expansion.** `barbara` and `group_identity` show
    a step labelled `UI`, which is not one of Dau's six. It is *sound* —
    `derived_rules.py:52` builds it from IT+ plus a join, and `apply_derived`
    documents the collapse — but the interface never says so. Showing the
    expansion converts Dau's likeliest objection into a demonstration of rigour.
11. **An ontology being *developed*, not imported, for Sowa.** All eight
    imported ontologies carry a 2-step residence chain only; `peirce_order_1881`
    (6 × ADMIT_TO_M) is the sole example of assembly. Nothing shows an imported
    ontology corrected, extended, or refuted in play. `foaf_core` (3 relations)
    is too thin to show him.
12. **A two-player EPG inning for Pietarinen.** Every existing episode is
    single-voiced; `swan_episode_unpacked`'s six rules live as a `derivation`
    list inside one step's params on a working copy, not as replayable steps.
13. **Curate the 14 literature titles** from the CSL records already in each
    `provenance.json` (F2).

**Correctness and credibility:**

14. Flag vacuous satisfaction and rank it below grounded holds (F5).
15. Act on the §6 ruling for the game registers (F6).
16. Repoint `test_tomos_parsing.py:11` at the real corpus so the round-trip
    guard runs (F8); it is currently among the 217 silent skips.
17. Compute Organon browse step-counts from `history/chain.jsonl` instead of the
    stale `index.json`, which reports "1 state / 0 transformations" for all 52.
18. Populate `linear_forms/` on disk, or accept that letters cannot link to a
    CGIF/CLIF file.

### Tier 2 — the functional URL (Q4)

**Nothing is exposed until the first item lands.**

19. **Sanitize `uod_id` / `scratch_id`** with `is_relative_to` containment.
    Today `uod_id` reaches a filesystem path with only `.strip()`.
20. **Decide the exposure shape.** Two honest options:
    - **Read-only Organon behind a reverse proxy** — GET-only, CORS locked to
      the origin, `/docs` closed. Days-scale, and it demonstrates the archive,
      the lenses, the chains and the exports. It does **not** let a scholar play.
    - **Full interactive** — requires a single uvicorn worker (four unlocked
      process-global session dicts make >1 worker unsafe), per-visitor scratch
      namespacing, removal of the global `GET /ergasterion/scratch` listing
      (which today lists and can delete anyone's drafts), and a `tomos/`
      snapshot-and-restore timer, since visitors can append to the corpus.
      `DEPLOYMENT_AND_MULTIUSER.md` already calls this "an integration project
      you own", and it is right.

    Given Q1 — all three must find satisfaction, and each will explore the
    whole — a read-only Organon URL will not carry the letters by itself.
    Ergasterion and Agon are where two of the three recipients live.

### Tier 3 — greenfield checkout (the follow-on offer)

21. After Tier 0 item 5, the cold-clone job *is* the greenfield guarantee. What
    remains is a one-page "run it yourself" with the true prerequisite set —
    Python ≥3.12, uv, Node.js — and honest optional extras (Playwright for E2E,
    Quarto + LaTeX for the book, `rsvg-convert` for PNG/PDF export).

## 9. Artifacts for the letters — what already exists

`export_peirce_chain_document` + `POST /export/chain` already emit one captioned
TikZ figure per proof step, compiling under plain `pdflatex`, wedded to the
attested layout. That is precisely the "calculus through steps" attachment. The
remaining three attachment kinds — ontology and domain modelling, alternative
paths resolving, the EPG's effect on model evolution — need the Tier 1
exemplars before they can be exported.

## 10. Sequencing

Tier 0 is hours and unblocks everything, including any remote reader.
Tier 1 items 8–13 are the real work and the reason the letters are not ready;
they are exemplar authoring, not engineering. Tier 2 item 19 is small and must
precede any exposure. The Tier 2 shape decision (item 20) should be made early,
because a read-only demo and an interactive one are different projects.

## 11. Rulings (2026-09-06)

- **Q5 — build the eliminative register.** See §6. The naive outcome is real and
  feeds the non-binary question of what it means for M; strata 2 and 3 are built.
- **Q6 — the public URL is interactive.** A read-only Organon demo is declined:
  if the URL is exposed at all it must let a visitor play. That accepts the
  integration work in Tier 2 item 20 — a single uvicorn worker (four unlocked
  process-global session dicts make more unsafe), per-visitor scratch
  namespacing, removal of the global `GET /ergasterion/scratch` listing that
  today lists and can delete anyone's drafts, a `tomos/` snapshot-and-restore
  timer, CORS locked to the origin, and `/docs` closed. The path-traversal fix
  (item 19) precedes all of it.
- **Q7 — exemplar authoring becomes its own arc**, with its own specification,
  rather than a block of items inside this document. Tier 1 items 8-13 move
  there; this document keeps the correctness items (14-18).

## 12. Status

- **Tier 0: DONE** (`d118f9d`). Landing page reachable and legible with a
  regression guard; Node.js and `npm install` documented with the symptom in
  TROUBLESHOOTING; the `agon.py` arity bug fixed with a guard, so all seven
  imported T-boxes are identified and materialize; e2e guards probe the browser
  by launching (2 skipped in 0.62s and no leaked server, where a fresh clone
  previously got 29 errors); a greenfield workflow that runs only the documented
  steps and then renders a real graph; PySide6 moved to a `qt` extra
  (1.5 GB → 374 MB); `.python-version` pinned to 3.12; three stale test-count
  claims corrected. Full suite 4,618 passed / 217 skipped / 1 xfailed / 0 failed.
- **Next:** the exemplar arc specification (Q7), then Tier 1 correctness items,
  then Tier 2 interactive deployment (Q6).
