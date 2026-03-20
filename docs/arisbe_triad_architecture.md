# Arisbe Triad Architecture

## Overview

Arisbe implements a complete cycle of inquiry through three interconnected modes that model Peirce's vision of logic as a living, diagrammatic practice. The three modes correspond to the three phases of reasoning: *knowing* (Organon), *making* (Ergasterion), and *contesting* (Agon).

The graphical interface is not merely a renderer of logical structures. Following Peirce's conception of "moving pictures of thought," it functions as a facilitator of aesthetic, expressive, and interpretive engagement with diagrams.

---

## The Three Modes

### Organon — Corpus and Exploration

**Purpose**: Knowledge corpus management, graph browsing, linear form import, read-only visualization.

**Location**: `src/gui_clean/organon/`

**Core functions**:
- Browse the tomos (corpus) of EGI graphs by category and metadata
- Import EGIs from linear forms (EGIF, CGIF, CLIF, FOPL)
- View diagrams in multiple styles (Dau, Peirce, Sowa)
- Inspect transformation history (diachronic view of a reasoning session)
- Export to SVG, PNG, LaTeX/TikZ

**Data flow**:
```
Linear form (EGIF/CGIF/CLIF) → parser → EGI → TomosService storage
EGI corpus → OrganonMode → DiagramController → layout → display
```

**API surface**:
```python
from tomos_service import TomosService
corpus = TomosService(Path("corpus"))
uods = corpus.list_uods(is_static=True)
uod = corpus.load_uod(uod_id, load_history=True)
```

**Current status**: Functional for corpus browsing and diagram viewing. Metadata panel and search are pending.

---

### Ergasterion — Workshop and Practice

**Purpose**: Interactive graph construction, transformation practice, derivation sequences.

**Location**: `src/gui_clean/ergasterion/`

**Core functions**:
- Build EGI graphs from scratch using DC+ as the primary composition rule
- Apply any of the six transformation rules to a working graph
- Practice derivations with step-by-step undo/redo
- Work within a composition context (a negatively-enclosed area on the sheet)
- Save completed graphs to the Organon corpus

**Composition principle**: Every graph utterance begins from an empty sheet (or a double-cut context) and is built through rule-governed transformations. The sheet of assertion is the axiomatic ground; DC+ provides the first negation context; INS places content; IT+ and ERA develop and simplify.

**Data flow**:
```
Empty sheet → DC+ → composition context → INS sequence → EGI
EGI → transformation rules → new EGI → history tracking → corpus save
```

**API surface**:
```python
from diagram_controller import DiagramController
from formal_transformation_rules import TransformationContext, AreaPolarity

controller = DiagramController()
controller.load_egi(egi)
# Apply rule
context = TransformationContext(
    source_egi=egi,
    target_area=area_id,
    selected_subgraph=frozenset(element_ids),
    area_polarity=AreaPolarity.NEGATIVE,
    nesting_depth=1,
)
result = InsertionRule().apply_transformation(context)
```

**Current status**: Stub. Development depends on completing the REPL/CLI Endoporeutic Game engine, which provides the core transformation workflow logic.

---

### Agon — Formal Game and Reasoning

**Purpose**: Formal dialogical reasoning via the Endoporeutic Game, proof construction, semantic validation.

**Location**: `src/gui_clean/agon/` (GUI wrapper), `src/endoporeutic_game.py` (engine — pending)

**Core functions**:
- Load a domain model (Universe of Discourse) as an EGIF
- Propose an assertion (another EGIF) to be tested against the domain
- Play the Endoporeutic Game: Proposer (Graphist) and Skeptic (Grapheus) alternate moves
- Validate proofs: a sequence of rule applications from premises to conclusion
- Classify outcomes: tautology, contradiction, or contingent (hypothesis)

**Game structure**:
- **Proposer** seeks to prove their assertion is true in the domain
- **Skeptic** seeks to find a counter-model
- In positive contexts, Skeptic chooses the rule; in negative contexts, Proposer chooses
- The Umpire (automated) validates each move and determines the final outcome

**Domain model as EGIF**: All domain knowledge is represented as an EGIF graph, not as external data or a separate knowledge base. The domain model is itself an EGI — it can be browsed, transformed, and reasoned about using the same tools.

**Data flow**:
```
Domain EGIF → parse → EGI (universe of discourse)
Assertion EGIF → parse → EGI (hypothesis)
GameEngine.play() → alternating moves → GameOutcome
```

**Current status**: The GUI stub is in place. The game engine (`src/endoporeutic_game.py`) is the next major development target. It will be designed as a standalone REPL/CLI first, then wrapped by the GUI.

---

## Shared Infrastructure

### EGI Core (`egi_core_dau.py`)

The single source of truth for all logical content. All three modes read from and write to immutable EGI structures. The mode boundaries are defined by what operations are permitted, not by separate data models.

### DiagramController (`diagram_controller.py`)

Central coordinator shared across all three modes. Manages:
- Current EGI and layout DTO
- Transformation history (diachronic workflow)
- User-defined layout deltas (aesthetic overrides)
- Rule application and validation

### TomosService (`tomos_service.py`)

Corpus management shared across Organon and Agon. Provides fast index-based browsing, UoD loading with history, and persistence.

### Style System (`style_loader.py`, `style_specification.py`)

Three styles selectable across all modes:
- **Dau**: Mathematical — vertex dots, precise labeling
- **Peirce**: Authentic — lines of identity, minimal decoration
- **Sowa**: Conceptual graph — CG-style boxes and ovals

---

## Integration Workflows

### Workflow 1: Import and Browse

```
1. Organon: paste EGIF text or open file
2. parser → EGI → TomosService.save_uod()
3. Organon: corpus browser reflects new entry
4. User selects → DiagramController.load_egi() → display
```

### Workflow 2: Practice a Derivation

```
1. Organon: select starting graph → "Edit in Ergasterion"
2. Ergasterion: DiagramController loads EGI
3. User selects elements → picks rule → TransformationContext built
4. Rule.apply_transformation() → new EGI
5. DiagramController records history step
6. Repeat until goal reached
7. "Save to Corpus" → TomosService persists full UoD with history
```

### Workflow 3: Play the Endoporeutic Game

```
1. Agon: load domain model (EGIF)
2. Agon: enter assertion (EGIF)
3. GameEngine.start_game(domain, assertion)
4. REPL/GUI loop:
   - Proposer: apply rule in negative context
   - Skeptic: challenge or apply rule in positive context
   - Umpire: validate each move
5. GameEngine.evaluate() → WIN | LOSE | DRAW
6. Full game transcript saved as proof notation (EGIF sequence)
```

---

## Architecture Principles

**Immutability**: EGIs are never modified in place. Every transformation produces a new EGI. The history is a DAG of EGI states with rule applications as edges.

**EGIF as the universal language**: Every domain model, assertion, proof step, and corpus entry is representable as EGIF. There is no separate "data model" for the domain — it is an EGI.

**Rule-governed construction**: Every graph utterance in Ergasterion and Agon is produced by applying formal transformation rules. Arbitrary graph editing is not permitted during logical reasoning (only during initial composition in Ergasterion's composition mode).

**Mode separation by permission, not by data**: All three modes operate on the same EGI structures via the same `DiagramController`. The difference is in which operations are available: Organon is read-only; Ergasterion permits composition and practice transformations; Agon enforces the game protocol.

**GUI as facilitator, not renderer**: The graphical interface is designed to develop aesthetic, expressive, and interpretive skills. It exposes the structure of EGI in ways that reward careful attention — not merely displaying a computed picture, but enabling the user to see and think with the diagram.
