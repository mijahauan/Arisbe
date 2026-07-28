# The Gamma Demonstrations — Peirce's modal drawings, expressed in Beta

> **What this is.** The demonstrations companion to
> [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) (the doctrine). That document
> argues that Beta EG plus the diachronic branching DAG expresses □/◇ with **no new modal
> mark**, up to the second-order frontier. This document earns the claim. Peirce attempted
> to draw specific modal meanings with his never-completed Gamma graphs: the broken cut of
> the 1903 Lowell Lectures, the tinctured would-be and the book of separate sheets of the
> 1906 *Prolegomena*. It expresses each of them with the machinery Arisbe already
> has, as corpus exemplars you can open in Organon and read through the lenses.
>
> Built 2026-07-04. Every Peirce citation below was verified against the in-repo Roberts
> extract (`docs/derived/"Existential Graphs of Peirce_extracted.txt"` — Don D. Roberts,
> *The Existential Graphs of Charles S. Peirce*, Mouton, 1973). Builder:
> `tools/build_gamma_modal_exemplars.py` · tests: `tests/test_gamma_demonstrations.py`.

## 1 · What Peirce drew, and what carries it here

Peirce's Gamma (1903–1911) ran several projects at once. Three of them concern modality,
and those three receive demonstrations below. The rest — graphs of graphs, abstraction,
the "potentials" — belong to the second order and remain the honestly-named frontier
([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) §7).

| Peirce's device | Where he drew it | What carries it in Arisbe |
|---|---|---|
| **The broken cut** — a cut "with many little interruptions", saying the graph on its area is *contingent* | Lowell Lectures 1903, Lecture IV; CP 4.510–4.516; convention C10 at CP 4.410 | the shape of the derivation DAG, read by `modal_query` (§2) |
| **The tinctured would-be** — a blue-tinted area making a conditional *strict*, not material | Ms 490 (the passage omitted at the end of CP 4.575); the argument at CP 4.546, 4.549 | a branching DAG of *courses of experience*, the proposal peeled at every world (§4) |
| **The book of separate sheets** — SA replaced by "a book of separate sheets, tacked together at points" | CP 4.512, 4.514 (Lowell IV) | the UoD itself: one EGI state per sheet, the DAG tacking them together (§5) |

Three corpus UoDs carry the demonstrations:

| UoD id | Register (what R is) | The Peirce figure it reconstructs |
|---|---|---|
| `broken_cut_square` | derivability — every edge a sound ERA | the broken cut and its combinations (all four modal statuses) |
| `would_be_de_inesse` | synchronic — no frame at all | P *de inesse*: the material conditional, CP 4.546's "too easily true" reading |
| `would_be_courses` | experiential — every edge a `new_fact` revision | the blue-tinted strict implication of Ms 490 |

## 2 · D1: the broken-cut square (`broken_cut_square`)

Peirce's own Fig. 1 (Lowell IV) is a broken cut around **"It rains"**: not the denial of
rain, but *"it is possible that it does not rain"* (CP 4.410, convention C10). Combining
broken and solid cuts yields the four traditional modes (CP 2.382: *possibile,
impossibile, contingens, necessarium*). The exemplar realizes all four as verdicts of one
branching derivation, with no mark:

```
(rains)(daylight)(mist) --ERA mist--> (rains)(daylight) --ERA rains--+
    |                                                                 v
    +--------- ERA rains --> (daylight)(mist) --- ERA mist -->   (daylight)
```

| Peirce's drawing | Reads | On this frame | The modal lens shows |
|---|---|---|---|
| broken cut around g | ◇¬g — "possible that not-g" | some reachable sheet lacks `(rains)` | the amber chip's counterexample worlds |
| solid cut around broken cut around g | □g — "necessary" | `(daylight)` on every reachable sheet | the green **□ Necessary** column |
| broken cut around solid cut around g | ◇g — "possible" | `(rains)`, `(mist)` on some sheet, not all | the amber **◇ Possible** column |
| solid cut around g inside a broken-cut denial, i.e. ¬◇g | □¬g — "impossible" | `(thunders)` on no reachable sheet | absent from both columns |

*Possibility is branching, necessity is convergence* — the doctrine's slogan is here a
picture you can open: Organon → `broken_cut_square` → the modal lens (columns) and the
derivation-DAG lens (the diamond itself).

## 3 · D2: Peirce's broken-cut rules, re-derived as frame facts

The Syllabus (Ms 478, p. 158) gives the broken cut its own transformation regime, and the
trajectory semantics validates precisely the moves Peirce licensed:

- **R6 cut-conversion.** *(a)* An **evenly enclosed** solid cut may be *half-erased* into
  a broken cut — semantically ¬g ⊨ ◇¬g, a weakening, legal in a positive place. *(b)* An
  **oddly enclosed** broken cut may be *filled up* into a solid cut — the dual
  strengthening in a negative place. Both are theorems of the trajectory reading (a solid
  denial is strictly stronger than a contingency claim).
- **His worked inferences** (Lowell IV; Roberts pp. 83–84): □g ⊨ g (Figs. 2→4), □g ⊨ ◇g
  (Figs. 2→5), □¬g ⊨ ¬g (Figs. 6→8). On the reflexive `over="states"` reading these hold
  on every frame — they are the T-axioms, and `tests/test_gamma_demonstrations.py`
  checks them on the exemplar's frame.
- **His caution** (CP 4.519): g and ◇□g "can neither of them be inferred from the other."
  On this very frame, `(rains)` holds at the base while ◇□rains fails — the test
  exhibits it by iterating `modal_query.necessarily(base=w)` over the reachable worlds.
- **What he withheld**: no iteration/deiteration across a broken cut (R3/R4). In the
  trajectory reading nothing needs to cross, because there is no drawn boundary to
  cross — the modality is the DAG's shape, and the open problem Peirce was actually
  wrestling with there (a line of identity crossing into a possibility) is the
  trans-world-identity frontier of §7 below.

## 4 · D3: the would-be (`would_be_de_inesse` · `would_be_courses`)

The centerpiece. Peirce's proposition P (*Prolegomena*, CP 4.546): **"There is some
married woman who will commit suicide in case her husband fails in business."**

**P de inesse** (`would_be_de_inesse`) is the material reading on one synchronic sheet —
two generic lines of identity (the woman, the husband) declared on the sheet and
threading into a scroll:

```
(married_woman *w) (husband *h w) ~[ (fails_in_business h) ~[ (commits_suicide w) ] ]
```

Pure Beta. And, as Peirce complains, *too easily true*: it holds if the husband merely
never fails — no connection between failure and suicide is asserted (CP 4.546, 4.549;
Roberts p. 96 gives the two-move derivation from "some married man does not fail").
Open it in Organon: the modal lens rightly reports **no branching frame** — a synchronic
sheet has nothing for ◇/□ to range over. The de inesse reading is all there is.

**The would-be** (`would_be_courses`) is what Peirce reached for with the tinctures: his
blue-tinted figure (Ms 490; Roberts p. 89) asserts *"It is not possible that a man fails
in business without suiciding"* — a strict implication. Here the tinted possibility is a
branching DAG of **courses of experience**: prosperity; ruin (failure and the suicide);
prosperity-then-late-ruin. Each edge is a `new_fact` revision — the assertoric register,
what a course of experience admits, not what the rules derive. The would-be

```
G = ~[ (fails_in_business "Otto") ~[ (commits_suicide "Clara") ] ]
```

peels **TRUE at every reachable world**: □G, the strict implication, drawn as a habit of
every course rather than a colour on one sheet. The contrast proposal
`~[ (fails_in_business "Otto") ~[ (prospers "Otto") ] ]` is refuted by the ruin course —
◇ only, with a named counterexample world. And the de inesse trap stays visible
per-world: at the prosperity worlds G is TRUE *merely because Otto has not failed* — the
lens shows exactly the emptiness Peirce diagnosed, world by world.

Read it: Organon → `would_be_courses` → modal lens. The proposal box pre-fills with G
(the UoD's declared `audit-proposal`); the verdict banner reads **□G**; each world in the
strip is drawn (the pictures themselves) and badged with G's verdict there. The audit
lens shows the same conditional as a verdict ribbon along the history.

## 5 · D4: the book of separate sheets

In the same Lowell lecture, Peirce proposed replacing the sheet of assertion with "a book
of separate sheets, tacked together at points, if not otherwise connected" (CP 4.512) —
the upper sheet the universe of existents, the deeper leaves "altogether different
universes with which our discourse has to do" (CP 4.514). He set the idea aside as not
yet "convenient to work with" — and Roberts notes it became central to his last revision
of EG.

Arisbe's Universe of Discourse **is** that book, built without a new mark: each DAG state
is a leaf; the transitions are the tacking-together; the storyboard and time-stack lenses
flip through the leaves in order, and the derivation-DAG lens shows the whole binding at
once. This is not an analogy added after the fact — the UoD architecture
([UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md)) was
built for diachronic reasoning, and the book-of-sheets image lands on it exactly. The
"moving pictures of thought" are the pages turning.

## 6 · D5: the tinctures, honestly scoped

Peirce's 1906 tinctures distinguish *modes* — metals for actuality, colours for kinds of
possibility, furs for the interrogative and imperative. Two things carry that load here,
and one thing does not:

- **Choice of accessibility relation R = choice of mode.** The two diachronic exemplars
  differ in *register*: `broken_cut_square`'s R is derivability (Dau moves);
  `would_be_courses`' R is experiential (revision moves). Same machinery, different
  frame, different modality — the multimodal recovery of the doctrine
  ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) §2), demonstrated rather than
  asserted.
- **Subjective possibility is already in the verdicts.** Peirce's 1903 gloss on the
  broken cut — possible "in the present state of information" — is epistemic, and the
  open-world peel returns exactly that shape: Kleene UNKNOWN, the abstention that says
  the current record does not compel. The modal proposal reading reports
  `unknown_worlds` separately, never coerced.
- **What does not carry over** — tinctures as first-class *marks* on one sheet, and the
  second-order uses (qualities, abstraction) — stays where the doctrine put it: the
  MODALITY_WITHOUT_GAMMA §5 abbreviation horizon and the MODALITY_WITHOUT_GAMMA §7
  frontier, respectively. No mark bears modality here.

## 7 · Honest limits (stated in the exemplars themselves)

- **Trans-world identity by constant.** `would_be_courses` carries "Clara" and "Otto"
  across worlds as constant labels — rigid designators, a constant-domain policy. That
  is a *choice*, stated in the UoD's annotations; a **generic** line of identity carried
  across a transition (Peirce's Ms 490 "special relation", the doctrine's
  MODALITY_WITHOUT_GAMMA §2 crux) remains unimplemented, and the domain-policy
  question (MODALITY_WITHOUT_GAMMA §3) remains open.
- **States vs leaves.** A would-be quantifies most naturally over *completed* courses
  (`over="leaves"`). The exemplar's single-step courses make □G hold on both readings,
  but a finer-grained course (failure admitted, the sequel not yet) would make G FALSE
  at a mid-course world while TRUE at every leaf — the toggle in the lens is exactly
  this distinction, worth teaching, not hiding.
- **Propositional reach.** `modal_query` reads one world at a time; the proposal reader
  peels a closed G per world. Nested modalities (◇□g) are expressible by iterating
  queries with `base=` (the CP 4.519 test does this), not yet by one drawn graph.
- **Second order.** Untouched, as pre-registered: graphs-of-graphs and abstraction are
  the real frontier, grown via the schema/φ-hole path, never via a modal mark.

## 8 · Using them (the exercises)

- **Organon**: open any of the three UoDs. The **modal lens** now takes a proposal G
  (EGIF) and reads ◇G/□G across the worlds, each world drawn as a thumbnail and badged
  with its verdict; the **audit lens** shows G's ribbon along the history; the
  **derivation-DAG lens** shows the frame itself.
- **Challenge mode** (Ergasterion): two new targets — `de-inesse` (draw Peirce's CP 4.546
  graph freehand: two lines of identity into a scroll) and `would-be-course` (draw one
  world of the would-be: plain facts, no cuts — the modality lives across the courses,
  not inside one).

## 9 · Dogfood findings (the UI-polish ledger)

*Recorded while driving the demonstrations through the lenses (2026-07-04) — the point
of the exercise. Fixed-in-pass items are marked; the rest are named follow-ups.*

**Fixed in-pass:**

- **The modal lens was unreachable on a synchronic UoD** — `organon.html` hid it when no
  chain exists, so the lens's own teaching note ("a static graph has no branching frame")
  could never be seen, and the de inesse half of D3 lost its punchline. Now always
  offered; the lens explains itself on a synchronic sheet.
- **The modal lens could not read a compound meaning** — per-relation ◇/□ only; Peirce's
  would-be ◻(fails→suicides) had no display. Built: the proposal reading (route
  `?proposal=` + the lens's box, pre-filled from the UoD's declared `audit-proposal`),
  three-valued per world, abstentions reported.
- **The worlds strip showed strings, not pictures** — raw EGIF cards. Built: each world
  drawn as a §3.3-attested thumbnail (EGIF demoted to tooltip/fallback; omitted with a
  note past 24 worlds).
- **A derived line of development could not be named** — `ProofChain.apply_derived` took
  no `branch=`, so the courses UoD's DAG edges rendered unlabeled in the derivation-DAG
  lens. Added (mirrors `apply`); the lens now shows *prosperity / ruin / late-ruin*.

**Named follow-ups:**

- World thumbnails render small for portrait-shaped sheets (a 210×120 box); a
  click-to-enlarge (or reusing `DiagramViewer` per world) would make the strip properly
  readable.
- Browser E2E for the proposal box + thumbnails belongs in
  `tests/test_organon_lenses_e2e.py`; blocked in the build environment (Playwright
  browsers not installed) — route-level coverage lives in
  `tests/test_gamma_demonstrations.py` meanwhile.
- The modal lens's proposal box accepts EGIF only; the plain-English door
  (`/agon/propose-nl`) could feed it the same way it feeds Agon.

## References

- Peirce, C.S. *Collected Papers* 4.410, 4.510–4.519 (the broken cut, Lowell 1903);
  4.512–4.514 (the book of sheets); 4.546, 4.549, 4.575 (end), 4.580 (the would-be,
  *Prolegomena* 1906 / Ms 490); 2.382 (the four modes).
- Roberts, Don D. *The Existential Graphs of Charles S. Peirce*. Mouton, 1973. Ch. 5
  (Gamma, pp. 81–84), ch. 6 (the tinctures, pp. 87–96). — the verification source for
  every citation above (in-repo extract under `docs/derived/`).
- Zeman, J.J. *The Graphical Logic of C.S. Peirce* (1964) — the broken-cut systems as
  S4/S5; via [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md) "What Gamma keeps".
- van Benthem, J. *Modal Correspondence Theory* (1976) — the standard translation the
  trajectory reading instantiates.
