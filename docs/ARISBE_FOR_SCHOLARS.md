# Arisbe: A Working Environment for Existential Graphs

*An introduction for scholars, teachers, and researchers of Peirce's logic*

**Status**: active development · **Reviewed**: 2026-06-08 ·
Repository: <https://github.com/mijahauan/Arisbe>

---

## In one paragraph

Arisbe is an environment for **doing logic in pictures, not pictures of logic** —
Charles Sanders Peirce's "moving pictures of thought" made operational. A user
asserts, transforms, and contests Existential Graphs directly, as diagrams that
evolve; Frithjof Dau's formalization is the guarantor of correctness. The
**central engineering and research problem** the system exists to solve is the
**inerrant correspondence between an EG's linear written form and its graphical
drawn form** — picture and proposition denoting the same mathematical object
across every transformation, every re-layout, every edit, every round-trip. The
system is real and running: a transformation engine over Dau's six rules, a
runtime correctness attestation, a curated corpus of worked proofs and imported
ontologies, three working modes (archive, workshop, and an Endoporeutic-Game
arena), all behind a browser interface. It is also frankly unfinished in
well-marked places, which is part of why this introduction exists.

## Why the correspondence problem is the heart of it

Most tools that "support" Existential Graphs treat the diagram as a *rendering* of
an underlying formula — a picture downstream of the logic. Arisbe inverts this.
The drawn mark **is** the logical sign: every pixel inside a drawn cut line is a
child of that cut's area; containment, incidence, and ligature-crossing are read
off the drawn shape, identically across visual styles (Dau, Peirce-authentic,
Sowa). The linear form (EGIF/CGIF/CLIF) and the graphical form are two projections
of one coordinate-free structure, and Arisbe holds them in provable
correspondence.

This is enforced at runtime. A §3.3 *correspondence attestation* (`attest_correspondence`)
checks every (EGI, drawing) pair before it is served, saved, or admitted to the
corpus, and **refuses** any pair that does not correspond — raising a
`CorrespondenceViolation` rather than displaying a graph that means something
other than it says. The invariant is scoped to three regimes, which keeps it
honest rather than tyrannical: **composition** (workshop drafts — suspended),
**asserted/canonical** (every rule application, every corpus item — mandatory and
attested), and **presentation-only** (restyling and hand-nudges — free by
construction, preserved through a dedicated regime-3 API).

To my knowledge this *inerrant, runtime-attested* coupling of the linear and the
diagrammatic is novel for EGs, and it is the contribution I would most want a Peirce
scholar's eyes on: it is a precise, mechanized claim about the iconicity of EGs —
that the graph is not a notation *for* a proposition but a sign that *is* one.

## What is built today

- **The transformation engine** — Dau's six rules (ERA, INS, IT+, IT−, DC+, DC−),
  Beta-aware (lines of identity, shared vertices across cuts), with a headless
  stepwise protocol for constructing and replaying proofs. The mathematical core
  has a protected test suite that must always pass.
- **Linear ↔ graphical round-tripping** — production parsers/generators for
  **EGIF**, **CGIF** (ISO/IEC 24707-adjacent), and **CLIF** (Common Logic), tested
  across ~90 canonical examples, plus FOPL translation in Dau's Chapter-18 sense.
- **Layout as projection** — a coordinate-free "natural layout" (containment tree,
  per-ligature required crossing-sequence, incidence, ports) from which concrete
  drawings are derived; the renderer is a pluggable projection (an ELK-based
  engine and an experimental "tension" engine that draws a line of identity as one
  taut thread through the cut nest, the Peircean single-line reading).
- **A curated corpus** of ~23 worked items, each carrying typed provenance and an
  annotation layer: authored and transcribed **proofs** (Peirce's Law, Barbara,
  the uniqueness of the group identity, Leibniz's *Praeclarum Theorema*),
  **exemplars** from Peirce/Roberts/Sowa/Dau, an argument **pattern**, a **domain
  model**, and imported **ontologies** (Porphyry's Tree, a FOAF slice, and the
  upper spine of SUMO translated from SUO-KIF).
- **An import doorway with a warrant model** — external material is admitted at
  **low warrant** (parsed, §3.3-attested, attributed), never asserted true; the
  philosophical floor is explicit (*attest correspondence, not truth*).
- **Three modes, in the browser** — **Organon** (a read-only archive/corpus
  browser), **Ergasterion** (a workshop for composing and transforming drafts),
  and **Agon** (the Endoporeutic-Game arena, V1: hot-seat play with the engine
  enforcing each role's territory, and a post-game *disposition* step).

## What a scholar, teacher, or student might do with it

- **Teach Peirce's logic as a practice, not a notation.** The Endoporeutic Game is
  *playable*: a student proposes a graph against a domain model and watches it
  resolve to a theorem, a refutation, a new fact, or a productive contradiction.
  A companion document, [ARISBE\_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md), walks six
  everyday scenarios in non-technical language; the
  [ENDOPOREUTIC\_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) gives the formal
  account and its Peircean grounding.
- **Work with a shared, inspectable corpus.** Every proof is a real chain of sound
  rule applications with deterministic provenance; every item states its source
  and its warrant. The corpus is meant to grow by contribution.
- **Probe the research claims directly.** The correspondence invariant, the
  warrant/provenance model, and the *Agonothetes* construct (below) are all open
  to critique — and the code is the argument: each is a module you can read, run,
  and try to break.

## The approaching frontier 

The Endoporeutic-Game side is deliberately the least finished, and the guide
marks design-only material in place. Not yet built: a **proof mode** (the
constructive direction, INS/IT+/DC+) as a wired game loop; an **automated
Grapheus** opponent (V1 is hot-seat only); the **ontology-as-M pipeline**
(OWL→CLIF→EGI from WordNet/SNOMED/Wikidata); the inner **semantic game** as a
first-class, step-exposed API; and the **warrant lifecycle** that would raise a
graph from *low* to *tested* by its surviving Agon. I would rather say this
plainly than oversell a demo.

## For you in particular

Arisbe's treatment of the game is directly informed by your treatise on the
endoporeutic interpretation as a semantic game (*Signs of Logic*, 2006). The
guide separates **two layers** that are often conflated: the inner **semantic
evaluation game** (your four-rule, boolean, always-terminating game over the
model) and the outer **transformation game** (Dau's six-rule proof-theoretic
system), bridged by deiteration (IT−) as the proof-theoretic form of "this
content holds in M." We would value your judgment on whether that bridge is drawn
correctly.

Two places where I have ventured beyond the received account and most want a
critical reading:

1. **The *Agonothetes*.** Peirce's game terminates at a dyad — true or false. But
   his own semiotic is irreducibly triadic, so we name a third, *telic* function:
   the Agonothetes (ἀγωνοθέτης, "organizer of the contest") is the **interpretant**
   of the game-as-semiosis — not a third player but the function that turns a
   boolean result into an act of inquiry (a theorem registered, a model revised, a
   hypothesis held). It maps the game's mechanical outcome onto a taxonomy of
   pragmatic dispositions. We believe this is faithful to Peirce; we would like to
   be told if it is not.

2. **The correspondence invariant as mechanized iconicity.** The runtime guarantee
   that the drawn graph and its symbolic form denote one object is, in effect, an
   operational claim about the iconic character of EGs. Whether it captures what
   Peirce meant by the diagram *being* the proposition — rather than standing for
   it — is exactly the kind of question I am not equipped to settle alone.

You know more about Peirce's existential graphs than I do, and almost certainly
more about how an effort like this might serve scholars, teachers, and students.
That is the collaboration we are seeking: a reading from someone in the tradition,
a steer on where the formalization is sound and where it strays, and — if any of
it proves useful — a way to make it useful to the people who study and teach this
logic.

## Pointers

- **Read first:** [ARISBE\_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) (narrative),
  then [ENDOPOREUTIC\_GAME_GUIDE.md](ENDOPOREUTIC_GAME_GUIDE.md) (formal).
- **The central contract:** [LINEAR\_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md).
- **The Peircean grounding of the provenance/inquiry model:**
  [CHAIN\_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md) and
  [MANIFEST\_AND_MEANING.md](MANIFEST_AND_MEANING.md).
- **The corpus and import model:** [CORPUS\_AND\_IMPORT_MODEL.md](CORPUS_AND_IMPORT_MODEL.md).
- **Run it:** `uv sync --extra dev` then
  `uv run uvicorn web_api.main:app --reload --port 8000` and open `/organon`.
