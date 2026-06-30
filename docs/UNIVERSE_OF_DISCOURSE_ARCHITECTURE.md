# Universe of Discourse: The Fundamental Entity
**Philosophical Foundation and Architectural Implications**

---

## Executive Summary

The fundamental entity in Arisbe is **not** a static Existential Graph Instance ([EGI](GLOSSARY.md#egi)) diagram, but the **Universe of Discourse ([UoD](GLOSSARY.md#uod))** - the diachronic process of logical reasoning itself.

**Key Insight**: A single EGI is a **synchronic snapshot** (a photograph) within the larger **diachronic process** (the film) of evolving logical discourse.

This understanding elevates Arisbe from a diagram editor to a **formal reasoning environment** where justification, transformation history, and logical process are first-class citizens.

For the Peircean reading of *why* the diachronic chain is the unit of meaning — a reasoning episode as a **chain of semiosis**, every rule application an attestation event — see [CHAIN_OF_SEMIOSIS.md](CHAIN_OF_SEMIOSIS.md).

---

## The Problem: Static EGI Focus

### What the Literature Emphasizes
- **A particular graph** (EGI in Dau's formalism)
- Static structural properties
- Transformation rules as isolated operations
- Syntactic well-formedness

### What the Literature Underemphasizes
- **The overall structure** in which an EGI exists and makes sense
- The **context** that gave rise to a particular graph
- The **history** of transformations that produced it
- The **process** of inquiry, abduction, and justification
- The **dynamic evolution** of logical thought

### Result: Incomplete Model
The literature's synchronic focus treats Existential Graphs ([EGs](GLOSSARY.md#eg)) as if they spring into existence fully formed, disconnected from the reasoning process that produced them.

---

## The Solution: Universe of Discourse (UoD)

### Definition
**Universe of Discourse (UoD)**: The complete, evolving logical environment consisting of:

1. **The transformation history** (the recorded sequence of justified rule applications)
2. **The synchronic states** (EGI + LayoutDeltas at each point in time)
3. **The in-forming events** (user actions that drive evolution)
   - **Assertions**: Introducing new facts into the Sheet of Assertion
   - **Abductions**: Proposing hypotheses that explain existing states
   - **Deductions**: Applying formal transformation rules
   - **User edits**: Visual presentation deltas for stability and clarity

### Analogy: Film vs. Photograph
- **Single EGI** = A photograph or frame
  - Has specific composition and meaning
  - Static, synchronic view
  - What the literature focuses on
  
- **Universe of Discourse** = The entire film
  - Coherent sequence of frames
  - Each frame linked by meaningful transitions
  - Full meaning emerges from watching the sequence
  - Dynamic, diachronic process
  - What Arisbe models

---

## Components of a Universe of Discourse

### 1. The Log of Transformations (The History)
**What**: Recorded sequence of valid rule applications  
**Metaphor**: The "plot" of the logical film  
**Implementation**: `EGITransformationHistory` with `TransformationStep` records

**Contains**:

- Rule applications (IT+, IT-, DC+, DC-, INS, ERA)
- Provenance tracking (who, when, why)
- Logical justifications
- Branch management (exploration vs. main path)
- Collaboration metadata (reviewer approvals, annotations)

**Purpose**: Complete audit trail of reasoning process

### 2. The Synchronic States (The EGIs)
**What**: Complete states at each point in the history  
**Metaphor**: Individual "frames" of the film  
**Implementation**: `StateSnapshot` containing `(EGI_Model, LayoutDeltas)`

**Each state captures**:

- **EGI**: Logical structure (RelationalGraphWithCuts)
- **LayoutDeltas**: User-specified visual presentation preferences
- **Linear forms**: Existential Graph Interchange Format ([EGIF](GLOSSARY.md#egif)), Conceptual Graph Interchange Format ([CGIF](GLOSSARY.md#cgif)), Common Logic Interchange Format ([CLIF](GLOSSARY.md#clif)) representations
- **Metadata**: Timestamps, descriptions, domain contexts
- **Natural language**: Human-readable summaries

**Purpose**: Recovery of any historical state for inspection, rollback, or branching

### 3. The In-forming Events (The Director's Cuts)
**What**: External actions that drive the UoD's evolution  
**Metaphor**: The "director's cuts" that change the course of the film  
**Implementation**: User commands in the three application modules

**Event Types**:

#### a. Asserting Facts
- Introducing new EGI content into the Sheet of Assertion
- Sources: Literature imports, Ergasterion promotions, direct user input
- Validation: Must pass [Endoporeutic](GLOSSARY.md#endoporeutic) (reading a graph from the outside in) Game challenge (Agon)

#### b. Abduction
- User proposes new hypothesis (subgraph)
- If accepted, would explain an existing state
- Opens new reasoning branches
- Subject to justification through Agon

#### c. Deduction
- Applying formal transformation rules
- Truth-preserving logical steps
- Recorded in transformation history
- Creates new synchronic state

#### d. User Edits (Visual Deltas)
- Positioning vertices/predicates
- Adjusting ligature routing
- Cut sizing and layout
- **Propagate forward** through history for visual stability
- Logic-indifferent (meaning-preserving)

---

## Three-Module Architecture

### Organon: The Archive 🏛️
**Greek**: ὄργανον ("tool" or "instrument")  
**Role**: Interface to the UoD's history and external world

**Responsibilities**:

1. **History Navigation**
   - Move back/forward through timeline (undo/redo)
   - Jump to specific historical states
   - Visualize transformation sequences
   - Branch exploration and comparison

2. **Exploration**
   - Inspect any EGI state in the history
   - View linear forms (EGIF, CGIF, CLIF)
   - Examine transformation provenance
   - Search and filter corpus

3. **Import/Export**
   - Load UoDs from corpus
   - Import literature examples as standalone EGIs
   - Export snapshots (SVG, LaTeX, PDF)
   - Export proof sequences (YAML, formal proofs)
   - Publish to external formats

**Metaphor**: The library and archives - holds published proceedings, enables reading, citation, export

**User Actions**:

- Browse [tomos](GLOSSARY.md#tomos) of UoDs
- Open historical UoD for inspection
- Navigate transformation history
- Export current state or proof sequence
- Compare states or branches

### Ergasterion: The Workshop 🔬
**Greek**: ἐργαστήριον ("workshop")  
**Role**: Private sandbox for creation and practice

**Responsibilities**:

1. **Draft New Graphs**
   - Create EGI from scratch
   - Build complex facts or hypotheses
   - Experiment with structures
   - No impact on main UoD

2. **Practice Transformations**
   - Apply rules to temporary graphs
   - Build proficiency with transformation rules
   - Explore "what if" scenarios
   - Learn EG calculus safely

3. **Prepare for Promotion**
   - Refine graph until satisfied
   - Validate well-formedness
   - Document intent and justification
   - Ready for challenge by Agon

**Metaphor**: Researcher's private lab - run experiments, work out ideas on whiteboard

**User Actions**:

- Start new practice session
- Load example as starting point
- Apply transformations experimentally
- **Promote** completed work to Agon for acceptance into UoD

**Isolation**: 
- Completely separate from main UoD
- No history tracking (ephemeral)
- Can be discarded without consequence
- Success → Promotion → Agon challenge

### Agon: The Arena ⚔️
**Greek**: ἀγών ("contest" or "struggle")  
**Role**: Core reasoning engine and referee

**Responsibilities**:

1. **Validate Logical Changes**
   - Accept proposed facts from Ergasterion
   - Validate transformation rule applications
   - Enforce Dau formalism compliance
   - Generate next (EGI, Deltas) state

2. **Endoporeutic Game (The Contest)**
   - Referee the justification process
   - Manage Graphist vs. Grapheus dialogue
   - Apply game rules from outside-in (endoporeutic method)
   - Determine acceptance/rejection of assertions

3. **Advance the UoD**
   - Record successful transformations in history
   - Create new synchronic states
   - Maintain diachronic coherence
   - Preserve logical provenance

**Metaphor**: Official conference room - researcher presents validated findings, formally added to record

**The Endoporeutic Game**:

- **Graphist** (Defender/User): Asserts a graph, must defend it
- **Grapheus** (Challenger/System): Attempts to falsify by finding counterexample
- **Game board**: Sheet of Assertion with proposed graph
- **Moves**: Valid transformation rules
- **Goal (Grapheus)**: Reduce graph to empty sheet (prove it's already implied)
- **Goal (Graphist)**: Defend assertion with counter-moves
- **Method**: Read graph from outside-in (endoporeutic)
- **Outcome**: If Graphist wins → assertion accepted into UoD

**User Actions**:

- Propose new fact (from Ergasterion)
- Accept Endoporeutic Game challenge
- Defend assertion with counter-moves
- Apply validated transformation rules
- Observe formal acceptance into UoD history

---

## Complete Workflow

### Scenario: Introducing a New Fact

1. **Proposal** (Ergasterion 🔬)
   - User drafts `EGI_fact` in isolated workshop
   - Experiments with structure
   - Validates well-formedness
   - Refines until satisfied

2. **Challenge** (Agon ⚔️)
   - User proposes `EGI_fact` to main UoD
   - Agon initiates Endoporeutic Game
   - User becomes Graphist (defender)
   - System becomes Grapheus (challenger)

3. **Justification** (Agon ⚔️)
   - Game proceeds with valid transformation moves
   - Grapheus attempts to reduce to empty sheet
   - Graphist defends with counter-moves
   - Process follows endoporeutic method (outside-in)

4. **Acceptance** (Agon ⚔️)
   - If Graphist wins → fact is justified
   - Agon commits `EGI_fact` via `TomosService` (`save_uod` / `save_uod_with_chain`)
   - New `TransformationStep` recorded in history
   - New `StateSnapshot` created: `State_n+1 = (EGI_n+1, Deltas_n+1)`
   - UoD advances to next frame in the film

5. **Archive** (Organon 🏛️)
   - New state now visible in history timeline
   - Can be inspected, exported, cited
   - Forms part of permanent record
   - Available for future reference or rollback

### Scenario: Exploring Transformations

1. **Open** (Organon 🏛️)
   - User loads UoD from corpus
   - Browses history timeline
   - Selects state of interest

2. **Practice** (Ergasterion 🔬)
   - User copies state to Ergasterion
   - "What if I applied IT- here?"
   - Experiments without affecting main UoD
   - Learns by doing

3. **Apply** (Agon ⚔️)
   - User satisfied with experimental result
   - Applies same transformation to main UoD via Agon
   - Transformation validated and recorded
   - UoD history advances

---

## Data Model Implications

### Implemented model: UniverseOfDiscourse
**Current model** (`src/universe_of_discourse.py`):
```python
@dataclass
class UniverseOfDiscourse:
    metadata: UoDMetadata
    current_egi: RelationalGraphWithCuts
    history: Optional[EGITransformationHistory]
```

The earlier `GraphEntity` (`src/graph_entity.py`) was **renamed** to
`UniverseOfDiscourse`, and `EntityMetadata`/`EntityCategory` became
`UoDMetadata`/`UoDCategory` — the "Recommended Refinement" this section once
proposed is **done**. Both the synchronic (`current_egi`) and diachronic
(`history`) aspects are present; persistence is via `TomosService`
(`save_uod`/`load_uod`, and `save_uod_with_chain`/`load_chain` for a worked
chain). For the live developer API see `src/tomos_service.py`,
[CORE_API_USAGE_GUIDE.md](CORE_API_USAGE_GUIDE.md), and
[ARISBE_CORE_API_REFERENCE.md](ARISBE_CORE_API_REFERENCE.md).

### Design rationale: UniverseOfDiscourse

**Model** (implemented in `src/universe_of_discourse.py`):
```python
@dataclass
class UniverseOfDiscourse:
    """
    The fundamental entity: a diachronic process of logical reasoning.
    
    A UoD is NOT a static EGI diagram, but the complete evolving environment
    in which EGIs exist, make sense, and undergo justified transformations.
    
    Components:
    1. Transformation history (the log)
    2. Synchronic states (EGI + LayoutDeltas snapshots)
    3. In-forming events (recorded user actions)
    
    Metaphor: UoD is the film; EGI is a single frame.
    """
    
    # Identity and provenance
    uod_id: str
    name: str
    description: str
    category: UoDCategory
    
    # Timestamps
    created: datetime
    last_modified: datetime
    
    # Synchronic aspect: current state
    current_egi: RelationalGraphWithCuts
    current_layout_deltas: Optional[LayoutDeltas] = None
    
    # Diachronic aspect: complete history
    history: EGITransformationHistory
    
    # Domain and semantic context
    domain_contexts: Set[str] = field(default_factory=set)
    natural_language_summary: Optional[str] = None
    
    # Authorship and collaboration
    authors: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    
    # External references
    source_citation: Optional[str] = None  # For literature imports
    related_uods: List[str] = field(default_factory=list)  # Links to other UoDs
    
    # Tomos storage
    corpus_path: Optional[Path] = None
```

**UoDCategory** (refined from EntityCategory):
```python
class UoDCategory(Enum):
    """Category of Universe of Discourse."""
    
    # Static imports (synchronic snapshots only)
    LITERATURE_EXAMPLE = "literature_example"  # Peirce, Roberts, Sowa, etc.
    CANONICAL_PATTERN = "canonical_pattern"    # Standard logical patterns
    
    # Dynamic reasoning (full diachronic histories)
    ACTIVE_INQUIRY = "active_inquiry"          # User's ongoing reasoning
    THEOREM_PROOF = "theorem_proof"            # Mathematical proof in progress
    DOMAIN_MODEL = "domain_model"              # Real-world modeling
    EPG_SESSION = "epg_session"                # Endoporeutic Game session
    PRACTICE_SESSION = "practice_session"      # Ergasterion practice
    
    # Archives
    COMPLETED_PROOF = "completed_proof"        # Finished theorem proof
    PUBLISHED_ARGUMENT = "published_argument"  # Validated, published reasoning
```

### Key Distinctions

**Static UoD** (from literature):

- Single EGI state
- No transformation history
- Category: `LITERATURE_EXAMPLE`, `CANONICAL_PATTERN`
- Imported from external sources
- Read-only in Organon
- Can be copied to Ergasterion for practice

**Dynamic UoD** (active reasoning):

- Complete transformation history
- Multiple states (timeline)
- Category: `ACTIVE_INQUIRY`, `THEOREM_PROOF`, etc.
- Created and evolved by user
- Full diachronic record
- Main entity for Agon and Ergasterion

---

## Tomos Organization

### Current Structure (Fragmented)
```
tomos/
  graphs/
    <graph_id>/              # Confusing name - not just a graph
      <graph_id>.egi.json    # Single EGI
      <graph_id>.json        # Minimal metadata
      EGDF/
      EXPORTS/
```

### Recommended Structure (UoD-Centric)
```
tomos/
  index.json                         # Tomos index
  
  universes/                         # Main UoD storage
    <uod_id>/
      # Core identity
      uod.meta.json                  # UoD metadata (name, category, authors, etc.)
      
      # Current synchronic state
      current.egi.json               # Current EGI (source of truth)
      current.deltas.json            # Current LayoutDeltas
      
      # Diachronic history
      history/
        history.jsonl                # Transformation log (streaming format)
        snapshots/                   # Full state snapshots every N steps
          state_0000.json            # (EGI + Deltas)
          state_0010.json
          state_0020.json
      
      # Derived artifacts
      linear_forms/                  # Cached linear representations
        current.egif
        current.cgif
        current.clif
      
      exports/                       # User exports
        proof_sequence_001.yaml
        diagram_001.svg
        diagram_001.pdf
      
      # Domain and semantic
      domain_contexts.json           # Domain-specific annotations
      natural_language.md            # Human-readable summary
  
  # Legacy support
  literature/                        # Static literature examples (no history)
    peirce_modus_ponens/
      peirce_modus_ponens.egi.json
      peirce_modus_ponens.meta.json
```

### Index Structure
```json
{
  "corpus_name": "Arisbe Corpus",
  "version": "2.0",
  "universes": [
    {
      "uod_id": "inquiry_001",
      "name": "Investigation of Modus Ponens",
      "category": "active_inquiry",
      "created": "2025-10-14T08:00:00Z",
      "last_modified": "2025-10-14T10:30:00Z",
      "total_states": 15,
      "total_transformations": 14,
      "authors": ["user_123"],
      "tags": ["propositional", "inference"],
      "is_static": false,
      "path": "tomos/universes/inquiry_001"
    },
    {
      "uod_id": "peirce_modus_ponens",
      "name": "Peirce's Modus Ponens Example",
      "category": "literature_example",
      "created": "2025-08-31T12:00:00Z",
      "last_modified": "2025-08-31T12:00:00Z",
      "total_states": 1,
      "total_transformations": 0,
      "source_citation": "Peirce CP 4.394",
      "is_static": true,
      "path": "tomos/literature/peirce_modus_ponens"
    }
  ]
}
```

---

## Module-Specific Data Requirements

### Organon (Archive & Publishing)

**Read Operations**:

- Load UoD index for browsing
- Load UoD metadata (fast, no EGI load)
- Load specific synchronic state (EGI + Deltas)
- Load transformation history (timeline)
- Access specific historical state

**Write Operations**:

- Export current state (SVG, PDF, LaTeX)
- Export proof sequence (YAML, formal proof)
- Export entire UoD (archival format)

**Data Model Needs**:

- Lightweight index for fast browsing
- Lazy loading of history (don't load all states at once)
- Efficient state navigation (jump to arbitrary point)
- Export format converters

### Ergasterion (Workshop)

**Isolation Requirements**:

- Completely separate from main corpus
- Ephemeral storage (can be discarded)
- No automatic history tracking
- Optional: Save as new UoD for later

**Read Operations**:

- Import literature example as starting point
- Copy state from existing UoD
- Load saved practice session

**Write Operations**:

- Save practice session (optional)
- Promote to Agon (triggers UoD creation or update)

**Data Model Needs**:

- Temporary workspace storage
- Import/copy utilities
- Promotion mechanism → Agon validation
- Optional persistence (save/load practice)

### Agon (Core Reasoning Engine)

**Primary Responsibility**:

- Advance the UoD's diachronic history
- Validate all logical changes
- Record transformation steps
- Create new synchronic states

**Read Operations**:

- Load active UoD
- Access current state
- Query transformation history
- Check game state (Endoporeutic Game)

**Write Operations**:

- Record new transformation step
- Create new state snapshot
- Update current state pointer
- Branch history (for explorations)
- Merge branches (after validation)

**Data Model Needs**:

- Transactional state updates (atomic)
- Efficient history append (streaming JSONL)
- Snapshot strategy (balance between full states and deltas)
- Branch management (directed acyclic graph ([DAG](GLOSSARY.md#dag)) of states)
- Validation cache (avoid recomputing)

---

## Implementation Strategy

> **Status (2026-06-08):** this roadmap is largely realized. The
> `UniverseOfDiscourse` model, `UoDCategory`, layout deltas, and the
> UoD-centric `TomosService` (Phases 2–3) are built; all three web modes —
> Organon, Ergasterion, Agon (Phase 4) — are live; the Endoporeutic Game
> engine + Agon V1 arena (Phase 5) shipped 2026-06-01. The phase list below is
> retained as the original plan and its day-estimates as history.

### Phase 1: Conceptual Alignment (Current)
- ✅ Document philosophical foundation (this document)
- ✅ Identify gaps in current model
- ✅ Design `UniverseOfDiscourse` model
- ✅ Refine tomos structure

### Phase 2: Model Refactoring (1-2 days)
- Rename `GraphEntity` → `UniverseOfDiscourse`
- Refactor `EntityCategory` → `UoDCategory`
- Add `LayoutDeltas` to state snapshots
- Enhance metadata for UoD identity

### Phase 3: Storage Migration (2-3 days)
- Implement new tomos structure (`universes/`)
- Migrate existing graphs → UoDs
- Update `TomosService` for UoD-centric operations
- Maintain backward compatibility for literature imports

### Phase 4: Module Integration (3-4 days)
- Update Organon for UoD browsing and history navigation
- Implement Ergasterion isolation and promotion workflow
- Implement Agon validation and history recording
- Connect all three modules through unified `TomosService`

### Phase 5: Endoporeutic Game (5-7 days)
- Implement game logic in Agon
- Graphist vs. Grapheus role management
- Outside-in move validation
- Win/loss conditions
- Integration with transformation history

### Phase 6: Documentation (1-2 days)
- Update README with UoD philosophy
- Document three-module workflow
- Create user guides for each module
- Update API documentation

**Total Estimated Time**: 2-3 weeks

---

## Success Criteria

### Conceptual Clarity
- [ ] Users understand UoD as fundamental entity
- [ ] Distinction between synchronic (EGI) and diachronic (UoD) is clear
- [ ] Three-module architecture maps to user mental model

### Data Model
- [ ] `UniverseOfDiscourse` replaces `GraphEntity`
- [ ] All states are `(EGI, LayoutDeltas)` pairs
- [ ] History is complete audit trail
- [ ] Static vs. dynamic UoDs clearly distinguished

### Tomos Organization
- [ ] Tomos organized around UoDs, not isolated EGIs
- [ ] Efficient storage (JSONL streaming, snapshots)
- [ ] Fast browsing (lightweight index)
- [ ] Literature imports have clear identity

### Module Functionality
- [ ] **Organon**: Navigate history, export, browse corpus
- [ ] **Ergasterion**: Isolated workspace, practice, promotion
- [ ] **Agon**: Validate changes, record history, Endoporeutic Game

### User Experience
- [ ] Workflow matches research analogy (lab → conference → library)
- [ ] Justification through game is intuitive
- [ ] History timeline is explorable
- [ ] Exports preserve provenance

---

## Philosophical Foundation: Pragmatism and Inquiry

### Peirce's Pragmatic Maxim
> "Consider what effects, that might conceivably have practical bearings, we conceive the object of our conception to have. Then, our conception of these effects is the whole of our conception of the object."

**Application to UoD**:

- The "object" is not a static diagram, but the **process of inquiry**
- Its "effects" are the **justified transformations** that advance understanding
- Its "practical bearings" are the **actions** users can take (assert, challenge, defend)
- The "whole conception" is the **diachronic history** of these effects

### Abduction, Deduction, Induction
**Abduction** (Ergasterion):

- Propose hypothesis that explains observations
- Draft new graph structure
- Prepare for challenge

**Deduction** (Agon):

- Apply formal rules to derive consequences
- Truth-preserving transformations
- Recorded in UoD history

**Induction** (Future extension):

- Generalize from multiple UoDs
- Discover patterns across reasoning sessions
- Meta-level learning

### The Endoporeutic Method
From Peirce: Read the graph from **outside to inside** (ἔνδον = "within", πορεύω = "to go")

**Implementation**:

- Start at Sheet of Assertion (outermost)
- Work inward through nested cuts
- Apply rules at each level of nesting
- Grapheus tries to reduce to True (empty sheet)
- Graphist defends with counter-moves

This method embodies the **dialogical nature of inquiry** - truth emerges through contest and justification, not passive acceptance.

---

## Conclusion

By establishing the **Universe of Discourse** as the fundamental entity, Arisbe transcends the limitations of diagram editors and becomes a **true logical reasoning environment**.

**Key Achievements**:

1. **Philosophical rigor**: Aligns with Peirce's pragmatism and dialogical inquiry
2. **Architectural clarity**: Three modules with distinct, coherent responsibilities
3. **Data model fidelity**: Captures both synchronic and diachronic aspects
4. **User empowerment**: Supports drafting, justification, and publication workflows
5. **Historical provenance**: Complete audit trail of reasoning process

**The Paradigm Shift**:

- **Before**: EGI is a static diagram to be edited
- **After**: UoD is a dynamic process; EGI is a frame in that process

**The Result**:

A system that honors Peirce's vision of "moving pictures of thought" - not merely rendering static diagrams, but supporting the **living process of logical inquiry**.

---

**Last Updated**: 2025-10-14  
**Status**: Foundational Architecture Document  
**Next Steps**: Model refactoring and implementation
