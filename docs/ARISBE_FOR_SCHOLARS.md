# Arisbe: A Working Environment for Existential Graphs

*An introduction for scholars, teachers, and researchers of Peirce's logic*

**Status**: active development · **Reviewed**: 2026-07-27 (second-storey revision) ·
Repository: <https://github.com/mijahauan/Arisbe>

---

## In one paragraph

Arisbe offers an environment for **doing logic in pictures, not pictures of
logic**. It makes Charles Sanders Peirce's "moving pictures of thought"
operational. A user asserts, transforms, and contests Existential Graphs
directly, as diagrams that evolve; Frithjof Dau's formalization guarantees
correctness. The system exists to solve one **central engineering and research
problem**: the **inerrant correspondence between an Existential Graph
([EG](GLOSSARY.md#eg))'s linear written form and its graphical drawn form** —
picture and proposition denoting the same mathematical object across every
transformation, every re-layout, every edit, every round-trip. The system
exists and runs: a transformation engine over Dau's six rules, a runtime
correctness attestation, a curated corpus of worked proofs and imported
ontologies, three working modes (archive, workshop, and an [Endoporeutic](GLOSSARY.md#endoporeutic)-Game
arena), and, since mid-2026, the game running *autonomously* against live
sources, all behind a browser interface. It now also carries a second storey,
a stated research program voiced as a proposition and graded point by point.
Both storeys remain frankly unfinished in well-marked places, which partly
explains why this introduction exists.

## Why the correspondence problem is the heart of it

Most tools that "support" Existential Graphs treat the diagram as a *rendering* of
an underlying formula — a picture downstream of the logic. Arisbe inverts this.
The drawn mark **is** the logical sign. Every pixel inside a drawn cut line
counts as a child of that cut's area; containment, incidence, and
ligature-crossing come straight off the drawn shape, identically across visual
styles (Dau, Peirce-authentic,
Sowa). The linear form (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif))/Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif))/Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif))) and the graphical form stand as two projections
of one coordinate-free structure, and Arisbe holds them in provable
correspondence.

The system enforces this at runtime. A §3.3 *correspondence attestation* (`attest_correspondence`,
§3.3 of [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md))
checks every (Existential Graph Instance ([EGI](GLOSSARY.md#egi)), drawing) pair before the system serves, saves, or admits it to the
corpus, and **refuses** any pair that fails to correspond, raising a
`CorrespondenceViolation` rather than displaying a graph that means something
other than it says. Three regimes scope the invariant, which keeps it
honest rather than tyrannical: **composition** (workshop drafts — suspended),
**asserted/canonical** (every rule application, every corpus item — mandatory and
attested), and **presentation-only** (restyling and hand-nudges — free by
construction, preserved through a dedicated regime-3 API).

To my knowledge this *inerrant, runtime-attested* coupling of the linear and the
diagrammatic stands as unusual if not novel, and on this contribution I would most want a Peirce
scholar's eyes. It makes a precise, mechanized claim about the iconicity of EGs:
the graph serves not as a notation *for* a proposition but as a sign that *is* one.

## What is built today

- **The transformation engine** — Dau's six rules (ERA, INS, IT+, IT−, DC+, DC−),
  Beta-aware (lines of identity, shared vertices across cuts), with a headless
  stepwise protocol for constructing and replaying proofs. The mathematical core
  carries a protected test suite that must always pass.
- **Linear ↔ graphical round-tripping** — production parsers/generators for
  **EGIF**, **CGIF** (ISO/IEC 24707-adjacent), and **CLIF** (Common Logic), tested
  across ~90 canonical examples, plus First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl)) translation in Dau's Chapter-18 sense.
- **Layout as projection** — a coordinate-free "natural layout" (containment tree,
  per-ligature required crossing-sequence, incidence, ports) from which concrete
  drawings derive. The renderer works as a pluggable projection, and a reader
  (`read_drawing`) recovers the graph from geometry alone. That inverse
  direction makes freeform *drawing a graph by hand* a first-class way in.
- **A curated corpus** of worked items, each carrying typed provenance and an
  annotation layer: authored and transcribed **proofs** (Peirce's Law, Barbara,
  the uniqueness of the group identity, Leibniz's *Praeclarum Theorema*),
  **exemplars** from Peirce/Roberts/Sowa/Dau, **domain models**, imported
  **ontologies** (Porphyry's Tree, a FOAF slice, the upper spine of SUMO), and
  **diachronic model-development runs** the automated game itself produced.
- **The Endoporeutic Game, playable and autonomous** — the interpretation
  register plays *given M, then G*: choose a reference model, then
  [peel](GLOSSARY.md#peel) the proposal against it to a three-valued verdict,
  with the witness or counterexample named. M can be **materialized** (facts
  plus Horn rules forward-chain to the least Herbrand model), and an ontology
  can stand as M for theorem queries. The full **automated game** runs as
  well: three Large-Language-Model roles — a Graphist voicing doubts, a
  Grapheus defending M, an Agonothetes selecting among the votes cast, never
  a referee — argue under an incorruptible mechanical peel (*the LLM
  argues, the calculus decides*). **Live membranes** feed it (Wikidata's
  crawl and recent-changes stream, run bounded, paced, and checkpointed), and a
  meta-learning layer studies which resolution mechanisms produce durable
  knowledge.
- **The discipline of the record** — nothing contingent stands unguarded at the
  sheet's top level (M resides in a standing world-scroll of cut-wrapped
  cells); every model change runs as a licensed rule application carrying its
  executed derivation; entertained hypotheses are drawn *without force* and
  discharge only through a confirming evaluation; a standing corpus gate
  re-verifies every recorded verdict, forever.
- **Scholarly reproduction** — Peirce's manuscript figures (MS 280, MS 514,
  CP 4.394) reproduced as publication-ready pure-TikZ LaTeX **wedded to the
  underlying EGI** (a pure function of the attested layout, never a mere
  picture), with the iconic self-continuing scroll glyph and a
  provenance-to-citation path that fabricates nothing.
- **Three modes, in the browser** — **Organon** (archive, with modal and audit
  lenses over the diachronic record), **Ergasterion** (workshop: freeform
  draw-then-read composition, challenge mode with legible grading), and
  **Agon** (the game arena, hot-seat, with the disposition step).

## The second storey — the program, and the contribution we would headline

Since 2026-07 the project states, beside the instrument, a research program,
voiced deliberately as **a proposition scribed into a wider Endoporeutic
Game** in which the traditions and communities addressed play as the other
players. It *proposes* rather than asserts; its pre-registered priors and run
logs stand as peels already played; a competent refutation would mean the game
working, not the game lost ([VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §8,
with a four-grade warrant discipline; the claim-by-claim examination is
[CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md)'s graded
concordance map).

**For logicians and Peirce scholars we would headline the treatment of the
*question*: erotetics with an economics, on an indexed
record.** A verdict of UNKNOWN marks no terminus here. It mints a standing
question, the {atom, denial} pair, as a first-class object of the record, and
the question then has a *career*. The record traces the consequences of each
answer (materiality, a vector, never a scalar). An attention economy
**prices** each question (severity · cost · decay), so that open questions
compete for the inquirer's next probe instead of evaporating. And a question
is **settled only by licensed ink**: the record resolves it only by citing the
sound, replayable step that introduced its answer. The whole structure
amounts to an **index over the reasoning record** ("index-over-ink"). It
holds no evidence of its own, only pointers to gate-checked steps,
re-checkable forever; evidence lives in the record, earned, or nowhere. We
read this as Peirce's account of doubt and inquiry made operational — the
question given the same formal citizenship as the assertion — and as a
unification: the erotetic tradition (Hamblin, Belnap, Wiśniewski),
truth-maintenance, attention, modality (alternatives contested across the
diachronic record's branching futures), and the deliberative interval meet in
one structure
([ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md);
the worked corpus exemplar is `swan_alternatives`).

## What a scholar, teacher, or student might do with it

- **Teach Peirce's logic as a practice, not a notation.** The Endoporeutic Game is
  *playable*: a student proposes a graph against a domain model and watches it
  resolve to a theorem, a refutation, a new fact, or a standing question with
  a priced career. Freeform challenge mode grades a freehand drawing in EG
  vocabulary (`same_graph` plus a legible diff). A companion document,
  [ARISBE\_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md), walks everyday scenarios in
  non-technical language; the
  [ENDOPOREUTIC\_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) gives the formal
  account and its Peircean grounding.
- **Work with a shared, inspectable corpus.** Every proof stands as a real chain of sound
  rule applications with deterministic provenance; every item states its source
  and its warrant; the standing gates re-verify the record on every run. We
  mean the corpus to grow by contribution.
- **Reproduce and publish.** Export any attested graph — including your own
  hand-adjusted arrangement of it — as compilable TikZ with scholarly
  citations ([FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md](FEATURE_PEIRCE_SCHOLARLY_REPRODUCTION.md)).
- **Probe the research claims directly.** The correspondence invariant, the
  question-career machinery, the [Agonothetes](GLOSSARY.md#agonothetes)
  construct, and the program's graded claims all stand open to critique — and
  the code is the argument: each lives in a module you can read, run, and try to
  break. (Exact commands — the core suite, the conservativity gate, a worked
  chain end to end — are in [GETTING_STARTED.md](GETTING_STARTED.md), the
  logician door's "How to try to break it.")

## The frontier (stated honestly)

What an earlier revision of this page listed as unbuilt has since shipped. The
ontology-as-M pipeline (Web Ontology Language ([OWL](GLOSSARY.md#owl))→CLIF→EGI, with SUMO/FOAF/Porphyry imported
and theorem queries deciding subsumption against them) and the automated game
with dynamic M-development exist as real systems; they run, and they leave
logs (`runs/`). The honest
frontier today:

- **The browser arena is hot-seat; the autonomous game runs headless.** The
  live loops (membranes, decay, the question register) have instrument-panel
  lenses in Organon but not yet an arena surface.
- **WordNet/SNOMED remain unwired** as import sources (the pipeline exists;
  those adapters do not).
- **Two determinants are named, not modeled**: identity/plausibility-structure
  maintenance, and the physical substrate under "doubt"
  ([THE_KYTOS.md](THE_KYTOS.md) §5).
- **The most exposed phrases stay graded as conjecture** — an "operational
  model of consciousness / free will" is and remains queued-conjecture; the
  grading discipline exists precisely so such phrases cannot glow.
- **The tutor loop is design-only** (a documented plan for the game as
  tutorial protocol; nothing built).

We would rather say this plainly than oversell a demo.

## Questions for the tradition

This section stood, in earlier revisions, as a letter to Ahti-Veikko
Pietarinen in particular; personal letters (to Pietarinen, Dau, Sowa, and
others) are now being prepared separately, and the questions belong to the
whole tradition:

1. **The *Agonothetes*.** Peirce's game terminates at a dyad — true or false. But
   his own semiotic remains irreducibly triadic, so we name a third, *telic*
   function. The Agonothetes (ἀγωνοθέτης, "organizer of the contest") is the
   **interpretant** of the game-as-semiosis. Not a third player — the ratified
   account allows two players only and no move-by-move referee, since legality
   belongs to the calculus — but the maker of two **risked choices**: before
   play, the choice of the reference model M; after, the selection of the
   outcome's fate from an agreed taxonomy. We believe this is faithful to
   Peirce; we would like to be told if it is not.
2. **The correspondence invariant as mechanized iconicity.** The runtime guarantee
   that the drawn graph and its symbolic form denote one object amounts, in
   effect, to an operational claim about the iconic character of EGs. Does it
   capture what Peirce meant by the diagram *being* the proposition, rather
   than standing for it? Exactly the kind of question we are not equipped to
   settle alone.
3. **Modality without Gamma.** Arisbe draws no modal mark: the diachronic
   branching record is itself the drawn Kripke frame
   ([MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md)). We know this runs
   against the rehabilitated broken-cut calculi (Ma & Pietarinen 2018); our
   claim remains, deliberately, adequacy rather than completeness — and
   whether that positioning is honest falls to the tradition to judge.
4. **Mention-ascent.** The dotted oval, Peirce's graph-of-a-graph, lives in
   the core as quotation (mention, never use), conservativity-gated
   so the second-order layer licenses no new first-order assertion. Is this
   the right reading of Peirce's device, and of hypostatic abstraction as the
   ascent operator?

You know more about Peirce's existential graphs than we do, and almost certainly
more about how an effort like this might serve scholars, teachers, and students.
We seek that collaboration: a reading from someone in the tradition,
a steer on where the formalization holds sound and where it strays, and, if any of
it proves useful, a way to make it useful to the people who study and teach this
logic.

## Pointers

- **Read first:** [ARISBE\_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) (narrative),
  then [ENDOPOREUTIC\_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (formal).
- **The central contract:** [LINEAR\_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md).
- **The program, voiced and graded:** [VISION_AND_SCOPE.md](VISION_AND_SCOPE.md) §8 +
  [CONTRIBUTION_AND_PRIOR_ART.md](CONTRIBUTION_AND_PRIOR_ART.md).
- **The Peircean grounding of the provenance/inquiry model:**
  [CHAIN\_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) and
  [MANIFEST\_AND_MEANING.md](MANIFEST_AND_MEANING.md).
- **The question's career:** [ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md](ALTERNATIVE_SET_INTELLECTUAL_HISTORY.md).
- **The corpus and import model:** [CORPUS\_AND\_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md).
- **Run it:** `uv sync --extra dev --extra web` then
  `uv run uvicorn --app-dir src web_api.main:app --reload --port 8000` and open `/organon`.
  (Full install/run steps: the *Install & run* chapter.)
