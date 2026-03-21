# Arisbe: Existential Graph System

**The Guiding Star** - Read this first when context is lost

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
- **90 validated core tests** - Mathematical correctness is non-negotiable
- **Protected core modules** - Foundation cannot be casually modified

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
- [x] 90/90 core tests passing (100% mathematical validation)
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

**Phase**: GUI Development - Diachronic Delta Workflow  
**Last Major Milestone**: Area containment validation with layout delta persistence  
**Next Milestone**: Tomos validation and transformation UI  
**Overall Progress**: ~70% complete (foundation solid, GUI progressing)

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

**Last Updated**: 2025-10-13  
**Next Review**: 2025-12-31
