# Arisbe: Existential Graph System

**The Guiding Star** - Read this first when context is lost

---

## What Arisbe is, mid-2026

Arisbe is a Python 3.12 implementation of **Frithjof Dau's formalization of
Peirce's Existential Graphs**, focused on rigor first and ergonomics second.

The mathematical core is in good shape and is the asset to protect:
the EGI data model (immutable; Dau's 6+1 components), the six transformation
rules with full Beta-graph support (lines of identity across cuts), the
headless `RuleInteraction` protocol that lets a UI drive proofs step by step,
linear-format round-trips across **EGIF, CGIF, CLIF, FOPL, JSON** validated
against 130+ corpus examples, and the **Universe of Discourse** abstraction
that treats logical reasoning as a *diachronic process* (a sequence of
synchronic EGI states + transformation history + layout deltas) rather than
a static diagram. Around all of this, ~355 tests pass; 15 modules are
explicitly protected; the protection system, quality dashboard, and corpus
validation tooling work.

What is *not* in good shape, as of the May 2026 review, is the user
interface. The original plan envisioned **Organon / Ergasterion / Agon** as
three Qt windows — corpus browser, transformation workshop, and Endoporeutic
Game arena. That Qt implementation made it ~40% of the way through Organon,
left Ergasterion untested, and never started Agon. In April 2026 active work
shifted to a web viewer (FastAPI + ELK-based layout + browser SVG). In
May 2026 we accepted that bet and archived the Qt code to
`archive/qt-gui-2025/`.

So the 2026 form of the vision is:

- **Mathematical core**: the foundation. Protected. The yardstick for every
  other change.
- **Universe of Discourse**: the central abstraction. The unit of inquiry is
  the diachronic UoD, not the synchronic EGI snapshot.
- **Web viewer** (`src/web_api/` + `src/web_viewer/`) is the canonical user
  surface. The ELK layout engine and SVG renderer are the canonical render
  path.
- **Organon / Ergasterion / Agon** remain as the *conceptual modes* of
  engagement — corpus browsing, transformation practice, formal game —
  but are now best understood as **routes within the web app**, not
  separate windows. Implementing that mapping is the next major UI
  workstream.

The known follow-ups identified during the review (EGIF generator
round-trip bugs found by hypothesis, a stale API-reference regenerator, the
web-app mode implementation, property-test expansion, ELK ligature edge
cases) are tracked as GitHub issues rather than inline here, because that
material moves too fast for a vision doc.

The sections below remain the longer philosophical statement of *why*
this project exists and *who* it serves; they predate the May 2026
realignment and should be read in light of the note above.

---

## What We Are Building

A complete implementation of **Dau's formalism for Peirce's Existential Graphs**, providing:

### Core Capabilities
- **Formal graph representation** - EGI data model (vertices, edges, cuts, areas)
- **Visual diagram system** - Layout generation and rendering
- **Transformation rules** - DC±, INS/ERA, IT± with full Dau compliance
- **Linear format translation** - EGIF, CGIF, CLIF, FOPL bidirectional conversion
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
Existential Graphs represent a **rigorous, complete visual logic system** that:

- Is **sound and complete** (proven by Dau)
- Is **more intuitive** than symbolic logic for certain reasoning tasks
- Has **historical significance** (Peirce's major contribution to logic)
- Is **severely under-tooled** (no modern, rigorous implementation exists)

### Our Solution
Arisbe provides the **first production-quality implementation** that:

- Maintains **mathematical rigor** (Dau's formalism is non-negotiable)
- Provides **practical usability** (researchers can actually use it)
- Enables **interactive exploration** (not just static diagrams)
- Preserves **provenance** (transformation history tracking)

---

## Core Principles

### 1. Mathematical Rigor
- **Dau's formalism is the foundation** - No shortcuts or approximations
- **The mathematical core test suite must always pass** - currently ~355 tests
  covering data model, transformation rules, Beta graphs, closure validation,
  isomorphism, and proof exercises
- **Protected core modules** - 15 modules cannot be casually modified
  (see `tools/core_protection_system.py`)

### 2. Immutable Data Model
- **EGI transformations produce new graphs** - No in-place mutations
- **Diachronic state tracking** - State_n = (EGI_n, LayoutDeltas_n)
- **Transformation provenance** - Complete history of logical derivations

### 3. Visual Fidelity
- **Dau-compliant rendering** - Diagrams follow formal specifications
- **Iron-clad area mapping** - Spatial representation matches logical structure
- **User customization** - Layout deltas preserve aesthetic preferences

### 4. Practical Usability
- **Interactive performance** - Fast enough for real-time use
- **Intuitive interface** - Researchers can focus on logic, not software
- **Robust tomos handling** - Works with published EG literature

---

## Success Criteria

### Phase 1: Foundation (COMPLETE ✅)
- [x] EGI core data model with immutable operations
- [x] Core test suite passing (~355 tests as of 2026-05-29)
- [x] Linear format bidirectional translation (EGIF, CGIF, CLIF, FOPL)
- [x] Transformation rules (DC±, INS/ERA, IT±)
- [x] Layout engine with Dau-compliant rendering

### Phase 2: GUI Implementation (IN PROGRESS 🟡)
- [x] Organon mode - Tomos browsing and visualization
- [x] Ergasterion mode - Interactive editing and learning
- [x] Diachronic delta workflow - User layout persistence
- [ ] Transformation UI - Visual rule application
- [ ] Agon mode - Endoporeutic Game implementation

### Phase 3: Production Readiness (PLANNED 📋)
- [ ] Complete tomos validation (51 published graphs)
- [ ] Performance optimization for complex graphs
- [ ] Documentation and user guide
- [ ] Academic publication describing the system

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

**Last Updated**: 2026-05-29 (mid-2026 realignment note added; vision body unchanged)  
**Next Review**: 2026-12-31
