# Arisbe — Vision & Scope

> **What this is.** A thin top-down orientation to the whole project: what Arisbe is, the one
> problem it exists to solve, what is bedrock and non-negotiable, who it is for, what is in and out
> of scope, and where it is going. It is deliberately short and **links out** to the deep docs rather
> than restating them. Read this first; then follow the pointers.
>
> **Companion documents:** [CAPABILITY_MAP.md](CAPABILITY_MAP.md) (what works today, where it lives,
> what guards it) · [ROADMAP.md](ROADMAP.md) (what's next, in order) · [GLOSSARY.md](GLOSSARY.md)
> (terms + a reading order by audience). **New here?** [GETTING_STARTED.md](GETTING_STARTED.md) is the
> layered, role-aware on-ramp (assumes no logic background, then branches by expertise). For the
> developer-facing module map and commands, see [../CLAUDE.md](../CLAUDE.md).
>
> *Last consolidated: 2026-06-27.*

---

## 1. What Arisbe is

Arisbe is an environment for **doing logic in pictures, not pictures of logic** — Charles Sanders
Peirce's "moving pictures of thought" made operational. You draw and transform Existential Graphs
([EGs](GLOSSARY.md#eg)) directly; the picture *is* the reasoning, not an illustration of reasoning done elsewhere.

Peirce is the **aim**; Frithjof Dau's formalization is the **guarantor of correctness**. Arisbe does
not try to improve Peirce's calculus — it implements Dau's rigorous formalization of Alpha (the cut,
the sheet, juxtaposition) and Beta (the line of identity) faithfully, and builds outward from that
bedrock. (See [FIDELITY_AND_DEPARTURES.md](FIDELITY_AND_DEPARTURES.md) for the debt to Peirce and the
three places Arisbe consciously departs, each examined adversarially and surviving with amendment.)

The fundamental entity is **not a static diagram** but the **Universe of Discourse ([UoD](GLOSSARY.md#uod))** — a
*diachronic* (evolving) process of reasoning. A single EG is a *synchronic* snapshot (a photograph)
within that larger film. See [UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md).

---

## 2. The central problem — correspondence

The one engineering-and-research problem the whole codebase exists to solve:

> **The inerrant correspondence between an EG's linear written form and its graphical drawn form** —
> picture and proposition denoting the *same mathematical object* across every transformation, every
> layout regeneration, every user edit, every round-trip.

When the two come apart, the system has failed its central purpose — *not because the logic is wrong*
(Dau guarantees that) *but because the picture and the proposition have parted*. This contract is
**stated, tested, and runtime-attested**:

- **Stated** — [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md), the central
  contract. Read it before touching anything that produces or consumes an `(EGI, drawing)` pair.
- **Tested** — `tests/test_correspondence_invariant.py` (the six §7 shapes against the corpus).
- **Attested at runtime** — `correspondence_attestation.attest_correspondence(egi, dto)` raises
  `CorrespondenceViolation`; hooked into the web serving + save/load boundaries.

A crucial discipline: **correspondence is attested, never truth.** §3.3 certifies that *this linear
form and this drawing denote the same graph* — it is internal consistency, *not* a claim that either
is true of the world. A correspondence failure is not falsehood but *voidness* (Pauli's "not even
wrong"). Truth is settled elsewhere — in use, in the Agon. See
[MANIFEST_AND_MEANING.md](MANIFEST_AND_MEANING.md).

A third correspondence has recently joined the doctrine: **diagram ↔ narration** (a narrated proof is
a chain of Discourse Representation Structures ([DRSs](GLOSSARY.md#drs)), and a DRS *is* a Beta EG). It is a measurement/validation lens, not yet surfaced in
the UI — see [THE_MINIMAL_IN_VIEW_SET.md](THE_MINIMAL_IN_VIEW_SET.md) §10.

---

## 3. Bedrock — the non-negotiables

These are the commitments that may **not** be traded away. Everything else is negotiable engineering.

1. **Dau's calculus is the correctness floor.** All six transformation rules (ERA, INS, IT+, IT−,
   DC+, DC−) are implemented in full compliance, Beta-aware. The mathematical core test suite must
   always pass; a failing core test is a real correctness defect, not test noise.

2. **The Existential Graph Instance ([EGI](GLOSSARY.md#egi)) is immutable.** State advances only by constructing a new graph (`.with_vertex()`,
   `.with_edge()`), never by mutation. Provenance is therefore append-only and the history is a directed acyclic graph ([DAG](GLOSSARY.md#dag)).

3. **A step and its warrant are the same act.** You cannot make a change and *then* check it: the only
   way to advance the chain is to apply a rule, and a rule will not apply unless its preconditions
   hold. The move *is* its proof of soundness. See [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md).

4. **The correspondence invariant, scoped to three regimes** (below). Mandatory where things are
   asserted; suspended where things are merely entertained.

5. **We attest correspondence, never truth.** Warrant is a *gradient* (posited → derived → withstood)
   that rises by surviving challenge and can fall; "fact" is the defeasible status of the
   last-standing trajectory, never a glow in the ink. No mark bears actuality.

### The three regimes (the scope of the invariant)

| Regime | Where | Invariant |
|--------|-------|-----------|
| **1 — composition** | Ergasterion drafts (freeform drawing) | **Suspended on purpose** — the freedom to scramble and recombine is how inquiry probes. |
| **2 — asserted / canonical** | Agon, Organon, every rule application | **Mandatory, runtime-attested** (§3.3). |
| **3 — presentation-only** | restyling, re-layout, nudging | **Free, but preserved by construction** via the `presentation_ops` API (boundary crossings raise `Regime3Violation`). |

### The "protected core" mechanism — and an open decision

A pre-commit guard (`tools/core_protection_system.py`) blocks edits to **17 named modules** unless
`.core_modification_authorized` is present, coupled to "the math core suite must pass." Its purpose is
a deliberate authorization speed-bump guarding Dau's formalization from inadvertent change.

A re-audit this pass (2026-06-27) found, and the author then acted:
- The "16 vs 17" count drift the prior handoff worried about was **already reconciled** — the report
  prints the full set, matching CLAUDE.md. No ghosts: every protected member has a live importer.
- **The mechanism did not guard the central invariant.** `correspondence_attestation.py` and
  `presentation_ops.py` — which *enforce* the correspondence the protection exists to defend — are the
  two **most-imported** modules in `src/` (28 and 31 importers) yet were **unprotected**.
- The real guard is the **core test subset** (the fast gate), not the name-match speed-bump.

→ **Decision taken (2026-06-27):** *(a, "keep + extend")* `correspondence_attestation.py`,
`presentation_ops.py`, and `natural_layout.py` were **added** to the protected set — so the §3.3 enforcers
now require authorization to change; *(b, "trim")* the six EGIF/CGIF/CLIF parsers/generators were
**removed** as application-level I/O the calculus doesn't import (guarded instead by corpus round-trip
tests in CI). Net **17 → 14** modules, now the genuine calculus core. *(c, "replace with a CODEOWNERS-style
note") was declined:* CODEOWNERS routes PR reviews and would not fire in a solo, no-PR workflow — instead
the protected set's inline comments now **double as the bedrock note**, one artifact that both documents
*and* enforces. The pre-commit gate is kept because its real job in an AI-assisted solo workflow — making
an inadvertent edit to the calculus impossible to miss — is one neither a doc-note nor CODEOWNERS can do.
*(The corpus-wide `test_correspondence_*` suites were **not** added to the fast gate: minutes-long, far
past its <30s budget; they run in CI, and the invariant is guarded at commit time by the module
protection.)* See [ROADMAP.md](ROADMAP.md) #1.

---

## 4. Who it is for

Condensed personas (the fuller narrative lives in [ARISBE_IN_PRACTICE.md](ARISBE_IN_PRACTICE.md) and
[ARISBE_FOR_SCHOLARS.md](ARISBE_FOR_SCHOLARS.md)):

- **The teacher** — walks a class through a proof in **Organon** (read-only archive), stepping the
  chain of semiosis with per-move rule + narration.
- **The student** — composes freehand in **Ergasterion** (workshop): draw marks, fix them into a
  graph, practice transformations, and learn correspondence by being graded against a target
  (challenge mode).
- **The researcher / domain expert** — contests a claim in **Agon**: pick a model M, peel a
  proposition G against it, get a verdict + witness/counterexample, or ask "in what domain does G
  hold?" (the inverse pivot).
- **The logician** — round-trips a form across modes and across four linear notations (Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)) / Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)) /
  Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)) / First-Order Predicate Logic ([FOPL](GLOSSARY.md#fopl))), trusting that the same proposition stays recognizable everywhere.
- **The scholar** — transcribes a historical graph with provenance, faithful to a community across
  history rather than cured into one consistent whole.

---

## 5. Scope

### In scope (and shipped — see [CAPABILITY_MAP.md](CAPABILITY_MAP.md))
Alpha + Beta EGs in Dau's formalization; the six transformation rules; the diachronic UoD + branching
DAG history; four round-tripped linear formats; the correspondence machinery (coordinate-free layout,
§3.3 attestation, regime-3 presentation algebra, drawn→EG reading); the three web modes; freeform
draw-then-read composition; the Endoporeutic Game (contest + interpretation registers); ontology/Web Ontology Language ([OWL](GLOSSARY.md#owl))/
Resource Description Framework ([RDF](GLOSSARY.md#rdf)) import as a *bridge*; an NL→logic front-end where "the LLM proposes, Arisbe disposes."

### Out of scope — deliberate, with reasons
- **Gamma as a *modal* extension.** Not a problem Arisbe needs to solve: the diachronic DAG (worlds =
  sheets, accessibility = legal transition) *is* the drawn Kripke frame, so □/◇ are ordinary Beta
  quantifiers drawn rather than hidden. The **real** frontier is *second-order logic about the graphs
  themselves*, not modal marks. See [MODALITY_WITHOUT_GAMMA.md](MODALITY_WITHOUT_GAMMA.md).
- **Reading a raster image** (photo/scan/hand-drawn ink → EGI). The hard inverse problem, explicitly
  deferred. (Note: reading a *structured* freeform drawing — typed marks on the canvas — **is** in
  scope and shipped; it is pixels that are out.) See [EXACT_CORRESPONDENCE.md](EXACT_CORRESPONDENCE.md).
- **The Qt desktop GUI.** Archived to `archive/qt-gui-2025/` (May 2026); the web app is the canonical
  UI.

### Deferred — wanted, not yet built
Manchester OWL syntax (no maintained Python parser); a semantic layer + automated Grapheus opponent +
dynamically-learned M for the Endoporeutic Game (a thin V1 ships today); Gamma *tinctures* as a
non-load-bearing map symbol (channels reserved, forward-compatible by construction); the layout-perf
frontier for very large ontologies. These live in [ROADMAP.md](ROADMAP.md).

---

## 6. Governing principles

The invariants a contributor should internalize before changing anything:

- **Immutability** — never mutate an EGI; construct a new one.
- **Correspondence-or-suspend** — assert nothing whose picture and proposition have not been
  attested to match; suspend the invariant only in regime-1 composition.
- **Attest, don't assert** — the system certifies correspondence, not truth.
- **Polarity in words, not hue** — a region's positive/negative polarity is named in words, never
  smuggled in by colour (colour would invite reading actuality off the ink).
- **Warrant is a gradient** — posited / derived / withstood; it rises and falls; nothing is exempt
  from being drawn back under a cut and challenged again.
- **The blank sheet is the only unconditioned thing** — and it asserts nothing. No contingent
  proposition sits unenclosed on the recto; every given enters under a cut, built from the blank by
  legal nesting. See [LEVEL_ZERO_AND_THE_REGISTERS.md](LEVEL_ZERO_AND_THE_REGISTERS.md).
- **Local is primary, GitHub is backup** — the corpus on disk is the source of truth; pushes are
  backup, not collaboration.
- **No direct workshop → corpus route** — a graph reaches the attested corpus *only* by being tested
  through Agon, or as a style-only reprojection of an already-attested graph.

---

## 7. The system at a glance

```
Universe of Discourse (diachronic): State_n = (EGI_n, LayoutDeltas_n) + DAG history
        │
        ├── EGI  ── immutable RelationalGraphWithCuts (V, E, ν, ⊤, Cut, area, ρ)
        │          cut-containment (tree) + ligatures (W-partition)
        │
        ├── linear forms  ── EGIF · CGIF · CLIF · FOPL · JSON  (round-trip tested)
        │
        ├── correspondence layer ── natural_layout → ELK / tension → SVG; §3.3 attested
        │
        └── three modes (web app: src/web_api + src/web_viewer):
            Organon      "instrument" — read-only archive / browser / player
            Ergasterion  "workshop"   — compose, transform, challenge, define
            Agon         "contest"    — Endoporeutic Game: contest + interpretation
```

The full annotated module map, the commands, and the test inventory live in
[../CLAUDE.md](../CLAUDE.md). The architecture deep-dives are
[UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md](UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md) and
[DAG_HISTORY_ARCHITECTURE.md](DAG_HISTORY_ARCHITECTURE.md).

---

## 8. Trajectory

The near-term arc: **consolidate** (this pass), then decide the **protected-core** question, then the
two safe near-term builds the in-view-set work teed up (a *ground/legend panel* and a *render-M*
neighborhood view), with one **architectural fork** waiting on an author decision (a first-class
reference/transclusion node that would touch the core data model). The long-running UX arc is the
**newcomer / EGIF-authoring on-ramp**. The named research frontier is **second-order logic about the
graphs**. All of this, sequenced with dependencies, is [ROADMAP.md](ROADMAP.md).

---

## 9. How this spine is maintained

This document and its two companions are a **consolidation** of material that is otherwise distributed
across `docs/`, `tests/`, and the session log. They are thin by design:

- **VISION_AND_SCOPE** changes only when a *commitment* changes (a new non-negotiable, a scope
  decision, a principle).
- **CAPABILITY_MAP** is a living table — update the relevant row when a capability ships or its status
  changes.
- **ROADMAP** is the working backlog — re-order and prune as priorities move.

`CURRENT_PLAN.md` remains the chronological session log / working handoff; this spine is the
*structural* view that the log is not meant to provide.
