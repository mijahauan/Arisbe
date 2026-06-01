# Arisbe: Existential Graph System

**The Guiding Star** - Read this first when context is lost

---

## What Arisbe is, mid-2026

Arisbe is an environment for **doing logic in pictures, not pictures of
logic**. The aim is Charles Sanders Peirce's "moving pictures of thought" —
diagrammatic reasoning treated as a process, not a notation. Frithjof Dau's
formalization is the guarantor that the underlying logic is correct, and
that correctness is non-negotiable. But the central engineering and
research problem — the thing this codebase exists to solve — is the
**inerrant correspondence between an EGI's linear written form and its
graphical drawn form**.

Every EGI has two co-resident representations: a linear written form (EGIF,
CGIF, CLIF, FOPL, JSON) and a graphical drawn form (vertices at positions,
cuts as nested regions, predicates with hooks, ligatures as continuous
curves). The contract Arisbe enforces — and that distinguishes it from a
diagram editor on one side and a symbolic-logic theorem prover on the
other — is that both representations denote the *same* mathematical object
across every transformation, every layout regeneration, every user edit,
every round-trip. When picture and proposition come apart, the system has
failed its central purpose, even if the logic itself is sound.

As of the May 2026 review, this contract is **stated, tested, and
runtime-attested**:

- **Stated** in [docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md),
  which defines what every workstream (transformation rules, layout,
  rendering, sessions, the three modes, the Endoporeutic Game) must
  respect. The spec covers totality, injectivity, containment fidelity,
  identity fidelity (the W-partition realisation that is the hardest
  case), incidence and argument-order fidelity, and convention
  compliance, scoped across three regimes (composition, asserted,
  presentation-only).
- **Tested** by property tests in `tests/test_correspondence_invariant.py`
  covering all six §7 test shapes against the tomos corpus. The three
  regime-3 operations (vertex translation, cut reshape, ligature
  reroute) are exposed as a production API in `src/presentation_ops.py`
  that refuses boundary-crossing proposals at the source — `§5.5`'s
  "structural impossibility of regime-3 abuse" made concrete.
- **Runtime-attested** at the boundary where (EGI, drawing) pairs leave
  the system. `src/correspondence_attestation.py` runs the full §3.3
  check; the hook in `src/web_api/services/layout_service.py` raises
  `CorrespondenceViolation` if drift is detected. The system refuses to
  serve a drawing it can't attest.

The mathematical core — the EGI data model, the six transformation rules
with Beta-graph support, the headless `RuleInteraction` protocol,
linear-format round-trips across EGIF/CGIF/CLIF/FOPL/JSON validated against
130+ corpus examples, and the **Universe of Discourse** abstraction that
treats logical reasoning as a diachronic process rather than a static
diagram — is the bedrock that makes the correspondence contract testable
in the first place. That core is protected (17 modules), the test suite
(654 passing, 17 skipped across 40 test files) is the yardstick for every
change, and the protection system + quality dashboard + corpus validation
tooling work.

The user interface story remains in transition. The original plan
envisioned **Organon / Ergasterion / Agon** as three Qt windows; that Qt
implementation made it ~40% of the way through Organon and was archived
in May 2026 to `archive/qt-gui-2025/`. Active work shifted to a web viewer
(FastAPI + ELK-based layout + browser SVG). The three modes remain as the
conceptual modes of engagement and now correspond directly to the three
regimes of the correspondence invariant:

- **Ergasterion** (workshop) — the composition regime. The user is still
  figuring out what to say; the invariant is suspended because there is
  no canonical EGI for drafts to correspond to.
- **Organon** (archive) and **Agon** (arena) — the asserted regime. The
  graph is claimed to mean something definite; correspondence is
  mandatory and runtime-attested.
- Presentation-only operations — the third regime, always free —
  cross-cut both: reposition a vertex, reshape a cut, reroute a ligature
  whenever, in any mode. They are structurally incapable of changing the
  EGI (`src/presentation_ops.py` enforces this by refusing any proposal
  that would cross a boundary).

Implementing the Organon/Agon routes in the web app is the next major UI
workstream. The known follow-ups identified during the review (projection
conventions, additional boundary attestation, Hypothesis-driven
exhaustive rule testing, ELK ligature edge cases) are tracked as GitHub
issues.

The deeper Peircean grounding — *why* a reasoning episode is preserved as
a chain of sound, attested steps, and what that is in service of — is set
out in [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md): every rule
application is an attestation event, the chain (not the snapshot) is the
unit of meaning, and the whole apparatus serves Peirce's aim of analyzing
reasoning toward clearer thinking.

The sections below restate the longer philosophical case for *why* this
project exists and *who* it serves; they predate the May 2026 realignment
and should be read with the framing above in mind.

---

## What We Are Building

A reasoning environment in which logic is **done in pictures** — Peirce's
"moving pictures of thought" made operational. The work has three
distinct layers; each is necessary, and confusing them is how the project
gets framed wrong.

### The Aim — Peirce's "moving pictures of thought"
Logic studied *in* pictures, not pictures *of* logic. The picture is the
object of study, not a visualization of something more fundamental. The
Endoporeutic Game's two-player dialogical contest is the prototypical
inquiry: meaning unfolds through transformation of the diagram, not
through reduction to symbolic form.

### The Guarantor — Dau's formalization
Non-negotiable mathematical bedrock. All six transformation rules
(ERA, INS, IT±, DC±) are implemented in full compliance, with Beta-graph
support (lines of identity across cut boundaries) for first-order logic.
Closure validation, isomorphism, and Z3-backed semantic verification
ensure that nothing claimed to be a valid transformation is in fact
unsound. Dau's formalism is the means; Peirce's aim is the end.

### The Central Problem — Linear-graphical correspondence
The hardest and most distinctive part of the work. Two genuinely
different kinds of space (combinatorial structure on one side,
metric/topological/projected geometry on the other) must denote the
same mathematical object. Recent issues #5, #9, #10, #11 are all
instances of this single problem: matching the graphical form to the
logical form. The correspondence invariant
([docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md))
is the contract; the property tests, the `presentation_ops` regime-3
API, and the runtime attestation hook are its operational realization.

### Visible capabilities
- **Formal graph representation** — EGI data model (vertices, edges,
  cuts, areas)
- **Visual diagram system** — Layout generation and rendering,
  correspondence-attested at the service boundary
- **Transformation rules** — DC±, INS/ERA, IT± with full Dau compliance
- **Linear format translation** — EGIF, CGIF, CLIF, FOPL bidirectional
- **Three interaction modes**:
  - **Organon**: Visualization and exploration (read-only)
  - **Ergasterion**: Learning and practice (rule-based editing)
  - **Agon**: Formal interaction (Endoporeutic Game)

---

## Who It Is For

### Primary Users
1. **Researchers** studying Peirce's Existential Graph system and Dau's extensions
2. **Logicians** working with diagrammatic reasoning systems
3. **Students** learning formal logic through visual methods
4. **Educators** teaching logic using graphical notation

### Use Cases
- Transcribing and studying historical EG manuscripts
- Composing and proving logical theorems visually
- Comparing EG notation with symbolic logic systems
- Playing the Endoporeutic Game for theorem validation

---

## Why It Matters

### The Problem
Peirce's Existential Graphs represent a **rigorous, complete visual logic
system** that:

- Is **sound and complete** (proven by Dau)
- Is **more intuitive** than symbolic logic for certain reasoning tasks
- Has **historical significance** (Peirce's major contribution to logic)
- Is **severely under-tooled** (no modern, rigorous implementation exists)

But underneath the under-tooling problem sits a harder one: **doing logic
in pictures requires inerrant correspondence between the picture and the
logic it represents**. Earlier work has tended to treat the drawing as a
visualization of an underlying symbolic structure, where divergences
between drawing and structure are aesthetic preferences. Peirce's view —
and Arisbe's — is the inverse: the picture is the object, and the
symbolic form is a serialization. Correspondence is therefore not a
nicety; it is the condition under which the work is doing what it
claims to.

### Our Solution
Arisbe provides the **first production-quality implementation** that:

- Treats correspondence as a **stated, tested, runtime-attested
  invariant** ([LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md))
- Maintains **mathematical rigor** (Dau's formalism is non-negotiable)
- Provides **practical usability** (researchers can actually use it)
- Enables **interactive exploration** (not just static diagrams)
- Preserves **provenance** (transformation history tracking)

---

## Core Principles

### 1. Peirce's aim, Dau's correctness
Doing logic in pictures is the goal. Dau's formalization guarantees the
logic is right; the correspondence contract guarantees the picture is
saying what the logic says. Framing Arisbe as "an implementation of
Dau" inverts this and misses what the project is for. Dau is the
guarantor; Peirce is the aim.

### 2. Linear-graphical correspondence is the central invariant
The contract is scoped to three regimes (see [LINEAR_GRAPHICAL_CORRESPONDENCE.md](LINEAR_GRAPHICAL_CORRESPONDENCE.md) §4):

- **Composition** (Ergasterion drafts): invariant suspended. Malformed
  and incomplete graphs are how thinking happens; the system's job is
  to help the user *reach* a corresponding state, not enforce one in
  flight.
- **Asserted / canonical** (Agon, Organon, finished work, every
  transformation-rule application): invariant mandatory and
  runtime-attested.
- **Presentation-only**: invariant preserved by construction.
  Reshape and reroute are always free; the API
  (`src/presentation_ops.py`) refuses any proposal that would cross a
  regime boundary.

### 3. Mathematical Rigor
- **Dau's formalism is the foundation** — no shortcuts or
  approximations
- **The mathematical core test suite must always pass** — 654 tests
  passing across 40 test files as of the May 2026 review, covering
  data model, transformation rules, Beta graphs, closure validation,
  isomorphism, proof exercises, and the §3.3 / §5.5 correspondence
  properties
- **Protected core modules** — 17 modules cannot be casually modified
  (see `tools/core_protection_system.py`)

### 4. Immutable Data Model
- **EGI transformations produce new graphs** — no in-place mutations
- **Diachronic state tracking** — `State_n = (EGI_n, LayoutDeltas_n)`
- **Transformation provenance** — complete history of logical
  derivations

### 5. Visual Fidelity
- **Dau-compliant rendering** — diagrams follow formal specifications
- **Correspondence-attested** — every (EGI, drawing) pair the user
  sees passes the §3.3 check at the service boundary
- **Iron-clad area mapping** — spatial representation matches logical
  structure
- **User customization** — layout deltas preserve aesthetic
  preferences

### 6. Practical Usability
- **Interactive performance** — fast enough for real-time use
- **Intuitive interface** — researchers can focus on logic, not
  software
- **Robust tomos handling** — works with published EG literature

---

## Success Criteria

### Phase 1: Foundation (COMPLETE ✅)
- [x] EGI core data model with immutable operations
- [x] Core test suite passing (654 tests, 17 skipped as of 2026-05-31)
- [x] Linear format bidirectional translation (EGIF, CGIF, CLIF, FOPL)
- [x] Transformation rules (DC±, INS/ERA, IT±) with Beta-graph support
- [x] Layout engine with Dau-compliant rendering
- [x] Endoporeutic Game engine (`endoporeutic_game.py`, REPL,
      Z3-validated)

### Phase 2: Correspondence as a Stated Invariant (COMPLETE ✅)
- [x] Specification (`docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`)
- [x] Property tests for all six §7 test shapes
- [x] Regime-3 operations as a production API
      (`src/presentation_ops.py`) that refuses boundary-crossing
      proposals
- [x] Runtime attestation at the layout-service boundary
      (`src/correspondence_attestation.py`)

### Phase 3: Web UI Implementation (IN PROGRESS 🟡)
- [x] FastAPI + ELK layout + browser SVG (canonical render path)
- [x] Diagram serving with correspondence attestation
- [ ] **Organon route** — corpus browser, timeline navigation
- [ ] **Ergasterion route** — private editor, draft graph workflow
- [ ] **Agon route** — Endoporeutic Game arena (REPL available today)
- [ ] Transformation UI — visual rule application with regime-3
      affordances

### Phase 4: Production Readiness (PLANNED 📋)
- [ ] Complete tomos validation (87+ published graphs already covered;
      pending more)
- [ ] Projection conventions named and tested (§3.3 convention
      compliance row)
- [ ] Performance optimization for complex graphs
- [ ] Documentation and user guide
- [ ] Academic publication describing the system, with the
      correspondence invariant as the central contribution

### Long-Term Vision
- [ ] Community adoption by EG researchers
- [ ] Published papers using Arisbe for theorem proving
- [ ] Educational use in logic courses
- [ ] Foundation for further EG research tools

---

## What We Are NOT Building

### Out of Scope
- ❌ General-purpose graph editors
- ❌ Non-EG diagrammatic systems
- ❌ Symbolic logic theorem provers
- ❌ Natural language to logic translation
- ❌ Automated theorem proving (beyond rule validation)

### Boundaries
- **Focus**: Existential Graphs and Dau's formalism specifically
- **Target**: Research and education, not commercial applications
- **Scope**: Implementation and interaction, not logical theory development

---

## Current Status

See the "What Arisbe is, mid-2026" section at the top of this document for
the up-to-date statement.

---

## How to Use This Document

### For AI Assistants
- **Read this first** when starting any session
- **Align all suggestions** with these principles
- **Reference success criteria** when proposing new work
- **Stay in scope** - no feature creep

### For Developers
- **The North Star** - When lost, return here
- **Decision framework** - Does this align with the vision?
- **Scope control** - Is this in bounds or out of scope?
- **Progress tracking** - Update status as milestones complete

### For Review
- **Revisit quarterly** - Ensure vision remains current
- **Update status** - Reflect actual progress
- **Refine criteria** - As we learn what "success" really means

---

*This document is our guiding star. All development decisions should align with this vision. If they don't, either the decision is wrong, or the vision needs updating.*

**Last Updated**: 2026-05-31 (Peirce-first reframe; correspondence
named as central invariant; success criteria refreshed)
**Next Review**: 2026-12-31
